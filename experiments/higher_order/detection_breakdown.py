# -*- coding: utf-8 -*-
"""How the detection and edge counts of Table 3 are computed, with every changed edge broken down.

For each Task 2 configuration (rows of the final cross-fitted run, bai2_rows_full.pkl), an edge counts as
  flagged   if repair changes its label;
  hit       if it is flagged and was wrong before repair (whether or not the new label is right);
  fixed     if it is flagged, was wrong, and the new label is the gold label;
  wrong->wrong  if it is flagged, was wrong, and the new label is still wrong (hit - fixed);
  broken    if it is flagged and was right before repair.
Detection precision = hit / flagged, recall = hit / wrong before repair.
Also prints the majority-label baseline per edge kind for Table 2.
Run from src/.
"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import json, pickle
from collections import Counter, defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
LABELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
R = pickle.load(open(SRC / "artifacts" / "bai2_rows_full.pkl", "rb"))

gold, kinds = {}, {}
for line in open(SRC / "graph" / "valid.jsonl", encoding="utf-8"):
    d = json.loads(line); nd = d["nodes"]
    es = [e for e in d["target_edges"] if nd[e["s"]]["kind"] in ("event", "timex") and nd[e["t"]]["kind"] in ("event", "timex")]
    gold[d["doc_id"]] = [e["rel"] for e in es]
    k = lambda n: "TX" if nd[n]["kind"] == "timex" else "EV"
    kinds[d["doc_id"]] = [k(e["s"]) + "->" + k(e["t"]) for e in es]

def macro(pairs):
    tp, pp, gp = Counter(), Counter(), Counter()
    for g, p in pairs:
        gp[g] += 1; pp[p] += 1; tp[g] += (g == p)
    f = []
    for l in LABELS:
        P = tp[l] / pp[l] if pp[l] else 0.0; Rr = tp[l] / gp[l] if gp[l] else 0.0
        f.append(2 * P * Rr / (P + Rr) if P + Rr else 0.0)
    return 100 * sum(f) / len(LABELS), [100 * x for x in f]

start = R["start"]
for nm, rows in sorted(R["rows"].items()):
    c = Counter()
    for doc, fin in rows.items():
        for s, f, g in zip(start[doc], fin, gold[doc]):
            c["n"] += 1; c["wrong0"] += (s != g)
            if f != s:
                c["flag"] += 1
                if s != g:
                    c["hit"] += 1
                    if f == g: c["fix"] += 1
                    else: c["ww"] += 1
                else: c["brk"] += 1
    P = c["hit"] / c["flag"]; Rr = c["hit"] / c["wrong0"]
    print("%-24s flagged %6d = hit %6d (fixed %6d + wrong->wrong %5d) + broken %5d | P %.1f R %.1f F1 %.1f"
          % (nm, c["flag"], c["hit"], c["fix"], c["ww"], c["brk"], 100 * P, 100 * Rr, 200 * P * Rr / (P + Rr)))

# majority label per edge kind (training split), scored on the validation set
tr = defaultdict(Counter)
for line in open(SRC / "graph" / "train.jsonl", encoding="utf-8"):
    d = json.loads(line); nd = d["nodes"]
    k = lambda n: "TX" if nd[n]["kind"] == "timex" else "EV"
    for e in d["target_edges"]:
        if nd[e["s"]]["kind"] in ("event", "timex") and nd[e["t"]]["kind"] in ("event", "timex"):
            tr[k(e["s"]) + "->" + k(e["t"])][e["rel"]] += 1
maj = {k: c.most_common(1)[0][0] for k, c in tr.items()}
print("majority label per kind:", maj)
pairs = defaultdict(list)
for doc in gold:
    for g, kk in zip(gold[doc], kinds[doc]):
        pairs[kk].append((g, maj[kk])); pairs["All"].append((g, maj[kk]))
for kk in ("EV->EV", "EV->TX", "TX->EV", "TX->TX", "All"):
    m, f = macro(pairs[kk]); acc = 100 * sum(g == p for g, p in pairs[kk]) / len(pairs[kk])
    print("majority %-7s macro-F1 %.2f acc %.2f | per-label %s" % (kk, m, acc, " ".join("%.1f" % x for x in f)))
