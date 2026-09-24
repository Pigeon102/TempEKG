# FRAMEWORK — Recall ≥ PaTeCon, Precision đo được và cao hơn

Xây từ toàn bộ EXP1–20 + tái lập PaTeCon gốc. Mục tiêu do người dùng đặt:
**recall bằng hoặc vượt họ, và precision đo được trên MAVEN, cao hơn họ.**

---

# 1. Vì sao PaTeCon không đo được precision — và vì sao mình đo được

## 1.1 Nguyên nhân gốc: Wikidata KHÔNG CÓ DƯ THỪA

Mỗi fact Wikidata được khẳng định **một lần**. `(Q23, P569, 17320222)` chỉ có một nguồn.
Khi constraint báo nó sai, **không có nguồn thứ hai để đối chiếu**. Nên họ buộc phải viết:

> *"only conflicting pairs are detected and no resolution is performed, so **precision is
> not calculated**"* — §6.1.2

Cách duy nhất họ đo được là **recall** trên tập gán nhãn thủ công (WD-411): so hai phiên bản
dump, fact bị xoá là ứng viên sai, 2 chuyên gia kiểm.

## 1.2 MAVEN CÓ dư thừa — đo được (EXP20)

MAVEN-ERE annotate **bốn task riêng biệt** trên cùng tập event. Mỗi task ràng buộc quan hệ
thời gian một cách **độc lập**:

| Nguồn | Từ đâu | Ràng buộc suy ra |
|---|---|---|
| **S1** | quan hệ thời gian trực tiếp | chính nhãn đó |
| **S2** | quan hệ nhân quả | nguyên nhân **không** sau kết quả |
| **S3** | quan hệ subevent | cha **chứa** con |
| **S4** | bắc cầu từ cạnh thời gian khác | $a<b<c \Rightarrow a<c$ |

**Số đo (EXP20), 597,571 cặp event:**

| số nguồn ràng buộc | số cặp | tỉ lệ |
|---|---|---|
| 1 nguồn | 108,500 | 18.2% |
| **2 nguồn** | **466,102** | **78.0%** |
| **3 nguồn** | **22,969** | **3.8%** |
| **≥2 nguồn → ĐO ĐƯỢC PRECISION** | **489,071** | **81.8%** |

Trong 489,071 cặp được đối chiếu chéo: **116 mâu thuẫn (0.02%)**, mỗi cái được **≥2 lớp
annotation độc lập xác nhận**.

> **Đây là lợi thế cấu trúc của substrate event mà KG thực thể không có** — và là chìa khoá
> cho toàn bộ framework.

---

# 2. Giao thức đánh giá: HELD-OUT SOURCE

## 2.1 Nguyên tắc

> **Không bao giờ dùng cùng một nguồn để vừa phát hiện vừa kiểm chứng.**

```
   nguồn A ──► phát hiện conflict
                      │
   nguồn B ──► kiểm chứng độc lập  ──► precision
```

## 2.2 Định nghĩa

Với tập nguồn $\mathcal{S} = \{S_1, S_2, S_3, S_4\}$, chọn $A \subset \mathcal{S}$ để phát
hiện và $B = \mathcal{S} \setminus A$ để kiểm chứng:

$$\text{Precision}_A = \frac{|\{\text{cặp } A \text{ gắn cờ}\} \cap \{\text{cặp } B \text{ xác nhận sai}\}|}{|\{\text{cặp } A \text{ gắn cờ}\}|}$$

$$\text{Recall}_A = \frac{|\{\text{cặp } A \text{ gắn cờ}\} \cap \{B \text{ xác nhận sai}\}|}{|\{\text{cặp } B \text{ xác nhận sai}\}|}$$

**Không cần annotate.** Không vòng lặp — A và B là các task annotation khác nhau.

## 2.3 So sánh trực tiếp với PaTeCon

| | PaTeCon | Framework này |
|---|---|---|
| Recall | ✅ trên WD-411 (gán nhãn thủ công) | ✅ trên tập xác nhận chéo |
| **Precision** | ❌ **không tính được** | ✅ **tính được, không cần annotate** |
| Chi phí gán nhãn | 2 chuyên gia × 822 fact | **0** |
| Vì sao khác | Wikidata 1 nguồn/fact | MAVEN **81.8% cặp có ≥2 nguồn** |

---

# 3. Cấu trúc đồ thị — suy ra TỪ YÊU CẦU, không phải thẩm mỹ

Yêu cầu §2 buộc đồ thị phải: **lưu nhiều nguồn ràng buộc độc lập cho cùng một cặp**, và
**giữ nguồn tách biệt** để hold-out được.

## 3.1 Multi-layer edge — mỗi cặp, nhiều cạnh có nhãn nguồn

```sql
-- Lop 0: node
events(event_id PK, doc_id, type, sent_id, char_start, char_end)
entities(entity_id PK, doc_id, ent_type)
timex(timex_id PK, doc_id, surface, norm_lo, norm_hi, granularity)

-- Lop 1: tham du (n-ary event hyperedge, phang hoa)
args(event_id, role, filler_id, filler_kind, link_conf)

-- Lop 2: RANG BUOC, tach theo NGUON  <-- diem mau chot
constraint_edge(
   doc_id, e1, e2,
   source     ENUM('S1_temporal','S2_causal','S3_subevent','S4_closure','S5_mined'),
   implied    VARCHAR,      -- rang buoc thoi gian suy ra
   strength   ENUM('hard','soft'),
   conf       FLOAT,        -- 1.0 voi hard
   PRIMARY KEY (doc_id, e1, e2, source)
)
```

