# -*- coding: utf-8 -*-
"""TIMEX-aware contextual representation for Bai 1, without touching target edges.

The earlier "+0.00 for structure" test collapsed the whole TIMEX neighbourhood into one
boolean, shared_timex = True/False. That is far too poor a representation to conclude
anything from, and the review was right to object.

This tests the representation properly, in three tracks:

  A  current            event + entity features (the 257-rule baseline's feature space)
  T1 intrinsic TIMEX    type, anchorability, count, distance, relative position -- all
                        read from TIMEX NODES, never from an event-timex edge
  T2 T1 + typed shared  the same, plus which KIND of timex sits where relative to the pair
  C  absolute anchors   T2 plus parsed calendar values -- kept separate, because a date
                        on each side very nearly answers the question

Everything in T1/T2 comes from node attributes (timex_type, anchorable, sent_first,
tok_first) and positional geometry. No temporal relation is read. Track C is reported
only as a ceiling, not as a candidate for the core setting.
"""
import sys, io, json, math, re, hashlib
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
PRIOR = {"BEFORE": .91045, "CONTAINS": .07430, "SIMULTANEOUS": .00862,
         "OVERLAP": .00597, "BEGINS-ON": .00044, "ENDS-ON": .00022}
Z = 1.959963985
MON = {m: i+1 for i, m in enumerate(
    "january february march april may june july august september october november december".split())}

def wlb(k, n):
    if n == 0: return 0.0
    p = k/n
    return (p + Z*Z/(2*n) - Z*math.sqrt(p*(1-p)/n + Z*Z/(4*n*n)))/(1 + Z*Z/n)
def macro(pred, gold):
    tp, fp, fn = Counter(), Counter(), Counter()
    for p, g in zip(pred, gold):
        if p == g: tp[g] += 1
        else: fp[p] += 1; fn[g] += 1
    per = {}
    for r in RELS:
        P = tp[r]/(tp[r]+fp[r]) if tp[r]+fp[r] else 0.0
        R = tp[r]/(tp[r]+fn[r]) if tp[r]+fn[r] else 0.0
        per[r] = 2*P*R/(P+R) if P+R else 0.0
    return sum(per.values())/6, per, sum(tp.values())/len(gold)
def bkt(d):
    if d == 0: return "0"
    if d == 1: return "1"
    if d <= 3: return "2-3"
    return "4+"
def parse_date(t):
    s = t.lower().replace(",", " ")
    y = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", s)
    if not y: return None
    yr = int(y.group(1)); mo = dy = 0
    for nm, num in MON.items():
        if nm[:3] in s: mo = num; break
    d = re.search(r"\b([0-3]?[0-9])\b(?!\d)", s)
    if d and mo:
        v = int(d.group(1))
        if 1 <= v <= 31: dy = v
    return (yr, mo, dy)

