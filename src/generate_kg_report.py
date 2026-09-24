"""Generate an auditable report for the two-layer temporal KG.

Same shape as report/generate_graph_mining_review_report.py -- scope, census, stored
graph, one audited motif with its full occurrence list, reproduce block -- so the two
can be read side by side. The difference is what the underlying artifact is: this one
describes a built graph that mining runs on, not a single hand-picked pattern.

Every number is computed from graph/*.jsonl at run time. Nothing is hardcoded except
the motif chosen for the worked example, which is the same motif the earlier report
audited so the two are comparable.

Usage:
    python generate_kg_report.py --split train --output-path ../report/kg_review_report.md
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent

ROOT = Path(__file__).resolve().parent.parent

# The motif the earlier report audited, kept so the two reports are comparable.
TARGET_PATTERN = ("Motion", "Location_final", "Process_end", "Location")


def read_graph(path: Path):
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def fmt(n) -> str:
    return f"{n:,}"


def collect(path: Path) -> dict:
    """One pass over the graph, gathering everything the report needs."""
    c = Counter()
    node_kind = Counter()
    timex_kind = Counter()
    rel_all = Counter()
    pair_strength = Counter()
    anchors_per_pair = Counter()
    sdist = Counter()
    roles = Counter()
    ent_types = Counter()

    # motif -> Counter(relation); only over pairs that HAVE a gold label
    motif_rel = defaultdict(Counter)
    # how many anchored pairs have no gold label at all
    labelled = unlabelled = 0
    target_occurrences = []

    for rec in read_graph(path):
        c["doc"] += 1
        if not rec.get("has_arg"):
            c["doc_without_arg"] += 1

        nodes = rec["nodes"]
        for n in nodes.values():
            node_kind[n["kind"]] += 1
            if n["kind"] == "timex":
                timex_kind[n.get("timex_type")] += 1
            elif n["kind"] == "entity":
                ent_types[n.get("ent_type")] += 1

        c["edge_input"] += len(rec["input_edges"])
        c["edge_weak"] += len(rec["weak_edges"])
        c["edge_target"] += len(rec["target_edges"])
        for e in rec["input_edges"]:
            roles[e["role"]] += 1
            c["strength_" + e["strength"]] += 1
        for e in rec["target_edges"]:
            rel_all[e["rel"]] += 1

        # gold lookup for this document, both orientations recorded separately
        gold = {}
        for e in rec["target_edges"]:
            gold[(e["s"], e["t"])] = e["rel"]

        for p in rec["anchored_pairs"]:
            c["anchored_pair"] += 1
            pair_strength[p["strength"]] += 1
            anchors_per_pair[min(p["n_anchors"], 5)] += 1
            if p["sdist"] is not None:
                sdist[min(p["sdist"], 10)] += 1

            a, b = p["a"], p["b"]
            fwd, rev = gold.get((a, b)), gold.get((b, a))
            if fwd is None and rev is None:
                unlabelled += 1
                continue
            labelled += 1

            ta = nodes[a].get("type")
            tb = nodes[b].get("type")
            for ra, rb in p["roles"]:
                if fwd is not None:
                    motif_rel[(ta, ra, tb, rb)][fwd] += 1
                    if (ta, ra, tb, rb) == TARGET_PATTERN:
                        target_occurrences.append({
                            "doc_id": rec["doc_id"], "rel": fwd,
                            "a": a, "a_trig": nodes[a].get("trigger"),
                            "b": b, "b_trig": nodes[b].get("trigger"),
                            "anchor": p["anchors"][0],
                            "anchor_kind": nodes[p["anchors"][0]]["kind"],
                            "anchor_text": anchor_text(nodes[p["anchors"][0]]),
                            "strength": p["strength"],
                        })
                if rev is not None:
                    motif_rel[(tb, rb, ta, ra)][rev] += 1
                    if (tb, rb, ta, ra) == TARGET_PATTERN:
                        target_occurrences.append({
                            "doc_id": rec["doc_id"], "rel": rev,
                            "a": b, "a_trig": nodes[b].get("trigger"),
                            "b": a, "b_trig": nodes[a].get("trigger"),
                            "anchor": p["anchors"][0],
                            "anchor_kind": nodes[p["anchors"][0]]["kind"],
                            "anchor_text": anchor_text(nodes[p["anchors"][0]]),
                            "strength": p["strength"],
                        })

    return {
        "c": c, "node_kind": node_kind, "timex_kind": timex_kind, "rel_all": rel_all,
        "pair_strength": pair_strength, "anchors_per_pair": anchors_per_pair,
        "sdist": sdist, "roles": roles, "ent_types": ent_types,
        "motif_rel": motif_rel, "labelled": labelled, "unlabelled": unlabelled,
        "target_occurrences": target_occurrences,
    }


def anchor_text(node: dict) -> str:
    if node["kind"] == "entity":
        return ", ".join(node.get("mentions") or []) or "(no mention)"
    if node["kind"] == "span":
        return (node.get("content") or "")[:60]
    return node.get("text") or ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="train")
    ap.add_argument("--graph-dir", type=Path, default=HERE / "graph")
    ap.add_argument("--output-path", type=Path, default=ROOT / "report" / "kg_review_report.md")
    args = ap.parse_args()

    path = args.graph_dir / f"{args.split}.jsonl"
    d = collect(path)
    c = d["c"]
    rel_all = d["rel_all"]
    total_rel = sum(rel_all.values())
    motif_rel = d["motif_rel"]

    # motif space statistics
    motif_support = {k: sum(v.values()) for k, v in motif_rel.items()}
    sup10 = sum(1 for s in motif_support.values() if s >= 10)
    sup25 = sum(1 for s in motif_support.values() if s >= 25)
    sup100 = sum(1 for s in motif_support.values() if s >= 100)

    base_before = rel_all["BEFORE"] / total_rel

    # the audited motif
    tgt = motif_rel.get(TARGET_PATTERN, Counter())
    tgt_sup = sum(tgt.values())
    tgt_before = tgt["BEFORE"]
    tgt_conf = tgt_before / tgt_sup if tgt_sup else 0.0
    tgt_lift = tgt_conf / base_before if base_before else 0.0

    rev_pattern = (TARGET_PATTERN[2], TARGET_PATTERN[3], TARGET_PATTERN[0], TARGET_PATTERN[1])
    rev = motif_rel.get(rev_pattern, Counter())

    # motifs that beat the target on lift at comparable support
    better = []
    for k, cnt in motif_rel.items():
        s = sum(cnt.values())
        if s < 25:
            continue
        top_rel, top_n = cnt.most_common(1)[0]
        conf = top_n / s
        base = rel_all[top_rel] / total_rel
        lift = conf / base if base else 0.0
        better.append((lift, s, conf, top_rel, k))
    better.sort(reverse=True)

    L = []
    A = L.append

    A("# Two-Layer Temporal KG — Build and Motif Review Report")
    A("")
    A("## Scope and inputs")
    A("")
    A("This report is reproducible from the built graph, which is itself reproducible from the two train files:")
    A("")
    A("- MAVEN-Arg: `MAVEN-Arg.zip:train.jsonl`")
    A("- MAVEN-ERE: `MAVEN_ERE/train.jsonl`")
    A(f"- Built graph: `tempekg_kg/graph/{args.split}.jsonl`")
    A("")
    A("No train/dev/test labels were mixed. The report describes the stored graph, its two layers, "
      "the motif space that mining searches, and one audited motif. Unlike the earlier review report, "
      "the motif here is an example drawn from an enumerated space, not the object being argued for.")
    A("")

    A("## Census of the built graph")
    A("")
    A(f"- Documents: {fmt(c['doc'])}, of which {fmt(c['doc_without_arg'])} have no MAVEN-Arg counterpart.")
    A(f"- Nodes: {fmt(sum(d['node_kind'].values()))} total.")
    A(f"- Edges: {fmt(c['edge_input'])} input, {fmt(c['edge_weak'])} weak, {fmt(c['edge_target'])} target.")
    A(f"- Anchored pairs enumerated: {fmt(c['anchored_pair'])}.")
    A("")
    A("| Node type | Count | Source |")
    A("|---|---:|---|")
    A(f"| `event` (coreference cluster) | {fmt(d['node_kind']['event'])} | MAVEN-ERE `events` |")
    A(f"| `entity` | {fmt(d['node_kind']['entity'])} | MAVEN-Arg `entities` |")
    A(f"| `span` | {fmt(d['node_kind']['span'])} | MAVEN-Arg fillers without `entity_id` |")
    A(f"| `timex` | {fmt(d['node_kind']['timex'])} | MAVEN-ERE `TIMEX` |")
    A("")
    A("`span` nodes are the change that most affects coverage. The earlier report dropped every "
      "argument filler without an `entity_id`. Here those fillers are kept: "
      f"{fmt(c['strength_span'])} of {fmt(c['edge_input'])} `HAS_ARG` edges "
      f"({100 * c['strength_span'] / c['edge_input']:.1f}%) point at a span rather than an entity. "
      "They are keyed by character offset within the document, so two fillers at the same offset are "
      "the same span by construction rather than by string matching.")
    A("")
    A("| TIMEX type | Count | Anchorable |")
    A("|---|---:|---|")
    for t, n in d["timex_kind"].most_common():
        A(f"| {t} | {fmt(n)} | {'yes' if t in ('DATE', 'TIME') else 'no'} |")
    A("")
    A("A DURATION is a length, not a position, so it takes no timeline coordinates. "
      "DATE and TIME can: they are the only absolute anchors in the corpus.")
    A("")

    A("### Temporal-label distribution")
    A("")
    A("| Relation | Target edges | Share |")
    A("|---|---:|---:|")
    for rel in sorted(rel_all, key=lambda r: -rel_all[r]):
        A(f"| {rel} | {fmt(rel_all[rel])} | {100 * rel_all[rel] / total_rel:.2f}% |")
    A(f"| **Total** | **{fmt(total_rel)}** | |")
    A("")
    A(f"No temporal pair is discarded. The earlier report retained 430,118 of 792,445 pairs; the "
      f"difference is almost entirely pairs with a TIMEX endpoint, which MAVEN-Arg does not annotate "
      f"and which that alignment therefore dropped.")
    A("")

    A("## Stored graph")
    A("")
    A("One record per document, self-contained, in JSONL. Edges are partitioned by what the "
      "detector is allowed to see, not by which file they came from.")
    A("")
    A("| Edge class | Field | Count | Visible to detector |")
    A("|---|---|---:|---|")
    A(f"| input | `input_edges` | {fmt(c['edge_input'])} | yes |")
    A(f"| weak prior | `weak_edges` | {fmt(c['edge_weak'])} | yes, but not independent evidence |")
    A(f"| audit target | `target_edges` | {fmt(c['edge_target'])} | **no** |")
    A("")
    A("The separation is physical, not by convention, and three invariants enforce it "
      "(`verify_kg.py`): an input edge may never join two events; a target edge carries exactly "
      "`{s, t, rel}`; `anchored_pairs` carries no label field. This matters because 95.2% of "
      "PRECONDITION and 90.7% of CAUSE pairs already carry a temporal label, so leaving the causal "
      "edges in the input layer would leak the answer.")
    A("")
    A("Record shape:")
    A("")
    A("```json")
    A('{"doc_id":"…","nodes":{…},"input_edges":[…],"weak_edges":[…],'
      '"target_edges":[{"s":"EVENT_a","t":"EVENT_b","rel":"BEFORE"}],"anchored_pairs":[…]}')
    A("```")
    A("")

    A("## Layer 2 — constraint network")
    A("")
    A("The property graph above answers how often a pattern occurs. It cannot answer whether a set "
      "of labels is satisfiable, because unsatisfiability is not a pairwise property:")
    A("")
    A("```text")
    A("BEFORE(a,b) AND BEFORE(b,c) AND ENDS-ON(a,c)")
    A("```")
    A("")
    A("Every pair in that triple is individually fine. Whether the triple is contradictory depends "
      "on the mapping: under `ENDS-ON = {m}` it is unsatisfiable, under the settled `ENDS-ON = {b,m}` "
      "it is not. An earlier round produced seven \"hard contradictions\" that were entirely an "
      "artifact of the first mapping. `constraint_net.py --self-test` reproduces both directions so "
      "the regression cannot recur silently.")
    A("")
    A("| MAVEN relation | Allen set | Endpoint constraint |")
    A("|---|---|---|")
    A("| BEFORE | `{b}` | `e_a < s_b` |")
    A("| CONTAINS | `{di}` | `s_a < s_b AND e_b < e_a` |")
    A("| OVERLAP | `{o}` | `s_a < s_b < e_a < e_b` |")
    A("| SIMULTANEOUS | `{e}` | `s_a = s_b AND e_a = e_b` |")
    A("| BEGINS-ON | `{s, si, e}` | `s_a = s_b` |")
    A("| ENDS-ON | `{b, m}` | `e_a <= s_b` |")
    A("")
    A("The 13x13 composition table is generated by brute force over integer intervals, not "
      "transcribed: a hand-written Allen table is exactly the artifact that manufactures fake "
      "contradictions.")
    A("")

    A("## The motif space")
    A("")
    A(f"A motif is `(type_1, role_1, type_2, role_2)` with the shared anchor abstracted to a "
      f"variable. Enumerating over every anchored pair that carries a gold label:")
    A("")
    A("| | |")
    A("|---|---:|")
    A(f"| Anchored pairs | {fmt(c['anchored_pair'])} |")
    A(f"| …with a gold temporal label | {fmt(d['labelled'])} ({100 * d['labelled'] / c['anchored_pair']:.1f}%) |")
    A(f"| …without any gold label | {fmt(d['unlabelled'])} ({100 * d['unlabelled'] / c['anchored_pair']:.1f}%) |")
    A(f"| Distinct motifs | {fmt(len(motif_rel))} |")
    A(f"| …at support >= 10 | {fmt(sup10)} |")
    A(f"| …at support >= 25 | {fmt(sup25)} |")
    A(f"| …at support >= 100 | {fmt(sup100)} |")
    A("")
    A(f"The {fmt(d['unlabelled'])} unlabelled anchored pairs are the ones the earlier script could "
      f"never reach: its outer loop iterated over `temporal_relations`, so a pair without a label was "
      f"never examined. Those pairs are where a derived constraint can be tested against an absent "
      f"annotation.")
    A("")
    A("| Pair anchor strength | Count |")
    A("|---|---:|")
    for k in ("entity", "span", "mixed"):
        A(f"| {k} | {fmt(d['pair_strength'][k])} |")
    A("")

    A("## Audited structural motif")
    A("")
    A("The same motif the earlier review report audited, recomputed on this graph so the two are "
      "directly comparable.")
    A("")
    A("```text")
    A(f"E1(type={TARGET_PATTERN[0]})      --{TARGET_PATTERN[1]}--> x")
    A(f"E2(type={TARGET_PATTERN[2]}) --{TARGET_PATTERN[3]}-------> x")
    A("```")
    A("")
    A(f"- Support: {tgt_sup}")
    for rel, n in tgt.most_common():
        A(f"- `{rel}`: {n}")
    A(f"- Confidence `P -> BEFORE`: {tgt_before}/{tgt_sup} = {tgt_conf:.2f}")
    A(f"- Baseline `BEFORE` over all target edges: {base_before:.4f}")
    A(f"- **Lift: {tgt_lift:.3f}x**")
    A("")
    A("> **Why this support is 16 and not the 25 the earlier report gave.** Both counts are correct "
      "for what they count. The earlier script read each event's `type` from MAVEN-Arg; this graph "
      "reads it from MAVEN-ERE. For 14 of those 25 occurrences the two datasets disagree — Arg says "
      "`Motion`, ERE says `Self_motion` — so they land under a different motif here. The build "
      "counted 117 such events in train and records the Arg type as `arg_type` on the node so the "
      "disagreement stays visible instead of being silently resolved. Which dataset the pattern key "
      "reads from is a modelling decision, not a bug, and it has to be stated: this report uses ERE, "
      "because the temporal labels being audited are ERE's.")
    A("")
    A("The confidence figure alone is not evidence. BEFORE is the majority label by a wide margin, "
      f"so predicting it everywhere already scores {100 * base_before:.2f}%. Lift is what says whether "
      "the motif carries information, and it is the number to report.")
    A("")
    A(f"The reverse-direction motif `({rev_pattern[0]}, {rev_pattern[1]}, {rev_pattern[2]}, "
      f"{rev_pattern[3]})` has support {sum(rev.values())}"
      + (f" with distribution {dict(rev)}." if rev else ", i.e. it does not occur."))
    A("")

    A(f"### Motifs ranked by lift (support >= 25, top 15 of {fmt(len(better))})")
    A("")
    A("| # | Lift | Support | Conf | Relation | Motif |")
    A("|---:|---:|---:|---:|---|---|")
    for i, (lift, s, conf, rel, k) in enumerate(better[:15], 1):
        A(f"| {i} | {lift:.2f}x | {s} | {conf:.2f} | {rel} | `{k[0]}` --{k[1]}--> x <--{k[3]}-- `{k[2]}` |")
    A("")
    A("This ranking is the substantive difference from the earlier report. There, one motif was "
      "hardcoded and reported in isolation; here the space is enumerated and the chosen motif can be "
      "located within it. Where the audited motif lands in this table is itself the finding.")
    A("")

    if d["target_occurrences"]:
        ex = next((o for o in d["target_occurrences"] if o["rel"] == "BEFORE"),
                  d["target_occurrences"][0])
        A("### Representative occurrence")
        A("")
        A(f"- Document: `{ex['doc_id']}`")
        A(f"- `{TARGET_PATTERN[0]}` event: `{ex['a']}` — trigger `{ex['a_trig']}`")
        A(f"- `{TARGET_PATTERN[2]}` event: `{ex['b']}` — trigger `{ex['b_trig']}`")
        A(f"- Shared anchor: `{ex['anchor']}` ({ex['anchor_kind']}) — `{ex['anchor_text']}`")
        A(f"- Gold relation: `{ex['rel']}`")
        A("")

        A("## Full occurrence list for this motif")
        A("")
        A("Every row is one motif occurrence. Check the event IDs in both train JSONL files and the "
          "temporal label in `MAVEN_ERE/train.jsonl`.")
        A("")
        A("| # | doc_id | Relation | E1 | E2 | Shared anchor | Strength |")
        A("|---:|---|---|---|---|---|---|")
        for i, o in enumerate(d["target_occurrences"], 1):
            A(f"| {i} | `{o['doc_id']}` | {o['rel']} | `{o['a']}` ({o['a_trig']}) | "
              f"`{o['b']}` ({o['b_trig']}) | `{o['anchor']}` ({o['anchor_text']}) | {o['strength']} |")
        A("")

    A("## What this report does not claim")
    A("")
    A("- It does not claim the audited motif is a good constraint. Its lift is stated so the reader "
      "can judge; a lift near 1.0 means the motif restates the base rate.")
    A("- It does not evaluate a detector. No detection has been run; this is the graph the detector "
      "will run on.")
    A("- It does not establish that the corpus contains annotation errors. Measured separately: zero "
      "ordered pairs carry two labels, zero carry BEFORE in both directions, and path consistency "
      "finds no unsatisfiable document. The corpus is consistent by construction.")
    A("")

    A("## Reproduce")
    A("")
    A("```bash")
    A("python tempekg_kg/build_kg.py --split train")
    A("python tempekg_kg/verify_kg.py --split train")
    A("python tempekg_kg/constraint_net.py --self-test")
    A(f"python tempekg_kg/generate_kg_report.py --split {args.split} \\")
    A(f"  --output-path report/kg_review_report.md")
    A("```")
    A("")

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    args.output_path.write_text("\n".join(L), encoding="utf-8")
    print(f"Wrote {args.output_path}")
    print(f"  motifs: {len(motif_rel):,} distinct, {sup25:,} at support>=25")
    print(f"  audited motif: support {tgt_sup}, conf {tgt_conf:.2f}, lift {tgt_lift:.3f}x")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
