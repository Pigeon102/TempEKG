# Bài 2 — Phát hiện và sửa cạnh sai trong đồ thị thời gian

**Trạng thái: có kết quả trên toàn bộ 705 document.** R_all **29,29%**, repair@k **91,99%**.

---

## 1. Bài toán

Cho một đồ thị quan hệ thời gian **đã tồn tại** nhưng có cạnh sai, hãy tìm và sửa chúng.

Khác Bài 1 ở một điểm quyết định: **nhãn của các cạnh khác đã biết**. Đây là lý do cùng bộ
luật thất bại ở Bài 1 lại hiệu quả ở đây.

Nguồn cạnh sai: đầu ra của chính classifier Bài 1 (257 luật) — không phải nhiễu ngẫu nhiên.
Đây là điểm quan trọng, xem mục 5.

## 2. Ba tầng kiểm toán

| Tầng | Cơ chế | Vai trò |
|---|---|---|
| **date bridge** | `pin(A)=d₁, pin(B)=d₂, d₁<d₂ ⟹ A BEFORE B` | chứng minh — precision gần tuyệt đối, phủ rất hẹp |
| **closure** | suy luận một bước bằng đại số Allen, hỏi nhãn hiện tại có tương thích không | loại trừ |
| **higher-order** | chữ ký tam giác `(A–C, C–B) → A–B` học từ train | chủ lực |

Điểm khác nhau cốt lõi: closure chỉ nói *"nhãn này không tương thích"*, còn luật bậc cao nói
thẳng **nhãn nào đúng** kèm trọng số.

## 3. Ba tầng có bổ sung nhau không? (E1)

Câu hỏi quan trọng nhất trước khi xây pipeline: chúng sửa cùng một tập lỗi hay khác nhau?

### Từng tầng riêng lẻ (149 document)

| Tầng | gắn cờ | đúng | precision | sửa đúng | R_all |
|---|---|---|---|---|---|
| date bridge | 12 | 12 | **100,00%** | 12 | 0,36% |
| closure | 343 | 242 | 70,55% | 220 | 6,52% |
| higher-order | 1.767 | 1.393 | 78,83% | 1.324 | **39,25%** |

### Chồng lấn

```
hợp của ba tầng: 1.879 cạnh

chỉ date bridge riêng:     2
chỉ closure riêng:       110
chỉ higher-order riêng: 1.528
cả ba cùng gắn cờ:         4
```

Higher-order ∩ closure chỉ **233/1.767 = 13,2%**. Tức **86,8% cạnh higher-order tìm được là
mới** — closure không chạm tới.

**Ba tầng không sửa cùng một tập lỗi.** Đây là cơ sở để xếp chồng chúng.

### Thứ tự có ảnh hưởng nhỏ

| Thứ tự | R_all | cạnh sai còn lại |
|---|---|---|
| date → closure → HO | 39,99% | 9,14% |
| **HO → closure → date** | **40,26%** | **8,87%** |

Chạy higher-order trước tốt hơn: closure chạy trước "tiêu thụ" một số case mà HO xử lý tốt
hơn (HO chỉ còn tìm được 1.517 thay vì 1.767). Chênh 0,27 điểm nên không phải yếu tố lớn.

## 4. Giao thức sạch (E3)

Luật bậc cao ban đầu mine trên cả 400 document train rồi kiểm trên valid — cùng lối tắt mà
Bài 1 đã phải bỏ. Áp giao thức xác nhận độc lập:

```
DISCOVERY     229 document   đề xuất chữ ký tam giác
CONFIRMATION  171 document   chấm lại trên nhãn CHƯA tham gia đề xuất
─────────────────────────────────────────────────────
VALID         705 document   mở một lần, trên bộ luật đã đóng băng
```

**Chia hai, không chia ba.** Bài 1 cần tập dev vì `vote.py` quét 31 cấu hình `(method, tau)`.
Bài 2 không tune siêu tham số nào — cổng lọc `n≥30, k≥10, doc≥5, wlb≥0,50` là hằng số cố
định — nên cắt thêm dev chỉ làm mất dữ liệu. Cắt nhầm khiến R_all giảm từ 29,29% xuống 19,19%.

Kết quả: 55 chữ ký → 30 ứng viên → **21 luật đóng băng** (BEFORE 14, CONTAINS 5,
SIMULTANEOUS 1, OVERLAP 1).

## 5. Kết quả trên toàn bộ 705 document (E4)

109.929 cặp, **13.331 cạnh sai** (12,13%) do classifier Bài 1 tạo ra.

| Tầng | gắn cờ | đúng | sửa đúng |
|---|---|---|---|
| higher-order | 5.514 | 4.029 | 3.706 |
| closure | 242 | 183 | 166 |
| date bridge | 41 | 33 | 33 |
| **TỔNG** | **5.797** | **4.245** | **3.905** |

| Chỉ số | Giá trị | Nghĩa |
|---|---|---|
| P@k | **73,23%** | trong số cạnh gắn cờ, bao nhiêu thật sự sai |
| found_all | 31,84% | trong toàn bộ cạnh sai, tìm được bao nhiêu |
| repair@k | **91,99%** | trong số tìm được, sửa đúng bao nhiêu |
| R_all | **29,29%** | vừa tìm vừa sửa đúng, trên tổng số lỗi |

Tỷ lệ cạnh sai: **12,13% → 9,98%**.

### So sánh

| Phương pháp | R_all |
|---|---|
| closure đơn lẻ (điểm xuất phát) | 8,24% |
| **ba tầng, giao thức sạch** | **29,29%** |
| ba tầng, luật mine trên cả 400 doc | 37,63% |

Bản sạch **gấp 3,6 lần** closure. Bản dùng hết dữ liệu cao hơn nhưng không có xác nhận độc lập.

**Xác nhận độc lập còn cải thiện precision:** P@k của bản sạch (73,23%) cao hơn bản không
confirm (71,84%), dù ít hơn 14 luật. Nó loại đúng những luật kém.

### Ổn định giữa 149 và 705 document

| | 149 doc | 705 doc |
|---|---|---|
| repair@k | 93,53% | 93,22% |
| R_all (luật cũ) | 40,26% | 37,63% |

Lệch nhỏ — con số trên tập con trước đó không bị thổi phồng.

## 6. Vì sao closure thất bại trên lỗi model thật (Task 5)

Đây là phát hiện khiến toàn bộ hướng đi thay đổi.

Mọi con số audit trước đây đo trên **gold + nhiễu ngẫu nhiên**. Chạy lại trên lỗi thật của
classifier, cùng tỷ lệ 12,46%, cùng document:

| Chỉ số | Model thật | Nhiễu ngẫu nhiên |
|---|---|---|
| P@k | 8,63% | 12,03% |
| **repair@k** | **31,84%** | **96,61%** |
| R_all | 8,24% | 27,43% |

**repair@k sụp gấp 3 lần.** Nguyên nhân nằm ở ma trận nhầm lẫn:

```
BEFORE   → CONTAINS   1.660  (49,2% số lỗi)
CONTAINS → BEFORE     1.257  (37,3% số lỗi)
```

**86,5% lỗi của model là một cặp nhãn hoán đổi qua lại.** Nhiễu ngẫu nhiên rải đều theo phân
phối corpus nên closure sửa dễ; lỗi model tập trung vào đúng chỗ closure khó phân biệt nhất —
cả BEFORE lẫn CONTAINS đều tương thích với hầu hết ngữ cảnh.

