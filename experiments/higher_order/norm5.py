# -*- coding: utf-8 -*-
"""Is the quintuple gain real, or just louder voting?

A quintuple rule fires 18.8 times per edge on average, a triangle rule far less. Summing
raw weights therefore lets order-5 drown out order-3 regardless of which is more reliable.
Two controls:

  MEAN   average the weights of the rules that fire at each order, so an order that fires
         more often does not win by volume alone.
  MAX    take the single strongest rule at each order.

If order 5 still leads under both, the gain is real.
"""
import sys, io, json, math
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
from constraint_net import MAVEN_TO_ALLEN
src = open(r"quint.py", encoding="utf-8").read()
exec(src.split("# ================================================================ A.")[0])

def adjof(es):
    adj = defaultdict(dict)
    for a, b, r in es: adj[a][b] = r; adj[b][a] = r
    return adj
CAP = 6
RELS = ["BEFORE","CONTAINS","SIMULTANEOUS","OVERLAP","BEGINS-ON","ENDS-ON"]

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

print("khai thac ...", flush=True)
M = {3: mine(1), 4: mine(2), 5: mine(3)}
for o in (3,4,5): print("  bo %d: %s luat" % (o, format(len(M[o]), ",")), flush=True)

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

def run(orders, mode):
    gold = []; pred = []; fired = 0
    for doc, es in VA:
        adj = adjof(es)
        for a, b, r in es:
            gold.append(r)
            mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
            agg = Counter()
            for o in orders:
                bucket = defaultdict(list)
                for k in keys(adj, a, b, mids, o-2):
                    t = M[o].get(k)
                    if t: bucket[t[0]].append(t[1])
                for lab, ws in bucket.items():
                    if mode == "sum":  agg[lab] += sum(ws)
                    elif mode == "mean": agg[lab] += sum(ws)/len(ws)
                    else:              agg[lab] = max(agg[lab], max(ws))
            if agg: fired += 1; pred.append(agg.most_common(1)[0][0])
            else: pred.append("BEFORE")
    m, per, acc = macro(pred, gold)
    return m, per, acc, fired/len(gold)

print()
print("%-20s%10s%10s%10s" % ("cau hinh", "sum", "mean", "max"))
print("-" * 52)
for nm, os_ in (("chi bo 3", (3,)), ("chi bo 4", (4,)), ("chi bo 5", (5,)),
                ("bo 3+4", (3,4)), ("bo 3+4+5", (3,4,5))):
    vals = []
    for mode in ("sum", "mean", "max"):
        m, per, acc, cov = run(os_, mode)
        vals.append(m)
    print("%-20s%9.2f%%%9.2f%%%9.2f%%" % (nm, 100*vals[0], 100*vals[1], 100*vals[2]))

print()
print("Chi tiet cau hinh tot nhat theo MEAN:")
for nm, os_ in (("bo 5", (5,)), ("bo 3+4+5", (3,4,5))):
    m, per, acc, cov = run(os_, "mean")
    print("  %-12s macro-F1 %.2f%%  acc %.2f%%  phu %.1f%%" % (nm, 100*m, 100*acc, 100*cov))
    print("    " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per[r]) for r in RELS))
