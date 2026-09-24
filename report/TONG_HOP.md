# Tổng hợp hai bài toán — trạng thái đến 21/09/2026

Mọi con số trong tài liệu này đều đã đo, có script tái tạo được. Số nào chưa đo thì ghi rõ
"chưa đo".

---

## Bối cảnh chung

KG dựng từ MAVEN-ERE: 2.913 document train, 710 valid. **Ba loại cặp, và chúng là ba bài
toán khác nhau — không được gộp bảng kết quả:**

| Loại cặp | Cạnh (train) | BEFORE | non-BEFORE |
|---|---:|---:|---:|
| EV-EV | 203.449 | 92,03% | 7,97% |
| EV-TIMEX | 97.354 | 78,61% | **18,46%** |
| TIMEX-TIMEX | 15.186 | 82,87% | 17,13% |

Phân bố nhãn valid trên **EV-EV** (tập dùng cho mọi bảng dưới đây trừ §1.3b):

| Nhãn | Valid | Tỉ lệ |
|---|---:|---:|
| BEFORE | 98.866 | **89,94%** |
| CONTAINS | 9.391 | 8,54% |
| SIMULTANEOUS | 1.062 | 0,97% |
| OVERLAP | 570 | 0,52% |
| BEGINS-ON | **25** | 0,02% |
| ENDS-ON | **15** | 0,01% |

**Độ lệch này chi phối mọi kết quả.** Một chương trình chỉ biết in "BEFORE" đã đúng 89,94%.

---

# BÀI 1 — Temporal classifier

> Mask nhãn cạnh trên valid, đoán lại.

## 1.1. Đã làm gì

| Bước | Script | Kết quả |
|---|---|---|
| Dựng KG hai tầng | `build_kg.py` | 9/9 bất biến, 3 chống rò rỉ nhãn |
| Đối chiếu nguồn | `verify_kg.py` | weak train 45.509 / valid 12.524, khớp MAVEN-ERE |
| Mine rule 8 view | `mine_views.py` | 155.136 rule thô |
| Rút gọn | `dedupe_families.py` | 1.453 → 1.073 họ |
| Tối thiểu hoá | `minimise.py` | **68 rule** (bitset + lazy greedy CELF) |

## 1.2. Đạt được gì

**Kết quả chính — phải báo macro-F1, không báo accuracy:**

| Cấu hình | Accuracy | **Macro-F1** |
|---|---:|---:|
| hằng số "luôn BEFORE" | **89,94%** | 15,78% |
| 68 rule, argmax-wlb | 86,27% | 22,62% |
| 1.453 family, norm-wlb τ=100 | 80,98% | 23,49% |
| **4.380 rule gộp, norm-wlb τ=200** | **88,05%** | **24,61%** |

Rule **thua accuracy** nhưng **thắng macro-F1 7,71 điểm**. Accuracy che mất hoàn toàn đóng
góp của rule.

**F1 từng nhãn (valid) — đây mới là bảng nên dẫn:**

| Nhãn | Hằng số | 68 rule | families | **gộp 4.380** |
|---|---:|---:|---:|---:|
| BEFORE | 94,70% | 92,40% | 89,70% | 93,72% |
| CONTAINS | 0% | **43,29%** | 32,78% | 33,25% |
| SIMULTANEOUS | 0% | 0% | 11,88% | **14,60%** |
| OVERLAP | 0% | 0% | **6,55%** | 6,09% |
| BEGINS-ON | 0% | 0% | 0% | 0% |
| ENDS-ON | 0% | 0% | 0% | 0% |
| **Macro-F1** | 15,78% | 22,62% | 23,49% | **24,61%** |

**4/6 quan hệ giờ có điểm**, thay vì 2/6. Cách làm: chuẩn hoá trọng số rule theo base rate
của nhãn — rule SIMULTANEOUS ở wlb 0,14 tính nặng hơn rule CONTAINS cùng wlb, vì SIMULTANEOUS
chiếm 0,86% corpus còn CONTAINS 7,43%. Cộng dồn thô (`sum-wlb`) **thua** argmax vì CONTAINS
đông rule nhất nên thắng mọi phép cộng.

**Không overfit:** train 35,35% vs valid 35,25% precision.

## 1.2b. Kết quả trên EV-TIMEX — tập khác, bảng riêng

`mine_timex.py` + `classify_timex.py`, **66.508 cặp valid**. Không cộng vào bảng §1.2.

