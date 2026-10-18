# -*- coding: utf-8 -*-
"""Bai 2 ablations of the triangle energy model (step 3.2, run alone), each choice changed one at a time:
  pipeline      PMI, beta = 10, grid over weighting (mean/sum), lambda, alpha in {0, 0.5}, noise channel
  raw freq      triangle term = -log p~(c) instead of -PMI(c)
  beta 0 / 100  no smoothing towards independence / heavy smoothing
  alpha 0       pure Bayes posterior (alpha fixed to 0)
  sum / mean    weighting fixed
  no channel    noise term removed (every observed label equally trusted)
  no triangles  lambda = 0 (unary terms only)
Scenarios: (1) Bai 1 output, cross-fit on valid exactly as bai2_combo's 'triangle only' row (two folds by
hash, channel = confusion on the fold's tuning third); (2) injected noise 10% on all four edge types
(channel known, tuned on CONFIRMATION-2 of train, seed 51 / valid seed 37). Choice by macro-F1.
Run from src/ with TAG=_full. Log: experiments/logs/ablate_tri.log"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import io, os, math, hashlib, sys
from pathlib import Path
from collections import Counter
HERE = Path(__file__).resolve().parent
JSRC = io.open(HERE/"joint_repair.py", encoding="utf-8").read()
exec(JSRC[:JSRC.index("def evaluate(docs, obs_of, fin_of):")])
J = JSRC[JSRC.index("def corrupt(docs, rho, seed):"):JSRC.index("print()\nprint(\"=\" * 130)")]
exec(J)

def H(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)
_c = {}
def tri_score(kinds, olabs, V):
    key = (V["score"], V["beta"]) + kinds + olabs
    v = _c.get(key)
    if v is not None: return v
    pairs = ((kinds[0], kinds[1]), (kinds[1], kinds[2]), (kinds[0], kinds[2]))
    lq = 0.0
    for (kx, ky), l in zip(pairs, olabs):
        if l.startswith("i"): k, base = ky + kx, l[1:]
        else: k, base = kx + ky, l
        lq += math.log(Q.get(k, Q["EE"]).get(base, 1e-6))
    b = V["beta"]; ck = kinds + olabs
    p = (FREQ.get(ck, 0) + b*math.exp(lq)) / (TOT.get(kinds, 0) + b) if b > 0 else max(FREQ.get(ck, 0), 1e-6) / max(TOT.get(kinds, 0), 1)
    v = math.log(p) - (lq if V["score"] == "pmi" else 0.0)
    _c[key] = v
    return v

def repair_v(d, obs, C, lam, mode, alpha, V, max_sweeps=4):
    lab = list(obs); edges = d["edges"]; tris = d["tris"]; inc = d["inc"]
    def local(j, l):
        k = edges[j][3]
        u = -(1 - alpha) * math.log(Q[k][l]) - (C[(k, obs[j], l)] if V["chan"] else 0.0)
        ts = inc.get(j, ())
        if not ts or lam == 0: return u
        s = 0.0
        for tid, pos_ in ts:
            kinds, parts = tris[tid]
            ol = [olab(lab[jj], rev) for jj, rev in parts]; ol[pos_] = olab(l, parts[pos_][1])
            s -= tri_score(kinds, tuple(ol), V)
        if mode == "mean": s /= len(ts)
        return u + lam * s
    todo = set()
    for kinds, parts in tris:   # suspicious triangles are always found with the pipeline's PMI
        if tri_pmi(kinds, tuple(olab(lab[j], rev) for j, rev in parts)) < 0: todo.update(j for j, _ in parts)
    for _ in range(max_sweeps):
        if not todo: break
        nxt = set()
        for j in todo:
            cur = lab[j]; best, bv = cur, local(j, cur)
            for l in LABS:
                if l == cur or Q[edges[j][3]][l] < 1e-4: continue
                v = local(j, l)
                if v < bv - 1e-9: best, bv = l, v
            if best != cur:
                lab[j] = best
                for tid, _ in inc.get(j, ()):
                    for jj, _ in tris[tid][1]:
                        if jj != j: nxt.add(jj)
        todo = nxt
    return lab

FULL = [("mean", l, a) for l in (0.2, 0.5, 1.0, 2.0) for a in (0.0, 0.5)] + [("sum", l, 0.0) for l in (0.03, 0.1)]
P = {"score": "pmi", "beta": 10.0, "chan": True}
VARIANTS = [
    ("pipeline (PMI, beta 10, kenh nhieu, luoi day du)", P, FULL),
    ("tan suat tho thay PMI", dict(P, score="logp"), FULL),
    ("beta = 0 (khong lam tron)", dict(P, beta=0.0), FULL),
    ("beta = 100", dict(P, beta=100.0), FULL),
    ("alpha = 0 (Bayes thuan)", P, [g for g in FULL if g[2] == 0.0]),
    ("chi cach can sum", P, [g for g in FULL if g[0] == "sum"] + [("sum", 0.3, 0.0), ("sum", 1.0, 0.0)]),
    ("chi cach can mean", P, [g for g in FULL if g[0] == "mean"]),
    ("khong mo hinh nhieu", dict(P, chan=False), FULL),
    ("khong tam giac (lambda = 0)", P, [("mean", 0.0, 0.0), ("mean", 0.0, 0.5)]),
]

def metrics(docs, obs, fin):
    c = Counter(); pred = []; gold = []; sp = []
    for d in docs:
        for (a, b, r, k), s, f in zip(d["edges"], obs[d["id"]], fin[d["id"]]):
            c["n"] += 1; c["b0"] += (s != r); c["b1"] += (f != r)
            if f != s:
                if s != r: c["fix"] += (f == r)
                else: c["brk"] += 1
            pred.append(f); gold.append(r)
            if s != r: sp.append((f, r))
    m = prf(pred, gold)[0]; ms, _, acc = prf([x[0] for x in sp], [x[1] for x in sp])
    return m, c, ms, acc

def macro_of(docs, fin):
    return prf([f for d in docs for f in fin[d["id"]]], [e[2] for d in docs for e in d["edges"]])[0]

def report(name, docs, obs, fin, cfgs):
    m, c, ms, acc = metrics(docs, obs, fin)
    print("  %-48s macro %6.2f%% | loi %5.2f%% -> %5.2f%% | sua %6d pha %5d rong %+6d | canh sai: acc %5.1f%% macro %5.1f%% | %s" % (
        name, 100*m, 100*c["b0"]/c["n"], 100*c["b1"]/c["n"], c["fix"], c["brk"], c["fix"] - c["brk"], 100*acc, 100*ms, cfgs), flush=True)

cls = lambda d: [PL.get("%s|%s|%s" % (d["id"], e[0], e[1]), "BEFORE") for e in d["edges"]]
which = sys.argv[1:] or ["cls", "inj"]
SKIP_CLS = {int(x) for x in os.environ.get("SKIP_CLS", "").split(",") if x}
if "cls" in which:
    print("=" * 130); print("1. DAU RA BAI 1, cross-fit tren valid (nhu dong 'chi tam giac' cua bai2_combo), chon theo macro-F1"); print("=" * 130)
    START = {d["id"]: cls(d) for d in VA}
    m0, c0, _, _ = metrics(VA, START, START)
    print("  chua sua: macro %.2f%%, loi %.2f%%" % (100*m0, 100*c0["b0"]/c0["n"]))
    for vi, (name, V, grid) in enumerate(VARIANTS):
        if vi in SKIP_CLS: continue
        fin = {}; cfgs = []
        for k in (0, 1):
            trn = [d for d in VA if H("cf" + d["id"]) % 2 != k]; tst = [d for d in VA if H("cf" + d["id"]) % 2 == k]
            tune = [d for d in trn if H("in3" + d["id"]) % 3 == 2]
            C = chan_confusion(tune, lambda dd: START[dd["id"]])
            best = None
            for mode, lam, alpha in grid:
                f = {d["id"]: repair_v(d, START[d["id"]], C, lam, mode, alpha, V) for d in tune}
                mm = macro_of(tune, f)
                if best is None or mm > best[0]: best = (mm, mode, lam, alpha)
            _, mode, lam, alpha = best; cfgs.append((mode, lam, alpha))
            for d in tst: fin[d["id"]] = repair_v(d, START[d["id"]], C, lam, mode, alpha, V)
        report(name, VA, START, fin, cfgs)
if "inj" in which:
    print("=" * 130); print("2. NHIEU BOM 10%% CA BON LOAI CANH (kenh nhieu biet truoc), chon theo macro-F1"); print("=" * 130)
    rho = 0.10; C = chan_injected(rho)
    tune_obs = corrupt(TUNE, rho, 51); obs = corrupt(VA, rho, 37)
    m0, c0, _, _ = metrics(VA, obs, obs)
    print("  chua sua: macro %.2f%%, loi %.2f%%" % (100*m0, 100*c0["b0"]/c0["n"]))
    for name, V, grid in VARIANTS:
        best = None
        for mode, lam, alpha in grid:
            f = {d["id"]: repair_v(d, tune_obs[d["id"]], C, lam, mode, alpha, V) for d in TUNE}
            mm = macro_of(TUNE, f)
            if best is None or mm > best[0]: best = (mm, mode, lam, alpha)
        _, mode, lam, alpha = best
        fin = {d["id"]: repair_v(d, obs[d["id"]], C, lam, mode, alpha, V) for d in VA}
        report(name, VA, obs, fin, [(mode, lam, alpha)])
log("xong")
