# -*- coding: utf-8 -*-
"""Bai 1: do semantic signals the rule language never saw add anything to the 257 rules?

The 257 frozen rules are all 2-condition conjunctions over ~30 surface attributes (event
type, sentence position, role sets, entity types). Four sources of meaning were never in the
language:

  LEX   the trigger word itself (crude lemma: lower-case, suffix stripping -- no NLP library
        on this machine)
  DUR   a learned "container" lexicon: how often each trigger lemma (type as fallback) sits on
        the containing / contained side of a CONTAINS edge, from DISCOVERY gold only; bucketed
        hi / mid / lo against the global rate, plus which side of the pair contains more
  GRP   event types grouped by their argument FRAME (role and entity-type profile, k-means,
        k=12 and k=30). MAVEN's own type hierarchy is not on this machine; role frames are the
        closest legal substitute and use no temporal label
  CONN  connectives from the sentence text: between the two triggers (same sentence), in the
        3 tokens before each trigger, and at the start of the later sentence
  WEAK  MAVEN-ERE's SUBEVENT / CAUSE / PRECONDITION annotation between the two events. This is
        GOLD annotation of another layer (like EV-TX in context A): reported as a ceiling, not
        as a realistic result

Rules: depth 1 (one new condition) or depth 2 (new condition AND any condition), for
CONTAINS / SIMULTANEOUS / OVERLAP. Counting is done on positive instances only, then support
by posting-list intersection. Mined on DISCOVERY, confirmed on CONFIRMATION, tau chosen on
CONFIRMATION, VALID opened once. Two gates, as in the motif study:
  strict  confirmation Wilson bound must beat the 257-rule classifier's own precision
  lift    lift >= 2 and wlb/prior >= 1.5 on discovery, cwlb/prior >= 1.5, top 70% per label
Scores combine with the 257 rules under max-norm (wlb/prior), fallback BEFORE.
"""
import sys, io, json, math, re, hashlib, time, random
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V
from mine_compositional import candidate_conditions, pair_features
from mine_mdd import relational_conditions

T0 = time.time()
def log(*a): print("[%5.0fs] " % (time.time()-T0) + " ".join(str(x) for x in a), flush=True)

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
RAW = Path(r"C:\Reseach_Quang\MAVEN_ERE")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
LABS = ("CONTAINS", "SIMULTANEOUS", "OVERLAP")
PRIOR = {"BEFORE": .91045, "CONTAINS": .07430, "SIMULTANEOUS": .00862,
         "OVERLAP": .00597, "BEGINS-ON": .00044, "ENDS-ON": .00022}
Z = 1.959963985
def wlb(k, n):
    if n == 0: return 0.0
    p = k/n
    return (p + Z*Z/(2*n) - Z*math.sqrt(p*(1-p)/n + Z*Z/(4*n*n)))/(1 + Z*Z/n)
def split_of(doc): return "conf" if int(hashlib.md5(doc.encode()).hexdigest(), 16) % 10 < 4 else "disc"

CONN = set("""after before during while when whilst until till since following then later afterwards
afterward subsequently meanwhile as amid amidst prior eventually finally previously earlier once upon
throughout and but thereafter soon immediately simultaneously whereupon""".split())

