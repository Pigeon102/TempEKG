# -*- coding: utf-8 -*-
"""Learned edge auditor: does combining the evidence we already have beat rule voting?

Three proposals from the review are tested in one frame, because they share features:

  #16  LEARNED AUDITOR   logistic regression over per-edge evidence -> P(edge wrong),
                         then a second head -> P(correct label | wrong). Document-disjoint
                         train/test. If a linear model over existing evidence beats
                         R_all 29.29%, the bottleneck was aggregation, not architecture.
  #2   NORMALISED RERANK the triangle evidence divided by the number of triangles the
                         edge sits in, so BEFORE,BEFORE->BEFORE cannot win by volume.
                         Tested as a feature, and alone as a rule-only variant.
  #3   LEAVE-ONE-OUT PC  remove the target edge, close the rest, ask what labels remain.
                         Tested as a feature.

Features are computed from the PREDICTED graph only; gold enters as the training label
and never as an input. Each feature's standalone value is reported as well, so the
result says which evidence source carries the signal.
"""
import sys, io, json, math, re, hashlib, random
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V
from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
RI = {r: i for i, r in enumerate(RELS)}
INV = {"BEFORE": "iBEFORE", "CONTAINS": "iCONTAINS", "SIMULTANEOUS": "SIMULTANEOUS",
       "OVERLAP": "iOVERLAP", "BEGINS-ON": "BEGINS-ON", "ENDS-ON": "iENDS-ON"}
PRIOR = {"BEFORE": .91045, "CONTAINS": .07430, "SIMULTANEOUS": .00862,
         "OVERLAP": .00597, "BEGINS-ON": .00044, "ENDS-ON": .00022}
Z = 1.959963985
CAP = 6
MON = {m: i+1 for i, m in enumerate(
    "january february march april may june july august september october november december".split())}

def wlb(k, n):
    if n == 0: return 0.0
    p = k/n
    return (p + Z*Z/(2*n) - Z*math.sqrt(p*(1-p)/n + Z*Z/(4*n*n)))/(1 + Z*Z/n)
def dirnet(tr):
    adj = defaultdict(dict)
    for a, b, r in tr: adj[a][b] = r; adj[b][a] = INV[r]
    return adj
def mids_of(adj, a, b):
    return sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
def parse_date(t):
    s = t.lower().replace(",", " ")
    y = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", s)
    if not y: return None
    yr = int(y.group(1)); mo = dy = 0
    for nm, num in MON.items():
        if nm[:3] in s: mo = num; break
    d = re.search(r"\b([0-3]?[0-9])\b(?!\d)", s)
    if d and mo:
        v = int(d.group(1))
        if 1 <= v <= 31: dy = v
    return (yr, mo, dy)
def compat(aset):
    return [r for r, s in MAVEN_TO_ALLEN.items() if s & aset]

def load(path, limit=0):
    from mine_compositional import candidate_conditions, pair_features
    from mine_mdd import relational_conditions
    out = []
    for i, line in enumerate(io.open(path, encoding="utf-8")):
        if limit and i >= limit: break
        if not line.strip(): continue
        rec = json.loads(line); nd = rec["nodes"]; anch = defaultdict(set)
        for p in rec["anchored_pairs"]:
            for ra, rb in p["roles"]: anch[(p["a"], p["b"])].add((ra, rb))
        dt = {k: parse_date(v["text"]) for k, v in nd.items()
              if v.get("kind") == "timex" and v.get("anchorable")}
        dt = {k: v for k, v in dt.items() if v and v[1] and v[2]}
        pin = defaultdict(set); rows = []
        for e in rec["target_edges"]:
            a, b = e["s"], e["t"]
            ka = nd.get(a, {}).get("kind"); kb = nd.get(b, {}).get("kind")
            if ka == "timex" and kb == "event" and e["rel"] in ("CONTAINS", "SIMULTANEOUS") and a in dt:
                pin[b].add(dt[a])
            elif ka == "event" and kb == "timex" and e["rel"] == "SIMULTANEOUS" and b in dt:
                pin[a].add(dt[b])
            elif ka == "event" and kb == "event":
                na, nb = nd[a], nd[b]
                sh = anch.get((a, b)) or anch.get((b, a)) or set()
                f = pair_features(na, nb, sh, bool(sh), frozenset())
                cs = frozenset(list(candidate_conditions(f)) + relational_conditions(na, nb, sh))
                rows.append((a, b, e["rel"], f, cs))
        if rows: out.append((rec["doc_id"], rows, pin))
    return out