| | Hằng số | Rule (argmax τ=0,4) |
|---|---:|---:|
| BEFORE | 87,26% | 88,07% |
| CONTAINS | 0% | **39,21%** |
| **Macro-F1** | **14,54%** | **21,21%** |

535 rule, **375 (70,1%) giữ lift≥1,5 trên valid**, 18/18 rule đầu giữ được. wlb cao nhất
**0,666** so với 0,598 của EV-EV — base rate thấp hơn nên trần lift cao hơn.

Rule đọc được: `Use_firearm` cùng câu với timex → CONTAINS **90,00%** · `Terrorism` 86,67% ·
`Sign_agreement` 76,67%.

> **Cảnh báo:** mọi rule top đều chứa `sdist=0`, và riêng điều kiện đó đã cho 59,29% CONTAINS
> (base 21,10%). `ev_type` thêm giá trị thật ở `Use_firearm` (+30,71) và `Expressing_publicly`
> (+19,58), nhưng `Attack` (+0,13) và `Competition` (−1,05) chỉ là `sdist=0` đội lốt.
> **Luôn báo baseline `sdist=0` bên cạnh.**

## 1.3. Vấn đề đang gặp

### (a) Vì sao nhãn hiếm khó — và cách đã gỡ được một phần

Giả thuyết ban đầu của tôi: *"greedy loại sạch SIMULTANEOUS vì CONTAINS chiếm 88,1% khối
non-BEFORE"*. **Đã kiểm chứng và sai.** Nguyên nhân thật:

| Nhãn | Rule | wlb cao nhất | Rule wlb≥0,4 |
|---|---:|---:|---:|
| CONTAINS | 1.033 | 0,598 | **43** |
| SIMULTANEOUS | 279 | **0,141** | **0** |
| OVERLAP | 141 | **0,125** | **0** |

Rule tốt nhất cho SIMULTANEOUS chỉ đúng ~14% số lần. Greedy chọn CONTAINS vì đó là nhãn
**duy nhất có rule đáng tin**.

Đã thử greedy per-label (chạy riêng từng nhãn): **120 rule, precision 8,73%** so với 35,25%
của bộ 68. **Tệ hơn 4 lần.** Hướng này đã chết.

**Cách gỡ được:** không mine thêm, mà **chuẩn hoá trọng số theo base rate** khi kết hợp rule
(`norm-wlb`, §1.2). SIMULTANEOUS lên **11,88%** và OVERLAP lên **6,55%** — hai nhãn này trước
đó luôn ở 0% với mọi phương pháp.

### (b) BEGINS-ON và ENDS-ON — đã thử ba cách, đều không được

| Cách thử | Kết quả |
|---|---|
| Greedy per-label trên EV-EV | 120 rule, precision 8,73% (bộ 68 đạt 35,25%) — tệ hơn 4× |
| Hạ ngưỡng `k≥3` trên EV-EV | F1 0,137% và 0,118%; **99,94% cảnh báo sai** |
| **Mine EV-TIMEX** (ra 38 + 13 rule) | **vẫn F1 = 0** |

Hướng thứ ba từng có vẻ hứa hẹn: mine trên EV-TIMEX **ra được rule** cho hai nhãn này, lần
đầu tiên. Nhưng chấm như classifier thì vẫn 0. Chẩn đoán trực tiếp:

| | BEGINS-ON | ENDS-ON |
|---|---:|---:|
| Cặp gold trên valid | **14** | **4** |
| Rule bắn đúng chỗ | 14/14 | **0/4** |
| Rule đó **thắng** | 2 | 0 |
| Rule bắn **nhầm** chỗ | **38.090** | 4.475 |

Tỉ lệ nhiễu **2.721:1**. Kể cả thắng hết 14 cặp thì precision cũng chỉ 0,037%. 13 rule
ENDS-ON chỉ khớp train — trên valid không chạm cặp nào.

> **Có rule là điều kiện cần, nhưng còn xa mới đủ.** Không combiner nào cứu được (argmax và
> norm-wlb đều để 0), hạ τ thì 38.090 false positive tràn vào. Với **14 và 4 mẫu**, không
> phương pháp nào học được — đây là **giới hạn dữ liệu**, không phải lựa chọn thuật toán.
>
> **Đề nghị chốt:** báo macro-F1 trên **4 lớp có ≥100 mẫu**, ghi rõ hai lớp kia và lý do.

### (c) Con số 93,40% dễ bị hiểu nhầm — phải sửa trước khi nộp

