# TempEKG — Spec kiểm chứng framework
**Ngày 30/08/2026 · Nhựt (Phase 2) · 43 ngày đến COLING 2027**

---

## 0. Mục đích của tài liệu này

Đây **không phải** spec xây dựng. Đây là spec **kiểm chứng**: trước khi bỏ 40 ngày xây
graph + mining pipeline, phải trả lời được ba câu hỏi sinh tử. Nếu câu trả lời là "không",
framework phải đổi *trước*, không phải đổi ở ngày 30.

| # | Câu hỏi sinh tử | Thí nghiệm | Trạng thái |
|---|---|---|---|
| Q1 | Giao thức đánh giá đề xuất (edge-level holdout) có đo được gì không? | EXP1 | ✅ **Đã trả lời — KHÔNG** |
| Q2 | Pattern mine được có sức dự đoán vượt baseline tầm thường không? | EXP2 | ⚠️ **Đã trả lời — RẤT YẾU** |
| Q3 | Ở chế độ đúng của PaTeCon (conf ≥ 0.9, bỏ NONE), pattern có "đúng" và giữ được trên held-out không? | EXP3 | 🔄 đang chạy |

---

## 1. Bối cảnh — vì sao phải kiểm chứng trước

Ba giả định nền của PaTeCon đều **sai** trên MAVEN merged (số đã đo):

| Giả định PaTeCon | Thực tế | Hệ quả |
|---|---|---|
| Entity lặp lại toàn cục | 0/68,348 entity vượt document | entity-level confidence suy biến → phải mine ở type level |
| Mọi statement có interval | 44.9% event có anchor chặt; TIMEX không có value | ~55% rơi vào `unknown` |
| KG nhiễu nên có conflict | 0 cycle, closed 100.0%, **~72 mâu thuẫn toàn corpus** | mục tiêu "tìm conflict trên gold" gần rỗng |

Giả định thứ ba là chí mạng. Mọi thiết kế trước đều đặt cược headline vào việc phát hiện
conflict trong một corpus chỉ có 72 cái — và đều bị hostile review cho 4/10.

**Nguyên tắc thiết kế rút ra: đóng góp không được lấy "conflict tồn tại" làm điều kiện tiên quyết.**

---

## 2. Framework đang được kiểm chứng

### 2.1 Ba kênh nối event

Số liệu quan trọng nhất: **chỉ 17.9%** cặp event có quan hệ thời gian là chia sẻ participant
(106,340 / 593,433). Tức 82% tín hiệu thời gian **nằm ngoài tầm với của SP(a)**.

| Kênh | Cơ chế nối | Số lượng | Analogue PaTeCon | Sức ràng buộc |
|---|---|---|---|---|
| **C1** | chia sẻ participant | 212,743 cặp | SP(a) | mềm (thống kê) |
| **C2** | causal / subevent | 46,014 + 12,019 | **SP(b)** | **cứng (logic)** |
| **C3** | đồng hiện trong document | phần còn lại (~75%) | *không có* | prior |

C2 là chỗ **toàn bộ ~72 mâu thuẫn thật nằm** (61 subevent + 11 causal). Không ngẫu nhiên:
chỉ kênh có ràng buộc cứng mới có gì để vi phạm.

### 2.2 SP(c) — pattern thứ ba mà PaTeCon không diễn đạt được

```
SP(a):  (x,p1,e1,t1), (x,p2,e2,t2)                  -- 1 subject
SP(b):  (x,p1,z,t1), (x,p0,y), (y,p2,w,t2)          -- 2 subject NỐI nhau bởi p0
SP(c):  (x,ra,e1,t1), (x,rc,e2,t2),
        (y,rb,e1,t1), (y,rd,e2,t2)                  -- 2 subject KHÔNG nối nhau,
                                                       cùng tham gia CẢ HAI event
```

x và y không có cạnh nào giữa chúng — chúng chỉ cùng xuất hiện trong hai event. Không phải
SP(a), không phải SP(b). Với event hyperedge đây là phép giao hai tập slot-filler; với
statement nhị phân đây là join 4 bảng không có ràng buộc nối.

**Bằng chứng SP(c) đáng giá** (đã đo, xấp xỉ bare-year):

