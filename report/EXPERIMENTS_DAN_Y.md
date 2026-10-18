# Dàn ý phần Experiments (bản đọc trước)

Bản này là dàn ý tiếng Việt của phần thực nghiệm, đọc trước khi sửa LaTeX. Mỗi mục ghi: **mục đích**, **thông
điệp cần nhấn**, **nội dung và số liệu**, và **việc còn phải quyết**. Bản LaTeX tương ứng:
`latex/src/experiments_draft.tex`. Ký hiệu theo `main.tex`: λ = hệ số làm trơn PMI (= 10), β = trọng số tam giác,
γ = hệ số làm yếu prior.

Cách viết theo PaTeCon: mở đầu nói có mấy nhóm thí nghiệm, liệt kê kết quả chính thành danh sách đánh số; phần
Setup gom dữ liệu, thước đo, môi trường và mọi ngưỡng; mỗi kết quả đi kèm một bảng và một đoạn đọc bảng.

---

## Đoạn mở đầu

**Mục đích:** người đọc biết ngay có những thí nghiệm nào và kết luận gì, trước khi vào chi tiết.

**Nội dung:** ba nhóm thí nghiệm:
1. Task 1 dự đoán tốt đến đâu, và cần bao nhiêu luật.
2. Task 2 sửa được bao nhiêu, với ba nguồn lỗi.
3. Ablation: vì sao chọn từng thành phần, và mỗi thành phần mang lại gì.

**Ba kết quả chính** (viết thành danh sách đánh số):
1. Luật đạt 30,84% macro-F1 trên mọi cạnh; rút gọn còn 713 luật mà không đổi dự đoán nào.
2. Repair khôi phục phần lớn lỗi ngẫu nhiên: với nhiễu EV–EV 5–20%, lỗi còn 0,96–3,36%, F1 phát hiện 89–92%.
   Với đầu ra Task 1 (lỗi có hệ thống), macro-F1 tăng 30,84% → 31,89%.
3. Mô hình nhiễu và tam giác là cốt lõi của repair; PMI thay tần suất thô, Wilson thay confidence hay lift mỗi thứ
   đáng 1–3 điểm.

---

## 5.1 Experimental Setup

**Mục đích:** cho thấy đánh giá không rò rỉ và tái lập được.

**Dữ liệu và cách chia.** Chia train theo bài viết: tập khám phá 60% (tìm luật), tập xác nhận 20% (chấm lại luật),
tập chọn ngưỡng 20% (chọn ngưỡng và tham số repair). Valid chấm một lần cho mỗi cấu hình. Với đầu ra Task 1, repair
phải học từ lỗi thật của classifier nên dùng cross-fit trên valid: chia valid làm hai nửa theo bài, học trên nửa này,
chấm nửa kia, rồi đổi vai.

**Ba nguồn lỗi cho Task 2.**

| Nguồn | Là gì | Đặc điểm |
|---|---|---|
| Đầu ra Task 1 | đồ thị classifier đoán, sai 15,31% (28.916 cạnh) | lỗi có hệ thống, tụ cụm |
| Nhiễu EV–EV | file nhiễu đã công bố (bảng trong phần Dataset), đổi 5–20% cạnh sự kiện – sự kiện | lỗi ngẫu nhiên, cạnh TIMEX giữ đúng |
| Nhiễu mọi loại cạnh | đổi 10% / 20% cạnh của cả 4 loại, cùng cách sinh | kiểm tra cạnh có mốc thời gian |

**Thước đo.** Macro-F1 trên 6 nhãn là thước chính cho cả hai task. Riêng Task 2 báo thêm:
- tỷ lệ cạnh sai trước và sau;
- P / R / F1 phát hiện: một cạnh được tính là "phát hiện" khi repair đổi nó, và "phát hiện đúng" khi nó vốn sai;
- số cạnh sửa đúng, số cạnh đúng bị phá, sửa ròng = sửa − phá;
- accuracy và macro-F1 tính riêng trên các cạnh sai ban đầu (trước khi sửa, cả hai đều bằng 0).

**Baseline.** Hiện chỉ có baseline nội bộ (xem mục "Cần quyết định").

