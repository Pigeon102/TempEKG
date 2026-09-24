# Dữ liệu hiện tại bị gì — bằng chứng và hệ quả

**Câu hỏi:** đề tài bắt buộc làm temporal conflict. Vậy dữ liệu bị gì, số liệu ở đâu,
và vì sao cách đang làm không chạy được?

**Trả lời ngắn:** làm được, nhưng **không phải trên gold**. Gold không có conflict để tìm.
Conflict nằm ở **dữ liệu dự đoán** — và đó là chỗ chưa ai đào.

---

## 1. Vấn đề gốc: gold gần như không có conflict

### Bằng chứng (2 đường đo độc lập, cùng kết quả)

**Đường 1** — audit trực tiếp trên toàn bộ 3,623 document:

```
BEFORE cycles                    : 0        (tren 843,808 cap)
vi pham doi xung a<b va b<a      : 0
BEFORE dong kin bac cau a<b<c=>a<c: 100.0%  (thieu 7 / 6,718,279)
```

**Đường 2** — mining kênh C2 (EXP6), đo lại độc lập:

```
CAUSE        : 3 vi pham / 8,420
PRECONDITION : 8 vi pham / 37,594
SUBEVENT     : 61 vi pham / 12,019
--------------------------------
TONG         : 72 vi pham
```

Hai đường ra **đúng cùng con số 72**. Đây không phải sai số đo.

### Vì sao gold sạch như vậy

MAVEN-ERE được annotate **dưới ràng buộc đóng bắc cầu**. Annotator không được để lại mâu
thuẫn. Nên gold **nhất quán theo cấu tạo**, không phải tình cờ.

### Hệ quả

Mục tiêu "mine constraint rồi phát hiện conflict trong dataset" có **~72 mục tiêu trên
toàn corpus**. Không đủ để làm precision/recall, không đủ để làm benchmark.

> ⚠️ Nhưng chú ý: **1,577 cặp subevent thiếu CONTAINS ngụ ý** (13.6%). Đó là **thiếu sót**,
> không phải mâu thuẫn — gấp **22 lần** số conflict thật. Nếu định nghĩa lại bài toán theo
> hướng "phát hiện quan hệ thiếu" thì target lớn hơn hẳn.

---

## 2. Vấn đề thứ hai: mining không thêm thông tin

Đây là kết quả riêng, độc lập với vấn đề 1.

| Thí nghiệm | Kiểm chứng | Kết quả |
|---|---|---|
| EXP13 | C1 (chia sẻ participant — đúng kiểu PaTeCon) | **không bao giờ** bất đồng với majority |
| EXP14 | 636 signature C2 theo kiểu event | lãi ròng **+0** |
| EXP15 | kiểu event, khoảng cách câu, TIMEX anchor | lãi ròng **+0** trên 109,666 cặp |

**Toàn bộ tín hiệu học được nằm trong 6 luật:**

```
(CAUSE,        FWD) -> BEFORE_FWD     71.8%
(CAUSE,        REV) -> BEFORE_REV     77.2%
(PRECONDITION, FWD) -> BEFORE_FWD     93.2%
(PRECONDITION, REV) -> BEFORE_REV     88.7%
(SUBEVENT,     FWD) -> CONTAINS_FWD   99.0%
(SUBEVENT,     REV) -> CONTAINS_REV   97.9%
```

### 🔑 Nhưng đây KHÔNG phải lý do không làm được

**Điểm mấu chốt bị hiểu nhầm ở bản kết luận trước:** "6 luật tầm thường" là kết quả xấu cho
**MINING**, nhưng là kết quả **TỐT** cho **DETECTION**.

Một detector không cần mới lạ — nó cần **đáng tin**. Luật `SUBEVENT → CONTAINS` đúng
**99.0%** nghĩa là: bất kỳ đồ thị nào có cặp subevent **không** phải CONTAINS thì **99% là
sai**. Đó là một detector xuất sắc.

Ta **đã có** bộ constraint đã kiểm chứng held-out ở 95–100%. Cái thiếu là **đối tượng để
áp vào**.

---

## 3. Vấn đề thứ ba: thiếu thời gian tuyệt đối

