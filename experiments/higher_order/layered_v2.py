# -*- coding: utf-8 -*-
"""Layered graph v2 -- the layered miner of layered_rules.py, restructured with the ideas of
tempekg_exp/ecskg/FORMAL.md (Event-Centric PaTeCon):

  derived_from (FORMAL 11.7)   every layer attribute declares its source; the miner refuses any
                               attribute derived from target (temporal) edges
  anchor sets + hull (8.4, 11.3) each event gets the set of dated TIMEX of its own sentence and
                               the previous one (text only, no event-timex edge is read), its size,
                               its spread, and the HULL of their calendar values. The two events'
                               hulls are compared with a THREE-VALUED predicate (4.1): a_before /
                               b_before / a_contains / b_contains / overlap / equal / unk; unk
                               never counts as evidence either way
  durative class (8.4)         event types whose events carry several spread-out anchors in text
                               (learned on DISCOVERY from text anchors, not labels) are durative
  refinement in the view lattice (3.1)
                               instead of enumerating every 2/3-pattern cross-layer combination,
                               a pattern whose confirmation bound is still below a decisive level
                               is refined by conjoining a pattern of ANOTHER layer, kept only if
                               the discovery Wilson bound rises by >= 0.05 (up to 3 layers)
  BH-FDR (10.3)                every refined rule gets a one-sided binomial p-value against the
                               label prior on CONFIRMATION-1; Benjamini-Hochberg at q = 0.05
  is_enriched (11.8)           results are reported separately on enriched pairs (shared entity,
                               or >= 3 roles on a side, or text anchors on both sides) and the rest

Protocol as layered_rules.py: first 400 train documents excluded, DISCOVERY / CONFIRMATION-1 /
CONFIRMATION-2, valid opened once. EV-EV edges (the other types keep their stage-1 labels here:
the new attributes are about pairs of events).
"""
import io, os, math
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_L = io.open(HERE/"layered_rules.py", encoding="utf-8").read()
exec(SRC_L[:SRC_L.index('log("dung dieu kien theo tang ...")')])
from mine_compositional import log_binom_tail
exec(SRC_L[SRC_L.index("# ---------------------------------------------------------------- stage A: per-layer patterns"):SRC_L.index("FINAL = {}")])
SMOKE = os.environ.get("SMOKE") == "1"
if SMOKE:
    TR = TR[:300]; VA = VA[:80]

# ---------------------------------------------------------------- derived_from declarations
DERIVED_FROM = {
    "ONT": "node attributes (type)", "ARG": "input edges (roles, entities)",
    "DISC": "token positions and text", "LEX": "trigger text; container lexicon from DISCOVERY gold",
    "TIME": "TIMEX node text and positions", "HULL": "TIMEX node text and positions (anchor sets)",
}
for ly, origin in DERIVED_FROM.items():
    assert "target" not in origin and "temporal edge" not in origin, ly

# ---------------------------------------------------------------- anchor sets from text
def dval(t):
    dt = parse_date(t)
    if not dt: return None
    y, m, d = dt
    lo = (y, m or 1, d or 1); hi = (y, m or 12, d or 31)
    return lo, hi
def anchor_set(d, e):
    nd = d["nd"]; se = pos(nd[e])[0]; out = []
    for t in d["txs"]:
        T = nd[t]
        if T.get("timex_type") not in ("DATE", "TIME"): continue
        st = pos(T)[0]
        if st in (se, se - 1):
            v = dval(T.get("text"))
            if v: out.append(v)
    return out
def hull(vs):
    if not vs: return None
    return min(v[0] for v in vs), max(v[1] for v in vs)
def comp3(ha, hb):
    """Three-valued interval comparison on hulls: unk when either side has no anchor."""
    if ha is None or hb is None: return "unk"
    if ha[1] < hb[0]: return "a_before"
    if hb[1] < ha[0]: return "b_before"
    if ha == hb: return "equal"
    if ha[0] <= hb[0] and hb[1] <= ha[1]: return "a_contains"
    if hb[0] <= ha[0] and ha[1] <= hb[1]: return "b_contains"
    return "overlap"

# durative event types: learned on DISCOVERY from TEXT anchors only (spread across >= 2 years)
spread = Counter(); seen = Counter()
for d in TR:
    if d["sp"] != "disc": continue
    for e in d["evs"]:
        A = anchor_set(d, e); ty = d["nd"][e].get("type")
        if A:
            seen[ty] += 1
            if len({v[0][0] for v in A}) >= 2 or len(A) >= 3: spread[ty] += 1
DURATIVE = {ty for ty, n in seen.items() if n >= 20 and spread[ty]/n >= 0.25}
log("loai su kien keo dai (hoc tu anchor van ban tren disc): %d loai, vd %s" % (len(DURATIVE), sorted(DURATIVE)[:8]))

