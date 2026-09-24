# TRẠNG THÁI — đã làm được gì, còn thiếu gì

Cập nhật sau EXP26. Toàn bộ số là đo thật.

---

# PHẦN 1 — ĐÃ LÀM ĐƯỢC

## 1.1 Tái lập PaTeCon (nền tảng để so sánh)

| | Kết quả |
|---|---|
| Tải code gốc (11 module) + dataset chính thức từ Drive | ✅ |
| Dataset khớp Table 3: 50,000 fact, **17,176 entity**, 6 property | ✅ **khớp tuyệt đối** |
| Constraint: paper 13 vs chạy lại **12** | ✅ truy được nguyên nhân: constraint #13 có conf $80/89 = 0.8989$, thiếu ngưỡng 0.9 đúng **1 instance** |
| Tất định qua 3 lần chạy | ✅ 12 constraint / 819 conflict, y hệt |
| Chạy trên 7 dataset của họ | ✅ tỉ lệ conflict **0.52–1.79%**, dao động 3.4× |
| Chạy PaTeCon trên MAVEN | ⚠️ vocabulary đầy đủ (459 prop) **quá 30 phút**; rút gọn (151 prop) xong ~3 phút → 348 constraint / 535 conflict |

## 1.2 Phát hiện về PaTeCon

| Phát hiện | Bằng chứng |
|---|---|
| **57.3% giá trị thời gian trong WD50K chính thức kết thúc `0101`** | 209× mức ngẫu nhiên 0.27% |
| **25.5% conflict của họ thuộc mẫu thô-vs-mịn** | 185/747, đo trực tiếp |
| 18% mẫu `0101` xác nhận là precision=NĂM | Wikidata API, 45 truy vấn thành công |
| **Wikidata CÓ trường `precision`; PaTeCon vứt đi khi pad** | `Q849 P570: 14640000 precision=9` → họ ghi `14640101` |
| Tiêu chí WD-411 gộp "SAI" với "THÔ HƠN" | 2.3% mẫu là refinement, không phải lỗi |
| $O(\lvert R_t\rvert^2\lvert R\rvert)$ nổ theo vocabulary | WD50K 6 prop = 1.1s; MAVEN 459 prop >30 phút |
| Ngưỡng cứng 0.9 mong manh ở support thấp | constraint #13: 1 instance đổi kết quả |
| Họ **không đo precision** (tự thừa nhận §6.1.2) | Wikidata 1 nguồn/fact |
| **Không xử lý T5 granularity, không nhắc tới** | rà toàn văn |

## 1.3 Hệ thống TempEKG đã xây

| Thành phần | Trạng thái | Số đo |
|---|---|---|
| Đồ thị multi-source (`source` trong PK) | ✅ | 84,285 event, 1,109,655 cạnh, 4 nguồn |
| TIMEX normaliser | ✅ | **75.7%** độ phủ (regex 63.1 + refprop 11.6 + gazetteer 1.0) |
| **Held-out source precision** (giao thức mới) | ✅ | **họ không thể chạy** |
| T2 có xét sự kiện lặp lại | ✅ | 487 thô → loại **58.3%** lặp lại → 203 |
| T3 ordering | ✅ | 72 conflict, xác nhận độc lập 2 lần |
| T4 mở rộng (2 nhánh họ bỏ) | ✅ cài xong | **0 constraint** — granularity quá thô |
| T5 granularity trên MAVEN | ✅ | **336** conflict đáng tin (6.30%) |
| Benchmark lưu trữ | ✅ | S3 nhanh 9×, incremental 0.03 ms/doc |
| Tái lập sinh ứng viên WD-411 | ✅ | 19.1% bị xoá, 2.3% refinement |

## 1.4 Kết quả âm tính có kiểm soát (cũng là đóng góp)

| | Số đo |
|---|---|
| Constraint mine bằng thống kê phát hiện lỗi thật | **precision 0.00%** (giao 0/4,874 với 14 conflict cứng) |
| C1 (SP(a) chia sẻ participant, kiểu PaTeCon) | **không bao giờ** bất đồng với majority |
| 636 signature theo type | lãi ròng **+0** so với 6 luật viết tay |
| Mọi đặc trưng khác (khoảng cách câu, TIMEX anchor) | lãi ròng **+0** |
| FDR nếu dùng ngưỡng kiểu họ | **34.7%** → sau Wilson+BH: **0.0%** |

---

# PHẦN 2 — WD-411: TÁI LẬP ĐƯỢC MỘT PHẦN

