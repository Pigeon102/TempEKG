# -*- coding: utf-8 -*-
"""Re-verify higher-order structures (bo 3 / bo 4 / bo 5) under a clean protocol.

The earlier quintuple study (quint.py) is void: its adjacency gave the reverse direction the SAME
label (adj[b][a] = r, LUAT_BAC_CAO 10.1), it mined on 400 documents, summed votes, and its
signatures depended on node-id order. This script redoes it on the current pipeline.

Structure around a target edge (a, b), all four edge types, neighbours may be events or TIMEX:
  bo 3   one common neighbour c           atom(c) = (kind c, L(a,c), L(c,b))          (a triangle)
  bo 4   two common neighbours {c, d}     sorted pair of atoms                        (two triangles on ab)
  bo 4K  same plus the label L(c,d)       the full 4-clique (6 edges), when c-d is an edge
  bo 5   three common neighbours          sorted triple of atoms
L(x,y) is the label of the edge in its stored direction, or the CONVERSE label (~r) when the edge
is stored as (y, x). Neighbours: all common neighbours except a and b, sorted by node id, first
CAP = 6 (frozen protocol: candidates -> drop self -> CAP).

Neighbour labels come from GOLD (oracle, a ceiling that is not reachable at test time) or from the
current layered classifier's PREDICTIONS (realistic; pred_layered_full.json, TAG=_full pipeline).

Protocol (same as the main pipeline):
  mine       DISCOVERY: signature -> label r with n >= 30, k >= 10, >= 5 documents,
             k/n >= min(1.5 * prior_r, (1 + prior_r)/2) and wlb > prior_r   (prior per edge type)
  confirm    CONFIRMATION-1: cn >= 10 and wlb(ck, cn) > prior_r
  combiner   highest confirmed wlb among firing rules whose wlb clears the floor of (edge type,
             label); floors by coordinate ascent on CONFIRMATION-2 macro-F1
  modes      override: a firing rule replaces the classifier's label (what Bai 1 could use)
             alone:    no firing rule -> BEFORE (the structure by itself)
  valid      opened once per configuration
Usage: python motif345.py gold|pred
"""
import sys, io, json, math, hashlib, time
from collections import Counter, defaultdict
from pathlib import Path
from itertools import combinations

SRC = Path(r"C:\Reseach_Quang\tempekg\src"); GRAPH = SRC/"graph"; ART = SRC/"artifacts"
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
SYM = {"SIMULTANEOUS", "BEGINS-ON"}
CAP = 6; Z = 1.959963985
NB = sys.argv[1] if len(sys.argv) > 1 else "gold"
T0 = time.time()
def log(*a): print("[%6.0fs] " % (time.time() - T0) + " ".join(str(x) for x in a), flush=True)
def wlb(k, n):
    if n == 0: return 0.0
    p = k/n
    return (p + Z*Z/(2*n) - Z*math.sqrt(p*(1-p)/n + Z*Z/(4*n*n)))/(1 + Z*Z/n)
def h(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)
def split_of(doc):
    if h(doc) % 10 >= 4: return 0
    return 1 if h("s2" + doc) % 2 == 0 else 2
def conv(r): return r if r in SYM else ("~" + r if not r.startswith("~") else r[1:])

PRED = json.load(io.open(ART/"pred_layered_full.json", encoding="utf-8"))
DOCS = []                                   # (doc, split, kinds, edges[(a,b,gold,pred,etype)])
for split, sp_fixed in (("train", None), ("valid", 3)):
    for line in io.open(GRAPH/f"{split}.jsonl", encoding="utf-8"):
        rec = json.loads(line); nd = rec["nodes"]; doc = rec["doc_id"]
        K = {}; es = []
        for e in rec["target_edges"]:
            na, nb = nd.get(e["s"]), nd.get(e["t"])
            if not na or not nb: continue
            ka = "E" if na["kind"] == "event" else "T"; kb = "E" if nb["kind"] == "event" else "T"
            K[e["s"]] = ka; K[e["t"]] = kb
            p = PRED["%s|%s|%s" % (doc, e["s"], e["t"])]
            es.append((e["s"], e["t"], e["rel"], p, ka + kb))
        if es: DOCS.append((doc, split_of(doc) if sp_fixed is None else 3, K, es))
log("%d document; neighbour labels = %s" % (len(DOCS), NB))

def instances(doc_item, orders):
    """Yield (edge record, {order: [signatures]}) for every target edge of a document."""
    doc, sp, K, es = doc_item
    L = {}; nbr = defaultdict(set)
    for a, b, g, p, t in es:
        r = g if NB == "gold" else p
        L[(a, b)] = r; L[(b, a)] = conv(r); nbr[a].add(b); nbr[b].add(a)
    for a, b, g, p, t in es:
        mids = sorted(c for c in nbr[a] & nbr[b] if c not in (a, b))[:CAP]
        atoms = {c: (K[c], L[(a, c)], L[(c, b)]) for c in mids}
        sig = {}
        if "3" in orders: sig["3"] = [(t, atoms[c]) for c in mids]
        if "4" in orders or "4K" in orders:
            s4 = []; s4k = []
            for c, d in combinations(mids, 2):
                pair = tuple(sorted((atoms[c], atoms[d])))
                s4.append((t,) + pair)
                if (c, d) in L:
                    cd = L[(c, d)] if atoms[c] <= atoms[d] else L[(d, c)]
                    s4k.append((t,) + pair + (cd,))
            sig["4"] = s4; sig["4K"] = s4k
        if "5" in orders: sig["5"] = [(t,) + tuple(sorted((atoms[c], atoms[d], atoms[e]))) for c, d, e in combinations(mids, 3)]
        yield (doc, t, g, p), sig