**Môi trường và tham số** (một đoạn như PaTeCon): Python thuần, không thư viện số; máy 16 nhân, 15,7 GB RAM; mine
luật trên toàn train khoảng 6 phút với 4 tiến trình. Cổng lọc đặt trước: n ≥ 25, k ≥ 8, ≥ 5 bài, lift trong nhóm
≥ 1,5, Benjamini–Hochberg q = 0,05. Repair: λ = 10; chọn β ∈ {0,2; 0,5; 1; 2} và γ ∈ {0; 0,5} theo macro-F1 trên
dữ liệu chọn tham số.

---

## 5.2 Task 1: dự đoán quan hệ

**Thông điệp:** luật dùng được trên mọi loại cạnh; luật liên tầng cải thiện đều; mô hình gọn và đọc được. **Không
nhấn số tuyệt đối**, vì chưa có baseline ngoài.

**Bảng 1. Macro-F1 (%) trên valid theo loại cạnh**

| Phương pháp | EV–EV | EV→TX | TX→EV | TX–TX | Tất cả |
|---|---|---|---|---|---|
| Luật cho từng loại cạnh | 26,99 | 29,74 | 24,29 | 32,98 | 30,09 |
| + luật liên tầng | **27,44** | **30,51** | **26,24** | **34,93** | **30,84** |

**Đoạn đọc bảng:**
- Luật liên tầng cải thiện mọi loại cạnh, nhiều nhất ở mốc–mốc (F1 CONTAINS 46,3 → 57,6) và mốc → sự kiện
  (OVERLAP 4,4 → 16,0).
- F1 theo nhãn trên mọi cạnh: BEFORE 91,3 · CONTAINS 52,9 · SIMULTANEOUS 26,0 · OVERLAP 14,8. BEGINS-ON và ENDS-ON
  (69 và 34 cạnh) vẫn bằng 0, vì tín hiệu "since", "until" chỉ đi kèm hai nhãn này ở 1–10% số lần.
- **Độ gọn:** 68.495 luật qua bộ lọc, 5.721 luật có thể bỏ phiếu; rút gọn bằng set cover còn 713 luật cho đúng mọi
  dự đoán (EV–EV: 378 luật, cách chặn dưới 377 đúng một luật).

---

## 5.3 Task 2: sửa đồ thị

**Thứ tự trình bày:** mở bằng kết quả "sạch" (nhiễu tổng hợp, có kiểm soát), rồi mới đến ca khó (đầu ra Task 1).

### Nhiễu tổng hợp

**Thông điệp:** lỗi ngẫu nhiên phần lớn khôi phục được.

**Bảng 2. Sửa nhiễu tổng hợp** (hai cột cuối tính riêng trên các cạnh bị đổi)

| Bối cảnh | Macro-F1 trước → sau | Lỗi trước → sau | Sửa / phá / ròng | Cạnh bị đổi: accuracy / macro-F1 |
|---|---|---|---|---|
| EV–EV 5% | 81,37 → 94,02 | 4,97 → 0,96 | 4.874 / 472 / +4.402 | 89,28 / 24,60 |
| EV–EV 10% | 70,23 → 83,95 | 10,00 → 2,28 | 10.322 / 1.837 / +8.485 | 93,90 / 34,03 |
| EV–EV 15% | 61,25 → 79,78 | 14,98 → 2,56 | 15.042 / 1.391 / +13.651 | 91,34 / 36,00 |
| EV–EV 20% | 52,18 → 72,68 | 19,93 → 3,36 | 20.040 / 1.826 / +18.214 | 91,48 / 33,41 |
| Mọi loại cạnh 10% | 68,46 → 84,92 | 9,94 → 1,91 | 16.526 / 1.353 / +15.173 | 88,00 / 33,60 |
| Mọi loại cạnh 20% | 50,47 → 72,03 | 19,89 → 4,37 | 33.034 / 3.709 / +29.325 | 87,91 / 34,12 |

F1 phát hiện: EV–EV 90,3 / 89,3 / 91,6 / 91,8; mọi loại cạnh 90,4 / 89,2.

**Đoạn đọc bảng:**
- Ở mọi mức, repair loại 77–83% số lỗi, F1 phát hiện 89–92%, và chỉ đổi nhầm tối đa 2,5% số cạnh vốn đúng.
- Trên riêng các cạnh bị đổi: 88–94% được trả về đúng nhãn, nhưng macro-F1 chỉ 25–36%. Lý do: khoảng 90% cạnh bị đổi
  vốn là BEFORE; số ít cạnh nhãn hiếm bị đổi vẫn khó khôi phục.
