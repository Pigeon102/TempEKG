# Luật bậc cao (bộ 3, 4, 5) — kết quả trên Bài 1 và Bài 2

**Kết luận ngắn:** bộ 3/4/5 **không dùng được cho Bài 1**, nhưng làm **Bài 2 tốt gấp 3,9 lần**.

| | Bài 1 (classifier) | Bài 2 (audit) |
|---|---|---|
| Trước | 24,28% macro-F1 | R_all 8,24% |
| Sau khi áp bộ 3/4/5 | **18,26%** (tệ hơn 6,02đ) | **31,99%** (tốt hơn 3,9×) |

Lý do khác biệt nằm ở một giả định: luật bậc cao đọc **nhãn của cạnh kề**. Ở Bài 2 đồ thị
đã tồn tại nên nhãn đó có sẵn; ở Bài 1 chúng cũng là thứ phải dự đoán.

---

## 1. Xuất phát điểm: vì sao đi tìm bộ 3

Pair-level thất bại hoàn toàn với nhãn hiếm. Đào 97 instance BEGINS-ON và 42 instance
ENDS-ON thì thấy pattern có lift rất cao (759×, 228×) nhưng **không tồn tại thật**:

| Pattern BEGINS-ON | train | valid |
|---|---|---|
| `type_pair=(Hostile_encounter, Dispersal)` | 4/5 = 80% | **0/16 = 0%** |
| `type_pair=(Traveling, Traveling)` | 4/14 = 28,6% | **0/63 = 0%** |
| `type_pair=(Killing, Use_firearm)` | 3/52 = 5,8% | **0/27 = 0%** |

**1/14 pattern top bắt được dù một instance trên valid.** Nguyên nhân: gần như mọi pattern
có `doc = 1` — chúng là chữ ký của một document, không phải quy luật thời gian.

## 2. Chữ ký tam giác — tín hiệu thật

Với mỗi cạnh `(a,b)` và event thứ ba `c`, cặp nhãn `(a-c, c-b)` tạo một chữ ký tam giác.

| Nhãn | Chữ ký | k/n | lift |
|---|---|---|---|
| BEGINS-ON | `SIMULTANEOUS, BEGINS-ON` | **84/84** | 2.279× |
| ENDS-ON | `SIMULTANEOUS, ENDS-ON` | **32/32** | 5.263× |
| SIMULTANEOUS | `SIMULTANEOUS, SIMULTANEOUS` | **1.470/1.470** | 120× |
| OVERLAP | `SIMULTANEOUS, OVERLAP` | **392/392** | 178× |

Khác hẳn pair-level: `SIMU,SIMU → SIMU` xuất hiện 1.470 lần, không thể từ một bài viết.

### Tách định lý khỏi phát hiện

Không phải chữ ký nào cũng là phát hiện. `SIMULTANEOUS ∘ BEGINS-ON = BEGINS-ON` là **định lý**
của đại số Allen — precision 100% vì buộc phải đúng. Đo trên 36 chữ ký:

| Loại | Số chữ ký |
|---|---|
| Toán học ÉP ra 1 nhãn (định lý) | 5 |
| Toán học để ngỏ, dữ liệu chốt (**luật học được**) | **31** |

**31/36 là luật học được** — đại số không cho, dữ liệu chứng minh. Đây là phần bổ sung so
với bộ ràng buộc trong paper.

Ví dụ rõ nhất: `OVERLAP, OVERLAP → BEGINS-ON` (47/1.366, lift 78×). Allen composition của
`o ∘ o` cho `{b, m, o}` — **không** ép ra BEGINS-ON. Nhưng dữ liệu nói có.

### Luật giữ được trên valid

| Luật | train P | n | doc | valid P | nv |
|---|---|---|---|---|---|
| `SIMU, BEFO → BEFORE` | 100,0% | 15.014 | 192 | **100,0%** | 16.264 |
| `BEFO, SIMU → BEFORE` | 100,0% | 14.092 | 184 | **100,0%** | 13.428 |
| `BEFO, CONT → BEFORE` | 99,0% | 60.000 | 261 | **99,7%** | 64.593 |
| `SIMU, SIMU → SIMULTANEOUS` | 100,0% | 615 | 65 | **100,0%** | 855 |
| `BEGI, SIMU → BEGINS-ON` | 100,0% | 60 | 9 | **100,0%** | 22 |
| `OVER, CONT → CONTAINS` | 70,8% | 1.704 | 30 | 83,6% | 1.053 |

Cột `doc` cho 192, 184, 261 document — đây là quy luật thật, không phải chữ ký document.

### Ba luật KHÔNG giữ được

| Luật | train | valid | doc |
|---|---|---|---|
| `ENDS, BEFO → CONTAINS` | 78,5% | **15,1%** | 6 |
| `BEGI, CONT → CONTAINS` | 80,5% | 53,2% | 12 |
| `BEGI, BEFO → BEFORE` | 90,1% | 66,2% | 18 |

Document diversity lại là thứ dự báo — đúng như ở pair-level.

## 3. Bộ 4 và bộ 5

Cổng lọc giống nhau cho mọi bậc: `n≥30`, `k≥10`, `doc≥5`, `wlb≥0,50`.

| Bậc | Chữ ký | Luật qua cổng |
|---|---|---|
| 3 | 34 | 22 |
| 4 | 404 | 123 |
| 5 | 1.888 | 360 |

### Cảnh báo phương pháp: cách gộp phiếu đổi kết quả 13 điểm

Bộ 5 bắn trung bình **18,8 lần trên mỗi cạnh**, bộ 3 ít hơn nhiều. Cộng thô (`sum`) để số
lượng quyết định thay vì độ tin cậy:

| Cấu hình | #luật | sum | **mean** | max |
|---|---|---|---|---|
| chỉ bộ 3 | 22 | 20,08% | **33,14%** | 32,79% |
| chỉ bộ 4 | 123 | 32,37% | 35,70% | 34,58% |
| chỉ bộ 5 | 360 | 36,70% | 36,38% | 35,34% |
| bộ 3+4 | 145 | 29,71% | 36,53% | 36,04% |
| **bộ 3+4+5** | **505** | 34,09% | **36,70%** | 36,83% |

Bộ 3 được 20,08% với `sum` nhưng 33,14% với `mean` — **khác 13 điểm chỉ do cách đếm**.
Mọi so sánh giữa các bậc phải chuẩn hóa.

### Đường cong đóng góp (theo `mean`)

```
pair-level  25,60%
bộ 3        33,14%   +7,54
bộ 3+4      36,53%   +3,39
bộ 3+4+5    36,70%   +0,17   ← bão hòa
```

**Bộ 5 gần như hết tác dụng** khi đã có bộ 3+4. Không cần đi lên bộ 6.

Luật bộ 5 tự thân vững: median 15 document/luật, tối thiểu 5.

---

## 4. BÀI 1 — chạy lặp THẤT BẠI

Con số 36,70% ở trên **không phải kết quả Bài 1**, vì nó đọc nhãn cạnh kề. Phép thử công
bằng: 257 rule pair-level khởi tạo đồ thị, rồi bộ 3/4/5 tinh chỉnh trên chính dự đoán đó.
Mỗi cạnh bị **ẩn đi** khi đánh giá nó, nên luật không bao giờ đọc câu trả lời của chính mình.

| Vòng | macro-F1 | acc | cạnh đổi | đổi đúng |
|---|---|---|---|---|
| 0 (pair-level) | **24,28%** | 86,92% | — | — |
| 1 | 20,71% | 88,52% | 2.534 | 59,2% |
| 2 | 19,09% | 89,45% | 999 | 65,1% |
| 3 | 18,37% | 89,64% | 355 | 57,2% |
| 4 | 18,38% | 89,74% | 90 | 68,9% |
| 5 | **18,26%** | 89,76% | 54 | 57,4% |

**Mất 6,02 điểm macro-F1** dù accuracy *tăng* 2,84 điểm — đúng bẫy accuracy: hệ hội tụ về
đoán BEFORE.

F1 từng nhãn cho thấy rõ:

```
vòng 0:  CONT 34,9%   SIMU 15,1%   OVER 2,8%
vòng 5:  CONT 14,3%   SIMU  0,7%   OVER 0,0%
```

### Vì sao thất bại

Mỗi vòng đổi đúng chỉ **57–65%** — tức 35–43% thay đổi là sai. Vì BEFORE chiếm 90% dữ liệu,
thay đổi sai nghiêng về BEFORE, và vòng sau đọc chính nhãn sai đó làm bằng chứng. Số cạnh
đổi giảm dần (2.534 → 54) nên hệ **có hội tụ** — nhưng hội tụ vào điểm xấu.

### Trần trên cho thấy khoảng cách

| | macro-F1 | acc |
|---|---|---|
| Chạy lặp (thực tế) | 18,26% | 89,76% |
| Pair-level 257 rule | **24,28%** | 86,92% |
| Bộ 3/4/5 trên đồ thị **GOLD** | *34,41%* | *93,71%* |

34,41% là **trần không đạt được lúc test**. Khoảng cách 34,41% → 18,26% là cái giá của việc
phải tự đoán nhãn cạnh kề.

**Kết luận Bài 1: 257 rule pair-level (25,60%) vẫn là kết quả tốt nhất.** Luật bậc cao không
cải thiện được, và chạy lặp làm tệ đi.

