"""Run the injection experiments across seeds and report confidence intervals.

WHY. Every C3 number so far rests on one draw: 60 injected relabels and 56 deletions, seed 0.
At those counts a single edge moves recall by 1.7 points, so "89.3%" and "96.7%" are quoted
with a precision the sample cannot support. Anything we put in a paper needs a spread.

WHAT IT REPORTS. For each metric, the mean across seeds and a 95% interval. Two kinds of
variation are conflated if you are not careful, so this separates them:

    sampling  which edges got corrupted (differs per seed)
    method    how the detector behaves (fixed)

Only the first varies here, which is exactly the uncertainty we want to quote.

The interval is the normal approximation mean +/- 1.96 * sd / sqrt(n). With 5 seeds that is
itself rough, but it is honest about the order of magnitude, which a single point estimate
is not.

MEASURED over seeds 0-4 (300 docs, rate 0.001):

    repair (relabel)   93.67%  +/- 1.86   [91.80, 95.53]
    closure silent      5.90%  +/- 1.59
    repaired WRONG      0.44%  +/- 0.53   [0, 0.97]   <- the strongest claim in C3
    R_all (delete)     92.72%  +/- 4.64   [88.08, 97.36]

The single-seed figures reported earlier (96.7% repair, 89.3% recall) both fall inside these
intervals, so they are stable enough to quote -- but quote them WITH the interval: at 66-96
corrupted edges per seed, one edge moves recall by 1.22 points.

NOTE ON R_all vs propose_missing.py (92.72% here, 89.3% there). Not a contradiction, a
different protocol: this file scans pairs among events that appear in some edge, while
propose_missing.py scans every event node in the document, including the 20% that carry no
edge at all. The wider denominator lowers both recall and precision there. Use
propose_missing.py's number when comparing against the always-BEFORE baseline, since that
baseline also has to label every pair.

Usage:
    python sweep_seeds.py --seeds 0,1,2,3,4
    python sweep_seeds.py --seeds 0,1,2,3,4 --rate 0.001 --limit 300
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
from collections import Counter, defaultdict
from pathlib import Path

from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL

HERE = Path(__file__).resolve().parent
GRAPH = HERE / "graph"

RELATIONS = ("BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON")
FREQ_ORDER = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]


def compatible(aset):
    return [r for r, a in MAVEN_TO_ALLEN.items() if a & aset]


def one_step(out, a, b):
    imp = FULL
    for x, ax in out.get(a, {}).items():
        if x == b:
            continue
        xb = out.get(x, {}).get(b)
        if xb:
            imp = imp & compose(ax, xb)
    return imp


def load_docs(limit):
    docs = []
    labels = Counter()
    with (GRAPH / "train.jsonl").open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if limit and i >= limit:
                break
            if not line.strip():
                continue
            rec = json.loads(line)
            nodes = rec["nodes"]
            es = [(e["s"], e["t"], e["rel"]) for e in rec["target_edges"]
                  if nodes[e["s"]]["kind"] == "event"
                  and nodes[e["t"]]["kind"] == "event"
                  and e["rel"] in MAVEN_TO_ALLEN]
            if len(es) >= 3:
                docs.append(es)
                labels.update(r for _, _, r in es)
    total = sum(labels.values())
    return docs, {r: labels[r] / total for r in RELATIONS}


def one_seed(docs, marginal, rate, seed, max_compat=2):
    """One draw: corrupt, then measure repair (relabel) and proposal (delete)."""
    rng = random.Random(seed)

    # ---- relabel: can closure restore the original label?
    fixed = silent = wrong = n_bad = 0
    for edges in docs:
        cor = []
        bad = {}
        for a, b, r in edges:
            if rng.random() < rate:
                others = [x for x in RELATIONS if x != r]
                new = rng.choices(others, weights=[marginal.get(x, 0.0) for x in others])[0]
                cor.append((a, b, new))
                bad[(a, b)] = r
            else:
                cor.append((a, b, r))
        if not bad:
            continue
        n_bad += len(bad)
        adj = defaultdict(dict)
        for a, b, r in cor:
            aset = MAVEN_TO_ALLEN[r]
            adj[a][b] = aset
            adj[b][a] = converse(aset)
        for (a, b), orig in bad.items():
            held = defaultdict(dict)
            for x, d in adj.items():
                for y, v in d.items():
                    if (x, y) in ((a, b), (b, a)):
                        continue
                    held[x][y] = v
            imp = one_step(held, a, b)
            if imp == FULL or not imp:
                silent += 1
                continue
            adm = compatible(imp)
            if not adm:
                silent += 1
                continue
            pred = min(adm, key=FREQ_ORDER.index)
            if pred == orig:
                fixed += 1
            else:
                wrong += 1

    # ---- delete: can closure propose the missing label?
    rng = random.Random(seed + 10_000)
    tp = fp = 0
    n_del = 0
    for edges in docs:
        keep = []
        deleted = {}
        for a, b, r in edges:
            if rng.random() < rate:
                deleted[(a, b)] = r
            else:
                keep.append((a, b, r))
        if not deleted:
            continue
        n_del += len(deleted)
        adj = defaultdict(dict)
        labelled = set()
        for a, b, r in keep:
            aset = MAVEN_TO_ALLEN[r]
            adj[a][b] = aset
            adj[b][a] = converse(aset)
            labelled.add((a, b))
            labelled.add((b, a))
        evs = sorted({n for e in edges for n in e[:2]})
        for a in evs:
            for b in evs:
                if a == b or (a, b) in labelled:
                    continue
                imp = one_step(adj, a, b)
                if imp == FULL or not imp:
                    continue
                adm = compatible(imp)
                if not adm or len(adm) > max_compat:
                    continue
                pred = min(adm, key=FREQ_ORDER.index)
                if deleted.get((a, b)) == pred:
                    tp += 1
                else:
                    fp += 1

    return {
        "n_bad": n_bad,
        "repair_rate": fixed / n_bad if n_bad else 0.0,
        "silent_rate": silent / n_bad if n_bad else 0.0,
        "wrong_rate": wrong / n_bad if n_bad else 0.0,
        "n_del": n_del,
        "recall": tp / n_del if n_del else 0.0,
        "precision": tp / (tp + fp) if tp + fp else 0.0,
        "proposals": tp + fp,
    }


def ci(xs):
    """Mean and a 95% normal interval. With 5 seeds this is rough but honest."""
    if len(xs) < 2:
        return (xs[0] if xs else 0.0), 0.0
    m = statistics.mean(xs)
    half = 1.96 * statistics.stdev(xs) / math.sqrt(len(xs))
    return m, half


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", default="0,1,2,3,4")
    ap.add_argument("--rate", type=float, default=0.001)
    ap.add_argument("--limit", type=int, default=300)
    args = ap.parse_args()

    seeds = [int(x) for x in args.seeds.split(",")]
    docs, marginal = load_docs(args.limit)
    print(f"{len(docs):,} documents, rate {args.rate}, seeds {seeds}\n", flush=True)

    runs = []
    print(f"  {'seed':>5} {'#bad':>6} {'repair':>8} {'silent':>8} "
          f"{'#del':>6} {'recall':>8} {'prec':>8} {'props':>7}")
    print("  " + "-" * 62)
    for sd in seeds:
        r = one_seed(docs, marginal, args.rate, sd)
        runs.append(r)
        print(f"  {sd:>5} {r['n_bad']:>6,} {100*r['repair_rate']:>7.2f}% "
              f"{100*r['silent_rate']:>7.2f}% {r['n_del']:>6,} "
              f"{100*r['recall']:>7.2f}% {100*r['precision']:>7.3f}% "
              f"{r['proposals']:>7,}", flush=True)

    print()
    print("  95% interval over seeds (normal approximation)")
    print("  " + "-" * 62)
    for key, label in (("repair_rate", "sua dung (relabel)"),
                       ("silent_rate", "closure im lang"),
                       ("wrong_rate", "sua SAI"),
                       ("recall", "R_all (delete)"),
                       ("precision", "precision (delete)")):
        m, h = ci([r[key] for r in runs])
        print(f"  {label:<22} {100*m:>7.2f}%  +/- {100*h:>5.2f}   "
              f"[{100*(m-h):>6.2f}, {100*(m+h):>6.2f}]")

    nb = [r["n_bad"] for r in runs]
    nd = [r["n_del"] for r in runs]
    print()
    print(f"  mau: {min(nb)}-{max(nb)} canh bi doi nhan, {min(nd)}-{max(nd)} canh bi xoa")
    print(f"  mot canh = {100/statistics.mean(nb):.2f} diem recall -- do la do phan giai that")
    print()
    print("  Con so seed 0 da bao truoc day nam trong khoang nay hay khong, moi la dieu")
    print("  quyet dinh co duoc trich no nhu mot ket qua on dinh khong.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
