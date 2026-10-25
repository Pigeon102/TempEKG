# -*- coding: utf-8 -*-
"""What the auditor and the full Task 2 pipeline did on the Nicaragua worked example.

Reads the per-edge outputs of the final cross-fitted Task 2 run (src/artifacts/bai2_rows_full.pkl,
written by bai2_combo.py with DUMP_ROWS=1, the run behind Table 4) and prints, for every edge among
began / 1898 / 1912 / 1933 / 1934, the classifier label, the auditor label, the label after
auditor -> triangle repair, the label after triangle repair alone, and the gold label.
Run from src/.
"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import json, pickle
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
DOC = "f28bce270df5a122c09365002d247e76"
R = pickle.load(open(SRC / "artifacts" / "bai2_rows_full.pkl", "rb"))
print("rows:", sorted(R["rows"]))

g = None
for line in open(SRC / "graph" / "valid.jsonl", encoding="utf-8"):
    d = json.loads(line)
    if d["doc_id"] == DOC: g = d; break
nd = g["nodes"]
name = lambda n: nd[n].get("text") if nd[n]["kind"] == "timex" else nd[n].get("trigger")
# edge order used by the Task 2 code: target edges between events / TIMEX, as stored
edges = [(e["s"], e["t"], e["rel"]) for e in g["target_edges"]
         if nd[e["s"]]["kind"] in ("event", "timex") and nd[e["t"]]["kind"] in ("event", "timex")]
start = R["start"][DOC]
pick = lambda nm: R["rows"][nm][DOC]
aud, full, tri = pick("B | macro-F1" if "B | macro-F1" in R["rows"] else "B | macro"), \
    pick("B -> tam giac | macro-F1" if "B -> tam giac | macro-F1" in R["rows"] else "B -> tam giac | macro"), \
    pick("chi tam giac | macro-F1" if "chi tam giac | macro-F1" in R["rows"] else "chi tam giac | macro")
assert len(edges) == len(start) == len(aud), (len(edges), len(start), len(aud))
want = {"began", "1898", "1912", "1933", "1934"}
print("%-8s %-8s | %-12s %-12s %-12s %-12s | %-12s" % ("a", "b", "classifier", "auditor", "aud->tri", "tri only", "gold"))
for (a, b, gold), s, x, f, t in zip(edges, start, aud, full, tri):
    if name(a) in want and name(b) in want:
        print("%-8s %-8s | %-12s %-12s %-12s %-12s | %-12s" % (name(a), name(b), s, x, f, t, gold))
for nm, out in (("auditor", aud), ("aud->tri", full), ("tri only", tri)):
    ch = sum(1 for s, x in zip(start, out) if s != x)
    w0 = sum(1 for (a, b, gd), s in zip(edges, start) if s != gd)
    w1 = sum(1 for (a, b, gd), x in zip(edges, out) if x != gd)
    print("%-9s changes %d of %d edges; wrong %d -> %d" % (nm, ch, len(edges), w0, w1))