---

## 5. BÀI 2 — luật bậc cao THÀNH CÔNG

Đây là nơi giả định được thỏa mãn: đồ thị đã tồn tại, nhãn cạnh kề đã biết.

Bối cảnh — Task 5 đo auditor cũ trên cạnh model dự đoán và nó sụp đổ:

| | Model thật | Nhiễu ngẫu nhiên |
|---|---|---|
| repair@k | **31,84%** | 96,61% |
| R_all | 8,24% | 27,43% |

Nguyên nhân: **86,5% lỗi của model là một cặp nhãn hoán đổi** (BEFORE↔CONTAINS 1.660+1.257),
trong khi nhiễu ngẫu nhiên rải đều. Mọi số C3 cũ đang đo mô hình nhiễu, không phải phương pháp.

### Kết quả áp luật bậc cao

Trên 149 document valid, 27.063 cặp, 3.373 cạnh sai (12,46%):

| Chỉ số | closure cũ | **bậc cao** | tỷ lệ |
|---|---|---|---|
| Xếp hạng | 20.818 cạnh | **1.790 cạnh** | ít hơn 11,6× |
| P@k | 8,63% | **64,64%** | 7,5× |
| found_all | 25,88% | **34,30%** | 1,3× |
| repair@k | 31,84% | **93,26%** | 2,9× |
| **R_all** | 8,24% | **31,99%** | **3,9×** |

**repair@k 93,26%** gần bằng mức 96,61% mà closure chỉ đạt trên nhiễu nhân tạo — nghĩa là
luật bậc cao xử lý được lỗi thật của model, thứ closure thất bại.

### Vì sao hiệu quả

Closure chỉ nói *"nhãn này không tương thích"*; luật bậc cao nói thẳng **nhãn nào đúng** kèm
trọng số. Với lỗi BEFORE↔CONTAINS, closure không phân biệt được vì cả hai đều tương thích
với hầu hết ngữ cảnh.

Nó cũng **chọn lọc hơn nhiều**: gắn cờ 1.790 thay vì 20.818 cạnh mà tìm được nhiều hơn.

---

## 6. Lỗ hổng ánh xạ ENDS-ON

Hai phần tử Allen bị chia sẻ giữa các nhãn MAVEN:

```
'b' thuộc về: BEFORE, ENDS-ON
'e' thuộc về: SIMULTANEOUS, BEGINS-ON
```

`ENDS-ON → {b, m}` chứa `b` — cùng phần tử với BEFORE. Nên **mọi** suy luận ra `b` đều buộc
giữ ENDS-ON làm ứng viên. Đó là toàn bộ 80.571 cạnh "còn 2 nhãn" (73,3%).

Thử cách đọc `ENDS-ON → {f, fi, e}` ("kết thúc cùng lúc"):

| Ánh xạ | Mâu thuẫn | Ép ra 1 nhãn | Ép đúng | Ép SAI |
|---|---|---|---|---|
| hiện tại `{b,m}` | 26,64% | 1.573 (1,4%) | 1.533 | 40 |
| thay thế `{f,fi,e}` | 26,67% | **82.128 (74,7%)** | 79.832 | **2.296** |

Biến 1,4% → 74,7% số cạnh thành quyết định được, precision 97,2%.

**Chưa kết luận nên đổi**, ba lý do:

1. Ép SAI tăng từ 40 lên 2.296 — đắt trong ngữ cảnh audit.
2. Hàng xóm phổ biến nhất của cạnh ENDS-ON là `BEFORE/BEFORE` (357 lần), phù hợp với
   `{b,m}` hơn là "kết thúc cùng lúc".
3. Chỉ có 42 instance ENDS-ON — quá ít để phân xử bằng thống kê.

Đây là câu hỏi về **định nghĩa nhãn trong MAVEN**, cần tra tài liệu gốc.

---

## 7. Giới hạn

1. **BEGINS-ON / ENDS-ON vẫn 0%** ở mọi bậc. Chữ ký `SIMU,BEGI → BEGINS-ON` đạt precision
   100% nhưng chỉ 22–30 instance trên valid — không đủ để có F1 khi cạnh tranh với BEFORE.
2. **Luật bậc cao không dùng được cho Bài 1** trừ khi có nguồn nhãn cạnh kề đáng tin.
3. **Số Bài 2 đo trên 149 document** (không phải toàn bộ 705), vì chi phí duyệt bộ 5.
4. **Chưa qua giao thức confirmation split** như Bài 1 — luật bậc cao mới chỉ mine trên
   train, kiểm trên valid.

## 8. Tái tạo

```bash
# scratchpad, chưa đưa vào src/
python triad.py      # tách định lý khỏi luật học được
python quad.py       # bộ 4, phân tích mơ hồ còn lại
python quint.py      # bộ 5 + điều tra lỗ hổng ánh xạ
python norm5.py      # kiểm soát cách gộp phiếu
python iterate.py    # chạy lặp cho Bài 1
python task5b.py     # áp vào Bài 2
```

---

## 9. Bổ sung: ba cơ chế inference đều thất bại, và vì sao

Mục 4 kết luận "chạy lặp hỏng". Ba thí nghiệm tiếp theo loại trừ các giả thuyết cạnh tranh.

### 9.1 Soft one-pass — cũng hỏng, và hỏng đơn điệu

Giả thuyết: vấn đề là *hard label commitment*, dùng phân phối thay vì nhãn cứng sẽ cứu được.

```
Score(r_ab) = s_ab(r) + λ · Σ_c Σ_r1,r2  p(r_ac=r1)·p(r_cb=r2)·φ(r,r1,r2)
```

| λ | macro-F1 | acc |
|---|---|---|
| pair-only | **24,11%** | 87,54% |
| 0,1 | 22,90% | 82,71% |
| 0,5 | 16,96% | 90,87% |
| 1,0 | 16,39% | 91,13% |
| 4,0 | 16,09% | 91,16% |

**Không λ nào vượt pair-only**, và đường cong đơn điệu giảm — λ→0 về đúng pair-only.
Giả thuyết bị bác bỏ.

Nguyên nhân: tích `p(r_ac)·p(r_cb)` nhân hai phân phối thiên lệch BEFORE tạo thiên lệch
**bình phương**. CONTAINS sụp từ 34,1% xuống 3,0% ở λ=1,0.

### 9.2 Noise sweep — luật bậc cao KHÔNG mong manh

Bắt đầu từ đồ thị gold, làm hỏng hàng xóm theo tỷ lệ kiểm soát:

| Nhiễu | uniform | model-shaped |
|---|---|---|
| 0% | 33,03% | 33,03% |
| 10% | 28,66% | 28,78% |
| **12,5%** (tỷ lệ lỗi thật) | 27,00% | **27,66%** |
| 20% | 24,20% | 24,64% |
| 40% | 19,17% | 19,80% |

**Ở đúng mức nhiễu thực tế, luật bậc cao vẫn đạt 27,66% > 24,11% của pair-only.**
Nhưng thực tế chỉ đo được 18,24% (hard) và 22,90% (soft) — thiếu 9,42đ và 4,76đ.

Nhiễu model-shaped còn *tốt hơn* uniform ở mọi mức, nên cấu trúc lỗi BEFORE↔CONTAINS
**không phải** nguyên nhân.

### 9.3 Nguyên nhân thật: lỗi tụm theo document

| | giá trị |
|---|---|
| sd tỷ lệ lỗi giữa các document | **13,5%** |
| sd kỳ vọng nếu lỗi độc lập | **2,7%** |
| document tệ nhất | **71% cạnh sai** |
| phân vị 10/25/50/75/90 | 2% / 6% / 13% / 22% / 33% |

Gấp **5 lần** mức độc lập. Khi cả document sai cùng lúc, mọi tam giác trong đó hỏng đồng
thời — mô phỏng nhiễu rải đều không tái hiện được điều này.

### 9.4 Joint inference + MDD pruning — ILP không cứu được

Tối ưu toàn document bằng coordinate ascent, MDD pruning cắt miền theo Allen composition:

```
max  Σ_e s_e(y_e)  +  λ · Σ_triangles φ(y_ac, y_cb, y_ab)
```

| λ | không MDD | có MDD |
|---|---|---|
| pair-only | 22,90% | — |
| **0,10** | **23,10%** | 22,49% |
| 0,50 | 21,44% | 19,89% |
| 1,00 | 20,09% | 19,39% |

Tốt nhất **+0,20 điểm**, trong ngưỡng nhiễu. **MDD pruning làm tệ hơn ở mọi λ** — nó cắt
mất nhãn đúng khi hàng xóm đã sai.

**Phép thử quyết định** — so giá trị hàm mục tiêu tại nghiệm tìm được và tại gold:

```
λ=0,10:  GOLD điểm cao hơn ở  10/149 document, thấp hơn ở 139
λ=0,50:  GOLD điểm cao hơn ở  17/149 document, thấp hơn ở 132
```

**Ở 93% document, lời giải đúng có điểm THẤP HƠN lời giải sai.** Hàm mục tiêu trao điểm
cao cho câu trả lời sai. ILP tìm cực đại toàn cục của chính hàm đó, nên nó sẽ tìm *chính
xác hơn* cái cực đại sai. Không cần cài solver để biết.

