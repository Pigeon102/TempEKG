# -*- coding: utf-8 -*-
"""Controlled neighbour-noise sweep: is higher-order reasoning intrinsically fragile?

Three explanations survive for why higher-order rules reach 33% on a gold graph and
18-23% on a predicted one:

  A  intrinsic noise sensitivity -- the rules simply break when neighbours are wrong
  B  calibration / local-inference problem -- fixable with better inference
  C  genuine need for global joint optimisation

This separates them cheaply. Start from the GOLD graph and corrupt neighbouring labels
by a controlled fraction, under two noise shapes:

  uniform       a wrong label drawn from the corpus marginal
  model-shaped  a wrong label drawn from the pair classifier's own confusion profile
                P(predicted | gold), which is 86.5% a single BEFORE<->CONTAINS swap

If the curve at the classifier's real error rate (12.46%) lands near the 18-23% already
measured, the cause is A and no amount of inference machinery will help. If it stays
high, the cause is B or C and joint inference is worth building.
"""
import sys, io, json, math, random
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V

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

# ---------------------------------------------------------------- confusion profile
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
gold_flat = [g for d in docs for (_, _, g, _) in d]
pred_flat = [p for d in docs for (_, _, _, p) in d]
real_err = sum(1 for g, p in zip(gold_flat, pred_flat) if g != p) / len(gold_flat)

conf = defaultdict(Counter)
for g, p in zip(gold_flat, pred_flat):
    if g != p: conf[g][p] += 1
marg = Counter(gold_flat); tot = sum(marg.values())
print("valid %d doc, %s cap, ty le loi that %.2f%%"
      % (len(VF), format(len(gold_flat), ","), 100*real_err), flush=True)

def corrupt_graph(docs, rate, shape, rng):
    out = []
    for d in docs:
        nd = []
        for (a, b, g, _) in d:
            if rng.random() < rate:
                if shape == "uniform":
                    others = [r for r in RELS if r != g]
                    w = [marg[r]/tot for r in others]
                    lab = rng.choices(others, weights=w)[0]
                else:
                    c = conf.get(g)
                    if c:
                        ks = list(c); ws = [c[k] for k in ks]
                        lab = rng.choices(ks, weights=ws)[0]
                    else:
                        lab = rng.choice([r for r in RELS if r != g])
            else:
                lab = g
            nd.append((a, b, g, lab))
        out.append(nd)
    return out

def apply_ho(docs):
    pred = []
    for d in docs:
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
            pred.append(agg.most_common(1)[0][0] if agg else "BEFORE")
    return pred

print()
print("=" * 96)
print("NOISE SWEEP: bat dau tu do thi GOLD, lam hong hang xom theo ty le")
print("=" * 96)
print("  %-8s%22s%22s" % ("nhieu", "uniform", "model-shaped"))
print("  %-8s%11s%11s%11s%11s" % ("", "macro-F1", "acc", "macro-F1", "acc"))
print("  " + "-" * 52)
rng = random.Random(0)
for rate in (0.0, 0.05, 0.10, 0.1246, 0.20, 0.30, 0.40):
    row = []
    for shape in ("uniform", "model"):
        cd = corrupt_graph(docs, rate, shape, random.Random(0))
        m, per, acc = macro(apply_ho(cd), gold_flat)
        row += [100*m, 100*acc]
    mark = "  <- ty le loi that" if abs(rate - real_err) < 0.005 else ""
    print("  %-8s%10.2f%%%10.2f%%%10.2f%%%10.2f%%%s"
          % ("%.1f%%" % (100*rate), row[0], row[1], row[2], row[3], mark))

print()
print("  Doi chieu (da do truoc):")
print("    pair-only 257 rule        24.11%")
print("    hard iterative            18.24%")
print("    soft one-pass (tot nhat)  22.90%")