- Cần ghi rõ: các dòng nhiễu tổng hợp chỉ chạy bước tam giác, vì bước auditor cần lỗi thật của classifier để học.

### Đầu ra Task 1

**Thông điệp:** đây là ca khó; mỗi bước giúp một ít, ghép lại thì giúp nhiều nhất. Trình bày trung thực.

**Bảng 3. Sửa đầu ra Task 1** (cross-fit trên valid, tham số chọn theo macro-F1)

| Cấu hình | Macro-F1 | Lỗi | P / R / F1 phát hiện | Sửa / phá / ròng | Cạnh sai ban đầu: accuracy / macro-F1 |
|---|---|---|---|---|---|
| Chưa sửa | 30,84 | 15,31 | — | — | 0 / 0 |
| Chỉ bước 1 (auditor) | 31,53 | 13,47 | 68,0 / 23,5 / 34,9 | 6.664 / 3.199 / +3.465 | 23,1 / 7,8 |
| Chỉ bước 2 (tam giác) | 31,36 | 13,83 | 67,9 / 22,3 / 33,6 | 5.847 / 3.054 / +2.793 | 20,2 / 8,3 |
| **Bước 1 → bước 2** | **31,89** | **12,53** | 70,4 / 34,1 / 45,9 | 9.381 / 4.145 / +5.236 | 32,4 / 11,1 |

**Đoạn đọc bảng:** ghép hai bước cho kết quả tốt nhất. Trên 28.916 cạnh sai ban đầu, repair khôi phục 32,4%, thấp
xa mức 88–94% của nhiễu ngẫu nhiên., vì lỗi của classifier có hệ thống và tụ cụm chứ không ngẫu nhiên.

---

## 5.4 Ablation (chỉ văn xuôi; bảng ở Phụ lục A)

**Cách viết:** mỗi đoạn trả lời "vì sao chọn cách này, và nó mang lại lợi ích gì", dẫn một hai con số làm bằng
chứng và trỏ tới bảng ở phụ lục. Câu mở: mỗi biến thể chỉ đổi một lựa chọn và chọn lại mọi tham số còn lại; chênh
lệch dưới khoảng 0,5 điểm nằm trong mức dao động khi chia lại train.

**Task 1 — chấm điểm luật bằng cận dưới Wilson.** Luật ít mẫu có confidence không đáng tin; Wilson phạt luật ít mẫu
một cách có nguyên tắc. Lợi ích: hơn confidence thô khoảng 0,9 điểm và hơn lift khoảng 3 điểm; số luật được bật
cũng ít hơn hẳn (2.115 so với 3.839–11.017), nên mô hình gọn hơn.

**Task 1 — mỗi nhãn một ngưỡng.** Tỷ lệ nền của các nhãn chênh nhau hơn mười lần, nên một ngưỡng chung không thể vừa
lọc nhiễu cho nhãn phổ biến vừa giữ được nhãn hiếm. Lợi ích: giữ cho nhãn hiếm được đoán; một ngưỡng chung làm
SIMULTANEOUS và OVERLAP về 0 và mất 4,4 điểm.

**Task 1 — luật tối đa hai điều kiện.** Độ sâu 2 là mức lớn nhất còn vét cạn được, nên không bỏ sót luật nào; mỗi
luật còn gắn với một nhóm ngữ cảnh, nên thực chất đã là ba điều kiện. Luật dài hơn từng được thử và phần lớn là học
vẹt. Lợi ích: không mất điểm (luật một điều kiện và hai điều kiện chênh dưới 0,25 điểm) mà giữ được quá trình tìm
luật đầy đủ, nhanh (74 giây).

**Task 1 — chuỗi lọc luật.** Hai bước tạo điểm rõ nhất là chấm lại luật trên tập xác nhận (+0,63), vì loại được
luật chỉ đẹp trên dữ liệu đã dùng để tìm nó, và so lift trong từng nhóm ngữ cảnh (+0,57), vì tỷ lệ nền đổi theo
ngữ cảnh. Các cổng support, số bài và Benjamini–Hochberg không đổi điểm nhưng giữ bộ luật gọn; riêng cổng "điều kiện
thứ hai phải có ích" ngăn bộ luật phình từ 54.719 lên 433.323 luật.