Nguyên nhân: `BEFO,BEFO → BEFORE` có 3,1 triệu instance. Trọng số đủ mạnh để giúp cũng đủ
mạnh để kéo mọi thứ về BEFORE. Chuẩn hóa prior giải được ở pair-level vì mỗi cạnh một điểm;
ở joint, điểm cộng dồn theo **số tam giác**, và BEFORE luôn nhiều nhất.

### 9.5 Tổng kết ba giả thuyết

| Giả thuyết | Trạng thái |
|---|---|
| A — luật mong manh nội tại | **Bác bỏ** (27,66% ở nhiễu 12,46%) |
| B — calibration / inference cục bộ | **Bác bỏ** (soft đơn điệu giảm) |
| C — cần joint inference toàn cục | **Bác bỏ** (mục tiêu sai ở 93% doc) |
| **D — lỗi tương quan theo document** | **Được ủng hộ** (sd 13,5% vs 2,7%) |

### 9.6 Phát biểu cuối

> Cấu trúc sự kiện bậc cao chứa thông tin thời gian đáng kể (oracle gap 8,92 điểm) và chịu
> nhiễu **độc lập** tốt (27,66% ở mức nhiễu thực tế). Nhưng lỗi của classifier tương quan
> theo document ở mức gấp 5 lần độc lập, phá hủy toàn bộ tam giác trong một document cùng
> lúc. Ba cơ chế inference — hard, soft, joint với MDD pruning — đều không thu hồi được, và
> hàm mục tiêu joint trao điểm cao hơn cho lời giải sai ở 93% document.

---

# 10. SỬA LỖI HƯỚNG CẠNH — đo lại toàn bộ

**Mọi con số ở mục 1–9 đều sai.** Phần này thay thế chúng.

## 10.1 Lỗi

Cả 9 script bậc cao dựng đồ thị bằng:

```python
adj[a][b] = r ;  adj[b][a] = r        # SAI
```

Tức khẳng định "A BEFORE B" thì cũng "B BEFORE A". Chiều ngược phải mang **quan hệ
nghịch đảo**. `noise_aware.py` (code cũ trong repo) dùng đúng `converse`; chỉ script
mới của tôi sai.

Phát hiện nhờ kiểm tra tính nhất quán Allen của gold:

| | tam giác gold | vi phạm |
|---|---|---|
| hướng sai | 585.078 | 29.520 (**5,05%**) |
| **hướng đúng** | 585.078 | **0 (0,00%)** |

Vi phạm tập trung ở 3 chữ ký (`BEFO,BEFO→CONT`, `CONT,CONT→BEFO`, `BEFO,BEFO→SIMU`),
mỗi cái vi phạm **100%** — dấu hiệu lỗi hệ thống chứ không phải nhiễu dữ liệu.

**Gold nhất quán Allen tuyệt đối.** Mọi suy luận từ composition đều có cơ sở.

## 10.2 Số luật thay đổi

| | trước | **sau** |
|---|---|---|
| chữ ký bộ 3 | 34 | **58** |
| luật bộ 3 | 22 | **35** |
| luật bộ 4 | 123 | **327** |
| luật bộ 5 | 360 | **1.148** |

## 10.3 BÀI 1 — kết quả đo lại

| Hệ | trước | **sau** |
|---|---|---|
| pair-only 257 rule | 24,11% | 24,11% |
| **bộ 3 trên GOLD** | 33,14% | **38,30%** |
| bộ 3+4 trên GOLD | 36,53% | 37,83% |
| bộ 3+4+5 trên GOLD | 33,03% | 36,94% |
| chạy lặp 5 vòng | 18,24% | 19,41% |
| soft one-pass | 22,90% | 22,92% |

F1 từng nhãn của bộ 3 trên gold:

```
BEFO 98,1%   CONT 80,0%   SIMU 18,6%   OVER 33,1%   BEGI 0,0%   ENDS 0,0%
```

### Ba kết luận ĐỔI

**1. Bộ 3 một mình tốt nhất (38,30%).** Trước tôi kết luận "bộ 5 bão hòa"; thực ra bộ 4
và 5 **làm tệ đi** (38,30 → 37,83 → 36,94). Chúng là biến thể nhiễu của cùng tam giác,
không mang thông tin mới.

**2. Oracle gap lớn hơn nhiều:** 38,30 − 24,11 = **14,19 điểm** (trước báo 8,92).

**3. CONTAINS trên gold đạt 80,0%** (trước 55,9%), OVERLAP 33,1% (trước 26,8%).

### Kết luận KHÔNG đổi

Trên **dự đoán** vẫn thua pair-only: chạy lặp 19,41%, soft 22,92%, đều dưới 24,11%.

## 10.4 BÀI 2 — đo lại

| Chỉ số | closure | **bậc cao** | tỷ lệ |
|---|---|---|---|
| Xếp hạng | 20.818 | **1.527** | ít hơn 13,6× |
| P@k | 8,63% | **61,76%** | 7,2× |
| found_all | 25,88% | **27,96%** | 1,1× |
| repair@k | 31,84% | **93,53%** | 2,9× |
| **R_all** | 8,24% | **26,15%** | **3,2×** |

Thấp hơn con số cũ (31,99%) nhưng **vẫn gấp 3,2 lần** closure. Kết luận Bài 2 đứng vững.

## 10.5 Noise sweep đo lại — kết luận ĐỔI

| Nhiễu | macro-F1 | acc |
|---|---|---|
| 0% | 38,30% | 96,48% |
| 5% | 32,40% | 89,08% |
| 10% | 28,19% | 82,42% |
| **12,5%** (lỗi thật) | **25,81%** | 79,23% |
| 20% | 23,27% | 72,11% |
| 30% | 19,32% | 63,67% |

Với hướng đúng, đường cong **dốc hơn nhiều**: 38,30 → 25,81 khi nhiễu đạt 12,5%.

Trước đây tôi kết luận "luật bậc cao chịu nhiễu tốt (27,66%) nên vấn đề là inference".
Giờ 25,81% tại mức nhiễu thật, còn thực tế đo được 22,92% (soft) — **khoảng cách chỉ
còn 2,89 điểm** thay vì 4,76.

Nghĩa là **phần lớn tổn thất giải thích được bằng chính độ nhạy nhiễu**, không cần viện
đến lỗi tụm theo document. Giả thuyết A (mong manh nội tại) giờ **được ủng hộ**, không
phải bị bác bỏ.

## 10.6 Bảng trạng thái giả thuyết, cập nhật

| Giả thuyết | trước | **sau khi sửa** |
|---|---|---|
| A — luật mong manh với nhiễu hàng xóm | bác bỏ | **được ủng hộ** |
| B — calibration / inference cục bộ | bác bỏ | bác bỏ |
| C — cần joint inference toàn cục | bác bỏ | bác bỏ |
| D — lỗi tụm theo document | ủng hộ | góp phần, không phải chính |

## 10.7 Trần pair-level — LOẠI BỎ

Đo được "trần 99,26%" cho classifier pair-level. Nhưng **92,5% tổ đặc trưng chỉ chứa
1 cặp** (24.863 tổ / 27.063 cặp, median size 1). Đó là ghi nhớ, không phải trần thật.
Con số này không dùng được.

## 10.8 Phát biểu cuối, sau khi sửa

> Tam giác sự kiện chứa lượng thông tin thời gian rất lớn — bộ 3 trên đồ thị gold đạt
> 38,30% macro-F1 so với 24,11% của pair-level, oracle gap **14,19 điểm**, với CONTAINS
> đạt 80,0%. Nhưng thông tin đó **nhạy với nhiễu hàng xóm**: ở đúng mức lỗi của classifier
> (12,46%), luật tam giác chỉ còn 25,81%, và mọi cơ chế inference thực tế đều cho 19–23%.
> Bộ 4 và bộ 5 không thêm gì (37,83% và 36,94%, đều thấp hơn bộ 3).
>
> Ở Bài 2, nơi nhãn hàng xóm đã biết, cùng bộ luật cho R_all **26,15% so với 8,24%** của
> closure — gấp 3,2 lần, với repair@k 93,53%.

---

# 11. Thông tin mất ở đâu — feature hay inference?

## 11.1 Ablation bốn tầng nguồn ngữ cảnh

Protocol **đóng băng** cho mọi tầng: `candidates → drop self → CAP`. Sai khác 28,56 vs
38,30 ở mục 10 là do áp CAP *trước* khi lọc self; từ đây mọi số dùng cùng một protocol.

| Tầng | #luật | macro-F1 | acc | vs A' |
|---|---|---|---|---|
| A pair-only (257 rule) | 257 | 24,11% | 87,54% | — |
| A' pair-only (mine lại) | 85.982 | 20,61% | 89,27% | — |
| **B + cấu trúc (KHÔNG nhãn)** | 127.591 | **20,73%** | 88,27% | **+0,12** |
| C + hàng xóm dự đoán | 35 | 21,21% | 91,03% | +0,60 |
| **D + hàng xóm GOLD** | 35 | **28,56%** | 94,06% | **+7,96** |

Tầng B mô tả hàng xóm chung **không đọc một nhãn thời gian nào**: số event chung, loại của
chúng, vai trò chúng đảm nhiệm, có chia sẻ thực thể với hai đầu không, độ trải câu. Mọi
thứ đều hợp lệ lúc test — không cái nào là `target_edge`.

