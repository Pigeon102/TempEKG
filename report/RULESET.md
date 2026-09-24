# Bộ luật TempEKG: luật là gì, dựng ra sao, trông thế nào

*Cập nhật 24/09/2026. Mọi luật và ví dụ trong tài liệu này lấy từ bộ luật và document thật; số liệu
đo trên valid MAVEN-ERE (710 document), valid chỉ mở một lần cho mỗi bộ luật.*

Pipeline dùng năm bộ luật, mỗi bộ cho một bước:

| Bước | Bộ luật | Số luật | Đoán gì | Kết quả trên valid |
|---|---|---|---|---|
| 2.1 | Luật EV–EV mine trên toàn bộ train | 54.719 sau xác nhận, 2.794 được bật; **rút gọn có chứng minh còn 378** (mục 12) | nhãn của cặp sự kiện | macro-F1 EV–EV **26,99%** |
| 2.1 | Luật EV→TIMEX / TIMEX→EV / TIMEX–TIMEX | 1.412 / 1.710 / 416 | nhãn của cạnh có TIMEX | 29,74% / 24,29% / 32,98% |
| 2.2 | Pattern từng tầng → luật liên tầng | pattern / luật: EV–EV 1.673 / 6.184 · EV→TX 245 / 715 · TX→EV 248 / 627 · TX–TX 98 / 450 | ghi đè nhãn 2.1 khi đủ chắc | gộp 4 loại cạnh 30,09% → **30,84%** |
| 3.1 | Auditor Bài 2 theo (loại cạnh, nhãn hiện tại), có tầng GRAPH | mine lại trong từng fold cross-fit | cạnh nào sai, đúng ra là gì | lỗi 15,31% → 12,80% |
| 3.2 | Tần suất cấu hình tam giác (không phải luật dạng if-then) | 6,31 triệu tam giác gold | độ hợp lý của cả tam giác | lỗi → **11,62%** (sau 3.1) |

Bộ 257 luật cũ (25,60%) chỉ được chọn trên 400 document train đầu; nó được thay bằng bộ ở dòng
đầu. Lịch sử ở mục 10.

---

## 1. Một luật trông thế nào

Bản ghi thật trong `experiments/rules_full/rules_confirmed.pkl` (xuất ra `src/artifacts/rules_full.json`).
Đây là luật có `wlb` cao nhất trong 54.719 luật; nó **không** nằm trong bộ 378 (mục 4, mục 12) nhưng
minh hoạ đủ mọi trường của một luật:

```json
{"view": "bucket_a", "sig": "lead",
 "conds": [["EQ", "type_a", "Hostile_encounter"], ["EQ", "nrole_a", 0]],
 "rel": "CONTAINS",
 "k": 239, "n": 254,
 "ck": 37,  "cn": 37,
 "wlb": 0.906, "base": 0.326}
```

Đọc là: *trong lớp các cặp mà sự kiện A nằm ở đoạn mở đầu văn bản (`bucket_a = lead`), nếu A là một
cuộc giao tranh (`Hostile_encounter`) và A không có tham số nào, thì A CONTAINS B.* Trên DISCOVERY
luật bắn 254 lần, đúng 239; trên CONFIRMATION-1 (nhãn chưa từng dùng để chọn luật) bắn 37, đúng 37.
Trong ngữ cảnh: câu đầu bài Wikipedia về một trận đánh thường nhắc tên trận (“The Battle of X was
…”), và trận đánh đó bao trùm mọi sự kiện kể sau.

| Trường | Nghĩa |
|---|---|
| `view`, `sig` | luật chỉ áp trong **một lớp** của một view (ở đây: lớp `lead` của view `bucket_a`) |
| `conds` | 1 hoặc 2 điều kiện nguyên tử, nối bằng AND |
| `rel` | nhãn luật dự đoán |
| `k` / `n` | số lần đúng / số lần bắn trên DISCOVERY (nơi luật được đề xuất) |
| `ck` / `cn` | số lần đúng / số lần bắn trên CONFIRMATION-1 |
| `wlb` | cận dưới Wilson 95% của `ck/cn`, tức độ tin cậy **đo trên nhãn độc lập**; combiner dùng số này |
| `base` | tỷ lệ nền của nhãn `rel` trong lớp đó (trên DISCOVERY) |

## 2. Nguyên liệu: điều kiện nguyên tử

Với mỗi cặp sự kiện, `pair_features` tính mọi đặc trưng **không đọc nhãn của chính cặp đó**, rồi
mỗi đặc trưng sinh các điều kiện nguyên tử (trung bình 40,9 điều kiện mỗi cặp). Sáu dạng, kèm số lần
xuất hiện trong 54.719 luật:

| Dạng | Nghĩa | Ví dụ thật | Số lần |
|---|---|---|---|
| EQ | thuộc tính bằng đúng giá trị | `EQ(type_b, Bodily_harm)` | 37.616 |
| HAS | tập chứa giá trị | `HAS(roleset_a, Cause)` | 35.715 |
| CNT | tập có đúng k phần tử | `CNT(anchor_roles, 3)` | 11.023 |
| REL | so sánh giữa hai sự kiện | `REL(a_before_b, False)` | 10.454 |
| MIX | tập có ít nhất 2 loại phần tử | — | 4.590 |
| ALL | tập chỉ gồm đúng giá trị đó | `ALL(etypeset_a, Person)` | 3.416 |

