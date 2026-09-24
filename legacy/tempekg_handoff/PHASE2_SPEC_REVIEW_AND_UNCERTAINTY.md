# Phase-2 spec review + graded temporal uncertainty
### Soi §3 của FINAL_PLAN, và thiết kế tầng uncertainty (exact day / nearly / quite near / quite far)
_29 Aug 2026 · mọi số đo bằng `probe_uncertainty.py` trên MAVEN-Arg train+valid + MAVEN-ERE train+valid_

---

## 0. Tóm tắt 4 phát hiện

| # | Phát hiện | Hệ quả |
|---|---|---|
| 1 | **§3.3 có bug gây false-positive hàng loạt.** 28.0 % (150,951/539,072) cặp BEFORE có **cả hai event treo vào cùng một TIMEX** | Phải sửa cách bound anchor day-precision, nếu không STP báo UNSAT sai trên diện rộng |
| 2 | **G2 gate đo được: 1,792 signature** sống sót ở support ≥10 **document** (plan chỉ *ước lượng* 600–1,200; gate fail dưới 400) | Gate qua với biên 4.5×, biết được **ngày 1** thay vì ngày 8 |
| 3 | **Granularity CONFLICT base rate = 12.8 %** (1,351/10,541 event multi-anchor giải được) | Plan không biết bucket này có "700 hay 7" event — câu trả lời là ~1,351 |
| 4 | **Anchor-vs-BEFORE contradictions = 1,269** (0.79 % của 161,362 cặp có anchor) — **gấp 17× so với ~72** | Gold **không** nhất quán với chính TIMEX của nó. Đây là target population thật cho detection arm |

Phát hiện #4 là quan trọng nhất: vấn đề cốt tử của plan ("chỉ có 72 conflict tồn tại") **là artefact của việc chỉ đóng BEFORE**. Khi đóng network kèm anchor bounds, số conflict tăng 17×.

---

## 1. Soi §3 — cái gì đúng, cái gì phải sửa

### 1.1 §3.2 Interval representation — **giữ nguyên, đúng**

Quadruple 4 endpoint `⟨[b_lo,b_hi],[f_lo,f_hi]⟩` trên day chronon là đúng: nó bao trùm cả 3 population (TIGHT 44.9 % / LOOSE 27.2 % / NONE 27.9 %) không cần special-case, và degrade về `(start,finish)` của PaTeCon chỉ bằng đổi tên.

Nhận định sắc nhất của spec, và nó **đúng**:

> "Granularity is stored separately and is never recoverable from the interval. Nếu normalise `'1815'` thành `[1815-01-01, 1815-12-31]` rồi không giữ gì khác, granularity conflict trở thành interval containment thông thường và conflict type thứ hai **biến mất**."

Đây chính là lý do `precision_set` phải là một cột riêng. Không thương lượng.

### 1.2 §3.3 STP compilation — **có bug, phải sửa trước khi code**

Spec ghi:

```
BEFORE(i,j)          : f_i − b_j ≤ (0,−1)     -- strict at ε, ZERO days
ANCHOR CONTAINS(t,e) : b_e ≥ lo ; f_e ≤ hi
```

Với anchor day-precision, `lo = hi = D`, nên `b_e ≥ D` và `f_e ≤ D` ⇒ `b_e = f_e = D`: event **sụp thành một điểm**. Nếu hai event `i, j` cùng treo vào TIMEX day-precision đó và có `BEFORE(i,j)`, thì STP đòi `f_i < b_j` ⇒ `D < D` ⇒ **UNSAT**. Đây là false positive hệ thống, không phải hiếm.

**Đo được population rủi ro:**

```
event-event BEFORE pairs                     : 539,072
...cả hai event treo vào CÙNG một TIMEX      : 150,951  (28.0 %)
```

**Cách sửa (1 dòng khái niệm, ~5 dòng code).** Anchor day-precision phải bound vào **ε-extent của ngày đó**, không phải vào một điểm:

```
ANCHOR CONTAINS(t,e), t day-precision D:
    b_e ≥ (D, 0)
    f_e ≤ (D, K)        với K = 2^20 − 1, tức "cuối ngày D"
```