_old_EE = layered_EE
def layered_EE(d, a, b):
    L = _old_EE(d, a, b)
    nd = d["nd"]; Aa, Ab = anchor_set(d, a), anchor_set(d, b)
    ha, hb = hull(Aa), hull(Ab)
    H = []
    for side, A_, e in (("a", Aa, a), ("b", Ab, b)):
        H.append(("n_anchor_" + side, "0" if not A_ else ("1" if len(A_) == 1 else "2+")))
        if A_ and len({v[0][0] for v in A_}) >= 2: H.append(("spread_" + side, True))
        H.append(("durative_" + side, nd[e].get("type") in DURATIVE))
    c = comp3(ha, hb)
    H.append(("hull_cmp", c))
    L["HULL"] = H
    return L

log("dung dieu kien theo tang (v2) ...")
ITR = [x for x in build(TR) if x["k"] == "EE"]; IVA = [x for x in build(VA) if x["k"] == "EE"]
LAYERS = ("ONT", "ARG", "DISC", "LEX", "TIME", "HULL")
log("instance EV-EV: train %d, valid %d" % (len(ITR), len(IVA)))

def enriched(x):
    L = x["L"]
    shared = any(c[1] == "shares_anchor" and c[2] is True for c in L.get("ARG", ()))
    roles3 = any(c[1] in ("nrole_a", "nrole_b") and isinstance(c[2], int) and c[2] >= 3 for c in L.get("ARG", ()))
    anch = ("n_anchor_a", "0") not in L.get("HULL", ()) and ("n_anchor_b", "0") not in L.get("HULL", ())
    return shared or roles3 or anch

# ---------------------------------------------------------------- stage A (per layer), reused
disc = [x for x in ITR if x["sp"] == "disc"]; c1 = [x for x in ITR if x["sp"] == "conf1"]; c2 = [x for x in ITR if x["sp"] == "conf2"]
pr = Counter(x["g"] for x in disc); maj = pr.most_common(1)[0][0]; prior = {r: pr[r]/len(disc) for r in RELS if pr[r]}
PAT = {}; per_layer = {}
for ly in LAYERS:
    res = mine_keys(disc, c1, layer_keyfun(ly), prior, maj)
    kept = 0
    for r, lst in res.items():
        for cw, key in lst[:150]:
            PAT[(ly,) + key] = (ly, key, r, cw); kept += 1
    per_layer[ly] = kept
log("pattern theo tang: %s" % per_layer)

def fires(x, pid):
    ly, key = PAT[pid][0], PAT[pid][1]
    atoms = x["L"].get(ly, frozenset())
    return all(c in atoms for c in key)
def posting(insts, pid):
    return {j for j, x in enumerate(insts) if fires(x, pid)}
log("posting cho pattern ...")
PD = {pid: posting(disc, pid) for pid in PAT}
PC1 = {pid: posting(c1, pid) for pid in PAT}

# ---------------------------------------------------------------- stage B': refinement in the lattice
HI = {r: min(0.9, max(0.5, 8*prior[r])) for r in prior}       # decisive precision per label
def refine():
    rules = []                                                    # (tuple of pids, label, disc wlb)
    for r in prior:
        if r == maj: continue
        seeds = sorted((pid for pid in PAT if PAT[pid][2] == r), key=lambda p: -PAT[p][3])[:200]
        pool = defaultdict(list)                                  # other-layer partners, top 50 per layer for r
        for pid in sorted(PAT, key=lambda p: -PAT[p][3]):
            if PAT[pid][2] == r and len(pool[PAT[pid][0]]) < 50: pool[PAT[pid][0]].append(pid)
        frontier = []
        for s in seeds:
            S = PD[s]; k = sum(1 for j in S if disc[j]["g"] == r)
            frontier.append(((s,), S, wlb(k, len(S))))
        for depth in (2, 3):
            nxt = []
            for key, S, w in frontier:
                if w >= HI[r]: continue                           # already decisive: PaTeCon stops refining
                used = {PAT[p][0] for p in key}
                for ly, lst in pool.items():
                    if ly in used: continue
                    for q in lst:
                        S2 = S & PD[q]
                        if len(S2) < 30: continue
                        k2 = sum(1 for j in S2 if disc[j]["g"] == r)
                        if k2 < 10 or len({disc[j]["doc"] for j in S2 if disc[j]["g"] == r}) < 5: continue
                        w2 = wlb(k2, len(S2))
                        if w2 >= w + 0.05: nxt.append((tuple(sorted(key + (q,))), S2, w2))
            best = {}
            for key, S2, w2 in nxt:
                if key not in best or w2 > best[key][1]: best[key] = (S2, w2)
            frontier = sorted(((k_, v[0], v[1]) for k_, v in best.items()), key=lambda t: -t[2])[:300]
            rules += [(k_, r, w_) for k_, S_, w_ in frontier]
    return rules
