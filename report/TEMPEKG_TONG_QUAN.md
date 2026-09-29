# TempEKG — Tổng quan từ đầu tới cuối

Tài liệu này là bản đồ của cả dự án: bài toán là gì, dữ liệu và đồ thị dựng ra sao, hai bài toán giải thế nào
qua từng bước, kết quả cuối, và muốn hiểu sâu phần nào thì đọc tài liệu nào. Mọi số đo trên MAVEN-ERE valid
(710 document, 188.924 cạnh quan hệ thời gian); valid chỉ mở một lần cho mỗi cấu hình. Cập nhật 27/09/2026.

---

## 1. Hai bài toán trong một câu

| | Bài 1 — phân loại quan hệ thời gian | Bài 2 — kiểm toán đồ thị thời gian có nhiễu |
|---|---|---|
| Đầu vào | văn bản + đồ thị tri thức (sự kiện, entity, TIMEX), **biết cặp nào có quan hệ** nhưng **che toàn bộ nhãn** | một đồ thị thời gian **đã có nhãn** nhưng chứa cạnh sai |
| Đầu ra | nhãn cho mọi cạnh, trong 6 nhãn | cạnh nào sai, và đúng ra là nhãn gì |
| Được dùng | chỉ thông tin của từng cặp; **không bao giờ** dùng nhãn thời gian của cạnh khác | nhãn các cạnh xung quanh (vì chúng là quan sát) |
| Thước đo | macro-F1 trên 6 nhãn | tỷ lệ cạnh sai sau sửa, và macro-F1 của đồ thị sau sửa |
| Kết quả | **30,84%** (luôn đoán BEFORE: 15,30%) | nhiễu classifier: macro-F1 30,84% → **31,89%** (lỗi 15,31% → 12,53%); nhiễu bơm 10% / 20%: lỗi → **1,94% / 4,42%** |

Hai bài nối với nhau: **đầu ra tốt nhất của Bài 1 là đồ thị cần kiểm toán của Bài 2**. Ngoài ra Bài 2 còn chạy
trên đồ thị gold bị bơm nhiễu (nhiễu nhân tạo) và trên fake_data.

Sáu nhãn: BEFORE, CONTAINS, SIMULTANEOUS, OVERLAP, BEGINS-ON, ENDS-ON. Dữ liệu cực lệch (84,8% cạnh là
BEFORE), nên thước đo chính là macro-F1, không phải accuracy.

> Đọc thêm: `TEMPEKG_KIEN_TRUC.md` §1 (dữ liệu, ý nghĩa BEGINS-ON / ENDS-ON theo RED guideline).

---

## 2. Dữ liệu

| Nguồn | Cung cấp |
|---|---|
| MAVEN-ERE | sự kiện (cụm đồng tham chiếu), TIMEX, quan hệ thời gian, nhân quả, sự kiện con |
| MAVEN-Arg | tham số của sự kiện: ai, ở đâu, với ai (143 vai trò) |

Train 2.913 document, valid 710 document. Bốn loại cạnh thời gian trên valid:

| Loại cạnh | Số cạnh | Nhãn chính |
|---|---|---|
| EV–EV (sự kiện – sự kiện) | 109.929 | BEFORE 89,9% · CONTAINS 8,5% |
| EV→TIMEX | 26.573 | BEFORE 91,3% · CONTAINS 6,8% |
| TIMEX→EV | 39.935 | BEFORE 68,1% · CONTAINS 30,6% |
| TIMEX–TIMEX | 12.487 | BEFORE 79,2% · CONTAINS 17,0% · SIMU 2,6% |

**Về MAVEN-Arg:** ablation bỏ toàn bộ đặc trưng từ MAVEN-Arg chỉ làm Bài 1 giảm 0,10 điểm (30,84 → 30,74%) và
Bài 2 giảm 0,12 điểm (31,89 → 31,77%), nằm trong mức dao động do cách chia. MAVEN-Arg **không phải đóng góp**;
pipeline hiện vẫn giữ nó trong KG, và có thể bỏ mà không mất gì đo được (`STATUS.md` §39).