| | Hnorm (entropy chuẩn hoá) | % cùng năm | n |
|---|---|---|---|
| chia sẻ 1 participant | 0.524 | 77.5% | 11,905 |
| chia sẻ ≥2 participant | **0.455** | **81.3%** | 2,881 |

Entropy thấp hơn = phân phối nhọn hơn = **dễ đạt confidence cao hơn**. Nên SP(c) không phải
"biểu diễn cho sang" mà là một **toán tử tinh chỉnh (refinement operator)** — thay thế cho
class-restriction của PaTeCon, vốn vô dụng ở đây vì MAVEN chỉ có 7 kiểu entity rất thô.

### 2.3 Hai graph, không phải một

PaTeCon gộp instance graph và corpus graph làm một, vì trong Wikidata entity lặp lại nên
chúng trùng nhau. Ở MAVEN thì không — và cố gộp là nguồn gốc của mọi lúng túng thiết kế.

**Graph A — instance graph** (mỗi document một cái, ~23 event):
```
Node:  Event (type, trigger, interval4) | Entity (doc-local) | Span | TIMEX
Edge:  Event --role--> Entity|Span      (236,937)
       Event --temporal--> Event        (593,433)
       Event --CAUSE/subevent--> Event  (58,033)
       TIMEX --CONTAINS--> Event        (66,418)
```
Event node = **sVertex của PaTeCon mở rộng n-ary**: thay `hasValue` (1 scalar) bằng
`slots: dict[role → list]`. Thời gian nằm **trên event node**, không trên role edge.

**Graph B — type graph** (một cái cho cả corpus, là *sản phẩm* của mining):
```
Node:  EventType (168) | Role (143) | EventType#Role (652)
Edge:  (T1,r1) --constraint--> (T2,r2)
         channel ∈ {C1,C2,C3} | phân phối nhãn | confidence | support (đếm theo DOCUMENT)
```

```
3,623 instance graph ──[mine, gom theo document]──▶ 1 type graph
                                                          │
        instance cần kiểm tra ◀──[chấm điểm]──────────────┘
```

Tách ra làm rõ ngay ba thứ trước đó lẫn lộn: **support đếm ở Graph B theo document**;
**conflict sống ở Graph A**; **constraint sống ở Graph B, không gắn instance nào**.

---

## 3. Thí nghiệm

### EXP1 — Giao thức edge-level holdout có đo được gì không? ❌ KHÔNG

**Giả thuyết cần bác bỏ:** vì gold đã closed 100%, giấu một cạnh BEFORE ngẫu nhiên thì
closure trên phần còn lại vẫn suy ra được → baseline bão hoà → constraint đóng góp ~0.

**Thiết kế:** mỗi document, giấu 10% cạnh BEFORE, hỏi closure có khôi phục được không.

**Kết quả:**
```
canh BEFORE bi giau      : 52,499
khoi phuc bang CLOSURE   : 43,782  →  83.4%
trung binh theo document :            69.0%
```

**Kết luận: edge-level holdout VÔ NGHĨA.** 83.4% khôi phục được mà không cần bất kỳ
constraint nào. Bất cứ recall nào báo cáo theo giao thức này chủ yếu đo closure, không đo
phương pháp. → Bắt buộc chuyển sang **event-level holdout**.

*(Đây là lỗi trong đề xuất T3 ban đầu của tôi, đã tự phát hiện và kiểm chứng.)*

### EXP2 — Pattern có sức dự đoán không? ⚠️ RẤT YẾU

**Thiết kế:** chia document 80/20 (seed 20261012, **chia theo document** để tránh rò rỉ qua
entity dùng chung). Mine phân phối nhãn theo signature trên MINE, dự đoán argmax trên EVAL.
Không gian nhãn 8 lớp gồm cả `NONE`.

**Kết quả:**

| | chia sẻ ≥1 participant | chia sẻ ≥2 |
|---|---|---|
| n (cặp trên EVAL) | 41,077 | 8,342 |
| MODEL (pattern) | 50.5% | 48.6% |
| B1 majority | 47.9% | 45.7% |
| B2 text-order | 36.0% | 31.3% |
| **vượt baseline mạnh nhất** | **+2.6** | **+2.9** |

Per-label cho thấy vấn đề thật: model đúng 81% trên `NONE` nhưng chỉ 31.5% trên
`BEFORE_FWD`, 2.4% trên `BEFORE_REV`, 3.0% `CONTAINS_FWD`, 0.8% `SIMULTANEOUS`,
**0% trên OVERLAP**. Nó gần như chỉ đang đoán lớp đa số.