Luật bậc cao xử lý được vì nó nói thẳng nhãn nào đúng, không chỉ nói không tương thích.

## 7. Date bridge — phát biểu chính xác

```
pin(A) = d₁   nếu  timex(d₁) --CONTAINS--> A   (hoặc A --SIMULTANEOUS--> timex)
d₁ < d₂  ⟹  A BEFORE B
```

| Tập | cặp bắc cầu | đúng |
|---|---|---|
| valid (gold) | 5.541 | **5.541 = 100,0%** |
| train (gold) | 7.405 | **7.405 = 100,0%** |

**12.946 suy luận, 0 lỗi.** Nó không học từ dữ liệu — là phép so sánh trên trục số.

Ba điều phải nói kèm:

1. **Yêu cầu ngày đủ y/m/d.** Với ngày chỉ có năm, precision tụt: 105 báo động giả xuất hiện
   vì so ngày cấp năm với ngày cấp ngày. Ví dụ *Battle of Malacca (1641)* có event `took` neo
   vào `1606` — timex là bối cảnh nền, không phải thời điểm.
2. **Chỉ `CONTAINS`/`SIMULTANEOUS` mới định vị.** Cạnh `event BEFORE timex` là *biên*, không
   phải *vị trí*. Dùng nhầm nó làm neo cho kết quả BEFORE↔AFTER lẫn lộn.
3. **Các neo event–timex hiện lấy từ gold.** Trên hệ thật chúng cũng phải dự đoán. Nên phát
   biểu đúng là *precision 100% với điều kiện các neo là đúng*, chưa phải vô điều kiện.

## 8. Giới hạn

1. **found_all chỉ 31,84%** — hệ im lặng trên 68% cạnh sai. Với bài toán audit đây là tính
   chất tốt (người dùng chỉ xem 5,3% đồ thị), nhưng nếu mục tiêu là sửa hết thì cần nới ngưỡng.
2. **Chỉ 21 luật**, chủ yếu BEFORE và CONTAINS. Nhãn hiếm gần như không có luật.
3. **Nguồn lỗi là một classifier cụ thể.** Kết quả có thể khác với classifier khác có ma trận
   nhầm lẫn khác.
4. **Date bridge phụ thuộc neo gold** (mục 7.3).

## 9. Tái tạo

```bash
python experiments/higher_order/e1_stack.py 150     # E1 — chồng lấn ba tầng
python experiments/higher_order/e3e4.py            # E3+E4 — giao thức sạch, 705 doc
python src/noise_aware.py --rates 0.01,0.05,0.10   # đối chứng nhiễu ngẫu nhiên
```

---

## 10. Kiểm tra sáu đề xuất từ literature review

Review đề xuất sáu hướng; ba trong số đó đo được ngay vì chỉ cần đặc trưng đã có.
Đánh giá 2-fold theo document trên valid (705 doc), gold chỉ làm nhãn huấn luyện.

### #16 Learned auditor — logistic regression trên 42 đặc trưng

| Ngưỡng | gắn cờ | P@k | found_all | repair@k | R_all |
|---|---|---|---|---|---|
| 0,9 | 15.054 | 49,04% | 55,38% | 56,98% | 31,56% |
| 0,5 | 16.536 | 46,33% | 57,47% | 56,65% | 32,56% |
| 0,4 | 16.836 | 45,84% | 57,89% | 56,38% | 32,64% |
| **rule-only (E4)** | 5.797 | **73,23%** | 31,84% | **91,99%** | 29,29% |

**R_all tăng 3,35 điểm, nhưng bằng cách hy sinh precision.** Auditor học được gắn cờ gấp
gần 3 lần (16.836 vs 5.797), tìm được nhiều hơn (57,89% vs 31,84%), nhưng:

- P@k **rớt từ 73% xuống 46%** — hơn một nửa cảnh báo là giả
- repair@k **rớt từ 92% xuống 56%** — sửa sai gần một nửa số cạnh tìm được

Với bài toán audit — nơi người dùng phải xem từng cảnh báo — đây là **đánh đổi xấu**.
Review tự nói *"precision cao quan trọng hơn recall trong auditing"*; theo tiêu chí đó,
auditor học được **thua** rule-only.

Mô hình tuyến tính không đủ; nhưng điều đó cũng có nghĩa vấn đề không nằm ở cách gộp bằng
chứng đơn giản. Muốn vượt cần biểu diễn khác (text, endpoint), không phải cách kết hợp khác.

### #2 Chuẩn hóa theo số tam giác — LÀM TỆ HƠN

| Biến thể | gắn cờ | P@k | found_all | R_all |
|---|---|---|---|---|
| HO raw vote (E4) | 5.514 | 73,07% | 30,22% | **27,80%** |
| HO chuẩn hóa | 4.060 | 76,55% | 23,31% | 21,24% |

Precision tăng 3,5 điểm nhưng R_all **mất 6,56 điểm**. Giả thuyết "`BEFORE,BEFORE→BEFORE`
thắng bằng số lượng" **không đúng ở Bài 2** — vì ở đây cạnh kề là quan sát được, nhiều tam
giác đồng thuận thực sự là bằng chứng mạnh hơn, không phải nhiễu cộng dồn.

Chuẩn hóa hợp lý ở Bài 1 (nơi hàng xóm là dự đoán nhiễu) nhưng sai ở Bài 2.

### #3 Leave-one-out PC — precision thấp, phủ rất hẹp

| Biến thể | gắn cờ | P@k | repair@k | R_all |
|---|---|---|---|---|
| LOO ép ra nhãn khác | 333 | 47,75% | 79,25% | 0,95% |
| LOO nhãn hiện tại không tương thích | 2.400 | 65,38% | 89,23% | 10,50% |

Không thay thế được higher-order (27,80%). Đúng như review dự đoán: LOO bắt lỗi gây mâu
thuẫn toàn cục, còn BEFORE↔CONTAINS (86,5% lỗi) thường vẫn nhất quán.

### Trọng số lớn nhất của error detector

```
+ pc_OVERLAP        8,73    + date_contra          3,39
+ cur_OVERLAP       8,67    + ho_raw_SIMULTANEOUS  2,34
```

Hai đặc trưng đầu nói: *nếu classifier đoán OVERLAP thì gần như chắc sai* — đúng, vì OVERLAP
precision chỉ 27,5%. Đây là tín hiệu **về lỗi hệ thống của classifier**, không phải về cấu
trúc đồ thị. `date_contra` đứng thứ ba xác nhận date bridge là bằng chứng mạnh.

### Ba hướng chưa đo

| # | Hướng | Vì sao chưa |
|---|---|---|
| #1 | Text + graph auditor | cần `torch`/`transformers`, môi trường chưa có |
| #4 | Endpoint / interval representation | cần thiết kế lại toàn bộ biểu diễn nhãn |
| #5 | KG embedding trust score | cần `numpy` tối thiểu |
| #6 | Global LLM regeneration | review tự xếp thấp, không ưu tiên |

### Kết luận

