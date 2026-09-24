"""Mine rules per SUBGRAPH (view) instead of over the whole corpus at once.

FORMAL.md section 3: a set of attributes A induces a view V_A that partitions the events
into signature classes, and each class is its own subgraph to mine. PaTeCon's refinement
is search upward in this lattice. The previous miner searched conjunctions over one flat
pool, which is not the same thing: a conjunction adds a condition to a rule, a view
changes the population the rule's statistics are computed against.

That difference matters when the base rate varies across the partition. BEFORE is 91%
corpus-wide, but inside the same-sentence view it is 79%, so a rule that looks unremarkable
globally can be strongly enriched locally, and vice versa. Mining per view makes the
comparison local.

Selection policy is Wilson lower bound, not lift. Measured on valid: ranking matched rules
by lift gives 2.76% accuracy, by Wilson lower bound 7.96% -- lift promotes rules with tiny
support (n=5 at lift 39x is noise), and the lower bound is what penalises that.

Usage:
    python mine_views.py                       # all views, compare
    python mine_views.py --views sdist,order   # a subset
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from mine_compositional import (
    candidate_conditions, pair_features, fmt_rule, wilson_lower,
)

GRAPH = Path(__file__).resolve().parent / "graph"
RELATIONS = ("BEFORE", "CONTAINS", "OVERLAP", "SIMULTANEOUS", "BEGINS-ON", "ENDS-ON")


# Each view maps an instance to a signature. Mining then runs independently inside every
# signature class, so support, base rate and enrichment are all local to that subgraph.
VIEWS = {
    "global":     lambda f: "*",
    "sdist":      lambda f: f["s"]["sdist"],
    "order":      lambda f: f["s"]["order"],
    "anchor":     lambda f: f["s"]["shares_anchor"],
    "bucket_a":   lambda f: f["s"]["bucket_a"],
    "etype_a":    lambda f: f["s"]["type_a"],
    "sdist_ord":  lambda f: (f["s"]["sdist"], f["s"]["order"]),
    "anchor_sd":  lambda f: (f["s"]["shares_anchor"], f["s"]["sdist"]),
}


def load(path: Path):
    """(features, conditions, relation) for every labelled event-event pair."""
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            nodes = rec["nodes"]
            anchor_roles = defaultdict(set)
            for p in rec["anchored_pairs"]:
                for ra, rb in p["roles"]:
                    anchor_roles[(p["a"], p["b"])].add((ra, rb))
            for e in rec["target_edges"]:
                a, b = e["s"], e["t"]
                na, nb = nodes.get(a), nodes.get(b)
                if not na or not nb or na["kind"] != "event" or nb["kind"] != "event":
                    continue
                shared = anchor_roles.get((a, b)) or anchor_roles.get((b, a)) or set()
                f = pair_features(na, nb, shared, bool(shared), frozenset())
                out.append((f, frozenset(candidate_conditions(f)), e["rel"]))
    return out


def mine_view(data, view_fn, sup_min: int, lift_min: float, depth: int, beam: int):
    """Mine independently inside every signature class of one view.

    Returns rule -> (wlb, lift, relation, k, n, signature).
    """
    groups = defaultdict(list)
    for i, (f, _, _) in enumerate(data):
        groups[view_fn(f)].append(i)

    rules = {}
    for sig, idx in groups.items():
        if len(idx) < sup_min * 2:
            continue
        # base rate LOCAL to this subgraph -- the whole point of mining per view
        base = Counter(data[i][2] for i in idx)
        tot = len(idx)

        posting = defaultdict(list)
        for i in idx:
            for c in data[i][1]:
                posting[c].append(i)
        level1 = [c for c, v in posting.items() if len(v) >= sup_min]

        def score(members):
            n = len(members)
            if n < sup_min:
                return None
            cnt = Counter(data[i][2] for i in members)
            best = None
            for rel, k in cnt.items():
                if k < 5:
                    continue
                exp = base[rel] / tot
                if exp <= 0:
                    continue
                lift = (k / n) / exp
                if lift < lift_min:
                    continue
                cand = (wilson_lower(k, n), lift, rel, k, n, sig)
                if best is None or cand > best:
                    best = cand
            return best

        for c in level1:
            s = score(posting[c])
            if s:
                rules[(c,)] = s

        if depth < 2:
            continue
        top = sorted(level1, key=lambda c: -len(posting[c]))[:beam]
        sets = {c: set(posting[c]) for c in top}
        for i in range(len(top)):
            for j in range(i + 1, len(top)):
                a, b = top[i], top[j]
                if a[1] == b[1]:
                    continue
                inter = sets[a] & sets[b]
                if len(inter) < sup_min:
                    continue
                s = score(list(inter))
                if s:
                    key = tuple(sorted((a, b)))
                    if key not in rules or s > rules[key]:
                        rules[key] = s
    return rules


def evaluate(rules, data, view_fn):
    """Apply a view's rules, selecting by Wilson lower bound.

    A rule only applies inside the signature class it was mined in -- that is what makes
    this a view and not just another conjunction.
    """
    by_cond = defaultdict(list)
    for r, s in rules.items():
        by_cond[r[0]].append((r, s))

    matched = correct = oracle = 0
    fired = Counter()
    hit_gold = Counter()

    for f, conds, rel in data:
        sig = view_fn(f)
        hits = []
        for c in conds:
            for r, s in by_cond.get(c, ()):
                if s[5] != sig:
                    continue
                if all(x in conds for x in r):
                    hits.append((r, s))
        if not hits:
            continue
        matched += 1
        hit_gold[rel] += 1
        if any(s[2] == rel for _, s in hits):
            oracle += 1
        hits.sort(key=lambda rs: -rs[1][0])          # Wilson lower bound
        pred = hits[0][1][2]
        fired[pred] += 1
        if pred == rel:
            correct += 1

    return {"matched": matched, "correct": correct, "oracle": oracle,
            "fired": fired, "hit_gold": hit_gold}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--views", default="")
    ap.add_argument("--sup-min", type=int, default=25)
    ap.add_argument("--lift-min", type=float, default=1.5)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--beam", type=int, default=220)
    args = ap.parse_args()

    names = [v.strip() for v in args.views.split(",") if v.strip()] or list(VIEWS)

    print("loading train ...")
    tr = load(GRAPH / "train.jsonl")
    print(f"  {len(tr):,} labelled event-event pairs")
    print("loading valid ...")
    va = load(GRAPH / "valid.jsonl")
    print(f"  {len(va):,} pairs")

    gold = Counter(rel for _, _, rel in va)
    n_va = len(va)
    print()
    print("valid base: " + str({k: f"{100*v/n_va:.2f}%" for k, v in gold.most_common(3)}))
    print()

    hdr = f"{'view':<12} {'rules':>7} {'matched':>9} {'cover':>7} {'prec':>8} {'oracle':>8} {'const':>8}"
    print(hdr)
    print("-" * len(hdr))

    results = {}
    for name in names:
        fn = VIEWS[name]
        rules = mine_view(tr, fn, args.sup_min, args.lift_min, args.depth, args.beam)
        ev = evaluate(rules, va, fn)
        m = ev["matched"]
        if not m:
            print(f"{name:<12} {len(rules):>7,}      no match")
            continue
        best_const = ev["hit_gold"].most_common(1)[0]
        results[name] = (rules, ev)
        print(f"{name:<12} {len(rules):>7,} {m:>9,} {100*m/n_va:>6.1f}% "
              f"{100*ev['correct']/m:>7.2f}% {100*ev['oracle']/m:>7.2f}% "
              f"{100*best_const[1]/m:>7.2f}%")

    # union of all views, still selecting by Wilson lower bound
    print()
    print("UNION of all views (Wilson LB across views):")
    allrules = {}
    for name, (rules, _) in results.items():
        for r, s in rules.items():
            key = (name,) + r
            allrules[key] = s
    by_cond = defaultdict(list)
    for key, s in allrules.items():
        by_cond[key[1]].append((key, s))

    matched = correct = oracle = 0
    hit_gold = Counter()
    per_view = Counter()
    for f, conds, rel in va:
        sigs = {name: VIEWS[name](f) for name in results}
        hits = []
        for c in conds:
            for key, s in by_cond.get(c, ()):
                if sigs.get(key[0]) != s[5]:
                    continue
                if all(x in conds for x in key[1:]):
                    hits.append((key, s))
        if not hits:
            continue
        matched += 1
        hit_gold[rel] += 1
        if any(s[2] == rel for _, s in hits):
            oracle += 1
        hits.sort(key=lambda rs: -rs[1][0])
        key, s = hits[0]
        per_view[key[0]] += 1
        if s[2] == rel:
            correct += 1

    if matched:
        bc = hit_gold.most_common(1)[0]
        print(f"  rules {len(allrules):,}  matched {matched:,} ({100*matched/n_va:.1f}%)")
        print(f"  precision {correct:,}/{matched:,} = {100*correct/matched:.2f}%")
        print(f"  oracle    {oracle:,}/{matched:,} = {100*oracle/matched:.2f}%")
        print(f"  constant '{bc[0]}' {100*bc[1]/matched:.2f}%")
        print(f"  winning view: {dict(per_view.most_common())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
