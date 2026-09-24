# -*- coding: utf-8 -*-
"""Where is the information lost -- in the features, or in the inference?

Four context sources, one protocol, same documents:

  A  pair-only                    the 257-rule classifier
  B  pair + STRUCTURAL context    neighbourhood described WITHOUT any temporal label:
                                  how many events share an entity with both endpoints,
                                  which types those events are, which roles they fill.
                                  Legal at test time -- none of it is a target edge.
  C  pair + PREDICTED neighbours  triangle rules over the classifier's own output
  D  pair + GOLD neighbours       triangle rules over the true graph (not reachable)

If B lands above A, observable structure carries usable signal and the loss is in the
inference step. If B sits at A, the KG's structure is exhausted and the remaining gap
needs text.

Protocol frozen for every level: candidates -> drop self -> CAP -> score. The earlier
28.56 / 38.30 discrepancy came from applying CAP before the self-filter.
"""
import sys, io, json, math
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V

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
def dirnet(tr):
    adj = defaultdict(dict)
    for a, b, r in tr: adj[a][b] = r; adj[b][a] = INV[r]
    return adj
def mids_of(adj, a, b):
    """frozen protocol: candidates -> drop self -> CAP."""
    return sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]

def load(path, limit=0):
    """documents with gold edges, node records and the anchor map."""
    out = []
    for i, line in enumerate(io.open(path, encoding="utf-8")):
        if limit and i >= limit: break
        if not line.strip(): continue
        rec = json.loads(line); nd = rec["nodes"]
        anch = defaultdict(set)
        for p in rec["anchored_pairs"]:
            for ra, rb in p["roles"]: anch[(p["a"], p["b"])].add((ra, rb))
        es = [(e["s"], e["t"], e["rel"]) for e in rec["target_edges"]
              if nd.get(e["s"], {}).get("kind") == "event"
              and nd.get(e["t"], {}).get("kind") == "event"]
        if es: out.append((rec["doc_id"], es, nd, anch))
    return out

TR = load(GRAPH/"train.jsonl", 400)
VA = load(GRAPH/"valid.jsonl", LIMIT)
print("train %d doc  valid %d doc" % (len(TR), len(VA)), flush=True)

# ---------------------------------------------------------------- structural context (no labels)
def struct_conds(nd, anch, a, b, others):
    """Describe the shared neighbourhood WITHOUT reading any temporal label.

    `others` are the events adjacent to both a and b in the *candidate* graph, which is
    every event pair present in the document -- adjacency here means "a target edge
    exists", a fact given at test time, unlike the label on it.
    """
    out = []
    n = len(others)
    out.append(("NSH", "count", "0" if n == 0 else ("1" if n == 1 else ("2-3" if n <= 3 else "4+"))))
    ts = Counter(nd[c].get("type") for c in others if c in nd)
    for t, k in ts.most_common(3):
        out.append(("NSH", "type", t))
    # roles the shared events fill
    rs = Counter()
    for c in others:
        for r in (nd.get(c, {}).get("roleset") or ()): rs[r] += 1
    for r, k in rs.most_common(4):
        out.append(("NSH", "role", r))
    # do the shared events also share an entity with a or b?
    sh = sum(1 for c in others if anch.get((a, c)) or anch.get((c, a))
             or anch.get((b, c)) or anch.get((c, b)))
    out.append(("NSH", "anchored", "0" if sh == 0 else ("1" if sh == 1 else "2+")))
    # sentence spread of the neighbourhood
    sf = [nd[c].get("sent_first") for c in others if c in nd and nd[c].get("sent_first") is not None]
    if sf:
        sp = max(sf) - min(sf)
        out.append(("NSH", "spread", "0" if sp == 0 else ("1-3" if sp <= 3 else ("4-7" if sp <= 7 else "8+"))))
    return out

def build_rows(docs):
    from mine_compositional import candidate_conditions, pair_features
    from mine_mdd import relational_conditions
    rows = []
    for doc, es, nd, anch in docs:
        adj = dirnet(es)
        for a, b, r in es:
            na, nb = nd.get(a), nd.get(b)
            if not na or not nb: continue
            sh = anch.get((a, b)) or anch.get((b, a)) or set()
            f = pair_features(na, nb, sh, bool(sh), frozenset())
            pair_cs = list(candidate_conditions(f)) + relational_conditions(na, nb, sh)
            others = mids_of(adj, a, b)
            st = struct_conds(nd, anch, a, b, others)
            rows.append((doc, a, b, r, f, frozenset(pair_cs), frozenset(pair_cs + st), adj))
    return rows

print("dung dac trung ...", flush=True)
TRr = build_rows(TR)
VAr = build_rows(VA)
print("  train %s cap  valid %s cap" % (format(len(TRr), ","), format(len(VAr), ",")), flush=True)

