# -*- coding: utf-8 -*-
"""Two things, one load.

F  Validate the Bai 2 auditors on fake_data/: MAVEN-ERE valid with EV-EV labels relabelled at
   5/10/15/20% (fake label drawn from the corpus marginal without the gold label; TIMEX edges
   untouched). Unlike classifier noise, here every wrong edge is known and the noise process
   is independent of the text, so a rule's behaviour can be read off directly.
     context A  EV-TX / TX-TX gold -- exactly what fake_data ships
     context B  EV-TX from the 273-rule classifier, TX-TX from calendar comparison
   The NEW gate needs the reliability of each label in the layer under audit. Two versions:
     rel=clf  classifier reliability (what the auditor was built with -- mismatched here)
     rel=sim  the same relabelling process simulated on CONFIRMATION documents at the same
              rate; uses the noise rate, never an edge of valid

B  Dig into context B (classifier noise, everything predicted), where the upgraded auditor
   gained only +7% net over E4. Three ideas, each chosen on CONFIRMATION, valid opened once:
     B1  rules mined on the NOISY graph, keyed by (signature, current label): learn
         P(gold | what the auditor actually sees), instead of gold-mined rules applied to
         predicted context -- the pg mismatch Bai 1 already measured
     B2  drop EV-TX legs whose predicting rule is weak (label -> UNK), so gold-mined rules
         only fire on context that is likely right
     B3  B1 then B2 then OLD -> closure -> date

Every configuration is scored by NET reduction (fixed - broken), not R_all alone.
Date-bridge pins now use PREDICTED EV-TX in context B (the earlier run used gold pins there;
that layer contributed 1 fix, so earlier numbers are unaffected in substance).
"""
import sys, io, re, json, random
from pathlib import Path
HERE = Path(__file__).resolve().parent
src = io.open(HERE/"bai2_auditor.py", encoding="utf-8").read()
exec(src[:src.index("OLD = mine_old()")])

FAKE = Path(r"C:\Reseach_Quang\fake_data")

# ---------------------------------------------------------------- shared machinery
def pred_tx_c(dr, ev, t):
    best = None
    for c in tx_feats(dr, ev, t):
        x = TXR.get(c)
        if x:
            v = x[1]/PRIOR[x[0]]
            if best is None or v > best[0]: best = (v, x[0], x[1])
    return (best[1], best[2]) if best else ("BEFORE", 0.0)
for d in TR + VA:
    d["txp"] = [pred_tx_c(dr, d["nd"][e], d["nd"][t]) for (e, t, dr, r) in d["tx"]]
    d["ttp"] = [pred_tt(d["nd"], a, b) for (a, b, r) in d["tt"]]

def lab_ctx(d, ev_labels, ctx, theta=0.0):
    """EV-EV from ev_labels; EV-TX/TX-TX gold (A) or predicted (B, legs below theta -> UNK)."""
    L = {}
    if ctx == "A":
        for (a, b, r) in d["edges"]: L[(a, b)] = r; L[(b, a)] = inv(r)
    else:
        for (e, t, dr, r), (p, c) in zip(d["tx"], d["txp"]):
            if c < theta: p = "UNK"
            if dr == "E": L[(e, t)] = p; L[(t, e)] = inv(p)
            else:         L[(t, e)] = p; L[(e, t)] = inv(p)
        for (a, b, r), p in zip(d["tt"], d["ttp"]):
            L[(a, b)] = p; L[(b, a)] = inv(p)
    for (a, b, g, f, cs), p in zip(d["ee"], ev_labels):
        L[(a, b)] = p; L[(b, a)] = inv(p)
    return L

def set_pins(docs, ctx):
    for d in docs:
        pin = defaultdict(set)
        for (e, t, dr, r), (p, c) in zip(d["tx"], d["txp"]):
            if ctx == "B": r = p
            dt = parse_date(d["nd"][t].get("text"))
            if not dt or not dt[1] or not dt[2] or not d["nd"][t].get("anchorable"): continue
            if (dr == "T" and r in ("CONTAINS", "SIMULTANEOUS")) or (dr == "E" and r == "SIMULTANEOUS"):
                pin[e].add(dt)
        d["pin"] = pin

