# -*- coding: utf-8 -*-
"""Probe: is there room for SUBGRAPH-level (triangle) reasoning beyond per-edge decisions?

Every decision so far is made per edge (with neighbourhood features). Here the unit is the
TRIANGLE: three nodes (events or TIMEX) with all three edges present, its configuration =
node kinds + the three oriented labels. Configuration frequencies are learnt from GOLD train
graphs (all train documents except the first 400 -- no valid label is read).

On valid, for a graph under audit (the layered classifier's output, and injected noise 10%):
  1. how many wrong edges sit in at least one triangle whose configuration is rare or never seen
     in gold (coverage), and how many edges in such triangles are wrong (precision)
  2. triangle-vote repair: for each rare triangle, the single-edge change that turns it into the
     most frequent gold configuration votes for that edge; an edge is relabelled when it has at
     least `v` votes and they agree. Net errors fixed, and macro-F1, compared with no change.
"""
import io, json, random
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
HERE = Path(__file__).resolve().parent
SRC = io.open(HERE/"bai1_all_edges.py", encoding="utf-8").read()
exec(SRC[:SRC.index("# ---------------------------------------------------------------- miner")])
exec(SRC[SRC.index("def prf(pred, gold):"):SRC.index("def show(nm, pred, gold):")])
PL = json.load(io.open(ART/"pred_layered.json", encoding="utf-8"))
first400 = set()
for i, line in enumerate(io.open(GRAPH/"train.jsonl", encoding="utf-8")):
    if i >= 400: break
    first400.add(json.loads(line)["doc_id"])
TRg = [d for d in TR if d["id"] not in first400]
SYMM = {"SIMULTANEOUS", "BEGINS-ON"}
def inv_(l): return l if l in SYMM else ("i" + l)

def kinds(d):
    return {n: ("E" if v.get("kind") == "event" else "T") for n, v in d["nd"].items() if v.get("kind") in ("event", "timex")}

def triangles(d, lab):
    """Yield (a, b, c) with a<b<c by id, and the oriented labels L(a,b), L(b,c), L(a,c)."""
    L = {}; nbr = defaultdict(set)
    for (a, b, r, k), q in zip(d["edges"], lab):
        L[(a, b)] = q; L[(b, a)] = inv_(q); nbr[a].add(b); nbr[b].add(a)
    for a in nbr:
        for b in nbr[a]:
            if b <= a: continue
            for c in nbr[a] & nbr[b]:
                if c <= b: continue
                yield (a, b, c), (L[(a, b)], L[(b, c)], L[(a, c)])

def cfg(K, t, labs): return (K[t[0]], K[t[1]], K[t[2]]) + labs

# ---------------------------------------------------------------- gold configuration statistics
FREQ = Counter()
for d in TRg:
    K = kinds(d)
    for t, labs in triangles(d, [e[2] for e in d["edges"]]): FREQ[cfg(K, t, labs)] += 1
TOT = defaultdict(int)
for c, n in FREQ.items(): TOT[c[:3]] += n
print("cau hinh tam giac gold: %d loai, %d tam giac" % (len(FREQ), sum(FREQ.values())))
def p(c): return FREQ.get(c, 0) / max(1, TOT[c[:3]])

LABS6 = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
def run(name, lab_of):
    """lab_of(d) -> list of current labels for d['edges']."""
    print()
    print(name)
    for thr in (0.0, 0.001, 0.01):
        wrong_in = set(); edges_in = set(); nbad = 0; votes = defaultdict(Counter)
        for d in VA:
            K = kinds(d); lab = lab_of(d); idx = {(e[0], e[1]): i for i, e in enumerate(d["edges"])}
            for i, (e, q) in enumerate(zip(d["edges"], lab)): nbad += (q != e[2])
            for t, labs in triangles(d, lab):
                c = cfg(K, t, labs)
                if p(c) > thr: continue
                a, b, cc = t
                pairs = ((a, b), (b, cc), (a, cc))
                ids = []
                for (u, v) in pairs:
                    j = idx.get((u, v)); ids.append((j, False) if j is not None else (idx.get((v, u)), True))
                for j, _ in ids:
                    edges_in.add((d["id"], j))
                    if lab[j] != d["edges"][j][2]: wrong_in.add((d["id"], j))
                # best single-edge change toward the most frequent gold configuration
                best = None
                for pos_, (j, rev) in enumerate(ids):
                    for r in LABS6:
                        rr = inv_(r) if rev else r
                        nl = list(labs); nl[pos_] = rr
                        sc = p(cfg(K, t, tuple(nl)))
                        if sc > p(c) and (best is None or sc > best[0]): best = (sc, j, r)
                if best: votes[(d["id"], best[1])][best[2]] += 1
        prec = sum(1 for x in edges_in if x in wrong_in) / max(1, len(edges_in))
        print("  nguong p<=%.3f: canh trong tam giac bat thuong %d, trong do sai %.1f%%; phu %.1f%% so canh sai"
              % (thr, len(edges_in), 100*prec, 100*len(wrong_in)/max(1, nbad)))
        for v in (1, 2, 3):
            fix = brk = 0; newlab = {}
            for key, cnt in votes.items():
                r, n = cnt.most_common(1)[0]
                if n >= v and n > sum(cnt.values()) - n: newlab[key] = r
            pred = []; gold = []
            for d in VA:
                lab = lab_of(d)
                for j, (e, q) in enumerate(zip(d["edges"], lab)):
                    r = newlab.get((d["id"], j), q)
                    if r != q:
                        if q != e[2] and r == e[2]: fix += 1
                        elif q == e[2]: brk += 1
                    pred.append(r); gold.append(e[2])
            m = prf(pred, gold)[0]
            print("     bo phieu >=%d: sua %6d  hong %6d  rong %+6d  macro-F1 %.2f%%" % (v, fix, brk, fix - brk, 100*m))
    base = prf([q for d in VA for q in lab_of(d)], [e[2] for d in VA for e in d["edges"]])[0]
    print("  (khong sua: loi %d canh, macro-F1 %.2f%%)" % (sum(1 for d in VA for e, q in zip(d["edges"], lab_of(d)) if q != e[2]), 100*base))

run("DO THI CLASSIFIER TANG (30,83%)",
    lambda d: [PL.get("%s|%s|%s" % (d["id"], e[0], e[1]), "BEFORE") for e in d["edges"]])
prior_k = defaultdict(Counter)
for d in TRg:
    for e in d["edges"]: prior_k[e[3]][e[2]] += 1
NZ = {}
rng = random.Random(37)
for d in VA:
    out = []
    for e in d["edges"]:
        g = e[2]
        if rng.random() < 0.10:
            labs = [r for r in prior_k[e[3]] if r != g]; out.append(rng.choices(labs, [prior_k[e[3]][r] for r in labs])[0])
        else: out.append(g)
    NZ[d["id"]] = out
run("NHIEU BOM 10% CA BON LOAI", lambda d: NZ[d["id"]])