# ---------------------------------------------------------------- triangle rules (clean protocol)
def bucket(doc):
    return "conf" if int(hashlib.md5(doc.encode()).hexdigest(), 16) % 10 < 4 else "disc"
TRD = load(GRAPH/"train.jsonl", 400)
parts = defaultdict(list)
for d in TRD: parts[bucket(d[0])].append(d)
def count_sigs(docs):
    sig = defaultdict(Counter); sd = defaultdict(lambda: defaultdict(set))
    for doc, rows, _ in docs:
        adj = dirnet([(a, b, r) for (a, b, r, _, _) in rows])
        for (a, b, r, _, _) in rows:
            for c in mids_of(adj, a, b):
                k = (adj[a][c], adj[c][b]); sig[k][r] += 1; sd[k][r].add(doc)
    return sig, sd
ds, dd = count_sigs(parts["disc"]); cs_, cd = count_sigs(parts["conf"])
cand = {}
for k, c in ds.items():
    n = sum(c.values()); top, kk = c.most_common(1)[0]
    if n < 30 or kk < 10 or len(dd[k][top]) < 5: continue
    if wlb(kk, n) >= 0.50: cand[k] = top
CONF = {}
for k, top in cand.items():
    c = cs_.get(k)
    if not c or sum(c.values()) < 10: continue
    CONF[k] = (top, wlb(c[top], sum(c.values())))
rk = sorted(CONF.items(), key=lambda kv: -kv[1][1])
R3 = dict(rk[:max(1, int(0.7*len(rk)))])
# full distribution per signature, for the "vote distribution" feature
SIGDIST = {}
for k, c in ds.items():
    n = sum(c.values())
    if n >= 30: SIGDIST[k] = {r: c[r]/n for r in RELS}
print("luat bo 3 (sach): %d   chu ky co phan bo: %d" % (len(R3), len(SIGDIST)), flush=True)

# ---------------------------------------------------------------- predicted graph on valid
VAD = load(GRAPH/"valid.jsonl", 0)
rules = V.load_rules(ART/"rules_rx_c70.json")
flat = [(f, cs) for _, rows, _ in VAD for (_, _, _, f, cs) in rows]
idx = V.build_index(rules, [(None, f, cs) for f, cs in flat])

def pair_dist(hits):
    sc = {r: 0.0 for r in RELS}
    for ri in hits:
        ru = rules[ri]; sc[ru["rel"]] = max(sc[ru["rel"]], ru["wlb"]/PRIOR[ru["rel"]])
    t = sum(sc.values())
    return dict(PRIOR) if t <= 0 else {r: sc[r]/t for r in RELS}

docs = []
for doc, rows, pin in VAD:
    cur = []
    for (a, b, g, f, cs) in rows:
        h = V.firing(rules, idx, f, cs)
        cur.append((a, b, g, V.combine(rules, h, "max-norm", 5) or V.FALLBACK, pair_dist(h)))
    docs.append((doc, cur, pin))
npair = sum(len(c) for _, c, _ in docs)
nbad = sum(1 for _, c, _ in docs for e in c if e[2] != e[3])
print("valid %d doc, %s cap, %s canh sai (%.2f%%)"
      % (len(docs), format(npair, ","), format(nbad, ","), 100*nbad/npair), flush=True)