Nghĩa là event chiếm *một phần* của ngày D, không phải toàn bộ điểm D. Khi đó `BEFORE(i,j)` trong cùng một ngày vẫn SAT (`f_i = (D,k₁) < b_j = (D,k₂)` với `k₁ < k₂`). Đúng ngữ nghĩa: MAVEN-ERE annotate BEFORE trong cùng một ngày là hoàn toàn bình thường.

Ghi chú: spec đã dùng packed `int64 = d·2²¹ + k`, nên hạ tầng có sẵn — chỉ là chỗ **áp** ε bị sai. Spec áp ε cho BEFORE nhưng không áp cho anchor.

### 1.3 §3.6 Support arithmetic — dùng số sai của mình, nhưng kết luận **tốt hơn**

Spec viết: *"274,525 → 139,093 (50.7 %) → ~111K in MINE → 2,688 signatures → mean ≈41 pairs/signature → expect 600–1,200 signatures survive ≥10-document support."*

Cả chuỗi này xây trên số đếm trùng của mình (xem ERRATA trong FINAL_PLAN.md). Nhưng thay vì sửa ước lượng, **mình đo thẳng**:

```
(T1,r1,T2,r2) signatures với >=  5 documents : 4,576
(T1,r1,T2,r2) signatures với >= 10 documents : 1,792   <-- G2 gate
(T1,r1,T2,r2) signatures với >= 20 documents :   643
(tham chiếu) >= 10 PAIRS                     : 2,730
```

**1,792 so với gate 400 ⇒ biên 4.5×.** G2 không phải rủi ro. Và con số này tính được ngày 1, nên **chuyển G2 từ gate thành fact** — giải phóng buffer mà plan dành cho nó.

### 1.4 §3.4 `multi_day_flag` — bỏ danh sách curated

Spec dùng "a curated durative set (`Military_operation`, `Hostile_encounter`, `Process_start`, `Besieging`, …)". Đó là free parameter, reviewer sẽ hỏi chọn thế nào. Thay bằng đo: **phân bố empirical của anchor span theo event type** trên MINE split. Type nào có median span > ngưỡng thì durative. Cùng một dòng code, không có tham số tay, và bản thân bảng đó là một số liệu đáng báo cáo.

### 1.5 Normaliser — xác nhận ước lượng ~1 tuần

Normaliser deterministic (regex + reference-time propagation, ~80 dòng) đạt:

```
TIMEX resolved: 14,059 / 20,827 = 67.5 %
```

So với ước lượng 62.1 % chỉ-regex của mình — refprop thêm ~5.4 điểm. Với gazetteer tên chiến tranh (~50 entry) và refprop tốt hơn, mốc 85–90 % là thực tế. Xác nhận: **critical path ~1 tuần, không phải 3.**

---

## 2. Hai phát hiện mới, đủ để đổi framing

### 2.1 Granularity CONFLICT có target thật: 12.8 %

```
multi-anchor events, tất cả anchor giải được : 10,541
intersection RỖNG (CONFLICT)                 :  1,351  (12.8 %)
intersection khác rỗng (REFINEMENT/COMPAT)   :  9,190  (87.2 %)
```

Plan viết *"CONFLICT sẽ bị dominate bởi ba population artefact"* và *"claim đúng dù bucket có 700 event hay 7"*. Giờ có số: **~1,351 với normaliser thô**. Đủ để arm này có bảng thật, và đúng như plan yêu cầu, **100 % set này phải adjudicate tay** vào {genuine, normalisation error, coreference error, durative artefact}.

### 2.2 Anchor-vs-BEFORE: gold không nhất quán với TIMEX của chính nó

```
BEFORE pairs có cả hai event được anchor : 161,362
anchors PHỦ ĐỊNH edge BEFORE             :   1,269  (0.79 %)
```

Điều kiện phủ định: `hi_j < lo_i` — anchor buộc `j` kết thúc hoàn toàn trước khi `i` bắt đầu, ngược với `BEFORE(i,j)`.

**So sánh: ~72 contradiction từ closure chỉ-BEFORE. Ở đây 1,269 — gấp 17×.**

Đây chính là Backup Claim 1 của plan, được xác nhận bằng số: *"kết quả 0 BEFORE cycles đã công bố là BEFORE-only; chưa ai đóng network với 66,418 anchor bounds"*. Mình vừa đóng một phần và tìm thấy 1,269.

