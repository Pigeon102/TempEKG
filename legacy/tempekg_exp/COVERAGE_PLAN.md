# Kế hoạch bao phủ ĐẦY ĐỦ 5 loại temporal conflict

Yêu cầu: phải giải quyết **cả** T5 granularity và T4 (họ không xử lý) **lẫn** các loại
họ có xử lý. Kèm **lý do** cho từng việc.

---

# 1. Bảng bao phủ

| | PaTeCon | Framework này | Vì sao cần |
|---|---|---|---|
| **T1** representation `start>end` | ✅ loại trước khi mine | ✅ **giữ làm chỉ số riêng** | 2.3–3.7% dữ liệu của họ. Họ **vứt đi**; ta **báo cáo** — đó là tín hiệu chất lượng dữ liệu |
| **T2** mutual exclusion | ✅ | ✅ **phải cài** | **87% conflict của họ** là loại này. Không cài thì recall không thể bằng họ |
| **T3** ordering | ✅ | ✅ đã có | lõi chung, để so sánh trực tiếp |
| **T4** disjointness | ⚠️ **chỉ cùng property + cùng chủ thể** | ✅ **mở rộng** | họ tự khai báo bỏ 2 nhánh (§3.2) |
| **T5** granularity | ❌ **không có, không nhắc** | ✅ **mới hoàn toàn** | 13.35% dữ liệu **của họ**, 49× mức ngẫu nhiên |

---

# 2. Từng loại: làm gì và VÌ SAO

## T1 — REPRESENTATION

**Làm:** kiểm $t.s > t.e$ trên mọi fact; báo cáo tỉ lệ thay vì lặng lẽ xoá.

**Vì sao cần:**
- PaTeCon loại **1,166/50,000 (2.33%)** fact rồi **không bao giờ nhắc lại**. Đó là conflict
  đã phát hiện nhưng không được tính vào kết quả.
- Rẻ nhất trong 5 loại: **không cần constraint nào**, chỉ đọc 1 fact.
- Cho một cột so sánh miễn phí giữa hai substrate.

**Chi phí:** ~0.5 ngày.

## T2 — MUTUAL EXCLUSION

**Làm:** mine constraint dạng $\textsf{false} \leftarrow (x,p,y,t_1),(x,p,z,t_2), y\ne z$.

**Vì sao cần — đây là lý do quan trọng nhất về recall:**

| | |
|---|---|
| Tỉ trọng trong conflict của PaTeCon | **87.2%** (715/820) |
| Framework hiện tại có không | ❌ |

> **Không cài T2 thì recall KHÔNG THỂ bằng họ**, vì gần 9/10 cái họ bắt được thuộc loại này.
> Đây là điều kiện tiên quyết cho mục tiêu "recall ≥ họ".

**Lưu ý cho MAVEN:** MAVEN **không lưu giá trị thuộc tính lặp** nên T2 dạng Wikidata không
tồn tại. Nhưng có **dạng tương ứng**: một event không thể có hai anchor TIMEX mâu thuẫn —
và đó chính là **cầu nối sang T5**.

**Chi phí:** 1.5 ngày (Wikidata) + gộp vào T5 (MAVEN).

## T3 — ORDERING

**Làm:** đã có. Giữ nguyên, thêm Wilson + FDR.

**Vì sao vẫn cần:** là **lõi chung** để so sánh trực tiếp hai phương pháp trên cùng thước.
Không có nó thì không có điểm neo.

**Chi phí:** đã xong.

## T4 — DISJOINTNESS (mở rộng vượt họ)

**Họ bỏ gì — trích nguyên văn:**

> *"the disjointness between a pair of time intervals with **different properties** is
> trivial, so we only consider the case of the same property"* — §2.3

> *"to keep the search manageable, **we do not extract the disjointness relationships
> between different subjects**"* — §2.4