93,40% là precision *trên các cặp rule bắn và đoán CONTAINS*, sau khi đã bỏ BEFORE khỏi mẫu
số. Chấm như classifier thật: CONTAINS **P 35,25% / R 56,07% / F1 43,29%**.

**Đặt vào bảng classifier phải dùng 35,25%.** Nếu để 93,40% mà không nói mẫu số, reviewer
sẽ bắt.

## 1.4. Phát hiện quan trọng nhất — trần là 65,85%, không phải 22,62%

Oracle: với mỗi cặp, nếu **bất kỳ** rule nào bắn ra đúng nhãn gold thì lấy nhãn đó, không
thì fallback BEFORE.

| Cấu hình | Macro-F1 |
|---|---:|
| hằng số BEFORE | 15,78% |
| 68 rule hiện tại | 22,57% |
| **ORACLE (giữ fallback)** | **65,85%** |

Từng nhãn ở oracle: BEFORE 99,77% · CONTAINS 97,95% · **SIMULTANEOUS 99,53%** · OVERLAP
97,85% · BEGINS-ON 0% · ENDS-ON 0%.

**SIMULTANEOUS đạt 99,53% dù rule tốt nhất chỉ wlb 0,141.** Rule đúng **có** bắn ở đúng
chỗ — nó bắn kèm hàng chục rule sai, và cách chọn hiện tại (lấy wlb cao nhất) chọn nhầm.

> **Khoảng cách 43 điểm là bài toán XẾP HẠNG, không phải bài toán mining.**

**ĐÃ THỬ, và khoảng cách này KHÔNG lấy được.** `src/vote.py` với 6 combiner: tốt nhất
(`norm-wlb` τ=100) chỉ **+0,87 điểm** so với argmax-wlb — khoảng **2%** khoảng cách, không
phải 30–45% như tôi ước lượng. Nguyên nhân: rule bắn trên **96,3% số cặp, 46,4 rule/cặp**;
oracle chọn đúng *vì nó đã biết đáp án*, combiner mù thì gần như không có tín hiệu phân biệt.
**Đừng trích 65,85% như headroom lấy được.**

*Lưu ý bắt buộc:* oracle **không** giữ fallback chỉ được 20,13%, vì nó bỏ BEFORE (F1 8,16%)
ở mọi chỗ có rule bắn. Luôn giữ fallback khi trích con số này.

---

# BÀI 2 — Noise-aware reasoning

> Cho graph có cạnh sai, tìm và sửa.

## 2.1. Đã làm gì

| Bước | Script | Kết quả |
|---|---|---|
| Bơm lỗi có kiểm soát | `inject.py` | relabel + delete, mô hình gold-marginal |
| Phát hiện nhãn sai (C3-A) | `detect.py` | constraint τ=0,005 |
| Đề xuất cạnh thiếu (C3-B) | `propose_missing.py` | closure + prior tần suất |
| Đánh giá theo mức nhiễu | `noise_aware.py` | xếp hạng rồi lấy top-k |
| Trần closure | `proof_ceiling.py` | 4,9% (strict) |

## 2.2. Đạt được gì

### (a) C3-B — kết quả mạnh nhất toàn dự án

| Phương pháp | Đề xuất | P | R | F1 |
|---|---:|---:|---:|---:|
| luôn đoán BEFORE | 199.918 | 0,026% | 92,9% | 0,052% |
| closure strict (đòi 1 nhãn) | 1 | 100% | 1,8% | 3,509% |
| **closure + majority, `|compat|≤2`** | **1.572** | **3,181%** | 89,3% | **6,143%** |

**F1 gấp 118× baseline, đề xuất ít hơn 127×.**

Ý chính: **giá trị của closure là ở chỗ biết im lặng.** Nó từ chối 191.752/199.918 cặp
(95,9%) vì không có đường dẫn suy luận.

Nới lỏng này hợp lệ: đòi đúng một nhãn thì vứt 89,3% case có hai nhãn — mà 49/50 là cùng
dạng `{b}` = BEFORE hoặc ENDS-ON. Chọn theo tần suất corpus (3.000:1) đúng **49/49**.

### (b) Sửa nhãn — 93,67% [91,80–95,53], sửa sai chỉ 0,44%

Sweep 5 seed (`sweep_seeds.py`, 300 doc, rate 0,001):