**Chẩn đoán — có lỗi trong thiết kế thí nghiệm của tôi**, không chỉ ở framework:

1. **Đưa `NONE` vào không gian nhãn là sai.** Nó gộp hai bài toán khác bản chất: *có quan hệ
   không* (link prediction) và *quan hệ nào* (constraint checking). PaTeCon không dự đoán sự
   tồn tại của quan hệ — nó ràng buộc quan hệ **đã có**. `NONE` chiếm 50.5% nên argmax bị nó
   nuốt.
2. **argmax trên MỌI signature là sai chế độ.** PaTeCon chỉ giữ signature có conf ≥ 0.9. Trộn
   signature tự tin với signature mù mờ rồi lấy accuracy trung bình thì đo nhầm thứ.

→ EXP3 sửa cả hai.

### EXP3 — Ở đúng chế độ PaTeCon, pattern có "đúng" không? ✅ CÓ

**Sửa so với EXP2:** (a) bỏ `NONE`, chỉ xét cặp **thực sự có quan hệ**; (b) chỉ giữ signature
đạt conf ≥ θ với support ≥ 10 trên MINE, rồi hỏi **nó có giữ được conf đó trên EVAL không**.

Đây là kiểm chứng trực tiếp cho ý *"mine pattern đúng rồi từ pattern đúng tìm contradiction"*:
một pattern chỉ dùng để tuyên bố contradiction được **nếu nó đã được xác nhận độc lập trên
held-out**.

**Kết quả — level=type, chia sẻ ≥1 participant** (baseline majority `BEFORE_FWD` = 69.3%):

| θ | signature qua ngưỡng | phủ (cặp EVAL) | conf **giữ được** trên EVAL | vượt majority |
|---|---|---|---|---|
| 0.9 | 403 | 1,617 (7.6%) | **86.1%** | **+16.8** |
| 0.8 | 806 | 4,151 (19.4%) | 82.0% | +12.7 |
| 0.7 | 1,154 | 6,681 (31.2%) | 79.1% | +9.8 |

**Kết luận: pattern là THẬT.** Signature đạt conf ≥ 0.9 trên MINE giữ được **86.1%** trên
document chưa từng thấy, vượt lớp đa số **+16.8 điểm**. Đánh đổi phủ/độ chính xác đơn điệu
và lành mạnh — đúng dấu hiệu của quy luật thật, không phải nhiễu.

**Kết quả SP(c)** (chia sẻ ≥2 participant):

| level | θ | signature | phủ | giữ được | vượt majority |
|---|---|---|---|---|---|
| type | 0.9 | 22 | 62 | 85.5% | **+26.1** |
| role | 0.9 | 145 | 215 | 77.2% | **+21.6** |
| role | 0.7 | 327 | 1,102 | 70.5% | +14.9 |

SP(c) cho **lift lớn hơn** (+26.1 so với +16.8) — toán tử tinh chỉnh hoạt động đúng hướng.
Nhưng phủ rất nhỏ (62 cặp ở θ=0.9). Nhất quán với đo entropy trước đó: hiệu ứng thật, quần
thể nhỏ.

Chú ý: majority baseline **tụt** khi đòi ≥2 participant (69.3% → 59.4%), tức cặp đa-participant
đa dạng hơn về loại quan hệ. Bài toán khó hơn nhưng cũng nhiều thông tin để thu hơn — đó là
lý do lift lớn hơn.

**Đối chiếu ngưỡng quyết định đã đặt trước:**

| Ngưỡng | Đạt? |
|---|---|
| giữ conf ≥ 0.85 | ✅ 86.1% tại θ=0.9 |
| vượt majority ≥ +10 điểm | ✅ +16.8 |
| phủ ≥ 5,000 cặp | ❌ chỉ 1,617 tại θ=0.9 (đạt 6,681 nhưng phải hạ xuống θ=0.7) |

→ **Framework đứng được. Nút thắt không phải độ đúng mà là ĐỘ PHỦ.**

---

### EXP4 — Audit thống kê ✅ 2/3 lỗ hổng có thật

