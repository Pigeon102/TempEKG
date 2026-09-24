# -*- coding: utf-8 -*-
"""Is the +2.69 from EV-TIMEX patterns real, or is it reading target edges?

The triad signature is (rel(A,T), rel(B,T)). Both of those are event-timex edges, and in
MAVEN-ERE every temporal relation -- EV-EV, EV-TIMEX, TIMEX-TIMEX alike -- sits in
target_edges. So the gain measured with gold anchors is an ORACLE number, the same shape
as the 38.30% from EV-EV triangles.

Three settings separate the cases:

  ORACLE     gold EV-TIMEX anchors                         (what was measured: +2.69)
  PREDICTED  an EV-TIMEX classifier trained on train docs, its output used as anchors
  STRUCTURE  only the FACT that A and B share a TIMEX, never which relation holds

STRUCTURE is the one that is unambiguously legal at test time: whether an event-timex
edge exists is given by the candidate set, the same way event-event candidacy is given.
If STRUCTURE alone carries the gain, the finding survives. If only ORACLE does, this is
the EV-EV triangle story again.
"""
import sys, io, json, math, hashlib
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
PRIOR = {"BEFORE": .91045, "CONTAINS": .07430, "SIMULTANEOUS": .00862,
         "OVERLAP": .00597, "BEGINS-ON": .00044, "ENDS-ON": .00022}
Z = 1.959963985
CAPT = 4

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
def disc(doc):
    return int(hashlib.md5(doc.encode()).hexdigest(), 16) % 10 >= 4

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
        ev2t = defaultdict(dict); rows = []; tx = []
        for e in rec["target_edges"]:
            a, b = e["s"], e["t"]
            ka = nd.get(a, {}).get("kind"); kb = nd.get(b, {}).get("kind")
            if ka == "event" and kb == "timex":
                ev2t[a][b] = "E>" + e["rel"]
                tx.append((a, b, "E", e["rel"], nd[a], nd[b]))
            elif ka == "timex" and kb == "event":
                ev2t[b][a] = "T>" + e["rel"]
                tx.append((b, a, "T", e["rel"], nd[b], nd[a]))
            elif ka == "event" and kb == "event":
                na, nb = nd[a], nd[b]
                sh = anch.get((a, b)) or anch.get((b, a)) or set()
                f = pair_features(na, nb, sh, bool(sh), frozenset())
                cs = frozenset(list(candidate_conditions(f)) + relational_conditions(na, nb, sh))
                rows.append((a, b, e["rel"], f, cs))
        if rows: out.append((rec["doc_id"], rows, ev2t, tx))
    return out

TR = load(GRAPH/"train.jsonl", 400)
VA = load(GRAPH/"valid.jsonl", 0)
D = [d for d in TR if disc(d[0])]
C = [d for d in TR if not disc(d[0])]
print("train %d doc (disc %d / conf %d), valid %d doc" % (len(TR), len(D), len(C), len(VA)), flush=True)

# ---------------------------------------------------------------- EV-TIMEX classifier
def tx_feats(direction, ev, t):
    """Features of one event-timex pair -- no temporal label anywhere."""
    f = []
    f.append(("dir", direction))
    f.append(("etype", ev.get("type")))
    f.append(("ttype", t.get("timex_type")))
    f.append(("anch", t.get("anchorable")))
    se, st = ev.get("sent_first"), t.get("sent_first")
    if se is not None and st is not None:
        d = se - st
        f.append(("sdist", "0" if d == 0 else ("e>t" if d > 0 else "t>e")))
        f.append(("adist", "0" if abs(d) == 0 else ("1" if abs(d) == 1 else ("2-4" if abs(d) <= 4 else "5+"))))
    f.append(("bucket", ev.get("sent_bucket")))
    f.append(("nrole", min(ev.get("n_role", 0), 4)))
    for r in (ev.get("roleset") or ())[:4]: f.append(("role", r))
    return frozenset(f)

print("hoc classifier EV-TIMEX ...", flush=True)
cnt = defaultdict(Counter); cdoc = defaultdict(lambda: defaultdict(set))
for doc, rows, ev2t, tx in D:
    for (e, t, dr, rel, nev, ntx) in tx:
        for c in tx_feats(dr, nev, ntx):
            cnt[c][rel] += 1; cdoc[c][rel].add(doc)
TXR = {}
for c, cc in cnt.items():
    n = sum(cc.values()); top, k = cc.most_common(1)[0]
    if n < 30 or k < 10 or len(cdoc[c][top]) < 5: continue
    w = wlb(k, n)
    if w >= 0.40: TXR[c] = (top, w)
print("  %d luat EV-TIMEX" % len(TXR), flush=True)

def predict_tx(dr, nev, ntx):
    sc = {}
    for c in tx_feats(dr, nev, ntx):
        t = TXR.get(c)
        if t:
            v = t[1]/PRIOR[t[0]]
            if v > sc.get(t[0], 0): sc[t[0]] = v
    return max(sc, key=sc.get) if sc else "BEFORE"