# ---------------------------------------------------------------- TIMEX context features
def timex_ctx(txs, ea, eb, track):
    """txs: list of (sent, tok, type, anchorable, date|None). ea/eb: sentence of each event.

    Reads only node attributes and positions. No event-timex relation is consulted.
    """
    out = []
    if not txs:
        out.append(("TX", "none", True))
        return out
    lo, hi = (ea, eb) if ea <= eb else (eb, ea)
    # --- T1: intrinsic and density
    n = len(txs)
    out.append(("TX", "n", "0" if n == 0 else ("1" if n == 1 else ("2-4" if n <= 4 else "5+"))))
    ty = Counter(t[2] for t in txs)
    for k in ("DATE", "TIME", "DURATION", "SET"):
        if ty.get(k): out.append(("TX", "has_" + k, True))
    if any(t[3] for t in txs): out.append(("TX", "has_anchorable", True))
    if any(not t[3] for t in txs): out.append(("TX", "has_vague", True))
    # nearest to each endpoint
    da = min(abs(t[0]-ea) for t in txs); db = min(abs(t[0]-eb) for t in txs)
    out.append(("TX", "dist_a", bkt(da)))
    out.append(("TX", "dist_b", bkt(db)))
    out.append(("TX", "same_sent_a", any(t[0] == ea for t in txs)))
    out.append(("TX", "same_sent_b", any(t[0] == eb for t in txs)))
    # --- position relative to the pair
    before = [t for t in txs if t[0] < lo]
    between = [t for t in txs if lo <= t[0] <= hi]
    after = [t for t in txs if t[0] > hi]
    out.append(("TX", "pos_before", bool(before)))
    out.append(("TX", "pos_between", bool(between)))
    out.append(("TX", "pos_after", bool(after)))
    out.append(("TX", "n_between", "0" if not between else ("1" if len(between) == 1 else "2+")))
    if track == "T1":
        return out
    # --- T2: typed position, which KIND of timex sits where
    for nm, grp in (("bef", before), ("btw", between), ("aft", after)):
        g = Counter(t[2] for t in grp)
        for k in ("DATE", "TIME", "DURATION"):
            if g.get(k): out.append(("TX", nm + "_" + k, True))
        if any(t[3] for t in grp): out.append(("TX", nm + "_anch", True))
    # typed nearest
    for nm, ev in (("a", ea), ("b", eb)):
        near = min(txs, key=lambda t: abs(t[0]-ev))
        out.append(("TX", "near_" + nm + "_type", near[2]))
        out.append(("TX", "near_" + nm + "_anch", near[3]))
    # does the same sentence hold a timex for BOTH endpoints
    out.append(("TX", "both_same_sent",
                any(t[0] == ea for t in txs) and any(t[0] == eb for t in txs)))
    if track == "T2":
        return out
    # --- C: absolute calendar values (ceiling only)
    da_ = [t[4] for t in txs if t[4] and abs(t[0]-ea) <= 1]
    db_ = [t[4] for t in txs if t[4] and abs(t[0]-eb) <= 1]
    if da_ and db_:
        x, y = min(da_), min(db_)
        out.append(("TX", "cal", "lt" if x < y else ("gt" if x > y else "eq")))
        out.append(("TX", "cal_yr", "lt" if x[0] < y[0] else ("gt" if x[0] > y[0] else "eq")))
    else:
        out.append(("TX", "cal", "unk"))
    return out

def load(path, limit=0):
    from mine_compositional import candidate_conditions, pair_features
    from mine_mdd import relational_conditions
    out = []
    for i, line in enumerate(io.open(path, encoding="utf-8")):
        if limit and i >= limit: break
        if not line.strip(): continue
        rec = json.loads(line); nd = rec["nodes"]; anch = defaultdict(set)
        for p in rec["anchored_pairs"]:
            for ra, rb in p["roles"]: anch[(p["a"], p["b"])].add((ra, rb))
        txs = []
        for k, v in nd.items():
            if v.get("kind") != "timex": continue
            txs.append((v.get("sent_first", -1), v.get("tok_first", -1),
                        v.get("timex_type"), bool(v.get("anchorable")),
                        parse_date(v.get("text", ""))))
        rows = []
        for e in rec["target_edges"]:
            a, b = e["s"], e["t"]
            na, nb = nd.get(a), nd.get(b)
            if not na or not nb or na.get("kind") != "event" or nb.get("kind") != "event": continue
            sh = anch.get((a, b)) or anch.get((b, a)) or set()
            f = pair_features(na, nb, sh, bool(sh), frozenset())
            base = frozenset(list(candidate_conditions(f)) + relational_conditions(na, nb, sh))
            ea = na.get("sent_first", 0) or 0; eb = nb.get("sent_first", 0) or 0
            ctx = {t: frozenset(timex_ctx(txs, ea, eb, t)) for t in ("T1", "T2", "C")}
            rows.append((a, b, e["rel"], base, ctx))
        if rows: out.append((rec["doc_id"], rows))
    return out

