"""Combine the rules that fire on a pair, instead of taking the single best one.

WHY. Selecting by highest Wilson lower bound scores macro-F1 22.57% on valid. An oracle over
the same rules -- take the gold label whenever ANY firing rule proposes it, else fall back to
BEFORE -- scores 65.85%, with SIMULTANEOUS at 99.53% even though its best rule has wlb 0.141.

The right rule is almost always already firing. It fires next to many wrong ones, and
argmax-wlb picks a wrong one. That is a 43-point ranking problem, not a mining problem: no
new rules are needed, only a better way to read the ones that fired.

FOUR COMBINERS, cheapest first:

    argmax-wlb      current behaviour, the baseline to beat
    sum-wlb         every firing rule votes for its own relation, weighted by wlb
    sum-logodds     weight log(p/(1-p)) instead, so two independent weak rules can
                    outvote one middling rule -- the naive-Bayes reading
    count           unweighted vote, to show whether the weights matter at all

Each needs a margin over the BEFORE prior before it overrides the fallback, since BEFORE is
89.94% of the data and a lone weak rule should not beat that. `--tau` sweeps the margin.

NO GPU. The cost is discrete set matching (is every condition of this rule in this pair's
candidate set?), which is hash lookups, not dense arithmetic. Rarest-condition indexing keeps
it to a few candidate rules per instance. Measured: ~2 minutes over 593k instances.

Usage:
    python vote.py --rules families.json --tau-sweep
"""

from __future__ import annotations

import argparse
import json
import math
import hashlib
from collections import Counter, defaultdict
from pathlib import Path

from mine_compositional import candidate_conditions, pair_features
from mine_views import VIEWS
from mine_mdd import relational_conditions

HERE = Path(__file__).resolve().parent
GRAPH = HERE / "graph"
ART = HERE / "artifacts"

RELATIONS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
# Train base rates. Used to normalise a rule's weight by how surprising its relation is:
# a rule for a 0.86% relation carries more information than one for a 7.43% relation at
# the same Wilson score.
PRIOR = {"BEFORE": 0.91045, "CONTAINS": 0.07430, "SIMULTANEOUS": 0.00862,
         "OVERLAP": 0.00597, "BEGINS-ON": 0.00044, "ENDS-ON": 0.00022}
FALLBACK = "BEFORE"          # 89.94% of valid; every combiner must beat this to fire


def dev_doc(doc_id: str) -> bool:
    """A fifth of documents, chosen by hash so the split is stable across runs.

    The split is BY DOCUMENT, not by pair: pairs from one document share its topic,
    its annotation style and its event distribution, so splitting pairs at random
    would put near-copies on both sides and make held-out numbers look better than
    they are.
    """
    return int(hashlib.md5(doc_id.encode()).hexdigest(), 16) % 5 == 0


def load_rows(path: Path, limit: int = 0, keep=None):
    """(gold, features, condition-set) per event-event pair.

    keep(doc_id) -> bool selects a document subset; None takes every document.
    """
    rows = []
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if limit and i >= limit:
                break
            if not line.strip():
                continue
            rec = json.loads(line)
            if keep is not None and not keep(rec["doc_id"]):
                continue
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
                cs = list(candidate_conditions(f))
                # MDD rules may carry REL:* conditions, which pair_features does not
                # produce. Without these the 337 relational rules could never fire.
                cs += relational_conditions(na, nb, shared)
                rows.append((e["rel"], f, frozenset(cs)))
    return rows


def load_rules(path: Path):
    out = []
    for r in json.loads(path.read_text(encoding="utf-8")):
        out.append({
            "conds": tuple((c[0], c[1], tuple(c[2]) if isinstance(c[2], list) else c[2])
                           for c in r["conds"]),
            "rel": r["rel"],
            "view": r.get("view", "global"),
            "sig": r.get("sig", "*"),
            "wlb": r.get("wlb", 0.0),
        })
    return out


def build_index(rules, rows):
    """Index each rule under its rarest condition, so most rules are never even considered."""
    df = Counter()
    for _, _, cs in rows:
        for c in cs:
            df[c] += 1
    idx = defaultdict(list)
    for i, r in enumerate(rules):
        if r["conds"]:
            idx[min(r["conds"], key=lambda x: df.get(x, 0))].append(i)
    return idx


