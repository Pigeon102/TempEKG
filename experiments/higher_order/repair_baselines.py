# -*- coding: utf-8 -*-
"""Simple repair baseline: prior + noise channel only (no audit rules, no triangles).

Each edge independently takes  argmin_l  -log C(o | l) - (1 - gamma) log q_kind(l), i.e. the per-edge MAP label
under the same noise channel and damped prior that triangle repair uses. Same cross-fit as bai2_combo.py:
validation documents in two folds by hash; inside the training fold, the TUNE third estimates the channel
(confusion of the observed labels) and selects gamma in {0, 0.5} by macro-F1; the other fold is scored once.
The classifier to repair is PL_FILE (default: the Task 1 output).  Run from src/ with TAG=_full.
"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import io, math, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_J = io.open(HERE/"joint_repair.py", encoding="utf-8").read()
exec(SRC_J[:SRC_J.index("def evaluate(docs, obs_of, fin_of):")])
def H(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)

obs = {d["id"]: [PL.get("%s|%s|%s" % (d["id"], e[0], e[1]), "BEFORE") for e in d["edges"]] for d in VA}
docs = sorted(obs)
D = {d["id"]: d for d in VA}

def map_labels(doc, C, gamma):
    out = []
    for (a, b, r, k), o in zip(D[doc]["edges"], obs[doc]):
        best = None
        for l in LABS:
            if Q[k][l] < 1e-4: continue
            v = -C[(k, o, l)] - (1 - gamma) * math.log(Q[k][l])
            if best is None or v < best[0]: best = (v, l)
        out.append(best[1])
    return out

fin = {}
for k in (0, 1):
    trn = [d for d in docs if H("cf" + d) % 2 != k]; tst = [d for d in docs if H("cf" + d) % 2 == k]
    tune = [d for d in trn if H("in3" + d) % 3 == 2]
    C = chan_confusion([D[d] for d in tune], lambda dd: obs[dd["id"]])
    best = None
    for g in (0.0, 0.5):
        pred = [l for d in tune for l in map_labels(d, C, g)]; gold = [e[2] for d in tune for e in D[d]["edges"]]
        m = prf(pred, gold)[0]
        if best is None or m > best[0]: best = (m, g)
    log("fold %d: gamma %.1f (tune macro %.2f%%)" % (k, best[1], 100 * best[0]))
    for d in tst: fin[d] = map_labels(d, C, best[1])

c = Counter(); pred = []; gold = []
for d in docs:
    for e, s, f in zip(D[d]["edges"], obs[d], fin[d]):
        g = e[2]; c["n"] += 1; c["b0"] += (s != g); c["b1"] += (f != g)
        if f != s:
            c["flag"] += 1
            if s != g: c["hit"] += 1; c["fix"] += (f == g)
            else: c["brk"] += 1
        pred.append(f); gold.append(g)
P = c["hit"] / max(1, c["flag"]); R = c["hit"] / max(1, c["b0"]); F = 2 * P * R / (P + R) if P + R else 0
m0 = prf([s for d in docs for s in obs[d]], gold)[0]; m, per, acc = prf(pred, gold)
print("=" * 110); print("PRIOR + NOISE CHANNEL ONLY on %s" % _os.environ.get("PL_FILE", "pred_layered%s.json" % TAG)); print("=" * 110)
print("  macro-F1 %.2f%% -> %.2f%% | error %.2f%% -> %.2f%% | P %.1f R %.1f F1 %.1f | fixed %d broken %d net %+d"
      % (100 * m0, 100 * m, 100 * c["b0"] / c["n"], 100 * c["b1"] / c["n"], 100 * P, 100 * R, 100 * F, c["fix"], c["brk"], c["fix"] - c["brk"]))
print("  F1 per label: " + "  ".join("%s %.1f" % (r[:4], 100 * per[r][2]) for r in LABS))
log("xong")