def net(docs, S_, layers, start):
    state = [list(x) for x in start]; fix = brk = flag = hit = 0
    for nm, fn in layers:
        for d, cur, S in zip(docs, state, S_):
            touched = d.setdefault("_t", set())
            for i, prop in fn(d, cur, S):
                if i in touched: continue
                touched.add(i); flag += 1
                g = d["ee"][i][2]
                if g != cur[i]:
                    hit += 1; fix += (prop == g)
                elif prop and prop != cur[i]: brk += 1
                if prop: cur[i] = prop
    for d in docs: d.pop("_t", None)
    nbad = sum(1 for d, st in zip(docs, start) for e, p in zip(d["ee"], st) if e[2] != p)
    left = sum(1 for d, cur in zip(docs, state) for e, p in zip(d["ee"], cur) if e[2] != p)
    npair = sum(len(d["ee"]) for d in docs)
    return dict(flag=flag, hit=hit, fix=fix, brk=brk, nbad=nbad, left=left, npair=npair)

def show(nm, r):
    print("  %-44s co %6s  P@k %6.2f%%  rep %6.2f%%  R_all %6.2f%%  hong %5d  rong %+6d  loi %5.2f%% -> %5.2f%%"
          % (nm, format(r["flag"], ","), 100*r["hit"]/max(1, r["flag"]), 100*r["fix"]/max(1, r["hit"]),
             100*r["fix"]/max(1, r["nbad"]), r["brk"], r["nbad"]-r["left"],
             100*r["nbad"]/r["npair"], 100*r["left"]/r["npair"]), flush=True)

def mine_new_r(fams, rel):
    cnt = defaultdict(Counter); dd = defaultdict(lambda: defaultdict(set))
    for d, S in zip(DISC, dG):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for x in s:
                if x.split("|", 1)[0] in fams: cnt[x][g] += 1; dd[x][g].add(d["id"])
    cand = []
    for x, c in cnt.items():
        n = sum(c.values())
        if n < 30: continue
        for r in AUD:
            k = c[r]
            if k >= 10 and len(dd[x][r]) >= 5 and wlb(k, n) > rel[r]: cand.append((x, r))
    need = {x for x, _ in cand}
    cc = defaultdict(Counter)
    for d, S in zip(CONF, cG):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for x in s:
                if x in need: cc[x][g] += 1
    R = defaultdict(dict)
    for x, r in cand:
        cn = sum(cc[x].values())
        if cn < 10: continue
        cw = wlb(cc[x][r], cn)
        if cw > rel[r]: R[x][r] = cw
    return R

def ho_r(R, rel, margin=0.0):
    def f(d, cur, S):
        out = []
        for i, s in enumerate(S):
            best = {}
            for x in s:
                for r, cw in R.get(x, {}).items():
                    if cw > best.get(r, 0.0): best[r] = cw
            if not best: continue
            p = cur[i]
            alt = max((r for r in best if r != p), key=lambda r: best[r], default=None)
            if alt and best[alt] > max(rel.get(p, 0.0), best.get(p, 0.0)) + margin: out.append((i, alt))
        return out
    return f

OLD = mine_old()
NEWc = mine_new_r(set(FAMS), REL)
log("OLD %d luat, NEW(rel=clf) %d luat" % (len(OLD), sum(len(v) for v in NEWc.values())))

# ================================================================ F: fake_data
def fake_start(tag):
    m = json.load(io.open(FAKE/("valid_%s.manifest.json" % tag), encoding="utf-8"))
    ch = {(x["doc"], x["event1"], x["event2"]): x["fake"] for x in m["changed"]}
    out = []; used = 0
    for d in VA:
        lab = []
        for (a, b, g, f, cs) in d["ee"]:
            k = ch.get((d["id"], a, b)) or ch.get((d["id"], b, a))
            if k: used += 1
            lab.append(k or g)
        out.append(lab)
    return out, used, m["n_changed"]

def rel_sim(rate, seed=0):
    rng = random.Random(seed); cp = Counter(); co = Counter()
    for d in CONF:
        for e in d["ee"]:
            g = e[2]
            if rng.random() < rate:
                labs = [r for r in RELS if r != g]
                o = rng.choices(labs, [PRIOR[r] for r in labs])[0]
            else: o = g
            cp[o] += 1; co[o] += (o == g)
    return {r: co[r]/cp[r] if cp[r] else 0.0 for r in RELS}