Thuộc tính dùng nhiều nhất: `anchor_roles` (vai của entity mà hai sự kiện cùng chia sẻ, 13.378),
`roleset_b` 8.882, `roleset_a` 8.661, `roleset_shared` 7.513, `type_b` 7.446, `etypeset_shared`
6.873, `type_a` 5.475, `type_pair` 4.974. Tức là luật chủ yếu nói về **loại sự kiện** và **ai tham
gia vào cả hai sự kiện**.

## 3. Luật được dựng thế nào (bước 2.1, EV–EV)

```
cặp sự kiện train (483.504)            chia theo hash document
   │                                  DISCOVERY 292.719 · CONF-1 95.352 · CONF-2 95.433 cặp
   ▼
điều kiện nguyên tử + chữ ký 8 view    mã hoá một lần, lưu cache
   ▼
vét cạn độ sâu ≤ 2 trong mọi lớp       40 đơn vị (view × nhãn không phải BEFORE), 4 tiến trình
của 8 view, trên DISCOVERY             đếm support bằng bitset: n = popcount(mask_a & mask_b)
   ▼
4 cổng thống kê                        106.242 ứng viên
   ▼
BH-FDR q < 0,05                        92.773 ứng viên
   ▼
xác nhận trên CONF-1                   54.719 luật
   ▼
chọn combiner trên CONF-2              ngưỡng precision theo nhãn → 2.794 luật được bật
   ▼
valid mở một lần                       macro-F1 26,99%, accuracy 87,90%
```

Tổng thời gian khoảng 6 phút với 4 tiến trình (mine 74 giây; phần còn lại là bắn luật trên CONF-2 và
valid để chọn combiner).

### 3.1 View: mine trong từng lớp, chấm theo tỷ lệ nền của lớp

Một view chia các cặp thành lớp; luật được mine và chấm **bên trong một lớp**, so với tỷ lệ nền của
chính lớp đó. Trong lớp các cặp cùng câu BEFORE chỉ còn 79,1% (toàn train 91,0%) và SIMULTANEOUS tăng từ 0,86% lên 5,4%,
nên tín hiệu cho nhãn hiếm lộ ra mà ở mức toàn cục bị BEFORE che mất.

| View | Lớp theo | Số luật |
|---|---|---|
| `global` | một lớp duy nhất | 6.139 |
| `sdist` | khoảng cách câu (0, 1, 2, 3+…) | 8.928 |
| `order` | thứ tự trong văn bản (`fwd`, `rev`, `same`) | 6.697 |
| `anchor` | hai sự kiện có chung entity hay không | 4.067 |
| `bucket_a` | vị trí câu của A (`lead`, `early`, `mid`, `late`) | 8.816 |
| `etype_a` | loại sự kiện của A | 6.011 |
| `sdist_ord` | khoảng cách câu × thứ tự | 8.585 |
| `anchor_sd` | có chung entity × khoảng cách câu | 5.476 |

### 3.2 Vét cạn độ sâu ≤ 2 bằng bitset

Trong mỗi lớp, mỗi điều kiện nguyên tử được lưu thành một số nguyên Python mà bit thứ i bật khi cặp
thứ i thoả điều kiện. Support của luật hai điều kiện là `popcount(mask_a & mask_b)`, số đúng là
`popcount(mask_a & mask_b & mask_nhãn)`. Nhờ vậy duyệt **mọi** cặp điều kiện trong mọi lớp, không cần
beam search như bộ cũ.

### 3.3 Bốn cổng trên DISCOVERY, rồi BH-FDR

| Cổng | Điều kiện | Chống lại |
|---|---|---|
| 1 | `n ≥ 25`, `k ≥ 8` | luật dựa trên quá ít mẫu |
| 2 | `k/n ≥ 1,5 × base` (lift cục bộ trong lớp) | luật không nói gì hơn tỷ lệ nền |
| 3 | các lần bắn đúng nằm ở ≥ 5 document | luật chỉ đúng trong vài bài (luật từ 2–3 document rớt 19,2 điểm precision khi sang valid) |
| 4 | Δlogit ≥ 0,5 so với điều kiện cha tốt nhất (với luật 2 điều kiện) | điều kiện thứ hai thừa |
| BH | Benjamini–Hochberg q < 0,05 trên toàn bộ ứng viên | luật đẹp do may khi thử hàng trăm nghìn giả thuyết |

**Sai khác so với thiết kế gốc:** bước BH dùng kiểm định nhị thức một phía so với tỷ lệ nền của lớp,
không dùng 200 hoán vị theo khối document (quá chậm trên 480 nghìn cặp). Cổng ≥ 5 document bù lại một
phần cho việc các cặp trong cùng document không độc lập.

### 3.4 Xác nhận trên CONFIRMATION-1

Mỗi ứng viên được đếm lại trên CONF-1: giữ nếu `cn ≥ 10` và `wlb(ck, cn) > base`. Còn 54.719 luật:
CONTAINS 29.049, SIMULTANEOUS 20.538, OVERLAP 4.583, BEGINS-ON 523, ENDS-ON 26. 6.624 luật một điều
kiện, 48.095 luật hai điều kiện.

### 3.5 Combiner: ngưỡng precision theo nhãn, chọn trên CONFIRMATION-2

Trung bình **147 luật bắn trên một cặp**. Luật chỉ được bỏ phiếu cho nhãn của nó khi `wlb` vượt ngưỡng
của nhãn đó; cặp nhận nhãn của luật có `wlb` cao nhất; không luật nào đủ ngưỡng thì BEFORE.

| Nhãn | Ngưỡng | Luật được bật |
|---|---|---|
| CONTAINS | 0,5 | 2.109 |
| SIMULTANEOUS | 0,15 | 278 |
| OVERLAP | 0,1 | 407 |
| BEGINS-ON, ENDS-ON | tắt | 0 |

