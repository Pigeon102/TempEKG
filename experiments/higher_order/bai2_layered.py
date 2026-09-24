# -*- coding: utf-8 -*-
"""Bai 2 on the layered design, auditing the layered Bai 1 classifier (30.83%) on all four edge
types.

The auditor is the layered miner with one more layer:
  GRAPH  motif signatures of the edge in the graph UNDER AUDIT (paths a-x-b and a-x-y-b through
         events and TIMEX, oriented labels on the path). In Bai 2 these neighbour labels are the
         observed graph, not something the auditor predicts.
Instances are partitioned by (edge type, CURRENT label): inside a partition the miner learns what
that current label really is, i.e. which of its instances are wrong and what they should be.

  A  GRAPH layer only                      (the unified-graph auditor, rebuilt in this frame)
  B  all layers + GRAPH, cross-layer rules
  C  all layers without GRAPH              (how much the graph itself adds)
Each auditor overrides the current label when its best firing rule clears a per-label floor;
floors chosen by NET error reduction or by MACRO-F1.

Noise:
  N1  classifier noise: the whole graph as the layered classifier predicted it. The classifier
      learnt on DISCOVERY (rules) and CONFIRMATION (checks), so audit rules are mined on
      CONFIRMATION-2 (halves 2a mine / 2b confirm), floors chosen on CONFIRMATION-1, valid once
  N2  injected noise on all four edge types at 10% and 20% (fake_data generator per edge type):
      mined on DISCOVERY, confirmed on CONFIRMATION-1, floors on CONFIRMATION-2, valid once
First 400 train documents excluded throughout.
"""
import io, os, json, random, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_L = io.open(HERE/"layered_rules.py", encoding="utf-8").read()
exec(SRC_L[:SRC_L.index("FINAL = {}")])
SMOKE = os.environ.get("SMOKE") == "1"
PL = json.load(io.open(ART/("pred_layered%s.json" % os.environ.get("TAG", "")), encoding="utf-8"))
SYMM = {"SIMULTANEOUS", "BEGINS-ON"}
def inv_(l): return l if l in SYMM else ("i" + l)
CAP = 4

DOCS = {d["id"]: d for d in TR + VA}
BYDOC = defaultdict(list)
for x in ITR + IVA:
    x["key"] = "%s|%s|%s" % (x["doc"], x["a"], x["b"])
    x["n1"] = PL.get(x["key"], x["p"])
    BYDOC[x["doc"]].append(x)
if SMOKE:
    keep = set(list(BYDOC)[:250]) | {d["id"] for d in VA[:60]}
    ITR = [x for x in ITR if x["doc"] in keep]; IVA = [x for x in IVA if x["doc"] in keep]
    BYDOC = {k: v for k, v in BYDOC.items() if k in keep}

# ---------------------------------------------------------------- motif structure (labels read later)
def structure(docid):
    d = DOCS[docid]; xs = BYDOC[docid]
    nbr = defaultdict(set)
    for x in xs: nbr[x["a"]].add(x["b"]); nbr[x["b"]].add(x["a"])
    K = {n: ("E" if v.get("kind") == "event" else "T") for n, v in d["nd"].items() if v.get("kind") in ("event", "timex")}
    for x in xs:
        a, b = x["a"], x["b"]; Na = nbr[a] - {a, b}; Nb = nbr[b] - {a, b}
        byf = defaultdict(list)
        for m in Na & Nb: byf[x["k"] + "3" + K[m]].append((m,))
        for m in Na:
            for y in nbr[m] & Nb:
                if y != m: byf[x["k"] + "4" + K[m] + K[y]].append((m, y))
        x["inst"] = [(f, nodes) for f, lst in byf.items() for nodes in sorted(lst)[:CAP]]
log("dung cau truc motif ...")
for docid in BYDOC: structure(docid)
log("xong cau truc")

