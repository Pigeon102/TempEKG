"""Score the detectors against injected ground truth.

This is the measurement that injection exists for. On clean gold every firing is a false
positive by definition, which gives specificity but never recall. With known corruptions
both are computable.

C3-A, wrong-edge. The detector flags a labelled pair when a constraint forbids its label.
Precision and recall are against the relabelled set.

C3-B, missing-edge. The detector proposes a label for an unlabelled pair when one-step Allen
closure forces exactly one. Precision and recall are against the deleted set.

    R_all     = recovered / all deletions
    R_beyond  = recovered on the residual / residual

The split matters: closure alone recovers 80.4% of deletions, so a single recall figure
lets that pass as the method's contribution. The residual -- deletions closure cannot
decide -- is where mined rules have anything to add.

BASELINES, reported alongside every number:
    all-non-BEFORE   flag every pair whose label is not BEFORE   (10.06% of valid)
    Brare            flag {BEGINS-ON, ENDS-ON} only              (two lines, no mining)

Brare is here because under a uniform corruption model it beats the mined family outright
(F1 0.557 vs 0.378); under gold-marginal it collapses. Printing it keeps that visible.

Usage:
    python detect.py --tag gold-marginal-r0.001-s0 --limit 300
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL

HERE = Path(__file__).resolve().parent
ART = HERE / "artifacts"   # mined artifacts; see data/README.md
GRAPH = HERE / "graph"
RELATIONS = ("BEFORE", "CONTAINS", "OVERLAP", "SIMULTANEOUS", "BEGINS-ON", "ENDS-ON")


def prf(tp: int, fp: int, fn: int):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def line(name: str, tp: int, fp: int, fn: int, extra: str = ""):
    p, r, f = prf(tp, fp, fn)
    print(f"  {name:<26} P {100*p:6.2f}%  R {100*r:6.2f}%  F1 {100*f:6.2f}%   "
          f"tp={tp:<6,} fp={fp:<7,} fn={fn:<6,}{extra}")


# ------------------------------------------------------------------ C3-A

def load_constraints(tau: str):
    data = json.loads((ART / "constraints.json").read_text(encoding="utf-8"))
    out = []
    for c in data[tau]:
        conds = tuple((x[0], x[1], tuple(x[2]) if isinstance(x[2], list) else x[2])
                      for x in c["conds"])
        out.append({"conds": conds, "view": c["view"], "sig": c["sig"],
                    "forbidden": set(c["forbidden"])})
    return out


def load_minimal_rules():
    """The 68 greedy-minimal rules, as a wrong-edge detector.

    A constraint says "label L is forbidden here" and fires on rel in forbidden. A rule says
    "the label here is R" and fires on rel != R -- the disagreement IS the flag. Worth trying
    because the 68 rules all predict CONTAINS (88.1% of the non-BEFORE mass), and CONTAINS is
    a label the gold-marginal sampler actually injects, unlike the ENDS-ON/BEGINS-ON that
    tau=0.001 spends 19,927 constraints forbidding.
    """
    data = json.loads((HERE / "minimal_rules.json").read_text(encoding="utf-8"))
    out = []
    for c in data:
        conds = tuple((x[0], x[1], tuple(x[2]) if isinstance(x[2], list) else x[2])
                      for x in c["conds"])
        out.append({"conds": conds, "view": c["view"], "sig": c["sig"],
                    "rel": c["rel"], "wlb": c.get("wlb", 0.0)})
    return out


def score_wrong_edge(corrupt_path: Path, truth, tau: str, limit: int):
    """Flag a labelled pair when some constraint forbids the label it carries."""
    from mine_compositional import candidate_conditions, pair_features
    from mine_views import VIEWS

    cons = load_constraints(tau)
    injected = {(t["doc"], t["a"], t["b"]) for t in truth if t["op"] == "relabel"}

    df = Counter()
    rows = []
    with corrupt_path.open(encoding="utf-8") as fh:
        for i, ln in enumerate(fh):
            if limit and i >= limit:
                break
            if not ln.strip():
                continue
            rec = json.loads(ln)
            nodes = rec["nodes"]
            anchors = defaultdict(set)
            for p in rec["anchored_pairs"]:
                for ra, rb in p["roles"]:
                    anchors[(p["a"], p["b"])].add((ra, rb))
            for e in rec["target_edges"]:
                a, b = e["s"], e["t"]
                na, nb = nodes.get(a), nodes.get(b)
                if not na or not nb or na["kind"] != "event" or nb["kind"] != "event":
                    continue
                shared = anchors.get((a, b)) or anchors.get((b, a)) or set()
                f = pair_features(na, nb, shared, bool(shared), frozenset())
                cs = frozenset(candidate_conditions(f))
                for c in cs:
                    df[c] += 1
                rows.append((rec["doc_id"], a, b, e["rel"], f, cs))

    by_rare = defaultdict(list)
    for i, c in enumerate(cons):
        by_rare[min(c["conds"], key=lambda x: df.get(x, 0))].append(i)

    tp = fp = 0
    flagged = set()
    sig_cache = {}
    for doc, a, b, rel, f, cs in rows:
        hit = False
        for cond in cs:
            for i in by_rare.get(cond, ()):
                c = cons[i]
                v = c["view"]
                if v not in sig_cache:
                    sig_cache[v] = str(VIEWS[v](f))
                if sig_cache[v] != c["sig"]:
                    continue
                if all(x in cs for x in c["conds"]) and rel in c["forbidden"]:
                    hit = True
                    break
            if hit:
                break
        sig_cache.clear()
        if hit:
            flagged.add((doc, a, b))
            if (doc, a, b) in injected:
                tp += 1
            else:
                fp += 1
    fn = len(injected) - tp

    # --- the 68 minimal rules on the SAME rows, as a second detector
    rules = load_minimal_rules()
    rdf = Counter()
    for _, _, _, _, _, cs in rows:
        for c in cs:
            rdf[c] += 1
    r_by_rare = defaultdict(list)
    for i, c in enumerate(rules):
        r_by_rare[min(c["conds"], key=lambda x: rdf.get(x, 0))].append(i)

    r_tp = r_fp = 0
    for doc, a, b, rel, f, cs in rows:
        hit = False
        for cond in cs:
            for i in r_by_rare.get(cond, ()):
                c = rules[i]
                v = c["view"]
                if v not in sig_cache:
                    sig_cache[v] = str(VIEWS[v](f))
                if sig_cache[v] != c["sig"] and c["sig"] != "*":
                    continue
                # a rule predicting R disagrees with an edge labelled anything but R
                if all(x in cs for x in c["conds"]) and rel != c["rel"]:
                    hit = True
                    break
            if hit:
                break
        sig_cache.clear()
        if hit:
            if (doc, a, b) in injected:
                r_tp += 1
            else:
                r_fp += 1

    # baselines on the same rows
    bl = {}
    for name, pred in (("all non-BEFORE", lambda r: r != "BEFORE"),
                       ("Brare {BEG,ENDS}", lambda r: r in ("BEGINS-ON", "ENDS-ON"))):
        btp = bfp = 0
        for doc, a, b, rel, _, _ in rows:
            if pred(rel):
                if (doc, a, b) in injected:
                    btp += 1
                else:
                    bfp += 1
        bl[name] = (btp, bfp, len(injected) - btp)

    return {"tp": tp, "fp": fp, "fn": fn, "n_rows": len(rows),
            "n_injected": len(injected), "baselines": bl,
            "rules": (r_tp, r_fp, len(injected) - r_tp)}


# ------------------------------------------------------------------ C3-B

def maven_compatible(aset):
    return [r for r, a in MAVEN_TO_ALLEN.items() if a & aset]


def score_missing_edge(corrupt_path: Path, truth, limit: int):
    """Propose a label for an unlabelled pair when closure forces exactly one.

    Stratified into closure-recoverable and residual, because one-step closure alone
    recovers most deletions and a single recall number would hide that.
    """
    deleted = {(t["doc"], t["a"], t["b"]): t["original"]
               for t in truth if t["op"] == "delete"}

    tp = fp = 0
    resid_tp = resid_n = 0
    wrong_label = 0
    by_label = Counter()

    with corrupt_path.open(encoding="utf-8") as fh:
        for i, ln in enumerate(fh):
            if limit and i >= limit:
                break
            if not ln.strip():
                continue
            rec = json.loads(ln)
            nodes = rec["nodes"]
            edges = [(e["s"], e["t"], e["rel"]) for e in rec["target_edges"]
                     if nodes[e["s"]]["kind"] == "event" and nodes[e["t"]]["kind"] == "event"]
            if len(edges) < 2:
                continue

            adj = defaultdict(dict)
            labelled = set()
            for s, t, r in edges:
                aset = MAVEN_TO_ALLEN.get(r)
                if not aset:
                    continue
                adj[s][t] = aset
                adj[t][s] = converse(aset)
                labelled.add((s, t))
                labelled.add((t, s))

            evs = [k for k, v in nodes.items() if v["kind"] == "event"]
            for ai in range(len(evs)):
                for bi in range(len(evs)):
                    if ai == bi:
                        continue
                    a, b = evs[ai], evs[bi]
                    if (a, b) in labelled:
                        continue
                    implied = FULL
                    for x, ax in adj.get(a, {}).items():
                        if x == b:
                            continue
                        xb = adj.get(x, {}).get(b)
                        if xb:
                            implied = implied & compose(ax, xb)
                    if implied == FULL:
                        continue
                    adm = maven_compatible(implied)
                    if len(adm) != 1:
                        continue          # closure did not decide
                    pred = adm[0]
                    key = (rec["doc_id"], a, b)
                    if key in deleted:
                        if deleted[key] == pred:
                            tp += 1
                            by_label[pred] += 1
                        else:
                            wrong_label += 1
                    else:
                        fp += 1

    # residual: deletions closure never proposed a label for at all
    resid_n = len(deleted) - tp - wrong_label
    return {"tp": tp, "fp": fp, "fn": len(deleted) - tp,
            "wrong_label": wrong_label, "residual": resid_n,
            "n_deleted": len(deleted), "by_label": by_label}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--split", default="train")
    ap.add_argument("--tag", default="gold-marginal-r0.001-s0")
    ap.add_argument("--tau", default="0.001")
    ap.add_argument("--limit", type=int, default=300)
    args = ap.parse_args()

    rel_path = GRAPH / f"{args.split}.relabel-{args.tag}.jsonl"
    rel_truth = GRAPH / f"{args.split}.relabel-{args.tag}.truth.json"
    del_path = GRAPH / f"{args.split}.delete-{args.tag}.jsonl"
    del_truth = GRAPH / f"{args.split}.delete-{args.tag}.truth.json"

    for p in (rel_path, rel_truth, del_path, del_truth):
        if not p.exists():
            print(f"missing {p.name} -- run inject.py with the same tag first")
            return 1

    print("=" * 78)
    print(f"C3-A  WRONG-EDGE   tau={args.tau}  tag={args.tag}  docs={args.limit}")
    print("=" * 78)
    t = json.loads(rel_truth.read_text(encoding="utf-8"))
    ra = score_wrong_edge(rel_path, t, args.tau, args.limit)
    print(f"  pairs examined {ra['n_rows']:,}   injected errors {ra['n_injected']:,}")
    print()
    line(f"constraints tau={args.tau}", ra["tp"], ra["fp"], ra["fn"])
    line("68 minimal rules", *ra["rules"])
    for name, (btp, bfp, bfn) in ra["baselines"].items():
        line(name, btp, bfp, bfn)

    # Absolute precision is meaningless without the prior: 60 errors in 82,064 pairs is
    # 0.073%, so every detector here looks terrible on raw precision alone.
    prior = ra["n_injected"] / ra["n_rows"] if ra["n_rows"] else 0
    print()
    print(f"  random-flagging prior {100*prior:.4f}%  -- lift vs that prior:")
    rows_ = [(f"constraints tau={args.tau}", ra["tp"], ra["fp"]),
             ("68 minimal rules", ra["rules"][0], ra["rules"][1])]
    rows_ += [(nm, t, f) for nm, (t, f, _) in ra["baselines"].items()]
    for nm, t, f in rows_:
        fl = t + f
        if fl and prior:
            print(f"    {nm:<26} flagged {fl:>7,}   precision {100*t/fl:>6.2f}%   "
                  f"{t/fl/prior:>6.1f}x")

    print()
    print("=" * 78)
    print(f"C3-B  MISSING-EDGE   tag={args.tag}  docs={args.limit}")
    print("=" * 78)
    t2 = json.loads(del_truth.read_text(encoding="utf-8"))
    rb = score_missing_edge(del_path, t2, args.limit)
    print(f"  deleted edges {rb['n_deleted']:,}")
    print()
    line("closure (1-step)", rb["tp"], rb["fp"], rb["fn"])
    print(f"    proposed a label but the WRONG one: {rb['wrong_label']:,}")
    print(f"    closure never proposed anything (residual): {rb['residual']:,}")
    if rb["n_deleted"]:
        print(f"    R_all = {100*rb['tp']/rb['n_deleted']:.1f}%   "
              f"residual share = {100*rb['residual']/rb['n_deleted']:.1f}%")
    print(f"    recovered by label: {dict(rb['by_label'].most_common())}")
    print()
    print("  R_beyond (rules on the residual) is not measured here: no rule-based")
    print("  missing-edge proposer exists yet. The residual is the population it needs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
