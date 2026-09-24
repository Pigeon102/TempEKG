"""Compositional rule mining over event-pair features, per FORMAL.md section 5.

The earlier miner (mine_triangles.py) implemented only the EQ condition form on a handful
of axes. FORMAL.md section 5.1 specifies five forms over three tiers, and section 5.2
measured compositional patterns at 4.85x hold-out lift against 3.63x for single conditions.
This implements the full language so that a weak result is a fact about the data rather
than about the miner.

Condition forms:
    EQ(attr, v)      attr == v                       scalar attributes
    HAS(attr, v)     v in attr                       set-valued attributes
    ALL(attr, v)     attr is non-empty and == {v}    set-valued
    CNT(attr, k)     |attr| >= k                     set-valued or counts
    MIX(attr)        |attr| >= 2                     set-valued; heterogeneity

Search: beam over conjunctions up to depth 3, scored by the Wilson lower bound of the
per-relation enrichment. Raw confidence is useless here -- the base rate is 91% BEFORE --
so ranking is by lift with a Wilson floor, and a binomial tail with Benjamini-Hochberg
control decides significance.

Two mandatory guards from FORMAL.md section 6:
  - STRATIFY: candidate rules are scored within strata so no rule can win by a mechanical
    artifact of the stratifying variable.
  - FORBIDDEN FEATURES (6.1): any feature computable from the quantities that define the
    label is refused by name, with the reason recorded.

Usage:
    python mine_compositional.py --depth 3 --beam 400
    python mine_compositional.py --depth 1          # ablation: single conditions only
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAPH = Path(__file__).resolve().parent / "graph"

RELATIONS = ("BEFORE", "CONTAINS", "OVERLAP", "SIMULTANEOUS", "BEGINS-ON", "ENDS-ON")

# FORMAL.md 6.1. A feature computable from the quantities defining the label must never
# enter the pattern language. Recorded by name so the exclusion is auditable rather than
# a matter of the author remembering.
FORBIDDEN = {
    "rel": "is the label",
    "gold": "is the label",
    "allen": "is the label under another name",
    "n_temporal_edges": "counted from the target layer",
    "temporal_degree": "counted from the target layer",
    "hull": "FORMAL.md 6.1: hull>0 <=> conflict at k=2, gave a fake 11.16x lift",
}


def wilson_lower(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - m) / d)


def log_binom_tail(k: int, n: int, p: float) -> float:
    """log10 of P(X >= k) for X ~ Binomial(n, p). Normal approximation with continuity
    correction; adequate for ranking at the supports used here (>= 25)."""
    if k <= 0 or p <= 0 or p >= 1:
        return 0.0
    mu = n * p
    if k <= mu:
        return 0.0
    sd = math.sqrt(n * p * (1 - p))
    if sd == 0:
        return -99.0
    z = (k - 0.5 - mu) / sd
    # log10 of the upper normal tail
    if z > 8:
        return -(z * z / 2) / math.log(10) - math.log10(z * math.sqrt(2 * math.pi))
    return math.log10(max(1e-300, 0.5 * math.erfc(z / math.sqrt(2))))


# --------------------------------------------------------------------------- features

def sd_bucket(d) -> str:
    if d is None:
        return "unk"
    if d == 0:
        return "0"
    if d == 1:
        return "1"
    if d <= 3:
        return "2-3"
    if d <= 7:
        return "4-7"
    return "8+"


def pair_features(na: dict, nb: dict, shared_roles, shares_anchor: bool,
                  weak_kinds: frozenset) -> dict:
    """Every feature of an event pair, all computed without reading that pair's label.

    Scalars go under 's', set-valued attributes under 'm'. The miner generates EQ over
    the first and HAS / ALL / CNT / MIX over the second.
    """
    sa, sb = na.get("sent_first"), nb.get("sent_first")
    if sa is None or sb is None:
        order, dist = "unk", None
    else:
        order = "fwd" if sa < sb else ("same" if sa == sb else "rev")
        dist = abs(sa - sb)

    scal = {
        "type_a": na.get("type"),
        "type_b": nb.get("type"),
        "type_pair": (na.get("type"), nb.get("type")),
        "same_type": na.get("type") == nb.get("type"),
        "order": order,
        "sdist": sd_bucket(dist),
        "bucket_a": na.get("sent_bucket"),
        "bucket_b": nb.get("sent_bucket"),
        "nrole_a": min(na.get("n_role", 0), 5),
        "nrole_b": min(nb.get("n_role", 0), 5),
        "shares_anchor": shares_anchor,
        "multi_mention_a": na.get("n_mentions", 1) > 1,
        "multi_mention_b": nb.get("n_mentions", 1) > 1,
        "has_person_a": na.get("has_person", False),
        "has_person_b": nb.get("has_person", False),
        "has_org_a": na.get("has_org", False),
        "has_org_b": nb.get("has_org", False),
        "has_loc_a": na.get("has_loc", False),
        "has_loc_b": nb.get("has_loc", False),
        # weak-layer edges between the two events. These are NOT independent evidence
        # (95.2% of PRECONDITION pairs already carry a temporal label), so they are kept
        # separable: --no-weak drops them and the difference is reported.
        "weak": tuple(sorted(weak_kinds)) if weak_kinds else None,
    }

    multi = {
        "roleset_a": frozenset(na.get("roleset") or ()),
        "roleset_b": frozenset(nb.get("roleset") or ()),
        "etypeset_a": frozenset(na.get("etypeset") or ()),
        "etypeset_b": frozenset(nb.get("etypeset") or ()),
        "roleset_shared": frozenset(na.get("roleset") or ()) & frozenset(nb.get("roleset") or ()),
        "etypeset_shared": frozenset(na.get("etypeset") or ()) & frozenset(nb.get("etypeset") or ()),
        "anchor_roles": frozenset(shared_roles),
    }
    return {"s": scal, "m": multi}


def iter_instances(path: Path, use_weak: bool = True):
    """Yield (features, relation, stratum) for every labelled event-event pair."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            nodes = rec["nodes"]

            anchor_roles = defaultdict(set)
            for p in rec["anchored_pairs"]:
                key = (p["a"], p["b"])
                for ra, rb in p["roles"]:
                    anchor_roles[key].add((ra, rb))

            weak = defaultdict(set)
            if use_weak:
                for e in rec["weak_edges"]:
                    weak[(e["s"], e["t"])].add(e["kind"])

            for e in rec["target_edges"]:
                a, b, rel = e["s"], e["t"], e["rel"]
                na, nb = nodes.get(a), nodes.get(b)
                if not na or not nb or na["kind"] != "event" or nb["kind"] != "event":
                    continue
                shared = anchor_roles.get((a, b)) or anchor_roles.get((b, a)) or set()
                wk = frozenset(weak.get((a, b), set()) | weak.get((b, a), set()))
                feats = pair_features(na, nb, shared, bool(shared), wk)
                # FORMAL.md 6: stratify so a rule cannot win on an artifact of the
                # stratifying variable. Sentence distance is the strongest such variable
                # here (same-sentence pairs are 27x more likely to be SIMULTANEOUS).
                stratum = feats["s"]["sdist"]
                yield feats, rel, stratum


