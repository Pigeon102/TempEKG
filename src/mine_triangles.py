"""Direction 3: mine the temporal graph itself, not pairs in isolation.

Two questions, both answered by counting on the built graph:

  (A) TRIANGLE FORCING. For every path a->b->c whose two edges are labelled, Allen
      composition gives the set of relations the a-c edge may take. Three outcomes:
        - a-c is labelled and inside the set        -> consistent
        - a-c is labelled and outside the set       -> HARD CONTRADICTION
        - a-c is unlabelled and the set is a single -> FORCED, a derived label
      The third is the one that matters: it produces labels the annotation does not
      have, which is the only honest way to say "the annotator missed one".

  (B) RULE SPACE. Whether one motif generalises into a family, measured over the
      independent axes that MAVEN has and Wikidata does not: type pair, discourse
      order, sentence distance, anchor role pair. Reports how many rules clear
      support and lift at each axis combination, so the lattice is chosen from
      numbers rather than from taste.

Usage:
    python mine_triangles.py --split train
    python mine_triangles.py --split train --mode rules
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL

ROOT = Path(__file__).resolve().parent.parent

# Inverse map: an Allen set back to the MAVEN label(s) it could be reported as.
ALLEN_TO_MAVEN = {}
for _rel, _aset in MAVEN_TO_ALLEN.items():
    ALLEN_TO_MAVEN.setdefault(frozenset(_aset), []).append(_rel)


def read_graph(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def wilson_lower(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - m) / d)


def maven_label_of(allen_set: frozenset) -> str | None:
    """If an Allen set is exactly one MAVEN label's set, name it."""
    names = ALLEN_TO_MAVEN.get(allen_set)
    return names[0] if names and len(names) == 1 else None


def mine_triangles(path: Path, limit: int = 0) -> dict:
    stats = Counter()
    forced_by_rule = Counter()
    contradiction_examples = []
    forced_examples = []
    # (rel_ab, rel_bc) -> Counter over what the gold a-c actually is
    composition_evidence = defaultdict(Counter)

    for i, rec in enumerate(read_graph(path)):
        if limit and i >= limit:
            break
        stats["doc"] += 1
        nodes = rec["nodes"]

        # adjacency over labelled edges, both orientations
        out = defaultdict(dict)
        gold = {}
        for e in rec["target_edges"]:
            a, b, rel = e["s"], e["t"], e["rel"]
            aset = MAVEN_TO_ALLEN.get(rel)
            if aset is None:
                continue
            out[a][b] = aset
            out[b][a] = converse(aset)
            gold[(a, b)] = rel
            gold[(b, a)] = None  # marker: pair is known, stored the other way

        nodes_with_edges = list(out)
        for a in nodes_with_edges:
            for b, ab in out[a].items():
                if b == a:
                    continue
                for c, bc in out[b].items():
                    if c in (a, b):
                        continue
                    stats["path"] += 1
                    implied = compose(ab, bc)
                    if implied == FULL:
                        stats["path_uninformative"] += 1
                        continue

                    key = (a, c)
                    observed = None
                    if key in gold and gold[key] is not None:
                        observed = gold[key]
                    elif (c, a) in gold and gold[(c, a)] is not None:
                        # stored the other way; compare against the converse
                        observed = None

                    ac_edge = out[a].get(c)
                    if ac_edge is not None:
                        stats["path_ac_labelled"] += 1
                        if not (ac_edge & implied):
                            stats["HARD_CONTRADICTION"] += 1
                            if len(contradiction_examples) < 10:
                                contradiction_examples.append({
                                    "doc": rec["doc_id"], "a": a, "b": b, "c": c,
                                    "ab": gold.get((a, b)) or gold.get((b, a)),
                                    "bc": gold.get((b, c)) or gold.get((c, b)),
                                    "ac_observed": observed,
                                })
                        else:
                            stats["path_ac_consistent"] += 1
                            if observed:
                                ab_lbl = gold.get((a, b))
                                bc_lbl = gold.get((b, c))
                                if ab_lbl and bc_lbl:
                                    composition_evidence[(ab_lbl, bc_lbl)][observed] += 1
                    else:
                        stats["path_ac_unlabelled"] += 1
                        derived = maven_label_of(implied)
                        if derived is not None:
                            stats["FORCED_single"] += 1
                            ab_lbl = gold.get((a, b))
                            bc_lbl = gold.get((b, c))
                            if ab_lbl and bc_lbl:
                                forced_by_rule[(ab_lbl, bc_lbl, derived)] += 1
                            if len(forced_examples) < 10:
                                forced_examples.append({
                                    "doc": rec["doc_id"],
                                    "a": nodes[a].get("trigger"), "b": nodes[b].get("trigger"),
                                    "c": nodes[c].get("trigger"),
                                    "ab": ab_lbl, "bc": bc_lbl, "derived": derived,
                                })
                        elif len(implied) < 13:
                            stats["FORCED_set"] += 1

    return {
        "stats": stats,
        "forced_by_rule": forced_by_rule,
        "contradictions": contradiction_examples,
        "forced_examples": forced_examples,
        "composition_evidence": composition_evidence,
    }


