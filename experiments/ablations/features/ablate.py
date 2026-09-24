"""Do the mined rules beat a plain classifier on the same KG features?

The reviewer question: is rule mining doing anything a softmax regression on event
types and roles would not? Five feature sets of growing richness are trained on
TRAIN-INNER (discovery + confirmation documents, never dev or valid) and compared
against the 257-rule library on the same valid split.

Sparse one-hot features, softmax regression by SGD, class-balanced loss so the
model is scored on the same macro-F1 objective the rules are. No numpy available,
so the maths is written out; features per pair are few (tens), which keeps it cheap.
"""
import sys, io, json, math, random, hashlib, time
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from pathlib import Path
from collections import Counter, defaultdict
import vote as V

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
R6 = V.RELATIONS
RI = {r: i for i, r in enumerate(R6)}

SETS = {
 "A types only":      lambda f: [("ta",f.get("type_a")),("tb",f.get("type_b")),
                                 ("tp",str(f.get("type_pair")))],
 "B +position":       None, "C +roles": None, "D all KG": None,
}

def feats(F, cs, which):
    """one-hot feature names for a pair under feature-set `which`.

    Scalars live under F["s"]; the set-valued attributes are already expanded into
    the condition set `cs` by the miner, so roles are read from there.
    """
    f = F["s"]
    out = [("ta", f.get("type_a")), ("tb", f.get("type_b")), ("tp", str(f.get("type_pair")))]
    if which in ("B", "C", "D"):
        out += [("or", f.get("order")), ("sd", f.get("sdist")),
                ("ba", f.get("bucket_a")), ("bb", f.get("bucket_b"))]
    if which in ("C", "D"):
        out += [("na", f.get("nrole_a")), ("nb", f.get("nrole_b")),
                ("sa", f.get("shares_anchor"))]
        for c in cs:
            if c[0] in ("HAS", "ALL") and c[1] in ("roleset_a","roleset_b","anchor_roles"):
                out.append((c[0]+":"+c[1], str(c[2])))
    if which == "D":
        for c in cs:
            if c[0] in ("HAS","ALL","CNT","MIX") or (c[0]=="EQ" and c[1] not in
               ("type_a","type_b","type_pair","order","sdist","bucket_a","bucket_b")):
                out.append((c[0]+":"+c[1], str(c[2])))
            elif c[0] == "REL":
                out.append(("REL:"+c[1], str(c[2])))
    return [f"{k}={v}" for k, v in out if v is not None]

def conf_doc(d): return int(hashlib.md5(d.encode()).hexdigest(),16) % 10 in (1,2,3)
def inner(d):    return not V.dev_doc(d)     # discovery + confirmation

print("loading ...", flush=True)
tr = V.load_rows(GRAPH/"train.jsonl", 400, keep=inner)
va = V.load_rows(GRAPH/"valid.jsonl", 0)
print(f"train-inner {len(tr):,}   valid {len(va):,}", flush=True)

def train_eval(which, epochs=3, lr=0.25, seed=0):
    X = [feats(f, cs, which) for _, f, cs in tr]
    y = [RI[r] for r, _, _ in tr]
    vocab = {}
    for row in X:
        for k in row: vocab.setdefault(k, len(vocab))
    Xi = [[vocab[k] for k in row] for row in X]
    # class weights: balance so macro-F1 is the objective, not accuracy
    cnt = Counter(y); n = len(y)
    w = {c: n/(len(R6)*cnt[c]) for c in cnt}
    W = [[0.0]*len(vocab) for _ in R6]; b = [0.0]*len(R6)
    rng = random.Random(seed); order = list(range(len(Xi)))
    for ep in range(epochs):
        rng.shuffle(order)
        for t, i in enumerate(order):
            idxs = Xi[i]
            z = [b[c] + sum(W[c][j] for j in idxs) for c in range(len(R6))]
            m = max(z); e = [math.exp(v-m) for v in z]; s = sum(e)
            p = [v/s for v in e]
            g = w[y[i]] * lr
            for c in range(len(R6)):
                d = g * ((1.0 if c == y[i] else 0.0) - p[c])
                if d:
                    b[c] += d
                    for j in idxs: W[c][j] += d
        print(f"    epoch {ep+1}/{epochs}", flush=True)
    # evaluate
    tp, fp, fn = Counter(), Counter(), Counter()
    for r, f, cs in va:
        idxs = [vocab[k] for k in feats(f, cs, which) if k in vocab]
        z = [b[c] + sum(W[c][j] for j in idxs) for c in range(len(R6))]
        pred = R6[max(range(len(R6)), key=lambda c: z[c])]
        if pred == r: tp[r]+=1
        else: fp[pred]+=1; fn[r]+=1
    per = {}
    for r in R6:
        P = tp[r]/(tp[r]+fp[r]) if tp[r]+fp[r] else 0.0
        R_ = tp[r]/(tp[r]+fn[r]) if tp[r]+fn[r] else 0.0
        per[r] = 2*P*R_/(P+R_) if P+R_ else 0.0
    acc = sum(tp.values())/len(va)
    return sum(per.values())/6, per, acc, len(vocab)

print(f"\n{'feature set':<24}{'#feat':>8}{'macro-F1':>10}{'acc':>8}   per-label F1")
print("-"*92)
for which, nm, ep, lr in (("D","D all KG (3ep)",3,0.25),("D","D all KG (10ep)",10,0.25),
                          ("D","D all KG (10ep lr.05)",10,0.05),("D","D all KG (20ep lr.05)",20,0.05)):
    t0=time.time()
    m, per, acc, nv = train_eval(which, epochs=ep, lr=lr)
    nz = " ".join(f"{r.split('-')[0][:4]} {100*per[r]:.0f}" for r in R6 if per[r]>0)
    print(f"{nm:<24}{nv:>8,}{100*m:>9.2f}%{100*acc:>7.2f}%   {nz}   ({time.time()-t0:.0f}s)", flush=True)
