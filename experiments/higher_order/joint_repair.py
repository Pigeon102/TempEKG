# -*- coding: utf-8 -*-
"""Bai 2: document-level JOINT repair over triangles (instead of one edge at a time).

Energy of a labelling L of one document:

  E(L) = sum_e  U_e(l_e)  +  lam * sum_t  W_t * T_t(L)

  U_e(l)  = -log P(l | edge type) - log P(observed label p_e | true l)        (unary: prior + noise channel)
  T_t     = -[ log p~(config_t) - sum_{e in t} log P(l_e | edge type) ]       (triangle: minus PMI)

A triangle = 3 nodes (events or TIMEX) with all three edges; its configuration = node kinds + the
three oriented labels. p~ comes from GOLD train graphs (DISCOVERY + CONFIRMATION-1, first 400 docs
excluded), smoothed towards the product of marginals. Using PMI and not the raw frequency matters:
a raw-frequency term rewards turning everything into BEFORE, which is exactly how the crude
triangle vote destroyed rare labels. W_t is 1 ('sum') or 1/#triangles of the edge ('mean').

Optimisation: iterated conditional modes, started from the observed labels, visiting only edges
that sit in a triangle with negative PMI and re-queueing the neighbours of every changed edge.

Noise channel P(p | l):
  injected   known generator: 1-rho if p = l, else rho * q(p) / (1 - q(l))  (q = type marginal)
  classifier confusion matrix of the classifier per edge type, estimated on CONFIRMATION-2
lam and the weighting mode are chosen on CONFIRMATION-2 (same noise, different seed for injected
noise), by net errors or by macro-F1; valid opened once.
"""
import io, os, json, math, random, time
from pathlib import Path
from collections import Counter, defaultdict
HERE = Path(__file__).resolve().parent
SRC = io.open(HERE/"bai1_all_edges.py", encoding="utf-8").read()
exec(SRC[:SRC.index("# ---------------------------------------------------------------- miner")])
exec(SRC[SRC.index("def prf(pred, gold):"):SRC.index("def show(nm, pred, gold):")])
SMOKE = os.environ.get("SMOKE") == "1"
TAG = os.environ.get("TAG", "")
PL = json.load(io.open(ART/("pred_layered%s.json" % TAG), encoding="utf-8"))
first400 = set()
if not TAG or os.environ.get("EXCL400"):
    for i, line in enumerate(io.open(GRAPH/"train.jsonl", encoding="utf-8")):
        if i >= 400: break
        first400.add(json.loads(line)["doc_id"])
TRg = [d for d in TR if d["id"] not in first400]
if SMOKE: TRg = TRg[:600]; VA = VA[:120]
STATS = [d for d in TRg if d["sp"] in ("disc", "conf1")]; TUNE = [d for d in TRg if d["sp"] == "conf2"]
log("thong ke gold: %d doc, chinh tham so: %d doc, valid %d doc" % (len(STATS), len(TUNE), len(VA)))
LABS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
SYMM = {"SIMULTANEOUS", "BEGINS-ON"}
def inv_(l): return l if l in SYMM else ("i" + l)

# ---------------------------------------------------------------- structure: triangles per document
def prepare(d):
    K = {n: ("E" if v.get("kind") == "event" else "T") for n, v in d["nd"].items() if v.get("kind") in ("event", "timex")}
    idx = {}; nbr = defaultdict(set)
    for j, (a, b, r, k) in enumerate(d["edges"]): idx[(a, b)] = j; nbr[a].add(b); nbr[b].add(a)
    tris = []; inc = defaultdict(list)
    for a in nbr:
        for b in nbr[a]:
            if b <= a: continue
            for c in nbr[a] & nbr[b]:
                if c <= b: continue
                parts = []
                for (u, v) in ((a, b), (b, c), (a, c)):
                    j = idx.get((u, v))
                    parts.append((j, False) if j is not None else (idx[(v, u)], True))
                tid = len(tris); tris.append(((K[a], K[b], K[c]), parts))
                for pos_, (j, rev) in enumerate(parts): inc[j].append((tid, pos_))
    d["tris"] = tris; d["inc"] = inc
t0 = time.time()
for d in STATS + TUNE + VA: prepare(d)
log("tam giac: thong ke %d, chinh %d, valid %d" % (sum(len(d["tris"]) for d in STATS), sum(len(d["tris"]) for d in TUNE), sum(len(d["tris"]) for d in VA)))

