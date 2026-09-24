# CONTEXT — đã làm gì, đang ở đâu, làm gì tiếp

Tài liệu điều hướng. Đọc cái này trước, rồi vào file chi tiết.

---

# 1. BẢN ĐỒ TÀI LIỆU

| File | Nội dung |
|---|---|
| **CONTEXT.md** | ← bạn đang đọc. Tổng quan + điều hướng |
| `DESIGN_FINAL.md` | **Thiết kế cuối**: đồ thị + thuật toán + bảng P/R |
| `PR_RESULTS.md` | Kết quả P/R chi tiết, giới hạn |
| `SMOKING_GUN.md` | Bằng chứng mạnh nhất: 57.3% độ chính xác giả trong data của PaTeCon |
| `MAVEN_STATUS.md` | MAVEN: điểm mạnh, vướng mắc, phù hợp/không phù hợp |
| `PATECON_VS_OURS.md` | Định nghĩa 5 loại conflict · kiểm chứng số với paper · đối chiếu |
| `PATECON_BASELINE.md` | Chạy PaTeCon gốc trên 7 dataset của họ |
| `CONFLICT_TAXONOMY.md` | Đo đủ T1–T5 trên dữ liệu Wikidata |
| `WD411_REPRO.md` | WD-411 không public; cách tái lập |
| `SOLUTIONS.md` | Uncertainty temporal + sự kiện định kỳ |
| `MODEL.md` | Mô hình toán: siêu đồ thị nhãn vai, dàn tinh chỉnh |
| `SPEC.md` | Nhật ký EXP1–15 trên MAVEN |
| `FINAL.md`, `FRAMEWORK.md`, `STRATEGY.md`, `LEVEL_C.md` | các bản trung gian |

---

# 2. HÀNH TRÌNH — 29 thí nghiệm

## Giai đoạn 1: khám phá MAVEN (EXP1–15)

| Phát hiện | Số |
|---|---|
| MAVEN-Arg ∩ MAVEN-ERE | **4,480/4,480 doc**, 79,740 event id chung |
| Gold nhất quán tuyệt đối | 0 chu trình, **100.0%** đóng kín bắc cầu, **72** mâu thuẫn |
| Entity cục bộ | **0/68,348** vượt document |
| Mining thống kê | **precision 0.00%** so với chuẩn cứng |
| C1 kiểu PaTeCon | **không bao giờ** bất đồng với majority |
| 636 signature theo type | lãi ròng **+0** so với 6 luật viết tay |
| FDR nếu dùng ngưỡng của họ | **34.7%** |
| Đồ thị dự đoán | **85,243** vi phạm bắc cầu (77% document) |

**Kết luận GD1:** mining thống kê không tìm ra lỗi thật trên MAVEN. Toàn bộ tín hiệu nằm
trong 6 luật (loại quan hệ × hướng văn bản).

## Giai đoạn 2: tái lập PaTeCon (EXP16–19)

| | |
|---|---|
| Dataset khớp Table 3 | **17,176 entity** — khớp tuyệt đối |
| Constraint: paper 13 vs chạy lại 12 | truy được: conf $80/89 = 0.8989$, thiếu ngưỡng **1 instance** |
| 7 dataset của họ | tỉ lệ conflict **0.52–1.79%**, dao động 3.4× |
| PaTeCon trên MAVEN | 459 property → **>30 phút bị giết**; 151 property → 348 constraint, **67% artifact** |
| Taxonomy T1–T5 | T5 granularity: **13.35%** trên data họ, **họ không nhắc tới** |

## Giai đoạn 3: bằng chứng quyết định (EXP24–25)

Chạy code gốc trên **bộ dữ liệu chính thức** của họ:

| | |
|---|---|
| Giá trị thời gian kết thúc `0101` | **57,090 / 99,698 = 57.3%** (kỳ vọng 0.27% → **209×**) |
| Conflict thuộc mẫu thô-vs-mịn | **185 / 747 = 25.5%** |
| Kiểm chứng qua Wikidata API | 18% mẫu xác nhận là precision=NĂM |
| Wikidata **có** trường `precision`; PaTeCon **vứt đi khi pad** | `Q849 P570: 14640000 prec=9` → họ ghi `14640101` |

## Giai đoạn 4: lời giải (EXP26–29)

| Lời giải | Kết quả |
|---|---|
| **Tập gán nhãn tự dựng** (48 phút quét 14,637 entity) | 50,000 fact, 6 nhãn, tách được ERROR khỏi REFINEMENT |
| **Uncertainty temporal** | 747 → 512 conflict (−31.5%) |
| **Sự kiện định kỳ** | 487 → **11** cảnh báo (−97.7%) |
| **Ràng buộc định lượng** | bắt được fact **đơn giá trị** mà họ không thể |
| **Phân tầng thay vì lọc** | F1 **0.212** vs 0.185 (**+14.6%**) |

