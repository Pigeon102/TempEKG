# Ba lời giải đã cài và kiểm chứng

Cài xong mục 3 (uncertainty temporal) và mục 6 (sự kiện định kỳ). Mục 1 đang chạy nền.

---

# 1. UNCERTAINTY TEMPORAL — lời giải gốc cho T5

## Vấn đề

PaTeCon biểu diễn thời gian bằng **điểm** `YYYYMMDD`. "Năm 1638" bị pad thành `16380101`,
không phân biệt được với "ngày 1/1/1638". Hậu quả đo được: 57.3% giá trị kết thúc `0101`
(209× mức ngẫu nhiên), 25.5% conflict thuộc mẫu thô-vs-mịn.

## Lời giải: KHOẢNG + ĐỘ CHÍNH XÁC

```
"nam 1638"    ->  [1638-01-01, 1638-12-31]  gran=year
"1/1/1638"    ->  [1638-01-01, 1638-01-01]  gran=day
"2/12/1638"   ->  [1638-12-02, 1638-12-02]  gran=day
```

Với giá trị `YYYY0101` **không biết precision**, gán `gran='suspect_year'` — **không khẳng
định là ngày**. Cơ sở: 57.3% vs kỳ vọng 0.27%, tức 209×.

Vị từ trả về **ba giá trị** (giữ tinh thần `FuzzyTime`): `TRUE` / `FALSE` / `UNKNOWN`.
`disjoint` chỉ trả `FALSE` khi **cả hai** đều chính xác đến ngày.

## Kết quả trên chính 747 conflict của PaTeCon

| | số | tỉ lệ |
|---|---|---|
| **CONFLICT thật** (giao rỗng) | **512** | 68.5% |
| **REFINEMENT** (một cái làm mịn cái kia) | **201** | **26.9%** |
| UNDECIDABLE | 34 | 4.6% |

**Giảm 747 → 512 (−31.5%).**

```
REFINEMENT (GIA):
   16380101 -> [1638-01-01..1638-12-31] suspect_year
   16381202 -> [1638-12-02..1638-12-02] day          -> LONG NHAU

CONFLICT (THAT):
   19180411 -> [1918-04-11..1918-04-11] day
   19180412 -> [1918-04-12..1918-04-12] day          -> HAI NGAY KHAC NHAU
```

Ước lượng bằng pattern-matching trước đó là 25.5%; cách nguyên tắc cho **26.9%** — nhất quán,
xác nhận chéo.

**File:** `uncertain_time.py`, `exp27_uncertain_fix.py`

---

# 2. SỰ KIỆN ĐỊNH KỲ — lời giải cho vấn đề bạn nêu

## Vấn đề

Hội thảo thường niên, giải đấu hàng năm: cùng entity, cùng loại event, thời gian khác nhau
→ **không phải lỗi**. PaTeCon gắn cờ hết. Ngưỡng thô "≥3 năm" của bản trước chưa đủ.

## Lời giải: phân loại theo CẤU TRÚC chuỗi thời điểm

| nhãn | tiêu chí | hợp lệ? |
|---|---|---|
| `PERIODIC` | ≥3 mốc, khoảng cách **đều** (độ lệch ≤0.5) | ✅ |
| `CONTINUOUS` | các mốc **liên tiếp** từng năm | ✅ sự kiện kéo dài |
| `RECURRING` | khoảng cách nhỏ nhất ≥ **ngưỡng học riêng theo loại event** | ✅ |
| `SUSPECT` | cùng năm khác giá trị, hoặc cách gần dưới ngưỡng | ⚠️ đáng ngờ |

## Kết quả trên MAVEN (346 cặp đa-mốc)

| nhãn | số | tỉ lệ |
|---|---|---|
| RECURRING | 212 | 61.3% |
| CONTINUOUS | 112 | 32.4% |
| PERIODIC | 11 | 3.2% |
| **SUSPECT** | **11** | **3.2%** |

**Hợp lệ 96.8%.** So với ngưỡng thô 3 năm (203 đáng ngờ) → còn **11**, **giảm 18×**.

```
[PERIODIC  ] Verification        [2010, 2012, 2013]   gan deu, TB 1.5 nam
[CONTINUOUS] Military_operation  [1779, 1780]         lien tiep
[RECURRING ] Social_event        [2006, 2012, 2014, 2016]
[SUSPECT   ] Sending             [1642, 1644]         cach gan, dang ngo
```

Đây **chính là future work PaTeCon tuyên bố** (§8): *"predicates can be broadened to
encompass quantitative relationships, such as $t_2 - t_1 \le 10$ years... Future work"*.

**Điểm yếu còn lại:** ngưỡng học được đều ra 1 (phân vị 10% quá thấp). Phần lớn công việc
do `CONTINUOUS` gánh. Cần chỉnh phân vị hoặc dùng ước lượng khác.

**File:** `recurrence.py`

---

# 3. TẬP GÁN NHÃN WD50K — đang chạy

Quét toàn bộ 14,637 entity của WD50K qua Wikidata API, gán 6 nhãn:

| nhãn | nghĩa |
|---|---|
| `ALIVE` | còn nguyên, khớp chính xác |
| `COARSE` | precision thật là NĂM/THÁNG ⇒ **độ chính xác giả trong dataset** |
| `REFINED` | `0101` bị thay bằng ngày chính xác ⇒ **thô hơn, không sai** |
| `CHANGED` | đổi ngày trong cùng năm ⇒ nghi ngờ |
| `DELETED` | biến mất hoàn toàn ⇒ **ứng viên SAI** |
| `NOPROP` | entity/property không còn |

Trên mẫu 598 fact: DELETED 19.1%, NOPROP 13.4%, REFINED 2.3%.

> **Tập này TỐT HƠN WD-411** vì tách được `DELETED` (sai thật) khỏi `REFINED`/`COARSE`
> (thô hơn) — điều mà tiêu chí "fact bị xoá = fact sai" của họ **gộp chung**.
> Và **không cần chuyên gia**, vì trường `precision` của Wikidata là nhãn vàng có sẵn.

**File:** `scan_wd50k.py` → `patecon_data/wd50k_labeled.tsv`

---

# 4. Tác động tổng hợp lên kết quả của PaTeCon

| | PaTeCon gốc | Sau khi sửa |
|---|---|---|
| Conflict trên WD50K | **747** | **512** (−31.5%) |
| Conflict mutual-exclusion | 715 | 488 |
| Cảnh báo sự kiện lặp lại trên MAVEN | 487 (gắn cờ hết) | **11** (−97.7%) |
| Kiểm soát FDR | ❌ | ✅ 34.7% → 0% |
| Đo precision | ❌ không thể | ✅ held-out source |

## Còn lại

| # | Việc | Trạng thái |
|---|---|---|
| 1 | Quét WD50K | 🔄 **đang chạy**, ~15 phút |
| 2 | Chạy PaTeCon + TempEKG trên tập đó, đo P/R | ⏳ chờ mục 1 |
| 4 | Normaliser lên mức ngày/tháng → mở khoá T4 | ⏳ ~1 tuần |
| 5 | Mức C: model TRE + tầng sửa | ⏳ ~2 tuần |