**`source` nằm trong khoá chính.** Đó là toàn bộ điểm khác biệt so với mọi thiết kế trước:
cùng một cặp $(e_1,e_2)$ có **nhiều dòng**, mỗi dòng một nguồn. Hold-out = `WHERE source != A`.

## 3.2 Vì sao KHÔNG cần hypergraph engine / adjacency

Đã đo (EXP7, EXP10):

| Định làm | Số đo | Quyết định |
|---|---|---|
| hypergraph engine n-ary | bậc TB 1.11 → 2.84 sau linking | ❌ bảng phẳng |
| adjacency cho causal/subevent | closure thêm **0.2–0.5%**, độ sâu 1 | ❌ bảng cạnh |
| cross-document | 0/68,348 entity vượt doc | ❌ không tồn tại |

**S3 materialized-pairs**: build 0.20s, mining **0.04s** (nhanh 9×), incremental
**0.03 ms/doc**. Ba thiết kế cho **cùng** 11,817 signature (đã kiểm chứng).

## 3.3 Bài học scale từ PaTeCon+

PaTeCon chạy WD50K (**6 property**) trong 1.1s. Trên MAVEN (**459 property** sau chiếu
`EventType#Role`) index $|R|^2$ lớn hơn **5,800×** và chạy quá 5 phút chưa xong.

→ **Chiếu nhị phân làm nổ vocabulary.** Giữ event node n-ary trong bảng phẳng, chỉ chiếu
khi cần chạy code của họ để đối chiếu. Đây là lý do kỹ thuật, có số, để **không** chiếu.

---

# 4. Thuật toán mining — giữ gì từ PaTeCon, sửa gì

## 4.1 Giữ (đã chứng minh giá trị)

| Thành phần | Vai trò | Bằng chứng giữ |
|---|---|---|
| **Logic ba trị** pos/neg/**unknown** | ước lượng có điều kiện trên *tính đo được* | 55% event thiếu anchor |
| **SP(b)** hai chủ thể nối bởi cạnh phi thời gian | → kênh C2 causal/subevent | C2 macro **96.7%**, +31.7 vs majority |
| Khung support/confidence + refinement | kiểm định phân tầng | tái lập được 12/13 constraint |

## 4.2 Sửa (mỗi cái có bằng chứng)

| Sửa | Lỗi được sửa | Bằng chứng |
|---|---|---|
| **Cận dưới Wilson** thay điểm ước lượng | ngưỡng lật vì **1 instance** | constraint #13 = $80/89 = 0.8989$, Wilson$_{lo} \approx 0.82$ |
| **BH-FDR $q \le 0.05$** | khám phá giả | FDR **34.7% → 0.0%** |
| **Support đếm theo document** | cặp trong doc không độc lập | trung vị 10 doc/signature |
| **Held-out validation** | không ai kiểm constraint | giữ **86.1%** trên doc chưa thấy |
| **Bỏ SP(a) chia sẻ participant** | thông tin = 0 | **chưa bao giờ** bất đồng với majority |

## 4.3 Thêm (họ không có)

| Thêm | Vì sao |
|---|---|
| **Tách hard / soft** | hard = ngữ nghĩa quan hệ (subevent⇒contains), vi phạm = **lỗi chắc chắn** |
| **Held-out source precision** | §2 — họ không đo được |
| **T5 granularity** | 13.35% dữ liệu **của họ**, 49× mức ngẫu nhiên, zero cơ chế |

---

# 5. Pipeline

```
   MAVEN-Arg ─┐
              ├─► join event_id ─► ECKG (bang phang, multi-layer edge)
   MAVEN-ERE ─┘                        │
                                       ├─► S1 temporal   (hard, tu annotation)
                                       ├─► S2 causal     (hard, ngu nghia)
                                       ├─► S3 subevent   (hard, ngu nghia)
                                       ├─► S4 closure    (hard, logic)
                                       └─► S5 mined      (soft, Wilson+FDR+held-out)
                                            │
              hold-out source ──────────────┤
                                            ▼
                              PRECISION + RECALL khong can annotate
```

---

# 6. Bảng kết quả dự kiến cho bài báo

| | PaTeCon (WD50K) | PaTeCon (MAVEN) | Framework này (MAVEN) |
|---|---|---|---|
| Constraint | 12 (12C/0M/0W) | *đang chạy* | mined + hard, có Wilson/FDR |
| Conflict phát hiện | 819 | *đang chạy* | S5 gắn cờ |
| **Recall** | trên WD-411 | — | trên 116 cặp xác nhận chéo |
| **Precision** | ❌ **không tính được** | ❌ | ✅ **held-out source** |
| FDR kiểm soát | ❌ | ❌ | ✅ BH $q \le 0.05$ |
| Held-out validation | ❌ | ❌ | ✅ 86.1% |
| T5 granularity | ❌ | ❌ | ✅ |

---

# 7. Việc phải làm, xếp theo thứ tự

| # | Việc | Chi phí | Chặn cái gì |
|---|---|---|---|
| 1 | Cài held-out source precision (§2) | 2 ngày | **con số chính của bài** |
| 2 | Hoàn tất PaTeCon-trên-MAVEN để có cột đối chiếu | đang chạy | bảng §6 |
| 3 | TIMEX normaliser (62.1% regex + reference-time) | ~1 tuần | T5 granularity trên MAVEN |
| 4 | Cài mutual-exclusion + disjointness cho ngang bao phủ | 3 ngày | recall ≥ họ |
| 5 | Mức C: model TRE + tầng sửa | ~2 tuần | target 85,243 |

**Mục 1 là quan trọng nhất** — nó tạo ra con số mà PaTeCon **về cấu trúc không thể có**,
và nó không phụ thuộc normaliser hay model mới.
