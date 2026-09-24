# Định nghĩa cho MAVEN Constraint Mining

> Tài liệu quyết định, kết thúc giai đoạn định nghĩa.
> Mọi con số trong tài liệu này đều kèm nguồn: `file:line`, lệnh đã chạy, hoặc mục trong paper.
> Những gì chưa đo được đánh dấu **MỞ** một cách rõ ràng — không suy đoán.
>
> Phạm vi đo mặc định: **MAVEN-ERE train = 2.913 documents, 792.445 temporal relations** (toàn bộ file,
> không phải mẫu). Khi dùng split hoặc mẫu khác, con số đó ghi rõ tại chỗ.

---

## 0. Tóm tắt quyết định

| item_id | Quyết định (một dòng) | Trạng thái | Bằng chứng |
|---|---|---|---|
| **A1** | TIMEX là node hạng nhất, **OPAQUE** (không parse ra lịch); key bắt buộc là `(doc_id, node_id)` | **CHỐT** | Bỏ TIMEX mất 308.901/792.445 = 38,98% quan hệ; 456 TIMEX id trùng qua tối đa 35 doc |
| **A2** | Motif khớp ở mức **CLUSTER**, không phải mention | **CHỐT** | Bắt buộc: mọi endpoint quan hệ đều là cluster id; mention id không bao giờ xuất hiện |
| **A3** | **KHÔNG merge** entity cùng surface string; giữ `entity_id` thô | **CHỐT** | Merge được +0,45 điểm phần trăm, đổi lại ≥15,38% merge sai chứng minh được |
| **A4** | Candidate = **mọi cặp node trong document**, không cửa sổ câu; cặp không nhãn = UNKNOWN | **CHỐT** | 1.994.647 cặp (không phải 100 triệu); mật độ chú thích phẳng theo khoảng cách câu |
| **A4b** | Key cặp phải là **ordered canonical** `(u,v), u<v` kèm orientation, không phải unordered | **CHỐT** | `L({u,v})` như đề xuất không well-defined: cùng input cho hai output |
| **B1** | **ENDS-ON = {b, m}**, không phải `{m}`, không phải `{f,fi,e}` | **CHỐT** (sửa) | Cả hai đều 21/21 sound, nhưng `{m}` sinh 42 bad triple / 3 doc, `{b,m}` sinh 0 |
| **B1b** | **OVERLAP = {o}**, không phải `{o,oi}` | **CHỐT** (sửa) | `{o}` → 21/21 sound; `{o,oi}` → 19/21, phá vỡ đúng hai luật OVERLAP của chính paper |
| **B2** | Chỉ mirror **SIMULTANEOUS** và **BEGINS-ON**; dedupe 100 BEGINS-ON lưu hai chiều | **CHỐT** | 0/5.821 SIMULTANEOUS và 0/6.376 OVERLAP có chiều ngược; BEGINS-ON 100/453 |
| **B3** | Sàn xung đột logic trong gold = **0**, không phải 7 | **CHỐT** (sửa) | 7 "mâu thuẫn" biến mất hoàn toàn dưới ENDS-ON={b,m} |
| **B4** | Giữ trivalent pos/neg/unknown và drop-unknown, **nhưng confidence thoái hoá** | **CHỐT** | neg = 0 ⇒ mọi confidence = 1,0; phải xếp hạng bằng lift/binomial |
| **B5** | Vắng nhãn = UNKNOWN; chỉ transitive forcing mới được gọi là "thiếu sót" | **CHỐT** | 681/689 residual trên valid là ABSENT; 8 cái còn lại mang SIMULTANEOUS hợp lệ |
| **C1** | Lattice 3 trục độc lập (không phải chuỗi); giữ L1, L3, L4; **bỏ L4s** | **CHỐT** | L1 4.251 pattern @sup≥25 phủ 75,7%; L4s chỉ 231, 0 thành viên family |
| **C1b** | **L2 không bị loại** — nó đóng góp 67/1.456 thành viên family | **CHỐT** (sửa) | C1 nói "DROP L2" nhưng C5 dùng 67 thành viên L2 và C2 xếp L2 ưu tiên cao nhất |
| **C1c** | **L4 = `(t1,t2,sdist_abs)`** (3-tuple); torder tách thành trục refinement riêng | **CHỐT** | Holdout: tái lập 82,00% vs 85,00%, z=1,181 **p=0,2374 không ý nghĩa**; 3-tuple cho 378 vs 340 constraint tái lập, phủ 8.427 vs 6.735 instance valid |
| **C2** | **BỎ refinement khỏi thiết kế.** Đã chạy đủ trên full train; đóng góp riêng +0,071 pp | **CHỐT (âm tính)** | 81,7% child có allowed-set **rộng hơn** cha (matched 4,03→5,92); sàn falsifiability n=189 |
| **C3** | Chấm điểm bằng **per-relation enrichment + binomial + BH-FDR + lift≥2**, không dùng raw confidence | **CHỐT** | raw conf≥0,90 cho 3.366 pattern, **0** cái non-BEFORE; Wilson cũng không cứu được |
| **C4** | Pattern ánh xạ tới **tập cho phép** (Wilson-UB), không phải một quan hệ | **CHỐT** | 38,84% pattern L1 cần ≥2 quan hệ để phủ 95% khối lượng; L3 là 82,6% |
| **C5** | Family giữ nguyên định nghĩa, nhưng **khung DỰ ĐOÁN bị RÚT LẠI**: không luật giải đa khớp nào thắng hằng số | **CHỐT (âm tính)** | Trên tập khớp n=70.697: const-BEFORE 67,85%, const-CONTAINS 28,38%, SPEC 28,24% — SPEC **thua** (net −93, McNemar b=1.004 c=1.097); trần ORACLE 30,19% |
| **D1** | Causal/subevent chỉ là **bộ lọc yếu**, tuyệt đối không phải bằng chứng độc lập | **CHỐT** | Paper Sec 2.3: causal chỉ chú thích trên cặp đã có nhãn BEFORE/OVERLAP |
| **D1b** | TIMEX normalization là kênh **ít tương quan nhất**, không phải "độc lập hoàn toàn" | **CHỐT** (sửa) | Annotator cũng đọc chuỗi TIMEX khi xếp timeline (Sec 2.2) |
| **D2** | Dùng **Allen 13×13 đầy đủ + PC-2 tới fixpoint**, bảng sinh bằng brute force | **CHỐT** | Bảng 21 luật của paper không đủ và không biểu diễn được trạng thái phân ly |
| **D3** | Thứ tự ưu tiên P1..P6 đúng; gold không bao giờ thắng | **CHỐT** | Nếu gold thắng thì detector trả về tập rỗng theo định nghĩa |
| **D3b** | Bảng hai pha 11 row + 4 row escalation; **row 1 gate bằng unsat core**, không bằng `H2=EMPTY` | **CHỐT** | Chạy đủ 2.913 doc trong 89 s; một cung inject làm rỗng **99,9%** ô của document, nên row-1-như-đặc-tả cho 383.930 cờ; gate bằng core còn ~667 |
| **D3c** | **Row 4, E1, E4 chết theo cấu trúc** — không phải thiếu dữ liệu | **CHỐT** | Row 4: `M ⊆ MAP(G)` theo khởi tạo, 0/129.452 ô kích hoạt; E4 test `base=REVIEW-LOW` mà pha 1 không bao giờ phát ra giá trị đó |
| **E1** | Mine 5-fold trên **train+valid pooled**, chia theo document; test.jsonl vô dụng | **CHỐT** | test không có key `events` và 0 quan hệ; 7.755 candidate out-of-fold |
| **E2** | N=150, **hai judge**, blinded, Cohen's kappa, pilot gate κ≥0,40 | **CHỐT** | MAVEN-ERE chỉ đạt κ=67,8% với annotator được huấn luyện |
| **E3** | Precision@k + Wilson CI; **recall không đo được**; baseline B3 là phép so quyết định | **CHỐT** | Không có gold error set; toàn bộ candidate ⊂ tập non-BEFORE (100%) |
| **E4** | Elicit nhãn của judge **trước**, suy ra outcome bằng script; bắt buộc có decoy | **CHỐT** | s = BEFORE cho 1.464/1.464 candidate ⇒ judge đoán theo prior sẽ luôn "xác nhận" |
| **E5** | Nêu circularity thẳng thắn; track miễn nhiễm là **rỗng thật** | **CHỐT** | 0 mâu thuẫn cứng sau khi sửa B1; 681/689 residual là UNKNOWN có tài liệu |
| **E5b** | **ĐÃ GỠ CHẶN bằng tiêm tổng hợp.** Câu hỏi đổi từ "gold có lỗi không" (cấu trúc: không) sang "detector thu hồi được bao nhiêu lỗi đã tiêm" | **CHỐT** | Gold vẫn 0 mâu thuẫn cứng; nhưng recall nay **đo được** trên ground truth tiêm, kèm trần phát hiện phải báo cùng |
| **C3R** | Hàm chấm điểm cho DETECTION **khác hẳn C3**: `FORBIDS(p,r) ⟺ WilsonUB(k_r,n_p) < τ`. Không enrichment, không BH, không lift | **CHỐT** | C3 kiểm **đuôi dưới**, detection cần **đuôi trên**; τ=0,05 cho FP valid 0,673%, recall 38,80% (uniform) / 16,96% (gold-marginal) |
| **C3Rb** | **BEFORE không thể bị cấm** ở mọi level — thuộc tính cấu trúc, phải ghi vào paper | **CHỐT** | 0/8.156 pattern có WilsonUB(BEFORE) < τ; min WilsonUB(BEFORE) = **0,446**; recall trên nhãn tiêm BEFORE đúng **0,000%** |
| **INJ** | **Tiêm tổng hợp là giao thức đánh giá chính.** Chi tiết ở `INJECTION_SPEC.md` | **CHỐT** | Mô hình hỏng phải là **gold-marginal**, không uniform: uniform làm baseline tầm thường `Brare` thắng giả (F1 0,557 vs family 0,378), gold-marginal lật ngược (0,006 vs **0,245**) |

**Tổng: 33 CHỐT · 0 CẦN ĐO THÊM · 0 BỊ CHẶN.**

> **Bổ sung 2026-09-20 tối — xem mục 11.** Các định nghĩa trên vẫn đúng, nhưng có thêm 8 kết
> quả đo và **ba chỗ phải sửa**: (a) C5 — subsumption phá tín hiệu, abstraction thì giữ;
> (b) xếp hạng phải dùng **Wilson LB**, không dùng lift (2,9× khác biệt); (c) artifact thứ tư
> — mất chữ ký view cho precision giả 70,52%. (26 mục cũ + 4 mục mới sinh ra từ vòng đo này: D3c, C3R,
C3Rb, INJ; ba mục còn lại là C1c/C2/C5 chuyển trạng thái, D3b chuyển trạng thái, E5b gỡ chặn.)

> Vòng đo này đóng toàn bộ 5 mục CẦN ĐO THÊM và gỡ chặn E5b. Bốn trong số đó chốt ở **kết quả âm tính**
> (C2 bỏ refinement; C5 rút lại khung dự đoán; D3c bốn row chết theo cấu trúc; C3Rb BEFORE bất khả cấm).
> Kết quả âm tính vẫn là kết quả đã chốt: chúng loại bỏ công việc cài đặt, và ba trong bốn cái là **phát
> biểu cấu trúc chứng minh được**, không phải quan sát may rủi.

---

## 1. Sự thật nền đã kiểm chứng

### 1.1. PaTeCon (code)

| Sự thật | Trích dẫn |
|---|---|
| `add_eVertex` trả về vertex **đang tồn tại** khi key trùng — id trùng lặp sẽ âm thầm hợp nhất node | `Graph_Structure.py:86-95`; `:263` gọi trên id trần |
| Literal nhận key đếm tăng dần `'L'+LiteralNum`, nên literal **không bao giờ join** | `Graph_Structure.py:277-278, 293-294`; `Constraint_Mining.py:154` bỏ qua literal |
| Unknown bị loại **bằng cách bỏ sót** ở nhánh `elif`, không có bộ đếm `unk` nào | `Constraint_Mining.py:218-224` |
| Confidence là tỉ số trần `pos/(pos+neg)`, không smoothing, không Wilson, không prior | `Constraint_Mining.py:230-233`; grep `wilson\|laplace\|smooth\|bonferroni\|fdr\|binom` → rỗng |
| Ngưỡng mặc định: support=100, candidate=0.5, confidence=0.9 | `Constraint_Mining.py:1826-1835` |
| Hằng số pruning **đóng băng lúc import** từ giá trị mặc định; dòng tính lại bị comment | `Constraint_Mining.py:17-19` vs `:1851-1853` |
| Dòng bị comment dùng hệ số **5**, dòng sống dùng **10** — bỏ comment sẽ **đổi ngữ nghĩa**, không phải sửa lỗi | `:19` `10*support_threshold` vs `:1853` `# ... 5 * support_threshold` (tự đọc, đã xác nhận) |
| Ngưỡng CLI **không lan** sang refinement: nó chạy ở support=100 bất kể `--support` | `Refinement_Mining.py:7-10`, không nơi nào ghi đè |
| Refinement: trigger dải `[0.5, 0.9)`, top-K = 10/5/3, **một pass, không đệ quy** | `Refinement_Mining.py:1065-1070`, `:12-14`, `:148` |
| Cha bị "thay thế" chỉ do **trùng bộ lọc**, không có liên kết parent/child nào được ghi | `Constraint_Mining.py:1801-1823` (cùng cắt ≥0.9 cho cả hai file) |
| `transitive_closure` tồn tại nhưng **call site bị comment** — PaTeCon xuất xưởng không tính closure | `Constraint_Mining.py:1509-1534`, call site `:1779` |
| Vòng lặp fixpoint đó có bug: `Old_...=transitive_closure_set` là **alias**, nên `len(x)==len(x)` luôn đúng và vòng lặp thoát sau đúng một pass | `Constraint_Mining.py:1519-1527` |
| SP3/SP4 chỉ phát ra **một** predicate qua chuỗi if/elif ưu tiên cố định | `Constraint_Mining.py:699-719`, `:1124-1147` |
| Detection tách refined/unrefined bằng **test substring thô** `c.__contains__("class")` | `Conflict_Detection.py:952-956` |
| MutualExclusion **không so sánh thời gian bao giờ**; nó chiếm 715/747 = 95,7% conflict trên WD50K | `Conflict_Detection.py:57-133`, append tại `:126` không có `if` bảo vệ |
| `FuzzyTime` căn phải YYYYMMDD; heuristic `if Day==1` hạ độ chính xác | `Interval_Relations.py:13`, `:17-23` |
| Đánh giá **chỉ có recall**, không precision, không F1 | `evaluate.py:790-791` |

### 1.2. PaTeCon (paper, AAAI-23)

| Sự thật | Mục |
|---|---|
| Paper định nghĩa **hai** structural pattern (a) và (b), không phải bốn | Figure 3, Table 6 |
| Chấm chất lượng constraint 3 mức C/M/W, 3 annotator, **không báo cáo kappa** | Evaluation Metrics and Setting |
| Pattern (b) trên WD27M: 41% C / 38% M / 21% W | Table 6 |
| Tham số: θ_freq=100, θ_c1=0.5, θ_c2=0.9 | Environments and Parameters |

### 1.3. MAVEN-ERE

| Sự thật | Nguồn |
|---|---|
| Nhãn **không** được chú thích theo cặp; annotator sắp xếp các điểm đầu/cuối trên một timeline và quan hệ được **suy ra tự động** | Sec 2.2, `ere.txt:311-319` |
| Cặp không nhãn = **sub-timeline, UNKNOWN có tài liệu**, không phải annotator quên | Sec 2.2, `ere.txt:325-329` |
| Không giới hạn phạm vi theo câu liền kề | Sec 2.2, `ere.txt:330-334` |
| "Ngoại trừ SIMULTANEOUS và BEGINS-ON, các loại quan hệ là **một chiều**, tức head phải bắt đầu trước tail" | Sec 2.2, `ere.txt:291-295` — **câu định nghĩa duy nhất trong paper** |
| Table 11 có **đúng 21** luật transitivity temporal (tôi đã đọc verbatim `ere.txt:1208-1229`) | Appendix B |
| Causal chỉ chú thích trên cặp **đã có nhãn** BEFORE/OVERLAP | Sec 2.3, `ere.txt:404-407` |
| Subevent chỉ chú thích trên cặp **đã có nhãn** CONTAINS | Sec 2.4, `ere.txt:456-458` |
| Causal và subevent chú thích **cùng một stage** ⇒ lỗi của chúng tương quan với nhau | `ere.txt:423-425` |
| Temporal relation: **1 annotator + 1 expert reviser**, κ Cohen = 67,8% (TIMEX được 3 annotator, κ Fleiss 78,4%) | Sec 2.2 |
| Table 12: **25.843** là số TIMEX, **15.841** là số subevent | Appendix |
| Chỉ 0,85% lỗi model là "Transitivity Fixable"; paper gọi đó là **tỉ lệ nhỏ** | Table 10, `ere.txt:756-767` |
| Limitations **không nêu** tỉ lệ lỗi nào | Limitations |

**Số liệu đo trên train (2.913 doc):**

| Đại lượng | Giá trị |
|---|---|
| Tổng quan hệ temporal | 792.445 |
| BEFORE / CONTAINS / OVERLAP / SIMULTANEOUS / BEGINS-ON / ENDS-ON | 683.581 / 95.933 / 6.376 / 5.821 / 453 / 281 |
| Theo loại endpoint: EE / TE / ET / TT | 483.544 / 160.008 / 102.388 / 46.505 |
| Mất nếu bỏ TIMEX | 308.901 = **38,98%** |
| Event cluster / mention | 67.984 / 73.939 (96,36% singleton) |
| TIMEX record / bare id phân biệt / id trùng qua doc | 16.688 / 15.879 / **456** (tối đa 35 doc) |
| TIMEX node tham gia ≥1 quan hệ (key `(doc,id)`) | **15.423/16.688 = 92,42%** |
| EVENT node tham gia ≥1 quan hệ | 55.039/67.984 = 80,96% |
| Cặp EE có nhãn / khả dĩ | 483.504 / 1.072.158 = 45,10% |
| Cặp ordered mang >1 nhãn | **0** |
| Self-loop | **0** |
| Cặp lưu hai chiều | 100, **toàn bộ** BEGINS-ON↔BEGINS-ON |
| Event type phân biệt trong ERE | **168** |
| test.jsonl | 857 doc, **không có key `events`**, 0 quan hệ |

### 1.4. MAVEN-Arg

| Sự thật | Nguồn |
|---|---|
| Không có TIMEX, không có time role — đây là **quyết định thiết kế được nêu rõ** | Sec 2 nguyên tắc (3): "Temporal and causal relations ... describe When and Why" |
| Entity coreference **chỉ trong document**; entity object chỉ có `{id, type, mention}`, không link KB | Sec 2.2 + đo trực tiếp 55.421 entity |
| 143 role name bề mặt (paper nói 612 = số slot theo từng event type) | Đo trên train+valid+test |
| Argument value có **đúng hai hình dạng**, không bao giờ trộn: `{entity_id}` 76.882 (40,36%) hoặc `{content, offset}` 113.597 (59,64%) | Đo toàn bộ Arg train |
| Offset là **ký tự** trong một chuỗi `document` phẳng — khác hệ toạ độ với ERE (token trong câu) | Đo trực tiếp |
| Event type phân biệt trong Arg | **162** |
| ENTITY_ id **duy nhất toàn cục**: 68.348 record, 0 va chạm qua doc | Đo trên train+valid |
| Cặp EE có nhãn khớp được cả hai đầu với Arg | 432.027 (51.517 bị loại vì thiếu endpoint) |
| Trong số đó chia sẻ ≥1 entity / ≥2 entity | 87.001 = **20,14%** / 17.733 = 4,10% |

---

## 2. Những điều tưởng đúng mà sai

Phần này tồn tại để bạn **không xây trên tiền đề sai**. Mỗi mục: điều đã tin → sự thật → bằng chứng.

### 2.1. Ba sai lầm quan trọng nhất

**(1) ENDS-ON = `{m}` (meets). SAI. Đúng là `{b, m}`.**

Cụm B và D đều kết luận ENDS-ON nghĩa là "meets" và coi đó là phát hiện lớn nhất của mình.
Lập luận soundness của họ đúng về mặt loại bỏ `{f,fi,e}`, nhưng **không phân biệt được** `{m}` với `{b,m}` —
chính B cũng thừa nhận trong ngoặc rồi im lặng bỏ `{b,m}` đi.

Tôi đã chạy lại cả hai tiêu chí trên toàn bộ dữ liệu:

| ENDS-ON | OVERLAP | Sound / 21 luật | Bad ordered triple (train đầy đủ) | Document không thoả |
|---|---|---|---|---|
| `{m}` | `{o}` | **21/21** | **42** | **3** |
| `{b,m}` | `{o}` | **21/21** | **0** | **0** |
| `{b}` | `{o}` | 21/21 | — | — |
| `{f,fi,e}` | `{o}` | 18/21 | 812 | 95 |
| `{m}` | `{o,oi}` | 19/21 | 42 | 3 |
| `{b,m}` | `{o,oi}` | 19/21 | 0 | 0 |

Soundness không chọn được giữa `{b}`, `{m}`, `{b,m}`. Dữ liệu thì chọn được: `{m}` để lại 42 tam giác
không thoả, `{b,m}` để lại 0. Tôi cũng chạy path consistency đầy đủ trên ba document nghi vấn:

```
EO={m},OV={o}    -> cb776b54 INCONSISTENT, 6b13e7ec INCONSISTENT, 2950b444 INCONSISTENT
EO={b,m},OV={o}  -> cb776b54 CONSISTENT,   6b13e7ec CONSISTENT,   2950b444 CONSISTENT
```

Cả 7 "mâu thuẫn cứng" mà cụm B được khen là phát hiện ra đều có **cùng một hình dạng**:
`BEFORE(a,b) + BEFORE(b,c) + ENDS-ON(a,c)`. Chuỗi BEFORE ép một khoảng trống chặt, còn `{m}`
đòi tiếp giáp chính xác. Chúng là **hiện vật của lựa chọn ánh xạ**, không phải lỗi chú thích.

> **Hệ quả nghiêm trọng:** nếu bạn giữ `{m}`, paper sẽ công bố 7 "lỗi chú thích logic" mà bạn tự tạo ra —
> đúng thứ mà chính phần risk của cụm D gọi là "kết cục tệ nhất có thể của dự án".

Đọc bằng tiếng Việt thường: "Chiến tranh Barbary **kết thúc vào** đầu thế kỷ 19" đặt điểm cuối của
cuộc chiến **bên trong** biểu thức thời gian đó — không phải tiếp giáp. `{b,m}` cho phép điều này; `{m}` thì không.

**(2) OVERLAP = `{o,oi}`. SAI. Đúng là `{o}`.**

Cụm D chỉ thị "B1 **phải** đặt OVERLAP={o,oi}" với ba lý do, cả ba đều sai:

| Lý do đưa ra | Sự thật |
|---|---|
| "Cần `{o,oi}` để luật SIMULTANEOUS+OVERLAP=OVERLAP hoạt động" | Rỗng nghĩa. `comp({e},{o}) = {o} ⊆ {o}` — luật này đúng dưới **cả hai**. SIMULTANEOUS là `{e}`, hợp thành với `{e}` là phép đồng nhất. |
| "OVERLAP+BEFORE=BEFORE không hợp lệ trong interval algebra" | Chỉ không hợp lệ **dưới chính lựa chọn `{o,oi}` của họ**. `comp({o},{b,m}) = {b} ⊆ {b,m}` — hợp lệ hoàn toàn. Đây là lập luận vòng tròn. |
| "Phù hợp với câu một-chiều của paper hiểu theo thứ tự START" | Ngược hoàn toàn. OVERLAP **không** nằm trong danh sách ngoại lệ, nên paper khẳng định head.start < tail.start. Quan hệ Allen `oi` nghĩa là head bắt đầu **sau** — nó là phần tử duy nhất của `{o,oi}` vi phạm đúng câu được viện dẫn. |

