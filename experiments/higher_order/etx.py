# -*- coding: utf-8 -*-
"""E1+E2: do Event-TIMEX-Event patterns carry signal the EV-EV graph misses?

Bai 1 was closed on an EV-EV representation, but 31.2% of the corpus's temporal relations
touch a TIMEX node and were never mined. 881,264 event pairs share a TIMEX neighbour.

E1  Count the triads  A --R1--> T <--R2-- B  and ask what they say about R(A,B).
    Scored exactly like the EV-EV triangles: support, document diversity, Wilson bound,
    mined on discovery documents and checked on valid.

E2  Add them to the pair-level classifier under the same protocol and see whether
    macro-F1 moves off 25.60%.

The decisive comparison is against the EV-EV triangle result (38.30% on gold context),
since a TIMEX hub is observable at test time in a way a neighbour's temporal LABEL is not
-- the edges A-T and B-T are themselves target edges, so this has the same caveat.
"""
import sys, io, json, math, hashlib
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
PRIOR = {"BEFORE": .91045, "CONTAINS": .07430, "SIMULTANEOUS": .00862,
         "OVERLAP": .00597, "BEGINS-ON": .00044, "ENDS-ON": .00022}
Z = 1.959963985
CAPT = 4          # at most this many shared TIMEX per pair

def wlb(k, n):
    if n == 0: return 0.0
    p = k/n
    return (p + Z*Z/(2*n) - Z*math.sqrt(p*(1-p)/n + Z*Z/(4*n*n)))/(1 + Z*Z/n)
def macro(pred, gold):
    tp, fp, fn = Counter(), Counter(), Counter()
    for p, g in zip(pred, gold):
        if p == g: tp[g] += 1
        else: fp[p] += 1; fn[g] += 1
    per = {}
    for r in RELS:
        P = tp[r]/(tp[r]+fp[r]) if tp[r]+fp[r] else 0.0
        R = tp[r]/(tp[r]+fn[r]) if tp[r]+fn[r] else 0.0
        per[r] = 2*P*R/(P+R) if P+R else 0.0
    return sum(per.values())/6, per, sum(tp.values())/len(gold)
def disc(doc):
    return int(hashlib.md5(doc.encode()).hexdigest(), 16) % 10 >= 4

def load(path, limit=0, feats=False):
    """Each document: EV-EV rows, and the event<->timex edges with their direction."""
    if feats:
        from mine_compositional import candidate_conditions, pair_features
        from mine_mdd import relational_conditions
    out = []
    for i, line in enumerate(io.open(path, encoding="utf-8")):
        if limit and i >= limit: break
        if not line.strip(): continue
        rec = json.loads(line); nd = rec["nodes"]; anch = defaultdict(set)
        for p in rec["anchored_pairs"]:
            for ra, rb in p["roles"]: anch[(p["a"], p["b"])].add((ra, rb))
        ev2t = defaultdict(dict)     # event -> {timex: signed relation}
        rows = []
        for e in rec["target_edges"]:
            a, b = e["s"], e["t"]
            ka = nd.get(a, {}).get("kind"); kb = nd.get(b, {}).get("kind")
            if ka == "event" and kb == "timex":
                ev2t[a][b] = "E>" + e["rel"]           # event -> timex
            elif ka == "timex" and kb == "event":
                ev2t[b][a] = "T>" + e["rel"]           # timex -> event
            elif ka == "event" and kb == "event":
                if feats:
                    na, nb = nd[a], nd[b]
                    sh = anch.get((a, b)) or anch.get((b, a)) or set()
                    f = pair_features(na, nb, sh, bool(sh), frozenset())
                    cs = frozenset(list(candidate_conditions(f)) + relational_conditions(na, nb, sh))
                    rows.append((a, b, e["rel"], f, cs))
                else:
                    rows.append((a, b, e["rel"], None, None))
        if rows: out.append((rec["doc_id"], rows, ev2t))
    return out

def triads(doc_rows, ev2t, a, b):
    """Signatures (rel(A,T), rel(B,T)) over TIMEX nodes both events touch."""
    ta, tb = ev2t.get(a), ev2t.get(b)
    if not ta or not tb: return []
    shared = sorted(set(ta) & set(tb))[:CAPT]
    return [(ta[t], tb[t]) for t in shared]

TR = load(GRAPH/"train.jsonl", 400)
print("train %d doc" % len(TR), flush=True)

# how much reach do the triads have?
reach = tot = 0
for doc, rows, ev2t in TR:
    for (a, b, r, _, _) in rows:
        tot += 1
        if triads(rows, ev2t, a, b): reach += 1
print("  cap EV-EV co TIMEX chung: %s/%s = %.1f%%" % (format(reach, ","), format(tot, ","), 100*reach/tot), flush=True)

# ---------------------------------------------------------------- E1 mine on discovery
D = [d for d in TR if disc(d[0])]
C = [d for d in TR if not disc(d[0])]
print("  discovery %d doc, confirmation %d doc" % (len(D), len(C)), flush=True)

