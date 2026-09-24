# Bỏ ERE khi inference — kết quả đầy đủ

**Đề xuất của bạn:** ERE chỉ dùng để **học** ra constraint. Khi mining/phát hiện thì chỉ dùng
**graph** (event + argument + TIMEX + vị trí văn bản), không dùng nhãn ERE.

Đây là kịch bản triển khai thật — document mới không có annotate ERE.

**Kết luận ngắn:** ý tưởng đúng, nhưng đo được **ngưỡng cứng chưa đạt**. Cần chất lượng gán
TIMEX **p ≥ 0.841**; hiện đạt **0.514**. Dưới ngưỡng đó thì detection hỏng hoàn toàn
(đã thử 4 cách, đều thất bại), mining chỉ trùng ~50%.

---

# 1. Vấn đề: toàn bộ tầng ràng buộc phụ thuộc nhãn

| nguồn | đến từ đâu | có ở document mới không? |
|---|---|---|
| S1 temporal | **nhãn ERE** | ❌ |
| S2 causal | **nhãn ERE** | ❌ |
| S3 subevent | **nhãn ERE** | ❌ |
| S4 closure | suy từ S1 | ❌ |
| TIMEX→event (CONTAINS) | **nhãn ERE** | ❌ |

Thành phần cần thay quan trọng nhất: **gán TIMEX cho event** — nguồn của mọi interval.

---

# 2. Năm cách thử — tiến trình chất lượng gán TIMEX

| # | cách | gán TIMEX P/R/F1 | T5 conflict rate | T5 vs gold F1 |
|---|---|---|---|---|
| 1 | TIMEX gần nhất | — (1 anchor) | **không chạy được** | — |
| 2 | tất cả TIMEX trong câu | — | 77.3% | — |
| 3 | perceptron, đặc trưng vị trí | 54.0 / 24.1 / **33.4** | 72.5% | **8.3%** |
| 4 | LR + đặc trưng từ vựng | 46.5 / 45.1 / **45.8** | 58.8% | **9.3%** |
| 5 | **ranking loss (softmax ứng viên)** | 43.2 / 52.9 / **47.5** | 51.2% | — |

Gold: conflict rate **16.1%**.

Đặc trưng từ vựng (giới từ trước TIMEX, trigger word, hạng khoảng cách, từ ở giữa) nâng
gán TIMEX **+12.4 điểm F1**, độ phủ khớp gold (35.0% vs 32.9%). **Nhưng T5 gần như không
cải thiện.**

Ranking loss (mỗi event chọn anchor từ tập ứng viên cạnh tranh, có lựa chọn `NULL`) thêm
**+1.7 điểm F1**, recall tốt hơn hẳn (45.1% → 52.9%).

## ⚠️ Trần precision của đặc trưng thủ công

Quét ngưỡng trên model ranking:

| theta | P | R |
|---|---|---|
| 0.20 | 40.6% | 54.2% |
| 0.50 | 57.7% | 29.6% |
| 0.70 | 67.5% | 16.3% |
| **0.80** | **71.7%** | 10.3% |

> **Trần ~72% precision** ngay cả khi hi sinh gần hết recall. Ba họ model độc lập
> (perceptron / LR / listwise ranking) đều chững ở F1 **46–48%**.
> Ngưỡng cần là **84%** → **không với tới được bằng đặc trưng thủ công.**

## Đặc trưng mạnh nhất mà model học được

```
et = Causation        -5.094      trig_prep = contested>on  +2.240
et = Participation    -2.801      trig_prep = event>on      +2.005
et = Aiming           -2.364      trig_prep = event>in      -1.805
```

Model học đúng ngữ nghĩa: event trừu tượng (Causation, Participation) **không** có mốc thời
gian; giới từ `on` sau trigger cụ thể thì **có**.

---

# 3. ⭐ LUẬT KHUẾCH ĐẠI LỖI — phát hiện chính

T5 precision **không đổi** dù gán TIMEX cải thiện từ 37% lên 76%:

| theta | gán TIMEX P | **T5 P** |
|---|---|---|
| 0.20 | 37.1% | 5.0% |
| 0.40 | 53.3% | 5.5% |
| 0.50 | 60.4% | 9.5% |
| 0.70 | 76.1% | **0.0%** |

Vì T5 là phép **giao ≥2 anchor** — một anchor sai là lật kết quả:

$$\text{rate}_{\text{obs}} = p^2 \cdot r + (1-p^2)\cdot q$$

- $p$ = precision gán TIMEX
- $r$ = tỉ lệ conflict thật (gold) = **0.161**
- $q$ = tỉ lệ hai mốc **ngẫu nhiên** cùng document rời nhau = **0.712** (đo trên 6,468 cặp)

## Kiểm chứng thực nghiệm

| | |
|---|---|
| $p$ đo được | 0.514 |
| **dự đoán** $p^2 r + (1-p^2)q$ | **0.567** |
| **quan sát** | **0.550** |
| sai lệch | **0.017** (3%) |

**Luật khớp.** Hệ quả trực tiếp:

> Để tỉ lệ conflict ≤ 2× gold, cần $p \ge \mathbf{0.841}$.
> Hiện đạt **0.514**. Đây là **ngưỡng cứng**, không phải vấn đề tinh chỉnh.

Đây là kết quả **định lượng, có thể công bố**: giải thích tại sao mọi hệ thống phát hiện
xung đột thời gian dựa trên giao interval đều dễ vỡ khi anchor không hoàn hảo.

---

# 4. Thử cứu detection bằng điểm có trọng số — THẤT BẠI

Theo bài học L3 (AUDIT.md: *xếp hạng thay vì lọc*), thay giao boolean bằng:

$$\text{score}(e) = p_{(1)} \cdot p_{(2)} \cdot \mathbb{1}[\text{giao rỗng}]$$

| top-k | P | R | **lift** |
|---|---|---|---|
| 25 | 4.0% | 0.5% | **0.57×** |
| 50 | 2.0% | 0.5% | **0.28×** |
| 100 | 5.0% | 2.4% | 0.71× |
| 200 | 8.0% | 7.7% | 1.14× |
| tất cả (356) | 7.0% | 12.0% | 1.00× |

**Lift < 1 ở đầu bảng — tệ hơn ngẫu nhiên.** Nguyên nhân: model tự tin cao ⇒ anchor **đúng**
⇒ anchor đúng thì **hiếm khi** xung đột (gold chỉ 16.1%). Điểm số bị **đảo chiều**.

→ Detection ERE-free **hỏng theo hai cách độc lập**. Không cứu bằng hậu xử lý được.

---

# 5. Mining thì sao — lỗi TRIỆT TIÊU thay vì khuếch đại

Giả thuyết: mining gộp qua nhiều cặp nên lỗi ngẫu nhiên tự triệt tiêu.

## 5.1 Tương quan tỉ lệ rời-nhau theo signature

| | |
|---|---|
| signature chung (sup≥5) | 160 |
| **Pearson r** | **0.670** |
| **Spearman** | **0.642** |
| MAE | 0.173 |
| trùng top-10 / top-20 / top-50 | 60% / 55% / **66%** |

**Tốt hơn detection rất nhiều** ở cùng $p = 0.514$ — giả thuyết đúng.

## 5.2 Nhưng tập constraint cuối chỉ trùng một nửa

| cấu hình | GOLD | MODEL | GIAO | **P** | **R** |
|---|---|---|---|---|---|
| sup≥5 conf≥0.90 | 102 | 43 | 23 | **53.5%** | 22.5% |
| sup≥5 conf≥0.95 | 93 | 39 | 21 | 53.8% | 22.6% |
| sup≥10 conf≥0.90 | 25 | 12 | 6 | 50.0% | 24.0% |

## 5.3 Kiểm tra chất lượng không cần annotate — áp constraint lên graph GOLD

Constraint tốt thì **hiếm khi bị vi phạm** trên đồ thị gold:

| constraint mine từ | cặp vi phạm / cặp phủ | **tỉ lệ vi phạm** |
|---|---|---|
| **GOLD (có ERE)** | 13 / 899 | **1.45%** ✅ |
| **KHÔNG-ERE** | 43 / 386 | **11.14%** ❌ |

