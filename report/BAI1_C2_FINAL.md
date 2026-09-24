# Bài 1 (C2) — Temporal relation classification bằng mined rules

**Trạng thái: ĐÓNG.** Cấu hình đóng băng: `rules/final/rules_rx_c70.json`, 257 rule,
macro-F1 **25,60%** trên valid. Không tune thêm sau khi đã nhìn valid.

Commit: `8bdb0d5` → `fa4ddb7` → `bffef72` → `2caa15f` → `a902820` → `0f93b85` → `1964d33`

---

## 1. Bài toán

Cho một cặp event trong cùng document, dự đoán quan hệ thời gian giữa chúng: một trong
sáu nhãn BEFORE / CONTAINS / SIMULTANEOUS / OVERLAP / BEGINS-ON / ENDS-ON.

Đây là **temporal relation classification**, không phải full ETRE extraction: cặp event
đã được cho sẵn, không có nhãn NA/no-relation. Vì vậy **không so sánh trực tiếp** được
với con số 55,8 F1 của RoBERTa baseline trong paper MAVEN-ERE, vì protocol khác nhau.

Giả thuyết được kiểm định:

> Các pattern có cấu trúc trong event-centric KG chứa thông tin chuyển giao được về
> quan hệ thời gian.

Kết luận: **được ủng hộ**.

## 2. Khó khăn chính: mất cân bằng nhãn

| Nhãn | valid | tỷ lệ |
|---|---|---|
| BEFORE | 98.866 | 89,94% |
| CONTAINS | 9.391 | 8,54% |
| SIMULTANEOUS | 1.062 | 0,97% |
| OVERLAP | 570 | 0,52% |
| BEGINS-ON | 25 | 0,023% |
| ENDS-ON | 15 | 0,014% |

Đoán BEFORE cho mọi cặp đạt **89,94% accuracy** mà macro-F1 chỉ 15,78%. Nên accuracy
không phải thước đo ở đây; mọi hệ thống cố gắng gọi tên năm nhãn còn lại đều **giảm**
accuracy. Toàn bộ báo cáo này dùng macro-F1 làm thước đo chính.

Mất cân bằng này quyết định hình học của bài toán, không chỉ là phiền toái: nó làm cho
precision không có cùng ý nghĩa giữa các nhãn, và đó là lý do không tồn tại một scalar
“rule quality” duy nhất (xem mục 6).

## 3. Giao thức: chia dữ liệu theo DOCUMENT

```
DISCOVERY     197 docs   63.270 cặp   đề xuất rule; nhãn ở đây quyết định rule nào tồn tại
CONFIRMATION  126 docs   29.455 cặp   ước lượng lại effect trên nhãn CHƯA từng chọn rule
DEV-INNER      77 docs   18.389 cặp   chọn combiner và ngưỡng
VALID         705 docs  109.929 cặp   mở một lần, trên cấu hình đã đóng băng
```

Chia theo **document**, không theo cặp: cặp trong cùng document chia sẻ chủ đề, phong
cách chú thích và phân bố event, nên chia ngẫu nhiên theo cặp sẽ đặt gần-bản-sao ở cả
hai phía và làm số hold-out đẹp hơn thực tế.

Leakage audit đã chạy trên toàn pipeline. Chỉ một chỗ leak có thật: `vote.py` quét 31
cấu hình rồi lấy max trên valid. Đo được: **leak = 0,00 điểm** (dev-inner và valid cùng
chọn `norm-wlb tau=200`), nhưng vẫn đã sửa thành `--select-on dev-inner` mặc định.
`mine_mdd.py` và `mine_views.py` đều sạch — chúng chỉ *in* số valid, không lọc theo nó.

## 4. Kết quả

| | #rule | macro-F1 | macro-F1 (4 nhãn) | F1 không-BEFORE | acc |
|---|---|---|---|---|---|
| Baseline hằng số BEFORE | 0 | 15,78% | 23,67% | 0% | **89,94%** |
| Gộp hai file (điểm xuất phát) | 4.380 | 24,61% | 36,91% | 29,53% | 88,05% |
| 4 gate thống kê | 861 | 25,14% | 37,71% | 35,47% | 86,06% |
| **+ confirmation (đóng băng)** | **257** | **25,60%** | **38,40%** | **37,12%** | 87,87% |

