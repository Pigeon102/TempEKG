# -*- coding: utf-8 -*-
"""Every Bai 2 auditor lowers the error rate but also LOWERS the graph's macro-F1
(new classifier: 26.15% -> 21.5-23.6%). The auditors are tuned to net error reduction, and the
cheapest way to remove errors is to turn rare labels into BEFORE: SIMULTANEOUS predictions are
84% wrong, so erasing all of them removes errors while taking SIMULTANEOUS F1 to zero.

Test a macro-F1-aware auditor on the same cross-fit:
  B1-norm  the same (signature, current label) rules, but compare labels by wlb / prior -- the
           prior normalisation that lifted rare labels in Bai 1 -- and flip only when the best
           alternative beats the current label by a factor (1 + margin)
  selection of the margin by MACRO-F1 on the training fold (inner split), not by net errors
Both classifiers, both objectives, reported with error rate and graph macro-F1."""
import io
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_NC = io.open(HERE/"bai2_newclf.py", encoding="utf-8").read()
exec(SRC_NC[:SRC_NC.index('print("BAI 2 TREN')])

def ho_norm(R, margin):
    def f(d, cur, S):
        out = []
        for i, s in enumerate(S):
            p = cur[i]; keep = 0.0; best = None
            for x in set(s):
                t = R.get((x, p))
                if not t: continue
                keep = max(keep, t[p]/PRIOR[p])
                for r, w in t.items():
                    v = w/PRIOR[r]
                    if r != p and (best is None or v > best[1]): best = (r, v)
            if best and best[1] > keep*(1 + margin): out.append((i, best[0]))
        return out
    return f

def run_macro(name, startV):
    vN = [sigs_L(d, lab_ctx(d, st, "B")) for d, st in zip(VA, startV)]
    set_pins(VA, "B")
    fold = [int(hashlib.md5(("cf" + d["id"]).encode()).hexdigest(), 16) % 2 for d in VA]
    sub = [int(hashlib.md5(("in" + d["id"]).encode()).hexdigest(), 16) % 2 for d in VA]
    def mine_c(idx):
        cnt = defaultdict(Counter); dd = defaultdict(lambda: defaultdict(set))
        for j in idx:
            d = VA[j]
            for (a, b, g, f, cs), s, p in zip(d["ee"], vN[j], startV[j]):
                for x in set(s): cnt[(x, p)][g] += 1; dd[(x, p)][g].add(d["id"])
        R = {}
        for key, c in cnt.items():
            n = sum(c.values())
            if n < 20: continue
            p = key[1]; t = {p: wlb(c[p], n)}
            alts = {r: wlb(k, n) for r, k in c.items() if r != p and k >= 5 and len(dd[key][r]) >= 3}
            if alts: t.update(alts); R[key] = t
        return R
    def sub_run(idx, layers):
        c, st = run_layers([VA[j] for j in idx], [vN[j] for j in idx], layers, [startV[j] for j in idx])
        m, _ = macro6([VA[j] for j in idx], st)
        return c, st, m
    variants = {
        "B1 (chon theo giam loi)":      (ho_cond, (0.0, 0.05, 0.10, 0.20, 0.30), "net"),
        "B1 (chon theo macro-F1)":      (ho_cond, (0.0, 0.05, 0.10, 0.20, 0.30, 0.5, 1.0, 9.9), "macro"),
        "B1-norm (chon theo macro-F1)": (ho_norm, (0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 99.0), "macro"),
    }
    tot = defaultdict(Counter); final = defaultdict(dict); chosen = defaultdict(list)
    for k in (0, 1):
        trn = [j for j in range(len(VA)) if fold[j] != k]; tst = [j for j in range(len(VA)) if fold[j] == k]
        tA = [j for j in trn if sub[j] == 0]; tB = [j for j in trn if sub[j] == 1]
        RA = mine_c(tA); R1 = mine_c(trn)
        for nm, (mk, grid, obj) in variants.items():
            best = None
            for m in grid:
                c, _, mac = sub_run(tB, [("x", mk(RA, m))])
                val = (c["nbad"]-c["left"]) if obj == "net" else mac
                if best is None or val > best[0]: best = (val, m)
            chosen[nm].append(best[1])
            c, st, _ = sub_run(tst, [("x", mk(R1, best[1]))])
            tot[nm].update(c)
            for j, s in zip(tst, st): final[nm][j] = s
    print()
    print(name)
    m0, F0 = macro6(VA, startV)
    print("  %-30s loi %5.2f%%  macro-F1 %6.2f%%  (CONT %.1f SIMU %.1f OVER %.1f)"
          % ("khong kiem toan", 100*sum(1 for d, st in zip(VA, startV) for e, p in zip(d["ee"], st) if e[2] != p)/109929,
             100*m0, 100*F0["CONTAINS"], 100*F0["SIMULTANEOUS"], 100*F0["OVERLAP"]))
    for nm, c in tot.items():
        m, Fr = macro6(VA, [final[nm][j] for j in range(len(VA))])
        print("  %-30s margin %-12s co %5d  sua %5d  hong %5d  loi %5.2f%% -> %5.2f%%  macro-F1 %6.2f%% (%+.2f)  (CONT %.1f SIMU %.1f OVER %.1f)"
              % (nm, chosen[nm], c["flag"], c["fix"], c["brk"], 100*c["nbad"]/c["npair"], 100*c["left"]/c["npair"],
                 100*m, 100*(m-m0), 100*Fr["CONTAINS"], 100*Fr["SIMULTANEOUS"], 100*Fr["OVERLAP"]), flush=True)

print()
print("=" * 120)
print("BAI 2 -- MUC TIEU GIAM LOI hay MACRO-F1 (boi canh B, cross-fit)")
print("=" * 120)
run_macro("CU: 257 luat", [list(d["pp"]) for d in VA])
for d in VA:
    d["pp_new"] = [NEWP.get("%s|%s|%s" % (d["id"], e[0], e[1]), p) for e, p in zip(d["ee"], d["pp"])]
run_macro("MOI: 257 + 719 luat trigger", [list(d["pp_new"]) for d in VA])
log("xong")