## 11.2 Kết luận: cấu trúc KG quan sát được đã cạn

**B chỉ hơn A' 0,12 điểm** dù thêm 41.609 luật. Nếu mất mát nằm ở inference thì B phải
vượt A' — cấu trúc có sẵn lúc test, không cần đoán gì. Nó không vượt.

> **Trong feature space hiện tại, không còn bằng chứng cho thấy structural information
> không chứa temporal labels có thêm signal đáng kể. Phần signal còn lại nằm trong
> relational temporal labels của graph, nhưng việc khai thác chúng đòi hỏi một
> representation/learning mechanism khác thay vì post-hoc structured inference trên nhãn
> dự đoán.**

*Phát biểu trước đó — "thông tin mất ở feature representation, không phải ở structured
inference" — quá mạnh.* Tầng B bác bỏ giả thuyết "chỉ cần khai thác thêm topology",
nhưng không chứng minh **mọi** structured inference đều vô ích. Vấn đề cụ thể hơn:
label-space context vừa nhiễu vừa nội sinh (endogenous).

Toàn bộ 7,96 điểm của tầng D đến từ **chính các nhãn thời gian** của cạnh kề, không phải
từ cấu trúc chứa chúng.

*Lưu ý so sánh:* A' (20,61%) thấp hơn A (24,11%) vì A' mine 85.982 luật thô không qua bốn
gate thống kê. So sánh hợp lệ là **B vs A'** — cùng miner, cùng cổng lọc.

## 11.3 Kiểm tra bốn khẳng định khác

| Khẳng định | Kết quả |
|---|---|
| Phân rã 88% nhiễu / 12% inference | **Bác bỏ** |
| Clustering gây thiệt hại | **Xác nhận** |
| LUPI có tiền đề | Có |
| Rò rỉ nhãn trong LUPI | **Rủi ro cao** |

### Phân rã 88% — bác bỏ

Phép cộng `14,19 = 12,49 + 2,89` ghép hai thí nghiệm khác thang: nhiễu mô phỏng trên gold
vs inference trên dự đoán. Đo lại với cùng một thang:

```
oracle gap        4,46 điểm
do nhiễu rải đều  1,80 điểm  (40%)
do phần còn lại   5,56 điểm  (125%)
```

Phần "còn lại" **lớn hơn cả gap** — không tách bạch được. Nên nói "cả nhiễu lẫn inference
đều góp phần" thay vì gán tỷ lệ.

### Clustering — xác nhận

Giữ nguyên số cạnh sai (3.373), chỉ đổi cách phân bố:

| Phân bố | #cạnh sai | macro-F1 |
|---|---|---|
| thật (tụm theo document) | 3.373 | **21,21%** |
| dồn nhân tạo vào ít document | 3.373 | 22,86% |

Kiểu tụm của classifier còn tệ hơn dồn nhân tạo.

### LUPI — có tiền đề nhưng rò rỉ quá cao

2.304 cạnh (8,5%) mà bộ 3 đúng còn pair-level sai, có đặc trưng pair-level phân biệt rõ:

```
83,28×  type_pair=(Competition, Preserving)
29,80×  HAS(anchor_roles, (Event, Event))
29,46×  HAS(roleset_a, Loser)
27,43×  HAS(roleset_a, Winner)
```

Toàn nhóm thể thao/thi đấu. **Nhưng** bộ 3 trên gold context đoán đúng **94,06%** số cạnh —
context gần như *chính là* nhãn, không phải privileged information theo nghĩa LUPI. Rủi ro
rò rỉ quá lớn để theo hướng này.

## 11.4 Hệ quả cho hướng đi

| Hướng | Trạng thái |
|---|---|
| Mine thêm rule bậc cao hơn | Bác bỏ — bộ 4/5 đã làm tệ đi |
| Joint inference / ILP | Bác bỏ 3 lần — mục tiêu sai ở 93% document |
| LUPI | Rủi ro rò rỉ 94% |
| Đặc trưng cấu trúc không nhãn | **Bác bỏ — chỉ +0,12đ** |
| **Text baseline / fusion** | **Hướng duy nhất còn cơ sở** |

Ablation tầng B vừa loại trừ khả năng "còn signal trong KG chưa khai thác". Nếu muốn vượt
25,60%, phải lấy thông tin từ **văn bản**, không phải từ đồ thị.

## 11.5 Phát biểu cuối cho Bài 1

> Với hợp đồng *input = cặp event + đặc trưng KG quan sát được*, 257 rule ở **25,60%** là
> gần trần của nguồn thông tin này. Không phải vì miner yếu — đo được bằng tầng B: thêm
> 41.609 luật mô tả toàn bộ hàng xóm chung chỉ cho **+0,12 điểm**.
>
> Cấu trúc bậc cao chứa **+7,96 điểm** thông tin, nhưng toàn bộ nằm ở *nhãn thời gian* của
> cạnh kề — thứ chính là đầu ra cần dự đoán. Nó là tín hiệu cho **auditing** (Bài 2,
> R_all gấp 3,2×), không phải cho **classification**.

---

# 12. Thang thông tin và đóng Bài 1

## 12.1 Bốn bậc, đo trên cùng protocol

| Nguồn ngữ cảnh | macro-F1 | chênh so với bậc dưới |
|---|---|---|
| Pair features | 20,61% | — |
| + cấu trúc KG không nhãn | 20,73% | **+0,12** |
| + nhãn thời gian **dự đoán** | 21,21% | **+0,48** |
| + nhãn thời gian **gold** | 28,56% | **+7,35** |

Đọc từng bậc:

- **+0,12** — không có bằng chứng rằng đặc trưng cấu trúc *không chứa nhãn* bổ sung đáng kể.
- **+0,48** — thêm nhãn hàng xóm dự đoán *có* cải thiện, nhưng context nhiễu nên không giải
  phóng được phần lớn signal.
- **+7,35** — khi hàng xóm là gold, nhãn thời gian ở context mang lượng thông tin rất lớn.

Nên **7,96 điểm không nên gọi là "structured inference thất bại"**. Signal tồn tại trong
*relational temporal labels*, nhưng không khai thác an toàn được bằng cách lấy nhãn dự đoán
làm context.

## 12.2 Câu hỏi nghiên cứu được đặt lại

Từ:

> Làm sao cải thiện rule mining?

thành:

> **How can temporal relational information from neighboring events be transferred to
> pairwise temporal classification without relying on gold temporal labels or propagating
> errors from predicted labels?**

## 12.3 Phát biểu để dùng trong paper

Không viết *"Bài 1 đã giải xong"*. Viết:

> Under the current KG feature space and rule-mining protocol, further exploitation of
> unlabeled graph structure yields negligible gains, establishing a practical information
> ceiling for the current representation.

> However, an oracle experiment reveals a substantial residual signal in neighboring
> temporal labels, motivating a shift from post-hoc rule mining toward text-grounded
> temporal representation learning.

**25,60% không phải trần tuyệt đối của Bài 1** — nó là trần của *nguồn thông tin + hypothesis
class + protocol hiện tại*. Text representation hoàn toàn có thể phá trần đó.

## 12.4 Ba hướng, trạng thái cuối

| Hướng | Trạng thái |
|---|---|
| **Text baseline / fusion** | **Việc tiếp theo** — cần cả ba nhánh `KG-only → text-only → KG+text` |
| LUPI | **Tạm đóng.** Gold context chứa 94,06% thông tin của Y — quá gần target. Giữ làm diagnostic upper bound, không làm contribution chính. |
| Joint inference / ILP | **Đóng ở phiên bản hiện tại.** Không tăng complexity để cứu một objective đã cho thấy không align với gold. Quay lại thì phải đổi representation/objective, không phải thêm solver. |

Vì sao cần cả ba nhánh chứ không chỉ `KG+text`: để phân biệt được text có signal độc lập,
KG có signal độc lập, và hai nguồn có bổ sung nhau hay không.

## 12.5 BÀI 1 — ĐÓNG

Cấu hình đóng băng: `rules/final/rules_rx_c70.json`, **257 rule, macro-F1 25,60%** trên valid.

Năm phát hiện:

| # | Phát hiện |
|---|---|
| 1 | Đặc trưng event quan sát được chứa signal mạnh cho nhãn thiểu số (F1 không-BEFORE 29,53% → 37,12%) |
| 2 | Cấu trúc đồ thị thời gian chứa thêm **+7,96 điểm** trên gold context |
| 3 | Khi context phải tự dự đoán, higher-order reasoning không chuyển hóa được oracle gain |
| 4 | Lỗi **không** iid — tụm theo document (sd 13,5% vs 2,7%) phá hỏng local higher-order reasoning |
| 5 | Cùng bộ luật đó rất hữu ích khi đồ thị đã tồn tại (Bài 2, R_all gấp 3,2×) |

Tài liệu: `report/BAI1_C2_FINAL.md` · `report/RULESET.md` · `report/THUAT_NGU.md` ·
ablation ở `experiments/ablations/` và `experiments/higher_order/`.

---

# 13. Event–TIMEX–Event: khoảng trống 31% có lấp được không?