def firing(rules, idx, feats, conds):
    """Indices of the rules whose conditions and view signature both match this pair."""
    hits = []
    sig_cache = {}
    for cond in conds:
        for i in idx.get(cond, ()):
            r = rules[i]
            v = r["view"]
            if r["sig"] != "*":
                if v not in sig_cache:
                    sig_cache[v] = str(VIEWS[v](feats))
                if sig_cache[v] != r["sig"]:
                    continue
            if all(x in conds for x in r["conds"]):
                hits.append(i)
    return hits


def combine(rules, hits, method, tau):
    """Pick a relation from the firing rules, or None to keep the BEFORE fallback."""
    if not hits:
        return None
    score = defaultdict(float)
    for i in hits:
        r = rules[i]
        w = r["wlb"]
        if method == "argmax-wlb":
            if w > score[r["rel"]]:
                score[r["rel"]] = w
        elif method == "sum-wlb":
            score[r["rel"]] += w
        elif method == "count":
            score[r["rel"]] += 1.0
        elif method == "norm-wlb":
            # Normalise each rule's weight by how common its relation is. A SIMULTANEOUS
            # rule at wlb 0.14 is far more informative than a CONTAINS rule at 0.14,
            # because SIMULTANEOUS is 0.86% of the corpus and CONTAINS is 7.43%.
            score[r["rel"]] += w / PRIOR[r["rel"]]
        elif method == "max-norm":
            v = w / PRIOR[r["rel"]]
            if v > score[r["rel"]]:
                score[r["rel"]] = v
        elif method == "sum-logodds":
            # clamp: wlb can reach 0 or 1 and log-odds would blow up
            p = min(max(w, 1e-4), 1 - 1e-4)
            score[r["rel"]] += math.log(p / (1 - p))
        else:
            raise ValueError(method)
    if not score:
        return None
    best = max(score, key=score.get)
    return best if score[best] >= tau else None


