# Kiểm tra benchmark `results/` trước khi dùng

**Kết luận: benchmark có rò rỉ trường dữ liệu.** Chỉ so hai cột của cùng một dòng —
`timex_raw` với `time_start` — đã phát hiện **100%** ba trong bốn loại conflict.
Cần sửa trước khi dùng để đánh giá TempEKG, nếu không mọi con số sẽ đến từ phép so cột chứ
không phải từ suy luận đồ thị.

---

## 1. Cấu trúc benchmark

`base` → `LLM` → `final` là **ba bước của pipeline sinh dữ liệu**, không phải kết quả của các
phương pháp khác nhau:

| Tầng | Làm gì | Bằng chứng |
|---|---|---|
| `base` | inject conflict vào trường có cấu trúc (`time_start`) | 2.739 dòng ở mức 20% |
| `LLM` | viết lại `text_span` cho khớp với ngày giả | `refine_strategy`: `zone_rewrite` 263, `passthrough` 151, `+paraphrase` 97 |
| | LLM judge xác nhận bản viết lại | `judge_reason`: *"dates swapped correctly"*, `judge_confidence` 80–95 |
| `final` | thêm `lexical_score` | 2.702 dòng (37 dòng bị loại ở bước LLM) |

Ví dụ một ORDERING_CONFLICT sau khi viết lại:

```
timex_raw   24 September 1898                    ← ngày THẬT, không bị đổi
time_start  1901-05-05                           ← ngày GIẢ
text_span   "...held in Melbourne on May 05, 1901..."   ← đã viết lại cho khớp ngày giả
```

`text_span` và `time_start` nhất quán với nhau — nhưng `timex_raw` vẫn giữ ngày gốc.

## 2. Baseline tầm thường: so `timex_raw` với `time_start`

Không dùng đồ thị, không dùng văn bản, không dùng event khác. Chỉ parse `timex_raw` rồi so với
`time_start` trên cùng dòng:

| Mức nhiễu | n | conflict | P | R | F1 |
|---|---|---|---|---|---|
| 5% | 2.300 | 109 | 64,56% | 93,58% | 76,40% |
| 10% | 2.415 | 224 | 78,29% | 90,18% | 83,82% |
| 15% | 2.554 | 363 | 85,45% | 90,63% | 87,97% |
| 20% | 2.702 | 511 | 89,17% | 90,22% | **89,69%** |

### Theo loại conflict (mức 20%)

| Loại | n | bắt được | recall |
|---|---|---|---|
| ANCHOR_CONFLICT | 174 | 174 | **100,0%** |
| ORDERING_CONFLICT | 161 | 161 | **100,0%** |
| GRANULARITY_CONFLICT | 126 | 126 | **100,0%** |
| IMPLICIT_ORDERING | 50 | 0 | **0,0%** |

### Toàn bộ 56 false positive là lỗi parser của tôi, không phải conflict thật

```
raw "4–5 January 1919"        → time_start 1919-01-05   parser đọc thành ngày 4
raw "17:40 p.m., March 16"    → time_start 1957-03-16   parser đọc "17" từ giờ
```

Số FP **không đổi (56) ở cả bốn mức nhiễu** — đúng dấu hiệu của lỗi hệ thống ở ground truth,
không phải nhiễu. Với parser tốt hơn (xử lý khoảng ngày, bỏ qua giờ), FP → gần 0 và baseline
tầm thường đạt **~100% trên ba loại**.

### IMPLICIT_ORDERING là loại duy nhất thật sự khó

50 dòng, recall 0%. Loại này không đổi `time_start` — chỉ đổi từ nối trong văn bản
(`when` → `after`). 43/50 có `time_start` bằng `timex_raw`, 7/50 không có `time_start`.
Phát hiện nó cần **hiểu văn bản**, không so cột được.

## 3. Hệ quả

Nếu chạy TempEKG trên benchmark này nguyên trạng, nó sẽ báo con số gần hoàn hảo mà **không
chứng minh được gì** về suy luận đồ thị — một dòng `if parse(timex_raw) != time_start` đã làm
được điều đó.

