# -*- coding: utf-8 -*-
"""Check four claims from the feedback before any of them goes in a paper.

1 THE 88% DECOMPOSITION. The claim is that 12.49 of the 14.19-point oracle gap is
  neighbour noise and only 2.89 is inference. That arithmetic mixes two different
  experiments: the 25.81% came from corrupting a GOLD graph at 12.5%, the 22.92% from
  soft inference over PREDICTED labels. They are only comparable if injected noise and
  real prediction errors do the same damage. Test: corrupt the gold graph using exactly
  the classifier's per-edge decisions rather than a sampled rate.

2 DOES CLUSTERING ACTUALLY MATTER? sd 13.5% vs 2.7% is a fact about the errors, not
  proof it costs anything. Test: hold the overall error rate fixed at 12.46% and vary
  only how the errors are distributed -- spread evenly across documents, versus
  concentrated in the worst ones. If the two score the same, clustering is a red
  herring.

3 LUPI, SMALLEST USEFUL VERSION. Can gold triangle context, available only at training
  time, improve a classifier that sees pair features only at test time? Test the
  precondition: do the edges where higher-order rules are right, and pair rules wrong,
  share features the pair level could learn from?

4 IS THE PRIVILEGED SIGNAL JUST THE LABEL? The feedback flags leakage risk. Test: how
  much of the triangle rule's answer is recoverable from the target edge's own label,
  i.e. would a teacher trained on it simply be memorising Y.
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
sig = defaultdict(Counter); sd = defaultdict(lambda: defaultdict(set))
for doc, es in TRG:
    adj = dirnet(es)
    for a, b, r in es:
        for c in sorted(set(adj[a]) & set(adj[b]))[:CAP]:
            if c in (a, b): continue
            k = (adj[a][c], adj[c][b])
            sig[k][r] += 1; sd[k][r].add(doc)
R3 = {}
for k, c in sig.items():
    n = sum(c.values()); top, kk = c.most_common(1)[0]
    if n < 30 or kk < 10 or len(sd[k][top]) < 5: continue
    w = wlb(kk, n)
    if w >= 0.50: R3[k] = (top, w)
print("luat bo 3: %d" % len(R3), flush=True)

rules = V.load_rules(ART/"rules_rx_c70.json")
VF = load_feat(GRAPH/"valid.jsonl", LIMIT)
flat = [(f, cs) for _, rows in VF for (_, _, _, f, cs) in rows]
idx = V.build_index(rules, [(None, f, cs) for f, cs in flat])
docs = []
for doc, rows in VF:
    cur = []
    for (a, b, g, f, cs) in rows:
        h = V.firing(rules, idx, f, cs)
        cur.append((a, b, g, V.combine(rules, h, "max-norm", 5) or V.FALLBACK, cs))
    docs.append(cur)
gold = [g for d in docs for (_, _, g, _, _) in d]
err = sum(1 for d in docs for (_, _, g, p, _) in d if g != p) / len(gold)
print("valid %d doc, %s cap, loi %.2f%%" % (len(VF), format(len(gold), ","), 100*err), flush=True)

def ho(graph):
    out = []
    for d in graph:
        adj = dirnet([(a, b, lab) for (a, b, _, lab) in d])
        for (a, b, g, lab) in d:
            agg = Counter()
            for c in sorted(set(adj[a]) & set(adj[b]))[:CAP]:
                if c in (a, b): continue
                t = R3.get((adj[a][c], adj[c][b]))
                if t: agg[t[0]] += t[1]
            out.append(agg.most_common(1)[0][0] if agg else "BEFORE")
    return out

gd = [[(a, b, g, g) for (a, b, g, _, _) in d] for d in docs]
pd_ = [[(a, b, g, p) for (a, b, g, p, _) in d] for d in docs]
mG = macro(ho(gd), gold)[0]; mP = macro(ho(pd_), gold)[0]
mpair = macro([p for d in docs for (_, _, _, p, _) in d], gold)[0]
print()
print("=" * 92)
print("1. PHAN RA 88% CO DUNG KHONG?")
print("=" * 92)
print("  pair-only            %.2f%%" % (100*mpair))
print("  bo 3 tren GOLD       %.2f%%" % (100*mG))
print("  bo 3 tren DU DOAN    %.2f%%" % (100*mP))
# the honest control: corrupt gold using the classifier's ACTUAL per-edge errors
# this is exactly the predicted graph, so it must equal mP -- stated for clarity
# instead, corrupt at the same RATE but choosing which edges at random
rng = random.Random(0)
runs = []
for seed in range(3):
    rng = random.Random(seed)
    cd = []
    for d in docs:
        nd = []
        for (a, b, g, p, _) in d:
            nd.append((a, b, g, p if rng.random() < err else g))
        cd.append(nd)
    runs.append(macro(ho(cd), gold)[0])
mR = sum(runs)/len(runs)
print("  bo 3, loi RAI DEU cung ty le (3 seed)  %.2f%%" % (100*mR))
print()
gap = mG - mpair
print("  oracle gap          %.2f diem" % (100*gap))
print("  do nhieu rai deu    %.2f diem  (%.0f%% cua gap)" % (100*(mG-mR), 100*(mG-mR)/gap))
print("  do phan con lai     %.2f diem  (%.0f%% cua gap)" % (100*(mR-mP), 100*(mR-mP)/gap))

print()
print("=" * 92)
print("2. CLUSTERING CO THUC SU GAY THIET HAI KHONG?")
print("=" * 92)
print("  Giu nguyen tong so canh sai, chi doi CACH PHAN BO giua cac document")
nerr = sum(1 for d in docs for (_, _, g, p, _) in d if g != p)
# (a) spread evenly: same count, but each document gets the same rate
even = []
rng = random.Random(0)
for d in docs:
    k = int(round(err*len(d)))
    ids = rng.sample(range(len(d)), min(k, len(d)))
    nd = []
    for i, (a, b, g, p, _) in enumerate(d):
        nd.append((a, b, g, p if i in ids else g))
    even.append(nd)
ne = sum(1 for d in even for (_, _, g, l) in d if g != l)
# (b) concentrated: fill the worst documents completely first
order = sorted(range(len(docs)), key=lambda i: -sum(1 for (_, _, g, p, _) in docs[i] if g != p))
budget = nerr; conc = [None]*len(docs)
for i in order:
    d = docs[i]; nd = []
    for (a, b, g, p, _) in d:
        if budget > 0 and g != p:
            nd.append((a, b, g, p)); budget -= 1
        else:
            nd.append((a, b, g, g))
    conc[i] = nd
# (b) as built equals the real graph; instead concentrate by moving errors into few docs
conc2 = []
budget = nerr
rng = random.Random(1)
for i, d in enumerate(docs):
    nd = []
    for (a, b, g, p, _) in d:
        if budget > 0 and p != g:
            nd.append((a, b, g, p)); budget -= 1
        elif budget > 0:
            alt = rng.choice([r for r in RELS if r != g])
            nd.append((a, b, g, alt)); budget -= 1
        else:
            nd.append((a, b, g, g))
    conc2.append(nd)
nc = sum(1 for d in conc2 for (_, _, g, l) in d if g != l)
print("  %-42s%10s%12s" % ("phan bo loi", "so canh sai", "macro-F1"))
print("  " + "-" * 66)
print("  %-42s%10s%11.2f%%" % ("that te (tum theo document)", format(nerr, ","), 100*mP))
print("  %-42s%10s%11.2f%%" % ("rai deu moi document cung ty le", format(ne, ","), 100*macro(ho(even), gold)[0]))
print("  %-42s%10s%11.2f%%" % ("don vao it document dau tien", format(nc, ","), 100*macro(ho(conc2), gold)[0]))

print()
print("=" * 92)
print("3. LUPI CO TIEN DE KHONG?")
print("=" * 92)
hp = ho(gd); pp = [p for d in docs for (_, _, _, p, _) in d]
allcs = [cs for d in docs for (_, _, _, _, cs) in d]
win = [(i, g) for i, (g, h_, p_) in enumerate(zip(gold, hp, pp)) if h_ == g and p_ != g]
print("  canh ma bo 3 (gold context) DUNG nhung pair-level SAI: %s" % format(len(win), ","))
print("     %.1f%% tong so canh" % (100*len(win)/len(gold)))
cw = Counter(g for _, g in win)
print("     phan bo nhan: %s" % dict(cw.most_common()))
# do those edges share pair-level features?  measure how distinguishable they are
wid = set(i for i, _ in win)
fw, fo = Counter(), Counter()
for i, cs in enumerate(allcs):
    tgt = fw if i in wid else fo
    for c in cs: tgt[c] += 1
nw, no = len(wid), len(allcs)-len(wid)
cand = []
for c, k in fw.items():
    if k < 30: continue
    pw = k/nw; po = fo.get(c, 0)/no
    if po > 0: cand.append((pw/po, k, c))
cand.sort(reverse=True)
print("     dac trung pair-level phan biet nhom nay (lift, k):")
for L, k, c in cand[:5]:
    print("       %5.2fx  k=%-6s %s" % (L, format(k, ","), c))
print("     -> %s" % ("co tin hieu, teacher/student co tien de" if cand and cand[0][0] > 1.5
                      else "KHONG co dac trung nao phan biet manh; LUPI kho co cho bam"))

print()
print("=" * 92)
print("4. TIN HIEU PRIVILEGED CO PHAI CHINH LA NHAN KHONG?")
print("=" * 92)
same = sum(1 for g, h_ in zip(gold, hp) if g == h_)
print("  bo 3 tren gold context doan dung %.2f%% so canh" % (100*same/len(gold)))
print("  -> teacher hoc tu context nay se hoc mot ham gan dung bang Y o %.0f%% truong hop"
      % (100*same/len(gold)))
print("     Do la rui ro ro ri that: privileged context chua gan het thong tin cua Y.")