**Làm:** mở rộng 2 nhánh họ bỏ:
- **T4a khác property**: $(x,p_1,y,t_1),(x,p_2,z,t_2)$ — vd không thể vừa bị giam vừa thi đấu
- **T4b khác chủ thể**: $(x,p,y,t_1),(z,p,y,t_2)$ — vd một đội không thể có 2 HLV trưởng cùng lúc

**Vì sao cần:**
- Họ nói nhánh khác-property là *"trivial"* nhưng **không chứng minh**. Trên MAVEN nó
  **không trivial**: một Person có thể vừa là `Killing#Victim` vừa là `Employment#Patient`,
  và hai cái đó **không thể** chồng thời gian.
- Nhánh khác-chủ thể họ bỏ vì **chi phí tính toán**, không phải vì vô nghĩa. Với bảng phẳng
  + index của mình (mining 0.04s) chi phí đó **không còn là vấn đề**.
- ⚠️ **Cạm bẫy đã đo**: đo thô cho 30.2% cặp chồng nhau — nhưng phần lớn **hợp lệ**
  (cầu thủ ở CLB + đội tuyển). **Bắt buộc** dùng confidence + Wilson để lọc, đúng như
  PaTeCon làm với `P54 disjoint` (conf 0.68 → loại).

**Chi phí:** 2 ngày.

## T5 — GRANULARITY (hoàn toàn mới)

**Làm:** ba dạng con.

| | Định nghĩa | Trên Wikidata | Trên MAVEN |
|---|---|---|---|
| **T5a** giá trị thô hơn khoảng bao nó | $\text{prec}(O) < \text{prec}(T)$ | đo được | cần normaliser |
| **T5b** độ chính xác giả | `YYYY0101`, `YYYY0000` | **13.35%**, 49× | — |
| **T5c** anchor mâu thuẫn | $\bigcap_i T_i = \emptyset$ | — | **17,102 event có ≥2 anchor** |

**Vì sao cần — novelty lớn nhất:**

1. **PaTeCon không nhắc tới một lần nào.** Không phải họ làm dở, mà là **loại này nằm ngoài
   khung của họ**: cả 3 họ constraint đều thao tác trên *khoảng*, còn T5 là về *độ chính xác
   của chính khoảng đó*.
2. **Phổ biến hơn ordering 20–50 lần** ngay trên dữ liệu của họ (13.35% vs 0.24–0.58%).
3. **Bằng chứng không phụ thuộc MAVEN** — đến từ dữ liệu gốc của bài mình kế thừa, nên
   reviewer không thể bác bằng "anh chọn dataset thuận lợi".
4. `FuzzyTime` của họ **dung thứ** granularity khi so sánh (trả `unknown`), nhưng **không
   phát hiện** granularity bị khai man. Đây là phân biệt cốt lõi phải nêu rõ trong bài.

**Chi phí:** T5b trên Wikidata ~1 ngày (đã đo xong). T5c trên MAVEN cần **normaliser ~1 tuần**.

---

# 3. Lý do cho từng mục trong danh sách việc

| # | Việc | **VÌ SAO CẦN** | Chặn cái gì | Chi phí |
|---|---|---|---|---|
| 1 | **Held-out source precision** | PaTeCon **về cấu trúc không thể** đo precision (Wikidata 1 nguồn/fact). MAVEN có **81.8% cặp ≥2 nguồn**. Đây là con số duy nhất họ không thể đối chiếu | toàn bộ tuyên bố "precision cao hơn" | 2 ngày |
| 2 | **T2 mutual exclusion** | **87.2%** conflict của họ thuộc loại này. Thiếu nó thì recall **không thể** bằng | mục tiêu "recall ≥ họ" | 1.5 ngày |
| 3 | **T4 mở rộng** | họ **tự khai báo bỏ** 2 nhánh; một nhánh bỏ vì chi phí mà mình đã giải quyết (0.04s) | tuyên bố "bao phủ rộng hơn" | 2 ngày |
| 4 | **TIMEX normaliser** | T5c trên MAVEN **bị chặn hoàn toàn** nếu không có. 62.1% regex + reference-time propagation | T5 trên MAVEN | ~1 tuần |
| 5 | **PaTeCon trên MAVEN** | cần cột đối chiếu trong bảng kết quả. **Xem §4 — có vấn đề** | bảng so sánh | xem §4 |
| 6 | **Mức C** (model TRE + sửa) | gold có 72 conflict; đồ thị **dự đoán** có **85,243**. Target lớn nhất | quy mô kết quả | ~2 tuần |

