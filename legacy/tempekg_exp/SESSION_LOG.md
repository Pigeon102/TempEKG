# Nhật ký phiên: normaliser triệt để, ràng buộc cứng, mining phủ định, audit

---

# 1. NORMALISER v2 — viết lại thay vì vá

## Cách làm

Thay vì vá từng lỗi, dump **toàn bộ 3,370 TIMEX chưa giải** của v1, phân loại thành **18 họ**,
xử lý hết trong một lần. File mới: `timex_norm2.py`.

| họ | ví dụ |
|---|---|
| H1 sự kiện có tên (25 mục) | `the seven years ' war`, `the napoleonic wars`, `the iraq war` |
| H2 trước Công nguyên | `40 bc` |
| H3–H5 modifier + thế kỷ/thập niên/năm | `the early 19th century`, `the late 1970s`, `mid-2012` |
| H7–H9 ngày/tháng/năm đầy đủ | `7 november 1778` |
| H10–H11 thiếu năm | `1 july`, `september`, `early september` |
| H12 thứ trong tuần (kể cả số nhiều) | `friday`, `saturdays` |
| H13 mốc tương đối theo ngày | `a few days later`, `hours later`, `16:00`, `midnight` |
| H14 mốc tương đối theo năm | `that year`, `the end of the year`, `spring 1945` |
| H14b–c | `the end of august`, `the first day` |
| H15 thời lượng thuần | `twelve hours`, `nearly a year`, `decades` |

## Ba cải tiến then chốt

**1. Truyền tham chiếu HAI LƯỢT.** v1 chỉ truyền xuôi, nên TIMEX tương đối xuất hiện *trước*
mốc tuyệt đối đầu tiên đều thất bại (cold-start). v2 quét lượt 1 tìm mốc tuyệt đối bất kỳ
trong tài liệu, dùng làm mốc mặc định cho lượt 2.
→ **88.8% → 90.3%**

**2. Cập nhật ref từ MỌI mốc giải được** (kể cả `refprop`), không chỉ `regex` — chuỗi tham
chiếu không bị đứt.

**3. Định lượng nhiều từ.** v1 dùng `(\w+)?` nên `"a few days"` (hai từ trước đơn vị) không
khớp. v2 cho phép `a|an` + `few|couple of|several|many`.

## Kết quả

| phiên bản | độ phủ |
|---|---|
| v1 ban đầu | 75.7% |
| v1 vá | 83.8% |
| v2 một lượt | 88.8% |
| v2 hai lượt | 90.3% |
| **v2 + vá cuối** | **91.3%** |

```
regex      13,880  66.6%
refprop     4,879  23.4%
gazetteer     256   1.2%
chua giai   1,812   8.7%   <- "later", "shortly", "night": mo ho THAT
```

## Tác động lên T5

| | v1 (75.7%) | **v2 (91.3%)** |
|---|---|---|
| kết luận được | 49.1% | **66.1%** |
| CONFLICT | 11.1% | 15.1% |
| **conflict đáng tin (regex thuần)** | **336** | **430** |
| chênh regex vs refprop | 3.1× | **3.3×** |

> ⚠️ **Giới hạn không giải được bằng độ phủ:** tỉ lệ nhiễu của reference-propagation
> **không giảm** (7.27% vs 23.75%, vẫn 3.3×). Suy diễn tham chiếu là **đoán**, và đoán sai
> gấp ~3 lần. Chỉ có thể *đánh dấu* nó (`norm_method`), không *sửa* được.

---

# 2. TẦNG SỬA BẰNG RÀNG BUỘC CỨNG — thất bại, lý do mới

| | precision | recall | F1 |
|---|---|---|---|
| gốc | 59.73% | 32.25% | 39.21% |
| sửa bằng confidence | 59.81% | 32.19% | 39.19% (−0.02) |
| **sửa bằng ràng buộc CỨNG** | 59.81% | 32.21% | **39.21% (−0.01)** |

**Lý do khác lần trước:** chỉ **12 cạnh** trong output model vi phạm ràng buộc cứng
(trên 51,644). Model đã tôn trọng ngữ nghĩa subevent/causal sẵn — **không có gì để sửa**.

Trước đó tôi cho rằng repair thất bại vì *chọn sai cạnh*. Thực tế: **không có cạnh sai để chọn**.

---

# 3. MINING PHỦ ĐỊNH — không đủ đất trên WD50K

Ý tưởng: mine constraint gần-tuyệt-đối (conf ≈ 1.0) rồi coi mọi vi phạm là sai.

| θ | số luật | fact | P | R | F1 |
|---|---|---|---|---|---|
| 1.000 | 0 | 0 | — | — | — |
| 0.99 | **1** | 38 | 13.16% | 0.67% | 0.013 |

Chỉ mine được **một** constraint: `P569→P570` (sinh trước chết), conf 0.9977.

**Nguyên nhân:** WD50K chỉ có **6 property**; sau khi lọc support ≥30 chỉ còn một cặp đồng
xuất hiện đủ nhiều. Hướng này **quy về đúng constraint `before` PaTeCon đã có**.

→ Cần vocabulary giàu hơn. WD27M có **93 temporal property** — đang chạy kiểm chứng.

---

# 4. AUDIT — hai nghi vấn đã giải quyết

## #7 precision 0.00%: **KHÔNG phải artifact** ✅

```
cap S5 xet         : 593,433
cap nguon CUNG xet : 493,209
CHONG LAN          : 489,071 = 82.4%
```

82.4% chồng lấn → hai detector cùng xét phần lớn cùng tập cặp nhưng gắn cờ khác hẳn.
Kết luận *"mining thống kê không phát hiện lỗi thật"* đứng vững.

## #11 latency 4.6×: **THIÊN VỊ, đã sửa** ⚠️

| phạm vi | PaTeCon | TempEKG | tỉ lệ |
|---|---|---|---|
| đầu-cuối (họ **mine**, ta dùng luật sẵn) | 2.002 s | 0.437 s | 4.6× — không công bằng |
| **chỉ phát hiện** | **0.819 s** | **0.415 s** | **2.0×** ✅ |

**Dùng 2.0×, không dùng 4.6×.**

---

# 5. Đang chạy

**WD27M** (12,000 entity, 6 property chung với WD50K, không trùng entity) — kiểm chứng
tổng quát hoá trên dataset thứ hai. `norm_time` **đã sửa xử lý ngày âm** trong script này.

Sau khi xong: chạy lại mining phủ định trên vocabulary 93 property.
