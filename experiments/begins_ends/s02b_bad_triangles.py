# -*- coding: utf-8 -*-
"""List the triangles that violate ENDS-ON = meets (a.e = c.s): BEFORE-chains of length 2 around an ENDS-ON edge."""
import io
from collections import defaultdict
from common import *
out = io.open(OUT/"logs"/"s02b_bad_triangles.log", "w", encoding="utf-8")
raw = {}
bad = []
for split in ("train", "valid"):
    for rec in iter_kg(split):
        L = {(e["s"], e["t"]): e["rel"] for e in rec["target_edges"]}
        if "ENDS-ON" not in L.values(): continue
        nd = rec["nodes"]
        for (a, c), r in L.items():
            if r != "ENDS-ON": continue
            for (u, x), r1 in L.items():
                if u == a and r1 == "BEFORE" and L.get((x, c)) == "BEFORE":
                    bad.append((split, rec["doc_id"], rec["title"], a, x, c, nd))
for split, doc, title, a, x, c, nd in bad:
    d = lambda n: (nd[n].get("trigger") or nd[n].get("text"), nd[n]["sent_first"])
    out.write("%s %s %s | ENDS-ON(%s) but BEFORE(a,%s) and BEFORE(%s,c)\n" % (split, doc[:8], title, d(a) + d(c), d(x), d(x)))
out.write("total %d violating (a,x,c) chains in %d documents\n" % (len(bad), len({b[1] for b in bad})))
out.close()
print(io.open(OUT/"logs"/"s02b_bad_triangles.log", encoding="utf-8").read())
