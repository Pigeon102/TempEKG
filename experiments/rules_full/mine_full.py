# -*- coding: utf-8 -*-
"""Re-mine the EV-EV rule set on the FULL train set, in parallel.

The frozen 257 rules were selected on the first 400 train documents only (197 DISCOVERY / 126
CONFIRMATION / 77 DEV-INNER): about 14% of train. BEGINS-ON and ENDS-ON got no rule because no
candidate reached 25 instances on 197 documents. This script redoes the documented procedure on
all 2,913 train documents, with the same hash split the later experiments use:

  DISCOVERY      md5(doc) % 10 >= 4      proposes rules
  CONFIRMATION-1 half of the rest        re-scores rules on labels that took no part
  CONFIRMATION-2 other half              chooses the fraction kept per label and tau
  VALID                                  opened once

Candidate generation = EXHAUSTIVE depth <= 2 inside every class of the 8 views (global, sdist,
order, anchor, bucket_a, etype_a, sdist_ord, anchor_sd), each scored against its class's own base
rate. This covers both earlier branches (beam search per view, and the exhaustive MDD branch which
was global only). Counting uses Python integers as bitsets over the class's instances: the support
of a conjunction is popcount(mask_a & mask_b).

Gates (DISCOVERY): n >= 25, k >= 8, >= 5 documents, local lift >= 1.5, delta-logit >= 0.5 over the
best single-condition parent (depth 2), and Benjamini-Hochberg q < 0.05 over all candidates on a
one-sided binomial test against the class base rate. DEVIATION: the original gate 3 used 200
document-block permutations; a permutation test in pure Python on 480k instances is too slow, so the
analytic test is used and the >= 5 documents gate keeps the document clustering in check.

Parallelism: the main process encodes every pair once (condition ids, label, document, 8 view
signatures) into a compact cache; a pool of workers loads it and processes (view, label) units.
"""
import sys, io, os, json, math, hashlib, pickle, time
from array import array
from collections import Counter, defaultdict
from pathlib import Path
from multiprocessing import Pool

SRC = Path(r"C:\Reseach_Quang\tempekg\src"); sys.path.insert(0, str(SRC))
GRAPH = SRC/"graph"; ART = SRC/"artifacts"
OUT = Path(__file__).resolve().parent
SEED = os.environ.get("SEED", "")                   # seed sweep: salts the split, separate output dir
BASE_CACHE = OUT/"cache_ee.pkl"
if SEED:
    OUT = OUT/("seed_" + SEED); OUT.mkdir(exist_ok=True)
SFX = "_s" + SEED if SEED else ""
MF_OUT = os.environ.get("MF_OUT", "")              # ablations: separate output dir and artifact suffix
if MF_OUT:
    OUT = OUT/MF_OUT; OUT.mkdir(exist_ok=True); SFX = "_" + MF_OUT
ARG_ATTRS = {"anchor_roles", "roleset_a", "roleset_b", "roleset_shared", "etypeset_a", "etypeset_b", "etypeset_shared",
             "nrole_a", "nrole_b", "n_anchor", "has_loc_a", "has_loc_b", "has_person_a", "has_person_b", "has_org_a",
             "has_org_b", "role_subset", "role_overlap", "shares_anchor"}   # all derived from MAVEN-Arg arguments
CACHE = OUT/"cache_ee.pkl"
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
VIEW_NAMES = ["global", "sdist", "order", "anchor", "bucket_a", "etype_a", "sdist_ord", "anchor_sd"]
Z = 1.959963985
T0 = time.time()
def log(*a): print("[%6.0fs] " % (time.time()-T0) + " ".join(str(x) for x in a), flush=True)
def wlb(k, n):
    if n == 0: return 0.0
    p = k/n
    return (p + Z*Z/(2*n) - Z*math.sqrt(p*(1-p)/n + Z*Z/(4*n*n)))/(1 + Z*Z/n)
