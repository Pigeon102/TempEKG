# Tổ chức Knowledge Graph trên MAVEN — chi tiết thực tế

Số đo từ đồ thị **đã dựng thật** (`tempekg.py::build()`), không phải thiết kế trên giấy.

---

# 1. QUY MÔ THỰC TẾ

## Node

| loại | số lượng | ghi chú |
|---|---|---|
| **Event** | **84,285** | 168 kiểu |
| **Entity** (doc-local) | **28,339** | chỉ tính entity thực sự lấp vai |
| TIMEX | 20,827 span | chuẩn hoá được **91.3%** |

## Edge

| tầng | loại | số lượng | tỉ lệ |
|---|---|---|---|
| ràng buộc | **S1** temporal | 593,477 | 53.5% |
| ràng buộc | **S4** closure | 458,145 | 41.3% |
| ràng buộc | **S2** causal | 46,014 | 4.1% |
| ràng buộc | **S3** subevent | 12,019 | 1.1% |
| | **TỔNG ràng buộc** | **1,109,655** | |
| hyperedge | role edge (event→filler) | **93,884** | 132 vai |

## Bậc

| | trung bình | max | ghi chú |
|---|---|---|---|
| role / event | **1.89** | 59 | bậc 0: **0.0%** (mọi event đều có ít nhất 1 vai) |
| event / entity | **3.13** | 53 | |
| **anchor / event** | **0.20** | — | **chỉ 19.7% event có ≥1 anchor**, 0.4% có ≥2 |

## Phân bố theo document

```
3,623 document | event/doc: TB 23.3 · trung vi 19 · max 121
```

---

# 2. CẤU TRÚC HYPEREDGE — event là gì trong đồ thị này

Một event **không phải node đơn** mà là **siêu cạnh có nhãn vai**:

```
                  EVENT_76bb...  [type=Killing]
                        │
        ┌───────────────┼───────────────┬──────────────┐
     Killer          Victim          Location      Instrument
        │               │                │              │
   ENT_british     ENT_valley      ENT_newyork      (trong)
```

Hình thức hoá (MODEL.md §1.2):

$$\tau : \mathcal{E}_d \to T, \qquad \iota : \mathcal{E}_d \times R \to 2^{\mathcal{X}_d}$$

**Mệnh đề 1** — PaTeCon là trường hợp riêng bậc **đúng bằng 2** với vai cố định
$\{\mathsf{subj}, \mathsf{obj}\}$: `sVertex` = siêu cạnh, `eVertex` = đỉnh.

**Thực tế đo được:** bậc trung bình **1.89** vai/event (chỉ đếm vai có entity_id).
Nghĩa là siêu cạnh **rất mỏng** — gần với nhị phân hơn là n-ary thực sự.

> Đây là lý do **KHÔNG dùng hypergraph engine**: bậc 1.89 không đủ để biện minh chi phí.
> Bảng phẳng + index là đủ.

---

# 3. BỐN TẦNG RÀNG BUỘC — vì sao `source` nằm trong khoá chính

```sql
constraint_edge(doc_id, e1, e2, source, ...)
  PRIMARY KEY (doc_id, e1, e2, source)
                              ^^^^^^
```

Cùng một cặp $(e_1, e_2)$ có **nhiều dòng**, mỗi dòng một nguồn:

```
(doc, EVENT_a, EVENT_b, 'S1_temporal')  -> 'BEFORE'      hard
(doc, EVENT_a, EVENT_b, 'S2_causal')    -> 'NOT_AFTER'   hard
(doc, EVENT_a, EVENT_b, 'S4_closure')   -> 'BEFORE'      hard
```

**Đo được:** **81.8%** cặp có ≥2 nguồn độc lập ràng buộc.

| số nguồn | số cặp | tỉ lệ |
|---|---|---|
| 1 | 108,500 | 18.2% |
| **2** | **466,102** | **78.0%** |
| **3** | **22,969** | **3.8%** |

Đây là thứ cho phép **held-out source precision** — giữ một nguồn ra ngoài để kiểm chứng.
Wikidata mỗi fact **một nguồn** nên PaTeCon buộc phải viết *"precision is not calculated"*.

---

# 4. TẦNG THỜI GIAN — chỗ yếu nhất

```
TIMEX span (20,827)
     │  normaliser v2, 91.3% do phu
     ▼
(lo, hi, granularity, norm_method)
     │  qua canh CONTAINS (66,418)
     ▼
interval cua EVENT
```

