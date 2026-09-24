"""Inject known errors into the KG so C3 recall becomes measurable.

Four independent measurements say the gold has no findable annotation errors: 0 pairs with
two labels, 0 PC-inconsistent documents, 0 closure conflicts over 164,803 pairs, and the 103
constraint violations at tau=0.001 are mostly rule errors. MAVEN-ERE labels are a read-off
from one sorted timeline per document, so the annotation is realizable by construction.

There is nothing to find, which means recall cannot be measured on gold at all. Injection
supplies the missing ground truth: corrupt edges we chose, then ask what the detector
recovers.

TWO OPERATORS, TWO PROBLEMS (INJECTION_SPEC.md section 8):

    RELABEL  (a,b,r) -> (a,b,r')   simulates a wrong annotation   -> C3-A
    DELETE   (a,b,r) -> nothing    simulates a missing annotation -> C3-B

After a relabel the graph still has every edge, so it can contradict itself. After a delete
it stays consistent but poorer. The two therefore need different detectors and different
metrics, and must never be reported as one number.

CORRUPTION MODEL: gold-marginal, not uniform. Drawing r' uniformly from the five other
labels puts 40% of injections on {BEGINS-ON, ENDS-ON}, which together are 0.09% of the
corpus -- a 432x enrichment. A two-line baseline that flags those two labels then beats the
mined family (F1 0.557 vs 0.378) purely as a sampler artifact. Drawing from the corpus
marginal removes that. Uniform stays available as a control column, never as the headline.

RATE: 0.1% by default. Measured decoherence: 13.1% of documents become PC-inconsistent at
0.1%, rising to 87.9% at 5%; attributability falls from 61.5% to 3.8% over the same range.
0.1% leaves most documents clean so clean-data false positives can be measured in the same
run. k is drawn Binomial(|E|, p), not round(p*|E|) -- the latter loads low rates with the
largest documents.

Usage:
    python inject.py --rate 0.001 --seed 0
    python inject.py --rate 0.001 --model uniform      # control
    python inject.py --sweep                            # decoherence curve
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

from constraint_net import MAVEN_TO_ALLEN, path_consistency

HERE = Path(__file__).resolve().parent
GRAPH = HERE / "graph"
RELATIONS = ("BEFORE", "CONTAINS", "OVERLAP", "SIMULTANEOUS", "BEGINS-ON", "ENDS-ON")


def corpus_marginal(path: Path) -> dict:
    """Label distribution over event-event edges, used by the gold-marginal sampler."""
    c = Counter()
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            nodes = rec["nodes"]
            for e in rec["target_edges"]:
                if nodes[e["s"]]["kind"] == "event" and nodes[e["t"]]["kind"] == "event":
                    c[e["rel"]] += 1
    tot = sum(c.values())
    return {r: c[r] / tot for r in RELATIONS}


def draw_replacement(rng: random.Random, original: str, marginal: dict, model: str) -> str:
    """A label other than `original`."""
    others = [r for r in RELATIONS if r != original]
    if model == "uniform":
        return rng.choice(others)
    w = [marginal.get(r, 0.0) for r in others]
    if sum(w) <= 0:
        return rng.choice(others)
    return rng.choices(others, weights=w, k=1)[0]


def inject_document(rec: dict, rng: random.Random, rate: float, marginal: dict,
                    model: str, op: str):
    """Return (corrupted record, ground-truth list) for one document.

    k ~ Binomial(|E|, rate) so the per-edge probability is uniform across documents of every
    size. Only event-event edges are eligible; TIMEX endpoints are left alone because the
    detectors under test only look at event pairs.
    """
    nodes = rec["nodes"]
    eligible = [i for i, e in enumerate(rec["target_edges"])
                if nodes[e["s"]]["kind"] == "event" and nodes[e["t"]]["kind"] == "event"]
    if not eligible:
        return rec, []

    k = sum(1 for _ in eligible if rng.random() < rate)
    if k == 0:
        return rec, []
    picked = rng.sample(eligible, min(k, len(eligible)))

    truth = []
    out = dict(rec)
    edges = list(rec["target_edges"])

    if op == "relabel":
        for i in picked:
            e = edges[i]
            new = draw_replacement(rng, e["rel"], marginal, model)
            truth.append({"doc": rec["doc_id"], "a": e["s"], "b": e["t"],
                          "op": "relabel", "original": e["rel"], "injected": new})
            edges[i] = {"s": e["s"], "t": e["t"], "rel": new}
    else:  # delete
        drop = set(picked)
        for i in picked:
            e = edges[i]
            truth.append({"doc": rec["doc_id"], "a": e["s"], "b": e["t"],
                          "op": "delete", "original": e["rel"], "injected": None})
        edges = [e for i, e in enumerate(edges) if i not in drop]

    out["target_edges"] = edges
    return out, truth


def pc_consistent(rec: dict) -> bool:
    """Whether the document's event-event constraint network is satisfiable."""
    nodes = rec["nodes"]
    cons = {}
    for e in rec["target_edges"]:
        if nodes[e["s"]]["kind"] != "event" or nodes[e["t"]]["kind"] != "event":
            continue
        aset = MAVEN_TO_ALLEN.get(e["rel"])
        if aset:
            key = (e["s"], e["t"])
            cons[key] = cons.get(key, aset) & aset
    if not cons:
        return True
    ns = sorted({n for pair in cons for n in pair})
    if len(ns) > 60:          # PC is O(n^3); the tail is rare and would dominate runtime
        return True
    ok, _ = path_consistency(ns, cons)
    return ok


