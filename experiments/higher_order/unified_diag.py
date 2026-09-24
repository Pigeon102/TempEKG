# -*- coding: utf-8 -*-
"""Check the realistic +0.00 of unified_graph.py before believing it.

1. Stage-1 quality on the mining set (conf2), the tuning set (conf1) and valid: if the
   classifiers are in-sample on conf1/conf2, the rules learn the wrong error distribution.
2. The realistic statistic at every margin on conf1 AND on valid (valid is only printed, not
   used to choose anything), so a mis-chosen margin would show.
3. Cross-fit on valid itself (2 folds by document hash, rules mined on one half, applied to the
   other, margin chosen inside the training half): every classifier is out-of-sample there."""
import io, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = io.open(HERE/"unified_graph.py", encoding="utf-8").read()
exec(SRC[:SRC.index('print("=" * 118)')])

print()
print("1. CHAT LUONG GIAI DOAN 1 THEO TAP")
for nm, docs in (("conf2 (mine)", C2), ("conf1 (chon)", C1), ("valid", VA)):
    labs = [[x[4] for x in d["E"]] for d in docs]
    m, per, acc, n = prf(docs, labs)
    cells = []
    for kinds, lab in ((("EE",), "EE"), (("ET",), "ET"), (("TE",), "TE"), (("TT",), "TT")):
        mk, _, ak, nk = prf(docs, labs, kinds); cells.append("%s acc %.1f%% F %.1f%%" % (lab, 100*ak, 100*mk))
    print("  %-14s acc %.2f%% macro %.2f%%   %s" % (nm, 100*acc, 100*m, "  ".join(cells)))

R = mine(C2, False)
print()
print("2. MOI MARGIN (thuc te, 1 vong): conf1 va valid (valid chi in ra)")
m1b, _, _, _ = prf(C1, [[x[4] for x in d["E"]] for d in C1]); mvb, _, _, _ = prf(VA, [[x[4] for x in d["E"]] for d in VA])
for m in (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.7):
    m1, _, _, _ = prf(C1, run(R, C1, m, 1, False)); mv, _, _, _ = prf(VA, run(R, VA, m, 1, False))
    print("  margin %.2f   conf1 %+.2f   valid %+.2f" % (m, 100*(m1-m1b), 100*(mv-mvb)), flush=True)

print()
print("3. CROSS-FIT TREN VALID (luat hoc tu nua valid kia, margin chon trong nua hoc)")
fold = [h("cf" + d["id"]) % 2 for d in VA]; sub = [h("in" + d["id"]) % 2 for d in VA]
final = [None]*len(VA)
for k in (0, 1):
    trn = [j for j in range(len(VA)) if fold[j] != k]; tst = [j for j in range(len(VA)) if fold[j] == k]
    tA = [VA[j] for j in trn if sub[j] == 0]; tB = [VA[j] for j in trn if sub[j] == 1]
    RA = mine(tA, False); best = None
    for m in (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 9.0):
        mc, _, _, _ = prf(tB, run(RA, tB, m, 1, False))
        if best is None or mc > best[0]: best = (mc, m)
    Rk = mine([VA[j] for j in trn], False)
    labs = run(Rk, [VA[j] for j in tst], best[1], 1, False)
    for j, L in zip(tst, labs): final[j] = L
    print("  fold %d: margin %.2f" % (k, best[1]))
report("cross-fit, do thi hop nhat", VA, final)
print("      (giai doan 1: macro-F1 %.2f%%)" % (100*mvb))
log("xong")
