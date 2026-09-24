"""Mine once and write the rule set, the abstract families and the constraints to disk.

Everything produced so far lives only in run logs: the 956 families and the 1,730 constraints
cannot be reloaded, re-scored or cited without re-running a pipeline that takes over an hour.
This does the mining once and dumps three artifacts, so every later step reads a file instead
of recomputing.

    rules.json        every mined rule with its statistics, view and signature
    families.json     the abstract families (type literal replaced by a wildcard)
    constraints.json  forbidden-set form at several tau, the audit-ready artifact

No evaluation here on purpose. Scoring belongs downstream, where it can run in seconds
against these files.

Usage:
    python export_rules.py
    python export_rules.py --tau 0.001 0.005 0.01
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
ART = HERE / "artifacts"   # mined artifacts; see data/README.md
GRAPH = HERE / "graph"
RELATIONS = ("BEFORE", "CONTAINS", "OVERLAP", "SIMULTANEOUS", "BEGINS-ON", "ENDS-ON")

# A rule predicting the majority relation restates the prior: BEFORE is 91% of event-event
# pairs, so 1/0.91 = 1.10 never clears a lift threshold honestly. Inside a subgraph with a
# locally low base rate such a rule can slip through and then dominate corpus-wide -- that
# is the artifact that produced a fake 70.52% precision.
MAJORITY = "BEFORE"

# Attributes whose value is a bare type literal; a family is what remains without them.
TYPE_ATTRS = frozenset({"type_a", "type_b", "type_pair"})


def wilson_upper(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 1.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return min(1.0, (c + m) / d)


def fmt_rule(conds) -> str:
    return " AND ".join(fmt_cond(c) for c in conds)


def skeleton(conds):
    return tuple(sorted((f, a, "*") if a in TYPE_ATTRS else (f, a, v) for f, a, v in conds))


def rule_distributions(data, keyed):
    """Full relation distribution per rule, respecting each rule's view signature.

    Indexed by each rule's RAREST condition: indexing by the first condition puts most rules
    behind something 98% of instances satisfy, so the index does not filter.
    """
    df = Counter()
    for _, cs, _ in data:
        for c in cs:
            df[c] += 1

    by_rare = defaultdict(list)
    for key in keyed:
        conds, rel, view, sig = key
        by_rare[min(conds, key=lambda c: df.get(c, 0))].append(key)

    dist = defaultdict(Counter)
    sig_cache = {}
    for f, cs, rel in data:
        for c in cs:
            for key in by_rare.get(c, ()):
                conds, prel, view, ksig = key
                if view not in sig_cache:
                    sig_cache[view] = VIEWS[view](f)
                if sig_cache[view] != ksig:
                    continue
                if all(x in cs for x in conds):
                    dist[key][rel] += 1
        sig_cache.clear()
    return dist


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sup-min", type=int, default=25)
    ap.add_argument("--lift-min", type=float, default=1.5)
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--beam", type=int, default=220)
    ap.add_argument("--min-family", type=int, default=3)
    ap.add_argument("--tau", type=float, nargs="+", default=[0.001, 0.005, 0.01])
    args = ap.parse_args()

    import time
    t0 = time.time()
    print("loading train ...", flush=True)
    tr = load(GRAPH / "train.jsonl")
    print(f"  {len(tr):,} labelled event-event pairs  ({time.time()-t0:.0f}s)", flush=True)

    print("\nmining 8 views ...", flush=True)
    rules = {}
    for name, fn in VIEWS.items():
        r = mine_view(tr, fn, args.sup_min, args.lift_min, args.depth, args.beam)
        kept = 0
        for rule, s in r.items():
            if s[2] == MAJORITY:
                continue
            rules[(rule, s[2], name, s[5])] = s
            kept += 1
        print(f"  {name:<12} {len(r):>7,} mined, {kept:>7,} kept", flush=True)
    print(f"  TOTAL {len(rules):,} rules (after refusing {MAJORITY})  "
          f"({time.time()-t0:.0f}s)", flush=True)

    # ------------------------------------------------------------------ rules.json
    payload = []
    for (conds, rel, view, sig), s in sorted(rules.items(), key=lambda kv: -kv[1][0]):
        payload.append({
            "conds": [list(c) for c in conds],
            "text": fmt_rule(conds),
            "rel": rel, "view": view, "sig": str(sig),
            "wlb": round(s[0], 5), "lift": round(s[1], 3), "k": s[3], "n": s[4],
        })
    (ART / "rules.json").write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"\nwrote rules.json ({len(payload):,} rules)", flush=True)

    # ------------------------------------------------------------------ families.json
    print("\nabstracting to families ...", flush=True)
    fams = defaultdict(list)
    for (conds, rel, view, sig), s in rules.items():
        fams[(skeleton(conds), rel, view, sig)].append((conds, s))

    base = Counter(rel for _, _, rel in tr)
    tot = len(tr)
    families = []
    for (skel, rel, view, sig), members in fams.items():
        if len(members) < args.min_family:
            continue
        abs_conds = tuple(c for c in skel if c[2] != "*")
        if not abs_conds:
            continue
        fn = VIEWS[view]
        idx = [i for i, (f, cs, _) in enumerate(tr)
               if fn(f) == sig and all(c in cs for c in abs_conds)]
        n = len(idx)
        if n < args.sup_min:
            continue
        k = sum(1 for i in idx if tr[i][2] == rel)
        if k < 5:
            continue
        sub = [i for i, (f, _, _) in enumerate(tr) if fn(f) == sig]
        sub_base = Counter(tr[i][2] for i in sub)
        exp = sub_base[rel] / len(sub) if sub else 0
        if exp <= 0:
            continue
        lift = (k / n) / exp
        if lift < args.lift_min:
            continue
        families.append({
            "conds": [list(c) for c in abs_conds],
            "text": fmt_rule(abs_conds),
            "rel": rel, "view": view, "sig": str(sig),
            "wlb": round(wilson_lower(k, n), 5), "lift": round(lift, 3),
            "k": k, "n": n, "members": len(members),
            "types": sorted({v for c, _ in members
                             for f, a, v in c if a in TYPE_ATTRS})[:12],
        })
    families.sort(key=lambda f: -f["wlb"])
    (ART / "families.json").write_text(json.dumps(families, indent=1), encoding="utf-8")
    print(f"wrote families.json ({len(families):,} families)  "
          f"({time.time()-t0:.0f}s)", flush=True)

    # ------------------------------------------------------------------ constraints.json
    print("\nbuilding constraints ...", flush=True)
    dist = rule_distributions(tr, list(rules))
    print(f"  distributions for {len(dist):,} rules  ({time.time()-t0:.0f}s)", flush=True)

    out = {}
    for tau in args.tau:
        cons = []
        for key, cnt in dist.items():
            conds, rel, view, sig = key
            n = sum(cnt.values())
            if n < args.sup_min:
                continue
            forbidden = [r for r in RELATIONS if wilson_upper(cnt.get(r, 0), n) < tau]
            allowed = [r for r in RELATIONS if r not in forbidden]
            if not forbidden or not allowed:
                continue
            cons.append({
                "conds": [list(c) for c in conds],
                "text": fmt_rule(conds),
                "view": view, "sig": str(sig),
                "allowed": allowed, "forbidden": forbidden,
                "n": n, "dist": dict(cnt),
            })
        cons.sort(key=lambda c: -c["n"])
        out[str(tau)] = cons
        print(f"  tau={tau}: {len(cons):,} constraints", flush=True)

    (ART / "constraints.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    sizes = {t: len(v) for t, v in out.items()}
    print(f"wrote constraints.json {sizes}")

    print(f"\ntotal {time.time()-t0:.0f}s")
    for f in ("rules.json", "families.json", "constraints.json"):
        p = HERE / f
        print(f"  {f:<20} {p.stat().st_size/1e6:>7.1f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
