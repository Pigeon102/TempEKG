# Tìm bộ rule nhỏ nhất

> Code: `tempekg_kg/minimise.py`. Kết quả: `minimal_rules.json`.
> Bài toán: phủ nhiều nhất, precision cao nhất, số rule ít nhất.
> Ba mục tiêu này xung đột nhau, nên tài liệu này nói rõ cách đánh đổi.

---

## 0. Vì sao cần

Mine trên 8 view cho **155.467 rule**. Không ai đọc được, và đo được là phần lớn là nhiễu:

| Tập rule | Rule | Phủ | Precision |
|---|---:|---:|---:|
| tất cả | 155.467 | 100% | 10,68% |
| sau subsumption | 129.987 | 100% | 8,55% |
| **956 họ trừu tượng** | **956** | 93,8% | **8,76%** |
| general + specific | 124.037 | 100% | 8,55% |

Thêm 123.275 rule type-specific vào 956 họ **không cải thiện gì**. Nên câu hỏi không phải
"cắt bớt bao nhiêu" mà **"tập nhỏ nhất giữ được tín hiệu là tập nào"**.

---

## 1. Biểu diễn toán học

Gọi $\mathcal{C}$ là tập điều kiện nguyên tử, $\mathcal{X}$ là tập instance.
Rule là cặp $(P, r)$ với $P \subseteq \mathcal{C}$.

Với instance $x$, gọi $\text{cond}(x)$ là tập điều kiện nó thỏa. Rule khớp khi
$P \subseteq \text{cond}(x)$. **Tập phủ**:

$$\text{cov}(P) = \{x \in \mathcal{X} : P \subseteq \text{cond}(x)\}$$

Hai tính chất, cả hai kiểm được bằng phép tập hợp:

$$P \subseteq Q \implies \text{cov}(Q) \subseteq \text{cov}(P) \qquad \text{(đơn điệu giảm)}$$

$$\text{cov}(P \cup Q) = \text{cov}(P) \cap \text{cov}(Q)$$

Tính chất thứ hai cho phép biến kiểm tra tập con thành **phép AND trên bitmask**.

### 1.1. Bitset

Đánh số instance $0..n-1$. Mỗi rule thành một số nguyên $n$ bit; bit $i$ bật nghĩa là rule
khớp instance $i$. Python `int` là bignum nên AND và popcount là **một phép trên toàn corpus**.

Đo được: **6,8 µs** cho AND + popcount trên 110.000 bit; **34 µs** trên 483.504 bit.

Thêm `cor(P)` — tập instance rule khớp **và đoán đúng**. Đây mới là thứ đáng tối ưu:
rule phủ rộng mà đoán sai thì vô giá trị.

### 1.2. Ba quan hệ giữa rule

| Quan hệ | Công thức bit | Nghĩa |
|---|---|---|
| Tổng quát hơn | $P \subseteq Q$ | $P$ phủ rộng hơn $Q$ |
| **Dư thừa** | `cov(P) == cov(Q)` | khớp **đúng cùng** tập instance |
| Bị trội | `cov(Q) & ~cov(P) == 0` và $\text{wlb}(Q) \le \text{wlb}(P)$ | hẹp hơn mà không chính xác hơn |
| Trùng lặp họ | $J = \dfrac{\lvert A \cap B\rvert}{\lvert A \cup B\rvert}$ | Jaccard; $J \to 1$ thì một cái thừa |

---

## 2. Lỗi đã sửa: cú pháp vs ngữ nghĩa

Hàm `subsume()` ở vòng trước loại rule khi **điều kiện của nó là siêu tập** của một rule
khác. Đó là kiểm tra **cú pháp**, và đo được nó **mất 2,13 điểm precision**:

```
tất cả          155.467   10,68%
sau subsumption 129.987    8,55%   ← mất 2,13 điểm
```

