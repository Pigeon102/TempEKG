# -*- coding: utf-8 -*-
"""Bai 2, step 3.1: how many audit rules, and how few are needed -- same proof as the EV-EV rules.

The auditor's combiner (classify_k) has the same form as the EV-EV combiner:
    final(x) = label of argmax_{r in A(x)} key(r),  or the CURRENT label if A(x) is empty,
A(x) = rules of x's partition (edge type, current label) that fire on x with cw >= floor(type, label).
Rules only ever propose a label different from the partition's current label, so the argument of
compress.py carries over with "keep the current label" in place of "BEFORE":
  L1  rules under their floor never vote                                   -> exact
  L3  set cover over the pairs the auditor changes (A: every change, B: every correct change),
      C(x) = rules of the chosen label whose key beats every other-label rule firing on x.
Covers are built on the fold's TRAINING documents (mine + confirm + tune), scored on the test fold,
both folds summed -- the same cross-fit as bai2_combo.py. Run with TAG=_full.
"""
import io, heapq
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_C = io.open(HERE/"bai2_combo.py", encoding="utf-8").read()
exec(SRC_C[:SRC_C.index("rows = defaultdict(dict)")])

def cover(elems, W):
    by_rule = defaultdict(list)
    for e, C in enumerate(elems):
        for r in C: by_rule[r].append(e)
    if not elems: return set(), 0, 0
    forced = {next(iter(C)) for C in elems if len(C) == 1}
    covered = [False]*len(elems); K = set()
    for r in forced:
        K.add(r)
        for e in by_rule[r]: covered[e] = True
    heap = [(-len(es), -W[r], r) for r, es in by_rule.items() if r not in K]; heapq.heapify(heap)
    while heap:
        g, w, r = heapq.heappop(heap)
        gain = sum(1 for e in by_rule[r] if not covered[e])
        if gain == 0: continue
        if gain < -g: heapq.heappush(heap, (-gain, w, r)); continue
        K.add(r)
        for e in by_rule[r]: covered[e] = True
    cc = [0]*len(elems)
    for r in K:
        for e in by_rule[r]: cc[e] += 1
    for r in sorted(K, key=lambda r: (len(by_rule[r]), W[r])):
        if all(cc[e] >= 2 for e in by_rule[r]):
            K.discard(r)
            for e in by_rule[r]: cc[e] -= 1
    used = set(); lb = 0
    for C in sorted(elems, key=len):
        if not (C & used): used |= C; lb += 1
    return K, len(forced), lb

docs_all = sorted({x["doc"] for x in IVA})
TOT = defaultdict(lambda: defaultdict(list))        # (obj, variant) -> {"fin": [...], "g": [...], "cur": [...], "k": [...]}
STATS = []
for fold in (0, 1):
    trn = [d for d in docs_all if H("cf" + d) % 2 != fold]; tst = [d for d in docs_all if H("cf" + d) % 2 == fold]
    part = lambda d: H("in3" + d) % 3
    mine = [x for d in trn if part(d) == 0 for x in BYDOC[d]]
    conf = [x for d in trn if part(d) == 1 for x in BYDOC[d]]
    tune_x = [x for d in trn if part(d) == 2 for x in BYDOC[d]]
    test = [x for d in tst for x in BYDOC[d]]
    AR = audit_rules(mine, conf, "n1", LAYB, True); idx = rule_index(AR)
    activate(mine + conf + tune_x + test, AR, "n1", LAYB)
    RID = {}; REL_ = []; CW = []; TYP = []; NK = []
    for pt, (PAT, rules) in AR.items():
        for key, r, cw in rules:
            RID[(key, r)] = len(REL_); REL_.append(r); CW.append(cw); TYP.append(pt[0]); NK.append(len(key))
    npat = sum(len(PAT) for PAT, _ in AR.values())
    log("fold %d: %d nhom (loai canh, nhan hien tai), %d pattern, %d luat (1 pattern: %d, 2-3 pattern lien tang: %d)" %
        (fold, len(AR), npat, len(REL_), sum(1 for k in NK if k == 1), sum(1 for k in NK if k > 1)))
    def hits(x, TH):
        out = []
        for c in x["act"]:
            for key, r, cw in idx.get(c, ()):
                if cw >= TH.get((x["k"], r), 9) and all(z in x["act"] for z in key[1:]): out.append(RID[(key, r)])
        return out
    for obj in ("net", "macro"):
        TH = tune(idx, tune_x, "n1", obj)
        active = {i for i in range(len(REL_)) if CW[i] >= TH.get((TYP[i], REL_[i]), 9)}
        ky = lambda r: (CW[r], -r)
        def final(x, h, keep=None):
            best = None
            for r in h:
                if keep is not None and r not in keep: continue
                if best is None or ky(r) > ky(best): best = r
            return REL_[best] if best is not None else x["n1"]
        H_tr = [(x, hits(x, TH)) for x in mine + conf + tune_x]; H_te = [(x, hits(x, TH)) for x in test]
        ref = classify_k(idx, TH, test, "n1")
        same_ref = sum(1 for (x, h), f in zip(H_te, ref) if final(x, h) == f)/len(test)
        res = {"full": active}
        for vn, corr in (("A", False), ("B", True)):
            el = []
            for x, h in H_tr:
                if not h: continue
                p = final(x, h)
                if corr and p != x["g"]: continue
                other = [ky(r) for r in h if REL_[r] != p]; M = max(other) if other else (-1.0, 0)
                el.append(frozenset(r for r in h if REL_[r] == p and ky(r) > M))
            K, nf, lb = cover(el, CW); res[vn] = K
            STATS.append((fold, obj, vn, len(REL_), len(active), len(el), nf, lb, len(K)))
        for vn, K in res.items():
            for x, h in H_te:
                t = TOT[(obj, vn)]
                t["fin"].append(final(x, h, K)); t["ref"].append(final(x, h)); t["g"].append(x["g"]); t["cur"].append(x["n1"]); t["k"].append(x["k"])
        log("  fold %d %s: %d luat hoat dong / %d; khop classify_k %.4f%%" % (fold, obj, len(active), len(REL_), 100*same_ref))

print(); print("=" * 110); print("BAI 2 -- SO LUAT AUDITOR (buoc 3.1) VA RUT GON CO CHUNG MINH, cross-fit tren valid"); print("=" * 110)
print("  fold  muc tieu  bien the | luat mine  hoat dong | vu tru  bat buoc  chan duoi  ket qua")
for s in STATS:
    print("   %d    %-6s    %s       | %7d  %7d     | %6d  %6d  %8d  %7d" % s)
for obj in ("net", "macro"):
    for vn in ("full", "A", "B"):
        t = TOT[(obj, vn)]
        n = len(t["g"]); err = sum(1 for f, g in zip(t["fin"], t["g"]) if f != g)/n
        agree = sum(1 for f, r in zip(t["fin"], t["ref"]) if f == r)/n
        m = prf(t["fin"], t["g"])[0]
        print("  %-6s %-4s  loi %.2f%%  macro-F1 %.2f%%  giu nguyen dau ra auditor %.3f%%" % (obj, vn, 100*err, 100*m, 100*agree))
log("xong")