def lemma(w):
    w = (w or "").lower().strip()
    for suf, rep in (("ies", "y"), ("ied", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("s", "")):
        if len(w) > len(suf) + 3 and w.endswith(suf): return w[:-len(suf)] + rep
    return w

# ---------------------------------------------------------------- load
def load(split, limit=0):
    raw = {}
    for i, line in enumerate(io.open(RAW/f"{split}.jsonl", encoding="utf-8")):
        if limit and i >= limit: break
        r = json.loads(line); raw[r["id"]] = r["tokens"]
    out = []
    for i, line in enumerate(io.open(GRAPH/f"{split}.jsonl", encoding="utf-8")):
        if limit and i >= limit: break
        rec = json.loads(line); nd = rec["nodes"]; anch = defaultdict(set)
        for p in rec["anchored_pairs"]:
            for ra, rb in p["roles"]: anch[(p["a"], p["b"])].add((ra, rb))
        weak = {}
        for e in rec["weak_edges"]: weak[(e["s"], e["t"])] = e["kind"]
        d = {"id": rec["doc_id"], "nd": nd, "tok": raw.get(rec["doc_id"], []), "ee": [], "input": rec["input_edges"]}
        for e in rec["target_edges"]:
            a, b = e["s"], e["t"]
            if nd.get(a, {}).get("kind") != "event" or nd.get(b, {}).get("kind") != "event": continue
            sh = anch.get((a, b)) or anch.get((b, a)) or set()
            f = pair_features(nd[a], nd[b], sh, bool(sh), frozenset())
            cs = frozenset(list(candidate_conditions(f)) + relational_conditions(nd[a], nd[b], sh))
            w = []
            if (a, b) in weak: w.append(("WEAK", weak[(a, b)], "ab"))
            if (b, a) in weak: w.append(("WEAK", weak[(b, a)], "ba"))
            d["ee"].append((a, b, e["rel"], cs, w)); d.setdefault("f", []).append(f)
        if d["ee"]: out.append(d)
    return out

log("nap du lieu ...")
TR = load("train"); VA = load("valid")
DISC = [d for d in TR if split_of(d["id"]) == "disc"]; CONF = [d for d in TR if split_of(d["id"]) == "conf"]
log("train %d doc (disc %d / conf %d), valid %d doc; cap: disc %d conf %d valid %d" % (
    len(TR), len(DISC), len(CONF), len(VA), sum(len(d["ee"]) for d in DISC),
    sum(len(d["ee"]) for d in CONF), sum(len(d["ee"]) for d in VA)))

# ---------------------------------------------------------------- 257-rule base scores
rules = V.load_rules(ART/"rules_rx_c70.json")
def base_scores(docs):
    allrows = [(None, f, cs) for d in docs for (_, _, _, cs, _), f in zip(d["ee"], d["f"])]
    idx = V.build_index(rules, allrows)
    it = iter(allrows)
    for d in docs:
        d["ps"] = []
        for _ in d["ee"]:
            _, f, cs = next(it)
            sc = {}
            for ri in V.firing(rules, idx, f, cs):
                ru = rules[ri]; v = ru["wlb"]/PRIOR[ru["rel"]]
                if v > sc.get(ru["rel"], 0): sc[ru["rel"]] = v
            d["ps"].append(sc)
base_scores(TR); base_scores(VA)

def predict(sc, tau): return max(sc, key=sc.get) if sc and max(sc.values()) >= tau else "BEFORE"
def prf(pred, gold):
    tp, fp, fn = Counter(), Counter(), Counter()
    for p, g in zip(pred, gold):
        if p == g: tp[g] += 1
        else: fp[p] += 1; fn[g] += 1
    per = {}
    for r in RELS:
        P = tp[r]/(tp[r]+fp[r]) if tp[r]+fp[r] else 0.0; R = tp[r]/(tp[r]+fn[r]) if tp[r]+fn[r] else 0.0
        per[r] = (P, R, 2*P*R/(P+R) if P+R else 0.0)
    return sum(v[2] for v in per.values())/6, per
gV = [e[2] for d in VA for e in d["ee"]]
m0, per0 = prf([predict(sc, 5) for d in VA for sc in d["ps"]], gV)
log("BASE 257 luat tren valid: macro-F1 %.2f%%" % (100*m0))
cp = Counter(); co = Counter()
for d in CONF:
    for e, sc in zip(d["ee"], d["ps"]):
        p = predict(sc, 5); cp[p] += 1; co[p] += (p == e[2])
CLF = {r: co[r]/cp[r] if cp[r] else 0.0 for r in LABS}
log("do chinh xac classifier tren conf: %s" % {r: "%.1f%%" % (100*v) for r, v in CLF.items()})

# ---------------------------------------------------------------- DUR lexicon (DISCOVERY gold only)
deg = Counter(); src = Counter(); tgt = Counter(); tdeg = Counter(); tsrc = Counter(); ttgt = Counter()
for d in DISC:
    nd = d["nd"]
    for (a, b, r, cs, w) in d["ee"]:
        la, lb = lemma(nd[a].get("trigger")), lemma(nd[b].get("trigger"))
        ta, tb = nd[a].get("type"), nd[b].get("type")
        deg[la] += 1; deg[lb] += 1; tdeg[ta] += 1; tdeg[tb] += 1
        if r == "CONTAINS": src[la] += 1; tgt[lb] += 1; tsrc[ta] += 1; ttgt[tb] += 1
G_SRC = sum(src.values())/max(1, sum(deg.values())); G_TGT = sum(tgt.values())/max(1, sum(deg.values()))
def rates(node):
    l, t = lemma(node.get("trigger")), node.get("type")
    if deg[l] >= 20: n, s, g = deg[l], src[l], tgt[l]
    else: n, s, g = tdeg[t], tsrc[t], ttgt[t]
    return (s + 20*G_SRC)/(n + 20), (g + 20*G_TGT)/(n + 20)
def bucket(x, g): return "hi" if x > 2*g else ("lo" if x < 0.5*g else "mid")
log("DUR: %d lemma co >=20 canh tren disc" % sum(1 for v in deg.values() if v >= 20))

# ---------------------------------------------------------------- GRP: role-frame clusters of event types
prof = defaultdict(Counter)
for d in TR:
    nd = d["nd"]
    for e in d["input"]:
        s = nd.get(e["s"], {})
        if s.get("kind") != "event": continue
        prof[s["type"]]["R:" + e["role"]] += 1
        t = nd.get(e["t"], {})
        if t.get("ent_type"): prof[s["type"]]["E:" + t["ent_type"]] += 1
    for k, v in nd.items():
        if v.get("kind") == "event": prof[v["type"]]["_n"] += 1
dims = sorted({k for c in prof.values() for k in c if k != "_n"})
def vec(t):
    c = prof[t]; n = max(1, c["_n"]); v = [c[k]/n for k in dims]
    s = math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/s for x in v]
