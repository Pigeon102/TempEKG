# -*- coding: utf-8 -*-
"""Iterative refinement: pair-level rules seed the graph, higher-order rules refine it.

The 36.70% measured earlier is not comparable to the 257-rule 25.60%, because the
higher-order rules read the labels on adjacent edges -- which at test time are exactly
what has to be predicted. This closes that gap honestly:

    round 0   257 pair-level rules label every edge
    round t   higher-order rules re-label each edge from its CURRENT neighbours
              (the edge itself is hidden, so a rule never reads its own answer)

Two things are watched. Whether accuracy improves, and whether it converges or oscillates.
An iterative scheme on its own predictions can also reinforce its own mistakes, so the
run reports how many edges change each round and in which direction.
"""
import sys, io, json, math
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V
from constraint_net import MAVEN_TO_ALLEN

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
Z = 1.959963985
CAP = 6
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 0

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

def load_raw(path, limit=0):
    """documents as (doc_id, [(a,b,gold)]) -- for mining higher-order rules on gold."""
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
    """documents with features, for the pair-level classifier."""
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

def adjof(triples):
    adj = defaultdict(dict)
    for a, b, r in triples:
        adj[a][b] = r; adj[b][a] = r
    return adj

def keys(adj, a, b, mids, nmid):
    if nmid == 1:
        for c in mids:
            if c in adj[a] and c in adj[b]: yield (adj[a][c], adj[c][b])
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

# ---------------------------------------------------------------- mine higher order on TRAIN gold
TR = load_raw(GRAPH/"train.jsonl", 400)
print("train %d doc" % len(TR), flush=True)
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

# ---------------------------------------------------------------- round 0: pair-level
rules = V.load_rules(ART/"rules_rx_c70.json")
VF = load_feat(GRAPH/"valid.jsonl", LIMIT)
flat = [(f, cs) for _, rows in VF for (_, _, _, f, cs) in rows]
idx = V.build_index(rules, [(None, f, cs) for f, cs in flat])
state = []          # per document: [(a, b, gold, current_label)]
for doc, rows in VF:
    cur = []
    for (a, b, g, f, cs) in rows:
        h = V.firing(rules, idx, f, cs)
        cur.append((a, b, g, V.combine(rules, h, "max-norm", 5) or V.FALLBACK))
    state.append(cur)
gold = [g for d in state for (_, _, g, _) in d]
npair = len(gold)
print("valid %d doc, %s cap" % (len(VF), format(npair, ",")), flush=True)

def report(tag, state, changed=None):
    pred = [p for d in state for (_, _, _, p) in d]
    m, per, acc = macro(pred, gold)
    extra = "" if changed is None else "   doi %s canh" % format(changed, ",")
    print("  %-22s macro-F1 %6.2f%%   acc %6.2f%%%s" % (tag, 100*m, 100*acc, extra))
    print("     " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per[r]) for r in RELS))
    return m, acc

print()
print("=" * 92)
print("CHAY LAP: 257 rule khoi tao, bo 3/4/5 tinh chinh (mode=mean)")
print("=" * 92)
report("vong 0 (pair-level)", state)

def refine(state, orders):
    new_state = []; changed = 0; right = 0
    for d in state:
        adj = adjof([(a, b, p) for (a, b, _, p) in d])
        nd = []
        for (a, b, g, p) in d:
            # hide this edge so a rule never reads its own answer
            mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
            agg = Counter()
            for o in orders:
                bucket = defaultdict(list)
                for k in keys(adj, a, b, mids, o-2):
                    t = M[o].get(k)
                    if t: bucket[t[0]].append(t[1])
                for lab, ws in bucket.items():
                    agg[lab] += sum(ws)/len(ws)      # mean, the control that was fair
            np_ = agg.most_common(1)[0][0] if agg else p
            if np_ != p:
                changed += 1
                if np_ == g: right += 1
            nd.append((a, b, g, np_))
        new_state.append(nd)
    return new_state, changed, right

cur = state
for t in range(1, 6):
    cur, ch, right = refine(cur, (3, 4, 5))
    m, acc = report("vong %d" % t, cur, ch)
    if ch:
        print("     trong %s canh doi: %s dung (%.1f%%)" % (format(ch, ","), format(right, ","), 100*right/ch))
    if ch == 0:
        print("  hoi tu sau %d vong" % t); break

# ---------------------------------------------------------------- oracle: higher order on GOLD graph
print()
print("=" * 92)
print("DOI CHUNG: bo 3/4/5 tren do thi GOLD (tran tren, khong dat duoc luc test)")
print("=" * 92)
gstate = [[(a, b, g, g) for (a, b, g, _) in d] for d in state]
gpred = []
for d in gstate:
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
        gpred.append(agg.most_common(1)[0][0] if agg else "BEFORE")
m, per, acc = macro(gpred, gold)
print("  %-22s macro-F1 %6.2f%%   acc %6.2f%%" % ("tren gold", 100*m, 100*acc))
print("     " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per[r]) for r in RELS))