## 2.1 Bản gốc: KHÔNG có

Rà GitHub (`resource/`, `output/`, `dataset_build/`), Google Drive, `property final.tsv`
(chỉ là 108 property + label). **WD-411 và FB-128 không được phát hành.**

## 2.2 Nhưng quy trình sinh ứng viên thì tái lập được — ĐÃ LÀM

Quy trình của họ: so dump 2019 với Wikidata hiện tại → fact bị xoá = ứng viên sai → 2 chuyên
gia kiểm.

**Bước 1–3 đã tái lập** (EXP26, mẫu 598 fact theo đúng phân bố property của WD-411):

| trạng thái | số | tỉ lệ |
|---|---|---|
| còn nguyên (khớp chính xác) | 385 | 64.4% |
| **bị xoá hoàn toàn** | **114** | **19.1%** ← ứng viên |
| entity/property không còn | 80 | 13.4% |
| **thô hơn → đã làm mịn** | 14 | 2.3% |
| đổi ngày cùng năm | 5 | 0.8% |

Ngoại suy lên WD50K (50,000 fact): **~16,000 ứng viên**. WD-411 của họ là 411 mẫu trong đó.

**Khả thi kỹ thuật:** batch API 50 entity/2.9s → quét toàn bộ WD50K mất **~50 phút**.

## 2.3 Và có thể làm TỐT HƠN WD-411

Tiêu chí của họ gộp chung hai hiện tượng. Ta tách được bằng trường `precision`:

```
Q80236  P54  Q314851   -> [] rong          = SAI that (fact bi go)
Q849    P570 14640101  -> 14640000 prec=9  = THO HON (van dung, chi la nam-only)
Q119483 P569 19550101  -> 19551214 prec=11 = LAM MIN (khong sai)
```

> **Tập gán nhãn của mình sẽ phân biệt được ERROR vs REFINEMENT — WD-411 thì không.**
> Và nó **không cần chuyên gia**, vì `precision` của Wikidata là nhãn vàng có sẵn.

## 2.4 Còn thiếu gì để có recall so với họ

| | Cần | Trạng thái |
|---|---|---|
| Ứng viên | quét toàn WD50K qua API | ⏳ ~50 phút, **chưa chạy** |
| Nhãn đúng/sai | `precision` + trạng thái xoá | ✅ **miễn phí, không cần chuyên gia** |
| Chạy PaTeCon và TempEKG trên cùng tập, đo recall | | ⏳ **chưa làm** |
| So sánh với con số recall trong paper họ | ❌ | **không thể** — họ báo recall trên WD-411/FB-128 mà tập đó không công khai |

> **Kết luận:** so recall **trên tập mình tự dựng** thì được (và tập đó tốt hơn vì tách được
> refinement). So recall **trực tiếp với con số trong paper họ** thì **không**, vì tập gốc
> không tồn tại công khai.

---

# PHẦN 3 — CÒN THIẾU

| # | Việc | Vì sao cần | Chi phí |
|---|---|---|---|
| 1 | **Quét toàn WD50K qua API** → dựng tập gán nhãn | mắt xích cuối để có recall | **~1 giờ** |
| 2 | Chạy PaTeCon + TempEKG trên tập đó, đo P/R | bảng so sánh chính của bài | 1 ngày |
| 3 | **Biểu diễn uncertainty temporal** (interval + granularity thay cho điểm) | giải quyết gốc T5: `1638` thành `[1638-01-01, 1638-12-31]` thì `1638-12-02` là REFINEMENT tự động | 2 ngày |
| 4 | Nâng normaliser lên mức ngày/tháng | mở khoá **T4** (hiện 0 constraint vì granularity thô), giảm nhiễu T5 từ 3× | ~1 tuần |
| 5 | Mức C: model TRE + tầng sửa | target **85,243** vi phạm trên đồ thị dự đoán | ~2 tuần |
| 6 | Xử lý sự kiện định kỳ đúng cách (chu kỳ, ngưỡng theo loại) | hiện dùng ngưỡng thô 3 năm; đúng future work họ để ngỏ | 3 ngày |

**Thứ tự đề xuất: 1 → 3 → 2 → 6 → 4 → 5.**

Mục 1 rẻ nhất (~1 giờ) và mở khoá mục 2 — bảng kết quả chính. Mục 3 là lời giải gốc cho T5
mà bạn đã chỉ ra, và nó rẻ (2 ngày) vì schema đã có sẵn cột `granularity` + `norm_method`.