Ngưỡng chọn bằng coordinate ascent trên macro-F1 của CONF-2 (26,36%), thắng combiner `max-norm` cũ
(25,88%). `max-norm` chia `wlb` cho prior của nhãn, nên với 54 nghìn luật, một luật BEGINS-ON có `wlb`
0,01 đã được 23 điểm (prior 0,044%) và lấn hết nhãn khác.

### 3.6 Ablation: tách 60/20/20 hay dùng toàn bộ train (K-fold)

| Cách (luật EV–EV, cùng valid giấu nhãn) | Tìm luật | Chấm độ tin cậy | Chọn ngưỡng | Luật hoạt động | Valid macro-F1 | Accuracy | SIMU P / R |
|---|---|---|---|---|---|---|---|
| **A (pipeline chính)** | DISCOVERY 60% | CONF-1 20% | CONF-2 20% | 2.794 | **26,99%** | **87,90%** | 17,2 / 15,1 |
| A, cách chia train khác (seed 1) | 60% | 20% | 20% | — | 26,51% | 87,66% | — |
| C: K-fold (K = 5), hợp luật mọi fold | 4/5 train, 5 lần | fold còn lại (ngoài fold) | dự đoán ngoài fold của toàn bộ train | 6.787 | 26,32% | 87,00% | 10,7 / 29,3 |
| C + lọc ổn định (luật được cả 5 fold chọn) | như trên | như trên | như trên | 4.975 | 26,39% | 87,48% | 11,3 / 28,7 |

Hướng C dùng **toàn bộ** train cho cả tìm luật lẫn chấm luật, mà không luật nào tự chấm chính mình
(K-fold cross-fitting). Macro-F1 ngoài fold trên train là 27,37–27,44%, nhưng trên valid không hơn A. Lọc ổn
định chỉ thêm +0,07. Lý giải khả dĩ (suy luận, chưa kiểm chứng riêng): độ tin cậy gộp từ 5 fold sát precision thô
hơn, nên ở cùng ngưỡng 0,15 có nhiều luật SIMULTANEOUS vượt ngưỡng hơn, recall gấp đôi nhưng precision tụt 17 → 11%.
Chênh lệch A − C (0,6) cỡ bằng dao động của chính A khi đổi cách chia train (26,99 → 26,51), nên không kết luận A
tốt hơn C một cách có ý nghĩa. Pipeline chính giữ A. Script: `experiments/rules_full/kfold_mine.py`,
`kfold_stab.py`; log `kfold_mine.log`, `kfold_stab.log`.

## 4. Luật thật

Cột *Bộ 378* cho biết luật (hoặc một luật cùng phần mở rộng, tức cùng phát biểu) có nằm trong bộ gọn đang
dùng hay không. Luật không có trong bộ 378 vẫn là luật thật đã qua xác nhận, nhưng mọi cặp nó bắn đã có luật
khác cùng nhãn vượt ngưỡng và thắng, nên bỏ nó không đổi dự đoán (mục 12).

### Luật mạnh nhất trong bộ 378

| Nhãn | Lớp | Luật | DISCOVERY | CONF-1 | wlb |
|---|---|---|---|---|---|
| CONTAINS | `etype_a = Military_operation` | `roleset_a = {Location}` | 245/345 | 31/31 | 0,890 |
| SIMULTANEOUS | `etype_a = Damaging` | `a_before_b = False ∧ order = same` | 11/54 | 8/18 | 0,246 |
| OVERLAP | `sdist = 0` | `roleset_a ∋ Victim ∧ type_b = Bodily_harm` | 36/98 | 13/34 | 0,239 |

### CONTAINS

| Lớp | Luật | DISCOVERY | CONF-1 | wlb | Bộ 378 |
|---|---|---|---|---|---|
| `bucket_a = lead` | `type_a = Hostile_encounter ∧ nrole_a = 0` (mạnh nhất trong 54.719) | 239/254 | 37/37 | 0,906 | không |
| `global` (phủ rộng nhất) | `bucket_a = lead ∧ type_a = Hostile_encounter` | 2.587/4.694 | 904/1.478 | 0,587 | có (đại diện: lớp `bucket_a = lead`, `type_a = Hostile_encounter`) |
| `order = same` | `a_before_b = False ∧ type_a = Military_operation` | 97/164 | 35/53 | 0,526 | có (đại diện ở lớp `sdist = 0`) |

### SIMULTANEOUS

| Lớp | Luật | DISCOVERY | CONF-1 | wlb | Bộ 378 |
|---|---|---|---|---|---|
| `order = rev` | `shares_anchor = True ∧ type_pair = (Attack, Attack)` (mạnh nhất trong 54.719) | 12/84 | 10/18 | 0,337 | không |
| `global` | `HAS(roleset_shared, Agent) ∧ HAS(anchor_roles, (Victim, Victim))` | 8/35 | 6/10 | 0,313 | không |
| `anchor = True` (phủ rộng nhất) | `a_before_b = False ∧ same_type = True` | 284/1.231 | 81/424 | 0,156 | có |

### OVERLAP

| Lớp | Luật | DISCOVERY | CONF-1 | wlb | Bộ 378 |
|---|---|---|---|---|---|
| `bucket_a = early` | `order = same ∧ type_pair = (Killing, Bodily_harm)` (mạnh nhất trong 54.719) | 16/35 | 7/12 | 0,320 | không |
| `global` (phủ rộng nhất) | `order = same ∧ type_a = Damaging` | 37/280 | 19/119 | 0,105 | có (đại diện ở lớp `etype_a = Damaging`) |

