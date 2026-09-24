# -*- coding: utf-8 -*-
"""Approach C: use ALL train documents both to find rules and to score them, without a rule ever
grading itself (K-fold cross-fitting).

  folds      train documents split in K = 5 by md5("kf" + doc) % 5
  mine       for each fold j: exhaustive depth <= 2 in every class of the 8 views on the OTHER four
             folds (same gates and BH-FDR as mine_full.py)            -> candidate set S_j
  score      the candidates of S_j are counted on fold j (never seen by their selection)
  weight     w(rule) = Wilson bound of the rule's out-of-fold evidence pooled over the folds that
             selected it; kept if pooled cn >= 10 and w > class base rate
  floors     out-of-fold predictions for every train pair: a pair of fold j is predicted with the
             rules of S_j and weights pooled over the OTHER folds' evaluations (no label of fold j
             is used); per-label floors by coordinate ascent on the macro-F1 of those predictions
  final      union of the rules, pooled out-of-fold weights, the chosen floors; valid opened once;
             then compressed with the set cover of rule_cover.py
Compare with approach A (mine_full.py: DISCOVERY 60% / CONF-1 20% / CONF-2 20%): valid 26.99%.
"""
import os, sys, io, json, math, pickle, time
os.environ["SEED"] = "kfold"                    # redirects mine_full.OUT to rules_full/seed_kfold
from collections import Counter, defaultdict
from pathlib import Path
from array import array
from multiprocessing import Pool
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mine_full as MF
import rule_cover as RC
K = 5
NW = int(os.environ.get("NW", "4"))
RELS = MF.RELS
log = MF.log

def fold_of(doc): return MF.h("kf" + doc) % K

def write_caches():
    with open(MF.BASE_CACHE, "rb") as fh: data = pickle.load(fh)
    T = data["train"]; V = data["valid"]; dn = T["docnames"]
    fold = [fold_of(dn[d]) for d in T["doc"]]
    def dump(code, idx, S):
        part = {"conds": [S["conds"][i] for i in idx], "lab": [S["lab"][i] for i in idx], "doc": [S["doc"][i] for i in idx],
                "sig": [[S["sig"][v][i] for i in idx] for v in range(len(MF.VIEW_NAMES))]}
        with open(MF.OUT/("cache_sp%d.pkl" % code), "wb") as fh: pickle.dump(part, fh, protocol=pickle.HIGHEST_PROTOCOL)
    for j in range(K):
        dump(10 + j, [i for i, f in enumerate(fold) if f != j], T)     # mining part
        dump(20 + j, [i for i, f in enumerate(fold) if f == j], T)     # held-out fold
    dump(3, list(range(len(V["lab"]))), V)
    meta = {"fold": fold, "lab": list(T["lab"]), "vlab": list(V["lab"]), "cond_names": data["cond_names"], "sig_names": data["sig_names"]}
    with open(MF.OUT/"kfold_meta.pkl", "wb") as fh: pickle.dump(meta, fh)
    log("cache K-fold: %s cap moi fold" % [sum(1 for f in fold if f == j) for j in range(K)])

# ---------------------------------------------------------------- firing with an arbitrary rule list
FG = {}
def init_fire(code, rules_file):
    with open(MF.OUT/("cache_sp%d.pkl" % code), "rb") as fh: FG.update(pickle.load(fh))
    with open(rules_file, "rb") as fh: R = pickle.load(fh)
    idx = defaultdict(list)
    for rid, (v, s, key) in enumerate(R): idx[(v, s, key[0])].append((rid, key[1:]))
    FG["idx"] = idx
def fire_chunk(bounds):
    i0, i1 = bounds; out = []
    for i in range(i0, i1):
        cs = set(FG["conds"][i]); hits = []
        for v in range(len(MF.VIEW_NAMES)):
            s = FG["sig"][v][i]
            for c in cs:
                for rid, rest in FG["idx"].get((v, s, c), ()):
                    if all(z in cs for z in rest): hits.append(rid)
        out.append(hits)
    return i0, out
def fire(code, n, rules_vsk):
    rf = MF.OUT/("fire_rules_%d.pkl" % code)
    with open(rf, "wb") as fh: pickle.dump(rules_vsk, fh)
    res = [None]*n; chunks = [(i, min(n, i + 4000)) for i in range(0, n, 4000)]
    with Pool(NW, initializer=init_fire, initargs=(code, str(rf))) as pool:
        for i0, out in pool.imap_unordered(fire_chunk, chunks): res[i0:i0 + len(out)] = out
    return res

