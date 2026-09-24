# -*- coding: utf-8 -*-
"""Follow-up to semantic_tracks.py: the naive union of tracks lost the gains (CONTAINS
precision 39.8% -> 32.7%). Choose the track subset and a stricter margin on CONFIRMATION,
then open VALID once. Rules are mined once per subset under the strict gate; the margin
keeps only rules whose confirmation Wilson bound beats the classifier by at least delta."""
import io
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_ST = io.open(HERE/"semantic_tracks.py", encoding="utf-8").read()
exec(SRC_ST[:SRC_ST.index('print("BAI 1 -- TRACK')])

SUBSETS = [("LEX", ["LEX"]), ("DUR", ["DUR"]), ("LEX+DUR", ["LEX", "DUR"]),
           ("LEX+DUR+CONN", ["LEX", "DUR", "CONN"]), ("LEX+DUR+GRP+CONN", ["LEX", "DUR", "GRP", "CONN"])]
DELTAS = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30)
TAUS = (5, 10, 20)
print()
print("=" * 110)
print("CHON (tap track, delta, tau) tren CONFIRMATION; base valid %.2f%%" % (100*m0))
print("=" * 110)
best = None; mined = {}
for nm, tr in SUBSETS:
    R = mine(tr, "strict"); mined[nm] = R
    for dl in DELTAS:
        Rd = {k: v for k, v in R.items() if v[1] > CLF[v[0]] + dl}
        if not Rd: continue
        for tau in TAUS:
            mc, _, _, _ = apply(Rd, CONF, tr, tau)
            if best is None or mc > best[0]: best = (mc, nm, tr, dl, tau)
        mc5, _, _, _ = apply(Rd, CONF, tr, 5)
        print("  %-18s delta %.2f  %5d luat  conf macro (tau 5) %.2f%%" % (nm, dl, len(Rd), 100*mc5), flush=True)
mc, nm, tr, dl, tau = best
print("  -> chon: %s, delta %.2f, tau %d (conf %.2f%%)" % (nm, dl, tau, 100*mc))
Rd = {k: v for k, v in mined[nm].items() if v[1] > CLF[v[0]] + dl}
m, per, ch, ok = apply(Rd, VA, tr, tau)
print()
print("VALID (mo mot lan): %s  %d luat  macro-F1 %.2f%% (%+.2f)  doi %d dung %.1f%%" % (nm, len(Rd), 100*m, 100*(m-m0), ch, 100*ok/max(1, ch)))
for r in RELS:
    print("   %-13s P %6.2f%%  R %6.2f%%  F1 %6.2f%%   (base F1 %6.2f%%)" % (r, 100*per[r][0], 100*per[r][1], 100*per[r][2], 100*per0[r][2]))
print()
print("Doi chieu tren valid (khong dung de chon), cung delta/tau:")
for nm2, tr2 in SUBSETS:
    R2 = {k: v for k, v in mined[nm2].items() if v[1] > CLF[v[0]] + dl}
    if R2:
        m2, _, c2, o2 = apply(R2, VA, tr2, tau)
        print("   %-18s %5d luat  macro %.2f%% (%+.2f)  doi %5d dung %.1f%%" % (nm2, len(R2), 100*m2, 100*(m2-m0), c2, 100*o2/max(1, c2)))
log("xong")
