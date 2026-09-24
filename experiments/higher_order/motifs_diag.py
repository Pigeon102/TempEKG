# -*- coding: utf-8 -*-
"""Are the pp motif rules wrong, or is the combiner mis-weighting them?

Two measurements independent of tau:
  * PRECISION WHEN FIRING: when a rule for label r fires on a valid pair, how often is
    gold == r -- against the base rate of r and against the 257-rule classifier's own
    precision for r
  * CHANGE AUDIT: of the predictions the family flips, how many flips are correct
And one that re-tunes the combiner fairly: tau chosen on CONFIRMATION docs, applied to valid.
"""
import sys, io
from pathlib import Path
src = io.open(str(Path(__file__).resolve().parent / "motifs2.py"), encoding="utf-8").read()
exec(src[:src.index("# ---------------------------------------------------------------- gold (oracle)")])

def firing_prec(R, val_sigs):
    hit = Counter(); ok = Counter()
    for d, S in zip(VA, val_sigs):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            labs = {R[x][0] for x in s if x in R}
            for r in labs:
                hit[r] += 1; ok[r] += (g == r)
    return {r: (ok[r], hit[r]) for r in hit}

def combine_eval(R, docs, sigS, tau):
    pred = []; gold = []; ch = cc = 0
    for d, S in zip(docs, sigS):
        for (a, b, g, f, cs), sc0, p0, s in zip(d["ee"], d["ps"], d["pp"], S):
            sc = dict(sc0)
            for x in s:
                t = R.get(x)
                if t:
                    v = t[1]/PRIOR[t[0]]
                    if v > sc.get(t[0], 0): sc[t[0]] = v
            p = max(sc, key=sc.get) if sc and max(sc.values()) >= tau else "BEFORE"
            pred.append(p); gold.append(g)
            if p != p0:
                ch += 1; cc += (p == g)
    m, per, acc = macro(pred, gold)
    return m, ch, cc

# base classifier's precision per label on valid
bp = Counter(); bo = Counter()
for d in VA:
    for (a, b, g, f, cs), p in zip(d["ee"], d["pp"]):
        bp[p] += 1; bo[p] += (p == g)
nva = sum(len(d["ee"]) for d in VA)
base_rate = Counter(r[2] for d in VA for r in d["ee"])

print("=" * 100)
print("Do chinh xac cua 257 luat khi du doan nhan r (valid):")
for r in ("CONTAINS", "SIMULTANEOUS", "OVERLAP"):
    print("  %-13s %6.2f%%  (%s/%s)   base rate %.2f%%" % (r, 100*bo[r]/max(1, bp[r]), format(bo[r], ","), format(bp[r], ","), 100*base_rate[r]/nva))

for mode in ("gold", "pred"):
    dS = [sigs(d, mode) for d in DISC]; cS = [sigs(d, mode) for d in CONF]; vS = [sigs(d, mode) for d in VA]
    print()
    print("=" * 100)
    print("CHE DO %s  (mine va ap cung che do)" % mode.upper())
    print("=" * 100)
    for fam in FAMS + ["ALL"]:
        R = mine(dS, cS, fam)
        if not R:
            print("  %-4s  0 luat" % fam); continue
        fp = firing_prec(R, vS)
        cell = "  ".join("%s %5.1f%% (%d)" % (r[:4], 100*o/h, h) for r, (o, h) in sorted(fp.items()))
        # tau on confirmation, then valid once
        best = None
        for tau in (5, 10, 20, 40, 80, 160):
            mc, _, _ = combine_eval(R, CONF, cS, tau)
            if best is None or mc > best[0]: best = (mc, tau)
        tau = best[1]
        m5, ch5, cc5 = combine_eval(R, VA, vS, 5)
        mt, cht, cct = combine_eval(R, VA, vS, tau)
        print("  %-4s %3d luat | ban dung: %s" % (fam, len(R), cell))
        print("        tau=5  : macro %6.2f%% (%+.2f)  doi %5d, dung %5d (%.1f%%)"
              % (100*m5, 100*(m5-0.2560), ch5, cc5, 100*cc5/max(1, ch5)))
        print("        tau=%-3d: macro %6.2f%% (%+.2f)  doi %5d, dung %5d (%.1f%%)   [tau chon tren confirmation]"
              % (tau, 100*mt, 100*(mt-0.2560), cht, cct, 100*cct/max(1, cht)))
