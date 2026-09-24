# TempEKG — Bài 1: Phân loại quan hệ thời gian giữa sự kiện

**Trạng thái: ĐÓNG.** Kết quả: 257 luật, macro-F1 **25,60%** trên tập valid.

Tài liệu này viết cho người chưa theo dõi dự án. Nó giải thích bài toán, cách tiếp cận,
kết quả, và — phần dài nhất — những hướng đã thử mà không hiệu quả.

---

## 1. Bài toán là gì

Cho một văn bản đã được đánh dấu các **sự kiện** (event), với mỗi cặp sự kiện trong cùng
văn bản, hãy xác định quan hệ thời gian giữa chúng.

Ví dụ, trong bài viết về một trận đánh:

```
"Quân đội tấn công thành phố vào rạng sáng. Nhiều dân thường bị thương."

    event A = "tấn công"        event B = "bị thương"
    quan hệ?  →  OVERLAP  (hai sự việc chồng lấn về thời gian)
```

Có sáu nhãn có thể:

| Nhãn | Nghĩa | Ví dụ |
|---|---|---|
| BEFORE | A xong rồi B mới bắt đầu | *bầu cử* → *nhậm chức* |
| CONTAINS | A bao trùm B | *chiến tranh* chứa *một trận đánh* |
| SIMULTANEOUS | A và B cùng lúc | hai cuộc biểu tình cùng ngày |
| OVERLAP | chồng lấn một phần | *tấn công* và *bị thương* |
| BEGINS-ON | bắt đầu cùng lúc | |
| ENDS-ON | kết thúc cùng lúc | |

Dữ liệu: **MAVEN-ERE**, 400 văn bản để học, 705 văn bản để đánh giá (109.929 cặp sự kiện).

## 2. Khó khăn trung tâm: dữ liệu cực kỳ mất cân bằng

| Nhãn | Số cặp (valid) | Tỷ lệ |
|---|---|---|
| BEFORE | 98.866 | **89,94%** |
| CONTAINS | 9.391 | 8,54% |
| SIMULTANEOUS | 1.062 | 0,97% |
| OVERLAP | 570 | 0,52% |
| BEGINS-ON | 25 | 0,023% |
| ENDS-ON | 15 | 0,014% |

Điều này tạo một cái bẫy: **cứ đoán BEFORE cho mọi cặp thì đạt 89,94% accuracy** — nghe rất
cao, nhưng hệ thống đó không bao giờ nhận ra năm nhãn còn lại.

Vì vậy thước đo chính không phải accuracy mà là **macro-F1**: trung bình F1 của sáu nhãn,
mỗi nhãn tính như nhau. Baseline "luôn đoán BEFORE" chỉ đạt **15,78% macro-F1**.

> **Đọc bảng kết quả:** accuracy giảm không nhất thiết là xấu. Mọi hệ thống cố gọi tên nhãn
> hiếm đều mất accuracy so với baseline. Điều đáng quan tâm là macro-F1 và F1 của nhóm
> không-BEFORE.

## 3. Cách tiếp cận: khai phá luật từ đồ thị tri thức

Thay vì huấn luyện một mạng nơ-ron, dự án dựng một **đồ thị tri thức hướng sự kiện**
(event-centric knowledge graph) rồi khai phá các **luật** có thể đọc và giải thích được.

### Đồ thị chứa gì

```
event  ──vai trò──>  entity (người, tổ chức, địa điểm)
event  ──vai trò──>  span (đoạn văn bản)
timex                (mốc thời gian: "November 11, 1778")

event ──quan hệ thời gian──> event      ← ĐÂY LÀ THỨ PHẢI DỰ ĐOÁN
```

Nguyên tắc bất di bất dịch: quan hệ thời gian **không bao giờ** được dùng làm đặc trưng đầu
vào. Nếu vi phạm, mô hình chỉ đang đọc đáp án.

### Một luật trông thế nào

```
NẾU  loại của A = Killing  VÀ  loại của B = Bodily_harm
THÌ  quan hệ = OVERLAP
```

Đọc được: *giết người và gây thương tích chồng lấn về thời gian*. Đây là điểm mạnh so với
mạng nơ-ron — mỗi dự đoán đều truy được về một phát biểu cụ thể.

Luật khác trong bộ cuối:

```
same_type=True VÀ A không đứng trước B trong văn bản   →  SIMULTANEOUS   (96/592)
A ở câu đầu VÀ cặp loại = (Catastrophe, Attack)        →  CONTAINS       (23/25)
```

