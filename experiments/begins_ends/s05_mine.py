# -*- coding: utf-8 -*-
"""Step 2c: mine conjunctive rules (1-3 atoms, scoped by edge type) for BEGINS-ON / ENDS-ON.

Protocol (project leakage discipline):
  DISCOVERY (split 0)   candidate conjunctions = subsets of positives' atoms; count n, k, documents
  CONFIRMATION-1 (1)    re-score every surviving rule: ck/cn, Wilson lower bound cwlb
  CONFIRMATION-2 (2)    choose one floor per (edge type, label) on pooled 6-label macro-F1
  VALID                 opened once per gate setting, at the end
A rule fires on an edge when all its atoms are present; if the best firing cwlb clears the floor of
its (edge type, label), the rule's label replaces the current classifier label (pred_layered_full.json).

Gate settings (fixed before looking at any result of this script):
  strict : DISC n>=25, k>=5, docs>=5, k/n >= min(1.5*prior,(1+prior)/2), wlb>prior ; CONF-1 cn>=10, cwlb>prior
  relaxed: DISC n>=10, k>=3, docs>=3, same ratio/wlb gates                         ; CONF-1 cn>=5,  cwlb>prior
Usage: python s05_mine.py strict|relaxed
"""
import sys, gzip, io, time
from itertools import combinations
from collections import Counter, defaultdict
from common import *

