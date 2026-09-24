# -*- coding: utf-8 -*-
"""Bai 2 on the unified graph: audit ALL FOUR edge types with patterns over every event and
TIMEX of the document.

Rules are the unified-graph rules of unified_graph.py, keyed (signature, current label),
mined on CONFIRMATION-2 under the SAME kind of noise the graph under audit carries, margin
chosen on CONFIRMATION-1, valid opened once. Scored by net error reduction (the Bai 2
objective) with detection P/R/F1, and by the graph's macro-F1.

  N1  classifier noise: the whole graph as stage 1 predicted it (4 edge types). Also scored
      with the margin chosen by macro-F1.
  N2  injected noise on ALL four edge types at 5/10/15/20%: each edge relabelled with
      probability rho to a label drawn from its edge type's marginal without the gold label
      (fake_data's generator, extended to TIMEX edges). Train noise and valid noise use
      different seeds.
  N3  the user's fake_data (EV-EV relabelled, TIMEX edges gold), with rules mined under the
      same EV-EV-only noise simulated on CONFIRMATION-2.
"""
import io, json, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = io.open(HERE/"unified_graph.py", encoding="utf-8").read()
exec(SRC[:SRC.index('print("=" * 118)')])
FAKE = Path(r"C:\Reseach_Quang\fake_data")

def mine_on(docs, starts):
    cnt = defaultdict(Counter); dd = defaultdict(lambda: defaultdict(set))
    for d, st in zip(docs, starts):
        for (a, b, g, k, p0), s, p in zip(d["E"], sigs(d, st, False), st):
            for x in s: cnt[(x, p)][g] += 1; dd[(x, p)][g].add(d["id"])
    R = {}
    for key, c in cnt.items():
        n = sum(c.values())
        if n < 20: continue
        p = key[1]; t = {p: wlb(c[p], n)}
        alts = {r: wlb(kk, n) for r, kk in c.items() if r != p and kk >= 5 and len(dd[key][r]) >= 3}
        if alts: t.update(alts); R[key] = t
    return R

def stats_on(R, docs, starts):
    return [statistic(R, d, st, False) for d, st in zip(docs, starts)]

def apply(stat, starts, margin):
    return [[r if (r and v > margin) else q for q, (r, v) in zip(st, S)] for st, S in zip(starts, stat)]

def score(docs, starts, finals):
    c = Counter()
    for d, st, fi in zip(docs, starts, finals):
        for (a, b, g, k, p0), s, f in zip(d["E"], st, fi):
            c["n"] += 1; c["bad0"] += (s != g); c["bad1"] += (f != g)
            if f != s:
                c["flag"] += 1
                if s != g: c["hit"] += 1; c["fix"] += (f == g)
                else: c["brk"] += 1
    P = c["hit"]/max(1, c["flag"]); Rr = c["hit"]/max(1, c["bad0"]); F = 2*P*Rr/(P+Rr) if P+Rr else 0
    m, _, _, _ = prf(docs, finals)
    return c, P, Rr, F, m

def show(nm, docs, starts, finals):
    c, P, Rr, F, m = score(docs, starts, finals)
    m0, _, _, _ = prf(docs, starts)
    print("  %-40s P %6.2f%%  R %6.2f%%  F1 %6.2f%%  sua %6d  hong %5d  rong %+6d  loi %5.2f%% -> %5.2f%%  macro-F1 %6.2f%% -> %6.2f%%"
          % (nm, 100*P, 100*Rr, 100*F, c["fix"], c["brk"], c["bad0"]-c["bad1"], 100*c["bad0"]/c["n"], 100*c["bad1"]/c["n"], 100*m0, 100*m), flush=True)
    return c

MARG = (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7, 9.0)
def choose(R, docs, starts, objective):
    stat = stats_on(R, docs, starts); best = None
    for m in MARG:
        fi = apply(stat, starts, m); c, P, Rr, F, mac = score(docs, starts, fi)
        val = (c["bad0"] - c["bad1"]) if objective == "net" else mac
        if best is None or val > best[0]: best = (val, m)
    return best[1]