# accuracy of that classifier on valid
gt = pt = 0
for doc, rows, ev2t, tx in VA:
    for (e, t, dr, rel, nev, ntx) in tx:
        gt += 1
        if predict_tx(dr, nev, ntx) == rel: pt += 1
print("  do chinh xac tren valid: %s/%s = %.2f%%" % (format(pt, ","), format(gt, ","), 100*pt/gt), flush=True)

# ---------------------------------------------------------------- mine triads under 3 settings
def anchors(doc_tuple, mode):
    """event -> {timex: signed relation}, built from gold / predicted / structure only."""
    doc, rows, ev2t, tx = doc_tuple
    if mode == "oracle": return ev2t
    out = defaultdict(dict)
    for (e, t, dr, rel, nev, ntx) in tx:
        if mode == "pred":
            out[e][t] = dr + ">" + predict_tx(dr, nev, ntx)
        else:                                   # structure: direction only, no relation
            out[e][t] = dr + ">*"
    return out

def triads(am, a, b):
    ta, tb = am.get(a), am.get(b)
    if not ta or not tb: return []
    return [(ta[t], tb[t]) for t in sorted(set(ta) & set(tb))[:CAPT]]

def mine(mode):
    sig = defaultdict(Counter); sd = defaultdict(lambda: defaultdict(set))
    for dt in D:
        am = anchors(dt, mode)
        for (a, b, r, _, _) in dt[1]:
            for k in triads(am, a, b):
                sig[k][r] += 1; sd[k][r].add(dt[0])
    cand = {}
    for k, c in sig.items():
        n = sum(c.values()); top, kk = c.most_common(1)[0]
        if n < 30 or kk < 10 or len(sd[k][top]) < 5: continue
        if wlb(kk, n) >= 0.50: cand[k] = top
    cs_ = defaultdict(Counter)
    for dt in C:
        am = anchors(dt, mode)
        for (a, b, r, _, _) in dt[1]:
            for k in triads(am, a, b): cs_[k][r] += 1
    CONF = {}
    for k, top in cand.items():
        c = cs_.get(k)
        if not c or sum(c.values()) < 10: continue
        CONF[k] = (top, wlb(c[top], sum(c.values())))
    rk = sorted(CONF.items(), key=lambda kv: -kv[1][1])
    return dict(rk[:max(1, int(0.7*len(rk)))])

rules = V.load_rules(ART/"rules_rx_c70.json")
flat = [(f, cs) for _, rows, _, _ in VA for (_, _, _, f, cs) in rows]
idx = V.build_index(rules, [(None, f, cs) for f, cs in flat])

gold = [g for _, rows, _, _ in VA for (_, _, g, _, _) in rows]
base = []
pairsc = []
for doc, rows, ev2t, tx in VA:
    for (a, b, g, f, cs) in rows:
        h = V.firing(rules, idx, f, cs)
        sc = {}
        for ri in h:
            ru = rules[ri]
            v = ru["wlb"]/PRIOR[ru["rel"]]
            if v > sc.get(ru["rel"], 0): sc[ru["rel"]] = v
        pairsc.append(sc)
        base.append(max(sc, key=sc.get) if sc and max(sc.values()) >= 5 else "BEFORE")
m0, per0, a0 = macro(base, gold)

print()
print("=" * 94)
print("EV-TIMEX-EV duoi BA gia dinh ve neo")
print("=" * 94)
print("  %-42s macro-F1 %6.2f%%  acc %6.2f%%" % ("A  chi 257 luat EV-EV", 100*m0, 100*a0))
for mode, nm in (("oracle", "B  neo GOLD (oracle -- doc target edge)"),
                 ("pred",   "C  neo DU DOAN (classifier EV-TIMEX)"),
                 ("struct", "D  chi CAU TRUC (co chung timex hay khong)")):
    R = mine(mode)
    pred = []; i = 0; nf = 0
    for doc, rows, ev2t, tx in VA:
        am = anchors((doc, rows, ev2t, tx), mode)
        for (a, b, g, f, cs) in rows:
            sc = dict(pairsc[i]); i += 1
            hit = False
            for k in triads(am, a, b):
                t = R.get(k)
                if t:
                    hit = True
                    v = t[1]/PRIOR[t[0]]
                    if v > sc.get(t[0], 0): sc[t[0]] = v
            if hit: nf += 1
            pred.append(max(sc, key=sc.get) if sc and max(sc.values()) >= 5 else "BEFORE")
    m, per, acc = macro(pred, gold)
    print("  %-42s macro-F1 %6.2f%%  acc %6.2f%%   (%d luat, ban %.1f%%)"
          % (nm, 100*m, 100*acc, len(R), 100*nf/len(gold)))
    print("       " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per[r]) for r in RELS)
          + "   chenh %+.2f" % (100*(m-m0)))