## 4. Ba cách sửa

| Cách | Làm gì | Buộc phương pháp phải |
|---|---|---|
| **A. Giấu `timex_raw`** | bỏ cột khỏi input lúc đánh giá | suy luận **giữa các event** trong cùng document — event này mâu thuẫn với đồ thị thời gian của event khác không |
| B. Viết lại cả `timex_raw` | cho `timex_raw` khớp ngày giả như `text_span` | tương tự A, nhưng dữ liệu tự nhiên hơn |
| C. Giữ nguyên, báo baseline | dùng 89,69% làm cận dưới, chỉ tính phần vượt | không đổi dữ liệu, nhưng khoảng trống để chứng minh rất hẹp |

Cách A là phép thử đúng cho TempEKG: ORDERING_CONFLICT có `pair_id` nối hai event — nếu
giấu `timex_raw`, chỉ có đồ thị quan hệ thời gian giữa các event mới phát hiện được thứ tự bị
đảo. Đó chính là thứ Bài 2 được xây để làm.

---

## 5. Rò rỉ còn nhiều hơn `timex_raw` — tổng cộng ít nhất 12 đường

| Rò rỉ | GT | conflict |
|---|---|---|
| **dòng gốc vẫn còn** — mỗi conflict là bản sao của một event thật | — | 511/511 trỏ tới dòng GT cùng `event_id` |
| `refined`, `refine_strategy`, `similarity_score`, `conflict_note` | 0/2191 | **511/511** |
| `judge_reason`, `judge_confidence` | 0/2191 | 477/511 |
| `paraphrased` | 0/2191 | 430/511 |
| `pair_id` | 0/2191 | 161/511 |
| `lexical_score` | toàn 0,0 | 477/511 khác 0 |
| `timex_raw` | — | giữ ngày thật |

**Nguy hiểm nhất là dòng trùng lặp:** conflict được **thêm vào** như bản sao của event thật,
nên 476 `event_id` xuất hiện hai lần. Chỉ cần đếm là biết event nào bị đụng tới.

## 6. Benchmark trung thực — cách dựng

- Mỗi event xuất hiện **một lần**: nếu có bản conflict thì nó **thay thế** dòng GT
- Chỉ giữ 7 cột: `doc_id`, `cluster_id`, `event_type`, `entities`, `time_start`, `text_span`,
  `timex_type`. Bỏ `timex_raw`, `source_event_id` và mọi cột pipeline
- `is_conflict` chỉ dùng để chấm điểm

`cluster_id` nối được **100%** (2.702/2.702) sang event node trong đồ thị TempEKG, nên có
thể kiểm tra `time_start` của từng event với đồ thị quan hệ thời gian.

## 7. Kết quả trên benchmark trung thực

### Bốn detector, không cái nào đọc cột đã bỏ

| Detector | Cơ chế |
|---|---|
| surface | `time_start` có dạng `YYYY-01-01` (dấu hiệu bị làm thô) |
| doc-outlier | năm của `time_start` lệch khỏi năm trung vị của document |
| graph | `time_start` mâu thuẫn với cạnh `A BEFORE B` trong đồ thị TempEKG — gắn cờ **cả hai** đầu |
| **blame** | như graph, nhưng quy trách nhiệm cho **một** đầu (đầu có nhiều mâu thuẫn hơn) |

`gold` = dùng cạnh gold của MAVEN; `pred` = dùng cạnh do classifier 257 luật dự đoán.

### Mức 20% — 2.191 event, 476 conflict

| Detector | P | R | F1 | ANCHOR | ORDERING | GRANULARITY | IMPLICIT |
|---|---|---|---|---|---|---|---|
| surface | **98,39%** | 12,82% | 22,68% | 0/160 | 1/156 | 60/111 | 0/49 |
| doc-outlier | 35,66% | 20,38% | 25,94% | 29/160 | 45/156 | 19/111 | 4/49 |
| graph-gold | 42,36% | 48,32% | 45,14% | 72/160 | 96/156 | 50/111 | 12/49 |
| graph-pred | 41,09% | 48,95% | 44,68% | 74/160 | 96/156 | 52/111 | 11/49 |
| blame-gold | 73,51% | 28,57% | 41,15% | 56/160 | 52/156 | 27/111 | 1/49 |
| blame-pred | 73,96% | 29,83% | 42,51% | 55/160 | 54/156 | 32/111 | 1/49 |
| **surface + blame-pred** | **78,66%** | 39,50% | **52,59%** | 55/160 | 54/156 | 78/111 | 1/49 |