| Kiểm tra | Kết quả |
|---|---|
| Support | median **14**; 58% ≤15. Wilson lower bound median **0.74**; chỉ **4/403** có LB ≥ 0.9 |
| **FDR (permutation null)** | **34.7%** — 139.8/403 signature qua ngưỡng do may rủi |
| Phụ thuộc document | median **10** doc/signature → **lo hão**, không ảnh hưởng |
| Macro vs micro | 84.8% vs 86.1% → kết quả **vững**, không do vài signature phủ rộng |

### EXP5 — Quy tắc sửa (Wilson + BH-FDR + ≥5 doc) ✅ dự đoán đúng

| θ | quy tắc | signature | phủ | micro | macro |
|---|---|---|---|---|---|
| 0.9 | cũ | 403 | 1,617 | 86.1% | 84.8% |
| 0.9 | mới | 4 | 77 | 90.9% | 95.0% |
| 0.7 | cũ | 1,154 | 6,681 | 79.1% | 78.7% |
| **0.7** | **mới** | **339** | **2,592** | 84.0% | **86.4%** |

**FDR 34.7% → 0.0%.** Điểm ngọt: **θ=0.7 + quy tắc mới** (+17 điểm so majority 69.3%).

### EXP7 — Yêu cầu cấu trúc graph ⚠️ đảo ngược thiết kế

```
entity / event : mean = 1.11  median = 1  |  37.5% event co ZERO entity
CAUSAL   : closure them 0.5%  | do sau median=1 max=3
SUBEVENT : closure them 0.2%  | do sau median=1 max=2
```

| Định làm | Số liệu | Sửa |
|---|---|---|
| Hypergraph engine n-ary | bậc TB **1.11** | ❌ bảng phẳng đủ |
| Adjacency cho C2 | closure +0.5% | ❌ bảng cạnh trực tiếp |
| SP(c) làm trục chính | 62 cặp ở θ=0.9 | ⚠️ giữ làm phụ |
| Nâng phủ bằng cấu trúc | 37.5% event bậc 0; 60% arg là span chưa link | ✅ **nút thắt là ENTITY LINKING** |

### EXP6 — Kênh C2 (causal/subevent) ✅ **mạnh hơn C1 nhiều**

**Độ phủ:** 52,984 cạnh C2, 92.8% có quan hệ thời gian. **65.4% không chia sẻ participant**
→ C2 mở rộng thêm **32,171 cặp mà C1 không chạm tới được**.

**Sức dự đoán** (majority baseline 65.5%):

| θ | quy tắc | signature | phủ | micro | macro | vs majority |
|---|---|---|---|---|---|---|
| 0.9 | mới | 49 | 1,085 | 99.6% | **99.7%** | **+34.1** |
| 0.7 | mới | 401 | 2,585 | 97.2% | **96.7%** | **+31.7** |

So với C1 (macro 86.4%, +17) → **C2 vượt trội**.

**Vi phạm ràng buộc cứng trên gold — khớp chính xác con số ~72 đã đo trước:**

```
CAUSE        : 3 / 8,420
PRECONDITION : 8 / 37,594
SUBEVENT     : 61 / 12,019   (58 con-trước-cha + 3 cha-trước-con)
-------------------------------------------
TONG VI PHAM : 72
THIEU CONTAINS: 1,577  (thieu sot, KHONG phai mau thuan)
```

### EXP8 — Ablation C2: nghi ngờ "quá dễ" đã **SAI**

Thang tăng dần độ chi tiết, đánh giá trên **cùng** 9,370 cặp EVAL:

| Mức | phủ | acc | số key | |
|---|---|---|---|---|
| L0 majority | 9,370 | 61.8% | 1 | |
| L1 kind | 9,370 | 80.5% | 3 | +18.7 |
| **L2 kind+hướng** | **9,370** | **90.0%** | **6** | **+9.5** |
| L3 kind+hướng+types | 3,701 | 87.4% | 636 | −2.6 |

**Luật trần từng kind — CAUSE KHÔNG hề tautology:**

```
CAUSE        -> BEFORE_FWD    conf 63.7%   (1,325/5,883 la CONTAINS_FWD!)
PRECONDITION -> BEFORE_FWD    conf 84.9%
SUBEVENT     -> CONTAINS_FWD  conf 86.4%
```

`CAUSE ⇒ BEFORE` chỉ đúng **63.7%** — một phần tư là `CONTAINS` (nguyên nhân *chứa* kết quả
về thời gian, vd chiến tranh đang diễn ra gây ra các cái chết bên trong nó). Nghi ngờ
"định nghĩa nên hiển nhiên" **bị bác bỏ**.

