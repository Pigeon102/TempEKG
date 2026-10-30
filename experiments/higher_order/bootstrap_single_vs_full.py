# -*- coding: utf-8 -*-
"""Paired bootstrap over validation documents: single-layer stage vs full Task 1 model (pooled macro-F1).

Reads pred_single_full.json (layered_rules.py with DUMP_SINGLE=1) and pred_layered_full.json. Documents are
resampled with replacement (10,000 rounds, seed 0); both systems are scored on the same resample, so the
interval is for the difference full - single.  Run from src/.
"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import json, random
from pathlib import Path
import numpy as np

SRC = Path(__file__).resolve().parents[2] / "src"
LABELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
LI = {l: i for i, l in enumerate(LABELS)}
S = json.load(open(SRC / "artifacts" / "pred_single_full.json", encoding="utf-8"))
F = json.load(open(SRC / "artifacts" / "pred_layered_full.json", encoding="utf-8"))

# per document: confusion counts (tp, pred, gold per label) for both systems
docs = []
for line in open(SRC / "graph" / "valid.jsonl", encoding="utf-8"):
    d = json.loads(line); nd = d["nodes"]
    cs = np.zeros((2, 3, 6))
    for e in d["target_edges"]:
        if nd[e["s"]]["kind"] not in ("event", "timex") or nd[e["t"]]["kind"] not in ("event", "timex"): continue
        key = "%s|%s|%s" % (d["doc_id"], e["s"], e["t"]); g = LI[e["rel"]]
        for j, P in enumerate((S, F)):
            p = LI[P[key]]; cs[j, 1, p] += 1; cs[j, 2, g] += 1; cs[j, 0, g] += (p == g)
    docs.append(cs)
docs = np.array(docs)

def macro(c):
    tp, pp, gp = c[0], c[1], c[2]
    P = np.divide(tp, pp, out=np.zeros(6), where=pp > 0); R = np.divide(tp, gp, out=np.zeros(6), where=gp > 0)
    f = np.divide(2 * P * R, P + R, out=np.zeros(6), where=(P + R) > 0)
    return 100 * f.mean()

tot = docs.sum(0)
ms, mf = macro(tot[0]), macro(tot[1])
rng = random.Random(0); n = len(docs); diffs = []
for _ in range(10000):
    idx = [rng.randrange(n) for _ in range(n)]
    c = docs[idx].sum(0); diffs.append(macro(c[1]) - macro(c[0]))
diffs = np.sort(np.array(diffs))
lo, hi = diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs)) - 1]
p_two = 2 * min((diffs <= 0).mean(), (diffs >= 0).mean())
print("single-layer %.2f  full %.2f  difference %.2f | 95%% CI [%.2f, %.2f] | two-sided bootstrap p = %.3f (%d documents, 10,000 resamples)"
      % (ms, mf, mf - ms, lo, hi, p_two, n))
