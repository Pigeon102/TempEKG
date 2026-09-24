# -*- coding: utf-8 -*-
"""Direction check (TRAIN only): calendar relation and text order of TIMEX-TIMEX rare edges (head = stored s)."""
import gzip, io
from collections import Counter, defaultdict
from common import *
c = defaultdict(Counter)
with gzip.open(OUT/"features.tsv.gz", "rt", encoding="utf-8") as f:
    for l in f:
        sp, doc, s, t, et, g, at = l.rstrip("\n").split("\t")
        if sp == "3" or g not in RARE: continue
        A = set(at.split("|"))
        key = (et, g); c[key]["n"] += 1
        for a in A:
            if a.startswith("CAL:") or a.startswith("ORD:"): c[key][a] += 1
L = io.open(OUT/"logs"/"s06b_direction.log", "w", encoding="utf-8")
for key in sorted(c):
    line = "%s %s n=%d: " % (key[0], key[1], c[key]["n"]) + ", ".join("%s %d" % (a, v) for a, v in sorted(c[key].items(), key=lambda z: -z[1]) if a != "n")
    print(line); L.write(line + "\n")
