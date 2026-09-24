# -*- coding: utf-8 -*-
"""Freeze the Bai 1 classifier chosen in semantic_combo.py (257 rules + LEX rules, strict gate,
delta 0.05, tau 5) and export its predictions for every train and valid EV-EV pair, so Bai 2
can audit the new classifier's graph."""
import io, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_ST = io.open(HERE/"semantic_tracks.py", encoding="utf-8").read()
exec(SRC_ST[:SRC_ST.index('print("BAI 1 -- TRACK')])
R = mine(["LEX"], "strict")
R = {k: v for k, v in R.items() if v[1] > CLF[v[0]] + 0.05}
log("LEX delta 0.05: %d luat" % len(R))
json.dump([{"cond": list(k[0]), "and": (list(k[1]) if k[1] is not None else None), "rel": r, "cwlb": cw}
           for k, (r, cw) in R.items()],
          io.open(ART/"rules_lex_d05.json", "w", encoding="utf-8"), ensure_ascii=False, default=list)
byc = defaultdict(list)
for (c, x), (r, cw) in R.items(): byc[c].append((x, r, cw/PRIOR[r]))
out = {}
for d in TR + VA:
    for i, ((a, b, g, cs, w), sc0) in enumerate(zip(d["ee"], d["ps"])):
        sc = dict(sc0); N = conds_of(d, i, ["LEX"]); allc = set(cs) | set(N)
        for c in set(N):
            for x, r, v in byc.get(c, ()):
                if (x is None or x in allc) and v > sc.get(r, 0): sc[r] = v
        out["%s|%s|%s" % (d["id"], a, b)] = predict(sc, 5)
json.dump(out, io.open(ART/"pred_lex_d05.json", "w", encoding="utf-8"))
m, per = prf([out["%s|%s|%s" % (d["id"], e[0], e[1])] for d in VA for e in d["ee"]], gV)
log("valid macro-F1 %.2f%% -- da luu %d du doan" % (100*m, len(out)))