print()
print("=" * 118)
print("F -- FAKE_DATA: auditor tren nhieu bom biet truoc (705 doc valid)")
print("=" * 118)
for tag, rate in (("r05", .05), ("r10", .10), ("r15", .15), ("r20", .20)):
    start, used, nch = fake_start(tag)
    RS = rel_sim(rate)
    NEWs = mine_new_r(set(FAMS), RS)
    print()
    print("muc %s: %d/%d canh doi khop KG.  rel=sim: %s   NEW(rel=sim) %d luat"
          % (tag, used, nch, {r[:4]: round(v, 3) for r, v in RS.items() if v}, sum(len(v) for v in NEWs.values())))
    for ctx in ("A", "B"):
        set_pins(VA, ctx)
        S = [sigs_L(d, lab_ctx(d, st, ctx)) for d, st in zip(VA, start)]
        print(" boi canh %s" % ctx)
        show("closure", net(VA, S, [("c", closure_layer)], start))
        show("OLD (21 luat)", net(VA, S, [("o", ho_old(OLD))], start))
        show("NEW rel=clf", net(VA, S, [("n", ho_r(NEWc, REL))], start))
        show("NEW rel=sim", net(VA, S, [("n", ho_r(NEWs, RS))], start))
        show("OLD -> closure -> date", net(VA, S, [("o", ho_old(OLD)), ("c", closure_layer), ("d", date_layer)], start))
        show("NEW rel=sim -> OLD -> closure -> date",
             net(VA, S, [("n", ho_r(NEWs, RS)), ("o", ho_old(OLD)), ("c", closure_layer), ("d", date_layer)], start))

# ================================================================ B: dig into context B
print()
print("=" * 118)
print("B -- BOI CANH B (nhieu classifier, moi thu du doan): chon tren CONFIRMATION, valid mo mot lan")
print("=" * 118)
startV = [list(d["pp"]) for d in VA]; startC = [list(d["pp"]) for d in CONF]; startD = [list(d["pp"]) for d in DISC]
set_pins(VA, "B"); set_pins(CONF, "B")

# ---- B1: rules mined on the noisy graph, keyed by (signature, current label)
log("B1: chu ky tren do thi nhieu (disc) ...")
dN = [sigs_L(d, lab_ctx(d, st, "B")) for d, st in zip(DISC, startD)]
cN = [sigs_L(d, lab_ctx(d, st, "B")) for d, st in zip(CONF, startC)]
vN = [sigs_L(d, lab_ctx(d, st, "B")) for d, st in zip(VA, startV)]
def mine_cond(nmin=20, kmin=5, dmin=3):
    cnt = defaultdict(Counter); dd = defaultdict(lambda: defaultdict(set))
    for d, S, st in zip(DISC, dN, startD):
        for (a, b, g, f, cs), s, p in zip(d["ee"], S, st):
            for x in set(s):
                cnt[(x, p)][g] += 1; dd[(x, p)][g].add(d["id"])
    R = {}
    for key, c in cnt.items():
        n = sum(c.values())
        if n < nmin: continue
        p = key[1]
        t = {p: wlb(c[p], n)}
        alts = {r: wlb(k, n) for r, k in c.items() if r != p and k >= kmin and len(dd[key][r]) >= dmin}
        if alts: t.update(alts); R[key] = t
    return R
def ho_cond(R, margin):
    def f(d, cur, S):
        out = []
        for i, s in enumerate(S):
            p = cur[i]; keep = 0.0; best = None
            for x in set(s):
                t = R.get((x, p))
                if not t: continue
                keep = max(keep, t[p])
                for r, w in t.items():
                    if r != p and (best is None or w > best[1]): best = (r, w)
            if best and best[1] > keep + margin: out.append((i, best[0]))
        return out
    return f
