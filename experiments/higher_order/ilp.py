# -*- coding: utf-8 -*-
"""Joint inference over a whole document, with MDD-style domain pruning.

The noise sweep showed higher-order rules reach 27.66% at the classifier's real error
rate when the wrong edges are scattered independently, but only 18-23% on the real
predictions. The difference is that real errors CLUSTER: per-document error rate has
sd 13.5% against 2.7% expected under independence, and the worst document is 71% wrong.
Local inference cannot see that; every edge trusts neighbours that a whole bad document
got wrong together.

Joint inference optimises the document as one object:

    maximise  SUM_e s_e(y_e)  +  lambda * SUM_triangles phi(y_ac, y_cb, y_ab)

No ILP solver is available here, so this uses coordinate ascent (ICM) from the pairwise
solution -- a local optimum of the same objective, which is what an ILP would find
globally. To separate "the objective is wrong" from "the search is too weak", the run
also reports the objective value reached, and a restart from the gold assignment: if
gold scores HIGHER under the objective but search does not find it, the search is the
problem; if gold scores LOWER, the objective itself is wrong and ILP cannot help.

MDD pruning: Allen composition over the neighbours restricts each edge's domain before
search, so coordinate ascent only ever considers labels the algebra admits.
"""
import sys, io, json, math
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V
from constraint_net import MAVEN_TO_ALLEN, compose, FULL

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

# ---------------------------------------------------------------- triangle factors
TR = load_raw(GRAPH/"train.jsonl", 400)
sig = defaultdict(Counter); sd = defaultdict(lambda: defaultdict(set))
for doc, es in TR:
    adj = adjof(es)
    for a, b, r in es:
        for c in set(adj[a]) & set(adj[b]):
            if c in (a, b): continue
            k = (adj[a][c], adj[c][b])
            sig[k][r] += 1; sd[k][r].add(doc)
PHI = {}       # (r_ac, r_cb, r_ab) -> weight
for k, c in sig.items():
    n = sum(c.values())
    for r in RELS:
        if c[r] < 10 or len(sd[k][r]) < 5: continue
        p = c[r]/n
        # log-odds against the prior: positive when the triangle argues FOR r
        PHI[(k[0], k[1], r)] = math.log(max(p, 1e-6) / PRIOR[r])
print("factor tam giac: %s" % format(len(PHI), ","), flush=True)

# ---------------------------------------------------------------- pairwise unary
rules = V.load_rules(ART/"rules_rx_c70.json")
VF = load_feat(GRAPH/"valid.jsonl", LIMIT)
flat = [(f, cs) for _, rows in VF for (_, _, _, f, cs) in rows]
idx = V.build_index(rules, [(None, f, cs) for f, cs in flat])

def unary(hits):
    s = {r: math.log(PRIOR[r]) for r in RELS}      # start from the prior in log space
    for ri in hits:
        ru = rules[ri]
        s[ru["rel"]] = max(s[ru["rel"]], math.log(max(ru["wlb"], 1e-6) / PRIOR[ru["rel"]]))
    return s

docs = []
for doc, rows in VF:
    cur = []
    for (a, b, g, f, cs) in rows:
        h = V.firing(rules, idx, f, cs)
        u = unary(h)
        cur.append((a, b, g, max(u, key=u.get), u))
    docs.append(cur)
gold = [g for d in docs for (_, _, g, _, _) in d]
print("valid %d doc, %s cap" % (len(VF), format(len(gold), ",")), flush=True)

def mdd_domain(adj, a, b):
    """Labels Allen composition still admits, given the current neighbour assignment."""
    imp = FULL
    for c in set(adj[a]) & set(adj[b]):
        if c in (a, b): continue
        sa = MAVEN_TO_ALLEN.get(adj[a][c]); sb = MAVEN_TO_ALLEN.get(adj[c][b])
        if sa and sb: imp = imp & compose(sa, sb)
    dom = [r for r in RELS if MAVEN_TO_ALLEN[r] & imp]
    return dom if dom else RELS            # empty means MAVEN cannot express it: keep all

