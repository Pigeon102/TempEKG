# KẾT QUẢ — Held-out source precision, T2 có xét lặp lại

Chạy thật trên MAVEN-Arg + MAVEN-ERE. Code: `tempekg.py`, `tempekg_eval.py`.

---

## 1. Đồ thị đã dựng

```
event                : 84,285
canh rang buoc       : 1,109,655
   S1 temporal (hard, annotation) : 593,477
   S2 causal   (hard, ngu nghia)  :  46,014
   S3 subevent (hard, ngu nghia)  :  12,019
   S4 closure  (hard, logic)      : 458,145
```

`source` nằm trong khoá chính → hold-out được. Đây là cấu trúc FRAMEWORK.md §3 yêu cầu.

---

## 2. HELD-OUT SOURCE PRECISION — giao thức mới

**Thiết kế:** DETECTOR = S5 (constraint mine được, mềm). VERIFIER = S2/S3/S4 (cứng, ngữ
nghĩa + logic). S5 **chỉ mine từ S1**, không đụng S2/S3/S4 → **không vòng lặp**.

Chia 80/20 theo document. S5 mine được **7,130 luật** (Wilson ≥ 0.7, support ≥ 10).

### Kết quả trên 725 document EVAL

| | số cặp |
|---|---|
| DETECTOR S5 (mềm) gắn cờ | **4,874** |
| VERIFIER S2/S3/S4 (cứng) gắn cờ | **14** |
| **giao nhau** | **0** |
| **PRECISION của S5** | **0.00%** |
| **RECALL của S5** | **0.00%** |
| tỉ lệ nền (random) | 0.0117% |

**Kiểm chứng chéo:** 14 conflict cứng trên EVAL khớp với 72 toàn corpus × 20% ≈ 14. ✅

### Diễn giải — kết quả âm tính, nhưng đo được

**Constraint mine bằng thống kê KHÔNG phát hiện được lỗi thật.** Giao nhau bằng **0** tuyệt
đối: 4,874 cặp S5 gắn cờ và 14 cặp nguồn cứng gắn cờ **không trùng một cặp nào**.

Lý do: hai thứ khác bản chất.

| | S5 gắn cờ khi | Nghĩa là |
|---|---|---|
| **mềm (thống kê)** | quan hệ khác với đa số của cặp loại event | **bất thường**, không phải sai |
| **cứng (ngữ nghĩa)** | vi phạm định nghĩa quan hệ (con nằm ngoài cha) | **sai chắc chắn** |

> Đây là xác nhận cuối cùng, bằng giao thức sạch nhất, cho điều EXP13–15 đã chỉ ra:
> **mining thống kê trên substrate này không tìm ra lỗi thật.**

### Vì sao kết quả này vẫn có giá trị công bố

**PaTeCon không thể chạy thí nghiệm này.** Họ tự viết *"precision is not calculated"* vì
Wikidata mỗi fact chỉ một nguồn. Ta đo được vì MAVEN có **81.8% cặp ≥2 nguồn độc lập**.

Kết luận rút ra: **giá trị nằm ở lớp CỨNG, không ở lớp mine.** Lớp cứng có precision ~100%
theo cấu tạo (chúng đúng theo định nghĩa quan hệ), và bắt được 14/14 conflict trên EVAL.

---

## 3. T2 MUTUAL EXCLUSION — có xét sự kiện lặp lại

Vấn đề người dùng chỉ ra: hội thảo thường niên, giải đấu hàng năm — cùng entity, cùng loại
event, thời gian khác nhau → **không phải lỗi**. PaTeCon sẽ gắn cờ hết.

### Số đo

| | số cặp | tỉ lệ |
|---|---|---|
| ứng viên thô (PaTeCon gắn cờ hết) | 487 | 100% |
| **loại vì LẶP LẠI hợp lệ (cách ≥3 năm)** | **284** | **58.3%** |
| còn lại thực sự đáng ngờ | 203 | 41.7% |

**→ Trần precision của T2 thô: 41.7%.** Tức nếu áp MutualExclusion kiểu PaTeCon lên đồ thị
event, **gần 6/10 cảnh báo là sai**.

### Loại event bị loại nhiều nhất

```
Hostile_encounter  48    Competition  43    Social_event  42
Hold               12    Catastrophe  12
```

Ví dụ thật: một entity dự `Social_event` các năm **[2006, 2012, 2014, 2016]** — rõ ràng là
sự kiện định kỳ.

### Đối chiếu với Wikidata

| | Wikidata `P569` (ngày sinh) | MAVEN `Competition` |
|---|---|---|
| Có thật sự là hàm không? | ✅ đúng một giá trị | ❌ lặp lại là bình thường |
| Confidence cao có nghĩa gì? | tính hàm thật | **chỉ là dữ liệu thưa** |

> **Trên đồ thị event, confidence cao của mutual exclusion thường phản ánh SỰ THƯA của
> annotation, không phải tính hàm thật.** Đây là bẫy mà PaTeCon không gặp trên Wikidata,
> vì `P569` thật sự là thuộc tính hàm.

---

## 4. ⚠️ GHI CHÚ ĐỂ XỬ LÝ SAU — trùng đúng future work của PaTeCon

Bộ lọc hiện tại dùng ngưỡng thô **≥3 năm**. Chưa đủ. Cần phân biệt ba trường hợp:

| Trường hợp | Ví dụ | Hiện xử lý |
|---|---|---|
| **Lặp lại định kỳ** | họp thường niên, giải hàng năm | ⚠️ ngưỡng 3 năm — thô |
| **Sự kiện kéo dài** | chiến tranh nhiều năm | ❌ chưa |
| **Lỗi thật** | hai ngày cho cùng một lần | ⚠️ lẫn với hai loại trên |

**Hướng xử lý (chưa làm):**
- Phát hiện **chu kỳ**: các năm cách đều nhau ⇒ định kỳ, không phải lỗi
- **Ràng buộc định lượng** $t_2 - t_1 \ge \Delta_{\text{type}}$: học ngưỡng riêng cho từng
  loại event thay vì dùng chung 3 năm
- Dùng **granularity** để phân biệt: `Competition` neo ở năm khác nhau = định kỳ;
  neo cùng năm nhưng ngày khác = có thể lỗi

Đây **chính là future work PaTeCon tuyên bố** (§8):

> *"the predicates can be broadened to encompass quantitative relationships, such as
> $t_2 - t_1 \le 10\ \text{years}$... **Future work** includes exploring extensions"*

Nên nếu giải quyết được, đó là đóng góp **trực tiếp lấp chỗ họ để ngỏ**.

---

## 5. Trạng thái so với mục tiêu

| Mục tiêu | Trạng thái |
|---|---|
| Recall ≥ PaTeCon | ⚠️ chưa — cần cài T2/T4 đầy đủ |
| **Precision đo được** | ✅ **làm được — họ không thể** |
| Precision cao hơn họ | ⚠️ lớp **mềm: 0%**; lớp **cứng: ~100%** → phải dùng lớp cứng |
| Bao phủ T1–T5 | T1 ✅ · T2 ✅ (có lọc lặp lại) · T3 ✅ · T4 ⏳ · T5 ⏳ cần normaliser |

**Điều chỉnh hướng dựa trên số:** đóng góp không nằm ở *mine constraint tốt hơn*, mà ở
**(a) giao thức đo precision không cần annotate**, **(b) lớp constraint cứng từ ngữ nghĩa
quan hệ**, **(c) xử lý sự kiện lặp lại mà họ để ngỏ**.
