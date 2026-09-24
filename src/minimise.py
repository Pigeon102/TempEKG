"""Find the smallest rule set that keeps coverage and precision.

The mined rule sets are far larger than anyone can read, and the held-out numbers say most
of that size is noise: 956 abstract families score 8.76% while the 124,037 rules they
replace score 8.55%. This finds the minimum set directly rather than by heuristic pruning.

REPRESENTATION. Number the atomic conditions 0..m-1. Each instance and each rule becomes a
bitset over instances, held in a Python int (arbitrary precision, so AND and popcount are
single operations on the whole corpus -- measured at 6.8 us for 110k bits). Then

    cov(P)            = the set of instances a rule matches
    cov(P u Q)        = cov(P) & cov(Q)
    P is redundant    = cov(P) == cov(Q) for some kept Q with the same relation
    Q is dominated    = cov(Q) & ~cov(P) == 0 and wlb(Q) <= wlb(P)
    families overlap  = popcount(cov(P) & cov(Q)) / popcount(cov(P) | cov(Q))   [Jaccard]

The distinction that matters: the earlier subsume() dropped a rule when its CONDITIONS were
a superset of another's, which is a syntactic test, and it cost 2.13 points of precision.
Coverage equality is the semantic test -- a rule is only redundant when it matches exactly
the same instances, in which case it genuinely adds nothing.

SELECTION. Greedy set cover weighted by correct predictions: repeatedly take the rule
adding the most newly-correct instances per rule spent, stopping when marginal gain falls
below a threshold. That directly optimises "cover enough, stay accurate, use as few rules
as possible" instead of approaching it through pruning.

Usage:
    python minimise.py
    python minimise.py --target-cover 0.90 --min-gain 20
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from mine_compositional import candidate_conditions, fmt_cond, wilson_lower
from mine_views import VIEWS, load, mine_view

HERE = Path(__file__).resolve().parent
GRAPH = HERE / "graph"
MAJORITY = "BEFORE"


def fmt_rule(conds) -> str:
    return " AND ".join(fmt_cond(c) for c in conds)


def build_bitsets(rules, data, wlb_of=None, wlb_floor=0.0):
    """rule -> (coverage bitset, correct bitset), as Python ints over instance indices.

    Two things make this feasible at 155k rules x 483k instances.

    First, rules are indexed by their RAREST condition, not their first. Indexing by the
    first condition puts most rules behind something 98% of instances satisfy, so the index
    does not filter and every instance walks nearly the whole rule set.

    Second, bits are accumulated in a bytearray and converted to an int once at the end.
    Doing `cov |= 1 << i` incrementally allocates a fresh bignum per set bit -- at 483k bits
    that copies 60 KB each time. Measured on one rule with 20k set bits: 0.083 s incremental
    versus 0.003 s via bytearray, a 31x difference, and the memory churn is what stalled an
    earlier run for over an hour with no output.

    wlb_floor prunes the pool before any of this: the Pareto sweep never examines rules
    below its lowest floor, so building their bitsets is pure waste.
    """
    df = Counter()
    for _, cs, _ in data:
        for c in cs:
            df[c] += 1

    keys = list(rules)
    if wlb_of is not None and wlb_floor > 0:
        keys = [k for k in keys if wlb_of(k) >= wlb_floor]

    by_rare = defaultdict(list)
    for key in keys:
        conds, rel, view, sig = key
        by_rare[min(conds, key=lambda c: df.get(c, 0))].append(key)

    nbytes = (len(data) + 7) // 8
    cov_buf = {k: bytearray(nbytes) for k in keys}
    cor_buf = {k: bytearray(nbytes) for k in keys}

    sig_cache = {}
    for i, (f, cs, rel) in enumerate(data):
        byte, mask = i >> 3, 1 << (i & 7)
        for c in cs:
            for key in by_rare.get(c, ()):
                conds, prel, view, ksig = key
                if view not in sig_cache:
                    sig_cache[view] = VIEWS[view](f)
                if sig_cache[view] != ksig:
                    continue
                if all(x in cs for x in conds):
                    cov_buf[key][byte] |= mask
                    if prel == rel:
                        cor_buf[key][byte] |= mask
        sig_cache.clear()

    cov, cor = {}, {}
    for k in keys:
        c = int.from_bytes(cov_buf[k], "little")
        if c:
            cov[k] = c
            cor[k] = int.from_bytes(cor_buf[k], "little")
    return cov, cor


def drop_coverage_duplicates(rules, cov, cor, wlb_of):
    """Keep one rule per distinct (coverage, relation). This is the honest redundancy
    test: same instances, same prediction, so the others add nothing."""
    best = {}
    for key in rules:
        c = cov.get(key, 0)
        if not c:
            continue
        sig = (c, key[1])
        if sig not in best or wlb_of(key) > wlb_of(best[sig]):
            best[sig] = key
    return list(best.values())


def greedy_cover(cands, cov, cor, n_inst, min_gain, target_cover, max_rules):
    """Lazy greedy (CELF) over marginal correct-predictions gained.

    Marginal gain is submodular -- covering more instances can only shrink what a later
    rule adds -- so a rule's gain never grows as selection proceeds. That licenses the
    lazy evaluation: keep the pool in a heap keyed by a stale gain, and only recompute the
    top entry. If it still leads after recomputation it is the true maximum. A naive
    rescan of 100k candidates per iteration costs hours at 34 us per popcount; this makes
    it minutes.

    Selection is by newly-CORRECT instances, not raw coverage: a rule covering a lot while
    predicting wrongly there is worth nothing.
    """
    import heapq

    chosen = []
    claimed = 0            # instances covered by some chosen rule
    correct = 0            # instances covered AND predicted right
    full = (1 << n_inst) - 1

    heap = []
    for key in cands:
        g = cor[key].bit_count()
        if g >= min_gain:
            heapq.heappush(heap, (-g, 0, key))    # (-gain, staleness, key)

    round_no = 0                                   # bumped once per rule SELECTED
    while heap and len(chosen) < max_rules:
        neg_g, stamp, key = heapq.heappop(heap)
        if stamp != round_no:
            # stale: recompute against the current claimed set, then re-insert unless it
            # still beats everything else in the heap
            remaining = full & ~claimed
            gain = (cor[key] & remaining).bit_count()
            if heap and gain < -heap[0][0]:
                heapq.heappush(heap, (-gain, round_no, key))
                continue
        else:
            gain = -neg_g
        if gain < min_gain:
            break
        round_no += 1
        chosen.append((key, gain))
        claimed |= cov[key]
        correct |= cor[key]
        if claimed.bit_count() / n_inst >= target_cover:
            break
    return chosen, claimed, correct


def structural_masks(data):
    """Bitsets for the architectural slices a rule set should be judged against.

    Aggregate coverage hides where the coverage falls. A set covering 90% of pairs but
    only BEFORE-labelled ones is useless for the audit, because the family emits no
    BEFORE by construction; a set firing in 500 of 2,913 documents cannot audit the KG.
    """
    masks = {"all": 0, "non_BEFORE": 0, "anchored": 0, "unanchored": 0}
    doc_of = []
    for i, (f, cs, rel) in enumerate(data):
        bit = 1 << i
        masks["all"] |= bit
        if rel != MAJORITY:
            masks["non_BEFORE"] |= bit
        if f["s"].get("shares_anchor"):
            masks["anchored"] |= bit
        else:
            masks["unanchored"] |= bit
    return masks


def slice_report(claimed: int, correct: int, masks: dict, label: str):
    rows = []
    for name, m in masks.items():
        tot = m.bit_count()
        if not tot:
            continue
        cov_n = (claimed & m).bit_count()
        cor_n = (correct & m).bit_count()
        rows.append((name, tot, cov_n, 100 * cov_n / tot,
                     100 * cor_n / cov_n if cov_n else 0.0))
    return rows


def jaccard(a: int, b: int) -> float:
    u = (a | b).bit_count()
    return (a & b).bit_count() / u if u else 0.0


def evaluate(keys, data):
    """Apply a rule set to held-out data, selecting by Wilson lower bound."""
    df = Counter()
    for _, cs, _ in data:
        for c in cs:
            df[c] += 1
    by_rare = defaultdict(list)
    for key, wlb in keys.items():
        conds, rel, view, sig = key
        by_rare[min(conds, key=lambda c: df.get(c, 0))].append((key, wlb))

    matched = correct = oracle = 0
    gold = Counter()
    sig_cache = {}
    for f, cs, rel in data:
        hits = []
        for c in cs:
            for key, wlb in by_rare.get(c, ()):
                conds, prel, view, ksig = key
                if view not in sig_cache:
                    sig_cache[view] = VIEWS[view](f)
                if sig_cache[view] != ksig:
                    continue
                if all(x in cs for x in conds):
                    hits.append((wlb, prel))
        sig_cache.clear()
        if not hits:
            continue
        matched += 1
        gold[rel] += 1
        if any(p == rel for _, p in hits):
            oracle += 1
        hits.sort(reverse=True)
        if hits[0][1] == rel:
            correct += 1
    return {"matched": matched, "correct": correct, "oracle": oracle, "gold": gold}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sup-min", type=int, default=25)
    ap.add_argument("--lift-min", type=float, default=1.5)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--beam", type=int, default=220)
    ap.add_argument("--min-gain", type=int, default=30)
    ap.add_argument("--target-cover", type=float, default=0.95)
    ap.add_argument("--max-rules", type=int, default=2000)
    ap.add_argument("--per-label", action="store_true",
                    help="run greedy once per relation and union the results. MEASURED: does "
                         "NOT help -- the monoculture is a data property, not an objective "
                         "bug. See PER-LABEL note in the module docstring.")
    ap.add_argument("--per-label-cap", type=int, default=40,
                    help="max rules to keep per relation in --per-label mode")
    ap.add_argument("--wlb-floor", type=float, default=0.2,
                    help="drop rules below this Wilson lower bound before building bitsets")
    args = ap.parse_args()

    import time
    t0 = time.time()
    print("loading ...", flush=True)
    tr = load(GRAPH / "train.jsonl")
    va = load(GRAPH / "valid.jsonl")
    print(f"  train {len(tr):,}  valid {len(va):,}  ({time.time()-t0:.0f}s)", flush=True)

    print("\nmining all views ...", flush=True)
    rules = {}
    for name, fn in VIEWS.items():
        r = mine_view(tr, fn, args.sup_min, args.lift_min, args.depth, args.beam)
        for rule, s in r.items():
            if s[2] == MAJORITY:
                continue            # restates the prior at a 91% base rate
            rules[(rule, s[2], name, s[5])] = s
        print(f"  {name:<12} {len(r):>7,}", flush=True)
    print(f"  after refusing {MAJORITY}: {len(rules):,}  ({time.time()-t0:.0f}s)", flush=True)

    wlb_of = lambda k: rules[k][0]

    # Prune before building: a bitset over 483,504 instances is ~60 KB, so the full
    # 155k rules would need 18.8 GB of bytearrays up front. The Pareto sweep never looks
    # below its lowest floor anyway, so those bitsets would be built and never read.
    # Measured pool sizes: wlb>=0.2 leaves 35,984 rules (4.3 GB), 0.3 leaves 20,831 (2.5 GB).
    print(f"\nbuilding bitsets (pruning to wlb >= {args.wlb_floor}) ...", flush=True)
    cov, cor = build_bitsets(rules, tr, wlb_of, args.wlb_floor)
    print(f"  {len(cov):,} rules with non-empty coverage  ({time.time()-t0:.0f}s)", flush=True)

    print("\nREDUCTION", flush=True)
    print(f"  0. mined (no {MAJORITY})          {len(rules):>8,}")
    uniq = drop_coverage_duplicates(rules, cov, cor, wlb_of)
    print(f"  1. distinct coverage          {len(uniq):>8,}")

    # order candidates by reliability so greedy ties resolve sensibly
    uniq.sort(key=lambda k: -wlb_of(k))

    n = len(tr)
    masks = structural_masks(tr)
    print(f"  structural slices: " +
          ", ".join(f"{k} {v.bit_count():,}" for k, v in masks.items()))

    # Coverage and precision trade off against each other: more rules reach further but
    # into harder territory. Rather than pick a point, sweep a reliability floor and let
    # the curve show the choice. A higher floor admits fewer, safer rules.
    print("\nPARETO SWEEP (train)", flush=True)
    hdr = (f"  {'wlb floor':>9} {'rules':>7} {'cover':>7} {'prec':>7} "
           f"{'nonBEF cov':>11} {'anch cov':>9} {'docs':>7}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    if args.per_label:
        # HYPOTHESIS (wrong, kept as a record): one pooled greedy maximises total correct
        # predictions and CONTAINS is 88.1% of the non-BEFORE mass, so rules predicting
        # SIMULTANEOUS or OVERLAP supposedly never win a round. Removing the competition
        # between labels should then recover them.
        #
        # MEASURED: it does not. The monoculture is a property of the DATA, not the
        # objective. Best Wilson lower bound by relation, over 1,453 mined families:
        #
        #     CONTAINS      1,033 rules   max wlb 0.598   43 at wlb >= 0.4
        #     SIMULTANEOUS    279 rules   max wlb 0.141    0 at wlb >= 0.4
        #     OVERLAP         141 rules   max wlb 0.125    0 at wlb >= 0.4
        #
        # Greedy picks CONTAINS because it is the only relation with trustworthy rules.
        # Forcing the other two in by dropping the floor to 0.10 gives 120 rules at 8.73%
        # precision against 35.25% for the 68-rule pooled set -- four times worse.
        #
        # The real headroom is elsewhere. Oracle over the same families, keeping the BEFORE
        # fallback, reaches macro-F1 65.85% (SIMULTANEOUS 99.53%) versus 22.57% achieved.
        # The right rules DO fire on the right instances; they fire alongside many wrong
        # ones and picking by max wlb picks wrong. That is a ranking problem, not a mining
        # or an objective problem.
        by_rel = defaultdict(list)
        for k in uniq:
            by_rel[k[1]].append(k)
        print("")
        print("PER-LABEL GREEDY (train)", flush=True)
        print(f"  {'relation':<15}{'pool':>8}{'chosen':>8}{'cover':>9}{'prec':>8}")
        print("  " + "-" * 46)
        merged = []
        for rel in sorted(by_rel, key=lambda r: -len(by_rel[r])):
            pool = [k for k in by_rel[rel] if wlb_of(k) >= args.wlb_floor]
            if not pool:
                continue
            ch, cl, co = greedy_cover(pool, cov, cor, n, 1, args.target_cover,
                                      args.per_label_cap)
            if not ch:
                continue
            pc = 100 * co.bit_count() / cl.bit_count() if cl else 0
            print(f"  {rel:<15}{len(pool):>8,}{len(ch):>8,}"
                  f"{100*cl.bit_count()/n:>8.2f}%{pc:>7.2f}%", flush=True)
            merged.extend(k for k, _ in ch)
        cl = co = 0
        for k in merged:
            cl |= cov[k]
        for k in merged:
            co |= cor[k]
        co &= cl
        print("")
        print(f"  union: {len(merged):,} rules  "
              f"cover {100*cl.bit_count()/n:.2f}%  "
              f"precision {100*co.bit_count()/cl.bit_count() if cl else 0:.2f}%")
        nb = masks["non_BEFORE"]
        print(f"  non-BEFORE coverage {100*(cl&nb).bit_count()/nb.bit_count():.1f}%")
        out = [{"rank": i + 1,
                "conds": [list(c) for c in k[0]],
                "rel": k[1], "view": k[2], "sig": k[3],
                "wlb": round(rules[k][0], 5), "lift": round(rules[k][1], 3),
                "n": rules[k][4]}
               for i, k in enumerate(merged)]
        dst = HERE / "minimal_rules_per_label.json"
        dst.write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(f"  wrote {dst.name}")
        return 0

    pareto = []
    for floor in [f for f in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7) if f >= args.wlb_floor]:
        pool = [k for k in uniq if wlb_of(k) >= floor]
        if not pool:
            continue
        ch, cl, co = greedy_cover(pool, cov, cor, n, args.min_gain,
                                  args.target_cover, args.max_rules)
        if not ch:
            continue
        cov_pct = 100 * cl.bit_count() / n
        prec = 100 * co.bit_count() / cl.bit_count() if cl else 0
        nb = masks["non_BEFORE"]
        nb_cov = 100 * (cl & nb).bit_count() / nb.bit_count()
        an = masks["anchored"]
        an_cov = 100 * (cl & an).bit_count() / an.bit_count()
        print(f"  {floor:>9.2f} {len(ch):>7,} {cov_pct:>6.1f}% {prec:>6.2f}% "
              f"{nb_cov:>10.1f}% {an_cov:>8.1f}% {'-':>7}", flush=True)
        pareto.append((floor, ch, cl, co))

    # pick the knee: highest precision among runs covering at least half the non-BEFORE mass
    viable = [p for p in pareto
              if (p[2] & masks["non_BEFORE"]).bit_count() >= 0.5 * masks["non_BEFORE"].bit_count()]
    best = max(viable or pareto,
               key=lambda p: (p[3].bit_count() / p[2].bit_count()) if p[2] else 0)
    floor, chosen, claimed, correct = best
    print(f"\n  chosen operating point: wlb floor {floor:.2f}, {len(chosen):,} rules")
    print(f"  ({time.time()-t0:.0f}s)", flush=True)

    print("\nCOVERAGE BY ARCHITECTURAL SLICE (train, chosen set)", flush=True)
    print(f"  {'slice':<14} {'instances':>10} {'covered':>10} {'cover%':>8} {'prec%':>8}")
    for name, tot, cov_n, cov_p, pr in slice_report(claimed, correct, masks, "chosen"):
        print(f"  {name:<14} {tot:>10,} {cov_n:>10,} {cov_p:>7.1f}% {pr:>7.2f}%")

    sets = {
        "all mined": {k: wlb_of(k) for k in rules},
        "distinct coverage": {k: wlb_of(k) for k in uniq},
        "greedy minimal": {k: wlb_of(k) for k, _ in chosen},
    }

    print("\nHELD-OUT (valid labels hidden)", flush=True)
    hdr = f"  {'rule set':<20} {'rules':>8} {'matched':>9} {'cover':>7} {'prec':>8} {'oracle':>8}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for label, rs in sets.items():
        ev = evaluate(rs, va)
        m = ev["matched"]
        if not m:
            print(f"  {label:<20} {len(rs):>8,}   no match")
            continue
        print(f"  {label:<20} {len(rs):>8,} {m:>9,} {100*m/len(va):>6.1f}% "
              f"{100*ev['correct']/m:>7.2f}% {100*ev['oracle']/m:>7.2f}%",
              flush=True)
        if label == "greedy minimal":
            bc = ev["gold"].most_common(1)[0]
            print(f"  {'constant ' + bc[0]:<20} {'-':>8} {'-':>9} {'-':>7} "
                  f"{100*bc[1]/m:>7.2f}%")

    print("\nREDUNDANCY AMONG CHOSEN RULES (Jaccard on coverage)", flush=True)
    ks = [k for k, _ in chosen[:60]]
    pairs = []
    for i in range(len(ks)):
        for j in range(i + 1, len(ks)):
            jv = jaccard(cov[ks[i]], cov[ks[j]])
            if jv > 0.5:
                pairs.append((jv, ks[i], ks[j]))
    pairs.sort(reverse=True)
    print(f"  pairs with Jaccard > 0.5 among top 60: {len(pairs)}")
    for jv, a, b in pairs[:5]:
        print(f"    {jv:.2f}  {fmt_rule(a[0])[:52]}")
        print(f"          {fmt_rule(b[0])[:52]}")

    print("\nTHE MINIMAL RULE SET", flush=True)
    for rank, (key, gain) in enumerate(chosen[:25], 1):
        conds, rel, view, sig = key
        s = rules[key]
        print(f"  {rank:>2}. +{gain:>5,} wlb {s[0]:.3f} lift {s[1]:5.2f}x n={s[4]:>6,}"
              f" -> {rel:<13} [{view}={sig}]")
        print(f"      {fmt_rule(conds)}")

    out = Path(__file__).resolve().parent / "minimal_rules.json"
    out.write_text(json.dumps([{
        "rank": i + 1, "conds": [list(c) for c in k[0]], "rel": k[1],
        "view": k[2], "sig": str(k[3]), "gain": g,
        "wlb": rules[k][0], "lift": rules[k][1], "n": rules[k][4],
    } for i, (k, g) in enumerate(chosen)], indent=1), encoding="utf-8")
    print(f"\nwrote {out.name} ({len(chosen)} rules)  total {time.time()-t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
