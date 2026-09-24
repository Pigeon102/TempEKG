# TempEKG — Thiết kế cuối: đồ thị và thuật toán mining

Tổng hợp EXP1–23. **Mọi số là đo thật trên MAVEN-Arg + MAVEN-ERE và WD50K.**

---

# 1. Bao phủ 5 loại conflict — kết quả THẬT

| | PaTeCon (WD50K) | TempEKG (MAVEN) | Ghi chú |
|---|---|---|---|
| **T1** representation | 1,166 (2.33%) | **không áp dụng** | MAVEN không lưu interval tường minh |
| **T2** mutual exclusion | 715 conflict | **203** sau lọc lặp lại | 487 thô → loại 284 (58.3%) là **lặp lại hợp lệ** |
| **T3** ordering | 105 conflict | **72** | xác nhận độc lập 2 lần |
| **T4** disjointness | 0 giữ lại (conf 0.68 < 0.9) | **0** | ❌ **granularity quá thô** — xem §2 |
| **T5** granularity | **0 — không có cơ chế** | **336** đáng tin | 6.30% event multi-anchor |

---

# 2. T4 KHÔNG làm được trên MAVEN — và lý do là dữ liệu, không phải thuật toán

Đã cài **cả hai nhánh PaTeCon tự khai báo bỏ**:

| nhánh | cặp xét | chồng nhau | constraint giữ lại |
|---|---|---|---|
| **T4a** khác property (§2.3 họ nói *"trivial"*) | 48,785 | **83.2%** | **0** |
| **T4b** khác chủ thể (§2.4 họ bỏ vì *chi phí*) | 17,984 | **88.5%** | **0** |

**Nguyên nhân:** anchor MAVEN chủ yếu ở mức **năm**. Hai event cùng năm → khoảng
`[YYYY-01-01, YYYY-12-31]` → **luôn chồng nhau**. Không thể thiết lập disjointness.

> **Kết luận trung thực:** PaTeCon bỏ T4a với lý do *"trivial"* mà không chứng minh. Ta
> chứng minh được — nhưng kết quả là **họ đúng về mặt hiệu quả, sai về mặt lý lẽ**. Trên
> MAVEN nó không trivial mà **không đo được**, vì thiếu độ chính xác thời gian.
>
> T4 cần anchor ở mức **ngày/tháng**. Đó là điều kiện tiên quyết, không phải vấn đề thuật toán.

---

# 3. T5 GRANULARITY — đóng góp mới, có kiểm soát nhiễu

## 3.1 Kết quả

17,102 event có ≥2 anchor. Sau chuẩn hoá (độ phủ **75.7%**):

| verdict | số | tỉ lệ |
|---|---|---|
| REFINEMENT (lồng nhau, hợp lệ) | 7,460 | 88.9% |
| **CONFLICT (giao rỗng)** | **933** | **11.1%** |
| UNDECIDABLE | 8,709 | 50.9% tổng |

## 3.2 Tự kiểm nhiễu — bắt buộc

Tách theo cách anchor được chuẩn hoá:

| nhóm | CONFLICT | tỉ lệ |
|---|---|---|
| **regex thuần** (đáng tin) | **336** | **6.30%** |
| có reference-propagation | 597 | **19.51%** |

Nhóm refprop có tỉ lệ conflict **gấp 3×**. Chênh lệch đó gần chắc là **lỗi normaliser**, không
phải lỗi annotation — ví dụ `"April 30"` bị gán vào 1861 ở event này và 1863 ở event kia.

> **→ Con số báo cáo được là 336 (6.30%), không phải 933.** Tự lọc nhiễu là bắt buộc, và
> chính việc đo được tỉ lệ nhiễu này là một đóng góp phương pháp.

Đối chiếu Wikidata: 13.35% giá trị day-precision là `01-01` (49× mức ngẫu nhiên). Hai cơ chế
khác nhau (khai man độ chính xác vs anchor mâu thuẫn) nhưng **cùng bậc độ lớn**, và **PaTeCon
không phát hiện được cái nào**.

---

# 4. THIẾT KẾ ĐỒ THỊ

## 4.1 Nguyên tắc: cấu trúc suy ra từ yêu cầu đo lường

| Yêu cầu | Hệ quả cấu trúc |
|---|---|
| Đo precision không cần annotate | `source` phải nằm trong **khoá chính** để hold-out |
| Bậc event trung bình 1.11 → 2.84 | ❌ không cần hypergraph engine — **bảng phẳng** |
| causal/subevent sâu 1, closure +0.2–0.5% | ❌ không cần adjacency — **bảng cạnh** |
| 0/68,348 entity vượt document | ❌ không có tầng cross-document |
| T5 cần độ chính xác | interval phải mang **granularity + phương pháp chuẩn hoá** |
| PaTeCon $O(\lvert R_t\rvert^2\lvert R\rvert)$ nổ ở 459 property | ❌ **không chiếu** sang nhị phân |

## 4.2 Schema

```sql
-- NODE
events(event_id PK, doc_id, type, sent_id, char_start, char_end)
entities(entity_id PK, doc_id, ent_type)          -- doc-local, cho san ca blind test
timex(timex_id PK, doc_id, surface, sent_id,
      norm_lo, norm_hi, granularity,               -- day|month|year|decade|century|duration
      norm_method ENUM('regex','refprop','gazetteer','none'))   -- <-- BAT BUOC cho §3.2

-- HYPEREDGE phang hoa
args(event_id, role, filler_id, filler_kind, link_conf)

-- KHOANG THOI GIAN SUY RA
intervals(event_id PK, lo, hi, granularity,
          source_anchors JSON, all_regex BOOLEAN)  -- all_regex = co dang tin khong

-- RANG BUOC, TACH THEO NGUON   <-- diem cot loi
constraint_edge(
   doc_id, e1, e2,
   source   ENUM('S1_temporal','S2_causal','S3_subevent','S4_closure','S5_mined'),
   implied  VARCHAR,
   strength ENUM('hard','soft'),
   conf     FLOAT,
   PRIMARY KEY (doc_id, e1, e2, source)
)
```

