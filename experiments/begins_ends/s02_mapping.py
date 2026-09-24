# -*- coding: utf-8 -*-
"""Step 1b: which endpoint reading of BEGINS-ON / ENDS-ON fits the gold triangles?

Every label is an endpoint predicate on (head a, tail b), a=(as,ae). Triangle satisfiability is
decided by brute force over all weak orders of the 6 endpoints (6^6 integer assignments), so the
check is exact, handles ties, and can optionally allow POINT intervals (s == e), which the MAVEN
timeline allows (Figure 1c places punctual events as single points).

Fixed readings for the other labels (project B1): BEFORE ae<bs; CONTAINS as<=bs & be<=ae;
OVERLAP as<bs<ae<be; SIMULTANEOUS as=bs & ae=be.

Outputs logs/s02_mapping.log:
  (1) inconsistent gold triangles (train and valid) that contain >= 1 rare edge, per candidate
  (2) discrimination test: for every edge of label L, is there a witness x whose two gold edges force
      a gap (i.e. make 'meets' impossible) / force same start / same end? Compare ENDS-ON to BEFORE.
  (3) atom table: most frequent (L(a,x), L(x,c)) around rare edges, per edge type
"""
import io
from itertools import product
from collections import Counter, defaultdict
from common import *

BASE = {
    "BEFORE": lambda a, b: a[1] < b[0],
    "CONTAINS": lambda a, b: a[0] <= b[0] and b[1] <= a[1],
    "OVERLAP": lambda a, b: a[0] < b[0] < a[1] < b[1],
    "SIMULTANEOUS": lambda a, b: a[0] == b[0] and a[1] == b[1],
}
BO = {
    "BO=same-start {s,si,e}": lambda a, b: a[0] == b[0],
    "BO=RED formal a.s=b.e {mi}": lambda a, b: a[0] == b[1],
    "BO=same-start, not equal {s,si}": lambda a, b: a[0] == b[0] and a[1] != b[1],
    "BO=any (unconstrained)": lambda a, b: True,
}
EO = {
    "EO={b,m} a.e<=b.s (project)": lambda a, b: a[1] <= b[0],
    "EO={m} a.e=b.s (RED formal)": lambda a, b: a[1] == b[0],
    "EO=same-end {f,fi,e}": lambda a, b: a[1] == b[1],
    "EO=same-end, head starts first {fi}": lambda a, b: a[1] == b[1] and a[0] < b[0],
    "EO=a ends inside b, a starts first": lambda a, b: a[0] < b[0] <= a[1] <= b[1],
    "EO=any (unconstrained)": lambda a, b: True,
}
LABS = RELS


def sat_table(preds, allow_points):
    """Set of satisfiable (lab_ab, lab_bc, lab_ac) where each lab = (rel, d); d=0 stored (u,v), d=1 stored (v,u)."""
    ok = set()
    rng = range(6)
    for v in product(rng, repeat=6):
        A = (v[0], v[1]); B = (v[2], v[3]); C = (v[4], v[5])
        if allow_points:
            if A[0] > A[1] or B[0] > B[1] or C[0] > C[1]: continue
        else:
            if A[0] >= A[1] or B[0] >= B[1] or C[0] >= C[1]: continue
        def holds(x, y):
            s = []
            for r in LABS:
                f = preds[r]
                if f(x, y): s.append((r, 0))
                if f(y, x): s.append((r, 1))
            return s
        for t in product(holds(A, B), holds(B, C), holds(A, C)):
            ok.add(t)
    return ok


# ---------------------------------------------------------------- load gold graphs (train + valid)
DOCS = []
for split in ("train", "valid"):
    for rec in iter_kg(split):
        nd = rec["nodes"]; L = {}; K = {}
        for e in rec["target_edges"]:
            na, nb = nd.get(e["s"]), nd.get(e["t"])
            if not na or not nb: continue
            L[(e["s"], e["t"])] = e["rel"]
            K[e["s"]] = na["kind"][0].upper(); K[e["t"]] = nb["kind"][0].upper()
        if any(r in RARE for r in L.values()):
            DOCS.append((rec["doc_id"], split, L, K))
