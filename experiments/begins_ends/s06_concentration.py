# -*- coding: utf-8 -*-
"""Why rules fail: document concentration, clique propagation, and text locality of the rare labels (TRAIN only)."""
import gzip, io
from collections import Counter, defaultdict
from common import *
perdoc = defaultdict(Counter); sd = defaultdict(Counter); nodeBO = defaultdict(Counter); edges = defaultdict(list)
with gzip.open(OUT/"features.tsv.gz", "rt", encoding="utf-8") as f:
    for l in f:
        sp, doc, s, t, et, g, at = l.rstrip("\n").split("\t")
        if sp == "3": continue
        A = at.split("|")
        sdv = [a for a in A if a.startswith("SD:")][0]
        sd[(et, g)][sdv] += 1
        if g in RARE:
            perdoc[g][doc] += 1
            nodeBO[(g, doc)][s] += 1; nodeBO[(g, doc)][t] += 1
            edges[g].append((doc, s, t, et))
L = io.open(OUT/"logs"/"s06_concentration.log", "w", encoding="utf-8")
def P(x=""): print(x); L.write(x + "\n")
for g in RARE:
    c = perdoc[g]; tot = sum(c.values()); top = sorted(c.values(), reverse=True)
    P("%s train: %d edges in %d docs; max %d in one doc; top-10 docs hold %d (%.1f%%); docs with 1 edge: %d"
      % (g, tot, len(c), top[0], sum(top[:10]), 100*sum(top[:10])/tot, sum(1 for v in top if v == 1)))
    shared = sum(1 for doc, s, t, et in edges[g] if nodeBO[(g, doc)][s] >= 2 or nodeBO[(g, doc)][t] >= 2)
    P("   edges sharing an endpoint with another %s edge (clique / fan propagation): %d (%.1f%%)" % (g, shared, 100*shared/tot))
P("\nSentence distance of the closest mention pair, per edge type and label (train)")
for et in ETYPES:
    for g in RELS:
        c = sd[(et, g)]; n = sum(c.values())
        if n == 0: continue
        P("  %s %-12s n=%7d  same sent %5.1f%%  adjacent %5.1f%%  2-3 %5.1f%%  4+ %5.1f%%" % (et, g, n, 100*c["SD:0"]/n, 100*c["SD:1"]/n, 100*c["SD:2-3"]/n, 100*c["SD:4+"]/n))