print()
print("=" * 130)
print("BAI 2 -- KIEM TOAN CA BON LOAI CANH TREN DO THI HOP NHAT (valid mo mot lan)")
print("=" * 130)

# ---------------------------------------------------------------- N1 classifier noise
pC2 = [[x[4] for x in d["E"]] for d in C2]; pC1 = [[x[4] for x in d["E"]] for d in C1]; pVA = [[x[4] for x in d["E"]] for d in VA]
R1 = mine_on(C2, pC2); statV = stats_on(R1, VA, pVA)
print()
print("N1 -- nhieu classifier (ca do thi do giai doan 1 du doan)")
for obj in ("net", "macro"):
    m = choose(R1, C1, pC1, obj)
    show("chon theo %s, margin %.2f" % ("giam loi" if obj == "net" else "macro-F1", m), VA, pVA, apply(statV, pVA, m))

# ---------------------------------------------------------------- noise generators
prior_k = defaultdict(Counter)
for d in C1 + C2:
    for (a, b, g, k, p) in d["E"]: prior_k[k][g] += 1
def corrupt(docs, rho, seed, kinds):
    rng = random.Random(seed); out = []
    for d in docs:
        st = []
        for (a, b, g, k, p) in d["E"]:
            if k in kinds and rng.random() < rho:
                labs = [r for r in prior_k[k] if r != g]
                st.append(rng.choices(labs, [prior_k[k][r] for r in labs])[0])
            else: st.append(g)
        out.append(st)
    return out

print()
print("N2 -- nhieu bom tren CA BON loai canh (quy trinh fake_data mo rong sang canh TIMEX)")
ALL4 = ("EE", "ET", "TE", "TT")
for rho in (0.05, 0.10, 0.15, 0.20):
    sC2 = corrupt(C2, rho, 11, ALL4); sC1 = corrupt(C1, rho, 12, ALL4); sVA = corrupt(VA, rho, 13, ALL4)
    R = mine_on(C2, sC2); m = choose(R, C1, sC1, "net")
    fin = apply(stats_on(R, VA, sVA), sVA, m)
    show("rho %.0f%%, margin %.2f" % (100*rho, m), VA, sVA, fin)
    cells = []
    for kinds, lab in ((("EE",), "EV-EV"), (("ET",), "EV>TX"), (("TE",), "TX>EV"), (("TT",), "TX-TX")):
        n0 = n1 = n = 0
        for d, s, f in zip(VA, sVA, fin):
            for x, a0, a1 in zip(d["E"], s, f):
                if x[3] in kinds: n += 1; n0 += (a0 != x[2]); n1 += (a1 != x[2])
        cells.append("%s %.2f%%->%.2f%%" % (lab, 100*n0/n, 100*n1/n))
    print("      loi theo loai: " + "   ".join(cells))

# ---------------------------------------------------------------- N3 user's fake_data
print()
print("N3 -- fake_data cua ban (chi EV-EV bi doi, canh TIMEX gold); luat mine duoi cung loai nhieu")
for tag, rho in (("r05", .05), ("r10", .10), ("r15", .15), ("r20", .20)):
    man = json.load(io.open(FAKE/("valid_%s.manifest.json" % tag), encoding="utf-8"))
    ch = {(x["doc"], x["event1"], x["event2"]): x["fake"] for x in man["changed"]}
    fVA = [[ch.get((d["id"], a, b)) or ch.get((d["id"], b, a)) or g for (a, b, g, k, p) in d["E"]] for d in VA]
    sC2 = corrupt(C2, rho, 21, ("EE",)); sC1 = corrupt(C1, rho, 22, ("EE",))
    R = mine_on(C2, sC2); m = choose(R, C1, sC1, "net")
    show("fake %s, margin %.2f" % (tag, m), VA, fVA, apply(stats_on(R, VA, fVA), fVA, m))
log("xong")
