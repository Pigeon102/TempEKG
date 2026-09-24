# -*- coding: utf-8 -*-
"""Follow-up to fake_and_b.py. Two findings to act on:

 1. On fake_data every rule auditor breaks ~6,000 correct edges at EVERY noise rate. The
    rules override an edge whenever its signature's majority disagrees, whatever the prior
    chance that the edge is wrong. At 5% noise that makes the net change negative.
    -> Bayes auditor: combine what the signatures say about the true label with a model of
       how the layer under audit was corrupted (the noise channel):
            post(r) ~ P(r | signatures) * P(observed p | true r)
       P(r | signatures): geometric mean over the edge's signatures of the smoothed gold label
       distribution mined on DISCOVERY (no overconfidence from correlated signatures).
       Channel for fake_data: known generator at rate rho (relabel to the marginal without
       gold). Flag when the best r != p beats p by a log-odds margin.
 2. In context B the noise-conditioned rules (B1) won on valid but lost on CONFIRMATION,
    because the 257-rule predictions on train documents are IN-SAMPLE (9.28% error vs 12.13%
    on valid): the rules learnt the wrong error distribution.
    -> Cross-fit on valid: 2 folds by document hash; everything learnt from the classifier's
       errors (B1 rules, Bayes channel, margins) comes from the other fold, which is
       out-of-sample for the classifier; the test fold is scored once. Totals are summed.
"""
import sys, io, math, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_FB = io.open(HERE/"fake_and_b.py", encoding="utf-8").read()
MK = "# ================================================================ F: fake_data"
exec(SRC_FB[:SRC_FB.index(MK)])
src2 = SRC_FB[SRC_FB.index(MK):SRC_FB.index('print("F -- FAKE_DATA')]
exec(src2)                                    # fake_start, rel_sim

ALPHA = 2.0
def sig_dist(pairs, nmin=30):
    cnt = defaultdict(Counter)
    for d, S in pairs:
        for e, s in zip(d["ee"], S):
            for x in set(s): cnt[x][e[2]] += 1
    D = {}
    for x, c in cnt.items():
        n = sum(c.values())
        if n >= nmin:
            D[x] = {r: math.log((c[r] + ALPHA*PRIOR[r])/(n + ALPHA)) for r in RELS}
    return D
SD = sig_dist(zip(DISC, dG))
log("Bayes: %d chu ky co phan phoi (disc, gold)" % len(SD))

def chan_fake(rho):
    return {p: {r: math.log(1-rho) if p == r else math.log(rho*PRIOR[p]/(1-PRIOR[r])) for r in RELS} for p in RELS}
def chan_counts(cm):
    """cm[(p, r)] = count of observed p with gold r."""
    out = {}
    for r in RELS:
        n = sum(cm[(p, r)] for p in RELS)
        for p in RELS:
            out.setdefault(p, {})[r] = math.log((cm[(p, r)] + 0.5)/(n + 3.0))
    return out
def bayes(logC, margin):
    def f(d, cur, S):
        out = []
        for i, s in enumerate(S):
            xs = [x for x in set(s) if x in SD]
            if not xs: continue
            p = cur[i]
            post = {r: sum(SD[x][r] for x in xs)/len(xs) + logC[p][r] for r in RELS}
            r = max(post, key=post.get)
            if r != p and post[r] - post[p] > margin: out.append((i, r))
        return out
    return f

def simulate(docs, rate, seed=1):
    rng = random.Random(seed); out = []
    for d in docs:
        lab = []
        for e in d["ee"]:
            g = e[2]
            if rng.random() < rate:
                labs = [r for r in RELS if r != g]
                lab.append(rng.choices(labs, [PRIOR[r] for r in labs])[0])
            else: lab.append(g)
        out.append(lab)
    return out

MARG = (-1.0, 0.0, 1.0, 2.0, 3.0)
RS_ = {}
print()
print("=" * 118)
print("F2 -- FAKE_DATA, BOI CANH A: auditor Bayes voi kenh nhieu; margin chon tren CONFIRMATION mo phong cung ty le")
print("=" * 118)
set_pins(VA, "A"); set_pins(CONF, "A")
gold0 = [[e[2] for e in d["ee"]] for d in VA]
S0 = [sigs_L(d, lab_ctx(d, st, "A")) for d, st in zip(VA, gold0)]
print()
print("do thi SACH (0% nhieu) -- nen bao dong gia:")
show("OLD (21 luat)", net(VA, S0, [("o", ho_old(OLD))], gold0))
show("NEW rel=clf", net(VA, S0, [("n", ho_r(NEWc, REL))], gold0))
show("closure", net(VA, S0, [("c", closure_layer)], gold0))
for rho in (0.05, 0.20):
    show("Bayes gia dinh rho=%.2f, margin 0" % rho, net(VA, S0, [("b", bayes(chan_fake(rho), 0.0))], gold0))

VS = {}
for tag, rate in (("r05", .05), ("r10", .10), ("r15", .15), ("r20", .20)):
    start, used, nch = fake_start(tag)
    S = [sigs_L(d, lab_ctx(d, st, "A")) for d, st in zip(VA, start)]
    VS[tag] = (start, S, rate)
    simC = simulate(CONF, rate)
    SC = [sigs_L(d, lab_ctx(d, st, "A")) for d, st in zip(CONF, simC)]
    best = None
    for m in MARG:
        r = net(CONF, SC, [("b", bayes(chan_fake(rate), m))], simC)
        if best is None or r["nbad"]-r["left"] > best[0]: best = (r["nbad"]-r["left"], m)
    M = best[1]
    RS = rel_sim(rate); NEWs = mine_new_r(set(FAMS), RS)
    print()
    print("muc %s -- margin chon tren conf mo phong: %.1f" % (tag, M))
    show("OLD (21 luat)", net(VA, S, [("o", ho_old(OLD))], start))
    show("NEW rel=sim", net(VA, S, [("n", ho_r(NEWs, RS))], start))
    show("closure", net(VA, S, [("c", closure_layer)], start))
    show("Bayes margin 0 (khong tune)", net(VA, S, [("b", bayes(chan_fake(rate), 0.0))], start))
    show("Bayes margin %.1f (chon tren conf)" % M, net(VA, S, [("b", bayes(chan_fake(rate), M))], start))
    show("Bayes m%.1f -> closure" % M, net(VA, S, [("b", bayes(chan_fake(rate), M)), ("c", closure_layer)], start))

