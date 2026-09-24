# -*- coding: utf-8 -*-
"""Why does context B catch so much less than fake_data?

For the best context-B auditor (B1, cross-fitted) and for fake_data r10 (error rate close to
the classifier's 12.13%), measure:
  1. which error types exist and how many of each the auditor fixes
  2. how CLUSTERED the errors are: among the triangle neighbours (A-X, X-B) of a wrong edge,
     what fraction are also wrong -- versus the overall error rate. Random relabelling leaves
     the neighbourhood mostly right, so the wrong edge contradicts it; classifier errors come
     from shared features, so the neighbours tend to be wrong in the same way
  3. how often the neighbourhood AGREES with the wrong label (the wrong edge is consistent
     with its context, so no context-based auditor can see it)
"""
import io
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_BB = io.open(HERE/"bayes_b.py", encoding="utf-8").read()
exec(SRC_BB[:SRC_BB.index("exec(SRC_BA[SRC_BA.index(")])
SRC_X = SRC_BA[SRC_BA.index("# ================================================================ B: cross-fit on valid"):]
exec(SRC_X[:SRC_X.index("tot = defaultdict")])      # folds, vN, mine_cond_on, sub_net

def fixed_by(idx, layers):
    """Return per-doc final labels after the layers, for docs idx."""
    docs = [VA[j] for j in idx]; S_ = [vN[j] for j in idx]
    state = [list(startV[j]) for j in idx]
    for nm, fn in layers:
        for d, cur, S in zip(docs, state, S_):
            touched = d.setdefault("_t", set())
            for i, prop in fn(d, cur, S):
                if i in touched: continue
                touched.add(i)
                if prop: cur[i] = prop
    for d in docs: d.pop("_t", None)
    return dict(zip(idx, state))

final = {}
for k in (0, 1):
    trn = [j for j in range(len(VA)) if fold[j] != k]; tst = [j for j in range(len(VA)) if fold[j] == k]
    tA = [j for j in trn if sub[j] == 0]; tB = [j for j in trn if sub[j] == 1]
    RA = mine_cond_on(tA); best = None
    for m in (0.0, 0.05, 0.10, 0.20, 0.30):
        r = sub_net(tB, [("b1", ho_cond(RA, m))])
        if best is None or r["nbad"]-r["left"] > best[0]: best = (r["nbad"]-r["left"], m)
    final.update(fixed_by(tst, [("b1", ho_cond(mine_cond_on(trn), best[1]))]))

def breakdown(nm, starts, finals):
    tot = Counter(); fx = Counter(); br = Counter()
    for j, d in enumerate(VA):
        for e, p, q in zip(d["ee"], starts[j], finals[j]):
            g = e[2]
            if g != p:
                tot[(g, p)] += 1; fx[(g, p)] += (q == g)
            elif q != p: br[(g, q)] += 1
    n = sum(tot.values())
    print("  %s: %d canh sai, sua dung %d (%.1f%%), lam hong %d" % (nm, n, sum(fx.values()), 100*sum(fx.values())/n, sum(br.values())))
    print("    %-28s %7s %7s %8s" % ("gold -> dang co", "so", "% loi", "da sua"))
    for key, c in tot.most_common(8):
        print("    %-28s %7d %6.1f%% %7.1f%%" % ("%s -> %s" % key, c, 100*c/n, 100*fx[key]/c))

def clustering(nm, starts):
    """Triangle neighbours of wrong vs right edges: fraction wrong, and agreement with the edge label."""
    wr = Counter(); agree = Counter(); base = Counter()
    for j, d in enumerate(VA):
        lab = {}; ok = {}
        for e, p in zip(d["ee"], starts[j]):
            lab[(e[0], e[1])] = p; ok[(e[0], e[1])] = (p == e[2])
            base["n"] += 1; base["bad"] += (p != e[2])
        nbr = defaultdict(set)
        for (a, b) in lab: nbr[a].add(b); nbr[b].add(a)
        for (a, b), p in lab.items():
            kind = "sai" if not ok[(a, b)] else "dung"
            for x in (nbr[a] & nbr[b]) - {a, b}:
                for u, v in ((a, x), (x, b)):
                    key = (u, v) if (u, v) in ok else (v, u)
                    wr[(kind, "n")] += 1; wr[(kind, "bad")] += (not ok[key])
                # does the triangle support the edge's current label? (A-X and X-B read the same way)
                l1 = lab.get((a, x)) or inv(lab.get((x, a), "?")); l2 = lab.get((x, b)) or inv(lab.get((b, x), "?"))
                if p == "BEFORE" and l1 == "BEFORE" and l2 == "BEFORE": agree[(kind, "sup")] += 1
                if p == "CONTAINS" and l1 == "CONTAINS" and l2 == "CONTAINS": agree[(kind, "sup")] += 1
                agree[(kind, "n")] += 1
    print("  %s: ty le loi chung %.2f%%" % (nm, 100*base["bad"]/base["n"]))
    for kind in ("sai", "dung"):
        print("    quanh canh %-4s: canh tam giac lan can sai %5.2f%%   tam giac ung ho dung nhan hien tai (bac cau) %5.2f%%"
              % (kind, 100*wr[(kind, "bad")]/max(1, wr[(kind, "n")]), 100*agree[(kind, "sup")]/max(1, agree[(kind, "n")])))

startF, _, _ = fake_start("r10")
print()
print("=" * 100)
print("1. LOAI LOI VA TY LE SUA")
print("=" * 100)
breakdown("B (classifier), B1 cross-fit", startV, [final[j] for j in range(len(VA))])
set_pins(VA, "A")
SF = [sigs_L(d, lab_ctx(d, st, "A")) for d, st in zip(VA, startF)]
simC = simulate(CONF, 0.10); SC = [sigs_L(d, lab_ctx(d, st, "A")) for d, st in zip(CONF, simC)]
best = None
for m in MARG:
    r = net(CONF, SC, [("b", bayes(chan_fake(0.10), m))], simC)
    if best is None or r["nbad"]-r["left"] > best[0]: best = (r["nbad"]-r["left"], m)
docs_state = [list(x) for x in startF]
for d, cur, S in zip(VA, docs_state, SF):
    t = set()
    for i, prop in bayes(chan_fake(0.10), best[1])(d, cur, S):
        if i not in t and prop: t.add(i); cur[i] = prop
breakdown("fake r10, Bayes", startF, docs_state)
print()
print("=" * 100)
print("2. LOI CO TU CUM KHONG")
print("=" * 100)
clustering("B (classifier)", startV)
clustering("fake r10", startF)
log("xong")
