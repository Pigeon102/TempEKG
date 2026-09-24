# -*- coding: utf-8 -*-
"""Systematic heterogeneous motif mining over the event+TIMEX temporal graph.

Earlier conclusions that "the graph is exhausted" rested on three families only:
triangles A-E-B, triads A-T-B, and 4-node STAR motifs over events. Two gaps remain:

  1. PATH motifs A-X-Y-B were never tested, for any node types. The TIMEX-TIMEX path
     A-T1-T2-B is the date bridge generalised, and was never used as a classifier feature.
  2. Every earlier "realistic" run mined signatures on GOLD context labels and applied them
     to PREDICTED ones -- a train/test mismatch. Mining directly on predicted context, so the
     rules learn the classifier's own noise, was never tried.

Families, for a target event pair (A,B):
  3E   A-E-B          3T   A-T-B
  4EE  A-E-E-B        4ET  A-E-T-B        4TE  A-T-E-B        4TT  A-T-T-B

Modes:
  gold  context labels gold, mined and applied on gold          (oracle, not reachable)
  pg    mined on gold, applied on predicted                     (what earlier runs did)
  pp    mined on predicted, applied on predicted                (new; realistic)
  st    node types + TIMEX type only, no relation labels        (legal structure)

Predicted context:
  EV-EV   the 257-rule classifier
  EV-TX   an EV-TIMEX classifier mined on discovery documents
  TX-TX   calendar comparison of the two TIMEX texts (node attributes), else UNK

Protocol per family and mode: mine on DISCOVERY (229 docs), confirm on CONFIRMATION
(171 docs), keep top 70% by confirmation Wilson bound, evaluate once on VALID (705 docs)
by adding the family's evidence to the 257-rule scores under max-norm, tau = 5.
"""
import sys, io, json, math, re, hashlib, time
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V
from mine_compositional import candidate_conditions, pair_features
from mine_mdd import relational_conditions

T0 = time.time()
def log(*a):
    print("[%5.0fs] " % (time.time()-T0) + " ".join(str(x) for x in a), flush=True)

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
PRIOR = {"BEFORE": .91045, "CONTAINS": .07430, "SIMULTANEOUS": .00862,
         "OVERLAP": .00597, "BEGINS-ON": .00044, "ENDS-ON": .00022}
SYM = {"SIMULTANEOUS", "BEGINS-ON", "UNK", "*"}
FAMS = ["3E", "3T", "4EE", "4ET", "4TE", "4TT"]
CAP = 6
Z = 1.959963985
MON = {m: i+1 for i, m in enumerate(
    "january february march april may june july august september october november december".split())}

def inv(l):
    if l in SYM: return l
    return l[1:] if l.startswith("i") else "i" + l
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
def parse_date(t):
    s = (t or "").lower().replace(",", " ")
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
def split_of(doc):
    return "conf" if int(hashlib.md5(doc.encode()).hexdigest(), 16) % 10 < 4 else "disc"

# ---------------------------------------------------------------- load
def load(path, limit=0):
    out = []
    for i, line in enumerate(io.open(path, encoding="utf-8")):
        if limit and i >= limit: break
        if not line.strip(): continue
        rec = json.loads(line); nd = rec["nodes"]; anch = defaultdict(set)
        for p in rec["anchored_pairs"]:
            for ra, rb in p["roles"]: anch[(p["a"], p["b"])].add((ra, rb))
        doc = {"id": rec["doc_id"], "nd": nd, "ee": [], "tx": [], "tt": [], "edges": []}
        for e in rec["target_edges"]:
            a, b, r = e["s"], e["t"], e["rel"]
            ka = nd.get(a, {}).get("kind"); kb = nd.get(b, {}).get("kind")
            if ka not in ("event", "timex") or kb not in ("event", "timex"): continue
            doc["edges"].append((a, b, r))
            if ka == "event" and kb == "event":
                sh = anch.get((a, b)) or anch.get((b, a)) or set()
                f = pair_features(nd[a], nd[b], sh, bool(sh), frozenset())
                cs = frozenset(list(candidate_conditions(f)) + relational_conditions(nd[a], nd[b], sh))
                doc["ee"].append((a, b, r, f, cs))
            elif ka == "event":
                doc["tx"].append((a, b, "E", r))          # event -> timex
            elif kb == "event":
                doc["tx"].append((b, a, "T", r))          # timex -> event, stored as (event, timex)
            else:
                doc["tt"].append((a, b, r))
        if doc["ee"]: out.append(doc)
    return out