Từ 4.380 xuống 257 rule (**17 lần ít hơn**): macro-F1 **+0,99đ**, F1 nhóm không-BEFORE
**+7,59đ**, accuracy giảm 0,18đ.

### P / R / F1 từng nhãn (valid, 109.929 cặp)

| Nhãn | n_gold | n_pred | TP | P | R | F1 |
|---|---|---|---|---|---|---|
| BEFORE | 98.866 | 99.047 | 92.525 | 93,42% | 93,59% | 93,50% |
| CONTAINS | 9.391 | 9.787 | 3.894 | 39,79% | 41,47% | 40,61% |
| SIMULTANEOUS | 1.062 | 1.055 | 168 | 15,92% | 15,82% | 15,87% |
| OVERLAP | 570 | 40 | 11 | 27,50% | 1,93% | 3,61% |
| BEGINS-ON | 25 | 0 | 0 | 0% | 0% | 0% |
| ENDS-ON | 15 | 0 | 0 | 0% | 0% | 0% |

### Theo nhóm quan hệ

| Nhóm | n_gold | P | R | F1 |
|---|---|---|---|---|
| BEFORE (thứ tự) | 98.866 | 93,42% | 93,59% | 93,50% |
| CONTAINS (bao hàm) | 9.391 | 39,79% | 41,47% | 40,61% |
| Đồng thời (SIM+OVL) | 1.632 | 16,35% | 10,97% | 13,13% |
| Biên (BEG+END) | 40 | 0% | 0% | 0% |
| **Không-BEFORE (5 nhãn)** | 11.063 | 37,43% | 36,82% | **37,12%** |

Độ phủ: rule bắn trên 15,9% số cặp; hệ phát nhãn (không rơi về fallback) trên 9,9%.

## 5. Bộ rule cuối cùng

257 rule, **tất cả đều depth-2** (hai điều kiện nối bằng AND). Median n=159, median k=68.
Phân bố: CONTAINS 254, SIMULTANEOUS 2, OVERLAP 1.

Cách chọn: bốn gate trên train-inner (`n≥25`, `Δlogit≥0,5` so với parent đơn điều kiện,
`q<0,05` Benjamini-Hochberg trên 200 hoán vị theo block document, `docs≥5`) cho 861 rule;
xếp hạng theo Wilson bound trên CONFIRMATION **riêng trong từng nhãn**, giữ top 30%.

Xếp hạng trong từng nhãn chứ không xuyên nhãn là thứ giữ nhãn hiếm sống: SIMULTANEOUS có
Wilson tối đa 0,141 và OVERLAP 0,125, nên bất kỳ ngưỡng tuyệt đối nào mà CONTAINS vượt
qua đều xóa sạch cả hai.

Rule đọc vào có nghĩa:

```
type_a=Killing AND type_b=Bodily_harm            → OVERLAP
same_type=True AND REL:a_before_b=False          → SIMULTANEOUS
bucket_a=lead AND type_pair=(Catastrophe,Attack) → CONTAINS
```

Giết người và gây thương tích chồng lấn thời gian; hai sự kiện cùng loại thường đồng thời.

## 6. Cái đã thử và KHÔNG hiệu quả

Đây là phần đáng giá nhất của C2, vì nó thu hẹp không gian giả thuyết cho người làm sau.

### 6.1 Sáu statistic thay thế đều thua `c70`

| Cơ chế | Kết quả |
|---|---|
| Δlogit vs parent | Spearman +0,229 với precision valid — tệ nhất trong năm |
| Conditional effect vs baseline stratum | corr với confirmation = **−0,039** |
| Stability selection (100 subsample) | max π: CONTAINS 1,00, SIM **0,09**, OVL **0,01** |
| LCB-Lift = WilsonLB/base_rate | thua c70 ở mọi λ và k_min trên dev-inner |
| Greedy downstream optimisation | dev 27,16% nhưng valid 25,40%, rớt 1,77đ |
| MDL / khử bao hàm | **0 rule bị loại** — mọi rule đều depth-2, không cái nào là superset |

