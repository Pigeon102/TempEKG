"""Why does every closure-vs-gold conflict involve BEGINS-ON?

All 51 conflicts found by closure_conflicts.py carry the gold label BEGINS-ON. A label that
is wrong 51 times and no other label wrong once is a bug in our handling, not 51 annotator
mistakes. Two suspects:

  (a) the mapping BEGINS-ON = {s, si, e} is wrong or too wide;
  (b) build_kg.py canonicalises symmetric relations to (min_id, max_id), which discards the
      recorded direction. Harmless for a symmetric relation on its own, but composition with
      an asymmetric relation reads the stored direction.

This separates them: rebuild each conflicting document from the RAW MAVEN-ERE file, keeping
the original direction, and see whether the conflict survives.

Usage:
    python probe_beginson.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL

ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
ART = HERE / "artifacts"   # mined artifacts; see data/README.md


def maven_labels_in(aset):
    return [r for r, a in MAVEN_TO_ALLEN.items() if a <= aset]


def conflicts_in(edges):
    """One-step closure conflicts over a list of (a, b, rel), directions as given."""
    out_ = []
    for i, (a, b, rel) in enumerate(edges):
        target = MAVEN_TO_ALLEN.get(rel)
        if not target:
            continue
        adj = defaultdict(dict)
        for j, (s, t, r) in enumerate(edges):
            if j == i:
                continue
            aset = MAVEN_TO_ALLEN.get(r)
            if not aset:
                continue
            adj[s][t] = aset
            adj[t][s] = converse(aset)
        implied = FULL
        for x, ax in adj.get(a, {}).items():
            if x == b:
                continue
            xb = adj.get(x, {}).get(b)
            if xb:
                implied = implied & compose(ax, xb)
        if implied == FULL:
            continue
        if rel not in maven_labels_in(implied):
            out_.append((a, b, rel, sorted(implied)))
    return out_


def main() -> int:
    conf = json.loads((ART / "closure_conflicts.json").read_text(encoding="utf-8"))
    docs = {c["doc"] for c in conf}
    print(f"conflicts on record: {len(conf)} over {len(docs)} documents")
    print(f"gold labels involved: {dict(Counter(c['gold'] for c in conf))}")
    print()

    # ---------------------------------------------------------------- suspect (b)
    print("=" * 74)
    print("SUSPECT (b): does canonicalisation of symmetric edges cause it?")
    print("=" * 74)
    raw = {}
    for line in (ROOT / "MAVEN_ERE" / "train.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        if d["id"] in docs:
            raw[d["id"]] = d
            if len(raw) == len(docs):
                break
    print(f"  reloaded {len(raw)} documents from the raw ERE file")

    built = {}
    for line in (HERE / "graph" / "train.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        if r["doc_id"] in docs:
            built[r["doc_id"]] = r
            if len(built) == len(docs):
                break

    tot_raw = tot_built = 0
    flipped = 0
    for doc_id, d in raw.items():
        ev = {e["id"] for e in d.get("events") or []}
        raw_edges = []
        for rel, pairs in (d.get("temporal_relations") or {}).items():
            for p in pairs:
                if p[0] in ev and p[1] in ev:
                    raw_edges.append((p[0], p[1], rel))
        b = built[doc_id]
        nd = b["nodes"]
        built_edges = [(e["s"], e["t"], e["rel"]) for e in b["target_edges"]
                       if nd[e["s"]]["kind"] == "event" and nd[e["t"]]["kind"] == "event"]

        # how many BEGINS-ON edges were stored with the endpoints swapped?
        raw_bo = {(a, b_) for a, b_, r in raw_edges if r == "BEGINS-ON"}
        for a, b_, r in built_edges:
            if r == "BEGINS-ON" and (a, b_) not in raw_bo and (b_, a) in raw_bo:
                flipped += 1

        tot_raw += len(conflicts_in(raw_edges))
        tot_built += len(conflicts_in(built_edges))

    print(f"  BEGINS-ON edges stored with endpoints swapped: {flipped}")
    print(f"  conflicts using RAW directions:   {tot_raw}")
    print(f"  conflicts using BUILT directions: {tot_built}")
    if tot_raw == tot_built:
        print("  -> canonicalisation is NOT the cause")
    else:
        print("  -> canonicalisation IS implicated")

    # ---------------------------------------------------------------- suspect (a)
    print()
    print("=" * 74)
    print("SUSPECT (a): is the mapping BEGINS-ON = {s,si,e} too wide?")
    print("=" * 74)
    print("  Candidate mappings, scored by how many conflicts each leaves:")
    print()
    candidates = {
        "{s,si,e}  (current)": frozenset({"s", "si", "e"}),
        "{s}       (a starts b)": frozenset({"s"}),
        "{s,si}    (co-start, either)": frozenset({"s", "si"}),
        "{e}       (identical)": frozenset({"e"}),
        "{s,si,e,d,di} (co-start, loose end)": frozenset({"s", "si", "e", "d", "di"}),
    }
    base = MAVEN_TO_ALLEN["BEGINS-ON"]
    for name, aset in candidates.items():
        MAVEN_TO_ALLEN["BEGINS-ON"] = aset
        tot = 0
        for doc_id, d in raw.items():
            ev = {e["id"] for e in d.get("events") or []}
            edges = []
            for rel, pairs in (d.get("temporal_relations") or {}).items():
                for p in pairs:
                    if p[0] in ev and p[1] in ev:
                        edges.append((p[0], p[1], rel))
            tot += len(conflicts_in(edges))
        print(f"  {name:<38} conflicts: {tot}")
    MAVEN_TO_ALLEN["BEGINS-ON"] = base

    # ---------------------------------------------------------------- the 21 rules
    print()
    print("=" * 74)
    print("Does a narrower mapping still satisfy the paper's 21 transitivity rules?")
    print("=" * 74)
    RULES = [
        ('BEFORE', 'BEFORE', 'BEFORE'), ('BEFORE', 'CONTAINS', 'BEFORE'),
        ('BEFORE', 'SIMULTANEOUS', 'BEFORE'), ('BEFORE', 'OVERLAP', 'BEFORE'),
        ('BEFORE', 'BEGINS-ON', 'BEFORE'), ('BEFORE', 'ENDS-ON', 'BEFORE'),
        ('CONTAINS', 'CONTAINS', 'CONTAINS'), ('CONTAINS', 'SIMULTANEOUS', 'CONTAINS'),
        ('CONTAINS', 'BEGINS-ON', 'CONTAINS'), ('CONTAINS', 'ENDS-ON', 'CONTAINS'),
        ('SIMULTANEOUS', 'BEFORE', 'BEFORE'), ('SIMULTANEOUS', 'CONTAINS', 'CONTAINS'),
        ('SIMULTANEOUS', 'SIMULTANEOUS', 'SIMULTANEOUS'), ('SIMULTANEOUS', 'OVERLAP', 'OVERLAP'),
        ('SIMULTANEOUS', 'BEGINS-ON', 'BEGINS-ON'), ('SIMULTANEOUS', 'ENDS-ON', 'ENDS-ON'),
        ('OVERLAP', 'BEFORE', 'BEFORE'), ('OVERLAP', 'SIMULTANEOUS', 'OVERLAP'),
        ('BEGINS-ON', 'SIMULTANEOUS', 'BEGINS-ON'), ('BEGINS-ON', 'BEGINS-ON', 'BEGINS-ON'),
        ('ENDS-ON', 'SIMULTANEOUS', 'ENDS-ON'),
    ]
    for name, aset in candidates.items():
        MAVEN_TO_ALLEN["BEGINS-ON"] = aset
        sound = sum(1 for ab, bc, ac in RULES
                    if MAVEN_TO_ALLEN[ac] <= compose(MAVEN_TO_ALLEN[ab], MAVEN_TO_ALLEN[bc]))
        print(f"  {name:<38} sound: {sound}/21")
    MAVEN_TO_ALLEN["BEGINS-ON"] = base
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
