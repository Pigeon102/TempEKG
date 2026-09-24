# -*- coding: utf-8 -*-
"""Bai 2 #1: upgrade the higher-order auditor with what the motif study found.

The auditor in production (E4, R_all 29.29%) uses 21 triangle rules, EV-EV only, each
kept for its MAJORITY label under wlb >= 0.50 -- the gate the motif study just showed
drops every rare-label rule. And it never uses TIMEX paths, which carry +3 to +5 points
of oracle signal each.

In Bai 2 that oracle signal is reachable, because the graph under audit already exists:
its other edges are observed, not predicted by the auditor. Setting, as in Task 5/E4:
the classifier's EV-EV edges are the noisy layer (13,331 wrong on 705 valid docs).

  context A  EV-TX and TX-TX edges as stored in the KG (gold); EV-EV as predicted
  context B  everything predicted (EV-TX classifier, TX-TX calendar) -- harder

Auditors compared on the same graph:
  OLD  21-rule majority-label triangle auditor, reproduced here
  NEW  per-label rules over all six families, mined on gold train (disc), confirmed on
       conf. BEFORE is kept -- repairing a wrong CONTAINS needs a BEFORE rule. A rule is
       kept only if its confirmation Wilson bound beats the classifier's own precision for
       that label: overriding an edge needs more evidence than the edge already has.
       Decision: flag (a,b) when some label r != current p has a firing rule whose cwlb
       exceeds both the classifier's reliability for p and the best rule agreeing with p.
Each auditor is also stacked with closure and date bridge in the E4 order.
"""
import sys, io, re
from pathlib import Path
src = io.open(str(Path(__file__).resolve().parent / "motifs2.py"), encoding="utf-8").read()
exec(src[:src.index("# ---------------------------------------------------------------- gold (oracle)")])
from noise_aware import score_document

AUD = ("BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP")

# classifier reliability per label, on confirmation docs
cp = Counter(); co = Counter()
for d in CONF:
    for (a, b, g, f, cs), p in zip(d["ee"], d["pp"]):
        cp[p] += 1; co[p] += (p == g)
REL = {r: co[r]/cp[r] if cp[r] else 0.0 for r in RELS}
log("do tin cay classifier tren confirmation: %s" % {r: "%.1f%%" % (100*v) for r, v in REL.items() if cp[r]})

def labmap_A(d):
    L = {}
    for (a, b, r) in d["edges"]: L[(a, b)] = r; L[(b, a)] = inv(r)      # gold everywhere...
    for (a, b, g, f, cs), p in zip(d["ee"], d["pp"]):                     # ...then EV-EV as predicted
        L[(a, b)] = p; L[(b, a)] = inv(p)
    return L

def sigs_L(d, L):
    out = []
    for (a, b, g, f, cs), inst in zip(d["ee"], d["inst"]):
        s = []
        for fam, nodes in inst:
            if len(nodes) == 1:
                x = nodes[0]; s.append(fam + "|" + L[(a, x)] + "|" + L[(x, b)])
            else:
                x, y = nodes; s.append(fam + "|" + L[(a, x)] + "|" + L[(x, y)] + "|" + L[(y, b)])
        out.append(s)
    return out

log("chu ky gold tren train ...")
dG = [sigs(d, "gold") for d in DISC]; cG = [sigs(d, "gold") for d in CONF]

# ---------------------------------------------------------------- OLD auditor (E4 reproduction)
def mine_old():
    cnt = defaultdict(Counter); dd = defaultdict(lambda: defaultdict(set))
    for d, S in zip(DISC, dG):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for x in s:
                if x.startswith("3E|"): cnt[x][g] += 1; dd[x][g].add(d["id"])
    cand = {}
    for x, c in cnt.items():
        n = sum(c.values()); top, k = c.most_common(1)[0]
        if n >= 30 and k >= 10 and len(dd[x][top]) >= 5 and wlb(k, n) >= 0.50: cand[x] = top
    cc = defaultdict(Counter)
    for d, S in zip(CONF, cG):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for x in s:
                if x in cand: cc[x][g] += 1
    keep = {x: (t, wlb(cc[x][t], sum(cc[x].values()))) for x, t in cand.items() if sum(cc[x].values()) >= 10}
    rk = sorted(keep.items(), key=lambda kv: -kv[1][1])
    return dict(rk[:max(1, int(0.7*len(rk)))])

# ---------------------------------------------------------------- NEW auditor
def mine_new(fams):
    cnt = defaultdict(Counter); dd = defaultdict(lambda: defaultdict(set))
    for d, S in zip(DISC, dG):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for x in s:
                if x.split("|", 1)[0] in fams: cnt[x][g] += 1; dd[x][g].add(d["id"])
    cand = []
    for x, c in cnt.items():
        n = sum(c.values())
        if n < 30: continue
        for r in AUD:
            k = c[r]
            if k >= 10 and len(dd[x][r]) >= 5 and wlb(k, n) > REL[r]: cand.append((x, r))
    need = {x for x, _ in cand}
    cc = defaultdict(Counter)
    for d, S in zip(CONF, cG):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for x in s:
                if x in need: cc[x][g] += 1
    R = defaultdict(dict)                      # sig -> {label: cwlb}
    for x, r in cand:
        cn = sum(cc[x].values())
        if cn < 10: continue
        cw = wlb(cc[x][r], cn)
        if cw > REL[r]: R[x][r] = cw
    return R

