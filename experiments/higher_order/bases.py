# -*- coding: utf-8 -*-
"""Four mathematical checks that could overturn the conclusions.

The claim now standing is that higher-order rules cannot help Bai 1 because classifier
errors cluster by document. Before that goes in a report, four things worth testing,
each of which would change it if it came out the other way.

1 ALLEN CONSISTENCY OF GOLD. Is the gold graph itself transitively consistent? If a
  sizeable fraction of gold triangles violate Allen composition, then every conclusion
  drawn from composition is built on sand -- including the 24.5% "contradiction" rate.

2 IS THE OBJECTIVE FIXABLE? The joint objective scored gold below its own solution on
  93% of documents. That was measured at two lambda values with one weighting. If a
  per-triangle normalisation (divide by how many triangles an edge has) reverses it, the
  objective was merely mis-scaled rather than wrong.

3 DOES THE ORACLE GAP SURVIVE DOCUMENT-LEVEL SPLITTING? The 33.03% gold-context number
  was measured with rules mined on train and applied to valid, but the triangles it reads
  come from the same documents it scores. Hiding a fraction of gold neighbours at random
  is not the same as hiding a whole document's worth.

4 UPPER BOUND ON PAIR-LEVEL. How well could ANY pair-level classifier do? If two event
  pairs have identical features but different gold labels, no function of those features
  separates them. That ceiling says whether 25.60% is near the limit of the feature set.
"""
import sys, io, json, math, random
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V
from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
PRIOR = {"BEFORE": .91045, "CONTAINS": .07430, "SIMULTANEOUS": .00862,
         "OVERLAP": .00597, "BEGINS-ON": .00044, "ENDS-ON": .00022}
Z = 1.959963985
CAP = 6
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 150

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
def adjof(tr):
    adj = defaultdict(dict)
    for a, b, r in tr: adj[a][b] = r; adj[b][a] = r
    return adj
def keys(adj, a, b, mids, nmid):
    if nmid == 1:
        for c in mids: yield (adj[a][c], adj[c][b])
    elif nmid == 2:
        for i in range(len(mids)):
            for j in range(i+1, len(mids)):
                c, d = mids[i], mids[j]
                yield (adj[a][c], adj[c][b], adj[a][d], adj[d][b])
    else:
        for i in range(len(mids)):
            for j in range(i+1, len(mids)):
                for l in range(j+1, len(mids)):
                    c, d, e = mids[i], mids[j], mids[l]
                    yield (adj[a][c], adj[c][b], adj[a][d], adj[d][b], adj[a][e], adj[e][b])

def load_raw(path, limit=0):
    out = []
    for i, line in enumerate(io.open(path, encoding="utf-8")):
        if limit and i >= limit: break
        if not line.strip(): continue
        rec = json.loads(line); nd = rec["nodes"]
        es = [(e["s"], e["t"], e["rel"]) for e in rec["target_edges"]
              if nd.get(e["s"], {}).get("kind") == "event"
              and nd.get(e["t"], {}).get("kind") == "event"]
        if es: out.append((rec["doc_id"], es))
    return out
def load_feat(path, limit=0):
    from mine_compositional import candidate_conditions, pair_features
    from mine_mdd import relational_conditions
    out = []
    for i, line in enumerate(io.open(path, encoding="utf-8")):
        if limit and i >= limit: break
        if not line.strip(): continue
        rec = json.loads(line); nd = rec["nodes"]; anch = defaultdict(set)
        for p in rec["anchored_pairs"]:
            for ra, rb in p["roles"]: anch[(p["a"], p["b"])].add((ra, rb))
        rows = []
        for e in rec["target_edges"]:
            a, b = e["s"], e["t"]
            na, nb = nd.get(a), nd.get(b)
            if not na or not nb or na["kind"] != "event" or nb["kind"] != "event": continue
            sh = anch.get((a, b)) or anch.get((b, a)) or set()
            f = pair_features(na, nb, sh, bool(sh), frozenset())
            cs = frozenset(list(candidate_conditions(f)) + relational_conditions(na, nb, sh))
            rows.append((a, b, e["rel"], f, cs))
        if rows: out.append((rec["doc_id"], rows))
    return out