AXES = ("type", "order", "sdist", "role")


def mine_rules(path: Path, limit: int = 0) -> dict:
    """Rule space over independent axes. Anchor (role) is optional, not required."""
    # per axis-subset: key -> Counter(relation)
    tables = {}
    subsets = []
    for mask in range(1, 1 << len(AXES)):
        sub = tuple(AXES[i] for i in range(len(AXES)) if mask >> i & 1)
        if "type" not in sub:
            continue  # type pair is the mandatory backbone
        subsets.append(sub)
        tables[sub] = defaultdict(Counter)

    base = Counter()
    n_pairs = 0

    for i, rec in enumerate(read_graph(path)):
        if limit and i >= limit:
            break
        nodes = rec["nodes"]

        role_of = defaultdict(list)
        for p in rec["anchored_pairs"]:
            role_of[(p["a"], p["b"])] = p["roles"]

        for e in rec["target_edges"]:
            a, b, rel = e["s"], e["t"], e["rel"]
            na, nb = nodes[a], nodes[b]
            if na["kind"] != "event" or nb["kind"] != "event":
                continue
            n_pairs += 1
            base[rel] += 1

            ta, tb = na.get("type"), nb.get("type")
            sa, sb = na.get("sent_first"), nb.get("sent_first")
            if sa is None or sb is None:
                order, sd = None, None
            else:
                order = "fwd" if sa < sb else ("same" if sa == sb else "rev")
                d = abs(sa - sb)
                sd = 0 if d == 0 else (1 if d == 1 else (2 if d <= 3 else (3 if d <= 7 else 4)))

            roles = role_of.get((a, b)) or role_of.get((b, a)) or [None]

            for sub in subsets:
                for rp in roles:
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
                    if "role" in sub and rp is None:
                        continue  # this pair has no anchor; it cannot instantiate a role rule
                    tables[sub][tuple(parts)][rel] += 1

    return {"tables": tables, "base": base, "n_pairs": n_pairs, "subsets": subsets}