### Theo mức nhiễu — cấu hình tốt nhất `surface + blame-pred`

| Mức | conflict | P | R | F1 |
|---|---|---|---|---|
| 5% | 104 | 52,44% | 41,35% | 46,24% |
| 10% | 211 | 70,83% | 40,28% | 51,36% |
| 15% | 343 | 73,63% | 39,07% | 51,05% |
| 20% | 476 | 78,66% | 39,50% | 52,59% |

## 8. Bốn phát hiện

**1. Benchmark trung thực khó hơn nhiều.** F1 tốt nhất **52,59%**, so với **89,69%** của
baseline tầm thường trên bản rò rỉ. Khoảng 37 điểm là do rò rỉ, không phải do phương pháp.

**2. Cạnh dự đoán tốt ngang cạnh gold.** `graph-pred` 44,68% vs `graph-gold` 45,14%;
`blame-pred` 42,51% vs `blame-gold` 41,15%. Đồ thị do classifier TempEKG dựng đủ tốt để kiểm
toán mốc thời gian — vì detector chỉ dùng cạnh BEFORE, và precision BEFORE của classifier là
93,42%.

**3. Quy trách nhiệm một đầu gần như nhân đôi precision.** `graph` gắn cờ cả hai đầu của cạnh
bị vi phạm nên precision bị chặn quanh 50%. `blame` đưa precision từ **41%** lên **74%**, đổi
lại recall giảm từ 49% xuống 30%.

**4. Mỗi detector mạnh ở một loại khác nhau.**

| Loại | Detector bắt tốt nhất | recall |
|---|---|---|
| ORDERING_CONFLICT | graph | **96/156 = 61,5%** — thứ tự bị đảo vi phạm trực tiếp cạnh BEFORE |
| GRANULARITY_CONFLICT | surface | 60/111 = 54,1% |
| ANCHOR_CONFLICT | graph | 74/160 = 46,3% |
| IMPLICIT_ORDERING | — | tối đa 12/49 = 24,5% |

ORDERING là nơi suy luận đồ thị phát huy rõ nhất — đúng loại conflict mà Bài 2 được thiết kế
để bắt.

## 9. Giới hạn

1. **`graph-gold` dùng cạnh gold của MAVEN làm tham chiếu tin cậy.** Đây là hướng kiểm toán
   ngược với Bài 2 gốc (Bài 2 kiểm cạnh quan hệ; ở đây kiểm mốc thời gian dựa trên cạnh). Bản
   `pred` không có giả định này và cho kết quả gần như bằng.
2. **IMPLICIT_ORDERING gần như không bắt được** (1–12/49). Loại này chỉ đổi từ nối trong văn
   bản, cần hiểu ngôn ngữ.
3. **Recall trần ~40%.** Event không có cạnh BEFORE nào với event khác, hoặc không có
   `time_start`, thì không kiểm được bằng đồ thị.

Tái tạo: `python experiments/benchmark_honest.py`

## 10. Mở rộng detector: mọi quan hệ Allen (#2) và từ nối (#3)

Detector ở mục 7 chỉ dùng cạnh BEFORE. Hai mở rộng, vẫn không đọc cột nào đã bỏ:

| # | Cơ chế |
|---|---|
| **#2** | ràng buộc **điểm bắt đầu** cho mọi quan hệ: `A BEFORE/CONTAINS/OVERLAP B` ⇒ `start(A) ≤ start(B)`; `A SIMULTANEOUS/BEGINS-ON B` ⇒ `start(A) = start(B)`. Vi phạm được quy trách nhiệm cho một đầu như `blame` |
| **#3** | văn bản event chứa `after/afterwards/following/later`, trong khi đồ thị nối nó với một event **cùng câu** bằng SIMULTANEOUS/CONTAINS/OVERLAP — câu và đồ thị bất đồng |

