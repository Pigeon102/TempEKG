# -*- coding: utf-8 -*-
"""Bai 2 on the NEW Bai 1 classifier (257 + LEX rules, macro-F1 26.15%) vs the old one (257
rules, 25.60%). Context B (everything predicted), cross-fitted on valid exactly as in
bayes_audit.py. Besides detection P/R/F1 and net reduction, report the macro-F1 of the graph
AFTER the audit: one number that joins Bai 1 and Bai 2."""
import io, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_BA = io.open(HERE/"bayes_audit.py", encoding="utf-8").read()
exec(SRC_BA[:SRC_BA.index("MARG = ")])
SRC_BB = io.open(HERE/"bayes_b.py", encoding="utf-8").read()
exec(SRC_BB[SRC_BB.index("def ho_cond"):SRC_BB.index("exec(SRC_BA[SRC_BA.index(")])
MARG = (-1.0, 0.0, 1.0, 2.0, 3.0)
NEWP = json.load(io.open(ART/"pred_lex_d05.json", encoding="utf-8"))

def macro6(docs, labels):
    tp, fp, fn = Counter(), Counter(), Counter()
    for d, L in zip(docs, labels):
        for e, p in zip(d["ee"], L):
            g = e[2]
            if p == g: tp[g] += 1
            else: fp[p] += 1; fn[g] += 1
    F = {}
    for r in RELS:
        P = tp[r]/(tp[r]+fp[r]) if tp[r]+fp[r] else 0; Rr = tp[r]/(tp[r]+fn[r]) if tp[r]+fn[r] else 0
        F[r] = 2*P*Rr/(P+Rr) if P+Rr else 0
    return sum(F.values())/6, F

def run_layers(docs, S_, layers, start):
    state = [list(x) for x in start]; c = Counter()
    for nm, fn in layers:
        for d, cur, S in zip(docs, state, S_):
            touched = d.setdefault("_t", set())
            for i, prop in fn(d, cur, S):
                if i in touched: continue
                touched.add(i); c["flag"] += 1
                g = d["ee"][i][2]
                if g != cur[i]: c["hit"] += 1; c["fix"] += (prop == g)
                elif prop and prop != cur[i]: c["brk"] += 1
                if prop: cur[i] = prop
    for d in docs: d.pop("_t", None)
    c["nbad"] = sum(1 for d, st in zip(docs, start) for e, p in zip(d["ee"], st) if e[2] != p)
    c["left"] = sum(1 for d, cur in zip(docs, state) for e, p in zip(d["ee"], cur) if e[2] != p)
    c["npair"] = sum(len(d["ee"]) for d in docs)
    return c, state

def crossfit(name, startV, NEWR, REL_):
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
        return run_layers([VA[j] for j in idx], [vN[j] for j in idx], layers, [startV[j] for j in idx])
    tail = lambda: [("o", ho_old(OLD)), ("c", closure_layer), ("d", date_layer)]
    tot = defaultdict(Counter); final = defaultdict(dict)
    for k in (0, 1):
        trn = [j for j in range(len(VA)) if fold[j] != k]; tst = [j for j in range(len(VA)) if fold[j] == k]
        tA = [j for j in trn if sub[j] == 0]; tB = [j for j in trn if sub[j] == 1]
        RA = mine_c(tA); best = None
        for m in (0.0, 0.05, 0.10, 0.20, 0.30):
            c, _ = sub_run(tB, [("b1", ho_cond(RA, m))])
            if best is None or c["nbad"]-c["left"] > best[0]: best = (c["nbad"]-c["left"], m)
        R1 = mine_c(trn); M1 = best[1]
        cm = Counter()
        for j in trn:
            for e, p in zip(VA[j]["ee"], startV[j]): cm[(p, e[2])] += 1
        LC = chan_counts(cm); best = None
        for m in MARG:
            c, _ = sub_run(trn, [("b", bayes(LC, m))])
            if best is None or c["nbad"]-c["left"] > best[0]: best = (c["nbad"]-c["left"], m)
        MB = best[1]
        confs = {
            "khong kiem toan": [],
            "E4: OLD -> closure -> date": tail(),
            "NEW m.05 -> OLD -> closure -> date": [("n", ho_r(NEWR, REL_, 0.05))] + tail(),
            "B1 cross-fit": [("b1", ho_cond(R1, M1))],
            "Bayes -> OLD -> closure -> date": [("b", bayes(LC, MB))] + tail(),
        }
        for nm, layers in confs.items():
            c, st = sub_run(tst, layers)
            tot[nm].update(c)
            for j, s in zip(tst, st): final[nm][j] = s
    print()
    print("%s  (tong hai fold test)" % name)
    for nm, c in tot.items():
        P = c["hit"]/max(1, c["flag"]); Rr = c["hit"]/max(1, c["nbad"]); F = 2*P*Rr/(P+Rr) if P+Rr else 0
        m, Fr = macro6(VA, [final[nm][j] for j in range(len(VA))])
        print("  %-36s P %6.2f%%  R %6.2f%%  F1 %6.2f%%  R_all %6.2f%%  rong %+5d  loi %5.2f%% -> %5.2f%%  | macro-F1 do thi %6.2f%%  (CONT %.1f SIMU %.1f OVER %.1f)"
              % (nm, 100*P, 100*Rr, 100*F, 100*c["fix"]/max(1, c["nbad"]), c["nbad"]-c["left"],
                 100*c["nbad"]/c["npair"], 100*c["left"]/c["npair"], 100*m,
                 100*Fr["CONTAINS"], 100*Fr["SIMULTANEOUS"], 100*Fr["OVERLAP"]), flush=True)

print()
print("=" * 120)
print("BAI 2 TREN CLASSIFIER CU vs MOI -- boi canh B, cross-fit tren valid")
print("=" * 120)
crossfit("CU: 257 luat (25,60%)", [list(d["pp"]) for d in VA], NEWc, REL)
for d in TR + VA:
    d["pp_new"] = [NEWP.get("%s|%s|%s" % (d["id"], e[0], e[1]), p) for e, p in zip(d["ee"], d["pp"])]
cp = Counter(); co = Counter()
for d in CONF:
    for e, p in zip(d["ee"], d["pp_new"]): cp[p] += 1; co[p] += (p == e[2])
REL2 = {r: co[r]/cp[r] if cp[r] else 0.0 for r in RELS}
log("do tin cay classifier moi tren conf: %s" % {r: "%.1f%%" % (100*v) for r, v in REL2.items() if cp[r]})
NEW2 = mine_new_r(set(FAMS), REL2)
crossfit("MOI: 257 + 719 luat trigger (26,15%)", [list(d["pp_new"]) for d in VA], NEW2, REL2)
log("xong")