**Ý nghĩa với luận điểm cũ của mình.** Mình từng nói với bạn "gold sạch, chỉ ~72 conflict, nên detection không có target". Câu đó **đúng nhưng hẹp**: nó đúng cho consistency *thuần quan hệ*. Khi đưa anchor vào, target lớn hơn 17 lần. Detection arm sống lại — nhưng ở dạng *anchor-vs-relation*, không phải *relation-vs-relation*.

Cảnh báo cần thiết: 1,269 này **chưa được adjudicate**. Một phần là lỗi normaliser của mình (refprop chọn sai năm), một phần là coreference cluster bị merge quá rộng. Tỉ lệ genuine là câu hỏi thực nghiệm — nhưng nó **là một câu hỏi có bảng trả lời**, khác hẳn với 72.

---

## 3. Tầng uncertainty — thiết kế

Yêu cầu của bạn ("exact day, nearly, interval, quite near, quite far") thực chất **gộp hai trục khác nhau**. Tách ra là bước quan trọng nhất, vì hai trục có nguồn gốc, độ tin cậy và giá trị novelty khác nhau.

### 3.1 Trục A — LOCALISATION (epistemic: biết event xảy ra khi nào *chính xác đến đâu*)

Suy ra **tất định** từ độ rộng interval. Không có tham số tự do.

| `loc_class` | Điều kiện (ngày) | Nguồn |
|---|---|---|
| `EXACT_DAY` | `b_lo=b_hi`, `f_lo=f_hi`, span ≤ 1 | anchor day-precision |
| `NEAR_DAY` | `width(b) ≤ 7` | tuần, "the next day" đã giải |
| `WITHIN_MONTH` | `≤ 31` | anchor month-precision |
| `WITHIN_YEAR` | `≤ 366` | anchor year-precision (29.9 % TIMEX) |
| `WITHIN_DECADE` | `≤ 3,653` | decade, year-range |
| `COARSE` | `> 3,653` | century, named period |
| `UNKNOWN` | sentinel | 27.9 % event không anchor |

Đây là "exact day / nearly / interval" của bạn, đã hình thức hoá. Nó **đã gần có** trong plan dưới dạng `precision`; chỉ cần thêm `loc_width_b`, `loc_width_f`, `loc_class` như cột dẫn xuất.

### 3.2 Trục B — PROXIMITY (relational: hai event cách nhau bao xa, và *có hợp lý không*)

Đây là "quite near / quite far", và đây là **chỗ có novelty**. Suy ra từ **gap interval sau STP closure**, rồi bin theo **quantile empirical điều kiện trên cặp event type**.

Quantile đo được trên toàn corpus:

```
BEFORE pairs có gap tính được: 160,093
q10=-365  q25=-364  q50=0  q75=25  q90=1,827  q99=27,760  max=458,015 ngày
gap > 1 năm : 27,110 (16.9 %)
gap > 10 năm: 10,813 ( 6.8 %)
gap > 50 năm:  2,387 ( 1.5 %)
```

`max = 458,015 ngày = 1,254 năm` giữa hai event trong **một** bài Wikipedia, có chung participant, có edge BEFORE.

| `gap_class` | Điều kiện |
|---|---|
| `SIMULTANEOUS_ISH` | gap interval chứa 0, `|gap|` nhỏ |
| `QUITE_NEAR` | trong `[q10, q50)` của cặp type |
| `TYPICAL` | `[q10, q90]` |
| `QUITE_FAR` | `(q90, q99]` |
| `IMPLAUSIBLE` | `> q99` của cặp type |
| `UNCONSTRAINED` | `gap_hi − gap_lo` quá rộng để phân loại |

**1,146 cặp type có ≥30 quan sát** — đủ để estimate quantile theo từng cặp. Ví dụ các cặp có đuôi rộng nhất:

```
Hostile_encounter -> Removing         n= 38  median=    0  q90= 40,909 ngày (112 năm)
Besieging -> Conquering               n= 46  median= -185  q90= 38,718
Change_of_leadership -> Destroying    n= 43  median=  641  q90= 32,507
Killing -> Catastrophe                n= 36  median=    0  q90= 25,204
```

### 3.3 Conflict type thứ ba: MAGNITUDE CONFLICT