| Đề xuất | Kết quả | Gain? |
|---|---|---|
| #16 Learned auditor (tuyến tính) | R_all +3,35 nhưng precision −27, repair −35 | **Negative** cho audit |
| #2 Normalised rerank | R_all −6,56 | **Negative** |
| #3 Leave-one-out PC | R_all 10,50%, không thay được HO | Bổ sung yếu |
| #1, #4, #5, #6 | chưa đo | — |

**Rule-only ba tầng (29,29% R_all, 91,99% repair@k) vẫn là cấu hình tốt nhất cho audit.**
Ba hướng đo được đều không vượt; hai trong ba làm tệ đi. Điều này ủng hộ nhận định của
review rằng muốn vượt cần **biểu diễn mới** (text hoặc endpoint), không phải cách kết hợp mới
trên bằng chứng cũ.

## 11. Nâng cấp tầng higher-order bằng kết quả motif của Bài 1 (23/09/2026)

Bài 1 cho thấy tín hiệu bậc cao rất mạnh khi nhãn ngữ cảnh là thật (oracle +15,67) nhưng
không dùng được khi phải tự dự đoán. Bài 2 khác: đồ thị cần kiểm toán **đã tồn tại**, các cạnh
kề là quan sát chứ không phải đầu ra của auditor. Câu hỏi: tín hiệu đó lấy lại được bao nhiêu?

### Thiết kế

| | OLD (E4, đang dùng) | NEW |
|---|---|---|
| Họ motif | chỉ tam giác EV–EV (3E) | 3E, 3T, 4EE, 4ET, 4TE, 4TT |
| Nhãn của luật | nhãn đa số, `wlb ≥ 0,50` | **mọi nhãn** BEFORE/CONTAINS/SIMULTANEOUS/OVERLAP |
| Cổng | ngưỡng tuyệt đối | cwlb trên confirmation **phải vượt precision classifier** ở nhãn đó |
| Quyết định | nhãn có tổng wlb lớn nhất ≠ nhãn hiện tại | nhãn thay thế có cwlb > max(độ tin cậy nhãn hiện tại, luật tốt nhất ủng hộ nhãn hiện tại) |
| Số luật | 21 | 175 (BEFORE 96, CONTAINS 64, SIMULTANEOUS 12, OVERLAP 3) |

Độ tin cậy classifier trên confirmation: BEFORE 94,6%, CONTAINS 40,6%, SIMULTANEOUS 16,3%,
OVERLAP 41,7%. Mine trên DISCOVERY (229 doc), xác nhận trên CONFIRMATION (171 doc), valid 705
doc mở một lần. Lớp nhiễu: 13.331 cạnh EV–EV sai do 257 luật Bài 1 tạo ra (12,13%).

Hai bối cảnh:

| Bối cảnh | Cạnh EV–TX, TX–TX | EV–EV |
|---|---|---|
| **A** | như trong KG (gold) | dự đoán |
| **B** | EV–TX từ classifier 273 luật (79,84%), TX–TX so lịch (UNK 65,1%) | dự đoán |

### Phải đo thêm một chỉ số: số cạnh đúng bị làm hỏng

R_all chỉ đếm cạnh sai được sửa đúng. Nó **không trừ** cạnh đúng bị auditor đổi thành sai. Chỉ
số quyết định cho sửa tự động là **giảm lỗi ròng = sửa đúng − làm hỏng**.

| Cấu hình | gắn cờ | P@k | R_all | sửa đúng | **làm hỏng** | **giảm ròng** | tỷ lệ lỗi |
|---|---|---|---|---|---|---|---|
| OLD stack (E4) | 5.797 | 73,23% | 29,29% | 3.905 | 1.544 | **2.361** | 12,13% → 9,98% |
| **A** — NEW stack | 7.468 | 81,41% | 43,40% | 5.786 | 1.380 | **4.406** | 12,13% → **8,12%** |
| **B** — NEW stack, không kiểm soát | 10.345 | 60,49% | 43,83% | 5.843 | **4.079** | 1.764 | 12,13% → 10,52% |
| **B** — NEW, margin 0,05 | 4.038 | 78,53% | 21,79% | 2.905 | 859 | 2.046 | 12,13% → 10,27% |
| **B** — NEW margin 0,05 → OLD → closure → date | 6.174 | 73,13% | 31,36% | 4.181 | 1.651 | **2.530** | 12,13% → **9,83%** |

Margin 0,05 (luật thay thế phải hơn nhãn hiện tại ít nhất 0,05) được chọn trên CONFIRMATION
theo giảm lỗi ròng, trong lưới margin {0; 0,02; 0,05; 0,10} × số luật đồng thuận {1, 2, 3}.

### Bối cảnh A: gain lớn, nhưng là suy diễn qua cạnh EV–TX gold

Họ 3T một mình đạt **P@k 100,00%**, repair@k 99,66%. Kiểm tra lại, không phải lỗi code: luật
3T mạnh nhất là **bắc cầu Allen qua TIMEX**:

| Chữ ký `rel(A,T), rel(T,B)` | nhãn | cwlb |
|---|---|---|
| BEFORE, BEFORE | BEFORE | 1,000 |
| iCONTAINS, BEFORE | BEFORE | 1,000 |
| BEFORE, CONTAINS | BEFORE | 1,000 |
| CONTAINS, iBEFORE | CONTAINS | 0,997 |
| CONTAINS, CONTAINS | CONTAINS | 0,995 |

Cờ gắn chủ yếu là CONTAINS → BEFORE (3.473) và BEFORE → CONTAINS (2.078), gần như luôn đúng.
Khi hai chân EV–TX là gold, cạnh EV–EV **suy ra được bằng logic**. Kết quả A vì vậy hợp lệ
**chỉ khi** tầng EV–TX của KG được tin là đúng — đó là giả định mạnh, và phải ghi rõ khi báo cáo.

### Bối cảnh B: gain thật nhỏ hơn nhiều

Khi EV–TX cũng phải dự đoán, 3T tụt từ P@k 100% xuống 56,63%. NEW không kiểm soát có R_all
43,83% — trông ngang A — nhưng **làm hỏng 4.079 cạnh đúng**, nên tỷ lệ lỗi còn 10,52%, **tệ hơn**
OLD (9,98%). R_all một mình sẽ dẫn đến kết luận sai.

Với margin chọn trên confirmation và xếp chồng trước OLD, cấu hình tốt nhất giảm ròng
**2.530 cạnh** so với **2.361** của OLD: **+169 cạnh, +7%**, tỷ lệ lỗi 9,98% → 9,83%.

### Kết luận

1. **Tín hiệu bậc cao của Bài 1 lấy lại được ở Bài 2 — nhưng chỉ đầy đủ khi các cạnh kề đáng
   tin.** Với EV–TX tin cậy (A), giảm lỗi ròng gần gấp đôi (2.361 → 4.406, tỷ lệ lỗi 8,12%).
2. **Trong bối cảnh hoàn toàn dự đoán (B), cải thiện chỉ +7%.** Cùng lý do vòng tròn của Bài 1:
   luật đọc nhãn EV–TX dự đoán không đáng tin hơn classifier sinh ra nhãn đó.
3. **Phải báo giảm lỗi ròng (hoặc số cạnh làm hỏng) bên cạnh R_all.** R_all không phạt sửa
   nhầm; ở B nó xếp cấu hình tệ nhất lên đầu.

