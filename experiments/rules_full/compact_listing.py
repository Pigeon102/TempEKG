# -*- coding: utf-8 -*-
"""Write report/RULES_COMPACT.md: the variant-A compact rule set (378 rules, same predictions as the
2,794 active rules on every train pair), grouped label -> family (template = condition forms and
attributes with the values abstracted). Rules that are also in variant B are marked."""
import io, json
from collections import defaultdict
from pathlib import Path
D = json.load(io.open(r"C:\Reseach_Quang\tempekg\src\artifacts\rules_compact.json", encoding="utf-8"))
A = D["variants"]["A: giu moi du doan"]; B = D["variants"]["B: giu moi du doan dung"]
sig = lambda x: (x["view"], json.dumps(x["sig"]), json.dumps(x["conds"]), x["rel"])
inB = {sig(x) for x in B}
def cond(c):
    f, a, v = c
    if isinstance(v, list): v = "(" + ", ".join(map(str, v)) + ")"
    return {"EQ": "%s = %s", "HAS": "%s ∋ %s", "ALL": "%s = {%s}", "CNT": "|%s| = %s", "REL": "%s = %s"}.get(f, "%s: %s") % (a, v) if f != "MIX" else "%s có ≥ 2 loại" % a
def tmpl(x): return " ∧ ".join("%s(%s)" % (c[0], c[1]) for c in sorted(x["conds"], key=lambda c: (c[0], c[1])))
out = ["# Bộ luật EV–EV gọn: 378 luật, cùng dự đoán với 54.719 luật", "",
       "Sinh tự động bởi `experiments/rules_full/compact_listing.py` từ `src/artifacts/rules_compact.json`.",
       "Cách rút gọn và chứng minh: `RULESET.md` mục 12. Mỗi họ = cùng nhãn, cùng dạng và thuộc tính điều kiện,",
       "khác giá trị. Cột *lớp* là view và lớp nơi luật áp dụng; `k/n` trên DISCOVERY, `ck/cn` trên",
       "CONFIRMATION-1; ★ = cũng nằm trong bộ 279 luật (biến thể B).", ""]
for rel in ("CONTAINS", "SIMULTANEOUS", "OVERLAP"):
    rs = [x for x in A if x["rel"] == rel]
    fam = defaultdict(list)
    for x in rs: fam[tmpl(x)].append(x)
    out += ["## %s — %d luật, %d họ" % (rel, len(rs), len(fam)), ""]
    for t, xs in sorted(fam.items(), key=lambda kv: (-len(kv[1]), -max(x["wlb"] for x in kv[1]))):
        out += ["### %s (%d)" % (t, len(xs)), "", "| | Lớp | Điều kiện | k/n | ck/cn | wlb |", "|---|---|---|---|---|---|"]
        for x in sorted(xs, key=lambda x: -x["wlb"]):
            s = x["sig"] if not isinstance(x["sig"], list) else "(" + ", ".join(map(str, x["sig"])) + ")"
            out.append("| %s | %s = %s | %s | %d/%d | %d/%d | %.3f |" % ("★" if sig(x) in inB else "", x["view"], s,
                       " ∧ ".join(cond(c) for c in x["conds"]), x["k"], x["n"], x["ck"], x["cn"], x["wlb"]))
        out.append("")
io.open(r"C:\Reseach_Quang\tempekg\report\RULES_COMPACT.md", "w", encoding="utf-8").write("\n".join(out))
print("ok", len(A), "luat A;", len(inB & {sig(x) for x in A}), "cung nam trong B")
