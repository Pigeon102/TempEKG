# -*- coding: utf-8 -*-
"""Appendix: every feature behind the EV-EV atomic conditions, counted from the encoded train cache and the
rule sets. Writes report/APPENDIX_DIEU_KIEN_NGUYEN_TU.md"""
import io, json, pickle
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
REP = HERE.parent.parent / "report"
d = pickle.load(open(HERE/"cache_ee.pkl", "rb"))
names = d["cond_names"]; T = d["train"]
rules = pickle.load(open(HERE/"rules_confirmed.pkl", "rb"))
cfg = json.load(io.open(HERE.parent.parent/"src"/"artifacts"/"rules_full.json", encoding="utf-8"))["config"]
compact = json.load(io.open(HERE.parent.parent/"src"/"artifacts"/"rules_compact.json", encoding="utf-8"))["variants"]["A: giu moi du doan"]
active = [r for r in rules if r["wlb"] >= cfg.get(r["rel"], 9)]

DESC = {  # attribute: (meaning, source, kind)
    "type_a": ("loại sự kiện của A", "MAVEN-ERE", "một giá trị"),
    "type_b": ("loại sự kiện của B", "MAVEN-ERE", "một giá trị"),
    "type_pair": ("cặp (loại A, loại B)", "MAVEN-ERE", "một giá trị"),
    "same_type": ("A và B cùng loại sự kiện", "MAVEN-ERE (so sánh)", "một giá trị"),
    "order": ("thứ tự: A trước / cùng câu / B trước", "MAVEN-ERE (vị trí)", "một giá trị"),
    "a_before_b": ("A xuất hiện trước B trong văn bản", "MAVEN-ERE (vị trí)", "một giá trị"),
    "sdist": ("khoảng cách câu: 0 / 1 / 2–3 / 4+", "MAVEN-ERE (vị trí)", "một giá trị"),
    "sent_gap": ("khoảng cách câu (cách chia thứ hai)", "MAVEN-ERE (vị trí)", "một giá trị"),
    "bucket_a": ("vị trí câu của A trong bài (đầu / sớm / giữa / cuối)", "MAVEN-ERE (vị trí)", "một giá trị"),
    "bucket_b": ("vị trí câu của B trong bài", "MAVEN-ERE (vị trí)", "một giá trị"),
    "multi_mention_a": ("A được nhắc nhiều lần", "MAVEN-ERE (đồng tham chiếu)", "một giá trị"),
    "multi_mention_b": ("B được nhắc nhiều lần", "MAVEN-ERE (đồng tham chiếu)", "một giá trị"),
    "mention_cmp": ("so sánh số lần nhắc của A và B", "MAVEN-ERE (đồng tham chiếu)", "một giá trị"),
    "nrole_a": ("số vai trò của A (tối đa 5)", "MAVEN-Arg", "một giá trị"),
    "nrole_b": ("số vai trò của B (tối đa 5)", "MAVEN-Arg", "một giá trị"),
    "has_person_a": ("A có tham số là người", "MAVEN-Arg", "một giá trị"),
    "has_person_b": ("B có tham số là người", "MAVEN-Arg", "một giá trị"),
    "has_org_a": ("A có tham số là tổ chức", "MAVEN-Arg", "một giá trị"),
    "has_org_b": ("B có tham số là tổ chức", "MAVEN-Arg", "một giá trị"),
    "has_loc_a": ("A có tham số là địa điểm", "MAVEN-Arg", "một giá trị"),
    "has_loc_b": ("B có tham số là địa điểm", "MAVEN-Arg", "một giá trị"),
    "shares_anchor": ("A và B có chung ít nhất một thực thể", "MAVEN-Arg (so sánh)", "một giá trị"),
    "n_anchor": ("số thực thể chung: 0 / 1 / 2+", "MAVEN-Arg (so sánh)", "một giá trị"),
    "role_overlap": ("A và B có chung tên vai trò", "MAVEN-Arg (so sánh)", "một giá trị"),
    "role_subset": ("tập vai trò của A nằm trong tập vai trò của B", "MAVEN-Arg (so sánh)", "một giá trị"),
    "roleset_a": ("tập vai trò của A", "MAVEN-Arg", "tập"),
    "roleset_b": ("tập vai trò của B", "MAVEN-Arg", "tập"),
    "roleset_shared": ("các vai trò có ở cả A và B", "MAVEN-Arg (so sánh)", "tập"),
    "etypeset_a": ("tập loại thực thể trong tham số của A", "MAVEN-Arg", "tập"),
    "etypeset_b": ("tập loại thực thể trong tham số của B", "MAVEN-Arg", "tập"),
    "etypeset_shared": ("loại thực thể có ở cả A và B", "MAVEN-Arg (so sánh)", "tập"),
    "anchor_roles": ("cặp vai trò (ở A, ở B) của mỗi thực thể chung", "MAVEN-Arg (so sánh)", "tập"),
}

n_atoms = Counter(n[1] for n in names)
forms = defaultdict(Counter)
for n in names: forms[n[1]][n[0]] += 1
cnt_pair = Counter()
for cs in T["conds"]:
    for c in cs: cnt_pair[names[c][1]] += 1