def olab(l, rev): return inv_(l) if rev else l

# ---------------------------------------------------------------- gold statistics
FREQ = Counter(); TOT = Counter(); MARG = defaultdict(Counter)
for d in STATS:
    for (a, b, r, k) in d["edges"]: MARG[k][r] += 1
    lab = [e[2] for e in d["edges"]]
    for kinds, parts in d["tris"]:
        c = kinds + tuple(olab(lab[j], rev) for j, rev in parts)
        FREQ[c] += 1; TOT[kinds] += 1
Q = {k: {r: (MARG[k][r] + 1) / (sum(MARG[k].values()) + 6) for r in LABS} for k in MARG}
def ktype(kx, ky): return kx + ky
BETA = 10.0
_cache = {}
def tri_pmi(kinds, olabs):
    """log p~(config) - sum log q(label of each edge in its stored direction) -- computed on the
    oriented labels; the marginal of an oriented label is the marginal of its stored label."""
    key = kinds + olabs
    v = _cache.get(key)
    if v is not None: return v
    pairs = ((kinds[0], kinds[1]), (kinds[1], kinds[2]), (kinds[0], kinds[2]))
    lq = 0.0
    for (kx, ky), l in zip(pairs, olabs):
        if l.startswith("i"): k, base = ky + kx, l[1:]
        else: k, base = kx + ky, l
        lq += math.log(Q.get(k, Q["EE"]).get(base, 1e-6))
    prod = math.exp(lq)
    p = (FREQ.get(key, 0) + BETA*prod) / (TOT.get(kinds, 0) + BETA)
    v = math.log(p) - lq
    _cache[key] = v
    return v

# ---------------------------------------------------------------- noise channels
def chan_injected(rho):
    C = {}
    for k in Q:
        for l in LABS:
            for p in LABS:
                C[(k, p, l)] = math.log(1 - rho) if p == l else math.log(max(1e-9, rho * Q[k][p] / (1 - Q[k][l])))
    return C
def chan_confusion(docs, labfn):
    cnt = Counter(); tot = Counter()
    for d in docs:
        for (a, b, r, k), p in zip(d["edges"], labfn(d)): cnt[(k, p, r)] += 1; tot[(k, r)] += 1
    return {(k, p, l): math.log((cnt[(k, p, l)] + 0.5) / (tot[(k, l)] + 3.0)) for k in Q for p in LABS for l in LABS}

# ---------------------------------------------------------------- ICM
def repair(d, obs, C, lam, mode, alpha=0.0, max_sweeps=4):
    lab = list(obs); edges = d["edges"]; tris = d["tris"]; inc = d["inc"]
    def local(j, l):
        k = edges[j][3]
        u = -(1 - alpha) * math.log(Q[k][l]) - C[(k, obs[j], l)]
        ts = inc.get(j, ())
        if not ts: return u
        s = 0.0
        for tid, pos_ in ts:
            kinds, parts = tris[tid]
            ol = [olab(lab[jj], rev) for jj, rev in parts]
            ol[pos_] = olab(l, parts[pos_][1])
            s -= tri_pmi(kinds, tuple(ol))
        if mode == "mean": s /= len(ts)
        return u + lam * s
    queue = []
    for tid, (kinds, parts) in enumerate(tris):
        if tri_pmi(kinds, tuple(olab(lab[j], rev) for j, rev in parts)) < 0:
            queue += [j for j, _ in parts]
    todo = set(queue)
    for _ in range(max_sweeps):
        if not todo: break
        nxt = set()
        for j in todo:
            cur = lab[j]; best, bv = cur, local(j, cur)
            for l in LABS:
                if l == cur or Q[edges[j][3]][l] < 1e-4: continue
                v = local(j, l)
                if v < bv - 1e-9: best, bv = l, v
            if best != cur:
                lab[j] = best
                for tid, _ in inc.get(j, ()):
                    for jj, _ in tris[tid][1]:
                        if jj != j: nxt.add(jj)
        todo = nxt
    return lab

