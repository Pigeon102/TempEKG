"""Noise-aware reasoning: rank suspicious edges, then repair the top-k.

WHY THIS FILE EXISTS. A proposed results table quoted 73.53% detection / 90.54% repair at 1%
noise and 74.16% repair at 30%, citing `patecon_maven/eval/noise_aware.py` -- a path that does
not exist anywhere on disk. This is that evaluation, written so the numbers can be checked.

It reports BOTH denominators, because the earlier table and an independent measurement
disagreed by 13x at 30% noise and the gap is almost certainly this:

    P@k       of the edges we FLAGGED, how many were really corrupted
    repair@k  of the flagged-and-corrupted edges, how many we restored correctly
    R_all     of ALL corrupted edges, how many we both found AND restored

P@k and repair@k condition on having flagged something, so they stay high while the method
quietly stops flagging. R_all is the one that falls, and it is the one a reader wants.

THE RANKING. Every unlabelled-after-hiding edge gets a suspicion score: hide it, run one-step
closure from the rest of the graph, and ask whether the label it carries is still compatible
with what closure implies. Three outcomes, scored differently:

    closure implies a set the carried label is NOT in   -> suspicion 1.0  (refutable)
    closure implies a set it IS in, but ambiguous       -> suspicion 0.0  (no evidence)
    closure learns nothing at all                       -> abstain, never ranked

Ranking then taking top-k beats flat flagging because the refutable cases come first.

THE REPAIR. For a flagged edge, propose the most frequent corpus label still compatible with
the implied Allen set -- the same rule that took C3-B from 1.8% to 89.3% (propose_missing.py).

WHAT THE NUMBERS ACTUALLY DO (measured here, not asserted): closure degrades by going SILENT,
not by going wrong. At 30% noise it abstains on ~94% of corrupted edges, so R_all collapses
while repair@k stays respectable. Report both or the method looks better than it is.

Usage:
    python noise_aware.py --rates 0.01,0.05,0.10,0.20,0.30 --limit 300
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL

HERE = Path(__file__).resolve().parent
GRAPH = HERE / "graph"

RELATIONS = ("BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON")
# Corpus frequency order, measured on train. A fixed prior, never fit to the eval set.
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


def corrupt(edges, rate, marginal, rng):
    """Relabel a fraction of edges, drawing replacements from the corpus marginal.

    Gold-marginal, not uniform: drawing uniformly from the five other labels puts 40% of
    corruptions on {BEGINS-ON, ENDS-ON}, which are together 0.09% of the corpus -- a 432x
    enrichment that lets a two-line baseline beat real methods as a sampler artifact.
    """
    out = []
    bad = {}
    for a, b, r in edges:
        if rng.random() < rate:
            others = [x for x in RELATIONS if x != r]
            new = rng.choices(others, weights=[marginal.get(x, 0.0) for x in others])[0]
            out.append((a, b, new))
            bad[(a, b)] = r
        else:
            out.append((a, b, r))
    return out, bad


def score_document(edges):
    """Suspicion score per edge, plus the repair closure would propose.

    Returns [(suspicion, a, b, carried_label, proposed_label_or_None)].
    Edges closure cannot speak to are omitted entirely -- abstention, not a low score.
    """
    adj = defaultdict(dict)
    for a, b, r in edges:
        aset = MAVEN_TO_ALLEN.get(r)
        if not aset:
            continue
        adj[a][b] = aset
        adj[b][a] = converse(aset)

    scored = []
    for a, b, r in edges:
        # hide this edge, then ask the rest of the graph what it should be
        held = defaultdict(dict)
        for x, d in adj.items():
            for y, v in d.items():
                if (x, y) in ((a, b), (b, a)):
                    continue
                held[x][y] = v
        imp = one_step(held, a, b)
        if imp == FULL or not imp:
            continue                      # closure has nothing to say -> abstain
        adm = compatible(imp)
        if not adm:
            continue                      # narrowed to an inverse MAVEN cannot express
        proposal = min(adm, key=FREQ_ORDER.index)
        suspicion = 0.0 if r in adm else 1.0
        scored.append((suspicion, a, b, r, proposal))
    return scored


def evaluate(docs, rate, marginal, seed, k_frac):
    rng = random.Random(seed)
    ranked = []
    n_bad = 0
    for edges in docs:
        cor, bad = corrupt(edges, rate, marginal, rng)
        n_bad += len(bad)
        for susp, a, b, carried, proposal in score_document(cor):
            ranked.append((susp, (a, b) in bad, bad.get((a, b)), proposal))

    ranked.sort(key=lambda t: -t[0])
    k = max(1, int(round(k_frac * n_bad))) if k_frac else len(ranked)
    top = ranked[:k]

    flagged_bad = sum(1 for _, is_bad, _, _ in top if is_bad)
    repaired = sum(1 for _, is_bad, orig, prop in top if is_bad and prop == orig)

    return {
        "n_bad": n_bad,
        "ranked": len(ranked),
        "k": len(top),
        "p_at_k": flagged_bad / len(top) if top else 0.0,
        "repair_at_k": repaired / flagged_bad if flagged_bad else 0.0,
        "r_all": repaired / n_bad if n_bad else 0.0,
        "found_all": flagged_bad / n_bad if n_bad else 0.0,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="train")
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--rates", default="0.01,0.05,0.10,0.20,0.30")
    ap.add_argument("--k-frac", type=float, default=3.0,
                    help="take k = k_frac x (number of corrupted edges); 0 = no cutoff")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    docs = []
    labels = Counter()
    with (GRAPH / f"{args.split}.jsonl").open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if args.limit and i >= args.limit:
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
    marginal = {r: labels[r] / total for r in RELATIONS}

    print("=" * 84)
    print(f"NOISE-AWARE REASONING   {len(docs):,} docs  {total:,} edges  "
          f"k = {args.k_frac}x |corrupted|")
    print("=" * 84)
    print(f"  {'noise':>6} {'corrupted':>10} {'ranked':>9} {'k':>8} "
          f"{'P@k':>8} {'repair@k':>10} {'found':>8} {'R_all':>8}")
    print("  " + "-" * 76)

    for rate in [float(x) for x in args.rates.split(",")]:
        r = evaluate(docs, rate, marginal, args.seed, args.k_frac)
        print(f"  {100*rate:>5.0f}% {r['n_bad']:>10,} {r['ranked']:>9,} {r['k']:>8,} "
              f"{100*r['p_at_k']:>7.2f}% {100*r['repair_at_k']:>9.2f}% "
              f"{100*r['found_all']:>7.2f}% {100*r['r_all']:>7.2f}%", flush=True)

    print()
    print("  P@k       of the edges FLAGGED, how many were really corrupted")
    print("  repair@k  of the flagged-and-corrupted, how many were restored correctly")
    print("  found     of ALL corrupted edges, how many were flagged at all")
    print("  R_all     of ALL corrupted edges, how many were found AND restored")
    print()
    print("  P@k and repair@k condition on having flagged something, so they hold up while")
    print("  the method quietly stops flagging. R_all is what falls, and it is the honest")
    print("  headline: closure degrades by going SILENT, not by going wrong.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