def macro_f1(pred, gold):
    tp, fp, fn = Counter(), Counter(), Counter()
    for p, g in zip(pred, gold):
        if p == g:
            tp[g] += 1
        else:
            fp[p] += 1
            fn[g] += 1
    per = {}
    for r in RELATIONS:
        P = tp[r] / (tp[r] + fp[r]) if tp[r] + fp[r] else 0.0
        R = tp[r] / (tp[r] + fn[r]) if tp[r] + fn[r] else 0.0
        per[r] = 2 * P * R / (P + R) if P + R else 0.0
    acc = sum(tp.values()) / len(gold) if gold else 0.0
    return sum(per.values()) / len(RELATIONS), per, acc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--rules", default="rules_rx_c70.json",
                    help="comma-separated rule files in artifacts/. The default is the "
                         "final library (257 rules, see rules/final/README.md). Several "
                         "files are merged if given; the LCB-Lift sets under "
                         "experiments/ablations/lcb are failed alternatives, kept for "
                         "reproduction and not loaded by default.")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--tau-sweep", action="store_true")
    ap.add_argument("--select-on", choices=("dev-inner", "valid"), default="dev-inner",
                    help="where (method, tau) is CHOSEN. 'dev-inner' holds out 20%% of "
                         "TRAIN documents and picks there, then touches valid once -- "
                         "this is the honest protocol. 'valid' reproduces the old "
                         "behaviour, which selects on the test set; measured leak on the "
                         "4,380-rule set was 0.00 points, but that is not guaranteed for "
                         "other rule sets.")
    args = ap.parse_args()

    rules = []
    for name in args.rules.split(","):
        part = load_rules(ART / name.strip())
        print(f"  {name.strip():<28}{len(part):>7,}  "
              f"{dict(Counter(r['rel'] for r in part).most_common())}")
        rules += part
    print(f"{len(rules):,} rules total  "
          f"{dict(Counter(r['rel'] for r in rules).most_common())}", flush=True)

    va = load_rows(GRAPH / "valid.jsonl", args.limit)
    gold = [r[0] for r in va]
    print(f"{len(va):,} valid pairs  "
          f"base {FALLBACK} {100*gold.count(FALLBACK)/len(gold):.2f}%\n", flush=True)

    idx = build_index(rules, va)
    fired = [firing(rules, idx, f, cs) for _, f, cs in va]
    n_fire = sum(1 for h in fired if h)
    print(f"rules fire on {n_fire:,} pairs ({100*n_fire/len(va):.1f}%), "
          f"mean {sum(len(h) for h in fired)/max(1,n_fire):.1f} rules per firing pair\n",
          flush=True)

    base_m, _, base_a = macro_f1([FALLBACK] * len(gold), gold)
    print(f"  {'combiner':<20}{'tau':>7}{'macro-F1':>10}{'acc':>8}   per-label F1")
    print("  " + "-" * 92)
    print(f"  {'constant BEFORE':<20}{'-':>7}{100*base_m:>9.2f}%{100*base_a:>7.2f}%")

    taus = {
        "argmax-wlb": [0.0, 0.2, 0.3, 0.4, 0.5],
        "sum-wlb": [0.0, 0.5, 1.0, 2.0, 4.0, 8.0],
        "count": [1, 2, 3, 5, 10],
        "sum-logodds": [-20.0, -10.0, -5.0, 0.0, 5.0],
        "norm-wlb": [5, 20, 50, 100, 200, 400],
        "max-norm": [5, 20, 50, 100, 200, 400],
    }
    def sweep(rows, fired_rows, gold_rows, show):
        """Score every (method, tau) on one split. Returns {(method, tau): (mf, acc)}."""
        got = {}
        for method in ("argmax-wlb", "sum-wlb", "count", "sum-logodds",
                       "norm-wlb", "max-norm"):
            for tau in (taus[method] if args.tau_sweep else taus[method][:1]):
                pred = [combine(rules, h, method, tau) or FALLBACK for h in fired_rows]
                m, per, acc = macro_f1(pred, gold_rows)
                got[(method, tau)] = (m, per, acc)
                if show:
                    nz = " ".join(f"{r.split('-')[0][:4]} {100*per[r]:.0f}"
                                  for r in RELATIONS if per[r] > 0)
                    print(f"  {method:<20}{tau:>7}{100*m:>9.2f}%{100*acc:>7.2f}%   {nz}",
                          flush=True)
        return got

    if args.select_on == "dev-inner":
        # Pick the configuration on held-out TRAIN documents, never on valid.
        dev = load_rows(GRAPH / "train.jsonl", args.limit or 400, keep=dev_doc)
        dgold = [r[0] for r in dev]
        didx = build_index(rules, dev)
        dfired = [firing(rules, didx, f, cs) for _, f, cs in dev]
        print(f"  selecting on DEV-INNER: {len(dev):,} pairs from held-out train docs",
              flush=True)
        dres = sweep(dev, dfired, dgold, show=False)
        method, tau = max(dres, key=lambda k: dres[k][0])
        print(f"  picked {method} tau={tau} at dev macro-F1 "
              f"{100*dres[(method, tau)][0]:.2f}%\n", flush=True)

    print(f"  {'combiner':<20}{'tau':>7}{'macro-F1':>10}{'acc':>8}   per-label F1  [VALID]")
    print("  " + "-" * 92)
    vres = sweep(va, fired, gold, show=True)

    if args.select_on == "valid":
        method, tau = max(vres, key=lambda k: vres[k][0])
        print("\n  NOTE: selected on valid -- this is selection on the test set.")
    m, per, acc = vres[(method, tau)]
    print()
    print(f"  BEST  {method} at tau={tau}:  macro-F1 {100*m:.2f}%  acc {100*acc:.2f}%"
          f"   (chosen on {args.select_on})")
    for r in RELATIONS:
        print(f"    {r:<15}{100*per[r]:>7.2f}%")
    print()
    print(f"  constant BEFORE {100*base_m:.2f}%  ->  {100*m:.2f}%  "
          f"({100*(m-base_m):+.2f} points)")
    print(f"  oracle ceiling is 65.85%; this closes "
          f"{100*(m-0.2257)/(0.6585-0.2257):.0f}% of the gap from argmax-wlb (22.57%)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