print("nap du lieu ...", flush=True)
TR = load(GRAPH/"train.jsonl", 400)
VA = load(GRAPH/"valid.jsonl", 0)
ntr = sum(len(r) for _, r in TR); nva = sum(len(r) for _, r in VA)
print("  train %s cap, valid %s cap" % (format(ntr, ","), format(nva, ",")), flush=True)

# ---------------------------------------------------------------- mine depth-2, same gates
def mine(docs, track, sup=25, kmin=10, dmin=5, target=0.40):
    cov = defaultdict(set); rel = []; doc = []
    i = 0
    for d, rows in docs:
        for (a, b, r, base, ctx) in rows:
            cs = base if track == "A" else (base | ctx[track])
            rel.append(r); doc.append(d)
            for c in cs: cov[c].add(i)
            i += 1
    keep = [c for c, s in cov.items() if len(s) >= sup]
    found = {}
    for r in RELS:
        kc = {c: sum(1 for j in cov[c] if rel[j] == r) for c in keep}
        order = sorted((c for c in keep if kc[c] >= kmin), key=lambda c: -kc[c])
        for ii, ci in enumerate(order):
            if wlb(kc[ci], kc[ci]) < target: break
            for cj in order[ii+1:]:
                m = min(kc[ci], kc[cj])
                if wlb(m, m) < target: break
                inter = cov[ci] & cov[cj]
                if len(inter) < sup: continue
                k = sum(1 for j in inter if rel[j] == r)
                if k < kmin: continue
                w = wlb(k, len(inter))
                if w < target: continue
                if len(set(doc[j] for j in inter if rel[j] == r)) < dmin: continue
                key = (ci, cj, r)
                if key not in found or w > found[key]: found[key] = w
    return found

def score(found, docs, track):
    """Inverted index: a rule is only considered when the pair has its first condition.

    Scanning all rules for every pair is 100k x 110k = 11 billion checks. Indexing by the
    first condition cuts that to the rules a pair could possibly match.
    """
    byc = defaultdict(list)
    for (ci, cj, rr), w in found.items():
        byc[ci].append((cj, rr, w/PRIOR[rr]))
    gold = []; pred = []
    for d, rows in docs:
        for (a, b, r, base, ctx) in rows:
            cs = base if track == "A" else (base | ctx[track])
            gold.append(r)
            sc = {}
            for c in cs:
                for cj, rr, v in byc.get(c, ()):
                    if cj in cs and v > sc.get(rr, 0): sc[rr] = v
            pred.append(max(sc, key=sc.get) if sc else "BEFORE")
    return macro(pred, gold)

print()
print("=" * 94)
print("TIMEX-AWARE CONTEXT: cung miner, cung cong loc, chi khac khong gian dac trung")
print("=" * 94)
print("  %-38s%8s%11s%10s" % ("khong gian dac trung", "#luat", "macro-F1", "acc"))
print("  " + "-" * 68)
res = {}
for track, nm in (("A",  "A   event + entity (hien tai)"),
                  ("T1", "T1  + TIMEX noi tai (type/anchor/vi tri)"),
                  ("T2", "T2  + TIMEX co phan loai theo vi tri"),
                  ("C",  "C   + gia tri lich tuyet doi (tran)")):
    print("    ... dang mine %s" % track, flush=True)
    f = mine(TR, track)
    print("    ... %s luat, dang cham" % format(len(f), ","), flush=True)
    m, per, acc = score(f, VA, track)
    res[track] = (m, per, acc, len(f))
    print("  %-38s%8s%10.2f%%%9.2f%%" % (nm, format(len(f), ","), 100*m, 100*acc))
    print("       " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per[r]) for r in RELS))
print()
mA = res["A"][0]
for t in ("T1", "T2", "C"):
    print("  %-6s chenh so voi A: %+.2f diem" % (t, 100*(res[t][0]-mA)))
