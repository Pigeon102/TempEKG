"""Per-label P/R/F1 and support of Task 1 by directed edge kind, on the validation graph.

Reads the stage-1 predictions (pred_all_edges_full.json) and the final predictions
(pred_layered_full.json) and prints one row per (kind, label), plus the pooled rows.
Used for the per-label table in the appendix of the paper.
"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "src" / "artifacts"
LABELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
KINDS = ["EV->EV", "EV->TX", "TX->EV", "TX->TX"]


def kind(a, b):
    k = lambda n: "TX" if n.startswith("TIME") else "EV"
    return k(a) + "->" + k(b)


def load_gold():
    gold = {}
    with open(ROOT / "src" / "graph" / "valid.jsonl", encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            for e in d["target_edges"]:
                gold["%s|%s|%s" % (d["doc_id"], e["s"], e["t"])] = e["rel"]
    return gold


def scores(pairs):
    tp, pp, gp = Counter(), Counter(), Counter()
    for g, p in pairs:
        gp[g] += 1; pp[p] += 1
        if g == p: tp[g] += 1
    out = {}
    for l in LABELS:
        P = tp[l] / pp[l] if pp[l] else 0.0
        R = tp[l] / gp[l] if gp[l] else 0.0
        out[l] = (P, R, 2 * P * R / (P + R) if P + R else 0.0, gp[l])
    return out


def main():
    gold = load_gold()
    preds = {nm: json.load(open(ART / fn)) for nm, fn in
             (("stage1", "pred_all_edges_full.json"), ("final", "pred_layered_full.json"))}
    full = lambda p: {"BEF": "BEFORE"}.get(p, p)
    norm = {l[:4]: l for l in LABELS}
    for nm, P in preds.items():
        rows = {k: [] for k in KINDS + ["All"]}
        miss = 0
        for key, g in gold.items():
            if key not in P: miss += 1; continue
            p = P[key]; p = norm.get(p[:4], p)
            _, a, b = key.split("|")
            rows[kind(a, b)].append((g, p)); rows["All"].append((g, p))
        print("== %s (missing %d)" % (nm, miss))
        for k, pairs in rows.items():
            sc = scores(pairs)
            macro = 100 * sum(v[2] for v in sc.values()) / len(LABELS)
            print("  %-7s n=%6d macro %.2f | " % (k, len(pairs), macro) +
                  "  ".join("%s %.1f (n=%d)" % (l[:4], 100 * sc[l][2], sc[l][3]) for l in LABELS))


if __name__ == "__main__":
    main()