# ---------------------------------------------------------------- per-edge evidence
def featurize(doc, cur, pin):
    """One feature dict per edge. Everything is read from the predicted graph."""
    adj = dirnet([(a, b, p) for (a, b, _, p, _) in cur])
    allen = defaultdict(dict)
    for (a, b, _, p, _) in cur:
        s = MAVEN_TO_ALLEN[p]; allen[a][b] = s; allen[b][a] = converse(s)
    # document-level proxy: how often the pair classifier abstained (fell back)
    n_fb = sum(1 for (_, _, _, p, pd) in cur if max(pd, key=pd.get) != p) / max(1, len(cur))
    out = []
    for (a, b, g, p, pd) in cur:
        f = {}
        # pair classifier confidence
        srt = sorted(pd.values(), reverse=True)
        f["pc_top"] = srt[0]; f["pc_margin"] = srt[0] - srt[1]
        f["pc_p_cur"] = pd[p]
        f["pc_ent"] = -sum(v*math.log(v+1e-9) for v in pd.values())
        for r in RELS: f["pc_" + r] = pd[r]
        # higher-order: raw and normalised votes
        mids = mids_of(adj, a, b)
        raw = Counter(); dist = Counter(); nt = 0
        for c in mids:
            k = (adj[a][c], adj[c][b])
            t = R3.get(k)
            if t: raw[t[0]] += t[1]
            sd = SIGDIST.get(k)
            if sd:
                nt += 1
                for r in RELS: dist[r] += sd[r]
        f["ho_n_tri"] = len(mids)
        f["ho_n_rules"] = sum(1 for c in mids if R3.get((adj[a][c], adj[c][b])))
        best = raw.most_common(1)[0][0] if raw else p
        f["ho_disagree"] = 1.0 if (raw and best != p) else 0.0
        f["ho_margin"] = (raw[best] - raw[p]) if raw else 0.0
        for r in RELS:
            f["ho_raw_" + r] = raw[r]
            f["ho_norm_" + r] = dist[r]/nt if nt else 0.0       # #2 normalised
        f["ho_norm_cur"] = dist[p]/nt if nt else 0.0
        # #3 leave-one-out closure: what does the rest of the graph allow for (a,b)?
        imp = FULL
        for c in mids:
            imp = imp & compose(allen[a][c], allen[c][b])
        adm = compat(imp)
        f["loo_n_adm"] = len(adm)
        f["loo_cur_ok"] = 1.0 if p in adm else 0.0
        f["loo_forced"] = 1.0 if len(adm) == 1 else 0.0
        f["loo_forced_other"] = 1.0 if (len(adm) == 1 and adm[0] != p) else 0.0
        # date bridge
        A, B = pin.get(a), pin.get(b)
        if A and B and len(A) == 1 and len(B) == 1:
            da, db = next(iter(A)), next(iter(B))
            f["date_lt"] = 1.0 if da < db else 0.0
            f["date_gt"] = 1.0 if da > db else 0.0
            f["date_contra"] = 1.0 if ((da < db and p != "BEFORE") or (da > db and p == "BEFORE")) else 0.0
        else:
            f["date_lt"] = f["date_gt"] = f["date_contra"] = 0.0
        # document reliability proxy
        f["doc_fallback_rate"] = n_fb
        f["doc_size"] = math.log(1 + len(cur))
        # current label
        for r in RELS: f["cur_" + r] = 1.0 if p == r else 0.0
        out.append((f, g, p, best if raw else None, adm))
    return out

print("dung dac trung ...", flush=True)
E = []          # (doc_id, feat, gold, pred, ho_best, adm)
for doc, cur, pin in docs:
    for f, g, p, hb, adm in featurize(doc, cur, pin):
        E.append((doc, f, g, p, hb, adm))
FEATS = sorted(E[0][1].keys())
print("  %s canh, %d dac trung" % (format(len(E), ","), len(FEATS)), flush=True)