Đo bằng chính tiêu chí mà cụm D dùng để chốt ENDS-ON: `{o}` cho **21/21** luật sound; `{o,oi}` cho **19/21**,
phá vỡ đúng `BEFORE+OVERLAP=BEFORE` và `OVERLAP+BEFORE=BEFORE`.

**(3) "Sàn xung đột logic là 7" (cụm B, sau phản biện) hoặc "là 0" (cụm B, ban đầu). Đúng là 0 — nhưng vì lý do khác.**

Cụm B ban đầu nói 0; lens data tìm ra 7 và gọi đó là fatal. Cả hai đều đúng một nửa:

- 7 tam giác **có thật** dưới ENDS-ON=`{m}` (tôi đo lại: 7 instance, 3 document — không phải 1 document như báo cáo nền nói).
- Nhưng chúng **biến mất hoàn toàn** dưới ENDS-ON=`{b,m}`, vốn là ánh xạ được dữ liệu ủng hộ.
- Test pairwise của cụm B bỏ sót chúng vì BEFORE và ENDS-ON **tương thích** ở mức cặp; mâu thuẫn chỉ hiện ở mức 3 biến.

Kết luận đúng: **sàn là 0, và phải dùng path consistency 3 biến chứ không phải bảng tương thích pairwise
để chứng minh điều đó.** Bảng pairwise về mặt nguyên tắc không thể thấy lớp mâu thuẫn này.

### 2.2. Các đính chính khác (theo cụm)

| Điều đã tin | Sự thật | Bằng chứng |
|---|---|---|
| "~15.841 TIMEX" | 15.841 là số **subevent**; TIMEX là 25.843 (toàn dataset), 16.688 (train) | Table 12, đọc verbatim |
| TIMEX participation 92,86% (mẫu số 15.879 bare id) | **92,42%** (15.423/16.688) dùng chính key `(doc,id)` mà A1 bắt buộc | Tôi đo lại; 15.879 là bare id, mâu thuẫn với chính A1 |
| 348.164 cặp event nối qua TIMEX hub, "0,72×" | **574.503** tổng, trong đó **124.990** chưa có nhãn trực tiếp = **0,259×** | Tôi đo lại toàn train; 348.164 không khớp đại lượng nào |
| TIMEX id trùng là "hash collision" | Id **suy từ nội dung**: cả 456 id trùng đều cùng surface string và cùng type. Key `(doc,id)` vẫn bắt buộc, nhưng vì lý do khác (TIMEX opaque ⇒ nghĩa của node là tập quan hệ cục bộ) | 456/456 cùng string, 456/456 cùng type |
| Groundability TIMEX = 52,80% | Không tái lập được: ba cài đặt độc lập cho 53,26% / 53,81% / 55,20%. Ghi là **~53–55%** | Grammar chưa công bố regex |
| Event type = 162 giá trị | **168 trong ERE**, 162 trong Arg, và **4.602/64.335 = 7,15% event lệch type** giữa hai bộ | Tôi đo trực tiếp; `Hostile_encounter`→`Military_operation` 1.963 lần |
| "0 non-BEFORE pattern sống sót ở **mọi** level" | 0 ở L1/L1s/L2/L4, nhưng L3 cho **2** (sup≥10) và **1** (sup≥25) | Chính `c_lattice.py` in ra; và một trong số đó là ví dụ mà C3 tự trích dẫn ở chỗ khác |
| CAUSE weak rule có 4 vi phạm | **3**. Cái thứ 4 là reverse-OVERLAP, không vi phạm luật đã viết | Tôi chạy đúng luật hình thức của họ |
| L2 "không sống sót, DROP khỏi lattice" | L2 đóng góp **67/1.456** thành viên family và được C2 xếp **ưu tiên cao nhất** khi giải đa khớp | Mâu thuẫn nội bộ C1 ↔ C5 ↔ C2 |
| Residual transitivity là "lỗi chú thích tiềm năng" | Trên valid, **681/689 residual là ABSENT** (UNKNOWN có tài liệu). 8 cái còn lại mang SIMULTANEOUS, **đúng về ngữ nghĩa** | Tôi phân loại toàn bộ 21 luật |
| "364 residual OVERLAP+BEFORE trên valid (EVENT-EVENT)" | 364 là số **all-node**; EVENT-EVENT chỉ **175** | Header bảng nói EE, thân bảng là all-node |
| "Model prediction có mâu thuẫn dồi dào" (pivot của B3) | Paper báo **0,85%** và gọi đó là "tỉ lệ nhỏ", dùng nó làm bằng chứng model **đã học được** transitivity | Table 10, `ere.txt:765-767` |
| Bảng incompatibility "chỉ có ô tương thích vì cho phép interval suy biến" | Ngược lại. Bảng được sinh với `range(a+1, N)` — **loại bỏ** interval suy biến. Cho phép suy biến sẽ **phá huỷ** 28/72 ô | `b_resid.py:23` |
| PaTeCon: bỏ comment dòng 1851-1853 để "sửa bug" | Dòng bị comment dùng hệ số **5**, dòng sống dùng **10**. Bỏ comment **đổi ngữ nghĩa** chứ không khôi phục | Tôi tự đọc file |
| Tie-break "most specific wins" là bắt buộc và tốt nhất | Chỉ **24,9%** instance đa khớp có bất đồng thật. Và majority vote đo được **28,12%** so với 26,26% của luật đề xuất | Đo trên cùng family 1.456 — **hai con số này đã bị mục 2.3 thay thế**, xem dưới |
| "26,26% vs base 9,12% = lift 2,88×" | So sai mẫu số. Trên chính 70.911 instance được khớp, predictor hằng "luôn CONTAINS" đạt **28,35%** — **thắng** phương pháp | Phân bố nhãn trên tập khớp: 67,86% BEFORE, 28,35% CONTAINS |

> **Hai dòng trên đúng về HƯỚNG nhưng con số đã lỗi thời** — chúng tính với vị từ `share` sai (role-pair thay
> vì entity-id). Bộ số hiện hành, đo lại với định nghĩa đã đóng băng: tập khớp **70.697**, phân bố
> **67,85% BEFORE / 28,38% CONTAINS**, SPEC **28,24%**, majority vote **28,24%**, trần ORACLE **30,19%**, và
> tỉ lệ đa khớp **bất đồng** đúng phải đếm theo `(key, relation)` = **59,00%**, không phải 24,9%. Xem mục
> 2.3 và C5. Kết luận không đổi và còn mạnh hơn: **SPEC thua** hằng-CONTAINS.
| Cụm B: "reconstruction duy nhất làm 21 luật sound" | Không duy nhất. Ít nhất 23 ánh xạ khác cũng 21/21, kể cả ánh xạ **rỗng** (thoả mãn rỗng nghĩa). Soundness đơn điệu giảm theo kích thước tập, nên **không bao giờ** định danh được | Tôi xác nhận: CONTAINS={di} cũng 21/21; ENDS-ON=∅ cũng 21/21 |

### 2.3. Đính chính từ vòng đo đóng (C1c, C2, C5, D3b, C3R, INJ)

Mỗi dòng dưới đây là một con số **đã bị verifier lật đổ bằng script chạy được**. Theo luật phân xử: verifier
có script thắng; không lấy trung bình, không nước đôi.

| Điều đã tin (vòng trước) | Sự thật đã đo lại | Bằng chứng |
|---|---|---|
| C1c: "giữ torder trong key L4" | **Ngược.** Ưu thế 4-tuple là 85,00% vs 82,00%, **z=1,181 p=0,2374 — không có ý nghĩa**. 3-tuple cho **378 vs 340** constraint tái lập | Holdout valid 710 doc chưa từng mine; tách theo torder làm **107/512** thành viên biến mất |
| C1c: 3-tuple phủ "9.887 vs 7.498 instance valid (+31,86%)" | **Đếm trùng.** Đó là tổng theo *member* `(key,relation)`, 20 và 15 key mang hai relation. Đúng theo **key phân biệt**: **8.427 vs 6.735** (+1.692 = **+25,12%**) | Hai lens độc lập cùng ra 8.427/6.735 |
| C1c: "signed sdist + torder ≡ abs sdist + torder, nên không gian thiết kế chỉ có 2 ứng viên" | Chỉ đúng khi delta ≠ 0. Ở **39.839** cặp cùng câu (9,22%) torder là **người mang thông tin duy nhất** (FWD 30.317 / BWD 9.522). `L4_signed` một mình chỉ 84.290 distinct vs 87.610 | Chênh 3.320 key chính là thông tin thứ tự cùng câu |
| C1c: chi2 gộp torder = 1.825,8 | **1.826,8** với chi2 2×2 không hiệu chỉnh. Nếu muốn dùng số điểm thì phải nói rõ biến thể | 10/10 tỉ lệ phần trăm tái lập đúng; chỉ thống kê chi2 lệch |
| C2: "mean \|allowed\| cha 5,801 → con 5,915" | **Hai tập chỉ mục khác nhau.** 5,801 là trung bình trên **toàn bộ 4.251** cha; 5,915 chỉ trên 284 con được nhận. Cặp khớp đúng là **4,03 → 5,92** (Δ = +1,89) | Trung bình hiệu = hiệu trung bình; 5,915−5,801=0,114 < 0,817 mà 81,7% con lớn hơn hẳn ⇒ bất khả về tổ hợp |
| C2: sàn falsifiability "n < 190" | **n = 189.** Dạng đóng `z²/(n+z²) < τ` cho `n > z²(1/τ−1) = 188,24` | WilsonUB(0,188)=0,020025 ≥ τ; WilsonUB(0,189)=0,019921 < τ |
| C2: "child bắt được 1 lỗi tiêm mà L1 bỏ sót" | **0.** Bắt được **không cái nào**, mất 75 (2%) / 170 (5%) | Chạy lại cùng seed 7, cùng mô hình hỏng |
| C2: "hạ sàn nhiễu 8,01% → 0,17%, giảm **47×**" | **Sai mẫu số.** 8,01% là nhiễu / **toàn bộ 4.251 cha**, không liên quan tới quyết định. Đại lượng đúng là FDP = nhiễu / **số thật sự bắn**: 22,62% → 4,21% = **5,4×** | Chọn đúng theo FDP là `k≥10 ∧ lift≥3` (FDP 8,11%, giữ 306 firing thật) chứ không phải `k≥25 ∧ lift≥3` (giữ 164) |
| C2: "most-specific-wins là nguồn gây hại chính" | **Không — luật hợp thành sai mới là nguồn.** Cha và con đều là ràng buộc hợp lệ trên cùng một cặp, nên phép hợp thành đúng là **giao**, không phải ghi đè. Dưới giao, refinement không mất gì | Ghi đè TP=1.091; giao TP=1.164 > L1 đơn độc 1.163 |
| C5: `args(ev) = {(role, entity_id)}` dùng cho vị từ share | **SAI — share tính trên ENTITY ID.** Chỉ định nghĩa entity-id mới tái lập bảng C1 đã công bố (L1s 636, L2 98) | Role-pair cho L1s 406 / L2 57; entity-id cho **636 / 98**. Tôi chạy lại độc lập: L1 4.251, L1s 636, L2 98, L3 538 |
| C5: "SPEC thắng const-CONTAINS +0,26 điểm, p=1,5e-07" | **Ngược dấu sau khi sửa share.** SPEC 28,24% **thua** const-CONTAINS 28,38% (net **−93**, McNemar b=1.004 c=1.097) | Tôi chạy lại toàn bộ với share entity-id: `FINAL_c5.py` |
| C5: "0 instance BEFORE hay CONTAINS vi phạm" | Tự mâu thuẫn. Nếu 1 pattern cấm CONTAINS thì các instance CONTAINS dưới nó **vi phạm theo định nghĩa**. Đúng: **189** in-sample / **237** LOO, trong đó **3 CONTAINS** | Pattern L1 `(Coming_to_be, Catastrophe)` n=501 k=3, WilsonUB=0,01746 < τ=0,02 |
| C5: đa khớp sau dedupe "35,50%" | Đó là dedupe theo **key**, gộp cả hai phát biểu bất đồng về cùng key — tức xoá đúng phần bằng chứng cạnh tranh mà luật giải đa khớp tồn tại để phân xử. Theo `(key, relation)`: **59,00%** | Tôi đo lại: cell 61,93% → (key,rel) 59,00% → key 51,96% |
| C5: "L2 có 67/70 thành viên là bản sao" | **64/67** — đúng bằng con số DEFINITIONS.md đã ghi. Vòng trước không "củng cố" phát hiện cũ, nó làm nhiễu bằng vị từ share sai | Tôi xác nhận trực tiếp: 67 thành viên L2, 64 trùng `(key,relation)` với L1/L1s |
| D3b: "một cung inject làm rỗng 67,5% ô" | **99,9%** (p50 527 ô). 67,5% là hiện vật của tối ưu hoá "bỏ qua cung còn FULL": kiểm chứng chỉ chạy trên 13 quan hệ **cơ sở**, bỏ sót mask **rỗng**, mà `comp(FULL, ∅) = ∅` chứ không phải FULL | Row-1-như-đặc-tả cho **383.930** cờ (không phải 260.012); precision 0,052% |
| D3b: "tiêm REVERSE chỉ phát hiện 95%, 5% là điểm mù của injector" | **100%, và là định lý.** Thêm BEFORE(j,i) lên BEFORE(i,j) làm `{b} ∩ {bi} = ∅` **ngay lúc ingest**, không cần chu trình | 200/200 ô rỗng trước khi PC chạy, 4 seed độc lập. 94% của RELABEL thì đúng |
| D3b: "lõi trung bình 3,21 cung, không bao giờ 1" | Lõi nhỏ nhất là **2**, và phổ biến: 15/40 lõi đúng bằng 2. Sàn 3 là hệ quả của cùng lỗi lan truyền ∅ ở trên | Lõi 2 cung `{fwd, rev}` đã mâu thuẫn, không cần cung thứ ba |
| D3b: OK-DERIVED "7.580" | **Đếm đôi.** UNLAB và PIN đều đối xứng, nên mọi ô OK-DERIVED có ô gương cũng OK-DERIVED (100% phủ gương). Số **fact phân biệt** là **3.790** | 2.340/2.340 ô trên 400 doc có gương cũng bật |
| INJ: "trượt timeline viết lại 27,3 nhãn, PC phát hiện 0/80 ⇒ chế độ lỗi thật không phát hiện được" | **Thí nghiệm không có control và không phân biệt được.** Nó đọc lại **mọi** nhãn từ toạ độ nhiễu, nên output là read-off của một timeline hiện thực được ⇒ nhất quán **theo cấu trúc**. Control: PC trên bản dựng **chưa trượt** cũng 0/80 | Bản dựng phá huỷ 1.718/1.718 nhãn non-BEFORE **trước** khi trượt. Trượt **cục bộ** (chỉ đọc lại cung kề event bị dời) cho **32,5–43,8%** qua 5 seed |
| INJ: "trần phát hiện 26,1% ± 2,1" | Đó là **recall đạt được** của một extractor dưới cap MAXE=400, không phải trần. Trần theo nguyên tắc, tính từ khả phát hiện từng toán tử × trọng số đã khai báo, là **60,9%** | delete 0% × trọng số 0,15 là **quy ước**, không phải đo; trần đổi 22%↔30% chỉ do trọng số delete |
| INJ: toán tử `cycle` "100% phát hiện được ở mức pairwise" | Định nghĩa tuần hoàn. Graph BEFORE của MAVEN **đóng bắc cầu**, nên hễ có đường a→…→b thì cạnh trực tiếp (a,b) **cũng có**; `cycle` vì thế luôn va vào nhãn sẵn có trên đúng cặp đó | 400/400 trial: (a,b) đã có nhãn trực tiếp, ở mọi độ dài đường 1/2/3; 279.124/279.124 đường 2-hop có cạnh trực tiếp |
| INJ/C5: family so với baseline được mine trên corpus **sạch** | Rò rỉ. `inj_strat2.py` / `inj_c5.py` mine ở dòng 52–53 từ `docs` sạch rồi mới làm hỏng fold held-out. Mine trên corpus **đã hỏng** hạ lift 1,36× → **1,22×** | Đúng luật do chính báo cáo đặt ra ("MINE ON THE CORRUPTED CORPUS") mà code không tuân |
| C3R: FP sạch dưới LODO "400 instance (0,0926%)" | **491 (0,1137%).** Không biến thể LODO nào cho 400; riêng L1 đã là 483 > 400, mà thêm level chỉ có thể tăng | LODO tạo **185 phát biểu chỉ tồn tại khi hold-out**, bắn 296 lần — đúng cơ chế làm LODO > in-sample |
| C3R: "family thắng B3 dứt khoát" | So ở **recall khác nhau** (0,358 vs 0,980) nên vô nghĩa. Ở cùng ngân sách FP, B3 thắng; family **không bao giờ** với tới recall của B3 (bão hoà 0,734) | Nhưng xem dòng dưới — kết luận cuối vẫn nghiêng về family, vì lý do khác |
| C3R: `Brare` (cấm {BEGINS-ON, ENDS-ON}) "thống trị family" | **Chỉ dưới mô hình hỏng uniform.** Uniform: Brare F1=0,557 > family 0,378. **Gold-marginal**: Brare **sụp còn 0,006**, family **0,245** — thắng B3 (0,152) gấp 1,6× và Brare gấp 39× | Tôi chạy lại độc lập: `FINAL_c3r.py`. Ưu thế của Brare là hiện vật của injector lấy mẫu quá nhiều quan hệ hiếm |

**Bài học chung của vòng này — một mô hình hỏng sai làm đảo kết luận.** Bốn phát hiện riêng biệt ở trên
(C3R/Brare, INJ/timeline-slip, INJ/cycle, C2/47×) đều là cùng một lỗi mặc một bộ quần áo khác: **so với sai
mẫu số, hoặc đo dưới một null/injector không hiện thực**. Đây đúng là lỗi mà mục 2.2 đã ghi một lần
("26,26% so sai mẫu số") và nó tái phát bốn lần ở tầng trên. Mọi con số recall/precision từ nay phải kèm
mô hình hỏng đã dùng và ít nhất một baseline tầm thường chạy qua **cùng** census.

---

## 3. A. Tầng dữ liệu

### A1 — Node nào vào graph?

**Quyết định: TIMEX là node hạng nhất, OPAQUE. Key bắt buộc `(doc_id, node_id)`. Argument entity-valued là node; content-only là thuộc tính.**

```
V_EVENT(d) = { (d, e.id) : e ∈ d.events }
V_TIMEX(d) = { (d, t.id) : t ∈ d.TIMEX }
V_TEMPORAL(d) = V_EVENT(d) ∪ V_TIMEX(d)        ← miền mà candidate pair chạy trên đó

ENT(d) = { (d, x.entity_id) }                   ← KHÔNG phải node; chỉ là join key cho shares_k

key(n) = doc_id + '#' + node_id                 ← LUÔN LUÔN, không bao giờ id trần
value(t) = UNDEFINED                            ← không tính giá trị lịch nào
```

> **Sửa so với đề xuất:** A1 liệt kê `V_ENT` trong `V(d)` còn A4 lại loại nó khỏi candidate set. Hai phát biểu
> hình thức định nghĩa hai graph không tương thích, và 55.421 entity trở thành đỉnh cô lập. **Chốt: entity
> KHÔNG phải node temporal.** Đúng theo lập luận lượng từ của chính A3 — `entity_id` chỉ xuất hiện bên trong
> `shares_k` dưới một lượng từ đơn-document. Bỏ nhánh `ENTITY` khỏi hàm `kind()`.

**Bằng chứng:** bỏ TIMEX mất 38,98% quan hệ train (41,81% trên valid — nhất quán qua split).
TIMEX có bậc trung bình 21,30 so với 18,08 của event. 456 TIMEX id xuất hiện ở nhiều document,
tối đa 35 — nạp id trần vào `Graph_Structure.add_eVertex` sẽ âm thầm hợp nhất chúng.

**Rủi ro:** nếu bỏ qua key ghép, 456 id hợp nhất qua tối đa 35 document, bịa ra constraint xuyên document
từ hư không, và điều này **vô hình trong output** — nó sẽ trông như một phát hiện mạnh và thật.

### A2 — "Event" là gì?

**Quyết định: CLUSTER. Đây không phải lựa chọn mô hình, nó bị dữ liệu ép buộc.**

Mọi endpoint của `temporal_relations` đều mang tiền tố `EVENT_` hoặc `TIME_`; mention id là 32-hex trần và
**không bao giờ** xuất hiện làm endpoint. Không tồn tại nhãn nào ở mức mention. Một hệ thống mention-level
phải tự bịa ra phép chiếu.

Câu hỏi tổng hợp gần như vô nghĩa: 96,36% cluster là singleton, và chỉ 4,34% instance quan hệ chạm vào
cluster đa mention. Luật: `sent(ev) = min(sent_id)`, argument lấy hợp (MAVEN-Arg vốn gắn argument vào
cluster, nên hợp đã có sẵn theo format).

> **Sửa nhỏ:** `ents(ev)` định nghĩa là **tập** `entity_id` sẽ nuốt mất role. 4.163 cặp (event, entity) gắn
> cùng một entity dưới ≥2 role khác nhau, và A3 lại đề xuất nhóm theo bộ ba có role. Định nghĩa
> `args(ev) = {(role, entity_id)}` và suy `ents(ev) = π₂(args(ev))`.

> **Sửa phạm vi:** "quy tắc tổng hợp chỉ ảnh hưởng ≤4%" đúng cho **supervision có nhãn**, nhưng lựa chọn
> min/max đổi khoảng cách câu của 61.222 cặp trong **không gian candidate** = 5,7%. Ghi cả hai mẫu số.

### A3 — Định danh entity

**Quyết định: KHÔNG merge.** Cân đo rõ ràng:

| Chính sách | share≥1 | share≥2 |
|---|---|---|
| `entity_id` thô | 87.001 (20,14%) | 17.733 (4,10%) |
| + merge cùng chuỗi | 88.934 (20,59%) | 17.943 (4,15%) |
| + merge, bỏ đại từ | 88.007 (20,37%) | — |

Lợi: **+0,45 điểm phần trăm**. Hại: **282/1.833 = 15,38%** nhóm va chạm chứa entity **xung đột type** —
những merge đó sai chứng minh được. Đổi chác kém khoảng một bậc độ lớn.

Câu hỏi "in-document có đủ không" — **có**, vì lý do tinh tế: constraint khai thác được lượng hoá trên
**TYPE** (từ vựng toàn cục: 168 event type ERE, 7 entity type, 143 role), còn `entity_id` chỉ dùng để kiểm
tra hai event **trong cùng document** có chạm cùng entity không. Đó là câu hỏi nội-document, và id nội-document
trả lời hoàn hảo.

> **Sửa:** "1.730/1.833 nhóm có chuỗi non-pronoun" không tái lập được; con số đúng là **1.833** (mọi nhóm).
> Điều này **củng cố** kết luận không merge.

**Trần cứng cho cụm C:** motif chia sẻ entity không bao giờ vượt quá **20,14%** cặp có nhãn.

### A4 — Cặp nào là candidate?

**Quyết định: mọi cặp node trong document. Không cửa sổ câu. Không cổng chia sẻ entity.**

Tiền đề của câu hỏi (có thể nổ lên 100 triệu) là **sai**: train+valid cho **1.994.647** cặp all-node.

Mật độ chú thích **phẳng** theo khoảng cách câu — đây là phát hiện mạnh nhất của cụm A và cả ba lens đều
tái lập chính xác:

| Khoảng cách | 0 | 1 | 2 | 3 | 5 | ≥10 |
|---|---|---|---|---|---|---|
| Mật độ có nhãn | 61,59% | 46,68% | 44,99% | 44,18% | 43,37% | **41,92%** |

Không có điểm gãy. Từ d=1 tới d≥10 mật độ chỉ giảm 46,68% → 41,92%. Mọi cửa sổ đều là **mất mát thuần**:
`|dist|≤1` giữ 23,08%, `≤3` giữ 45,63%, `≤5` giữ 62,53%.

**Sửa bắt buộc — hàm nhãn phải là ordered canonical:**