Giả định "rule dài bị rule ngắn bao hàm thì thừa" **sai**. Rule dài **hẹp hơn nên chính xác
hơn** trên vùng nó phủ; bỏ nó đi là bỏ đúng phần chính xác nhất.

Tiêu chí đúng là **ngữ nghĩa**: chỉ loại khi `cov(P) == cov(Q)`. Lúc đó rule thật sự không
mang thông tin gì thêm — nó khớp đúng cùng tập instance và đoán cùng nhãn.

---

## 3. Chọn tập nhỏ nhất — set cover có trọng số

Bài toán: chọn $S \subseteq R$ nhỏ nhất sao cho phủ đủ và precision cao.

Hàm mục tiêu là **số instance đoán đúng**:

$$f(S) = \Big\lvert \bigcup_{P \in S} \text{cor}(P) \Big\rvert$$

$f$ là **submodular**: thêm một rule vào tập lớn hơn thì lợi ích biên không thể lớn hơn khi
thêm vào tập nhỏ hơn. Chính thức, với $A \subseteq B$:

$$f(A \cup \{P\}) - f(A) \;\ge\; f(B \cup \{P\}) - f(B)$$

Greedy trên hàm submodular đạt tỉ lệ xấp xỉ $1 - 1/e \approx 0{,}63$ so với tối ưu — đủ tốt,
và bài toán tối ưu là NP-khó nên không có lựa chọn thực tế nào tốt hơn.

### 3.1. Lazy greedy (CELF)

Greedy ngây thơ quét toàn pool mỗi vòng: $2000 \times 100.000 \times 34\,\mu s \approx 2$ giờ.

Tính submodular cho phép **đánh giá lười**: gain của một rule **không bao giờ tăng** khi đã
chọn thêm rule khác. Nên giữ pool trong heap khóa theo gain cũ, chỉ tính lại phần tử đỉnh.
Nếu sau khi tính lại nó vẫn dẫn đầu thì đó **chắc chắn** là cực đại thật.

```
heap ← {(-gain₀(P), 0, P) : P ∈ pool}
lặp:
    (g, stamp, P) ← pop heap
    nếu stamp ≠ round:                    # cũ
        g ← |cor(P) & ~claimed|           # tính lại
        nếu g < -heap[0][0]:               # có kẻ khác tốt hơn
            push (-g, round, P); tiếp
    chọn P; claimed |= cov(P); round += 1
```

Giảm từ ~2 giờ xuống vài phút.

---

## 4. Đường cong Pareto — không chọn hộ

Phủ và precision **xung đột trực tiếp**. Thêm rule thì phủ tăng, nhưng phủ thêm ở **vùng
khó**, nơi mọi rule đều sai nhiều hơn.

Ba cách đặt bài toán cho ba kết quả khác nhau:

| Mục tiêu | Cách | Kết quả |
|---|---|---|
| Phủ tối đa | greedy trên `cov` | nhiều rule, precision thấp |
| Precision tối đa | chỉ giữ rule wlb cao | ít rule, phủ rất thấp |
| **Pareto** | quét sàn wlb | **người dùng chọn điểm** |

Nên chạy greedy nhiều lần với **sàn Wilson LB** khác nhau (0,0 → 0,7). Sàn cao thì nhận ít
rule nhưng an toàn hơn. Mỗi lần cho một điểm $(\text{số rule}, \text{phủ}, \text{precision})$.

Điểm vận hành mặc định: **precision cao nhất trong các lần phủ được ≥50% khối lượng
non-BEFORE**. Ràng buộc đó có lý do ở mục 5.

---

## 5. Phủ phải đọc theo kiến trúc KG

Phủ gộp **che giấu chỗ phủ rơi vào đâu**. Ba lát cắt phải báo riêng:

### 5.1. non-BEFORE

Family **không phát ra BEFORE theo định nghĩa** (base rate 91% nên
$1/0{,}91 = 1{,}10 <$ ngưỡng lift). Nên "phủ 100%" thực chất là phủ 100% **cơ hội**, mà 90%
trong đó là BEFORE ta bỏ qua.

