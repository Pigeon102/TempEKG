# -*- coding: utf-8 -*-
"""Compress the 54,719 full-train EV-EV rules with guarantees, not heuristics.

The combiner is  pred(x) = rel(argmax_{r in A(x)} key(r))  or BEFORE if A(x) is empty, where A(x) is
the set of ACTIVE rules firing on pair x (wlb >= floor of the rule's label) and key(r) = (wlb, -id).
Everything below follows from that one formula.

  L1  inactive rules      a rule with wlb < floor(rel) never enters A(x), so deleting it changes no
                          prediction anywhere (train, valid, any future pair).         -> exact
  L2  extensional classes two rules with the same label and the same firing set on all train pairs
                          are the same statement; keep one representative (fewest conditions).
                          Measured with a 61-bit fingerprint sum_{i in ext(r)} h(i) mod (2^61-1).
  L3  prediction-preserving cover
                          for a pair x predicted p != BEFORE let M(x) = max key of active rules of
                          other labels firing on x. Any kept set K that contains, for every such x,
                          at least one rule in C(x) = {r in A(x): rel(r) = p, key(r) > M(x)} gives
                          pred_K(x) = pred(x): the p-rule still beats every other label, and removing
                          rules can never create a firing. Pairs predicted BEFORE stay BEFORE.
                          Minimising |K| is SET COVER over the universe {x: pred(x) != BEFORE}.
                          Solved by lazy greedy (<= H(d) * OPT, d = largest candidate coverage),
                          then reverse deletion (the result is irredundant: no rule can be dropped).
                          A lower bound on OPT: a set of pairs with pairwise DISJOINT C(x) needs one
                          distinct rule each (greedy packing, smallest C(x) first).
            variant A     universe = every pair with pred != BEFORE -> identical predictions
            variant B     universe = pairs with pred = gold != BEFORE -> every correct pair stays
                          correct (accuracy can only go up on the cover's data); wrong predictions
                          may drop to BEFORE or move to another label
  L4  families            the kept rules grouped by template (label + condition forms/attributes,
                          values abstracted) -- the reduction that kept signal in the 155k study --
                          and by near-duplicate extension (single linkage, Jaccard >= 0.8).

Covers are built on DISCOVERY + CONFIRMATION-1 (the splits the rules were mined and confirmed on),
checked on CONFIRMATION-2, and valid is opened once for every variant. Floors are not re-tuned.
"""
import io, os, sys, json, math, pickle, hashlib, heapq, time
from collections import Counter, defaultdict
from pathlib import Path
from multiprocessing import Pool

OUT = Path(__file__).resolve().parent
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
FLOOR = {"CONTAINS": 0.5, "SIMULTANEOUS": 0.15, "OVERLAP": 0.1}
P61 = (1 << 61) - 1
T0 = time.time()
def log(*a): print("[%6.0fs] " % (time.time() - T0) + " ".join(str(x) for x in a), flush=True)

G = {}
def init(which):
    with open(OUT/("cache_sp%d.pkl" % which), "rb") as fh: G.update(pickle.load(fh))
    with open(OUT/"rules_confirmed.pkl", "rb") as fh: R = pickle.load(fh)
    idx = defaultdict(list)
    for rid, x in enumerate(R): idx[(x["v"], x["s"], x["key"][0])].append((rid, x["key"][1:]))
    G["ridx"] = idx; G["which"] = which
    G["active"] = [x["rel"] in FLOOR and x["wlb"] >= FLOOR[x["rel"]] for x in R]