| Chỉ số | Trung bình | Khoảng 95% |
|---|---:|---|
| Sửa đúng | **93,67%** | [91,80 – 95,53] |
| Closure im lặng | 5,90% | [4,31 – 7,48] |
| **Sửa SAI** | **0,44%** | **[0 – 0,97]** |
| R_all (delete) | 92,72% | [88,08 – 97,36] |

Số seed-0 cũ (96,7% và 89,3%) đều nằm trong khoảng ⇒ **ổn định, trích được** — nhưng phải
báo kèm khoảng, vì mỗi seed chỉ có 66–96 cạnh hỏng nên **một cạnh = 1,22 điểm recall**.

**Claim mạnh nhất của bài 2:** sửa sai chỉ **0,44%**, khoảng tin cậy chạm 0.

### (c) Hoà giải chênh lệch 13× giữa hai bảng số

| Nhiễu | ranked | **repair@k** | found | **R_all** |
|---:|---:|---:|---:|---:|
| 1% | 64.562 | **99,51%** | 75,58% | **75,21%** |
| 10% | 19.872 | **96,63%** | 23,74% | **22,94%** |
| 30% | 5.054 | **90,45%** | 6,14% | **5,55%** |

Hai bảng số trước đó lệch nhau 13× ở mức nhiễu 30%. **Không bên nào sai** — đó là hai mẫu
số khác nhau:

| Chỉ số | Nghĩa |
|---|---|
| `repair@k` | trong số **đã gắn cờ VÀ hỏng**, sửa đúng bao nhiêu |
| `found` | trong số **toàn bộ** cạnh hỏng, gắn cờ được bao nhiêu |
| `R_all` | trong số **toàn bộ** cạnh hỏng, **tìm ra VÀ sửa đúng** bao nhiêu |

`repair@k` có điều kiện "đã gắn cờ" nên giữ >90% mọi mức, trong khi phương pháp **lặng lẽ
ngừng gắn cờ**.

## 2.3. Vấn đề đang gặp

### (a) Closure sụp rất nhanh — vấn đề nghiêm trọng nhất

Cột `ranked` tụt từ 64.562 xuống **5.054** khi nhiễu từ 1% lên 30%. Nhiễu phá đúng những
đường dẫn bắc cầu mà closure cần.

Nếu dùng khung *"ERE thật sai 30–50%"* thì ở mức đó phương pháp **chạm tới ~6% số lỗi**.

Điểm an ủi: nó **im lặng** chứ không sai (đồng ý nhãn sai chỉ 0,40–0,61%). Nên precision
giữ được, recall mất.

### (b) Chưa từng chạy trên cạnh model dự đoán

Mọi số đều đo trên **gold đã bơm lỗi**. Bảng thiết kế ghi "Đầu vào: graph các cạnh đã dự
đoán" — đó là thứ **chưa có**.

Tin tốt: đã đo nhiễu tương quan **không tệ hơn** nhiễu độc lập (81,20% vs 75,83% ở mức 1%),
vì nó để lại nhiều vùng sạch. Nên **mức nhiễu** mới là thứ giết, không phải kiểu nhiễu.

### (c) Định vị yếu hơn sửa rất nhiều

| Việc | Kết quả |
|---|---|
| Cho trước cạnh hỏng → sửa | **96,7%** |
| Tự tìm cạnh hỏng (C3-A) | 25,1× lift, bắt 19/60 |

96,7% là con số **có điều kiện**. Phải đóng khung thành pipeline hai tầng và báo riêng.

### (d) `P@k` đi hình chữ U — không dùng làm headline

25,19% → 9,87% → **30,06%**. Ở nhiễu cao, cạnh hỏng nhiều đến mức gắn cờ bừa cũng trúng.

## 2.4. Bốn hướng rule cho bài 2 — đều âm

| Hướng | lift | Vì sao hỏng |
|---|---:|---|
| 68 rule minimal | 1,1× | cả 68 đoán CONTAINS ⇒ "bất đồng" = 93,13% số cạnh |
| 1.073 families | 0,9× | wlb median 0,107, gắn cờ 93,8% số cặp |
| 341 non-CONTAINS | 0,9× | không phải vấn đề nhãn mà là wlb thấp |
| claim nhị phân not-BEFORE | 10,1× | đạt 93% trần nhưng là **baseline trá hình** |

**Nguyên tắc rút ra: predictor dương trên lớp áp đảo không lật được thành detector âm.**
Constraint làm được vì nó nêu nhãn *bị cấm*, không nêu nhãn *kỳ vọng*.

---