Con số trung thực là **phủ trên tập non-BEFORE**. Một tập rule phủ 90% mà toàn cặp BEFORE
thì vô dụng.

### 5.2. anchored vs unanchored

| | Tỉ lệ cặp EV-EV có nhãn |
|---|---:|
| Chung anchor | 25,8% |
| Không chung gì | 74,2% |

Constraint mạnh nhất đều cần anchor. Tập rule phủ rộng nhưng toàn cặp không-anchor thì
không dùng được cho audit.

### 5.3. document

2.913 document. Tập rule chỉ bắn ở 500 doc thì không audit được toàn KG, dù phủ instance có
cao đến đâu.

---

## 6. Chạy

```bash
python minimise.py                                  # mặc định
python minimise.py --target-cover 0.90 --min-gain 20
```

| Tham số | Mặc định | Ý nghĩa |
|---|---|---|
| `--min-gain` | 30 | dừng khi rule tiếp theo thêm < 30 instance đúng |
| `--target-cover` | 0,95 | dừng sớm khi đạt mức phủ này |
| `--max-rules` | 2000 | chặn cứng số rule |
| `--lift-min` | 1,5 | ngưỡng lift lúc mine |

Xuất `minimal_rules.json` — mỗi rule kèm hạng, gain, wlb, lift, view và chữ ký.

---

## 7. Chi phí, và vì sao không cần GPU

| Pha | Chi phí | GPU giúp? |
|---|---|---|
| Mine 8 view | ~90 phút | **Không** — vòng lặp có điều kiện, không vector hoá |
| Dựng bitset | ~10 phút | **Không** — pointer chasing qua dict/frozenset |
| Greedy CELF | ~vài phút | **Không** — đã submodular, heap đã cắt hết việc thừa |
| Constraint | ~5 phút | **Không** — chỉ đếm và so ngưỡng |

Nút thắt là **kiểm tra tập con trên object Python**, không phải số học. GPU tăng tốc phép
tính song song trên mảng số; ở đây chi phí *chuyển dữ liệu* sang VRAM đã lớn hơn toàn bộ
phép tính.

Chỗ còn tối ưu được mà không cần GPU:

**Index theo điều kiện hiếm nhất.** Code cũ index rule theo điều kiện **đầu tiên**, mà điều
kiện đầu thường là thứ 98% instance đều có:

```
EQ(multi_mention_b=False)   98% instance
EQ(multi_mention_a=False)   98%
EQ(same_type=False)         97%
CNT(roleset_b>=1)           90%
```

Đo trên 4.000 instance:

| | Thời gian | Số lần kiểm tra |
|---|---:|---:|
| first-cond | 7,20 s | 8.911.313 |
| **rarest-cond** | **1,90 s** | **2.192.752** |

**3,8× nhanh hơn, kết quả giống hệt** (1.047.691 hits cả hai). Đã áp dụng trong `minimise.py`.

**numpy packbits** sẽ cho thêm 5–10× nữa, vẫn CPU. Hiện máy chưa cài numpy.

GPU chỉ đáng xét nếu rule lên hàng triệu hoặc corpus lớn gấp 10.

---

## 8. Kết quả

> Đang chạy. Sẽ điền: bảng Pareto, điểm vận hành chọn, phủ theo ba lát cắt, tập rule cuối,
> và Jaccard giữa các rule được chọn.

---

## 8. Kết quả

Chạy `python tempekg_kg/minimise.py --wlb-floor 0.4` — 1.751 s tổng.

### 8.1. Đường cong Pareto (train)

| Sàn wlb | Rule | Phủ | Precision | Phủ non-BEFORE | Phủ anchored |
|---:|---:|---:|---:|---:|---:|
| **0,40** | **68** | 13,0% | **35,35%** | **55,1%** | 22,9% |
| 0,50 | 60 | 6,9% | 48,59% | 39,2% | 12,3% |
| 0,60 | 47 | 3,2% | 61,80% | 23,1% | 5,4% |
| 0,70 | 31 | 0,6% | **84,63%** | 5,6% | 0,9% |

