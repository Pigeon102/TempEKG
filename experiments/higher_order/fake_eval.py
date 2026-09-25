# -*- coding: utf-8 -*-
"""Bai 2 on the user's fake_data files, with the CURRENT method (document-level joint repair over
triangles, step 3.2). fake_data = MAVEN-ERE valid gold with EV-EV labels changed at 5/10/15/20%
(seed 0); C:/Reseach_Quang/fake_data/valid_rXX.manifest.json lists every changed pair.

  graph to audit   valid: EV-EV labels from fake_data, TIMEX edges gold (fake_data leaves them alone)
  statistics       triangle configurations from gold train (DISCOVERY + CONF-1), as in the pipeline
  channel          known generator on EV-EV (1 - r if unchanged, else r * q(p) / (1 - q(l))); TIMEX edges
                   are observed exactly
  tuning           lambda / alpha / weighting chosen on CONFIRMATION-2 of TRAIN with EV-EV labels
                   corrupted the same way (different seed), by net errors and by EV-EV macro-F1;
                   valid (fake_data) scored once per objective
  false alarms     the same parameters run on the CLEAN valid graph: how many correct edges get changed
"""
import io, os, json, math, random, sys
from pathlib import Path
from collections import Counter, defaultdict
HERE = Path(__file__).resolve().parent
SRC_J = io.open(HERE/"joint_repair.py", encoding="utf-8").read()
SRC_J = SRC_J.replace('PL = json.load(io.open(ART/("pred_layered%s.json" % TAG), encoding="utf-8"))', "PL = {}")   # not needed here: saves ~0.5 GB
exec(SRC_J[:SRC_J.index("def evaluate(docs, obs_of, fin_of):")])
import gc
for _d in STATS: _d.pop("tris", None); _d.pop("inc", None)   # counts already in FREQ; frees memory
gc.collect()
FAKE = Path(r"C:\Reseach_Quang\fake_data")
GRID = [("mean", l, a) for l in (0.2, 0.5, 1.0, 2.0) for a in (0.0, 0.5)] + [("sum", l, 0.0) for l in (0.03, 0.1)]
SYMM_ = {"SIMULTANEOUS", "BEGINS-ON"}

def channel(rho):
    C = {}
    for k in Q:
        for l in LABS:
            for p in LABS:
                if k == "EE": C[(k, p, l)] = math.log(1 - rho) if p == l else math.log(max(1e-9, rho * Q[k][p] / (1 - Q[k][l])))
                else: C[(k, p, l)] = 0.0 if p == l else math.log(1e-9)
    return C

def corrupt_ee(docs, rho, seed):
    rng = random.Random(seed); out = {}
    for d in docs:
        o = []
        for (a, b, r, k) in d["edges"]:
            if k == "EE" and rng.random() < rho:
                labs = [x for x in LABS if x != r and MARG[k][x] > 0]
                o.append(rng.choices(labs, [MARG[k][x] for x in labs])[0])
            else: o.append(r)
        out[d["id"]] = o
    return out

def fake_obs(rate_tag):
    man = json.load(io.open(FAKE/("valid_r%s.manifest.json" % rate_tag), encoding="utf-8"))
    F = {}; skipped = 0
    for c in man["changed"]:
        F[(c["doc"], c["event1"], c["event2"])] = c["fake"]
    out = {}; used = 0
    for d in VA:
        o = []
        for (a, b, r, k) in d["edges"]:
            f = F.get((d["id"], a, b))
            if f is None and (d["id"], b, a) in F:                    # stored in the other direction
                g = F[(d["id"], b, a)]
                f = g if g in SYMM_ else None
                if f is None: skipped += 1
            if f is not None and k == "EE": o.append(f); used += 1
            else: o.append(r)
        out[d["id"]] = o
    return out, man["rate"], man["n_changed"], used, skipped

def score(obs, fin, only_ee=True):
    c = Counter(); pred = []; gold = []
    for d in VA:
        for (a, b, r, k), s, f in zip(d["edges"], obs[d["id"]], fin[d["id"]]):
            if only_ee and k != "EE":
                c["other_changed"] += (f != s); continue
            c["n"] += 1; c["b0"] += (s != r); c["b1"] += (f != r)
            if f != s:
                c["flag"] += 1
                if s != r: c["hit"] += 1; c["fix"] += (f == r)
                else: c["brk"] += 1
            pred.append(f); gold.append(r)
    P = c["hit"]/max(1, c["flag"]); R = c["hit"]/max(1, c["b0"]); F1 = 2*P*R/(P + R) if P + R else 0
    return c, P, R, F1, prf(pred, gold)[0]