Script: `experiments/higher_order/bai2_auditor.py` (hai bối cảnh, từng họ),
`bai2_control.py` (margin + giảm lỗi ròng), `bai2_check3t.py` (kiểm tra 3T). Log trong
`experiments/logs/`.

## 12. Kiểm định trên `fake_data/` và đào sâu bối cảnh B (23/09/2026)

### 12.1. Dữ liệu `fake_data/`

MAVEN-ERE valid, đổi nhãn cạnh EV–EV ở 4 mức 5/10/15/20% (mỗi mức một seed, các mức rút độc
lập). Nhãn giả rút theo phân phối biên của corpus trừ nhãn gold (BEFORE→CONTAINS chiếm 76%).
Cạnh TIMEX giữ nguyên gold. Đã kiểm tra: 22.012/22.012 cạnh trong manifest khớp KG (106 cạnh
ngược chiều), không có cạnh ngoài EV–EV bị đổi, không rò rỉ qua thứ tự dòng.

Vì EV–TX là gold, fake_data chính là **bối cảnh A**. Ưu điểm so với nhiễu classifier: biết
chính xác cạnh nào sai, và nhiễu độc lập với văn bản.

### 12.2. Phát hiện chính: auditor luật có nền báo động giả ~6.000 cạnh

Chạy trên đồ thị **gold sạch (0% nhiễu)**:

| Auditor | cạnh đúng bị đổi | tỷ lệ lỗi tạo ra |
|---|---|---|
| OLD (21 luật) | 5.789 | 5,27% |
| NEW (175 luật) | 3.205 | 2,92% |
| closure | 0 | 0% |

Luật ghi đè cạnh mỗi khi nhãn đa số của chữ ký khác nhãn hiện tại, bất kể xác suất tiên
nghiệm cạnh đó sai là bao nhiêu. Hệ quả trên fake_data: auditor bắt được ~92% cạnh giả nhưng
số cạnh làm hỏng gần như **không đổi theo mức nhiễu** (5.883 → 6.774), nên ở mức 5% OLD làm
tỷ lệ lỗi **tăng** 4,99% → 5,67%.

### 12.3. Auditor Bayes có mô hình kênh nhiễu

```
post(r) ∝ P(r | chữ ký) × P(nhãn quan sát p | nhãn thật r)
```

- `P(r | chữ ký)`: trung bình hình học phân phối nhãn gold (làm trơn) của mọi chữ ký của cạnh,
  mine trên DISCOVERY. Trung bình hình học tránh tự tin quá mức khi các chữ ký tương quan.
- `P(p | r)`: kênh nhiễu. Với fake_data: tỷ lệ ρ và đổi theo phân phối biên.
- Gắn cờ khi nhãn tốt nhất khác p và hơn p một margin log-odds. Margin chọn trên CONFIRMATION
  có **mô phỏng cùng quá trình nhiễu ở cùng tỷ lệ**; không dùng cạnh nào của valid.

Tỷ lệ lỗi sau kiểm toán (fake_data, 705 doc):

| Mức | ban đầu | OLD | NEW (rel mô phỏng) | closure | **Bayes** | **Bayes → closure** |
|---|---|---|---|---|---|---|
| 5% | 4,99% | 5,67% | 3,39% | 3,58% | 1,51% | **1,45%** |
| 10% | 10,05% | 6,30% | 6,11% | 7,83% | 2,96% | **2,69%** |
| 15% | 15,06% | 6,83% | 7,87% | 12,55% | 4,00% | **3,69%** |
| 20% | 20,02% | 7,85% | 9,21% | 17,56% | 5,20% | **4,95%** |

Bayes → closure loại **71–76% lỗi** ở mọi mức; OLD tốt nhất chỉ 61% (ở 20%) và âm ở 5%.
P@k của Bayes 87–94% so với 47–75% của OLD. Trên đồ thị sạch, Bayes (giả định ρ=5%) chỉ đổi
427 cạnh.

**Không nhạy với tỷ lệ nhiễu giả định sai** — giảm ròng (margin 0):

| thật \ giả định | 2% | 5% | 10% | 20% | 30% |
|---|---|---|---|---|---|
| 5% | +3.383 | **+3.819** | +2.792 | +1.747 | +1.167 |
| 10% | +6.598 | **+7.944** | +7.495 | +6.673 | +6.055 |
| 15% | +9.510 | +12.017 | **+12.099** | +11.571 | +11.087 |
| 20% | +12.204 | +15.739 | **+16.365** | +16.162 | +15.820 |

Mọi ô đều dương. Chỉ một ô thua OLD cùng mức (nhiễu thật 20%, giả định 2%: +12.204 so với +13.379). Với mọi mức nhiễu thật, giảm ròng cao nhất nằm ở giả định 5–10%.

**Giới hạn:** auditor biết họ phân phối của bộ sinh nhiễu (đổi theo phân phối biên). Với nhiễu
classifier, giả định "nhiễu độc lập với chữ ký" không còn đúng — xem 12.4.

### 12.4. Bối cảnh B: ba hướng, cross-fit

Lần chạy trước, luật mine trên đồ thị nhiễu (B1) thắng trên valid nhưng thua trên
CONFIRMATION nên không được chọn. Nguyên nhân: dự đoán 257 luật trên tài liệu train là
**in-sample** (lỗi 9,28% trên confirmation so với 12,13% trên valid) — luật học sai phân phối
lỗi. Sửa bằng **cross-fit trên valid**: 2 fold theo hash document; luật B1, kênh Bayes và
margin học từ fold kia (out-of-sample với classifier); fold test chấm một lần; cộng hai fold.

| Hướng | Cơ chế |
|---|---|
| B1 | luật khoá theo (chữ ký trên đồ thị nhiễu, nhãn hiện tại) → học thẳng P(gold \| cái auditor thấy) |
| B2 | bỏ chân EV–TX có luật dự đoán yếu (→ UNK) |
| Bayes | như 12.3, kênh = ma trận nhầm lẫn của classifier trên fold kia |

| Cấu hình (cross-fit, toàn bộ valid) | P@k | R_all | làm hỏng | **giảm ròng** | tỷ lệ lỗi |
|---|---|---|---|---|---|
| E4: OLD → closure → date | 72,94% | 29,14% | 1.551 | 2.334 | 10,00% |
| trước: NEW m0,05 → OLD → closure → date | 72,86% | 31,21% | 1.658 | 2.503 | 9,85% |
| **B1 cross-fit** | 69,66% | 40,89% | 2.534 | **2.917** | **9,47%** |
| B1 → OLD → closure → date | 67,82% | 43,67% | 2.935 | 2.887 | 9,50% |
| Bayes cross-fit | 71,63% | 32,53% | 1.842 | 2.494 | 9,86% |
| Bayes → OLD → closure → date | 69,68% | 37,63% | 2.324 | 2.692 | 9,68% |

*E4 giờ là 10,00% (trước 9,98%) vì date bridge ở bối cảnh B nay dùng neo EV–TX dự đoán thay vì
gold — sửa một rò rỉ nhỏ, lớp đó chỉ đóng góp 1 cạnh.*

- **B1 cross-fit là tốt nhất: +25% giảm ròng so với E4** (2.334 → 2.917), +17% so với cấu hình
  trước. Học từ lỗi out-of-sample là điều kiện cần — cùng phương pháp trên dự đoán in-sample
  thua ở confirmation.
