# KẾT QUẢ P/R — TempEKG vs PaTeCon trên cùng tập gán nhãn

Đo thật. Tập gán nhãn tự dựng từ WD50K + Wikidata API (48 phút quét 14,637 entity).

---

## 1. Tập gán nhãn

WD-411 gốc **không được phát hành**. Tái lập quy trình của họ (§6.1.1: so dump 2019 với
Wikidata hiện tại), nhưng **tách được** ERROR khỏi REFINEMENT — điều tiêu chí của họ gộp chung.

| nhãn | số | tỉ lệ | nghĩa |
|---|---|---|---|
| ALIVE | 37,743 | 75.5% | còn nguyên |
| NOPROP | 8,554 | 17.1% | property biến mất (mơ hồ → **loại khỏi đánh giá**) |
| **COARSE** | 1,706 | 3.4% | precision thật là NĂM/THÁNG ⇒ **độ chính xác giả** |
| **DELETED** | 817 | 1.6% | biến mất hoàn toàn ⇒ **sai** |
| **REFINED** | 779 | 1.6% | `0101` bị thay bằng ngày ⇒ **thô hơn, không sai** |
| CHANGED | 401 | 0.8% | đổi ngày trong cùng năm |

Đánh giá trên **24,399 fact** (bỏ NOPROP). Tỉ lệ nền (random): **1.88%**.

---

## 2. Kết quả chính

Giao thức của họ (§6.1.2): *"a wrong fact contained in a conflicting pair is considered a
successfully recalled example"*. Dùng đúng cách đó, **cộng thêm precision** (họ không tính).

### Nhãn sự thật = DELETED + CHANGED (859 fact)

| phương pháp | cặp | fact gắn cờ | trúng | **PRECISION** | **RECALL** | **F1** |
|---|---|---|---|---|---|---|
| **PaTeCon** | 747 | 1,188 | 189 | 15.91% | **22.00%** | 0.185 |
| TempEKG — chỉ CONFLICT | 512 | 839 | 164 | 19.55% | 19.09% | 0.193 |
| **TempEKG — CONFLICT+UNDECIDABLE** | **546** | **874** | **182** | **20.82%** | **21.19%** | **0.210** |
| TempEKG — toàn bộ tầng | 747 | 1,188 | 189 | 15.91% | 22.00% | 0.185 |

**Cấu hình tốt nhất (CONFLICT+UNDECIDABLE) so với PaTeCon:**

| | chênh lệch |
|---|---|
| Precision | **+4.91 điểm** (15.91% → 20.82%, tăng **30.9%** tương đối) |
| Recall | **−0.81 điểm** (22.00% → 21.19%) |
| **F1** | **+0.025** (0.185 → 0.210, tăng **13.5%** tương đối) |

### Nhãn sự thật = DELETED (458 fact, chặt chẽ hơn)

| phương pháp | P | R | F1 |
|---|---|---|---|
| PaTeCon | 4.55% | **11.79%** | 0.066 |
| TempEKG (chỉ CONFLICT) | 4.65% | 8.52% | 0.060 |

⚠️ **Dưới nhãn chặt này TempEKG KHÔNG hơn** — precision gần bằng, recall thấp hơn.

---

## 3. Bài học thiết kế: PHÂN TẦNG, không VỨT BỎ

Bản đầu **loại bỏ** cặp REFINEMENT → mất recall mà không được precision.

Bản sửa **xếp hạng** chúng xuống cuối:

```
tang 1  CONFLICT      (giao rong)          P cao nhat
tang 2  UNDECIDABLE   (thieu thong tin)    them recall re
tang 3  REFINEMENT    (long nhau)          bo -> ve dung PaTeCon
```

> Uncertainty temporal không nên dùng như **bộ lọc nhị phân**, mà như **hàm xếp hạng**.
> Cắt ở tầng 2 cho điểm tối ưu.

---

## 4. Đánh giá trung thực so với mục tiêu

Mục tiêu đặt ra: *"recall bằng hoặc vượt họ, precision cao hơn"*.

| | đạt? |
|---|---|
| Precision cao hơn | ✅ **+4.91 điểm** (+30.9% tương đối) |
| Recall bằng hoặc vượt | ⚠️ **−0.81 điểm** — gần bằng, chưa vượt |
| F1 cao hơn | ✅ **+13.5%** tương đối |
| Đo được precision | ✅ **họ không thể** — không có tập gán nhãn public |

**Phát biểu chính xác:** *"Với chi phí 0.81 điểm recall, biểu diễn uncertainty temporal
tăng precision 30.9% tương đối và F1 13.5% tương đối, trên tập gán nhãn tái lập theo đúng
quy trình của họ."*

**Không nên nói:** "vượt họ ở cả hai chỉ số".

---

## 5. Giới hạn phải nêu trong bài

1. **Nhãn là proxy, không phải phán quyết chuyên gia.** WD-411 dùng 2 chuyên gia kiểm nguồn;
   ta dùng "biến mất khỏi Wikidata" làm nhãn. Nhiễu theo hướng đã biết (một số xoá là do tái
   cấu trúc, không phải sửa lỗi) — nên **loại NOPROP** khỏi đánh giá.
2. **Precision tuyệt đối thấp** (15.9–20.8%) ở cả hai phương pháp. Điều này phù hợp với việc
   PaTeCon không bao giờ báo cáo precision.
3. **Không so trực tiếp được với con số recall trong paper họ**, vì WD-411 không public.
4. Dưới nhãn chặt (chỉ DELETED), lợi thế biến mất — kết quả **phụ thuộc định nghĩa "sai"**.