TYPES = sorted(prof); VEC = {t: vec(t) for t in TYPES}
def kmeans(k, seed=0, it=50):
    rng = random.Random(seed); cent = [VEC[t][:] for t in rng.sample(TYPES, k)]; asg = {}
    for _ in range(it):
        new = {t: max(range(k), key=lambda j: sum(a*b for a, b in zip(VEC[t], cent[j]))) for t in TYPES}
        if new == asg: break
        asg = new
        for j in range(k):
            mem = [VEC[t] for t in TYPES if asg[t] == j]
            if mem: cent[j] = [sum(x)/len(mem) for x in zip(*mem)]
    return asg
GRP12 = kmeans(12); GRP30 = kmeans(30)
log("GRP: %d loai event, %d chieu khung vai tro" % (len(TYPES), len(dims)))
ex = defaultdict(list)
for t in TYPES: ex[GRP12[t]].append(t)
for j in sorted(ex)[:4]: log("   nhom %d: %s" % (j, ", ".join(ex[j][:8])))

# ---------------------------------------------------------------- per-pair new conditions
def new_conds(d, a, b, w):
    nd, tok = d["nd"], d["tok"]; A, B = nd[a], nd[b]
    out = {"LEX": [], "DUR": [], "GRP": [], "CONN": [], "WEAK": list(w)}
    la, lb = lemma(A.get("trigger")), lemma(B.get("trigger"))
    out["LEX"] += [("LEX", "a", la), ("LEX", "b", lb)]
    (sa_, ta_), (sb_, tb_) = rates(A), rates(B)
    out["DUR"] += [("DUR", "src_a", bucket(sa_, G_SRC)), ("DUR", "src_b", bucket(sb_, G_SRC)),
                   ("DUR", "tgt_a", bucket(ta_, G_TGT)), ("DUR", "tgt_b", bucket(tb_, G_TGT)),
                   ("DUR", "src_cmp", "a>>b" if sa_ > 2*sb_ else ("b>>a" if sb_ > 2*sa_ else "~"))]
    ga, gb = GRP12.get(A.get("type")), GRP12.get(B.get("type"))
    out["GRP"] += [("G12", "a", ga), ("G12", "b", gb), ("G12", "pair", (ga, gb)),
                   ("G30", "a", GRP30.get(A.get("type"))), ("G30", "b", GRP30.get(B.get("type")))]
    s1, s2 = A.get("sent_first"), B.get("sent_first"); t1, t2 = A.get("tok_first"), B.get("tok_first")
    if tok and s1 is not None and s2 is not None and t1 is not None and t2 is not None and s1 < len(tok) and s2 < len(tok):
        for nm, s, t in (("pre_a", s1, t1), ("pre_b", s2, t2)):
            for x in tok[s][max(0, t-3):t]:
                if x.lower() in CONN: out["CONN"].append(("CONN", nm, x.lower()))
        if s1 == s2:
            lo, hi = sorted((t1, t2))
            btw = {x.lower() for x in tok[s1][lo+1:hi] if x.lower() in CONN}
            for x in btw: out["CONN"].append(("CONN", "btw", x))
            if not btw: out["CONN"].append(("CONN", "btw", "-"))
        else:
            later = s2 if s2 > s1 else s1
            for x in tok[later][:2]:
                if x.lower() in CONN: out["CONN"].append(("CONN", "sinit", x.lower()))
    return out