- **B2 không có tác dụng:** θ chọn trên confirmation là 0 (không lọc). Độ tin cậy của luật
  EV–TX không phân biệt được chân đúng và chân sai.
- **Bayes thắng lớn trên fake_data nhưng chỉ nhỉnh trong bối cảnh B.** Lỗi classifier tương
  quan với chính các chữ ký (cùng đặc trưng sinh ra cả hai), nên giả định độc lập bị vi phạm;
  B1 học trực tiếp phân phối có điều kiện nên không cần giả định đó.
- **Xếp chồng không còn cộng dồn:** B1 → OLD → … thấp hơn B1 một mình.

**Giới hạn của cross-fit:** B1 dùng nhãn gold của một nửa valid để học. Triển khai thật cần dự
đoán out-of-sample trên train — tức là mine lại 257 luật theo k-fold trên train. Chưa làm.

### 12.5. Kết luận

1. **fake_data làm lộ một lỗi thiết kế mà nhiễu classifier che mất:** auditor luật có nền báo
   động giả cố định, nên vô dụng khi nhiễu thấp. Đưa tỷ lệ nhiễu vào quyết định (Bayes) sửa được:
   71–76% lỗi bị loại ở mọi mức.
2. **Bối cảnh B cải thiện từ +7% lên +25% so với E4** khi luật học từ lỗi out-of-sample của
   classifier (9,47%). Bước tiếp theo để dùng được ngoài valid: dự đoán k-fold trên train.

Script: `experiments/higher_order/fake_and_b.py`, `bayes_audit.py`, `bayes_b.py`.
Log: `experiments/logs/fake_and_b.log`, `bayes_audit.log`, `bayes_b.log`.

### 12.6. Vì sao bối cảnh B bắt được ít hơn fake_data

Chẩn đoán trên cấu hình tốt nhất của B (B1 cross-fit) và fake_data 10% (tỷ lệ lỗi gần bằng):

**(a) Một nửa lỗi classifier là nhãn hiếm bị giấu dưới BEFORE — và auditor sửa được 0%.**

| Loại lỗi (gold → đang có) | B: số | B: đã sửa | fake 10%: số | fake: đã sửa |
|---|---|---|---|---|
| BEFORE → CONTAINS | 5.658 | **84,6%** | 8.380 | 83,8% |
| BEFORE → SIMULTANEOUS | 661 | **99,8%** | 987 | 84,5% |
| CONTAINS → BEFORE | 5.293 | **0,0%** | 952 | 3,7% |
| SIMULTANEOUS → BEFORE | 738 | **0,0%** | 94 | 0,0% |
| OVERLAP → BEFORE | 464 | **0,0%** | 57 | 0,0% |

Loại "nhãn hiếm gán nhầm cho cặp BEFORE" gần như luôn được sửa, ở cả hai tập. Loại ngược lại
(cặp thật là CONTAINS/SIMULTANEOUS/OVERLAP nhưng classifier đoán BEFORE) chiếm **48,7%** lỗi của
classifier, nhưng chỉ ~10% lỗi của fake_data. Muốn lật BEFORE (prior 91%, độ tin cậy 94,6%)
sang nhãn hiếm cần bằng chứng mạnh hơn classifier ở đúng chỗ classifier yếu nhất. Đây chính là
bài toán recall nhãn hiếm của Bài 1, nơi mọi biểu diễn đồ thị dự đoán đều không thắng được. Vì
vậy trần R_all của cách tiếp cận này trong bối cảnh B là khoảng **51%**.

Ở bối cảnh A (EV–TX gold), riêng họ 3T đã lật đúng 2.078 cạnh CONTAINS → BEFORE (mục 11). Vậy
nửa lỗi này sửa được khi neo EV–TX đáng tin; trong bối cảnh B, classifier EV–TX (79,84%) chưa đủ.

**(b) Lỗi classifier tụ cụm, lỗi giả thì không.**

| | lỗi chung | cạnh tam giác kề của cạnh **sai** cũng sai | tam giác bắc cầu **ủng hộ** nhãn sai |
|---|---|---|---|
| B (classifier) | 12,13% | **32,90%** (quanh cạnh đúng: 7,61%) | **10,08%** |
| fake 10% | 10,05% | 10,13% (quanh cạnh đúng: 10,04%) | 0,48% |

Nhiễu ngẫu nhiên để lại vùng lân cận gần như đúng, nên cạnh sai mâu thuẫn với ngữ cảnh. Lỗi
classifier sinh ra từ cùng đặc trưng nên sai theo cụm: quanh một cạnh sai, 1/3 cạnh kề cũng sai,
và tam giác ủng hộ nhãn sai nhiều gấp 21 lần so với fake. Auditor dựa trên ngữ cảnh không thấy
được một cạnh sai khi các cạnh kề sai cùng kiểu.

**Kết luận:** trong bối cảnh B, auditor làm tốt việc **gỡ nhãn hiếm gán nhầm** (85–100%), và hầu
như không làm được việc **tìm nhãn hiếm bị bỏ sót**. Nên báo R_all theo từng loại lỗi. Đòn bẩy
cho nửa còn lại là tầng EV–TX tốt hơn hoặc tín hiệu văn bản, không phải thêm luật đồ thị.

Script: `experiments/higher_order/diag_b.py`, log `experiments/logs/diag_b.log`.

## 13. Bài 2 trên classifier mới và câu hỏi macro-F1 (24/09/2026)

Classifier Bài 1 mới: 257 luật + 719 luật từ trigger, macro-F1 26,15%, tỷ lệ lỗi 12,41% (cũ:
25,60%, 12,13%). Bối cảnh B, cross-fit 2 fold trên valid như §12.4. Thêm một chỉ số: **macro-F1
của đồ thị sau kiểm toán**, để đo Bài 1 → Bài 2 bằng cùng một thước.

### 13.1. Auditor giảm lỗi — nhưng cũng giảm macro-F1

| Classifier | Cấu hình | P | R | F1 | Tỷ lệ lỗi | **macro-F1 đồ thị** | F1 CONT / SIMU |
|---|---|---|---|---|---|---|---|
| cũ | không kiểm toán | — | — | — | 12,13% | 25,60% | 40,6 / 15,9 |
| cũ | E4 | 72,94% | 31,70% | 44,19% | 10,00% | 22,49% | 37,5 / 2,8 |
| cũ | B1 cross-fit | 69,66% | 43,65% | 53,67% | 9,47% | 20,52% | 25,8 / 0,0 |
| **mới** | không kiểm toán | — | — | — | 12,41% | **26,15%** | 44,1 / 15,9 |
| mới | E4 | 74,47% | 34,18% | 46,85% | 9,92% | 23,59% | 43,1 / 3,7 |
| mới | NEW m0,05 → OLD → … | 74,33% | 36,32% | 48,80% | 9,75% | 23,23% | 42,9 / 1,8 |
| **mới** | **B1 cross-fit** | 70,47% | **49,40%** | **58,08%** | **9,19%** | 21,52% | 31,7 / 0,0 |
| mới | Bayes → OLD → … | 70,86% | 44,58% | 54,73% | 9,47% | 22,25% | 37,8 / 0,7 |

