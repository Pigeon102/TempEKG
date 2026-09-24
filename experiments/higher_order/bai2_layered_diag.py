# -*- coding: utf-8 -*-
"""Why do EV-EV and EV->TIMEX edges never change in bai2_layered.py? Injected noise 10%, auditor A
(GRAPH only): rules per partition, their bounds, the floors chosen, and what per-(edge type, label)
floors would give instead of one floor per label shared by all edge types."""
import io
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_B = io.open(HERE/"bai2_layered.py", encoding="utf-8").read()
exec(SRC_B[:SRC_B.index('print("=" * 130)')])
exec(SRC_B[SRC_B.index("prior_k = defaultdict(Counter)"):SRC_B.index("discs = [x for x in ITR")])
discs = [x for x in ITR if x["sp"] == "disc"]; c1s = [x for x in ITR if x["sp"] == "conf1"]; c2s = [x for x in ITR if x["sp"] == "conf2"]
corrupt(ITR, 0.10, 31, "nz"); corrupt(IVA, 0.10, 37, "nz"); set_graph("nz")
AR = audit_rules(discs, c1s, "nz", ("GRAPH",), False)
print("luat theo phan vung (loai canh, nhan hien tai):")
for part, (PAT, rules) in sorted(AR.items()):
    by = Counter(r for _, r, _ in rules); top = sorted((cw for _, _, cw in rules), reverse=True)[:3]
    print("  %-22s %4d luat %s  cwlb cao nhat %s" % (part, len(rules), dict(by), [round(t, 3) for t in top]))
idx = rule_index(AR); activate(c2s + IVA, AR, "nz", ("GRAPH",))
TH = tune(idx, c2s, "nz", "net"); print("nguong chung theo nhan:", TH)
n_act = Counter(x["k"] for x in IVA if x["act"]); print("instance valid co pattern bat:", dict(n_act))

def classify_k(idx, TH, xs, field):
    out = []
    for x in xs:
        best = None
        for c in x["act"]:
            for key, r, cw in idx.get(c, ()):
                if cw >= TH.get((x["k"], r), 9) and all(z in x["act"] for z in key[1:]) and (best is None or cw > best[1]): best = (r, cw)
        out.append(best[0] if best else x[field])
    return out
def tune_k(idx, xs, field):
    keys = sorted({(x["k"], r) for x in xs for c in x["act"] for _, r, _ in idx.get(c, ())})
    TH = {k: 9 for k in keys}
    def val(T):
        c, P, R, F, m = score(xs, classify_k(idx, T, xs, field), field); return c["bad0"] - c["bad1"]
    best = val(TH)
    for _ in range(2):
        for k in keys:
            for t in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 9):
                T2 = dict(TH); T2[k] = t; v = val(T2)
                if v > best: best, TH = v, T2
    return TH
THk = tune_k(idx, c2s, "nz"); print("nguong theo (loai canh, nhan):", {k: v for k, v in THk.items() if v < 9})
show("A, nguong chung theo nhan", IVA, "nz", classify_override(idx, TH, [x["act"] for x in IVA], [x["nz"] for x in IVA]))
show("A, nguong theo (loai canh, nhan)", IVA, "nz", classify_k(idx, THk, IVA, "nz"))
log("xong")