# Ba điều phải nói trong bài, nếu không reviewer sẽ bắt

### 1. Gold không có conflict nào để tìm

Bốn phép đo độc lập: 0 cặp mang hai nhãn · 0/2.913 document PC-inconsistent ·
**0/164.803** cặp closure loại nhãn gold · 0 BEFORE hai chiều.

Nhãn MAVEN là đọc ra từ **một timeline đã sắp xếp**, nên nhất quán theo cấu trúc. Mọi recall
về conflict **chỉ đo được bằng bơm lỗi nhân tạo**.

### 2. Không dùng accuracy làm thước đo bài 1

Base rate 89,94%. Phải báo **macro-F1 và F1 từng nhãn**, kèm baseline "luôn đoán BEFORE".

### 3. Luôn nói mẫu số — ba cặp số đã từng gây hiểu nhầm

| | |
|---|---|
| 93,40% vs 35,25% | precision trên cặp rule bắn, vs precision classifier |
| `repair@k` vs `R_all` | đã gắn cờ, vs toàn bộ lỗi |
| EV-EV vs EV-TIMEX | 109.929 cặp vs 66.508 cặp — **không cộng hai bảng** |

Báo `R_all` làm headline cho bài 2, kèm `found` bên cạnh.

---

# Cần làm gì trước — xếp theo giá trị trên chi phí

| # | Việc | Thời gian | Vì sao |
|---|---|---|---|
| ~~1~~ | ~~Kết hợp rule đang bắn~~ | ~~1 ngày~~ | **ĐÃ LÀM** — +0,87 điểm, SIMULTANEOUS và OVERLAP thoát 0%. Xem §1.2 |
| **2** | Sửa 93,40% → 35,25% trong mọi bảng classifier | ~30 phút | Rẻ, và là lỗi reviewer chắc chắn bắt |
| **3** | Sweep nhiều seed | ~15 phút | 56/60 lỗi là mẫu quá nhỏ, cần khoảng tin cậy |
| **4** | Khai thác EV-TIMEX | ~nửa ngày | **112.540 cạnh chưa dùng**, non-BEFORE đậm đặc **2,3×** (18,46% vs 7,97%) ⇒ trần lift cao hơn |
| **5** | Chạy bài 2 trên cạnh model dự đoán | cần model | Chỗ **duy nhất có thể làm hỏng câu chuyện**. Biết sớm thì tốt |
| **6** | Quyết cách xử lý BEGINS-ON/ENDS-ON | ~1 giờ | Hoặc gộp vào `OTHER`, hoặc báo thêm macro-F1 trên lớp ≥100 mẫu |

## Đề nghị thứ tự — cập nhật sau khi thử việc 1

Việc 1 đã làm và **biên độ nhỏ hơn hy vọng nhiều** (+0,87 điểm). Nhưng nó cho kết quả định
tính đáng giá: **4/6 quan hệ có điểm** thay vì 2/6.

Thứ tự còn lại:

1. **Việc 2 và 3** (45 phút) — dọn chỗ dễ bị bắt lỗi
2. **Việc 5** nếu có model — rủi ro duy nhất chưa đánh giá được, biết sớm thì tốt
3. **Việc 4** (EV-TIMEX) — 112.540 cạnh chưa dùng, biên độ chưa biết nhưng base rate thấp
   hơn nên trần lift cao hơn

Bài 1 giờ nên đóng khung là *"4/6 quan hệ có điểm, macro-F1 gấp 1,5× hằng số"*, dẫn bằng
bảng từng nhãn chứ không dẫn bằng con số gộp.

---

# Phụ lục: những gì đã bác bỏ (đừng thử lại)

| Ý tưởng | Kết quả đo |
|---|---|
| Greedy per-label để cứu SIMULTANEOUS/OVERLAP | 120 rule, precision 8,73% — tệ hơn 4× |
| Dùng rule làm detector C3-A | 4 hướng, tốt nhất 10,1× (baseline 10,7×) |
| PC-2 thay 1-step closure | khôi phục thêm **0 cạnh**, tốn hơn nhiều |
| Lọc theo anchor | mất **57,8%** khối non-BEFORE, chỉ giảm tải xuống 23% |
| Phép kiểm bao hàm cho C3-B | thổi 4,9% thành 80,4%; 97% lạm phát là BEFORE-vs-ENDS-ON |

Chi tiết đầy đủ ở `report/STATUS.md` §11–17 và `report/DEFINITIONS.md`.
