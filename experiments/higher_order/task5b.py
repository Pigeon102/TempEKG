# -*- coding: utf-8 -*-
"""Bai 2 with higher-order rules: can they audit a graph the classifier built?

Task 5 measured the existing closure-based auditor on model-predicted edges and it fell
apart: repair@k 31.84% against 96.61% on injected noise, because the classifier's errors
are 86.5% a single confusable pair (BEFORE <-> CONTAINS) while random corruption spreads
out. Higher-order rules are the natural candidate to fix that, since they reach exactly
that pair -- and here the assumption they need (neighbouring labels are known) is
satisfied, because Bai 2 starts from a graph that already exists.

Scored the same way as Task 5 so the numbers are comparable:
    P@k       of the edges flagged, how many were really wrong
    found_all of all wrong edges, how many were found
    repair@k  of those found, how many were repaired correctly
    R_all     of all wrong edges, how many were both found and repaired
"""
import sys, io, json, math, random
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V
from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL
from noise_aware import score_document, corrupt

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
Z = 1.959963985
CAP = 6
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 150

def wlb(k, n):
    if n == 0: return 0.0
    p = k/n
    return (p + Z*Z/(2*n) - Z*math.sqrt(p*(1-p)/n + Z*Z/(4*n*n)))/(1 + Z*Z/n)

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
        rec = json.loads(line)
        nd = rec["nodes"]
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
        rec = json.loads(line)
        nd = rec["nodes"]; anch = defaultdict(set)
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

# ---------------------------------------------------------------- mine on train gold
TR = load_raw(GRAPH/"train.jsonl", 400)
def mine(nmid):
    sig = defaultdict(Counter); sd = defaultdict(lambda: defaultdict(set))
    for doc, es in TR:
        adj = adjof(es)
        for a, b, r in es:
            mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
            for k in keys(adj, a, b, mids, nmid):
                sig[k][r] += 1; sd[k][r].add(doc)
    R = {}
    for k, c in sig.items():
        n = sum(c.values()); top, kk = c.most_common(1)[0]
        if n < 30 or kk < 10 or len(sd[k][top]) < 5: continue
        w = wlb(kk, n)
        if w >= 0.50: R[k] = (top, w)
    return R
M = {3: mine(1), 4: mine(2), 5: mine(3)}
print("luat: bo3 %d  bo4 %d  bo5 %d" % (len(M[3]), len(M[4]), len(M[5])), flush=True)

# ---------------------------------------------------------------- build the predicted graph
rules = V.load_rules(ART/"rules_rx_c70.json")
VF = load_feat(GRAPH/"valid.jsonl", LIMIT)
flat = [(f, cs) for _, rows in VF for (_, _, _, f, cs) in rows]
idx = V.build_index(rules, [(None, f, cs) for f, cs in flat])
docs = []
for doc, rows in VF:
    cur = []
    for (a, b, g, f, cs) in rows:
        h = V.firing(rules, idx, f, cs)
        cur.append((a, b, g, V.combine(rules, h, "max-norm", 5) or V.FALLBACK))
    docs.append(cur)
npair = sum(len(d) for d in docs)
nbad = sum(1 for d in docs for (_, _, g, p) in d if g != p)
print("valid %d doc, %s cap, %s canh sai (%.2f%%)"
      % (len(VF), format(npair, ","), format(nbad, ","), 100*nbad/npair), flush=True)

# ---------------------------------------------------------------- auditor
def audit_ho(docs, k_frac=3.0):
    """Suspicion = higher-order rules disagree with the carried label, weighted by wlb."""
    ranked = []
    for d in docs:
        adj = adjof([(a, b, p) for (a, b, _, p) in d])
        for (a, b, g, p) in d:
            mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
            agg = Counter()
            for o in (3, 4, 5):
                bucket = defaultdict(list)
                for k in keys(adj, a, b, mids, o-2):
                    t = M[o].get(k)
                    if t: bucket[t[0]].append(t[1])
                for lab, ws in bucket.items(): agg[lab] += sum(ws)/len(ws)
            if not agg: continue
            best, bw = agg.most_common(1)[0]
            if best == p: continue                 # rules agree, not suspicious
            susp = bw - agg.get(p, 0.0)            # how much better the alternative is
            ranked.append((susp, g != p, g, best))
    ranked.sort(key=lambda t: -t[0])
    k = max(1, int(round(k_frac * nbad))) if k_frac else len(ranked)
    top = ranked[:k]
    fb = sum(1 for _, ib, _, _ in top if ib)
    rp = sum(1 for _, ib, orig, prop in top if ib and prop == orig)
    return dict(ranked=len(ranked), k=len(top),
                p_at_k=fb/len(top) if top else 0.0,
                found=fb/nbad if nbad else 0.0,
                repair=rp/fb if fb else 0.0,
                r_all=rp/nbad if nbad else 0.0)

def audit_closure(docs, k_frac=3.0):
    ranked = []
    for d in docs:
        edges = [(a, b, p) for (a, b, _, p) in d]
        bad = {(a, b): g for (a, b, g, p) in d if g != p}
        for susp, a, b, carried, prop in score_document(edges):
            ranked.append((susp, (a, b) in bad, bad.get((a, b)), prop))
    ranked.sort(key=lambda t: -t[0])
    k = max(1, int(round(k_frac * nbad))) if k_frac else len(ranked)
    top = ranked[:k]
    fb = sum(1 for _, ib, _, _ in top if ib)
    rp = sum(1 for _, ib, o, p in top if ib and p == o)
    return dict(ranked=len(ranked), k=len(top),
                p_at_k=fb/len(top) if top else 0.0,
                found=fb/nbad if nbad else 0.0,
                repair=rp/fb if fb else 0.0,
                r_all=rp/nbad if nbad else 0.0)

print()
print("=" * 88)
print("BAI 2 tren canh MODEL DU DOAN — closure cu vs luat bac cao")
print("=" * 88)
c = audit_closure(docs)
h = audit_ho(docs)
print("  %-22s%14s%14s" % ("chi so", "closure", "bac cao"))
print("  " + "-" * 50)
print("  %-22s%14s%14s" % ("xep hang", format(c["ranked"], ","), format(h["ranked"], ",")))
for nm, k in (("P@k", "p_at_k"), ("found_all", "found"), ("repair@k", "repair"), ("R_all", "r_all")):
    print("  %-22s%13.2f%%%13.2f%%" % (nm, 100*c[k], 100*h[k]))
