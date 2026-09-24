# -*- coding: utf-8 -*-
"""Probe: what can 4-node subgraphs add beyond triangles?

A quad = 4 nodes with all 6 edges present; configuration = node kinds (in id order) + the 6
oriented labels. Gold statistics from a SAMPLE of quads (up to 300 per document) of the gold
train graphs used for triangle statistics (DISCOVERY + CONFIRMATION-1, first 400 docs out).

On the layered classifier's valid graph, the question is only about the errors that triangles
cannot see: wrong edges that sit in NO anomalous triangle (configuration unseen in gold). For
those edges, and for a sample of correct edges that are equally clean at triangle level, measure
how often they sit in a quad whose configuration is unseen in the gold sample. The ratio between
the two rates says whether quads carry detection signal where triangles are silent.
"""
import io, json, random
from pathlib import Path
from collections import Counter, defaultdict
HERE = Path(__file__).resolve().parent
SRC = io.open(HERE/"joint_repair.py", encoding="utf-8").read()
exec(SRC[:SRC.index("# ---------------------------------------------------------------- noise channels")])
rng = random.Random(5)

def quads_of_edge(d, lab, j, cap=200):
    a, b = d["edges"][j][0], d["edges"][j][1]
    nb = d["_nbr"]; common = sorted(nb[a] & nb[b])
    out = []
    for i in range(len(common)):
        for k in range(i+1, len(common)):
            c, e = common[i], common[k]
            if e in nb[c]:
                out.append(tuple(sorted((a, b, c, e))))
                if len(out) >= cap: return out
    return out

def qconfig(d, lab, nodes):
    K = d["_K"]; L = d["_L"]
    labs = []
    for i in range(4):
        for k in range(i+1, 4):
            labs.append(L[(nodes[i], nodes[k])])
    return tuple(K[n] for n in nodes) + tuple(labs)

def index_doc(d, lab):
    K = {n: ("E" if v.get("kind") == "event" else "T") for n, v in d["nd"].items() if v.get("kind") in ("event", "timex")}
    L = {}; nb = defaultdict(set)
    for (a, b, r, k), q in zip(d["edges"], lab):
        L[(a, b)] = q; L[(b, a)] = inv_(q); nb[a].add(b); nb[b].add(a)
    d["_K"], d["_L"], d["_nbr"] = K, L, nb

QF = Counter()
for d in STATS:
    lab = [e[2] for e in d["edges"]]; index_doc(d, lab)
    got = 0
    for j in rng.sample(range(len(d["edges"])), min(len(d["edges"]), 60)):
        for nodes in quads_of_edge(d, lab, j, cap=5):
            QF[qconfig(d, lab, nodes)] += 1; got += 1
        if got >= 300: break
log("mau quad gold: %d quad, %d cau hinh" % (sum(QF.values()), len(QF)))

wrong_clean = []; right_clean = []
for d in VA:
    lab = [PL.get("%s|%s|%s" % (d["id"], e[0], e[1]), "BEFORE") for e in d["edges"]]
    index_doc(d, lab)
    anom = set()
    for kinds, parts in d["tris"]:
        c = kinds + tuple(olab(lab[j], rev) for j, rev in parts)
        if FREQ.get(c, 0) == 0: anom.update(j for j, _ in parts)
    for j, e in enumerate(d["edges"]):
        if j in anom or not d["inc"].get(j): continue
        (wrong_clean if lab[j] != e[2] else right_clean).append((d, lab, j))
log("canh 'sach' o muc tam giac: sai %d, dung %d" % (len(wrong_clean), len(right_clean)))
right_clean = rng.sample(right_clean, min(len(right_clean), 20000))

def rate(items):
    hit = 0; nq = 0
    for d, lab, j in items:
        index_doc(d, lab)
        qs = quads_of_edge(d, lab, j)
        nq += len(qs)
        if any(QF.get(qconfig(d, lab, q), 0) == 0 for q in qs): hit += 1
    return hit / max(1, len(items)), nq / max(1, len(items))
rw, qw = rate(wrong_clean); rr, qr = rate(right_clean)
print()
print("CANH KHONG NAM TRONG TAM GIAC BAT THUONG NAO (classifier tang, valid):")
print("  canh sai : %.1f%% nam trong >=1 quad co cau hinh chua gap (trung binh %.0f quad/canh)" % (100*rw, qw))
print("  canh dung: %.1f%% (trung binh %.0f quad/canh)" % (100*rr, qr))
print("  ti so %.2fx" % (rw / max(1e-9, rr)))
log("xong")