---

## 3. Dựng đồ thị tri thức (KG)

Script `src/build_kg.py` (build train khoảng 5,5 giây), kiểm bằng `src/verify_kg.py` (9 bất biến, đều đạt).

**Node** (valid): sự kiện 16.301 (cụm đồng tham chiếu), entity 12.927 (có id), span 17.963 (tham số không có
id, khoá theo offset), TIMEX 4.139 (DATE/TIME là mốc neo được, DURATION thì không). Node sự kiện mang thuộc
tính quan sát được: loại sự kiện, trigger, vị trí câu, tập vai trò, tập loại entity.

**Ba lớp cạnh, tách vật lý** để chống rò rỉ:

| Lớp | Nội dung | Dùng làm đặc trưng? |
|---|---|---|
| `input_edges` | sự kiện –vai trò→ entity/span (từ MAVEN-Arg) | có |
| `weak_edges` | CAUSE, PRECONDITION, SUBEVENT | chỉ để đo trần, không dùng |
| `target_edges` | quan hệ thời gian (4 loại cạnh) | Bài 1: **không bao giờ** · Bài 2: là đồ thị đang kiểm toán |

Hai sự kiện cùng trỏ tới một entity/span tạo thành **cặp chung neo** (anchored pair), được tính sẵn lúc build
để mining thành phép group-by.

**Tầng ràng buộc Allen:** mỗi nhãn dịch sang tập quan hệ Allen trên hai điểm mút (BEFORE = {b}, CONTAINS = {di},
OVERLAP = {o}, SIMULTANEOUS = {e}, BEGINS-ON = {s, si, e}, ENDS-ON = {b, m}). Bảng hợp thành sinh bằng vét cạn;
kiểm trên gold: 0 vi phạm trong 585.078 tam giác. Tầng này chỉ dùng để **chẩn đoán** (chứng minh gold sạch, giải
thích vì sao closure không sửa được lỗi tụ cụm), không nằm trong pipeline.

**Ví dụ thật** (*Franco-Dutch War*, câu đầu): War –Agent→ France, War –Patient→ Dutch Republic, supported cũng trỏ
tới hai entity này → cặp chung neo; các cạnh thời gian: War CONTAINS supported (EV–EV), 1672 OVERLAP War
(TIMEX→EV), War OVERLAP 1678 (EV→TIMEX), 1672 BEFORE 1678 (TIMEX–TIMEX).

> Đọc thêm: `TEMPEKG_KIEN_TRUC.md` §3–4 (sơ đồ, ví dụ thật, bảng Allen); `KG_BUILD.md` (định dạng lưu, bất
> biến); `DEFINITIONS.md` (các quyết định định nghĩa); `TEMPEKG_TOAN_HOC.md` §1–2 (ký hiệu, chứng minh tầng Allen);
> hình vẽ ở `TEMPEKG_GIAI_THICH.html`.

---

## 4. Chia dữ liệu và chống rò rỉ

- Chia **theo document** bằng hash (không theo cặp):
  - **DISCOVERY** (60% train): được đề xuất luật;
  - **CONFIRMATION-1** (20%): chỉ được xác nhận luật trên nhãn chưa dùng để chọn luật;
  - **CONFIRMATION-2** (20%): chọn ngưỡng và tham số;
  - **valid**: mở một lần để chấm.
- **Bài 2 học từ lỗi thật của classifier bằng cross-fit trên valid:** chia valid làm hai theo hash, học trên
  nửa này, chấm nửa kia, rồi đổi vai. Lỗi của classifier chỉ out-of-sample trên valid.
- Ablation K-fold trên toàn train (hướng C) cho 26,32–26,39% so với 26,99% của cách chia 60/20/20, nằm trong
  dao động; pipeline giữ 60/20/20.

> Đọc thêm: `TEMPEKG_KIEN_TRUC.md` §2; `RULESET.md` §3.6 (ablation K-fold).

---

## 5. Bài 1 — từng bước

```
KG + văn bản ─► 2.1 luật riêng cho 4 loại cạnh (30,09%) ─► 2.2 luật liên tầng ghi đè (30,84%) ─► đồ thị cho Bài 2
```