def set_graph(field):
    """GRAPH layer from the labels in x[field] of every edge of the document."""
    for docid, xs in BYDOC.items():
        L = {}
        for x in xs:
            v = x[field]; L[(x["a"], x["b"])] = v; L[(x["b"], x["a"])] = inv_(v)
        for x in xs:
            a, b = x["a"], x["b"]; s = set()
            for f, nodes in x["inst"]:
                if len(nodes) == 1: s.add((f, L[(a, nodes[0])], L[(nodes[0], b)]))
                else: s.add((f, L[(a, nodes[0])], L[(nodes[0], nodes[1])], L[(nodes[1], b)]))
            x["L"]["GRAPH"] = frozenset(s)

# ---------------------------------------------------------------- the auditor
def mine_keys2(disc, c1, keyfun, prior, majority):
    """mine_keys with a gate that adapts to the partition's base rate. Inside a partition
    (edge type, current label) the label to restore can be the MAJORITY of the partition --
    60% of the classifier's EV-EV CONTAINS are really BEFORE -- where 'lift >= 2' demands a
    precision above 100% and no rule can pass. Here a rule must reach
    k/n >= min(2*prior, (1+prior)/2) with a Wilson bound above the prior on DISCOVERY, and a
    confirmation bound above the prior."""
    kpos = defaultdict(Counter); kdoc = defaultdict(lambda: defaultdict(set)); post = defaultdict(set)
    for j, x in enumerate(disc):
        atoms, keys = keyfun(x)
        for c in atoms: post[c].add(j)
        if x["g"] != majority:
            for key in keys: kpos[x["g"]][key] += 1; kdoc[x["g"]][key].add(x["doc"])
    def supp(key, P):
        S = P.get(key[0], set())
        for c in key[1:]: S = S & P.get(c, set())
        return S
    cand = []
    for r in kpos:
        pr_ = prior.get(r, 0)
        if pr_ == 0: continue
        need = min(2*pr_, (1 + pr_)/2)
        for key, kk in kpos[r].items():
            if kk < 10 or len(kdoc[r][key]) < 5: continue
            n = len(supp(key, post))
            if n < 30 or kk/n < need or wlb(kk, n) <= pr_: continue
            cand.append((key, r))
    needc = {c for key, _ in cand for c in key}; cpost = defaultdict(set)
    for j, x in enumerate(c1):
        atoms, _ = keyfun(x, need_only=needc)
        for c in atoms: cpost[c].add(j)
    out = defaultdict(list)
    for key, r in cand:
        S = supp(key, cpost)
        if len(S) < 10: continue
        cw = wlb(sum(1 for q in S if c1[q]["g"] == r), len(S))
        if cw > prior[r]: out[r].append((cw, key))
    for r in out: out[r].sort(key=lambda t: -t[0])
    return out

def classify_k(idx, TH, xs, field):
    out = []
    for x in xs:
        best = None
        for c in x["act"]:
            for key, r, cw in idx.get(c, ()):
                if cw >= TH.get((x["k"], r), 9) and all(z in x["act"] for z in key[1:]) and (best is None or cw > best[1]): best = (r, cw)
        out.append(best[0] if best else x[field])
    return out

