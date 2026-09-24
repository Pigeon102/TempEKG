# -*- coding: utf-8 -*-
"""Re-run every higher-order experiment with edge direction handled correctly.

The adjacency bug (adj[b][a] = r instead of the converse) affected all nine scripts, so
every number derived from a triangle signature has to be recomputed: Bai 2 audit, the
iterative refinement, soft one-pass, the noise sweep, and joint inference.
"""
import sys, io, json, math, random
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V
from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL
from noise_aware import score_document

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
INV = {"BEFORE": "iBEFORE", "CONTAINS": "iCONTAINS", "SIMULTANEOUS": "SIMULTANEOUS",
       "OVERLAP": "iOVERLAP", "BEGINS-ON": "BEGINS-ON", "ENDS-ON": "iENDS-ON"}
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
def dirnet(triples):
    adj = defaultdict(dict)
    for a, b, r in triples:
        adj[a][b] = r; adj[b][a] = INV[r]
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
    return R
M = {3: mine(1), 4: mine(2), 5: mine(3)}
print("luat: bo3 %d  bo4 %d  bo5 %d" % (len(M[3]), len(M[4]), len(M[5])), flush=True)

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
def probs(hits):
    sc = {r: 0.0 for r in RELS}
    for ri in hits:
        ru = rules[ri]
        sc[ru["rel"]] = max(sc[ru["rel"]], ru["wlb"]/PRIOR[ru["rel"]])
    t = sum(sc.values())
    return dict(PRIOR) if t <= 0 else {r: sc[r]/t for r in RELS}

docs = []
for doc, rows in VF:
    cur = []
    for (a, b, g, f, cs) in rows:
        h = V.firing(rules, idx, f, cs)
        cur.append((a, b, g, V.combine(rules, h, "max-norm", 5) or V.FALLBACK,
                    unary(h), probs(h)))
    docs.append(cur)
gold = [g for d in docs for (_, _, g, _, _, _) in d]
nbad = sum(1 for d in docs for (_, _, g, p, _, _) in d if g != p)
print("valid %d doc, %s cap, %s canh sai (%.2f%%)"
      % (len(VF), format(len(gold), ","), format(nbad, ","), 100*nbad/len(gold)), flush=True)

def ho_on(graph, orders=(3,)):
    out = []
    for d in graph:
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
print("=" * 94); print("1. BAI 1"); print("=" * 94)
pp = [p for d in docs for (_, _, _, p, _, _) in d]
m0, _, a0 = macro(pp, gold)
print("  %-32s macro-F1 %6.2f%%  acc %6.2f%%" % ("pair-only 257 rule", 100*m0, 100*a0))
gd = [[(a, b, g, g) for (a, b, g, _, _, _) in d] for d in docs]
for od, nm in (((3,), "bo 3 GOLD"), ((3,4), "bo 3+4 GOLD"), ((3,4,5), "bo 3+4+5 GOLD")):
    m, per, acc = macro(ho_on(gd, od), gold)
    print("  %-32s macro-F1 %6.2f%%  acc %6.2f%%" % (nm, 100*m, 100*acc))
    if od == (3,): print("     " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per[r]) for r in RELS))

# iterative
cur = [[(a, b, g, p) for (a, b, g, p, _, _) in d] for d in docs]
for t in range(5):
    cur = [[(a, b, g, lab) for (a, b, g, lab) in zip2] for zip2 in
           [[(a, b, g, nl) for (a, b, g, _), nl in zip(d, ho_on([d], (3,)))] for d in cur]]
predB = [p for d in cur for (_, _, _, p) in d]
mB, _, aB = macro(predB, gold)
print("  %-32s macro-F1 %6.2f%%  acc %6.2f%%" % ("chay lap 5 vong (bo 3)", 100*mB, 100*aB))

# soft
best = (0, None)
for LAM in (0.1, 0.3, 1.0):
    pc = []
    for d in docs:
        dist = {}; nb = defaultdict(set)
        for (a, b, _, _, _, pr) in d:
            dist[(a, b)] = pr
            dist[(b, a)] = {INV.get(r, r): v for r, v in pr.items()}
            nb[a].add(b); nb[b].add(a)
        for (a, b, g, p, u, pr) in d:
            sc = {r: pr[r] for r in RELS}
            for c in sorted(nb[a] & nb[b])[:CAP]:
                pac, pcb = dist.get((a, c)), dist.get((c, b))
                if not pac or not pcb: continue
                for r1, v1 in pac.items():
                    if v1 < 0.01: continue
                    for r2, v2 in pcb.items():
                        if v2 < 0.01: continue
                        t3 = M[3].get((r1, r2))
                        if t3: sc[t3[0]] += LAM * v1 * v2 * t3[1]
            pc.append(max(sc, key=sc.get))
    m, _, acc = macro(pc, gold)
    if m > best[0]: best = (m, LAM, acc)
