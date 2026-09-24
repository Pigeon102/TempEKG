"""Measure the exported constraint set against gold, per tau.

The 0.035% violation rate quoted in the documents belongs to an older, smaller constraint
set (1,730 rules mined on one flat pool). The exported set is mined across eight views and
is 7.9x larger at the same tau, so its violation rate has to be measured, not inherited.

Gold is internally consistent — 0 pairs with two labels, 0 BEFORE both ways, 0
PC-inconsistent documents — so every violation here is either an annotation error or a rule
error, with no third possibility. That makes the rate a direct specificity measurement with
no human judging.

Also reports what each tau actually forbids. A constraint that only ever forbids the two
rarest labels is safe but nearly vacuous, and the documents should say so rather than let a
low violation rate read as strength.

Usage:
    python score_constraints.py
    python score_constraints.py --split valid --tau 0.001
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from mine_compositional import candidate_conditions, fmt_cond
from mine_views import VIEWS, load

HERE = Path(__file__).resolve().parent
ART = HERE / "artifacts"   # mined artifacts; see data/README.md
GRAPH = HERE / "graph"
RELATIONS = ("BEFORE", "CONTAINS", "OVERLAP", "SIMULTANEOUS", "BEGINS-ON", "ENDS-ON")


def load_constraints(tau: str):
    data = json.loads((ART / "constraints.json").read_text(encoding="utf-8"))
    out = []
    for c in data[tau]:
        conds = tuple(tuple(x) if not isinstance(x[2], list) else (x[0], x[1], tuple(x[2]))
                      for x in c["conds"])
        out.append({"conds": conds, "view": c["view"], "sig": c["sig"],
                    "forbidden": set(c["forbidden"]), "allowed": c["allowed"],
                    "n": c["n"], "text": c["text"]})
    return out


def score(cons, data, want_examples: int = 0):
    """Apply constraints, counting a pair once even if several constraints fire on it.

    Indexed by each constraint's rarest condition; indexing by the first condition puts
    most of them behind something 98% of instances satisfy.
    """
    df = Counter()
    for _, cs, _ in data:
        for c in cs:
            df[c] += 1

    by_rare = defaultdict(list)
    for i, c in enumerate(cons):
        by_rare[min(c["conds"], key=lambda x: df.get(x, 0))].append(i)

    total = violated = 0
    by_rel = Counter()
    by_cons = Counter()
    fired_any = 0
    examples = []
    sig_cache = {}

    for f, cs, rel in data:
        total += 1
        hit = False
        fired = False
        for cond in cs:
            for i in by_rare.get(cond, ()):
                c = cons[i]
                v = c["view"]
                if v not in sig_cache:
                    sig_cache[v] = str(VIEWS[v](f))
                if sig_cache[v] != c["sig"]:
                    continue
                if not all(x in cs for x in c["conds"]):
                    continue
                fired = True
                if rel in c["forbidden"]:
                    hit = True
                    by_cons[i] += 1
                    if len(examples) < want_examples:
                        examples.append({"gold": rel, "text": c["text"],
                                         "view": v, "sig": c["sig"],
                                         "allowed": c["allowed"], "n": c["n"]})
                    break
            if hit:
                break
        sig_cache.clear()
        if fired:
            fired_any += 1
        if hit:
            violated += 1
            by_rel[rel] += 1

    return {"total": total, "violated": violated, "fired_any": fired_any,
            "by_rel": by_rel, "by_cons": by_cons, "examples": examples}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tau", nargs="+", default=["0.001", "0.005", "0.01"])
    ap.add_argument("--examples", type=int, default=6)
    args = ap.parse_args()

    print("loading splits ...", flush=True)
    tr = load(GRAPH / "train.jsonl")
    va = load(GRAPH / "valid.jsonl")
    print(f"  train {len(tr):,}  valid {len(va):,}", flush=True)

    nb_va = sum(1 for _, _, r in va if r != "BEFORE")
    print(f"  trivial baseline (flag every non-BEFORE on valid): "
          f"{nb_va:,} = {100*nb_va/len(va):.2f}%")

    print()
    hdr = (f"  {'tau':>6} {'cons':>7} {'fires on':>17} "
           f"{'train viol':>17} {'valid viol':>17} {'selectivity':>12}")
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))

    detail = {}
    for tau in args.tau:
        cons = load_constraints(tau)
        rt = score(cons, tr)
        rv = score(cons, va, args.examples)
        detail[tau] = (cons, rt, rv)
        sel = nb_va / rv["violated"] if rv["violated"] else float("inf")
        print(f"  {tau:>6} {len(cons):>7,} "
              f"{rv['fired_any']:>8,} ({100*rv['fired_any']/rv['total']:>4.1f}%) "
              f"{rt['violated']:>8,} ({100*rt['violated']/rt['total']:>5.3f}%) "
              f"{rv['violated']:>8,} ({100*rv['violated']/rv['total']:>5.3f}%) "
              f"{sel:>11.1f}x", flush=True)

    print()
    for tau in args.tau:
        cons, rt, rv = detail[tau]
        forb = Counter()
        for c in cons:
            for r in c["forbidden"]:
                forb[r] += 1
        print(f"tau={tau}")
        print(f"  constraints forbidding each label: {dict(forb.most_common())}")
        print(f"  violations by gold label (valid):  {dict(rv['by_rel'].most_common())}")
        if rv["by_cons"]:
            top = rv["by_cons"].most_common(3)
            print(f"  most-violated constraints:")
            for i, k in top:
                c = cons[i]
                print(f"    {k:>5,} x  [{c['view']}={c['sig'][:18]}] {c['text'][:62]}")
                print(f"             allowed={c['allowed']}  n={c['n']:,}")
        print()

    tau0 = args.tau[0]
    cons, rt, rv = detail[tau0]
    if rv["examples"]:
        print("=" * 74)
        print(f"SAMPLE VIOLATIONS at tau={tau0}")
        print("=" * 74)
        for i, e in enumerate(rv["examples"], 1):
            print(f"  {i}. gold={e['gold']} forbidden by [{e['view']}={e['sig'][:18]}]")
            print(f"     {e['text'][:68]}")
            print(f"     allowed={e['allowed']}  n={e['n']:,}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
