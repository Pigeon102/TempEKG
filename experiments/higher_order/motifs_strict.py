# -*- coding: utf-8 -*-
"""Last objection: were the pp negatives a gating artifact?

The per-label gate (lift >= 2) is far too weak for BEGINS-ON: its prior is 0.044%, so a
rule firing at 0.09% precision passes, then scores cwlb/0.00044 and overrides everything.
Those rules flipped 20,485 predictions in 4TT with 9 correct.

Strict gate, the one a context rule actually has to meet to be useful:
  * only CONTAINS, SIMULTANEOUS, OVERLAP (BEFORE is the fallback; BEGINS/ENDS-ON too rare)
  * kept only if its confirmation Wilson bound EXCEEDS the 257-rule classifier's own
    precision for that label on the confirmation documents -- a rule that is less
    reliable than the classifier it would override can only do harm
  * tau chosen on confirmation, valid opened once
The classifier is in-sample on confirmation docs, so its precision there is inflated and
the gate is conservative.
"""
import sys, io
from pathlib import Path
src = io.open(str(Path(__file__).resolve().parent / "motifs2.py"), encoding="utf-8").read()
exec(src[:src.index("# ---------------------------------------------------------------- gold (oracle)")])
LABS = ("CONTAINS", "SIMULTANEOUS", "OVERLAP")

cp = Counter(); co = Counter()
for d in CONF:
    for (a, b, g, f, cs), p in zip(d["ee"], d["pp"]):
        cp[p] += 1; co[p] += (p == g)
CLF = {r: co[r]/cp[r] if cp[r] else 0.0 for r in LABS}
print("do chinh xac cua 257 luat tren confirmation:", {r: "%.1f%%" % (100*v) for r, v in CLF.items()})

def mine_strict(dS, cS, fam):
    cnt = defaultdict(Counter); dd = defaultdict(lambda: defaultdict(set))
    for d, S in zip(DISC, dS):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for x in s:
                if fam == "ALL" or x.startswith(fam + "|"):
                    cnt[x][g] += 1; dd[x][g].add(d["id"])
    cand = []
    for x, c in cnt.items():
        n = sum(c.values())
        if n < 30: continue
        for r in LABS:
            k = c[r]
            if k >= 10 and len(dd[x][r]) >= 5 and wlb(k, n) > CLF[r]: cand.append((x, r))
    need = {x for x, _ in cand}
    cc = defaultdict(Counter)
    for d, S in zip(CONF, cS):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for x in s:
                if x in need: cc[x][g] += 1
    R = {}
    for x, r in cand:
        cn = sum(cc[x].values())
        if cn < 10: continue
        cw = wlb(cc[x][r], cn)
        if cw > CLF[r] and (x not in R or cw/PRIOR[r] > R[x][1]/PRIOR[R[x][0]]): R[x] = (r, cw)
    return R

def run(R, docs, sigS, tau):
    pred = []; gold = []; ch = cc = 0
    for d, S in zip(docs, sigS):
        for (a, b, g, f, cs), sc0, p0, s in zip(d["ee"], d["ps"], d["pp"], S):
            sc = dict(sc0)
            for x in s:
                t = R.get(x)
                if t:
                    v = t[1]/PRIOR[t[0]]
                    if v > sc.get(t[0], 0): sc[t[0]] = v
            p = max(sc, key=sc.get) if sc and max(sc.values()) >= tau else "BEFORE"
            pred.append(p); gold.append(g)
            if p != p0: ch += 1; cc += (p == g)
    m, per, acc = macro(pred, gold)
    return m, per, ch, cc

print()
print("=" * 100)
print("CONG CHAT: luat phai chinh xac hon classifier o nhan do")
print("=" * 100)
for mode in ("gold", "pred"):
    dS = [sigs(d, mode) for d in DISC]; cS = [sigs(d, mode) for d in CONF]; vS = [sigs(d, mode) for d in VA]
    print()
    print("  che do %s" % mode.upper())
    for fam in FAMS + ["ALL"]:
        R = mine_strict(dS, cS, fam)
        if not R:
            print("    %-4s   0 luat qua cong" % fam); continue
        best = None
        for tau in (5, 10, 20, 40, 80):
            mc, _, _, _ = run(R, CONF, cS, tau)
            if best is None or mc > best[0]: best = (mc, tau)
        m, per, ch, cc = run(R, VA, vS, best[1])
        labs = dict(Counter(v[0] for v in R.values()))
        print("    %-4s %3d luat %-40s tau=%-3d macro %6.2f%% (%+.2f)  doi %5d dung %5.1f%%"
              % (fam, len(R), str(labs)[:40], best[1], 100*m, 100*(m-0.2560), ch, 100*cc/max(1, ch)))
