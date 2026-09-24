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


import difflib
# ---------------------------------------------------------------- sentence index for every event
SENT = {}
for d, rec in DOCS.items():
    for k, v in rec["nodes"].items():
        if v.get("kind") == "event": SENT[(d, k)] = v.get("sent_first")

# start-point constraint each relation places on (A, B) at day granularity
#   None = no usable constraint
def violates(rel, ta, tb):
    if rel in ("BEFORE", "CONTAINS", "OVERLAP"): return ta > tb       # A starts no later than B
    if rel in ("SIMULTANEOUS", "BEGINS-ON"):     return ta != tb      # same start day
    return None

def consistency(items, mode, rels):
    """Blame-assigned violations over the chosen relations (gold or predicted edges)."""
    bydoc = defaultdict(dict); yrs = defaultdict(list)
    for i, (inp, lab, ct) in enumerate(items):
        d, e = inp["cluster_id"].split("::"); t = ts(inp["time_start"])
        bydoc[d][e] = (i, t)
        if t: yrs[d].append(t[0])
    med = {d: statistics.median(v) for d, v in yrs.items()}
    viol = []
    for d, evs in bydoc.items():
        rec = DOCS.get(d)
        if not rec: continue
        for ed in rec["target_edges"]:
            a, b = ed["s"], ed["t"]
            if a not in evs or b not in evs: continue
            rel = ed["rel"] if mode == "gold" else PRED.get((d, a, b))
            if rel not in rels: continue
            (ia, ta), (ib, tb) = evs[a], evs[b]
            if ta is None or tb is None: continue
            if violates(rel, ta, tb): viol.append((d, ia, ib, ta, tb))
    raw = Counter()
    for d, ia, ib, ta, tb in viol: raw[ia] += 1; raw[ib] += 1
    blame = Counter()
    for d, ia, ib, ta, tb in viol:
        if raw[ia] != raw[ib]: blame[ia if raw[ia] > raw[ib] else ib] += 1
        else:
            da = abs(ta[0] - med.get(d, ta[0])); db = abs(tb[0] - med.get(d, tb[0]))
            blame[ia if da >= db else ib] += 1
    return {i for i, v in blame.items() if v >= 1}

def validity(items, mode):
    """False-alarm rate of each constraint on pairs where BOTH events are ground truth."""
    bydoc = defaultdict(dict)
    for i, (inp, lab, ct) in enumerate(items):
        if lab: continue
        d, e = inp["cluster_id"].split("::"); bydoc[d][e] = ts(inp["time_start"])
    st = defaultdict(Counter)
    for d, evs in bydoc.items():
        rec = DOCS.get(d)
        if not rec: continue
        for ed in rec["target_edges"]:
            a, b = ed["s"], ed["t"]
            if a not in evs or b not in evs or evs[a] is None or evs[b] is None: continue
            rel = ed["rel"] if mode == "gold" else PRED.get((d, a, b))
            v = violates(rel, evs[a], evs[b])
            if v is None: continue
            st[rel]["n"] += 1; st[rel]["v"] += v
    return st

CONN_AFTER = re.compile(r"\b(after|afterwards|following|later)\b", re.I)
CONN_WHEN = re.compile(r"\b(when|while|as|during|amid)\b", re.I)
def connective(items, mode):
    """'after' in the text while a same-sentence neighbour is related by a same-time relation.

    IMPLICIT_ORDERING turns 'when' into 'after'. 'after' asserts a sequence; if the graph
    relates this event to another event of the SAME sentence by SIMULTANEOUS / CONTAINS /
    OVERLAP, the sentence and the graph disagree.
    """
    bysent = defaultdict(list)
    for i, (inp, lab, ct) in enumerate(items):
        d, e = inp["cluster_id"].split("::"); bysent[(d, SENT.get((d, e)))].append((i, e))
    rel_of = {}
    for d, rec in DOCS.items():
        for ed in rec["target_edges"]:
            r = ed["rel"] if mode == "gold" else PRED.get((d, ed["s"], ed["t"]))
            if r: rel_of[(d, ed["s"], ed["t"])] = r; rel_of[(d, ed["t"], ed["s"])] = r
    out = set(); out_plain = set()
    for i, (inp, lab, ct) in enumerate(items):
        if not CONN_AFTER.search(inp["text_span"] or ""): continue
        out_plain.add(i)
        d, e = inp["cluster_id"].split("::")
        for j, f in bysent[(d, SENT.get((d, e)))]:
            if f == e: continue
            if rel_of.get((d, e, f)) in ("SIMULTANEOUS", "CONTAINS", "OVERLAP"):
                out.add(i); break
    return out, out_plain