- **Classifier mới cho pipeline tốt hơn theo số lỗi:** 9,19% (cũ 9,47%), giảm ròng 3.539 (cũ
  2.917), F1 phát hiện 58,08%. Classifier mới đoán CONTAINS nhiều hơn, tức có nhiều lỗi dạng
  "BEFORE bị gán CONTAINS" hơn — đúng loại auditor sửa giỏi.
- **Nhưng mọi auditor chọn theo số lỗi đều làm macro-F1 giảm 2,6–5 điểm.** Cách rẻ nhất để bớt lỗi
  là lật nhãn hiếm về BEFORE: 84% dự đoán SIMULTANEOUS là sai, nên xoá hết chúng thì bớt lỗi,
  nhưng F1 SIMULTANEOUS về 0. Đây chính là cái bẫy accuracy của Bài 1, lặp lại ở Bài 2.

### 13.2. Chọn theo macro-F1

Cùng luật B1, chỉ đổi mục tiêu chọn margin trên fold học: macro-F1 thay vì giảm lỗi ròng.

| Classifier | Mục tiêu chọn | gắn cờ | sửa đúng | làm hỏng | Tỷ lệ lỗi | **macro-F1 đồ thị** |
|---|---|---|---|---|---|---|
| cũ | giảm lỗi | 8.353 | 5.451 | 2.534 | 9,47% | 20,52% (−5,08) |
| cũ | **macro-F1** | 330 | 258 | 10 | 11,90% | **25,92% (+0,32)** |
| mới | giảm lỗi | 9.565 | 6.364 | 2.825 | 9,19% | 21,52% (−4,63) |
| mới | **macro-F1** | 356 | 288 | 9 | 12,16% | **26,50% (+0,35)** |

Chọn theo macro-F1, auditor chỉ gắn ~350 cờ với precision rất cao (288 sửa đúng, 9 làm hỏng),
và SIMULTANEOUS F1 tăng 15,9 → 17,8. Biến thể chuẩn hoá theo prior (như Bài 1) không giúp
(−0,23 đến +0,01).

### 13.3. Kết luận

1. **Hai mục tiêu cho hai cấu hình khác nhau.** Giảm số cạnh sai: B1 theo giảm lỗi, 12,41% →
   9,19%. Giữ và cải thiện nhãn hiếm: B1 theo macro-F1, 26,15% → **26,50%** — con số tốt nhất
   của cả pipeline Bài 1 + Bài 2.
2. **Phải báo cả hai chỉ số.** Chỉ báo tỷ lệ lỗi / R_all sẽ che việc auditor xoá nhãn hiếm.
3. Pipeline tốt nhất theo macro-F1: 25,60% (257 luật) → 26,15% (+ trigger) → 26,50% (+ kiểm toán
   theo macro-F1).

Script: `experiments/higher_order/semantic_export.py`, `bai2_newclf.py`, `bai2_macro.py`.

## 14. Kiểm toán cả bốn loại cạnh trên đồ thị hợp nhất (24/09/2026)

Luật đồ thị hợp nhất (đường qua mọi sự kiện và TIMEX, khoá theo chữ ký + nhãn hiện tại), mine
trên CONFIRMATION-2 **dưới cùng loại nhiễu** mà đồ thị cần kiểm toán mang, margin chọn trên
CONFIRMATION-1 theo giảm lỗi ròng, valid mở một lần. Tỷ lệ lỗi tính trên cả 188.924 cạnh.

| Nhiễu | P | R | F1 | Giảm ròng | Lỗi | macro-F1 đồ thị |
|---|---|---|---|---|---|---|
| Classifier (cả đồ thị do giai đoạn 1 dự đoán), chọn theo giảm lỗi | 72,25% | 28,59% | 40,97% | +4.505 | 15,22% → 12,83% | 29,87% → 27,46% |
| Classifier, chọn theo macro-F1 | 97,76% | 0,46% | 0,91% | +110 | 15,22% → 15,16% | 29,87% → 30,05% |
| Bơm trên cả 4 loại, 5% | 89,04% | 48,97% | 63,19% | +4.070 | 5,02% → 2,87% | 82,82% → 86,76% |
| Bơm trên cả 4 loại, 10% | 82,79% | 59,25% | 69,07% | +8.868 | 10,02% → 5,33% | 69,26% → 73,51% |
| Bơm trên cả 4 loại, 15% | 77,85% | 67,94% | 72,56% | +13.761 | 15,06% → 7,78% | 60,94% → 64,60% |
| Bơm trên cả 4 loại, 20% | 79,86% | 67,46% | 73,13% | +18.949 | 19,99% → 9,96% | 51,79% → 56,44% |
| fake_data của bạn r05 (chỉ EV–EV) | 92,71% | 75,41% | 83,17% | +3.806 (69%) | 2,90% → 0,89% | 90,32% → 94,19% |
| fake_data r10 | 84,31% | 84,66% | 84,49% | +7.589 (69%) | 5,85% → 1,83% | 83,76% → 89,20% |
| fake_data r15 | 86,94% | 84,66% | 85,78% | +11.868 (72%) | 8,76% → 2,48% | 77,30% → 84,38% |
| fake_data r20 | 86,22% | 87,21% | 86,72% | +16.069 (73%) | 11,65% → 3,15% | 71,35% → 79,56% |

Theo loại cạnh, với nhiễu bơm 20%: EV–EV 20,06% → 7,21%, EV→TIMEX 20,13% → 7,26%, TIMEX–TIMEX
19,60% → 13,29%, nhưng **TIMEX→EV 19,83% → 18,29%** — gần như không sửa được.

**Kết luận:**
1. Với nhiễu bơm, đồ thị hợp nhất sửa được **~50% lỗi trên toàn đồ thị**, ~64% ở EV–EV và
   EV→TIMEX. Trên fake_data (chỉ EV–EV) loại 69–73% lỗi — ngang auditor Bayes trên đồ thị EV–EV
   (71–76%), không hơn.
2. Cạnh TIMEX→EV hầu như không sửa được bằng pattern: nhầm lẫn chính ở đó là CONTAINS/BEFORE giữa
   một TIMEX và một sự kiện, và đường đi qua node khác không phân biệt được hai trường hợp.
3. Với nhiễu classifier, cùng mâu thuẫn như §13: chọn theo số lỗi thì giảm 15,22% → 12,83% nhưng
   macro-F1 giảm; chọn theo macro-F1 thì gần như không đổi.

Script: `experiments/higher_order/bai2_unified.py`.

## 15. Auditor theo tầng + tầng GRAPH, trên classifier tầng 30,83% (24/09/2026)

Auditor là miner theo tầng của Bài 1 (ONT/ARG/DISC/LEX/TIME) cộng thêm tầng **GRAPH**: chữ ký đường
đi a–x–b, a–x–y–b của cạnh trong đồ thị đang kiểm toán (ở Bài 2 các cạnh xung quanh là quan sát).
Luật học **theo từng nhóm (loại cạnh, nhãn hiện tại)**: trong nhóm, học cạnh nào sai và thực ra là gì.
Luật ghi đè khi vượt ngưỡng precision riêng theo (loại cạnh, nhãn); ngưỡng chọn theo giảm lỗi ròng
hoặc theo macro-F1. Cả bốn loại cạnh, valid mở một lần.