Đánh đổi đúng như dự đoán ở §4: sàn cao cho precision cao nhưng phủ sụp. Sàn 0,70 đạt
**84,63%** precision với 31 rule nhưng chỉ chạm 0,6% instance.

Điểm vận hành chọn tự động: **precision cao nhất trong các lần phủ ≥50% khối lượng
non-BEFORE** — ra sàn 0,40.

### 8.2. Phủ theo lát cắt kiến trúc (train, 68 rule)

| Lát cắt | Instance | Phủ | Tỉ lệ | Precision |
|---|---:|---:|---:|---:|
| all | 483.504 | 62.975 | 13,0% | 35,35% |
| **non_BEFORE** | 43.298 | 23.836 | **55,1%** | **93,40%** |
| anchored | 124.708 | 28.499 | 22,9% | 35,78% |
| unanchored | 358.796 | 34.476 | 9,6% | 35,00% |

Family không phát ra BEFORE theo định nghĩa, nên chấm nó trên toàn bộ instance (89,94% là
BEFORE) là chấm sai đối tượng. Trên đúng thứ nó nhắm: **93,40% precision, phủ 55,1%** với
68 rule.

> **Nhưng đây KHÔNG phải số cho bảng classifier.** Mẫu số là *các cặp rule có bắn và đoán
> CONTAINS*, sau khi đã bỏ toàn bộ BEFORE ra. Chấm như một classifier thật trên valid (giữ
> cả BEFORE trong mẫu số), CONTAINS đạt **P 35,25% / R 56,07% / F1 43,29%**, và macro-F1
> toàn hệ là **22,62%** so với 15,78% của hằng số.
>
> Hai con số đều đúng, trả lời hai câu hỏi khác nhau: 93,40% nói *"khi rule dám đoán CONTAINS
> thì nó đúng bao nhiêu"*, còn 35,25% nói *"trong toàn bộ bài toán phân loại, CONTAINS được
> dự đoán chính xác bao nhiêu"*. **Bảng classifier phải dùng 35,25%.**

Và phủ **đều** giữa anchored (35,78%) và unanchored (35,00%): rule không phụ thuộc việc có
anchor hay không. Quan trọng vì 74,2% cặp không chung anchor.

### 8.3. Held-out trên valid

| Tập rule | Rule | Khớp | Phủ | Precision | Oracle |
|---|---:|---:|---:|---:|---:|
| tất cả | 155.124 | 109.929 | 100% | 8,55% | 10,04% |
| phủ phân biệt | 7.103 | 18.096 | 16,5% | 31,52% | 31,52% |
| **greedy tối thiểu** | **68** | 14.937 | 13,6% | **35,25%** | 35,25% |
| *hằng BEFORE trên tập khớp* | — | — | — | *62,26%* | — |

**35,25% trên valid so với 35,35% trên train** — không overfit. Và **gấp 4,1 lần** bộ 155.124
rule đầy đủ, với **ít hơn 2.281 lần** số rule.

Hai quan sát:

`precision == oracle` ở cả hai tập cuối. Mọi rule bắn trên một instance đều **đồng ý cùng
nhãn** — không còn xung đột để chọn. Đó là hệ quả trực tiếp của dedupe theo tập phủ: các
rule khác cú pháp nhưng cùng phủ đã bị gộp.

Hằng BEFORE trên tập khớp chỉ còn **62,26%**, không phải 89,94%, vì 68 rule chọn lọc vào
vùng giàu non-BEFORE. Vẫn thua, nhưng khoảng cách thu từ 81 điểm xuống 27 điểm.

### 8.4. Dedupe theo tập phủ