def report_rules(res: dict, sup_min: int, lift_min: float) -> None:
    base, total = res["base"], sum(res["base"].values())
    print(f"event-event labelled pairs: {res['n_pairs']:,}")
    print("base rate:", {k: f"{100*v/total:.2f}%" for k, v in base.most_common()})
    print()
    print(f"RULE COUNTS  (support >= {sup_min}, lift >= {lift_min}, Wilson-LB used for ranking)")
    print()
    header = f"{'axes':32s} {'keys':>8s} {'keys@sup':>9s} {'rules':>8s} {'lift>=2':>8s} {'lift>=5':>8s} {'coverage':>9s}"
    print(header)
    print("-" * len(header))

    best = []
    for sub in res["subsets"]:
        tbl = res["tables"][sub]
        keys_at_sup = 0
        rules = l2 = l5 = 0
        covered = 0
        for key, cnt in tbl.items():
            s = sum(cnt.values())
            if s < sup_min:
                continue
            keys_at_sup += 1
            hit = False
            for rel, n in cnt.items():
                if n < 5:
                    continue
                conf = n / s
                b = base[rel] / total
                lift = conf / b if b else 0.0
                if lift >= lift_min:
                    rules += 1
                    hit = True
                    best.append((lift, wilson_lower(n, s), s, n, conf, rel, sub, key))
                if lift >= 2:
                    l2 += 1
                if lift >= 5:
                    l5 += 1
            if hit:
                covered += s
        name = "+".join(sub)
        print(f"{name:32s} {len(tbl):8,} {keys_at_sup:9,} {rules:8,} {l2:8,} {l5:8,} "
              f"{100*covered/res['n_pairs']:8.1f}%")

    print()
    best.sort(key=lambda r: -r[1])  # rank by Wilson lower bound, not raw lift
    print(f"TOP 20 RULES by Wilson-LB (of {len(best):,} with lift >= {lift_min})")
    print()
    for lift, wlb, s, n, conf, rel, sub, key in best[:20]:
        axes = "+".join(sub)
        print(f"  lift {lift:6.1f}x  wlb {wlb:.3f}  sup {s:5d}  n {n:4d}  conf {conf:.2f}  "
              f"{rel:13s} [{axes}] {key}")

    print()
    rel_counts = Counter(r[5] for r in best)
    print("rules by predicted relation:", dict(rel_counts.most_common()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="train")
    ap.add_argument("--graph-dir", type=Path, default=HERE / "graph")
    ap.add_argument("--mode", default="triangles", choices=["triangles", "rules", "both"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sup-min", type=int, default=25)
    ap.add_argument("--lift-min", type=float, default=2.0)
    args = ap.parse_args()

    path = args.graph_dir / f"{args.split}.jsonl"

    if args.mode in ("triangles", "both"):
        print("=" * 72)
        print("DIRECTION 3 -- TRIANGLE FORCING")
        print("=" * 72)
        r = mine_triangles(path, args.limit)
        s = r["stats"]
        print(f"documents                 {s['doc']:,}")
        print(f"two-edge paths a->b->c    {s['path']:,}")
        print(f"  composition = full      {s['path_uninformative']:,}  (no information)")
        print(f"  a-c already labelled    {s['path_ac_labelled']:,}")
        print(f"    consistent            {s['path_ac_consistent']:,}")
        print(f"    HARD CONTRADICTION    {s['HARD_CONTRADICTION']:,}")
        print(f"  a-c unlabelled          {s['path_ac_unlabelled']:,}")
        print(f"    FORCED to one label   {s['FORCED_single']:,}")
        print(f"    narrowed to a set     {s['FORCED_set']:,}")

        if r["forced_by_rule"]:
            print()
            print("composition rules that force a label (top 15):")
            for (ab, bc, d), n in r["forced_by_rule"].most_common(15):
                print(f"  {ab:13s} o {bc:13s} => {d:13s}  {n:,}")

        if r["forced_examples"]:
            print()
            print("forced-label examples:")
            for e in r["forced_examples"][:5]:
                print(f"  {e['a']} -{e['ab']}-> {e['b']} -{e['bc']}-> {e['c']}"
                      f"   =>  {e['a']} -{e['derived']}-> {e['c']}   ({e['doc'][:12]})")

        if r["contradictions"]:
            print()
            print("HARD CONTRADICTIONS:")
            for e in r["contradictions"]:
                print(f"  {e}")

        ce = r["composition_evidence"]
        if ce:
            print()
            print("where a-c IS labelled: does the gold agree with composition? (top 10 rules)")
            rows = sorted(ce.items(), key=lambda kv: -sum(kv[1].values()))[:10]
            for (ab, bc), cnt in rows:
                tot = sum(cnt.values())
                top = cnt.most_common(3)
                print(f"  {ab:13s} o {bc:13s}  n={tot:6,}  " +
                      "  ".join(f"{k}={100*v/tot:.0f}%" for k, v in top))
        print()

    if args.mode in ("rules", "both"):
        print("=" * 72)
        print("RULE SPACE -- CAN ONE MOTIF BECOME A FAMILY?")
        print("=" * 72)
        res = mine_rules(path, args.limit)
        report_rules(res, args.sup_min, args.lift_min)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