Bài 1 đóng trên biểu diễn EV–EV, nhưng **31,2% quan hệ thời gian trong corpus chạm vào node
TIMEX** và chưa từng được mine. Đo trên 400 document train:

| Loại cạnh | Số lượng | Tỷ lệ |
|---|---|---|
| event–event | 111.114 | 64,1% |
| timex–event | 31.559 | 18,2% |
| event–timex | 22.459 | 13,0% |
| timex–timex | 8.236 | 4,8% |

**881.264 cặp event chia sẻ ít nhất một TIMEX**, trong đó 88.536 cặp chưa có nhãn trực tiếp.
94,2% cặp EV–EV có TIMEX chung — độ phủ rất rộng.

## 13.1 Chữ ký EV–TIMEX–EV có tín hiệu thật

Với mỗi cặp (A,B) và TIMEX T mà cả hai cùng nối tới, chữ ký là `(rel(A,T), rel(B,T))`:

| lift | k/n | doc | Chữ ký → nhãn |
|---|---|---|---|
| 120,7 | 18/339 | 4 | `E>CONTAINS, E>CONTAINS → BEGINS-ON` |
| 116,0 | 42/42 | 8 | `E>SIMULTANEOUS, E>SIMULTANEOUS → SIMULTANEOUS` |
| 54,9 | 38/116 | 7 | `T>OVERLAP, T>OVERLAP → OVERLAP` |
| 13,5 | 760/760 | 56 | `E>CONTAINS, T>CONTAINS → CONTAINS` |
| 13,4 | 2.075/2.080 | 61 | `E>CONTAINS, E>BEFORE → CONTAINS` |

Hai dòng cuối có 56 và 61 document — không phải chữ ký một bài viết.

## 13.2 Nhưng tín hiệu đó là ORACLE

Ba giả định về neo event–timex, cùng protocol:

| | macro-F1 | acc | #luật | chênh |
|---|---|---|---|---|
| A — chỉ 257 luật EV–EV | 25,60% | 87,87% | 257 | — |
| **B — neo GOLD** | **28,29%** | **89,71%** | 15 | **+2,69** |
| C — neo DỰ ĐOÁN | 25,60% | 87,87% | 7 | **+0,00** |
| D — chỉ CẤU TRÚC (có chung timex hay không) | 25,60% | 87,87% | 2 | **+0,00** |

**Toàn bộ mức tăng biến mất khi neo phải dự đoán.** Và điều này không phải vì classifier
EV–TIMEX yếu — nó đạt **79,84%** độ chính xác trên valid, cao hơn nhiều so với classifier
EV–EV (87,87% accuracy nhưng macro-F1 chỉ 25,60%).

Lý do: chữ ký cần **nhãn quan hệ chính xác** ở cả hai chân. Với 20% lỗi mỗi chân, xác suất
cả hai đúng chỉ còn `0,8² ≈ 64%` — đủ để phá hủy các chữ ký hiếm mang nhiều thông tin nhất.

Số luật sống sót nói rõ điều đó: **15 → 7 → 2**.

## 13.3 Cùng một câu chuyện với EV–EV bậc cao

| Nguồn ngữ cảnh | Oracle | Dự đoán |
|---|---|---|
| EV–EV tam giác | 38,30% | 22,42% |
| EV–TIMEX–EV | 28,29% | 25,60% |
| Cấu trúc không nhãn | — | +0,12 |

Ba nguồn ngữ cảnh khác nhau, cùng một kết luận: **thông tin nằm ở nhãn quan hệ của cạnh kề,
và nhãn đó chính là đầu ra cần dự đoán.**

## 13.4 Kết luận cho câu hỏi "Bài 1 đã đóng chưa?"

Câu hỏi đặt ra chính đáng: kết luận 25,60% có phải chỉ đúng cho biểu diễn EV–EV không?

**Đã kiểm tra: có mở rộng sang TIMEX cũng không thay đổi.** Khoảng trống 31,2% là thật, chữ
ký EV–TIMEX–EV có lift 120× là thật, nhưng chúng không chuyển hóa được thành gain vì cùng
một rào cản đã chặn EV–EV bậc cao.

Phát biểu chính xác:

> Bài 1 đã đóng đối với **mọi biểu diễn chỉ dùng cấu trúc đồ thị thời gian**, bao gồm cả
> EV–EV bậc cao lẫn EV–TIMEX-mediated. Ba nguồn ngữ cảnh độc lập đều cho oracle gain lớn
> (+7,96 / +2,69) mà không chuyển hóa được (+0,00 / +0,12) khi ngữ cảnh phải tự dự đoán.

## 13.5 Nhưng TIMEX vẫn quan trọng — ở chỗ khác

Benchmark `results/` (fake conflict data) là bài toán **event-level**: mỗi event có
`timex_raw` và `time_start`, conflict được inject vào chính mốc thời gian.

| Loại conflict | Cơ chế |
|---|---|
| ANCHOR_CONFLICT | dịch mốc (`17/10/1860` → `1860-12-08`) |
| ORDERING_CONFLICT | hoán đổi thứ tự cặp |
| GRANULARITY_CONFLICT | làm thô (`23/9/1961` → `1961-01-01`) |
| IMPLICIT_ORDERING | đổi từ nối (`when` → `after`) |

Ở đó **cả `timex_raw` lẫn `time_start` đều có sẵn** — so hai vế là phát hiện được, không cần
đoán nhãn quan hệ nào. Đây mới là chỗ công việc TIMEX có giá trị, và nó thuộc Bài 2 chứ
không phải Bài 1.

---

# 14. TIMEX-aware context: bốn track, không track nào nhúc nhích

Phép thử trước (`shared_timex = True/False`) bị phê bình đúng — collapse cả vùng lân cận
TIMEX vào một boolean là biểu diễn quá nghèo để kết luận. Làm lại đầy đủ.

## 14.1 Bốn không gian đặc trưng, cùng miner cùng cổng lọc

| Track | #luật | macro-F1 | acc | chênh |
|---|---|---|---|---|
| A — event + entity (hiện tại) | 100.922 | **22,64%** | 85,93% | — |
| T1 — + TIMEX nội tại | 127.502 | 22,60% | 85,52% | **−0,04** |
| T2 — + TIMEX phân loại theo vị trí | 149.687 | 22,62% | 85,31% | **−0,02** |
| C — + giá trị lịch tuyệt đối *(trần)* | 154.065 | 22,62% | 85,31% | **−0,02** |

**Cả bốn nằm trong 0,04 điểm của nhau.** F1 từng nhãn gần như y hệt:

```
A :  BEFO 92,2  CONT 40,3  SIMU 0,0  OVER 3,3
T1:  BEFO 92,0  CONT 40,3  SIMU 0,0  OVER 3,3
T2:  BEFO 91,8  CONT 40,6  SIMU 0,0  OVER 3,3
C :  BEFO 91,8  CONT 40,6  SIMU 0,0  OVER 3,3
```

Thêm **53.143 luật** mô tả TIMEX mà không dịch chuyển gì.

### Đặc trưng đã thử (chỉ đọc thuộc tính node, không đọc quan hệ nào)

| Tầng | Đặc trưng |
|---|---|
| T1 | `timex_type` (DATE/TIME/DURATION), `anchorable`, số lượng, khoảng cách câu tới mỗi đầu, cùng câu hay không, vị trí trước/giữa/sau cặp |
| T2 | + loại TIMEX **ở từng vị trí** (DATE ở giữa A-B? DURATION trước A?), loại của TIMEX gần nhất mỗi đầu |
| C | + so sánh giá trị lịch của TIMEX gần nhất hai đầu |

## 14.2 Vì sao track C (giá trị lịch) cũng không giúp

C giống T2 **đúng từng chữ số** — đáng ngờ, nên đã kiểm tra. Đặc trưng `cal` không suy biến:
nó có giá trị trên **29,2%** số cặp (lt 14,1%, eq 10,6%, gt 4,5%).

Nhưng sức mạnh dự báo gần như bằng không:

| `cal` | n | BEFORE | CONTAINS |
|---|---|---|---|
| lt | 5.186 | 92,9% | 6,7% |
| gt | 1.647 | 90,2% | 8,2% |
| eq | 3.899 | 83,5% | 11,4% |
| unk | 26.027 | 90,7% | 8,3% |
| *base rate* | | *90,2%* | *8,4%* |

`cal=lt` cho BEFORE **92,9%** so với base **90,2%** — chỉ hơn **2,7 điểm**. `cal=gt` cho đúng
bằng base rate.

### Tương phản với date bridge

Date bridge đạt **100%** trên 12.946 suy luận. Khác biệt nằm ở một chỗ:

| | Cách xác định TIMEX nào neo event nào |
|---|---|
| date bridge | quan hệ `timex --CONTAINS--> event` — **là target edge** |
| track C | gần nhau trong văn bản (≤1 câu) — **hợp lệ nhưng sai** |

Một TIMEX đứng gần event trong văn bản thường **không phải** mốc neo của event đó. Đây chính
là hiện tượng đã thấy ở *Battle of Malacca (1641)*: event `took` nằm cạnh `1606` nhưng `1606`
là bối cảnh nền.

**Toàn bộ sức mạnh của date bridge đến từ việc biết đúng neo — và neo đó là target edge.**

## 14.3 Kết luận