**Luật là gì.** Một luật là hội tối đa 2 (hoặc 3) điều kiện quan sát được → một nhãn, ví dụ
`a_before_b = False ∧ type_a = Military_operation → CONTAINS`. Độ tin cậy của luật là **cận dưới Wilson 95%**
(wlb) của precision, gộp support và confidence làm một.

**Bước 2.1a — luật EV–EV.** Vét cạn độ sâu ≤ 2 trong từng lớp của 8 view (toàn cục, khoảng cách câu, thứ tự,
chung neo, vị trí, loại sự kiện…) trên DISCOVERY, bằng bitset (74 giây).
- Cổng: n ≥ 25, k ≥ 8, ≥ 5 document, lift ≥ 1,5, Δlogit ≥ 0,5, rồi BH-FDR q < 0,05.
- Xác nhận trên CONF-1: 54.719 luật.
- Combiner chọn trên CONF-2: mỗi nhãn một ngưỡng precision; luật có wlb cao nhất vượt ngưỡng thì thắng, không có
  thì BEFORE. 2.794 luật được bật.
- Kết quả: EV–EV **26,99%**. Rút gọn có chứng minh còn **378 luật** cho cùng dự đoán.

**Bước 2.1b — ba loại cạnh TIMEX.** Luật riêng cho EV→TIMEX, TIMEX→EV, TIMEX–TIMEX với điều kiện về TIMEX (loại,
độ mịn lịch, so sánh lịch, giới từ trước TIMEX, TIMEX gần nhất). Gộp 4 loại cạnh: **30,09%**.

**Bước 2.2 — luật liên tầng.** Chia điều kiện thành 5 tầng theo nguồn gốc: ONT (loại sự kiện), ARG (vai trò),
DISC (vị trí, từ nối), LEX (trigger, từ trong TIMEX), TIME (TIMEX gần, lịch).
- Stage A: mine pattern trong từng tầng.
- Stage B: ghép 2–3 pattern từ **các tầng khác nhau** thành luật liên tầng.
- Stage C: luật ghi đè nhãn 2.1 khi vượt ngưỡng chọn trên CONF-2.
- Kết quả: **30,84% — kết quả Bài 1**.

Đây vẫn là luật theo từng cặp, **không phải transitivity**. Mọi phương pháp đọc nhãn cạnh xung quanh thuộc Bài 2:
nếu dùng nhãn dự đoán của cạnh kề ở Bài 1 thì thành vòng tròn.

**Tổng số luật Bài 1:** 68.495 sau xác nhận, 5.721 được bật, **713** sau rút gọn có chứng minh (cùng dự đoán).

**Giới hạn đã biết:** BEGINS-ON và ENDS-ON có F1 = 0 (69 và 34 cạnh valid). Tín hiệu bậc cao (nhãn xung quanh)
có trần rất cao (+15 điểm khi biết nhãn gold xung quanh) nhưng ở Bài 1 thì không dùng được.

> Đọc thêm: `TEMPEKG_BAI1.md` (bảng kết quả chính ở đầu, §3–5 từng bước, §6 ranh giới với Bài 2, §8 ablation,
> phụ lục số liệu từng nhãn); `RULESET.md` (luật thật, luật bắn thế nào trên cặp thật, cổng,
> combiner, rút gọn §12); `RULES_COMPACT.md` (378 luật gom theo nhãn); `TEMPEKG_TOAN_HOC.md` §3–7 (ngôn ngữ luật,
> thống kê chọn luật, combiner, chứng minh rút gọn).

---

## 6. Bài 2 — từng bước

```
đồ thị cần kiểm toán ─► 3.1 auditor tầng + GRAPH ─► 3.2 sửa chung theo tam giác ─► đồ thị đã sửa
```

**Ba nguồn nhiễu được thử:**