def evaluate(docs, obs_of, fin_of):
    c = Counter(); pred = []; gold = []; per = defaultdict(Counter)
    for d in docs:
        for (a, b, r, k), s, f in zip(d["edges"], obs_of(d), fin_of(d)):
            c["n"] += 1; c["bad0"] += (s != r); c["bad1"] += (f != r)
            per[k]["n"] += 1; per[k]["b0"] += (s != r); per[k]["b1"] += (f != r)
            if f != s:
                c["flag"] += 1
                if s != r: c["hit"] += 1; c["fix"] += (f == r)
                else: c["brk"] += 1
            pred.append(f); gold.append(r)
    P = c["hit"]/max(1, c["flag"]); R = c["hit"]/max(1, c["bad0"]); F = 2*P*R/(P+R) if P+R else 0
    return c, P, R, F, prf(pred, gold)[0], per

def show(nm, docs, obs_of, fin_of):
    c, P, R, F, m, per = evaluate(docs, obs_of, fin_of)
    m0 = prf([q for d in docs for q in obs_of(d)], [e[2] for d in docs for e in d["edges"]])[0]
    print("  %-38s P %6.2f%% R %6.2f%% F1 %6.2f%%  sua %6d hong %5d rong %+6d  loi %5.2f%% -> %5.2f%%  macro %6.2f%% -> %6.2f%%"
          % (nm, 100*P, 100*R, 100*F, c["fix"], c["brk"], c["bad0"]-c["bad1"], 100*c["bad0"]/c["n"], 100*c["bad1"]/c["n"], 100*m0, 100*m), flush=True)
    print("      loi theo loai: " + "   ".join("%s %.1f->%.1f" % (k, 100*per[k]["b0"]/per[k]["n"], 100*per[k]["b1"]/per[k]["n"]) for k in ("EE", "ET", "TE", "TT")))

GRID = [("mean", l) for l in (0.2, 0.5, 1.0, 2.0)] + [("sum", l) for l in (0.03, 0.1, 0.3, 1.0)]
ALPHAS = (0.0, 0.5, 1.0)
def run_scenario(title, tune_obs, test_obs, C):
    """alpha weakens the label prior in the unary term: alpha = 0 is the Bayes posterior, which
    turns rare observed labels into BEFORE on its own (P(SIMULTANEOUS true | SIMULTANEOUS seen)
    is 16% for the classifier); alpha = 1 keeps a label unless the triangles argue against it."""
    print(); print(title)
    results = {}
    for mode, lam in GRID:
        for alpha in ALPHAS:
            fin = {d["id"]: repair(d, tune_obs[d["id"]], C, lam, mode, alpha) for d in TUNE}
            c, P, R, F, m, _ = evaluate(TUNE, lambda d: tune_obs[d["id"]], lambda d: fin[d["id"]])
            results[(mode, lam, alpha)] = (c["bad0"] - c["bad1"], m)
            log("  chinh %s lam=%.3f alpha=%.1f: rong %+d macro %.2f%%" % (mode, lam, alpha, c["bad0"] - c["bad1"], 100*m))
    for obj, idx in (("giam loi", 0), ("macro-F1", 1)):
        mode, lam, alpha = max(results, key=lambda k: results[k][idx])
        fin = {d["id"]: repair(d, test_obs[d["id"]], C, lam, mode, alpha) for d in VA}
        show("tam giac, chon theo %s (%s, lam %.2f, a %.1f)" % (obj, mode, lam, alpha), VA, lambda d: test_obs[d["id"]], lambda d: fin[d["id"]])

def corrupt(docs, rho, seed):
    rng = random.Random(seed); out = {}
    for d in docs:
        o = []
        for (a, b, r, k) in d["edges"]:
            if rng.random() < rho:
                labs = [x for x in LABS if x != r and MARG[k][x] > 0]
                o.append(rng.choices(labs, [MARG[k][x] for x in labs])[0])
            else: o.append(r)
        out[d["id"]] = o
    return out

print()
print("=" * 130)
print("BAI 2 -- SUA CHUNG THEO DOCUMENT TREN TAM GIAC (valid mo mot lan)")
print("=" * 130)
for rho in (0.10, 0.20):
    run_scenario("nhieu bom %.0f%% ca bon loai canh (kenh nhieu biet truoc)" % (100*rho),
                 corrupt(TUNE, rho, 51), corrupt(VA, rho, 37), chan_injected(rho))
cls = lambda d: [PL.get("%s|%s|%s" % (d["id"], e[0], e[1]), "BEFORE") for e in d["edges"]]
run_scenario("nhieu classifier tang (kenh = ma tran nham lan tren conf2)",
             {d["id"]: cls(d) for d in TUNE}, {d["id"]: cls(d) for d in VA}, chan_confusion(TUNE, cls))
log("xong")