print("documents with a rare edge:", len(DOCS))


def lab(L, u, v):
    if (u, v) in L: return (L[(u, v)], 0)
    if (v, u) in L: return (L[(v, u)], 1)
    return None


# triangles containing >= 1 rare edge, each once
TRI = []   # (doc, split, (a,b,c), (lab_ab, lab_bc, lab_ac))
for doc, split, L, K in DOCS:
    nbr = defaultdict(set)
    for (u, v) in L: nbr[u].add(v); nbr[v].add(u)
    seen = set()
    for (u, v), r in L.items():
        if r not in RARE: continue
        for x in nbr[u] & nbr[v]:
            tri = tuple(sorted((u, v, x)))
            if tri in seen: continue
            seen.add(tri)
            a, b, c = tri
            TRI.append((doc, split, tri, (lab(L, a, b), lab(L, b, c), lab(L, a, c))))
print("triangles with >= 1 rare edge:", len(TRI))

LOG = io.open(OUT / "logs" / "s02_mapping.log", "w", encoding="utf-8")
def P(*a):
    s = " ".join(str(x) for x in a); print(s); LOG.write(s + "\n"); LOG.flush()

P("Triangles (3 nodes pairwise labelled in gold) containing >= 1 BEGINS-ON/ENDS-ON edge: %d in %d documents"
  % (len(TRI), len({t[0] for t in TRI})))
P("Per triangle: satisfiable under the endpoint readings? (exact, brute force over endpoint orders)\n")
res = {}
for pts in (False, True):
    P("=== intervals %s ===" % ("may be POINTS (s <= e)" if pts else "non-degenerate (s < e), as in constraint_net.py"))
    P("%-36s %-40s %10s %8s %10s %8s" % ("BEGINS-ON reading", "ENDS-ON reading", "bad train", "docs", "bad valid", "docs"))
    for bn, bf in BO.items():
        for en, ef in EO.items():
            preds = dict(BASE); preds["BEGINS-ON"] = bf; preds["ENDS-ON"] = ef
            ok = sat_table(preds, pts)
            bad = Counter(); bdocs = defaultdict(set); byrare = Counter()
            for doc, split, tri, labs in TRI:
                if labs not in ok:
                    bad[split] += 1; bdocs[split].add(doc)
                    for l in labs:
                        if l[0] in RARE: byrare[l[0]] += 1
            res[(pts, bn, en)] = (bad, bdocs, byrare)
            P("%-36s %-40s %10d %8d %10d %8d   (rare edges in bad: BO %d, EO %d)" % (
                bn, en, bad["train"], len(bdocs["train"]), bad["valid"], len(bdocs["valid"]),
                byrare["BEGINS-ON"], byrare["ENDS-ON"]))
    P("")

# ---------------------------------------------------------------- (2) discrimination test
# For every edge (a,c) with label L in documents with a rare edge (plus a BEFORE baseline sampled from
# the same documents), look at every witness x and ask what the two other gold edges force about (a,c).
P("\n(2) What do the witnesses force on the edge itself?  For an edge (a,c), a witness x forces")
P("    GAP      : a.e < c.s strictly   (makes 'meets' impossible)   e.g. BEFORE(a,x)+BEFORE(x,c)")
P("    NOGAP    : a.e >= c.s           (makes 'before with a gap' impossible)")
P("    SAMEEND  / NOTSAMEEND / SAMESTART / NOTSAMESTART likewise.")
P("    Each witness is evaluated with only its two edges (the edge itself is left unlabelled);")
P("    readings of the other labels: BASE above, BEGINS-ON=same-start, ENDS-ON=unconstrained (to avoid circularity).")
P("    Points allowed (s <= e).\n")