print("  %-32s macro-F1 %6.2f%%  acc %6.2f%%  (lambda=%.1f)"
      % ("soft one-pass tot nhat", 100*best[0], 100*best[2], best[1]))

print()
print("=" * 94); print("2. BAI 2 — audit tren canh model du doan"); print("=" * 94)
def audit_ho(k_frac=3.0):
    ranked = []
    for d in docs:
        adj = dirnet([(a, b, p) for (a, b, _, p, _, _) in d])
        for (a, b, g, p, _, _) in d:
            mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
            agg = Counter()
            for o in (3, 4, 5):
                bk = defaultdict(list)
                for k in keys(adj, a, b, mids, o-2):
                    t = M[o].get(k)
                    if t: bk[t[0]].append(t[1])
                for l, ws in bk.items(): agg[l] += sum(ws)/len(ws)
            if not agg: continue
            bl, bw = agg.most_common(1)[0]
            if bl == p: continue
            ranked.append((bw - agg.get(p, 0.0), g != p, g, bl))
    ranked.sort(key=lambda t: -t[0])
    k = max(1, int(round(k_frac*nbad)))
    top = ranked[:k]
    fb = sum(1 for _, ib, _, _ in top if ib)
    rp = sum(1 for _, ib, o, pr in top if ib and pr == o)
    return len(ranked), (fb/len(top) if top else 0), fb/nbad, (rp/fb if fb else 0), rp/nbad
def audit_cl(k_frac=3.0):
    ranked = []
    for d in docs:
        es = [(a, b, p) for (a, b, _, p, _, _) in d]
        bad = {(a, b): g for (a, b, g, p, _, _) in d if g != p}
        for s, a, b, c_, pr in score_document(es):
            ranked.append((s, (a, b) in bad, bad.get((a, b)), pr))
    ranked.sort(key=lambda t: -t[0])
    k = max(1, int(round(k_frac*nbad)))
    top = ranked[:k]
    fb = sum(1 for _, ib, _, _ in top if ib)
    rp = sum(1 for _, ib, o, pr in top if ib and pr == o)
    return len(ranked), (fb/len(top) if top else 0), fb/nbad, (rp/fb if fb else 0), rp/nbad
c = audit_cl(); h = audit_ho()
print("  %-14s%14s%14s" % ("chi so", "closure", "bac cao"))
print("  " + "-" * 44)
print("  %-14s%14s%14s" % ("xep hang", format(c[0], ","), format(h[0], ",")))
for i, nm in ((1, "P@k"), (2, "found_all"), (3, "repair@k"), (4, "R_all")):
    print("  %-14s%13.2f%%%13.2f%%" % (nm, 100*c[i], 100*h[i]))

print()
print("=" * 94); print("3. NOISE SWEEP (bo 3, tu gold)"); print("=" * 94)
conf = defaultdict(Counter)
for d in docs:
    for (_, _, g, p, _, _) in d:
        if g != p: conf[g][p] += 1
print("  %-10s%14s%14s" % ("nhieu", "macro-F1", "acc"))
for rate in (0.0, 0.05, 0.10, 0.1246, 0.20, 0.30):
    rng = random.Random(0); cd = []
    for d in docs:
        nd = []
        for (a, b, g, _, _, _) in d:
            lab = g
            if rng.random() < rate and conf.get(g):
                ks = list(conf[g]); ws = [conf[g][k] for k in ks]
                lab = rng.choices(ks, weights=ws)[0]
            nd.append((a, b, g, lab))
        cd.append(nd)
    m, _, acc = macro(ho_on(cd, (3,)), gold)
    mk = "  <- ty le loi that" if abs(rate - nbad/len(gold)) < 0.005 else ""
    print("  %-10s%13.2f%%%13.2f%%%s" % ("%.1f%%" % (100*rate), 100*m, 100*acc, mk))
