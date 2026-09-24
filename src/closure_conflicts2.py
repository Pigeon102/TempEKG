"""Closure-vs-gold conflicts, with self-inverse paths excluded.

The first pass found 51 conflicts and every one carried the gold label BEGINS-ON. A label
wrong 51 times while no other label is wrong once is a bug in the method, not 51 annotator
mistakes, and tracing the paths showed why: closure was travelling through pairs of
mutually inverse edges.

    a --CONTAINS--> x <--CONTAINS-- b        296 times
    a --BEFORE----> x <--BEFORE---- b        281 times

Those configurations say almost nothing about a-b: both events merely contain x, or both
precede x. But composing {di} with its own converse yields a narrow set, and that set
happens to exclude {s,si,e} -- so BEGINS-ON was hit because of where it sits in Allen's
algebra, not because of the data.

This excludes any two-edge path whose two labels are converses of each other, then reports
what survives. Whatever is left is a real candidate: gold says one thing, the remaining
evidence in the same document says it cannot be that.

Usage:
    python closure_conflicts2.py --docs 600
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL

ROOT = Path(__file__).resolve().parent.parent
GRAPH = Path(__file__).resolve().parent / "graph"


def maven_labels_in(aset):
    """Labels COMPATIBLE with an implied Allen set.

    Compatibility is a non-empty intersection, not containment. A label whose Allen set has
    several members -- BEGINS-ON is {s, si, e} -- is still admissible when closure narrows
    the pair to just one of them: closure saying "si" and the annotation saying BEGINS-ON
    agree, because si is one of the readings BEGINS-ON allows.

    Testing `a <= aset` instead demanded that the whole label set fit inside the implied
    set, which no multi-member label can satisfy once closure narrows to a singleton. That
    is why an earlier run reported 59 conflicts and every one was BEGINS-ON: it is the only
    label with several members that closure regularly pins down.
    """
    return [r for r, a in MAVEN_TO_ALLEN.items() if a & aset]


def scan(path: Path, limit: int, drop_self_inverse: bool):
    found = []
    stats = Counter()
    docs = 0

    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if limit and docs >= limit:
                break
            rec = json.loads(line)
            nodes = rec["nodes"]
            edges = [(e["s"], e["t"], e["rel"]) for e in rec["target_edges"]
                     if nodes[e["s"]]["kind"] == "event" and nodes[e["t"]]["kind"] == "event"]
            if len(edges) < 3:
                continue
            docs += 1

            for i, (a, b, rel) in enumerate(edges):
                target = MAVEN_TO_ALLEN.get(rel)
                if not target:
                    continue
                stats["pairs"] += 1

                # adjacency over every other edge, carrying the Allen set AND whether the
                # stored direction was flipped, so a self-inverse path can be recognised
                adj = defaultdict(dict)
                for j, (s, t, r) in enumerate(edges):
                    if j == i:
                        continue
                    aset = MAVEN_TO_ALLEN.get(r)
                    if not aset:
                        continue
                    adj[s][t] = (aset, r, False)
                    adj[t][s] = (converse(aset), r, True)

                implied = FULL
                paths = []
                for x, (ax, ra, fa) in adj.get(a, {}).items():
                    if x == b:
                        continue
                    hit = adj.get(x, {}).get(b)
                    if not hit:
                        continue
                    xb, rb, fb = hit
                    # a -R-> x <-R- b : the two legs are the same relation in opposite
                    # storage directions, so the path carries no real ordering evidence
                    if drop_self_inverse and ra == rb and fa != fb:
                        stats["dropped_self_inverse"] += 1
                        continue
                    implied = implied & compose(ax, xb)
                    paths.append((x, ra, rb))

                if implied == FULL:
                    stats["no_path"] += 1
                    continue
                adm = maven_labels_in(implied)
                if rel in adm:
                    stats["consistent"] += 1
                    continue

                stats["EXCLUDED"] += 1
                if len(adm) == 1:
                    stats["excluded_single"] += 1
                found.append({
                    "doc": rec["doc_id"], "a": a, "b": b, "gold": rel,
                    "trig_a": nodes[a].get("trigger"), "trig_b": nodes[b].get("trigger"),
                    "type_a": nodes[a].get("type"), "type_b": nodes[b].get("type"),
                    "sent_a": nodes[a].get("sent_first"), "sent_b": nodes[b].get("sent_first"),
                    "implied": sorted(implied), "admissible": adm,
                    "paths": [{"via": nodes[x].get("trigger"), "leg1": r1, "leg2": r2}
                              for x, r1, r2 in paths[:4]],
                    "n_paths": len(paths),
                })
    return found, stats, docs


def load_sentences(doc_ids: set) -> dict:
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
    ap.add_argument("--split", default="train")
    ap.add_argument("--docs", type=int, default=600)
    ap.add_argument("--show", type=int, default=10)
    ap.add_argument("--drop-self-inverse", action="store_true",
                    help="ablation: ignore a->x<-b paths whose legs are converses")
    ap.add_argument("--containment", action="store_true",
                    help="use the old (wrong) containment test, to reproduce the artifact")
    args = ap.parse_args()

    # self-inverse paths are legitimate evidence; the earlier suspicion was wrong and the
    # real bug was the containment test. Kept as a flag only for ablation.
    found, st, docs = scan(GRAPH / f"{args.split}.jsonl", args.docs,
                           args.drop_self_inverse)

    print(f"documents scanned          {docs:,}")
    print(f"labelled event-event pairs {st['pairs']:,}")
    print(f"  self-inverse paths dropped {st['dropped_self_inverse']:,}")
    print(f"  no closure path          {st['no_path']:,} "
          f"({100*st['no_path']/st['pairs']:.1f}%)")
    print(f"  closure agrees           {st['consistent']:,} "
          f"({100*st['consistent']/st['pairs']:.1f}%)")
    print(f"  CLOSURE EXCLUDES GOLD    {st['EXCLUDED']:,} "
          f"({100*st['EXCLUDED']/st['pairs']:.4f}%)")
    print(f"    names exactly one label: {st['excluded_single']:,}")

    if not found:
        print()
        print("No conflict survives. Gold is consistent under one-step closure once")
        print("self-inverse paths are excluded -- the 51 earlier hits were all artifacts.")
        return 0

    found.sort(key=lambda f: (len(f["admissible"]), -f["n_paths"]))
    by_doc = Counter(f["doc"] for f in found)
    by_gold = Counter(f["gold"] for f in found)
    print()
    print(f"spread over {len(by_doc):,} documents "
          f"(most in one: {by_doc.most_common(1)[0][1]})")
    print(f"gold labels: {dict(by_gold)}")

    out = Path(__file__).resolve().parent / "closure_conflicts2.json"
    out.write_text(json.dumps(found, indent=1), encoding="utf-8")
    print(f"wrote {out.name} ({len(found)} candidates)")

    show = found[:args.show]
    sents = load_sentences({f["doc"] for f in show})
    print()
    print("=" * 74)
    print(f"HAND INSPECTION -- {len(show)} sharpest, with source text")
    print("=" * 74)
    for i, f in enumerate(show, 1):
        print()
        print(f"--- {i} --- doc {f['doc'][:16]}  ({f['n_paths']} path(s))")
        print(f"  gold:     {f['gold']}")
        print(f"  closure:  {f['implied']} -> admits {f['admissible']}")
        print(f"  A: {f['type_a']:<22} '{f['trig_a']}'  sent {f['sent_a']}")
        print(f"  B: {f['type_b']:<22} '{f['trig_b']}'  sent {f['sent_b']}")
        for p in f["paths"]:
            print(f"     via '{p['via']}': {p['leg1']} then {p['leg2']}")
        ss = sents.get(f["doc"]) or []
        for lbl, si in (("A", f["sent_a"]), ("B", f["sent_b"])):
            if si is not None and 0 <= si < len(ss):
                print(f"  text {lbl}: {ss[si][:230]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
