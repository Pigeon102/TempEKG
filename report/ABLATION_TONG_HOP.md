# Ablation tổng hợp: vì sao pipeline chọn cái này, bỏ cái kia

> **Số chuẩn của paper nằm ở repo `tempekg-numbers`** (bảng LaTeX + mọi con số kèm log nguồn). Các mục ghi
> "classifier cũ", "bộ cũ", "257 luật" trong tài liệu này là lịch sử, chỉ để so sánh.

Mỗi bảng đổi **một** lựa chọn của pipeline, giữ nguyên mọi thứ khác, chạy lại và chấm trên valid (mở một lần cho
mỗi biến thể). Mọi tham số của từng biến thể đều được chọn lại trên dữ liệu chọn tham số của chính biến thể đó,
theo macro-F1, để so sánh công bằng. Cập nhật 18/10/2026 (đối chiếu từng ô với log).

Cách đọc: cột **tập chọn ngưỡng** là điểm mà pipeline dùng để ra quyết định; cột **valid** là điểm báo cáo. Chênh
lệch dưới khoảng 0,5 điểm nằm trong mức dao động khi đổi cách chia dữ liệu (cùng pipeline, chia train khác: 26,51%
so với 26,99%), nên không coi là khác biệt thật.

---

## Bài 1 — bộ luật cạnh sự kiện – sự kiện (macro-F1)

### 1.1 Độ sâu luật, cách chấm điểm luật, ngưỡng

Chạy trên 54.719 luật đã xác nhận, không mine lại (`experiments/rules_full/ablate_score.py`, log `ablate_score.log`).
Ngưỡng của mọi biến thể chọn bằng cùng một lưới (lưới cố định cộng các phân vị điểm của từng nhãn), nên pipeline
ở đây cho 27,09% thay vì 26,99% chính thức.

| Biến thể | Tập chọn ngưỡng | Valid | Accuracy | Luật được bật | F1 CONTAINS / SIMU / OVERLAP |
|---|---|---|---|---|---|
| **Pipeline: luật 1 và 2 điều kiện, điểm Wilson, ngưỡng riêng từng nhãn** | **27,01%** | 27,09% | 89,15% | 2.115 | 42,0 / 18,1 / 8,1 |
| Chỉ luật 1 điều kiện | 26,67% | **27,23%** | 87,73% | 301 | 40,7 / 19,2 / 9,9 |
| Chỉ luật 2 điều kiện | 26,87% | 27,01% | 89,29% | 1.875 | 41,4 / 17,7 / 8,6 |
| Confidence thô (trên tập xác nhận) thay Wilson | 26,04% | 26,18% | 88,16% | 3.839 | 39,8 / 14,4 / 9,2 |
| Confidence thô (trên tập khám phá) thay Wilson | 26,15% | 26,09% | 84,22% | 11.017 | 42,4 / 13,8 / 9,0 |
| Lift thay Wilson | 24,59% | 24,05% | 84,25% | 3.161 | 36,7 / 10,6 / 5,5 |
| Wilson, **một** ngưỡng chung cho mọi nhãn | 22,39% | 22,74% | 88,77% | 2.109 | 42,5 / **0** / **0** |

**Kết luận**
- **Điểm Wilson** hơn confidence thô khoảng 0,9 điểm và hơn lift khoảng 3 điểm. Confidence thô và lift ưu ái luật
  ít mẫu nhưng tình cờ đúng hết, nên bật nhiều luật hơn (3.839–11.017) và nhãn hiếm kém đi (SIMULTANEOUS 13,8–14,4
  so với 18,1).
- **Ngưỡng riêng từng nhãn** là bắt buộc: một ngưỡng chung làm SIMULTANEOUS và OVERLAP về F1 = 0 (−4,4 điểm).
- **Độ sâu:** ba biến thể chênh nhau dưới 0,25 điểm, nhỏ hơn mức dao động. Trên tập chọn ngưỡng, kết hợp 1 và 2
  điều kiện cao nhất; trên valid, chỉ luật 1 điều kiện cao nhất. Độ sâu 2 không mang lại lợi ích rõ về điểm; luật 1
  điều kiện (301 luật được bật) gần như đủ. Lý do giữ độ sâu ≤ 2 nằm ở mục 3.