**Task 2 — mô hình nhiễu.** Mô hình nhiễu cho biết nên tin nhãn đang thấy đến đâu. Lợi ích: đây là thành phần quan
trọng nhất; thiếu nó, repair phá hàng loạt cạnh đúng và macro-F1 còn thấp hơn lúc chưa sửa (27,47% với đầu ra Task 1,
43,58% với nhiễu 10%).

**Task 2 — tam giác.** Mọi lần sửa đều đến từ tam giác; không có phần tam giác thì không cạnh nào được đổi. Lợi ích:
tam giác là nguồn bằng chứng duy nhất cho biết một cạnh mâu thuẫn với các cạnh xung quanh.

**Task 2 — PMI thay vì tần suất thô.** Tần suất thô thưởng cho cấu hình toàn BEFORE chỉ vì BEFORE phổ biến; PMI chỉ
thưởng sự kết hợp nhãn hợp lý. Lợi ích: giữ được nhãn hiếm; dùng tần suất thô thì macro-F1 của đầu ra Task 1 thấp hơn
lúc chưa sửa dù giảm được nhiều lỗi hơn.

**Task 2 — chia trung bình theo số tam giác.** Một cạnh có thể nằm trong rất nhiều tam giác; cộng thẳng để những cạnh
đó lấn át. Lợi ích: phá ít cạnh đúng hơn, tốt hơn cộng thẳng ở cả hai bối cảnh.

**Task 2 — làm yếu prior bằng γ.** Khi mô hình nhiễu chỉ là ước lượng (đầu ra Task 1), Bayes thuần đổi nhãn hiếm
thành BEFORE; γ = 0,5 tránh điều đó. Khi cách sinh nhiễu biết chính xác, Bayes thuần lại tốt hơn. Vì vậy γ được
chọn theo dữ liệu chứ không cố định. Lợi ích: thích nghi với từng nguồn lỗi.

**Task 2 — làm trơn λ.** λ kéo cấu hình ít dữ liệu về mức "không phán xét". λ = 10 là giá trị đặt trước; ablation
cho thấy chưa tối ưu, nên ghi thẳng ra như một tham số còn có thể chọn theo dữ liệu.

**Task 2 — auditor** (đang chạy): lý do có tầng đường đi, luật liên tầng, cổng thích ứng, học theo nhóm (loại cạnh,
nhãn hiện tại). Có số sẽ bổ sung.

---

## Phụ lục A. Bảng ablation

**Bảng A1. Ablation Task 1** (EV–EV, macro-F1 valid)

| Biến thể | Số luật | Macro-F1 |
|---|---|---|
| **Pipeline** (Wilson, ngưỡng riêng từng nhãn, độ sâu ≤ 2), cùng lưới ngưỡng | 54.719 | **27,09** |
| · confidence thô (tập xác nhận) | | 26,18 |
| · confidence thô (tập khám phá) | | 26,09 |
| · lift | | 24,05 |
| · một ngưỡng chung cho mọi nhãn | | 22,74 |
| · chỉ luật 1 điều kiện | 6.624 | 27,23 |
| · chỉ luật 2 điều kiện | 48.095 | 27,01 |
| **Pipeline** (lưới ngưỡng chính thức) | 54.719 | **26,99** |
| · bỏ bước chấm lại trên tập xác nhận | 92.773 | 26,36 |
| · bỏ chia nhóm ngữ cảnh (view) | 6.140 | 26,42 |
| · bỏ cổng "đúng ở ≥ 5 bài" | 57.970 | 26,85 |
| · hạ support (n ≥ 10, k ≥ 3) | 62.574 | 26,93 |
| · bỏ Benjamini–Hochberg | 57.004 | 26,98 |
| · bỏ cổng Δlogit | 433.323 | 27,30 |


**Bảng A2. Ablation mô hình tam giác** (macro-F1 valid)

| Biến thể | Đầu ra Task 1 | Mọi loại cạnh 10% |
|---|---|---|
| Chưa sửa | 30,84 | 68,46 |
| **Pipeline** (PMI, λ = 10, mô hình nhiễu, cách cân trung bình) | **31,36** | **84,92** |
| · không tam giác (β = 0) | 30,84 | 68,46 |
| · không mô hình nhiễu | 27,47 | 43,58 |
| · tần suất thô thay PMI | 29,71 | 83,42 |
| · cộng thẳng thay cách cân trung bình | 28,68 | 83,32 |
| · γ = 0 (Bayes thuần) | 28,78 | 86,80 |
| · λ = 0 (không làm trơn) | 31,27 | 86,79 |
| · λ = 100 | 31,58 | 86,32 |