`wlb` 0,1–0,3 nghe thấp, nhưng tỷ lệ nền của SIMULTANEOUS là 1–2% và của OVERLAP 0,4–0,6% trong các
lớp này: luật OVERLAP `(Killing, Bodily_harm)` mạnh gấp khoảng 70 lần tỷ lệ nền của lớp.

### BEGINS-ON và ENDS-ON

Có 523 và 26 luật qua xác nhận (so với tỷ lệ nền cực nhỏ nên lift cao), nhưng luật tốt nhất theo `wlb`
chỉ đúng 12/1.968 (0,6%) và 4/1.412 (0,3%) trên CONF-1. Không ngưỡng nào giúp macro-F1 trên CONF-2, nên
hai nhãn này bị tắt; bộ 378 không có luật nào của hai nhãn này.

Mine lại có chủ đích theo định nghĩa RED (BEGINS-ON = cùng bắt đầu, ENDS-ON = meets) trong `experiments/begins_ends/`: tín hiệu
văn bản có ("since/from X", "from A to B", "until X") nhưng nhãn chỉ được chọn ở 1–10% số lần tín hiệu xuất hiện.
Ghi đè lên bước 2.2 cho macro-F1 30,84% → 31,65% (cổng chặt) / 32,36% (cổng nới), đổi lại sửa đúng 6–7 cạnh và
làm hỏng 163–216 cạnh đúng, nên chưa đưa vào pipeline. Luật đáng giữ nhất: TIMEX–TIMEX "ngày = điểm đầu của khoảng" →
BEGINS-ON (CONF-1 7/9, valid 3/10).

## 5. Ví dụ thật: luật bắn thế nào trên một cặp

Ba cặp valid. “Luật bắn” đếm trong 54.719 luật sau xác nhận; chỉ những luật vượt ngưỡng mới được bỏ
phiếu, và mọi luật vượt ngưỡng liệt kê dưới đây đều nằm trong bộ 378 (kiểm bằng
`COMPACT=1 python experiments/rules_full/worked_example.py`).

**Cyclone Forrest** — “In Thailand, the system produced significant storm surge, damaged or
**destroyed** 1,700 homes, and killed two people.” A = *destroyed* (Destroying), B = *damaged*
(Damaging). Gold: SIMULTANEOUS.

- 1.066 luật bắn (SIMULTANEOUS 418, OVERLAP 459, CONTAINS 99, BEGINS-ON 72, ENDS-ON 18).
- Vượt ngưỡng: `REL(a_before_b, False) ∧ CNT(anchor_roles, 3)` → SIMULTANEOUS, wlb 0,152 (có ở 4
  view cùng câu); `HAS(anchor_roles, (Agent, Agent)) ∧ HAS(roleset_b, Loss)` → OVERLAP, wlb 0,127.
- SIMULTANEOUS có `wlb` cao hơn nên thắng. Đúng.

**King David Hotel bombing** — “Some of the inflicted **deaths** and **injuries** occurred in the road
outside the hotel …”. A = *deaths* (Death), B = *injuries* (Bodily_harm). Gold: OVERLAP.

- 298 luật bắn; vượt ngưỡng chỉ có `HAS(roleset_a, Cause) ∧ type_b = Bodily_harm` → OVERLAP,
  wlb 0,142 (DISCOVERY 23/66, CONF-1 5/16). Đúng.

**Battle of Orthez** — “The engagement **occurred** near the end of the Peninsular **War**.”
A = *War* (Military_operation), B = *occurred* (Presence). Gold: CONTAINS.

- 245 luật bắn; vượt ngưỡng: `a_before_b = False ∧ type_a = Military_operation` → CONTAINS, wlb
  0,526, và `HAS(etypeset_a, Location) ∧ type_a = Military_operation` → CONTAINS, wlb 0,508. Đúng.

Cùng một phát biểu thường xuất hiện ở nhiều view (`sdist = 0`, `order = same`, `sdist_ord = (0,
same)` đều nghĩa là “cùng câu”). Vì vậy 54.719 luật không phải 54.719 phát biểu độc lập; combiner chỉ
lấy luật mạnh nhất nên bản trùng không bị đếm hai lần.

## 6. Luật cho ba loại cạnh TIMEX (bước 2.1)

Cùng quy trình (mine DISCOVERY, xác nhận CONF-1, ngưỡng theo nhãn trên CONF-2), điều kiện khác:

- **phía sự kiện:** loại, lemma trigger, vị trí câu, vai trò;
- **phía TIMEX:** loại, độ mịn lịch (`y`, `ym`, `ymd`…), từ nội dung (“war”, “world”, “century”);
- **hình học:** cùng câu, khoảng cách token, thứ tự, TIMEX có phải là TIMEX gần sự kiện nhất;
- **giới từ ngay trước TIMEX:** in, on, during, since, between, to, of…;
- **TIMEX–TIMEX:** so sánh lịch của hai giá trị (`cal = eq`, chứa trong…).

Cổng: `n ≥ 30`, `k ≥ 10`, ≥ 5 document, lift ≥ 2, `wlb/prior ≥ 1,5`; xác nhận `cwlb/prior ≥ 1,5`.