def h(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)
def split_of(doc):
    if h(SEED + doc) % 10 >= 4: return 0          # DISCOVERY
    return 1 if h(SEED + "s2" + doc) % 2 == 0 else 2   # CONFIRMATION-1 / -2
def logit(k, n):
    p = (k + 0.5)/(n + 1.0)
    return math.log(p/(1-p))

# ---------------------------------------------------------------- cache (main process only)
def build_cache():
    from mine_compositional import candidate_conditions, pair_features
    from mine_mdd import relational_conditions
    from mine_views import VIEWS
    cid = {}; names = []; sid = [dict() for _ in VIEW_NAMES]; snames = [[] for _ in VIEW_NAMES]
    data = {}
    for split in ("train", "valid"):
        conds = []; lab = array("b"); doc = array("i"); sp = array("b"); sig = [array("i") for _ in VIEW_NAMES]
        docnames = []
        for line in io.open(GRAPH/f"{split}.jsonl", encoding="utf-8"):
            rec = json.loads(line); nd = rec["nodes"]; anch = defaultdict(set)
            for p in rec["anchored_pairs"]:
                for ra, rb in p["roles"]: anch[(p["a"], p["b"])].add((ra, rb))
            di = len(docnames); docnames.append(rec["doc_id"])
            s = split_of(rec["doc_id"]) if split == "train" else 3
            for e in rec["target_edges"]:
                a, b = e["s"], e["t"]; na, nb = nd.get(a), nd.get(b)
                if not na or not nb or na["kind"] != "event" or nb["kind"] != "event": continue
                sh = anch.get((a, b)) or anch.get((b, a)) or set()
                f = pair_features(na, nb, sh, bool(sh), frozenset())
                cs = list(candidate_conditions(f)) + relational_conditions(na, nb, sh)
                ids = array("i")
                for c in set(cs):
                    j = cid.get(c)
                    if j is None: j = cid[c] = len(names); names.append(c)
                    ids.append(j)
                conds.append(ids); lab.append(RELS.index(e["rel"])); doc.append(di); sp.append(s)
                for v, vn in enumerate(VIEW_NAMES):
                    sv = str(VIEWS[vn](f)); j = sid[v].get(sv)
                    if j is None: j = sid[v][sv] = len(snames[v]); snames[v].append(sv)
                    sig[v].append(j)
        data[split] = {"conds": conds, "lab": lab, "doc": doc, "sp": sp, "sig": sig, "docnames": docnames}
        log("  %s: %d cap EV-EV" % (split, len(lab)))
    data["cond_names"] = names; data["sig_names"] = snames
    with open(CACHE, "wb") as fh: pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)
    log("cache: %d dieu kien, %.0f MB" % (len(names), CACHE.stat().st_size/1e6))

# ---------------------------------------------------------------- worker side
G = {}
def write_split_caches(data):
    """Small per-split caches so each worker loads only the instances it works on."""
    for x in (0, 1, 2, 3):                       # DISCOVERY, CONF-1, CONF-2, valid
        T = data["train"] if x < 3 else data["valid"]
        keep = [i for i, s in enumerate(T["sp"]) if s == x]
        part = {"conds": [T["conds"][i] for i in keep], "lab": [T["lab"][i] for i in keep],
                "doc": [T["doc"][i] for i in keep], "sig": [[T["sig"][v][i] for i in keep] for v in range(len(VIEW_NAMES))]}
        with open(OUT/("cache_sp%d.pkl" % x), "wb") as fh: pickle.dump(part, fh, protocol=pickle.HIGHEST_PROTOCOL)

def init_worker(which):
    with open(OUT/("cache_sp%d.pkl" % which), "rb") as fh: G.update(pickle.load(fh))

def bitmasks(members, need=None, min_n=25):
    """Per condition, a Python-int bitset over the class-local positions of `members`."""
    conds = G["conds"]; cnt = Counter()
    for m in members:
        for c in conds[m]:
            if need is None or c in need: cnt[c] += 1
    keepc = {c for c, n in cnt.items() if n >= min_n}
    nbytes = (len(members) + 7)//8
    buf = {c: bytearray(nbytes) for c in keepc}
    for pos, m in enumerate(members):
        byte, bit = pos >> 3, 1 << (pos & 7)
        for c in conds[m]:
            b = buf.get(c)
            if b is not None: b[byte] |= bit
    return {c: int.from_bytes(b, "little") for c, b in buf.items()}