## Vấn đề định lượng

| | số |
|---|---|
| event có **≥1 anchor** | **19.7%** ⚠️ |
| event có ≥2 anchor (để xét T5) | 0.4% của toàn bộ = **17,102 event** |
| anchor/event trung bình | **0.20** |

> **80.3% event KHÔNG có mốc thời gian tuyệt đối nào.** Với chúng, mọi vị từ thời gian trả
> về `unknown`. Đây là giới hạn cứng của substrate, không phải của thuật toán.

## Nhiễu từ suy diễn tham chiếu

| nhóm | tỉ lệ conflict |
|---|---|
| anchor **regex thuần** | **7.27%** |
| anchor có **refprop** | **23.75%** |
| chênh | **3.3×** |

Nâng độ phủ 75.7% → 91.3% **không giảm** tỉ lệ này. Nên schema **bắt buộc** giữ
`timex.norm_method` để tách hai nhóm khi báo cáo.

---

# 5. SO SÁNH TỔ CHỨC: MAVEN vs WIKIDATA

| | Wikidata (WD50K) | **MAVEN** |
|---|---|---|
| đơn vị cơ bản | fact nhị phân `(S,P,O,T)` | **siêu cạnh event có nhãn vai** |
| bậc | luôn 2 | TB **1.89**, max 59 |
| property vocabulary | **6** | 168 type × 132 role → **459** khi chiếu |
| entity | lặp toàn cục | **0/68,348 vượt document** |
| thời gian | mọi fact có interval | **19.7%** event có anchor |
| nguồn ràng buộc / cặp | **1** | **81.8% có ≥2** |
| constraint ngữ nghĩa | ❌ phải mine từ tần suất | ✅ subevent/causal, precision ~100% |
| gold consistency | có lỗi (57.3% pad `0101`) | **100% đóng kín bắc cầu** |

---

# 6. LƯU TRỮ & HIỆU NĂNG

| thiết kế | build | mining | incremental |
|---|---|---|---|
| on-the-fly | 0.00s | 0.36s | — |
| inverted index | 0.04s | 0.19s | 0.01 ms/doc |
| **materialized pairs** | 0.20s | **0.04s** | **0.03 ms/doc** |

Ba thiết kế cho **cùng** 11,817 signature (đã kiểm chứng bằng nhau).

**Không dùng:** hypergraph engine (bậc 1.89) · adjacency (closure +0.2–0.5%, độ sâu 1) ·
cross-document index (0 entity vượt doc) · chiếu nhị phân (459 property → PaTeCon >30 phút).

---

# 7. ĐÁNH GIÁ TỔ CHỨC HIỆN TẠI

## Đúng

✅ `source` trong khoá chính → held-out precision (**không substrate nào khác làm được**)
✅ Bảng phẳng thay hypergraph engine → mining **0.04s**, incremental **0.03 ms/doc**
✅ `norm_method` + `granularity` → tách nhiễu, phân biệt REFINEMENT/CONFLICT
✅ Tách instance graph / type graph → support đếm đúng đơn vị (document)

## Còn thiếu

| | vấn đề | ảnh hưởng |
|---|---|---|
| ⚠️ | **80.3% event không có anchor** | mọi vị từ thời gian → `unknown` |
| ⚠️ | 60% argument là span chưa link (mới link được bằng khớp chuỗi) | bậc thật có thể cao hơn 1.89 |
| ⚠️ | Không có tập gán nhãn đúng/sai | **chưa tính được P/R trên MAVEN** |
| ⚠️ | `recurrence_class` chưa ghi vào schema thực (mới tính on-the-fly) | |

## Việc tổ chức KG cần làm tiếp

| # | việc | vì sao |
|---|---|---|
| 1 | Vật chất hoá schema ra Parquet/DuckDB | hiện đồ thị dựng lại mỗi lần chạy (~40s) |
| 2 | Ghi `recurrence_class` và `norm_method` vào bảng | đang tính lại mỗi lần |
| 3 | Lan truyền anchor qua quan hệ thời gian | có thể nâng 19.7% → cao hơn nhiều: event không anchor nhưng `BEFORE` một event có anchor thì suy ra được cận |

**Mục 3 đáng làm nhất** — nó tấn công trực tiếp điểm yếu lớn nhất (80.3% event không có mốc),
và dùng chính S1/S4 đã có trong đồ thị.