ORDERS = ("3", "4", "4K", "5")
prior = defaultdict(Counter)
for doc, sp, K, es in DOCS:
    if sp == 0:
        for a, b, g, p, t in es: prior[t][g] += 1
PRIOR = {t: {r: c[r]/sum(c.values()) for r in c} for t, c in prior.items()}

# ------------------------------------------------ mine on DISCOVERY
cnt = {o: defaultdict(Counter) for o in ORDERS}
for d in DOCS:
    if d[1] != 0: continue
    for (doc, t, g, p), sig in instances(d, ORDERS):
        for o in ORDERS:
            for s in set(sig[o]): cnt[o][s][g] += 1
pre = {o: {} for o in ORDERS}                # gates that need only counts
for o in ORDERS:
    for s, c in cnt[o].items():
        n = sum(c.values())
        if n < 30: continue
        for r, k in c.items():
            pr = PRIOR[s[0]].get(r, 0)
            if pr == 0 or k < 10: continue
            if k/n >= min(1.5*pr, (1 + pr)/2) and wlb(k, n) > pr: pre[o][(s, r)] = (k, n)
    log("bo %s: %d chu ky, %d qua cong dem" % (o, len(cnt[o]), len(pre[o])))
del cnt
dsets = {o: defaultdict(set) for o in ORDERS}   # second pass: documents of the correct firings
want = {o: {s for s, r in pre[o]} for o in ORDERS}
for d in DOCS:
    if d[1] != 0: continue
    for (doc, t, g, p), sig in instances(d, ORDERS):
        for o in ORDERS:
            for s in set(sig[o]):
                if s in want[o] and (s, g) in pre[o]: dsets[o][(s, g)].add(doc)
cand = {o: {k: v for k, v in pre[o].items() if len(dsets[o][k]) >= 5} for o in ORDERS}
for o in ORDERS: log("bo %s: %d ung vien (>= 5 document)" % (o, len(cand[o])))
del dsets, pre

# ------------------------------------------------ confirm on CONF-1
cc = {o: defaultdict(Counter) for o in ORDERS}
need = {o: {s for s, r in cand[o]} for o in ORDERS}
for d in DOCS:
    if d[1] != 1: continue
    for (doc, t, g, p), sig in instances(d, ORDERS):
        for o in ORDERS:
            for s in set(sig[o]):
                if s in need[o]: cc[o][s][g] += 1
RULES = {o: {} for o in ORDERS}              # signature -> list of (label, cwlb)
for o in ORDERS:
    for (s, r), (k, n) in cand[o].items():
        cn = sum(cc[o][s].values()); ck = cc[o][s][r]
        if cn < 10: continue
        cw = wlb(ck, cn)
        if cw > PRIOR[s[0]].get(r, 0): RULES[o].setdefault(s, []).append((r, cw))
    log("bo %s: %d luat sau xac nhan (%s)" % (o, sum(len(v) for v in RULES[o].values()),
        dict(Counter(r for v in RULES[o].values() for r, _ in v))))
del cc

# ------------------------------------------------ firing lists on CONF-2 and valid
def fire(sp):
    out = []
    for d in DOCS:
        if d[1] != sp: continue
        for (doc, t, g, p), sig in instances(d, ORDERS):
            f = {}
            for o in ORDERS:
                best = {}
                for s in set(sig[o]):
                    for r, cw in RULES[o].get(s, ()):
                        if cw > best.get(r, 0): best[r] = cw
                f[o] = best
            out.append((t, g, p, f))
    return out
F2 = fire(2); FV = fire(3)
log("ban luat: CONF-2 %d canh, valid %d canh" % (len(F2), len(FV)))

def macro(pred, gold):
    tp, fp, fn = Counter(), Counter(), Counter()
    for q, g in zip(pred, gold):
        if q == g: tp[g] += 1
        else: fp[q] += 1; fn[g] += 1
    per = {}
    for r in RELS:
        P = tp[r]/(tp[r] + fp[r]) if tp[r] + fp[r] else 0.0; R = tp[r]/(tp[r] + fn[r]) if tp[r] + fn[r] else 0.0
        per[r] = 2*P*R/(P + R) if P + R else 0.0
    return sum(per.values())/6, per, sum(tp.values())/len(gold)

def merged(rows, cfg):
    """Per row: (edge type, gold, classifier label, {label: best cwlb over the configuration})."""
    out = []
    for t, g, p, f in rows:
        m = {}
        for o in cfg:
            for r, cw in f[o].items():
                if cw > m.get(r, 0): m[r] = cw
        out.append((t, g, p, m))
    return out