Câu hỏi *"mine rule chưa hề để timex vào?"* có câu trả lời đầy đủ:

| Nguồn thông tin TIMEX | Hợp lệ? | Kết quả |
|---|---|---|
| Quan hệ event–timex (target edge) | Không | oracle +2,69 |
| Quan hệ đó, dự đoán trước | Có | +0,00 |
| Thuộc tính node: type, anchorable | Có | **−0,04** |
| Hình học vị trí, phân loại theo vị trí | Có | **−0,02** |
| Giá trị lịch qua vị trí gần | Có | **−0,02** |

Năm cách đưa TIMEX vào Bài 1, không cách nào cho gain. Phát biểu chặt:

> **TIMEX node-level và contextual information, khi không dùng temporal edge labels, không
> cung cấp thêm predictive signal đo được cho việc phân loại quan hệ EV–EV. Toàn bộ giá trị
> của TIMEX trong bài toán này nằm ở quan hệ neo event–timex, mà quan hệ đó chính là một
> phần của đầu ra cần dự đoán.**

Điều này khớp với TimeML: *anchoring events to temporal expressions* và *ordering events with
one another* là hai nguồn thông tin khác nhau. Neo không suy ra được từ vị trí văn bản.

---

# 15. Motif dị thể event–timex bậc 3 và bậc 4 — kiểm chứng có hệ thống

Các kết luận "đồ thị đã cạn" trước đây dựa trên ba họ motif: tam giác A–E–B, A–T–B và bộ 4
dạng sao chỉ gồm event. Hai lỗ hổng còn lại:

1. **Motif dạng đường A–X–Y–B chưa từng được thử**, cho bất kỳ loại node nào. A–T₁–T₂–B chính
   là date bridge tổng quát, chưa bao giờ được dùng làm đặc trưng classifier.
2. **Mọi lần "thực tế" trước đều mine trên nhãn gold rồi áp lên nhãn dự đoán** — lệch phân
   phối train/test. Mine trực tiếp trên nhãn dự đoán chưa từng được thử.

## 15.1 Thiết kế

| Họ | Hình dạng | | Chế độ | Ý nghĩa |
|---|---|---|---|---|
| 3E | A–E–B | | gold | nhãn ngữ cảnh gold — oracle |
| 3T | A–T–B | | pg | mine gold, áp dự đoán — cách cũ |
| 4EE | A–E–E–B | | **pp** | **mine dự đoán, áp dự đoán — mới** |
| 4ET | A–E–T–B | | st | chỉ cấu trúc, không nhãn |
| 4TE | A–T–E–B | | | |
| 4TT | A–T₁–T₂–B | | | |

Nhãn ngữ cảnh dự đoán: EV–EV từ 257 luật (lỗi 12,13% trên valid), EV–TX từ classifier
273 luật (đúng 79,84%), TX–TX từ **so sánh lịch** của hai TIMEX (thuộc tính node, hợp lệ;
đúng 95,8% khi quyết định được, UNK 65,1%).

Độ phủ trên valid: mọi họ đều trên 90% số cặp (3E 99,7%, 4TT 90,3%).

## 15.2 Hai lỗi phương pháp tìm được giữa chừng — cả hai đều cho kết luận sai

**Lỗi 1: chỉ lấy nhãn đa số của chữ ký.** Lần chạy đầu cho toàn bộ cột `pp` đúng **+0,00**
đến từng chữ số. Kiểm tra: **163/163 luật `pp` đều là BEFORE**. Luật BEFORE có điểm
`wlb/0,91 ≤ 1,1`, không bao giờ vượt τ=5, nên không đổi được dự đoán nào. `+0,00` là hiện vật
của cổng lọc — đúng cái cổng `wlb ≥ ngưỡng tuyệt đối` đã giết nhãn hiếm ở Bài 1. Sửa: xét mọi
nhãn của mỗi chữ ký, lọc theo độ giàu so với prior, xếp hạng riêng từng nhãn.

**Lỗi 2: cổng `lift ≥ 2` quá yếu cho nhãn cực hiếm.** BEGINS-ON có prior 0,044%, nên luật
precision 0,09% đã qua cổng — rồi được điểm `cwlb/0,00044` rất lớn và ghi đè mọi thứ. Ở 4TT,
luật BEGINS-ON bắn **22.640 lần với precision 0,1%**, lật 20.485 dự đoán, đúng 9. Đó là thứ
kéo 4TE/4TT xuống −2,56/−1,77. Sửa: cổng chặt (mục 15.4).

## 15.3 Chẩn đoán: luật motif trên nhãn dự đoán không chính xác hơn classifier

Đo độc lập với τ — khi luật bắn nhãn r, gold có bằng r không:

| Nhãn | 257 luật đoán nhãn đó | luật motif `pp` khi bắn | luật motif gold khi bắn |
|---|---|---|---|
| CONTAINS | 39,79% | 20–47% | 50–99% |
| SIMULTANEOUS | 15,92% | 3–8% | 5–80% |
| OVERLAP | 27,50% | 0,3–1,1% | 1–90% |

Trên nhãn dự đoán, luật motif **không đáng tin hơn chính classifier sinh ra nhãn ngữ cảnh của
nó**. Mọi họ `pp` lật đúng dưới 25% số dự đoán nó đổi; τ chọn lại trên confirmation giữ
nguyên 5.

## 15.4 Kết quả cuối — cổng chặt

Luật chỉ được giữ nếu Wilson bound trên confirmation **vượt precision của 257 luật ở cùng
nhãn** (đo trên confirmation, in-sample nên cổng này thận trọng): một luật kém tin cậy hơn
classifier mà nó định ghi đè thì chỉ có thể gây hại. Chỉ xét CONTAINS/SIMULTANEOUS/OVERLAP. τ
chọn trên confirmation, valid mở một lần. Base 257 luật: **25,60%**.

| Họ | gold (oracle) | | **dự đoán (thực tế)** | |
|---|---|---|---|---|
| | macro-F1 | chênh | macro-F1 | chênh |
| 3E | 41,19% | +15,59 | 25,86% | **+0,26** |
| 3T | 31,04% | +5,44 | 25,77% | +0,17 |
| 4EE | 29,07% | +3,47 | 25,77% | +0,17 |
| 4ET | 30,64% | +5,04 | — | **0 luật qua cổng** |
| 4TE | 28,83% | +3,23 | — | **0 luật qua cổng** |
| 4TT | 30,24% | +4,64 | — | **0 luật qua cổng** |
| ALL | **41,27%** | **+15,67** | 25,86% | +0,26 |

## 15.5 Kết luận

**Oracle: tín hiệu rất mạnh, mạnh hơn mọi lần đo trước.** Gộp mọi họ, gold đạt **41,27%
(+15,67)**. Luật gold bắn đúng tới 99,1% (CONTAINS), 90,4% (OVERLAP). Mọi họ đường có TIMEX đều
mang +3 đến +5 điểm khi nhãn ngữ cảnh là thật.

**Thực tế: tối đa +0,26, và không họ nào có TIMEX đóng góp.** 4ET, 4TE, 4TT không sinh nổi một
luật nào chính xác hơn classifier. Toàn bộ +0,26 đến từ 8 luật CONTAINS trên tam giác EV–EV.

**Nguyên nhân: tính vòng tròn.** Nhãn ngữ cảnh dự đoán đến từ chính classifier (EV–EV), từ
classifier yếu hơn (EV–TX 80%), hoặc không quyết định được (TX–TX UNK 65%). Một luật đọc nhãn
ngữ cảnh không thể đáng tin hơn classifier sinh ra nhãn đó — và đo được đúng như vậy ở mục 15.3.

Mine trực tiếp trên nhãn dự đoán (`pp`) **ít hại hơn** mine trên gold rồi áp (`pg`: tới −5,55)
— lệch phân phối là thật — nhưng không biến nhiễu thành tín hiệu.

## 15.6 Chưa kiểm chứng

**Bộ 5 (đường A–X–Y–Z–B).** Chưa chạy. Chi phí liệt kê tăng theo `deg³` (~8.000 đường mỗi cặp,
~1,8 tỷ phép thử trên train+valid). Kỳ vọng rỗng vì mọi họ bậc 4 có TIMEX đã cho 0 luật ở chế
độ thực tế, và thêm một chân dự đoán chỉ làm tín hiệu yếu thêm — nhưng đó là dự đoán, chưa
phải kiểm chứng.

---

# 16. Metapath entity–vai trò — lớp hợp lệ cuối cùng

Mọi motif trên nhãn thời gian đều thất bại ở chế độ thực tế vì tính vòng tròn (mục 15.5). Còn
một lớp tránh được rào cản đó: đường đi qua **cạnh event–entity** (`input_edges`, quan sát được,
không phải đầu ra). Vai trò làm cho đường có nghĩa thay vì liệt kê vét cạn.

| Họ | Hình dạng | Ví dụ |
|---|---|---|
| M2 | `A –r1→ X ←r2– B` | cùng một người làm hai việc |
| M4 | `A –r1→ X ←r2– C –r3→ Y ←r4– B` | chuỗi qua event thứ ba C |
| M4p | M4 + vị trí của C so với A, B trong văn bản (giữa / ngoài) | |

