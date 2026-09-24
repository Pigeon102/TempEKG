# -*- coding: utf-8 -*-
"""How much do triples contribute, and does a fourth event add anything on top?

Three questions, in order:

  1. WHAT IS LEFT AMBIGUOUS after triangles. 73.3% of edges keep exactly two candidate
     labels. Which two? If it is {BEFORE, CONTAINS} that is the same pair the classifier
     confuses 86.5% of the time, so resolving it would matter a great deal.

  2. WHAT TRIPLES ACTUALLY BUY, measured as a classifier rather than as lift. Apply the
     learned triangle rules (mined on train, frozen) to valid and score them the same way
     the 257-rule set was scored. Lift 2000x means nothing if coverage is 0.1%.

  3. WHETHER QUADRUPLES RESOLVE WHAT TRIPLES CANNOT. For each still-ambiguous edge, look
     at pairs of intermediate events (c, d) and ask whether the four-node configuration
     concentrates on one label where the three-node one did not.

Everything is mined on TRAIN documents and checked on VALID documents.
"""
import json, io, sys, math
from collections import Counter, defaultdict
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from pathlib import Path
from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
Z = 1.959963985
def wlb(k, n):
    if n == 0: return 0.0
    p = k/n
    return (p + Z*Z/(2*n) - Z*math.sqrt(p*(1-p)/n + Z*Z/(4*n*n)))/(1 + Z*Z/n)
def compatible(a):
    return [r for r, s in MAVEN_TO_ALLEN.items() if s & a]

def load(path, limit=0):
    docs = []
    for i, line in enumerate(io.open(path, encoding="utf-8")):
        if limit and i >= limit: break
        if not line.strip(): continue
        rec = json.loads(line)
        nd = rec["nodes"]
        es = [(e["s"], e["t"], e["rel"]) for e in rec["target_edges"]
              if nd.get(e["s"], {}).get("kind") == "event"
              and nd.get(e["t"], {}).get("kind") == "event"]
        if es: docs.append((rec["doc_id"], es))
    return docs

TR = load(GRAPH/"train.jsonl", 400)
VA = load(GRAPH/"valid.jsonl", 0)
print("train %d doc  valid %d doc" % (len(TR), len(VA)), flush=True)

def adjof(es):
    adj = defaultdict(dict)
    for a, b, r in es:
        adj[a][b] = r; adj[b][a] = r
    return adj

# ================================================================ 1. what stays ambiguous
print()
print("=" * 98)
print("1. SAU TAM GIAC, CON LAI NHUNG CAP NHAN NAO?")
print("=" * 98)
amb_pairs = Counter(); amb_gold = defaultdict(Counter)
for doc, es in VA:
    adj = adjof(es)
    for a, b, r in es:
        cs = [c for c in set(adj[a]) & set(adj[b]) if c not in (a, b)]
        if not cs: continue
        imp = FULL
        for c in cs:
            sa = MAVEN_TO_ALLEN.get(adj[a][c]); sb = MAVEN_TO_ALLEN.get(adj[c][b])
            if sa and sb: imp = imp & compose(sa, sb)
        adm = compatible(imp)
        if len(adm) == 2:
            key = tuple(sorted(adm))
            amb_pairs[key] += 1
            amb_gold[key][r] += 1
t2 = sum(amb_pairs.values())
print("  %s canh con dung 2 nhan" % format(t2, ","))
print("  %-34s %10s %7s   phan bo nhan that" % ("cap nhan con lai", "so canh", "%"))
for k, v in amb_pairs.most_common(6):
    g = amb_gold[k]
    dist = " ".join("%s %.0f%%" % (x[:4], 100*g[x]/v) for x, _ in g.most_common(3))
    print("  %-34s %10s %6.1f%%   %s" % (" / ".join(x[:12] for x in k), format(v, ","), 100*v/t2, dist))

# ================================================================ 2. triples as a classifier
print()
print("=" * 98)
print("2. LUAT TAM GIAC LAM CLASSIFIER (mine tren train, dong bang, cham tren valid)")
print("=" * 98)
sig = defaultdict(Counter); sigdoc = defaultdict(lambda: defaultdict(set))
for doc, es in TR:
    adj = adjof(es)
    for a, b, r in es:
        for c in set(adj[a]) & set(adj[b]):
            if c in (a, b): continue
            k = (adj[a][c], adj[c][b])
            sig[k][r] += 1; sigdoc[k][r].add(doc)

# freeze rules: enough support, enough documents, high Wilson bound
TRI = {}
for k, c in sig.items():
    n = sum(c.values()); top, kk = c.most_common(1)[0]
    if n < 30 or kk < 10: continue
    if len(sigdoc[k][top]) < 5: continue          # document diversity gate
    w = wlb(kk, n)
    if w < 0.50: continue
    TRI[k] = (top, w, kk, n, len(sigdoc[k][top]))
print("  %d luat tam giac qua cong (n>=30, k>=10, doc>=5, wlb>=0.50)" % len(TRI))

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

gold = []; pred = []; fired = 0
for doc, es in VA:
    adj = adjof(es)
    for a, b, r in es:
        gold.append(r)
        votes = Counter()
        for c in set(adj[a]) & set(adj[b]):
            if c in (a, b): continue
            t = TRI.get((adj[a][c], adj[c][b]))
            if t: votes[t[0]] += t[1]
        if votes:
            fired += 1; pred.append(votes.most_common(1)[0][0])
        else:
            pred.append("BEFORE")
