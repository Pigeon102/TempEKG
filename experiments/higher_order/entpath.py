# -*- coding: utf-8 -*-
"""Bai 1, last untested legal class: meaningful ENTITY-ROLE metapaths.

Every temporal-label motif failed in the realistic setting for one reason: a rule that
reads predicted context labels cannot be more reliable than the classifier producing them.
Metapaths through event-ENTITY edges avoid that entirely -- input_edges are observed, not
predicted -- and the roles make them meaningful rather than exhaustive:

  M2   A -r1-> X <-r2- B                          shared participant, typed
       e.g.  A -Agent-> Garibaldi <-Agent- B        (the same person does two things)
  M4   A -r1-> X <-r2- C -r3-> Y <-r4- B          chain through a third event C
       e.g.  A -Victim-> X <-Agent- C -Agent-> Y <-Patient- B
  M4p  M4 plus where C sits in the text relative to A and B (between / outside)

Signature carries roles and entity types (Person / Organization / Location / ...).
Earlier structural features covered only the one-hop form (anchor_roles, shared entity);
multi-hop role chains were never tried.

Protocol identical to the motif study: mine on DISCOVERY, confirm on CONFIRMATION, tau
chosen on CONFIRMATION, VALID opened once. Two gates are reported:
  strict  a rule is kept only if its confirmation Wilson bound beats the 257-rule
          classifier's own precision for that label (the bar a rule must clear to help)
  lift    per-label enrichment (lift >= 2, wlb/prior >= 1.5), BEGINS/ENDS-ON excluded
"""
import sys, io
import json
from pathlib import Path
src = io.open(str(Path(__file__).resolve().parent / "motifs2.py"), encoding="utf-8").read()
exec(src[:src.index('log("dung motif ...")')])

LABS = ("CONTAINS", "SIMULTANEOUS", "OVERLAP")
CAPM = 8

# ---------------------------------------------------------------- event -> [(entity, role)]
def add_roles(path, docs, limit=0):
    byid = {d["id"]: d for d in docs}
    for i, line in enumerate(io.open(path, encoding="utf-8")):
        if limit and i >= limit: break
        if not line.strip(): continue
        rec = json.loads(line)
        d = byid.get(rec["doc_id"])
        if not d: continue
        nd = rec["nodes"]; ev2 = defaultdict(list); ent2 = defaultdict(list)
        for e in rec["input_edges"]:
            if nd.get(e["t"], {}).get("kind") != "entity": continue
            ev2[e["s"]].append((e["t"], e["role"]))
            ent2[e["t"]].append((e["s"], e["role"]))
        d["ev2"] = ev2; d["ent2"] = ent2
add_roles(GRAPH/"train.jsonl", TR, 400); add_roles(GRAPH/"valid.jsonl", VA)

def metapaths(d):
    nd = d["nd"]; ev2 = d.get("ev2", {}); ent2 = d.get("ent2", {})
    ET = lambda x: nd.get(x, {}).get("ent_type") or "?"
    out = []
    for (a, b, g, f, cs) in d["ee"]:
        s = []
        ea = ev2.get(a, ()); eb = {x: r for x, r in ev2.get(b, ())}
        # M2: shared participant
        m2 = sorted("M2|%s|%s|%s" % (r1, ET(x), eb[x]) for x, r1 in ea if x in eb)
        s += m2[:CAPM]
        # M4: A -> X <- C -> Y <- B
        sa, sb = nd[a].get("sent_first", 0) or 0, nd[b].get("sent_first", 0) or 0
        lo, hi = min(sa, sb), max(sa, sb)
        m4 = []
        for x, r1 in ea:
            for c, r2 in ent2.get(x, ()):
                if c in (a, b): continue
                sc = nd.get(c, {}).get("sent_first", 0) or 0
                pos = "btw" if lo <= sc <= hi else "out"
                for y, r3 in ev2.get(c, ()):
                    if y == x or y not in eb: continue
                    core = "%s|%s|%s|%s|%s|%s" % (r1, ET(x), r2, r3, ET(y), eb[y])
                    m4.append(("M4|" + core, "M4p|" + core + "|" + pos))
        m4.sort()
        for u, v in m4[:CAPM]: s += [u, v]
        out.append(s)
    return out

