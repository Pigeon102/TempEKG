# -*- coding: utf-8 -*-
"""Quintuples, and a careful look at the ENDS-ON mapping hole.

Part A -- the {b,m} hole. ENDS-ON maps to the Allen set {b, m}, which contains b, the
same element BEFORE maps to. So any inference that narrows to b keeps ENDS-ON alive as
a candidate forever. 80,571 of the "ambiguous" edges are exactly this. Two questions:
is the mapping defensible, and what happens to every downstream number if it is fixed?

Part B -- quintuples. Triples gave +2.62 over pair-level, quadruples +3.34 on top. Does
a fifth event keep the trend, or has the signal been exhausted? Measured the same way:
mined on train documents, frozen, scored on valid.
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
def compat(a, mapping):
    return [r for r, s in mapping.items() if s & a]

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

def adjof(es):
    adj = defaultdict(dict)
    for a, b, r in es:
        adj[a][b] = r; adj[b][a] = r
    return adj

TR = load(GRAPH/"train.jsonl", 400)
VA = load(GRAPH/"valid.jsonl", 0)
print("train %d doc  valid %d doc" % (len(TR), len(VA)), flush=True)

# ================================================================ A. the {b,m} hole
print()
print("=" * 100)
print("A. DIEU TRA LO HONG ANH XA ENDS-ON -> {b, m}")
print("=" * 100)
print("  Anh xa hien tai:")
for r in RELS:
    print("    %-14s -> %s" % (r, sorted(MAVEN_TO_ALLEN[r])))
print()
print("  Phan tu Allen nao bi CHIA giua nhieu nhan MAVEN?")
owner = defaultdict(list)
for r, s in MAVEN_TO_ALLEN.items():
    for x in s: owner[x].append(r)
for x, rs in sorted(owner.items()):
    if len(rs) > 1:
        print("    '%s' thuoc ve: %s" % (x, ", ".join(rs)))

# what does the corpus say ENDS-ON really is?
print()
print("  ENDS-ON co thuc su la {b, m} khong? Kiem tra bang cau truc do thi.")
print("  Neu A ENDS-ON B nghia la 'A ket thuc cung luc B ket thuc', thi A va B phai")
print("  chong lan; neu la 'b' (A hoan toan truoc B) thi khong the chong lan.")
ends = []
for doc, es in TR + VA:
    adj = adjof(es)
    for a, b, r in es:
        if r != "ENDS-ON": continue
        # look at shared neighbours to see whether a and b behave as overlapping
        shared = [c for c in set(adj[a]) & set(adj[b]) if c not in (a, b)]
        pat = Counter()
        for c in shared:
            pat[(adj[a][c], adj[c][b])] += 1
        ends.append((doc, a, b, pat))
print("    %d instance ENDS-ON, %d co hang xom chung" % (len(ends), sum(1 for e in ends if e[3])))
agg = Counter()
for _, _, _, pat in ends:
    for k, v in pat.items(): agg[k] += v
print("    Chu ky hang xom pho bien nhat:")
for k, v in agg.most_common(6):
    print("      %-34s %5d" % ("%s / %s" % k, v))

# consistency test: if ENDS-ON were {b,m} only, A BEFORE C and C BEFORE B is impossible
# for an ENDS-ON pair only when ... actually test both readings against the data
def test_mapping(mapping, name):
    """How often does one-step composition contradict the carried label?"""
    bad = tot = 0
    for doc, es in VA:
        adj = adjof(es)
        for a, b, r in es:
            if r not in mapping: continue
            imp = FULL
            for c in set(adj[a]) & set(adj[b]):
                if c in (a, b): continue
                sa = mapping.get(adj[a][c]); sb = mapping.get(adj[c][b])
                if sa and sb: imp = imp & compose(sa, sb)
            if imp == FULL: continue
            tot += 1
            if not (mapping[r] & imp): bad += 1
    return bad, tot

ALT = dict(MAVEN_TO_ALLEN)
ALT["ENDS-ON"] = frozenset({"f", "fi", "e"})   # "ends together" reading
print()
print("  So sanh hai cach doc ENDS-ON bang ty le MAU THUAN tren valid:")
for mp, nm in ((MAVEN_TO_ALLEN, "hien tai  {b, m}"), (ALT, "thay the  {f, fi, e}")):
    bad, tot = test_mapping(mp, nm)
    print("    %-22s %s/%s canh mau thuan = %.2f%%"
          % (nm, format(bad, ","), format(tot, ","), 100*bad/tot if tot else 0))

# how much ambiguity does each mapping leave?
print()
print("  Anh xa nao de lai it mo ho hon?")
for mp, nm in ((MAVEN_TO_ALLEN, "hien tai"), (ALT, "thay the")):
    st = Counter()
    for doc, es in VA:
        adj = adjof(es)
        for a, b, r in es:
            cs = [c for c in set(adj[a]) & set(adj[b]) if c not in (a, b)]
            if not cs: st["khong tam giac"] += 1; continue
            imp = FULL
            for c in cs:
                sa = mp.get(adj[a][c]); sb = mp.get(adj[c][b])
                if sa and sb: imp = imp & compose(sa, sb)
            adm = compat(imp, mp)
            st["%d nhan" % len(adm)] += 1
            if len(adm) == 1: st["  ep dung" if adm[0] == r else "  ep SAI"] += 1
    t = sum(v for k, v in st.items() if not k.startswith("  "))
    print("    %-10s " % nm + "  ".join("%s:%s(%.1f%%)" % (k, format(v, ","), 100*v/t)
          for k, v in sorted(st.items()) if not k.startswith("  ")))
    print("             ep dung %s / ep SAI %s"
          % (format(st.get("  ep dung", 0), ","), format(st.get("  ep SAI", 0), ",")))

# ================================================================ B. quintuples
print()
print("=" * 100)
print("B. BO 5 — them mot su kien trung gian thu ba")
print("=" * 100)

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

CAP = 6
def mine(order):
    """order = 3, 4 or 5 -> number of nodes in the configuration."""
    sig = defaultdict(Counter); sd = defaultdict(lambda: defaultdict(set))
    nmid = order - 2
    for doc, es in TR:
        adj = adjof(es)
        for a, b, r in es:
            mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
            if len(mids) < nmid: continue
            if nmid == 1:
                for c in mids: sig[(adj[a][c], adj[c][b])][r] += 1; sd[(adj[a][c], adj[c][b])][r].add(doc)
            elif nmid == 2:
                for i in range(len(mids)):
                    for j in range(i+1, len(mids)):
                        c, d = mids[i], mids[j]
                        k = (adj[a][c], adj[c][b], adj[a][d], adj[d][b])
                        sig[k][r] += 1; sd[k][r].add(doc)
            else:
                for i in range(len(mids)):
                    for j in range(i+1, len(mids)):
                        for l in range(j+1, len(mids)):
                            c, d, e2 = mids[i], mids[j], mids[l]
                            k = (adj[a][c], adj[c][b], adj[a][d], adj[d][b], adj[a][e2], adj[e2][b])
                            sig[k][r] += 1; sd[k][r].add(doc)
    R = {}
    for k, c in sig.items():
        n = sum(c.values()); top, kk = c.most_common(1)[0]
        if n < 30 or kk < 10 or len(sd[k][top]) < 5: continue
        w = wlb(kk, n)
        if w >= 0.50: R[k] = (top, w)
    return R, len(sig)

print("  khai thac ...", flush=True)
TRI, n3 = mine(3);  print("    bo 3: %s chu ky -> %s luat" % (format(n3, ","), format(len(TRI), ",")), flush=True)
QUAD, n4 = mine(4); print("    bo 4: %s chu ky -> %s luat" % (format(n4, ","), format(len(QUAD), ",")), flush=True)
QUINT, n5 = mine(5); print("    bo 5: %s chu ky -> %s luat" % (format(n5, ","), format(len(QUINT), ",")), flush=True)

def run(use3, use4, use5):
    gold = []; pred = []; fired = 0
    for doc, es in VA:
        adj = adjof(es)
        for a, b, r in es:
            gold.append(r)
            mids = sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
            v = Counter()
            if use3:
                for c in mids:
                    t = TRI.get((adj[a][c], adj[c][b]))
                    if t: v[t[0]] += t[1]
            if use4:
                for i in range(len(mids)):
                    for j in range(i+1, len(mids)):
                        c, d = mids[i], mids[j]
                        t = QUAD.get((adj[a][c], adj[c][b], adj[a][d], adj[d][b]))
                        if t: v[t[0]] += t[1]
            if use5:
                for i in range(len(mids)):
                    for j in range(i+1, len(mids)):
                        for l in range(j+1, len(mids)):
                            c, d, e2 = mids[i], mids[j], mids[l]
                            t = QUINT.get((adj[a][c], adj[c][b], adj[a][d], adj[d][b], adj[a][e2], adj[e2][b]))
                            if t: v[t[0]] += t[1]
            if v: fired += 1; pred.append(v.most_common(1)[0][0])
            else: pred.append("BEFORE")
    m, per, acc = macro(pred, gold)
    return m, per, acc, fired, len(gold)

print()
print("  %-22s%8s%10s%10s%9s" % ("cau hinh", "#luat", "macro-F1", "acc", "do phu"))
print("  " + "-" * 60)
res = {}
for nm, f3, f4, f5, cnt in (("bo 3", 1,0,0, len(TRI)),
                            ("bo 3 + 4", 1,1,0, len(TRI)+len(QUAD)),
                            ("bo 3 + 4 + 5", 1,1,1, len(TRI)+len(QUAD)+len(QUINT)),
                            ("chi bo 5", 0,0,1, len(QUINT))):
    m, per, acc, fired, tot = run(f3, f4, f5)
    res[nm] = (m, per, acc)
    print("  %-22s%8s%9.2f%%%9.2f%%%8.1f%%" % (nm, format(cnt, ","), 100*m, 100*acc, 100*fired/tot))
    print("    " + "  ".join("%s %.1f%%" % (r.split('-')[0][:4], 100*per[r]) for r in RELS))
