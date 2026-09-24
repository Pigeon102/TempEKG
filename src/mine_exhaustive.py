"""Exhaustive depth-2 mining, plus the three extensions the current language cannot express.

WHY THIS EXISTS. The beam miner explores 220*1808 + 220^2 = 446,160 candidates out of
C(1808,3) = 983,383,856 depth-3 conjunctions -- **0.045%** of the space. So "we found all the
rules" is not a claim it can support. Depth-2 is a different matter: C(1808,2) = 1,633,528
candidates is tractable, so this file enumerates ALL of them and the claim becomes checkable.

FOURTH FACT, AND THE ONE THAT CHANGES THE SCALE. The 1,143 conditions with support >= 25
are NOT 1,143 independent booleans. They group into **19 multi-valued variables** whose
values are mutually exclusive: type_a=Attack and type_a=Killing can never both hold. Counting
conjunctions as C(n,k) therefore counts mostly impossible candidates:

    depth 2   C(1143,2) = 652,653      valid = 577,650        -11.5%
    depth 3   C(1143,3) = 248,225,691  valid =  14,072,484    -94.3%

So depth-3 is 14 million candidates, not the 10^9 an earlier estimate claimed -- that estimate
treated the conditions as independent. **Exhaustive depth-3 is therefore feasible**, which
makes "we found every rule" a checkable statement at depth 3 too, not just depth 2.

This is the decision-diagram insight applied correctly. A BDD would need 1,143 boolean
variables plus mutual-exclusion constraints; an MDD over 19 multi-valued variables encodes
the same space directly, with one node per variable and one edge per value. What a diagram
does NOT give us is the scoring: wlb is a statistic, not a predicate, so no diagram can
answer "which pattern correlates with the label" -- it can only enumerate the legal domain
efficiently. Coverage stays a bitset: at 90.7% distinct condition-sets there is too little
sharing for a ZDD to compress, and intersection over 483k-bit integers is already fast.

THREE ALGEBRAIC FACTS MAKE IT CHEAP (see report/RULE_ALGEBRA.md):

  1. Support is anti-monotone: phi subset psi => cov(psi) subset cov(phi). A conjunction
     below sup_min can never be rescued by extension, so whole branches die at once.

  2. Wilson has a support ceiling: wlb(k,n) <= wlb(n,n) = 1/(1 + z^2/n). At n=25 no rule can
     exceed 0.867; at n=10, 0.723. A target wlb therefore implies a minimum support, and
     everything below it is prunable WITHOUT LOSING ANY RULE. The beam miner never used this.

  3. Coverage-identical conjunctions are indistinguishable on this data whatever their
     syntax, so they collapse to one representative.

WHAT IS NEW BEYOND EXHAUSTIVENESS:

  NEGATION      The existing language is entirely positive -- there is no NOT(sdist=0). With
                six heavily skewed labels a negative condition can carry more than a positive
                one: "not same sentence AND no shared anchor => BEFORE" is unstateable today.

  RELATIONAL    Features describe a, describe b, or describe the pair, but never COMPARE the
                two events: type_a == type_b, |sent_a - sent_b| <= 2, roleset_a superset of
                roleset_b. Computable from data already loaded.

  MARGINAL GAIN A conjunction is kept only when it beats every sub-conjunction by a margin:
                wlb(phi) > max over psi subset phi of wlb(psi) + eps. Measured motivation:
                `Attack AND sdist=0` scores 59.42% on valid against 59.29% for `sdist=0`
                alone -- +0.13 points, i.e. the event type contributes nothing and the rule
                is `sdist=0` wearing a disguise. `Competition AND sdist=0` is actually WORSE
                (-1.05). Without this test both look like discoveries.

Usage:
    python mine_exhaustive.py --limit 400 --sup-min 25 --target-wlb 0.30
    python mine_exhaustive.py --limit 400 --no-negation --no-relational   # ablation
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from mine_compositional import candidate_conditions, pair_features

HERE = Path(__file__).resolve().parent
GRAPH = HERE / "graph"

RELATIONS = ("BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON")
Z = 1.96


def wilson_lower(k: int, n: int, z: float = Z) -> float:
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z * z / n
    return (p + z * z / (2 * n) - z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / d


def min_support_for(target_wlb: float, z: float = Z) -> int:
    """Smallest n whose best case wlb(n,n) = 1/(1+z^2/n) can still reach target_wlb.

    Fact 2 in the header. Everything below this support is prunable without loss.
    """
    if target_wlb <= 0:
        return 1
    if target_wlb >= 1:
        return 10 ** 9
    return max(1, math.ceil(z * z * target_wlb / (1 - target_wlb)))


def relational_conditions(na, nb, shared):
    """Conditions that COMPARE the two events. None of these exist in the current language."""
    out = []
    ta, tb = na.get("type"), nb.get("type")
    out.append(("REL", "same_type", ta == tb))

    sa, sb = na.get("sent_first", 0), nb.get("sent_first", 0)
    out.append(("REL", "sent_gap", "0" if sa == sb else ("1" if abs(sa - sb) == 1 else
                                                         ("2-3" if abs(sa - sb) <= 3 else "4+"))))
    out.append(("REL", "a_before_b", sa < sb if sa != sb
                else na.get("tok_first", 0) < nb.get("tok_first", 0)))

    ma, mb = na.get("n_mentions", 1), nb.get("n_mentions", 1)
    out.append(("REL", "mention_cmp", "a>b" if ma > mb else ("a<b" if ma < mb else "eq")))

    ra = frozenset(na.get("roleset") or ())
    rb = frozenset(nb.get("roleset") or ())
    if ra or rb:
        out.append(("REL", "role_overlap", bool(ra & rb)))
        out.append(("REL", "role_subset", bool(ra) and ra <= rb))
        out.append(("REL", "role_equal", ra == rb))
    out.append(("REL", "n_shared_anchor", "0" if not shared else
                ("1" if len(shared) == 1 else "2+")))
    return out


def load(path: Path, limit: int, relational: bool):
    rows = []
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if limit and i >= limit:
                break
            if not line.strip():
                continue
            rec = json.loads(line)
            nodes = rec["nodes"]
            anchors = defaultdict(set)
            for p in rec["anchored_pairs"]:
                for ra, rb in p["roles"]:
                    anchors[(p["a"], p["b"])].add((ra, rb))
            for e in rec["target_edges"]:
                a, b = e["s"], e["t"]
                na, nb = nodes.get(a), nodes.get(b)
                if not na or not nb or na["kind"] != "event" or nb["kind"] != "event":
                    continue
                shared = anchors.get((a, b)) or anchors.get((b, a)) or set()
                f = pair_features(na, nb, shared, bool(shared), frozenset())
                cs = list(candidate_conditions(f))
                if relational:
                    cs += relational_conditions(na, nb, shared)
                rows.append((e["rel"], frozenset(cs)))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--sup-min", type=int, default=25)
    ap.add_argument("--target-wlb", type=float, default=0.30)
    ap.add_argument("--min-k", type=int, default=5)
    ap.add_argument("--eps", type=float, default=0.02,
                    help="a conjunction must beat its best sub-conjunction by this margin")
    ap.add_argument("--no-negation", action="store_true")
    ap.add_argument("--no-relational", action="store_true")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--allow-majority", action="store_true",
                    help="keep rules predicting BEFORE; off by default because at a 91%% "
                         "base rate they restate the prior (measured: lift ~1.07x)")
    args = ap.parse_args()

    tr = load(GRAPH / "train.jsonl", args.limit, not args.no_relational)
    va = load(GRAPH / "valid.jsonl", 0, not args.no_relational)
    n_tr = len(tr)
    base = Counter(r for r, _ in tr)
    print(f"train {n_tr:,} pairs   valid {len(va):,}")

    # Support floor implied by the target wlb -- prunes without losing any rule (fact 2).
    floor = max(args.sup_min, min_support_for(args.target_wlb))
    print(f"  target wlb {args.target_wlb} => support floor {floor} "
          f"(wlb(n,n) = 1/(1+z^2/n) can't reach it below that)")

    post = defaultdict(list)
    for i, (_, cs) in enumerate(tr):
        for c in cs:
            post[c].append(i)
    lvl1 = [c for c, v in post.items() if len(v) >= floor]
    print(f"  conditions {len(post):,}  with support >= {floor}: {len(lvl1):,}")

    # NEGATION: every surviving condition also gives its complement. cov(NOT c) is the
    # complement of cov(c), so support is free -- no extra pass over the data.
    neg = {}
    if not args.no_negation:
        allidx = set(range(n_tr))
        for c in lvl1:
            comp = allidx - set(post[c])
            if len(comp) >= floor:
                neg[("NOT",) + (c,)] = comp
        print(f"  negated conditions with support >= {floor}: {len(neg):,}")

    universe = {c: set(post[c]) for c in lvl1}
    universe.update(neg)
    keys = sorted(universe, key=lambda c: -len(universe[c]))
    print(f"  universe {len(keys):,} => C(n,2) = {len(keys)*(len(keys)-1)//2:,} pairs\n")

    # Group EQ conditions by attribute. Two values of one attribute are mutually exclusive,
    # so their conjunction has empty coverage and must never be generated. This is what
    # turns depth-3 from 248M candidates into 14M.
    attr_of = {}
    for c in keys:
        if isinstance(c, tuple) and len(c) == 3 and c[0] == "EQ":
            attr_of[c] = c[1]
    print(f"  {len(set(attr_of.values()))} multi-valued variables covering "
          f"{len(attr_of):,} conditions; {len(keys)-len(attr_of):,} independent")
    print("  same-attribute pairs are impossible and are skipped")

    lab = [r for r, _ in tr]

    def score(members):
        n = len(members)
        if n < floor:
            return None
        cnt = Counter(lab[i] for i in members)
        best = None
        for rel, k in cnt.items():
            if k < args.min_k:
                continue
            if rel == "BEFORE" and not args.allow_majority:
                continue     # restates the 91% prior; measured lift ~1.07x, useless
            exp = base[rel] / n_tr
            if exp <= 0:
                continue
            w = wilson_lower(k, n)
            cand = (w, (k / n) / exp, rel, k, n)
            if best is None or cand > best:
                best = cand
        return best

    single = {}
    for c in keys:
        s = score(universe[c])
        if s:
            single[c] = s

    # Exhaustive depth 2. Anti-monotonicity (fact 1) lets us skip a whole row once the
    # intersection cannot reach the floor.
    pairs = {}
    examined = pruned = 0
    for i, ci in enumerate(keys):
        si = universe[ci]
        if len(si) < floor:
            continue
        for cj in keys[i + 1:]:
            sj = universe[cj]
            if len(sj) < floor:
                break                      # keys sorted by support: the rest are smaller
            # mutual exclusion: two values of one attribute never co-occur
            if ci in attr_of and cj in attr_of and attr_of[ci] == attr_of[cj]:
                continue
            examined += 1
            inter = si & sj
            if len(inter) < floor:
                pruned += 1
                continue
            s = score(inter)
            if s:
                pairs[(ci, cj)] = s

    print(f"depth-2: examined {examined:,}, pruned by support {pruned:,} "
          f"({100*pruned/max(1,examined):.1f}%), scored {len(pairs):,}")

    # MARGINAL GAIN: keep a conjunction only if it beats both its parts by eps.
    kept = {}
    dropped_flat = 0
    for (ci, cj), s in pairs.items():
        parent = max(single.get(ci, (0,))[0], single.get(cj, (0,))[0])
        if s[0] > parent + args.eps:
            kept[(ci, cj)] = (s, parent)
        else:
            dropped_flat += 1
    print(f"  marginal-gain test (eps={args.eps}): kept {len(kept):,}, "
          f"dropped {dropped_flat:,} that add nothing over their best half\n")

    # hold out
    cnt_va = Counter()
    hit_va = defaultdict(Counter)
    for rel, cs in va:
        for c in cs:
            cnt_va[c] += 1
            hit_va[c][rel] += 1
    nv = len(va)
    bva = Counter(r for r, _ in va)

    def valid_stats(conj, rel):
        """Recompute coverage on valid; negation needs the complement, so scan."""
        k = n = 0
        for r, cs in va:
            ok = True
            for c in conj:
                if isinstance(c, tuple) and c and c[0] == "NOT":
                    if c[1] in cs:
                        ok = False
                        break
                elif c not in cs:
                    ok = False
                    break
            if ok:
                n += 1
                if r == rel:
                    k += 1
        return k, n

    ranked = sorted(kept.items(), key=lambda kv: -kv[1][0][0])
    print(f"  {'wlb':>6}{'gain':>7}{'k':>7}{'n':>8}  {'rel':<13}"
          f"{'VALID p':>9}{'v-lift':>7}  conjunction")
    print("  " + "-" * 108)
    surv = 0
    shown = 0
    for (ci, cj), (s, parent) in ranked:
        w, lift, rel, k, n = s
        kv, nv2 = valid_stats((ci, cj), rel)
        pv = kv / nv2 if nv2 else 0.0
        lv = pv / (bva[rel] / nv) if nv2 and bva[rel] else 0.0
        if lv >= 1.5 and nv2 >= 10:
            surv += 1
        if shown < args.top:
            shown += 1

            def fmt(c):
                if isinstance(c, tuple) and c and c[0] == "NOT":
                    inner = c[1]
                    return "NOT " + (f"{inner[1]}={inner[2]}" if inner[0] == "EQ"
                                     else f"{inner[0]}({inner[1]},{inner[2]})")
                if c[0] == "REL":
                    return f"REL:{c[1]}={c[2]}"
                return f"{c[1]}={c[2]}" if c[0] == "EQ" else f"{c[0]}({c[1]},{c[2]})"

            print(f"  {w:>6.3f}{w-parent:>7.3f}{k:>7,}{n:>8,}  {rel:<13}"
                  f"{100*pv:>8.2f}%{lv:>7.2f}  {fmt(ci)[:40]} AND {fmt(cj)[:40]}")
    print()
    print(f"  giu duoc lift>=1.5 tren valid: {surv:,} / {len(kept):,} "
          f"({100*surv/max(1,len(kept)):.1f}%)")

    nneg = sum(1 for (a, b) in kept
               if (isinstance(a, tuple) and a and a[0] == "NOT")
               or (isinstance(b, tuple) and b and b[0] == "NOT"))
    nrel = sum(1 for (a, b) in kept if a[0] == "REL" or b[0] == "REL")
    print(f"  trong do co phu dinh : {nneg:,}")
    print(f"  trong do co quan he  : {nrel:,}")
    print()
    print("  Depth-2 o day la VET CAN: moi hoi hai dieu kien deu duoc xet, nen 'tim het'")
    print("  la phat bieu kiem chung duoc -- khac han beam search o depth-3 (0,045%).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
