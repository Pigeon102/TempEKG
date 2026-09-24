"""Check the built KG against the invariants it is supposed to guarantee.

Every check here corresponds to a way the build could be silently wrong. The one that
matters most is LEAK: if any target (temporal) edge can be reconstructed from the input
layer, the whole audit is circular and every downstream number is meaningless.

Usage:
    python verify_kg.py --split train
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent

ROOT = Path(__file__).resolve().parent.parent

SYMMETRIC = frozenset({"SIMULTANEOUS", "BEGINS-ON"})


class Check:
    def __init__(self):
        self.failures = []
        self.counts = Counter()

    def fail(self, name: str, detail: str):
        self.failures.append((name, detail))
        self.counts["FAIL/" + name] += 1

    def ok(self, name: str):
        self.counts["ok/" + name] += 1


def verify_document(rec: dict, c: Check) -> None:
    doc_id = rec["doc_id"]
    nodes = rec["nodes"]
    node_ids = set(nodes)

    # --- structural: no dangling endpoints anywhere -------------------------
    for layer in ("input_edges", "weak_edges", "target_edges"):
        for e in rec[layer]:
            if e["s"] not in node_ids:
                c.fail("dangling_source", f"{doc_id} {layer} {e['s']}")
            if e["t"] not in node_ids:
                c.fail("dangling_target", f"{doc_id} {layer} {e['t']}")
    c.ok("no_dangling")

    # --- LEAK: the input layer must not encode the target layer -------------
    # input edges connect events to anchors (entity/span); they must never connect
    # two events directly, which would be a temporal edge wearing another name.
    for e in rec["input_edges"]:
        s_kind = nodes[e["s"]]["kind"]
        t_kind = nodes[e["t"]]["kind"]
        if s_kind != "event":
            c.fail("input_source_not_event", f"{doc_id} {e['s']} is {s_kind}")
        if t_kind not in ("entity", "span"):
            c.fail("input_target_not_anchor", f"{doc_id} {e['t']} is {t_kind}")
    c.ok("input_layer_shape")

    # target edges must carry no attribute beyond the relation itself
    for e in rec["target_edges"]:
        if set(e) != {"s", "t", "rel"}:
            c.fail("target_edge_extra_fields", f"{doc_id} {sorted(e)}")
    c.ok("target_minimal")

    # anchored_pairs are derived from the input layer only: they must not mention
    # any relation label
    for p in rec["anchored_pairs"]:
        if any(k in p for k in ("rel", "relation", "label", "gold")):
            c.fail("pair_carries_label", f"{doc_id} {p['a']},{p['b']}")
    c.ok("pairs_label_free")

    # --- semantic: symmetric relations are canonicalised --------------------
    for e in rec["target_edges"]:
        if e["rel"] in SYMMETRIC and e["s"] > e["t"]:
            c.fail("symmetric_not_canonical", f"{doc_id} {e['rel']} {e['s']}>{e['t']}")
    c.ok("symmetric_canonical")

    # no ordered pair carries two different temporal labels
    seen = {}
    for e in rec["target_edges"]:
        key = (e["s"], e["t"])
        if key in seen and seen[key] != e["rel"]:
            c.fail("pair_two_labels", f"{doc_id} {key} {seen[key]}/{e['rel']}")
        seen[key] = e["rel"]
    c.ok("one_label_per_pair")

    # no self loops
    for layer in ("input_edges", "weak_edges", "target_edges"):
        for e in rec[layer]:
            if e["s"] == e["t"]:
                c.fail("self_loop", f"{doc_id} {layer} {e['s']}")
    c.ok("no_self_loop")

    # --- node invariants ----------------------------------------------------
    for nid, n in nodes.items():
        kind = n.get("kind")
        if kind == "timex":
            expect = n.get("timex_type") in ("DATE", "TIME")
            if n.get("anchorable") != expect:
                c.fail("timex_anchorable_wrong", f"{doc_id} {nid} {n.get('timex_type')}")
        elif kind == "event":
            if n.get("n_mentions", 0) < 1:
                c.fail("event_no_mention", f"{doc_id} {nid}")
            if n.get("sent_span", 0) > n.get("n_mentions", 0):
                c.fail("span_exceeds_mentions", f"{doc_id} {nid}")
        elif kind == "span":
            if not n.get("offset"):
                c.fail("span_no_offset", f"{doc_id} {nid}")
    c.ok("node_invariants")

    # --- anchored_pairs are consistent with input_edges ---------------------
    anchor_of = {}
    for e in rec["input_edges"]:
        anchor_of.setdefault(e["t"], set()).add(e["s"])
    for p in rec["anchored_pairs"]:
        for a_id in p["anchors"]:
            members = anchor_of.get(a_id, set())
            if p["a"] not in members or p["b"] not in members:
                c.fail("pair_anchor_mismatch", f"{doc_id} {p['a']},{p['b']} via {a_id}")
        if p["n_anchors"] != len(p["anchors"]):
            c.fail("n_anchors_wrong", f"{doc_id} {p['a']},{p['b']}")
        if not p["roles"]:
            c.fail("pair_no_roles", f"{doc_id} {p['a']},{p['b']}")
    c.ok("pairs_consistent")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="train")
    ap.add_argument("--graph-dir", type=Path, default=HERE / "graph")
    ap.add_argument("--show", type=int, default=10, help="failures to print per check")
    args = ap.parse_args()

    path = args.graph_dir / f"{args.split}.jsonl"
    c = Check()
    census = Counter()

    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            verify_document(rec, c)
            census["doc"] += 1
            for n in rec["nodes"].values():
                census["node/" + n["kind"]] += 1
            census["edge/input"] += len(rec["input_edges"])
            census["edge/weak"] += len(rec["weak_edges"])
            census["edge/target"] += len(rec["target_edges"])
            census["anchored_pair"] += len(rec["anchored_pairs"])
            for p in rec["anchored_pairs"]:
                census["pair_strength/" + p["strength"]] += 1

    print("CENSUS")
    for k in sorted(census):
        print(f"  {k:30s} {census[k]:>12,}")

    # Reconcile against the MAVEN-ERE source. A stale documented count for valid weak_edges
    # (10,712 instead of 12,524) survived for months because nothing compared the built KG
    # back to the corpus it came from; the number predated PRECONDITION joining CAUSAL_RELS.
    # Two discrepancies are expected and are NOT errors:
    #   temporal: the source stores BEGINS-ON in both directions, and build_kg canonicalises
    #             each pair to one edge (symmetric_canonical), so the KG is legitimately
    #             smaller -- 50 fewer on train, 4 on valid.
    src = HERE.parent.parent / "MAVEN_ERE" / f"{args.split}.jsonl"
    if src.exists():
        weak = Counter()
        with src.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                d = json.loads(line)
                cr = d.get("causal_relations")
                if isinstance(cr, dict):
                    for rel, lst in cr.items():
                        weak[rel] += len(lst)
                sub = d.get("subevent_relations")
                if isinstance(sub, list):
                    weak["SUBEVENT"] += len(sub)
        total = sum(weak.values())
        print("")
        print("SOURCE RECONCILIATION")
        for k in sorted(weak):
            print(f"  source weak/{k:22s} {weak[k]:>12,}")
        built = census["edge/weak"]
        mark = "OK" if built == total else "MISMATCH"
        print(f"  {'source weak total':30s} {total:>12,}")
        print(f"  {'built  weak total':30s} {built:>12,}   {mark}")
        if built != total:
            print(f"  -> weak_edges differs by {abs(total-built):,}. Unlike the temporal "
                  f"counts, weak edges are copied straight through, so any gap is a bug "
                  f"or a stale build -- not canonicalisation.")

    print("\nINVARIANTS")
    failed = Counter()
    for name, detail in c.failures:
        failed[name] += 1
    if not failed:
        checks = sorted({k.split("/", 1)[1] for k in c.counts if k.startswith("ok/")})
        for name in checks:
            print(f"  PASS  {name}")
        print("\nAll invariants hold.")
        return 0

    for name in sorted(failed):
        print(f"  FAIL  {name}: {failed[name]:,}")
        shown = 0
        for n, d in c.failures:
            if n == name and shown < args.show:
                print(f"          {d}")
                shown += 1
    print(f"\n{sum(failed.values()):,} invariant violations.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