MODE = sys.argv[1] if len(sys.argv) > 1 else "relaxed"
G = {"strict": dict(n=25, k=5, d=5, cn=10), "relaxed": dict(n=10, k=3, d=3, cn=5)}[MODE]
KMIN = 3
MAXLEN = 3
T0 = time.time()
LOG = io.open(OUT / "logs" / ("s05_mine_%s.log" % MODE), "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); LOG.write(s + "\n"); LOG.flush()
def tlog(*a): P("[%5.0fs]" % (time.time() - T0), *a)

def rows():
    with gzip.open(OUT / "features.tsv.gz", "rt", encoding="utf-8") as f:
        for l in f:
            sp, doc, s, t, et, g, at = l.rstrip("\n").split("\t")
            yield int(sp), doc, s, t, et, g, at

# ---------------------------------------------------------------- pass 1: DISC positives, row counts
posrows = defaultdict(list)       # et -> [(label, atoms frozenset, doc)]
nrows = Counter()                 # (split, et) -> rows
disc_lab = defaultdict(Counter)
for sp, doc, s, t, et, g, at in rows():
    nrows[(sp, et)] += 1
    if sp == 0:
        disc_lab[et][g] += 1
        if g in RARE:
            posrows[et].append((g, frozenset(at.split("|")), doc))
PRIOR = {et: {r: c[r] / sum(c.values()) for r in RARE} for et, c in disc_lab.items()}
tlog("pass 1 done; DISC positives:", {et: len(v) for et, v in posrows.items()})

U = {}
CAND = {}                          # et -> {(conj, label): (k, docs)}
for et, pr in posrows.items():
    ac = Counter(a for g, A, d in pr for a in A)
    U[et] = {a for a, c in ac.items() if c >= KMIN}
    cc = defaultdict(lambda: [0, set()])
    for g, A, d in pr:
        AU = sorted(A & U[et])
        for L in range(1, MAXLEN + 1):
            for conj in combinations(AU, L):
                x = cc[(conj, g)]; x[0] += 1; x[1].add(d)
    CAND[et] = {k: (v[0], len(v[1])) for k, v in cc.items() if v[0] >= G["k"] and v[1] and len(v[1]) >= G["d"]}
    tlog("  %s: universe %d atoms, %d candidate (conj,label) with k>=%d, docs>=%d" % (et, len(U[et]), len(CAND[et]), G["k"], G["d"]))

# ---------------------------------------------------------------- pass 2: bitsets per split
idx = Counter()
bits = {}                           # (sp, et, atom) -> bytearray
labbits = {}                        # (sp, et, label) -> bytearray
keep = {2: [], 3: []}               # rows of CONF-2 and VALID: (et, gold, doc, s, t, row index in (sp,et))
def ba(sp, et):
    return bytearray((nrows[(sp, et)] + 7) // 8)
for sp, doc, s, t, et, g, at in rows():
    i = idx[(sp, et)]; idx[(sp, et)] += 1
    if et in U:
        for a in set(at.split("|")) & U[et]:
            key = (sp, et, a)
            if key not in bits: bits[key] = ba(sp, et)
            bits[key][i >> 3] |= 1 << (i & 7)
        if g in RARE:
            key = (sp, et, g)
            if key not in labbits: labbits[key] = ba(sp, et)
            labbits[key][i >> 3] |= 1 << (i & 7)
    if sp in (2, 3):
        keep[sp].append((et, g, doc, s, t, i))
BITS = {k: int.from_bytes(v, "little") for k, v in bits.items()}; del bits
LBITS = {k: int.from_bytes(v, "little") for k, v in labbits.items()}; del labbits
tlog("pass 2 done; %d atom bitsets" % len(BITS))

def conj_bits(sp, et, conj):
    full = (1 << nrows[(sp, et)]) - 1
    b = full
    for a in conj:
        b &= BITS.get((sp, et, a), 0)
        if not b: break
    return b

# ---------------------------------------------------------------- DISC scoring + CONF-1 confirmation
RULES = []   # (et, label, conj, k, n, docs, ck, cn, cwlb)
stats = Counter()
for et in CAND:
    for (conj, g), (k, d) in CAND[et].items():
        n = conj_bits(0, et, conj).bit_count()
        pr = PRIOR[et][g]
        stats["cand"] += 1
        if n < G["n"]: continue
        stats["n_ok"] += 1
        if not (k / n >= min(1.5 * pr, (1 + pr) / 2) and wlb(k, n) > pr): continue
        stats["disc_ok"] += 1
        cb = conj_bits(1, et, conj)
        cn = cb.bit_count(); ck = (cb & LBITS.get((1, et, g), 0)).bit_count()
        if cn < G["cn"]: continue
        stats["cn_ok"] += 1
        cw = wlb(ck, cn)
        if cw <= pr: continue
        stats["confirmed"] += 1
        RULES.append((et, g, conj, k, n, d, ck, cn, cw))
tlog("gate funnel:", dict(stats))
P("rules confirmed per (edge type, label):", dict(Counter((r[0], r[1]) for r in RULES)))

# ---------------------------------------------------------------- firing on CONF-2 and VALID
def firing(sp):
    best = defaultdict(dict)          # (et, row) -> {label: cwlb}
    for et, g, conj, k, n, d, ck, cn, cw in RULES:
        b = conj_bits(sp, et, conj)
        while b:
            low = b & -b; i = low.bit_length() - 1; b ^= low
            m = best[(et, i)]
            if cw > m.get(g, 0): m[g] = cw
    return best

need_docs = {x[2] for sp in (2, 3) for x in keep[sp]}
PRED = load_preds(need_docs)
tlog("predictions loaded for %d edges" % len(PRED))

def table(sp):
    f = firing(sp)
    out = []
    for et, g, doc, s, t, i in keep[sp]:
        out.append((et, g, PRED[(doc, s, t)], f.get((et, i), {})))
    return out
F2 = table(2); FV = table(3)

def decide(rows_, TH):
    out = []
    for et, g, p, m in rows_:
        best = None
        for r, cw in m.items():
            if cw >= TH.get((et, r), 9) and (best is None or cw > best[1]): best = (r, cw)
        out.append(best[0] if best else p)
    return out

def macro_of(rows_, TH):
    return macro(decide(rows_, TH), [x[1] for x in rows_])

keys = sorted({(et, r) for et, g, p, m in F2 for r in m})
TH = {k: 9 for k in keys}
best = macro_of(F2, TH)[0]
base2 = best
for _ in range(3):
    for k in keys:
        grid = sorted({m[k[1]] for et, g, p, m in F2 if et == k[0] and k[1] in m}) + [9]
        for th in grid:
            T2 = dict(TH); T2[k] = th
            v = macro_of(F2, T2)[0]
            if v > best + 1e-12: best, TH = v, T2
P("\nCONF-2: classifier macro-F1 %.2f%% -> with rules %.2f%%" % (100 * base2, 100 * best))
P("floors chosen on CONF-2 (9 = switched off):", {"%s/%s" % k: (round(v, 4) if v != 9 else 9) for k, v in TH.items()})

# ---------------------------------------------------------------- VALID, opened once
gv = [x[1] for x in FV]
base = macro([x[2] for x in FV], gv)
pv = decide(FV, TH)
new = macro(pv, gv)
P("\n=== VALID (%d edges), gates=%s ===" % (len(FV), MODE))
P("pooled 6-label macro-F1: classifier %.2f%%  ->  with rules %.2f%%  (%+.2f)" % (100 * base[0], 100 * new[0], 100 * (new[0] - base[0])))
for r in RARE:
    P("  %-9s classifier P/R/F1 %.3f/%.3f/%.3f   with rules %.3f/%.3f/%.3f" % ((r,) + base[1][r] + new[1][r]))
broken = sum(1 for (et, g, p, m), q in zip(FV, pv) if p == g and q != g)
fixed = sum(1 for (et, g, p, m), q in zip(FV, pv) if p != g and q == g)
changed = sum(1 for (et, g, p, m), q in zip(FV, pv) if p != q)
P("  edges relabelled %d: fixed %d, broke %d previously-correct labels" % (changed, fixed, broken))
P("  per edge type (BEGINS-ON / ENDS-ON, with rules):")
for et in ETYPES:
    sub = [(x, q) for x, q in zip(FV, pv) if x[0] == et]
    for r in RARE:
        tp = sum(1 for x, q in sub if q == r and x[1] == r); fp = sum(1 for x, q in sub if q == r and x[1] != r)
        fn = sum(1 for x, q in sub if q != r and x[1] == r)
        if tp + fp + fn: P("    %s %-9s tp %3d fp %4d fn %3d  P/R/F1 %.3f/%.3f/%.3f" % ((et, r, tp, fp, fn) + prf(tp, fp, fn)))

# ---------------------------------------------------------------- best rules, with valid k/n (descriptive)
P("\nBest confirmed rules per (edge type, label), by CONF-1 Wilson bound (top 8); valid k/n shown after the fact")
for et in ETYPES:
    for r in RARE:
        rs = sorted([x for x in RULES if x[0] == et and x[1] == r], key=lambda x: -x[8])[:8]
        if not rs: continue
        P("  %s %s (floor %s)" % (et, r, TH.get((et, r), "n/a")))
        for _, g, conj, k, n, d, ck, cn, cw in rs:
            vb = conj_bits(3, et, conj); vn = vb.bit_count(); vk = (vb & LBITS.get((3, et, g), 0)).bit_count()
            P("     %-78s DISC %3d/%-5d (%d docs)  CONF-1 %2d/%-4d cwlb %.3f  VALID %2d/%d" % (" & ".join(conj)[:78], k, n, d, ck, cn, cw, vk, vn))
tlog("done")
