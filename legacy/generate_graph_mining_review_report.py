#!/usr/bin/env python3
"""Generate an auditable report for the Event-Centric Graph and one mined motif."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


TARGET_PATTERN = ("Motion", "Location_final", "Process_end", "Location")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def argument_entity_roles(event: dict[str, Any]) -> dict[str, list[str]]:
    roles: dict[str, list[str]] = {}
    for role, values in event.get("argument", {}).items():
        for value in values:
            if "entity_id" in value:
                roles.setdefault(value["entity_id"], []).append(role)
    return roles


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arg-path", type=Path, required=True)
    parser.add_argument("--ere-path", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    args = parser.parse_args()

    arg_documents = read_jsonl(args.arg_path)
    ere_documents = read_jsonl(args.ere_path)
    arg_by_id = {document["id"]: document for document in arg_documents}
    ere_by_id = {document["id"]: document for document in ere_documents}

    relation_distribution: Counter[str] = Counter()
    accepted_distribution: Counter[str] = Counter()
    excluded_missing_arg_event = 0
    excluded_type_id_mismatch = 0
    motif_matches: list[dict[str, str]] = []

    for ere_document in ere_documents:
        arg_document = arg_by_id.get(ere_document["id"])
        if not arg_document:
            continue
        arg_events = {event["id"]: event for event in arg_document["events"]}
        ere_events = {event["id"]: event for event in ere_document["events"]}
        entities = {entity["id"]: entity for entity in arg_document["entities"]}
        for relation, pairs in ere_document["temporal_relations"].items():
            relation_distribution[relation] += len(pairs)
            for event_1_id, event_2_id in pairs:
                if event_1_id not in arg_events or event_2_id not in arg_events:
                    excluded_missing_arg_event += 1
                    continue
                if event_1_id not in ere_events or event_2_id not in ere_events:
                    # In the current train data this is covered by the previous condition.
                    excluded_missing_arg_event += 1
                    continue
                event_1 = arg_events[event_1_id]
                event_2 = arg_events[event_2_id]
                if (
                    event_1["type_id"] != ere_events[event_1_id]["type_id"]
                    or event_2["type_id"] != ere_events[event_2_id]["type_id"]
                ):
                    excluded_type_id_mismatch += 1
                    continue
                accepted_distribution[relation] += 1
                roles_1 = argument_entity_roles(event_1)
                roles_2 = argument_entity_roles(event_2)
                for entity_id in set(roles_1) & set(roles_2):
                    for role_1 in roles_1[entity_id]:
                        for role_2 in roles_2[entity_id]:
                            pattern = (event_1["type"], role_1, event_2["type"], role_2)
                            if pattern == TARGET_PATTERN:
                                entity_mentions = ", ".join(
                                    mention["mention"] for mention in entities[entity_id].get("mention", [])
                                )
                                motif_matches.append(
                                    {
                                        "doc_id": ere_document["id"],
                                        "relation": relation,
                                        "event_1_id": event_1_id,
                                        "event_1_trigger": ", ".join(
                                            mention["trigger_word"] for mention in event_1["mention"]
                                        ),
                                        "event_2_id": event_2_id,
                                        "event_2_trigger": ", ".join(
                                            mention["trigger_word"] for mention in event_2["mention"]
                                        ),
                                        "shared_entity_id": entity_id,
                                        "shared_entity_mentions": entity_mentions,
                                    }
                                )

    motif_counts = Counter(match["relation"] for match in motif_matches)
    support = len(motif_matches)
    before_confidence = motif_counts["BEFORE"] / support if support else 0.0
    example = next(match for match in motif_matches if match["relation"] == "BEFORE")
    lines = [
        "# Event-Centric Graph and Motif-Mining Review Report",
        "",
        "## Scope and inputs",
        "",
        "This report is reproducible from the two train files only:",
        "",
        f"- MAVEN-Arg: `{args.arg_path}`",
        f"- MAVEN-ERE: `{args.ere_path}`",
        "",
        "No train/dev/test labels were mixed. The report describes alignment, a document-level Event-Centric Graph, and one structural motif; it does not implement a general temporal miner.",
        "",
        "## Alignment and usable temporal pairs",
        "",
        f"- Documents: MAVEN-Arg={len(arg_documents)}, MAVEN-ERE={len(ere_documents)}, matched={len(set(arg_by_id) & set(ere_by_id))}.",
        "- Alignment key: `doc_id + EVENT_* id`, validated by equal `type_id` in both datasets.",
        f"- All MAVEN-ERE temporal pairs: {sum(relation_distribution.values()):,}.",
        f"- Retained pairs: {sum(accepted_distribution.values()):,}.",
        f"- Excluded because an endpoint is absent from MAVEN-Arg event clusters: {excluded_missing_arg_event:,}.",
        f"- Excluded because an aligned endpoint has a `type_id` mismatch: {excluded_type_id_mismatch:,}.",
        "",
        "### Temporal-label distribution",
        "",
        "| Relation | All MAVEN-ERE pairs | Retained aligned pairs |",
        "|---|---:|---:|",
    ]
    for relation in sorted(relation_distribution):
        lines.append(
            f"| {relation} | {relation_distribution[relation]:,} | {accepted_distribution[relation]:,} |"
        )

    lines.extend(
        [
            "",
            "## Stored Event-Centric Graph",
            "",
            "Store one heterogeneous graph per document. Event clusters are central nodes. The temporal relation under prediction is stored separately from input edges.",
            "",
            "| Node type | Source fields | Key attributes |",
            "|---|---|---|",
            "| `document` | `id`, `title` | `doc_id`, title |",
            "| `event` | MAVEN-Arg/MAVEN-ERE `events` | event ID, type, type ID, trigger mentions |",
            "| `entity` | MAVEN-Arg `entities` | entity ID, entity type, mentions |",
            "| `argument_span` | MAVEN-Arg event arguments without `entity_id` | text, character offset |",
            "",
            "| Edge type | Source → target | Properties |",
            "|---|---|---|",
            "| `HAS_EVENT` | document → event | — |",
            "| `HAS_ARGUMENT` | event → entity or argument span | argument role, e.g. `Agent`, `Location` |",
            "| temporal target | event → event | label such as `BEFORE`; excluded from input when that pair is masked |",
            "",
            "Recommended record shape:",
            "",
            "```json",
            '{"doc_id":"…","nodes":[…],"input_edges":[…],"temporal_targets":[{"source":"event:E1","target":"event:E2","relation":"BEFORE"}]}',
            "```",
            "",
            "The prototype graph artifact is `event_temporal_mining/data/processed/graph_demo/event_centric_graph_sample.json`. It contains a temporal edge solely for illustration and marks it `available_to_pattern_extractor_when_masked: false`.",
            "",
            "## Audited structural motif",
            "",
            "Pattern signature, with the raw entity ID abstracted to variable `x`:",
            "",
            "```text",
            "E1(type=Motion)      --Location_final--> x",
            "E2(type=Process_end) --Location-------> x",
            "```",
            "",
            "Only direct MAVEN-Arg `entity_id` sharing is considered shared-entity evidence. Identical raw argument strings are not promoted to entity identity.",
            "",
            f"- Support: {support}",
            f"- `BEFORE`: {motif_counts['BEFORE']}",
            f"- `CONTAINS`: {motif_counts['CONTAINS']}",
            f"- Constraint confidence `P → BEFORE`: {motif_counts['BEFORE']}/{support} = {before_confidence:.2f}",
            "",
            "For a masked pair, extract this motif using only node types and `HAS_ARGUMENT` edges. Look up its train-derived relation counts and predict the relation with the largest count. The masked pair's temporal target is never an input feature.",
            "",
            "### Representative occurrence",
            "",
            f"- Document: `{example['doc_id']}`",
            f"- `Motion` event: `{example['event_1_id']}` — trigger `{example['event_1_trigger']}`",
            f"- `Process_end` event: `{example['event_2_id']}` — trigger `{example['event_2_trigger']}`",
            f"- Shared entity: `{example['shared_entity_id']}` — `{example['shared_entity_mentions']}`",
            f"- Gold relation: `{example['relation']}`",
            "",
            "## Full occurrence list for this motif",
            "",
            "Every row is one motif occurrence. Check its event IDs in both train JSONL files and its temporal label in `MAVEN_ERE/train.jsonl`.",
            "",
            "| # | doc_id | Relation | Motion event | Process-end event | Shared entity |",
            "|---:|---|---|---|---|---|",
        ]
    )
    for index, match in enumerate(motif_matches, start=1):
        lines.append(
            "| {index} | `{doc_id}` | {relation} | `{event_1_id}` ({event_1_trigger}) | "
            "`{event_2_id}` ({event_2_trigger}) | `{shared_entity_id}` ({shared_entity_mentions}) |".format(
                index=index, **match
            )
        )
    lines.extend(
        [
            "",
            "## Reproduce",
            "",
            "```bash",
            "python3 event_temporal_mining/src/generate_graph_mining_review_report.py \\",
            "  --arg-path MAVEN-Arg/train.jsonl \\",
            "  --ere-path MAVEN_ERE/train.jsonl \\",
            "  --output-path event_temporal_mining/results/graph_mining_review_report.md",
            "```",
            "",
        ]
    )
    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output_path} with {support} motif occurrences.")


if __name__ == "__main__":
    main()