Chi tiết trong `experiments/ablations/{lcb,greedy}/RESULTS.md`.

### 6.2 Một lỗi lập luận đã bị bác bỏ

Tôi từng kết luận “lift dự báo tốt hơn WLB” từ bảng tương quan Spearman. Sai: trong cùng
một nhãn, `lift = precision / base_rate` với base_rate là hằng số, nên
`Spearman(lift, precision) = 1,0000` **theo định nghĩa**. Bảng đó đo precision với chính nó.

### 6.3 Giả thuyết “utility tập trung ở vài rule đầu” cũng bị bác bỏ

Trace greedy trên dev gợi ý long-tail, nhưng replay trên valid cho thấy hai mức tăng lớn
nhất là rule **thứ 20** (+1,24đ) và **thứ 23** (+1,26đ), trong khi rule 13–19 góp ~+0,01
mỗi cái. Thứ tự greedy là thứ tự tăng điểm trên dev, không phải thứ tự giá trị chuyển
giao được.

### 6.4 Ngưỡng tuyệt đối giết nhãn hiếm

Áp cả ba cơ chế “bắt buộc” (conditional baseline + stability + confirmation) với ngưỡng
tuyệt đối: **18 rule, toàn CONTAINS**. Không phải vì rule nhãn hiếm xấu, mà vì base rate
0,86% khiến chúng không bao giờ đạt ngưỡng.

## 7. Rule mining có cần thiết không?

Câu hỏi reviewer trực tiếp nhất. Softmax regression trên cùng KG feature, train trên
train-inner, đo trên cùng valid:

| Feature set | #tham số | macro-F1 |
|---|---|---|
| A: chỉ event type | 15.557 | 18,81% |
| B: + vị trí | 15.573 | 19,44% |
| C: + roles | 17.823 | 16,48% |
| D: toàn bộ KG | 18.076 | 20,07% |
| **E: 257 mined rules** | **257** | **25,60%** |

Rule hơn **5,53 điểm** với **70 lần ít tham số hơn**. Đã kiểm tra hội tụ (3/10/20 epoch,
hai mức lr) trước khi kết luận: gains phẳng từ 10 epoch, bản 20 epoch phân kỳ.

Một chi tiết: **C (+roles) thấp hơn B**. Role vào dưới dạng nhiều one-hot thưa; với
class-balanced loss chúng kéo model tuyến tính về nhãn hiếm nhanh hơn mức signal cho phép.
Rule conjunction không có failure mode này vì nó chỉ bắn khi **cả hai** điều kiện đúng.

Caveat: chỉ một model class (tuyến tính trên one-hot). GBM hoặc MLP có thể thu hẹp khoảng
cách vì chúng mô hình hóa được chính loại tương tác mà depth-2 rule mã hóa tường minh.

## 8. Giới hạn

1. **BEGINS-ON / ENDS-ON = 0%.** Trên discovery (197 doc) **không một candidate nào** qua
   `n≥25` cho hai nhãn này — số 0, không phải ít. Đây là phát biểu về dữ liệu (25 và 15
   mẫu trong 109.929 cặp), không phải về gate hay model.
2. **OVERLAP recall 1,93%.** Chỉ còn 1 rule sau gate. Biến thể giữ 4 rule cho macro-F1
   gần y hệt (25,58%), nên đây không phải vấn đề tune được.
3. **Chưa chứng minh rule signal độc lập với text.** C2 chứng minh `KG rules → dự đoán
   thời gian hữu ích`, chưa chứng minh `KG rules → thông tin text không có`. Hai mệnh đề
   này phải tách riêng. So sánh Text / KG / Text+KG là **Future Work**; quantity đáng quan
   tâm là `ΔF1(Text+KG, Text)`, không phải F1 của riêng từng hệ.
