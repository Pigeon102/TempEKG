# -*- coding: utf-8 -*-
"""Honest version of the results/ conflict benchmark, and TempEKG on it.

The shipped benchmark leaks in at least twelve ways (see report/BENCHMARK_AUDIT.md):
timex_raw keeps the true date, nine pipeline columns are populated only on conflict rows,
lexical_score is 0.0 on every ground-truth row, and -- worst -- each conflict is ADDED as
a duplicate of a real event, so the true row is still present to compare against.

Construction used here:
  * every event appears ONCE: if a conflict version exists it REPLACES the ground truth
    row, otherwise the ground truth row is kept
  * input columns only: doc_id, cluster_id, event_type, entities, time_start, text_span,
    timex_type. Everything else is dropped, including timex_raw and source_event_id
  * the label is_conflict is used only to score

Detectors, none of which read a dropped column:
  surface     time_start is YYYY-01-01 (a coarsened date looks like this)
  doc-outlier time_start's year is far from the median year of its document
  graph-gold  time_start ordering contradicts a GOLD event-event temporal edge in the
              TempEKG graph -- audits timestamps against a trusted relational graph
  graph-pred  the same against the 257-rule classifier's PREDICTED edges -- realistic
"""
import sys, io, csv, json, re, statistics
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V

RES = Path(r"C:\Reseach_Quang\results\results")
GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
KEEP = ("doc_id", "cluster_id", "event_type", "entities", "time_start", "text_span", "timex_type")

def ts(t):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", t or "")
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None

def build(split, pct):
    """One row per event, conflict replacing ground truth. Returns (inputs, label, ctype)."""
    rows = list(csv.DictReader(io.open(RES/split/"final"/f"maven_augmented_{pct}pct_refined_scored.csv",
                                       encoding="utf-8")))
    by = {}
    for r in rows:
        eid = r["event_id"]
        if r["is_conflict"] == "True":
            if eid not in by or by[eid][1] is False:
                by[eid] = ({k: r[k] for k in KEEP}, True, r["conflict_type"])
        else:
            if eid not in by:
                by[eid] = ({k: r[k] for k in KEEP}, False, "GROUND_TRUTH")
    return list(by.values())

# ---------------------------------------------------------------- TempEKG graph (valid)
print("nap do thi TempEKG ...", flush=True)
DOCS = {}
for line in io.open(GRAPH/"valid.jsonl", encoding="utf-8"):
    rec = json.loads(line); DOCS[rec["doc_id"]] = rec

# predicted EV-EV edges from the 257-rule classifier
from mine_compositional import candidate_conditions, pair_features
from mine_mdd import relational_conditions
rules = V.load_rules(ART/"rules_rx_c70.json")
PRED = {}                                   # (doc, a, b) -> label
allrows = []
for d, rec in DOCS.items():
    nd = rec["nodes"]; anch = defaultdict(set)
    for p in rec["anchored_pairs"]:
        for ra, rb in p["roles"]: anch[(p["a"], p["b"])].add((ra, rb))
    for e in rec["target_edges"]:
        a, b = e["s"], e["t"]
        if nd.get(a, {}).get("kind") != "event" or nd.get(b, {}).get("kind") != "event": continue
        sh = anch.get((a, b)) or anch.get((b, a)) or set()
        f = pair_features(nd[a], nd[b], sh, bool(sh), frozenset())
        cs = frozenset(list(candidate_conditions(f)) + relational_conditions(nd[a], nd[b], sh))
        allrows.append((d, a, b, f, cs))
idx = V.build_index(rules, [(None, f, cs) for (_, _, _, f, cs) in allrows])
for (d, a, b, f, cs) in allrows:
    PRED[(d, a, b)] = V.combine(rules, V.firing(rules, idx, f, cs), "max-norm", 5) or V.FALLBACK
print("  %s canh EV-EV da du doan" % format(len(PRED), ","), flush=True)

def graph_flags(items, mode):
    """Count, per event, how many EV-EV BEFORE edges its time_start contradicts.

    A BEFORE B asserts A ends before B starts, so ts(A) > ts(B) is a contradiction.
    Only BEFORE is used: it is the one label with an unambiguous order implication.
    The event with more contradictions is the likelier fake.
    """
    bydoc = defaultdict(dict)
    for i, (inp, lab, ct) in enumerate(items):
        d, e = inp["cluster_id"].split("::")
        bydoc[d][e] = (i, ts(inp["time_start"]))
    score = Counter()
    for d, evs in bydoc.items():
        rec = DOCS.get(d)
        if not rec: continue
        for ed in rec["target_edges"]:
            a, b = ed["s"], ed["t"]
            if a not in evs or b not in evs: continue
            rel = ed["rel"] if mode == "gold" else PRED.get((d, a, b))
            if rel != "BEFORE": continue
            (ia, ta), (ib, tb) = evs[a], evs[b]
            if ta is None or tb is None: continue
            if ta > tb:
                score[ia] += 1; score[ib] += 1
    return score