TRG = load_raw(GRAPH/"train.jsonl", 400)
VAG = load_raw(GRAPH/"valid.jsonl", LIMIT)

# ================================================================ 1. gold consistency
print("=" * 96)
print("1. DO THI GOLD CO NHAT QUAN VOI DAI SO ALLEN KHONG?")
print("=" * 96)
st = Counter()
for doc, es in VAG:
    adj = adjof(es)
    for a, b, r in es:
        ga = MAVEN_TO_ALLEN[r]
        for c in set(adj[a]) & set(adj[b]):
            if c in (a, b): continue
            sa, sb = MAVEN_TO_ALLEN.get(adj[a][c]), MAVEN_TO_ALLEN.get(adj[c][b])
            if not sa or not sb: continue
            st["tong"] += 1
            imp = compose(sa, sb)
            if ga & imp: st["nhat quan"] += 1
            else: st["VI PHAM"] += 1
t = st["tong"]
print("  %s tam giac gold" % format(t, ","))
print("  nhat quan  %10s  %6.2f%%" % (format(st["nhat quan"], ","), 100*st["nhat quan"]/t))
print("  VI PHAM    %10s  %6.2f%%" % (format(st["VI PHAM"], ","), 100*st["VI PHAM"]/t))
print()
print("  -> %s" % ("gold nhat quan, moi suy luan tu composition deu co co so"
      if st["VI PHAM"]/t < 0.05 else
      "gold KHONG nhat quan; moi ket luan tu composition can xem lai"))

# ================================================================ 2. objective, normalised
print()
print("=" * 96)
print("2. HAM MUC TIEU CO CUU DUOC BANG CHUAN HOA KHONG?")
print("=" * 96)
sig = defaultdict(Counter); sdoc = defaultdict(lambda: defaultdict(set))
for doc, es in TRG:
    adj = adjof(es)
    for a, b, r in es:
        for c in set(adj[a]) & set(adj[b]):
            if c in (a, b): continue
            k = (adj[a][c], adj[c][b])
            sig[k][r] += 1; sdoc[k][r].add(doc)
PHI = {}
for k, c in sig.items():
    n = sum(c.values())
    for r in RELS:
        if c[r] < 10 or len(sdoc[k][r]) < 5: continue
        PHI[(k[0], k[1], r)] = math.log(max(c[r]/n, 1e-6)/PRIOR[r])

rules = V.load_rules(ART/"rules_rx_c70.json")
VF = load_feat(GRAPH/"valid.jsonl", LIMIT)
flat = [(f, cs) for _, rows in VF for (_, _, _, f, cs) in rows]
idx = V.build_index(rules, [(None, f, cs) for f, cs in flat])
def unary(hits):
    s = {r: math.log(PRIOR[r]) for r in RELS}
    for ri in hits:
        ru = rules[ri]
        s[ru["rel"]] = max(s[ru["rel"]], math.log(max(ru["wlb"], 1e-6)/PRIOR[ru["rel"]]))
    return s
docs = []
for doc, rows in VF:
    cur = []
    for (a, b, g, f, cs) in rows:
        u = unary(V.firing(rules, idx, f, cs))
        cur.append((a, b, g, max(u, key=u.get), u))
    docs.append(cur)
gold = [g for d in docs for (_, _, g, _, _) in d]

def obj(d, lab, LAM, norm):
    adj = adjof([(a, b, lab[(a, b)]) for (a, b, _, _, _) in d])
    tot = 0.0
    for (a, b, _, _, u) in d:
        tot += u[lab[(a, b)]]
        mids = [c for c in set(adj[a]) & set(adj[b]) if c not in (a, b)]
        if not mids: continue
        s = sum(PHI.get((adj[a][c], adj[c][b], lab[(a, b)]), 0.0) for c in mids)
        tot += LAM * (s/len(mids) if norm else s)
    return tot

for norm in (False, True):
    for LAM in (0.1, 0.5, 2.0):
        win = 0
        for d in docs:
            lab_p = {(a, b): p for (a, b, _, p, _) in d}
            lab_g = {(a, b): g for (a, b, g, _, _) in d}
            if obj(d, lab_g, LAM, norm) > obj(d, lab_p, LAM, norm): win += 1
        print("  %-14s lambda=%-5.1f  GOLD thang o %3d/%d document (%.0f%%)"
              % ("chuan hoa" if norm else "khong chuan", LAM, win, len(docs), 100*win/len(docs)))

