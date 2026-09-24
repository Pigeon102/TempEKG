# Còn lại gì, và những phát hiện tôi nghĩ cần làm

---

# 1. LATENCY trên WD50K (EXP32)

50,000 fact · 17,176 entity · 6 property. Lấy min của 3 lần chạy.

| giai đoạn TempEKG | thời gian |
|---|---|
| 1. Đọc dữ liệu | 0.022 s |
| 2. Dựng khoảng + granularity (100k giá trị) | 0.052 s |
| 3. Index (entity, property) | 0.009 s |
| **4. Phân tầng uncertainty** | **0.321 s** ← nút thắt (73%) |
| 5. Detector fact đơn giá trị | 0.010 s |
| 6. Ràng buộc định lượng | 0.023 s |
| **TỔNG** | **0.437 s** |

| | thời gian |
|---|---|
| **TempEKG (đầu-cuối)** | **0.437 s** |
| PaTeCon `Constraint_Mining.py` | 1.183 s |
| PaTeCon `Conflict_Detection.py` | 0.819 s |
| **PaTeCon tổng** | **2.002 s** |
| **TempEKG nhanh hơn** | **4.6×** |

Thông lượng TempEKG: **114,320 fact/giây**.

Nút thắt là phân tầng — $O(\sum_v d(v)^2)$ trên 1,023,672 cặp trong cùng (entity, property).
Có thể giảm bằng cách chỉ xét cặp mà PaTeCon đã gắn cờ, nhưng khi đó mất khả năng phát hiện
độc lập.

---

# 2. ⚠️ PHÁT HIỆN QUAN TRỌNG NHẤT: một lỗi đã suýt vào bài báo

## Sự việc

Detector `entity-obj` được báo cáo đạt **precision 24.67%**, đóng góp phần lớn mức tăng
recall (từ 25.26% lên 38.18%). Khi kiểm tra chéo, nó tách ra thành hai nhóm:

| nhóm | số | P(sai) | lift |
|---|---|---|---|
| object là entity `Q...` | 355 | **2.82%** | **0.8×** ← dưới tỉ lệ nền |
| ngày ÂM (trước CN) `-12000101` | 103 | **100.00%** | 28.4× |

100% là dấu hiệu đáng ngờ. Truy tiếp:

```python
def norm_time(t):
    return '%04d%02d%02d' % (int(t[1:5]), int(t[6:8]), int(t[9:11]))
#                                 ^^^^ voi "-0068-10-01" thi t[1:5]='0068'... nhung
#                                      dau tru lam lech het cac vi tri con lai
```

Kết quả: `-0068-10-01` bị chuyển sai, **không bao giờ khớp** với giá trị trong dataset
→ mọi fact BC bị gán nhãn `DELETED` **oan** → detector "đạt 100%".

## Tác động

| | trước sửa | sau sửa |
|---|---|---|
| P | 22.41% | **20.44%** |
| R | 38.53% | **27.69%** |
| F1 | 0.283 | **0.235** |
| so với PaTeCon | +53.5% | **+29.1%** |

Kết luận **vẫn đứng** (trội cả hai chỉ số), nhưng biên độ nhỏ hơn nhiều.

## Bài học

> **Precision 100% trên tập ≥100 mẫu gần như luôn là artifact.** Phải truy đến tận pipeline
> gán nhãn, không dừng ở việc nhìn con số đẹp.

Đây là lỗi thứ **ba** thuộc loại này trong dự án:
1. Đo lift bằng nhãn loại trừ lẫn nhau → ra 0.0×, suýt bỏ cả hướng T5
2. Lift 12.4× của `0101` nhưng precision triển khai chỉ 5.03%
3. **Ngày âm phá pipeline gán nhãn → precision giả 100%**

---

# 3. NHỮNG VIỆC TÔI NGHĨ CẦN LÀM

## 3.1 Bắt buộc trước khi viết bài

| # | Việc | Vì sao |
|---|---|---|
| A | **Kiểm chứng trên FB37M hoặc WD27M** | mọi kết quả hiện chỉ trên **một** dataset (WD50K). Không có bằng chứng tổng quát hoá |
| B | **Khoảng tin cậy cho chênh lệch P/R** | +5.53 điểm trên 744 fact sai — chưa biết có ý nghĩa thống kê không |
| C | **Sửa `norm_time` xử lý ngày âm** rồi tính lại | 150 fact hiện bị loại; sửa xong có thể dùng lại |
| D | **Ablation theo định nghĩa "sai"** | dưới nhãn chặt (chỉ DELETED) lợi thế từng biến mất — phải báo cáo cả hai |

## 3.2 Phát hiện đáng theo đuổi

| # | Phát hiện | Vì sao đáng |
|---|---|---|
| E | `m00d00` đạt **P 25.17%, lift 16.7×** | tín hiệu sạch nhất tìm được. Wikidata dùng `00` để nói "không rõ" — đây là **granularity được khai báo tường minh**, không phải suy đoán |
| F | **Tầng sửa mức C: −99.2% chu trình nhưng ΔF1 ≈ 0** | kết quả âm tính mạnh: *nhất quán ≠ chính xác*. Đáng viết thành một section |
| G | **PaTeCon $O(\lvert R_t\rvert^2\lvert R\rvert)$** | 6 property = 1.1s; 459 property >30 phút. Giới hạn scale chưa ai công bố |
| H | **57.3% giá trị trong data chính thức của họ kết thúc `0101`** | bằng chứng mạnh nhất, trên chính dữ liệu họ phát hành |

## 3.3 Không nên làm

| | vì sao |
|---|---|
| ❌ Đuổi theo T4 trên MAVEN | 88.1% cặp chồng nhau kể cả ở mức ngày — tính chất substrate |
| ❌ Mine thêm constraint thống kê | precision 0.00% so với chuẩn cứng, đã đo bằng held-out |
| ❌ Dùng detector `entity-obj` | lift 0.8×, dưới tỉ lệ nền |

---

# 4. QUAY LẠI MAVEN — trạng thái và việc tiếp

## Đã có trên MAVEN

| | |
|---|---|
| Đồ thị multi-source | 84,285 event · 1,109,655 cạnh · 4 nguồn |
| Held-out source precision | 81.8% cặp có ≥2 nguồn |
| T2 có lọc lặp lại | 487 → **11** (−97.7%) |
| T3 ordering | **72** conflict |
| T5 granularity | **336** đáng tin |
| Mức C | model F1 **39.08%**, 612 chu trình → 5, **ΔF1 ≈ 0** |
| TIMEX normaliser | **75.7%** |

## Thiếu để hoàn chỉnh MAVEN

| # | Việc | Chi phí |
|---|---|---|
| 1 | **Tập gán nhãn 300 mục** | điều kiện **duy nhất** để có P/R trên MAVEN. 3 person-day |
| 2 | Normaliser 75.7% → 90% | 3 ngày — hiện refprop sai gấp 3× |
| 3 | Áp `m00d00` sang MAVEN | MAVEN không có `00` tường minh; cần tương đương (anchor granularity=year) |
| 4 | Tầng sửa mức C dùng **ràng buộc cứng** thay confidence | hướng duy nhất chưa thử để cứu ΔF1 |

**Ưu tiên: 1 → 4 → 2 → 3.**

Mục 1 vì không có nó thì mọi kết quả MAVEN đều không so được với gì. Mục 4 vì tầng sửa hiện
dùng confidence của model (không đáng tin); dùng lớp cứng (precision ~100%) là hướng khác hẳn.