log("nap train/valid ...")
TR = load(GRAPH/"train.jsonl", 400)
VA = load(GRAPH/"valid.jsonl", 0)
DISC = [d for d in TR if split_of(d["id"]) == "disc"]
CONF = [d for d in TR if split_of(d["id"]) == "conf"]
log("train %d doc (disc %d / conf %d), valid %d doc" % (len(TR), len(DISC), len(CONF), len(VA)))

# ---------------------------------------------------------------- predicted EV-EV (257 rules)
rules = V.load_rules(ART/"rules_rx_c70.json")
def pair_scores(docs):
    flat = [(f, cs) for d in docs for (_, _, _, f, cs) in d["ee"]]
    idx = V.build_index(rules, [(None, f, cs) for f, cs in flat])
    for d in docs:
        d["ps"] = []; d["pp"] = []
        for (a, b, g, f, cs) in d["ee"]:
            sc = {}
            for ri in V.firing(rules, idx, f, cs):
                ru = rules[ri]; v = ru["wlb"]/PRIOR[ru["rel"]]
                if v > sc.get(ru["rel"], 0): sc[ru["rel"]] = v
            d["ps"].append(sc)
            d["pp"].append(max(sc, key=sc.get) if sc and max(sc.values()) >= 5 else "BEFORE")
pair_scores(TR); pair_scores(VA)
for nm, docs in (("disc (in-sample)", DISC), ("valid", VA)):
    g = [r[2] for d in docs for r in d["ee"]]; p = [x for d in docs for x in d["pp"]]
    log("  257 luat EV-EV tren %-17s acc %.2f%%  loi %.2f%%" % (nm, 100*sum(a == b for a, b in zip(g, p))/len(g),
        100*sum(a != b for a, b in zip(g, p))/len(g)))

# ---------------------------------------------------------------- predicted EV-TX
def tx_feats(dr, ev, t):
    f = [("dir", dr), ("etype", ev.get("type")), ("ttype", t.get("timex_type")), ("anch", t.get("anchorable"))]
    se, st = ev.get("sent_first"), t.get("sent_first")
    if se is not None and st is not None:
        dd = se - st
        f.append(("sdist", "0" if dd == 0 else ("e>t" if dd > 0 else "t>e")))
        f.append(("adist", "0" if dd == 0 else ("1" if abs(dd) == 1 else ("2-4" if abs(dd) <= 4 else "5+"))))
    f.append(("bucket", ev.get("sent_bucket"))); f.append(("nrole", min(ev.get("n_role", 0), 4)))
    for r in (ev.get("roleset") or ())[:4]: f.append(("role", r))
    return frozenset(f)
cnt = defaultdict(Counter); cdoc = defaultdict(lambda: defaultdict(set))
for d in DISC:
    for (e, t, dr, r) in d["tx"]:
        for c in tx_feats(dr, d["nd"][e], d["nd"][t]):
            cnt[c][r] += 1; cdoc[c][r].add(d["id"])
TXR = {}
for c, cc in cnt.items():
    n = sum(cc.values()); top, k = cc.most_common(1)[0]
    if n >= 30 and k >= 10 and len(cdoc[c][top]) >= 5 and wlb(k, n) >= 0.40: TXR[c] = (top, wlb(k, n))
def pred_tx(dr, ev, t):
    sc = {}
    for c in tx_feats(dr, ev, t):
        x = TXR.get(c)
        if x:
            v = x[1]/PRIOR[x[0]]
            if v > sc.get(x[0], 0): sc[x[0]] = v
    return max(sc, key=sc.get) if sc else "BEFORE"
g = p = 0
for d in VA:
    for (e, t, dr, r) in d["tx"]:
        g += 1; p += pred_tx(dr, d["nd"][e], d["nd"][t]) == r
log("  classifier EV-TX (%d luat) tren valid: %.2f%%" % (len(TXR), 100*p/g))

def pred_tt(nd, a, b):
    x, y = parse_date(nd[a].get("text")), parse_date(nd[b].get("text"))
    if not x or not y: return "UNK"
    if x[1] and x[2] and y[1] and y[2]:
        return "BEFORE" if x < y else ("SIMULTANEOUS" if x == y else "iBEFORE")
    if x[0] != y[0]: return "BEFORE" if x[0] < y[0] else "iBEFORE"
    return "UNK"
tg = tk = tu = 0
for d in VA:
    for (a, b, r) in d["tt"]:
        pr = pred_tt(d["nd"], a, b); tg += 1
        if pr == "UNK": tu += 1
        elif pr == r: tk += 1
