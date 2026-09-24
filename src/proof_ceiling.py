"""How much of a deleted edge is recoverable by logic alone, at increasing strength.

An earlier measurement said one-step Allen closure recovers 79.2% of deleted edges and
called that "the ceiling for logical C3-B". That phrasing was too strong: it is the ceiling
for ONE-STEP closure under this deletion protocol, not an upper bound for any logical
method. Multi-step closure and full path consistency both see further.

This measures the ladder, so the paper can name the right baseline for each rung and report
what learned rules add beyond the strongest purely logical one.

    1-step     a-b forced by some path a->x->b
    2-step     also paths a->x->y->b
    PC-2       full path consistency to fixpoint over the remaining edges

Usage:
    python proof_ceiling.py --docs 300
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from constraint_net import MAVEN_TO_ALLEN, compose, converse, path_consistency, FULL

GRAPH = Path(__file__).resolve().parent / "graph"


def one_step(out, a, b):
    implied = FULL
    for x, ax in out.get(a, {}).items():
        if x == b:
            continue
        xb = out.get(x, {}).get(b)
        if xb:
            implied = implied & compose(ax, xb)
    return implied


def two_step(out, a, b):
    """One-step, intersected with everything reachable through two intermediates."""
    implied = one_step(out, a, b)
    for x, ax in out.get(a, {}).items():
        if x == b:
            continue
        for y, xy in out.get(x, {}).items():
            if y in (a, b):
                continue
            yb = out.get(y, {}).get(b)
            if yb:
                implied = implied & compose(compose(ax, xy), yb)
    return implied


def decided_as(implied, target):
    """RECOVERED: closure leaves exactly one MAVEN label, and it is the gold one.

    This is the honest recovery test, and the headline rate. Two weaker tests exist and
    must never be reported as recovery:

        contradiction?      allen(gold) & implied == {}   -> closure_conflicts2.py
        constrained enough? implied <= allen(gold)        -> constrained_as(), diagnostic only
        RECOVERED           exactly one label survives    -> HERE

    Why containment is not recovery. Measured on 948 held-out deletions:

        containment succeeds      770   81.2%
          of which truly decided   46    4.9%
          of which still ambiguous 724   76.4%

    and 701 of those 724 are one single case: gold BEFORE, closure narrows to {b}, which
    is still compatible with ENDS-ON={b,m}. So 91% of the 81.2% is "gold was BEFORE and
    closure agreed it was not CONTAINS/OVERLAP/SIMULTANEOUS" -- something the 89.94% BEFORE
    base rate hands over almost free. The mapping has only two overlaps, b (BEFORE/ENDS-ON)
    and e (SIMULTANEOUS/BEGINS-ON), and essentially all the inflation comes from the first.

    Report 4.4%. Keep containment only as a diagnostic, always with this decomposition.
    """
    adm = [r for r, a in MAVEN_TO_ALLEN.items() if a & implied]
    return len(adm) == 1 and MAVEN_TO_ALLEN[adm[0]] == target


def constrained_as(implied, target):
    """DIAGNOSTIC: every surviving reading satisfies gold, but maybe several labels do.

    Inflated by the b and e overlaps -- see decided_as(). Never a recovery rate.
    """
    return implied <= target


def pc_full(nodes, constraints, a, b):
    """Full path consistency over the surviving edges; read the a-b cell afterwards."""
    ok, (idx, m) = path_consistency(nodes, constraints)
    if not ok or a not in idx or b not in idx:
        return FULL
    return m[idx[a]][idx[b]]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--docs", type=int, default=300)
    ap.add_argument("--per-doc", type=int, default=3)
    args = ap.parse_args()

    stats = Counter()
    exact = Counter()          # implied set == the deleted label's set
    narrowed = Counter()       # informative but not exact
    residual_examples = []
    ambig = Counter()

    docs = 0
    with (GRAPH / "train.jsonl").open(encoding="utf-8") as fh:
        for line in fh:
            if docs >= args.docs:
                break
            rec = json.loads(line)
            nodes_d = rec["nodes"]
            edges = [(e["s"], e["t"], e["rel"]) for e in rec["target_edges"]
                     if nodes_d[e["s"]]["kind"] == "event"
                     and nodes_d[e["t"]]["kind"] == "event"]
            if len(edges) < 3:
                continue
            docs += 1

            step = max(1, len(edges) // args.per_doc)
            for idx0 in range(0, len(edges), step):
                a, b, rel = edges[idx0]
                target = MAVEN_TO_ALLEN.get(rel)
                if not target:
                    continue
                rest = [e for i, e in enumerate(edges) if i != idx0]

                out = defaultdict(dict)
                cons = {}
                for s, t, r in rest:
                    aset = MAVEN_TO_ALLEN.get(r)
                    if not aset:
                        continue
                    out[s][t] = aset
                    out[t][s] = converse(aset)
                    cons[(s, t)] = aset
                if not cons:
                    continue

                stats["tested"] += 1

                i1 = one_step(out, a, b)
                # diagnostic: containment, and how much of it is genuinely decided
                if constrained_as(i1, target):
                    stats["contained"] += 1
                    if decided_as(i1, target):
                        stats["contained_decided"] += 1
                    else:
                        stats["contained_ambiguous"] += 1
                        adm = tuple(sorted(r for r, a_ in MAVEN_TO_ALLEN.items()
                                           if a_ & i1))
                        ambig[(rel, adm)] += 1
                if decided_as(i1, target):
                    exact["1-step"] += 1
                elif i1 != FULL:
                    narrowed["1-step"] += 1

                i2 = two_step(out, a, b)
                if decided_as(i2, target):
                    exact["2-step"] += 1
                elif i2 != FULL:
                    narrowed["2-step"] += 1

                nodes_list = sorted({n for pair in cons for n in pair} | {a, b})
                if len(nodes_list) <= 40:
                    ipc = pc_full(nodes_list, cons, a, b)
                    stats["pc_run"] += 1
                    # same-population counters: only cases where all three methods ran
                    if decided_as(i1, target):
                        exact["1-step|pc"] += 1
                    if decided_as(i2, target):
                        exact["2-step|pc"] += 1
                    if decided_as(ipc, target):
                        exact["PC-2"] += 1
                    elif ipc != FULL:
                        narrowed["PC-2"] += 1
                    if i1 > target and decided_as(ipc, target):
                        stats["pc_beats_1step"] += 1
                    if not decided_as(i1, target) and not decided_as(ipc, target) and len(residual_examples) < 5:
                        residual_examples.append({
                            "doc": rec["doc_id"], "rel": rel,
                            "trig_a": nodes_d[a].get("trigger"),
                            "trig_b": nodes_d[b].get("trigger"),
                            "one_step": sorted(i1)[:6],
                            "pc": sorted(ipc)[:6],
                        })

    n = stats["tested"]
    npc = stats["pc_run"]
    print(f"documents sampled       {docs:,}")
    print(f"edges deleted & tested  {n:,}")
    print(f"  of which PC-2 ran on  {npc:,}  (skipped documents over 40 nodes)")
    print()
    print(f"  {'method':<10} {'exact':>8} {'rate':>8} {'narrowed':>10} {'no info':>9}")
    print("  " + "-" * 48)
    print("  (all deletions)")
    for m, denom in (("1-step", n), ("2-step", n)):
        e, w = exact[m], narrowed[m]
        if not denom:
            continue
        print(f"  {m:<10} {e:>8,} {100*e/denom:>7.1f}% {w:>10,} {denom-e-w:>9,}")

    print()
    print(f"  (restricted to the {npc:,} cases where PC-2 ran -- same population)")
    for m in ("1-step|pc", "2-step|pc", "PC-2"):
        key = m if m != "PC-2" else "PC-2"
        e, w = exact[key], narrowed[key] if key == "PC-2" else 0
        if npc:
            print(f"  {m:<10} {e:>8,} {100*e/npc:>7.1f}%")
    print()
    print(f"  PC-2 recovers {stats['pc_beats_1step']:,} edges that 1-step misses")
    if npc:
        gap = exact['PC-2'] - exact['1-step'] * npc / n if n else 0
        print(f"  -> the honest logical baseline is PC-2, not 1-step")

    print()
    print("  " + "=" * 68)
    print("  DIAGNOSTIC -- why the containment test must not be quoted as recovery")
    print("  " + "=" * 68)
    c, cd, ca = stats["contained"], stats["contained_decided"], stats["contained_ambiguous"]
    if n:
        print(f"  containment succeeds       {c:>6,}  {100*c/n:>5.1f}%")
        print(f"    of which truly decided   {cd:>6,}  {100*cd/n:>5.1f}%   <- the real rate")
        print(f"    of which still ambiguous {ca:>6,}  {100*ca/n:>5.1f}%")
    if ambig:
        print()
        print("  the ambiguous residue, by (gold label -> labels still compatible):")
        for (rel_, adm), k in ambig.most_common(6):
            print(f"    {rel_:<13} -> {list(adm)}   {k:,}")
        top = ambig.most_common(1)[0]
        if ca:
            print(f"  {100*top[1]/ca:.0f}% of the inflation is the single case "
                  f"{top[0][0]} vs {[x for x in top[0][1] if x != top[0][0]]}.")

    if residual_examples:
        print()
        print("RESIDUAL — not recovered even by PC-2 (the population rules must address):")
        for e in residual_examples:
            print(f"  {e['trig_a']} -{e['rel']}-> {e['trig_b']}   ({e['doc'][:12]})")
            print(f"     1-step narrows to {e['one_step']}")
            print(f"     PC-2   narrows to {e['pc']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
