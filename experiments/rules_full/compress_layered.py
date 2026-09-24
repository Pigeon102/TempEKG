# -*- coding: utf-8 -*-
"""Compress the layered (step 2.2) rule sets -- per-layer patterns used as rules plus cross-layer
rules -- with the proof of rule_cover.py. The combiner overrides the step-2.1 label, so the fallback
of each row is its incoming label p, and rules may propose p itself (blocking other labels): those
rows are constraints too (rule_cover.constraints handles it). Input: src/artifacts/layered_dump_full.pkl
written by  TAG=_full DUMP=1 python experiments/higher_order/layered_rules.py."""
import io, sys, pickle, time
from pathlib import Path
from collections import Counter, defaultdict
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rule_cover as RC, json
SAVEK = {}
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
D = pickle.load(open(Path(r"C:\Reseach_Quang\tempekg\src\artifacts")/"layered_dump_full.pkl", "rb"))
print("=" * 110); print("RUT GON BO LUAT LIEN TANG (buoc 2.2) -- co chung minh (rule_cover.py)"); print("=" * 110)
TOT = defaultdict(int); POOL = defaultdict(lambda: defaultdict(list))
for gname, G in D.items():
    rules, TH = G["rules"], G["TH"]
    W = [cw for _, _, cw in rules]; REL = [r for _, r, _ in rules]
    ACT = [i for i, (key, r, cw) in enumerate(rules) if cw >= TH.get(r, 9)]
    idx = defaultdict(list)
    for i in ACT: idx[rules[i][0][0]].append(i)
    def hits(act):
        out = []
        for c in act:
            for i in idx.get(c, ()):
                if all(z in act for z in rules[i][0][1:]): out.append(i)
        return out
    rows = {sp: [(hits(a), p, g) for a, p, g in lst] for sp, lst in G["rows"].items()}
    classes = RC.equivalence(rows["disc"] + rows["conf1"] + rows["conf2"], REL, ACT)
    reps = {min(c, key=lambda i: (len(rules[i][0]), i)) for c in classes}
    build = [([i for i in h if i in reps], p, g) for h, p, g in rows["disc"] + rows["conf1"]]
    npat = sum(1 for key, _, _ in rules if len(key) == 1)
    print("\n %s: %d luat (%d pattern + %d lien tang), %d hoat dong (nguong %s), %d phat bieu khac nhau" %
          (gname, len(rules), npat, len(rules) - npat, len(ACT), {r[:4]: t for r, t in TH.items() if t < 9}, len(classes)))
    for vn, corr in (("day du", None), ("dai dien", "rep"), ("A: giu moi dau ra", False), ("B: giu dau ra dung", True)):
        if corr is None: K = set(ACT); info = ""
        elif corr == "rep": K = reps; info = ""
        else:
            el = RC.constraints(build, W, REL, corr)
            K, nf, lb, d = RC.cover(el, W); info = "vu tru %d, bat buoc %d, chan duoi %d" % (len(el), nf, lb)
        cells = []
        for sp in ("conf2", "valid"):
            pf = [RC.output(h, p, W, REL) for h, p, g in rows[sp]]; pk = [RC.output(h, p, W, REL, K) for h, p, g in rows[sp]]
            gold = [g for h, p, g in rows[sp]]
            ag = sum(1 for a, b in zip(pf, pk) if a == b)/len(pf)
            m, acc, per = RC.macro(pk, gold, RELS)
            cells.append("%s giu %.3f%% macro %.2f%% acc %.2f%%" % (sp, 100*ag, 100*m, 100*acc))
            if sp == "valid": POOL[vn]["pred"] += pk; POOL[vn]["gold"] += gold
        nk = sum(1 for i in K if len(rules[i][0]) == 1)
        if corr in (False, True): SAVEK.setdefault(gname, {})["A" if corr is False else "B"] = [{"key": list(rules[i][0]), "rel": rules[i][1], "w": rules[i][2]} for i in sorted(K)]
        print("   %-20s %5d luat (%d pattern + %d lien tang) | %s | %s" % (vn, len(K), nk, len(K) - nk, " | ".join(cells), info))
        TOT[vn] += len(K)
print()
for vn in ("day du", "dai dien", "A: giu moi dau ra", "B: giu dau ra dung"):
    m, acc, per = RC.macro(POOL[vn]["pred"], POOL[vn]["gold"], RELS)
    print(" GOP 4 loai canh, %-20s %5d luat  valid macro-F1 %.2f%%  acc %.2f%%" % (vn, TOT[vn], 100*m, 100*acc))

json.dump(SAVEK, io.open("C:/Reseach_Quang/tempekg/src/artifacts/rules_compact_layered.json", "w", encoding="utf-8"), ensure_ascii=False, default=list)
print("da luu rules_compact_layered.json")