def chunk(bounds):
    """For each pair: active firing rules; for every rule: (count, fingerprint) over the chunk."""
    i0, i1 = bounds; act = []; cnt = Counter(); fp = defaultdict(int); A = G["active"]
    for i in range(i0, i1):
        cs = set(G["conds"][i]); hits = []
        for v in range(8):
            s = G["sig"][v][i]
            for c in cs:
                for rid, rest in G["ridx"].get((v, s, c), ()):
                    if all(z in cs for z in rest): hits.append(rid)
        h = int(hashlib.md5(b"%d:%d" % (G["which"], i)).hexdigest()[:15], 16)
        for rid in hits: cnt[rid] += 1; fp[rid] = (fp[rid] + h) % P61
        act.append([rid for rid in hits if A[rid]])
    return i0, act, dict(cnt), dict(fp)

def fire_split(which, NW):
    n = len(pickle.load(open(OUT/("cache_sp%d.pkl" % which), "rb"))["lab"])
    chunks = [(i, min(n, i + 3000)) for i in range(0, n, 3000)]
    act = [None]*n; cnt = Counter(); fp = defaultdict(int)
    with Pool(NW, initializer=init, initargs=(which,)) as pool:
        for i0, a, c, f in pool.imap_unordered(chunk, chunks):
            act[i0:i0 + len(a)] = a
            for k, v in c.items(): cnt[k] += v
            for k, v in f.items(): fp[k] = (fp[k] + v) % P61
    return act, cnt, fp