| Loại cạnh | Luật | Ngưỡng (CONF-2) | Luật thật |
|---|---|---|---|
| EV→TIMEX | 1.412 | CONT 0,4 · OVER 0,15 · SIMU 0,15 | `lemma = hurricane ∧ giới từ = on` → CONTAINS (0,758); `giới từ = between ∧ khoảng cách ≤ 8` → OVERLAP (0,397) |
| TIMEX→EV | 1.710 | CONT 0,6 · OVER 0,15 | `giới từ = of ∧ TIMEX chứa “world”` → CONTAINS (0,968); `giới từ = during ∧ “world”` → CONTAINS (0,926) |
| TIMEX–TIMEX | 416 | 0,5 cho mọi nhãn | `cả hai neo được ∧ cal = eq` → SIMULTANEOUS (0,771); `B có độ mịn ymd ∧ A chứa “world”` → CONTAINS (0,871) |

## 7. Pattern từng tầng và luật liên tầng (bước 2.2)

Mọi điều kiện quan sát được xếp vào năm tầng: **ONT** (loại sự kiện, loại TIMEX), **ARG** (vai trò,
entity, neo chung), **DISC** (vị trí, khoảng cách, thứ tự, từ nối, giới từ), **LEX** (trigger, từ điển
sự kiện bao chứa, từ trong TIMEX), **TIME** (TIMEX gần mỗi sự kiện, độ mịn, so sánh lịch).

1. **Stage A — pattern:** mine trong từng tầng (độ sâu ≤ 2), xác nhận trên CONF-1, giữ tối đa 150
   pattern mỗi nhãn mỗi tầng.
2. **Stage B — luật:** hội của 2–3 pattern từ **các tầng khác nhau**, qua cùng cổng và cùng xác nhận.
3. **Stage C — ghi đè:** luật đổi nhãn của bước 2.1 khi độ tin cậy vượt ngưỡng riêng của nhãn (chọn
   trên CONF-2). Pattern chỉ học trên nhãn gold, không đọc nhãn dự đoán.

Luật liên tầng thật (cwlb = cận Wilson trên CONF-1):

| Loại cạnh | Luật | Nhãn | cwlb |
|---|---|---|---|
| EV–EV | DISC: `bucket_a = lead ∧ bucket_b = mid` & LEX: `trigger_a = war ∧ trigger A hay làm bên bao chứa (dur_src = hi)` | CONTAINS | 0,954 |
| EV–EV | DISC: `từ nối giữa = and ∧ từ nối trước B = and` & ONT: `type_pair = (Killing, Bodily_harm)` | OVERLAP | 0,326 |
| EV→TIMEX | ARG: `vai Loss` & DISC: `sự kiện ở đầu bài ∧ sự kiện trước TIMEX` & LEX: `trigger = cyclone` | CONTAINS | 0,816 |
| TIMEX→EV | DISC: `sự kiện ở giữa bài ∧ giới từ during` & LEX: `TIMEX chứa “war”, “world”` | CONTAINS | 0,954 |
| TIMEX–TIMEX | DISC: `B đứng trước A` & TIME: `cal = eq` | SIMULTANEOUS | 0,771 |

| Loại cạnh | Pattern | Luật liên tầng | Macro-F1: 2.1 → 2.2 |
|---|---|---|---|
| EV–EV | 1.673 | 6.184 | 26,99 → 27,44 |
| EV→TIMEX | 245 | 715 | 29,74 → 30,51 |
| TIMEX→EV | 248 | 627 | 24,29 → 26,24 |
| TIMEX–TIMEX | 98 | 450 | 32,98 → 34,93 |
| **Gộp 188.924 cạnh** | | | **30,09 → 30,84** |

## 8. Luật của Bài 2 (bước 3.1 và 3.2)

**Auditor 3.1.** Giống bước 2.2 nhưng thêm tầng **GRAPH** và đổi câu hỏi. Tầng GRAPH là chữ ký các
đường đi a–x–b và a–x–y–b của cạnh trên đồ thị **đang kiểm toán**: loại node trung gian cộng nhãn có
hướng trên từng chặng. Ví dụ thật (document *United States occupation of Nicaragua*): cạnh *began →
1934* có đường qua TIMEX “1912” với chữ ký (TIMEX, *began ← CONTAINS – 1912*, *1912 – BEFORE → 1934*).

Luật được học **riêng cho từng nhóm (loại cạnh, nhãn hiện tại)**, và mỗi luật trả lời: *trong các
cạnh đang mang nhãn này, cạnh nào sai và đúng ra là gì*. Cổng thích ứng theo tỷ lệ nền của nhóm:
`k/n ≥ min(2·prior, (1+prior)/2)` và `wlb > prior`. Cổng lift ≥ 2 cũ không qua được khi nhãn cần khôi
phục là đa số của nhóm: 57% cạnh EV–EV mà classifier gán CONTAINS thực ra là BEFORE. Luật mine lại
trong từng fold cross-fit trên valid (học một nửa, chấm nửa kia), nên không có một bộ luật cố định.

Mỗi fold mine khoảng 1.400–1.560 luật (8 nhóm loại cạnh × nhãn hiện tại); sau ngưỡng còn 87–287 luật
hoạt động; rút gọn có chứng minh (mục 12, với "giữ nhãn hiện tại" thay cho BEFORE) còn **42–83 luật**:

| Fold · mục tiêu | Luật mine (pattern + liên tầng) | Hoạt động | A: giữ mọi thay đổi (chặn dưới) | B: giữ thay đổi đúng (chặn dưới) |
|---|---|---|---|---|
| 0 · giảm lỗi | 1.559 (1.409 + 150) | 211 | 83 (83) | 73 (73) |
| 0 · macro-F1 | 1.559 | 111 | 70 (70) | 67 (66) |
| 1 · giảm lỗi | 1.433 (1.294 + 139) | 287 | 76 (76) | 69 (69) |
| 1 · macro-F1 | 1.433 | 87 | 42 (42) | 36 (36) |