log("  TX-TX theo lich tren valid: %d canh, UNK %.1f%%, dung %.1f%% trong so da quyet dinh"
    % (tg, 100*tu/tg, 100*tk/max(1, tg-tu)))

# ---------------------------------------------------------------- label maps and motif instances
def labmap(d, mode):
    L = {}
    if mode == "gold":
        for (a, b, r) in d["edges"]: L[(a, b)] = r; L[(b, a)] = inv(r)
        return L
    if mode == "st":
        for (a, b, r) in d["edges"]: L[(a, b)] = "*"; L[(b, a)] = "*"
        return L
    for (a, b, r), p in zip([(x[0], x[1], x[2]) for x in d["ee"]], d["pp"]):
        L[(a, b)] = p; L[(b, a)] = inv(p)
    for (e, t, dr, r) in d["tx"]:
        p = pred_tx(dr, d["nd"][e], d["nd"][t])
        if dr == "E": L[(e, t)] = p; L[(t, e)] = inv(p)
        else:         L[(t, e)] = p; L[(e, t)] = inv(p)
    for (a, b, r) in d["tt"]:
        p = pred_tt(d["nd"], a, b); L[(a, b)] = p; L[(b, a)] = inv(p)
    return L

def instances(d):
    """Motif instances per target pair -- structure only, computed once and reused."""
    nbr = defaultdict(set)
    for (a, b, r) in d["edges"]: nbr[a].add(b); nbr[b].add(a)
    K = lambda x: "E" if d["nd"][x].get("kind") == "event" else "T"
    out = []
    for (a, b, g, f, cs) in d["ee"]:
        Na = nbr[a] - {a, b}; Nb = nbr[b] - {a, b}
        byf = defaultdict(list)
        for x in Na & Nb: byf["3" + K(x)].append((x,))
        for x in Na:
            for y in nbr[x]:
                if y in Nb and y != x: byf["4" + K(x) + K(y)].append((x, y))
        inst = []
        for fam, lst in byf.items():
            for nodes in sorted(lst)[:CAP]: inst.append((fam, nodes))
        out.append(inst)
    d["inst"] = out
log("dung motif ...")
for d in TR + VA: instances(d)
cov = Counter(); npair = 0
for d in VA:
    for inst in d["inst"]:
        npair += 1
        for fam in {f for f, _ in inst}: cov[fam] += 1
log("  do phu motif tren valid (%s cap): %s" % (format(npair, ","),
    "  ".join("%s %.1f%%" % (f, 100*cov[f]/npair) for f in FAMS)))

def sigs(d, mode):
    L = labmap(d, mode); nd = d["nd"]; out = []
    for (a, b, g, f, cs), inst in zip(d["ee"], d["inst"]):
        s = []
        for fam, nodes in inst:
            if mode == "st":
                s.append(fam + "|" + "|".join(nd[x].get("timex_type") or nd[x].get("kind") for x in nodes))
            elif len(nodes) == 1:
                x = nodes[0]; s.append(fam + "|" + L[(a, x)] + "|" + L[(x, b)])
            else:
                x, y = nodes; s.append(fam + "|" + L[(a, x)] + "|" + L[(x, y)] + "|" + L[(y, b)])
        out.append(s)
    return out

def mine(disc_sigs, conf_sigs, fam):
    """Per-LABEL mining, prior-aware -- the lesson Bai 1 already paid for.

    The first version kept only each signature's MAJORITY label and required wlb >= 0.50.
    On predicted context every signature's majority is BEFORE, and a BEFORE rule scores
    wlb/0.91 <= 1.1, which can never reach tau = 5 -- so the pp column came out at exactly
    +0.00 as an artifact of the gate, not as evidence. This version:
      * considers every label of every signature, not only the majority
      * candidate if n >= 30, k >= 10, >= 5 documents, and the label is ENRICHED:
        lift >= 2 and LCB-lift = wlb/prior >= 1.5
      * confirmed if still enriched on CONFIRMATION (cwlb/prior >= 1.5, cn >= 10)
      * keeps the top 70% by confirmation Wilson bound WITHIN each label
    BEFORE can never reach lift 2 (prior 0.91), which is fine: it is the fallback already.
    """
    cnt = defaultdict(Counter); dd = defaultdict(lambda: defaultdict(set))
    for d, S in zip(DISC, disc_sigs):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for x in s:
                if fam == "ALL" or x.startswith(fam + "|"):
                    cnt[x][g] += 1; dd[x][g].add(d["id"])
    cand = []
    for x, c in cnt.items():
        n = sum(c.values())
        if n < 30: continue
        for r, k in c.items():
            if k < 10 or len(dd[x][r]) < 5: continue
            if (k/n)/PRIOR[r] >= 2 and wlb(k, n)/PRIOR[r] >= 1.5: cand.append((x, r))
    need = {x for x, r in cand}
    cc = defaultdict(Counter)
    for d, S in zip(CONF, conf_sigs):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for x in s:
                if x in need: cc[x][g] += 1
    bylab = defaultdict(list)
    for x, r in cand:
        cn = sum(cc[x].values())
        if cn < 10: continue
        cw = wlb(cc[x][r], cn)
        if cw/PRIOR[r] >= 1.5: bylab[r].append((cw, x))
    R = {}
    for r, lst in bylab.items():
        lst.sort(reverse=True)
        for cw, x in lst[:max(1, int(0.7*len(lst)))]:
            if x not in R or cw/PRIOR[r] > R[x][1]/PRIOR[R[x][0]]: R[x] = (r, cw)
    return R