m, per, acc = macro(pred, gold)
print("  ban tren %s/%s canh (%.1f%%)" % (format(fired, ","), format(len(gold), ","), 100*fired/len(gold)))
print("  macro-F1 %.2f%%   accuracy %.2f%%" % (100*m, 100*acc))
print("  " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per[r]) for r in RELS))
mb, _, ab = macro(["BEFORE"]*len(gold), gold)
print("  (hang so BEFORE: macro-F1 %.2f%%  acc %.2f%%)" % (100*mb, 100*ab))

# ================================================================ 3. quadruples
print()
print("=" * 98)
print("3. BO 4 CO GIAI QUYET DUOC PHAN TAM GIAC BO SOT KHONG?")
print("=" * 98)
print("  Xet cap trung gian (c,d); chu ky = (r_ac, r_cb, r_ad, r_db)", flush=True)

q_sig = defaultdict(Counter); q_doc = defaultdict(lambda: defaultdict(set))
CAP = 6          # at most this many intermediates per edge, keeps the count finite
for doc, es in TR:
    adj = adjof(es)
    for a, b, r in es:
        mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
        for i in range(len(mids)):
            for j in range(i+1, len(mids)):
                c, d = mids[i], mids[j]
                k = (adj[a][c], adj[c][b], adj[a][d], adj[d][b])
                q_sig[k][r] += 1; q_doc[k][r].add(doc)
print("  %s chu ky bo 4 tren train" % format(len(q_sig), ","))

QUAD = {}
for k, c in q_sig.items():
    n = sum(c.values()); top, kk = c.most_common(1)[0]
    if n < 30 or kk < 10: continue
    if len(q_doc[k][top]) < 5: continue
    w = wlb(kk, n)
    if w < 0.50: continue
    QUAD[k] = (top, w, kk, n, len(q_doc[k][top]))
print("  %s luat bo 4 qua cung bo cong" % format(len(QUAD), ","))

# which of them say something the triangles did not?
NEW = {}
for k, (top, w, kk, n, nd) in QUAD.items():
    rac, rcb, rad, rdb = k
    t1 = TRI.get((rac, rcb)); t2_ = TRI.get((rad, rdb))
    said = {t[0] for t in (t1, t2_) if t}
    if not said or top not in said:
        NEW[k] = (top, w, kk, n, nd, sorted(said))
print("  trong do %s luat NOI KHAC voi ca hai tam giac con" % format(len(NEW), ","))

if NEW:
    print()
    print("  %-52s %8s %7s %5s  %s" % ("(r_ac, r_cb | r_ad, r_db) -> nhan", "train P", "n", "doc", "tam giac noi gi"))
    print("  " + "-" * 104)
    for k, (top, w, kk, n, nd, said) in sorted(NEW.items(), key=lambda x: -x[1][1])[:15]:
        lbl = "%s,%s | %s,%s -> %s" % tuple([x[:4] for x in k] + [top[:4]])
        print("  %-52s %7.1f%% %7s %5d  %s" % (lbl, 100*kk/n, format(n, ","), nd,
              ", ".join(s[:4] for s in said) if said else "(khong luat nao)"))

# quad as classifier, on top of triangles
gold2 = []; pred2 = []; fired2 = 0; only_quad = 0
for doc, es in VA:
    adj = adjof(es)
    for a, b, r in es:
        gold2.append(r)
        votes = Counter()
        mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
        for c in mids:
            t = TRI.get((adj[a][c], adj[c][b]))
            if t: votes[t[0]] += t[1]
        had_tri = bool(votes)
        for i in range(len(mids)):
            for j in range(i+1, len(mids)):
                c, d = mids[i], mids[j]
                q = QUAD.get((adj[a][c], adj[c][b], adj[a][d], adj[d][b]))
                if q: votes[q[0]] += q[1]
        if votes:
            fired2 += 1
            if not had_tri: only_quad += 1
            pred2.append(votes.most_common(1)[0][0])
        else:
            pred2.append("BEFORE")
m2, per2, acc2 = macro(pred2, gold2)
print()
print("  TAM GIAC + BO 4:  ban tren %s canh (%.1f%%), trong do %s chi bo 4 ban duoc"
      % (format(fired2, ","), 100*fired2/len(gold2), format(only_quad, ",")))
print("  macro-F1 %.2f%%   accuracy %.2f%%" % (100*m2, 100*acc2))
print("  " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per2[r]) for r in RELS))
print()
print("  %-26s%12s%12s%10s" % ("", "tam giac", "+ bo 4", "chenh"))
print("  " + "-" * 60)
print("  %-26s%11.2f%%%11.2f%%%9.2f" % ("macro-F1", 100*m, 100*m2, 100*(m2-m)))
print("  %-26s%11.2f%%%11.2f%%%9.2f" % ("accuracy", 100*acc, 100*acc2, 100*(acc2-acc)))
print("  %-26s%11.1f%%%11.1f%%%9.1f" % ("do phu", 100*fired/len(gold), 100*fired2/len(gold2),
                                        100*(fired2-fired)/len(gold)))
