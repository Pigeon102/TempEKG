# Kiểm chứng trên WD27M — dataset thứ hai

**Kết quả: hướng đúng, biên độ rất nhỏ, và một thành phần KHÔNG tổng quát hoá.**

---

# 1. Thiết lập

| | |
|---|---|
| Nguồn | `WD27M.tsv` chính thức (1.05 GB) từ Google Drive của họ |
| Mẫu | 12,000 entity **không trùng** WD50K → 21,078 fact |
| Property | 6 (giữ chung với WD50K để so công bằng) |
| Gán nhãn | Wikidata API, 21 phút |

## ⚠️ Lỗi format bắt được (lỗi thứ TƯ cùng loại)

Lần chạy đầu cho **CHANGED 72.6%** — so với 0.8% trên WD50K, chênh **90×**.

Nguyên nhân: **WD27M dùng object dạng ISO, WD50K dùng dạng đóng gói**:

```
WD50K : Q23        P569 17320222                (dong goi)
WD27M : Q41599038  P569 1895-12-16 00:00:00Z    (ISO)
```

Bộ gán nhãn so `p[2]` với `18951216` → không khớp, nhưng tiền tố năm khớp → CHANGED.

Sau khi sửa parser hỗ trợ cả hai format:

| nhãn | WD27M | WD50K |
|---|---|---|
| ALIVE | 52.8% | 75.5% |
| **DELETED** | **17.8%** | 1.6% |
| COARSE | 9.3% | 3.4% |
| REFINED | 9.3% | 1.6% |
| CHANGED | **1.4%** | 0.8% |
| NOPROP | 9.3% | 17.1% |

WD27M có tỉ lệ DELETED cao hơn **11×** — mẫu phủ entity ít nổi tiếng hơn, bị dọn nhiều hơn.

---

# 2. Kết quả so sánh

| cấu hình | fact | trúng | **P** | **R** | **F1** |
|---|---|---|---|---|---|
| **PaTeCon** | 242 | 43 | 17.77% | 1.15% | 0.022 |
| phân tầng | 192 | 42 | 21.88% | 1.12% | 0.021 |
| phân tầng + `m00d00` | 192 | 42 | 21.88% | 1.12% | 0.021 |
| **+ định lượng** | 212 | 45 | **21.23%** | **1.20%** | **0.023** |

18,784 fact evaluable · **tỉ lệ nền 19.97%**

## Đọc kết quả trung thực

| | WD50K | WD27M |
|---|---|---|
| tỉ lệ nền | 3.06% | **19.97%** |
| PaTeCon R | 23.52% | **1.15%** |
| TempEKG − PaTeCon (P) | +5.53 | **+3.46** |
| TempEKG − PaTeCon (R) | +4.17 | **+0.05** |
| TempEKG − PaTeCon (F1) | +29.1% | **+4.5%** |

**Hướng nhất quán** (trội cả hai chỉ số ở cả hai dataset) nhưng **biên độ sụt mạnh**.

---

# 3. ⚠️ `m00d00` KHÔNG tổng quát hoá — giới hạn nghiêm trọng

| dataset | giá trị 8 chữ số | có `00` | `0101` | ngày thật |
|---|---|---|---|---|
| WD50K | 99,698 | **0 (0.00%)** | 57.3% | 42.7% |
| WD27M | 41,363 | **0 (0.00%)** | 38.9% | 61.1% |

**Cả hai đều không có `00` ở cột start/end.** Detector `m00d00` trên WD50K lấy `00` từ **cột
object** (nơi WD50K để nguyên dạng đóng gói). WD27M dùng ISO nên không có.

→ Trên WD27M, `m00d00` **bắn 0 lần** (192 → 192 fact).

> **Đây là giới hạn phải nêu rõ:** thành phần đóng góp recall lớn nhất trên WD50K
> (25.26% → 38.18% ở bản trước) là **phụ thuộc quy ước biểu diễn của một dataset cụ thể**,
> không phải tín hiệu ngữ nghĩa tổng quát.

**Cái tổng quát hoá được:**
- ✅ **Phân tầng uncertainty** — P +4.11 điểm trên WD27M (17.77% → 21.88%)
- ✅ **Ràng buộc định lượng** — thêm 20 fact, 3 trúng
- ❌ `m00d00` — 0 tác dụng

---

# 4. Vì sao recall thấp trên WD27M (1.15% vs 23.52%)

PaTeCon chỉ gắn cờ **242/18,784 fact** trong khi có **3,751 fact sai**. Lý do: mẫu WD27M lấy
entity ngẫu nhiên, phần lớn chỉ có **một** giá trị cho mỗi property → constraint cần ≥2 fact
không bắn được. Đúng điểm mù cấu trúc đã xác định (88% cái họ bỏ sót là đơn giá trị) — nhưng
ở WD27M tỉ lệ đó còn cao hơn.

---

# 5. Kết luận cho bài báo

## Được phép nói

- ✅ TempEKG trội PaTeCon **cả precision lẫn recall trên CẢ HAI dataset**
- ✅ **Phân tầng uncertainty** là thành phần tổng quát hoá được: P +5.53 (WD50K), +4.11 (WD27M)
- ✅ Ràng buộc định lượng tổng quát hoá được (biên độ nhỏ)

## KHÔNG được nói

- ❌ F1 +29.1% là con số chung → **chỉ đúng trên WD50K**; WD27M chỉ **+4.5%**
- ❌ `m00d00` là đóng góp phương pháp → **phụ thuộc format của một dataset**
- ⚠️ Recall của cả hai phương pháp trên WD27M đều **rất thấp** (~1%) — phải nêu

## Bài học

> Lỗi format là **lỗi thứ tư cùng loại** trong dự án (sau: nhãn loại trừ lẫn nhau, lift vs
> precision triển khai, ngày âm). Quy tắc bổ sung cho checklist AUDIT.md:
>
> **8. Trước khi chạy trên dataset mới, in ra 3 dòng đầu và so sánh format với dataset cũ.**