Đề xuất định nghĩa miền là cặp **không thứ tự** `{u,v}` nhưng mọi nhánh lại phân biệt trên tra cứu
**có thứ tự** `[u,v]` vs `[v,u]`. Với bất kỳ BEFORE(a,b) nào, gán `u:=a,v:=b` cho BEFORE còn `u:=b,v:=a`
cho `inv(BEFORE)` — cùng input, hai output. Ảnh hưởng 100% của 981.373 instance. Thêm nữa, `inv()` không
bao giờ được định nghĩa và codomain của nó (AFTER, IS-CONTAINED-BY) nằm ngoài từ vựng 6 nhãn.

```
C(d) = { (u,v) : u,v ∈ V_TEMPORAL(d), u < v }          ← thứ tự từ điển cố định trên node id
L(u,v) ∈ (SIX_RELATIONS × {fwd, rev}) ∪ {UNKNOWN}

  SYMMETRIC = {SIMULTANEOUS, BEGINS-ON}                ← orientation gộp thành một giá trị
  DIRECTED  = {BEFORE, CONTAINS, OVERLAP, ENDS-ON}     ← orientation giữ nguyên
```

**Symmetrization là bắt buộc:** 0/5.821 SIMULTANEOUS và 0/6.376 OVERLAP có chiều ngược được lưu.
Một phép kiểm tra thành viên có hướng sẽ **âm thầm mất toàn bộ 12.197** sự kiện này.

> **Lưu ý:** BEGINS-ON là quan hệ **đối xứng** theo chính paper, và là quan hệ **duy nhất** được vật chất hoá
> hai chiều (100/453). Đề xuất A4 xếp nó vào nhóm **inverted** — sai, và mâu thuẫn với điều khoản
> symmetrization ngay kế bên.

**Cặp không nhãn (~50%) = UNKNOWN**, phải được **liệt kê rồi bỏ ở bước tổng hợp**, không phải vắng mặt khỏi
phép liệt kê. Nếu chúng bị coi là negative, mọi confidence sụp một nửa và toàn bộ lần chạy vô hiệu.
Đây là **ràng buộc xuyên cụm nguy hiểm nhất trong tầng A**.

---

## 4. B. Ngữ nghĩa quan hệ

### B1 — Ánh xạ nhãn MAVEN → tập Allen

> **Cập nhật 25/09/2026.**
> - Ánh xạ code thực dùng (`src/constraint_net.py`) là BEFORE {b}, CONTAINS {di}, OVERLAP {o},
>   SIMULTANEOUS {e}, BEGINS-ON {s, si, e}, ENDS-ON {b, m}. Bảng endpoint dưới đây là mô hình nới lỏng cũ.
> - Nguồn định nghĩa đã tìm thấy: README MAVEN-ERE → RED guideline. RED cho ENDS-ON = `A.end = B.start` (meets {m}).
> - Phép thử "nhân chứng khoảng hở" cho thấy dữ liệu hành xử như {m}: 5 / 315 cạnh ENDS-ON có nhân chứng, so với
>   91–98% cạnh BEFORE. {b, m} là bản nới lỏng hấp thụ 7 tam giác nhiễu trong 3 document.
> - BEGINS-ON: cách đọc {mi} của RED bị loại (1.141–3.374 tam giác mâu thuẫn); "cùng bắt đầu" đúng.
> - Chi tiết: `experiments/begins_ends/` (log `s02_mapping.log`, `s02b_bad_triangles.log`).

**Đây là artifact chịu lực của cả dự án.** Mô hình bằng **ràng buộc điểm đầu/cuối**, không phải tập Allen
như biểu diễn chính — nhưng hai cách **tương đương** trên interval không suy biến (tôi đã kiểm chứng:
mỗi nhãn sinh ra đúng tập Allen ghi bên cạnh), nên chọn endpoint chỉ vì tiện cài đặt.

**Giả định miền bắt buộc, phát biểu một lần cho toàn dự án: `x.s < x.e` (interval KHÔNG suy biến).**
Cho phép interval độ dài 0 sẽ làm 28/72 ô của bảng incompatibility sụp thành "tương thích" và bảng trở nên
gần như vô dụng.

| Nhãn MAVEN | Ràng buộc endpoint (a=head, b=tail) | Tập Allen | Đối xứng? |
|---|---|---|---|
| **BEFORE** | `a.e ≤ b.s` | `{b, m}` | Không |
| **CONTAINS** | `a.s ≤ b.s ∧ b.e ≤ a.e` | `{di, si, fi, e}` | Không (nhưng không phản đối xứng) |
| **OVERLAP** | `a.s < b.s < a.e < b.e` | `{o}` | Không |
| **SIMULTANEOUS** | `a.s = b.s ∧ a.e = b.e` | `{e}` | **Có** |
| **BEGINS-ON** | `a.s = b.s` | `{s, si, e}` | **Có** |
| **ENDS-ON** | `a.e ≤ b.s` | **`{b, m}`** | Không |

**ENDS-ON = `{b, m}`, không phải `{m}`.** Xem mục 2.1(1) cho toàn bộ bằng chứng.
**OVERLAP = `{o}`, không phải `{o,oi}`.** Xem mục 2.1(2).

Điều gì **bị loại chắc chắn**: `ENDS-ON = {f, fi, e}` (đọc trực giác "cùng kết thúc"). Nó cho 18/21 sound,
phá vỡ `BEFORE+ENDS-ON`, `ENDS-ON+CONTAINS`, `ENDS-ON+BEGINS-ON`, và 812 bad triple trên train.
Dữ liệu cũng bác: cả 23 chuỗi ENDS-ON+ENDS-ON đều giải thành BEFORE, không cái nào thành ENDS-ON —
điều bất khả nếu ENDS-ON có tính bắc cầu (đồng kết thúc thì bắc cầu).

> **Cảnh báo về phương pháp:** soundness 21/21 là bộ lọc **cần**, không phải bộ **định danh**. Nó đơn điệu giảm
> theo kích thước tập, nên ánh xạ rỗng cũng đạt 21/21. Có ít nhất 23 ánh xạ 21/21 khác. Tiêu chí phân biệt
> thật là: (i) tính cực đại, (ii) dữ liệu tam giác toàn corpus, (iii) câu một-chiều của paper.
> **Đừng viết "reconstruction duy nhất" trong paper** — reviewer sẽ bác trong một dòng.