| Nguồn | Là gì | Độ khó |
|---|---|---|
| Nhiễu classifier | đồ thị do Bài 1 dự đoán (lỗi 15,31%) | khó: lỗi tụ thành cụm, có hệ thống, nhất quán với nhau |
| Nhiễu bơm | đổi 10% / 20% nhãn gold theo phân phối biên của từng loại cạnh, trên cả 4 loại cạnh | dễ hơn: lỗi ngẫu nhiên, hàng xóm vẫn đúng |
| fake_data | gold valid với cạnh EV–EV bị đổi nhãn 5 / 10 / 15 / 20%, cạnh TIMEX giữ gold | như nhiễu bơm, chỉ trên EV–EV |

**Bước 3.1 — auditor tầng + GRAPH.** Giống bước 2.2 nhưng thêm tầng **GRAPH**: chữ ký các đường a–x–b và a–x–y–b
trên đồ thị đang kiểm toán (loại node trung gian + nhãn có hướng từng chặng).
- Luật học **riêng cho từng nhóm (loại cạnh, nhãn hiện tại)**. Mỗi luật trả lời: *trong các cạnh đang mang nhãn
  này, cạnh nào sai và đúng ra là gì*.
- Cổng thích ứng theo tỷ lệ nền của nhóm, vì nhãn cần khôi phục thường là đa số: 57% cạnh EV–EV bị đoán
  CONTAINS thực ra là BEFORE.
- Với nhiễu classifier, học bằng cross-fit trên valid. Mỗi fold mine khoảng 1.400–1.560 luật, rút gọn còn
  42–83 luật.
- Kết quả: lỗi 15,31% → 12,80%.

**Bước 3.2 — mô hình năng lượng tam giác** (không phải luật if-then).
- Đếm tần suất mọi cấu hình tam giác (loại 3 node + 3 nhãn có hướng) trên gold train: 2.326 document, 6,31
  triệu tam giác. Mỗi tam giác nhận điểm −PMI của cấu hình của nó, cộng một kênh nhiễu (xác suất quan sát
  nhãn này khi nhãn thật là nhãn kia).
- Cả document được gán lại nhãn bằng ICM (coordinate descent, tối đa 4 lượt) để giảm tổng năng lượng.
- Tham số (cách cân, λ, α) chọn bằng lưới, theo một trong hai mục tiêu: giảm số lỗi, hoặc macro-F1.
- Ví dụ thật (*Nicaragua*): bộ (1912 CONTAINS began, 1912 BEFORE 1934, began OVERLAP 1934) gặp 0 lần trong
  gold; đổi cạnh cuối thành BEFORE thì cấu hình gặp 27.582 lần, nên mô hình sửa theo hướng đó.
- Chạy một mình trên đồ thị Bài 1: macro-F1 31,36% (dòng ablation "chỉ 3.2").

**Kết quả Bài 2** (valid; mọi tham số chọn theo một mục tiêu duy nhất là macro-F1):

| Đồ thị cần kiểm toán | Macro-F1: trước → sau | Lỗi: trước → sau |
|---|---|---|
| Đầu ra Bài 1 (3.1 → 3.2) | 30,84% → **31,89%** | 15,31% → 12,53% |
| Bơm 10%, 4 loại cạnh (3.2) | 69,1% → **85,1%** | 9,94% → 1,94% |
| Bơm 20%, 4 loại cạnh (3.2) | 51,0% → **72,6%** | 19,89% → 4,42% |
| fake_data 5 / 10 / 15 / 20% (3.2, EV–EV) | 81,4 / 70,2 / 61,3 / 52,2% → **94,0 / 84,0 / 79,8 / 72,7%** | 4,97 / 10,00 / 14,98 / 19,93% → 0,96 / 2,28 / 2,56 / 3,36% |

**Cách đọc số fake_data:** macro-F1 EV–EV của fake_data cao vì đồ thị đầu vào vốn gần đúng: 80–95% cạnh là
gold. Chấm riêng trên các cạnh bị fake:
- accuracy 0 → 89–94%, nhưng macro-F1 chỉ 0 → 25–36%;
- 98–99,6% cạnh sạch vẫn giữ đúng nhãn;
- nhãn hiếm vẫn khó khôi phục (`experiments/logs/fake_eval_subset.log`).

