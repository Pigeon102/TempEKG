"""Build the two-layer temporal KG from MAVEN-ERE + MAVEN-Arg.

One JSONL line per document, self-contained. Layer 1 (property graph) is materialised
here; layer 2 (constraint network) is derived on demand by constraint_net.py.

Design decisions and the measurements behind them are in report/DEFINITIONS.md and
report/KG_BUILD.md. The load-bearing ones:

  - Event nodes are coreference CLUSTERS (96.4% are singletons, so the cluster/mention
    question is moot for almost all data; n_mentions and sent_span are kept as attributes
    so the 3.4% that span sentences can be filtered when it matters).
  - TIMEX is split by timex_type: DATE/TIME carry a position on the timeline (ANCHOR),
    DURATION does not (a length has no location). 79.9% are DATE.
  - Argument fillers without entity_id are NOT dropped: they are 59.6% of all fillers.
    They become Span nodes keyed by (doc_id, char offset), which gives a weaker but
    checkable anchor. Every HAS_ARG edge records which kind it is.
  - Edges are partitioned by epistemic role, not by source file: input / weak / target.
    TEMPORAL is the audit target and never enters input. CAUSAL and SUBEVENT are weak
    priors, not independent evidence: 95.2% of PRECONDITION and 90.7% of CAUSE pairs
    already carry a temporal label (MAVEN-ERE Sec 2.3 annotates causal only on pairs
    that already have BEFORE/OVERLAP).

ERE uses (sent_id, token offset); Arg uses character offsets into a joined document.
The two never need to be reconciled because both key events by the same EVENT_ id.

Usage:
    python build_kg.py --split train
    python build_kg.py --split valid --out graph/
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

ROOT = Path(__file__).resolve().parent.parent

TEMPORAL_RELS = ("BEFORE", "CONTAINS", "OVERLAP", "SIMULTANEOUS", "BEGINS-ON", "ENDS-ON")
CAUSAL_RELS = ("CAUSE", "PRECONDITION")

# B2: relations stored symmetrically must be mirrored on ingest and deduped.
SYMMETRIC = frozenset({"SIMULTANEOUS", "BEGINS-ON"})

# A1: DURATION is a length, not a position -- it gets no timeline coordinates.
ANCHOR_TIMEX_TYPES = frozenset({"DATE", "TIME"})


def span_id(offset) -> str:
    """Stable id for an argument filler that has no entity_id.

    Keyed on the character offset alone: two fillers at the same offset in the same
    document are the same span by construction, which is checkable rather than guessed.
    """
    return "SPAN_" + hashlib.md5(f"{offset[0]}:{offset[1]}".encode()).hexdigest()[:16]


def read_ere(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def read_arg(zip_path: Path, member: str) -> dict:
    out = {}
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(member) as fh:
            for line in io.TextIOWrapper(fh, encoding="utf-8"):
                if line.strip():
                    doc = json.loads(line)
                    out[doc["id"]] = doc
    return out


# FORMAL.md section 3 measured roleset and etypeset as the strongest view axes. All of these
# are computed from MAVEN-Arg arguments and node offsets only -- none of them reads
# temporal_relations, so none can leak the label being predicted.
PROFILE_KEYS = ("n_role", "roleset", "etypeset", "has_person", "has_org", "has_loc",
                "n_entity_arg", "n_span_arg")
EMPTY_PROFILE = {"n_role": 0, "roleset": [], "etypeset": [], "has_person": False,
                 "has_org": False, "has_loc": False, "n_entity_arg": 0, "n_span_arg": 0}


def argument_profile(arg_ev: dict, entity_types: dict, stats: Counter) -> dict:
    """Role and entity-type profile of one event, from its MAVEN-Arg arguments.

    roleset is the SET of argument roles; etypeset the SET of entity types those arguments
    resolve to. Both are sorted so the signature is order-independent and hashable.
    """
    roles, etypes = set(), set()
    n_entity = n_span = 0
    for role, fillers in (arg_ev.get("argument") or {}).items():
        for filler in fillers:
            roles.add(role)
            ent_id = filler.get("entity_id")
            if ent_id:
                n_entity += 1
                et = entity_types.get(ent_id)
                if et:
                    etypes.add(et)
            else:
                n_span += 1

    profile = {
        "n_role": len(roles),
        "roleset": sorted(roles),
        "etypeset": sorted(etypes),
        "has_person": "Person" in etypes,
        "has_org": "Organization" in etypes,
        "has_loc": "Location" in etypes,
        "n_entity_arg": n_entity,
        "n_span_arg": n_span,
    }
    stats["event_with_roles"] += 1 if roles else 0
    if len(roles) >= 2:
        stats["event_ge2_roles"] += 1
    return profile


def sent_bucket(sent_id) -> str:
    """Coarse position of the event in the document, as FORMAL.md T_event uses it."""
    if sent_id is None:
        return "unk"
    if sent_id == 0:
        return "lead"
    if sent_id <= 2:
        return "early"
    if sent_id <= 7:
        return "mid"
    return "late"


def build_event_nodes(ere_doc: dict, arg_doc: dict | None, entity_types: dict,
                      stats: Counter) -> dict:
    """Event clusters from ERE, enriched with Arg's type when the two disagree.

    7.15% of events carry a different type_id in Arg than in ERE. The L1 pattern key
    reads ERE's type; Arg's is kept as arg_type so the disagreement stays visible
    instead of being silently resolved.
    """
    arg_events = {e["id"]: e for e in (arg_doc or {}).get("events", [])}
    nodes = {}
    for ev in ere_doc.get("events") or []:
        mentions = ev.get("mention") or []
        sent_ids = [m["sent_id"] for m in mentions if m.get("sent_id") is not None]
        first = min(mentions, key=lambda m: (m.get("sent_id", 0), m.get("offset", [0])[0])) if mentions else None

        node = {
            "kind": "event",
            "type": ev.get("type"),
            "type_id": ev.get("type_id"),
            "n_mentions": len(mentions),
            "sent_span": len(set(sent_ids)) if sent_ids else 0,
            "sent_first": min(sent_ids) if sent_ids else None,
            "tok_first": first["offset"][0] if first and first.get("offset") else None,
            "trigger": first.get("trigger_word") if first else None,
            "sent_bucket": sent_bucket(min(sent_ids) if sent_ids else None),
        }

        arg_ev = arg_events.get(ev["id"])
        if arg_ev is not None:
            node["in_arg"] = True
            if arg_ev.get("type_id") != ev.get("type_id"):
                node["arg_type"] = arg_ev.get("type")
                node["arg_type_id"] = arg_ev.get("type_id")
                stats["event_type_disagreement"] += 1
            node.update(argument_profile(arg_ev, entity_types, stats))
        else:
            node["in_arg"] = False
            node.update(EMPTY_PROFILE)
            stats["event_not_in_arg"] += 1

        nodes[ev["id"]] = node
        stats["node_event"] += 1
        if node["sent_span"] > 1:
            stats["event_multi_sentence"] += 1
    return nodes


def build_timex_nodes(ere_doc: dict, stats: Counter) -> dict:
    nodes = {}
    for tx in ere_doc.get("TIMEX") or []:
        ttype = tx.get("type")
        is_anchor = ttype in ANCHOR_TIMEX_TYPES
        nodes[tx["id"]] = {
            "kind": "timex",
            "timex_type": ttype,
            # A1: anchors can take timeline coordinates; durations cannot.
            "anchorable": is_anchor,
            "text": tx.get("mention"),
            "sent_first": tx.get("sent_id"),
            "tok_first": (tx.get("offset") or [None])[0],
        }
        stats["node_timex"] += 1
        stats["timex_" + ("anchor" if is_anchor else "duration")] += 1
    return nodes


def build_arg_nodes_and_edges(arg_doc: dict | None, event_ids: set, stats: Counter):
    """Entity and Span nodes, plus the HAS_ARG edges that are the detector's input.

    Returns (nodes, edges). A filler with entity_id gives strength='entity';
    one without gives strength='span', keyed by character offset.
    """
    if not arg_doc:
        return {}, []

    nodes = {}
    for ent in arg_doc.get("entities") or []:
        mentions = [m.get("mention") for m in (ent.get("mention") or [])]
        nodes[ent["id"]] = {
            "kind": "entity",
            "ent_type": ent.get("type"),
            "n_mentions": len(mentions),
            "mentions": mentions[:5],
        }
        stats["node_entity"] += 1

    edges = []
    for ev in arg_doc.get("events") or []:
        if ev["id"] not in event_ids:
            # Present in Arg but not in ERE: no temporal target can attach, so it
            # cannot participate in a pattern. Skip rather than create a dangling node.
            stats["arg_event_not_in_ere"] += 1
            continue
        for role, fillers in (ev.get("argument") or {}).items():
            for filler in fillers:
                ent_id = filler.get("entity_id")
                if ent_id:
                    if ent_id not in nodes:
                        # Referenced but not declared in entities[]; keep it as a stub
                        # so the edge is not dangling.
                        nodes[ent_id] = {"kind": "entity", "ent_type": None,
                                         "n_mentions": 0, "mentions": [], "stub": True}
                        stats["entity_stub"] += 1
                    target, strength = ent_id, "entity"
                    stats["arg_filler_entity"] += 1
                else:
                    offset = filler.get("offset")
                    if not offset:
                        stats["arg_filler_dropped_no_offset"] += 1
                        continue
                    target = span_id(offset)
                    if target not in nodes:
                        nodes[target] = {
                            "kind": "span",
                            "offset": list(offset),
                            "content": (filler.get("content") or "")[:120],
                        }
                        stats["node_span"] += 1
                    strength = "span"
                    stats["arg_filler_span"] += 1

                edges.append({"s": ev["id"], "t": target, "role": role, "strength": strength})
    return nodes, edges


def build_relation_edges(ere_doc: dict, node_ids: set, stats: Counter):
    """Partition relations into target (temporal) and weak (causal, subevent).

    B2: SIMULTANEOUS and BEGINS-ON are symmetric and partly stored both ways; they are
    mirrored and deduped so orientation carries no spurious signal. The rest keep their
    stored orientation.
    """
    target, weak = [], []
    seen_temporal = set()

    for rel in TEMPORAL_RELS:
        for pair in (ere_doc.get("temporal_relations") or {}).get(rel) or []:
            a, b = pair[0], pair[1]
            if a not in node_ids or b not in node_ids:
                stats["temporal_dangling"] += 1
                continue
            if a == b:
                stats["temporal_self_loop"] += 1
                continue
            if rel in SYMMETRIC:
                key = (rel, min(a, b), max(a, b))
                if key in seen_temporal:
                    stats["temporal_symmetric_dedup"] += 1
                    continue
                seen_temporal.add(key)
                a, b = min(a, b), max(a, b)
            target.append({"s": a, "t": b, "rel": rel})
            stats["edge_temporal"] += 1
            stats["temporal_" + rel] += 1

    for rel in CAUSAL_RELS:
        for pair in (ere_doc.get("causal_relations") or {}).get(rel) or []:
            a, b = pair[0], pair[1]
            if a not in node_ids or b not in node_ids:
                stats["causal_dangling"] += 1
                continue
            weak.append({"s": a, "t": b, "kind": rel})
            stats["edge_causal"] += 1

    subevent = ere_doc.get("subevent_relations") or []
    if isinstance(subevent, dict):
        subevent = [p for v in subevent.values() for p in v]
    for pair in subevent:
        a, b = pair[0], pair[1]
        if a not in node_ids or b not in node_ids:
            stats["subevent_dangling"] += 1
            continue
        weak.append({"s": a, "t": b, "kind": "SUBEVENT"})
        stats["edge_subevent"] += 1

    return target, weak


def index_anchors(input_edges: list) -> dict:
    """anchor_id -> {event_id: [(role, strength), ...]}

    Materialised at build time so mining is a group-by rather than a graph traversal,
    and so the pattern keys are frozen on disk and reproducible.
    """
    idx = defaultdict(lambda: defaultdict(list))
    for e in input_edges:
        idx[e["t"]][e["s"]].append((e["role"], e["strength"]))
    return {a: dict(m) for a, m in idx.items() if len(m) >= 2}


def build_pair_keys(nodes: dict, anchors: dict, stats: Counter) -> list:
    """Every (event, event) pair that shares at least one anchor, with its pattern keys.

    Only anchored pairs are enumerated: ~80% of node pairs share no anchor and can never
    match an anchored pattern, so enumerating them all is wasted work.
    """
    shared = defaultdict(list)
    for anchor_id, members in anchors.items():
        ids = sorted(members)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                shared[(ids[i], ids[j])].append(anchor_id)

    out = []
    for (a, b), anchor_ids in shared.items():
        na, nb = nodes.get(a), nodes.get(b)
        if not na or not nb or na["kind"] != "event" or nb["kind"] != "event":
            continue

        roles = []
        strengths = set()
        for anchor_id in anchor_ids:
            for ra, sa in anchors[anchor_id][a]:
                for rb, sb in anchors[anchor_id][b]:
                    roles.append([ra, rb])
                    strengths.add(sa if sa == sb else "mixed")

        sa_, sb_ = na.get("sent_first"), nb.get("sent_first")
        sdist = abs(sa_ - sb_) if sa_ is not None and sb_ is not None else None
        ta, tb = na.get("tok_first"), nb.get("tok_first")
        if sa_ is not None and sb_ is not None and ta is not None and tb is not None:
            torder = "fwd" if (sa_, ta) <= (sb_, tb) else "rev"
        else:
            torder = None

        out.append({
            "a": a, "b": b,
            "anchors": anchor_ids,
            "n_anchors": len(anchor_ids),
            "roles": roles,
            "strength": ("entity" if strengths == {"entity"}
                         else "span" if strengths == {"span"} else "mixed"),
            "sdist": sdist,
            "torder": torder,
        })
        stats["anchored_pair"] += 1
    return out


def build_document(ere_doc: dict, arg_doc: dict | None, stats: Counter) -> dict:
    entity_types = {e["id"]: e.get("type")
                    for e in (arg_doc or {}).get("entities", [])}
    nodes = build_event_nodes(ere_doc, arg_doc, entity_types, stats)
    event_ids = set(nodes)
    nodes.update(build_timex_nodes(ere_doc, stats))

    arg_nodes, input_edges = build_arg_nodes_and_edges(arg_doc, event_ids, stats)
    nodes.update(arg_nodes)

    target_edges, weak_edges = build_relation_edges(ere_doc, set(nodes), stats)

    anchors = index_anchors(input_edges)
    pairs = build_pair_keys(nodes, anchors, stats)

    stats["doc"] += 1
    if arg_doc is None:
        stats["doc_without_arg"] += 1

    return {
        "doc_id": ere_doc["id"],
        "title": ere_doc.get("title"),
        "has_arg": arg_doc is not None,
        "nodes": nodes,
        "input_edges": input_edges,
        "weak_edges": weak_edges,
        "target_edges": target_edges,
        "anchored_pairs": pairs,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="train", choices=["train", "valid"])
    ap.add_argument("--ere-dir", type=Path, default=ROOT / "MAVEN_ERE")
    ap.add_argument("--arg-zip", type=Path, default=ROOT / "MAVEN-Arg.zip")
    ap.add_argument("--out", type=Path, default=HERE / "graph")
    ap.add_argument("--limit", type=int, default=0, help="stop after N documents (0 = all)")
    args = ap.parse_args()

    ere_path = args.ere_dir / f"{args.split}.jsonl"
    if not ere_path.exists():
        print(f"missing {ere_path}", file=sys.stderr)
        return 1

    print(f"loading MAVEN-Arg {args.split} ...", file=sys.stderr)
    arg_by_id = read_arg(args.arg_zip, f"{args.split}.jsonl")
    print(f"  {len(arg_by_id)} arg documents", file=sys.stderr)

    args.out.mkdir(parents=True, exist_ok=True)
    out_path = args.out / f"{args.split}.jsonl"

    stats = Counter()
    with out_path.open("w", encoding="utf-8") as out:
        for i, ere_doc in enumerate(read_ere(ere_path)):
            if args.limit and i >= args.limit:
                break
            record = build_document(ere_doc, arg_by_id.get(ere_doc["id"]), stats)
            out.write(json.dumps(record, ensure_ascii=False) + "\n")
            if (i + 1) % 500 == 0:
                print(f"  {i + 1} docs", file=sys.stderr)

    size_mb = out_path.stat().st_size / 1e6
    print(f"\nwrote {out_path}  ({size_mb:.1f} MB)\n", file=sys.stderr)

    stats_path = args.out / f"{args.split}.stats.json"
    stats_path.write_text(json.dumps(dict(sorted(stats.items())), indent=2), encoding="utf-8")

    print("BUILD STATISTICS", file=sys.stderr)
    for key in sorted(stats):
        print(f"  {key:34s} {stats[key]:>10,}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