### 1.2 Các cổng lọc luật

Mỗi biến thể mine lại toàn bộ (`MF_OUT=abl_* ABL_*=1 python mine_full.py`, log `experiments/rules_full/abl_*.log`),
cùng lưới ngưỡng với pipeline chính thức (26,99%).

| Biến thể | Luật sau xác nhận | Tập chọn ngưỡng | Valid | Accuracy | Kết luận |
|---|---|---|---|---|---|
| **Pipeline** | 54.719 | 26,36% | **26,99%** | 87,90% | |
| Bỏ cổng "đúng ở ≥ 5 bài" | 57.970 | 26,19% | 26,85% | 87,59% | cổng giúp nhẹ (+0,14) |
| Bỏ kiểm định Benjamini–Hochberg | 57.004 | 26,37% | 26,98% | 87,87% | không đổi điểm; BH chủ yếu bỏ 2.285 luật thừa |
| Bỏ cổng Δlogit (điều kiện thứ hai phải có ích) | **433.323** | 26,37% | 27,30% | 89,14% | điểm trong mức dao động, nhưng số luật gấp 8 lần |
| Bỏ bước chấm lại trên tập xác nhận | 92.773 | 26,36% | 26,36% | 86,02% | bước chấm lại đóng góp **+0,63** |
| Hạ ngưỡng support (n ≥ 10, k ≥ 3) | 62.574 | 26,38% | 26,93% | 87,79% | thêm 8 nghìn luật, không lợi gì |
| Chỉ một nhóm ngữ cảnh (không chia view) | 6.140 | 25,99% | 26,42% | 88,91% | chia 8 nhóm ngữ cảnh đóng góp **+0,57** |

**Kết luận:** hai thành phần đóng góp rõ nhất là **chấm lại trên tập xác nhận** (+0,63) và **so trong từng nhóm
ngữ cảnh** (+0,57). Cổng support, cổng số bài, BH gần như không đổi điểm, nhưng giữ bộ luật gọn và tránh luật giả.
Cổng Δlogit cần để bộ luật không bùng nổ (433 nghìn luật).

---

## Bài 2 — mô hình năng lượng tam giác (bước 3.2, chạy một mình)