print()
print("Do nhay voi ty le nhieu GIA DINH (margin 0), giam rong:")
print("  %-10s" % "that \\ gia" + "".join("%12s" % ("rho=%.2f" % a) for a in (0.02, 0.05, 0.10, 0.20, 0.30)))
for tag, (start, S, rate) in VS.items():
    cells = []
    for a in (0.02, 0.05, 0.10, 0.20, 0.30):
        r = net(VA, S, [("b", bayes(chan_fake(a), 0.0))], start)
        cells.append("%+12d" % (r["nbad"]-r["left"]))
    print("  %-10s" % ("%.0f%%" % (100*rate)) + "".join(cells), flush=True)

# ================================================================ B: cross-fit on valid
print()
print("=" * 118)
print("B3 -- BOI CANH B, CROSS-FIT tren valid (2 fold theo hash doc; moi thu hoc tu fold kia)")
print("=" * 118)
set_pins(VA, "B")
startV = [list(d["pp"]) for d in VA]
vN = [sigs_L(d, lab_ctx(d, st, "B")) for d, st in zip(VA, startV)]
fold = [int(hashlib.md5(("cf" + d["id"]).encode()).hexdigest(), 16) % 2 for d in VA]
sub = [int(hashlib.md5(("in" + d["id"]).encode()).hexdigest(), 16) % 2 for d in VA]

def mine_cond_on(idx, nmin=20, kmin=5, dmin=3):
    cnt = defaultdict(Counter); dd = defaultdict(lambda: defaultdict(set))
    for j in idx:
        d = VA[j]
        for (a, b, g, f, cs), s, p in zip(d["ee"], vN[j], startV[j]):
            for x in set(s):
                cnt[(x, p)][g] += 1; dd[(x, p)][g].add(d["id"])
    R = {}
    for key, c in cnt.items():
        n = sum(c.values())
        if n < nmin: continue
        p = key[1]; t = {p: wlb(c[p], n)}
        alts = {r: wlb(k, n) for r, k in c.items() if r != p and k >= kmin and len(dd[key][r]) >= dmin}
        if alts: t.update(alts); R[key] = t
    return R
def sub_net(idx, layers):
    return net([VA[j] for j in idx], [vN[j] for j in idx], layers, [startV[j] for j in idx])
def tail():
    return [("o", ho_old(OLD)), ("c", closure_layer), ("d", date_layer)]

tot = defaultdict(lambda: Counter())
for k in (0, 1):
    trn = [j for j in range(len(VA)) if fold[j] != k]; tst = [j for j in range(len(VA)) if fold[j] == k]
    # B1: mine on one half of the training fold, choose margin on the other half, re-mine on all of it
    tA = [j for j in trn if sub[j] == 0]; tB = [j for j in trn if sub[j] == 1]
    RA = mine_cond_on(tA); best = None
    for m in (0.0, 0.05, 0.10, 0.20, 0.30):
        r = sub_net(tB, [("b1", ho_cond(RA, m))])
        if best is None or r["nbad"]-r["left"] > best[0]: best = (r["nbad"]-r["left"], m)
    M1 = best[1]; R1 = mine_cond_on(trn)
    # Bayes: channel = classifier confusion on the training fold; margin on the training fold
    cm = Counter()
    for j in trn:
        for e, p in zip(VA[j]["ee"], startV[j]): cm[(p, e[2])] += 1
    LC = chan_counts(cm); best = None
    for m in MARG:
        r = sub_net(trn, [("b", bayes(LC, m))])
        if best is None or r["nbad"]-r["left"] > best[0]: best = (r["nbad"]-r["left"], m)
    MB = best[1]
    print("fold %d: test %d doc; B1 %d khoa, margin %.2f; Bayes margin %.1f" % (k, len(tst), len(R1), M1, MB))
    confs = {
        "E4: OLD -> closure -> date": tail(),
        "truoc: NEW m.05 -> OLD -> closure -> date": [("n", ho_r(NEWc, REL, 0.05))] + tail(),
        "B1 cross-fit": [("b1", ho_cond(R1, M1))],
        "B1 cross-fit -> OLD -> closure -> date": [("b1", ho_cond(R1, M1))] + tail(),
        "Bayes cross-fit": [("b", bayes(LC, MB))],
        "Bayes cross-fit -> OLD -> closure -> date": [("b", bayes(LC, MB))] + tail(),
        "B1 -> Bayes -> OLD -> closure -> date": [("b1", ho_cond(R1, M1)), ("b", bayes(LC, MB))] + tail(),
    }
    for nm, layers in confs.items():
        r = sub_net(tst, layers)
        for key in ("flag", "hit", "fix", "brk", "nbad", "left", "npair"): tot[nm][key] += r[key]
print()
print("TONG HAI FOLD TEST (= toan bo valid, moi doc duoc cham dung mot lan):")
for nm, r in tot.items(): show(nm, r)
log("xong")