def ee_macro(docs, obs, fin):
    pred = []; gold = []; c = Counter()
    for d in docs:
        for (a, b, r, k), s, f in zip(d["edges"], obs[d["id"]], fin[d["id"]]):
            if k != "EE": continue
            pred.append(f); gold.append(r); c["b0"] += (s != r); c["b1"] += (f != r)
    return c["b0"] - c["b1"], prf(pred, gold)[0]

print("=" * 116); print("BAI 2 TREN FAKE_DATA -- sua chung theo tam giac (buoc 3.2), valid cham mot lan moi muc tieu"); print("=" * 116)
clean = {d["id"]: [e[2] for e in d["edges"]] for d in VA}
for tag in (sys.argv[1:] or ["05", "10", "15", "20"]):
    obs, rho, nchg, used, skipped = fake_obs(tag)
    C = channel(rho)
    tune_obs = corrupt_ee(TUNE, rho, 51)
    res = {}
    for mode, lam, alpha in GRID:
        fin = {d["id"]: repair(d, tune_obs[d["id"]], C, lam, mode, alpha) for d in TUNE}
        res[(mode, lam, alpha)] = ee_macro(TUNE, tune_obs, fin)
    log("muc %s%%: chinh tren CONF-2 xong (%d canh doi trong fake_data, dung %d, bo %d)" % (tag, nchg, used, skipped))
    for obj, idx in (("giam loi", 0), ("macro-F1", 1)):
        cfg = max(res, key=lambda k: res[k][idx]); mode, lam, alpha = cfg
        fin = {d["id"]: repair(d, obs[d["id"]], C, lam, mode, alpha) for d in VA}
        c, P, R, F1, m = score(obs, fin); m0 = prf([s for d in VA for s, e in zip(obs[d["id"]], d["edges"]) if e[3] == "EE"],
                                                    [e[2] for d in VA for e in d["edges"] if e[3] == "EE"])[0]
        fa = {d["id"]: repair(d, clean[d["id"]], C, lam, mode, alpha) for d in VA}
        cf, *_ = score(clean, fa)
        print("  %s%% | %-8s (%s, %.2f, %.1f) | EV-EV loi %5.2f%% -> %5.2f%% | P %5.1f R %5.1f F1 %5.1f | sua %5d hong %4d rong %+6d | macro EV-EV %5.2f -> %5.2f | canh TIMEX bi doi %d | bao dong gia tren gold sach: %d canh EV-EV (+%d TIMEX)" %
              (tag, obj, mode, lam, alpha, 100*c["b0"]/c["n"], 100*c["b1"]/c["n"], 100*P, 100*R, 100*F1, c["fix"], c["brk"], c["b0"] - c["b1"],
               100*m0, 100*m, c["other_changed"], cf["brk"], cf["other_changed"]))
        # scored on the injected edges only (before repair every one is wrong: accuracy 0, macro-F1 0)
        sp = [(f, e[2]) for d in VA for e, s, f in zip(d["edges"], obs[d["id"]], fin[d["id"]]) if e[3] == "EE" and s != e[2]]
        ms, per, acc = prf([x[0] for x in sp], [x[1] for x in sp])
        pres = [r for r in RELS if per[r][3]]
        print("       chi tren %d canh bi fake: acc 0 -> %5.2f%% | macro-F1 (6 nhan) 0 -> %5.2f | macro tren %d nhan co mat %5.2f | canh sach giu dung %5.2f%%" %
              (len(sp), 100*acc, 100*ms, len(pres), 100*sum(per[r][2] for r in pres)/len(pres), 100*(1 - c["brk"]/(c["n"] - c["b0"]))))
        print("       " + "  ".join("%s P%.1f R%.1f F%.1f (n=%d)" % (r[:4], 100*per[r][0], 100*per[r][1], 100*per[r][2], per[r][3]) for r in RELS))
log("xong")
