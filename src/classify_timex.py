"""Score the EV-TIMEX rules as a classifier, with the same protocol used for event pairs.

WHY SEPARATELY. These rules apply to a different population: 66,508 valid event-TIMEX pairs,
not the 109,929 event-event ones. Merging the two tables would compare numbers computed over
different denominators, which is the mistake this project has already made twice (93.40% vs
35.25%, repair@k vs R_all). They are reported side by side and never summed.

WHAT IS AT STAKE. BEGINS-ON and ENDS-ON score F1 = 0 in every event-event configuration -- no
rule predicts them there. The EV-TIMEX mining produced 38 and 13 rules for them, so this is
the first chance for those two labels to score anything at all.

THE COMBINER is norm-wlb, which won on event pairs: each firing rule contributes
wlb / prior(relation), so a rule for a 0.16% relation outweighs one for a 19.97% relation at
equal confidence. Plain summing loses because the common relations simply have more rules.

Priors here are the EV-TIMEX base rates, NOT the event-event ones -- BEFORE is 78.61% here
against 91.05% there, and CONTAINS 19.97% against 7.43%.

MEASURED. On the EV-TIMEX population the rules beat the constant by +6.67 points
(14.54% -> 21.21% macro-F1, argmax-wlb at tau=0.4), with CONTAINS at 39.21%.

BUT BEGINS-ON AND ENDS-ON STILL SCORE ZERO, and the reason is not fixable by tuning:

    BEGINS-ON   14 gold pairs in valid.  Rules for it fire on 14/14 -- and also on
                38,090 pairs that are NOT BEGINS-ON. They win 2 of the 14.
    ENDS-ON      4 gold pairs in valid.  Rules for it fire on 0 of them, and on 4,475
                pairs that are not.

A noise ratio of 2,721:1. Even winning all 14 would give precision 0.037%. The 13 ENDS-ON
rules matched only train; on valid they never touch a true instance.

So having rules for a relation is necessary but nowhere near sufficient. Neither combiner
helps (argmax and norm-wlb both leave these at 0), and lowering tau just lets the 38,090
false positives through. With 14 and 4 instances no method can learn these two labels --
it is a data limit, not an algorithm choice. Report macro-F1 over the four relations with
>= 100 instances and state these two separately.

Usage:
    python classify_timex.py --tau-sweep
"""

from __future__ import annotations

import argparse
import math
from collections import Counter, defaultdict
from pathlib import Path

from mine_timex import load, wilson_lower, GRAPH, RELATIONS

HERE = Path(__file__).resolve().parent
FALLBACK = "BEFORE"


def mine(tr, sup_min, min_k, lift_min):
    """Same miner as mine_timex.py, returning condition -> (relation, wlb)."""
    base = Counter(r for r, _ in tr)
    n = len(tr)
    cnt = Counter()
    hit = defaultdict(Counter)
    for rel, cs in tr:
        for c in cs:
            cnt[c] += 1
            hit[c][rel] += 1

    out = {}
    for c, N in cnt.items():
        if N < sup_min:
            continue
        best = None
        for rel, k in hit[c].items():
            if k < min_k:
                continue
            exp = base[rel] / n
            if exp <= 0 or (k / N) / exp < lift_min:
                continue
            cand = (wilson_lower(k, N), rel)
            if best is None or cand > best:
                best = cand
        if best:
            out[c] = best
    return out, {r: base[r] / n for r in RELATIONS}


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
    ap.add_argument("--sup-min", type=int, default=25)
    ap.add_argument("--min-k", type=int, default=5)
    ap.add_argument("--lift-min", type=float, default=1.5)
    ap.add_argument("--tau-sweep", action="store_true")
    args = ap.parse_args()

    tr = load(GRAPH / "train.jsonl")
    va = load(GRAPH / "valid.jsonl")
    rules, prior = mine(tr, args.sup_min, args.min_k, args.lift_min)
    print(f"train {len(tr):,}  valid {len(va):,}  rules {len(rules):,}")
    print(f"  by relation: {dict(Counter(r for _, r in rules.values()).most_common())}")
    print(f"  prior EV-TIMEX: " +
          "  ".join(f"{r} {100*prior[r]:.2f}%" for r in RELATIONS if prior[r]) + "\n")

    gold = [r for r, _ in va]
    fired = []
    for _, cs in va:
        hits = [rules[c] for c in cs if c in rules]
        fired.append(hits)
    nz = sum(1 for h in fired if h)
    print(f"rules fire on {nz:,}/{len(va):,} pairs ({100*nz/len(va):.1f}%), "
          f"mean {sum(len(h) for h in fired)/max(1,nz):.1f} per firing pair\n")

    base_m, base_per, base_a = macro_f1([FALLBACK] * len(gold), gold)
    print(f"  {'method':<24}{'tau':>7}{'macro-F1':>10}{'acc':>8}   per-label F1")
    print("  " + "-" * 96)
    print(f"  {'constant BEFORE':<24}{'-':>7}{100*base_m:>9.2f}%{100*base_a:>7.2f}%")

    best = None
    taus = [0, 5, 20, 50, 100, 200, 500] if args.tau_sweep else [100]
    for method in ("argmax-wlb", "norm-wlb"):
        for tau in ([0.0, 0.2, 0.4, 0.5] if method == "argmax-wlb" and args.tau_sweep
                    else ([0.4] if method == "argmax-wlb" else taus)):
            pred = []
            for hits in fired:
                score = defaultdict(float)
                for wlb, rel in hits:
                    if method == "argmax-wlb":
                        score[rel] = max(score[rel], wlb)
                    else:
                        score[rel] += wlb / max(prior[rel], 1e-9)
                if score:
                    b = max(score, key=score.get)
                    pred.append(b if score[b] >= tau else FALLBACK)
                else:
                    pred.append(FALLBACK)
            m, per, acc = macro_f1(pred, gold)
            shown = " ".join(f"{r.split('-')[0][:4]} {100*per[r]:.0f}"
                             for r in RELATIONS if per[r] > 0)
            print(f"  {method:<24}{tau:>7}{100*m:>9.2f}%{100*acc:>7.2f}%   {shown}",
                  flush=True)
            if best is None or m > best[0]:
                best = (m, method, tau, per, acc)

    m, method, tau, per, acc = best
    print()
    print(f"  BEST  {method} tau={tau}:  macro-F1 {100*m:.2f}%  acc {100*acc:.2f}%")
    print(f"  {'relation':<16}{'constant':>10}{'rules':>10}")
    for r in RELATIONS:
        mark = "  <-- first non-zero anywhere" if per[r] > 0 and r in (
            "BEGINS-ON", "ENDS-ON") else ""
        print(f"  {r:<16}{100*base_per[r]:>9.2f}%{100*per[r]:>9.2f}%{mark}")
    print()
    print(f"  constant {100*base_m:.2f}%  ->  {100*m:.2f}%  ({100*(m-base_m):+.2f} points)")
    print()
    print("  This population is EV-TIMEX only (66,508 valid pairs). Do NOT add these numbers")
    print("  to the event-event table (109,929 pairs) -- different denominators.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