| | Số đo |
|---|---|
| Event có TIMEX anchor chặt | **44.9%** (37,852) |
| Chỉ có cận lỏng | 27.2% |
| Không có anchor nào | 27.9% |
| TIMEX có giá trị chuẩn hoá sẵn | **0** — chỉ có chuỗi bề mặt |

TIMEX normaliser: 62.1% xử lý được bằng regex, 37.9% cần ngữ cảnh (4 họ xử lý được),
ước tính **~1 tuần**. Chưa xây.

---

## 4. Vấn đề thứ tư: entity cục bộ theo document

```
entity xuat hien o >1 document : 0 / 68,348
event / entity                 : trung binh 3.15
```

Làm **entity-level confidence của PaTeCon suy biến** thành fact-level. Đây vừa là hạn chế
vừa là đóng góp lý thuyết duy nhất sống sót qua hostile review.

---

## 5. Vậy làm temporal conflict thế nào?

### Chỗ conflict THẬT SỰ tồn tại: dữ liệu dự đoán

Đã kiểm tra — dữ liệu dự đoán **có sẵn trong repo**:

| File | Nội dung |
|---|---|
| `MAVEN_Arg_Pipeline (1)/data/ed_preds/dev_triggers.jsonl` | 710 doc, trigger dự đoán + score |
| `MAVEN_Arg_Pipeline (1)/exps/pipeline_infer/dev_predictions.jsonl` | 6,034 dự đoán pipeline |
| `mavenarg-base_seed48/validation_predictions_span.jsonlines` | 16,996 PAIE span trên gold trigger |

**Bằng chứng conflict tồn tại — dòng đầu tiên của pipeline output:**

```json
{"event_type": "Attack", "roles": {"Agent": ["British"], "Consequence": ["British"],
                                   "Location": ["British"], "Patient": ["British"]}}
```

Cùng span `"British"` điền **cả 4 vai** Agent / Consequence / Location / Patient. Một địa
điểm không thể đồng thời là tác nhân và bệnh nhân. Đây là conflict thật, quan sát được ngay,
trong dữ liệu thật.

### Ba mức khả thi, xếp theo chi phí

| Mức | Cần gì | Có sẵn? | Target |
|---|---|---|---|
| **A. Role-consistency conflict** | chỉ argument dự đoán | ✅ **có ngay** | mọi event dự đoán |
| **B. Subevent/causal conflict** | quan hệ C2 + interval | ⚠️ cần normaliser (~1 tuần) | 58,033 cặp |
| **C. Temporal ordering conflict** | mô hình dự đoán quan hệ thời gian | ❌ **chưa có trong repo nào** | 593,433 cặp |

**Mức A chạy được ngay hôm nay** và cho số liệu thật từ mining thật.
**Mức C** — đúng nghĩa "temporal conflict" đầy đủ — đòi một thành phần mới: mô hình temporal
relation extraction. Không repo nào (`PAIE_Maven`, `DEEIA_Maven`, `SCPRG`, `TSAR_Maven`,
`MAVEN_Arg_Pipeline`) có nó; grep `temporal_relations|TIMEX|BEFORE` chỉ ra **1 comment code**.

---

## 6. Kết luận thẳng

**Không phải "không làm được".** Là ba điều cụ thể:

1. **Gold sai chỗ để tìm conflict** — 72 cái, đo hai lần độc lập. Phải chuyển sang dữ liệu
   dự đoán, nơi conflict thật tồn tại và đã quan sát được.
2. **Mining không sinh ra constraint mới** — nhưng ta **đã có** 6 constraint đạt 95–100%
   held-out. Đủ để làm detector. Đóng góp phải nằm ở *phát hiện + đánh giá*, không ở *khai phá*.
3. **Thiếu 1–2 thành phần** để lên mức đầy đủ: TIMEX normaliser (~1 tuần, đã đo độ khó) và
   temporal relation model (chưa có, là hạng mục lớn nhất).

Việc nên làm tiếp: **chạy mức A ngay** để có số liệu conflict thật trên dữ liệu dự đoán, rồi
quyết định có đầu tư vào mức B/C trong 43 ngày còn lại không.