# --------------------------------------------------------------------------- conditions

def candidate_conditions(feats: dict):
    """All atomic conditions this instance satisfies, as hashable keys."""
    out = []
    for attr, val in feats["s"].items():
        if attr in FORBIDDEN:
            continue
        if val is None:
            continue
        out.append(("EQ", attr, val))
    for attr, vals in feats["m"].items():
        if attr in FORBIDDEN:
            continue
        n = len(vals)
        if n == 0:
            out.append(("CNT", attr, 0))
            continue
        for v in vals:
            out.append(("HAS", attr, v))
        if n == 1:
            out.append(("ALL", attr, next(iter(vals))))
        if n >= 2:
            out.append(("MIX", attr, None))
        for k in (1, 2, 3):
            if n >= k:
                out.append(("CNT", attr, k))
    return out


def fmt_cond(c) -> str:
    form, attr, v = c
    if form == "MIX":
        return f"MIX({attr})"
    if form == "CNT":
        return f"CNT({attr}>={v})"
    return f"{form}({attr}={v})"


def fmt_rule(conds) -> str:
    return " AND ".join(fmt_cond(c) for c in conds)


# --------------------------------------------------------------------------- mining

def mine(path: Path, depth: int, beam: int, sup_min: int, lift_min: float,
         use_weak: bool, verbose: bool = True):
    print(f"loading instances from {path.name} ...")
    data = []
    base = Counter()
    strata = Counter()
    for feats, rel, stratum in iter_instances(path, use_weak):
        data.append((candidate_conditions(feats), rel, stratum))
        base[rel] += 1
        strata[stratum] += 1
    n = len(data)
    print(f"  {n:,} labelled event-event pairs")
    print(f"  base: " + str({k: f"{100*v/n:.2f}%" for k, v in base.most_common()}))
    print(f"  strata: " + str(dict(strata.most_common())))

    # index: condition -> list of instance indices
    posting = defaultdict(list)
    for i, (conds, _, _) in enumerate(data):
        for c in conds:
            posting[c].append(i)
    print(f"  {len(posting):,} distinct atomic conditions")

    level1 = [c for c, idx in posting.items() if len(idx) >= sup_min]
    print(f"  {len(level1):,} conditions clear support >= {sup_min}")

    # per-stratum base rates, so enrichment is measured against the right denominator
    stratum_base = defaultdict(Counter)
    for _, rel, st in data:
        stratum_base[st][rel] += 1

    def score(idx):
        """Best (relation, lift, wlb, logp) for a candidate rule's instance set,
        computed against a stratum-weighted expectation."""
        sup = len(idx)
        if sup < sup_min:
            return None
        cnt = Counter()
        st_cnt = Counter()
        for i in idx:
            cnt[data[i][1]] += 1
            st_cnt[data[i][2]] += 1
        best = None
        for rel, k in cnt.items():
            if k < 5:
                return_early = False
                continue
            # expected count under the stratum mix of THIS rule, not the global base
            exp = 0.0
            for st, m in st_cnt.items():
                tot_st = sum(stratum_base[st].values())
                exp += m * (stratum_base[st][rel] / tot_st if tot_st else 0.0)
            if exp <= 0:
                continue
            lift = k / exp
            if lift < lift_min:
                continue
            wlb = wilson_lower(k, sup)
            logp = log_binom_tail(k, sup, exp / sup)
            cand = (wlb, lift, rel, k, sup, logp)
            if best is None or cand > best:
                best = cand
        return best

    results = {}
    frontier = []
    for c in level1:
        idx = posting[c]
        s = score(idx)
        if s:
            rule = (c,)
            results[rule] = s
        frontier.append((c, idx))

    # keep only the most promising single conditions as beam seeds
    frontier.sort(key=lambda ci: -len(ci[1]))
    frontier = frontier[:beam]
    print(f"  depth 1: {len(results):,} rules; beam carries {len(frontier)} conditions")

    current = [((c,), set(idx)) for c, idx in frontier]
    for d in range(2, depth + 1):
        nxt = []
        seen = set()
        for rule, idx in current:
            last = rule[-1]
            for c, cidx in frontier:
                if c <= last:            # canonical order; avoids permutations
                    continue
                if c[1] == last[1]:      # same attribute twice adds nothing useful
                    continue
                new = idx.intersection(cidx)
                if len(new) < sup_min:
                    continue
                nr = rule + (c,)
                key = frozenset(nr)
                if key in seen:
                    continue
                seen.add(key)
                s = score(list(new))
                if s:
                    results[nr] = s
                nxt.append((nr, new))
        nxt.sort(key=lambda ri: -results.get(ri[0], (0,))[0])
        current = nxt[:beam]
        print(f"  depth {d}: {len(results):,} rules cumulative; "
              f"{len(nxt):,} candidates, beam keeps {len(current)}")
        if not current:
            break

    # Benjamini-Hochberg over the whole rule set
    items = sorted(results.items(), key=lambda kv: kv[1][5])
    m = len(items)
    kept = {}
    for rank, (rule, s) in enumerate(items, 1):
        if s[5] <= math.log10(0.05 * rank / m) if m else False:
            kept[rule] = s
    print(f"  BH-FDR at 0.05 keeps {len(kept):,} of {m:,}")
    return kept or results, base, n