def lab_mask(members, r):
    nbytes = (len(members) + 7)//8; b = bytearray(nbytes)
    for pos, m in enumerate(members):
        if G["lab"][m] == r: b[pos >> 3] |= 1 << (pos & 7)
    return int.from_bytes(b, "little")

def docs_of(mask, members, cap=5):
    seen = set(); pos = 0
    while mask and len(seen) < cap:
        low = mask & -mask; p = low.bit_length() - 1
        seen.add(G["doc"][members[p]]); mask ^= low
    return len(seen)

def mine_unit(args):
    """One (view, label): exhaustive depth <= 2 inside every class of the view, on DISCOVERY."""
    from mine_compositional import log_binom_tail
    v, r = args
    byclass = defaultdict(list)
    for i, s in enumerate(G["sig"][v]): byclass[s].append(i)
    out = []
    for s, members in byclass.items():
        n_cls = len(members); k_cls = sum(1 for m in members if G["lab"][m] == r)
        if n_cls < 25 or k_cls < 8: continue
        p0 = k_cls / n_cls
        M = bitmasks(members); POS = lab_mask(members, r)
        single = {}
        for c, m in M.items():
            n = m.bit_count(); k = (m & POS).bit_count()
            if k >= 8: single[c] = (n, k)
        conds = sorted(single, key=lambda c: -single[c][1])
        def gate(key, n, k, parents):
            if n < 25 or k < 8 or (k/n) < 1.5*p0: return None
            if parents:
                dl = logit(k, n) - max(logit(pk, pn) for pn, pk in parents)
                if dl < 0.5: return None
            else: dl = 0.0
            return dl
        for c in conds:
            n, k = single[c]
            dl = gate((c,), n, k, None)
            if dl is not None and docs_of(M[c] & POS, members) >= 5:
                out.append((v, s, r, (c,), n, k, log_binom_tail(k, n, p0), p0))
        for i, a in enumerate(conds):
            ma = M[a] & POS; na_, ka = single[a]
            for b in conds[i+1:]:
                mk = ma & M[b]; k = mk.bit_count()
                if k < 8: continue
                n = (M[a] & M[b]).bit_count()
                dl = gate((a, b), n, k, (single[a], single[b]))
                if dl is None: continue
                if docs_of(mk, members) < 5: continue
                out.append((v, s, r, (a, b), n, k, log_binom_tail(k, n, p0), p0))
    return out

def confirm_unit(args):
    """Re-score the candidates of one view on the instances loaded in this worker."""
    v, cands = args
    byclass = defaultdict(list)
    for i, s in enumerate(G["sig"][v]): byclass[s].append(i)
    need_by_class = defaultdict(set)
    for (s, r, key) in cands: need_by_class[s].update(key)
    res = {}
    for s, need in need_by_class.items():
        members = byclass.get(s, [])
        if not members: continue
        M = bitmasks(members, need=need, min_n=1)
        LM = {r: lab_mask(members, r) for r in range(len(RELS))}
        for (s2, r, key) in cands:
            if s2 != s or any(c not in M for c in key): continue
            m = M[key[0]]
            for c in key[1:]: m &= M[c]
            res[(v, s, r, key)] = (m.bit_count(), (m & LM[r]).bit_count())
    return res