def audit_rules(mine_set, conf_set, field, layers, cross):
    """Per partition (edge type, current label): stage A per layer, optional stage B across layers.
    Returns {partition: (PAT, rules)} with pattern ids namespaced by partition."""
    out = {}
    parts = defaultdict(list); cparts = defaultdict(list)
    for x in mine_set: parts[(x["k"], x[field])].append(x)
    for x in conf_set: cparts[(x["k"], x[field])].append(x)
    for part, disc_ in parts.items():
        c1_ = cparts.get(part, [])
        if len(disc_) < 200 or len(c1_) < 50: continue
        cur = part[1]
        pr_ = Counter(x["g"] for x in disc_); prior_ = {r: pr_[r]/len(disc_) for r in RELS if pr_[r]}
        if all(r == cur for r in prior_): continue
        PAT = {}
        for ly in layers:
            res = mine_keys2(disc_, c1_, layer_keyfun(ly), prior_, cur)
            for r, lst in res.items():
                for cw, key in lst[:150]: PAT[(part, ly) + key] = (ly, key, r, cw)
        rules = [((pid,), PAT[pid][2], PAT[pid][3]) for pid in PAT]
        if cross and PAT:
            byatom = defaultdict(list)
            for pid, (ly, key, r, cw) in PAT.items(): byatom[(ly, key[0])].append(pid)
            def act(x):
                byl = defaultdict(list)
                for ly, atoms in x["L"].items():
                    if ly not in layers: continue
                    for c in atoms:
                        for pid in byatom.get((ly, c), ()):
                            if all(z in atoms for z in PAT[pid][1]): byl[ly].append((PAT[pid][3], pid))
                o = []
                for ly, lst in byl.items(): o += [pid for cw, pid in sorted(set(lst), key=lambda t: -t[0])[:3]]
                return frozenset(o)
            for x in disc_ + c1_: x["_act"] = act(x)
            def ck(x, need_only=None):
                A = sorted(x["_act"], key=repr)
                if need_only is not None: return [c for c in A if c in need_only], []
                keys = []
                for i in range(len(A)):
                    for j in range(i+1, len(A)):
                        if A[i][1] == A[j][1]: continue
                        keys.append((A[i], A[j]))
                        for l in range(j+1, len(A)):
                            if A[l][1] in (A[i][1], A[j][1]): continue
                            keys.append((A[i], A[j], A[l]))
                return A, keys
            CR = mine_keys2(disc_, c1_, ck, prior_, cur)
            rules += [(key, r, cw) for r, lst in CR.items() for cw, key in lst]
        out[part] = (PAT, rules)
    return out

def activate(xs, AR, field, layers):
    """Active pattern ids of each instance under its own partition's patterns (all that fire)."""
    for x in xs:
        part = (x["k"], x[field]); pr_ = AR.get(part)
        if not pr_: x["act"] = frozenset(); continue
        PAT = pr_[0]; a = set()
        for pid, (ly, key, r, cw) in PAT.items():
            if ly in layers and all(c in x["L"].get(ly, ()) for c in key): a.add(pid)
        x["act"] = frozenset(a)

def rule_index(AR):
    byf = defaultdict(list)
    for part, (PAT, rules) in AR.items():
        for key, r, cw in rules: byf[key[0]].append((key, r, cw))
    return byf

def score(xs, finals, field):
    c = Counter()
    for x, f in zip(xs, finals):
        s = x[field]; g = x["g"]; c["n"] += 1; c["bad0"] += (s != g); c["bad1"] += (f != g)
        if f != s:
            c["flag"] += 1
            if s != g: c["hit"] += 1; c["fix"] += (f == g)
            else: c["brk"] += 1
    P = c["hit"]/max(1, c["flag"]); R = c["hit"]/max(1, c["bad0"]); F = 2*P*R/(P+R) if P+R else 0
    m = prf(finals, [x["g"] for x in xs])[0]
    return c, P, R, F, m

def tune(idx, xs, field, objective):
    """Floors per (edge type, label), coordinate ascent on the tuning set."""
    keys = sorted({(x["k"], r) for x in xs for c in x["act"] for _, r, _ in idx.get(c, ())})
    TH = {k: 9 for k in keys}
    def val(T):
        fin = classify_k(idx, T, xs, field); c, P, R, F, m = score(xs, fin, field)
        return (c["bad0"] - c["bad1"]) if objective == "net" else m
    best = val(TH)
    for _ in range(2):
        for k in keys:
            for t in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 9):
                T2 = dict(TH); T2[k] = t; v = val(T2)
                if v > best: best, TH = v, T2
    return TH