# --------------------------------------------------------------------------- evaluation

def evaluate(rules: dict, path: Path, use_weak: bool):
    """Apply the family to a held-out split whose labels are hidden until scoring."""
    # index rules by their conditions for fast matching
    by_cond = defaultdict(list)
    for rule, s in rules.items():
        by_cond[rule[0]].append((rule, s))

    matched = 0
    fired = Counter()
    correct = Counter()
    matched_gold = Counter()
    oracle = 0
    total = 0
    per_rule = defaultdict(lambda: [0, 0])

    for feats, rel, _ in iter_instances(path, use_weak):
        total += 1
        conds = set(candidate_conditions(feats))
        hits = []
        for c in conds:
            for rule, s in by_cond.get(c, ()):
                if all(x in conds for x in rule):
                    hits.append((rule, s))
        if not hits:
            continue
        matched += 1
        matched_gold[rel] += 1
        if any(s[2] == rel for _, s in hits):
            oracle += 1
        # most specific wins, then highest Wilson lower bound
        hits.sort(key=lambda rs: (-len(rs[0]), -rs[1][0]))
        rule, s = hits[0]
        fired[s[2]] += 1
        per_rule[rule][1] += 1
        if s[2] == rel:
            correct[s[2]] += 1
            per_rule[rule][0] += 1

    return {"total": total, "matched": matched, "fired": fired, "correct": correct,
            "matched_gold": matched_gold, "oracle": oracle, "per_rule": per_rule}


