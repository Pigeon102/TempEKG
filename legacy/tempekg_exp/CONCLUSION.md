# TempEKG — Kết luận: trả lời goal bằng bằng chứng

**16 thí nghiệm trên MAVEN-Arg + MAVEN-ERE thật. Không có số giả.**
Nhật ký từng thí nghiệm: [SPEC.md](SPEC.md) · Mô hình toán: [MODEL.md](MODEL.md)

---

## Câu 1 — Merge hai bộ dữ liệu có khả thi không?

**Có, và bắt buộc.** Mỗi bộ thiếu đúng thứ bộ kia có.

| | MAVEN-Arg | MAVEN-ERE |
|---|---|---|
| event + type + argument | ✅ 80,479 event / 236,937 arg / 143 role | ❌ |
| quan hệ event–event | ❌ | ✅ 593,433 cặp |
| TIMEX | ❌ | ✅ 20,827 span (không có value) |
| entity cluster | ✅ có ở cả blind test | ❌ |

Join sạch: `doc_id` (4,480/4,480) và `event_id` (**79,740** chung).

---

## Câu 2 — Loại đồ thị nào và construct ra sao?

### Đối tượng toán học (MODEL.md §1)

Siêu đồ thị có nhãn vai, mỗi document một cái:
$$\tau : \mathcal{E}_d \to T, \qquad \iota : \mathcal{E}_d \times R \to 2^{\mathcal{X}_d}$$

**Mệnh đề 1** — PaTeCon là hạn chế xuống **bậc đúng bằng 2** với vai
$\{\mathsf{subj},\mathsf{obj}\}$. `sVertex` = siêu cạnh, `eVertex` = đỉnh.

### Nhưng số liệu bác bỏ việc xây engine siêu đồ thị

| Định làm | Số đo | Quyết định |
|---|---|---|
| Hypergraph engine n-ary | bậc TB **1.11** (EXP7) → **2.84** sau linking (EXP11) | ❌ bảng phẳng đủ |
| Adjacency cho causal/subevent | closure chỉ thêm **0.2–0.5%**, độ sâu median **1** (EXP7) | ❌ bảng cạnh trực tiếp |
| Cross-document entity | **0/68,348** entity vượt document | ❌ không tồn tại |

### Thiết kế được chọn: **S3 materialized-pairs** (EXP10)

| Thiết kế | build | mục lưu | mining | incremental |
|---|---|---|---|---|
| S1 on-the-fly | 0.00s | 0 | 0.36s | — |
| S2 inverted-index | 0.04s | 88,576 | 0.19s | 0.01 ms/doc |
| **S3 materialized-pairs** | 0.20s | 105,367 | **0.04s** | **0.03 ms/doc** |

Cả ba cho **cùng** 11,817 signature — đã kiểm chứng bằng nhau.

- **Lưu trữ**: 105K dòng bảng phẳng, không cần graph engine
- **Data mới**: **0.03 ms/document**, thời gian hằng số, không phải tính lại closure
- **Tốc độ**: nhanh **9×** so với tính on-the-fly

> ⚠️ **Trung thực:** ở quy mô MAVEN thời gian **không phải nút thắt** — tệ nhất 0.36 giây
> cho toàn corpus. Giá trị của S3 là **incremental**, không phải cứu một vấn đề đang có.

---

## Câu 3 — Thuật toán mining tối ưu?

### Câu trả lời: **6 luật.** Mining không thêm gì.

```
(CAUSE,        FWD) -> BEFORE_FWD     71.8%
(CAUSE,        REV) -> BEFORE_REV     77.2%
(PRECONDITION, FWD) -> BEFORE_FWD     93.2%
(PRECONDITION, REV) -> BEFORE_REV     88.7%
(SUBEVENT,     FWD) -> CONTAINS_FWD   99.0%
(SUBEVENT,     REV) -> CONTAINS_REV   97.9%
```

### Bằng chứng — ba kết quả âm tính độc lập

