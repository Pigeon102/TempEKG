# -*- coding: utf-8 -*-
"""Soft one-pass higher-order evidence: does it recover the gold-context gap?

Hard iterative propagation destroyed 6.02 macro-F1 points (24.28 -> 18.26) while the
same rules on a gold graph reach 34.41. The hypothesis is that the failure is the hard
label commitment, not the rules: each round overwrites a label with a neighbour's
prediction that is itself only 57-65% right, and the next round reads that as fact.

The soft version never commits. A neighbouring edge contributes a DISTRIBUTION, and a
higher-order rule contributes its weight in proportion to how likely its trigger pattern
actually is:

    Score(r_ab) = s_ab(r) + lambda * SUM over c, r1, r2 of
                  p(r_ac = r1) * p(r_cb = r2) * phi(r, r1, r2)

phi is the mined rule: it is w if the rule with signature (r1, r2) predicts r, else 0.
One pass only -- no feedback, so no cascade is possible by construction.

Four systems are compared on identical documents:
    A  pair-only                (the 257-rule baseline)
    B  hard iterative           (measured before, reproduced here)
    C  soft one-pass            (this experiment)
    D  higher-order on gold     (the unreachable ceiling)
"""
import sys, io, json, math
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
CAP = 6
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 200

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

# ---------------------------------------------------------------- pair-level: hard label AND distribution
rules = V.load_rules(ART/"rules_rx_c70.json")
VF = load_feat(GRAPH/"valid.jsonl", LIMIT)
flat = [(f, cs) for _, rows in VF for (_, _, _, f, cs) in rows]
idx = V.build_index(rules, [(None, f, cs) for f, cs in flat])

def distribution(hits):
    """max-norm scores turned into a probability over the six labels."""
    sc = {r: 0.0 for r in RELS}
    for ri in hits:
        ru = rules[ri]
        sc[ru["rel"]] = max(sc[ru["rel"]], ru["wlb"] / PRIOR[ru["rel"]])
    tot = sum(sc.values())
    if tot <= 0:
        return dict(PRIOR)                       # nothing fired: fall back to the prior
    # temper, so a single firing rule does not become a certainty
    return {r: sc[r]/tot for r in RELS}

docs = []
for doc, rows in VF:
    cur = []
    for (a, b, g, f, cs) in rows:
        h = V.firing(rules, idx, f, cs)
        lab = V.combine(rules, h, "max-norm", 5) or V.FALLBACK
        cur.append((a, b, g, lab, distribution(h)))
    docs.append(cur)
gold = [g for d in docs for (_, _, g, _, _) in d]
print("valid %d doc, %s cap" % (len(VF), format(len(gold), ",")), flush=True)

def show(tag, pred):
    m, per, acc = macro(pred, gold)
    print("  %-30s macro-F1 %6.2f%%   acc %6.2f%%" % (tag, 100*m, 100*acc))
    print("     " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per[r]) for r in RELS))
    return m

print()
print("=" * 94)
print("A / B / C / D tren cung tap document")
print("=" * 94)

# ---- A pair only
predA = [p for d in docs for (_, _, _, p, _) in d]
mA = show("A  pair-only (257 rule)", predA)

# ---- B hard iterative (5 rounds)
cur = [[(a, b, g, p) for (a, b, g, p, _) in d] for d in docs]
for t in range(5):
    nxt = []
    for d in cur:
        adj = adjof([(a, b, p) for (a, b, _, p) in d])
        nd = []
        for (a, b, g, p) in d:
            mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
            agg = Counter()
            for o in (3, 4, 5):
                bk = defaultdict(list)
                for k in keys(adj, a, b, mids, o-2):
                    t2 = M[o].get(k)
                    if t2: bk[t2[0]].append(t2[1])
                for lab, ws in bk.items(): agg[lab] += sum(ws)/len(ws)
            nd.append((a, b, g, agg.most_common(1)[0][0] if agg else p))
        nxt.append(nd)
    cur = nxt
predB = [p for d in cur for (_, _, _, p) in d]
mB = show("B  hard iterative (5 vong)", predB)

# ---- C soft one-pass, lambda swept
print()
for LAM in (0.1, 0.3, 0.5, 1.0, 2.0, 4.0):
    predC = []
    for d in docs:
        dist = {}
        for (a, b, _, _, pr) in d:
            dist[(a, b)] = pr; dist[(b, a)] = pr
        nb = defaultdict(set)
        for (a, b, _, _, _) in d:
            nb[a].add(b); nb[b].add(a)
        for (a, b, g, p, pr) in d:
            sc = {r: pr[r] for r in RELS}          # unary
            mids = sorted(c for c in nb[a] & nb[b] if c not in (a, b))[:CAP]
            for c in mids:
                pac, pcb = dist.get((a, c)), dist.get((c, b))
                if not pac or not pcb: continue
                for r1 in RELS:
                    if pac[r1] < 0.01: continue
                    for r2 in RELS:
                        if pcb[r2] < 0.01: continue
                        t3 = M[3].get((r1, r2))
                        if t3:
                            sc[t3[0]] += LAM * pac[r1] * pcb[r2] * t3[1]
            predC.append(max(sc, key=sc.get))
    m, per, acc = macro(predC, gold)
    star = "  <-- tot nhat" if m > mA else ""
    print("  C  soft one-pass lambda=%-5.1f       macro-F1 %6.2f%%   acc %6.2f%%%s"
          % (LAM, 100*m, 100*acc, star))
    if LAM == 1.0:
        print("     " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per[r]) for r in RELS))

# ---- D gold context
print()
gpred = []
for d in docs:
    adj = adjof([(a, b, g) for (a, b, g, _, _) in d])
    for (a, b, g, _, _) in d:
        mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
        agg = Counter()
        for o in (3, 4, 5):
            bk = defaultdict(list)
            for k in keys(adj, a, b, mids, o-2):
                t = M[o].get(k)
                if t: bk[t[0]].append(t[1])
            for lab, ws in bk.items(): agg[lab] += sum(ws)/len(ws)
        gpred.append(agg.most_common(1)[0][0] if agg else "BEFORE")
mD = show("D  bo 3/4/5 tren GOLD (tran)", gpred)