**MỞ:** RED guidelines (O'Gorman et al. 2016) — tôi xác nhận `red.txt` chỉ nhắc begins-on/ends-on trong một
bảng IAA và **không định nghĩa chúng**. Ánh xạ này là **suy luận**, không phải trích dẫn. Đường giải quyết:
repo THU-KEG/MAVEN-ERE có thể ship annotation guidelines; hoặc email tác giả.

**MỞ:** OVERLAP `{o}` vs any-intersection. Soundness chọn `{o}` (21/21 vs 19/21) và câu một-chiều của paper
cũng chọn `{o}`. Nhưng 1.816 residual OVERLAP+BEFORE trên train chưa được đọc tay. Cần xem ~20 instance.

**Lưu ý về TIMEX:** ánh xạ này áp cho **mọi** node, gồm TIMEX. Nhưng DURATION TIMEX ("14 năm", "12 ngày")
là **độ dài**, không phải vị trí — không nên đặt toạ độ `(s,e)` trên timeline. DURATION chỉ chiếm
2.901/16.688 = 17,38% và loại được bằng một predicate trên `timex_type`.

### B2 — Lưu một lần hay hai lần?

| Quan hệ | Instance | Có chiều ngược lưu kèm | Chính sách |
|---|---|---|---|
| BEFORE | 683.581 | 0 | Giữ nguyên |
| CONTAINS | 95.933 | 0 | Giữ nguyên |
| OVERLAP | 6.376 | 0 | Giữ nguyên |
| SIMULTANEOUS | 5.821 | 0 | **Mirror khi nạp** |
| BEGINS-ON | 453 | **100 (22,08%)** | **Mirror + dedupe** |
| ENDS-ON | 281 | 0 | Giữ nguyên |

`motif_key(ta, r, tb)` = `(min(ta,tb), r, max(ta,tb))` nếu `r` đối xứng, ngược lại `(ta, r, tb)`.

> **Sửa thuật ngữ:** đừng gọi nhóm còn lại là "phản đối xứng" — CONTAINS **không** phản đối xứng
> (CONTAINS(a,b) và CONTAINS(b,a) cùng đúng thì ép ra đẳng thức, và bảng của chính B3 đánh ô đó là "ok").
> Gọi đúng tên phép toán: **MIRROR-ON-INGEST** vs **KEEP-AS-STORED**.

Bất đối xứng 25-vs-4 (Process_start BEFORE Expend_resource) là **tín hiệu thật**: 0 cặp lưu hai chiều, nên
4 instance ngược là 4 cặp event khác thật. Nhưng nó **yếu**: 25 đến từ 12 document, 4 từ 2. Dùng
**support theo document**, không theo instance.

> **Sửa đơn vị:** "4.334 motif, 1.191 significant" đếm **cặp type không thứ tự**, trong khi B2 định nghĩa
> motif là bộ ba có thứ tự. Theo chính định nghĩa của B2, con số là **8.770 / 2.382**. Thêm nữa,
> `b_signal.py:55` dùng `if ta>=tb: continue`, làm rơi toàn bộ **đường chéo** (Attack BEFORE Attack, v.v.):
> 83 motif cùng type với n≥20, phủ 16.503 instance BEFORE. Con số đã sửa là **4.439 / 1.194**.

> **Cảnh báo thống kê:** p-value hiện tại không hợp lệ cho phát biểu đang đưa ra — trial không độc lập
> (25 instance từ 12 doc, tái sử dụng head event), không hiệu chỉnh đa so sánh trên 4.334 test đồng thời
> (ở α=0,01 kỳ vọng ~43 significant dưới null thật), và H₀=0,5 không phải đại lượng quan tâm khi corpus
> là ~86–91% BEFORE. Cần: gộp về một quan sát/document, BH-FDR, và H₀ = tỉ lệ nền theo hướng.

### B3 — Bảng không tương thích pairwise

Sinh bằng brute force trên **interval không suy biến**, không viết tay.

**Cùng chiều** — hàng `r1(a,b)`, cột `r2(a,b)`; `X` = bất khả:

| | BEFORE | CONTAINS | OVERLAP | SIMUL | BEGINS-ON | ENDS-ON |
|---|---|---|---|---|---|---|
| **BEFORE** | ok | X | X | X | X | **ok** |
| **CONTAINS** | X | ok | X | ok | ok | X |
| **OVERLAP** | X | X | ok | X | X | X |
| **SIMULTANEOUS** | X | ok | X | ok | ok | X |
| **BEGINS-ON** | X | ok | X | ok | ok | X |
| **ENDS-ON** | **ok** | X | X | X | X | ok |

**Ngược chiều** — hàng `r1(a,b)`, cột `r2(b,a)`:

| | BEFORE | CONTAINS | OVERLAP | SIMUL | BEGINS-ON | ENDS-ON |
|---|---|---|---|---|---|---|
| **BEFORE** | X | X | X | X | X | X |
| **CONTAINS** | X | ok | X | ok | ok | X |
| **OVERLAP** | X | X | X | X | X | X |
| **SIMULTANEOUS** | X | ok | X | ok | ok | X |
| **BEGINS-ON** | X | ok | X | ok | ok | X |
| **ENDS-ON** | X | X | X | X | X | X |

> **Sửa chú thích:** ghi chú gốc nói "các ô tương thích chỉ tồn tại vì cho phép interval suy biến" là
> **ngược hoàn toàn**. Bảng được sinh với `range(a+1, N)` (`b_resid.py:23`), tức **loại** interval suy biến.
> Cho phép suy biến làm 28/72 ô lật sang "ok" và bảng gần như rỗng nghĩa.

**Bảng pairwise là KHÔNG ĐỦ.** Nó về nguyên tắc không thấy được mâu thuẫn 3 biến — chính xác là lớp mà
`BEFORE+BEFORE+ENDS-ON` rơi vào, vì BEFORE và ENDS-ON tương thích ở mức cặp. **Bộ phát hiện phải dùng
path consistency trên hệ ràng buộc endpoint** (D2), không phải tra bảng pairwise.

**Bỏ hẳn công thức SCC/collapse của cụm B.** Gộp CONTAINS thành "thành phần đẳng thức" là **không sound**:
CONTAINS(a,b) yếu hơn đẳng thức nghiêm ngặt, nên a thừa hưởng cạnh BEFORE của b và bịa ra chu trình không
suy ra được. Phản ví dụ cụ thể: a=(0,10), b=(2,3), c=(5,6) — CONTAINS(a,b) ∧ BEFORE(b,c) đúng, nhưng
CONTAINS(a,c) cũng đúng, nên "chu trình" a→c là giả.

**Kết quả đo, sàn xung đột:**

| Phép kiểm tra | Train | Valid |
|---|---|---|
| Cặp ordered mang >1 nhãn | 0 | 0 |
| Vi phạm cứng cùng chiều | 0 | 0 |
| Vi phạm cứng ngược chiều | 0 | 0 |
| Chu trình BEFORE độ dài 2 / 3 | 0 / 0 | 0 / 0 |
| Path consistency (ENDS-ON=`{b,m}`) | **0 document** | 0 document |
| Path consistency (ENDS-ON=`{m}`) | 3 document / 42 triple | — |

**Sàn là 0.** Nguyên nhân là **cấu trúc, không phải may mắn**: annotator không khẳng định nhãn theo cặp,
họ sắp xếp điểm đầu/cuối trên một timeline và nhãn được đọc ra cơ học. Một chú thích là **hiện thực được
theo định nghĩa**, nên nó không thể tự mâu thuẫn.

> **Cảnh báo về tính vòng tròn:** con số 0 này **không phải bằng chứng cho B1**. Ánh xạ "đồng kết thúc" bị
> B1 bác bỏ cũng cho đúng 0 vi phạm pairwise trên cùng dữ liệu. Hãy báo cáo 0 như nó vốn là:
> **hệ quả giải tích của công cụ chú thích, chứng minh được a priori từ `ere.txt:311-319`**, và là một
> phép kiểm tra tỉnh táo rằng pipeline không có bug — không phải một phát hiện thực nghiệm.

### B4 — Trivalent pos/neg/unknown

Giữ nguyên cơ chế của PaTeCon, thay cách tính verdict:

```
verdict(a, b, P):
  if labels(a,b) = ∅ ∧ labels(b,a) = ∅:               return UNKNOWN     # ~50% cặp
  if ∃h ∈ labels(a,b) : incompat_same(P, h):          return NEGATIVE
  if ∃h ∈ labels(b,a) : incompat_opp(P, h):           return NEGATIVE
  if ∃h ∈ labels(a,b) : entails(h, P):                return POSITIVE
  return UNKNOWN                                        # tương thích nhưng không kéo theo
```

`entails` tính trước bằng brute force 6×6 (bất biến với lựa chọn suy biến — tôi đã kiểm chứng):
`entails(SIMULTANEOUS, CONTAINS)=True`, `entails(CONTAINS, SIMULTANEOUS)=False`, `entails(ENDS-ON, BEFORE)=True`.

Tổng hợp **theo document** (không theo cặp), bắt chước tổng hợp theo entity của PaTeCon.
**Cần thêm guard:** yêu cầu ≥1 cặp khớp trước khi document được bỏ phiếu — "mọi cặp đều positive" là
**đúng rỗng nghĩa** cho document không có cặp nào. PaTeCon chặn điều này ở `Constraint_Mining.py:157`;
đề xuất không mang theo.

> **PHÁT HIỆN QUAN TRỌNG — confidence của PaTeCon THOÁI HOÁ trên MAVEN gold.** Vì neg = 0 (B3),
> `pos/(pos+neg)` = **đúng 1,0** cho mọi constraint có mẫu số khác 0. Nó **không mang thông tin nào**.
> Một bảng constraint toàn confidence 1,0 sẽ bị reviewer bắt ngay lập tức.

Thêm nữa, ngay cả khi có neg, ngưỡng 0,9 vẫn vô nghĩa: **constraint rỗng** "mọi cặp ⇒ BEFORE" đạt
440.206/483.544 = **0,9104** và **vượt** `confidence_threshold=0.9` của PaTeCon. Hàm chấm điểm không phân
biệt được quy luật thật với tỉ lệ nền. Xếp hạng **phải** dùng lift / PMI / binomial tail, không phải tỉ số trần.

### B5 — Vắng nhãn nghĩa là gì?

**Chính sách: UNKNOWN theo mặc định, và KHÔNG BAO GIỜ được gọi là lỗi chú thích — trừ một ngoại lệ hẹp:
transitive forcing.**

| Đại lượng | Train | Valid |
|---|---|---|
| Cặp không nhãn | 806.711 (50,45%) | — |
| Bị ép bởi closure 1 bước (cặp phân biệt) | **3.481** = 0,43% số cặp không nhãn | 563 |
| Trong đó suy ra >1 nhãn khác nhau | **0** | 0 |
| Xung đột closure (suy ra ≠ đã khẳng định) | **0** | 0 |

Phát biểu đúng cho paper: **"MAVEN-ERE nhất quán nội bộ 100% và đóng suy diễn 99,5% ở 1 bước;
3.481 cặp còn lại là phần BỔ SUNG, không phải phần SỬA."**

> **Sửa số học kép:** B5 đồng thời (a) bác luật OVERLAP+BEFORE là "không biện minh được" và (b) dùng chính
> luật đó để tính con số headline 3.481 của mình. 1.816 residual OVERLAP+BEFORE **đã nằm trong** 3.481,
> không cộng thêm — nên "3.481 → ~5.300" là đếm hai lần. Bỏ luật đó thì headline tụt xuống **2.265 cặp**.
> Vì tôi đã chốt OVERLAP=`{o}` (làm luật này **sound** — `comp({o},{b,m})={b}`), **giữ luật và giữ 3.481**,
> nhưng bỏ hẳn câu "tôi không biện minh được luật này".

Tôi phân loại toàn bộ residual của cả 21 luật trên valid:

| Luật | Vi phạm | Phân loại |
|---|---|---|
| OVERLAP+BEFORE | 364 | **100% ABSENT** |
| BEFORE+OVERLAP | 296 | **100% ABSENT** |
| BEFORE+ENDS-ON | 16 | 100% ABSENT |
| BEFORE+BEGINS-ON | 5 | 100% ABSENT |
| BEGINS-ON+BEGINS-ON | 8 | Mang **SIMULTANEOUS** — đúng ngữ nghĩa, không phải xung đột |

**681/689 là ABSENT** = UNKNOWN có tài liệu. 8 cái còn lại là một clique BEGINS-ON 4-event trong **một**
document, và cặp hợp thành được gán SIMULTANEOUS, hoàn toàn hợp lý cho hai event bắt đầu cùng lúc và
đồng phạm vi. **Không có residual nào là lỗi chú thích.** Câu hỏi mở "nên xem tay 20 cái" đã **được trả lời
bằng phép đo** — không cần xem nữa.

---

## 5. C. Ngôn ngữ pattern

### C1 — Lattice

Đếm trên 432.027 instance EE có nhãn với cả hai endpoint có trong MAVEN-Arg:

| Level | Key | Distinct | sup≥10 | sup≥25 | sup≥100 | inst@sup25 | Phán quyết |
|---|---|---|---|---|---|---|---|
| **L1** | `(t1,t2)` | 20.145 | 8.320 | **4.251** | 792 | 326.992 | **Xương sống** |
| L1s | `(t1,t2)` + share≥1 | 11.472 | 1.965 | 636 | 80 | 40.783 | Yếu, giữ |
| L2 | `(t1,t2)` + share≥2 | 3.988 | 293 | 98 | 14 | 7.061 | **Giữ** (67 thành viên family) |
| **L3** | `(t1,t2,entType)` | 22.204 | 1.928 | 539 | 58 | 32.162 | Giữ — **lift cao nhất** |
| L3r | `(t1,t2,role1,role2)` | 27.417 | 2.193 | 650 | 78 | 40.290 | Giữ |
| **L4** | `(t1,t2,sdist_abs)` | 65.240 | 10.887 | **3.191** | 243 | 162.470 | **Giữ — ĐÃ CHỐT** |
| L4t | `(t1,t2,sdist,torder)` | 87.610 | 9.873 | 2.595 | 181 | 128.716 | **BỎ khỏi key**; torder thành trục riêng |
| L4s | L4 + share≥1 | 32.841 | 1.218 | 231 | 19 | 11.316 | **BỎ** |

> **ĐÃ GỠ CHẶN (C1c, đo trên full train 2.913 doc).** Cả hai bộ số cũ tái lập **chính xác**: 4-tuple
> 87.610 distinct / 2.595 @sup≥25; 3-tuple 65.240 / 3.191. Nhưng khuyến nghị "giữ torder" **bị bác bỏ bằng
> holdout**: trên valid (710 doc, chưa từng dùng để mine), tỉ lệ tái lập lift≥2 của thành viên L4 là
> 4-tuple **340/400 = 85,00%** vs 3-tuple **378/461 = 82,00%** — **z = 1,181, p = 0,2374, KHÔNG có ý nghĩa
> thống kê**. Đổi lại, 3-tuple cho **378 ràng buộc tái lập được so với 340** (+11,18%), phủ **8.427 vs 6.735
> instance valid** phân biệt (+1.692 = **+25,12%**; 8,590% vs 6,865% của 98.108).
>
> Phép tách theo torder **phá nhiều hơn tinh chỉnh**: **107/512** thành viên 3-tuple **biến mất** khi tách
> (cả hai con rơi dưới sup≥25 hoặc k≥10), chỉ **38** tách thành cả FWD lẫn BWD, và trong số sống sót lift
> con tốt nhất cao hơn cha **207** lần nhưng **thấp hơn 177** lần. Chỉ **5/448** thành viên 4-tuple không có
> đối ứng 3-tuple. **CHỐT: L4 = `(t1, t2, sdist_abs)`.**
>
> **Cảnh báo — 207/177 KHÔNG phải bằng chứng chống torder.** Chạy null đối chứng (tách bằng nhãn nhị phân
> ngẫu nhiên khớp biên P=0,8483, 3 seed) cho **245–248 lift-up vs 172–183 lift-down** và mất 83–94 thành
> viên. Tức nhiễu do chia mẫu thuần tuý tạo ra tỉ lệ up/down **mạnh hơn** (~1,42) so với torder (1,17), và
> "107 biến mất" tái lập đầy đủ bằng một nhãn vô nghĩa. Thống kê này **không mang thông tin** về torder;
> lý do chốt 3-tuple là hai dòng trên (không ý nghĩa thống kê + nhiều constraint tái lập hơn), không phải nó.
>
> **torder KHÔNG vô dụng** — nó cực kỳ thông tin về BEFORE-hay-không: P(BEFORE) = 81,54% FWD vs 71,00% BWD
> ở sdist 0; 92,67% vs 84,03% ở sdist 1 (chi2 gộp 5 df = **1.826,8**, chi2 2×2 không hiệu chỉnh). Nó phải là
> **một trục refinement riêng**, áp dụng có chọn lọc — đúng theo nguyên tắc "lattice là tích 3 trục độc lập"
> của chính C1 — chứ không nung vào key, vì nung vào key trả giá support trên **mọi** pattern.
>
> **Cảnh báo phát sinh — rò rỉ BH-FDR xuyên level.** Số thành viên L1 đổi 445 → 446 giữa hai biến thể **dù
> level L1 không đổi một byte nào**: đổi key L4 làm đổi kích thước pool giả thuyết gộp (10.393 vs 9.715),
> làm dịch chỉ số cắt BH, lật một cell L1 ở biên. Mọi con số family theo level vì thế **phụ thuộc vào lựa
> chọn key L4**. Muốn số theo level ổn định thì phải chạy BH **trong từng level**, không gộp.

> **Định nghĩa đóng băng của sdist và torder (C1c).**
> `sentence_distance` = **trị tuyệt đối** hiệu `sent_id` của **mention đầu tiên** (first mention = min theo
> thứ tự `(sent_id, offset)`), bucket {0, 1, 2-3, 4-8, 9+}. Dấu được mang **riêng** bởi torder.
> *Đã đo trước khi chọn:* chỉ **3,3846%** cluster (2.301/67.984) trải trên >1 câu; **5,1349%** instance
> (22.184/432.027) có ít nhất một đầu mút đa câu. **first và min trùng nhau 100%** (0 instance lệch) — đây
> là **hệ quả tất yếu** của việc sort `pts` theo `(sent_id, offset)`, ghi lại như một phép kiểm chứng rằng
> sort làm đúng, **không phải** một phát hiện thực nghiệm. Median lệch first ở **4,8833%** instance và **đổi
> bucket ở 3,1091%** (13.432). Chọn first/min: nó là điểm người đọc **lần đầu** biết sự kiện tồn tại — đúng
> ngữ nghĩa của một đặc trưng khoảng cách diễn ngôn; median không có diễn giải diễn ngôn nào.
>
> `textual_order` = so sánh **từ điển trên tuple `(sent_id, offset_start)`** của mention đầu tiên (KHÔNG
> phải offset token phẳng — MAVEN-ERE cho offset **theo câu**). Giá trị đo được: FWD **366.506 (84,834%)**,
> BWD **65.521 (15,166%)**. **Luật hoà (SAME) không bao giờ kích hoạt: 0/432.027** — hai cluster khác nhau
> không thể cùng có mention đầu ở đúng một `(câu, offset)`, vì đó là cùng một token span và MAVEN chú thích
> thành một event. Đã kiểm chứng trực tiếp trên cả 2.913 doc: **0** vị trí `(sent_id, offset)` chứa >1
> cluster. **Xoá SAME khỏi tập giá trị trong đặc tả**, giữ nhánh trong code phòng khi nhận TIMEX.
>
> **TIMEX không phát sinh** ở tầng này: luồng instance L4 là EVENT-EVENT và phải nằm trong MAVEN-Arg, vốn
> không có TIMEX. Nếu sau này nhận TIMEX (lấy lại 38,98% quan hệ đang bị bỏ), neo là chính `(sent_id, offset)`
> của TIMEX đó, và nhánh SAME phải quay lại vì TIMEX và event **có thể** chung vị trí bắt đầu.
>
> *Kiểm tra đồng nhất thức:* **42.870** key 3-tuple có đúng 1 giá trị torder, **22.370** có cả hai →
> 42.870 + 2×22.370 = **87.610**, khớp đúng số distinct 4-tuple. Hai bộ đếm xác nhận lẫn nhau.
>
> *Lưu ý thiết kế — KHÔNG được viết "signed sdist ≡ abs sdist + torder" vào paper.* Đẳng thức chỉ đúng khi
> delta **khác 0**. Ở **39.839** instance cùng câu (9,22%), sdist có dấu sụp về một bucket "0" không dấu, và
> torder là **người mang duy nhất** thông tin thứ tự ở đó (FWD 30.317 / BWD 9.522). Chính vì vậy `L4_signed`
> một mình chỉ cho **84.290** distinct chứ không phải 87.610 — chênh 3.320 key đúng bằng phần thông tin đó.
> Hai key 87.610 trùng nhau **chỉ sau khi** bucket 0 bị bỏ dấu.

> **Sửa (đã kiểm chứng C1c, khớp chính xác).** ERE train có **168** event type xuất hiện trên 67.984 event
> cluster; **162 là inventory của Arg** — nên "(162 giá trị)" không phải bịa, nó là con số **đúng của sai bộ
> dữ liệu**. Trong 64.335 cluster có mặt ở cả hai bộ, **4.602 = 7,1532%** mang type khác nhau; 10 type chỉ
> có ở ERE, 4 chỉ có ở Arg.
> **Key L1 đọc type từ MAVEN-ERE**, `aev` **chỉ** dùng để lọc alignment và lấy entity/role, **không bao giờ**
> lấy type. Đây là quyết định **chịu lực**, không phải chi tiết: **15,5231%** instance (67.064/432.027) có ít
> nhất một đầu mút lệch type — **hơn gấp đôi** con số 7,15% vốn đếm theo cluster — và đổi key sang type Arg
> làm L1 tụt từ **20.145 → 19.161** distinct và **4.251 → 4.014** ở sup≥25. Các bất đồng là **hệ thống**:
> `Hostile_encounter→Military_operation` (1.963), `Self_motion→Motion` (912), `Escaping→Retreat` (709) — Arg
> cắt inventory thô hơn đúng ở nhóm xung đột/chuyển động vốn thống trị corpus này. Chọn ERE là **đúng**
> (quan hệ thời gian đang mine là chú thích của ERE, key phải sống cùng không gian chú thích với nhãn),
> nhưng **paper bắt buộc phải nói ra**, vì người đọc giả định type Arg sẽ tái lập ra số khác trên 15,5% dữ liệu.

> **Sửa nội bộ:** C1 ra lệnh "DROP L2" nhưng C5 dùng 67 thành viên L2 và C2 xếp L2 **đặc thù nhất** trong
> SPEC. Một level không thể vừa bị bỏ vừa là người phân xử ưu tiên cao nhất. **Chốt: giữ L2**; nó chỉ trượt
> phép thử argmax/confidence — đúng phép thử mà C3 bác bỏ.

Lattice là **tích 3 trục độc lập**, không phải chuỗi. Và lưu ý: node lattice là cặp `(level, key)`, không
phải key — L1/L1s/L2 dùng **cùng một keyspace** `(t1,t2)` và chỉ khác vị từ thành viên. Tính đơn điệu
theo từng ô đúng (0 vi phạm), nhưng L3 là **set-valued** nên các con **không phân hoạch** cha:
111 cha L1 có tổng support con vượt cha, và 11.146 instance nằm trong ≥2 ô L3 — điều này âm thầm thổi phồng
pool giả thuyết BH.

### C2 — Refinement

Hình dạng của PaTeCon chuyển giao được (một pass, fan-out có chặn, không vòng lặp hội tụ). **Trigger và
acceptance thì không.**

| Khía cạnh | PaTeCon | MAVEN | Lý do |
|---|---|---|---|
| Trigger | confidence ∈ [0,5, 0,9) | entropy ≥ ngưỡng ∨ enriched | 61,2% pattern L1 đã đơn-quan-hệ ở mức 95%; dải confidence bắn vào nhóm sai |
| Trục | 1 (class của object) | 3–4 (share, entity type, role pair, sdist) | MAVEN không có hình dạng triple (subject, relation, object) |
| Acceptance | ngưỡng tuyệt đối | so với **CHA**, two-proportion + BH | Với prior BEFORE 90,88%, ngưỡng tuyệt đối để nhiễu lọt |
| Supersession | tai nạn (cùng bộ lọc) | **BỎ** — xem phán quyết dưới | Luật ghi đè là **không đúng đắn** cho tập ràng buộc |

> **ĐÃ ĐO — thủ tục đã chạy đầy đủ trên full train (3,03 s). PHÁN QUYẾT: BỎ REFINEMENT KHỎI THIẾT KẾ.**
>
> Cài với MAX_DEPTH=1 (một trục mỗi child), parent = 4.251 pattern L1 sup≥25, 4 trục (share-count, entity
> type, role pair, sentence distance). Trigger H≥0,8341 (phân vị 90 thực đo) ∨ enriched. Acceptance:
> two-proportion child vs **phần-còn-lại-của-cha** + BH q=0,05 + lift≥2.
>
> **Fan-out thật:** alphabet toàn cục là **1.628** giá trị (role pair một mình 1.614, entity type **6** giá
> trị quan sát được: Art, Building, Location, Organization, Person, Product), không phải 24. Nhưng fan-out
> **thực hiện** chỉ ~15,6 child/parent vì phần lớn role pair không bao giờ đồng xuất hiện với một cặp type
> cho trước. Depth-2 chỉ nở ~2,9× và chạy dưới 2 s — **MAX_DEPTH=2 không hề bất khả thi về chi phí**; nó bị
> bác vì **phân mảnh support**, không vì tốn kém. (Tỉ lệ child depth-2 qua được sup≥25 đo được 2,83%; một
> lần đo khác cho 9,06% — chênh lệch nằm ở quy ước liệt kê ô khi trục set-valued rỗng, và **phải ghi rõ quy
> ước đó** nếu con số này được trích dẫn. Cả hai giá trị đều ủng hộ cùng kết luận.)
>
> **Ngưỡng entropy suy từ đuôi trên thật:** 10% → H≥0,8341; 5% → H≥0,9852; 1% → H≥1,1629. Ngưỡng 0,35 của
> tài liệu bắn vào **34,89%** (không phải 38,5%) và tương ứng top-1 share 0,9342 cho pattern 2-quan-hệ.
> 25,88% pattern có entropy đúng bằng 0.
>
> **REFINEMENT KHÔNG GIÚP GÌ — đo trên holdout valid (98.108 instance, family mine chỉ trên train):**
> - Đóng góp riêng của refinement: **+0,071 pp** precision, **+0,002 pp** coverage.
> - Dưới most-specific-wins nó **tệ hơn: −1,307 pp**.
> - Con số +5,04 pp nếu đổi sang rank-by-confidence là **ảo**: phân rã cho thấy **+4,969 pp** đến từ việc
>   đổi luật phân xử áp lên **L1 một mình, không refinement gì cả**.
> - Quét 20 cấu hình: delta từ **−0,934 pp đến +0,080 pp**. Ngưỡng 0,35 của chính tài liệu cho **−0,517 pp**.
> - Coverage mới: dưới **0,05%** instance trên cả hai split (đo được 2–32 trên valid tuỳ kích thước family
>   nền; con số tuyệt đối không ổn định, bậc độ lớn thì ổn định).
>
> **CƠ CHẾ THẤT BẠI (quan trọng cho paper):** child mất support. Median child n=48 so với cha n=289 (tỉ lệ
> 0,166). Mà WilsonUB(0,n) ≥ τ=0,02 với mọi **n ≤ 188**, nên child nhỏ hơn mức đó **không cấm được quan hệ
> nào** — tập allowed của nó là cả 6 theo cấu trúc. Đo được: **81,7% child được chấp nhận có tập allowed
> LỚN HƠN cha, 0% nhỏ hơn**; cặp khớp đúng là **4,03 → 5,92** (Δ = **+1,89** quan hệ). **95,7%** child nằm
> dưới sàn falsifiability. Refinement đẩy tầng constraint C4 **ngược chiều**.
>
> > **Nhưng phải nói kèm null, nếu không sẽ là phát biểu rỗng:** WilsonUB đơn điệu theo n, nên **mọi** tập
> > con nhỏ hơn đều có khoảng rộng hơn. Đối chứng bằng cách lấy mẫu con ngẫu nhiên **cùng cỡ** của chính cha
> > cho **81,9% lớn hơn, Δ trung bình +1,858** — trùng con số thật tới ba chữ số thập phân. Vậy 81,7% **không
> > mang thông tin** về refinement; điều đúng và đáng viết là dạng tổng quát: *không một lược đồ đặc thù hoá
> > nào có thể làm constraint sắc hơn ở mức support này, vì falsifiability phải mua bằng n.*
>
> **Trong khung INJECTION (2% và 5%, seed 7):** thêm child bắt được **0** lỗi tiêm mà L1 bỏ sót, nhưng
> **làm mất 75 (2%) / 170 (5%)** lỗi mà L1 một mình đã bắt được.
>
> > **Nguyên nhân là luật hợp thành sai, không phải refinement.** Cha và con đều là ràng buộc **hợp lệ** trên
> > cùng một cặp, nên phép hợp thành đúng là **GIAO**, không phải để con ghi đè cha. Vứt một constraint chặt
> > hơn chỉ vì một constraint lỏng hơn "đặc thù hơn" là lỗi của luật, không phải của tầng. Đo được: dưới
> > **giao**, refinement bắt TP=1.164 so với L1 đơn độc 1.163 — **không mất gì**. Vậy phát biểu đúng là:
> > *supersession kiểu ghi-đè là KHÔNG ĐÚNG ĐẮN cho tập ràng buộc và phải thay bằng giao* — chứ không phải
> > "most-specific-wins gây hại". Refinement vẫn bị bỏ, nhưng vì +0,071 pp, không vì con số −73/−170 này.
>
> **PHÁN QUYẾT: bỏ C2 khỏi thiết kế.** Tiết kiệm toàn bộ công cài refinement và supersession. Giữ L1 làm
> tầng pattern duy nhất.

**Nhánh `enriched` — sửa con số và chốt effect size:**

WilsonLB(10,n) > 0,00022684 (base ENDS-ON) đúng cho n tới **23.947** — tài liệu cũ ghi 4.999, **thấp hơn
thực tế ~5 lần**. Quy tắc này kích hoạt trên 1.506/4.251 = 35,43% parent, trong đó ~341 kích hoạt trên
**nhiễu thuần** dưới null hoán vị nhãn **trong từng document** (5 lần chạy: 335/348/323/348/349).

> **Chọn effect size theo FDP, không theo "FPR".** Con số "giảm 47×" là **sai mẫu số**: 8,01% là nhiễu chia
> cho **toàn bộ 4.251 parent**, một mẫu số không liên quan tới quyết định. Đại lượng quyết định là
> **FDP = nhiễu / số thật sự bắn**:
>
> | Quy tắc | Bắn | Nhiễu (null) | FDP | Firing thật giữ lại |
> |---|---|---|---|---|
> | WilsonLB, k≥10 | 1.506 | 340,6 | 22,62% | 1.165 |
> | k≥10 ∧ lift≥2 | 413 | 111,6 | 27,02% | 301 |
> | k≥25 ∧ lift≥2 | 187 | 32,0 | 17,11% | 155 |
> | **k≥10 ∧ lift≥3** | **333** | **27,0** | **8,11%** | **306** |
> | k≥25 ∧ lift≥3 | 171 | 7,2 | 4,21% | 164 |
>
> Cải thiện thật là **22,62% → 8,11% = 2,8×** (hoặc 5,4× nếu đi tới k≥25), **không phải 47×**.
> **CHỐT: `k ≥ 10 ∧ lift ≥ 3,0`** — giữ **306** firing thật ở FDP 8,11%, gần gấp đôi sản lượng của
> `k≥25 ∧ lift≥3` (164) với độ tinh khiết cùng bậc.
>
> Null hoán vị **trong từng document** là công cụ đúng và phải dùng toàn dự án: khác với null xáo **toàn
> cục** mà C3 đã phê phán (cho kết quả rỗng), null này trả về một sàn nhiễu **thực chất và ổn định**.

### C3 — support_min, confidence_min, hàm chấm điểm

**`sup_min = 25`, `k_min = 10`, chấm bằng per-relation enrichment + binomial tail + BH-FDR q=0,05 + lift ≥ 2,0.**

Giả thuyết của brief được xác nhận và còn mạnh hơn phát biểu. Tỉ lệ nền BEFORE = 90,880%.

| Hàm chấm điểm | Sống sót @L1 sup≥25 | Trong đó non-BEFORE |
|---|---|---|
| raw confidence ≥ 0,90 | 3.366 | **0** |
| Wilson LB trên argmax ≥ 0,90 | 1.286 | **0** |
| Wilson LB ≥ 0,80 + lift ≥ 1,05 | 2.496 | **0** |

**Điểm phân tích then chốt: Wilson KHÔNG cứu được.** Wilson hiệu chỉnh **cỡ mẫu**, không hiệu chỉnh
**prior lệch**. Đây là điều đáng viết rõ trong paper vì Wilson là cách sửa hiển nhiên đầu tiên mà ai cũng nghĩ tới,
và nó chứng minh được là không hoạt động ở đây.

**Cách sửa:** chấm từng **cell** `(pattern, relation)` so với tỉ lệ nền của chính quan hệ đó, thay vì chấm
pattern bằng argmax. Việc này biến bài toán phân loại 6 lớp vô vọng trước đa số 90,9% thành 6 phép thử
enrichment one-vs-rest độc lập.

| Quan hệ | Pattern enriched @L1 | Lift cao nhất |
|---|---|---|
| CONTAINS | 414 | 9,27× (Competition/Connect 21/30) |
| SIMULTANEOUS | 42 | 27,81× (Committing_crime/Committing_crime 11/45) |
| OVERLAP | 32 | 34,69× (Killing/Bodily_harm 81/383) |
| BEGINS-ON | 1 | — |
| ENDS-ON | 0 | — |

**Ba phép kiểm chứng đều qua:** BH-FDR q=0,05 trên 6.484 giả thuyết → 1.692 significant, 900 non-BEFORE.
Holdout trên valid (chưa bao giờ dùng để mine): CONTAINS 273/307 = 88,9%, SIMULTANEOUS 40/41 = 97,6%,
OVERLAP 28/31 = 90,3%. Permutation null: 0 / 0 / 0 significant qua 3 lần so với 1.227 quan sát được.

> **Sửa:** "0 non-BEFORE ở **mọi** level và **mọi** support" sai. L3 cho **2** (sup≥10) và **1** (sup≥25).
> Và một trong số đó — `(Social_event, Competition, Person)` CONTAINS 36/37 lift 12,88 — được chính C3 trích
> dẫn ở chỗ khác như một phát hiện enrichment headline. Phát biểu đúng **củng cố** C1: L3 là level duy nhất
> mà pattern non-BEFORE sống sót được cả phép thử argmax, tức đúng là nơi tín hiệu nằm.

> **Cảnh báo về permutation null:** nó xáo nhãn **toàn cục** trên cả 432.027 instance rồi chấm ngược lại
> chính tỉ lệ nền toàn cục đó. Một null phá huỷ nhiều cấu trúc hơn giả thuyết đang kiểm sẽ cho kết quả
> rỗng gần như chắc chắn. Nó chứng minh máy BH không hỏng, **không** chặn được FDR dưới null thực tế.
> Chạy lại với xáo **trong từng document**. Holdout là phép kiểm mạnh hơn nhiều — hãy để nó gánh lập luận.

### C4 — Một quan hệ hay một tập?

**Tập cho phép, dựng từ Wilson UPPER bound: `r ∈ ALLOWED(p) ⟺ WilsonUB(k_r, n_p) ≥ τ`, `τ = 0,02`.**

| Level | npat | meanH (bit) | mean top-1 | Cần ≥2 quan hệ để phủ 95% |
|---|---|---|---|---|
| L1 | 4.251 | 0,312 | 0,9285 | 1.651 = **38,84%** |
| L1s | 636 | 0,614 | 0,8314 | 454 = 71,4% |
| L3 | 539 | 0,792 | 0,7659 | 445 = **82,6%** |
| L4 | 2.595 | 0,383 | 0,8915 | 1.161 = 44,7% |

Ánh xạ một-quan-hệ sai cho 38,84% pattern L1 và **82,6%** pattern L3 — tức nó hỏng **nặng nhất đúng ở nơi
pattern giàu thông tin nhất**.

Wilson-UB tốt hơn cumulative-mass vì **falsifiability phải được kiếm bằng support**: pattern có n=25 và
k_r=0 cho UB = 0,1332 > τ, nên nó **không cấm gì cả**. Cumulative mass thì bắt pattern n=25 khẳng định
cùng loại trừ như pattern n=5.000.

**Kết quả trung thực và quan trọng:** constraint **có** falsifiable, nhưng trên gold chúng chỉ bị vi phạm bởi
**297 instance ở L1**.

> **Sửa mẫu số:** 297/432.027 = **0,0687%**, không phải 0,0908%. Con số 0,0908% là 297/326.992, tức chỉ tính
> khối lượng instance được phủ bởi pattern sup≥25. Đề xuất ghép sai mẫu số ở **ba** chỗ. Viết đúng:
> *"297 trong 326.992 instance được phủ bởi pattern L1 tại sup≥25 (0,0908%), tức 0,0687% của toàn bộ 432.027."*

> **Vấn đề vòng tròn chưa giải:** `TABLE[L][p][r(x)]` **đếm cả chính x**. Instance bị gắn cờ là bất thường vì
> nó là một trong số ít instance cùng loại, và nó là một trong số ít vì chính nó đang được đếm. Điều này
> đổi phán quyết ở biên: n=200,k=1 **không** bị cấm in-sample nhưng **bị** cấm sau leave-one-out.
> **Sửa: định nghĩa FORBIDDEN bằng đếm leave-one-document-out.**
> Cũng bỏ hàm SEVERITY hiện tại — nó xếp một cell có 19 vi phạm là nghiêm trọng hơn cell có 1, tức càng
> lỗi nhiều thì mỗi lỗi càng nghiêm trọng, ngược với mọi prior về lỗi chú thích.

> **Thuộc tính cấu trúc đáng ghi vào paper:** 0 pattern nào ở L1 sup≥25 có WilsonUB(BEFORE) < 0,05.
> **Không constraint nào có thể loại trừ BEFORE.** Ngược lại, 942 pattern loại trừ được SIMULTANEOUS
> (phủ 35,92% instance) và 357 loại trừ CONTAINS (13,86%).
>
> **Định lượng hoá (C3Rb).** Phát biểu này đúng nhưng phải viết **có điều kiện τ**, nếu không reviewer bác
> được bằng một dòng. Đo trên cả năm level: **0/8.156** pattern có WilsonUB(BEFORE) < τ, và **min WilsonUB
> (BEFORE) = 0,446** (đạt tại `(Military_operation, Hostile_encounter)`, n=419, k=167). Nên phát biểu đúng là:
> *BEFORE bất khả cấm với mọi τ < 0,446 — tức ở mọi điểm vận hành dùng được* — chứ không phải "bất khả cấm
> vô điều kiện". Hệ quả đo được: recall trên xung đột tiêm thành nhãn BEFORE là **đúng 0,000%**.

> **Sàn falsifiability đo được (hệ quả của C2, đáng đưa vào paper).** Với τ=0,02 và z=1,96, dạng đóng
> `WilsonUB(0,n) = z²/(n+z²)`, nên điều kiện `< τ` là `n > z²(1/τ − 1) = 188,24`:
> **n ≤ 188 không thể loại trừ bất kỳ quan hệ nào; n = 189 là support nhỏ nhất làm được.**
> (WilsonUB(0,188) = 0,020025 ≥ τ; WilsonUB(0,189) = 0,019921 < τ.) Các sàn khác, α=0,05:
> τ=0,01 → n≥381; τ=0,05 → n≥73; τ=0,10 → n≥35. Với α=0,01: 657 / 326 / 127 / 60.
> Đây là ràng buộc **cứng** lên mọi nỗ lực đặc thù hoá: càng chia nhỏ pattern càng mất khả năng phủ định.
> Nó là lý do toán học khiến C2 thất bại, và nó cũng làm `sup_min` gần như **vô tác dụng** — Wilson-UB tự áp
> sàn chặt hơn nhiều, nên sup=25 / 50 / 100 cho kết quả **giống hệt** ở τ≤0,05. Giữ `sup_min=25` cho vệ sinh,
> nhưng **không được trình bày nó như một siêu tham số đã tinh chỉnh**.

### C5 — Characteristic family

**Family = tập cell `(pattern, relation)` BH-significant với lift ≥ 2, gộp qua mọi level còn sống.**

| Đại lượng | L4 = 3-tuple **(ĐÃ CHỐT)** | L4 = 4-tuple (bỏ) |
|---|---|---|
| Giả thuyết quét | 10.393 | 9.715 |
| BH-significant | 2.583 | 2.483 |
| Sau lọc lift ≥ 2 | **1.456** | 1.393 |
| Theo quan hệ | CONTAINS 1.253 / SIMUL 137 / OVERLAP 65 / BEGINS-ON 1 / **BEFORE 0** | CONTAINS 1.198 / SIMUL 136 / OVERLAP 58 / BEGINS-ON 1 |
| Theo level | L4 512 / L1 445 / L3 237 / L1s 195 / L2 67 | L4 448 / L1 **446** / L3 237 / L1s 195 / L2 67 |
| Phủ | 70.911 = 16,41% | 70.713 = 16,37% |

> Hai cột trên là bảng **không B2-dedupe** đã công bố, giữ lại để đối chiếu lịch sử. Dưới định nghĩa đóng
> băng đầy đủ (B2-dedupe + share entity-id + L4 3-tuple) tôi đo lại được **1.392** thành viên và tập khớp
> **70.697 = 16,37%** — xem khối chi tiết bên dưới. Chênh lệch với 1.456 là 38 instance B2 và nhiễu biên BH;
> **đừng trộn hai bộ số trong cùng một bảng của paper.** Lưu ý L1 đổi 445 → 446 giữa hai cột **dù level L1
> không đổi**: đó là rò rỉ BH-FDR xuyên level đã ghi ở C1.

**0 thành viên BEFORE là hệ quả toán học**, không phải hiện vật: `1/0,90880 = 1,100 < 2,0`, nên BEFORE
không thể đạt lift 2. Đây chính là điểm: family đúng bằng tập phát biểu **không phải** diễn đạt lại tỉ lệ nền.

**Công thức argmax bị bác bỏ bằng đo đạc**: 225 thành viên, phủ 9,57%, và chỉ **5** thành viên có tập
cho phép khác `{BEFORE}`, tất cả với lift 1,06–1,08. Một family 98% là "BEFORE thường gặp ở đây" không phải
kết quả khoa học.

> **ĐÃ ĐO — KHUNG DỰ ĐOÁN BỊ RÚT LẠI. Không một luật giải đa khớp nào đáng có.**
>
> Tất cả số dưới đây đo lại với vị từ share **đúng** (xem cảnh báo ngay sau), trên 431.989 instance
> B2-deduped, tập được khớp **n = 70.697 (16,37%)**.
>
> **Phân bố gold trên tập được khớp:** BEFORE **67,85%** · CONTAINS **28,38%** · SIMULTANEOUS 2,29% ·
> OVERLAP 1,32% · BEGINS-ON 0,13% · ENDS-ON 0,03%.
>
> | Chính sách | Accuracy |
> |---|---|
> | hằng "luôn BEFORE" | **67,85%** |
> | hằng "luôn CONTAINS" | **28,38%** |
> | SPEC như viết (L2>L1s>L4>L3>L1) | 28,24% |
> | majority vote | 28,24% |
> | SPEC đảo ngược | 27,96% |
> | no rule (ngẫu nhiên có seed) | 26,23% |
> | highest lift | 25,27% |
> | highest support | 25,12% |
> | *ORACLE (chọn đúng khi có thành viên nào đúng)* | *30,19%* |
>
> **SPEC THUA hằng-CONTAINS**, net **−93** instance (McNemar b=1.004, c=1.097). Đây là **đảo dấu** so với
> vòng đo trước, vốn báo SPEC thắng +0,26 điểm với p=1,5e-07; chênh lệch đó là hiện vật của vị từ share sai.
> Và cả hai đều thua xa hằng-BEFORE.
>
> > **Nhưng đừng dùng hằng-BEFORE làm baseline quyết định.** Family chứa **0 thành viên BEFORE theo cấu
> > trúc** (`1/0,90888 = 1,100 < 2,0`), nên không chính sách nào **có thể** phát ra BEFORE, và 67,85% tập
> > khớp nằm ngoài không gian output. Khoảng cách ~39 điểm tới hằng-BEFORE đo **định nghĩa của family**, không
> > đo chất lượng luật phân xử. Baseline **trong tầm** là **ORACLE 30,19%**, và SPEC ở 28,24% tức đạt **93,5%**
> > trần khả đạt. Phát biểu trung thực: *ràng buộc là **độ phủ nhãn của family**, không phải luật giải đa
> > khớp; luật nào cũng chạm gần trần, và trần thì thấp.* Giữ hằng-BEFORE làm **cước chú** cho thấy family cố
> > tình không phải bộ phân loại — đừng làm nó thành lập luận chính.
>
> **Kết luận: rút lại use case (i) (dự đoán).** Không phải vì một luật cụ thể sai, mà vì cả họ luật chỉ di
> chuyển trong dải 25,1%–28,2% dưới trần 30,2%, trong khi một hằng số không cần mining đạt 28,38%.

> **CẢNH BÁO ĐỊNH NGHĨA — vị từ `share` tính trên ENTITY ID, không phải cặp (role, entity).**
> Đây là lỗi đã làm hỏng một vòng đo trọn vẹn và phải ghi rõ ở đây. A2 định nghĩa
> `args(ev) = {(role, entity_id)}` **và** `ents(ev) = π₂(args(ev))`; L1s/L2 dùng **`ents`**, còn cặp
> `(role, entity)` chỉ dùng cho trục **L3r**. Kiểm chứng: chỉ định nghĩa entity-id mới tái lập bảng C1 đã
> công bố — L1 4.251 / L1s **636** / L2 **98** / L3 538 — trong khi role-pair cho L1s 406 / L2 57. Tỉ lệ cặp
> chia sẻ ≥1 entity cũng chỉ khớp 20,14% dưới entity-id (role-pair cho 13,08%).

**Kích thước family dưới định nghĩa đã đóng băng (L4 3-tuple, share entity-id):** 1.392 thành viên —
L1 446 / L4 448 / L3 236 / L1s 195 / L2 67; theo quan hệ CONTAINS 1.197 / SIMULTANEOUS 136 / OVERLAP 58 /
BEGINS-ON 1 / **BEFORE 0**. Trong đó **1.148** phát biểu `(key, relation)` phân biệt, **244** bản sao.
**64/67** thành viên L2 là bản sao `(key, relation)` y hệt của một thành viên L1 hoặc L1s — con số này
**khớp đúng** giá trị đã ghi từ trước, không phải 67/70.

> **Đa khớp phải đếm theo `(key, relation)`, không theo `key`.** Dedupe theo key một mình sẽ **gộp hai phát
> biểu bất đồng về cùng một key thành một** — tức xoá đúng phần bằng chứng cạnh tranh mà luật giải đa khớp
> tồn tại để phân xử. Đo được ba mức: theo **cell** 61,93% → theo **`(key, relation)`** **59,00%** → theo
> **key** 51,96%. Con số phải báo cáo là **59,00%**; phần giảm do trùng level là 61,93% → 59,00%, tức ~2,9
> điểm, không phải hơn chục điểm.

**SPEC order — ngược chiều cục bộ nhưng không sửa được bằng đảo.** Trên các instance mà lựa chọn L4 và L1s
bất đồng, lựa chọn của SPEC (L1s) đúng ~139 lần còn lựa chọn bị loại (L4) đúng ~724 lần — bất đối xứng
~5,2×, tái lập vững qua cả ba biến thể L4 và cả hai định nghĩa share. **Nhưng đảo toàn bộ SPEC cho 27,96%,
TỆ HƠN** bản gốc 28,24%.

> Không được kết luận từ đó rằng "thứ tự không mã hoá gì". Đảo **toàn bộ** không phải là phép sửa mà chẩn
> đoán L4-vs-L1s gợi ý: nó còn đẩy L1 lên đầu, L3 trên L4, L2 xuống cuối — một hoán vị khác hẳn trong 120
> hoán vị, và chỉ một cái được thử. Phép sửa **tối thiểu** (hoán vị **chỉ** L4 với L1s) chưa từng được đo.
> Thêm nữa, chẩn đoán chạy trên thành viên **raw** còn chính sách chấm trên thành viên **deduped** — hai tập
> khác nhau, không ghép thành một kết luận được. Vì use case (i) đã rút lại, đây là **điểm treo vô hại**:
> ghi lại là chưa đo, đừng tuyên bố thứ tự vô nghĩa.

**Dùng phi-dự-đoán — đây mới là đóng góp còn lại.** Family đọc như **tập phát biểu khả phủ chứng**:
**189** instance gold vi phạm in-sample, **237** dưới leave-one-document-out (0,044% / 0,055% của 431.989).

> **Sửa:** phát biểu cũ "không instance BEFORE hay CONTAINS nào vi phạm" **tự mâu thuẫn** — nếu có 1 pattern
> cấm CONTAINS thì các instance CONTAINS dưới nó vi phạm theo định nghĩa. Đúng là: **BEFORE 0** (cấu trúc,
> chứng minh được — xem C3Rb), **CONTAINS 3**. Ba cái đó nằm dưới pattern L1 `(Coming_to_be, Catastrophe)`,
> n=501, k=3, WilsonUB = 0,01746 < τ = 0,02 — định danh được và kiểm chứng được bởi bên thứ ba.

**Trần phủ 16,41% là trung thực và phải nêu kèm ba nguyên nhân đo được:** (a) 90,88% instance là BEFORE và
family cố tình loại BEFORE; (b) chỉ 20,14% cặp chia sẻ entity; (c) OVERLAP và SIMULTANEOUS chỉ có 2.634 và
3.797 instance toàn corpus.

---

## 6. D. Tầng suy luận

### D1 — Bốn nguồn ràng buộc suy ra

**Chia làm hai lớp. Chúng không so sánh được với nhau.**

**LỚP A — KHÔNG độc lập, chỉ dùng làm bộ lọc yếu.** Cả ba được chú thích **bên trong một phạm vi do chính
nhãn temporal định nghĩa**, nên mọi tỉ lệ đồng thuận là vòng tròn theo cấu trúc.

Tỉ lệ kiểm chứng thực nghiệm (train đầy đủ):

| Nguồn | n có nhãn | Luật NGHIÊM | Luật TRUNG | **Luật YẾU (CHỌN)** |
|---|---|---|---|---|
| CAUSE | 6.168 | ⇒BEFORE **72,18%** (1.716 vi phạm) | ⇒{BEF,CONT} 96,84% (195) | không-đảo-chiều **99,95%** (**3** vi phạm) |
| PRECONDITION | 28.103 | ⇒BEFORE **92,47%** (2.116) | ⇒{BEF,CONT} 98,71% (362) | không-đảo-chiều **99,98%** (7) |
| SUBEVENT | 8.094 | ⇒CONTAINS 98,83% | +BEGINS-ON 99,09% | không-rời-nhau 99,31% (56) |
| TIMEX (BEFORE) | 10.388 | — | — | thứ tự interval 98,58% (147) |
| TIMEX (CONTAINS) | 906 | — | — | 96,91% (28) |
| TIMEX (SIMULTANEOUS) | 644 | — | — | **99,07%** (6) |
| TIMEX (OVERLAP) | 8 | — | — | 50,00% (4) |

Luật nghiêm **bị bác bỏ dứt khoát**: `CAUSE ⇒ BEFORE` chỉ đúng 72,18% và sẽ phát ra 1.716 "lỗi" mà tuyệt đại
đa số là chú thích **đúng** (một nguyên nhân hoàn toàn có thể bao chứa hệ quả của nó về thời gian — đo được
1.521 trường hợp CAUSE+CONTAINS). Đây đúng là chế độ hỏng "30% vi phạm" mà brief cảnh báo.

> **Sửa số:** CAUSE weak rule có **3** vi phạm (99,951%), không phải 4. Cái thứ tư là reverse-OVERLAP, và
> dưới chính ánh xạ của họ thì `inv({o}) = {oi} ⊄ {bi,mi}`, nên nó **không** vi phạm. Họ đếm dòng census thô
> `REV_*` thay vì chạy luật của chính mình. D3 tính đúng (S4 = 10 = 3 + 7), nên D1 và D3 mâu thuẫn nhau.

> **Sửa hướng:** `R_SUBEVENT` viết `rel(a,b) ∩ {d,s,f,e} ≠ ∅` là **ngược**. `subevent_relations` lưu
> `[parent, child]` và nhãn temporal chủ đạo là CONTAINS **thuận chiều** — nên tập đúng là `{di,si,fi,e}`.
> Hôm nay nó vẫn qua được 7.999 ca CONTAINS chỉ nhờ phần tử chung `e`, tức bằng **trùng hợp**. Cả hai cho
> đúng 56 vi phạm hôm nay (tôi đã kiểm chứng), nên lỗi đang bị che — nhưng sau closure, bất kỳ cạnh
> parent-child nào bị thu về `{di}` sẽ cho `{di} ∩ {d,s,f,e} = ∅` và bị phát ra thành lỗi giả.

> **Cảnh báo về sức phân biệt:** 99,95% **không phải** bằng chứng luật yếu được kiểm chứng — nó gần như
> không thể sai. Dưới ánh xạ B1, `R_CAUSE` chỉ bác được khi `MAP[nhãn] ⊆ {bi,mi}`, đúng **2** trong 12 cấu
> hình (nhãn × chiều). Hãy báo cáo nó như nó vốn là: **đếm thô số cặp causal có reverse-BEFORE/reverse-ENDS-ON
> (10 cái)**, không phải "constraint được ủng hộ 99,95%".

**LỚP B — TIMEX normalization, kênh ít tương quan nhất.** Đây là nguồn có sản lượng cao nhất: **185 mâu
thuẫn** trên 88 document, so với 0 từ logic nội-document (sau khi sửa B1). Các ví dụ không cần phán đoán:
`BEFORE('1997', '1994')`, `BEFORE('November 1944', 'October 1944')`, `BEFORE('1 May 2003', '12 April 2003')`.

> **Sửa cách gọi:** đừng gọi nó là "độc lập hoàn toàn / nằm ngoài vòng chú thích". Theo chính Sec 2.2,
> annotator xếp điểm đầu/cuối của **cả TIMEX** lên timeline — nên để đặt TIMEX "1994" họ **phải** đọc chuỗi
> "1994" và hiểu nó là một năm. Đó đúng là phép toán mà normalizer thực hiện. Nó vẫn là nguồn tốt nhất,
> nhưng vì lý do đúng: **nó không chia sẻ chế độ hỏng của con người** (một regex không mất tập trung, không
> trôi dạt timeline qua một document dài). Gọi là "ít tương quan", không phải "độc lập".

**Bảng sổ tổng (train đầy đủ), sau khi sửa B1:**

| Nguồn | Sản lượng | Document |
|---|---|---|
| S1 TIMEX | **185** | 88 |
| S2 path consistency | **0** (đã là 7 dưới ENDS-ON=`{m}` sai) | 0 |
| S3 SUBEVENT | 56 | 41 |
| S4 CAUSAL đảo chiều | 10 | 9 |
| **TỔNG** | **251** | ~137 |

> **Sửa:** "254" và "258" đều sai và cả hai đều xuất hiện trong đề xuất. 185+56+10 = 251; +3 (document) = 254;
> +7 (tam giác) = 258. Đơn vị của S2 bị trộn. Sau khi chốt ENDS-ON=`{b,m}`, **S2 = 0** và tổng là **251**.

### D2 — Bảng hợp thành và độ sâu closure

**Dùng bảng Allen 13×13 đầy đủ với hợp thành tập, chạy PC-2 tới fixpoint theo từng document.**

**Không** dùng bảng 6×6 rút gọn trên nhãn MAVEN: hợp thành nhãn cho ra **tập**, và bảng 6×6 không có ô nào để
chứa `{b,m,o}` — chính là thông tin mà closure sinh ra.

**Không** dùng bảng 21 luật của paper làm engine: nó **không đầy đủ** (không có CONTAINS+BEFORE,
OVERLAP+OVERLAP, OVERLAP+CONTAINS...). Nhưng lưu ý — dưới ánh xạ đã chốt của tôi, cả 21 luật đều **sound**;
lý do loại nó là tính không đầy đủ và không biểu diễn được trạng thái phân ly, **không phải** tính không sound.

**Bảng phải được SINH, không chép tay.** Đây là bài học đã trả giá: bảng chép tay đầu tiên trong dự án có
**18 vi phạm luật nghịch đảo**. Bảng sinh của tôi kiểm chứng: 0 ô thiếu, 0 vi phạm đồng nhất,
0 vi phạm nghịch đảo, 0 bộ ba không kết hợp.

> **Sửa ví dụ:** ô minh hoạ cho bug bảng chép tay bị bịa sai chi tiết. Ô thật `('b','mi')` trong `d2_pc.py`
> chứa `{b,m,o,s,d}` — **đúng**. Ô sai thật là `('m','bi')`: bảng tay có `{bi,d,f,mi,oi}` còn giá trị đúng là
> `{bi,di,mi,oi,si}`. Con số 18 đúng, ví dụ thì sai và còn đảo ngược đâu là lỗi đâu là bản sửa.

**Độ sâu: fixpoint đầy đủ.** Chi phí **đã đo lại**, thay cho ước lượng cũ ~100–200 giây: **59,7 s PC-2 cho
toàn bộ 2.913 document** (62,8 s kể cả parse + build), document chậm nhất **1,12 s ở n=120 node, 5.738 cung**.
Số node: p50 25, p90 52, p99 87, max 129, mean 29,07. Số mũ thực nghiệm theo n: **2,90** (phù hợp lý thuyết
n³). Chặn độ sâu không tiết kiệm gì và sẽ âm thầm bỏ sót ràng buộc.

> **Nhưng chỉ đạt được với hai tối ưu, và một trong hai có điều kiện.** Memoise `comp_sets` theo cặp
> `(mask, mask)` — **đúng đắn vô điều kiện**. Bỏ qua cung còn FULL — **chỉ đúng khi mạng còn nhất quán**:
> kiểm chứng `comp(FULL,x)=FULL` chạy trên 13 quan hệ **cơ sở** (0/26 vi phạm) nhưng miền thật của một ô là
> cả 2¹³ mask, và `comp(FULL, ∅) = ∅`. Xem D3b khiếm khuyết 3. PC-2 giáo khoa chậm hơn ~67× (~100 phút toàn
> corpus), nên một bản port ngây thơ sẽ **có vẻ như** bác bỏ kết luận "fixpoint khả thi".

> **Bảng hợp thành phải được SINH mỗi lần chạy, và assert lúc import.** Lỗi này đã tái phát: một bảng chép
> tay khác trong dự án có **11 ô sai và 18 vi phạm luật nghịch đảo** — đúng chế độ hỏng mà chính mục này đã
> cảnh báo. Bảng sinh bằng brute force kiểm chứng 0 ô rỗng / 0 vi phạm đồng nhất / 0 vi phạm nghịch đảo /
> 0 vi phạm kết hợp. **Mọi con số đã tính bằng một engine dùng bảng chép tay đều phải chạy lại.**

**Sản lượng closure:** +54.636 cung được ràng buộc thêm (+6,9%), trong đó 1.091 chốt về một quan hệ Allen duy nhất.

> **Sửa:** con số "569 nhãn duy nhất" thiên lệch vì chỉ quét tam giác trên `i<j` của một quan hệ **có hướng**.
> Một cặp mà chiều i→j cho `{bi,mi}` không chiếu ra nhãn nào, còn chiều j→i cho `{b,m}` chiếu ra BEFORE —
> nên khoảng một nửa bị mất. Con số đúng là **585 cặp không thứ tự** (BEFORE 548, CONTAINS 36, BEGINS-ON 1).
> Lỗi ở `d2_full.py`, vòng `for j in range(i+1, len(nodes))` chỉ kiểm `M[i][j]`.

> **Trần cấu trúc chưa ai nêu:** ánh xạ nhãn→Allen **không phải antichain** — `MAP[ENDS-ON] ⊂ MAP[BEFORE]`
> và `MAP[SIMULTANEOUS] ⊂ MAP[CONTAINS]`. Nên `project()` với điều kiện `|project(S)| = 1` **không bao giờ**
> phát ra được ENDS-ON hay SIMULTANEOUS. Con số 585 là sàn trên **4 nhãn khả đạt**, không phải 6.
> Hệ quả thứ hai: detector **không bao giờ** gắn cờ được nhầm lẫn BEFORE↔ENDS-ON, vốn có lẽ là nhầm lẫn dễ
> xảy ra nhất giữa hai nhãn gần nghĩa. Muốn bắt được thì cần một **tiên đề loại trừ** riêng (mỗi cặp ordered
> có nhiều nhất một nhãn gold — tôi đã kiểm chứng: 0 vi phạm trên cả train và valid), không thể dựa vào
> giao tập.

**Kết luận đúng: closure là BỘ KIỂM TRA NHẤT QUÁN, không phải BỘ SINH quan hệ.** 585 nhãn mới trên 792.445
là 0,07%. Đừng tiếp thị nó như data augmentation.

**Và phải nói rõ:** path consistency là **sound nhưng không complete** cho Allen đầy đủ. INCONSISTENT là mâu
thuẫn chắc chắn; CONSISTENT chỉ là "không tìm thấy mâu thuẫn". Câu *"chúng tôi chứng minh 2.910 document còn
lại nhất quán về thời gian"* là **SAI** và không được viết.

### D3 — Thứ tự ưu tiên và bảng phán quyết

| Hạng | Nguồn | Lý do (khoảng cách nhân quả tới nhãn đang kiểm) |
|---|---|---|
| **P1** | TIMEX-norm | Ít tương quan nhất; không chia sẻ chế độ hỏng của người |
| **P2** | Allen path consistency | Suy diễn; không thêm thông tin; không thể sai nếu ánh xạ đúng |
| **P3** | SUBEVENT | Có chú thích, phạm vi bị CONTAINS ràng buộc ⇒ thông tin yếu |
| **P4** | CAUSAL | Có chú thích, phạm vi bị BEFORE/OVERLAP ràng buộc ⇒ thông tin yếu |
| **P5** | Mined soft pattern | Thống kê, mức corpus; **không có thẩm quyền** trên một instance |
| **P6** | Gold label | Đối tượng đang kiểm; **không bao giờ thắng** |

Nếu gold xếp trên, detector trả về **tập rỗng theo định nghĩa** và dự án không có kết quả. Đó chính là cái
bẫy đằng sau kết luận "MAVEN-ERE có 0 conflict".

**Hai luật chi phối:**
- **(A)** Soft pattern **không bao giờ được một mình kết tội** một nhãn gold. Mức cao nhất từ P5 đơn độc là
  REVIEW-LOW. Với BEFORE chiếm 86,26% corpus, mọi pattern có ngưỡng confidence sẽ dự đoán BEFORE gần như
  khắp nơi và gắn cờ đúng những nhãn thiểu số **đúng**.
- **(B)** UNKNOWN **không phải** negative. Cặp không nhãn → ABSTAIN, loại khỏi mọi mẫu số.

> **D3b — ĐÃ CÀI, ĐÃ ĐO (2.913 doc, 3.198.212 cặp ordered, 89 s). Ba khiếm khuyết đã sửa, phát hiện thêm
> khiếm khuyết thứ tư và thứ năm.**
>
> **Khiếm khuyết 1 (row 8 chết) — SỬA XONG.** Pha 1 ghi lại **mọi** row khớp (tập `fired`), verdict nền vẫn
> lấy row khớp đầu. Pha 2 là hàm escalation riêng trên `(base, fired, f)`, chỉ được **nâng** mức, trừ E4.
>
> **Khiếm khuyết 2 (row 7 chết) — SỬA XONG, nhưng cần thêm một sửa nữa.** Thu hẹp row 2 thành
> `G=NONE ∧ H2=FULL` là **cần nhưng CHƯA ĐỦ**. Phải định nghĩa `UNLABELLED = G=NONE ∧ GREV=NONE` (không nhãn
> ở **cả hai** chiều). MAVEN chỉ lưu một chiều BEFORE, nên ô ngược của một cung đã gắn nhãn có `G=NONE` và bị
> closure pin về `{bi}` một cách tầm thường. Không sửa: 10.957 OK-DERIVED trên 20 doc, trong đó **9.860 là
> `{bi}`** so với **274 `{b}`** — một bất đối xứng **bất khả** với closure đối xứng, và chính nó lộ ra bug.
> Giữ tỉ lệ bi/b làm **invariant kiểm tra thường trực**.
>
> > **Sửa số:** OK-DERIVED = 7.580 là đếm **ô ordered** và **đếm đôi**. `UNLABELLED` đối xứng theo định nghĩa
> > và `H2=PIN` đối xứng dưới closure đối xứng, nên mọi ô OK-DERIVED có ô gương cũng OK-DERIVED — đo được
> > **100%** phủ gương (2.340/2.340 trên 400 doc). Số **fact phân biệt** là **3.790**, không phải 7.580.
> > Thêm invariant "phủ gương = 100%" bên cạnh invariant bi/b.
>
> **Khiếm khuyết 3 (row 1 đòi giá trị không có) — SỬA XONG, hai giai đoạn.** PC-2 chạy tới fixpoint **không**
> return sớm (ô rỗng ghi vào set, propagation tiếp tục), nên `M` luôn xác định và `H2` tính được kể cả trong
> doc mâu thuẫn. Trích xuất lõi là **giai đoạn riêng**.
>
> **PHẢI dùng QuickXplain, không dùng xoá-một-cạnh-rồi-thử-lại.** Trên cùng tập doc: QuickXplain nhanh hơn
> ~7×, ít lần chạy PC hơn ~11×, đuôi tệ nhất tốt hơn ~8×, **và lõi nhỏ hơn**. Cả hai: 100% phục hồi cung
> được inject, 0 lõi không 1-minimal.
>
> **Row 1 PHẢI gate bằng lõi, KHÔNG phải `H2=EMPTY`.** Đây là phát hiện quan trọng nhất của D3b. Một cung
> inject duy nhất làm rỗng **99,9%** số ô của document (p50 **527** ô không thứ tự). Row 1 như đặc tả cũ cho
> **383.930** CONFLICT-HARD từ 200 injection — precision **0,052%**. Gate bằng lõi đưa về bậc **vài trăm**,
> giảm hơn **500×**, recall vẫn 100%. Thêm row 2 `collateral-of-inconsistency`
> (`DOCBAD ∧ ¬CORE ∧ H1≠CONTRA → ABSTAIN`) làm guard *ex falso*.
>
> > **Sửa số và sửa cả tối ưu hoá.** Con số 67,5% (p50 377) là **hiện vật của bug**, không phải phép đo: tối
> > ưu "bỏ qua cung còn FULL" chỉ được kiểm chứng trên **13 quan hệ cơ sở** (0/26 vi phạm), chưa bao giờ trên
> > mask **rỗng**, mà `comp(FULL, ∅) = ∅` **chứ không phải FULL**. Bỏ qua một cung FULL vì thế **chặn lan
> > truyền của tính rỗng**. Trên gold sạch không ô nào rỗng nên lỗi vô hại (số 59,7 s vẫn đúng); dưới
> > **injection** thì nó cắn. **Đặc tả: tối ưu FULL-skip chỉ đúng đắn khi mạng còn nhất quán; phải tắt hoặc
> > đặc-biệt-hoá mask rỗng trong mọi lần chạy injection.** Memoise `comp_sets` thì đúng đắn vô điều kiện.
>
> **Khiếm khuyết 4 — row 4 (closure-contra) KHÔNG THỂ TỚI ĐƯỢC THEO CẤU TRÚC.** Không phải do dữ liệu, và
> chứng minh được: `M[i][j]` được khởi tạo bằng `M &= MAP(G)` **trước** khi closure chạy, và PC không bao giờ
> **nới rộng** một ô (kiểm chứng: 0/79.234 ô nở ra), nên `M ⊆ MAP(G)` luôn đúng, nên `MAP(G) ∩ M = M`, chỉ
> rỗng khi `M` rỗng — mà `M` rỗng nghĩa là `H2=EMPTY`, row 1/2 bắt trước. Đo trên 300 doc / 129.452 ô có
> nhãn: 129.292 ô `= MAP(G)`, 160 ô tập con thực sự, **0 ô disjoint-non-empty**.
> Muốn row 4 sống phải đổi sang **closure leave-one-arc-out**: xoá cung, đóng, rồi hỏi phần còn lại của
> document có còn cho phép nhãn gold không. Bản sửa bắt ~96,7% relabel được inject, nhưng quét mù mọi cung
> tốn **~9,7 giờ** đơn luồng và bắn **0** trên gold sạch.
> **Khuyến nghị: chỉ chạy row 4 sửa trên các cung đã bị nguồn khác nghi ngờ, không quét toàn bộ.**
>
> **Khiếm khuyết 5 — E1 và E4 cũng chết theo cấu trúc.** Đây là cùng một lớp lỗi với khiếm khuyết 1, tái
> phát **bên trong bản sửa của chính nó**:
> - **E4** test `S=ALLOW ∧ base=REVIEW-LOW`, nhưng `base` là verdict **pha 1** và **không row pha 1 nào phát
>   ra REVIEW-LOW** — chỉ E3 (pha 2) phát ra. Điều kiện **bất khả thoả** trên toàn không gian đặc trưng
>   (brute-force 396.900 vector: E4 bắn **0** lần). Đây là đường **hạ cấp duy nhất** của đặc tả và nó chết
>   câm. **Sửa: E4 phải test verdict HIỆN TẠI (`out == REVIEW-LOW`), và xếp sau E3.**
> - **E1** cần row 3 và row 6 cùng bắn trên một cặp, nhưng row 3 đòi **cả hai** đầu mút là TIMEX còn row 6
>   đòi cặp subevent — và train có **0/9.193** dòng subevent với cả hai đầu mút TIMEX. Miền nguồn rời nhau.
>
> > **Công cụ đo khả đạt phải đổi.** Cột "any-match" gần như vô thông tin vì các row **không loại trừ nhau**
> > và row sau yếu hơn row trước: vị từ của row 11 đúng nghĩa đen là `True`, nên any-match của nó **bắt buộc**
> > bằng tổng số cặp. Ngược lại `first-match = 0` trộn lẫn "vị từ không bao giờ đúng" với "luôn bị row trước
> > che". **Thay bằng kiểm thoả được (satisfiability) trên không gian đặc trưng** — brute-force chạy dưới một
> > giây — và báo mỗi row là *thoả được và quan sát được* / *thoả được nhưng bị che* / *bất khả thoả*.
>
> **Bốn/năm row chết trên gold sạch — đây là KẾT QUẢ, không phải bug:** row 1 và row 2 = 0 (corpus có 0 doc
> mâu thuẫn; chỉ sống dưới injection), row 4 = 0 (**cấu trúc**), row 7 causal-contra = 0 (đúng như D1 cảnh
> báo: luật yếu gần như không thể sai), E1 = 0 (**cấu trúc**), E4 = 0 (**cấu trúc**).
>
> > **Cảnh báo về E3 = 34.316.** Con số này đến từ một **soft source giả lập** `(7i+13j) mod 100 < 30` trên
> > nhãn non-BEFORE — một hàm tất định của **thứ tự index** trong JSON, không mang nội dung ngữ nghĩa nào. Nó
> > đúng bằng 30% của 115.138 ô non-BEFORE. Nó chứng minh **đường ống chạy**, tuyệt đối không phải bằng chứng
> > escalation hữu ích. **Không được trích con số này vào paper**; chứng minh khiếm khuyết 1 đã sửa bằng lập
> > luận thoả được, không bằng số của stub.
>
> **Mẫu số candidate:** 3.198.212 là **cặp ordered trên events + TIMEX**. A4 ghi 1.994.647, là đại lượng
> khác (train+valid, không thứ tự). Trên riêng train tôi đếm 2.144.316 ordered chỉ-event và 1.072.158 không
> thứ tự chỉ-event. **Mọi tỉ lệ "phần trăm candidate" phải nói rõ tập node và tính có thứ tự hay không.**

**Luật báo cáo bắt buộc:** luôn tách sản lượng **theo nguồn**, đừng gộp. Đây là bài học trực tiếp từ thất bại
trình bày của PaTeCon: 715/747 = 95,7% conflict WD50K đến từ MutualExclusion, một predicate **không bao giờ
xem thời gian**. Một tổng số không phân tách đã che giấu điều hệ thống thực sự làm.

---

## 7. E. Đánh giá

### E1 — Chia dữ liệu

**test.jsonl không dùng được.** 857 document, key là `['id','title','tokens','sentences','event_mentions','TIMEX']`
— không có `events` (nên không có coreference cluster, không có `EVENT_` id) và không có key quan hệ nào.
Nó **tệ hơn** "không có nhãn": không có event cluster để gắn quan hệ vào.

**Chốt: 5-fold cross-validation trên train+valid gộp (3.623 doc), chia theo DOCUMENT, mọi candidate sinh
strictly out-of-fold.** Báo cáo split cố định train→valid như kết quả phụ để đối chiếu.

| Giao thức | Constraint | Matched | Candidate | Tỉ lệ vi phạm |
|---|---|---|---|---|
| train→valid cố định | 3.423 | 46.462 | 1.464 | 3,151% |
| **5-fold pooled** | — | 249.554 | **7.755** | **3,108%** |

Tỉ lệ theo từng fold: 3,310 / 2,933 / 3,477 / 2,990 / 2,862% — biên độ 0,6 điểm, rất ổn định.
Cross-validation còn cho **bộ lọc ổn định miễn phí**: 2.334/4.562 (51,2%) constraint xuất hiện ở cả 5 fold,
827 (18,1%) chỉ ở 1 fold.

**Chia theo document là bắt buộc, không phải thẩm mỹ:** nhãn trong một document là read-off tất định từ
**một** timeline toàn cục, nên chia trong document sẽ rò rỉ timeline qua ranh giới fold.

> **Khuyến nghị:** ghi `STABILITY(k/5)` như một **đặc trưng** trên mỗi candidate và **phân tầng** mẫu E2 theo nó.
> Đừng lọc cứng trước pilot — làm vậy sẽ vứt đi đúng dữ liệu cần để biện minh cho bộ lọc.

### E2 — Ground truth cho "lỗi chú thích"

Không có ground truth tiên nghiệm. Phải tạo ra. Mô phỏng chính thiết kế kiểm định chất lượng của MAVEN-ERE
(100 document, chú thích hai lần qua toàn pipeline, báo cáo Cohen's kappa = 67,8%).

**N = 150, phân tầng, HAI judge, chú thích đôi đầy đủ, Cohen's kappa kèm CI, bên thứ ba phân xử bất đồng.**

| N | Wilson CI nửa-độ-rộng @ p=0,5 |
|---|---|
| 50 | ±0,134 |
| 100 | ±0,096 |
| **150** | **±0,079** |
| 200 | ±0,069 |
| 384 | ±0,050 |

Từ 150→200 chỉ mua thêm 0,010 với chi phí +33%. Từ 100→150 mua 0,017 và nâng mọi ô phân tầng trên 30.
Công suất: phát hiện 0,10 vs 0,30 cần N=62/nhánh; 0,10 vs 0,25 cần N=100/nhánh — N=150 đủ cho cả hai.

**Hai judge là bắt buộc**, không phải xa xỉ: chú thích temporal của chính MAVEN-ERE dùng **1 annotator +
1 expert reviser** và vẫn chỉ đạt κ=67,8%. Nhiệm vụ của chúng ta — phán xét một nhãn đã công bố có **sai**
hay không — ít nhất cũng chủ quan bằng. Một judge duy nhất cho ra con số không thể bác bỏ, và reviewer sẽ nói vậy.

**Văn bản có đủ không? CÓ**, và tôi có số đo: khoảng cách câu của candidate có median 1, mean 3,26, p95 = 12;
59,8% trong vòng 2 câu, 77,9% trong vòng 5. Candidate còn **tập trung bất thường ở khoảng cách 0** (36,48%
so với 9,54% của quần thể), tức dễ phán xử hơn mức trung bình. Luật cửa sổ: `[min(s)-2, max(s)+2]`,
nếu trải quá 12 câu thì hiện cả document.

> **Sửa:** `sent(h)` được tính từ **mention đầu tiên** của cluster, nhưng cluster có thể có tới 17 mention.
> Cửa sổ neo vào một mention tuỳ ý có thể **bỏ sót chính mention biện minh cho nhãn** — sẽ đẩy judge về phía
> kỳ vọng BEFORE của hệ thống và thổi phồng outcome A. **Judge phải thấy mọi mention của cả hai cluster.**

> **Sửa nghiêm trọng về phân tầng:** mọi `N_s` được trích (364/59/203/294/544 và 1092/222/139/7/4, đều cộng
> lại thành 1.464) đến từ **split cố định**, nhưng E1 quy định mẫu phải rút từ pool out-of-fold **7.755**.
> Trọng số `N_s/N_total` và số hạng FPC đều sai. **Phải đo lại kích thước tầng trên pool 7.755 trước khi
> chốt phân bổ.** Thêm nữa, thiết kế khai báo hai nhân tố (5 CONF × 4 FOUND) nhưng chỉ chéo chúng bên trong
> L1 — chỉ số `s` trong công thức ước lượng không xác định cho L2/L3/L4.

**Nhớ: ước lượng phải được đánh trọng số.** Ô hiếm bị lấy mẫu vượt mức có chủ ý; ai báo cáo tỉ lệ mẫu thô
như "precision" sẽ sai.

### E3 — Metric

**Precision@k với Wilson CI làm headline. Recall KHÔNG ĐO ĐƯỢC — nói thẳng ra và nói tại sao.**

Ba lý do độc lập: (i) không có gold set lỗi MAVEN — tôi đọc Limitations của cả hai paper, không paper nào nêu
tỉ lệ lỗi; (ii) mẫu số "mọi lỗi thật trong MAVEN" đòi chú thích lại 3.623 document; (iii) **căn bản nhất**,
vắng nhãn là UNKNOWN **có tài liệu**, nên lỗi bỏ sót thậm chí không được định nghĩa tốt.
PaTeCon báo được recall chỉ vì nó có `WD27M_wrong_facts.tsv` — MAVEN không có tương đương.

**Thay recall bằng bộ ba sản lượng:** candidate yield 7.755/249.554 = 3,108%; coverage 249.554/593.477 = 42,05%;
ước lượng khối lượng lỗi = `P̂ × 7.755` kèm CI, **gắn nhãn rõ là ước lượng**, không bao giờ là recall.

> **Sửa phạm vi coverage:** mẫu số loại mọi quan hệ chạm TIMEX. 42,05% là coverage của **cặp EVENT-EVENT**;
> coverage của toàn bộ quan hệ temporal có nhãn chỉ khoảng **24,5%**. Vì E3 đưa coverage ra đúng như phần
> thay thế trung thực cho recall, việc lược bỏ phạm vi này đánh bại chính mục đích đó. Báo cả hai.

**Baseline — và một trong số đó có sức huỷ diệt, phải nhận thẳng:**

| ID | Baseline | Kích thước |
|---|---|---|
| B1 | Ngẫu nhiên trên toàn bộ 109.933 cặp EE có nhãn của valid | — |
| B2/B3 | **Gắn cờ mọi cặp không-BEFORE** | 11.067 = 10,07% |
| B4 | Classifier disagreement (hoặc LLM few-shot surrogate) | — |
| B5 | Pipeline của ta ở conf ∈ [0,5, 0,7) | — |

> **Sửa:** B2 và B3 là **cùng một tập**. B2 không cung cấp thứ hạng nào, nên đánh giá nó ở k chỉ có thể bằng
> cách rút k phần tử từ nó — đúng định nghĩa của B3. Đề xuất tự thừa nhận qua `|B2| = |B3| = 11067`.
> Đếm chúng là hai baseline làm phồng độ phủ baseline một cách giả tạo. Gộp lại, hoặc cho B2 một thứ hạng thật.

**SỰ THẬT KHÓ CHỊU, PHẢI NÊU TRONG PAPER:** cả **3.423/3.423** constraint được khai thác đều dự đoán BEFORE.
Hệ quả là candidate list là tập con **nghiêm ngặt** của tập không-BEFORE: overlap 1.464/1.464 = **100,00%**,
0 cặp được gắn cờ là BEFORE. Khung trung thực **không** phải "chúng tôi phát hiện xung đột thời gian" mà là
**"trong 11.067 cặp không-BEFORE, chúng tôi chọn ra 1.464 (giảm 7,6×) khả năng sai nhất"** — và toàn bộ gánh
nặng dồn vào việc chứng minh lựa chọn đó có precision cao hơn hẳn pool mà nó chọn ra.

**Luật quyết định tiền đăng ký: phương pháp được coi là hoạt động KHI VÀ CHỈ KHI `P@k(ta) − P@k(B3)` dương
có ý nghĩa thống kê.**

### E4 — Kết quả ba chiều

**Dùng {A, A*, P, D} nhưng TUYỆT ĐỐI KHÔNG hỏi judge chọn trực tiếp.** Hỏi "annotator sai hay pattern sai?"
đã tiết lộ rằng có một hệ thống đưa ra dự đoán, và mời gọi sự đồng thuận thụ động.

```
GIAI ĐOẠN 1 (judge, bịt mắt):
  Thấy: cửa sổ câu, hai trigger được tô, hai event type, 6 định nghĩa quan hệ.
  KHÔNG thấy: nhãn gold, nhãn hệ thống kỳ vọng, confidence, support, hay bất kỳ dấu hiệu bị gắn cờ nào.
  Q1 ∈ {6 nhãn} ∪ {NONE} ∪ {MULTIPLE(tập chấp nhận được)}
  Q2 ∈ {cao, trung bình, thấp}

GIAI ĐOẠN 2 (script, không phải judge): suy outcome từ (g = gold, s = hệ thống, j = judge)
```

| Điều kiện | Outcome | Vào tử số P@k? |
|---|---|---|
| `j = s ∧ j ≠ g` | A | Có |
| `j = g` | P | Không |
| `j = NONE` | P | Không |
| `j = MULTIPLE(adm)`, `g ∈ adm`, `s ∈ adm` | D | Không |
| `j = MULTIPLE(adm)`, `g ∈ adm`, `s ∉ adm` | P | Không |
| `j = MULTIPLE(adm)`, `s ∈ adm`, `g ∉ adm` | A | Có |
| `j = MULTIPLE(adm)`, cả hai ∉ adm | A* | Có (báo riêng) |
| `j ∉ {g, s}`, nhãn đơn | A* | Có (báo riêng) |

Tại sao thiết kế này, bằng số đo: **mọi** candidate đều là "kỳ vọng BEFORE, tìm thấy không-BEFORE"
(1.092 CONTAINS + 222 SIMULTANEOUS + 139 OVERLAP + 7 ENDS-ON + 4 BEGINS-ON), và BEFORE là prior corpus ở
89,93%. Judge được cho biết "hệ thống kỳ vọng BEFORE", lại cũng biết BEFORE cực kỳ phổ biến, sẽ nói BEFORE.
Bịt mắt cộng suy diễn cơ học **loại bỏ hoàn toàn kênh này**.

**DECOY LÀ BẮT BUỘC.** Trộn vào, không đánh dấu, các cặp hệ thống **không** gắn cờ. Nếu judge "tìm thấy lỗi"
ở decoy với tỉ lệ tương đương candidate, con số precision đang đo **sự hoài nghi của judge**, không phải chất
lượng hệ thống. Rẻ: 200 item thay vì 150.

> **Sửa thiết kế decoy — ba khiếm khuyết:**
> 1. **Decoy loại 2 (cặp không-BEFORE mà hệ thống không gắn cờ) không dùng được.** Vì mọi constraint đều dự
>    đoán BEFORE, cách duy nhất một cặp không-BEFORE không bị gắn cờ là **không constraint nào khớp** —
>    nên `s` không xác định và **không dòng nào** trong bảng suy diễn bắn được. Script bắt buộc phải
>    "assert bảng là vét cạn và fail loudly" sẽ **abort** trên một nửa số decoy.
>    **Bỏ decoy loại 2**; vai trò của nó (đối chứng hoài nghi khớp nhãn) đã do B3 đảm nhiệm.
> 2. **`LIFT = P@k − DECOY_FLAG_RATE` trừ hai đại lượng khác loại.** P@k đếm {A, A*} và **loại** `j = NONE`;
>    tỉ lệ decoy đếm `j ≠ g` và **bao gồm** `j = NONE`. Cùng một câu trả lời NONE đóng góp 0 bên này và 1
>    bên kia. **Sửa: định nghĩa một vị từ chung** `FLAGGED(i) := (j ≠ g ∧ j ≠ NONE)` dùng cho cả hai.
> 3. **Cần cổng nhất quán tài liệu.** Câu trả lời của judge là phán đoán **theo cặp** về một nhãn chưa bao giờ
>    được sinh theo cặp. Hai endpoint của candidate tham gia nhiều nhãn khác (bậc gộp trung bình 39,2) mà judge
>    không thấy. Đo được: trong 128/1.092 ca CONTAINS, khẳng định `BEFORE(h,t)` **mâu thuẫn** với chú thích
>    khác trong cùng document. **Thêm outcome thứ năm I** (câu trả lời của judge làm document bất khả thoả),
>    kiểm bằng cỗ máy PC của D2.

**Cách đếm:** D nằm ở mẫu số, **không** ở tử số — lựa chọn bảo thủ, đúng tinh thần grade M của PaTeCon.
Báo cả `P_strict@k` (loại A*) để người đọc thấy phần nào phụ thuộc vào "annotator sai nhưng ta cũng sai về
nhãn thay thế".

**Ví dụ outcome-P có thật, đã kiểm chứng tận dữ liệu gốc:** document `1b9d9d5b328d`, event A = "transformed"
(type `Change`), event B = "Fiesta" (type `Social_event`). Gold nói `A CONTAINS B`; pattern kỳ vọng
`A BEFORE B` ở **confidence 1,0000 trên 31 instance train**. Văn bản: *"Frontier Fiesta is a three-day event..."*
/ *"Each year a piece of the campus is transformed into 'Fiesta City.'"* — chú thích của annotator **đúng**,
pattern **sai**, ở confidence tối đa. Đây là bằng chứng cụ thể rằng confidence cao không kéo theo outcome A,
và là lý do không được đoán con số precision trước pilot.

### E5 — Tính vòng tròn

**Nêu thẳng và xếp hạng phát hiện theo mức phơi nhiễm.** Vòng lặp là thật và không thể loại bỏ hoàn toàn:
ta khai thác "event loại A đi trước event loại B" từ nhãn MAVEN rồi dùng nó để cáo buộc một nhãn MAVEN là sai.

| Lớp phát hiện | Phụ thuộc nhãn MAVEN? | Giảm thiểu | Sản lượng đo được | Phán quyết |
|---|---|---|---|---|
| Mâu thuẫn cứng (đa nhãn, chu trình, PC) | **Không** (logic thuần) | không cần | **0** | **MIỄN NHIỄM nhưng RỖNG** |
| Residual transitivity | Từ luật, không phải từ học | M1 | 681/689 là ABSENT | **Không phải lỗi** |
| Vi phạm type-pair | **Có** (học từ nhãn) | M1–M4 | 7.755 | **PHƠI NHIỄM** |

**Bốn biện pháp giảm thiểu, theo độ mạnh giảm dần:**

- **M1 out-of-fold mining** (đã cài, đã đo). Loại bỏ tự-xác-nhận ở mức instance. Không tốn gì: 3,108% pooled
  so với 3,151% split cố định. **Không** loại bỏ vòng tròn mức corpus — mọi fold chung annotator, guideline,
  và cơ chế xếp timeline.
- **M2 constraint stability** (≥4/5 fold). Yếu hơn M1 — một thiên lệch annotator nhất quán thì **theo định
  nghĩa** ổn định qua mọi fold.
- **M3 blinded human adjudication từ văn bản** (E2/E4). Chỗ phá vòng mạnh nhất, vì bằng chứng phân xử —
  văn bản — nằm **thượng nguồn** của chú thích. Giới hạn: judge là người khác áp dụng cùng guideline, và
  chú thích đôi của chính MAVEN-ERE chỉ đạt κ=67,8%.
- **M4 bằng chứng độc lập từ cụm D.** **CÁI BẪY: causal relations KHÔNG THỂ đóng vai này.** Sec 2.3 giới hạn
  chú thích causal vào cặp **đã có nhãn** BEFORE/OVERLAP, nên cạnh causal nằm **hạ nguồn** của cạnh temporal.

**Track miễn nhiễm RỖNG, và phải nói ra.** Sau khi sửa B1 thành ENDS-ON=`{b,m}`: 0 cặp đa nhãn, 0 chu trình,
0 document bất khả thoả theo PC, 681/689 residual là UNKNOWN có tài liệu. Một paper mà phát hiện miễn nhiễm
bằng 0 thì không có nội dung ở track đó — nên giữ track thống kê và **gắn nhãn chính xác trạng thái nhận thức
của nó**.

**Câu bắt buộc cho paper (mẫu, thuộc abstract chứ không chỉ limitations):**

> *Constraint của chúng tôi được khai thác từ chính chú thích mà chúng dùng để kiểm tra. Chúng tôi giảm thiểu
> bằng out-of-fold mining và lọc ổn định qua fold, và giải quyết mọi candidate được báo cáo bằng phán xử
> người có bịt mắt đối chiếu văn bản gốc. Chúng tôi **không** khẳng định một cặp bị gắn cờ nhất thiết là sai;
> chúng tôi khẳng định nó **bất thường về mặt phân bố**, và báo cáo tỉ lệ lỗi đã phân xử trong nhóm đó.
> Chúng tôi cũng đã kiểm tra MAVEN-ERE tìm mâu thuẫn logic độc lập với nhãn và **không tìm thấy cái nào**,
> điều mà chúng tôi quy cho cơ chế chú thích xếp-timeline mô tả ở MAVEN-ERE Section 2.2.*

### E5b — Tiêm xung đột tổng hợp: ĐÃ GỠ CHẶN

**Trạng thái đổi từ BỊ CHẶN sang CHỐT.** Chi tiết giao thức ở tài liệu riêng `INJECTION_SPEC.md`; mục này
ghi **chính xác điều gì đã đổi** và **tuyên bố đánh giá mới** là gì.

**Điều gì KHÔNG đổi.** Sàn mâu thuẫn cứng trong gold vẫn là **0**, và vẫn vì lý do cấu trúc: nhãn là read-off
tất định từ **một** timeline đã sắp xếp, nên chú thích **hiện thực được theo định nghĩa**. Tôi đã xác nhận
lại qua closure Allen đầy đủ với bảng sinh: **0/2.913 document bất khả thoả**. Track "mâu thuẫn cứng trên
gold" vẫn **RỖNG THẬT** và phải tiếp tục được ghi như vậy.

**Điều gì đổi.** Trước đây E5b bị chặn vì **không có ground truth nào để tính recall**: không tồn tại tập lỗi
gold, nên mọi phát biểu recall đều vô nghĩa và E3 buộc phải ghi "recall KHÔNG ĐO ĐƯỢC". Tiêm tổng hợp tạo ra
ground truth đó **bằng xây dựng** — ta biết chính xác cung nào đã bị làm hỏng. Câu hỏi đánh giá vì thế đổi:

| | Khung cũ (bị chặn) | Khung mới (đo được) |
|---|---|---|
| Câu hỏi | "Gold có chứa lỗi logic không?" | "Detector thu hồi được bao nhiêu lỗi **đã tiêm**?" |
| Ground truth | không tồn tại | tập cung bị làm hỏng, biết chính xác |
| Recall | không đo được | **đo được**, kèm trần phát hiện |
| Precision | chỉ qua phán xử người (N=150) | đo được trên gold sạch (FP) **và** phán xử người |
| Trạng thái | **BỊ CHẶN** | **CHỐT** |

**Tuyên bố đánh giá mới — phải viết đúng như sau, không mạnh hơn:**

> *Chúng tôi không tuyên bố tìm ra lỗi chú thích trong MAVEN-ERE; chúng tôi đã kiểm tra và corpus **không
> chứa** mâu thuẫn logic, vì lý do cấu trúc mà chúng tôi nêu rõ. Thay vào đó chúng tôi đo **khả năng thu hồi**
> của phương pháp: tiêm xung đột tổng hợp ở tỉ lệ đã công bố dưới một mô hình hỏng **bảo toàn phân bố biên
> nhãn**, rồi báo cáo precision/recall/F1 đối chiếu ground truth tiêm, **luôn kèm trần phát hiện** và **luôn
> kèm ít nhất ba baseline tầm thường chạy qua cùng census.** Recall báo cáo là **cận trên** của recall thực
> tế, vì chế độ lỗi thật của MAVEN-ERE (trượt timeline) không đồng dạng với toán tử tiêm theo cặp.*

**Ba ràng buộc bắt buộc, tất cả đều do đo mà ra:**

1. **Mô hình hỏng phải là gold-marginal, không phải uniform.** Đây là ràng buộc quan trọng nhất và nó **đảo
   ngược kết luận**. Dưới uniform, một baseline hai dòng (`Brare`: cấm {BEGINS-ON, ENDS-ON}) đạt F1 **0,557**
   và **đè bẹp** family (0,378). Dưới gold-marginal, `Brare` **sụp còn 0,006** còn family đạt **0,245** —
   thắng B3 (0,152) gấp **1,6×** và Brare gấp **39×**. Uniform lấy 5/6 mẫu vào nhãn non-BEFORE vốn chỉ chiếm
   ~1,6% corpus, tức **chế tạo** ưu thế cho mọi quy tắc "gắn cờ nhãn hiếm". Một paper báo số uniform mà không
   báo số gold-marginal đang báo cáo hiện vật của sampler.
2. **Trần phát hiện phải in cạnh mọi con số recall.** Phải tách bạch trần **theo nguyên tắc** (~60,9% dưới
   trọng số toán tử đã khai báo, tính từ khả phát hiện từng toán tử) với **recall đạt được** của một
   extractor cụ thể (~26%). Vòng đo trước gọi con số thứ hai là "trần" — sai, và nó hạ thấp trần thật ~2,3×.
   Thêm nữa, trần phụ thuộc **trọng số delete** (delete là 0% khả phát hiện **theo định nghĩa**): trần đổi
   22%↔30% chỉ do một trọng số do ta tự chọn. **Báo trần như một hàm của mix, không như một đại lượng vô hướng.**
3. **Mine trên corpus ĐÃ HỎNG, không mine trên corpus sạch.** Trong bối cảnh thật không tồn tại bản sạch.
   Vòng đo trước đặt ra luật này rồi **vi phạm chính nó** trong code (mine ở fold sạch rồi mới làm hỏng fold
   held-out); sửa lại làm lift tụt 1,36× → **1,22×**. Chi phí mine trên dữ liệu hỏng đã đo và nhỏ ở tỉ lệ
   khuyến nghị: Jaccard family so với family mine-sạch là **0,9815** ở 0,1%.

**Điều này KHÔNG giải được tính vòng tròn.** Tiêm cho ta recall, không cho ta tính độc lập. Constraint vẫn
khai thác từ chính chú thích mà chúng kiểm tra, nên bảng M1–M4 ở trên vẫn đứng nguyên và M3 (phán xử người
bịt mắt) vẫn là chỗ phá vòng mạnh nhất. Xem `INJECTION_SPEC.md` mục 7 cho phản biện *"bạn chỉ tìm thấy đúng
cái bạn đã trồng"* và câu trả lời trung thực cho nó.

---

## 8. Cái gì chặn cái gì

Thứ tự phụ thuộc. **Không viết dòng code mining nào trước khi bốn mục ở Tầng 0 được chốt.**

```
TẦNG 0 — CHẶN MỌI THỨ (phải chốt trước tiên)
  B1  ánh xạ nhãn → Allen           ⟹ B3, B4, B5, D1, D2, D3, và toàn bộ sản lượng của D và E
  A1  key node (doc_id, node_id)    ⟹ mọi thứ chạm graph; sai là hỏng âm thầm
  A4b ordered canonical pair key    ⟹ mọi tra cứu nhãn; sai là hàm không well-defined
  A4c unknown = UNKNOWN, KHÔNG phải negative  ⟹ mọi mẫu số confidence trong B, C, E

TẦNG 1 — chặn tầng mining
  A2  cluster-level                 ⟹ C1 key, E1 unit  (đã bị dữ liệu ép, không có rủi ro)
  A3  không merge entity            ⟹ trần 20,14% cho mọi motif chia sẻ entity trong C
  B2  MIRROR-ON-INGEST = {SIMUL, BEGINS-ON}  ⟹ C đếm motif; sai là mất 12.197 fact
  C1c L4 = (t1,t2,sdist_abs)        ⟹ ĐÃ CHỐT. torder là trục refinement riêng, không nằm trong key
  A2s share tính trên ENTITY ID     ⟹ L1s/L2/L3; dùng (role,entity) làm L1s sẽ hỏng âm thầm cả C5

TẦNG 2 — chặn tầng chấm điểm
  B4  confidence thoái hoá          ⟹ C3 phải dùng enrichment, không dùng tỉ số
  C3  hàm chấm điểm                 ⟹ C5 family, E3 candidate pool
  C4  leave-one-out forbidden set   ⟹ sản lượng D3 row 1, kích thước pool E2

TẦNG 3 — chặn tầng đánh giá
  C5  đơn vị motif                  ⟹ MỌI con số trong E (E tự ghi rõ: nếu C đổi motif, E phải đo lại)
  D3b tách hai pha bảng quyết định  ⟹ ĐÃ CHỐT; row 1 gate bằng unsat core, không bằng H2=EMPTY
  E2  kích thước tầng trên pool 7.755  ⟹ trọng số ước lượng precision
  INJ mô hình hỏng gold-marginal    ⟹ MỌI con số recall/precision/F1; uniform làm đảo kết luận
```

**Bốn thứ phải sửa trước dòng code đầu tiên:**

1. **ENDS-ON = `{b,m}`, OVERLAP = `{o}`.** Nếu sai chỗ này, D2 phát ra 7 lỗi bịa và toàn bộ phần đóng góp
   "chúng tôi tìm thấy mâu thuẫn logic" là sản phẩm của lựa chọn ánh xạ của chính chúng ta.
2. **Interval không suy biến `x.s < x.e`, phát biểu một lần cho toàn dự án.** B1 viết `≤`, B3 sinh bảng với
   `<`. Hai mục đặc tả trên hai vũ trụ khác nhau và bảng B3 vô hiệu dưới miền mà B1 tuyên bố.
3. **`share` tính trên ENTITY ID, `L4 = (t1,t2,sdist_abs)`.** Hai định nghĩa này đã làm hỏng trọn một vòng
   đo khi bị hiểu sai. Viết chúng vào **một** module định nghĩa và import từ đó.
4. **Bảng Allen phải được SINH và assert lúc import.** Đã có **hai** bảng chép tay hỏng trong dự án (18 vi
   phạm nghịch đảo ở bảng thứ nhất, 11 ô sai + 18 vi phạm ở bảng thứ hai). Đây không còn là rủi ro giả định.

---

## 9. Rủi ro đã biết

Xếp theo mức nghiêm trọng × xác suất.

### R1 — Đóng khung dự án như "phát hiện lỗi chú thích" (NGHIÊM TRỌNG · CHẮC CHẮN XẢY RA nếu không sửa)

**Hỏng cái gì:** không có xung đột logic nào để tìm. Sàn là 0, và nguyên nhân là cấu trúc: nhãn là read-off
tất định từ một timeline đã sắp xếp, nên chú thích **hiện thực được theo định nghĩa**. Một bộ phát hiện xung
đột kiểu PaTeCon chạy trên MAVEN-ERE sẽ trả về tập rỗng — không phải vì constraint kém, mà vì không có gì để tìm.

**Phát hiện sớm:** bạn đã phát hiện rồi — đây chính là kết quả đo. Nếu bất kỳ lần chạy nào báo số khác 0 trên
gold, đó là **bug**, khả năng cao là (a) coi closure residual không nhãn là xung đột (sẽ cho ~1.842 giả),
hoặc (b) quên symmetrize BEGINS-ON (sẽ cho 100 giả). Cả hai đều đúng là con số mà một lần chạy cẩu thả sinh ra.

**Xử lý:** đổi khung thành **"bất thường phân bố + phân xử người + thu hồi lỗi đã tiêm"**. Mọi câu dạng
"chúng tôi phát hiện N lỗi chú thích" phải thành "chúng tôi đưa ra N candidate, trong đó một mẫu 150 được
chú thích đôi có bịt mắt phân xử được P̂ là lỗi annotator (95% CI ...)", cộng với recall đo trên ground truth
tiêm (E5b, `INJECTION_SPEC.md`).

> **Chế độ lỗi thật của MAVEN-ERE là trượt timeline — và mức phát hiện được của nó là một câu hỏi MỞ, không
> phải 0.** Annotator không bao giờ khẳng định một nhãn theo cặp; họ sắp xếp điểm đầu/cuối trên timeline và
> nhãn được suy ra máy móc. Một lần đặt nhầm vị trí vì thế viết lại **nhiều** nhãn cùng lúc.
>
> Vòng đo trước kết luận "PC phát hiện 0/80, nên chế độ lỗi thật không phát hiện được". **Kết luận đó không
> đứng vững:** thí nghiệm đọc lại **mọi** nhãn từ toạ độ đã nhiễu, nên output là read-off của một timeline
> hiện thực được, tức nhất quán **theo cấu trúc** bất kể có tiêm hay không — và control xác nhận đúng thế:
> PC trên bản dựng **chưa trượt** cũng cho 0/80. Một thủ tục trả 0 dù có hay không có corruption thì không
> phân biệt được gì. Bản dựng đó còn phá huỷ **1.718/1.718** nhãn non-BEFORE trước khi trượt.
>
> Mô hình đúng là **trượt cục bộ**: annotator dời một event, nên chỉ các cung **kề event đó** được đọc lại,
> phần còn lại giữ nhãn đã ghi. Đo lại như vậy: PC phát hiện **32,5%–43,8%** qua 5 seed. Vẫn phải nêu rằng
> tiêm theo cặp không đồng dạng với trượt timeline, và recall báo cáo là **cận trên** — nhưng **không** được
> viết rằng chế độ lỗi thật là bất khả phát hiện.
>
> Bổ sung: paper MAVEN-ERE cho phép annotator tạo **sub-timeline**, và event trên hai timeline khác nhau
> được coi là không có quan hệ. Vậy giao diện cho phép **hai** chế độ lỗi, không phải một: đặt sai vị trí
> *trong* một timeline, và gán sai *sub-timeline*. Cái thứ hai chưa được mô hình hoá; hoặc đưa vào bộ toán
> tử, hoặc tuyên bố rõ là ngoài phạm vi.

### R1b — Mô hình hỏng sai làm đảo kết luận (NGHIÊM TRỌNG · ĐÃ XẢY RA BỐN LẦN · dễ tái phát)

**Hỏng cái gì:** một injector không hiện thực, hoặc một null quá yếu, hoặc một mẫu số sai — cả ba đều cùng
một bệnh — có thể lật ngược thứ hạng giữa phương pháp và baseline. Đây không phải rủi ro giả định: nó đã
xảy ra **bốn lần** trong vòng đo vừa rồi, mỗi lần mặc một bộ quần áo khác.

| Biểu hiện | Hậu quả nếu không bắt |
|---|---|
| Injector **uniform** (rút đều 5 nhãn sai) | `Brare` hai dòng code thắng family 0,557 vs 0,378. Gold-marginal đảo lại: 0,006 vs 0,245 |
| Trượt timeline **đọc lại toàn bộ** nhãn | Kết luận "chế độ lỗi thật bất khả phát hiện". Trượt cục bộ cho 32,5–43,8% |
| Toán tử `cycle` trên graph **đóng bắc cầu** | "100% phát hiện" là định nghĩa tuần hoàn — cạnh trực tiếp luôn tồn tại sẵn |
| "FPR" = nhiễu / **toàn bộ parent** | "giảm 47×" trong khi FDP thật chỉ giảm 2,8–5,4×, và chọn sai effect size |

**Phát hiện sớm — ba phép kiểm bắt buộc, rẻ, chạy trước mọi bảng kết quả:**

1. **Control rỗng.** Chạy đúng đường ống với **0 corruption**. Nếu nó cũng trả về cùng con số, phép đo không
   phân biệt được gì. (Đây là phép kiểm bắt được vụ timeline slip, và nó tốn một dòng.)
2. **Baseline tầm thường qua CÙNG census.** Tối thiểu: random, `flag-all-non-BEFORE`, `constant-CONTAINS`,
   và một quy tắc "gắn cờ nhãn hiếm". Nếu một quy tắc hai dòng thắng, phương pháp chưa có đóng góp.
3. **Null khớp biên.** Khi tuyên bố một trục/đặc trưng có ích, đối chứng bằng **nhãn ngẫu nhiên khớp biên
   của chính nó**. Đây là phép kiểm cho thấy "81,7% child rộng hơn cha" và "107 thành viên biến mất" là
   **rỗng nghĩa** — null cho 81,9% và 83–94.

**Xử lý:** mọi con số recall/precision/F1 trong paper phải in kèm (a) mô hình hỏng đã dùng, (b) trần phát
hiện dưới mix toán tử đó, (c) ít nhất ba baseline qua cùng census. Không có ba thứ đó thì con số không được
vào bảng.

### R2 — Vòng tròn (NGHIÊM TRỌNG · CHẮC CHẮN · đã giảm thiểu một phần)

**Hỏng cái gì:** constraint được khai thác từ chính nhãn chúng kiểm tra. Reviewer thấy điều này sẽ bác ngay
nếu paper nói "chúng tôi phát hiện lỗi" chứ không nói "bất thường phân bố".

**Phát hiện sớm:** chạy B3 (baseline non-BEFORE) trong pilot **trước khi viết**. Nếu `P@k(ta)` không thắng
`P@k(B3)` rõ rệt, đặc tả "một cách cầu kỳ để gắn cờ nhãn không-BEFORE" là **đúng** và paper không có đóng góp.

**Còn lại:** M1 chỉ đánh bại tự-xác-nhận mức instance; mọi fold chung annotator và guideline. M3 yếu hơn
oracle SPARQL bên ngoài của PaTeCon vì oracle của ta là **một người đọc khác cùng một văn bản**, không phải
một bản ghi độc lập về thế giới. Điều này xứng đáng một câu trong limitations.

### R3 — Dùng cạnh causal/subevent làm bằng chứng độc lập (NGHIÊM TRỌNG · dễ vô tình phạm phải)

**Hỏng cái gì:** paper nói "quan hệ causal độc lập xác nhận 88% constraint của chúng tôi"; reviewer đọc Sec 2.3
thấy 88% bị **ép bởi phạm vi chú thích** và bác thẳng.

**Bằng chứng:** `ere.txt:404-407` — *"we limit the annotation scope to event pairs with BEFORE and OVERLAP
relations labeled in temporal annotation"*. Annotator **chỉ từng được xem** cặp đã có nhãn BEFORE/OVERLAP.
Rò rỉ đo được: 88,03% PRECONDITION và 65,50% CAUSE là forward-BEFORE; chỉ 9/36.316 cặp causal có reverse-BEFORE.
Subevent còn tệ hơn: `ere.txt:456-458` giới hạn vào cặp đã có nhãn CONTAINS, nên
`SUBEVENT ⇒ CONTAINS = 98,83%` **gần như là hằng đúng**, không phải phát hiện được kiểm chứng.

**Thêm:** causal và subevent chú thích **cùng một stage** (`ere.txt:423-425`), nên P3 và P4 **không phải hai
phiếu độc lập** trên cùng một cặp.

**Xử lý:** trích dẫn `ere.txt:404-407` tường minh và dùng chúng **chỉ** như bộ lọc yếu.

### R4 — Confidence thoái hoá bị bỏ sót (CAO · dễ xảy ra)

**Hỏng cái gì:** paper báo một bảng constraint toàn confidence 1,0 và trình bày như kết quả mạnh. Reviewer
bắt ngay. Tệ hơn: constraint rỗng "mọi cặp ⇒ BEFORE" đạt 0,9104 và **vượt** ngưỡng 0,9 của PaTeCon,
nên hàm chấm điểm không phân biệt được quy luật thật với tỉ lệ nền.

**Phát hiện sớm:** tính tỉ lệ nền trước khi tính bất kỳ confidence nào. Nếu majority class > ngưỡng của bạn,
ngưỡng đó vô nghĩa.

**Xử lý:** lift/PMI hoặc binomial tail + BH-FDR. Nêu rõ trong paper rằng neg = 0 **theo cấu trúc**.

### R5 — Coi cặp không nhãn là negative (CAO · thảm hoạ nếu xảy ra · dễ phát hiện)

**Hỏng cái gì:** 806.711 negative bịa ra (50,45% cặp), mọi confidence sụp về gần 0, không constraint nào sống sót.

**Phát hiện sớm:** nếu không constraint nào vượt ngưỡng, đây là nghi phạm đầu tiên. Kiểm mẫu số:
nó phải là `pos + neg`, **không** phải số cặp được khớp.

### R6 — Quên symmetrize, hoặc symmetrize nhầm (CAO · hỏng âm thầm)

**Hỏng cái gì:** không mirror SIMULTANEOUS/BEGINS-ON → mất 12.197 fact và mỗi motif bị đếm thiếu ~một nửa.
Mirror **nhầm** BEFORE hoặc CONTAINS → mọi confidence có hướng sụp về 0,5 và tín hiệu 1.194 motif lệch bị
phá huỷ. Không dedupe 100 BEGINS-ON hai chiều → đếm đôi.

**Phát hiện sớm:** assert sau khi nạp — `count(SIMULTANEOUS)` phải **đúng gấp đôi** 5.821, `count(BEFORE)` phải
**giữ nguyên** 683.581.

### R7 — Key node id trần (TRUNG BÌNH · vô hình nếu xảy ra)

**Hỏng cái gì:** 456 TIMEX id hợp nhất qua tối đa 35 document trong `eVertexList` phẳng của PaTeCon,
bịa ra constraint xuyên document. **Vô hình trong output và trông giống một phát hiện thật mạnh.**

**Phát hiện sớm:** assert `len(set(node_keys)) == sum(len(doc_nodes))` sau khi dựng graph.

### R8 — Ước lượng precision có trọng số bị báo cáo sai (TRUNG BÌNH · dễ phạm)

**Hỏng cái gì:** phân bổ hybrid lấy mẫu vượt mức ô hiếm có chủ ý. Báo tỉ lệ mẫu thô như precision sẽ sai.
Và trọng số hiện tại tính trên pool 1.464 sai (phải là 7.755).

**Xử lý:** viết công thức trọng số vào paper và cài trong script phân tích, đừng để nó chỉ nằm trong đầu.

### R9 — Chi phí enumeration motif chưa đo (TRUNG BÌNH · MỞ)

Tầng **cặp** là 2,0M và chứng minh được là nhỏ. Nhưng nếu C liệt kê motif **trên** mỗi candidate — cặp quan hệ
có thứ tự, hay bộ ba 3-hop kiểu SP4 — chi phí thật là tích đó, chưa ai đo. Fan-out depth-2 của C2 là 24×23,
không phải 24.

### R10 — Port thừa hưởng hằng số pruning của PaTeCon (THẤP · dễ tránh · dễ bỏ sót)

`relation_prune_threshold = 10 × support_threshold = 1000` đóng băng lúc import. Trên corpus 3.623 document,
nó sẽ prune gần như mọi cặp quan hệ. Và **đừng** bỏ comment dòng 1851-1853 để "sửa" — dòng đó dùng hệ số **5**,
khác hệ số **10** đang sống. Đặt cả ba hằng số **tường minh sau argparse**.

---

## 10. Bước tiếp theo

Thứ tự có chủ đích: mục đầu tiên là **phép đo rẻ nhất mà nếu ra kết quả bất ngờ sẽ thay đổi kế hoạch nhiều nhất**.

### Bước 1 — ĐÃ TRẢ LỜI BẰNG PHÉP ĐO. Không cần pilot 40 item để mở cổng này.

Câu hỏi "family có vượt được baseline tầm thường không" đã được giải bằng **census vét cạn out-of-sample**
trên valid (110 nghìn instance, chưa từng dùng để mine), không phải bằng mẫu.

| Detector | FP sạch (valid) | Recall uniform | Recall gold-marginal | F1 @eps=0,01 uniform | F1 @eps=0,01 **gold-marginal** |
|---|---|---|---|---|---|
| **family τ=0,05** | 0,673% | 0,388 | **0,170** | 0,378 | **0,185** |
| **family τ=0,10** | 1,869% | 0,613 | **0,397** | 0,354 | **0,245** |
| B3 (mọi non-BEFORE) | 10,064% | 0,980 | 0,902 | 0,164 | 0,152 |
| B3' (ngoài {BEFORE,CONTAINS}) | 1,521% | 0,797 | 0,138 | 0,483 | 0,104 |
| Brare ({BEGINS-ON,ENDS-ON}) | 0,036% | 0,400 | 0,003 | **0,557** | **0,006** |

**Phán quyết: đóng góp TỒN TẠI, nhưng chỉ dưới mô hình hỏng hiện thực, và biên độ khiêm tốn.**

- Dưới **uniform** (mô hình giả tạo), `Brare` — hai dòng code, không mining, không Wilson, không lattice —
  **thắng** family 0,557 vs 0,378. Nếu paper báo số uniform, reviewer sẽ dựng `Brare` và bác thẳng.
- Dưới **gold-marginal** (mô hình hiện thực), thứ hạng **đảo hoàn toàn**: `Brare` sụp còn 0,006, B3' còn
  0,104, còn family giữ **0,245** — thắng baseline tốt nhất gấp **1,6×**.
- Lý do đảo: uniform tiêu 5/6 số lần rút vào các nhãn chiếm ~1,6% corpus, tức **tặng không** recall cho mọi
  quy tắc "gắn cờ nhãn hiếm". Đó là hiện vật của sampler, không phải tính chất của detector.

*Cổng đã mở, nhưng kèm hai điều kiện bắt buộc:* (a) mọi bảng kết quả phải in **cả ba** baseline chạy qua
**cùng** census; (b) mô hình hỏng headline phải là gold-marginal, với uniform chỉ là cột đối chiếu.
Pilot người (Bước 7) vẫn cần — nó trả lời câu **khác**: candidate bị gắn cờ có thật sự là lỗi annotator
không. Tiêm chỉ trả lời: detector tìm lại được lỗi đã biết ở tỉ lệ nào.

### Bước 2 — Chốt B1 bằng bằng chứng bên ngoài. Một ngày.

Lấy annotation guidelines từ repo THU-KEG/MAVEN-ERE; nếu không có, email tác giả hỏi định nghĩa chính xác
của ENDS-ON và OVERLAP. Song song, đọc tay ~20 instance ENDS-ON và ~20 instance OVERLAP trong ngữ cảnh.

**Tại sao sớm:** B1 chặn B3, B4, B5, D1, D2, D3 và mọi con số của D và E. Bằng chứng hiện tại (21/21 sound +
0 bad triple + câu một-chiều) ủng hộ mạnh `{b,m}` và `{o}`, nhưng nó là **suy luận, không phải trích dẫn**,
và paper phải ghi rõ như vậy cho tới khi bước này xong.

### Bước 3 — Chốt và đóng băng tầng định nghĩa. Một ngày.

Viết **một** module định nghĩa duy nhất chứa: ánh xạ B1, giả định `x.s < x.e`, key node `(doc_id, node_id)`,
key cặp ordered canonical, tập MIRROR-ON-INGEST, và **một** định nghĩa L4. Sinh bảng Allen bằng brute force
và assert 0 vi phạm đồng nhất / nghịch đảo / kết hợp khi import. Mọi script hạ nguồn import từ đây.

Đây là chỗ sửa ba mâu thuẫn nội bộ: `V_ENT` trong A1 nhưng không trong A4; L4 hai định nghĩa; L2 vừa bị bỏ
vừa được ưu tiên.

### Bước 4 — ĐÃ CHẠY. C4/C5 dưới định nghĩa đã đóng băng.

Family giữ **1.456** (L4 3-tuple là bản đã dùng từ đầu cho C4/C5, nên **không phải sửa gì** ở hai mục đó);
dưới định nghĩa đóng băng đầy đủ kèm B2-dedupe đo lại được 1.392. Forbidden set đã chuyển sang
leave-one-document-out. Dedupe `(key, relation)`: 244 bản sao, 64/67 thành viên L2 là trùng lặp.

**Kết quả đã biết, và nó âm tính:** predictor hằng "luôn CONTAINS" đạt **28,38%** còn SPEC đạt **28,24%** —
phương pháp **không thắng được nó**. Trần ORACLE là 30,19%. Use case (i) rút lại. Xem C5.

Hai việc **còn lại** ở bước này, cả hai đều nhỏ:
- Đo phép sửa SPEC **tối thiểu** (hoán vị chỉ L4 với L1s) thay vì đảo toàn bộ — chưa từng chạy. Vô hại vì
  use case (i) đã rút, nhưng đừng để tài liệu tuyên bố "thứ tự không mã hoá gì" khi chưa đo.
- Chạy BH **trong từng level** thay vì gộp, để số family theo level không còn phụ thuộc lựa chọn key L4.

### Bước 5 — Đo lại kích thước tầng trên pool out-of-fold 7.755. Nửa ngày.

Mọi `N_s` trong E2 hiện lấy từ split cố định 1.464. Phân bổ và trọng số phải tính trên pool thật.

### Bước 6 — Chạy B4 (classifier disagreement) sớm. Hai ngày.

Đây là baseline mà reviewer **chắc chắn sẽ đòi**, và nó có thể **thắng** phương pháp của bạn — nó có văn bản,
còn bạn chỉ có type. Surrogate rẻ: LLM few-shot trên cửa sổ câu.

Nếu nó thắng, paper trung thực đổi khung sang **tính bổ trợ**: đo overlap giữa hai candidate list và báo cáo
phương pháp của bạn tìm được gì mà classifier bỏ sót.

### Bước 7 — Nghiên cứu chú thích đầy đủ. Một tuần.

N=150 + 25 decoy loại 1, hai judge, bịt mắt, pilot 30 item với cổng κ≥0,40, bên thứ ba phân xử.
Công bố guidelines và 150 item đã phân xử như một micro-benchmark công khai — hiện chưa tồn tại tài nguyên
nào như vậy, và đó là ground truth bền vững duy nhất dự án này có thể tạo ra.

### Bước 8 — Mở rộng có điều kiện (chỉ khi Bước 1 và 7 thuận lợi)

- **Anchoring EVENT-TIMEX**: lan truyền ngày TIMEX đã normalize lên event qua CONTAINS/SIMULTANEOUS, rồi so
  hai event đã neo. Đây là mở rộng **sản lượng cao nhất chưa khai thác** của S1 — EVENT-EVENT là 61% quan hệ
  trong khi TIMEX-TIMEX chỉ ~6%.
- **Normalizer mạnh hơn** (HeidelTime/SUTime/LLM). Hiện tại chỉ giải được 53,77% DATE TIMEX, nên 185 là
  **cận dưới**. Cảnh báo: MAVEN không có document creation time, nên ~47% TIMEX tương đối không có neo.

---

## Phụ lục — Điều gì chuyển giao được từ PaTeCon

| Thành phần PaTeCon | Chuyển giao? | Ghi chú |
|---|---|---|
| Tổng hợp trivalent pos/neg/unknown + drop-unknown | **Có** | Unknown ở MAVEN có **tài liệu** (sub-timeline), nên biện minh còn mạnh hơn ở Wikidata |
| Liệt kê all-pairs trong một nhóm có chặn | **Có** | Nhóm là **document**, không phải statement bucket của subject |
| Hình dạng refinement (một pass, top-K, không đệ quy) | **Có** | Nhưng trigger và acceptance thì không |
| Literal nhận key đếm tăng, không bao giờ join | **Có** | Argument content-only của MAVEN **chính là** literal của PaTeCon |
| Kỷ luật ghi (constraint, support, confidence) ra file phẳng | **Có** | — |
| `Interval_Relations.py` (đại số interval) | **KHÔNG** | Chiều tính toán bị đảo: MAVEN **cho sẵn** predicate làm nhãn; PaTeCon phải **suy ra** từ timestamp. Thay bằng lookup + closure. |
| Confidence `pos/(pos+neg)` làm bộ xếp hạng | **KHÔNG** | Thoái hoá trên MAVEN (neg = 0); và null constraint đạt 0,9104 > ngưỡng 0,9 |
| Định danh subject toàn cục (Wikidata QID) | **KHÔNG** | `entity_id` của MAVEN chỉ trong document; guard `len(hasStatement)<2` của PaTeCon sẽ loại gần như mọi thứ |
| Ngưỡng `[0,5, 0,9)` làm trigger refinement | **KHÔNG** | 61,2% pattern L1 đã đơn-quan-hệ ở mức 95% |
| Emission một-predicate qua chuỗi if/elif ưu tiên | **KHÔNG** | Sai cho 38,84% pattern L1 và 82,6% pattern L3 |
| Supersession ngầm qua bộ lọc chung | **KHÔNG** | Không ghi liên kết parent/child; MAVEN có 66,9% đa khớp |
| Mine và detect trên cùng graph (không split) | **KHÔNG** | MAVEN cho đơn vị split tự nhiên (document) gần như miễn phí — đây là chiến thắng uy tín rẻ nhất so với PaTeCon |
| Đánh giá chỉ-recall với gold wrong-fact list | **KHÔNG** | MAVEN không có tương đương. Tình huống **đảo ngược**: recall không đo được, precision thì đo được |
| Test substring `c.__contains__("class")` | **KHÔNG** | Event type của MAVEN là từ tiếng Anh — đây là hiểm hoạ sống, không phải lý thuyết |
| Hằng số pruning đóng băng lúc import | **KHÔNG** | Đặt cả ba tường minh sau argparse; đừng bỏ comment dòng 1851-1853 (hệ số 5 ≠ 10) |

---

## 11. Kết quả sau khi chốt định nghĩa (bổ sung 2026-09-20 tối)

> Các định nghĩa ở mục 0–10 **vẫn đúng**. Mục này ghi những gì đo được sau đó, và ba chỗ
> phải sửa. Chi tiết: `STATUS.md`, `ARCHITECTURE.md`, `MINIMISE.md`.

### 11.1. Multi-view mining — trục mới, không có trong mục C

Mine **độc lập trong từng lớp chữ ký** của 8 view, base rate tính **cục bộ**.

| View | Rule | Phủ | Precision | Oracle |
|---|---:|---:|---:|---:|
| global | 11.894 | 99,9% | 8,38% | 9,81% |
| etype_a | 49.358 | 95,3% | **9,12%** | **10,35%** |
| bucket_a | 16.349 | 99,7% | 8,80% | 10,06% |
| anchor_sd | 17.749 | 99,8% | 7,86% | 8,86% |
| **HỢP NHẤT** | **155.467** | **100%** | **10,68%** | **12,45%** |

Khác biệt với dàn view ở mục C1: **conjunction thêm điều kiện vào rule; view đổi quần thể mà
thống kê được tính trên đó**. BEFORE là 91% toàn corpus nhưng 79,1% trong view cùng câu.

View càng tinh vi thì **đứng riêng càng kém**; chỉ hợp nhất mới ăn thua. Oracle tăng
9,11% → 12,45% chứng tỏ các view bổ sung thông tin thật.

### 11.2. SỬA C5 — subsumption phá tín hiệu, abstraction giữ

| Tập rule | Rule | Phủ | Precision |
|---|---:|---:|---:|
| tất cả | 155.467 | 100% | **10,68%** |
| sau subsumption | 129.987 | 100% | 8,55% |
| **956 họ trừu tượng** | **956** | 93,8% | **8,76%** |
| general + specific | 124.037 | 100% | 8,55% |

**Subsumption mất 2,13 điểm.** Giả định "rule dài bị rule ngắn bao hàm thì thừa" **sai** —
rule dài hẹp hơn nên chính xác hơn trên vùng nó phủ. Tiêu chí đúng là `cov(P) == cov(Q)`
(ngữ nghĩa), không phải `P ⊆ Q` (cú pháp).

**Abstraction thì giữ:** 956 họ đạt 8,76%, cao hơn 129.987 rule nó thay, với 136× ít rule hơn.
Thêm 123.275 rule type-specific vào **không cải thiện gì** — chúng là nhiễu.

### 11.3. Xếp hạng — Wilson LB, không dùng lift

| Luật chọn khi nhiều rule cùng khớp | Accuracy trên valid |
|---|---:|
| lift | 2,76% |
| most specific + lift | 2,76% |
| highest support | 2,61% |
| **Wilson LB** | **7,96%** |
| most specific + Wilson | 7,93% |
| *oracle* | *9,11%* |

Gấp **2,9×**. Lift thưởng rule `n=5/287` lift 39,5× — nhiễu thuần. Thêm "most specific" làm
**tệ đi**, nên Wilson LB một mình là đủ.

### 11.4. Artifact thứ tư — mất chữ ký view

Bổ sung vào danh sách rò rỉ ở mục 2:

| Biểu hiện | Nguyên nhân |
|---|---|
| precision **70,52%** | `dedupe` vứt chữ ký `(view, sig)`, nên rule mine trong view `sdist=0` được áp cho cặp cách 8 câu. Cộng với `lift_min=1.5`, **60 rule dự đoán BEFORE** lọt qua từ 2 view có base rate cục bộ thấp (etype_a 14, bucket_a 46). 70,52% chính là **hằng-BEFORE đội lốt** |

Đã sửa: chữ ký là **phần định danh của rule** xuyên suốt 4 giai đoạn, và rule dự đoán quan hệ
đa số bị từ chối tường minh qua hằng `MAJORITY`.

### 11.5. Constraint — sweep đầy đủ, chốt τ

| τ | Constraint | Vi phạm train | Vi phạm valid | Chọn lọc hơn baseline |
|---|---:|---:|---:|---:|
| **0,001** | 1.730 | **0,054%** | **0,035%** | **~290×** |
| 0,005 | 7.575 | 0,437% | 0,407% | ~25× |
| 0,01 | 9.746 | 1,314% | 1,352% | ~7× |
| 0,02 | 11.758 | 1,594% | 1,737% | ~6× |
| 0,05 | 14.034 | 2,915% | 3,352% | 3,0× |

Train ≈ valid ở cả năm mức — **không overfit**. Xác nhận C3R nhưng ở τ chặt hơn nhiều: C3R
dùng τ=0,05 cho FP 0,673%, còn τ=0,001 cho 0,035%.

Lý do chốt τ=0,001: ở τ=0,05 constraint bị vi phạm nhiều nhất cấm SIMULTANEOUS dù quan hệ đó
có **1.370 lần** trong train — **lỗi rule**, không phải lỗi annotator.

### 11.6. Baseline PaTeCon — đã chạy, đã đo

| | PaTeCon trên MAVEN | Của mình |
|---|---:|---:|
| Constraint | 348 | 1.730 (τ=0,001) |
| **Độ phủ** | **0,0374%** (181/483.504) | 100% (rule family) |
| Precision (annotator sai) | **≈ 0** | chưa chấm tay |

Trong 256 cặp bị gọi là conflict, **171/181 cặp có nhãn gold là BEFORE bình thường**. Ba
nguyên nhân: `include` chiếm 91,2% conflict (vị từ không nhìn thời gian sâu), timestamp là
**khoảng cả năm** (`201301–201312`), và đơn vị `(entity, relation, entity)` không tồn tại ở MAVEN.

Đây là bằng chứng thực nghiệm cho toàn bộ cột "KHÔNG" trong phụ lục.

### 11.7. Per-document là đúng ngữ nghĩa, không phải hạn chế

| | Số đo |
|---|---|
| `entity_id` dùng lại ở >1 doc | **0 / 55.421** |
| `EVENT_id` dùng lại ở >1 doc | **0 / 67.984** |
| Quan hệ temporal có endpoint ngoài doc | **0 / 792.445** |

Dòng thứ ba mới là lý do quyết định: **không có cạnh nào nối hai document**, nên đồ thị toàn
cục chỉ là 2.913 thành phần rời rạc. Gộp lại không thêm thông tin, mà làm PC-2 bất khả thi
(68k node thay vì median 21).

Mất mát thật: cùng một thực thể ở hai doc là hai node khác nhau, nên không mine được pattern
kiểu "sự kiện của cùng một tổ chức thường...". Lấp được bằng entity linking xuyên doc, nhưng
MAVEN không cho dữ liệu để kiểm chứng.

### 11.8. Chi phí và tối ưu — GPU không giúp

| Pha | Chi phí | GPU? |
|---|---|---|
| Mine 8 view | ~90 phút | **Không** — vòng lặp có điều kiện trên frozenset |
| Dựng bitset | ~10 phút | **Không** — pointer chasing |
| Greedy CELF | ~vài phút | **Không** — đã submodular |
| Constraint | ~5 phút | **Không** — chỉ đếm và so ngưỡng |

Tối ưu thật sự: **index theo điều kiện hiếm nhất** thay vì điều kiện đầu. Điều kiện đầu
thường là thứ 98% instance đều có (`EQ(multi_mention_b=False)`), nên index không lọc gì.
Đo trên 4.000 instance: **7,20 s → 1,90 s, nhanh 3,8×**, kết quả giống hệt.

Bignum Python cho AND + popcount **6,8 µs** trên 110k bit — đủ nhanh, không cần GPU.

---

## 12. Đối chiếu `feedback.md` — proof bằng `proof_feedback.py`

> `report/feedback.md` đề xuất đổi khung nghiên cứu. Lập luận kiến trúc của nó đáng lấy,
> nhưng **4/5 con số kiểm được đều sai** vì lấy từ README dataset chứ không phải từ file.
> Chạy lại: `python tempekg_kg/proof_feedback.py`.

### 12.1. Bốn con số bị bác

| # | Claim | Thực tế đo | Nguyên nhân |
|---|---|---|---|
| 1 | MAVEN-Arg có **612** argument role | **143** (train+valid+test) | 612 là kích thước *schema*; dữ liệu phát hành chỉ instantiate 143 |
| 2 | MAVEN-ERE có **162** event type | **168** (ERE train) | — |
| 3 | BEFORE 1.042.709 / 1.216.217 = 85,7% | **843.808 / 981.373 = 85,98%** | Con số của họ gồm cả test, mà bản phát hành ta có **không chứa quan hệ nào** ở test |
| 4 | Motif ví dụ có support **25** (BEFORE 24, CONTAINS 1) | **support 16, toàn BEFORE** | Script cũ đọc event type từ **MAVEN-Arg**; KG này đọc từ **MAVEN-ERE** |

Claim 4 không phải lỗi của feedback mà là số cũ đã lỗi thời. Nguyên nhân đo được ở claim 5.

### 12.2. Claim được xác nhận

**7,15% event mang type khác nhau giữa hai dataset** — 4.602/64.335 event đã align. Đây là
lý do motif đổi từ support 25 xuống 16: 14/25 occurrence có Arg ghi `Motion` còn ERE ghi
`Self_motion`.

Quyết định mô hình: **key pattern đọc type từ ERE**, vì nhãn temporal đang audit là của ERE.
Type của Arg lưu làm `arg_type` để bất đồng không bị giấu.

### 12.3. Phát hiện mới — C3 phải tách hai

Feedback đề xuất tách audit thành wrong-edge và missing-edge. **Đo được là đúng**, và lý do
mạnh hơn feedback nêu:

| | |
|---|---:|
| Cặp event khả dĩ (không thứ tự) | 1.072.158 |
| Có nhãn → ứng viên **C3-A** | 483.504 |
| **Không nhãn → ứng viên C3-B** | **588.654 (54,9%)** |

C3-A có mẫu số xác định. C3-B thì **mọi cặp không nhãn đều là ứng viên** trước khi lọc, nên
nó cần một hàng rào mà C3-A không cần. Gộp hai bài toán làm một là sai về phương pháp.

### 12.4. Thang closure cho C3-B — **4,9%**, không phải 80,4%

> Đo bằng `tempekg_kg/proof_ceiling.py`, 200 document, 948 cạnh bị xoá.
> Xoá một cạnh temporal, hỏi suy luận logic có ép lại đúng nhãn không.

**Con số 80,4% trong các bản trước là sai** — không sai ở phép đo mà sai ở *câu hỏi*. Nó dùng
phép kiểm **bao hàm** `implied ⊆ allen(gold)`: "mọi khả năng còn lại đều thoả gold". Phép đó
không đòi closure chỉ ra được *một* nhãn.

| Phép kiểm | Câu hỏi | Kết quả |
|---|---|---:|
| `allen(gold) ∩ implied = ∅` | có mâu thuẫn không | 0 / 164.803 |
| `implied ⊆ allen(gold)` | có bị ràng buộc đủ không | 81,2% |
| **`len(compat(implied)) = 1`** | **có đoán ra được một nhãn không** | **4,9%** |

Phân rã 81,2% cho thấy nó rỗng:

| | Case | Tỉ lệ |
|---|---:|---:|
| bao hàm thành công | 770 | 81,2% |
| — trong đó **thực sự quyết định được** | 46 | **4,9%** |
| — trong đó vẫn còn mơ hồ | 724 | 76,4% |

Và 724 case mơ hồ ấy gần như chỉ là **một** case lặp lại:

| Gold | Nhãn còn tương thích | Case |
|---|---|---:|
| BEFORE | BEFORE, ENDS-ON | **701** |
| SIMULTANEOUS | BEGINS-ON, SIMULTANEOUS | 21 |
| BEGINS-ON | BEGINS-ON, SIMULTANEOUS | 2 |

**97% độ lạm phát đến từ đúng một chỗ: BEFORE vs ENDS-ON.** Ánh xạ MAVEN→Allen chỉ chồng lấn
ở hai ký hiệu — `b` (BEFORE ⊂ ENDS-ON) và `e` (SIMULTANEOUS ⊂ BEGINS-ON) — và hầu hết lạm phát
nằm ở cái thứ nhất. Khi closure thu về `{b}`, nó đã loại CONTAINS/OVERLAP/SIMULTANEOUS, nhưng
**không tách được BEFORE khỏi ENDS-ON**. Với base rate BEFORE 89,94%, "đoán BEFORE" có sẵn
gần như miễn phí; phép bao hàm chỉ đang đo lại điều đó.

| Phương pháp | Khôi phục đúng | Mẫu |
|---|---:|---:|
| 1-step closure | 46 = **4,9%** | 948 |
| 2-step closure | 46 = **4,9%** | 948 |
| PC-2 tới fixpoint | 40 = **5,0%** | 808 |

**Closure sâu hơn không thêm gì** — PC-2 khôi phục đúng **0 cạnh** mà 1-step bỏ sót. So trên
cùng population (808 case PC-2 chạy được).

Điều này **thay đổi câu chuyện của C3-B theo hướng tốt hơn cho ta**. Trước đây closure ăn mất
80,4% và rule chỉ còn 19,6% residual để chứng minh giá trị. Thực tế:

> Closure thuần tuý chỉ khôi phục **4,9%** cạnh bị xoá. **95,1% còn lại** là population mà
> bằng chứng ngữ nghĩa — vai, entity chung, vị trí diễn ngôn — là nguồn thông tin duy nhất.

Con số 1,8% mà `detect.py` báo trên 56 cạnh xoá thật là **cùng phép kiểm này**, khác biệt chỉ
do cỡ mẫu và population PC-2. Hai con số nhất quán.

**Không gọi 4,9% là "trần logic"** — đó là trần của closure dưới protocol xoá cạnh hiện tại,
không phải cận trên toán học. Tên gọi residual: *closure-undetermined under the 1-step protocol*.

Vẫn phải báo cả hai:

$$R_\text{all} = \frac{\text{khôi phục được}}{\text{tổng cạnh xoá}}, \qquad R_\text{beyond} = \frac{\text{khôi phục trên residual}}{\text{residual}}$$

### 12.5. Chỗ KHÔNG lấy từ feedback

| Đề xuất | Lý do từ chối |
|---|---|
| Đổi C2 thành "relation inference" | Đổi tên, không đổi bản chất — vẫn là rule → nhãn, vẫn bị trần oracle 12,45% chặn. Trung thực hơn là **nêu thẳng trần oracle như phát hiện về dataset** |
| Tách "C4 — Allen consistency" thành contribution riêng | Đo được **0/2.913 document bất khả thoả** trên gold. Allen layer là công cụ verify mapping rất tốt (21/21 luật paper sound) nhưng **chưa bắt được lỗi nào**. Để trong C1 làm phần kiến trúc |

### 12.6. Ba tầng thuật ngữ — lấy

Hiện tài liệu dùng "rule" cho cả bốn khái niệm, gây rối khi viết bài. Chốt:

| Tầng | Định nghĩa | Ví dụ |
|---|---|---|
| **Motif** | cấu trúc đồ thị thuần | `A --role--> X <--role-- B` |
| **Pattern** | motif + thuộc tính | `+ A.type=Motion, B.type=Process_end` |
| **Rule** | pattern + ngữ nghĩa thống kê | `→ allowed={BEFORE}, n=16, wlb=...` |
| **Constraint** | rule ở dạng phủ định | `→ forbidden={CONTAINS, OVERLAP, ...}` |
| **Audit finding** | constraint áp lên KG bị vi phạm | `(a,b) observed=CONTAINS, forbidden` |