**Điều kiện theo type giúp CÓ CHỌN LỌC:**

| kind | L1 | L3 | delta |
|---|---|---|---|
| CAUSE | 59.5% | 56.7% | **−2.7** ❌ |
| PRECONDITION | 82.2% | 89.8% | **+7.6** ✅ |
| SUBEVENT | 87.8% | **99.7%** | **+11.9** ✅✅ |

**Kết luận:** phần lớn sức mạnh của C2 đến từ **L2 = kind + hướng văn bản** (2 đặc trưng,
6 key) chứ không từ 636 signature theo type. Mining theo type chỉ đáng cho **SUBEVENT**
(lên 99.7%) và **PRECONDITION**; với **CAUSE thì làm hỏng**.

→ Thiết kế đúng là **cascade backoff L3 → L2 → L1** (chính là dàn tinh chỉnh ở MODEL.md §2.4):
lấy độ chính xác của L3 ở nơi có, lùi về L2 ở nơi thưa. Cascade nhiều khả năng vượt cả 4 mức.

### EXP9 — Cascade trên MẪU SỐ TRUNG THỰC ⚠️ **kết quả tỉnh táo nhất**

Mọi con số trước đó đo trên **tập con đã chọn lọc**. EXP9 đổi mẫu số sang **toàn bộ
106,880 cặp có quan hệ thời gian** trên EVAL.

| Chế độ | T1 (C2+types) | T2 (C2+kind+hướng) | T3 (C1+types) | T4 (majority) | TỔNG |
|---|---|---|---|---|---|
| naive | 3.5% @ 87.4% | 5.3% @ 91.8% | 11.1% @ **65.4%** | 80.1% @ 79.6% | **78.9%** |
| wilson θ=0.7 | 2.4% @ 97.2% | 6.3% @ 87.3% | 2.0% @ 83.9% | 89.2% @ 78.0% | **79.1%** |
| wilson θ=0.8 | 1.8% @ 98.1% | 5.9% @ 91.7% | 0.5% @ 87.1% | *abstain* | phủ **8.2%** @ **92.8%** |

**Majority một mình trên mẫu số này = 76.7%.** Cascade đầy đủ = 79.1% → **chỉ hơn +2.4 điểm.**

Ba điều bị phơi bày:

1. **Độ phủ là sát thủ.** 80–89% cặp rơi xuống majority. T1+T2+T3 gộp lại chỉ chạm ~10–19%.
2. **C1 không lọc thì LÀM HẠI.** T3 đạt 65.4% — *thấp hơn* majority 76.7%. Con số 86.4%
   ở EXP5 chỉ đúng trên tập signature đã lọc conf cao, không đúng khi dùng đại trà.
3. **Majority mạnh hơn tưởng.** Trên mẫu số đầy đủ là 76.7% chứ không phải 69.3% — vì
   69.3% đo trên cặp chia sẻ participant, một tập con thiên lệch.

**Đánh đổi thật của hệ thống:** hoặc **92.8% chính xác trên 8.2% độ phủ** (θ=0.8, abstain
phần còn lại), hoặc **79.1% trên 100% độ phủ** (chỉ +2.4 so majority).

### EXP10 — Benchmark lưu trữ · incremental · thời gian

Ba thiết kế, **cùng dữ liệu, cùng kết quả** (11,817 signature — đã kiểm chứng bằng nhau):

| Thiết kế | build (s) | mục lưu | mining (s) | incr / doc |
|---|---|---|---|---|
| S1 on-the-fly (code EXP2–9) | 0.00 | 0 | 0.36 | 0.00 ms |
| S2 inverted-index | 0.04 | 88,576 | 0.19 | 0.01 ms |
| **S3 materialized-pairs** | 0.20 | 105,367 | **0.04** | **0.03 ms** |

**S3 nhanh gấp 9× khi mining**, đổi lại 105K mục lưu và 0.2s build. Thêm một document mới
tốn **0.03 ms**, không phải tính lại gì.

**Nhưng phát hiện trung thực nhất: ở quy mô MAVEN, thời gian KHÔNG phải nút thắt.**
Trường hợp tệ nhất mining toàn corpus mất **0.36 giây**. Tối ưu lưu trữ ở đây là chuẩn bị
cho việc mở rộng corpus, không phải để giải quyết một vấn đề đang có.