**Thứ tự đề xuất: 1 → 2 → 3 → 4 → 6.** Mục 1 trước vì nó không phụ thuộc gì cả và tạo ra
con số khác biệt nhất.

---

# 4. Ước lượng: PaTeCon trên MAVEN bao giờ xong?

## Câu trả lời: **với bản chiếu đầy đủ, KHÔNG BAO GIỜ**

Nút thắt ở `Mutiple_Entity_Temporal_Order` (SP(b)), dòng 736–752:

```python
for i in range(len(temporalRelationList)):        # |R_t|
    for j in range(len(relationList)):            # |R|
        for k in range(len(temporalRelationList)):# |R_t|
```

Độ phức tạp **bậc ba theo số property**: $O(|R_t|^2 \cdot |R|)$.

| dataset | $\lvert R\rvert$ | số entry index | RAM ước tính | kết quả **đã đo** |
|---|---|---|---|---|
| WD50K | **6** | 216 | ~0 | ✅ xong trong **1.1 s** |
| MAVEN `EventType#Role` | **459** | **96,702,579** | **~40.6 GB** | ❌ **quá 30 phút chưa xong, bị timeout giết** |
| MAVEN `EventType` | **151** | 3,442,951 | ~1.4 GB | ✅ xong ~**3 phút**, 348 constraint / 535 conflict |

**Bằng chứng cho dòng giữa:** log dừng ngay sau khi in danh sách 459 property (thứ in ra
*trước* giai đoạn mining), và **không file kết quả nào được tạo**. `timeout 1800` giết tiến
trình. (Lưu ý đọc log: `exit code 0` là của lệnh cuối trong chuỗi shell, **không phải** của
`Constraint_Mining.py`.)

Phát biểu chính xác: **PaTeCon chạy quá 30 phút mà chưa qua nổi giai đoạn dựng index trên
MAVEN với vocabulary đầy đủ, trong khi WD50K xong trong 1.1 giây** — chênh lệch ít nhất
**1,600×**. Không khẳng định "không bao giờ xong", chỉ khẳng định vượt xa mọi ngưỡng thực dụng.

## Vì sao — và đây là một phát hiện kỹ thuật thật

> **Chiếu đồ thị event sang nhị phân làm nổ property vocabulary từ 6 lên 459.**
> KG thực thể có ít property (Wikidata temporal: 6, WD27M: 93). Đồ thị event chiếu ra
> `EventType#Role` cho **459** — gấp **76×**. Với thuật toán bậc ba, đó là **44,000×** công việc.

Đây là lý do kỹ thuật, có số, để **không** chiếu sang nhị phân — bổ sung cho lý do lý thuyết
(Mệnh đề 2, MODEL.md) rằng chiếu làm mất pattern $K_{2,2}$.

## Cách lấy được cột đối chiếu

| Cách | Vocabulary | Khả thi | Đánh đổi |
|---|---|---|---|
| `EventType#Role` | 459 | ❌ 40 GB | — |
| **`EventType`** | **151** | ✅ **đang chạy** | mất thông tin vai |
| chỉ `Role` | 143 | ✅ | mất thông tin loại event |
| tắt SP(b) | 459 | ✅ | mất pattern 2 chủ thể |

**Đang chạy bản `EventType`.** Nếu xong, ta có cột PaTeCon-trên-MAVEN cho bảng so sánh, kèm
chú thích rõ là **bản rút gọn vocabulary** — và bản thân việc phải rút gọn **chính là một
kết quả**.