def show(nm, xs, field, finals):
    c, P, R, F, m = score(xs, finals, field)
    m0 = prf([x[field] for x in xs], [x["g"] for x in xs])[0]
    cells = []
    for k, lab in (("EE", "EV-EV"), ("ET", "EV>TX"), ("TE", "TX>EV"), ("TT", "TX-TX")):
        idx = [i for i, x in enumerate(xs) if x["k"] == k]
        b0 = sum(1 for i in idx if xs[i][field] != xs[i]["g"]); b1 = sum(1 for i in idx if finals[i] != xs[i]["g"])
        cells.append("%s %.1f->%.1f" % (lab, 100*b0/max(1, len(idx)), 100*b1/max(1, len(idx))))
    print("  %-34s P %6.2f%% R %6.2f%% F1 %6.2f%%  sua %6d hong %5d rong %+6d  loi %5.2f%% -> %5.2f%%  macro %6.2f%% -> %6.2f%%"
          % (nm, 100*P, 100*R, 100*F, c["fix"], c["brk"], c["bad0"]-c["bad1"], 100*c["bad0"]/c["n"], 100*c["bad1"]/c["n"], 100*m0, 100*m), flush=True)
    print("      loi theo loai: " + "   ".join(cells))

OBS = ("ONT", "ARG", "DISC", "LEX", "TIME")
AUDITORS = (("A: chi GRAPH", ("GRAPH",), False), ("B: moi tang + GRAPH, lien tang", OBS + ("GRAPH",), True),
            ("C: moi tang, khong GRAPH", OBS, True))

def scenario(title, field, mine_set, conf_set, tune_set, test_set):
    print()
    print(title)
    print("  %-34s loi %.2f%%  macro %.2f%%" % ("do thi dang kiem toan", 100*sum(1 for x in test_set if x[field] != x["g"])/len(test_set),
                                             100*prf([x[field] for x in test_set], [x["g"] for x in test_set])[0]))
    for nm, layers, cross in AUDITORS:
        log("  %s: mine ..." % nm)
        AR = audit_rules(mine_set, conf_set, field, layers, cross)
        idx = rule_index(AR)
        activate(tune_set + test_set, AR, field, layers)
        for obj in ("net", "macro"):
            TH = tune(idx, tune_set, field, obj)
            fin = classify_k(idx, TH, test_set, field)
            show("%s | %s" % (nm, "giam loi" if obj == "net" else "macro-F1"), test_set, field, fin)

print()
print("=" * 130)
print("BAI 2 -- KIEM TOAN THEO TANG (+ tang GRAPH) TREN CLASSIFIER TANG 30,83%, CA BON LOAI CANH (valid mo mot lan)")
print("=" * 130)

# ---------------------------------------------------------------- N1 classifier noise
def half(docid): return int(hashlib.md5(("s3" + docid).encode()).hexdigest(), 16) % 2
c2a = [x for x in ITR if x["sp"] == "conf2" and half(x["doc"]) == 0]
c2b = [x for x in ITR if x["sp"] == "conf2" and half(x["doc"]) == 1]
c1s = [x for x in ITR if x["sp"] == "conf1"]
set_graph("n1")
scenario("N1 -- nhieu classifier (do thi do classifier tang du doan)", "n1", c2a, c2b, c1s, IVA)

# ---------------------------------------------------------------- N2 injected noise, all four types
prior_k = defaultdict(Counter)
for x in ITR: prior_k[x["k"]][x["g"]] += 1
def corrupt(xs, rho, seed, field):
    rng = random.Random(seed)
    for x in xs:
        g = x["g"]
        if rng.random() < rho:
            labs = [r for r in prior_k[x["k"]] if r != g]
            x[field] = rng.choices(labs, [prior_k[x["k"]][r] for r in labs])[0]
        else: x[field] = g
discs = [x for x in ITR if x["sp"] == "disc"]; c2s = [x for x in ITR if x["sp"] == "conf2"]
for rho in (0.10, 0.20):
    corrupt(ITR, rho, 31, "nz"); corrupt(IVA, rho, 37, "nz")
    set_graph("nz")
    scenario("N2 -- nhieu bom %.0f%% tren ca bon loai canh" % (100*rho), "nz", discs, c1s, c2s, IVA)
log("xong")