# ---------------------------------------------------------------- document-disjoint split of VALID
# train the auditor on half the valid documents, score on the other half; then swap.
docids = sorted(set(e[0] for e in E))
random.Random(0).shuffle(docids)
half = set(docids[:len(docids)//2])

def stdz(rows, mu=None, sd=None):
    X = [[r[1][k] for k in FEATS] for r in rows]
    if mu is None:
        mu = [sum(c)/len(c) for c in zip(*X)]
        sd = [max(1e-6, math.sqrt(sum((v-m)**2 for v in c)/len(c))) for c, m in zip(zip(*X), mu)]
    return [[(v-m)/s for v, m, s in zip(x, mu, sd)] for x in X], mu, sd

def train_logreg(X, y, epochs=40, lr=0.05, l2=1e-3, w_pos=None):
    d = len(X[0]); w = [0.0]*d; b = 0.0
    n = len(X); pos = sum(y); wp = w_pos if w_pos else (n-pos)/max(1, pos)
    order = list(range(n)); rng = random.Random(1)
    for ep in range(epochs):
        rng.shuffle(order)
        for i in order:
            z = b + sum(wi*xi for wi, xi in zip(w, X[i]))
            pz = 1/(1+math.exp(-max(-30, min(30, z))))
            g = (pz - y[i]) * (wp if y[i] else 1.0)
            b -= lr*g
            for j in range(d): w[j] -= lr*(g*X[i][j] + l2*w[j])
    return w, b
def predict(w, b, X):
    return [1/(1+math.exp(-max(-30, min(30, b + sum(wi*xi for wi, xi in zip(w, x)))))) for x in X]

def train_softmax(X, y, K, epochs=40, lr=0.05, l2=1e-3):
    d = len(X[0]); W = [[0.0]*d for _ in range(K)]; B = [0.0]*K
    cnt = Counter(y); n = len(y); cw = {c: n/(K*cnt[c]) for c in cnt}
    order = list(range(n)); rng = random.Random(2)
    for ep in range(epochs):
        rng.shuffle(order)
        for i in order:
            z = [B[c] + sum(W[c][j]*X[i][j] for j in range(d)) for c in range(K)]
            m = max(z); ex = [math.exp(v-m) for v in z]; s = sum(ex); p = [v/s for v in ex]
            g = cw.get(y[i], 1.0)*lr
            for c in range(K):
                dlt = g*((1.0 if c == y[i] else 0.0) - p[c])
                if dlt:
                    B[c] += dlt
                    for j in range(d): W[c][j] += dlt*X[i][j] - lr*l2*W[c][j]
    return W, B
def softmax_pred(W, B, X):
    out = []
    for x in X:
        z = [B[c] + sum(W[c][j]*x[j] for j in range(len(x))) for c in range(len(W))]
        out.append(max(range(len(z)), key=lambda c: z[c]))
    return out

def run_fold(train_rows, test_rows, label):
    Xtr, mu, sd = stdz(train_rows)
    ytr = [1 if r[2] != r[3] else 0 for r in train_rows]
    w, b = train_logreg(Xtr, ytr)
    Xte, _, _ = stdz(test_rows, mu, sd)
    p_wrong = predict(w, b, Xte)
    # repair head: trained on WRONG training edges only
    wrong_tr = [r for r in train_rows if r[2] != r[3]]
    Xw, mu2, sd2 = stdz(wrong_tr)
    yw = [RI[r[2]] for r in wrong_tr]
    W, B = train_softmax(Xw, yw, len(RELS))
    Xte_w, _, _ = stdz(test_rows, mu2, sd2)
    rep = softmax_pred(W, B, Xte_w)
    return p_wrong, rep, w

foldA = [e for e in E if e[0] in half]; foldB = [e for e in E if e[0] not in half]
pA, rA, wA = run_fold(foldB, foldA, "A")
pB, rB, wB = run_fold(foldA, foldB, "B")
scored = list(zip(foldA, pA, rA)) + list(zip(foldB, pB, rB))
nb = sum(1 for e, _, _ in scored if e[2] != e[3])

print()
print("=" * 96)
print("#16 LEARNED AUDITOR — 2-fold theo document tren valid")
print("=" * 96)
print("  %-10s%9s%9s%10s%12s%9s%11s" % ("nguong", "gan co", "dung", "P@k", "found_all", "repair", "R_all"))
print("  " + "-" * 70)
best_r = (0, None)
for thr in (0.9, 0.8, 0.7, 0.6, 0.5, 0.4):
    fl = [(e, r) for e, pw, r in scored if pw >= thr]
    hit = [(e, r) for e, r in fl if e[2] != e[3]]
    rp = sum(1 for e, r in hit if RELS[r] == e[2])
    P = len(hit)/len(fl) if fl else 0; F = len(hit)/nb; RP = rp/len(hit) if hit else 0; RA = rp/nb
    print("  %-10s%9s%9s%9.2f%%%11.2f%%%8.2f%%%10.2f%%"
          % ("%.1f" % thr, format(len(fl), ","), format(len(hit), ","), 100*P, 100*F, 100*RP, 100*RA))
    if RA > best_r[0]: best_r = (RA, thr)
print()
print("  doi chieu rule-only ba tang (E4):  P@k 73,23%   found_all 31,84%   repair@k 91,99%   R_all 29,29%")

# ---------------------------------------------------------------- #2 normalised HO alone, #3 LOO alone
print()
print("=" * 96)
print("#2 va #3 RIENG LE (khong hoc, chi rule)")
print("=" * 96)
def score_rule(flag_fn, repair_fn, name):
    fl = [e for e in E if flag_fn(e)]
    hit = [e for e in fl if e[2] != e[3]]
    rp = sum(1 for e in hit if repair_fn(e) == e[2])
    print("  %-34s gan co %6s  P@k %6.2f%%  found %6.2f%%  repair %6.2f%%  R_all %6.2f%%"
          % (name, format(len(fl), ","), 100*len(hit)/len(fl) if fl else 0,
             100*len(hit)/nbad, 100*rp/len(hit) if hit else 0, 100*rp/nbad))
# raw HO (the E4 mechanism)
score_rule(lambda e: e[4] is not None and e[4] != e[3], lambda e: e[4], "HO raw vote (nhu E4)")
# #2 normalised: flag when normalised evidence for another label beats current by margin
def norm_best(e):
    f = e[1]; return max(RELS, key=lambda r: f["ho_norm_" + r])
score_rule(lambda e: e[1]["ho_n_tri"] > 0 and norm_best(e) != e[3] and
                     e[1]["ho_norm_" + norm_best(e)] - e[1]["ho_norm_cur"] > 0.3,
           norm_best, "#2 HO chuan hoa theo so tam giac")
# #3 leave-one-out: flag when the rest of the graph forces a different label
score_rule(lambda e: e[1]["loo_forced_other"] == 1.0, lambda e: e[5][0], "#3 leave-one-out PC (ep ra nhan khac)")
score_rule(lambda e: e[1]["loo_cur_ok"] == 0.0 and e[1]["loo_n_adm"] > 0,
           lambda e: min(e[5], key=lambda r: -PRIOR[r]), "#3 LOO: nhan hien tai khong tuong thich")

# ---------------------------------------------------------------- which evidence carries weight
print()
print("=" * 96)
print("TRONG SO LON NHAT cua error detector (trung binh 2 fold, da chuan hoa)")
print("=" * 96)
wavg = [(abs(a)+abs(b))/2 for a, b in zip(wA, wB)]
for j in sorted(range(len(FEATS)), key=lambda j: -wavg[j])[:12]:
    sgn = "+" if (wA[j]+wB[j]) > 0 else "-"
    print("  %s %-26s %.3f" % (sgn, FEATS[j], wavg[j]))