# ---------------------------------------------------------------- main
def main():
    NW = int(os.environ.get("NW", "6"))
    if not CACHE.exists() and os.environ.get("NOARG") and BASE_CACHE.exists():
        log("NOARG: bo moi dieu kien tu MAVEN-Arg va hai view anchor / anchor_sd ...")
        with open(BASE_CACHE, "rb") as fh: data = pickle.load(fh)
        drop = {i for i, n in enumerate(data["cond_names"]) if n[1] in ARG_ATTRS}
        for sp in ("train", "valid"):
            T = data[sp]; T["conds"] = [array("i", [c for c in cs if c not in drop]) for cs in T["conds"]]
            for v, vn in enumerate(VIEW_NAMES):
                if vn in ("anchor", "anchor_sd"): T["sig"][v] = array("i", [0]*len(T["lab"]))
        with open(CACHE, "wb") as fh: pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)
        log("  bo %d / %d dieu kien" % (len(drop), len(data["cond_names"]))); del data
    if not CACHE.exists() and SEED and BASE_CACHE.exists():
        log("seed %s: dung lai cache goc, chia lai train ..." % SEED)
        with open(BASE_CACHE, "rb") as fh: data = pickle.load(fh)
        T = data["train"]; dn = T["docnames"]
        T["sp"] = array("b", [split_of(dn[d]) for d in T["doc"]])
        with open(CACHE, "wb") as fh: pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)
        del data
    if not CACHE.exists():
        log("dung cache ..."); build_cache()
    with open(CACHE, "rb") as fh: data = pickle.load(fh)
    names = data["cond_names"]; snames = data["sig_names"]
    if not (OUT/"cache_sp3.pkl").exists(): write_split_caches(data)
    T = data["train"]; V = data["valid"]
    log("train: DISCOVERY %d, CONF-1 %d, CONF-2 %d cap; valid %d cap" % tuple(
        [sum(1 for s in T["sp"] if s == x) for x in (0, 1, 2)] + [len(V["lab"])]))
    if (OUT/"rules_confirmed.pkl").exists() and os.environ.get("REMINE") != "1":
        with open(OUT/"rules_confirmed.pkl", "rb") as fh: rules = pickle.load(fh)
        log("dung lai %d luat da xac nhan (dat REMINE=1 de mine lai)" % len(rules))
        select_and_test(data, rules, NW); return
    units = [(v, r) for v in range(len(VIEW_NAMES)) for r in range(1, len(RELS))]
    log("mine %d don vi (view, nhan) tren %d tien trinh ..." % (len(units), NW))
    cands = []
    with Pool(NW, initializer=init_worker, initargs=(0,)) as pool:
        for res in pool.imap_unordered(mine_unit, units):
            cands += res
            log("  +%d ung vien (tong %d)" % (len(res), len(cands)))
    # BH-FDR over all candidates
    cands.sort(key=lambda t: t[6]); m = len(cands); cut = 0
    for i, c in enumerate(cands, 1):
        if c[6] <= math.log(0.05*i/m): cut = i
    cands = cands[:cut]
    log("BH-FDR q=0.05: %d / %d ung vien giu lai; theo nhan %s" % (cut, m, dict(Counter(RELS[c[2]] for c in cands))))
    # confirmation on CONF-1, in parallel per view
    byview = defaultdict(list)
    for c in cands: byview[c[0]].append((c[1], c[2], c[3]))
    conf = {}
    with Pool(min(NW, len(byview)), initializer=init_worker, initargs=(1,)) as pool:
        for res in pool.imap_unordered(confirm_unit, list(byview.items())): conf.update(res)
    rules = []
    for (v, s, r, key, n, k, lp, p0) in cands:
        cn, ck = conf.get((v, s, r, key), (0, 0))
        if cn < 10: continue
        cw = wlb(ck, cn)
        if cw <= p0: continue
        rules.append({"view": VIEW_NAMES[v], "sig": snames[v][s], "v": v, "s": s, "rel": RELS[r], "key": key,
                      "conds": [list(names[c]) for c in key], "k": k, "n": n, "ck": ck, "cn": cn, "wlb": cw, "base": p0})
    log("sau xac nhan tren CONF-1: %d luat; theo nhan %s" % (len(rules), dict(Counter(x["rel"] for x in rules))))

    with open(OUT/"rules_confirmed.pkl", "wb") as fh: pickle.dump(rules, fh)
    select_and_test(data, rules, NW)

