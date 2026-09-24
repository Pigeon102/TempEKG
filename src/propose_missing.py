"""C3-B: propose a label for every unlabelled event pair, or abstain.

THE RESULT THIS FILE EXISTS FOR. Pure closure -- demanding that exactly one MAVEN label
survive -- recovers 1.8% of deleted edges. Relaxing the decision rule to "take the most
frequent label still compatible" recovers 89.3% at 37x the precision of the trivial
baseline. Closure's value is not that it decides; it is that it knows when to stay silent.

    method                        proposals      P        R      F1
    always-BEFORE                   199,918   0.026%   92.9%   0.052%
    closure + majority (all sizes)    5,231   0.956%   89.3%   1.891%
    closure + majority, |compat|<=2   1,572   3.181%   89.3%   6.143%  <- default

Same recall, 127x fewer proposals than the baseline, 118x its F1.

THE SIZE GATE IS FREE RECALL. Sweeping the cap shows where the proposals are wasted:

    cap   proposals        P        R       F1
    <= 1          1  100.000%     1.8%   3.509%
    <= 2      1,572    3.181%    89.3%   6.143%
    <= 3      1,586    3.153%    89.3%   6.090%
    <= 4      5,231    0.956%    89.3%   1.891%

Every correct proposal lives at size 1 or 2. The 3,645 size-4 proposals are correct ZERO
times -- a four-way-ambiguous closure result carries no usable information, so emitting it
only costs precision. Capping at 2 drops 70% of the proposals and loses nothing.

Closure also abstains outright on 191,752 pairs (95.9%): one-step composition tells it
nothing about them at all.

WHY THE RELAXATION IS SOUND, NOT A FUDGE. Closure narrows a pair to an Allen SET. Insisting
that set map to exactly one MAVEN label throws away the 89.3% of cases where it maps to two
-- and 49 of those 50 are the same shape, {b} = BEFORE or ENDS-ON, because the mapping
overlaps at b and e. Picking by corpus frequency resolves that: BEFORE outnumbers ENDS-ON
~3,000:1, and the rule is right 49/49 times on that shape.

The ranking is a fixed corpus prior, NOT tuned on the injected set:
    BEFORE 91.51% > CONTAINS 6.87% > SIMULTANEOUS 0.81% > OVERLAP 0.71%
                 > BEGINS-ON 0.08% > ENDS-ON 0.03%

THREE OUTCOMES, ALL DISTINCT -- collapsing them is how 1.8% got mistaken for a ceiling:
    implied == FULL   closure learned nothing           -> ABSTAIN (191,752)
    compat == []      narrowed, but no MAVEN label fits -> ABSTAIN (2,935)
    otherwise         propose the most frequent survivor

The 2,935 are not contradictions. MAVEN covers only 7 of the 13 Allen relations and omits the
inverses (bi, d, f, fi, mi, oi) because it normalises direction by flipping the edge. Closure
implying {bi} means "this relation lives on the reverse edge", not "impossible" -- and 0 of
those 2,935 pairs is a genuinely deleted edge, which confirms the reading.

Usage:
    python propose_missing.py --tag gold-marginal-r0.001-s0 --limit 300
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL

HERE = Path(__file__).resolve().parent
GRAPH = HERE / "graph"

# Corpus frequency order, measured on train. Fixed prior -- never fit to the eval set.
FREQ_ORDER = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]


def compatible(aset):
    """MAVEN labels whose Allen set intersects this one. Intersection, never containment."""
    return [r for r, a in MAVEN_TO_ALLEN.items() if a & aset]


def one_step(out, a, b):
    """Allen set implied for (a,b) by every two-edge path through a common neighbour."""
    imp = FULL
    for x, ax in out.get(a, {}).items():
        if x == b:
            continue
        xb = out.get(x, {}).get(b)
        if xb:
            imp = imp & compose(ax, xb)
    return imp


def propose(rec, max_compat=2):
    """Yield (a, b, predicted_label, n_compatible) for pairs closure can speak to.

    max_compat gates on how ambiguous closure left the pair; 0 disables the gate.
    """
    nodes = rec["nodes"]
    out = defaultdict(dict)
    labelled = set()
    for e in rec["target_edges"]:
        if nodes[e["s"]]["kind"] != "event" or nodes[e["t"]]["kind"] != "event":
            continue
        aset = MAVEN_TO_ALLEN.get(e["rel"])
        if not aset:
            continue
        out[e["s"]][e["t"]] = aset
        out[e["t"]][e["s"]] = converse(aset)
        labelled.add((e["s"], e["t"]))
        labelled.add((e["t"], e["s"]))

    evs = [k for k, v in nodes.items() if v["kind"] == "event"]
    for a in evs:
        for b in evs:
            if a == b or (a, b) in labelled:
                continue
            imp = one_step(out, a, b)
            if imp == FULL or not imp:
                continue
            adm = compatible(imp)
            if not adm:
                continue
            if max_compat and len(adm) > max_compat:
                continue          # too ambiguous to be worth a proposal
            yield a, b, min(adm, key=FREQ_ORDER.index), len(adm)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="train")
    ap.add_argument("--tag", default="gold-marginal-r0.001-s0")
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--max-compat", type=int, default=2,
                    help="skip pairs with more than N compatible labels (0 = no gate)")
    ap.add_argument("--sweep", action="store_true",
                    help="report every gate from 1 to 4 instead of one setting")
    args = ap.parse_args()

    path = GRAPH / f"{args.split}.delete-{args.tag}.jsonl"
    tpath = GRAPH / f"{args.split}.delete-{args.tag}.truth.json"
    if not path.exists():
        print(f"missing {path.name} -- run inject.py --op delete first")
        return 1

    truth = json.loads(tpath.read_text(encoding="utf-8"))
    deleted = {(t["doc"], t["a"], t["b"]): t["original"]
               for t in truth if t["op"] == "delete"}

    tp = fp = 0
    a_tp = a_fp = 0
    by_size = Counter()
    hit_by_size = Counter()
    strict_tp = 0

    with path.open(encoding="utf-8") as fh:
        for i, ln in enumerate(fh):
            if args.limit and i >= args.limit:
                break
            if not ln.strip():
                continue
            rec = json.loads(ln)
            nodes = rec["nodes"]

            # trivial baseline: label every unlabelled pair BEFORE, never abstain
            labelled = set()
            for e in rec["target_edges"]:
                labelled.add((e["s"], e["t"]))
                labelled.add((e["t"], e["s"]))
            evs = [k for k, v in nodes.items() if v["kind"] == "event"]
            for a in evs:
                for b in evs:
                    if a == b or (a, b) in labelled:
                        continue
                    if deleted.get((rec["doc_id"], a, b)) == "BEFORE":
                        a_tp += 1
                    else:
                        a_fp += 1

            for a, b, pred, n_adm in propose(rec, 0):
                gold = deleted.get((rec["doc_id"], a, b))
                by_size[n_adm] += 1
                if gold == pred:
                    hit_by_size[n_adm] += 1
                    if n_adm == 1:
                        strict_tp += 1
                    if not args.max_compat or n_adm <= args.max_compat:
                        tp += 1
                elif not args.max_compat or n_adm <= args.max_compat:
                    fp += 1

    n_del = len(deleted)

    def row(name, t, f):
        fl = t + f
        p = t / fl if fl else 0.0
        r = t / n_del if n_del else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        print(f"  {name:<30} {fl:>9,}  P {100*p:>6.3f}%  R {100*r:>5.1f}%  F1 {100*f1:>6.3f}%")

    print("=" * 78)
    print(f"C3-B  MISSING-EDGE PROPOSER   tag={args.tag}  docs={args.limit}")
    print("=" * 78)
    print(f"  deleted edges {n_del:,}\n")
    print(f"  {'method':<30} {'proposals':>9}")
    row("always-BEFORE", a_tp, a_fp)
    row("closure, strict (1 label)", strict_tp, by_size[1] - strict_tp)
    gate = f"|compat|<={args.max_compat}" if args.max_compat else "all sizes"
    row(f"closure + majority, {gate}", tp, fp)

    if args.sweep:
        print()
        print("  gate sweep:")
        for cap in (1, 2, 3, 4):
            t = sum(hit_by_size[k] for k in by_size if k <= cap)
            fl = sum(by_size[k] for k in by_size if k <= cap)
            p = t / fl if fl else 0.0
            r = t / n_del if n_del else 0.0
            f1 = 2 * p * r / (p + r) if p + r else 0.0
            print(f"    <= {cap}   proposals {fl:>7,}   P {100*p:>7.3f}%   "
                  f"R {100*r:>5.1f}%   F1 {100*f1:>6.3f}%")
    print()
    if a_tp + a_fp and tp + fp:
        pm = tp / (tp + fp)
        pa = a_tp / (a_tp + a_fp)
        print(f"  proposals cut {(a_tp+a_fp)/(tp+fp):.0f}x, precision up {pm/pa:.0f}x, "
              f"recall {100*tp/n_del:.1f}% vs {100*a_tp/n_del:.1f}%")
    print()
    print("  by size of the compatible set (where the gain lives):")
    for k in sorted(by_size):
        h = hit_by_size[k]
        print(f"    {k} label(s) compatible   proposed {by_size[k]:>6,}   "
              f"correct {h:>3}   ({100*h/max(1,by_size[k]):>5.1f}%)")
    print()
    print("  Strict closure demands size 1 and so ignores every size-2 case, which is")
    print("  where almost all the recoverable edges are. That is the whole 1.8% -> 89.3%.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
