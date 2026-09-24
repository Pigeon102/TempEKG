# -*- coding: utf-8 -*-
"""Re-measure the higher-order results with edge direction handled correctly.

Every higher-order script so far built its adjacency with

    adj[a][b] = r ; adj[b][a] = r

which asserts that if A is BEFORE B then B is also BEFORE A. That is wrong: the reverse
direction carries the CONVERSE relation. The bug made 5.05% of gold triangles look
Allen-inconsistent; with converse applied the gold graph is consistent on all 585,078
triangles, so the bug was mine and not the corpus's.

The signature (r_ac, r_cb) was therefore being read partly in the wrong direction, so
every number that depends on it has to be recomputed. A directed signature is used here:
edges are stored one way, and a triangle is only counted when the two legs actually
compose (a->c->b), with the converse taken explicitly when an edge is stored the other way.
"""
import sys, io, json, math
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V
from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
INV = {"BEFORE": "iBEFORE", "CONTAINS": "iCONTAINS", "SIMULTANEOUS": "SIMULTANEOUS",
       "OVERLAP": "iOVERLAP", "BEGINS-ON": "BEGINS-ON", "ENDS-ON": "iENDS-ON"}
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

def dirnet(triples):
    """adj[x][y] = label of the x->y direction, inverse marked with the i-prefix."""
    adj = defaultdict(dict)
    for a, b, r in triples:
        adj[a][b] = r
        adj[b][a] = INV[r]
    return adj

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
print("train %d doc" % len(TRG), flush=True)

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

def mine(nmid):
    sig = defaultdict(Counter); sd = defaultdict(lambda: defaultdict(set))
    for doc, es in TRG:
        adj = dirnet(es)
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
    return R, len(sig)

M = {}; NS = {}
for o, nm in ((3, 1), (4, 2), (5, 3)):
    M[o], NS[o] = mine(nm)
    print("  bo %d: %s chu ky -> %s luat" % (o, format(NS[o], ","), format(len(M[o]), ",")), flush=True)

# ---------------------------------------------------------------- pair-level graph
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
gold = [g for d in docs for (_, _, g, _) in d]
nbad = sum(1 for d in docs for (_, _, g, p) in d if g != p)
print("valid %d doc, %s cap, %s canh sai (%.2f%%)"
      % (len(VF), format(len(gold), ","), format(nbad, ","), 100*nbad/len(gold)), flush=True)

def ho(graph_docs, orders=(3, 4, 5)):
    out = []
    for d in graph_docs:
        adj = dirnet([(a, b, lab) for (a, b, _, lab) in d])
        for (a, b, g, lab) in d:
            mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
            agg = Counter()
            for o in orders:
                bk = defaultdict(list)
                for k in keys(adj, a, b, mids, o-2):
                    t = M[o].get(k)
                    if t: bk[t[0]].append(t[1])
                for l, ws in bk.items(): agg[l] += sum(ws)/len(ws)
            out.append(agg.most_common(1)[0][0] if agg else "BEFORE")
    return out

print()
print("=" * 94)
print("DO LAI VOI HUONG CANH DUNG")
print("=" * 94)
pp = [p for d in docs for (_, _, _, p) in d]
m, per, acc = macro(pp, gold)
print("  %-34s macro-F1 %6.2f%%  acc %6.2f%%" % ("pair-only 257 rule", 100*m, 100*acc))

gd = [[(a, b, g, g) for (a, b, g, _) in d] for d in docs]
for orders, nm in (((3,), "bo 3 tren GOLD"), ((3,4), "bo 3+4 tren GOLD"), ((3,4,5), "bo 3+4+5 tren GOLD")):
    m2, per2, acc2 = macro(ho(gd, orders), gold)
    print("  %-34s macro-F1 %6.2f%%  acc %6.2f%%" % (nm, 100*m2, 100*acc2))
    if orders == (3,4,5):
        print("     " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per2[r]) for r in RELS))

m3, per3, acc3 = macro(ho(docs), gold)
print("  %-34s macro-F1 %6.2f%%  acc %6.2f%%" % ("bo 3+4+5 tren DU DOAN", 100*m3, 100*acc3))

# gold consistency, directed
st = Counter()
VAG = load_raw(GRAPH/"valid.jsonl", LIMIT)
for doc, es in VAG:
    adj = defaultdict(dict)
    for a, b, r in es:
        s = MAVEN_TO_ALLEN.get(r)
        if not s: continue
        adj[a][b] = s; adj[b][a] = converse(s)
    for a, b, r in es:
        ga = MAVEN_TO_ALLEN.get(r)
        if not ga: continue
        for c in set(adj[a]) & set(adj[b]):
            if c in (a, b): continue
            st["tong"] += 1
            if ga & compose(adj[a][c], adj[c][b]): st["ok"] += 1
print()
print("  gold nhat quan Allen: %s/%s = %.2f%%"
      % (format(st["ok"], ","), format(st["tong"], ","), 100*st["ok"]/st["tong"]))