Bảy trong tám bộ gọn bằng đúng chặn dưới, tức là tối ưu; bộ còn lại cách tối ưu tối đa 1 luật. Trên fold
test (cộng hai fold), auditor gọn giữ nguyên đầu ra ở 99,985% (A, giảm lỗi) và 99,993% (A, macro-F1) số
cạnh; lỗi 12,80% → 12,79%, macro-F1 31,53% không đổi. Script `experiments/higher_order/bai2_compress.py`,
log `experiments/logs/bai2_compress.log`.

**Sửa chung 3.2.** Không phải luật if-then mà là **tần suất cấu hình tam giác** trên gold train
(DISCOVERY + CONF-1, 2.326 document, 6,31 triệu tam giác). Cấu hình = loại 3 node + 3 nhãn có hướng.
Mỗi tam giác nhận điểm `−PMI` của cấu hình; cả document được gán lại nhãn bằng ICM để giảm tổng năng
lượng. Ví dụ thật: *1912 CONTAINS began*, *1912 BEFORE 1934*, *began OVERLAP 1934* là cấu hình gặp 0
lần trong gold; đổi cạnh cuối thành BEFORE cho cấu hình gặp 27.582 lần, khớp gold.

## 9. Những điều phải nói kèm

1. **BEGINS-ON và ENDS-ON vẫn không có luật dùng được trong pipeline** (mục 4). Valid có 69 và 34 cạnh trên cả
   bốn loại cạnh. Mine lại theo định nghĩa gốc có tăng macro-F1 nhưng làm hỏng nhiều cạnh đúng hơn số sửa được.
2. **Nhiều luật gần trùng giữa các view:** 54.719 luật chỉ là 33.215 phát biểu khác nhau, và 378 luật đủ
   cho cùng dự đoán (mục 12).
3. **Bước BH dùng kiểm định nhị thức, không dùng hoán vị** (mục 3.3).
4. **Độ sâu tối đa 2 trong một bộ luật.** Hội 3 điều kiện chỉ xuất hiện qua luật liên tầng (hội 2–3
   pattern, mỗi pattern tối đa 2 điều kiện).
5. **Bộ luật mới hơn bộ cũ ở EV–EV (+0,84 ở 2.1, +0,94 sau 2.2)**, nhưng lợi thế gần như biến mất khi
   gộp cả bốn loại cạnh sau bước 2.2 (30,83 → 30,84) và sau mô hình tam giác của Bài 2 (31,70 → 31,36). Chưa đo
   dao động theo seed cho các bước này, nên chưa thể nói chênh lệch −0,34 là thật hay nhiễu.

## 10. Lịch sử: bộ 257 luật cũ

| Bộ | Được chọn trên | Số luật | EV–EV valid |
|---|---|---|---|
| `rules/final/rules_rx_c70.json` | 400 document train đầu (197 / 126 / 77) | 257 (254 CONTAINS, 2 SIMU, 1 OVER) | 25,60% |
| + 719 luật trigger | như trên | 976 | 26,15% |
| **`rules_full` (hiện tại)** | **2.913 document train** | **54.719 qua xác nhận, 2.794 hoạt động, bộ gọn 378** | **26,99%** |

Bộ cũ đi qua chuỗi 155.467 luật thô → 1.453 họ trừu tượng (không qua subsumption) → 4.380 (gộp nhánh MDD vét cạn độ sâu 2 chỉ ở
view `global`) → 861 (bốn cổng) → 257 (giữ top 30% theo Wilson trên CONFIRMATION). Bộ mới thay cả hai
nhánh bằng vét cạn độ sâu 2 trong mọi lớp của 8 view. Chi tiết bộ cũ: `report/BAI1_C2_FINAL.md`.

## 11. Tái tạo

```bash
cd src
NW=4 python ../experiments/rules_full/mine_full.py                # 2.1 EV–EV, ~6 phút (REMINE=1 để mine lại)
python ../experiments/rules_full/export_full.py                   # bắn luật trên train + valid → pred_all_edges_full.json
python ../experiments/higher_order/bai1_all_edges.py              # 2.1 ba loại cạnh TIMEX
TAG=_full python ../experiments/higher_order/layered_rules.py     # 2.2 luật liên tầng, ~8 phút
TAG=_full python ../experiments/higher_order/bai2_combo.py        # Bài 2: 3.1, 3.2 (và tam giác một mình), cross-fit, ~34 phút
python ../experiments/rules_full/worked_example.py                # ví dụ thật ở mục 5
NW=4 python ../experiments/rules_full/compress.py                # rút gọn có chứng minh, ~3,5 phút (mục 12)
python ../experiments/rules_full/compact_listing.py               # → report/RULES_COMPACT.md
```

---

## 12. Rút gọn 54.719 luật, có chứng minh

54.719 là số luật **qua xác nhận**, không phải số luật cần để ra dự đoán. Toàn bộ rút gọn dưới đây suy
ra từ đúng một công thức của combiner:

```
pred(x) = nhãn của argmax_{r ∈ A(x)} key(r)      (BEFORE nếu A(x) rỗng)
A(x)    = các luật HOẠT ĐỘNG bắn trên cặp x (wlb ≥ ngưỡng của nhãn luật)
key(r)  = (wlb(r), −id(r))                        (thứ tự toàn phần, không có hoà)
```