npairs = len(T["conds"]); avg = sum(len(cs) for cs in T["conds"]) / npairs
def used(rs):
    u = defaultdict(set)
    for r in rs:
        for c in r["conds"]: u[c[1]].add(json.dumps(c, ensure_ascii=False))
    return u
U_all, U_act, U_cmp = used(rules), used(active), used(compact)
ex = defaultdict(Counter)
for r in active:
    for c in r["conds"]: ex[c[1]][tuple(c)] += 1
def fmt(c):
    f, a, v = c
    if f == "EQ": return "%s = %s" % (a, v)
    if f == "HAS": return "%s ∋ %s" % (a, v)
    if f == "ALL": return "%s = {%s}" % (a, v)
    if f == "CNT": return "|%s| ≥ %s" % (a, v) if v else "%s rỗng" % a
    if f == "MIX": return "%s có ≥ 2 phần tử" % a
    if f == "REL": return "%s = %s" % (a, v)
    return str(c)

L = []
L.append("# Phụ lục: điều kiện nguyên tử của bộ luật cạnh sự kiện – sự kiện\n")
L.append("Số liệu đếm trực tiếp từ dữ liệu train đã mã hoá (`experiments/rules_full/cache_ee.pkl`, %s cặp) và từ ba bộ luật "
         "(54.719 luật sau xác nhận, %s luật được bật, 378 luật bộ gọn). Script: `experiments/rules_full/appendix_atoms.py`.\n" % (
             format(npairs, ",").replace(",", "."), format(len(active), ",").replace(",", ".")))
L.append("## 1. Điều kiện nguyên tử được tạo thế nào\n")
L.append("1. **Đặc trưng của cặp** (32 đặc trưng, bảng ở mục 2) được tính cho mỗi cặp (A, B) từ thuộc tính node trong KG, "
         "không đọc nhãn thời gian (`pair_features` trong `src/mine_compositional.py`, `relational_conditions` trong `src/mine_mdd.py`).")
L.append("2. **Mẫu sinh điều kiện** (`candidate_conditions`): đặc trưng một giá trị → `EQ` (thuộc tính = giá trị); đặc trưng tập → "
         "`HAS` (chứa v), `ALL` (chỉ gồm đúng v), `MIX` (≥ 2 phần tử), `CNT` (rỗng, hoặc có **ít nhất** 1 / 2 / 3 phần tử); "
         "so sánh hai sự kiện → `REL`.")
L.append("3. Mỗi cặp thoả trung bình **%s** điều kiện; toàn bộ train có **%s** điều kiện khác nhau.\n" % (("%.1f" % avg).replace(".", ","), format(len(names), ",").replace(",", ".")))
L.append("## 2. Từng đặc trưng\n")
L.append("| Đặc trưng | Nghĩa | Nguồn | Kiểu | Dạng sinh ra | Số điều kiện | Dùng trong 54.719 / bật / 378 luật | Ví dụ điều kiện hay dùng nhất (trong luật được bật) |")
L.append("|---|---|---|---|---|---|---|---|")
order = sorted(DESC, key=lambda a: (DESC[a][1].split()[0], -n_atoms[a]))
for a in order:
    m, src, kind = DESC[a]
    fm = ", ".join("%s %d" % (f, k) for f, k in forms[a].most_common())
    e = "; ".join(fmt(c) for c, _ in ex[a].most_common(2)) or "—"
    L.append("| `%s` | %s | %s | %s | %s | %s | %d / %d / %d | %s |" % (
        a, m, src, kind, fm, format(n_atoms[a], ",").replace(",", "."), len(U_all[a]), len(U_act[a]), len(U_cmp[a]), e))
tot = (len(names), sum(len(v) for v in U_all.values()), sum(len(v) for v in U_act.values()), sum(len(v) for v in U_cmp.values()))
L.append("| **Tổng** | | | | | **%s** | **%d / %d / %d** | |\n" % ((format(tot[0], ",").replace(",", "."),) + tot[1:]))
L.append("## 3. Theo nguồn dữ liệu\n")
bysrc = defaultdict(lambda: [0, 0, 0, 0, 0])
for a in DESC:
    s = "MAVEN-Arg" if DESC[a][1].startswith("MAVEN-Arg") else "MAVEN-ERE"
    x = bysrc[s]; x[0] += 1; x[1] += n_atoms[a]; x[2] += len(U_all[a]); x[3] += len(U_act[a]); x[4] += len(U_cmp[a])
L.append("| Nguồn | Số đặc trưng | Số điều kiện | Dùng trong 54.719 / bật / 378 luật |")
L.append("|---|---|---|---|")
for s, x in bysrc.items(): L.append("| %s | %d | %d | %d / %d / %d |" % (s, x[0], x[1], x[2], x[3], x[4]))
L.append("\nBỏ toàn bộ đặc trưng MAVEN-Arg (ablation, `STATUS.md` §39) còn 13 đặc trưng, 21.806 điều kiện, 8.559 luật; "
         "macro-F1 EV–EV 26,99% → 26,56%, cả Bài 1 30,84% → 30,74%.")
io.open(REP/"APPENDIX_DIEU_KIEN_NGUYEN_TU.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
print("ok", len(L))