def count(docs):
    sig = defaultdict(Counter); sd = defaultdict(lambda: defaultdict(set))
    for doc, rows, ev2t in docs:
        for (a, b, r, _, _) in rows:
            for k in triads(rows, ev2t, a, b):
                sig[k][r] += 1; sd[k][r].add(doc)
    return sig, sd
ds, dd = count(D)
print("  %s chu ky EV-TIMEX-EV tren discovery" % format(len(ds), ","), flush=True)

cand = {}
for k, c in ds.items():
    n = sum(c.values()); top, kk = c.most_common(1)[0]
    if n < 30 or kk < 10 or len(dd[k][top]) < 5: continue
    if wlb(kk, n) >= 0.50: cand[k] = (top, wlb(kk, n), kk, n)
print("  -> %d ung vien qua cong loc" % len(cand), flush=True)

cs_, cd = count(C)
CONF = {}
for k, (top, w, kk, n) in cand.items():
    c = cs_.get(k)
    if not c or sum(c.values()) < 10: continue
    CONF[k] = (top, wlb(c[top], sum(c.values())))
rk = sorted(CONF.items(), key=lambda kv: -kv[1][1])
ETX = dict(rk[:max(1, int(0.7*len(rk)))])
print("  -> %d luat dong bang sau confirmation" % len(ETX), flush=True)
print("     nhan: %s" % dict(Counter(v[0] for v in ETX.values()).most_common()))

print()
print("=" * 94)
print("E1 — CHU KY EV-TIMEX-EV manh nhat (lift tren discovery)")
print("=" * 94)
rows_ = []
for k, c in ds.items():
    n = sum(c.values())
    if n < 30: continue
    for r in RELS:
        if c[r] < 10: continue
        L = (c[r]/n)/PRIOR[r]
        if L > 1.5: rows_.append((L, c[r], n, len(dd[k][r]), k, r))
rows_.sort(reverse=True)
print("  %7s%7s%8s%6s  %s" % ("lift", "k", "n", "doc", "(rel A-T, rel B-T) -> rel A-B"))
for L, kk, n, ndc, k, r in rows_[:14]:
    lbl = "%s | %s -> %s" % (k[0][:14], k[1][:14], r[:12])
    print("  %7.1f%7s%8s%6d  %s" % (L, format(kk, ","), format(n, ","), ndc, lbl))

# ---------------------------------------------------------------- E2 as a classifier
print()
print("=" * 94)
print("E2 — THEM VAO CLASSIFIER, cung protocol")
print("=" * 94)
VA = load(GRAPH/"valid.jsonl", 0, feats=True)
rules = V.load_rules(ART/"rules_rx_c70.json")
flat = [(f, cs) for _, rows, _ in VA for (_, _, _, f, cs) in rows]
idx = V.build_index(rules, [(None, f, cs) for f, cs in flat])

gold = []; base = []; withtx = []; nfire = 0
for doc, rows, ev2t in VA:
    for (a, b, g, f, cs) in rows:
        gold.append(g)
        h = V.firing(rules, idx, f, cs)
        sc = {}
        for ri in h:
            ru = rules[ri]
            v = ru["wlb"]/PRIOR[ru["rel"]]
            if v > sc.get(ru["rel"], 0): sc[ru["rel"]] = v
        p0 = max(sc, key=sc.get) if sc and max(sc.values()) >= 5 else "BEFORE"
        base.append(p0)
        # add EV-TIMEX-EV evidence with the same normalisation
        tsc = dict(sc)
        fired = False
        for k in triads(rows, ev2t, a, b):
            t = ETX.get(k)
            if t:
                fired = True
                v = t[1]/PRIOR[t[0]]
                if v > tsc.get(t[0], 0): tsc[t[0]] = v
        if fired: nfire += 1
        p1 = max(tsc, key=tsc.get) if tsc and max(tsc.values()) >= 5 else "BEFORE"
        withtx.append(p1)

m0, per0, a0 = macro(base, gold)
m1, per1, a1 = macro(withtx, gold)
ch = sum(1 for x, y in zip(base, withtx) if x != y)
right = sum(1 for x, y, g in zip(base, withtx, gold) if x != y and y == g)
print("  valid %s cap, luat EV-TIMEX ban tren %s (%.1f%%)"
      % (format(len(gold), ","), format(nfire, ","), 100*nfire/len(gold)))
print("  %-30s macro-F1 %6.2f%%  acc %6.2f%%" % ("A  chi 257 luat EV-EV", 100*m0, 100*a0))
print("     " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per0[r]) for r in RELS))
print("  %-30s macro-F1 %6.2f%%  acc %6.2f%%" % ("B  + luat EV-TIMEX-EV", 100*m1, 100*a1))
print("     " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per1[r]) for r in RELS))
print()
print("  chenh: %+.2f diem macro-F1" % (100*(m1-m0)))
if ch:
    print("  doi nhan tren %s canh, dung %s (%.1f%%)" % (format(ch, ","), format(right, ","), 100*right/ch))