# ---------------------------------------------------------------- firing (parallel)
def init_fire(which):
    with open(OUT/("cache_sp%d.pkl" % which), "rb") as fh: G.update(pickle.load(fh))
    with open(OUT/"rules_confirmed.pkl", "rb") as fh: R = pickle.load(fh)
    idx = defaultdict(list)                        # (view, class, first condition) -> [(rule id, other conditions)]
    for rid, x in enumerate(R): idx[(x["v"], x["s"], x["key"][0])].append((rid, x["key"][1:]))
    G["ridx"] = idx

def fire_chunk(bounds):
    i0, i1 = bounds; out = []
    for i in range(i0, i1):
        cs = set(G["conds"][i]); hits = []
        for v in range(len(VIEW_NAMES)):
            s = G["sig"][v][i]
            for c in cs:
                for rid, rest in G["ridx"].get((v, s, c), ()):
                    if all(z in cs for z in rest): hits.append(rid)
        out.append(hits)
    return i0, out

def fire_all(which, n, NW):
    """Rule ids firing on every instance of one split, computed once, in parallel chunks."""
    chunks = [(i, min(n, i + 4000)) for i in range(0, n, 4000)]; res = [None]*n
    with Pool(NW, initializer=init_fire, initargs=(which,)) as pool:
        for i0, out in pool.imap_unordered(fire_chunk, chunks):
            res[i0:i0 + len(out)] = out
    return res