TYPES = ("ANCHOR_CONFLICT", "ORDERING_CONFLICT", "GRANULARITY_CONFLICT", "IMPLICIT_ORDERING")
def row(nm, items, fl):
    P, R, F, bt = evaluate(items, fl)
    cell = "  ".join("%3d/%-3d" % bt.get(t, (0, 0)) for t in TYPES)
    print("  %-22s%8.2f%%%8.2f%%%8.2f%%   %s" % (nm, 100*P, 100*R, 100*F, cell))

print()
print("=" * 104)
print("DO TIN CAY CUA RANG BUOC DIEM BAT DAU tren cap GT-GT (ty le bao dong gia), muc 20%")
print("=" * 104)
it20 = build("valid", "20")
for mode in ("gold", "pred"):
    st = validity(it20, mode)
    print("  %s: " % mode + "  ".join("%s %.1f%% (%d)" % (r[:5], 100*c["v"]/c["n"], c["n"]) for r, c in sorted(st.items()) if c["n"]))

# ---------------------------------------------------------------- leak 13 quantified
print()
print("RO RI 13 -- text_span GAN TRUNG (0,85 < ratio < 1) voi mot dong anh em cung cau, muc 20%:")
bys = defaultdict(list)
for i, (inp, lab, ct) in enumerate(it20):
    d, e = inp["cluster_id"].split("::"); bys[(d, SENT.get((d, e)))].append(i)
hitc = Counter()
for i, (inp, lab, ct) in enumerate(it20):
    d, e = inp["cluster_id"].split("::")
    near = any(0.85 < difflib.SequenceMatcher(None, inp["text_span"], it20[j][0]["text_span"]).ratio() < 1.0
               for j in bys[(d, SENT.get((d, e)))] if j != i)
    hitc[(lab, near)] += 1
tp, fp = hitc[(True, True)], hitc[(False, True)]; pos = sum(1 for x in it20 if x[1])
print("  bat %d/%d conflict, bao dong gia %d GT  -> P %.1f%%  R %.1f%%   (KHONG dung lam detector)"
      % (tp, pos, fp, 100*tp/max(1, tp+fp), 100*tp/pos))

print()
print("=" * 104)
print("BENCHMARK TRUNG THUC -- detector mo rong (#2 moi quan he Allen, #3 tu noi)")
print("=" * 104)
REL_B = {"BEFORE"}
REL_ALL = {"BEFORE", "CONTAINS", "OVERLAP", "SIMULTANEOUS", "BEGINS-ON"}
for pct in ("05", "10", "15", "20"):
    items = build("valid", pct)
    pos = sum(1 for it in items if it[1])
    print()
    print("  muc %s%% -- %d conflict" % (pct, pos))
    print("  %-22s%9s%9s%9s   %s" % ("detector", "P", "R", "F1", "  ".join(t.split("_")[0][:5] for t in TYPES)))
    surf = {i for i, (inp, lab, ct) in enumerate(items) if (t := ts(inp["time_start"])) and t[1] == 1 and t[2] == 1}
    D = {}
    D["surface"] = surf
    D["blame BEFORE pred"] = consistency(items, "pred", REL_B)
    D["blame ALL pred  (#2)"] = consistency(items, "pred", REL_ALL)
    D["blame ALL gold  (#2)"] = consistency(items, "gold", REL_ALL)
    c_pred, c_plain = connective(items, "pred")
    D["'after' tran"] = c_plain
    D["'after'+do thi pred (#3)"] = c_pred
    D["surf+BEFORE (cu)"] = surf | D["blame BEFORE pred"]
    D["surf+ALL (#2)"] = surf | D["blame ALL pred  (#2)"]
    D["surf+ALL+conn (#2#3)"] = surf | D["blame ALL pred  (#2)"] | c_pred
    for nm, fl in D.items(): row(nm, items, fl)
