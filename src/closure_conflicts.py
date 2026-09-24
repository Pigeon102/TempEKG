"""Find pairs where Allen closure forces one label and the gold says another.

These are the cleanest audit candidates in the project. No statistics are involved: the
other temporal edges in the document, composed through Allen's algebra, admit exactly one
MAVEN label for this pair, and the annotation records a different one. Either the gold is
wrong here, or one of the edges the closure travelled through is wrong.

Every other candidate this project produces rests on a mined rule, so a reviewer can always
ask whether the rule is the thing that is wrong. These do not.

Scans every document rather than deleting edges: for each labelled event-event pair, compose
over all two-edge paths through the REMAINING edges and see whether the result excludes the
recorded label.

Usage:
    python closure_conflicts.py
    python closure_conflicts.py --docs 500 --show 10
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL

ROOT = Path(__file__).resolve().parent.parent
GRAPH = Path(__file__).resolve().parent / "graph"


def maven_labels_in(aset) -> list:
    return [r for r, a in MAVEN_TO_ALLEN.items() if a <= aset]


def scan(path: Path, limit: int):
    """Yield every pair whose recorded label is excluded by one-step closure."""
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

                # adjacency over every OTHER edge
                out = defaultdict(dict)
                for j, (s, t, r) in enumerate(edges):
                    if j == i:
                        continue
                    aset = MAVEN_TO_ALLEN.get(r)
                    if not aset:
                        continue
                    out[s][t] = aset
                    out[t][s] = converse(aset)

                implied = FULL
                path_via = []
                for x, ax in out.get(a, {}).items():
                    if x == b:
                        continue
                    xb = out.get(x, {}).get(b)
                    if xb:
                        implied = implied & compose(ax, xb)
                        path_via.append(x)
                if implied == FULL:
                    stats["no_path"] += 1
                    continue

                admissible = maven_labels_in(implied)
                if rel in admissible:
                    stats["consistent"] += 1
                    continue

                stats["EXCLUDED"] += 1
                if len(admissible) == 1:
                    stats["excluded_single"] += 1
                found.append({
                    "doc": rec["doc_id"], "a": a, "b": b, "gold": rel,
                    "trig_a": nodes[a].get("trigger"), "trig_b": nodes[b].get("trigger"),
                    "type_a": nodes[a].get("type"), "type_b": nodes[b].get("type"),
                    "sent_a": nodes[a].get("sent_first"), "sent_b": nodes[b].get("sent_first"),
                    "implied": sorted(implied),
                    "admissible": admissible,
                    "via": path_via[:4],
                    "n_via": len(path_via),
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
    ap.add_argument("--docs", type=int, default=0, help="0 = all")
    ap.add_argument("--show", type=int, default=12)
    args = ap.parse_args()

    found, stats, docs = scan(GRAPH / f"{args.split}.jsonl", args.docs)

    print(f"documents scanned          {docs:,}")
    print(f"labelled event-event pairs {stats['pairs']:,}")
    print(f"  no closure path          {stats['no_path']:,} "
          f"({100*stats['no_path']/stats['pairs']:.1f}%)")
    print(f"  closure agrees           {stats['consistent']:,} "
          f"({100*stats['consistent']/stats['pairs']:.1f}%)")
    print(f"  CLOSURE EXCLUDES GOLD    {stats['EXCLUDED']:,} "
          f"({100*stats['EXCLUDED']/stats['pairs']:.3f}%)")
    print(f"    of which closure names exactly one label: {stats['excluded_single']:,}")

    if not found:
        print("\nNothing to inspect.")
        return 0

    # the single-label cases are the sharpest; show those first
    found.sort(key=lambda f: (len(f["admissible"]), -f["n_via"]))
    by_doc = Counter(f["doc"] for f in found)
    print(f"\nspread over {len(by_doc):,} documents "
          f"(most in one document: {by_doc.most_common(1)[0][1]})")
    print(f"gold label of the excluded pairs: {dict(Counter(f['gold'] for f in found))}")

    out = Path(__file__).resolve().parent / "closure_conflicts.json"
    out.write_text(json.dumps(found, indent=1), encoding="utf-8")
    print(f"wrote {out.name} ({len(found)} candidates)")

    show = found[:args.show]
    sents = load_sentences({f["doc"] for f in show})
    print()
    print("=" * 74)
    print(f"HAND INSPECTION -- {len(show)} sharpest candidates, with source text")
    print("=" * 74)
    for i, f in enumerate(show, 1):
        print()
        print(f"--- {i} --- doc {f['doc'][:16]}  (closure travelled {f['n_via']} path(s))")
        print(f"  gold:       {f['gold']}")
        print(f"  closure:    {f['implied']}  -> admits only {f['admissible']}")
        print(f"  event A:    {f['type_a']:<22} '{f['trig_a']}'  câu {f['sent_a']}")
        print(f"  event B:    {f['type_b']:<22} '{f['trig_b']}'  câu {f['sent_b']}")
        ss = sents.get(f["doc"]) or []
        for lbl, si in (("A", f["sent_a"]), ("B", f["sent_b"])):
            if si is not None and 0 <= si < len(ss):
                print(f"  text {lbl}:     {ss[si][:260]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