def select_and_test(data, rules, NW):
    """Choose the combiner on CONFIRMATION-2 from precomputed firing lists, then open valid once.

    Two combiners compete: max-norm (keep the top fraction of rules per label, score wlb/prior,
    emit when >= tau) and per-label precision floors (a rule may vote for its label only when its
    confirmation bound clears that label's floor; highest bound wins). The second exists because
    with 54k rules the prior-normalised score of an extremely rare label explodes: a BEGINS-ON rule
    with bound 0.01 already scores 23 against a prior of 0.044%."""
    T = data["train"]; V = data["valid"]
    prior = Counter(T["lab"][i] for i in range(len(T["lab"])) if T["sp"][i] == 0)
    tot = sum(prior.values()); PRIOR = {r: prior[r]/tot for r in range(len(RELS))}
    RL = [RELS.index(x["rel"]) for x in rules]; CW = [x["wlb"] for x in rules]
    with open(OUT/"cache_sp2.pkl", "rb") as fh: C2 = pickle.load(fh)
    log("tinh luat ban tren CONF-2 (%d cap) va valid (%d cap), %d tien trinh ..." % (len(C2["lab"]), len(V["lab"]), NW))
    F2 = fire_all(2, len(C2["lab"]), NW)
    log("  CONF-2 xong; trung binh %.0f luat ban / cap" % (sum(len(x) for x in F2)/len(F2)))
    FV = fire_all(3, len(V["lab"]), NW)
    log("  valid xong")
    g2 = list(C2["lab"]); gv = list(V["lab"])
    def macro(pred, gold):
        tp, fp, fn = Counter(), Counter(), Counter()
        for p, g in zip(pred, gold):
            if p == g: tp[g] += 1
            else: fp[p] += 1; fn[g] += 1
        per = {}
        for r in range(len(RELS)):
            P = tp[r]/(tp[r]+fp[r]) if tp[r]+fp[r] else 0; R_ = tp[r]/(tp[r]+fn[r]) if tp[r]+fn[r] else 0
            per[r] = (P, R_, 2*P*R_/(P+R_) if P+R_ else 0)
        return sum(x[2] for x in per.values())/6, per
    rank = {}
    for r in range(1, len(RELS)):
        ids = sorted((i for i in range(len(rules)) if RL[i] == r), key=lambda i: -CW[i])
        for j, i in enumerate(ids): rank[i] = (j + 1)/max(1, len(ids))
    def pred_maxnorm(F, frac, tau):
        out = []
        for hits in F:
            sc = {}
            for rid in hits:
                if rank[rid] > frac: continue
                v = CW[rid]/PRIOR[RL[rid]]
                if v > sc.get(RL[rid], 0): sc[RL[rid]] = v
            out.append(max(sc, key=sc.get) if sc and max(sc.values()) >= tau else 0)
        return out
    def pred_floor(F, TH):
        out = []
        for hits in F:
            best = None
            for rid in hits:
                r = RL[rid]
                if CW[rid] >= TH[r] and (best is None or CW[rid] > best[1]): best = (r, CW[rid])
            out.append(best[0] if best else 0)
        return out
    results = []
    for frac in (0.05, 0.1, 0.2, 0.3, 0.5, 1.0):
        for tau in (3, 5, 10, 20, 40, 80):
            m, _ = macro(pred_maxnorm(F2, frac, tau), g2); results.append((m, "max-norm", (frac, tau)))
    log("  max-norm tot nhat tren CONF-2: %.2f%% %s" % (100*max(results)[0], max(results)[2]))
    TH = {r: 9 for r in range(len(RELS))}; bestf = macro(pred_floor(F2, TH), g2)[0]
    for _ in range(3):
        for r in range(1, len(RELS)):
            for t in (0.1, 0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 9):
                T2 = dict(TH); T2[r] = t; m = macro(pred_floor(F2, T2), g2)[0]
                if m > bestf: bestf, TH = m, T2
    results.append((bestf, "nguong theo nhan", dict(TH)))
    log("  nguong theo nhan tren CONF-2: %.2f%% %s" % (100*bestf, {RELS[r][:4]: t for r, t in TH.items() if t < 9}))
    results.sort(key=lambda t: -t[0])
    m, nm, cfg = results[0]
    pv = pred_maxnorm(FV, *cfg) if nm == "max-norm" else pred_floor(FV, cfg)
    mv, per = macro(pv, gv)
    acc = sum(1 for p, g in zip(pv, gv) if p == g)/len(gv)
    print()
    print("=" * 100)
    print("BO LUAT EV-EV MINE LAI TREN TOAN BO TRAIN -- valid mo mot lan")
    print("=" * 100)
    print("  %d luat sau xac nhan; combiner chon tren CONF-2 (%.2f%%): %s %s" % (len(rules), 100*m, nm, cfg))
    print("  valid macro-F1 %.2f%%  accuracy %.2f%%   (257 luat cu: 25,60%%; 257 + 719 trigger: 26,15%%)" % (100*mv, 100*acc))
    for r in range(len(RELS)):
        print("    %-13s P %6.2f%%  R %6.2f%%  F1 %6.2f%%" % (RELS[r], 100*per[r][0], 100*per[r][1], 100*per[r][2]))
    # keys of valid EV-EV pairs in cache order, for later steps
    keys = []
    for line in io.open(GRAPH/"valid.jsonl", encoding="utf-8"):
        rec = json.loads(line); nd = rec["nodes"]
        for e in rec["target_edges"]:
            na, nb = nd.get(e["s"]), nd.get(e["t"])
            if not na or not nb or na["kind"] != "event" or nb["kind"] != "event": continue
            keys.append("%s|%s|%s" % (rec["doc_id"], e["s"], e["t"]))
    assert len(keys) == len(pv)
    json.dump({k: RELS[p] for k, p in zip(keys, pv)}, io.open(OUT/"pred_valid_full.json", "w", encoding="utf-8"))
    json.dump({"combiner": nm, "config": ({RELS[k]: v for k, v in cfg.items()} if isinstance(cfg, dict) else list(cfg)),
               "rules": [{k: x[k] for k in ("view", "sig", "rel", "conds", "k", "n", "ck", "cn", "wlb")} for x in rules]},
              io.open(ART/("rules_full%s.json" % SFX), "w", encoding="utf-8"), ensure_ascii=False, default=list)
    log("da luu rules_full.json va pred_valid_full.json; xong")


if __name__ == "__main__":
    main()
