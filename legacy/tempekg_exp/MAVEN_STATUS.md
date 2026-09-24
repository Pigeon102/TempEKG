# MAVEN cho task temporal — điểm mạnh, vướng mắc, trạng thái

---

# 1. ĐIỂM MẠNH của MAVEN (những thứ Wikidata KHÔNG có)

## 1.1 Dư thừa nhiều lớp annotation — cho phép đo precision không cần gán nhãn

| | |
|---|---|
| Cặp event được ràng buộc bởi **≥2 nguồn độc lập** | **489,071 = 81.8%** |
| Nguồn | S1 temporal · S2 causal · S3 subevent · S4 closure |

> Wikidata mỗi fact **một nguồn** → PaTeCon buộc phải viết *"precision is not calculated"*.
> MAVEN có 4 lớp annotate độc lập → **held-out source precision** chạy được.

**Đây là điểm mạnh lớn nhất và không thể sao chép sang KG thực thể.**

## 1.2 Constraint NGỮ NGHĨA — đúng theo định nghĩa, không phải thống kê

$$\textsf{subevent}(e_1,e_2) \Rightarrow \textsf{contains}(t_1,t_2)$$
$$\textsf{CAUSE}(e_1,e_2) \Rightarrow \neg\,\textsf{after}(t_1,t_2)$$

Wikidata **không có gì tương đương**: `P569 before P570` đúng vì sinh học, nhưng KG không
*khai báo* quan hệ ngữ nghĩa nào giữa hai property — phải mine từ tần suất.

Precision của lớp này **~100% theo cấu tạo**. Đo được: bắt **14/14** conflict cứng trên EVAL.

## 1.3 Entity cho sẵn ở MỌI split, kể cả blind test

`entities` (id, 7 kiểu, offset) có trong cả `test.jsonl`. **Không phải dự đoán coreference.**

## 1.4 Quy mô quan hệ thời gian lớn

593,433 cặp event–event có quan hệ · 66,418 anchor TIMEX · 20,827 TIMEX span.

## 1.5 Gold nhất quán tuyệt đối — là TÀI SẢN để validate

0 chu trình, 0 vi phạm đối xứng, **100.0% đóng kín bắc cầu** (thiếu 7/6,718,279).
→ Tập validation hoàn hảo cho constraint mine được (đo: giữ **86.1%** trên document chưa thấy).

---

# 2. VƯỚNG MẮC

## 2.1 Chí mạng: TIMEX không có giá trị chuẩn hoá

MAVEN-ERE cho **span**, không cho **value**. Phải tự chuẩn hoá.

| | |
|---|---|
| Độ phủ normaliser hiện tại | **75.7%** |
| ├ regex thuần (đáng tin) | 63.1% |
| ├ reference-propagation | 11.6% — **tỉ lệ conflict cao gấp 3×** ⇒ nhiễu |
| └ gazetteer | 1.0% |
| Chưa giải được | 24.3% ("recent years", "this time", số trần) |

**Hệ quả đo được:** T5 thô ra 933 conflict, nhưng chỉ **336 đáng tin** (từ anchor regex thuần).
Không tự lọc thì **sai 2.8×**.

## 2.2 Chỉ 44.9% event có anchor thời gian

27.2% chỉ có cận lỏng, **27.9% không có anchor nào**. Với những event đó mọi vị từ thời gian
trả về `unknown`.

## 2.3 T4 disjointness gần như không tồn tại — tính chất substrate

| anchor | cặp | chồng nhau | constraint giữ lại |
|---|---|---|---|
| mức năm | 48,785 | 83.2% | **0** |
| mức ngày/tháng (rộng TB 10.2 ngày) | 22,689 | **88.1%** | **1** |

Dùng anchor mịn hơn **không cứu được** — chồng nhau còn tăng. Lý do: event đồng tham dự trong
**cùng một bài báo** thường **thực sự đồng thời**. Đây là tính chất của dữ liệu tin tức, không
phải lỗi độ chính xác.