**Bước 1: bỏ luật không bao giờ bỏ phiếu (chính xác tuyệt đối).** Luật có `wlb` dưới ngưỡng của nhãn nó
không bao giờ vào `A(x)`, nên xoá nó không đổi dự đoán ở bất kỳ cặp nào, kể cả cặp chưa gặp.
**51.925 luật** thuộc loại này (gồm toàn bộ 549 luật BEGINS-ON / ENDS-ON). Còn 2.794.

**Bước 2: gộp luật trùng phần mở rộng.** Phần mở rộng `ext(r)` = tập cặp train mà luật bắn. Hai luật
cùng nhãn và cùng `ext` là **một phát biểu** (quan hệ tương đương; mỗi lớp giữ một đại diện ít điều kiện
nhất). So sánh bằng dấu vân tay `(|ext|, Σ_{i ∈ ext} h(i) mod 2⁶¹−1)` trên 483.504 cặp train; xác suất
va chạm cỡ 10⁻¹⁰.

- 54.719 luật chỉ có **33.215 phát biểu khác nhau** (trung bình 1,65 luật mỗi lớp).
- 2.794 luật hoạt động chỉ có **1.621 phát biểu khác nhau**.
- Lớp lớn nhất có 19 luật: trong lớp `sdist = 0`, mọi luật kèm `HAS(anchor_roles, (Loser, Patient))`
  (thêm `type_a = Competition`, `roleset_a ∋ Winner`, …) đều bắn trên đúng cùng các cặp, vì điều kiện
  thứ nhất đã kéo theo điều kiện thứ hai.
- Kiểm tra: chỉ giữ đại diện đổi **0 / 593.433** dự đoán (train + valid).

**Bước 3: set cover giữ dự đoán.** Với cặp `x` được đoán nhãn `p ≠ BEFORE`, gọi `M(x)` là key lớn nhất
của các luật hoạt động **khác nhãn** bắn trên `x`, và

```
C(x) = { r ∈ A(x) : nhãn(r) = p,  key(r) > M(x) }
```

*Mệnh đề.* Nếu tập luật giữ lại `K` chứa ít nhất một phần tử của `C(x)` với mọi cặp `x` như vậy, thì
`pred_K(x) = pred(x)` với mọi `x`.
*Chứng minh.* Luật `r ∈ K ∩ C(x)` vẫn bắn và có key lớn hơn mọi luật khác nhãn, nên argmax vẫn mang nhãn
`p`. Cặp được đoán BEFORE không có luật hoạt động nào bắn; bỏ luật không thể làm luật bắn thêm, nên nó
vẫn là BEFORE. ∎

Tìm `K` nhỏ nhất là bài **set cover** (NP-khó). Cách giải:

1. **Luật bắt buộc:** cặp có `|C(x)| = 1` buộc phải giữ luật duy nhất đó.
2. **Greedy lười** (mỗi vòng chọn luật phủ nhiều cặp chưa phủ nhất): bảo đảm `|K| ≤ H(d)·OPT`, với `d` là
   số cặp lớn nhất một luật phủ.
3. **Xoá ngược:** bỏ lần lượt luật nào mà mọi cặp của nó còn luật khác phủ, nên kết quả không thừa luật
   nào.
4. **Chặn dưới cho OPT:** một tập cặp có `C(x)` đôi một rời nhau cần mỗi cặp một luật riêng, nên
   `OPT ≥` kích thước tập đó (xếp tham lam, `|C(x)|` nhỏ trước).

Hai biến thể, dựng trên DISCOVERY + CONF-1, kiểm trên CONF-2, valid mở một lần, ngưỡng không chỉnh lại:

| Biến thể | Vũ trụ | Luật bắt buộc | Chặn dưới OPT | **Kết quả** | Giữ nguyên dự đoán: CONF-2 / valid | Valid macro-F1 / acc |
|---|---|---|---|---|---|---|
| Đầy đủ | — | — | — | 2.794 | — | 26,99% / 87,90% |
| **A: giữ mọi dự đoán** | 37.316 cặp đoán ≠ BEFORE | 318 | **377** | **378** | 99,985% / 99,979% | **26,99% / 87,91%** |
| **B: giữ mọi dự đoán đúng** | 14.624 cặp đoán đúng ≠ BEFORE | 198 | **278** | **279** | 99,741% / 99,699% | **27,02% / 88,11%** |

- **Greedy cách tối ưu tối đa 1 luật:** 377 ≤ OPT_A ≤ 378 và 278 ≤ OPT_B ≤ 279. Với ngôn ngữ luật và tập
  ứng viên này, không cách chọn tập con nào giữ được mọi dự đoán mà dùng ít hơn 377 luật.
- **A** cho dự đoán giống hệt trên toàn bộ dữ liệu dựng (chứng minh ở trên) và chỉ lệch 0,021% trên valid
  (khoảng 23 cặp). Các bước sau (2.2 và Bài 2) chạy trên dự đoán của 2.794 luật hoạt động và chưa chạy
  lại với bộ 378; với mức lệch đó, thay đổi nếu có sẽ rất nhỏ.
- Mệnh đề được chứng minh cho combiner với tie-break `key = (wlb, −id)` mà `compress.py` cài lại; combiner
  gốc (`pred_floor`) phá hoà theo thứ tự bắn. Bản cài lại cho đúng macro-F1 của combiner gốc trên CONF-2
  (26,36%) và valid (26,99%, accuracy 87,90%).
- **B** bảo đảm mọi cặp đã đoán đúng trên dữ liệu dựng vẫn đúng; cặp đoán sai có thể về BEFORE. Trên
  valid accuracy +0,21, macro-F1 +0,03; F1 từng nhãn gần như không đổi (CONTAINS 42,5 → 42,7).
