"""Restate the mined rule family as falsifiable constraints and measure it on clean gold.

A rule "pattern P predicts relation R" is a prediction. A constraint is the negation:
"a pair matching P must not carry a relation in the FORBIDDEN set". The difference matters
because the gold corpus is internally consistent -- 0 pairs with two labels, 0 BEFORE in
both directions, 0 PC-inconsistent documents -- so every constraint violation on gold is
either an annotation error or a rule error, with no third possibility. The violation rate
therefore measures specificity directly, with no human judging required. That makes this
the cleanest measurement available in the project.

A relation is forbidden under P when its Wilson UPPER bound on train is below tau. The
upper bound is the right tail here: a prediction asks "how high can this proportion be",
a prohibition asks "how low can we be sure it stays".

Usage:
    python constraints.py --tau 0.01
    python constraints.py --sweep
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from mine_compositional import (
    candidate_conditions, iter_instances, fmt_rule, mine, wilson_lower,
)

GRAPH = Path(__file__).resolve().parent / "graph"
ROOT = Path(__file__).resolve().parent.parent
RELATIONS = ("BEFORE", "CONTAINS", "OVERLAP", "SIMULTANEOUS", "BEGINS-ON", "ENDS-ON")


def wilson_upper(k: int, n: int, z: float = 1.96) -> float:
    """Upper end of the Wilson interval. A relation may be forbidden only when even the
    optimistic end of its plausible range is negligible."""
    if n == 0:
        return 1.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return min(1.0, (c + m) / d)


def rule_distributions(path: Path, rules, use_weak: bool):
    """Full relation distribution of every rule on the mining split."""
    by_cond = defaultdict(list)
    for r in rules:
        by_cond[r[0]].append(r)

    dist = defaultdict(Counter)
    for feats, rel, _ in iter_instances(path, use_weak):
        conds = set(candidate_conditions(feats))
        for c in conds:
            for r in by_cond.get(c, ()):
                if all(x in conds for x in r):
                    dist[r][rel] += 1
    return dist


def build_constraints(dist, tau: float, sup_min: int):
    """rule -> (allowed, forbidden, support). Forbidden when Wilson-UB < tau."""
    out = {}
    for rule, cnt in dist.items():
        n = sum(cnt.values())
        if n < sup_min:
            continue
        forbidden, allowed = set(), set()
        for rel in RELATIONS:
            if wilson_upper(cnt.get(rel, 0), n) < tau:
                forbidden.add(rel)
            else:
                allowed.add(rel)
        if forbidden and allowed:
            out[rule] = (frozenset(allowed), frozenset(forbidden), n, dict(cnt))
    return out


def iter_pairs(path: Path, use_weak: bool):
    """Like iter_instances but also yields the document and endpoint ids, so a violation
    can be traced back to the source text."""
    from mine_compositional import pair_features

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
                yield rec["doc_id"], a, b, na, nb, feats, rel


def measure(path: Path, cons, use_weak: bool, want_examples: int = 10):
    by_cond = defaultdict(list)
    for r in cons:
        by_cond[r[0]].append(r)

    total = violated = 0
    by_rel = Counter()
    by_rule = Counter()
    by_doc = Counter()
    examples = []

    for doc_id, a, b, na, nb, feats, rel in iter_pairs(path, use_weak):
        total += 1
        conds = set(candidate_conditions(feats))
        hits = []
        for c in conds:
            for r in by_cond.get(c, ()):
                if all(x in conds for x in r):
                    hits.append(r)
        if not hits:
            continue
        bad = [r for r in hits if rel in cons[r][1]]
        if not bad:
            continue
        violated += 1
        by_rel[rel] += 1
        by_doc[doc_id] += 1
        # attribute to the most specific violated rule
        bad.sort(key=lambda r: (-len(r), -cons[r][2]))
        top = bad[0]
        by_rule[top] += 1
        if len(examples) < want_examples:
            allowed, forbidden, n, cnt = cons[top]
            examples.append({
                "doc": doc_id, "a": a, "b": b,
                "trig_a": na.get("trigger"), "trig_b": nb.get("trigger"),
                "type_a": na.get("type"), "type_b": nb.get("type"),
                "sent_a": na.get("sent_first"), "sent_b": nb.get("sent_first"),
                "gold": rel, "rule": fmt_rule(top),
                "allowed": sorted(allowed), "train_dist": cnt, "train_n": n,
            })

    return {"total": total, "violated": violated, "by_rel": by_rel,
            "by_rule": by_rule, "by_doc": by_doc, "examples": examples}


def load_sentences(doc_ids: set) -> dict:
    """Pull the raw sentences of the named documents from MAVEN-ERE train."""
    out = {}
    for split in ("train", "valid"):
        p = ROOT / "MAVEN_ERE" / f"{split}.jsonl"
        if not p.exists():
            continue
        with p.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                d = json.loads(line)
                if d["id"] in doc_ids:
                    out[d["id"]] = d.get("sentences") or []
                    if len(out) == len(doc_ids):
                        return out
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--beam", type=int, default=250)
    ap.add_argument("--sup-min", type=int, default=25)
    ap.add_argument("--lift-min", type=float, default=2.0)
    ap.add_argument("--tau", type=float, default=0.01)
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--examples", type=int, default=10)
    args = ap.parse_args()

    use_weak = False  # SUBEVENT/CONTAINS coincide 87% of the time; weak layer is leakage

    print("=" * 74)
    print("STEP 1 -- mine the rule family on train")
    print("=" * 74)
    rules, base, n = mine(GRAPH / "train.jsonl", args.depth, args.beam,
                          args.sup_min, args.lift_min, use_weak)

    print()
    print("=" * 74)
    print("STEP 2 -- full relation distribution per rule, on train")
    print("=" * 74)
    dist = rule_distributions(GRAPH / "train.jsonl", list(rules), use_weak)
    print(f"  distributions for {len(dist):,} rules")

    taus = [0.001, 0.005, 0.01, 0.02, 0.05] if args.sweep else [args.tau]

    print()
    print("=" * 74)
    print("STEP 3 -- constraints, and the violation rate on CLEAN GOLD")
    print("=" * 74)
    print("Every violation is a candidate annotation error OR a rule error. Gold has 0")
    print("internal contradictions, so a high rate means the rules are wrong.")
    print()

    last = None
    for tau in taus:
        cons = build_constraints(dist, tau, args.sup_min)
        if not cons:
            print(f"tau={tau}: no constraint has both a forbidden and an allowed relation")
            continue
        tr = measure(GRAPH / "train.jsonl", cons, use_weak, args.examples)
        va = measure(GRAPH / "valid.jsonl", cons, use_weak, args.examples)
        print(f"tau={tau:<6} constraints={len(cons):<6} "
              f"train {tr['violated']:>6,}/{tr['total']:,} = {100*tr['violated']/tr['total']:.3f}%   "
              f"valid {va['violated']:>6,}/{va['total']:,} = {100*va['violated']/va['total']:.3f}%")
        last = (tau, cons, tr, va)

    if not last:
        return 1
    tau, cons, tr, va = last

    print()
    print("=" * 74)
    print(f"DETAIL at tau={tau}")
    print("=" * 74)
    print(f"constraints: {len(cons):,}")
    print(f"train violations: {tr['violated']:,} over {len(tr['by_doc']):,} documents")
    print(f"valid violations: {va['violated']:,} over {len(va['by_doc']):,} documents")
    print()
    print("violations by gold relation (train):")
    for rel, k in tr["by_rel"].most_common():
        print(f"   {rel:14s} {k:7,}")

    print()
    print("TRIVIAL BASELINE: flag every pair whose label is not BEFORE")
    nb = sum(v for r, v in Counter(
        rel for *_, rel in iter_pairs(GRAPH / "valid.jsonl", use_weak)).items()
        if r != "BEFORE")
    print(f"   that flags {nb:,} of {va['total']:,} valid pairs = {100*nb/va['total']:.2f}%")
    print(f"   the constraint family flags {va['violated']:,} = {100*va['violated']/va['total']:.3f}%")
    if va["violated"]:
        print(f"   the family is {nb/va['violated']:.1f}x more selective")

    print()
    print("TOP VIOLATED CONSTRAINTS (train):")
    for rule, k in tr["by_rule"].most_common(10):
        allowed, forbidden, n, cnt = cons[rule]
        print(f"   {k:5,} violations | train n={n:5,} dist={cnt}")
        print(f"         {fmt_rule(rule)}")
        print(f"         allowed={sorted(allowed)}")

    print()
    print("=" * 74)
    print(f"HAND INSPECTION -- {len(tr['examples'])} violations with source text")
    print("=" * 74)
    sents = load_sentences({e["doc"] for e in tr["examples"]})
    for i, e in enumerate(tr["examples"], 1):
        print()
        print(f"--- {i} --- doc {e['doc'][:16]}")
        print(f"  rule:     {e['rule']}")
        print(f"  train:    n={e['train_n']} dist={e['train_dist']}  allowed={e['allowed']}")
        print(f"  gold:     {e['gold']}   <-- forbidden by the rule")
        print(f"  event A:  {e['type_a']:24s} trigger '{e['trig_a']}'  sent {e['sent_a']}")
        print(f"  event B:  {e['type_b']:24s} trigger '{e['trig_b']}'  sent {e['sent_b']}")
        ss = sents.get(e["doc"]) or []
        for lbl, si in (("A", e["sent_a"]), ("B", e["sent_b"])):
            if si is not None and 0 <= si < len(ss):
                txt = ss[si]
                print(f"  text {lbl}:   {txt[:300]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