- A = chỉ GRAPH · B = mọi tầng + GRAPH, luật liên tầng · C = mọi tầng, không GRAPH.
- Nhiễu classifier: mine trên CONFIRMATION-2 (nửa mine / nửa xác nhận), ngưỡng trên CONFIRMATION-1.
- Nhiễu bơm cả 4 loại: mine DISCOVERY, xác nhận CONFIRMATION-1, ngưỡng CONFIRMATION-2.

**Hai lỗi đã sửa giữa chừng.** (1) Cổng "lift ≥ 2" không thể qua khi nhãn cần khôi phục là đa số
trong nhóm (60% cạnh EV–EV classifier gán CONTAINS thực ra là BEFORE; với nhiễu bơm 10% là ~50%) —
bản đầu vì vậy không sửa được cạnh EV–EV nào. Thay bằng cổng thích ứng: `k/n ≥ min(2·prior, (1+prior)/2)`
và Wilson > prior. (2) Ngưỡng dùng chung cho mọi loại cạnh → tách theo (loại cạnh, nhãn).

### 15.1 Nhiễu classifier (đồ thị do classifier tầng dự đoán, lỗi 15,11%, macro-F1 30,83%)

| Auditor · mục tiêu | P | R | F1 | Giảm ròng | Lỗi | macro-F1 đồ thị |
|---|---|---|---|---|---|---|
| A · giảm lỗi | 69,95% | 29,86% | 41,86% | +4.655 | 15,11% → 12,65% | 30,83% → 31,96% |
| A · macro-F1 | 70,14% | 24,20% | 35,98% | +3.788 | → 13,11% | → 32,38% |
| **B · giảm lỗi** | 69,73% | **37,84%** | **49,05%** | **+5.741** | → **12,07%** | → 31,97% |
| **B · macro-F1** | 70,09% | 26,82% | 38,80% | +4.170 | → 12,91% | → **32,44%** |
| C · giảm lỗi | 75,63% | 22,73% | 34,95% | +4.100 | → 12,94% | → 31,31% |
| C · macro-F1 | 72,22% | 23,68% | 35,66% | +3.857 | → 13,07% | → 31,58% |

Theo loại (B · giảm lỗi): EV–EV 12,4% → 9,1%, EV→TIMEX 10,5% → 9,7%, TIMEX→EV 25,9% → 21,4%,
TIMEX–TIMEX 14,4% → 13,6%.

**Lần đầu tiên hai mục tiêu không còn mâu thuẫn:** chọn theo giảm lỗi vẫn **tăng** macro-F1
(30,83% → 31,97%). Các auditor trước (§13, §14) chọn theo giảm lỗi đều làm macro-F1 giảm 2,6–5 điểm,
vì chúng lật nhãn hiếm về BEFORE. Chia theo nhãn hiện tại khiến mỗi nhóm có luật riêng, nên nhóm
nhãn hiếm không bị xoá hàng loạt.

### 15.2 Nhiễu bơm trên cả bốn loại cạnh

| Mức | Auditor | P | R | F1 | Lỗi | macro-F1 đồ thị |
|---|---|---|---|---|---|---|
| 10% | A | 82,59% | 64,38% | 72,36% | 9,94% → 4,90% | 69,43% → 76,99% |
| 10% | **B** | 78,44% | 72,29% | **75,24%** | → **4,74%** | → **77,11%** |
| 10% | C | 72,29% | 56,08% | 63,16% | → 6,52% | → 73,30% |
| 20% | A | 85,51% | 62,82% | 72,43% | 19,89% → 9,54% | 51,25% → **63,51%** |
| 20% | **B** | 81,81% | 77,40% | **79,54%** | → **7,96%** | → 62,41% |
| 20% | C | 80,09% | 66,09% | 72,42% | → 10,06% | → 56,22% |

Theo loại (B, 20%): EV–EV 20,0% → 6,4%, EV→TIMEX 20,0% → 6,4%, **TIMEX→EV 19,5% → 12,6%**,
TIMEX–TIMEX 19,9% → 10,2%.

So với auditor đồ thị hợp nhất (§14): 10% lỗi còn 4,74% (trước 5,33%); 20% còn 7,96% (trước
9,96%). **TIMEX→EV giờ sửa được** (19,5% → 12,6%, trước 19,83% → 18,29%) nhờ chia theo nhãn hiện tại.

### 15.3 Kết luận

1. **Auditor tầng + GRAPH (B) là tốt nhất ở mọi loại nhiễu.** Nhiễu classifier: lỗi 15,11% →
   12,07%, F1 phát hiện 49,05%; nhiễu bơm 10–20%: loại 52–60% lỗi, F1 phát hiện 75–80%.
2. **Tầng GRAPH là phần quan trọng nhất** (C không có GRAPH kém hơn rõ, nhất là TIMEX→EV), còn các
   tầng quan sát thêm được khoảng +1.100 cạnh sửa ở nhiễu classifier (B so với A).
3. **Pipeline tốt nhất theo macro-F1: Bài 1 tầng 30,83% → Bài 2 B chọn theo macro-F1 32,44%.**
   Theo tỷ lệ lỗi: 15,11% → 12,07% mà macro-F1 vẫn tăng.

Script: `experiments/higher_order/bai2_layered.py`, log `experiments/logs/bai2_layered.log`.

## 16. Thăm dò: suy luận ở mức tam giác (bộ 3) thay vì từng cặp (24/09/2026)

Mọi quyết định trước đều theo từng cạnh. Ở đây đơn vị là **tam giác** (3 node sự kiện/TIMEX, đủ 3
cạnh); cấu hình = loại node + 3 nhãn có hướng. Tần suất cấu hình học từ gold train (bỏ 400 doc đầu):
792 loại cấu hình, 5.572.591 tam giác. Không đọc nhãn valid.

**Phát hiện:** tỷ lệ cạnh sai nằm trong ít nhất một tam giác có cấu hình **chưa từng xuất hiện trong gold**:

| Đồ thị | Cạnh sai được phủ | Cạnh trong tam giác bất thường mà sai |
|---|---|---|
| Classifier tầng (lỗi 15,11%) | **74,6%** | 27,8% |
| Nhiễu bơm 10% cả bốn loại | **98,4%** | 12,7% |

**Sửa thô bằng bỏ phiếu tam giác** (mỗi tam giác bất thường bầu cho thay đổi một cạnh đưa nó về cấu
hình gold phổ biến nhất; cạnh được đổi khi có ≥ v phiếu đồng thuận):

| Đồ thị | Cấu hình | Giảm ròng | Macro-F1 | So với auditor tầng B (§15) |
|---|---|---|---|---|
| Classifier tầng | ≥ 1 phiếu | +4.930 | 30,83% → 26,80% | B: +5.741, macro 31,97% |
| Classifier tầng | ≥ 3 phiếu | +4.038 | → 29,80% | |
| Nhiễu bơm 10% | **≥ 3 phiếu** | **+10.284** (55% lỗi) | 69,43% → **80,58%** | B: +9.818, macro 77,11% |