def decide(rows, TH, mode):
    out = []
    for t, g, p, m in rows:
        best = None
        for r, cw in m.items():
            if cw >= TH.get((t, r), 9) and (best is None or cw > best[1]): best = (r, cw)
        out.append(best[0] if best else (p if mode == "override" else "BEFORE"))
    return out

def macro_counts(tp, fp, fn):
    per = {}
    for r in RELS:
        P = tp[r]/(tp[r] + fp[r]) if tp[r] + fp[r] else 0.0; R = tp[r]/(tp[r] + fn[r]) if tp[r] + fn[r] else 0.0
        per[r] = 2*P*R/(P + R) if P + R else 0.0
    return sum(per.values())/6

def tune(cfg, mode):
    rows = merged(F2, cfg)
    fired = [x for x in rows if x[3]]; still = [x for x in rows if not x[3]]
    tp0, fp0, fn0 = Counter(), Counter(), Counter()
    for t, g, p, m in still:
        q = p if mode == "override" else "BEFORE"
        if q == g: tp0[g] += 1
        else: fp0[q] += 1; fn0[g] += 1
    def val(TH):
        tp, fp, fn = Counter(tp0), Counter(fp0), Counter(fn0)
        for (t, g, p, m), q in zip(fired, decide(fired, TH, mode)):
            if q == g: tp[g] += 1
            else: fp[q] += 1; fn[g] += 1
        return macro_counts(tp, fp, fn)
    keys = sorted({(t, r) for t, g, p, m in fired for r in m})
    TH = {k: 9 for k in keys}; best = val(TH)
    for _ in range(2):
        for k in keys:
            for th in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 9):
                T2 = dict(TH); T2[k] = th; v = val(T2)
                if v > best: best, TH = v, T2
    return TH, best

gv = [x[1] for x in FV]
base = macro([x[2] for x in FV], gv)
print(); print("=" * 110)
print("BO 3 / 4 / 5 -- hang xom %s, ca bon loai canh, valid mo mot lan" % ("GOLD (tran)" if NB == "gold" else "DU DOAN (thuc te)"))
print("=" * 110)
print("  classifier hien tai (buoc 2.2): macro-F1 %.2f%%  acc %.2f%%" % (100*base[0], 100*base[2]))
import os
if os.environ.get("SAVE_OVERRIDE"):
    # write the override predictions of one configuration (floors chosen on CONF-2) into a copy of the
    # layered prediction file, so the triangle step / Bai 2 can run on top of them (TAG=_full_motif)
    cfg = tuple(os.environ["SAVE_OVERRIDE"].split(","))
    TH, m2 = tune(cfg, "override")
    pv = decide(merged(FV, cfg), TH, "override")
    keys = ["%s|%s|%s" % (doc, a, b) for doc, sp, K, es in DOCS if sp == 3 for a, b, g, p, t in es]
    assert len(keys) == len(pv)
    m, per, acc = macro(pv, gv)
    print("  luu cau hinh %s (ghi de): CONF-2 %.2f%%, valid macro-F1 %.2f%% acc %.2f%%, doi %d nhan valid" %
          ("+".join(cfg), 100*m2, 100*m, 100*acc, sum(1 for x, q in zip(FV, pv) if q != x[2])))
    P = dict(PRED)
    for k, q in zip(keys, pv): P[k] = q
    json.dump(P, io.open(ART/"pred_layered_full_motif.json", "w", encoding="utf-8"))
    log("da luu pred_layered_full_motif.json; xong")
    sys.exit(0)
CFGS = (("bo 3", ("3",)), ("bo 4", ("4",)), ("bo 4K (du 6 canh)", ("4K",)), ("bo 5", ("5",)),
        ("bo 3 + 4", ("3", "4")), ("bo 3 + 4K", ("3", "4K")), ("bo 3 + 4 + 5", ("3", "4", "5")))
for mode in ("override", "alone"):
    print("\n  che do: %s" % ("GHI DE len classifier" if mode == "override" else "DUNG MOT MINH (khong co luat -> BEFORE)"))
    for nm, cfg in CFGS:
        TH, m2 = tune(cfg, mode)
        pv = decide(merged(FV, cfg), TH, mode); m, per, acc = macro(pv, gv)
        types = []
        for tt in ("EE", "ET", "TE", "TT"):
            idx = [i for i, x in enumerate(FV) if x[0] == tt]
            types.append("%s %.2f" % (tt, 100*macro([pv[i] for i in idx], [gv[i] for i in idx])[0]))
        on = sum(1 for k, v in TH.items() if v < 9)
        print("    %-20s CONF-2 %.2f%%  VALID macro-F1 %.2f%% (%+.2f)  acc %.2f%%  | %s | F1 %s | %d nguong bat" %
              (nm, 100*m2, 100*m, 100*(m - base[0]), 100*acc, "  ".join(types),
               " ".join("%s %.1f" % (r[:4], 100*per[r]) for r in RELS[:4]), on))
log("xong")
