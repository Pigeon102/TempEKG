# -*- coding: utf-8 -*-
"""Compress the three TIMEX-edge rule sets (EV->TIMEX, TIMEX->EV, TIMEX-TIMEX) with the proof of
rule_cover.py. Rules and floors are rebuilt exactly as bai1_all_edges.py builds them (same mining,
same CONFIRMATION-2 floors); covers are built on DISCOVERY + CONFIRMATION-1, checked on CONF-2 and
on valid (opened once)."""
import io, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rule_cover as RC, json
SAVEK = {}
SRC_T = io.open(HERE.parent/"higher_order"/"bai1_all_edges.py", encoding="utf-8").read()
exec(SRC_T[:SRC_T.index("SAVE = {}")])

print(); print("=" * 110); print("RUT GON BO LUAT CANH TIMEX -- co chung minh (rule_cover.py)"); print("=" * 110)
SUMMARY = []
for grp, kinds in (("EV->TIMEX", ("ET",)), ("TIMEX->EV", ("TE",)), ("TIMEX-TIMEX", ("TT",))):
    tr = instances(TR, kinds); va = instances(VA, kinds)
    maj = Counter(x[4] for x in tr if x[1] == "disc").most_common(1)[0][0]
    R, prior = mine(tr, maj)
    c2 = [x for x in tr if x[1] == "conf2"]
    TH, mc = tune(R, maj, c2)
    RULES = [(key, r, cw) for r, lst in R.items() for cw, key in lst]
    W = [cw for _, _, cw in RULES]; REL = [r for _, r, _ in RULES]
    ACT = [i for i, (key, r, cw) in enumerate(RULES) if cw >= TH.get(r, 9)]
    idx = defaultdict(list)
    for i in ACT: idx[RULES[i][0][0]].append(i)
    def hits(x):
        cs = x[6]; out = []
        for c in cs:
            for i in idx.get(c, ()):
                key = RULES[i][0]
                if len(key) == 1 or key[1] in cs: out.append(i)
        return out
    rows = {sp: [(hits(x), maj, x[4]) for x in tr if x[1] == sp] for sp in ("disc", "conf1", "conf2")}
    rows["valid"] = [(hits(x), maj, x[4]) for x in va]
    # sanity: re-implemented combiner vs the script's classify()
    ref = classify(R, TH, maj, va)
    same = sum(1 for (h, fb, g), p in zip(rows["valid"], ref) if RC.output(h, fb, W, REL) == p)/len(va)
    classes = RC.equivalence(rows["disc"] + rows["conf1"] + rows["conf2"], REL, ACT)
    reps = {min(c, key=lambda i: (len(RULES[i][0]), i)) for c in classes}
    build = rows["disc"] + rows["conf1"]
    print("\n %s: %d luat qua cong, %d hoat dong (nguong %s), %d phat bieu khac nhau; khop classify %.3f%%" %
          (grp, len(RULES), len(ACT), {r[:4]: t for r, t in TH.items() if t < 9}, len(classes), 100*same))
    for vn, corr in (("day du", None), ("dai dien", "rep"), ("A: giu moi dau ra", False), ("B: giu dau ra dung", True)):
        if corr is None: K = set(ACT); info = ""
        elif corr == "rep": K = reps; info = ""
        else:
            el = RC.constraints([([i for i in h if i in reps], fb, g) for h, fb, g in build], W, REL, corr)
            K, nf, lb, d = RC.cover(el, W); info = "vu tru %d, bat buoc %d, chan duoi %d" % (len(el), nf, lb)
        cells = []
        for sp in ("conf2", "valid"):
            pf = [RC.output(h, fb, W, REL) for h, fb, g in rows[sp]]; pk = [RC.output(h, fb, W, REL, K) for h, fb, g in rows[sp]]
            gold = [g for h, fb, g in rows[sp]]
            ag = sum(1 for a, b in zip(pf, pk) if a == b)/len(pf)
            m, acc, per = RC.macro(pk, gold, RELS)
            cells.append("%s giu %.3f%% macro %.2f%% acc %.2f%%" % (sp, 100*ag, 100*m, 100*acc))
        if corr in (False, True): SAVEK.setdefault(grp, {})["A" if corr is False else "B"] = [{"key": list(RULES[i][0]), "rel": RULES[i][1], "w": RULES[i][2]} for i in sorted(K)]
        print("   %-20s %4d luat | %s | %s" % (vn, len(K), " | ".join(cells), info))
        SUMMARY.append((grp, vn, len(K)))
print()
print(" TOM TAT: " + "; ".join("%s %s %d" % s for s in SUMMARY))
log("xong")

json.dump(SAVEK, io.open("C:/Reseach_Quang/tempekg/src/artifacts/rules_compact_timex.json", "w", encoding="utf-8"), ensure_ascii=False, default=list)
print("da luu rules_compact_timex.json")