log("dung metapath ...")
dS = [metapaths(d) for d in DISC]; cS = [metapaths(d) for d in CONF]; vS = [metapaths(d) for d in VA]
npair = sum(len(x) for x in vS)
for fam in ("M2", "M4", "M4p"):
    c = sum(1 for S in vS for s in S if any(x.startswith(fam + "|") for x in s))
    log("  do phu %-4s tren valid: %.1f%%" % (fam, 100*c/npair))

cp = Counter(); co = Counter()
for d in CONF:
    for (a, b, g, f, cs), p in zip(d["ee"], d["pp"]):
        cp[p] += 1; co[p] += (p == g)
CLF = {r: co[r]/cp[r] if cp[r] else 0.0 for r in LABS}

def mine_gate(fam, gate):
    cnt = defaultdict(Counter); dd = defaultdict(lambda: defaultdict(set))
    for d, S in zip(DISC, dS):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for x in set(s):
                if fam == "ALL" or x.startswith(fam + "|"):
                    cnt[x][g] += 1; dd[x][g].add(d["id"])
    cand = []
    for x, c in cnt.items():
        n = sum(c.values())
        if n < 30: continue
        for r in LABS:
            k = c[r]
            if k < 10 or len(dd[x][r]) < 5: continue
            ok = wlb(k, n) > CLF[r] if gate == "strict" else ((k/n)/PRIOR[r] >= 2 and wlb(k, n)/PRIOR[r] >= 1.5)
            if ok: cand.append((x, r))
    need = {x for x, _ in cand}
    cc = defaultdict(Counter)
    for d, S in zip(CONF, cS):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for x in set(s):
                if x in need: cc[x][g] += 1
    bylab = defaultdict(list)
    for x, r in cand:
        cn = sum(cc[x].values())
        if cn < 10: continue
        cw = wlb(cc[x][r], cn)
        if (cw > CLF[r]) if gate == "strict" else (cw/PRIOR[r] >= 1.5): bylab[r].append((cw, x))
    R = {}
    for r, lst in bylab.items():
        lst.sort(reverse=True)
        for cw, x in (lst if gate == "strict" else lst[:max(1, int(0.7*len(lst)))]):
            if x not in R or cw/PRIOR[r] > R[x][1]/PRIOR[R[x][0]]: R[x] = (r, cw)
    return R

def run(R, docs, S_, tau):
    pred = []; gold = []; ch = cc = 0
    for d, S in zip(docs, S_):
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

def firing(R):
    hit = Counter(); ok = Counter()
    for d, S in zip(VA, vS):
        for (a, b, g, f, cs), s in zip(d["ee"], S):
            for r in {R[x][0] for x in s if x in R}:
                hit[r] += 1; ok[r] += (g == r)
    return "  ".join("%s %.1f%%(%d)" % (r[:4], 100*ok[r]/hit[r], hit[r]) for r in sorted(hit))

print()
print("=" * 104)
print("BAI 1 -- METAPATH ENTITY-VAI TRO (hop le, khong doc target edge).  base 257 luat 25.60%%")
print("do chinh xac classifier tren confirmation: %s" % {r: "%.1f%%" % (100*v) for r, v in CLF.items()})
print("=" * 104)
for gate in ("strict", "lift"):
    print("  cong %s" % gate)
    for fam in ("M2", "M4", "M4p", "ALL"):
        R = mine_gate(fam, gate)
        if not R:
            print("    %-4s   0 luat qua cong" % fam); continue
        best = None
        for tau in (5, 10, 20, 40, 80):
            mc, _, _, _ = run(R, CONF, cS, tau)
            if best is None or mc > best[0]: best = (mc, tau)
        m, per, ch, cc = run(R, VA, vS, best[1])
        print("    %-4s %3d luat %-34s tau=%-3d macro %6.2f%% (%+.2f)  doi %5d dung %5.1f%%"
              % (fam, len(R), str(dict(Counter(v[0] for v in R.values())))[:34], best[1],
                 100*m, 100*(m-0.2560), ch, 100*cc/max(1, ch)))
        print("         ban dung: %s" % firing(R))
        if fam == "ALL":
            top = sorted(R.items(), key=lambda kv: -kv[1][1])[:6]
            for x, (r, cw) in top:
                print("           %-70s -> %-12s cwlb %.3f" % (x[:70], r, cw))
log("xong")