RC = mine_cond()
log("B1: %d khoa (chu ky, nhan hien tai) co nhan thay the" % len(RC))
print(" B1 -- chon margin tren CONFIRMATION:")
b1 = None
for m in (0.0, 0.05, 0.10, 0.20, 0.30):
    r = net(CONF, cN, [("b1", ho_cond(RC, m))], startC)
    print("   margin %.2f  co %5d  sua %5d  hong %5d  rong %+5d" % (m, r["flag"], r["fix"], r["brk"], r["nbad"]-r["left"]))
    if b1 is None or r["nbad"]-r["left"] > b1[0]: b1 = (r["nbad"]-r["left"], m)
M1 = b1[1]; print("   -> margin %.2f" % M1)

# ---- B2: confidence filter on EV-TX legs, gold-mined NEW rules
print(" B2 -- chon (theta, margin) tren CONFIRMATION:")
b2 = None; cS = {}
for th in (0.0, 0.5, 0.6, 0.7, 0.8, 0.9):
    cS[th] = [sigs_L(d, lab_ctx(d, st, "B", th)) for d, st in zip(CONF, startC)]
    for m in (0.0, 0.02, 0.05, 0.10):
        r = net(CONF, cS[th], [("n", ho_r(NEWc, REL, m))], startC)
        red = r["nbad"]-r["left"]
        print("   theta %.1f margin %.2f  co %5d  sua %5d  hong %5d  rong %+5d" % (th, m, r["flag"], r["fix"], r["brk"], red))
        if b2 is None or red > b2[0]: b2 = (red, th, m)
_, TH, M2 = b2; print("   -> theta %.1f, margin %.2f" % (TH, M2))
vT = [sigs_L(d, lab_ctx(d, st, "B", TH)) for d, st in zip(VA, startV)]

# ---- stacks chosen on CONFIRMATION
stacks = {
    "E4: OLD -> closure -> date": lambda C: [("o", ho_old(OLD)), ("c", closure_layer), ("d", date_layer)],
    "truoc: NEW m.05 -> OLD -> closure -> date": lambda C: [("n", ho_r(NEWc, REL, 0.05)), ("o", ho_old(OLD)), ("c", closure_layer), ("d", date_layer)],
    "B1 -> OLD -> closure -> date": lambda C: [("b1", ho_cond(RC, M1)), ("o", ho_old(OLD)), ("c", closure_layer), ("d", date_layer)],
    "B2 -> OLD -> closure -> date": lambda C: [("b2", ho_r(NEWc, REL, M2)), ("o", ho_old(OLD)), ("c", closure_layer), ("d", date_layer)],
    "B1 -> B2 -> OLD -> closure -> date": lambda C: [("b1", ho_cond(RC, M1)), ("b2", ho_r(NEWc, REL, M2)), ("o", ho_old(OLD)), ("c", closure_layer), ("d", date_layer)],
}
# B2 layers read the theta-filtered signatures; everything else reads the unfiltered ones.
def run_stack(docs, S_plain, S_theta, layers, start):
    wrapped = []
    for nm, fn in layers:
        if nm == "b2":
            wrapped.append((nm, (lambda fn: lambda d, cur, S: fn(d, cur, d["_ST"]))(fn)))
        else:
            wrapped.append((nm, fn))
    for d, st in zip(docs, S_theta): d["_ST"] = st
    r = net(docs, S_plain, wrapped, start)
    for d in docs: d.pop("_ST", None)
    return r
print()
print(" CONFIRMATION (chon cau hinh):")
best = None
for nm, mk in stacks.items():
    r = run_stack(CONF, cN, cS[TH], mk(None), startC)
    show(nm, r)
    if best is None or r["nbad"]-r["left"] > best[0]: best = (r["nbad"]-r["left"], nm)
print("   -> chon: %s" % best[1])
print()
print(" VALID (mo mot lan, in moi dong de doi chieu; dong duoc chon danh dau *):")
for nm, mk in stacks.items():
    r = run_stack(VA, vN, vT, mk(None), startV)
    show(("* " if nm == best[1] else "  ") + nm, r)
print()
print(" Tung lop rieng tren VALID:")
show("B1 margin %.2f" % M1, net(VA, vN, [("b1", ho_cond(RC, M1))], startV))
show("B2 theta %.1f margin %.2f" % (TH, M2), net(VA, vT, [("b2", ho_r(NEWc, REL, M2))], startV))
log("xong")
