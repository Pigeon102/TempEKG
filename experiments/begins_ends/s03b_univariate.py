# -*- coding: utf-8 -*-
"""Exploratory, DISCOVERY only: single atoms most enriched for BEGINS-ON / ENDS-ON per edge type,
and the size of the positive-atom universe (to size the conjunction search)."""
import gzip, io
from collections import Counter, defaultdict
from common import *
pos = defaultdict(Counter); tot = defaultdict(Counter); N = Counter(); K = Counter()
rows_atoms = defaultdict(list)
with gzip.open(OUT/"features.tsv.gz", "rt", encoding="utf-8") as f:
    for l in f:
        sp, doc, s, t, et, g, at = l.rstrip("\n").split("\t")
        if sp != "0": continue
        at = at.split("|"); N[et] += 1
        for a in at: tot[et][a] += 1
        if g in RARE:
            K[(et, g)] += 1
            for a in at: pos[(et, g)][a] += 1
L = io.open(OUT/"logs"/"s03b_univariate.log", "w", encoding="utf-8")
for (et, g), c in sorted(pos.items()):
    L.write("\n%s %s: %d positives / %d edges (prior %.5f)\n" % (et, g, K[(et, g)], N[et], K[(et, g)]/N[et]))
    sc = sorted(((wlb(k, tot[et][a]), k, tot[et][a], a) for a, k in c.items() if k >= 3), reverse=True)[:25]
    for w, k, n, a in sc:
        L.write("   wlb %.4f  %4d/%-7d  %s\n" % (w, k, n, a))
    L.write("   atoms with >=3 positives: %d\n" % sum(1 for a, k in c.items() if k >= 3))
L.close()
print(io.open(OUT/"logs"/"s03b_univariate.log", encoding="utf-8").read())
