# Phụ lục: điều kiện nguyên tử của bộ luật cạnh sự kiện – sự kiện

Số liệu đếm trực tiếp từ dữ liệu train đã mã hoá (`experiments/rules_full/cache_ee.pkl`, 483.504 cặp) và từ ba bộ luật (54.719 luật sau xác nhận, 2.794 luật được bật, 378 luật bộ gọn). Script: `experiments/rules_full/appendix_atoms.py`.

## 1. Điều kiện nguyên tử được tạo thế nào

1. **Đặc trưng của cặp** (32 đặc trưng, bảng ở mục 2) được tính cho mỗi cặp (A, B) từ thuộc tính node trong KG, không đọc nhãn thời gian (`pair_features` trong `src/mine_compositional.py`, `relational_conditions` trong `src/mine_mdd.py`).
2. **Mẫu sinh điều kiện** (`candidate_conditions`): đặc trưng một giá trị → `EQ` (thuộc tính = giá trị); đặc trưng tập → `HAS` (chứa v), `ALL` (chỉ gồm đúng v), `MIX` (≥ 2 phần tử), `CNT` (rỗng, hoặc có **ít nhất** 1 / 2 / 3 phần tử); so sánh hai sự kiện → `REL`.
3. Mỗi cặp thoả trung bình **48,8** điều kiện; toàn bộ train có **27.491** điều kiện khác nhau.

## 2. Từng đặc trưng