# ================================================================ 3. oracle gap, doc-level
print()
print("=" * 96)
print("3. ORACLE GAP CO SONG SOT KHI GIAU CA DOCUMENT KHONG?")
print("=" * 96)
M = {}
for nm in (1, 2, 3):
    s2 = defaultdict(Counter); d2 = defaultdict(lambda: defaultdict(set))
    for doc, es in TRG:
        adj = adjof(es)
        for a, b, r in es:
            mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
            for k in keys(adj, a, b, mids, nm):
                s2[k][r] += 1; d2[k][r].add(doc)
    R = {}
    for k, c in s2.items():
        n = sum(c.values()); top, kk = c.most_common(1)[0]
        if n < 30 or kk < 10 or len(d2[k][top]) < 5: continue
        w = wlb(kk, n)
        if w >= 0.50: R[k] = (top, w)
    M[nm+2] = R

def ho_pred(graph_docs):
    out = []
    for d in graph_docs:
        adj = adjof([(a, b, lab) for (a, b, _, lab) in d])
        for (a, b, g, lab) in d:
            mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
            agg = Counter()
            for o in (3, 4, 5):
                bk = defaultdict(list)
                for k in keys(adj, a, b, mids, o-2):
                    t = M[o].get(k)
                    if t: bk[t[0]].append(t[1])
                for l, ws in bk.items(): agg[l] += sum(ws)/len(ws)
            out.append(agg.most_common(1)[0][0] if agg else "BEFORE")
    return out

gd = [[(a, b, g, g) for (a, b, g, _, _) in d] for d in docs]
m, _, acc = macro(ho_pred(gd), gold)
print("  gold day du                      macro-F1 %6.2f%%  acc %6.2f%%" % (100*m, 100*acc))

# replace whole documents with pair-level predictions, keep the rest gold
rng = random.Random(0)
for frac in (0.25, 0.50, 0.75, 1.00):
    ndoc = int(round(frac*len(docs)))
    which = set(rng.sample(range(len(docs)), ndoc))
    mixed = []
    for i, d in enumerate(docs):
        if i in which:
            mixed.append([(a, b, g, p) for (a, b, g, p, _) in d])
        else:
            mixed.append([(a, b, g, g) for (a, b, g, _, _) in d])
    m, _, acc = macro(ho_pred(mixed), gold)
    print("  %3d%% document dung du doan      macro-F1 %6.2f%%  acc %6.2f%%"
          % (100*frac, 100*m, 100*acc))

# ================================================================ 4. pair-level ceiling
print()
print("=" * 96)
print("4. TRAN TREN CUA BAT KY CLASSIFIER PAIR-LEVEL NAO")
print("=" * 96)
buckets = defaultdict(Counter)
for doc, rows in VF:
    for (a, b, g, f, cs) in rows:
        buckets[cs][g] += 1
n = sum(sum(c.values()) for c in buckets.values())
best = sum(c.most_common(1)[0][1] for c in buckets.values())
pred = []
gold2 = []
for cs, c in buckets.items():
    top = c.most_common(1)[0][0]
    for r, k in c.items():
        pred += [top]*k; gold2 += [r]*k
m, per, acc = macro(pred, gold2)
print("  %s cap -> %s to dac trung phan biet" % (format(n, ","), format(len(buckets), ",")))
print("  tran accuracy (luon doan nhan pho bien nhat trong to): %.2f%%" % (100*best/n))
print("  tran macro-F1 tuong ung: %.2f%%" % (100*m))
print("     " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per[r]) for r in RELS))
coll = sum(1 for c in buckets.values() if len(c) > 1)
print("  to co NHIEU nhan khac nhau: %s (%.1f%%) -- khong ham nao tach duoc"
      % (format(coll, ","), 100*coll/len(buckets)))
print()
print("  doi chieu: 257 rule dat macro-F1 24,11%, accuracy 87,54%")