| Thí nghiệm | Kiểm chứng | Kết quả |
|---|---|---|
| **EXP13** | C1 (chia sẻ participant — kiểu PaTeCon) | **không bao giờ** bất đồng với majority → thông tin = 0 |
| **EXP14** | C2 type-level, 636 signature | **không bao giờ** bất đồng với 6 luật → lãi ròng **+0** |
| **EXP15** | kiểu event, khoảng cách câu, TIMEX anchor | lãi ròng **+0** trên 109,666 cặp |

Kênh C2 **có** giá trị thật so với majority toàn cục: **+3,700 cặp** đúng ở 95–100% (EXP13).
Nhưng giá trị đó đến **hoàn toàn** từ 2 đặc trưng (loại quan hệ × hướng văn bản), không từ
mining.

### Vì sao — đặc trưng hoá toán học (MODEL.md §7)

$$I(\rho;\sigma) > 0 \quad\text{nhưng}\quad \mathbb{E}[\text{lãi quyết định}] \approx 0$$

Hai rào cản độc lập:

1. **Quyết định** — tỉ lệ nền $p_0/p_1 \approx 5.0$ đòi log-odds $> 1.61$ nats *chỉ để hoà*
2. **Bằng chứng** — phải vượt cận dưới Wilson

| support ≥ | vượt rào 1 | NULL mô phỏng | vượt rào 2 |
|---|---|---|---|
| 10 | 5.11% | 0.30% | **0** |
| 30 | 2.17% | 0.00% | **0** |
| 100 | 1.04% | 0.00% | **0** |

Bất đồng cao hơn null **17×** → **có** liên hệ thống kê thật. Nhưng khi dùng để dự đoán,
**cả hai bên đều sai** (feature 29–32%, majority 17–42%) — đó là những cặp **bản chất mơ hồ**.
Lãi tốt nhất **+27 / 109,666 = +0.02%**.

> Đây là phân biệt mà support/confidence của PaTeCon **không thể hiện được**, và là lý do
> hình thức khiến việc port thất bại trên substrate này.

---

## Học được gì từ PaTeCon

| Thành phần | Vai trò hình thức | Dùng lại? |
|---|---|---|
| Logic ba trị (bỏ `unknown`) | ước lượng có điều kiện trên *tính đo được* | ✅ thiết yếu |
| SP(b) | hai subject nối bởi cạnh phi thời gian | ✅ → kênh C2 (causal/subevent) |
| support/confidence | | ⚠️ thiếu khoảng tin cậy + FDR (EXP4: **FDR 34.7%**) |
| entity-level confidence | | ❌ suy biến (0/68,348 entity vượt doc) |
| PaTeCon+ pruning | | ❌ không cần (0.36s toàn corpus) |
| SP(a) / chia sẻ participant | | ❌ **thông tin = 0** trên substrate này |

---

## Kết luận cho bài báo

Đây là **kết quả âm tính được thiết lập nghiêm ngặt**, đúng khung "port audit":

> *Pattern-based temporal constraint mining, khi port từ KG thực thể liên kết toàn cục sang
> đồ thị event cục bộ theo document, bị một baseline 6 luật (loại quan hệ × thứ tự văn bản)
> áp đảo. Chúng tôi định vị nguyên nhân: đặc trưng mang thông tin tương hỗ dương nhưng lãi
> quyết định bằng không — một phân biệt mà support/confidence không nắm bắt được.*

Đóng góp đứng vững, xếp theo độ chắc:

1. **Định lý suy biến** — entity-level ≡ fact-level trên đồ thị entity cục bộ (0/68,348)
2. **Trần với tới 17.9%** — entity-star chỉ chạm 106,340/593,433 cặp
3. **Baseline 6 luật** áp đảo mọi phương án mining đã thử
4. **Phân biệt $I > 0$ vs lãi quyết định $\approx 0$** — đặc trưng hoá vì sao port thất bại
5. **Đồ thị + normaliser + nhật ký 16 thí nghiệm** như một resource

Ba điều **không** nên tuyên bố: rằng mining tìm được constraint hữu ích; rằng hyperedge cải
thiện dự đoán; rằng phát hiện được conflict trong gold (chỉ có **72** cái, EXP6 xác nhận
trùng khớp con số đo độc lập trước đó).