# ---------------------------------------------------------------- helpers on firing lists
def main():
    NW = int(os.environ.get("NW", "4"))
    R = pickle.load(open(OUT/"rules_confirmed.pkl", "rb"))
    REL = [x["rel"] for x in R]; W = [x["wlb"] for x in R]
    key = lambda r: (W[r], -r)
    ACT = [i for i, x in enumerate(R) if x["rel"] in FLOOR and x["wlb"] >= FLOOR[x["rel"]]]
    log("%d luat; %d luat hoat dong (vuot nguong nhan)" % (len(R), len(ACT)))

    FIRE, LAB = {}, {}; CNT = Counter(); FP = defaultdict(int)
    for sp in (0, 1, 2, 3):
        log("ban luat tren phan %d ..." % sp)
        a, c, f = fire_split(sp, NW)
        FIRE[sp] = a; LAB[sp] = [RELS[l] for l in pickle.load(open(OUT/("cache_sp%d.pkl" % sp), "rb"))["lab"]]
        if sp < 3:
            for k, v in c.items(): CNT[k] += v
            for k, v in f.items(): FP[k] = (FP[k] + v) % (P61)
    log("xong ban luat")

    def predict(hits, keep=None):
        best = None
        for r in hits:
            if keep is not None and r not in keep: continue
            if best is None or key(r) > key(best): best = r
        return REL[best] if best is not None else "BEFORE"
    def macro(pred, gold):
        tp, fp, fn = Counter(), Counter(), Counter()
        for p, g in zip(pred, gold):
            if p == g: tp[g] += 1
            else: fp[p] += 1; fn[g] += 1
        per = {}
        for r in RELS:
            P = tp[r]/(tp[r] + fp[r]) if tp[r] + fp[r] else 0.0; Rc = tp[r]/(tp[r] + fn[r]) if tp[r] + fn[r] else 0.0
            per[r] = (P, Rc, 2*P*Rc/(P + Rc) if P + Rc else 0.0)
        return sum(v[2] for v in per.values())/6, sum(tp.values())/len(gold), per

    # ------------------------------------------------ L1 + L2
    print("\n" + "=" * 100); print("L1 + L2 -- luat khong bao gio anh huong du doan, va luat trung phan mo rong"); print("=" * 100)
    fired = [r for r in range(len(R)) if CNT[r] > 0]
    cls = defaultdict(list)
    for r in fired: cls[(REL[r], CNT[r], FP[r])].append(r)
    def canon(rs): return min(rs, key=lambda r: (len(R[r]["conds"]), R[r]["view"] != "global", -R[r]["cn"], r))
    rep = {r: canon(rs) for rs in cls.values() for r in rs}
    act_cls = defaultdict(list)
    for r in ACT: act_cls[rep[r]].append(r)
    print("  tong luat                                   %6d" % len(R))
    print("  L1: duoi nguong cua nhan (khong bao gio bo phieu)  %6d  -> bo, chinh xac tuyet doi" % (len(R) - len(ACT)))
    print("  luat hoat dong                              %6d" % len(ACT))
    print("  L2: lop tuong duong phan mo rong, tren 54.719 luat  %6d lop (trung binh %.2f luat / lop)" % (len(cls), len(fired)/len(cls)))
    print("      trong 2.794 luat hoat dong                     %6d lop" % len(act_cls))
    big = sorted(act_cls.values(), key=len, reverse=True)[:3]
    for g in big:
        print("      lop %d luat, vd:" % len(g))
        for r in g[:4]: print("         %-10s %-22s %s" % (R[r]["view"], str(R[r]["sig"])[:22], R[r]["conds"]))
    ACT2 = sorted(act_cls)                          # one representative per class
    KEEP2 = set(ACT2)
    same = sum(1 for sp in (0, 1, 2, 3) for h in FIRE[sp] if predict(h) != predict(h, KEEP2))
    print("  du doan doi khi chi giu dai dien lop: %d / %d cap (train + valid)" % (same, sum(len(FIRE[s]) for s in FIRE)))

    # ------------------------------------------------ L3 set cover
    def build_universe(sps, correct_only):
        elems = []
        for sp in sps:
            for i, h in enumerate(FIRE[sp]):
                hh = [r for r in h if r in KEEP2]
                if not hh: continue
                p = predict(hh)
                if correct_only and p != LAB[sp][i]: continue
                other = [key(r) for r in hh if REL[r] != p]
                M = max(other) if other else (-1.0, 0)
                C = frozenset(r for r in hh if REL[r] == p and key(r) > M)
                elems.append(C)
        return elems
    def cover(elems):
        by_rule = defaultdict(list)
        for e, C in enumerate(elems):
            for r in C: by_rule[r].append(e)
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
        assert all(covered)
        # reverse deletion -> irredundant
        cc = [0]*len(elems)
        for r in K:
            for e in by_rule[r]: cc[e] += 1
        for r in sorted(K, key=lambda r: (len(by_rule[r]), W[r])):
            if all(cc[e] >= 2 for e in by_rule[r]):
                K.discard(r)
                for e in by_rule[r]: cc[e] -= 1
        # lower bound: disjoint packing
        used = set(); lb = 0
        for C in sorted(elems, key=len):
            if not (C & used): used |= C; lb += 1
        d = max(len(es) for es in by_rule.values())
        return K, len(forced), lb, d

    def report(name, K):
        rows = []
        for sp, nm in ((0, "DISCOVERY"), (1, "CONF-1"), (2, "CONF-2"), (3, "VALID")):
            pf = [predict(h) for h in FIRE[sp]]; pk = [predict(h, K) for h in FIRE[sp]]
            agree = sum(1 for a, b in zip(pf, pk) if a == b)/len(pf)
            mf, af, _ = macro(pf, LAB[sp]); mk, ak, per = macro(pk, LAB[sp])
            rows.append((nm, agree, mf, mk, af, ak, per))
        print("  %-38s %5d luat" % (name, len(K)))
        for nm, ag, mf, mk, af, ak, per in rows:
            print("     %-9s  giu nguyen du doan %7.3f%%   macro-F1 %.2f%% -> %.2f%%   acc %.2f%% -> %.2f%%" % (nm, 100*ag, 100*mf, 100*mk, 100*af, 100*ak))
        per = rows[-1][-1]
        print("     VALID theo nhan: " + "  ".join("%s %.1f/%.1f/%.1f" % (r[:4], 100*per[r][0], 100*per[r][1], 100*per[r][2]) for r in RELS[:4]))
        return rows

    print("\n" + "=" * 100); print("L3 -- set cover giu du doan (dung tren DISCOVERY + CONF-1; kiem tren CONF-2; valid mo mot lan)"); print("=" * 100)
    full = set(ACT)
    report("Day du (2.794 luat hoat dong)", full)
    report("L2: dai dien lop tuong duong", KEEP2)
    res = {}
    for nm, corr in (("A: giu moi du doan", False), ("B: giu moi du doan dung", True)):
        el = build_universe((0, 1), corr)
        K, nf, lb, d = cover(el)
        print("\n  %s -- vu tru %d cap, bat buoc %d luat, can duoi OPT >= %d, greedy <= H(%d)=%.2f x OPT" %
              (nm, len(el), nf, lb, d, sum(1/k for k in range(1, d + 1))))
        report(nm, K); res[nm] = K

    # ------------------------------------------------ L4 families of the variant-B set
    print("\n" + "=" * 100); print("L4 -- gom nhom cac luat giu lai"); print("=" * 100)
    for nm, K in res.items():
        tmpl = defaultdict(list)
        for r in K: tmpl[(REL[r], tuple(sorted((c[0], c[1]) for c in R[r]["conds"])))].append(r)
        print("  %s: %d luat -> %d khuon (template); theo nhan %s" % (nm, len(K), len(tmpl), dict(Counter(REL[r] for r in K))))
    K = res["B: giu moi du doan dung"]
    tmpl = defaultdict(list)
    for r in K: tmpl[(REL[r], tuple(sorted((c[0], c[1]) for c in R[r]["conds"])))].append(r)
    print("\n  cac khuon lon nhat (B):")
    for (rel, t), rs in sorted(tmpl.items(), key=lambda kv: -len(kv[1]))[:15]:
        cover_n = sum(R[r]["cn"] for r in rs)
        ex = max(rs, key=lambda r: W[r])
        print("   %-12s %-60s %3d luat | vd %s %s wlb %.3f" % (rel, " ∧ ".join("%s(%s)" % t2 for t2 in t)[:60], len(rs), R[ex]["view"], R[ex]["conds"], W[ex]))
    # near-duplicate extensions (single linkage, Jaccard >= 0.8) on train
    ntr = [len(FIRE[s]) for s in (0, 1, 2)]; off = [0, ntr[0], ntr[0] + ntr[1]]
    bits = {r: bytearray((sum(ntr) + 7)//8) for r in K}
    for s in (0, 1, 2):
        for i, h in enumerate(FIRE[s]):
            j = off[s] + i
            for r in h:
                if r in bits: bits[r][j >> 3] |= 1 << (j & 7)
    ext = {r: int.from_bytes(b, "little") for r, b in bits.items()}; pc = {r: e.bit_count() for r, e in ext.items()}
    parent = {r: r for r in K}
    def find(r):
        while parent[r] != r: parent[r] = parent[parent[r]]; r = parent[r]
        return r
    Ks = sorted(K); pairs = 0
    for a in range(len(Ks)):
        for b in range(a + 1, len(Ks)):
            x, y = Ks[a], Ks[b]
            if REL[x] != REL[y]: continue
            inter = (ext[x] & ext[y]).bit_count()
            if inter and inter/(pc[x] + pc[y] - inter) >= 0.8:
                parent[find(x)] = find(y); pairs += 1
    comps = Counter(find(r) for r in K)
    print("\n  gan trung (Jaccard >= 0,8 tren train): %d cap; %d luat -> %d cum" % (pairs, len(K), len(comps)))

    json.dump({"floors": FLOOR,
               "variants": {nm: [{k: R[r][k] for k in ("view", "sig", "rel", "conds", "k", "n", "ck", "cn", "wlb")} for r in sorted(Kv)]
                            for nm, Kv in res.items()}},
              io.open(ART/"rules_compact.json", "w", encoding="utf-8"), ensure_ascii=False, default=list, indent=0)
    log("da luu src/artifacts/rules_compact.json; xong")

if __name__ == "__main__":
    main()