Giá trị thật của S3 là **incremental**: cấu trúc bảng phẳng cho phép chèn document mới
theo thời gian hằng số, khớp đúng với kết luận EXP7 (không cần adjacency, causal/subevent
phẳng nên không có closure phải cập nhật lại).

### EXP11 — Entity linking tấn công nút thắt độ phủ ✅ **hiệu quả lớn**

Link 60% span chưa gán bằng khớp chuỗi chuẩn hoá **trong document**: trùng mention của
entity có sẵn → gán vào entity đó; không trùng → tạo pseudo-entity theo chuỗi.

| | TRƯỚC | SAU | thay đổi |
|---|---|---|---|
| bậc trung bình | 1.11 | **2.84** | **+155%** |
| event bậc 0 | 30,157 (37.5%) | **3,782 (4.7%)** | **−87%** |
| cặp đồng-tham-dự | 212,743 | **380,022** | **+79%** |

```
span chua link : 142,015
  -> khop entity co san : 22,841 (16.1%)
  -> tao pseudo-entity  : 119,160 (83.9%)
```

**Cảnh báo:** 83.9% là pseudo-entity — hai span cùng chuỗi chuẩn hoá chưa chắc cùng sở chỉ.
Trong phạm vi một document thì khớp chuỗi là heuristic hợp lý, nhưng **phải đo xem đồ thị
mở rộng có thực sự cải thiện mining hay chỉ thêm nhiễu** (EXP12).

Đáng chú ý: bậc TB 1.11 → 2.84 làm **lập luận n-ary/hyperedge sống lại** — EXP7 bác nó vì
bậc quá thấp, nhưng bậc đó là hệ quả của việc bỏ 60% argument, không phải bản chất dữ liệu.

### EXP12 — Cascade trên đồ thị mở rộng ⚠️ **kênh tốt lên, hệ thống KHÔNG**

Cùng mẫu số 106,880 cặp:

| | C1 chạm tới | T3 dùng | T3 acc | **cascade tổng** |
|---|---|---|---|---|
| GỐC | 20.0% | 2.0% | 83.9% | **79.1%** |
| MỞ RỘNG | **33.5%** | **6.3%** | **86.1%** | **79.1%** |

Entity linking làm T3 dùng **gấp 3 lần** và **chính xác hơn** (83.9→86.1), nhưng tổng
**không đổi**.

**Vì sao:** T3 giành 6.3% cặp từ T4 majority, được 86.1% thay vì ~78% → lãi ~0.5 điểm.
Nhưng T4 cũng tụt (78.0→77.5) vì những cặp bị giành đi chính là những cặp majority vốn
đã đoán đúng. Bù trừ ≈ 0.

> **Bài học:** nút thắt **không phải độ phủ**. Majority đã đúng 76.7%, và constraint
> mine được **phần lớn ĐỒNG Ý với majority** trên chính những cặp chúng phủ. Constraint chỉ
> có giá trị ở nơi nó **BẤT ĐỒNG** với majority và đúng.

→ Chỉ số đúng phải là **độ chính xác trên tập bất đồng**, không phải accuracy tổng (EXP13).

### EXP13 — Độ chính xác trên TẬP BẤT ĐỒNG 🔴 **kết quả quyết định**

Majority = `BEFORE_FWD` (77.6%). Chỉ xét các cặp mà tầng **bắn** và dự đoán **khác** majority:

| θ | Tầng | bắn | **bất đồng** | tầng đúng | maj đúng | **LÃI RÒNG** |
|---|---|---|---|---|---|---|
| 0.7 | T1 C2+kind+hướng+types | 2,589 | 1,106 | **99.8%** | 0.0% | **+1,104** |
| 0.7 | T2 C2+kind+hướng | 9,370 | 2,794 | **94.7%** | 0.1% | **+2,643** |
| 0.7 | **T3 C1+types** | 7,907 | **0** | — | — | **KHÔNG BAO GIỜ BẤT ĐỒNG** |
| 0.9 | T1 | 1,085 | 649 | **100.0%** | 0.0% | +649 |
| 0.9 | T2 | 7,523 | 1,997 | **98.9%** | 0.2% | +1,973 |
| 0.9 | **T3** | 671 | **0** | — | — | **KHÔNG BAO GIỜ BẤT ĐỒNG** |