Đây là thứ trục B mở ra, và **crisp Allen algebra về mặt cấu trúc không thể biểu diễn được**:

> Một `Killing` xảy ra 1,254 năm sau `Attack` lên cùng một Victim là **Allen-consistent** — nên §3.3 không thấy nó — nhưng rõ ràng sai.

`MAGNITUDE CONFLICT` = gap interval sau STP closure nằm ngoài khoảng hợp lý mined theo cặp type. Nó **trực giao** với logical consistency, nên nó là một population target *khác*, không chồng lấn với 72 hay 1,269.

Điểm framing quan trọng: **PaTeCon đã có sẵn machinery này** — `validSpanBelow` / `validSpanAbove` / `relationsSpanBelow` / `relationsSpanAbove` tồn tại trong `Interval_Relations.py`. Nên đây là **mở rộng của paper gốc**, không phải rời khỏi nó. Nhưng PaTeCon chỉ dùng span *một fact*; đây là gap *có điều kiện trên cặp type* — mới.

### 3.4 Trả lời trực diện lý do plan CẮT fuzzy

Plan cắt "fuzzy / vague interval algebras" với hai lý do, và **cả hai đều được giải quyết** bởi thiết kế trên:

| Phản đối của plan | Trả lời |
|---|---|
| *"No supervision exists for membership functions"* | Supervision **là corpus**. Bin lấy từ quantile empirical, không phải membership function đặt tay. 1,146 cặp type có ≥30 quan sát. |
| *"Fuzziness destroys the crisp emptiness test that makes granularity decidable"* | **Kiến trúc hai tầng.** Tầng 1 = crisp SAT/UNSAT (complete, O(n³), *không đổi một dòng*). Tầng 2 = graded score, chỉ chạy trên instance đã SAT. Không có tương tác. |

**Quy tắc đặt tên, quan trọng cho review:** đừng gọi là "fuzzy". Gọi là **type-conditioned empirical quantile binning**. Reviewer thấy "fuzzy" sẽ đòi biện minh membership function; thấy "empirical quantile conditioned on type pair" sẽ hỏi sample size — mà bạn có.

### 3.5 Schema thêm vào (nhỏ — quan trọng vì còn 44 ngày)

```sql
-- thêm cột vào events (Trục A) — dẫn xuất, không phải dữ liệu mới
ALTER events ADD loc_class VARCHAR;      -- EXACT_DAY|NEAR_DAY|WITHIN_MONTH|...|UNKNOWN
ALTER events ADD loc_width_b BIGINT;     -- b_hi - b_lo
ALTER events ADD loc_width_f BIGINT;     -- f_hi - f_lo
-- precision_set đã có trong plan; giữ nguyên

-- prior theo cặp type, mine CHỈ trên MINE split, freeze + hash như constraint
gap_prior(event_type_1, role_1, event_type_2, role_2, rel,
          n_obs, n_docs, q10, q25, q50, q75, q90, q99, max_obs)

-- verdict theo cặp, CHỈ cho cặp đã pass Tầng 1
pair_proximity(doc_id, ev_i, ev_j, rel,
               gap_lo, gap_hi,           -- từ STP closure
               loc_class_i, loc_class_j, -- eligibility (xem 3.6)
               gap_class,                -- SIMULTANEOUS_ISH|QUITE_NEAR|TYPICAL|QUITE_FAR|IMPLAUSIBLE|UNCONSTRAINED
               type_pair, n_obs,
               q90_ref, q99_ref,         -- lưu lại để verdict audit được
               implaus_score)            -- log(gap_lo / q99) khi gap_lo > q99
```

Lưu `q90_ref`/`q99_ref` **vào từng dòng verdict**: không có nó thì verdict không tái lập được khi prior đổi.

### 3.6 Ba nguyên tắc kỷ luật, bỏ là mất bài

1. **`UNCONSTRAINED` là hạng nhất và phải báo cáo tỉ lệ.** Với ~55 % event không có tight anchor, gap interval là vô hạn. Đây chính là `unknown` của PaTeCon áp cho magnitude. Che nó đi là gian lận.