**Đọc kết quả:** tín hiệu phát hiện ở mức tam giác rất mạnh (phủ 75–98% lỗi) và không cần học gì
ngoài thống kê cấu hình gold. Với nhiễu bơm, bỏ phiếu thô đã **hơn** auditor tầng tốt nhất. Với nhiễu
classifier, phần *chọn cạnh nào để sửa và sửa thành gì* còn thô nên vẫn thua B và làm mất nhãn hiếm.
Hướng tiếp: sửa chung theo document (tối ưu tổng mức bất thường của mọi tam giác cộng chi phí đổi
nhãn theo độ tin cậy của B), và mở rộng lên bộ 4, bộ 5.

Script: `experiments/higher_order/subgraph_probe.py`.

## 17. Sửa chung theo document trên tam giác, bộ 4, và ghép với auditor tầng (24/09/2026)

### 17.1 Mô hình

Với mỗi document, tìm nhãn L cực tiểu năng lượng

```
E(L) = Σ_cạnh U_e(l_e) + λ · Σ_tam giác W_t · T_t(L)
U_e(l) = -(1-α)·log P(l | loại cạnh) - log P(nhãn đang thấy | nhãn thật l)     (một ngôi: prior + kênh nhiễu)
T_t    = -[ log p~(cấu hình t) - Σ_{cạnh ∈ t} log P(l_e | loại cạnh) ]         (tam giác: trừ PMI)
```

- p~ học từ gold train (DISCOVERY + CONFIRMATION-1, bỏ 400 doc đầu), làm trơn về tích biên.
- **Dùng PMI chứ không dùng tần suất thô:** tần suất thô thưởng cho việc đổi hết thành BEFORE, đúng
  lỗi của bản bỏ phiếu ở §16.
- **α làm yếu prior:** α = 0 là hậu nghiệm Bayes, tự nó đã lật nhãn hiếm về BEFORE
  (P(SIMULTANEOUS thật | thấy SIMULTANEOUS) = 16% với classifier).
- Tối ưu: ICM (đổi từng cạnh nếu năng lượng giảm), chỉ xét cạnh nằm trong tam giác có PMI âm, đẩy
  lại hàng xóm khi có thay đổi. λ, α, cách cân (tổng/trung bình) chọn trên tập chỉnh; valid mở một lần.

### 17.2 Kết quả trên dữ liệu đầy đủ

| Nhiễu | P | R | F1 | Lỗi | macro-F1 đồ thị | Auditor tầng B (§15) |
|---|---|---|---|---|---|---|
| Bơm 10%, cả 4 loại | 92,32% | 88,24% | **90,23%** | 9,94% → **1,94%** | 69,08% → **85,10%** | 4,74%, 77,11% |
| Bơm 20%, cả 4 loại | 93,52% | 85,31% | **89,23%** | 19,89% → **4,16%** | 50,98% → **72,46%** | 7,96%, 62,41% |
| Classifier tầng, chọn theo giảm lỗi | 71,09% | 35,20% | 47,09% | 15,11% → 12,32% | 30,83% → 27,43% | 12,07%, 31,97% |
| Classifier tầng, chọn theo macro-F1 | 60,27% | 24,29% | 34,63% | → 14,39% | → 31,01% | 32,44% |

Theo loại, nhiễu bơm 20%: EV–EV 20,0% → 3,9%, EV→TIMEX 20,0% → 2,1%, **TIMEX→EV 19,5% → 6,0%**,
TIMEX–TIMEX 19,9% → 4,8%.

**Với nhiễu bơm, sửa chung theo tam giác loại ~80% lỗi** (auditor tầng: 52–60%), chỉ cần thống kê
cấu hình gold và mô hình nhiễu. Với nhiễu classifier nó chỉ ngang auditor tầng, vì kênh nhiễu coi lỗi
từng cạnh độc lập còn lỗi classifier tụ thành cụm.

### 17.3 Bộ 4: không có tín hiệu thêm (ở cỡ mẫu này)

Cụm 4 node đủ 6 cạnh; thống kê từ mẫu 525.191 cụm gold (4.781 cấu hình). Xét các cạnh mà tam giác
không phát hiện: cạnh sai nằm trong cụm 4 "chưa gặp" 71,3%, cạnh đúng 75,6% — tỷ số 0,94×, **không
phân biệt được**. Không gian cấu hình bộ 4 (6⁶ tổ hợp nhãn mỗi kiểu node) quá thưa so với dữ liệu; bộ 5
thưa hơn nữa. Bộ 4–5 chỉ có ích nếu gộp cấu hình về dạng trừu tượng hơn — chưa làm.

### 17.4 Nhiễu classifier: ghép auditor tầng B rồi sửa chung tam giác, cross-fit trên valid

Mọi thứ học từ lỗi out-of-sample: valid chia 2 fold theo hash; trong fold học chia 3 phần (mine luật B
/ xác nhận luật B / chỉnh ngưỡng B, rồi kênh nhiễu của đầu ra B, λ, α). Fold test chấm một lần; cộng
hai fold.

| Cấu hình (cross-fit) | P | R | F1 | Giảm ròng | Lỗi | macro-F1 đồ thị |
|---|---|---|---|---|---|---|
| Classifier tầng | — | — | — | — | 15,11% | 30,83% |
| B · giảm lỗi | 68,29% | 36,48% | 47,56% | +5.262 | 12,33% | 31,30% |
| Chỉ tam giác · giảm lỗi | 71,08% | 33,86% | 45,87% | +5.076 | 12,43% | 27,41% |
| **B → tam giác · giảm lỗi** | 69,86% | **41,72%** | **52,24%** | **+6.231** | **11,81%** | 31,36% |
| B · macro-F1 | 67,32% | 25,36% | 36,85% | +3.542 | 13,24% | 31,89% |
| Chỉ tam giác · macro-F1 | 66,71% | 20,99% | 31,93% | +2.454 | 13,81% | 31,70% |
| **B → tam giác · macro-F1** | 71,02% | 34,12% | 46,09% | +5.232 | 12,34% | **32,25%** |

- **Ghép hai tầng tốt hơn từng tầng riêng** theo cả hai mục tiêu: lỗi 12,33% → **11,81%** (+969 cạnh so
  với B), macro-F1 31,89% → **32,25%**. F1 SIMULTANEOUS 29,5%, CONTAINS 56,7%.
- Cross-fit dùng ít dữ liệu mine hơn (~120 doc mỗi phần) nên B cross-fit (12,33%) kém hơn B mine trên
  CONFIRMATION-2 ở §15 (12,07%); hai con số không cùng protocol. So trong cùng protocol, ghép luôn thắng.
- **Cho Bài 1:** sửa chung đầu ra classifier theo tam giác (không dùng luật kiểm toán) nâng macro-F1
  30,83% → 31,70% (cross-fit), tức suy luận chung ở mức document thêm được +0,87.

### 17.5 Kết luận

1. **Tam giác là đơn vị suy luận đúng cho Bài 2:** với nhiễu bơm loại ~80% lỗi, F1 phát hiện ~90%.
2. **Bộ 4–5 không thêm tín hiệu** ở dạng cấu hình đầy đủ; cần trừu tượng hoá mới có hy vọng.
3. **Với nhiễu classifier, tốt nhất là ghép:** luật tầng theo cạnh sửa trước, tam giác sửa chung sau —
   lỗi 15,11% → 11,81%, hoặc macro-F1 30,83% → 32,25%, cross-fit trên valid.

Script: `joint_repair.py`, `quad_probe.py`, `bai2_combo.py`.