for d in TR + VA:
    d["nc"] = [new_conds(d, a, b, w) for (a, b, r, cs, w) in d["ee"]]
log("dieu kien moi da dung")

# ---------------------------------------------------------------- mining
def conds_of(d, i, tracks):
    n = []
    for t in tracks: n += d["nc"][i][t]
    return n

def mine(tracks, gate):
    # positive-only enumeration on DISCOVERY
    kpos = defaultdict(Counter); kdoc = defaultdict(lambda: defaultdict(set))
    post = defaultdict(set); lab = []; j = 0
    for d in DISC:
        for i, (a, b, r, cs, w) in enumerate(d["ee"]):
            N = conds_of(d, i, tracks)
            for c in N: post[c].add(j)
            for c in cs: post[c].add(j)
            lab.append(r)
            if r in LABS:
                Nset = set(N)
                keys = {(c, None) for c in Nset}
                for c in Nset:
                    for x in cs: keys.add((c, x))
                    for x in Nset:
                        if repr(x) > repr(c): keys.add((c, x))
                for k in keys: kpos[r][k] += 1; kdoc[r][k].add(d["id"])
            j += 1
    def supp(key, P):
        c, x = key
        return P.get(c, set()) if x is None else (P.get(c, set()) & P.get(x, set()))
    cand = []
    for r in LABS:
        for key, k in kpos[r].items():
            if k < 10 or len(kdoc[r][key]) < 5: continue
            S = supp(key, post); n = len(S)
            if n < 30: continue
            w_ = wlb(k, n)
            ok = w_ > CLF[r] if gate == "strict" else ((k/n)/PRIOR[r] >= 2 and w_/PRIOR[r] >= 1.5)
            if ok: cand.append((key, r))
    # confirmation
    cpost = defaultdict(set); clab = []; j = 0
    need = {c for (key, r) in cand for c in key if c is not None}
    for d in CONF:
        for i, (a, b, r, cs, w) in enumerate(d["ee"]):
            for c in conds_of(d, i, tracks):
                if c in need: cpost[c].add(j)
            for c in cs:
                if c in need: cpost[c].add(j)
            clab.append(r); j += 1
    bylab = defaultdict(list)
    for key, r in cand:
        S = supp(key, cpost); cn = len(S)
        if cn < 10: continue
        cw = wlb(sum(1 for q in S if clab[q] == r), cn)
        if (cw > CLF[r]) if gate == "strict" else (cw/PRIOR[r] >= 1.5): bylab[r].append((cw, key))
    R = {}
    for r, lst in bylab.items():
        lst.sort(key=lambda t: -t[0])
        for cw, key in (lst if gate == "strict" else lst[:max(1, int(0.7*len(lst)))]):
            if key not in R or cw/PRIOR[r] > R[key][1]/PRIOR[R[key][0]]: R[key] = (r, cw)
    return R