**Vì sao chỉ tối ưu theo macro-F1:** chọn tham số theo số lỗi thì mô hình đẩy nhãn hiếm về BEFORE (cái bẫy
accuracy). Macro-F1 cũng là thước của Bài 1, nên hai bài dùng chung một mục tiêu.

> Đọc thêm: `TEMPEKG_BAI2.md` (bảng kết quả chính ở đầu, §2 thước đo, §4 auditor, §5 mô hình tam giác, §6 vì sao
> đầu ra Bài 1 khó sửa, §8 ablation kể cả fake_data chấm riêng trên cạnh bị fake, phụ lục P.3 chi tiết); `RULESET.md` §8 (luật Bài 2);
> `TEMPEKG_TOAN_HOC.md` §8–9 (auditor, mô hình năng lượng) và §11 (định nghĩa P / R / giảm ròng).

---

## 7. Những kết luận đã chốt

- **Đơn vị suy luận đúng là tam giác.** 75–98% cạnh sai nằm trong ít nhất một tam giác có cấu hình chưa từng
  gặp trong gold. Chuỗi 3 bước không thêm gì: 99,86% cạnh đã có đường 2 bước, và 0 cạnh chỉ nối được qua 3 bước.
- **Bộ 4, bộ 5 thêm rất ít** khi nhãn xung quanh là dự đoán; cụm 4 node đủ 6 cạnh quá thưa để làm hạng tử.
- **Gold sạch.** Bốn phép đo độc lập không tìm thấy lỗi chú thích, nên muốn đo recall của Bài 2 phải bơm nhiễu.
- **Closure Allen gần như im lặng** trên lỗi classifier: lỗi tụ cụm nên vẫn nhất quán với nhau.
- **Xếp hạng luật theo Wilson, không theo lift:** lift thưởng cho luật n = 5 may mắn.
- **MAVEN-Arg không có đóng góp đo được** (mục 2).

---

## 8. Bản đồ tài liệu

| Muốn hiểu | Đọc | Mục |
|---|---|---|
| Kiến trúc chung: dữ liệu, KG, chia tập, thiết kế tầng, quy trình | `TEMPEKG_KIEN_TRUC.md` | §1–6 |
| Bài 1 từ đầu tới cuối | `TEMPEKG_BAI1.md` | kết quả chính, §1–9, ablation §8 |
| Bài 2 từ đầu tới cuối | `TEMPEKG_BAI2.md` | kết quả chính, §1–10, ablation §8 |
| Luật trông thế nào, luật thật, cổng, ngưỡng | `RULESET.md` | §1–8, §12 |
| Bộ 378 luật gọn EV–EV | `RULES_COMPACT.md` | |
| Định nghĩa và chứng minh (toán) | `TEMPEKG_TOAN_HOC.md` (+ `.html`) | §1–13 |
| Chi tiết dựng KG, bất biến | `KG_BUILD.md`, `DEFINITIONS.md` | |
| Đại số luật (bộ luật cũ) | `RULE_ALGEBRA.md` | |
| Tín hiệu bậc cao (bộ 3/4/5, lịch sử) | `LUAT_BAC_CAO.md` | |
| Mọi số liệu theo thời gian | `STATUS.md` | §22–39 |
| Bản có hình vẽ | `TEMPEKG_GIAI_THICH.html` | |
| Thuật ngữ | `THUAT_NGU.md` | |
| So với PaTeCon, MAVEN-Arg | `NOTES_MAVEN_PaTeCon.md` | |

**Thứ tự đọc gợi ý:** tài liệu này → `TEMPEKG_KIEN_TRUC.md` → `TEMPEKG_BAI1.md` → `RULESET.md` §1–5 →
`TEMPEKG_BAI2.md` → `TEMPEKG_TOAN_HOC.md` khi cần chứng minh.

**Tái tạo:** các lệnh chạy nằm ở mục "Tái tạo" của `TEMPEKG_BAI1.md` (§9) và `TEMPEKG_BAI2.md` (§10). Log gốc
của mọi số ở `experiments/logs/` và `experiments/rules_full/`.