Chữ ký gồm vai trò và `ent_type`. Cùng protocol: mine trên DISCOVERY, xác nhận trên
CONFIRMATION, τ chọn trên CONFIRMATION, valid mở một lần.

| | Kết quả |
|---|---|
| Độ phủ trên valid | M2 17,6%, M4 18,3% số cặp |
| Cổng chặt (phải hơn precision classifier) | **0 luật** qua cổng ở mọi họ |
| Cổng lift (lift ≥ 2, wlb/prior ≥ 1,5) | 13 luật, macro-F1 25,55% (**−0,05**) |
| Độ chính xác khi luật bắn | CONTAINS ~23% (classifier 39,8%), SIMULTANEOUS 3% (classifier 15,9%) |

Hai nguyên nhân: chỉ ~18% cặp có chung entity, và khi có, chữ ký vai trò **kém tin cậy hơn**
classifier đang có. Không vòng tròn, nhưng cũng không đủ thông tin.

Script: `experiments/higher_order/entpath.py`.

## 16.1 Tổng kết Bài 1 — mọi biểu diễn đồ thị đã thử

| Biểu diễn | Hợp lệ? | Oracle | Thực tế |
|---|---|---|---|
| EV–EV tam giác (mục 13.3) | nhãn dự đoán | 38,30% | 22,42% (mine gold áp dự đoán); +0,26 với cổng chặt (mục 15.4) |
| EV–TIMEX–EV (bộ 3) | nhãn dự đoán | +2,69 | +0,00 |
| Đường bộ 4 EE/ET/TE/TT | nhãn dự đoán | +3,2 đến +5,0 mỗi họ | 0 luật (ET/TE/TT), +0,17 (EE) |
| Gộp mọi họ motif | nhãn dự đoán | **+15,67** | **+0,26** |
| TIMEX node-level (T1/T2/C) | có | — | −0,02 đến −0,04 |
| Metapath entity–vai trò | có | — | 0 luật / −0,05 |
| Bộ 5 A–X–Y–Z–B | nhãn dự đoán | chưa chạy | chưa chạy |

> Bài 1 đóng ở **25,60%** cho mọi biểu diễn chỉ dùng đồ thị. Tín hiệu bậc cao là thật nhưng
> nằm trong nhãn cạnh kề — chính là đầu ra. Nó dùng được ở Bài 2, nơi các cạnh kề đã tồn tại.

---

# 17. Tín hiệu ngữ nghĩa ngoài ngôn ngữ luật (24/09/2026)

257 luật đóng băng đều là AND của đúng 2 điều kiện trên ~30 thuộc tính bề mặt (loại event, vị
trí câu, tập vai trò, loại entity). Bốn nguồn ngữ nghĩa chưa từng có trong ngôn ngữ luật:

| Track | Nội dung | Hợp lệ? |
|---|---|---|
| LEX | từ trigger (lemma thô: chữ thường + tách hậu tố; máy không có nltk/spacy) | có |
| DUR | từ điển "event bao chứa": mỗi lemma (hoặc loại) nằm ở phía chứa / bị chứa của CONTAINS bao nhiêu lần, học từ gold DISCOVERY | có |
| GRP | nhóm loại event theo khung vai trò (k-means k=12, 30 trên hồ sơ vai trò + loại entity). Phân cấp MAVEN không có trên máy; đây là thay thế gần nhất | có |
| CONN | từ nối trong câu: giữa hai trigger, 3 token trước mỗi trigger, đầu câu sau | có |
| WEAK | SUBEVENT / CAUSE / PRECONDITION gold của MAVEN-ERE | **gold — chỉ là trần** |

Luật bậc 1 (một điều kiện mới) hoặc bậc 2 (điều kiện mới AND điều kiện bất kỳ), cho CONTAINS /
SIMULTANEOUS / OVERLAP, cộng vào 257 luật theo max-norm. Mine trên DISCOVERY (1.715 doc train),
xác nhận trên CONFIRMATION (1.193 doc), τ chọn trên CONFIRMATION, valid mở một lần.

## 17.1 Từng track

| Track | Cổng chặt: #luật | macro-F1 | chênh | F1 CONTAINS | Cổng lift: macro-F1 |
|---|---|---|---|---|---|
| base 257 luật | — | 25,60% | — | 40,61% | — |
| LEX | 922 | 26,06% | **+0,46** | 43,8% | 25,49% (−0,11) |
| DUR | 174 | 25,99% | **+0,39** | 44,4% | 21,19% (−4,41) |
| GRP | 110 | 25,59% | −0,01 | 41,1% | 22,11% (−3,48) |
| CONN | 71 | 25,60% | 0,00 | 40,7% | 24,78% (−0,82) |
| Gộp thô cả bốn | 1.488 | 25,61% | +0,01 | 43,1% | 21,37% (−4,23) |
| *WEAK (gold, trần)* | 303 | *26,78%* | *+1,18* | *47,3%* | *26,69%* |

- **Lần đầu tiên có gain thật kể từ khi đóng Bài 1**, từ LEX và DUR. Luật mạnh nhất có nghĩa rõ:
  `trigger_a = "wars"` → CONTAINS (cwlb 0,93), `"during"` giữa hai trigger + `Military_operation`
  → CONTAINS (0,77).
- **Cổng chặt không giữ được luật SIMULTANEOUS/OVERLAP nào** ở bất kỳ track nào. Cổng lift có
  luật nhãn hiếm nhưng precision 3–9%, kéo macro-F1 xuống — cùng hiện vật cổng đã gặp ở mục 15.
- **Gộp thô mất hết gain:** precision CONTAINS tụt 39,8% → 32,7% vì quá nhiều luật cận ngưỡng
  cùng bắn.

## 17.2 Chọn tổ hợp trên CONFIRMATION

Chọn (tập track, δ, τ) trên CONFIRMATION; δ buộc cwlb vượt precision classifier ít nhất δ.

**Được chọn: LEX, δ = 0,05, τ = 5 → valid macro-F1 26,15% (+0,55)**, 719 luật.

| Nhãn | P | R | F1 | base F1 |
|---|---|---|---|---|
| BEFORE | 94,07% | 92,53% | 93,29% | 93,50% |
| CONTAINS | 39,93% | 49,26% | **44,11%** | 40,61% |
| SIMULTANEOUS | 15,92% | 15,82% | 15,87% | 15,87% |
| OVERLAP | 27,50% | 1,93% | 3,61% | 3,61% |
| BEGINS-ON / ENDS-ON | 0% | 0% | 0% | 0% |

Đối chiếu trên valid, không dùng để chọn: LEX+DUR 26,24% (+0,64), LEX+DUR+CONN 26,17%, cả bốn
26,08%.

## 17.3 Kết luận

1. **Ngữ nghĩa từ vựng giúp CONTAINS: F1 +3,5 điểm** (40,61% → 44,11%), recall 41,5% → 49,3%
   với precision giữ nguyên. Macro-F1 25,60% → 26,15%.
2. **Không track nào giúp SIMULTANEOUS/OVERLAP.** Nhãn hiếm vẫn là giới hạn chính.
3. **Kết luận "Bài 1 đóng ở 25,60%" cần sửa** thành: đóng cho biểu diễn đồ thị + thuộc tính bề
   mặt; từ vựng trigger thêm được +0,55.
4. SUBEVENT/CAUSE gold chỉ cho +1,18 — kể cả khi có quan hệ gold của lớp khác, gain vẫn nhỏ.

Script: `experiments/higher_order/semantic_tracks.py`, `semantic_combo.py`.
Log: `experiments/logs/semantic_tracks.log`, `semantic_combo.log`.

---

# 18. Bài 1 trên cả bốn loại cạnh, và đồ thị hợp nhất (24/09/2026)

## 18.1 Classifier cho ba loại cạnh TIMEX

Trước đây chỉ EV–EV có classifier thật. Classifier EV–TIMEX dùng làm ngữ cảnh trong nghiên cứu
motif chỉ đúng 79,84%, trong khi luôn đoán BEFORE đã đúng 77,4% — tầng TIMEX dự đoán gần như
không mang thông tin. Dựng lại bằng cùng cơ chế: đặc trưng phía sự kiện (loại, trigger, vị
trí), phía TIMEX (loại, độ mịn lịch, từ nội dung), hình học (cùng câu, khoảng cách, thứ tự,
TIMEX gần nhất, giới từ ngay trước TIMEX), và so sánh lịch cho TIMEX–TIMEX. Mô hình riêng cho
từng chiều; mỗi nhãn một ngưỡng precision chọn trên CONFIRMATION-2 (ngưỡng chuẩn hoá theo prior
dùng chung không làm được khi prior một nhãn là 0,3% và nhãn khác 30%).

| Loại cạnh (valid) | Số cạnh | Luôn BEFORE | Luật: macro-F1 | Accuracy | F1 nổi bật |
|---|---|---|---|---|---|
| EV–EV | 109.929 | 15,78% | 26,15% | 87,59% | CONTAINS 44,1 |
| EV→TIMEX | 26.573 | 15,91% | **29,74%** | 89,44% | CONTAINS 39,2 · SIMU 23,0 · OVER 21,6 |
| TIMEX→EV | 39.935 | 13,51% | **24,29%** | 74,09% (baseline 68,13%) | CONTAINS 59,9 |
| TIMEX–TIMEX | 12.487 | 14,73% (chỉ so lịch 29,94%) | **32,98%** | 84,35% | CONTAINS 46,3 · SIMU 60,4 |
| **Gộp** | **188.924** | 15,30% | **29,87%** | 84,78% | CONTAINS 51,4 · SIMU 25,2 · OVER 11,2 |