def graph_blame(items, mode):
    """Blame ONE endpoint per contradicted edge, not both.

    Flagging both ends of a contradicted BEFORE edge caps precision near 50%: exactly one
    of them is usually the corrupted event. Two passes: count every event's contradictions,
    then for each contradicted edge charge only the endpoint with more of them (ties go to
    the one farther from its document's median year).
    """
    raw = graph_flags(items, mode)
    bydoc = defaultdict(dict); yrs = defaultdict(list)
    for i, (inp, lab, ct) in enumerate(items):
        d, e = inp["cluster_id"].split("::")
        t = ts(inp["time_start"])
        bydoc[d][e] = (i, t)
        if t: yrs[d].append(t[0])
    med = {d: statistics.median(v) for d, v in yrs.items()}
    blame = Counter()
    for d, evs in bydoc.items():
        rec = DOCS.get(d)
        if not rec: continue
        for ed in rec["target_edges"]:
            a, b = ed["s"], ed["t"]
            if a not in evs or b not in evs: continue
            rel = ed["rel"] if mode == "gold" else PRED.get((d, a, b))
            if rel != "BEFORE": continue
            (ia, ta), (ib, tb) = evs[a], evs[b]
            if ta is None or tb is None or not (ta > tb): continue
            if raw[ia] != raw[ib]:
                blame[ia if raw[ia] > raw[ib] else ib] += 1
            else:
                da = abs(ta[0] - med.get(d, ta[0])); db = abs(tb[0] - med.get(d, tb[0]))
                blame[ia if da >= db else ib] += 1
    return blame

def evaluate(items, flagged):
    tp = sum(1 for i in flagged if items[i][1]); fp = len(flagged) - tp
    pos = sum(1 for it in items if it[1])
    P = tp/len(flagged) if flagged else 0; R = tp/pos if pos else 0
    F = 2*P*R/(P+R) if P+R else 0
    bytype = Counter(); tot = Counter()
    for i, it in enumerate(items):
        if it[1]:
            tot[it[2]] += 1
            if i in flagged: bytype[it[2]] += 1
    return P, R, F, {t: (bytype[t], tot[t]) for t in tot}

print()
print("=" * 100)
print("BENCHMARK TRUNG THUC — moi event mot lan, bo timex_raw va moi cot pipeline")
print("=" * 100)
TYPES = ("ANCHOR_CONFLICT", "ORDERING_CONFLICT", "GRANULARITY_CONFLICT", "IMPLICIT_ORDERING")
for pct in ("05", "10", "15", "20"):
    items = build("valid", pct)
    pos = sum(1 for it in items if it[1])
    print()
    print("  muc %s%% -- %s event, %d conflict" % (pct, format(len(items), ","), pos))
    print("  %-14s%9s%9s%9s   %s" % ("detector", "P", "R", "F1",
          "  ".join("%s" % t.split("_")[0][:5] for t in TYPES)))
    dets = {}
    dets["surface"] = {i for i, (inp, lab, ct) in enumerate(items)
                       if (t := ts(inp["time_start"])) and t[1] == 1 and t[2] == 1}
    yrs = defaultdict(list)
    for inp, lab, ct in items:
        t = ts(inp["time_start"])
        if t: yrs[inp["doc_id"]].append(t[0])
    med = {d: statistics.median(v) for d, v in yrs.items()}
    dets["doc-outlier"] = {i for i, (inp, lab, ct) in enumerate(items)
                           if (t := ts(inp["time_start"])) and abs(t[0] - med[inp["doc_id"]]) >= 1}
    for mode in ("gold", "pred"):
        sc = graph_flags(items, mode)
        dets["graph-" + mode] = {i for i, v in sc.items() if v >= 1}
        bl = graph_blame(items, mode)
        dets["blame-" + mode] = {i for i, v in bl.items() if v >= 1}
    dets["surf+outl+gold"] = dets["surface"] | dets["doc-outlier"] | dets["graph-gold"]
    dets["surf+outl+pred"] = dets["surface"] | dets["doc-outlier"] | dets["graph-pred"]
    dets["surf+blame-pred"] = dets["surface"] | dets["blame-pred"]
    for nm, fl in dets.items():
        P, R, F, bt = evaluate(items, fl)
        cell = "  ".join("%3d/%-3d" % bt.get(t, (0, 0)) for t in TYPES)
        print("  %-14s%8.2f%%%8.2f%%%8.2f%%   %s" % (nm, 100*P, 100*R, 100*F, cell))
