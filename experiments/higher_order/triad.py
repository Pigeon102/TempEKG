# -*- coding: utf-8 -*-
"""Which triangle rules are NEW, and which are just Allen composition restated?

A triangle signature (a-c, c-b) -> (a-b) can hold for two very different reasons:

  FORCED    Allen composition of the two known edges already pins the answer. The rule
            is a theorem; it holds in any corpus and adds nothing to what the algebra
            says. Precision 100% is guaranteed, not evidence.

  LEARNED   Composition leaves several labels possible and the corpus concentrates on
            one of them. THIS is a rule the algebra does not give you -- an empirical
            regularity of how people annotate events, verifiable from documents.

Only LEARNED rules are a contribution over the published constraint set. This measures
both, keeps them apart, and reports each learned rule with a Wilson bound and the
number of distinct documents behind it -- because a pattern from three documents is
not a rule, as the pair-level experiment already showed.

Also extends to quadruples: for triangles whose composition stays ambiguous, does a
fourth event resolve them?
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
    p = k / n
    return (p + Z*Z/(2*n) - Z*math.sqrt(p*(1-p)/n + Z*Z/(4*n*n))) / (1 + Z*Z/n)

def compatible(aset):
    """MAVEN labels whose Allen set still intersects `aset`."""
    return [r for r, a in MAVEN_TO_ALLEN.items() if a & aset]

def load(path, limit=0):
    docs = []
    for i, line in enumerate(io.open(path, encoding="utf-8")):
        if limit and i >= limit: break
        if not line.strip(): continue
        rec = json.loads(line)
        nodes = rec["nodes"]
        es = [(e["s"], e["t"], e["rel"]) for e in rec["target_edges"]
              if nodes.get(e["s"], {}).get("kind") == "event"
              and nodes.get(e["t"], {}).get("kind") == "event"]
        if es: docs.append((rec["doc_id"], es))
    return docs

TR = load(GRAPH / "train.jsonl", 400)
VA = load(GRAPH / "valid.jsonl", 0)
print("train %d doc, valid %d doc" % (len(TR), len(VA)), flush=True)

def triangles(docs):
    """(rel_ac, rel_cb) -> Counter{rel_ab}, plus the documents each combination came from."""
    sig = defaultdict(Counter)
    sigdoc = defaultdict(lambda: defaultdict(set))
    for doc, es in docs:
        adj = defaultdict(dict)
        for a, b, r in es:
            adj[a][b] = r
            adj[b][a] = r
        for a, b, r in es:
            for c in set(adj[a]) & set(adj[b]):
                if c in (a, b): continue
                key = (adj[a][c], adj[c][b])
                sig[key][r] += 1
                sigdoc[key][r].add(doc)
    return sig, sigdoc

print("dem tam giac ...", flush=True)
sig_tr, doc_tr = triangles(TR)
sig_va, doc_va = triangles(VA)
print("train %d chu ky, valid %d chu ky" % (len(sig_tr), len(sig_va)), flush=True)

# ---------------------------------------------------------------- classify each signature
print()
print("=" * 100)
print("1. MOI CHU KY TAM GIAC: toan hoc ep duoc hay khong?")
print("=" * 100)

rows = []
for key, cnt in sig_tr.items():
    rac, rcb = key
    sa, sb = MAVEN_TO_ALLEN.get(rac), MAVEN_TO_ALLEN.get(rcb)
    if not sa or not sb: continue
    implied = compose(sa, sb)          # what the algebra allows for (a,b)
    adm = compatible(implied)          # MAVEN labels still possible
    n = sum(cnt.values())
    top, k = cnt.most_common(1)[0]
    rows.append(dict(key=key, n=n, top=top, k=k, adm=adm, nadm=len(adm),
                     implied=implied, cnt=cnt,
                     ndoc=len(doc_tr[key][top])))

forced = [r for r in rows if r["nadm"] == 1]
amb    = [r for r in rows if r["nadm"] > 1]
none_  = [r for r in rows if r["nadm"] == 0]
print("  %d chu ky co du lieu train" % len(rows))
print("    toan hoc EP ra 1 nhan (forced):        %4d" % len(forced))
print("    toan hoc de NGO nhieu nhan (learned):  %4d" % len(amb))
print("    thu hep ve nghich dao MAVEN khong co:  %4d" % len(none_))

# do the forced ones actually hold?
if forced:
    ok = sum(1 for r in forced if r["top"] == r["adm"][0])
    nn = sum(r["n"] for r in forced)
    kk = sum(r["cnt"][r["adm"][0]] for r in forced)
    print()
    print("  Kiem chung nhom FORCED: %d/%d chu ky co nhan pho bien nhat dung bang nhan bi ep"
          % (ok, len(forced)))
    print("  Tren toan bo instance: %s/%s = %.2f%% khop voi dai so"
          % (format(kk, ","), format(nn, ","), 100*kk/nn if nn else 0))

# ---------------------------------------------------------------- learned rules
print()
print("=" * 100)
print("2. LUAT HOC DUOC — dai so de ngo, du lieu chot mot nhan")
print("=" * 100)
print("   (mine tren TRAIN, kiem chung tren VALID; doc = so document khac nhau)")
print()

cand = []
for r in amb:
    n, k, top = r["n"], r["k"], r["top"]
    if n < 30 or k < 10: continue
    p = k / n
    w = wlb(k, n)
    if w < 0.50: continue
    cv = sig_va.get(r["key"])
    kv = cv[top] if cv else 0
    nv = sum(cv.values()) if cv else 0
    cand.append((w, r, p, kv, nv))
cand.sort(key=lambda t: -t[0])

print("  %-42s %7s %6s %5s  | %8s %6s" % ("(a-c, c-b) -> (a-b)", "train P", "n", "doc", "valid P", "nv"))
print("  " + "-" * 92)
kept = []
for w, r, p, kv, nv in cand[:22]:
    rac, rcb = r["key"]
    lbl = "%s,%s -> %s" % (rac[:4], rcb[:4], r["top"][:4])
    pv = kv / nv if nv else 0
    mark = " " if nv >= 20 and pv >= 0.5 else ("!" if nv >= 20 else "?")
    print("  %-42s %6.1f%% %6s %5d  | %7.1f%% %6s %s"
          % (lbl, 100*p, format(r["n"], ","), r["ndoc"], 100*pv, format(nv, ","), mark))
    kept.append((r, p, pv, nv))
print()
print("  ! = khong giu duoc tren valid    ? = qua it du lieu valid de ket luan")

# ---------------------------------------------------------------- how much is forced overall
print()
print("=" * 100)
print("3. BAO NHIEU PHAN CANH DUOC TAM GIAC QUYET DINH?")
print("=" * 100)
stat = Counter()
for doc, es in VA:
    adj = defaultdict(dict)
    for a, b, r in es:
        adj[a][b] = r; adj[b][a] = r
    for a, b, r in es:
        cs = [c for c in set(adj[a]) & set(adj[b]) if c not in (a, b)]
        if not cs:
            stat["khong co tam giac"] += 1
            continue
        # intersect what every triangle allows
        imp = FULL
        for c in cs:
            sa = MAVEN_TO_ALLEN.get(adj[a][c]); sb = MAVEN_TO_ALLEN.get(adj[c][b])
            if not sa or not sb: continue
            imp = imp & compose(sa, sb)
        adm = compatible(imp)
        if len(adm) == 0: stat["mau thuan / ngoai MAVEN"] += 1
        elif len(adm) == 1:
            stat["EP ra 1 nhan"] += 1
            stat["  -> dung" if adm[0] == r else "  -> SAI"] += 1
        else:
            stat["con %d nhan" % len(adm)] += 1
tot = sum(v for k, v in stat.items() if not k.startswith("  "))
for k, v in sorted(stat.items(), key=lambda kv: -kv[1]):
    if k.startswith("  "):
        print("    %-28s %8s" % (k, format(v, ",")))
    else:
        print("  %-30s %8s  %5.1f%%" % (k, format(v, ","), 100*v/tot))