preds = dict(BASE); preds["BEGINS-ON"] = BO["BO=same-start {s,si,e}"]; preds["ENDS-ON"] = EO["EO=any (unconstrained)"]
# for each (lab_ax, lab_xc) atom, compute the set of feasible (a,c) endpoint facts
facts = {"GAP": lambda a, c: a[1] < c[0], "MEET": lambda a, c: a[1] == c[0],
         "SAMEEND": lambda a, c: a[1] == c[1], "SAMESTART": lambda a, c: a[0] == c[0],
         "OVERLAPPING": lambda a, c: a[1] > c[0] and c[1] > a[0]}
feas = defaultdict(set)
for v in product(range(6), repeat=6):
    A = (v[0], v[1]); X = (v[2], v[3]); C = (v[4], v[5])
    if A[0] > A[1] or X[0] > X[1] or C[0] > C[1]: continue
    hax = [(r, d) for r in LABS for d in (0, 1) if (preds[r](A, X) if d == 0 else preds[r](X, A))]
    hxc = [(r, d) for r in LABS for d in (0, 1) if (preds[r](X, C) if d == 0 else preds[r](C, X))]
    fs = tuple(sorted(k for k, f in facts.items() if f(A, C)))
    for p1 in hax:
        for p2 in hxc:
            feas[(p1, p2)].add(fs)


def forced(atom):
    """facts true in every feasible configuration / false in every one."""
    fs = feas.get(atom)
    if not fs: return None
    allt = set(facts); anyt = set()
    for f in fs:
        allt &= set(f); anyt |= set(f)
    return allt, set(facts) - anyt


stat = defaultdict(Counter)
atoms = defaultdict(Counter)
for doc, split, L, K in DOCS:
    nbr = defaultdict(set)
    for (u, v) in L: nbr[u].add(v); nbr[v].add(u)
    for (a, c), r in L.items():
        et = K[a] + K[c]
        key = (r, et)
        stat[key]["n"] += 1
        f_true = set(); f_false = set(); nw = 0; incons = False
        for x in nbr[a] & nbr[c]:
            at = (lab(L, a, x), lab(L, x, c))
            nw += 1
            if r in RARE:
                atoms[key][(K[x], at[0][0] + ("" if at[0][1] == 0 else "^-1"), at[1][0] + ("" if at[1][1] == 0 else "^-1"))] += 1
            fr = forced(at)
            if fr is None: incons = True; continue
            f_true |= fr[0]; f_false |= fr[1]
        if nw: stat[key]["has_witness"] += 1
        if incons: stat[key]["witness_pair_itself_inconsistent"] += 1
        for k in facts:
            if k in f_true: stat[key]["forced_" + k] += 1
            if k in f_false: stat[key]["forbidden_" + k] += 1

P("%-24s %6s %8s | %-9s %-9s %-9s %-9s %-9s %-9s %-9s" % ("label, edge type", "n", "witness", "GAP forc", "MEET forb", "MEET forc", "SAMEEND fb", "SAMEST fb", "SAMEST fc", "OVL forc"))
for key in sorted(stat, key=lambda k: (RELS.index(k[0]), k[1])):
    s = stat[key]; n = s["n"]
    if n < 10 and key[0] not in RARE: continue
    pc = lambda x: "%5.1f%%" % (100 * x / n)
    P("%-24s %6d %8s | %-9s %-9s %-9s %-9s %-9s %-9s %-9s" % (
        "%s %s" % key, n, pc(s["has_witness"]), pc(s["forced_GAP"]), pc(s["forbidden_MEET"]), pc(s["forced_MEET"]),
        pc(s["forbidden_SAMEEND"]), pc(s["forbidden_SAMESTART"]), pc(s["forced_SAMESTART"]), pc(s["forced_OVERLAPPING"])))
P("  (BEFORE etc. rows are restricted to the %d documents that contain a rare edge)" % len(DOCS))

P("\n(3) Most frequent witness atoms (kind x, L(a,x), L(x,c)) around rare edges; ^-1 = stored reversed")
for key in sorted(atoms):
    tot = sum(atoms[key].values())
    P("\n  %s %s  (%d witness atoms)" % (key[0], key[1], tot))
    for at, c in atoms[key].most_common(12):
        P("     %5d  %5.1f%%  %s" % (c, 100 * c / tot, at))