log("refinement ...")
REF = refine()
log("refinement: %d luat (%s)" % (len(REF), dict(Counter(r for _, r, _ in REF))))

# ---------------------------------------------------------------- BH-FDR on CONFIRMATION-1
tests = []
for key, r, w in REF:
    S = set(PC1[key[0]])
    for q in key[1:]: S &= PC1[q]
    n = len(S)
    if n < 10: continue
    k = sum(1 for j in S if c1[j]["g"] == r)
    lp = log_binom_tail(k, n, prior[r])
    tests.append((lp, key, r, wlb(k, n)))
tests.sort(key=lambda t: t[0])
m = len(tests); keep = []
for i, (lp, key, r, cw) in enumerate(tests, 1):
    if lp <= math.log(0.05*i/m): keep = tests[:i]
BH = [(key, r, cw) for lp, key, r, cw in keep if cw/prior[r] >= 1.5]
log("BH-FDR q=0.05: %d / %d luat giu lai" % (len(BH), m))

# ---------------------------------------------------------------- stage C and report
for x in ITR + IVA:
    x["act"] = frozenset(pid for pid in PAT if fires(x, pid))
def idx_of(rl):
    byf = defaultdict(list)
    for key, r, cw in rl: byf[key[0]].append((key, r, cw))
    return byf
pat_rules = [((pid,), PAT[pid][2], PAT[pid][3]) for pid in PAT]
labels = sorted(r for r in prior if r != maj)
va = IVA; gv = [x["g"] for x in va]; s1 = [x["p"] for x in va]
EN = [enriched(x) for x in va]
def sub(pred, flag):
    idx = [i for i, f in enumerate(EN) if f == flag]
    return prf([pred[i] for i in idx], [gv[i] for i in idx])[0], len(idx)
print()
print("=" * 110)
print("BAI 1 v2 -- DO THI THEO TANG + Y TUONG FORMAL.md (EV-EV, valid mo mot lan)")
print("=" * 110)
m0, per0, a0 = prf(s1, gv)
e1, ne = sub(s1, True); e0, nn = sub(s1, False)
print("  giai doan 1                         macro %6.2f%%  acc %6.2f%%   | giau thong tin (%d cap) %6.2f%%  | ngheo (%d cap) %6.2f%%" % (100*m0, 100*a0, ne, 100*e1, nn, 100*e0))
for nm, rl in (("+ pattern tung tang (co HULL)", pat_rules), ("+ pattern + refinement + BH-FDR", pat_rules + BH)):
    ix = idx_of(rl)
    TH = tune_floors(labels, ix, [x["act"] for x in c2], [x["p"] for x in c2], [x["g"] for x in c2])
    pv = classify_override(ix, TH, [x["act"] for x in va], s1)
    mm, per, acc = prf(pv, gv); e1, _ = sub(pv, True); e0, _ = sub(pv, False)
    ch = sum(1 for a, b in zip(pv, s1) if a != b); ok = sum(1 for a, b, g in zip(pv, s1, gv) if a != b and a == g)
    print("  %-35s macro %6.2f%% (%+.2f)  acc %6.2f%%   | giau %6.2f%%  | ngheo %6.2f%%   doi %d dung %.1f%%"
          % (nm, 100*mm, 100*(mm-m0), 100*acc, 100*e1, 100*e0, ch, 100*ok/max(1, ch)))
    print("      " + "  ".join("%s %.1f" % (r[:4], 100*per[r][2]) for r in RELS if per[r][3]))
print()
print("  HULL: phan bo hull_cmp tren valid va ty le nhan:")
dist = defaultdict(Counter)
for x in va:
    for c in x["L"].get("HULL", ()):
        if c[0] == "hull_cmp": dist[c[1]][x["g"]] += 1
for v, cnt in sorted(dist.items(), key=lambda t: -sum(t[1].values())):
    n = sum(cnt.values())
    print("    %-11s n=%6d  BEFORE %.1f%%  CONTAINS %.1f%%  SIMU %.1f%%  OVER %.1f%%" % (v, n, 100*cnt["BEFORE"]/n, 100*cnt["CONTAINS"]/n, 100*cnt["SIMULTANEOUS"]/n, 100*cnt["OVERLAP"]/n))
for key, r, cw in sorted(BH, key=lambda t: -t[2]/prior[t[1]])[:6]:
    print("    %-12s cwlb %.3f  %s" % (r, cw, " & ".join("%s:%s" % (p[0], p[1:]) for p in key)[:140]))
log("xong")