GOLD = [r[2] for d in VA for r in d["ee"]]
def evaluate(R, val_sigs):
    pred = []; fired = 0
    for d, S in zip(VA, val_sigs):
        for sc0, s in zip(d["ps"], S):
            sc = dict(sc0); hit = False
            for x in s:
                t = R.get(x)
                if t:
                    hit = True; v = t[1]/PRIOR[t[0]]
                    if v > sc.get(t[0], 0): sc[t[0]] = v
            fired += hit
            pred.append(max(sc, key=sc.get) if sc and max(sc.values()) >= 5 else "BEFORE")
    m, per, acc = macro(pred, GOLD)
    return m, per, acc, fired/len(GOLD)

m0, per0, a0 = macro([x for d in VA for x in d["pp"]], GOLD)
log("BASE 257 luat: macro-F1 %.2f%%  acc %.2f%%" % (100*m0, 100*a0))
RES = []
def report(fam, mode, R, val_sigs):
    m, per, acc, fr = evaluate(R, val_sigs)
    RES.append((fam, mode, len(R), fr, m, per, acc))
    if fam == "ALL": log("     nhan cua luat: %s" % dict(Counter(v[0] for v in R.values()).most_common()))
    log("  %-4s %-4s %4d luat  ban %5.1f%%  macro %6.2f%%  (%+.2f)  CONT %.1f SIMU %.1f OVER %.1f"
        % (fam, mode, len(R), 100*fr, 100*m, 100*(m-m0), 100*per["CONTAINS"],
           100*per["SIMULTANEOUS"], 100*per["OVERLAP"]))

# ---------------------------------------------------------------- gold (oracle)
log("=== che do GOLD (oracle) ===")
dS = [sigs(d, "gold") for d in DISC]; cS = [sigs(d, "gold") for d in CONF]; vS = [sigs(d, "gold") for d in VA]
RG = {}
for fam in FAMS + ["ALL"]:
    RG[fam] = mine(dS, cS, fam); report(fam, "gold", RG[fam], vS)
del dS, cS, vS

# ---------------------------------------------------------------- predicted
log("=== che do DU DOAN ===")
vP = [sigs(d, "pred") for d in VA]
for fam in FAMS + ["ALL"]: report(fam, "pg", RG[fam], vP)
dP = [sigs(d, "pred") for d in DISC]; cP = [sigs(d, "pred") for d in CONF]
for fam in FAMS + ["ALL"]:
    report(fam, "pp", mine(dP, cP, fam), vP)
del dP, cP, vP

# ---------------------------------------------------------------- structure only
log("=== che do CAU TRUC ===")
dS = [sigs(d, "st") for d in DISC]; cS = [sigs(d, "st") for d in CONF]; vS = [sigs(d, "st") for d in VA]
for fam in FAMS + ["ALL"]:
    report(fam, "st", mine(dS, cS, fam), vS)

print()
print("=" * 104)
print("TONG HOP -- base 257 luat macro-F1 %.2f%%" % (100*m0))
print("=" * 104)
print("  %-5s" % "ho" + "".join("%18s" % m for m in ("gold (oracle)", "pg (cu)", "pp (moi)", "st (cau truc)")))
for fam in FAMS + ["ALL"]:
    row = "  %-5s" % fam
    for mode in ("gold", "pg", "pp", "st"):
        r = [x for x in RES if x[0] == fam and x[1] == mode][0]
        row += "%11.2f (%+.2f)" % (100*r[4], 100*(r[4]-m0))
    print(row)
log("xong")
