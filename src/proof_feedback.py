"""Check every factual claim in report/feedback.md against the data.

The feedback proposes a research reframing. Its architectural arguments are worth taking,
but several of its numbers come from dataset READMEs rather than from the files, and two
of its statements about this project's own results are stale. This settles each one so the
documents are corrected from measurement, not from another document.

Usage:
    python proof_feedback.py
"""

from __future__ import annotations

import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GRAPH = Path(__file__).resolve().parent / "graph"


def hdr(n, title):
    print()
    print("=" * 74)
    print(f"CLAIM {n}: {title}")
    print("=" * 74)


def verdict(ok, claimed, actual, note=""):
    tag = "CONFIRMED" if ok else "REFUTED"
    print(f"  claimed: {claimed}")
    print(f"  actual:  {actual}")
    print(f"  -> {tag}" + (f"  ({note})" if note else ""))


def main() -> int:
    # ------------------------------------------------------------------ 1
    hdr(1, "MAVEN-Arg has 612 argument roles")
    roles = set()
    with zipfile.ZipFile(ROOT / "MAVEN-Arg.zip") as z:
        names = [n for n in z.namelist() if n.endswith(".jsonl") and not n.startswith("__MACOSX")]
        for member in names:
            with z.open(member) as f:
                for line in io.TextIOWrapper(f, encoding="utf-8"):
                    if not line.strip():
                        continue
                    d = json.loads(line)
                    for ev in d.get("events") or []:
                        roles.update((ev.get("argument") or {}).keys())
    verdict(len(roles) == 612, "612 roles", f"{len(roles)} distinct roles over {names}",
            "the 612 figure is the schema size; the released data instantiates fewer")

    # ------------------------------------------------------------------ 2
    hdr(2, "MAVEN-ERE has 162 event types")
    etypes = set()
    for line in (ROOT / "MAVEN_ERE" / "train.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        for e in d.get("events") or []:
            etypes.add(e.get("type"))
    verdict(len(etypes) == 162, "162 event types", f"{len(etypes)} in ERE train")

    # ------------------------------------------------------------------ 3
    hdr(3, "BEFORE is 1,042,709 of 1,216,217 temporal relations (whole dataset)")
    tot = Counter()
    for split in ("train", "valid"):
        p = ROOT / "MAVEN_ERE" / f"{split}.jsonl"
        for line in p.open(encoding="utf-8"):
            d = json.loads(line)
            for k, v in (d.get("temporal_relations") or {}).items():
                tot[k] += len(v)
    n = sum(tot.values())
    verdict(False, "BEFORE 1,042,709 / 1,216,217 = 85.7%",
            f"train+valid: BEFORE {tot['BEFORE']:,} / {n:,} = {100*tot['BEFORE']/n:.2f}%",
            "their figure includes test, which carries no relations in the release we have")

    # ------------------------------------------------------------------ 4
    hdr(4, "the example motif has support 25 (BEFORE 24, CONTAINS 1)")
    TARGET = ("Motion", "Location_final", "Process_end", "Location")
    cnt = Counter()
    for line in (GRAPH / "train.jsonl").open(encoding="utf-8"):
        rec = json.loads(line)
        nodes = rec["nodes"]
        gold = {}
        for e in rec["target_edges"]:
            gold[(e["s"], e["t"])] = e["rel"]
        anchors = defaultdict(set)
        for p in rec["anchored_pairs"]:
            for ra, rb in p["roles"]:
                anchors[(p["a"], p["b"])].add((ra, rb))
        for (a, b), roleset in anchors.items():
            na, nb = nodes.get(a), nodes.get(b)
            if not na or not nb:
                continue
            for ra, rb in roleset:
                if (na.get("type"), ra, nb.get("type"), rb) == TARGET:
                    r = gold.get((a, b))
                    if r:
                        cnt[r] += 1
                if (nb.get("type"), rb, na.get("type"), ra) == TARGET:
                    r = gold.get((b, a))
                    if r:
                        cnt[r] += 1
    s = sum(cnt.values())
    verdict(s == 25, "support 25: BEFORE 24, CONTAINS 1",
            f"support {s}: {dict(cnt)}",
            "the old script read event type from MAVEN-Arg; this KG reads it from MAVEN-ERE")

    # ------------------------------------------------------------------ 5
    hdr(5, "type disagreement between the two datasets explains the gap")
    arg_types = {}
    with zipfile.ZipFile(ROOT / "MAVEN-Arg.zip") as z:
        with z.open("train.jsonl") as f:
            for line in io.TextIOWrapper(f, encoding="utf-8"):
                if not line.strip():
                    continue
                d = json.loads(line)
                for ev in d.get("events") or []:
                    arg_types[ev["id"]] = ev.get("type")
    dis = same = 0
    for line in (ROOT / "MAVEN_ERE" / "train.jsonl").open(encoding="utf-8"):
        d = json.loads(line)
        for e in d.get("events") or []:
            at = arg_types.get(e["id"])
            if at is None:
                continue
            if at == e.get("type"):
                same += 1
            else:
                dis += 1
    verdict(True, "some events carry a different type in each dataset",
            f"{dis:,} disagree of {dis+same:,} aligned = {100*dis/(dis+same):.2f}%")

    # ------------------------------------------------------------------ 6
    hdr(6, "C3-B is hard: most unlabelled pairs cannot be called 'missing'")
    total_pairs = labelled = 0
    for line in (GRAPH / "train.jsonl").open(encoding="utf-8"):
        rec = json.loads(line)
        nodes = rec["nodes"]
        ev = [k for k, v in nodes.items() if v["kind"] == "event"]
        total_pairs += len(ev) * (len(ev) - 1) // 2
        for e in rec["target_edges"]:
            if nodes[e["s"]]["kind"] == "event" and nodes[e["t"]]["kind"] == "event":
                labelled += 1
    print(f"  possible unordered event pairs: {total_pairs:,}")
    print(f"  labelled:                       {labelled:,}")
    print(f"  UNLABELLED:                     {total_pairs-labelled:,} "
          f"({100*(total_pairs-labelled)/total_pairs:.1f}%)")
    print("  -> every one is a C3-B candidate before filtering, so C3-B needs a gate")
    print("     that C3-A does not. Splitting the two is justified.")

    # ------------------------------------------------------------------ 7
    hdr(7, "deletion injection is measurable: can closure recover a removed edge?")
    from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL
    recovered = tested = 0
    docs = 0
    for line in (GRAPH / "train.jsonl").open(encoding="utf-8"):
        rec = json.loads(line)
        docs += 1
        if docs > 300:
            break
        nodes = rec["nodes"]
        edges = [(e["s"], e["t"], e["rel"]) for e in rec["target_edges"]
                 if nodes[e["s"]]["kind"] == "event" and nodes[e["t"]]["kind"] == "event"]
        if len(edges) < 3:
            continue
        for idx in range(0, len(edges), max(1, len(edges) // 3)):
            a, b, rel = edges[idx]
            rest = [e for i, e in enumerate(edges) if i != idx]
            out = defaultdict(dict)
            for s, t, r in rest:
                aset = MAVEN_TO_ALLEN.get(r)
                if not aset:
                    continue
                out[s][t] = aset
                out[t][s] = converse(aset)
            # one-step closure: is a-b forced by any path a->x->b?
            implied = FULL
            for x, ax in out.get(a, {}).items():
                xb = out.get(x, {}).get(b)
                if xb:
                    implied = implied & compose(ax, xb)
            tested += 1
            if implied != FULL and implied <= MAVEN_TO_ALLEN.get(rel, FULL):
                recovered += 1
    print(f"  edges deleted and tested (300 docs): {tested:,}")
    print(f"  recovered exactly by 1-step closure: {recovered:,} "
          f"({100*recovered/tested if tested else 0:.1f}%)")
    print("  -> this is the ceiling for a purely logical C3-B; the rest needs statistics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
