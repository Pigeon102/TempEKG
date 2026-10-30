# -*- coding: utf-8 -*-
"""Baseline classifier on the same features: multinomial logistic regression per edge kind.

Features are the atoms of the five observable layers (ONT, ARG, DISC, LEX, TIME) that the cross-layer
rules use, built exactly as in layered_rules.py; no temporal label of another edge is read.
  train      DISCOVERY + CONFIRMATION parts of the training split (atoms seen >= 5 times)
  tune       per-label score offsets chosen on the TUNING part to maximise macro-F1 (the rule
             classifier's per-label thresholds play the same role)
  evaluate   validation set, opened once
Writes src/artifacts/pred_layered_lr.json (every train and validation pair), so that Task 2 can be run
on this classifier with PL_FILE=pred_layered_lr.json.  Run from src/ with TAG=_full.
"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import io, json
from pathlib import Path
from collections import Counter
import numpy as np
HERE = Path(__file__).resolve().parent
SRC_L = io.open(HERE/"layered_rules.py", encoding="utf-8").read()
exec(SRC_L[:SRC_L.index("FINAL = {}")])

LABS6 = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
LI = {l: i for i, l in enumerate(LABS6)}
rng = np.random.default_rng(0)

def feats(x):
    return [(ly, a) for ly in LAYERS for a in x["L"].get(ly, ())]

def macro_f1(pred, gold):
    tp, pp, gp = Counter(), Counter(), Counter()
    for p, g in zip(pred, gold):
        pp[p] += 1; gp[g] += 1; tp[g] += (p == g)
    f = []
    for l in range(6):
        P = tp[l] / pp[l] if pp[l] else 0.0; R_ = tp[l] / gp[l] if gp[l] else 0.0
        f.append(2 * P * R_ / (P + R_) if P + R_ else 0.0)
    return sum(f) / 6, f

def encode(xs, vocab):
    idx, ptr = [], [0]
    for x in xs:
        ids = sorted({vocab[f] for f in feats(x) if f in vocab}); idx += ids; ptr.append(len(idx))
    return np.array(idx, dtype=np.int64), np.array(ptr, dtype=np.int64)

def scores(W, b, idx, ptr):
    out = np.zeros((len(ptr) - 1, 6), dtype=np.float32)
    rows = np.repeat(np.arange(len(ptr) - 1), np.diff(ptr))
    np.add.at(out, rows, W[idx])
    return out + b

def train(idx, ptr, y, nfeat, epochs=8, batch=4096, lr=0.05, l2=1e-6):
    W = np.zeros((nfeat, 6), dtype=np.float32); b = np.zeros(6, dtype=np.float32)
    mW = np.zeros_like(W); vW = np.zeros_like(W); mb = np.zeros_like(b); vb = np.zeros_like(b); t = 0
    n = len(y)
    for ep in range(epochs):
        order = rng.permutation(n)
        for s in range(0, n, batch):
            sel = order[s:s + batch]
            bi = np.concatenate([idx[ptr[i]:ptr[i + 1]] for i in sel]) if len(sel) else np.zeros(0, np.int64)
            bp = np.concatenate([[0], np.cumsum([ptr[i + 1] - ptr[i] for i in sel])])
            z = scores(W, b, bi, bp); z -= z.max(1, keepdims=True)
            p = np.exp(z); p /= p.sum(1, keepdims=True)
            p[np.arange(len(sel)), y[sel]] -= 1.0; p /= len(sel)
            gW = np.zeros_like(W); rows = np.repeat(np.arange(len(sel)), np.diff(bp))
            np.add.at(gW, bi, p[rows]); gW += l2 * W; gb = p.sum(0)
            t += 1
            for P_, G, M, V in ((W, gW, mW, vW), (b, gb, mb, vb)):
                M *= 0.9; M += 0.1 * G; V *= 0.999; V += 0.001 * G * G
                P_ -= lr * (M / (1 - 0.9 ** t)) / (np.sqrt(V / (1 - 0.999 ** t)) + 1e-8)
    return W, b

def tune_offsets(S, y):
    off = np.zeros(6, dtype=np.float32)
    best = macro_f1(list(np.argmax(S, 1)), list(y))[0]
    for _ in range(3):
        for l in range(1, 6):
            for d in np.arange(-2.0, 6.01, 0.25):
                o2 = off.copy(); o2[l] = d
                m = macro_f1(list(np.argmax(S + o2, 1)), list(y))[0]
                if m > best: best, off = m, o2
    return off, best

SAVE = {}; ALLP = []; ALLG = []
print("=" * 110); print("BASELINE: logistic regression on the observable layer atoms, per edge kind"); print("=" * 110)
for k in ("EE", "ET", "TE", "TT"):
    tr = [x for x in ITR if x["k"] == k and x["sp"] in ("disc", "conf1")]
    tu = [x for x in ITR if x["k"] == k and x["sp"] == "conf2"]
    va = [x for x in IVA if x["k"] == k]
    cnt = Counter(f for x in tr for f in set(feats(x)))
    vocab = {f: i for i, f in enumerate(sorted(f for f, c in cnt.items() if c >= 5))}
    itr, ptr_tr = encode(tr, vocab); ytr = np.array([LI[x["g"]] for x in tr])
    W, b = train(itr, ptr_tr, ytr, len(vocab))
    itu, ptu = encode(tu, vocab); off, mt = tune_offsets(scores(W, b, itu, ptu), np.array([LI[x["g"]] for x in tu]))
    for part in (ITR_k := [x for x in ITR if x["k"] == k], va):
        ii, pp = encode(part, vocab); pr = np.argmax(scores(W, b, ii, pp) + off, 1)
        for x, p in zip(part, pr): SAVE["%s|%s|%s" % (x["doc"], x["a"], x["b"])] = LABS6[p]
    pv = [LI[SAVE["%s|%s|%s" % (x["doc"], x["a"], x["b"])]] for x in va]; gv = [LI[x["g"]] for x in va]
    m, f = macro_f1(pv, gv); acc = sum(p == g for p, g in zip(pv, gv)) / len(gv)
    ALLP += pv; ALLG += gv
    log("%s: %d features, train %d, tune macro %.2f%%" % (k, len(vocab), len(tr), 100 * mt))
    print("  %s  macro-F1 %6.2f%%  acc %6.2f%%  | %s" % (k, 100 * m, 100 * acc, "  ".join("%s %.1f" % (l[:4], 100 * v) for l, v in zip(LABS6, f))), flush=True)
m, f = macro_f1(ALLP, ALLG); acc = sum(p == g for p, g in zip(ALLP, ALLG)) / len(ALLG)
print("  All macro-F1 %6.2f%%  acc %6.2f%%  | %s" % (100 * m, 100 * acc, "  ".join("%s %.1f" % (l[:4], 100 * v) for l, v in zip(LABS6, f))))
json.dump(SAVE, io.open(ART/"pred_layered_lr.json", "w", encoding="utf-8"))
log("da luu %d du doan -> pred_layered_lr.json; xong" % len(SAVE))