def apply(R, docs, tracks, tau):
    byc = defaultdict(list)
    for (c, x), (r, cw) in R.items(): byc[c].append((x, r, cw/PRIOR[r]))
    pred = []; gold = []; ch = ok = 0
    for d in docs:
        for i, ((a, b, g, cs, w), sc0) in enumerate(zip(d["ee"], d["ps"])):
            sc = dict(sc0); N = conds_of(d, i, tracks); allc = set(cs) | set(N)
            for c in set(N):
                for x, r, v in byc.get(c, ()):
                    if (x is None or x in allc) and v > sc.get(r, 0): sc[r] = v
            p = predict(sc, tau); p0 = predict(sc0, 5)
            pred.append(p); gold.append(g)
            if p != p0: ch += 1; ok += (p == g)
    m, per = prf(pred, gold)
    return m, per, ch, ok

print()
print("=" * 110)
print("BAI 1 -- TRACK NGU NGHIA, cong vao 257 luat. Base valid macro-F1 %.2f%%" % (100*m0))
print("   base: " + "  ".join("%s P%.1f R%.1f F%.1f" % (r[:4], 100*per0[r][0], 100*per0[r][1], 100*per0[r][2]) for r in LABS))
print("=" * 110)
TRACKS = [("LEX", ["LEX"]), ("DUR", ["DUR"]), ("GRP", ["GRP"]), ("CONN", ["CONN"]),
          ("SEM = LEX+DUR+GRP+CONN", ["LEX", "DUR", "GRP", "CONN"]),
          ("WEAK (gold, tran)", ["WEAK"]), ("SEM + WEAK (gold, tran)", ["LEX", "DUR", "GRP", "CONN", "WEAK"])]
for gate in ("strict", "lift"):
    print()
    print(" cong %s" % gate)
    for nm, tr in TRACKS:
        R = mine(tr, gate)
        if not R:
            print("   %-26s 0 luat qua cong" % nm, flush=True); continue
        best = None
        for tau in (5, 10, 20, 40, 80):
            mc, _, _, _ = apply(R, CONF, tr, tau)
            if best is None or mc > best[0]: best = (mc, tau)
        m, per, ch, ok = apply(R, VA, tr, best[1])
        mb, _ = prf([predict(sc, best[1]) for d in VA for sc in d["ps"]], gV)
        labs = Counter(v[0] for v in R.values())
        print("   %-26s %4d luat (C%d S%d O%d) tau=%-2d macro %6.2f%% (%+.2f; base cung tau %.2f%%)  doi %5d dung %5.1f%%"
              % (nm, len(R), labs["CONTAINS"], labs["SIMULTANEOUS"], labs["OVERLAP"], best[1],
                 100*m, 100*(m-m0), 100*mb, ch, 100*ok/max(1, ch)), flush=True)
        print("      " + "  ".join("%s P%.1f R%.1f F%.1f" % (r[:4], 100*per[r][0], 100*per[r][1], 100*per[r][2]) for r in LABS))
        if gate == "strict" or nm.startswith("SEM ="):
            for key, (r, cw) in sorted(R.items(), key=lambda kv: -kv[1][1]/PRIOR[kv[1][0]])[:5]:
                print("        %-80s -> %-12s cwlb %.3f" % (str(key)[:80], r, cw))
log("xong")