Luật có nghĩa: `"between" + TIMEX cách sự kiện ≤ 8 token` → OVERLAP; `"of"/"during" + "world"`
(… World War) → TIMEX CONTAINS sự kiện (0,97); hai ngày bằng nhau → SIMULTANEOUS (0,77).

## 18.2 Đồ thị hợp nhất — pattern trên mọi sự kiện, mọi TIMEX, mọi cạnh

Mỗi document một đồ thị gồm mọi node và mọi cạnh thời gian với nhãn của giai đoạn 1. Với mỗi
cạnh (a, b) thuộc bất kỳ loại nào: đường a–x–b và a–x–y–b qua sự kiện hoặc TIMEX; luật khoá theo
(chữ ký đường đi, nhãn hiện tại). Mine trên CONFIRMATION-2 (bỏ 400 document đầu, nơi 257 luật
được mine), chọn margin trên CONFIRMATION-1, valid mở một lần.

| Cấu hình | macro-F1 gộp | EV–EV | EV→TX | TX→EV | TX–TX |
|---|---|---|---|---|---|
| Giai đoạn 1 | 29,87% | 26,15% | 29,74% | 24,29% | 32,98% |
| Đồ thị hợp nhất, ngữ cảnh dự đoán (chọn trên conf1) | 29,87% (+0,00) | — | — | — | — |
| Đồ thị hợp nhất, cross-fit trên valid | 30,12% (+0,25) | 26,47% | 29,66% | 23,98% | 32,98% |
| *Trần: ngữ cảnh gold* | *37,65% (+7,78)* | *33,61%* | *30,74%* | *36,38%* | *41,41%* |

Đã kiểm tra con số +0,00 trước khi tin: chất lượng giai đoạn 1 trên tập mine (29,77%) gần bằng
valid (29,87%); ở mọi margin, tập chọn và valid đi cùng chiều (tốt nhất +0,14 / +0,18 ở margin
0,7); cross-fit trên valid +0,25.

## 18.3 Kết luận

1. **Bài 1 đầy đủ bốn loại cạnh: macro-F1 29,87%** trên 188.924 cạnh (luôn BEFORE: 15,30%).
2. **Giả thuyết "thiếu thông tin EV–TIMEX–EV" đúng một nửa.** Thông tin có trong đồ thị hợp nhất:
   nếu các cạnh xung quanh đúng, macro-F1 lên 37,65% và accuracy 94,92%. Nhưng khi các cạnh đó
   phải tự dự đoán, pattern chỉ thêm tối đa +0,25 — cùng rào cản vòng tròn như mục 15.
3. Tín hiệu đó dùng được ở Bài 2, nơi phần lớn các cạnh xung quanh là quan sát.

Script: `bai1_all_edges.py`, `unified_graph.py`, `unified_diag.py`. Dự đoán mọi loại cạnh:
`src/artifacts/pred_all_edges.json`.

---

# 19. Đồ thị theo tầng: pattern từng tầng → bộ pattern chung → luật liên tầng (24/09/2026)

Mọi thông tin quan sát được về một cạnh được xếp vào một tầng (tầng nhãn dự đoán bị loại vì
vòng tròn): **ONT** (loại sự kiện, cặp loại, loại TIMEX), **ARG** (vai, loại entity, neo chung),
**DISC** (vị trí, khoảng cách, thứ tự, số lần nhắc, từ nối, giới từ), **LEX** (trigger, từ điển
bao chứa, từ trong TIMEX), **TIME** (TIMEX gần mỗi sự kiện, so sánh lịch).

- **Stage A:** mine từng tầng (độ sâu ≤ 2), xác nhận trên CONFIRMATION-1, giữ 150 pattern tốt
  nhất mỗi nhãn mỗi tầng.
- **Stage B:** gộp thành một bộ pattern; luật = hội 2–3 pattern từ **các tầng khác nhau**, cùng
  cổng, xác nhận trên CONFIRMATION-1.
- **Stage C:** luật ghi đè nhãn giai đoạn 1 khi vượt ngưỡng precision riêng từng nhãn (chọn trên
  CONFIRMATION-2); valid mở một lần. Bỏ 400 document train đầu.

## 19.1 Kết quả (v1)

| Loại cạnh | Giai đoạn 1 | + pattern từng tầng | **+ luật liên tầng** | Nhãn được lợi |
|---|---|---|---|---|
| EV–EV | 26,15% | 26,16% | **26,50% (+0,36)** | SIMU 15,9 → 17,4 · CONT 44,1 → 44,8 |
| EV→TIMEX | 29,74% | 30,12% | **30,17% (+0,43)** | OVER 21,6 → 23,5 |
| TIMEX→EV | 24,29% | 26,22% | **26,22% (+1,93)** | OVER 4,4 → 15,8 |
| TIMEX–TIMEX | 32,98% | 33,63% | **34,65% (+1,67)** | CONT 46,3 → 55,9 |
| **Gộp 188.924 cạnh** | **29,87%** | | **30,83% (+0,96)** | CONT 51,4 → 52,3 · SIMU 25,2 → 25,9 · OVER 11,2 → 15,3 |

Số lượng: EV–EV 1.596 pattern (ONT 358, ARG 600, DISC 476, LEX 261, TIME 152) và 7.690 luật liên
tầng. Luật liên tầng tiêu biểu: `ARG: chung Location & LEX: trigger "hurricane", lemma bao chứa cao &
TIME: TIMEX gần là năm` → CONTAINS (0,91); `DISC: "during", giữa bài & LEX: "world"` → TIMEX CONTAINS
sự kiện (0,95); `DISC: thứ tự ngược & TIME: hai ngày bằng nhau` → SIMULTANEOUS (0,76).

**Ghép liên tầng mới là phần tạo gain:** ở EV–EV, pattern từng tầng chỉ +0,01, thêm luật liên tầng
thành +0,36; ở TIMEX–TIMEX +0,65 → +1,67.

## 19.2 Bản v2 theo FORMAL.md (Event-Centric PaTeCon), chỉ EV–EV

| Ý từ FORMAL.md | Cài đặt |
|---|---|
| `derived_from` (§11.7) | mỗi tầng khai báo nguồn gốc; cấm thuộc tính dẫn xuất từ cạnh đích |
| tập anchor + hull, vị từ ba trị (§4.1, §8.4) | tầng HULL: mốc ngày trong câu của sự kiện và câu trước (chỉ từ văn bản), hull, so sánh hull hai phía a_before/b_before/a_contains/b_contains/overlap/equal/unk |
| lớp sự kiện kéo dài (§8.4) | loại có anchor văn bản trải ≥ 2 năm, học trên DISCOVERY: 11 loại |
| refinement trong dàn view (§3.1) | chỉ mở rộng pattern chưa quyết định, bằng pattern tầng khác, giữ khi wlb tăng ≥ 0,05, tối đa 3 tầng |
| BH-FDR (§10.3) | kiểm định nhị thức trên CONFIRMATION-1, q = 0,05: giữ 695/759 |
| `is_enriched` (§11.8) | báo tách cặp giàu thông tin (89.743) và nghèo (20.186) |

| EV–EV | macro-F1 | cặp giàu | cặp nghèo |
|---|---|---|---|
| Giai đoạn 1 | 26,15% | 26,34% | 23,94% |
| + pattern từng tầng (có HULL) | 26,16% | 26,36% | 23,84% |
| + refinement + BH-FDR | 26,24% (+0,09) | 26,42% | 24,04% |
| *v1: + luật liên tầng vét cạn* | *26,50% (+0,36)* | | |

Tầng HULL chỉ sinh 27 pattern. Phân bố trên valid cho thấy tín hiệu có nhưng yếu: `a_before` →
BEFORE 98,1% (nền 90,1%); `a_contains` → CONTAINS 16,2% (nền 8,6%); `equal` → SIMULTANEOUS 4,5%
(nền 0,8%). Khớp FORMAL.md §8.2a: mốc thời gian gán từ văn bản thiếu chính xác nên hull lấy từ
văn bản chỉ mang tín hiệu mờ.

## 19.3 Kết luận

1. **Thiết kế theo tầng + luật liên tầng là cách đầu tiên cho gain ở cả bốn loại cạnh: gộp
   29,87% → 30,83%**, rõ nhất ở nhãn hiếm (OVERLAP 11,2 → 15,3).
2. **Refinement kiểu PaTeCon + BH-FDR kém hơn liệt kê liên tầng vét cạn** (+0,09 so với +0,36 ở
   EV–EV): khi tập pattern mỗi tầng đã nhỏ, vét cạn bộ 2–3 là khả thi và tìm được nhiều luật hơn.
3. **Hull mốc thời gian từ văn bản chỉ là tín hiệu mờ**, vì gán mốc từ văn bản không chính xác.
   Đây đúng là chỗ chặn FORMAL.md §8.2a đã chỉ ra.

Script: `layered_rules.py` (v1, bốn loại cạnh), `layered_v2.py` (v2, EV–EV).