2. **Bảng eligibility `loc_class × loc_class` là một kết quả.** Chỉ cặp mà **cả hai** event localise đủ tốt mới phân loại proximity được. Dấu hiệu trong dữ liệu: `q10 = −365`, `q25 = −364` — âm *do cấu trúc*, vì anchor year-precision làm "minimum gap" âm. Nên phải chặn theo `loc_class`, và bảng đó nói lên **bao nhiêu phần của một event graph grounded-từ-text đủ điều kiện để nói chuyện magnitude** — chưa ai báo cáo con số này.

3. **`gap_prior` mine trên MINE, freeze, hash, trước khi có error nào.** Giống hệt constraint set. Nếu mine prior trên cả corpus rồi detect outlier trên cùng corpus đó → circular, đúng cái bệnh mà §5 vừa chữa.

### 3.7 Novelty — đánh giá thật

**Có prior work liền kề, phải cite và định vị.** Temporal commonsense đã học "duration/frequency điển hình của event": MC-TACO (Zhou et al. EMNLP 2019), TRACIE, "Temporal Common Sense Acquisition". Nên **"event type có duration điển hình" KHÔNG mới**.

Cái mới là tổ hợp: **gap prior có điều kiện trên *cặp* (type, role) dùng làm conflict detector trên event KG, với kiến trúc hai tầng bảo toàn decidability.** Đó là claim phải viết, và phải viết kèm đoạn định vị so với temporal commonsense — nếu không reviewer sẽ tự tìm ra và coi là thiếu sót.

**Rủi ro phải nói trước:** các cặp type đuôi rộng ở §3.2 gần như chắc chắn bị dominate bởi **lỗi coreference** (cluster gộp hai event khác nhau) và **lỗi normaliser**, không phải lỗi annotation. Điều đó không giết arm này — nhưng nó buộc **100 % set IMPLAUSIBLE phải adjudicate tay** vào cùng 4 nhãn như granularity. Nếu tỉ lệ genuine thấp, kết quả trở thành *"magnitude outlier là detector tốt cho lỗi coreference"* — vẫn là một finding, chỉ khác cái bạn nhắm.

---

## 4. Khuyến nghị thứ tự làm (Phase 2, 44 ngày còn lại)

| Ưu tiên | Việc | Ngày | Lý do |
|---|---|---|---|
| **P0** | Sửa ε-bound cho anchor day-precision (§1.2) | 0.5 | Không sửa thì 150,951 cặp UNSAT sai |
| **P0** | Normaliser: regex + refprop + gazetteer, có validation set blind 150 surface | 6 | Critical path, đã xác nhận 67.5 % → 85–90 % |
| **P0** | Quadruple + `precision_set` + STP + Floyd-Warshall | 4 | Xương sống, giữ nguyên như §3.2/§3.3 |
| **P1** | **Full-STP closure kèm anchor bounds** → báo cáo lại 1,269 | 1 | Phát hiện #4; đây là detection target thật |
| **P1** | `loc_class` + `loc_width_*` (Trục A) | 0.5 | Dẫn xuất, gần như miễn phí |
| **P1** | Granularity 4-verdict + adjudicate 100 % của ~1,351 | 3 + annot | Đã có số, arm này chạy được |
| **P2** | `gap_prior` trên MINE + `pair_proximity` + bảng eligibility (Trục B) | 3 | Novelty mới, nhưng sau khi P0/P1 xanh |
| **P2** | Adjudicate set IMPLAUSIBLE | annot | Bắt buộc nếu muốn claim magnitude |
| **CẮT** | Fuzzy membership function, Allen fuzzy algebra, periodic sets | — | Plan cắt đúng; §3.4 giữ được lợi ích mà không trả giá |

Bảng eligibility và `UNCONSTRAINED` rate nên tính **ngay sau P1**, vì nếu tỉ lệ eligible quá thấp thì Trục B không đủ dữ liệu và nên bỏ sớm chứ đừng bỏ ngày 35.

---

## 5. Script

| Script | Làm gì |
|---|---|
| `probe_uncertainty.py` | Sinh mọi số trong doc này: normaliser, E1 G2 gate, E2 same-TIMEX, E3a granularity, E3b anchor-vs-BEFORE, E3c gap distribution |
| `recount_pairs.py` | Sửa lỗi đếm trùng shared-participant pairs |
| `recount_signatures.py` | Đếm lại signature power cho đúng |
| `verify_plan_numbers.py` | Kiểm hai mẫu số trong abstract đề xuất |