# ---------------------------------------------------------------- mine depth-2 over a condition set
def mine_pairs(rows, which, sup=30, kmin=10, dmin=5, target=0.50):
    cov = defaultdict(set); rel = []; doc = []
    for i, row in enumerate(rows):
        rel.append(row[3]); doc.append(row[0])
        for c in row[which]: cov[c].add(i)
    keep = [c for c, s in cov.items() if len(s) >= sup]
    found = {}
    for r in RELS:
        kc = {}
        for c in keep:
            kc[c] = sum(1 for i in cov[c] if rel[i] == r)
        order = sorted((c for c in keep if kc[c] >= kmin), key=lambda c: -kc[c])
        for ii, ci in enumerate(order):
            if wlb(kc[ci], kc[ci]) < target: break
            for cj in order[ii+1:]:
                m = min(kc[ci], kc[cj])
                if wlb(m, m) < target: break
                inter = cov[ci] & cov[cj]
                if len(inter) < sup: continue
                k = sum(1 for i in inter if rel[i] == r)
                if k < kmin: continue
                w = wlb(k, len(inter))
                if w < target: continue
                if len(set(doc[i] for i in inter if rel[i] == r)) < dmin: continue
                key = (ci, cj, r)
                if key not in found or w > found[key][0]:
                    found[key] = (w, k, len(inter))
    return found

def score_with(found, rows, which):
    pred = []
    for row in rows:
        cs = row[which]
        agg = {}
        for (ci, cj, r), (w, k, n) in found.items():
            if ci in cs and cj in cs:
                v = w / PRIOR[r]
                if v > agg.get(r, 0.0): agg[r] = v
        pred.append(max(agg, key=agg.get) if agg else "BEFORE")
    return pred

gold = [row[3] for row in VAr]
print()
print("=" * 96)
print("ABLATION 4 TANG — cung document, cung protocol CAP")
print("=" * 96)

# A: pair-only, using the frozen 257-rule library for comparability
rules = V.load_rules(ART/"rules_rx_c70.json")
idx = V.build_index(rules, [(None, row[4], row[5]) for row in VAr])
predA = []
for row in VAr:
    h = V.firing(rules, idx, row[4], row[5])
    predA.append(V.combine(rules, h, "max-norm", 5) or V.FALLBACK)
mA, perA, aA = macro(predA, gold)
print("  A  pair-only (257 rule)              macro-F1 %6.2f%%  acc %6.2f%%" % (100*mA, 100*aA))
print("       " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*perA[r]) for r in RELS))

# A': same miner, pair conditions only -- the controlled baseline for B
fA = mine_pairs(TRr, 5)
mA2, perA2, aA2 = macro(score_with(fA, VAr, 5), gold)
print("  A' pair-only (mine lai, %4d luat)   macro-F1 %6.2f%%  acc %6.2f%%"
      % (len(fA), 100*mA2, 100*aA2))

# B: pair + structural context, no temporal labels anywhere
fB = mine_pairs(TRr, 6)
mB, perB, aB = macro(score_with(fB, VAr, 6), gold)
print("  B  + cau truc (KHONG nhan) %5d luat macro-F1 %6.2f%%  acc %6.2f%%"
      % (len(fB), 100*mB, 100*aB))
print("       " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*perB[r]) for r in RELS))

# C and D: triangle rules over predicted / gold neighbours
sig = defaultdict(Counter); sd = defaultdict(lambda: defaultdict(set))
for doc, es, nd, anch in TR:
    adj = dirnet(es)
    for a, b, r in es:
        for c in mids_of(adj, a, b):
            k = (adj[a][c], adj[c][b])
            sig[k][r] += 1; sd[k][r].add(doc)
R3 = {}
for k, c in sig.items():
    n = sum(c.values()); top, kk = c.most_common(1)[0]
    if n < 30 or kk < 10 or len(sd[k][top]) < 5: continue
    w = wlb(kk, n)
    if w >= 0.50: R3[k] = (top, w)

bydoc = defaultdict(list)
for i, row in enumerate(VAr): bydoc[row[0]].append(i)
def tri_pred(labels):
    out = [None]*len(VAr)
    for doc, ids in bydoc.items():
        adj = dirnet([(VAr[i][1], VAr[i][2], labels[i]) for i in ids])
        for i in ids:
            a, b = VAr[i][1], VAr[i][2]
            agg = Counter()
            for c in mids_of(adj, a, b):
                t = R3.get((adj[a][c], adj[c][b]))
                if t: agg[t[0]] += t[1]
            out[i] = agg.most_common(1)[0][0] if agg else "BEFORE"
    return out
mC, perC, aC = macro(tri_pred(predA), gold)
mD, perD, aD = macro(tri_pred(gold), gold)
print("  C  + hang xom DU DOAN (%3d luat)     macro-F1 %6.2f%%  acc %6.2f%%" % (len(R3), 100*mC, 100*aC))
print("  D  + hang xom GOLD (oracle)          macro-F1 %6.2f%%  acc %6.2f%%" % (100*mD, 100*aD))
print("       " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*perD[r]) for r in RELS))

print()
print("  %-38s%10s" % ("so voi A'", "chenh"))
print("  " + "-" * 50)
for nm, m in (("B  cau truc, khong nhan", mB), ("C  hang xom du doan", mC), ("D  hang xom gold", mD)):
    print("  %-38s%9.2f" % (nm, 100*(m - mA2)))
print()
print("  -> %s" % ("B vuot A': cau truc quan sat duoc CO tin hieu, mat mat nam o inference"
      if mB > mA2 + 0.005 else
      "B khong vuot A': cau truc KG da can, khoang cach con lai can text"))