`experiments/higher_order/ablate_tri.py`, log `experiments/logs/ablate_tri_part1.log` (hai dòng "tần suất thô" và
"β = 0" của bối cảnh 1) và `ablate_tri.log` (mọi dòng còn lại; dòng pipeline của bối cảnh 1 lấy từ "chỉ cách cân
mean", cùng cấu hình). Các log này chạy trước khi script có guard `PYTHONHASHSEED=0`, nên cùng một cấu hình có thể lệch 1–2 cạnh giữa
hai lần chạy (part1 cho 5.845 / +2.791, `ablate_tri.log` cho 5.847 / +2.793); macro-F1 giữ nguyên tới 2 chữ số thập phân. Bối cảnh 1 là cross-fit trên valid, giống hệt dòng "chỉ tam giác" của pipeline; bối cảnh 2 là nhiễu
bơm 10% trên cả bốn loại cạnh. Cột "cạnh sai" chấm riêng trên các cạnh sai trước khi sửa (trước đó đều bằng 0).

### 2.1 Bối cảnh 1: sửa đầu ra Bài 1 (chưa sửa: macro-F1 30,84%, lỗi 15,31%)

| Biến thể | Macro-F1 | Lỗi | Sửa / phá / ròng | Trên cạnh sai: accuracy / macro-F1 |
|---|---|---|---|---|
| **Pipeline: PMI, β = 10, mô hình nhiễu, cách cân mean, α chọn trong {0; 0,5}** | **31,36%** | 13,83% | 5.847 / 3.054 / +2.793 | 20,2% / 8,3% |
| Tần suất thô thay PMI | 29,71% | 13,38% | 4.871 / 1.238 / +3.633 | 16,8% / 5,0% |
| β = 0 (không làm trơn) | 31,27% | 13,73% | 5.526 / 2.540 / +2.986 | 19,1% / 7,3% |
| β = 100 | **31,58%** | 13,86% | 5.585 / 2.855 / +2.730 | 19,3% / 8,3% |
| α = 0 (Bayes thuần) | 28,78% | 14,09% | 8.084 / 5.792 / +2.292 | 28,0% / 10,4% |
| Chỉ cách cân sum | 28,68% | 15,05% | 7.813 / 7.325 / +488 | 27,0% / 13,1% |
| Chỉ cách cân mean | 31,36% | 13,83% | 5.847 / 3.054 / +2.793 | 20,2% / 8,3% |
| Không mô hình nhiễu | 27,47% | 14,91% | 8.704 / 7.958 / +746 | 30,1% / 12,6% |
| Không tam giác (λ = 0) | 30,84% | 15,31% | 0 / 0 / 0 | 0 / 0 |

### 2.2 Bối cảnh 2: nhiễu bơm 10% (chưa sửa: macro-F1 68,46%, lỗi 9,94%)

| Biến thể | Macro-F1 | Lỗi | Sửa / phá / ròng | Trên cạnh sai: accuracy / macro-F1 |
|---|---|---|---|---|
| **Pipeline** | **84,92%** | 1,91% | 16.526 / 1.353 / +15.173 | 88,0% / 33,6% |
| Tần suất thô thay PMI | 83,42% | 3,68% | 14.970 / 3.152 / +11.818 | 79,7% / 17,8% |
| β = 0 | 86,79% | **1,63%** | 16.182 / 478 / +15.704 | 86,2% / 31,3% |
| β = 100 | 86,32% | 2,35% | 16.928 / 2.587 / +14.341 | 90,1% / 33,4% |
| α = 0 (Bayes thuần) | **86,80%** | 2,27% | 17.074 / 2.583 / +14.491 | 90,9% / 35,2% |
| Chỉ cách cân sum | 83,32% | 2,63% | 17.047 / 3.230 / +13.817 | 90,8% / 34,3% |
| Chỉ cách cân mean | 84,92% | 1,91% | 16.526 / 1.353 / +15.173 | 88,0% / 33,6% |
| Không mô hình nhiễu | 43,58% | 7,18% | 17.144 / 11.932 / +5.212 | 91,3% / 34,4% |
| Không tam giác (λ = 0) | 68,46% | 9,94% | 0 / 0 / 0 | 0 / 0 |

### 2.3 Kết luận cho mô hình tam giác

- **Tam giác là nguồn duy nhất của mọi lần sửa** (λ = 0 không sửa gì ở cả hai bối cảnh).
- **Mô hình nhiễu là thành phần quan trọng nhất:** bỏ đi, macro-F1 tụt 3,9 điểm (đầu ra Bài 1) và 41 điểm (nhiễu
  bơm), vì hệ thống không biết nên tin nhãn đang thấy đến đâu và phá hàng loạt cạnh đúng.
- **PMI tốt hơn tần suất thô** ở cả hai bối cảnh (+1,65 và +1,5 điểm). Với đầu ra Bài 1, tần suất thô còn làm
  macro-F1 thấp hơn lúc chưa sửa, dù giảm lỗi nhiều hơn: nó đổi nhãn hiếm thành BEFORE.
- **Cách cân mean tốt hơn sum** ở cả hai bối cảnh; sum để cạnh nằm trong nhiều tam giác lấn át và phá nhiều.
- **α phụ thuộc bối cảnh:** với đầu ra Bài 1, α = 0 tụt 2,6 điểm (mô hình nhiễu chỉ là ước lượng); với nhiễu bơm,
  α = 0 tốt hơn 1,9 điểm (mô hình nhiễu biết chính xác, nên Bayes thuần đúng). Pipeline chọn α trên dữ liệu chọn tham
  số; ở nhiễu bơm, lựa chọn đó (0,5) không phải tốt nhất trên valid.
- **β chưa được tối ưu:** β = 10 là giá trị đặt trước. β = 100 tốt hơn ở đầu ra Bài 1 (+0,22); ở nhiễu bơm cả β = 0
  và β = 100 đều tốt hơn (+1,4 đến +1,9). Đây là một tham số nên quét thêm.

---

## Bài 2 — auditor (bước 3.1, chạy một mình)

`experiments/higher_order/ablate_audit.py`, log `experiments/logs/ablate_audit.log`. Cross-fit trên valid, giống hệt
dòng "chỉ 3.1" của pipeline (macro-F1 31,53%).

| Biến thể | P / R / F1 | Macro-F1 | Lỗi | Sửa / phá / ròng | Lỗi TIMEX→EV · TIMEX–TIMEX |
|---|---|---|---|---|---|
| **Pipeline: mọi tầng + tầng đồ thị, luật liên tầng, cổng thích ứng, học theo (loại cạnh, nhãn hiện tại)** | 68,0 / 23,5 / 34,9 | **31,53%** | **13,47%** | 6.664 / 3.199 / +3.465 | 21,2 · 14,1 |
| Không tầng đồ thị | 63,9 / 16,2 / 25,9 | 31,01% | 14,32% | 4.524 / 2.653 / +1.871 | 25,0 · 16,4 |
| Không luật liên tầng | 68,0 / 23,5 / 34,9 | 31,53% | 13,47% | 6.664 / 3.199 / +3.465 | 21,2 · 14,1 |
| Cổng lift ≥ 2 thay cổng thích ứng | 64,8 / 12,6 / 21,0 | 31,42% | 14,47% | 3.556 / 1.971 / +1.585 | 22,0 · 14,1 |
| Một nhóm cho mỗi loại cạnh (không theo nhãn hiện tại) | 59,6 / 3,1 / 5,9 | 31,02% | 15,17% | 862 / 604 / +258 | 25,1 · 14,5 |

Chưa sửa: lỗi TIMEX→EV 25,9%, TIMEX–TIMEX 14,5%.

**Kết luận:** học theo nhóm (loại cạnh, nhãn hiện tại) là quan trọng nhất (bỏ đi thì ròng còn 258); tầng đồ thị
giúp nhiều nhất ở cạnh TIMEX→EV và giữ cho TIMEX–TIMEX không xấu đi; cổng lift ≥ 2 cố định giảm recall một nửa vì
không đạt được ở nhóm có tỷ lệ nền cao; luật liên tầng không đổi dự đoán nào. Macro-F1 chênh tối đa 0,52 điểm,
nên đọc theo recall và số ròng.

---

## 3. Phụ lục: vì sao luật dừng ở độ sâu 2

1. **Luật thực chất đã có 3 điều kiện:** nhóm ngữ cảnh (view) + tối đa 2 điều kiện nguyên tử. Bỏ chia nhóm ngữ cảnh
   mất 0,57 điểm (mục 1.2).
2. **Độ sâu 2 so với 1 không khác biệt đo được** (mục 1.1, chênh dưới 0,25 điểm), nên đi sâu hơn khó có lợi.
3. **Vét cạn độ sâu 3 không khả thi:** 27.491 điều kiện cho khoảng 3,8 × 10⁸ cặp nhưng 3,5 × 10¹² bộ ba. Phải chuyển
   sang tìm kiếm có cắt tỉa, có thể bỏ sót luật.
4. **Độ sâu 3 đã được thử ở phiên bản trước** (beam search, `ARCHITECTURE.md` (tag `pre-cleanup`) §9): 16.254 luật, precision tổng 8,15%,
   thấp hơn 10,36% của luật 1 điều kiện. Kiểm trên dữ liệu giữ riêng (`tempekg_exp/ecskg/FORMAL.md`): 67–70% luật
   ghép là học vẹt; chỉ 16/49 luật 2 điều kiện và 22/74 luật 3 điều kiện giữ được lift trên 1,5.
5. **Ghép sâu hơn có kiểm soát đã có ở bước 2.2** (luật liên tầng, tới khoảng 6 điều kiện), chỉ thêm 0,75 điểm.
6. **Không có cổng Δlogit, số luật bùng nổ** từ 54.719 lên 433.323 ngay ở độ sâu 2 (mục 1.2); độ sâu 3 sẽ còn lớn
   hơn nhiều.