Constraint duy nhất tìm được: `(Killing, Legal_rulings)` conf 1.000, n=39 — hợp lý về ngữ nghĩa.

## 2.4 Entity cục bộ theo document

**0/68,348** entity vượt document. Làm entity-level confidence của PaTeCon **suy biến** thành
fact-level. Buộc mine ở **type level**.

## 2.5 Chiếu nhị phân làm nổ vocabulary

`EventType#Role` = **459 property** (Wikidata temporal: 6). PaTeCon $O(|R_t|^2|R|)$:

| | property | index | kết quả |
|---|---|---|---|
| WD50K | 6 | 216 | 1.1 giây |
| MAVEN | **459** | **96.7 triệu** (~40 GB) | **>30 phút, bị giết** |
| MAVEN rút gọn | 151 | 3.4 triệu | ~3 phút |

## 2.6 Mutual exclusion bị bẫy bởi SỰ KIỆN LẶP LẠI

487 ứng viên thô. Phân loại đúng: **96.8% hợp lệ** (RECURRING 61.3%, CONTINUOUS 32.4%,
PERIODIC 3.2%), chỉ **11 đáng ngờ**.

> Trên đồ thị event, confidence cao của mutual exclusion phản ánh **sự thưa của annotation**,
> không phải tính hàm thật. Wikidata `P569` thì thật sự là hàm — MAVEN `Competition` thì không.

## 2.7 Không có tập gán nhãn đúng/sai

Không thể tính recall kiểu WD-411 trên MAVEN. Cần ~3 person-day gán nhãn thủ công, hoặc hai
phiên bản annotation (không có).

## 2.8 Gold quá sạch cho task phát hiện conflict

Chỉ **72** mâu thuẫn toàn corpus. Mining conflict *trong gold* gần như không có mục tiêu.
Conflict thật nằm ở **đồ thị dự đoán**: đo được **85,243** vi phạm bắc cầu + **735** chu trình
(77% / 26% document).

---

# 3. TRẠNG THÁI HIỆN TẠI

| Loại | Trạng thái trên MAVEN | Số |
|---|---|---|
| T1 representation | ❌ không áp dụng (không có interval tường minh) | — |
| T2 mutual exclusion | ✅ có, kèm lọc lặp lại | 487 → **11** |
| T3 ordering | ✅ | **72** (xác nhận 2 lần độc lập) |
| T4 disjointness | ⚠️ gần như không tồn tại | **1** constraint |
| T5 granularity | ✅ | **336** đáng tin |
| Mức C (đồ thị dự đoán) | ⏳ chưa làm | target **85,243** |

---

# 4. ĐÁNH GIÁ THẲNG: MAVEN có phù hợp không?

## Phù hợp cho

✅ **Đo precision không cần annotate** — 81.8% dư thừa, không substrate nào khác có
✅ **Constraint ngữ nghĩa** — subevent/causal cho lớp cứng precision ~100%
✅ **Nghiên cứu conflict trên output MODEL** — 85,243 target, quy mô lớn nhất
✅ **T5 granularity ở cấp event** — 17,102 event đa-anchor

## KHÔNG phù hợp cho

❌ **T4 disjointness** — event đồng tham dự thường đồng thời (88.1% chồng)
❌ **T2 kiểu Wikidata** — không lưu giá trị thuộc tính lặp
❌ **Mining constraint thống kê** — precision 0.00% so với chuẩn cứng
❌ **So recall với PaTeCon** — không có tập gán nhãn

## Kết luận

> **MAVEN mạnh ở chỗ Wikidata yếu (dư thừa nhiều lớp, constraint ngữ nghĩa) và yếu ở chỗ
> Wikidata mạnh (giá trị thời gian tường minh, thuộc tính hàm thật, tập gán nhãn).**

Nên **không nên** cố lặp lại thí nghiệm của PaTeCon trên MAVEN — đã thử, cho 348 constraint
mà **67% là artifact** của granularity năm. Nên **khai thác đúng điểm mạnh**: held-out
precision, lớp constraint cứng, và conflict trên đồ thị dự đoán.
