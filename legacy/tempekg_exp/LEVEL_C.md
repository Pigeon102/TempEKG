# Mức C — Temporal conflict detection: đây MỚI là đề tài, và nó có target thật

**Sửa lại kết luận trước.** Kết quả âm tính về mining **không đóng** hướng temporal conflict.
Nó chỉ nói: đừng kỳ vọng *khai phá ra* constraint mới. Nhưng ở mức C, constraint **không
dùng để dự đoán** — chúng dùng để **kiểm định**. Đó là chuyện hoàn toàn khác.

---

## 1. Bằng chứng quyết định (EXP16)

Không cần train model mới: dùng chính cascade đã có (6 luật + majority) làm "model", sinh
đồ thị thời gian dự đoán trên 725 document EVAL, rồi đếm vi phạm ràng buộc.

| | GOLD | **DỰ ĐOÁN** |
|---|---|---|
| cạnh BEFORE | 108,529 | 117,778 |
| V1 vi phạm đối xứng | 0 | 0 |
| **V2 chu trình** | **0** | **735** |
| **V3 thiếu bắc cầu** | **2** | **85,243** |
| document có chu trình | 0% | **26%** |
| document thiếu bắc cầu | 0% | **77%** |

**85,243 vi phạm so với 2.** Gấp hơn **40,000 lần**.

### Vì sao — lý do cấu trúc, không phải ngẫu nhiên

> Gold đóng kín bắc cầu **100%** vì được annotate dưới ràng buộc đó.
> **Mọi** model TRE phân loại **từng cặp độc lập**, nên output của nó **không thể** đóng kín.
> Vi phạm là **tất yếu về mặt cấu trúc**, không phải do model kém.

Đây chính là chỗ conflict thật tồn tại, và nó **không biến mất** khi thay model tốt hơn —
baseline MAVEN-ERE đã công bố cũng không ép nhất quán toàn cục.

---

## 2. Bài toán được phát biểu lại cho đúng

**Sai (kế hoạch cũ):** mine constraint → tìm conflict trong gold.
→ Chết vì gold chỉ có **72** conflict.

**Đúng (mức C):**

```
model TRE  ──►  đồ thị thời gian dự đoán (KHÔNG nhất quán theo cấu trúc)
                          │
        constraint ──────►│  phát hiện vi phạm   (85,243 mục tiêu)
                          │  định vị thủ phạm
                          │  SỬA
                          ▼
                   đồ thị đã sửa  ──►  F1 có tăng không?
```

Constraint dùng ở đây gồm hai loại, **cả hai đều đã có sẵn**:

| Loại | Nguồn | Độ tin |
|---|---|---|
| **Ràng buộc logic** — đối xứng, phản xạ, bắc cầu, phi chu trình | tiên nghiệm, không cần mine | tuyệt đối |
| **6 luật quan hệ** — CAUSE/PRECONDITION/SUBEVENT × hướng | đã mine + kiểm chứng held-out | **95–100%** |

**Kết quả âm tính về mining trở nên vô hại**: ta không cần constraint mới, ta cần constraint
*đáng tin* — và đã có.

---

## 3. Insight riêng rút ra từ PaTeCon (không phải copy)

| PaTeCon | TempEKG mức C | Vì sao khác |
|---|---|---|
| Mine constraint để **tìm lỗi trong KG** | Dùng constraint để **sửa output model** | KG nhiễu; gold ở đây sạch, output model mới nhiễu |
| entity-level confidence | **bỏ** — suy biến | 0/68,348 entity vượt document |
| SP(a) chia sẻ participant | **bỏ** — thông tin = 0 (EXP13) | đo được, không suy đoán |
| SP(b) hai subject nối bởi cạnh phi thời gian | **giữ** → causal/subevent | analogue trực tiếp, chưa ai dùng |
| Logic ba trị pos/neg/**unknown** | **giữ nguyên** | 55% event thiếu anchor |
| support/confidence trần | **+ Wilson + BH-FDR** | FDR đo được **34.7%** nếu không sửa |

**Insight riêng, có số chống lưng:**

1. **Định lý suy biến** — trên đồ thị entity cục bộ, entity-level confidence của PaTeCon
   *chứng minh được* là suy biến thành fact-level. PaTeCon+ báo chênh lệch 38× trên WD27M;
   ở đây bị chặn quanh 1 **theo cấu trúc**.
2. **$I(\rho;\sigma) > 0$ nhưng lãi quyết định $\approx 0$** — đặc trưng có thông tin tương
   hỗ dương (bất đồng cao hơn null **17×**) nhưng không đổi được quyết định. Phân biệt này
   support/confidence **không nắm bắt được**.
3. **Nghịch đảo mục tiêu** — PaTeCon giả định KG nhiễu. Khi corpus nhất quán theo annotation,
   constraint mining đổi vai từ *khai phá* sang *kiểm định*, và target chuyển từ dữ liệu
   sang output model. **72 → 85,243.**

---

## 4. Cần gì để chạy mức C

| Thành phần | Trạng thái | Ước tính |
|---|---|---|
| Constraint logic (đối xứng/bắc cầu/chu trình) | ✅ đã cài trong EXP16 | xong |
| 6 luật quan hệ | ✅ đã mine + validate | xong |
| Đồ thị dự đoán để test | ✅ EXP16 đã sinh được | xong |
| **Model TRE thật** | ❌ chưa có | **2–4 ngày** (RoBERTa pair classifier, 593K mẫu train) |
| Tầng sửa (ILP / MaxSAT / greedy) | ❌ chưa có | 3–5 ngày |
| Đánh giá Δ F1 trước/sau sửa | ❌ | 2 ngày |

**Tổng ~2 tuần** trong 43 ngày còn lại. Khả thi.

> Đánh giá trước đây của mình rằng model TRE là "hạng mục lớn nhất" là **quá bi quan**.
> Đây là bài phân loại cặp chuẩn, có 593,433 mẫu train và baseline đã công bố.

---

## 5. Đóng góp bài báo ở mức C

1. **Phát hiện**: đồ thị thời gian do model sinh ra vi phạm ràng buộc ở quy mô lớn
   (**77%** document thiếu bắc cầu, **26%** có chu trình) trong khi gold sạch tuyệt đối —
   vì per-pair classification **không thể** đóng kín bắc cầu.
2. **Phương pháp**: constraint-based repair, với constraint đến từ hai nguồn (logic tiên
   nghiệm + 6 luật quan hệ đã kiểm chứng 95–100%).
3. **Insight về port**: ba điểm ở §3, mỗi điểm có số đo.
4. **Resource**: đồ thị, normaliser, và nhật ký 16 thí nghiệm.

---

## 6. Việc tiếp theo, theo thứ tự

1. Train model TRE trên MAVEN-ERE (train split) — RoBERTa pair classifier
2. Sinh đồ thị dự đoán trên EVAL, đo lại V1/V2/V3 với **model thật** (EXP16 mới dùng model thô)
3. Cài tầng sửa: closure + phá chu trình theo confidence thấp nhất
4. Đo Δ F1 trước/sau sửa — **đây là con số chính của bài báo**