**Hai kết luận dứt khoát:**

1. 🔴 **C1 — kênh kiểu PaTeCon — mang THÔNG TIN BẰNG KHÔNG.** Nó *chưa bao giờ* nói khác
   "đoán BEFORE_FWD". Mọi signature C1 mine được đều dư thừa hoàn toàn so với lớp đa số.
   Điều này giải thích trọn vẹn EXP12: mở rộng độ phủ C1 không đổi gì **vì C1 không nói gì cả**.

2. ✅ **C2 — kênh causal/subevent — mang thông tin THẬT.** ~3,700 cặp mà nó đúng còn majority
   sai, ở độ chính xác **95–100%**. Majority gần như **0%** đúng trên tập bất đồng — nghĩa là
   C2 bắt đúng chính xác những trường hợp mà quy tắc mặc định hỏng.

Vì sao EXP9/EXP12 chỉ thấy +2.4 điểm: 3,700/106,880 = **3.5%** tổng thể. Lãi là thật nhưng nhỏ
so với toàn quần thể — **không phải vì phương pháp yếu mà vì quần thể bị majority thống trị**.

> **Hệ quả cho thuật toán mining:** mine **C2**, bỏ **C1**. Dòng dõi PaTeCon (chia sẻ
> participant) không hoạt động trên substrate này; cấu trúc quan hệ mới là nơi có tín hiệu.

### EXP14 — Type-conditioning vs luật per-kind 🔴 **LÃI RÒNG = 0**

EXP13 đo bất đồng với global majority — nhưng SUBEVENT có majority riêng là `CONTAINS_FWD`
nên nó "bất đồng" một cách tầm thường. Câu hỏi công bằng: **trong từng kind**, điều kiện
theo kiểu event có thắng luật per-kind không?

**Sáu luật per-kind (viết tay được trong 2 phút):**

```
(CAUSE,        FWD) -> BEFORE_FWD     71.8%
(CAUSE,        REV) -> BEFORE_REV     77.2%
(PRECONDITION, FWD) -> BEFORE_FWD     93.2%
(PRECONDITION, REV) -> BEFORE_REV     88.7%
(SUBEVENT,     FWD) -> CONTAINS_FWD   99.0%
(SUBEVENT,     REV) -> CONTAINS_REV   97.9%
```

**Kết quả:**

| θ | KIND | bắn | bất đồng | lãi ròng |
|---|---|---|---|---|
| 0.7 | CAUSE | 60 | **0** | +0 |
| 0.7 | PRECONDITION | 1,429 | **0** | +0 |
| 0.7 | SUBEVENT | 1,100 | **0** | +0 |
| 0.9 | PRECONDITION | 436 | **0** | +0 |
| 0.9 | SUBEVENT | 649 | **0** | +0 |
| | **TỔNG** | | | **+0** |

🔴 **636 signature mine được KHÔNG BAO GIỜ nói khác 6 luật viết tay.**

### Tổng hợp hai kết quả âm tính

| Kênh | Kiểm chứng | Kết luận |
|---|---|---|
| C1 (chia sẻ participant, kiểu PaTeCon) | EXP13 | không bao giờ bất đồng với global majority → **thông tin = 0** |
| C2 type-level | EXP14 | không bao giờ bất đồng với luật per-kind → **thông tin = 0** |

**Toàn bộ tín hiệu nằm trong đúng 2 đặc trưng:** loại quan hệ (CAUSE/PRECONDITION/SUBEVENT)
và hướng văn bản (FWD/REV). Sáu luật. Mining không thêm gì.

> **Đây là một kết quả âm tính có giá trị công bố**, đúng khung "port audit" mà bản tổng hợp
> trước đã khuyến nghị: *pattern-based temporal constraint mining, khi port sang đồ thị
> event cục bộ theo document, bị một baseline 6 luật (loại quan hệ + thứ tự văn bản) áp đảo.*

### EXP15 — Có đặc trưng nào thoát khỏi 6 luật không? 🔴 **KHÔNG**

Quần thể: **109,666 cặp KHÔNG có liên kết C2** (~90% dữ liệu, nơi 22% lỗi còn lại nằm).
Majority `BEFORE_FWD` = 76.7% trên EVAL.