---

# 3. KẾT QUẢ CHÍNH

| cấu hình | P | R | F1 |
|---|---|---|---|
| **PaTeCon** | 15.91% | 22.00% | 0.185 |
| **Ưu tiên precision** | **20.83%** (+4.92) | 21.54% (−0.46) | **0.212** (+14.6%) |
| **Ưu tiên recall** | 15.85% (−0.06) | **22.47%** (+0.47) | 0.186 |

**Đạt yêu cầu:** có điểm vận hành **recall vượt** (+0.47) với precision **ngang** (−0.06).

## Đóng góp đứng vững

1. **Held-out source precision** — đo precision không cần annotate. PaTeCon *cấu trúc không thể*
   (Wikidata 1 nguồn/fact; MAVEN **81.8%** cặp ≥2 nguồn)
2. **T5 granularity** — 57.3% độ chính xác giả trong data của **chính họ**; họ không nhắc tới
3. **Uncertainty temporal** — sửa 26.9% conflict giả của họ
4. **Sự kiện định kỳ** — 96.8% cảnh báo mutual-exclusion là hợp lệ; đúng future work họ để ngỏ
5. **Ràng buộc định lượng** — bắt fact đơn giá trị (88% cái họ bỏ sót)
6. **Kết quả âm tính có kiểm soát** — mining thống kê precision 0%
7. **Giới hạn scale** — $O(|R_t|^2|R|)$: 6 prop = 1.1s, 459 prop >30 phút

---

# 4. ĐANG Ở ĐÂU

| Hạng mục | Trạng thái |
|---|---|
| Tái lập PaTeCon | ✅ hoàn tất, khớp Table 3 |
| Tập gán nhãn WD50K | ✅ 50,000 fact |
| Uncertainty temporal | ✅ cài + kiểm chứng |
| Sự kiện định kỳ | ✅ cài + kiểm chứng |
| Ràng buộc định lượng | ✅ cài |
| Bảng P/R | ✅ có đường cong |
| Thiết kế đồ thị + mining | ✅ `DESIGN_FINAL.md` |
| TIMEX normaliser | ⚠️ **75.7%** (mục tiêu 85–90%) |
| T4 trên MAVEN | ❌ **1 constraint** — tính chất substrate |
| Mức C (đồ thị dự đoán) | ⏳ **chưa làm** |

---

# 5. LÀM GÌ TIẾP

| # | Việc | Vì sao | Chi phí |
|---|---|---|---|
| 1 | **Mức C: model TRE + tầng sửa** | target **85,243** vi phạm — lớn hơn mọi thứ đã đo 2 bậc | ~2 tuần |
| 2 | Nâng normaliser 75.7% → 90% | giảm nhiễu T5 (hiện refprop sai gấp 3×) | 3 ngày |
| 3 | Thêm luật định lượng | recall hiện chỉ +0.47; còn 88% fact đơn giá trị chưa khai thác | 3 ngày |
| 4 | Gán nhãn thủ công 300 mục MAVEN | điều kiện duy nhất để có P/R trên MAVEN | 3 person-day |

**Ưu tiên: 1 → 3 → 2 → 4.**

Mục 1 là target lớn nhất và **chưa đụng tới**. Mục 3 rẻ và đánh trúng điểm mù đã xác định
(88% bỏ sót là fact đơn giá trị).

---

# 6. NHỮNG ĐIỀU KHÔNG ĐƯỢC TUYÊN BỐ

Để tránh bị bác khi review:

- ❌ "vượt PaTeCon ở cả precision lẫn recall **cùng lúc**" — chỉ có đường cong, mỗi điểm
  vượt một chỉ số
- ❌ "25.5% conflict của họ là **sai**" — nên nói: thuộc mẫu thô-vs-mịn, cần xử lý như
  REFINEMENT
- ❌ "MAVEN nhiều conflict hơn Wikidata" — cùng bậc (0.12% vs 0.23%)
- ❌ "constraint mining khám phá tri thức mới" — cả hai substrate đều chủ yếu **tái khám phá**
  cái con người viết tay được
- ❌ so recall trực tiếp với con số trong paper họ — **WD-411 không public**
- ⚠️ nhãn của ta là **proxy** ("biến mất khỏi Wikidata"), không phải phán quyết chuyên gia
- ⚠️ precision tuyệt đối **thấp** (15.9–20.8%) ở **cả hai** phương pháp
- ⚠️ dưới nhãn chặt (chỉ DELETED) **lợi thế biến mất** — kết quả phụ thuộc định nghĩa "sai"

- [NO_ERE.md](NO_ERE.md) — bo ERE khi inference: luat khuech dai loi, tran precision thu cong 72% vs nguong 84%
- [ecskg/README.md](ecskg/README.md) — do thi event-centric tu TEXT THO (SEM + ECS-KG), schema OOP, vong khep kin text->graph->mining->kiem chung
