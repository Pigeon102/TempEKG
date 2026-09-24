"""Mine rules on train, test them on valid. The only number that matters.

A rule family that does not survive a held-out split is a description of the training
set, not a finding. This measures, for the union family across axis subsets:

  - how many mined rules fire at all on valid
  - their precision on valid versus on train (shrinkage)
  - lift on valid against valid's own base rate
  - how many rules survive a Wilson lower bound on valid

Also reports the honest baselines a reviewer will ask for: predicting the majority
label, and predicting the majority label among non-BEFORE.

Usage:
    python holdout_rules.py
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

ROOT = Path(__file__).resolve().parent.parent

AXES = ("type", "order", "sdist", "role")


def wilson_lower(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - m) / d)


def instances(path: Path):
    """Yield (keys_by_subset, relation) for every labelled event-event pair."""
    subsets = []
    for mask in range(1, 1 << len(AXES)):
        sub = tuple(AXES[i] for i in range(len(AXES)) if mask >> i & 1)
        if "type" in sub:
            subsets.append(sub)

    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            nodes = rec["nodes"]
            role_of = {}
            for p in rec["anchored_pairs"]:
                role_of[(p["a"], p["b"])] = p["roles"]

            for e in rec["target_edges"]:
                a, b, rel = e["s"], e["t"], e["rel"]
                na, nb = nodes[a], nodes[b]
                if na["kind"] != "event" or nb["kind"] != "event":
                    continue
                ta, tb = na.get("type"), nb.get("type")
                sa, sb = na.get("sent_first"), nb.get("sent_first")
                if sa is None or sb is None:
                    order = sd = None
                else:
                    order = "fwd" if sa < sb else ("same" if sa == sb else "rev")
                    d = abs(sa - sb)
                    sd = 0 if d == 0 else (1 if d == 1 else (2 if d <= 3 else (3 if d <= 7 else 4)))
                roles = role_of.get((a, b)) or role_of.get((b, a)) or [None]

                keys = []
                for sub in subsets:
                    for rp in roles:
                        if "role" in sub and rp is None:
                            continue
                        parts = []
                        for ax in sub:
                            if ax == "type":
                                parts.append((ta, tb))
                            elif ax == "order":
                                parts.append(order)
                            elif ax == "sdist":
                                parts.append(sd)
                            elif ax == "role":
                                parts.append(tuple(rp) if rp else None)
                        keys.append((sub, tuple(parts)))
                yield keys, rel


def build_tables(path: Path):
    tbl = defaultdict(Counter)
    base = Counter()
    n = 0
    for keys, rel in instances(path):
        base[rel] += 1
        n += 1
        for k in keys:
            tbl[k][rel] += 1
    return tbl, base, n


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--graph-dir", type=Path, default=HERE / "graph")
    ap.add_argument("--sup-min", type=int, default=25)
    ap.add_argument("--lift-min", type=float, default=2.0)
    ap.add_argument("--wlb-min", type=float, default=0.0)
    args = ap.parse_args()

    print("mining on train ...")
    tr_tbl, tr_base, tr_n = build_tables(args.graph_dir / "train.jsonl")
    tr_tot = sum(tr_base.values())

    rules = {}
    for key, cnt in tr_tbl.items():
        s = sum(cnt.values())
        if s < args.sup_min:
            continue
        for rel, k in cnt.items():
            if k < 5:
                continue
            conf = k / s
            b = tr_base[rel] / tr_tot
            lift = conf / b if b else 0.0
            wlb = wilson_lower(k, s)
            if lift >= args.lift_min and wlb >= args.wlb_min:
                prev = rules.get(key)
                if prev is None or wlb > prev["wlb"]:
                    rules[key] = {"rel": rel, "conf": conf, "lift": lift,
                                  "wlb": wlb, "sup": s, "n": k}

    print(f"  train pairs {tr_n:,}, rules mined {len(rules):,}")
    print(f"  train base  " + str({k: f'{100*v/tr_tot:.2f}%' for k, v in tr_base.most_common()}))
    print()

    print("applying to valid ...")
    va_base = Counter()
    fired = Counter()
    correct = Counter()
    per_rule = defaultdict(lambda: [0, 0])
    n_va = 0
    matched_any = 0

    for keys, rel in instances(args.graph_dir / "valid.jsonl"):
        va_base[rel] += 1
        n_va += 1
        hits = [(k, rules[k]) for k in keys if k in rules]
        if not hits:
            continue
        matched_any += 1
        # most specific rule wins: longest axis subset, then highest Wilson-LB
        hits.sort(key=lambda kv: (-len(kv[0][0]), -kv[1]["wlb"]))
        key, r = hits[0]
        fired[r["rel"]] += 1
        per_rule[key][1] += 1
        if r["rel"] == rel:
            correct[r["rel"]] += 1
            per_rule[key][0] += 1

    va_tot = sum(va_base.values())
    print(f"  valid pairs {n_va:,}")
    print(f"  valid base  " + str({k: f'{100*v/va_tot:.2f}%' for k, v in va_base.most_common()}))
    print()

    tot_fired = sum(fired.values())
    tot_correct = sum(correct.values())
    print("=" * 72)
    print("HELD-OUT RESULT")
    print("=" * 72)
    print(f"instances matched by >=1 rule   {matched_any:,} / {n_va:,} = {100*matched_any/n_va:.1f}%")
    print(f"precision of fired rules        {tot_correct:,}/{tot_fired:,} = "
          f"{100*tot_correct/tot_fired:.2f}%" if tot_fired else "  no rule fired")
    print()
    print("by predicted relation:")
    print(f"  {'rel':14s} {'fired':>8s} {'correct':>8s} {'prec':>7s} {'valid base':>11s} {'lift':>7s}")
    for rel in sorted(fired, key=lambda r: -fired[r]):
        f, c = fired[rel], correct[rel]
        b = va_base[rel] / va_tot
        prec = c / f if f else 0.0
        print(f"  {rel:14s} {f:8,} {c:8,} {100*prec:6.2f}% {100*b:10.2f}% "
              f"{prec/b if b else 0:6.2f}x")

    print()
    print("baselines on the SAME matched instances:")
    # recompute the matched subset's gold distribution
    matched_gold = Counter()
    for keys, rel in instances(args.graph_dir / "valid.jsonl"):
        if any(k in rules for k in keys):
            matched_gold[rel] += 1
    m_tot = sum(matched_gold.values())
    for rel, n in matched_gold.most_common(3):
        print(f"  constant '{rel}'        {n:,}/{m_tot:,} = {100*n/m_tot:.2f}%")
    print(f"  our family              {tot_correct:,}/{tot_fired:,} = "
          f"{100*tot_correct/tot_fired:.2f}%")

    print()
    surviving = sum(1 for k, (c, f) in per_rule.items() if f >= 5 and c / f >= 0.5)
    print(f"rules that fired >=5 times on valid: {sum(1 for c, f in per_rule.values() if f >= 5):,}")
    print(f"  of those, precision >= 0.50:      {surviving:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