| Đặc trưng | bắn (θ=0.7) | bất đồng | lãi ròng |
|---|---|---|---|
| F1 (ta,tb) kiểu event | 40,707 | **0** | +0 |
| F2 khoảng cách câu | 101,883 | **0** | +0 |
| F3 (ta,tb,khoảng cách câu) | 32,780 | **0** | +0 |
| F4 có TIMEX anchor | 108,700 | **0** | +0 |
| F5 (khoảng cách câu, TIMEX) | 101,883 | **0** | +0 |

### Kiểm tra phản biện: bộ lọc Wilson có che khuất bất đồng không?

Nghi vấn chính đáng — bucket bất đồng với majority thì theo bản chất là bucket không có
nhãn nào áp đảo, nên confidence thấp, nên bị Wilson lọc. Kiểm tra bỏ bộ lọc:

| support ≥ | số bucket | argmax ≠ majority | còn lại sau Wilson ≥ 0.7 |
|---|---|---|---|
| 10 | 9,690 | **436 (4.5%)** | **0** |
| 30 | 2,891 | 60 (2.1%) | **0** |
| 100 | 454 | 7 (1.5%) | **0** |

**Kết luận mạnh hơn, không yếu đi:** bất đồng **có tồn tại** (4.5% bucket) nhưng **chưa bao
giờ đủ bằng chứng để tin**. Và tỉ lệ đó **teo dần theo support** (4.5% → 2.1% → 1.5%) —
đúng dấu hiệu của **nhiễu bị rửa trôi khi có thêm dữ liệu**, không phải tín hiệu thật bị
bỏ sót. Khớp với FDR 34.7% đo ở EXP4.

---

## 4. Điều đã học được cho đến giờ

1. **Gold nhất quán tuyệt đối vừa là tường vừa là tài sản.** Là tường nếu mục tiêu là tìm
   conflict trong gold. Là tài sản nếu mục tiêu là *xác nhận pattern đúng* — vì không có
   nhiễu annotation làm bẩn thống kê. Đây là lý do hướng "tìm pattern đúng trước" vững hơn
   hướng "xếp hạng bất thường".

2. **Baseline tầm thường mạnh hơn dự đoán.** Majority đạt 47.9%. Bất kỳ phương pháp nào
   không báo cáo baseline này đều đang tự lừa mình. Text-order chỉ 36% — yếu hơn majority,
   nhưng vẫn phải báo cáo cả hai.

3. **Lớp nhãn cực kỳ mất cân bằng.** `BEFORE_FWD` 58,849 vs `OVERLAP_REV` 175 (chênh 336
   lần). Mọi accuracy tổng phải kèm per-label, nếu không nó chỉ phản ánh lớp đa số.

4. **Giao thức đánh giá phải được kiểm chứng trước phương pháp.** EXP1 cho thấy một giao
   thức nghe hợp lý (hide edges, predict back) có thể vô nghĩa hoàn toàn vì một tính chất
   của dữ liệu (closure 100%) mà ta đã đo từ trước nhưng không nối vào.

---

## 5. Rủi ro còn mở

- **EXP3 có thể vẫn âm tính.** Nếu vậy, kết luận trung thực là: trên substrate này,
  pattern C1 không mang thông tin vượt lớp đa số, và bài báo phải lùi về C2 (ràng buộc cứng,
  ~72 case, đếm chính xác) + đóng góp đo lường (định lý suy biến, trần với tới 17.9%).
- **Số 0.455 vs 0.524 mới ở mức bare-year**, n=2,881. Đủ để biện minh xây cấu trúc n-ary,
  **chưa đủ** làm headline.
- **C3 (đồng hiện document) là prior, không phải constraint.** Cắt nếu thiếu thời gian.
- **TIMEX normalizer vẫn là đường găng** cho mọi thứ liên quan granularity: 62.1% regex,
  37.9% cần ngữ cảnh (4 họ xử lý được), ước tính ~1 tuần.

---

## 6. Tệp

```
tempekg_exp/
  exp1_closure_saturation.py    kiểm chứng lỗi edge-level holdout
  exp2_holdout_prediction.py    dự đoán quan hệ, có NONE  (thiết kế lỗi, giữ để đối chiếu)
  exp3_pattern_validation.py    validation đúng chế độ PaTeCon
  exp2_out.txt / exp3_out.txt   kết quả thô
  SPEC.md                       tài liệu này
```