- Khác hai lần rút gọn trước: **bỏ theo bao hàm** làm mất tín hiệu (−2,13 precision), và **set cover
  gộp mọi nhãn** chỉ giữ luật CONTAINS. Ở đây ràng buộc đặt trên đúng quyết định của combiner ở từng
  cặp, nên nhãn hiếm được giữ nguyên: A còn 276 CONTAINS, 55 SIMULTANEOUS, 47 OVERLAP.

**Áp dụng cho mọi bộ luật của pipeline** (cùng chứng minh, `rule_cover.py`):

| Bộ luật | Sau xác nhận / qua cổng | Hoạt động | Phát biểu khác nhau | **Phủ A** (chặn dưới) | Valid: giữ nguyên / macro-F1 |
|---|---|---|---|---|---|
| EV–EV (2.1) | 54.719 | 2.794 | 1.621 | **378** (377) | 99,979% / 26,99% |
| EV→TIMEX (2.1) | 1.412 | 134 | 125 | **45** (45) | 100% / 29,74% |
| TIMEX→EV (2.1) | 1.710 | 598 | 583 | **93** (93) | 99,997% / 24,29% |
| TIMEX–TIMEX (2.1) | 416 | 100 | 90 | **16** (16) | 100% / 32,98% |
| Liên tầng EV–EV (2.2) | 7.856 | 1.595 | 1.015 | **152** (152) | 99,979% / 27,41% |
| Liên tầng EV→TIMEX | 959 | 273 | 217 | **12** (12) | 99,989% / 30,58% |
| Liên tầng TIMEX→EV | 875 | 6 | 6 | **5** (5) | 100% / 26,24% |
| Liên tầng TIMEX–TIMEX | 548 | 221 | 121 | **12** (12) | 100% / 34,93% |
| **Bài 1 tổng** | **68.495** | **5.721** | | **713** (712) | |
| Auditor Bài 2 (mỗi fold · mục tiêu) | 1.433–1.559 | 87–287 | | **42–83** (42–83) | 99,985–99,993% |

Mọi phủ A trừ EV–EV bằng đúng chặn dưới, tức là **tối ưu**; EV–EV cách tối ưu tối đa 1 luật. Luật liên tầng
dùng combiner ghi đè, nên tập cặp cần giữ gồm cả những cặp mà luật đề xuất đúng nhãn đang có để chặn nhãn
khác (`experiments/rules_full/rule_cover.py`). Script: `compress_timex.py`, `compress_layered.py`; bộ gọn:
`src/artifacts/rules_compact_timex.json`, `rules_compact_layered.json`. Chạy lại bước liên tầng để xuất luật
cho 30,83% thay vì 30,84% (207 / 981.319 dự đoán khác nhau): bước này không tái lập từng bit, vì thứ tự duyệt
set phụ thuộc hash seed.

**Bước 4: gom nhóm để đọc.** Họ = cùng nhãn, cùng dạng và thuộc tính điều kiện, khác giá trị (cách trừu
tượng hoá đã giữ được tín hiệu ở nghiên cứu 155 nghìn luật).

| | Luật | Họ | CONTAINS / SIMU / OVER |
|---|---|---|---|
| A | 378 | 209 | 276 / 55 / 47 |
| B | 279 | 170 | 211 / 37 / 31 |

Họ lớn nhất (A): `EQ(type_pair)` → CONTAINS, 23 luật, ví dụ `(Military_operation, Hostile_encounter)`
180/292 · 61/92 và `(Catastrophe, Damaging)`; `EQ(bucket_b) ∧ EQ(type_a)` → CONTAINS; `EQ(type_pair)` →
OVERLAP, ví dụ `(Damaging, Destroying)`. Không còn cặp luật gần trùng: 0 cặp cùng nhãn có Jaccard phần mở
rộng ≥ 0,8 trong bộ B, tức các luật giữ lại gần như trực giao. Danh sách đầy đủ theo nhãn → họ → luật:
`RULES_COMPACT.md`.

| Tầng rút gọn | Số luật | Dự đoán |
|---|---|---|
| Sau xác nhận | 54.719 | — |
| Bước 1: bỏ luật dưới ngưỡng | 2.794 | giống hệt, mọi nơi |
| Bước 2: một đại diện mỗi phát biểu | 1.621 | giống hệt trên train + valid |
| **Bước 3A: set cover giữ dự đoán** | **378** (209 họ) | giống hệt trên dữ liệu dựng; valid 99,979% |
| Bước 3B: set cover giữ dự đoán đúng | 279 (170 họ) | valid 99,699%; accuracy tăng |

**Một điểm yếu lộ ra khi đọc danh sách.** Nhiều luật có precision thấp trên DISCOVERY nhưng rất cao trên
CONF-1, ví dụ `type_pair = (Catastrophe, Motion_directional)`: 11/32 rồi 12/12, wlb 0,758. `wlb` tính trên
CONF-1 cho 92 nghìn ứng viên nên bị “lời nguyền người thắng”: luật được xếp cao nhờ may trên tập xác nhận
nhỏ. Hướng sửa: gộp bằng chứng hai phần (`k + ck` trên `n + cn`) hoặc co về tiên nghiệm (Bayes
thực nghiệm) trước khi so với ngưỡng. Chưa làm.

Script: `experiments/rules_full/compress.py` (khoảng 3,5 phút, 4 tiến trình), log `compress.log`, kết
quả `src/artifacts/rules_compact.json`, danh sách `compact_listing.py` → `report/RULES_COMPACT.md`.