## 4. Làm sao biết một luật là thật, không phải trùng hợp

Đây là phần chiếm nhiều công sức nhất của dự án. Khai phá trên 111.114 cặp sinh ra hàng trăm
nghìn luật ứng viên; phần lớn là nhiễu.

### Bốn cổng lọc

| Cổng | Điều kiện | Chống lại |
|---|---|---|
| 1. Support | luật phải bắn ít nhất 25 lần | luật dựa trên vài mẫu |
| 2. Incremental | Δlogit ≥ 0,5 so với luật cha | luật chỉ lặp lại điều đã biết |
| 3. Ý nghĩa thống kê | q < 0,05 (Benjamini-Hochberg) | luật đẹp do may mắn khi thử hàng nghìn giả thuyết |
| 4. **Đa dạng văn bản** | xuất hiện ở ≥ 5 văn bản | luật chỉ đúng trong vài bài viết |

**Cổng 4 là phát hiện quan trọng.** Đo được:

| Luật lấy dữ liệu từ | Precision train | Precision valid | Rớt |
|---|---|---|---|
| 1 văn bản | 53,8% | 39,2% | −14,6đ |
| 2–3 văn bản | 62,4% | 43,2% | **−19,2đ** |
| ≥ 11 văn bản | 47,0% | 46,1% | **−0,9đ** |

Luật rút từ ít văn bản trông rất tốt khi học nhưng sụp khi gặp văn bản mới — chúng học đặc
điểm của *một bài viết cụ thể*, không phải quy luật thời gian.

### Giao thức chống rò rỉ

Tập học được chia **ba phần theo văn bản** (không phải theo cặp — vì các cặp trong cùng bài
viết chia sẻ chủ đề và phong cách):

```
DISCOVERY     197 văn bản   đề xuất luật
CONFIRMATION  126 văn bản   chấm lại trên nhãn CHƯA từng tham gia chọn luật
DEV-INNER      77 văn bản   chọn tham số
─────────────────────────────────────────────
VALID         705 văn bản   mở MỘT LẦN, trên cấu hình đã đóng băng
```

Đây là điều khiến kết quả đáng tin: con số 25,60% chưa từng được dùng để ra bất kỳ quyết
định nào.

## 5. Kết quả

| | Số luật | macro-F1 | F1 không-BEFORE | Accuracy |
|---|---|---|---|---|
| Baseline (luôn đoán BEFORE) | 0 | 15,78% | 0% | 89,94% |
| Bộ ban đầu | 4.380 | 24,61% | 29,53% | 88,05% |
| + bốn cổng lọc | 861 | 25,14% | 35,47% | 86,06% |
| **+ xác nhận độc lập** | **257** | **25,60%** | **37,12%** | 87,87% |

**Từ 4.380 xuống 257 luật — ít hơn 17 lần — mà điểm tăng.** Đây là kết quả trung tâm.

### Chi tiết từng nhãn

| Nhãn | Số thật | Đoán ra | Đúng | P | R | F1 |
|---|---|---|---|---|---|---|
| BEFORE | 98.866 | 99.047 | 92.525 | 93,42% | 93,59% | 93,50% |
| CONTAINS | 9.391 | 9.787 | 3.894 | 39,79% | 41,47% | 40,61% |
| SIMULTANEOUS | 1.062 | 1.055 | 168 | 15,92% | 15,82% | 15,87% |
| OVERLAP | 570 | 40 | 11 | 27,50% | 1,93% | 3,61% |
| BEGINS-ON | 25 | 0 | 0 | 0% | 0% | 0% |
| ENDS-ON | 15 | 0 | 0 | 0% | 0% | 0% |

Phần cải thiện thật nằm ở **nhóm không-BEFORE**: F1 từ 29,53% lên 37,12%, recall từ 25,93%
lên 39,66% — tức tìm được **nhiều hơn 53%** số quan hệ mà baseline bỏ sót hoàn toàn.

### Rule mining có cần thiết không?

Câu hỏi hiển nhiên: sao không dùng thẳng một classifier? Đã đo, trên **cùng đặc trưng**:

| Hệ thống | Tham số | macro-F1 |
|---|---|---|
| Softmax regression, chỉ loại sự kiện | 15.557 | 18,81% |
| + vị trí trong văn bản | 15.573 | 19,44% |
| + vai trò | 17.823 | 16,48% |
| + toàn bộ đặc trưng KG | 18.076 | 20,07% |
| **257 luật khai phá** | **257** | **25,60%** |

