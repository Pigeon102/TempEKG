# -*- coding: utf-8 -*-
"""Bai 1 ablations on the confirmed full-train EV-EV rules (no re-mining):
  depth     only 1-condition rules / only 2-condition rules / both (pipeline)
  score     the rule weight used by the combiner: Wilson lower bound on CONF-1 (pipeline),
            raw confidence on CONF-1, raw confidence on DISCOVERY, lift (CONF-1 confidence / class prior)
  combiner  per-label floors (pipeline) vs one global floor for every label
Floors are chosen on CONFIRMATION-2 by coordinate ascent on macro-F1 (grid = fixed steps plus the
weight quantiles of that label, so every score gets a fair grid); valid is opened once per variant.
Log: experiments/rules_full/ablate_score.log"""
import os, sys, pickle, json
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import mine_full as MF

RELS = MF.RELS
def macro(pred, gold):
    tp, fp, fn = Counter(), Counter(), Counter()
    for p, g in zip(pred, gold):
        if p == g: tp[g] += 1
        else: fp[p] += 1; fn[g] += 1
    per = []
    for r in range(len(RELS)):
        P = tp[r]/(tp[r]+fp[r]) if tp[r]+fp[r] else 0; R = tp[r]/(tp[r]+fn[r]) if tp[r]+fn[r] else 0
        per.append(2*P*R/(P+R) if P+R else 0)
    return sum(per)/6, per

def main():
    NW = int(os.environ.get("NW", "4"))
    rules = pickle.load(open(MF.OUT/"rules_confirmed.pkl", "rb"))
    g2 = list(pickle.load(open(MF.OUT/"cache_sp2.pkl", "rb"))["lab"])
    gv = list(pickle.load(open(MF.OUT/"cache_sp3.pkl", "rb"))["lab"])
    fc = MF.OUT/"fired_c2_valid.pkl"
    if fc.exists():
        F2, FV = pickle.load(open(fc, "rb"))
    else:
        F2 = MF.fire_all(2, len(g2), NW); FV = MF.fire_all(3, len(gv), NW)
        pickle.dump((F2, FV), open(fc, "wb"))
    RL = [RELS.index(x["rel"]) for x in rules]
    SC = {
        "Wilson (pipeline)": [x["wlb"] for x in rules],
        "confidence thô trên tập xác nhận": [x["ck"]/x["cn"] if x["cn"] else 0 for x in rules],
        "confidence thô trên tập khám phá": [x["k"]/x["n"] for x in rules],
        "lift (confidence / tỷ lệ nền)": [(x["ck"]/x["cn"] if x["cn"] else 0)/max(1e-9, x["base"]) for x in rules],
    }
    DEPTH = {"cả 1 và 2 điều kiện (pipeline)": lambda x: True,
             "chỉ 1 điều kiện": lambda x: len(x["key"]) == 1,
             "chỉ 2 điều kiện": lambda x: len(x["key"]) == 2}

    def run(W, keep, per_label=True):
        ok = [keep(x) for x in rules]
        NEG = -1.0
        def tops(F):                               # per pair: strongest rule weight of every label
            out = []
            for hits in F:
                m = [NEG] * len(RELS)
                for rid in hits:
                    if ok[rid] and W[rid] > m[RL[rid]]: m[RL[rid]] = W[rid]
                out.append(m)
            return out
        T2_, TV_ = tops(F2), tops(FV)
        def pred(F, TH):
            M = T2_ if F is F2 else TV_
            out = []
            for m in M:
                best, bw = 0, None
                for r in range(1, len(RELS)):
                    if m[r] >= TH[r] and (bw is None or m[r] > bw): best, bw = r, m[r]
                out.append(best)
            return out
        grids = {}
        for r in range(1, len(RELS)):
            ws = sorted(W[i] for i in range(len(rules)) if ok[i] and RL[i] == r)
            qs = [ws[int(q*(len(ws)-1))] for q in (0.5, 0.7, 0.8, 0.9, 0.95, 0.98, 0.99, 0.995)] if ws else []
            steps = [0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8] if max(W) <= 1.0001 else []
            grids[r] = sorted(set(steps + qs)) + [float("inf")]
        if per_label:
            TH = {r: float("inf") for r in range(len(RELS))}; best = macro(pred(F2, TH), g2)[0]
            for _ in range(3):
                for r in range(1, len(RELS)):
                    for t in grids[r]:
                        T2 = dict(TH); T2[r] = t; m = macro(pred(F2, T2), g2)[0]
                        if m > best: best, TH = m, T2
        else:
            allg = sorted(set(t for r in grids for t in grids[r]))
            best, TH = -1, None
            for t in allg:
                T2 = {r: (t if r else float("inf")) for r in range(len(RELS))}; m = macro(pred(F2, T2), g2)[0]
                if m > best: best, TH = m, T2
        pv = pred(FV, TH); mv, per = macro(pv, gv)
        acc = sum(1 for p, g in zip(pv, gv) if p == g)/len(gv)
        n_rules = sum(ok); n_on = sum(1 for i in range(len(rules)) if ok[i] and W[i] >= TH[RL[i]])
        return best, mv, acc, per, n_rules, n_on

    print("=" * 110); print("ABLATION BAI 1 (EV-EV, bo luat toan train): do sau, cach cham diem luat, combiner"); print("=" * 110)
    print("%-36s %-34s %8s %8s %8s %7s %6s | F1 CONT SIMU OVER" % ("do sau", "diem luat", "CONF-2", "valid", "acc", "luat", "bat"))
    rows = [(d, s, True) for d in DEPTH for s in ("Wilson (pipeline)",)] + \
           [("cả 1 và 2 điều kiện (pipeline)", s, True) for s in SC if s != "Wilson (pipeline)"] + \
           [("cả 1 và 2 điều kiện (pipeline)", "Wilson, MỘT ngưỡng chung cho mọi nhãn", False)]
    for d, s, pl in rows:
        W = SC["Wilson (pipeline)"] if s.startswith("Wilson") else SC[s]
        b, mv, acc, per, nr, non = run(W, DEPTH[d], pl)
        print("%-36s %-34s %7.2f%% %7.2f%% %7.2f%% %7d %6d | %5.1f %5.1f %5.1f" % (d, s, 100*b, 100*mv, 100*acc, nr, non, 100*per[1], 100*per[2], 100*per[3]), flush=True)
    MF.log("xong")

if __name__ == "__main__":
    main()