def objective(d, lab, LAM):
    adj = adjof([(a, b, lab[(a, b)]) for (a, b, _, _, _) in d])
    tot = 0.0
    for (a, b, _, _, u) in d:
        tot += u[lab[(a, b)]]
        for c in set(adj[a]) & set(adj[b]):
            if c in (a, b): continue
            tot += LAM * PHI.get((adj[a][c], adj[c][b], lab[(a, b)]), 0.0)
    return tot

def icm(d, LAM, use_mdd, init="pair", rounds=4):
    lab = {}
    for (a, b, g, p, u) in d:
        lab[(a, b)] = g if init == "gold" else p
    U = {(a, b): u for (a, b, _, _, u) in d}
    for _ in range(rounds):
        adj = adjof([(a, b, lab[(a, b)]) for (a, b, _, _, _) in d])
        changed = 0
        for (a, b, _, _, _) in d:
            mids = [c for c in set(adj[a]) & set(adj[b]) if c not in (a, b)]
            dom = mdd_domain(adj, a, b) if use_mdd else RELS
            best, bs = lab[(a, b)], None
            for r in dom:
                s = U[(a, b)][r]
                for c in mids:
                    s += LAM * PHI.get((adj[a][c], adj[c][b], r), 0.0)
                if bs is None or s > bs: bs, best = s, r
            if best != lab[(a, b)]:
                lab[(a, b)] = best; adj[a][b] = best; adj[b][a] = best; changed += 1
        if not changed: break
    return lab

print()
print("=" * 92)
print("JOINT INFERENCE (coordinate ascent tren tung document)")
print("=" * 92)
base = [p for d in docs for (_, _, _, p, _) in d]
m0, _, a0 = macro(base, gold)
print("  %-34s macro-F1 %6.2f%%  acc %6.2f%%" % ("pair-only (unary argmax)", 100*m0, 100*a0))
print()
print("  %-14s%12s%12s%12s%12s" % ("lambda", "khong MDD", "acc", "co MDD", "acc"))
print("  " + "-" * 62)
best = (m0, None)
for LAM in (0.05, 0.1, 0.2, 0.5, 1.0):
    row = []
    for use_mdd in (False, True):
        pred = []
        for d in docs:
            lab = icm(d, LAM, use_mdd)
            for (a, b, _, _, _) in d: pred.append(lab[(a, b)])
        m, per, acc = macro(pred, gold)
        row += [100*m, 100*acc]
        if m > best[0]: best = (m, (LAM, use_mdd, per))
    print("  %-14s%11.2f%%%11.2f%%%11.2f%%%11.2f%%" % ("%.2f" % LAM, row[0], row[1], row[2], row[3]))

if best[1]:
    LAM, use_mdd, per = best[1]
    print()
    print("  tot nhat: lambda=%.2f  MDD=%s  macro-F1 %.2f%%" % (LAM, use_mdd, 100*best[0]))
    print("    " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per[r]) for r in RELS))
else:
    print()
    print("  KHONG cau hinh nao vuot pair-only")

# ---------------------------------------------------------------- is the objective right?
print()
print("=" * 92)
print("MUC TIEU CO DUNG KHONG? So gia tri ham muc tieu tai nghiem tim duoc va tai GOLD")
print("=" * 92)
for LAM in (0.1, 0.5):
    win = lose = 0
    for d in docs:
        lab_s = icm(d, LAM, True)
        lab_g = {(a, b): g for (a, b, g, _, _) in d}
        os_, og = objective(d, lab_s, LAM), objective(d, lab_g, LAM)
        if og > os_: win += 1          # gold scores higher -> search is the problem
        else: lose += 1                # gold scores lower  -> objective is wrong
    print("  lambda=%.2f: GOLD diem cao hon o %d/%d document, thap hon o %d"
          % (LAM, win, len(docs), lose))
    print("     -> %s" % ("tim kiem yeu, ILP co the giup"
                          if win > lose else "HAM MUC TIEU SAI, ILP khong cuu duoc"))