4. **BH-FDR với hypothesis phụ thuộc.** Các rule A, A∧B, A∧C không độc lập. Không nên
   viết “BH guarantees FDR ≤ 5%” mà không nêu giả thiết; confirmation split là lập luận
   dễ bảo vệ hơn.
5. **Không so sánh được với benchmark ETRE.** Protocol khác (không có NA, cặp cho sẵn).

## 9. Hai kết luận mang tính phương pháp

**Không gian giả thuyết rất lớn nhưng tín hiệu chuyển giao được rất thưa.**

```
155.467 raw rules → 956 families → 861 gated → 257 confirmed → 23 greedy
macro-F1 (valid):                   25,14%      25,60%         25,40%
```

Bốn bước cuối gần như không đổi điểm. Graph sinh ra rất nhiều mô tả tương đương hoặc gần
tương đương, nhưng tín hiệu tập trung vào một tập nhỏ.

**Independent confirmation quan trọng hơn một score thống kê tinh vi hơn.** Sáu statistic
có cơ sở lý thuyết đều thua một policy gần như không phát biểu gì (“giữ top 30% theo bằng
chứng confirmation trong từng nhãn”). Thứ làm rule set tốt lên không phải là một cách chấm
điểm tốt hơn, mà là việc **thay đổi quyền lực của dữ liệu**: discovery được phép tìm,
confirmation chỉ được phép xác nhận.

`c70` nên được hiểu là **capacity control**, không phải rule-quality measure. Đường cong
861 → 601 → 430 → 257 → 171 → 86 cho macro-F1 25,32 → 25,30 → 25,38 → **25,60** → 24,26 →
23,33: có một vùng capacity phù hợp, và 70% rơi vào đó.

## 10. Phát biểu để dùng trong paper

Không viết:

> TempEKG solves temporal relation classification.

Mà viết:

> The event-centric KG contains a compact set of transferable structural signals that
> can be mined into interpretable rules for temporal relation classification.

Với bằng chứng: 4.380 → 257 rule, macro-F1 24,61 → 25,60, và F1 nhóm không-BEFORE
29,53 → 37,12.

## 11. Tái tạo

```bash
python src/vote.py --tau-sweep
python experiments/ablations/features/ablate.py
```

`vote.py` mặc định `--rules rules_rx_c70.json --select-on dev-inner`.

---

## 12. Bổ sung sau khi khảo sát luật bậc cao

Sau khi đóng Bài 1, một nhánh thí nghiệm nữa đã chạy: luật bậc 3/4/5 trên cấu trúc đồ thị.
Kết quả **không đổi kết luận** nhưng làm rõ vị trí của 25,60%.

### Thang thông tin

| Nguồn ngữ cảnh | macro-F1 | chênh |
|---|---|---|
| Pair features | 20,61% | — |
| + cấu trúc KG không nhãn | 20,73% | +0,12 |
| + nhãn hàng xóm dự đoán | 21,21% | +0,48 |
| + nhãn hàng xóm **gold** | 28,56% | **+7,35** |

*(Thang này mine lại toàn bộ nên A' = 20,61% thấp hơn 257 rule = 24,11%; so sánh hợp lệ là
giữa các bậc với nhau, cùng miner cùng cổng lọc.)*

### Ba điều học được

1. **Cấu trúc KG không chứa nhãn đã gần cạn** — thêm 41.609 luật mô tả hàng xóm chung chỉ
   cho +0,12 điểm.
2. **Signal còn lại nằm ở nhãn thời gian của cạnh kề** (+7,35), tức chính là đầu ra cần dự
   đoán. Không khai thác an toàn được bằng propagation.
3. **Lỗi tụm theo document** (sd 13,5% vs 2,7% nếu iid, document tệ nhất sai 71%) khiến mọi
   tam giác trong một document hỏng đồng thời.

### Sửa một phát biểu ở mục 10

Giới hạn số 3 ghi *"chưa chứng minh rule signal độc lập với text"* vẫn đúng, và giờ có thêm
cơ sở: ablation cho thấy **text là hướng duy nhất còn lại** có khả năng phá trần 25,60%.

Chi tiết: `report/LUAT_BAC_CAO.md`.
