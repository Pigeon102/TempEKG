"""Mine rules for event-TIMEX pairs -- the 33% of the corpus nothing has touched.

WHY. Everything so far scores only event-event pairs. Measured on train:

    EV-EV        203,449 edges   BEFORE 92.03%   non-BEFORE  7.97%
    EV-TIMEX      97,354 edges   BEFORE 81.54%   non-BEFORE 18.46%
    TIMEX-TIMEX   15,186 edges   BEFORE 82.87%   non-BEFORE 17.13%

112,540 edges (35.6%) sit unused, and their non-BEFORE mass is 2.3x denser than EV-EV's.
A lower base rate means a higher lift ceiling, so rules here can be stronger than anything
mineable on event pairs. CONTAINS alone is 17.19% of EV-TIMEX against 6.87% of EV-EV, which
reads correctly: an event usually falls INSIDE a date, not before or after it.

FEATURES ARE DIFFERENT, so this cannot reuse pair_features(). A timex node carries
timex_type (DATE/TIME/DURATION/SET), anchorable, and its surface text; it has no event type,
no argument roles, no mention count. The informative combinations are therefore different
too -- "a DURATION timex containing a Process_end event" has no analogue on event pairs.

DIRECTION MATTERS AND IS NOT SYMMETRIC. The corpus stores (timex, event) and (event, timex)
both, and CONTAINS means opposite things in each. Orientation is kept as an explicit feature
rather than normalised away.

MEASURED (train 262,392 pairs, valid 66,508):

    535 rules at sup>=25, k>=5, lift>=1.5
    by relation: CONTAINS 197 · OVERLAP 193 · SIMULTANEOUS 94 · BEGINS-ON 38 · ENDS-ON 13
    375 / 535 (70.1%) keep lift >= 1.5 on valid; the top 18 keep it 18/18

This is the first rule set with rules for BEGINS-ON and ENDS-ON at all -- event-event mining
produced none, and those two labels have scored F1 = 0 in every classifier so far. Best
Wilson lower bound is 0.666, above the 0.598 ceiling on event pairs.

CAVEAT, measured rather than assumed: every top rule contains sdist=0, so most of the signal
is "the event and the date are in the same sentence" (59.29% CONTAINS on valid against a
21.10% base, lift 2.81x). Event type adds real signal on top for some types and none for
others:

    Use_firearm          90.00%   +30.71 over sdist=0 alone
    Expressing_publicly  78.87%   +19.58
    Sign_agreement       76.67%   +17.38
    Coming_to_be         66.40%    +7.11
    Attack               59.42%    +0.13   <- sdist=0 in disguise
    Competition          58.24%    -1.05   <- worse than the base condition

Report the sdist=0 baseline alongside any rule that includes it, or the event-type conditions
look like they are doing work they are not.

Usage:
    python mine_timex.py --sup-min 25 --lift-min 1.5
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
GRAPH = HERE / "graph"

RELATIONS = ("BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON")


def wilson_lower(k: int, n: int, z: float = 1.96) -> float:
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - margin) / d


def sent_bucket(i: int) -> str:
    if i == 0:
        return "lead"
    if i <= 2:
        return "early"
    if i <= 6:
        return "mid"
    return "late"


def timex_features(tnode, enode, t_first: bool):
    """Conditions for one (timex, event) pair. t_first records the stored direction."""
    f = {}
    f["tx_type"] = tnode.get("timex_type", "?")
    f["tx_anchorable"] = bool(tnode.get("anchorable"))
    txt = (tnode.get("text") or "").strip().lower()
    # A bare year behaves differently from "last Tuesday": the first spans a whole year and
    # tends to CONTAIN events, the second is a point.
    f["tx_isyear"] = txt.isdigit() and len(txt) == 4
    f["tx_len"] = "1" if len(txt.split()) <= 1 else ("2-3" if len(txt.split()) <= 3 else "4+")
    f["ev_type"] = enode.get("type", "?")
    f["ev_multi"] = enode.get("n_mentions", 1) > 1
    f["ev_bucket"] = enode.get("sent_bucket") or sent_bucket(enode.get("sent_first", 0))
    f["ev_inarg"] = bool(enode.get("in_arg"))
    f["timex_first"] = t_first

    ts, es = tnode.get("sent_first", 0), enode.get("sent_first", 0)
    d = abs(ts - es)
    f["sdist"] = "0" if d == 0 else ("1" if d == 1 else ("2-3" if d <= 3 else "4+"))
    f["same_sent"] = d == 0
    f["tx_before_ev"] = ts < es if ts != es else (tnode.get("tok_first", 0) <
                                                  enode.get("tok_first", 0))
    return f


def conditions(f):
    """Single conditions plus the pairs worth trying. Depth 2 only -- see mine_views.py."""
    out = [("EQ", k, v) for k, v in f.items()]
    # Deliberate combinations: timex kind x event kind, and each crossed with distance.
    key = [("tx_type", "ev_type"), ("tx_type", "sdist"), ("tx_isyear", "ev_type"),
           ("tx_type", "timex_first"), ("ev_type", "sdist"), ("tx_type", "same_sent"),
           ("tx_isyear", "sdist"), ("ev_bucket", "tx_type")]
    for a, b in key:
        out.append(("AND", (a, f[a]), (b, f[b])))
    return out


def load(path: Path, limit: int = 0):
    """(relation, condition list) for every event-TIMEX pair."""
    rows = []
    with path.open(encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            if limit and i >= limit:
                break
            if not line.strip():
                continue
            rec = json.loads(line)
            nodes = rec["nodes"]
            for e in rec["target_edges"]:
                na, nb = nodes.get(e["s"]), nodes.get(e["t"])
                if not na or not nb:
                    continue
                ka, kb = na["kind"], nb["kind"]
                if ka == "timex" and kb == "event":
                    f = timex_features(na, nb, True)
                elif ka == "event" and kb == "timex":
                    f = timex_features(nb, na, False)
                else:
                    continue
                rows.append((e["rel"], conditions(f)))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sup-min", type=int, default=25)
    ap.add_argument("--lift-min", type=float, default=1.5)
    ap.add_argument("--min-k", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--top", type=int, default=25)
    args = ap.parse_args()

    tr = load(GRAPH / "train.jsonl", args.limit)
    va = load(GRAPH / "valid.jsonl", args.limit)
    print(f"train {len(tr):,} cap EV-TIMEX   valid {len(va):,}")

    base = Counter(r for r, _ in tr)
    n = len(tr)
    print(f"  base rate train: " +
          "  ".join(f"{r} {100*base[r]/n:.2f}%" for r in RELATIONS if base[r]))
    bva = Counter(r for r, _ in va)
    nv = len(va)
    print(f"  base rate valid: " +
          "  ".join(f"{r} {100*bva[r]/nv:.2f}%" for r in RELATIONS if bva[r]))
    print()

    cnt = Counter()
    hit = defaultdict(Counter)
    for rel, cs in tr:
        for c in cs:
            cnt[c] += 1
            hit[c][rel] += 1

    rules = []
    for c, N in cnt.items():
        if N < args.sup_min:
            continue
        for rel, k in hit[c].items():
            if k < args.min_k:
                continue
            exp = base[rel] / n
            if exp <= 0:
                continue
            lift = (k / N) / exp
            if lift < args.lift_min:
                continue
            rules.append((wilson_lower(k, N), lift, rel, k, N, c))
    rules.sort(reverse=True)
    print(f"mined {len(rules):,} rules (sup>={args.sup_min}, k>={args.min_k}, "
          f"lift>={args.lift_min})")
    print(f"  by relation: {dict(Counter(r[2] for r in rules).most_common())}\n")

    # hold out: does each rule keep its edge on valid?
    cva = Counter()
    hva = defaultdict(Counter)
    for rel, cs in va:
        for c in cs:
            cva[c] += 1
            hva[c][rel] += 1

    print(f"  {'wlb':>7}{'lift':>7}{'k':>7}{'n':>8}  {'rel':<14}"
          f"{'VALID prec':>11}{'v-lift':>8}  condition")
    print("  " + "-" * 104)
    kept = 0
    for wlb, lift, rel, k, N, c in rules[:args.top]:
        Nv = cva.get(c, 0)
        kv = hva[c][rel] if Nv else 0
        pv = kv / Nv if Nv else 0.0
        lv = pv / (bva[rel] / nv) if Nv and bva[rel] else 0.0
        if lv >= 1.5:
            kept += 1
        desc = (f"{c[1]}={c[2]}" if c[0] == "EQ"
                else f"{c[1][0]}={c[1][1]} AND {c[2][0]}={c[2][1]}")
        print(f"  {wlb:>7.3f}{lift:>7.2f}{k:>7,}{N:>8,}  {rel:<14}"
              f"{100*pv:>10.2f}%{lv:>8.2f}  {desc[:44]}")

    # how many of ALL mined rules survive, not just the top slice
    surv = 0
    for wlb, lift, rel, k, N, c in rules:
        Nv = cva.get(c, 0)
        if not Nv or not bva[rel]:
            continue
        if ((hva[c][rel] / Nv) / (bva[rel] / nv)) >= 1.5:
            surv += 1
    print()
    print(f"  giu duoc lift>=1.5 tren valid: {surv:,} / {len(rules):,} "
          f"({100*surv/max(1,len(rules)):.1f}%)")
    print(f"  (trong {args.top} rule dau: {kept}/{args.top})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