def ho_old(R):
    def f(d, cur, S):
        out = []
        for i, s in enumerate(S):
            agg = Counter()
            for x in s:
                t = R.get(x)
                if t: agg[t[0]] += t[1]
            if agg:
                best = agg.most_common(1)[0][0]
                if best != cur[i]: out.append((i, best))
        return out
    return f

def ho_new(R):
    def f(d, cur, S):
        out = []
        for i, s in enumerate(S):
            best = defaultdict(float)
            for x in s:
                for r, cw in R.get(x, {}).items():
                    if cw > best[r]: best[r] = cw
            if not best: continue
            p = cur[i]
            alt = max((r for r in best if r != p), key=lambda r: best[r], default=None)
            if alt and best[alt] > max(REL.get(p, 0.0), best.get(p, 0.0)): out.append((i, alt))
        return out
    return f

def closure_layer(d, cur, S):
    edges = [(a, b, cur[i]) for i, (a, b, g, f, cs) in enumerate(d["ee"])]
    pos = {(a, b): i for i, (a, b, g, f, cs) in enumerate(d["ee"])}
    out = []
    for susp, a, b, carried, prop in score_document(edges):
        if susp > 0 and prop != carried and (a, b) in pos: out.append((pos[(a, b)], prop))
    return out

def pins(d):
    pin = defaultdict(set)
    for (e, t, dr, r) in d["tx"]:
        dt = parse_date(d["nd"][t].get("text"))
        if not dt or not dt[1] or not dt[2] or not d["nd"][t].get("anchorable"): continue
        if (dr == "T" and r in ("CONTAINS", "SIMULTANEOUS")) or (dr == "E" and r == "SIMULTANEOUS"):
            pin[e].add(dt)
    return pin
def date_layer(d, cur, S):
    pin = d["pin"]; out = []
    for i, (a, b, g, f, cs) in enumerate(d["ee"]):
        A, B = pin.get(a), pin.get(b)
        if not A or not B or len(A) > 1 or len(B) > 1: continue
        da, db = next(iter(A)), next(iter(B))
        if da < db and cur[i] != "BEFORE": out.append((i, "BEFORE"))
        elif da > db and cur[i] == "BEFORE": out.append((i, None))
    return out
for d in VA: d["pin"] = pins(d)

def audit(layers, vS):
    """Layers run in order; each sees the graph as repaired by the ones before."""
    nbad = sum(1 for d in VA for (a, b, g, f, cs), p in zip(d["ee"], d["pp"]) if g != p)
    flag = hit = fix = 0; per = []
    state = [list(d["pp"]) for d in VA]
    for nm, fn in layers:
        nf = nh = nx = 0
        for d, cur, S in zip(VA, state, vS):
            touched = d.setdefault("_t", set())
            for i, prop in fn(d, cur, S):
                if i in touched: continue
                touched.add(i); nf += 1
                g = d["ee"][i][2]
                if g != cur[i]:
                    nh += 1; nx += (prop == g)
                if prop: cur[i] = prop
        flag += nf; hit += nh; fix += nx; per.append((nm, nf, nh, nx))
    for d in VA: d.pop("_t", None)
    left = sum(1 for d, cur in zip(VA, state) for (a, b, g, f, cs), p in zip(d["ee"], cur) if g != p)
    return per, flag, hit, fix, nbad, left

def show(name, res):
    per, flag, hit, fix, nbad, left = res
    print("  %s" % name)
    for nm, nf, nh, nx in per:
        print("      %-14s gan co %6s  dung %6s  sua dung %6s" % (nm, format(nf, ","), format(nh, ","), format(nx, ",")))
    print("      P@k %6.2f%%  found_all %6.2f%%  repair@k %6.2f%%  R_all %6.2f%%   canh sai %.2f%% -> %.2f%%"
          % (100*hit/max(1, flag), 100*hit/nbad, 100*fix/max(1, hit), 100*fix/nbad,
             100*nbad/109929, 100*left/109929))


# Why is 3T at P@k 100% in context A? Check how deterministic gold 3T signatures are.
NEW3 = mine_new({"3T"})
print("3T rules:", sum(len(v) for v in NEW3.values()))
for x, rr in sorted(NEW3.items(), key=lambda kv: -max(kv[1].values()))[:20]:
    print("  %-40s %s" % (x, {r: round(c, 3) for r, c in rr.items()}))
# purity of gold 3T signatures on valid (gold everywhere)
cnt = defaultdict(Counter)
for d in VA:
    S = sigs(d, "gold")
    for (a, b, g, f, cs), s in zip(d["ee"], S):
        for x in set(s):
            if x.startswith("3T|"): cnt[x][g] += 1
tot = sum(sum(c.values()) for c in cnt.values())
pure = sum(sum(c.values()) for c in cnt.values() if c.most_common(1)[0][1] / sum(c.values()) >= 0.99)
print("gold 3T instances on valid: %d, in signatures >=99%% pure: %.1f%%" % (tot, 100*pure/tot))
# flags in context A: current label -> proposed label, with gold
vA = [sigs_L(d, labmap_A(d)) for d in VA]
fl = Counter()
f = ho_new(NEW3)
for d, S in zip(VA, vA):
    for i, prop in f(d, list(d["pp"]), S):
        fl[(d["pp"][i], prop, d["ee"][i][2])] += 1
for k, v in fl.most_common(12): print("  pred %-12s -> %-12s gold %-12s %d" % (k + (v,)))