Hai cột **không thể bỏ**:
- `constraint_edge.source` trong PK → cho phép held-out precision (§5)
- `timex.norm_method` → cho phép tách nhiễu normaliser (§3.2). Không có nó thì báo cáo 933
  thay vì 336, tức **sai 2.8×**.

## 4.3 Hiệu năng (đo, EXP10)

| | build | mining | incremental |
|---|---|---|---|
| on-the-fly | 0.00s | 0.36s | — |
| inverted index | 0.04s | 0.19s | 0.01 ms/doc |
| **materialized pairs** | 0.20s | **0.04s** | **0.03 ms/doc** |

Ba thiết kế cho **cùng** 11,817 signature (đã kiểm chứng bằng nhau).

---

# 5. THUẬT TOÁN MINING

## 5.1 Điều số liệu bắt phải thay đổi

Held-out source evaluation (giao thức PaTeCon không chạy được):

| | số cặp |
|---|---|
| S5 (mine thống kê) gắn cờ | 4,874 |
| S2/S3/S4 (cứng) gắn cờ | 14 |
| **giao nhau** | **0** |
| **precision của S5** | **0.00%** |

> **Constraint mine bằng thống kê KHÔNG phát hiện lỗi thật.** Giao nhau bằng 0 tuyệt đối.
> Xác nhận EXP13–15 bằng giao thức sạch nhất.

## 5.2 Thuật toán cuối

```
GIAI DOAN 1 — RANG BUOC CUNG (khong mine, suy tu ngu nghia)
   subevent(e1,e2)  => contains(t1,t2)          precision ~100% theo cau tao
   CAUSE(e1,e2)     => not after(t1,t2)
   closure          => bac cau
   -> phat hien 72 conflict, xac nhan doc lap 2 lan

GIAI DOAN 2 — T5 GRANULARITY (khong mine, kiem tra giao)
   event co >=2 anchor -> giao cac khoang
   giao rong => CONFLICT   |  long nhau => REFINEMENT
   CHI tinh khi tat ca anchor la regex thuan   <- loc nhieu bat buoc
   -> 336 conflict dang tin

GIAI DOAN 3 — T2 CO XET LAP LAI
   ung vien mutual exclusion
   LOAI neu cac lan xay ra cach >=3 nam  (58.3% bi loai)
   -> 203 con lai

GIAI DOAN 4 — CONSTRAINT MEM  [KHONG dung de phat hien]
   mine (T1,T2) -> quan he, voi Wilson_lo >= 0.7 + BH-FDR q <= 0.05
   dem support theo DOCUMENT
   DUNG DE: mo ta quy luat, khong dung de gan co conflict (precision 0%)
```

## 5.3 So sánh với PaTeCon

| | PaTeCon | TempEKG |
|---|---|---|
| Nguồn constraint | **chỉ tần suất** | tần suất **+ ngữ nghĩa quan hệ** |
| Ngưỡng | điểm ước lượng ≥0.9 | **cận dưới Wilson** |
| Kiểm soát bội | ❌ | **BH-FDR** (34.7% → 0%) |
| Đơn vị support | cặp | **document** |
| Held-out validation | ❌ | ✅ 86.1% |
| **Đo precision** | ❌ **không thể** | ✅ **held-out source** |
| Lặp lại hợp lệ | ❌ gắn cờ hết | ✅ lọc 58.3% |
| T5 granularity | ❌ | ✅ 336 |

---

# 6. Trạng thái so với mục tiêu đặt ra

| Mục tiêu | Kết quả |
|---|---|
| Recall ≥ PaTeCon | ⚠️ **không so được** — chưa có tập gán nhãn kiểu WD-411 cho MAVEN |
| Precision đo được | ✅ **làm được, họ không thể** |
| Precision cao hơn | lớp **mềm 0%** · lớp **cứng ~100%** → **phải dùng lớp cứng** |
| Bao phủ T1–T5 | T1 n/a · T2 ✅ · T3 ✅ · T4 ❌ (granularity) · T5 ✅ |

## Đóng góp đứng vững

1. **Giao thức held-out source** — đo precision không cần annotate; PaTeCon về cấu trúc
   không thể (Wikidata 1 nguồn/fact, MAVEN **81.8%** cặp ≥2 nguồn)
2. **T5 granularity** — 336 trên MAVEN, 13.35% trên chính dữ liệu của họ; họ **không nhắc tới**
3. **Xử lý sự kiện lặp lại** — 58.3% cảnh báo mutual exclusion là hợp lệ; đúng future work họ để ngỏ
4. **Kết quả âm tính có kiểm soát** — mining thống kê precision 0% so với chuẩn cứng
5. **Giới hạn scale của PaTeCon** — $O(\lvert R_t\rvert^2\lvert R\rvert)$, 459 property → >30 phút
   vs WD50K 1.1 giây

## Việc còn lại

| # | Việc | Vì sao |
|---|---|---|
| 1 | Tập gán nhãn kiểu WD-411 cho MAVEN (~300 mục, 3 person-day) | **điều kiện duy nhất** để so recall với họ |
| 2 | Nâng normaliser lên mức ngày/tháng | mở khoá **T4**, giảm nhiễu T5 từ 3× xuống |
| 3 | Mức C: model TRE + tầng sửa | target 85,243 vi phạm trên đồ thị dự đoán |