Luật hơn **5,53 điểm** với **70 lần ít tham số hơn**. Đã kiểm tra hội tụ (3/10/20 epoch) để
chắc chắn baseline không bị huấn luyện thiếu.

## 6. Những hướng đã thử mà KHÔNG hiệu quả

Phần này quan trọng ngang kết quả chính: nó thu hẹp không gian giả thuyết cho người làm sau.

### 6.1 Sáu cách chấm điểm luật thay thế

| Cơ chế | Kết quả |
|---|---|
| Δlogit so với luật cha | tương quan +0,229 với precision thật — tệ nhất trong năm |
| Conditional effect so với baseline stratum | tương quan với xác nhận độc lập = **−0,039** |
| Stability selection (100 lần lấy mẫu) | SIMULTANEOUS đạt tối đa π = 0,09 — không bao giờ qua ngưỡng |
| LCB-Lift (Wilson chia base rate) | thua ở mọi ngưỡng |
| Greedy tối ưu trực tiếp | dev 27,16% nhưng valid 25,40% — overfit |
| MDL / khử dư thừa | **0 luật bị loại** |

Không cơ chế nào thắng được một chính sách đơn giản ("giữ top 30% theo bằng chứng xác nhận,
riêng từng nhãn"). Bài học: **thứ cải thiện bộ luật không phải cách chấm điểm tinh vi hơn,
mà là thay đổi quyền lực của dữ liệu** — tập discovery được phép tìm, tập confirmation chỉ
được phép xác nhận.

### 6.2 Luật bậc cao (bộ 3, 4, 5)

Giả thuyết: có lẽ tín hiệu nằm ở tổ hợp ba sự kiện, không phải cặp. Với mỗi cạnh A–B và sự
kiện thứ ba C, cặp nhãn `(A–C, C–B)` tạo một *chữ ký tam giác*.

Tín hiệu có thật và rất mạnh:

```
SIMULTANEOUS, SIMULTANEOUS  →  SIMULTANEOUS     1.470/1.470
BEFORE, SIMULTANEOUS        →  BEFORE          16.264/16.264 trên valid
```

31/36 chữ ký là **luật học được** (đại số Allen để ngỏ, dữ liệu chốt), chỉ 5 là định lý.

**Nhưng không dùng được cho Bài 1.** Luật tam giác cần biết nhãn của cạnh kề — mà đó chính
là thứ phải dự đoán. Ba cách khai thác đều thất bại:

| Cách | macro-F1 |
|---|---|
| Pair-level (257 luật) | **24,11%** |
| Chạy lặp 5 vòng | 19,41% |
| Soft one-pass (phân phối thay vì nhãn cứng) | 22,92% |
| Joint inference + MDD pruning | 23,10% |
| *Trên đồ thị gold (không đạt được)* | *28,56%* |

Lý do gốc: **lỗi của classifier tụm theo văn bản.** Độ lệch chuẩn tỷ lệ lỗi giữa các văn bản
là 13,5%, trong khi nếu lỗi độc lập chỉ là 2,7% — gấp 5 lần. Văn bản tệ nhất sai 71% số cạnh.
Khi cả một văn bản sai cùng lúc, mọi tam giác trong đó hỏng đồng thời.

### 6.3 Thang thông tin — thí nghiệm quyết định

Câu hỏi cuối: thông tin còn thiếu nằm ở **đặc trưng** hay ở **suy luận**?

| Nguồn ngữ cảnh | macro-F1 | chênh |
|---|---|---|
| Đặc trưng cặp | 20,61% | — |
| + cấu trúc KG **không chứa nhãn** | 20,73% | **+0,12** |
| + nhãn hàng xóm **dự đoán** | 21,21% | +0,48 |
| + nhãn hàng xóm **gold** | 28,56% | **+7,35** |

Bậc thứ hai thêm 41.609 luật mô tả toàn bộ hàng xóm chung — số sự kiện chung, loại của chúng,
vai trò, độ trải câu — mà **chỉ được +0,12 điểm**.

Kết luận: cấu trúc đồ thị không chứa nhãn **đã gần cạn**. Toàn bộ 7,35 điểm còn lại nằm ở
*chính các nhãn thời gian* của cạnh kề, tức là đầu ra cần dự đoán.

### 6.4 Một lỗi đã tìm ra và sửa

Trong quá trình kiểm tra, phát hiện mọi script bậc cao dựng đồ thị sai:

```python
adj[a][b] = r ;  adj[b][a] = r        # SAI: "A trước B" không kéo theo "B trước A"
```

Chiều ngược phải mang quan hệ nghịch đảo. Lỗi làm 5,05% tam giác gold trông như vi phạm đại
số Allen. Sau khi sửa: **0 vi phạm trên 585.078 tam giác** — dữ liệu gold nhất quán tuyệt đối.

Mọi con số ở mục 6.2 và 6.3 là bản **sau khi sửa**.

## 7. Giới hạn

1. **BEGINS-ON và ENDS-ON không có luật nào.** Trên tập discovery, *không một ứng viên nào*
   đạt ngưỡng 25 mẫu — số 0, không phải ít. Hai nhãn này có 25 và 15 mẫu trong 109.929 cặp.
   Đây là giới hạn dữ liệu, không phải thuật toán.
2. **OVERLAP recall chỉ 1,93%** vì chỉ còn một luật sau lọc.
3. **Chưa so với mô hình ngôn ngữ.** Chưa chứng minh tín hiệu từ đồ thị là *bổ sung* cho
   thông tin trong văn bản hay chỉ tái tạo nó.
4. **Không so được với benchmark ETRE.** Bài toán ở đây là *phân loại* (cặp cho sẵn), còn
   benchmark là *trích xuất* (phải tự tìm cặp, có nhãn "không quan hệ"). Con số 55,8 F1 của
   RoBERTa trong paper MAVEN-ERE **không so trực tiếp** được với 25,60%.

## 8. Phát biểu chính xác cho báo cáo

Không viết *"đã giải xong bài toán phân loại quan hệ thời gian"*. Viết:

> Trong không gian đặc trưng KG và giao thức khai phá hiện tại, việc khai thác thêm cấu trúc
> đồ thị không chứa nhãn cho mức cải thiện không đáng kể, xác lập một trần thông tin thực
> tiễn cho biểu diễn hiện tại.

> Tuy nhiên, thí nghiệm oracle cho thấy còn lượng tín hiệu đáng kể trong nhãn thời gian của
> các sự kiện lân cận, gợi hướng chuyển từ khai phá luật hậu kỳ sang học biểu diễn thời gian
> có neo văn bản.

**25,60% không phải trần tuyệt đối** — nó là trần của *nguồn thông tin + lớp giả thuyết +
giao thức hiện tại*.

## 9. Đang ở đâu, đi đâu tiếp

| Hạng mục | Trạng thái |
|---|---|
| Bài 1 — phân loại | **ĐÓNG** ở 257 luật, 25,60% |
| Bài 2 — phát hiện và sửa cạnh sai | **ĐANG LÀM** |
| So sánh với mô hình ngôn ngữ | Future work |

Điều thú vị: **cùng bộ luật bậc cao thất bại ở Bài 1 lại rất hiệu quả ở Bài 2.** Vì Bài 2
bắt đầu từ một đồ thị đã tồn tại, nên nhãn cạnh kề là *quan sát được* chứ không phải đoán:

| Chỉ số | Phương pháp cũ | Luật bậc cao |
|---|---|---|
| Tỷ lệ gắn cờ đúng | 8,63% | **61,76%** |
| Sửa đúng khi đã tìm được | 31,84% | **93,53%** |
| Tìm và sửa đúng trên tổng số lỗi | 8,24% | **26,15%** |

Đây là phân biệt đáng giữ: **luật quan hệ thời gian phù hợp với việc kiểm toán đồ thị hơn là
phân loại trực tiếp.**

## 10. Tài liệu và mã nguồn

| Đường dẫn | Nội dung |
|---|---|
| `rules/final/rules_rx_c70.json` | 257 luật — bộ đang dùng |
| `report/BAI1_C2_FINAL.md` | báo cáo kỹ thuật, số liệu đầy đủ |
| `report/RULESET.md` | bộ luật là gì, biểu diễn ra sao |
| `report/LUAT_BAC_CAO.md` | khảo sát luật bậc 3/4/5 |
| `report/THUAT_NGU.md` | giải thích thuật ngữ |
| `experiments/ablations/` | các hướng đã thử mà thất bại |
| `experiments/higher_order/` | 13 script khảo sát bậc cao |

Tái tạo kết quả chính:

```bash
python src/vote.py --tau-sweep
```