---

## Cần quyết định

1. **Baseline cho Task 1.** Ba hướng: (a) dẫn số RoBERTa trong paper MAVEN-ERE và ghi rõ khác thước đo, khác cách
   chia; (b) huấn luyện một classifier có giám sát trên cùng đặc trưng; (c) chỉ giữ baseline nội bộ (bộ 257 luật cũ:
   25,60% EV–EV; classifier không có luật liên tầng).
2. **Có giữ "nhiễu mọi loại cạnh" không:** phần Dataset hiện chỉ mô tả nhiễu EV–EV.
3. **Case study *Nicaragua*:** giữ ở Methodology, hay chuyển thành mục cuối của Experiments như PaTeCon.

## Đã sửa trong `main.tex` (đã kiểm tra với dữ liệu và code; bản gốc lưu ở `main.tex.bak`)

| Chỗ | Trước | Sau | Căn cứ |
|---|---|---|---|
| Dataset | bốn nhãn hiếm "under 1.5%" | **1.7%** | 1.474 + 1.570 + 69 + 34 = 3.147 / 188.924 cạnh |
| Rule Mining | "41 conditions on average, drawn from five tiers…" | **48.8** điều kiện mỗi cặp sự kiện, gồm loại sự kiện, vai trò và thực thể chung, vị trí, số lần nhắc | đếm trên dữ liệu đã mã hoá (train 48,84; valid 48,79); năm tầng chỉ thuộc luật liên tầng |
| Rule Mining | luật 5/5 "may be right only 60%" | cận dưới Wilson chỉ **0,57** | công thức Wilson với k = n = 5 |
| Rule Mining | luật 2 điều kiện "beating its own one-condition prefix" | phải hơn **luật con tốt hơn** trong hai luật con ít nhất 0,5 logit | code `mine_unit` (so với max của hai điều kiện con) |
| Rule Mining | "The document filter matters most … one or two documents" | bỏ "matters most"; sửa thành "two or three documents"; thêm bước chấm lại trên tập xác nhận | ablation: cổng số bài chỉ +0,14, chấm lại +0,63; RULESET ghi "2–3 document" |
| Phương trình dự đoán | w(P, r) > τ | **≥** τ | code combiner dùng ≥ |
| Rule Mining | ngưỡng "0.5 … to 0.15" | thêm **0.1 cho OVERLAP**; ghi BEGINS-ON / ENDS-ON bị tắt | ngưỡng chọn trên tập chọn ngưỡng: CONT 0,5 · SIMU 0,15 · OVER 0,1 |
| Rule Mining | set cover "without changing a single prediction" | giữ đúng mọi dự đoán **trên dữ liệu dựng bộ luật**, và ≥ 99,97% trên valid | RULESET §12: valid giữ nguyên 99,979–100% |
| Graph Repair | "a fixed lift of 1.5 is unreachable" | lift cố định **2** mới đòi precision trên 100%; ghi công thức cổng thích ứng | 2 × 0,57 > 1, còn 1,5 × 0,57 < 1 |
| Graph Repair | 74,6% lỗi Task 1 nằm trong cấu hình chưa gặp | ghi rõ đo trên **phiên bản classifier trước** | tài liệu gốc ghi "đo với classifier cũ" |
| Graph Repair | "We set γ = 0.5 throughout" | **chọn** β ∈ {0,2; 0,5; 1; 2} và γ ∈ {0; 0,5} theo macro-F1 | fake_data 5% và 10% chọn γ = 0 |
| Graph Repair | "each accepted update lowers the energy … terminates" | dừng sau tối đa 4 lượt; bảo đảm giảm năng lượng chỉ đúng với cách cộng thẳng, cách chia trung bình là xấp xỉ | code `repair`: tối đa 4 lượt, cách cân "mean" |

Không đổi: số cạnh 792.445 / 188.928 (đúng với bản phát hành MAVEN-ERE), bảng mức nhiễu, các tỷ lệ theo loại cạnh,
mô tả Task, ví dụ Nicaragua (2,59 và 9,66 nats khớp với tính toán thật).
