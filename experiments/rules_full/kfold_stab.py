# -*- coding: utf-8 -*-
"""Approach C with a stability filter. kfold_mine.py kept the UNION of the five folds' rules, so the
final model (110k rules) was not the model its floors were tuned for (about 74k rules per fold) and
rules picked by a single fold -- likely by luck -- entered with evidence from one fold only.
Here a rule is kept only if at least m of the K folds selected it, the same filter is applied to
the out-of-fold predictions, and m and the floors are chosen on those out-of-fold predictions of
all train pairs. Valid is opened once, for the chosen m. Reuses seed_kfold/kfold_sel.pkl."""
import os, sys, io, json, math, pickle
os.environ["SEED"] = "kfold"
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kfold_mine as KM
MF = KM.MF; K = KM.K; RELS = MF.RELS; log = MF.log

def main():
    with open(MF.OUT/"kfold_meta.pkl", "rb") as fh: meta = pickle.load(fh)
    with open(MF.OUT/"kfold_sel.pkl", "rb") as fh: SEL = pickle.load(fh)
    fold = meta["fold"]; gold = meta["lab"]; ntr = len(fold)
    nsel = Counter(k for j in range(K) for k in SEL[j])
    def pooled(key, excl=None):
        cn = ck = 0; p0 = None
        for j in range(K):
            if j == excl or key not in SEL[j]: continue
            _, _, c_n, c_k, p0 = SEL[j][key]; cn += c_n; ck += c_k
        return cn, ck, p0
    pos = [[i for i, f in enumerate(fold) if f == j] for j in range(K)]
    OOF = [None]*ntr                                  # per train pair: list of (label, weight, stability)
    for j in range(K):
        rules_j = []
        for key in SEL[j]:
            cn, ck, p0 = pooled(key, excl=j)
            if cn >= 10 and MF.wlb(ck, cn) > p0: rules_j.append((key, MF.wlb(ck, cn)))
        F = KM.fire(20 + j, len(pos[j]), [(k[0], k[1], k[3]) for k, w in rules_j])
        for local, hits in enumerate(F):
            OOF[pos[j][local]] = [(rules_j[h][0][2], rules_j[h][1], nsel[rules_j[h][0]]) for h in hits]
        log("fold %d ban xong" % j)
    def f1s(tp, fp, fn):
        out = []
        for r in range(len(RELS)):
            P = tp[r]/(tp[r] + fp[r]) if tp[r] + fp[r] else 0; R_ = tp[r]/(tp[r] + fn[r]) if tp[r] + fn[r] else 0
            out.append((P, R_, 2*P*R_/(P + R_) if P + R_ else 0))
        return out
    def tune(m):
        rows = [([(r, w) for r, w, s in h if s >= m], g) for h, g in zip(OOF, gold)]
        fired = [(h, g) for h, g in rows if h]; base = Counter(g for h, g in rows if not h)
        def val(TH):
            tp, fp, fn = Counter(), Counter(), Counter()
            tp[0] += base[0]
            for r, c in base.items():
                if r: fp[0] += c; fn[r] += c
            for h, g in fired:
                best = None
                for r, w in h:
                    if w >= TH[r] and (best is None or w > best[1]): best = (r, w)
                p = best[0] if best else 0
                if p == g: tp[g] += 1
                else: fp[p] += 1; fn[g] += 1
            return sum(x[2] for x in f1s(tp, fp, fn))/6
        TH = {r: 9 for r in range(len(RELS))}; best = val(TH)
        for _ in range(2):
            for r in range(1, len(RELS)):
                for t in (0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 9):
                    T2 = dict(TH); T2[r] = t; v = val(T2)
                    if v > best: best, TH = v, T2
        return best, TH
    res = {}
    for m in (1, 2, 3, 4, 5):
        res[m] = tune(m)
        log("m = %d (luat duoc >= %d fold chon): macro ngoai fold %.2f%%, nguong %s" %
            (m, m, 100*res[m][0], {RELS[r][:4]: t for r, t in res[m][1].items() if t < 9}))
    mbest = max(res, key=lambda m: res[m][0]); TH = res[mbest][1]
    FIN = []
    for key, s in nsel.items():
        if s < mbest: continue
        cn, ck, p0 = pooled(key)
        if cn >= 10 and MF.wlb(ck, cn) > p0: FIN.append((key, MF.wlb(ck, cn)))
    FV = KM.fire(3, len(meta["vlab"]), [(k[0], k[1], k[3]) for k, w in FIN])
    gv = meta["vlab"]; tp, fp, fn = Counter(), Counter(), Counter()
    for hits, g in zip(FV, gv):
        best = None
        for h in hits:
            k, w = FIN[h]
            if w >= TH[k[2]] and (best is None or w > best[1]): best = (k[2], w)
        p = best[0] if best else 0
        if p == g: tp[g] += 1
        else: fp[p] += 1; fn[g] += 1
    per = f1s(tp, fp, fn); mv = sum(x[2] for x in per)/6; acc = sum(tp.values())/len(gv)
    active = sum(1 for k, w in FIN if w >= TH[k[2]])
    print(); print("=" * 100); print("HUONG C + LOC ON DINH -- m chon tren du doan ngoai fold, valid mo mot lan"); print("=" * 100)
    print("  m = %d; %d luat, %d hoat dong; nguong %s" % (mbest, len(FIN), active, {RELS[r][:4]: t for r, t in TH.items() if t < 9}))
    print("  valid macro-F1 %.2f%%  accuracy %.2f%%   (huong A 26,99%% / 87,90%%; huong C khong loc 26,32%% / 87,00%%)" % (100*mv, 100*acc))
    for r in range(len(RELS)):
        print("    %-13s P %6.2f%%  R %6.2f%%  F1 %6.2f%%" % (RELS[r], 100*per[r][0], 100*per[r][1], 100*per[r][2]))
    log("xong")

if __name__ == "__main__":
    main()