| Đặc trưng | Nghĩa | Nguồn | Kiểu | Dạng sinh ra | Số điều kiện | Dùng trong 54.719 / bật / 378 luật | Ví dụ điều kiện hay dùng nhất (trong luật được bật) |
|---|---|---|---|---|---|---|---|
| `anchor_roles` | cặp vai trò (ở A, ở B) của mỗi thực thể chung | MAVEN-Arg (so sánh) | tập | HAS 2881, ALL 2047, CNT 4, MIX 1 | 4.933 | 91 / 37 / 31 | anchor_roles ∋ ('Loser', 'Patient'); anchor_roles ∋ ('Location', 'Location') |
| `roleset_b` | tập vai trò của B | MAVEN-Arg | tập | HAS 143, ALL 86, CNT 4, MIX 1 | 234 | 73 / 27 / 22 | roleset_b ∋ Event; roleset_b ∋ Name |
| `roleset_a` | tập vai trò của A | MAVEN-Arg | tập | HAS 142, ALL 85, CNT 4, MIX 1 | 232 | 49 / 17 / 16 | roleset_a ∋ Event; roleset_a ∋ Loser |
| `roleset_shared` | các vai trò có ở cả A và B | MAVEN-Arg (so sánh) | tập | HAS 130, ALL 67, CNT 4, MIX 1 | 202 | 31 / 18 / 14 | roleset_shared ∋ Event; roleset_shared ∋ Name |
| `etypeset_a` | tập loại thực thể trong tham số của A | MAVEN-Arg | tập | HAS 6, ALL 6, CNT 4, MIX 1 | 17 | 16 / 14 / 10 | etypeset_a = {Location}; etypeset_a ∋ Location |
| `etypeset_b` | tập loại thực thể trong tham số của B | MAVEN-Arg | tập | HAS 6, ALL 6, CNT 4, MIX 1 | 17 | 17 / 9 / 7 | |etypeset_b| ≥ 3; etypeset_b ∋ Building |
| `etypeset_shared` | loại thực thể có ở cả A và B | MAVEN-Arg (so sánh) | tập | HAS 6, ALL 6, CNT 4, MIX 1 | 17 | 16 / 12 / 8 | etypeset_shared ∋ Building; |etypeset_shared| ≥ 2 |
| `nrole_a` | số vai trò của A (tối đa 5) | MAVEN-Arg | một giá trị | EQ 6 | 6 | 6 / 6 / 5 | nrole_a = 5; nrole_a = 1 |
| `nrole_b` | số vai trò của B (tối đa 5) | MAVEN-Arg | một giá trị | EQ 6 | 6 | 6 / 4 / 4 | nrole_b = 5; nrole_b = 4 |
| `n_anchor` | số thực thể chung: 0 / 1 / 2+ | MAVEN-Arg (so sánh) | một giá trị | REL 3 | 3 | 2 / 1 / 0 | n_anchor = 2+ |
| `has_person_a` | A có tham số là người | MAVEN-Arg | một giá trị | EQ 2 | 2 | 2 / 1 / 0 | has_person_a = True |
| `has_person_b` | B có tham số là người | MAVEN-Arg | một giá trị | EQ 2 | 2 | 2 / 2 / 1 | has_person_b = True; has_person_b = False |
| `has_org_a` | A có tham số là tổ chức | MAVEN-Arg | một giá trị | EQ 2 | 2 | 2 / 2 / 1 | has_org_a = False; has_org_a = True |
| `has_org_b` | B có tham số là tổ chức | MAVEN-Arg | một giá trị | EQ 2 | 2 | 2 / 2 / 1 | has_org_b = False; has_org_b = True |
| `has_loc_a` | A có tham số là địa điểm | MAVEN-Arg | một giá trị | EQ 2 | 2 | 2 / 2 / 1 | has_loc_a = True; has_loc_a = False |
| `has_loc_b` | B có tham số là địa điểm | MAVEN-Arg | một giá trị | EQ 2 | 2 | 2 / 2 / 1 | has_loc_b = True; has_loc_b = False |
| `shares_anchor` | A và B có chung ít nhất một thực thể | MAVEN-Arg (so sánh) | một giá trị | EQ 2 | 2 | 1 / 1 / 1 | shares_anchor = True |
| `role_overlap` | A và B có chung tên vai trò | MAVEN-Arg (so sánh) | một giá trị | REL 2 | 2 | 2 / 2 / 0 | role_overlap = True; role_overlap = False |
| `role_subset` | tập vai trò của A nằm trong tập vai trò của B | MAVEN-Arg (so sánh) | một giá trị | REL 2 | 2 | 2 / 2 / 1 | role_subset = True; role_subset = False |
| `type_pair` | cặp (loại A, loại B) | MAVEN-ERE | một giá trị | EQ 21439 | 21.439 | 238 / 54 / 37 | type_pair = ('Competition', 'Competition'); type_pair = ('Damaging', 'Destroying') |
| `type_a` | loại sự kiện của A | MAVEN-ERE | một giá trị | EQ 167 | 167 | 51 / 13 / 9 | type_a = Military_operation; type_a = Competition |
| `type_b` | loại sự kiện của B | MAVEN-ERE | một giá trị | EQ 167 | 167 | 86 / 27 / 21 | type_b = Bodily_harm; type_b = Military_operation |
| `sdist` | khoảng cách câu: 0 / 1 / 2–3 / 4+ | MAVEN-ERE (vị trí) | một giá trị | EQ 5 | 5 | 5 / 4 / 0 | sdist = 0; sdist = 2-3 |
| `same_type` | A và B cùng loại sự kiện | MAVEN-ERE (so sánh) | một giá trị | EQ 2, REL 2 | 4 | 4 / 4 / 2 | same_type = True; same_type = True |
| `sent_gap` | khoảng cách câu (cách chia thứ hai) | MAVEN-ERE (vị trí) | một giá trị | REL 4 | 4 | 4 / 4 / 1 | sent_gap = 0; sent_gap = 4+ |
| `bucket_a` | vị trí câu của A trong bài (đầu / sớm / giữa / cuối) | MAVEN-ERE (vị trí) | một giá trị | EQ 4 | 4 | 4 / 3 / 2 | bucket_a = lead; bucket_a = early |
| `bucket_b` | vị trí câu của B trong bài | MAVEN-ERE (vị trí) | một giá trị | EQ 4 | 4 | 4 / 4 / 3 | bucket_b = early; bucket_b = lead |
| `order` | thứ tự: A trước / cùng câu / B trước | MAVEN-ERE (vị trí) | một giá trị | EQ 3 | 3 | 3 / 3 / 2 | order = same; order = rev |
| `mention_cmp` | so sánh số lần nhắc của A và B | MAVEN-ERE (đồng tham chiếu) | một giá trị | REL 3 | 3 | 3 / 2 / 1 | mention_cmp = a>b; mention_cmp = a<b |
| `a_before_b` | A xuất hiện trước B trong văn bản | MAVEN-ERE (vị trí) | một giá trị | REL 2 | 2 | 2 / 1 / 1 | a_before_b = False |
| `multi_mention_a` | A được nhắc nhiều lần | MAVEN-ERE (đồng tham chiếu) | một giá trị | EQ 2 | 2 | 2 / 2 / 1 | multi_mention_a = True; multi_mention_a = False |
| `multi_mention_b` | B được nhắc nhiều lần | MAVEN-ERE (đồng tham chiếu) | một giá trị | EQ 2 | 2 | 1 / 1 / 1 | multi_mention_b = True |
| **Tổng** | | | | | **27.491** | **731 / 283 / 205** | |

## 3. Theo nguồn dữ liệu

| Nguồn | Số đặc trưng | Số điều kiện | Dùng trong 54.719 / bật / 378 luật |
|---|---|---|---|
| MAVEN-ERE | 13 | 21806 | 407 / 122 / 81 |
| MAVEN-Arg | 19 | 5685 | 324 / 161 / 124 |

Bỏ toàn bộ đặc trưng MAVEN-Arg (ablation, `STATUS.md` (tag `pre-cleanup`) §39) còn 13 đặc trưng, 21.806 điều kiện, 8.559 luật; macro-F1 EV–EV 26,99% → 26,56%, cả Bài 1 30,84% → 30,74%.