Chênh **7.7×**. Nửa constraint không trùng là **sai thật**, không phải khác góc nhìn.

> Chỉ số "tỉ lệ vi phạm trên graph gold" là **cách đo chất lượng constraint không cần
> annotate** — cùng mạch với held-out source precision của dự án. Đáng giữ làm công cụ.

---

# 6. Kết luận trung thực

## Ý tưởng ĐÚNG

✅ Kiến trúc "ERE để học, graph để chạy" là kịch bản triển khai đúng — phải làm
✅ Heuristic văn bản cho độ phủ event có anchor cao hơn (97.2% vs 43.8% với 1-anchor)
✅ Model học được ngữ nghĩa thật (Causation → không có mốc; `on` → có mốc)
✅ **Mining chống lỗi tốt hơn detection** — đã chứng minh bằng số (r 0.670 vs lift 1.0)

## Nhưng CHƯA ĐẠT NGƯỠNG

❌ Gán TIMEX **p = 0.514**, cần **p ≥ 0.841** (luật khuếch đại, đã kiểm chứng)
❌ Detection ERE-free hỏng — thử **4 cách**, kể cả xếp hạng có trọng số, đều thất bại
❌ Mining ERE-free: constraint P 53.5%, và nửa còn lại bị vi phạm **11.14%** trên graph gold

## Việc cần làm

| # | việc | vì sao | ước tính |
|---|---|---|---|
| 1 | **Model gán TIMEX neural** (RoBERTa) | trần thủ công 72% < ngưỡng 84%; **cần cài `torch` + `transformers`** | 3–5 ngày |
| 2 | Lan truyền anchor qua S1/S4 | 80.3% event không có mốc; suy cận từ event `BEFORE`/`AFTER` | 2 ngày |
| 3 | Thay S2/S3 bằng model causal/subevent | hai nguồn này cũng phụ thuộc ERE | 1 tuần |

**Mục 1 là nút thắt duy nhất.** Luật ở §3 cho biết chính xác cần đạt bao nhiêu — không phải
đoán mò.

> ⚠️ **Chặn kỹ thuật:** máy hiện **không có** `torch`, `transformers`, `numpy`, `scipy`,
> `sklearn`, `spacy`, `nltk`. Mọi thứ ở trên viết bằng Python thuần. Muốn qua trần 72%
> phải cài thư viện — đây là quyết định của bạn, không tự cài.

## Lộ trình đề xuất

Giữ ERE cho các kết quả hiện tại (đã kiểm chứng, dùng cho bài báo). Song song xây model gán
TIMEX neural. Khi $p \ge 0.84$ thì chuyển pipeline sang chế độ không-ERE và đo lại — luật
§3 cho phép **dự đoán trước** kết quả sẽ ra sao thay vì phải chạy thử.

---

# 7. Đóng góp phụ thu được

1. **Luật khuếch đại lỗi** $\text{rate} = p^2 r + (1-p^2)q$ — kiểm chứng sai lệch 0.017,
   giải thích tính dễ vỡ của mọi detector dựa trên giao interval
2. **Tỉ lệ vi phạm trên graph gold** — đo chất lượng constraint **không cần annotate**
3. **Bất đối xứng detection/mining** — mining chịu lỗi tốt hơn nhiều ở cùng chất lượng anchor;
   nghĩa là ưu tiên triển khai mining trước, detection sau

## File

`exp36_no_ere.py` · `exp37_anchor_model.py` · `exp38_anchor_tuned.py` ·
`exp39_anchor_lex.py` · `exp40_amplify.py` · `exp41_calibrated.py`

## Lỗi bắt được trong lượt này

`exp37` in "dương: 100.0%" — dùng `r[2]` (dict đặc trưng, luôn truthy) thay vì `r[3]` (nhãn).
Chỉ ảnh hưởng dòng thống kê, **không** ảnh hưởng huấn luyện/đánh giá. Tỉ lệ dương thật là
**15.5%**. Đúng quy tắc AUDIT #1: *số đẹp bất ngờ → giả định là bug*.