def run(split: str, rate: float, model: str, op: str, seed: int, out_tag: str,
        check_pc: bool, limit: int = 0):
    rng = random.Random(seed)
    marginal = corpus_marginal(GRAPH / f"{split}.jsonl")

    src = GRAPH / f"{split}.jsonl"
    dst = GRAPH / f"{split}.{out_tag}.jsonl"
    truth_path = GRAPH / f"{split}.{out_tag}.truth.json"

    truth = []
    stats = Counter()
    with src.open(encoding="utf-8") as fh, dst.open("w", encoding="utf-8") as out:
        for i, line in enumerate(fh):
            if not line.strip():
                continue
            if limit and i >= limit:
                out.write(line)
                continue
            rec = json.loads(line)
            stats["docs"] += 1
            corrupted, t = inject_document(rec, rng, rate, marginal, model, op)
            if t:
                stats["docs_injected"] += 1
                truth.extend(t)
                for x in t:
                    stats["inj_" + (x["injected"] or "DELETED")] += 1
                    stats["from_" + x["original"]] += 1
            if check_pc:
                if not pc_consistent(corrupted):
                    stats["pc_inconsistent"] += 1
                    if t:
                        stats["pc_inconsistent_injected"] += 1
                        if len(t) == 1:
                            stats["attributable"] += 1
            out.write(json.dumps(corrupted, ensure_ascii=False) + "\n")

    truth_path.write_text(json.dumps(truth, indent=1), encoding="utf-8")
    return dst, truth_path, truth, stats, marginal


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="train")
    ap.add_argument("--rate", type=float, default=0.001)
    ap.add_argument("--model", choices=["gold-marginal", "uniform"], default="gold-marginal")
    ap.add_argument("--op", choices=["relabel", "delete", "both"], default="both")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-pc", action="store_true", help="skip the consistency check")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--sweep", action="store_true",
                    help="decoherence curve over five rates instead of one injection")
    args = ap.parse_args()

    if args.sweep:
        print("DECOHERENCE CURVE (relabel, gold-marginal)")
        print(f"  {'rate':>7} {'injected':>9} {'docs hit':>9} "
              f"{'PC-inconsistent':>17} {'attributable':>13}")
        print("  " + "-" * 60)
        for rate in (0.001, 0.005, 0.01, 0.02, 0.05):
            _, _, truth, st, _ = run(args.split, rate, args.model, "relabel",
                                     args.seed, f"sweep{rate}", True, args.limit or 300)
            inc = st["pc_inconsistent"]
            att = st["attributable"]
            print(f"  {rate:>7.3f} {len(truth):>9,} {st['docs_injected']:>9,} "
                  f"{inc:>7,} ({100*inc/max(1,st['docs']):>5.1f}%) "
                  f"{att:>6,} ({100*att/max(1,inc):>5.1f}%)", flush=True)
        print()
        print("  attributable = PC-inconsistent documents carrying exactly one injection,")
        print("  i.e. the corruption can be localised rather than just detected.")
        return 0

    ops = ["relabel", "delete"] if args.op == "both" else [args.op]
    for op in ops:
        tag = f"{op}-{args.model}-r{args.rate}-s{args.seed}"
        dst, tp, truth, st, marg = run(args.split, args.rate, args.model, op,
                                       args.seed, tag, not args.no_pc, args.limit)
        print()
        print("=" * 74)
        print(f"{op.upper()}  rate={args.rate}  model={args.model}  seed={args.seed}")
        print("=" * 74)
        print(f"  documents            {st['docs']:,}")
        print(f"  documents injected   {st['docs_injected']:,} "
              f"({100*st['docs_injected']/max(1,st['docs']):.1f}%)")
        print(f"  edges corrupted      {len(truth):,}")
        if not args.no_pc:
            inc = st["pc_inconsistent"]
            print(f"  PC-inconsistent      {inc:,} "
                  f"({100*inc/max(1,st['docs']):.1f}% of documents)")
            if inc:
                print(f"    carrying exactly 1 injection: {st['attributable']:,} "
                      f"({100*st['attributable']/inc:.1f}%)")
        src_dist = {r[5:]: v for r, v in st.items() if r.startswith("from_")}
        print(f"  original labels      {dict(sorted(src_dist.items(), key=lambda kv: -kv[1]))}")
        if op == "relabel":
            inj = {r[4:]: v for r, v in st.items() if r.startswith("inj_")}
            print(f"  injected labels      {dict(sorted(inj.items(), key=lambda kv: -kv[1]))}")
            rare = sum(v for k, v in inj.items() if k in ("BEGINS-ON", "ENDS-ON"))
            if len(truth):
                base_rare = marg.get("BEGINS-ON", 0) + marg.get("ENDS-ON", 0)
                print(f"    share landing on the two rarest labels: "
                      f"{100*rare/len(truth):.1f}%  (corpus: {100*base_rare:.2f}%)")
        print(f"  wrote {dst.name}")
        print(f"  wrote {tp.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