def main():
    if not (MF.OUT/"kfold_meta.pkl").exists(): write_caches()
    with open(MF.OUT/"kfold_meta.pkl", "rb") as fh: meta = pickle.load(fh)
    fold = meta["fold"]; ntr = len(fold)
    # ------------------------------------------------ per fold: mine on the other folds, count on the fold
    SEL = {}                                          # j -> {(v,s,r,key): (n, k, cn, ck, p0)}
    sel_file = MF.OUT/"kfold_sel.pkl"
    if sel_file.exists():
        with open(sel_file, "rb") as fh: SEL = pickle.load(fh)
    for j in range(K):
        if j in SEL: continue
        units = [(v, r) for v in range(len(MF.VIEW_NAMES)) for r in range(1, len(RELS))]
        cands = []
        with Pool(NW, initializer=MF.init_worker, initargs=(10 + j,)) as pool:
            for res in pool.imap_unordered(MF.mine_unit, units): cands += res
        cands.sort(key=lambda t: t[6]); m = len(cands); cut = 0
        for i, c in enumerate(cands, 1):
            if c[6] <= math.log(0.05*i/m): cut = i
        cands = cands[:cut]
        byview = defaultdict(list)
        for c in cands: byview[c[0]].append((c[1], c[2], c[3]))
        conf = {}
        with Pool(min(NW, len(byview)), initializer=MF.init_worker, initargs=(20 + j,)) as pool:
            for res in pool.imap_unordered(MF.confirm_unit, list(byview.items())): conf.update(res)
        SEL[j] = {(v, s, r, key): (n, k) + conf.get((v, s, r, key), (0, 0)) + (p0,) for (v, s, r, key, n, k, lp, p0) in cands}
        log("fold %d: %d ung vien sau BH; nhan %s" % (j, len(SEL[j]), dict(Counter(RELS[x[2]] for x in SEL[j]))))
        with open(sel_file, "wb") as fh: pickle.dump(SEL, fh)
    # ------------------------------------------------ pooled out-of-fold evidence
    allkeys = set().union(*[set(SEL[j]) for j in range(K)])
    def pooled(key, excl=None):
        cn = ck = 0; p0 = None
        for j in range(K):
            if j == excl or key not in SEL[j]: continue
            _, _, c_n, c_k, p0 = SEL[j][key]; cn += c_n; ck += c_k
        return cn, ck, p0
    FINAL = []
    for key in allkeys:
        cn, ck, p0 = pooled(key)
        if cn >= 10 and MF.wlb(ck, cn) > p0: FINAL.append((key, MF.wlb(ck, cn), cn, ck, sum(1 for j in range(K) if key in SEL[j])))
    log("hop %d luat ung vien qua cac fold; %d qua xac nhan gop ngoai fold; nhan %s; so fold chon: %s" %
        (len(allkeys), len(FINAL), dict(Counter(RELS[k[2]] for k, *_ in FINAL)), dict(Counter(x[4] for x in FINAL))))
    # ------------------------------------------------ out-of-fold predictions on all train pairs
    oof_hits = [None]*ntr; oof_w = {}; oof_rel = {}
    pos_of_fold = [[i for i, f in enumerate(fold) if f == j] for j in range(K)]
    for j in range(K):
        rules_j = []
        for key in SEL[j]:
            cn, ck, p0 = pooled(key, excl=j)
            if cn >= 10 and MF.wlb(ck, cn) > p0: rules_j.append((key, MF.wlb(ck, cn)))
        F = fire(20 + j, len(pos_of_fold[j]), [(k[0], k[1], k[3]) for k, w in rules_j])
        for local, hits in enumerate(F):
            oof_hits[pos_of_fold[j][local]] = [(RELS.index(RELS[rules_j[h][0][2]]), rules_j[h][1]) for h in hits]
        log("fold %d: %d luat dung cho du doan ngoai fold" % (j, len(rules_j)))
    gold_tr = meta["lab"]
    def predict(hits_list, TH):
        out = []
        for hits in hits_list:
            best = None
            for r, w in hits:
                if w >= TH[r] and (best is None or w > best[1]): best = (r, w)
            out.append(best[0] if best else 0)
        return out
    def macro(pred, gold):
        tp, fp, fn = Counter(), Counter(), Counter()
        for p, g in zip(pred, gold):
            if p == g: tp[g] += 1
            else: fp[p] += 1; fn[g] += 1
        per = {}
        for r in range(len(RELS)):
            P = tp[r]/(tp[r] + fp[r]) if tp[r] + fp[r] else 0; R_ = tp[r]/(tp[r] + fn[r]) if tp[r] + fn[r] else 0
            per[r] = (P, R_, 2*P*R_/(P + R_) if P + R_ else 0)
        return sum(x[2] for x in per.values())/6, per
    fired = [i for i, h in enumerate(oof_hits) if h]; base = Counter(gold_tr[i] for i in range(ntr) if not oof_hits[i])
    sub_h = [oof_hits[i] for i in fired]; sub_g = [gold_tr[i] for i in fired]
    def val(TH):
        pred = predict(sub_h, TH); tp, fp, fn = Counter(), Counter(), Counter()
        tp[0] += base[0]
        for r, c in base.items():
            if r != 0: fp[0] += c; fn[r] += c
        for p, g in zip(pred, sub_g):
            if p == g: tp[g] += 1
            else: fp[p] += 1; fn[g] += 1
        F = []
        for r in range(len(RELS)):
            P = tp[r]/(tp[r] + fp[r]) if tp[r] + fp[r] else 0; R_ = tp[r]/(tp[r] + fn[r]) if tp[r] + fn[r] else 0
            F.append(2*P*R_/(P + R_) if P + R_ else 0)
        return sum(F)/6
    TH = {r: 9 for r in range(len(RELS))}; best = val(TH)
    for _ in range(3):
        for r in range(1, len(RELS)):
            for t in (0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 9):
                T2 = dict(TH); T2[r] = t; v = val(T2)
                if v > best: best, TH = v, T2
    log("nguong chon tren du doan ngoai fold cua toan bo train (macro %.2f%%): %s" % (100*best, {RELS[r][:4]: t for r, t in TH.items() if t < 9}))
    # ------------------------------------------------ final model on valid (opened once)
    FIN = [(k, w) for k, w, *_ in FINAL]
    FV = fire(3, len(meta["vlab"]), [(k[0], k[1], k[3]) for k, w in FIN])
    vh = [[(k[2], w) for k, w in (FIN[h] for h in hits)] for hits in FV]
    pv = predict(vh, TH); gv = meta["vlab"]
    mv, per = macro(pv, gv); acc = sum(1 for p, g in zip(pv, gv) if p == g)/len(gv)
    active = [i for i, (k, w) in enumerate(FIN) if w >= TH[k[2]]]
    print(); print("=" * 104); print("HUONG C -- CROSS-FIT K=%d TREN TOAN BO TRAIN, valid mo mot lan" % K); print("=" * 104)
    print("  %d luat (hop cac fold, xac nhan ngoai fold), %d hoat dong theo nguong" % (len(FIN), len(active)))
    print("  valid macro-F1 %.2f%%  accuracy %.2f%%   (huong A: 26,99%% / 87,90%%)" % (100*mv, 100*acc))
    for r in range(len(RELS)):
        print("    %-13s P %6.2f%%  R %6.2f%%  F1 %6.2f%%" % (RELS[r], 100*per[r][0], 100*per[r][1], 100*per[r][2]))
    # ------------------------------------------------ compression (set cover on the final model's train output)
    W = [w for k, w in FIN]; REL = [RELS[k[2]] for k, w in FIN]
    FT = [None]*ntr
    for j in range(K):
        F = fire(20 + j, len(pos_of_fold[j]), [(k[0], k[1], k[3]) for k, w in FIN])
        for local, hits in enumerate(F): FT[pos_of_fold[j][local]] = hits
    act = set(active)
    rows_tr = [([h for h in hits if h in act], "BEFORE", RELS[g]) for hits, g in zip(FT, gold_tr)]
    rows_va = [([h for h in hits if h in act], "BEFORE", RELS[g]) for hits, g in zip(FV, gv)]
    el = RC.constraints(rows_tr, W, REL, False)
    Kset, nf, lb, d = RC.cover(el, W)
    pk = [RC.output(h, fb, W, REL, Kset) for h, fb, g in rows_va]; pf = [RC.output(h, fb, W, REL) for h, fb, g in rows_va]
    mk, acck, _ = RC.macro(pk, [g for h, fb, g in rows_va], RELS)
    print("  rut gon (set cover giu moi du doan tren train): %d luat hoat dong -> %d (chan duoi %d); valid giu nguyen %.3f%%, macro-F1 %.2f%%" %
          (len(active), len(Kset), lb, 100*sum(1 for a, b in zip(pf, pk) if a == b)/len(pf), 100*mk))
    json.dump({"floors": {RELS[r]: t for r, t in TH.items() if t < 9},
               "rules": [{"view": MF.VIEW_NAMES[k[0]], "sig": meta["sig_names"][k[0]][k[1]], "rel": RELS[k[2]],
                          "conds": [list(meta["cond_names"][c]) for c in k[3]], "w": w} for k, w in FIN],
               "compact": sorted(Kset)},
              io.open(MF.ART/"rules_kfold.json", "w", encoding="utf-8"), ensure_ascii=False, default=list)
    log("xong")

if __name__ == "__main__":
    main()