def report(rules: dict, ev: dict, train_base: Counter, train_n: int):
    tot_f = sum(ev["fired"].values())
    tot_c = sum(ev["correct"].values())
    mg = ev["matched_gold"]
    m_tot = sum(mg.values())

    print()
    print("=" * 74)
    print("HELD-OUT EVALUATION (valid labels hidden during mining and matching)")
    print("=" * 74)
    print(f"rules in family                {len(rules):,}")
    print(f"valid instances                {ev['total']:,}")
    print(f"matched by >=1 rule            {ev['matched']:,} = {100*ev['matched']/ev['total']:.1f}%")
    if not tot_f:
        print("no rule fired")
        return
    print(f"precision of fired rules       {tot_c:,}/{tot_f:,} = {100*tot_c/tot_f:.2f}%")
    print()
    print(f"  {'rel':14s} {'fired':>8s} {'correct':>8s} {'prec':>8s} {'base':>8s} {'lift':>7s}")
    for rel in sorted(ev["fired"], key=lambda r: -ev["fired"][r]):
        f, c = ev["fired"][rel], ev["correct"][rel]
        b = mg[rel] / m_tot if m_tot else 0
        p = c / f if f else 0
        print(f"  {rel:14s} {f:8,} {c:8,} {100*p:7.2f}% {100*b:7.2f}% "
              f"{p/b if b else 0:6.2f}x")

    print()
    print("baselines on the SAME matched instances:")
    for rel, k in mg.most_common(3):
        print(f"  constant {rel:14s} {k:,}/{m_tot:,} = {100*k/m_tot:.2f}%")
    print(f"  ORACLE (any rule right)      {ev['oracle']:,}/{m_tot:,} = {100*ev['oracle']/m_tot:.2f}%")
    print(f"  >>> our family               {tot_c:,}/{tot_f:,} = {100*tot_c/tot_f:.2f}%")

    best_const = mg.most_common(1)[0]
    fam = tot_c / tot_f
    print()
    if fam > best_const[1] / m_tot:
        print(f"  FAMILY BEATS the best constant ({best_const[0]}) "
              f"by {100*(fam - best_const[1]/m_tot):.2f} points")
    else:
        print(f"  family LOSES to constant {best_const[0]} "
              f"by {100*(best_const[1]/m_tot - fam):.2f} points")
    if m_tot:
        print(f"  family reaches {100*fam/(ev['oracle']/m_tot):.1f}% of the in-class oracle ceiling")

    surv = [(r, c, f) for r, (c, f) in ev["per_rule"].items() if f >= 5]
    good = [x for x in surv if x[1] / x[2] >= 0.5]
    print()
    print(f"rules firing >=5 times on valid: {len(surv):,}; with precision >=0.50: {len(good):,}")

    print()
    print("TOP 15 RULES by held-out precision (>=10 firings):")
    strong = sorted([(c / f, f, r) for r, (c, f) in ev["per_rule"].items() if f >= 10],
                    reverse=True)
    for p, f, r in strong[:15]:
        s = rules[r]
        print(f"  prec {100*p:5.1f}%  n={f:4d}  train lift {s[1]:5.2f}x  -> {s[2]:13s}  {fmt_rule(r)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--graph-dir", type=Path, default=GRAPH)
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--beam", type=int, default=400)
    ap.add_argument("--sup-min", type=int, default=25)
    ap.add_argument("--lift-min", type=float, default=2.0)
    ap.add_argument("--no-weak", action="store_true",
                    help="drop causal/subevent features (they are not independent evidence)")
    args = ap.parse_args()

    use_weak = not args.no_weak
    print(f"forbidden features refused: {sorted(FORBIDDEN)}")
    print(f"weak-layer features: {'ON' if use_weak else 'OFF'}")
    print()

    rules, base, n = mine(args.graph_dir / "train.jsonl", args.depth, args.beam,
                          args.sup_min, args.lift_min, use_weak)
    ev = evaluate(rules, args.graph_dir / "valid.jsonl", use_weak)
    report(rules, ev, base, n)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