```
11.097 rule (sàn 0,4)
   ↓ cov(P) == cov(Q)
 7.103 tập phủ phân biệt   (36% dư thừa ngữ nghĩa)
   ↓ lazy greedy
    68 rule
```

36% rule khớp **đúng cùng tập instance** và đoán cùng nhãn — chỉ khác cách viết điều kiện.
Đây là phép dedupe đúng, khác hẳn subsumption cú pháp (§2) vốn làm mất 2,13 điểm.

### 8.5. Trùng lặp rất thấp

Chỉ **3 cặp** có Jaccard > 0,5 trong top 60:

```
0,67  EQ(bucket_a=lead) AND EQ(type_a=Catastrophe)
0,59  EQ(bucket_a=lead) AND HAS(etypeset_a=Organization)
0,58  CNT(etypeset_a>=1) AND EQ(type_a=Military_operation)
```

Bộ rule gần như **trực giao** — mỗi rule phủ vùng riêng, đúng như set cover mong đợi.

### 8.6. Một hệ quả phải nêu: cả 68 rule đều dự đoán CONTAINS

| | |
|---|---|
| Theo quan hệ | CONTAINS 68 · **không có nhãn nào khác** |
| Theo view | global 32 · etype_a 16 · bucket_a 6 · sdist 5 · anchor 3 · order 3 · sdist_ord 2 · anchor_sd 1 |

Đây là **hệ quả tất yếu của hàm mục tiêu**, không phải lỗi. Greedy tối đa hoá *số instance
đoán đúng*, mà CONTAINS chiếm **88,1%** khối lượng non-BEFORE (95.933 trên 108.864). Rule
dự đoán SIMULTANEOUS hay OVERLAP có gain biên nhỏ hơn hẳn nên không bao giờ được chọn.

Hệ quả: bộ 68 rule là **bộ phát hiện CONTAINS**, không phải bộ dự đoán quan hệ tổng quát.
Phải nói đúng như vậy trong bài.

Nếu muốn bộ phủ cả các nhãn hiếm thì phải đổi hàm mục tiêu — ví dụ greedy **theo từng nhãn**
rồi hợp nhất, hoặc chuẩn hoá gain theo tần suất nhãn. Đó là việc chưa làm.

### 8.7. Năm rule mạnh nhất

| Gain | wlb | lift | n | Pattern |
|---:|---:|---:|---:|---|
| +5.369 | 0,450 | 6,18× | 11.695 | `EQ(bucket_a=lead) ∧ EQ(multi_mention_a=True)` |
| +2.925 | 0,529 | 1,67× | 5.391 | `EQ(multi_mention_a=False) ∧ EQ(type_a=Hostile_encounter)` *(view bucket_a=lead)* |
| +2.185 | 0,409 | 5,67× | 5.831 | `CNT(etypeset_a=1) ∧ EQ(type_a=Military_operation)` |
| +2.111 | 0,407 | 5,64× | 6.498 | `EQ(type_a=Competition) ∧ HAS(roleset_a=Location)` |
| +1.258 | 0,402 | 5,55× | 7.930 | `EQ(bucket_b=mid) ∧ EQ(type_a=Hostile_encounter)` |

`bucket_a=lead` xuất hiện dày đặc — **sự kiện ở câu đầu bài thường bao trùm sự kiện sau**.
Đó là quy luật diễn ngôn thật, và nó là rule có gain lớn nhất.

### 8.8. Chi phí

| Pha | Thời gian |
|---|---:|
| Nạp + mine 8 view | 1.350 s |
| Dựng bitset (11.097 rule, sàn 0,4) | **36 s** |
| Pareto 4 mức + greedy | ~200 s |
| Đánh giá 3 tập trên valid | ~165 s |
| **Tổng** | **1.751 s** |

Bitset 36 giây so với **treo 70 phút rồi MemoryError** ở bản trước — xác nhận cả hai bản sửa
(bytearray thay `|=` từng bit, và lọc sàn trước khi cấp phát).