### Ràng buộc có đúng trên dữ liệu sạch không

Tỷ lệ báo động giả trên cặp **cả hai event đều là ground truth**, mức 20%:

| Quan hệ | cạnh gold | cạnh dự đoán |
|---|---|---|
| BEFORE | 1,9% (1.953 cặp) | 1,7% (1.961) |
| CONTAINS | 5,1% (273) | 6,1% (293) |
| SIMULTANEOUS | 0,0% (46) | 8,3% (36) |
| OVERLAP | 0,0% (19) | 0,0% (3) |

Ràng buộc đúng với gold ở mức 95–100%. SIMULTANEOUS dự đoán kém hơn (8,3%) vì precision của
classifier cho nhãn này chỉ 16%.

### Kết quả theo mức nhiễu (F1)

| Mức | surface + BEFORE (cũ) | **surface + ALL (#2)** | surface + ALL + từ nối (#2 #3) |
|---|---|---|---|
| 5% | 46,24% | **50,98%** | 45,57% |
| 10% | 51,36% | **53,41%** | 52,20% |
| 15% | 51,05% | **53,99%** | 53,74% |
| 20% | 52,59% | 55,54% | **56,45%** |

Mức 20% chi tiết:

| Detector | P | R | F1 | ANCHOR | ORDERING | GRANULARITY | IMPLICIT |
|---|---|---|---|---|---|---|---|
| blame BEFORE, dự đoán | 73,96% | 29,83% | 42,51% | 55/160 | 54/156 | 32/111 | 1/49 |
| blame ALL, dự đoán (#2) | 72,17% | 34,87% | 47,03% | 69/160 | 57/156 | 38/111 | 2/49 |
| blame ALL, gold (#2) | 73,13% | 34,87% | 47,23% | 70/160 | 58/156 | 36/111 | 2/49 |
| `after` trần | 29,10% | 19,75% | 23,53% | 21/160 | 32/156 | 11/111 | 30/49 |
| `after` + đồ thị (#3) | 46,34% | 3,99% | 7,35% | 3/160 | 5/156 | 1/111 | 10/49 |
| surface + BEFORE (cũ) | 78,66% | 39,50% | 52,59% | 55/160 | 54/156 | 78/111 | 1/49 |
| **surface + ALL (#2)** | 76,19% | 43,70% | **55,54%** | 69/160 | 57/156 | 80/111 | 2/49 |
| surface + ALL + #3 | 71,99% | 46,43% | **56,45%** | 70/160 | 59/156 | 81/111 | 11/49 |

**#2 thắng ở mọi mức nhiễu** (+2,0 đến +4,7 điểm F1), chủ yếu nhờ bắt thêm ANCHOR_CONFLICT
(55 → 69 ở mức 20%): dịch mốc thường vi phạm CONTAINS/SIMULTANEOUS chứ không chỉ BEFORE.
Cạnh dự đoán vẫn ngang cạnh gold (47,03% vs 47,23%).

**#3 không ổn định.** Nó là detector duy nhất bắt được IMPLICIT_ORDERING (10/49 với đồ thị,
30/49 trần), nhưng precision thấp nên chỉ giúp ở mức 20% (+0,91) và **làm hại** ở 5% (−5,41).
Không dùng làm cấu hình chính.

### Rò rỉ thứ 13 — text_span gần trùng

Kiểm tra thêm: conflict IMPLICIT/ORDERING sinh bằng cách sửa câu gốc, nên có thể còn một dòng
anh em cùng câu với `text_span` gần trùng. Detector `0,85 < ratio < 1` với một dòng cùng câu:
bắt 183/476, báo động giả 303 → **P 37,7%, R 38,4%**. Rò rỉ yếu, không dùng làm detector, nhưng
nên ghi nhận khi phát hành benchmark.

Tái tạo: `python experiments/benchmark_honest2.py`
