"""Reduce the mined rule set to a small set of general pattern families.

155,456 rules mined across eight views is not a result anyone can read, and most of it is
redundant: the same statement re-derived inside several views, and hundreds of sibling
rules that differ only in which event type they name. This collapses that set along three
axes, keeping only what survives held-out evaluation.

  1. DEDUPE     identical (conditions, predicted relation) across views.
  2. SUBSUME    drop a rule whose conditions are a superset of a kept rule that predicts
                the same relation and is at least as reliable -- the extra conditions buy
                nothing, so the shorter rule is the general one.
  3. ABSTRACT   collapse siblings that differ only in a type literal into one family keyed
                by the shared skeleton. A family is kept only if it holds up when the
                literal is dropped, i.e. the abstract version is itself a valid rule.

Then build forbidden-set constraints from the surviving families and measure them on clean
gold, where every violation is either an annotation error or a rule error.

Selection is by Wilson lower bound throughout: ranking matched rules by lift scores 2.76%
on valid, by Wilson lower bound 7.96%.

Usage:
    python generalise.py
    python generalise.py --tau 0.005 --min-family 3
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from mine_compositional import (
    candidate_conditions, pair_features, fmt_cond, wilson_lower,
)
from mine_views import VIEWS, load, mine_view

GRAPH = Path(__file__).resolve().parent / "graph"
RELATIONS = ("BEFORE", "CONTAINS", "OVERLAP", "SIMULTANEOUS", "BEGINS-ON", "ENDS-ON")

# Attributes whose value is a bare type literal. A rule naming one of these is a specific
# instance; the family is what remains when the literal is replaced by a wildcard.
TYPE_ATTRS = frozenset({"type_a", "type_b", "type_pair"})

# The corpus-wide majority relation. A rule predicting it restates the prior rather than
# adding information, and inside a subgraph with a locally low base rate such a rule can
# pass a lift threshold and then dominate once the rule set is applied corpus-wide.
MAJORITY = "BEFORE"


def wilson_upper(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 1.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return min(1.0, (c + m) / d)


def skeleton(rule):
    """The rule with every type literal replaced by a wildcard, as a hashable key."""
    out = []
    for form, attr, val in rule:
        out.append((form, attr, "*") if attr in TYPE_ATTRS else (form, attr, val))
    return tuple(sorted(out))


def fmt_rule_short(rule) -> str:
    return " AND ".join(fmt_cond(c) for c in rule)


def fmt_family(skel) -> str:
    parts = []
    for form, attr, val in skel:
        parts.append(f"{form}({attr}=*)" if val == "*" else fmt_cond((form, attr, val)))
    return " AND ".join(parts)


def dedupe(all_rules):
    """Collapse the same (conditions, relation) mined in several views.

    Keeps the instance with the highest Wilson lower bound, and records how many views
    independently found it -- a statement several views agree on is more trustworthy.
    """
    best = {}
    seen_in = Counter()
    for (view, *conds), s in all_rules.items():
        # the signature is part of the rule's identity: a rule mined inside the
        # same-sentence subgraph makes no claim about pairs eight sentences apart
        key = (tuple(sorted(conds)), s[2], view, s[5])
        seen_in[key] += 1
        if key not in best or s[0] > best[key][1][0]:
            best[key] = (view, s)
    return {k: (v[0], v[1], seen_in[k]) for k, v in best.items()}


def subsume(rules):
    """Drop a rule whose conditions strictly contain a kept rule's, same relation,
    when the kept rule is at least as reliable. The survivor is the general statement."""
    by_rel = defaultdict(list)
    for (conds, rel, view, sig), payload in rules.items():
        if rel == MAJORITY:
            continue          # restates the prior; see MAJORITY
        by_rel[(rel, view, sig)].append((frozenset(conds), conds, payload))
    kept = {}
    for (rel, view, sig), items in by_rel.items():
        items.sort(key=lambda t: (len(t[0]), -t[2][1][0]))   # shortest first, then best
        survivors = []
        for fs, conds, payload in items:
            dominated = False
            for kfs, _, kp in survivors:
                if kfs < fs and kp[1][0] >= payload[1][0] - 1e-9:
                    dominated = True
                    break
            if not dominated:
                survivors.append((fs, conds, payload))
        for _, conds, payload in survivors:
            kept[(conds, rel, view, sig)] = payload
    return kept


def abstract(rules, data, min_family: int, sup_min: int, lift_min: float):
    """Group siblings by skeleton, then test whether the abstract version holds.

    A family earns its name only if the rule with the type literal removed is itself
    supported by the data; otherwise the members are genuinely type-specific and are kept
    as they are.
    """
    fams = defaultdict(list)
    for (conds, rel, view, sig), payload in rules.items():
        fams[(skeleton(conds), rel, view, sig)].append((conds, payload))

    base = Counter(rel for _, _, rel in data)
    tot = len(data)

    generalised, kept_specific = {}, {}
    view_fns = {}
    for (skel, rel, view, sig), members in fams.items():
        keep_all = lambda: [kept_specific.__setitem__((c, rel, view, sig), p)
                            for c, p in members]
        if len(members) < min_family:
            keep_all()
            continue

        # the abstract rule is the skeleton with type conditions dropped entirely
        abs_conds = tuple(c for c in skel if c[2] != "*")
        if not abs_conds:
            keep_all()
            continue

        # the abstract rule must hold inside the SAME subgraph it was mined in
        fn = VIEWS[view]
        idx = [i for i, (f, cs, _) in enumerate(data)
               if fn(f) == sig and all(c in cs for c in abs_conds)]
        n = len(idx)
        if n < sup_min:
            keep_all()
            continue
        k = sum(1 for i in idx if data[i][2] == rel)
        if k < 5:
            keep_all()
            continue
        loc = Counter(data[i][2] for i in idx if True)
        sub = [i for i, (f, _, _) in enumerate(data) if fn(f) == sig]
        sub_base = Counter(data[i][2] for i in sub)
        exp = sub_base[rel] / len(sub) if sub else 0
        if exp <= 0:
            keep_all()
            continue
        lift = (k / n) / exp
        wlb = wilson_lower(k, n)
        if lift >= lift_min:
            generalised[(abs_conds, rel, view, sig)] = {
                "wlb": wlb, "lift": lift, "k": k, "n": n,
                "members": len(members),
                "types": [next((v for f, a, v in c if a in TYPE_ATTRS), None)
                          for c, _ in members][:8],
            }
        else:
            keep_all()
    return generalised, kept_specific


def evaluate_flat(rules, data):
    """Apply a rule set, selecting by Wilson lower bound.

    A rule fires only inside the view signature it was mined in. Dropping that guard
    applies subgraph-local statistics corpus-wide and inflates precision badly.
    """
    by_cond = defaultdict(list)
    for key, payload in rules.items():
        conds, rel, view, sig = key
        wlb = payload["wlb"] if isinstance(payload, dict) else payload[1][0]
        by_cond[conds[0]].append((conds, rel, wlb, view, sig))

    matched = correct = oracle = 0
    gold = Counter()
    sig_cache = {}
    for f, cs, rel in data:
        hits = []
        for c in cs:
            for conds, prel, wlb, view, sig in by_cond.get(c, ()):
                if view not in sig_cache:
                    sig_cache[view] = VIEWS[view](f)
                if sig_cache[view] != sig:
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


def constraints_from(rules, data, tau: float, sup_min: int):
    """Forbidden sets: a relation is forbidden under P when its Wilson UPPER bound < tau.

    Keyed by (conditions, view, signature) so a constraint stays scoped to the subgraph
    whose statistics justify it.
    """
    by_cond = defaultdict(list)
    for key in rules:
        conds, _, view, sig = key
        by_cond[conds[0]].append((conds, view, sig))
    uniq = {(conds, view, sig) for conds, _, view, sig in rules}

    dist = defaultdict(Counter)
    sig_cache = {}
    for f, cs, rel in data:
        for c in cs:
            for conds, view, sig in by_cond.get(c, ()):
                if view not in sig_cache:
                    sig_cache[view] = VIEWS[view](f)
                if sig_cache[view] != sig:
                    continue
                if all(x in cs for x in conds):
                    dist[(conds, view, sig)][rel] += 1
        sig_cache.clear()

    cons = {}
    for key in uniq:
        cnt = dist.get(key)
        if not cnt:
            continue
        n = sum(cnt.values())
        if n < sup_min:
            continue
        forbidden = {r for r in RELATIONS if wilson_upper(cnt.get(r, 0), n) < tau}
        allowed = set(RELATIONS) - forbidden
        if forbidden and allowed:
            cons[key] = (allowed, forbidden, n, dict(cnt))
    return cons


def apply_constraints(cons, data):
    by_cond = defaultdict(list)
    for key in cons:
        by_cond[key[0][0]].append(key)
    total = viol = 0
    by_rel = Counter()
    sig_cache = {}
    for f, cs, rel in data:
        total += 1
        hit = False
        for c in cs:
            for key in by_cond.get(c, ()):
                conds, view, sig = key
                if view not in sig_cache:
                    sig_cache[view] = VIEWS[view](f)
                if sig_cache[view] != sig:
                    continue
                if all(x in cs for x in conds) and rel in cons[key][1]:
                    viol += 1
                    by_rel[rel] += 1
                    hit = True
                    break
            if hit:
                break
        sig_cache.clear()
    return {"total": total, "viol": viol, "by_rel": by_rel}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sup-min", type=int, default=25)
    ap.add_argument("--lift-min", type=float, default=1.5)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--beam", type=int, default=220)
    ap.add_argument("--min-family", type=int, default=3)
    ap.add_argument("--tau", type=float, default=0.001)
    args = ap.parse_args()

    print("loading ...", flush=True)
    tr = load(GRAPH / "train.jsonl")
    va = load(GRAPH / "valid.jsonl")
    print(f"  train {len(tr):,}  valid {len(va):,}", flush=True)

    print("\nmining all views ...", flush=True)
    allr = {}
    for name, fn in VIEWS.items():
        r = mine_view(tr, fn, args.sup_min, args.lift_min, args.depth, args.beam)
        for rule, s in r.items():
            allr[(name,) + rule] = s
        print(f"  {name:<12} {len(r):>7,}", flush=True)
    print(f"  TOTAL        {len(allr):>7,}")

    print("\nREDUCTION", flush=True)
    print(f"  0. mined across views        {len(allr):>8,}")
    d = dedupe(allr)
    print(f"  1. after dedupe              {len(d):>8,}")
    s = subsume(d)
    print(f"  2. after subsumption         {len(s):>8,}")
    gen, spec = abstract(s, tr, args.min_family, args.sup_min, args.lift_min)
    print(f"  3. general families          {len(gen):>8,}")
    print(f"     type-specific kept        {len(spec):>8,}")

    merged = dict(gen)
    for k, v in spec.items():
        merged[k] = {"wlb": v[1][0], "lift": v[1][1], "k": v[1][2], "n": v[1][3],
                     "members": 1, "types": []}
    print(f"     (rules predicting {MAJORITY} were refused at the subsume stage)")
    print(f"     final rule set            {len(merged):>8,}")

    print("\nHELD-OUT (valid labels hidden)", flush=True)
    hdr = f"  {'rule set':<22} {'rules':>8} {'matched':>9} {'prec':>8} {'oracle':>8}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for label, rs in (("all mined (deduped)", {k: {"wlb": v[1][0]} for k, v in d.items()}),
                      ("after subsumption", {k: {"wlb": v[1][0]} for k, v in s.items()}),
                      ("general families", gen),
                      ("general + specific", merged)):
        ev = evaluate_flat(rs, va)
        m = ev["matched"]
        if not m:
            continue
        print(f"  {label:<22} {len(rs):>8,} {m:>9,} "
              f"{100*ev['correct']/m:>7.2f}% {100*ev['oracle']/m:>7.2f}%")
    bc = evaluate_flat(merged, va)["gold"].most_common(1)
    if bc:
        print(f"  {'constant ' + bc[0][0]:<22} {'-':>8} {'-':>9} "
              f"{100*bc[0][1]/evaluate_flat(merged, va)['matched']:>7.2f}%")

    print("\nTOP 15 GENERAL FAMILIES by Wilson LB", flush=True)
    top = sorted(gen.items(), key=lambda kv: -kv[1]["wlb"])[:15]
    for (conds, rel), m in top:
        types = ", ".join(str(t) for t in m["types"][:4] if t)
        print(f"  wlb {m['wlb']:.3f} lift {m['lift']:5.2f}x  n={m['n']:>6,} -> {rel:<13}"
              f" [{m['members']} biến thể] view={view}={sig}")
        print(f"      {fmt_rule_short(conds)}")
        if types:
            print(f"      gộp từ: {types[:90]}")

    print("\nCONSTRAINTS from the reduced set", flush=True)
    cons = constraints_from(merged, tr, args.tau, args.sup_min)
    ctr = apply_constraints(cons, tr)
    cva = apply_constraints(cons, va)
    print(f"  tau={args.tau}  constraints={len(cons):,}")
    print(f"  train violations {ctr['viol']:,}/{ctr['total']:,} = "
          f"{100*ctr['viol']/ctr['total']:.3f}%")
    print(f"  valid violations {cva['viol']:,}/{cva['total']:,} = "
          f"{100*cva['viol']/cva['total']:.3f}%")
    nb = sum(v for r, v in Counter(rel for _, _, rel in va).items() if r != "BEFORE")
    print(f"  trivial baseline (flag non-BEFORE): {nb:,} = {100*nb/len(va):.2f}%")
    if cva["viol"]:
        print(f"  -> {nb/cva['viol']:.0f}x more selective")
    print(f"  violations by gold relation: {dict(cva['by_rel'].most_common())}")

    out = Path(__file__).resolve().parent / "families.json"
    payload = [{"conds": [list(c) for c in conds], "rel": rel, "view": view, "sig": str(sig),
                **{k: v for k, v in m.items() if k != "types"}}
               for (conds, rel, view, sig), m in sorted(gen.items(),
                                                        key=lambda kv: -kv[1]["wlb"])]
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"\nwrote {out.name} ({len(payload)} families)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
