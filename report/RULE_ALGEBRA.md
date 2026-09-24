# Đại số rule — biểu diễn toán học, và chỗ nào còn tìm được thêm

> Viết để trả lời hai câu: *mine bằng cách nào* và *có thể tìm hết rule không*.
> Mọi con số đã đo, script tái tạo được.

---

## 1. Ký hiệu

Cho corpus $\mathcal{D}$ gồm các cặp sự kiện. Mỗi cặp $x = (a,b)$ mang:

- **nhãn** $y(x) \in \mathcal{R} = \{$BEFORE, CONTAINS, SIMULTANEOUS, OVERLAP, BEGINS-ON, ENDS-ON$\}$
- **tập điều kiện đúng** $\Phi(x) \subseteq \mathcal{C}$, với $\mathcal{C}$ là vũ trụ điều kiện

Một **rule** là cặp $(\varphi, r)$ trong đó $\varphi \subseteq \mathcal{C}$ là hội điều kiện và
$r \in \mathcal{R}$. Rule **bắn** trên $x$ khi $\varphi \subseteq \Phi(x)$.

Ký hiệu tập phủ và tập đúng:

$$\text{cov}(\varphi) = \{x : \varphi \subseteq \Phi(x)\}, \qquad
\text{cor}(\varphi, r) = \{x \in \text{cov}(\varphi) : y(x) = r\}$$

$$n = |\text{cov}(\varphi)|, \qquad k = |\text{cor}(\varphi, r)|$$

---

## 2. Vì sao không dùng confidence, và vì sao không dùng lift

**Confidence** $= k/n$ vô dụng: base rate BEFORE là 91,05%, nên rule rỗng đã đạt
confidence 0,91. Mọi rule đều "tốt".

**Lift** $= \dfrac{k/n}{P(r)}$ sửa được base rate nhưng **thưởng nhiễu**: một pattern với
$k=5, n=5$ cho lift $= 1/0{,}0086 = 116\times$ cho SIMULTANEOUS — chỉ là may.

**Wilson lower bound** phạt mẫu nhỏ:

$$\text{wlb}(k,n) = \frac{\hat{p} + \frac{z^2}{2n} - z\sqrt{\frac{\hat p(1-\hat p)}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}},
\qquad \hat p = k/n,\ z = 1{,}96$$

| $k$ | $n$ | $\hat p$ | wlb |
|---:|---:|---:|---:|
| 5 | 5 | 1,00 | 0,57 |
| 50 | 60 | 0,83 | 0,72 |
| 500 | 600 | 0,83 | 0,80 |

Đo được: xếp hạng bằng wlb cho **7,96%** precision, bằng lift chỉ **2,76%** — chênh 2,9×.

---

## 3. Base rate cục bộ — tám view

Một **view** là hàm phân hoạch $v: \mathcal{X} \to \Sigma_v$. Rule mine trong lớp
$\sigma \in \Sigma_v$ được chấm theo base rate **của chính lớp đó**:

$$\text{lift}_v(\varphi, r, \sigma) = \frac{|\text{cor}(\varphi,r) \cap v^{-1}(\sigma)|\,/\,|\text{cov}(\varphi) \cap v^{-1}(\sigma)|}{P(y = r \mid v(x) = \sigma)}$$

Điều này quan trọng: rule "cùng câu ⇒ CONTAINS" có lift cao toàn cục nhưng lift ≈ 1 **trong
lớp các cặp cùng câu** — tức nó không nói thêm gì.

> **Chữ ký lớp phải nằm trong khoá rule.** Bỏ nó đi từng gây precision giả **70,52%**: 333
> rule mine trong một lớp con bỗng áp dụng toàn corpus, và chúng đều đoán BEFORE.

---

## 4. Không gian tìm kiếm — đếm ngây thơ, rồi đếm đúng

Đo trên 400 document (111.114 cặp):

| | Số lượng |
|---|---:|
| Điều kiện phân biệt $\|\mathcal{C}\|$ | 19.224 |
| Có support ≥ 25 | **1.808** |

Số hội theo độ sâu:

$$\binom{1808}{1} = 1{,}8 \times 10^3, \qquad
\binom{1808}{2} = 1{,}63 \times 10^6, \qquad
\binom{1808}{3} = 9{,}83 \times 10^8$$

Beam search với `beam=220, depth=3` thăm khoảng $220 \cdot 1808 + 220^2 \approx 4{,}46 \times 10^5$
ứng viên — **0,045%** không gian depth-3.

### 4.1. Đếm lại — không gian nhỏ hơn hàng bậc

Cách đếm trên **sai**, vì nó coi mỗi điều kiện là một biến độc lập. Thực tế 1.143 điều kiện
(support ≥ 25, đo trên 200 document) gom thành **19 biến đa trị**, và các giá trị trong một
biến **loại trừ lẫn nhau**: `type_a=Attack` và `type_a=Killing` không bao giờ cùng đúng.

| Biến | Số giá trị |
|---|---:|
| `type_pair` | 322 |
| `type_a` | 154 |
| `type_b` | 152 |
| `nrole_a`, `nrole_b` | 6 |
| `sdist` | 5 |
| còn lại (13 biến) | ≤ 4 |
| **không phải EQ** (HAS/ALL/CNT/MIX) | 467 điều kiện độc lập |

Gọi $A_1,\dots,A_{19}$ là các biến và $F$ là tập điều kiện độc lập. Số hội **hợp lệ** ở
depth-$d$ là tổng tích trên các biến **khác nhau**:

$$N_d = \sum_{j=1}^{d} \sum_{1 \le i_1 < \dots < i_j \le 19} \left( \prod_{t=1}^{j} |A_{i_t}| \right) \binom{|F|}{d-j}$$

Kết quả:

| Độ sâu | $\binom{n}{d}$ ngây thơ | Hợp lệ | Cắt bỏ |
|---|---:|---:|---:|
| 2 | 652.653 | **577.650** | 11,5% |
| **3** | 248.225.691 | **14.072.484** | **94,3%** |

> **Depth-3 là 14 triệu ứng viên, không phải $10^9$.** Nên **vét cạn depth-3 cũng khả thi**,
> và "đã tìm hết rule" trở thành phát biểu kiểm chứng được ở cả hai độ sâu.

### 4.2. Vì sao BDD không phải công cụ đúng, nhưng ý tưởng thì đúng

Ý tưởng dùng decision diagram là **đúng hướng** — nó chính là thứ phát hiện ra cấu trúc trên.
Nhưng cần phân biệt:

| | Phù hợp |
|---|---|
| **BDD** | biến Boolean. Ở đây phải mã hoá 1.143 biến Boolean **cộng** ràng buộc loại trừ — lãng phí |
| **MDD** | biến đa trị: mỗi node một biến, mỗi cạnh một giá trị. **Khớp trực tiếp** với 19 biến |
| **ZDD** | nén họ tập hợp thưa. Đo được: **90,7%** tập điều kiện là phân biệt ⇒ ít chia sẻ, không nén được nhiều |

Và điều decision diagram **không** làm được: wlb là một **thống kê**, không phải vị từ Boolean.
Diagram liệt kê miền hợp lệ hiệu quả, nhưng không trả lời được *"pattern nào tương quan với
nhãn"* — phần đó vẫn phải quét dữ liệu.

**Nên kiến trúc đúng là:** MDD (hoặc phép đếm tương đương) để sinh miền hợp lệ, bitset để tính
$\text{cov}$, wlb để chấm điểm. `cov` giữ nguyên bitset vì phép giao trên 483k bit đã nhanh và
mức chia sẻ quá thấp để ZDD có lợi.

---

## 5. Ba tính chất đại số cho phép cắt tỉa an toàn

### 5.1. Đơn điệu của support (anti-monotone)

$$\varphi \subseteq \psi \implies \text{cov}(\psi) \subseteq \text{cov}(\varphi)
\implies n(\psi) \le n(\varphi)$$

Nên nếu $n(\varphi) < \text{sup}_{\min}$ thì **mọi** mở rộng của $\varphi$ cũng dưới ngưỡng.
Đây là cơ sở cắt tỉa kiểu Apriori — **cắt an toàn, không mất rule nào**.

### 5.2. Trần của wlb theo support

Với $k \le n$, giá trị wlb lớn nhất đạt khi $k = n$:

$$\text{wlb}(k,n) \le \text{wlb}(n,n) = \frac{1}{1 + z^2/n}$$

Nên một nhánh có $n = 25$ **không bao giờ** vượt $\text{wlb} = 0{,}867$, còn $n = 10$ chặn ở
0,723. Cho phép cắt theo ngưỡng wlb mục tiêu **mà không mất rule nào** — đây là điều beam
search hiện tại **chưa khai thác**.

### 5.3. Dư thừa theo phủ

Nếu $\text{cov}(\varphi) = \text{cov}(\psi)$ thì hai rule không phân biệt được trên dữ liệu
này, dù biểu thức khác nhau. Gom theo chữ ký phủ giảm 155.124 rule xuống **7.103** lớp phủ
phân biệt — **giảm 95,4% mà không mất thông tin**.

---

## 6. Ba chỗ còn tìm được thêm — xếp theo kỳ vọng

### 6.1. Vét cạn depth-2 *(khả thi, đo được ngay)*

Beam có thể bỏ sót hội depth-2 nếu **cả hai** điều kiện thành phần đều yếu đơn lẻ nhưng
mạnh khi kết hợp. Beam xếp hạng tầng 1 theo support rồi chỉ giữ 220 — một điều kiện hiếm
nhưng sắc bén sẽ bị loại trước khi kịp ghép.

Về hình thức, beam bỏ sót $(\varphi_1, \varphi_2)$ khi:

$$\varphi_1 \notin \text{top}_{220} \ \lor\ \varphi_2 \notin \text{top}_{220},
\quad \text{nhưng} \quad \text{wlb}(\varphi_1 \wedge \varphi_2) \gg \max_i \text{wlb}(\varphi_i)$$

Đây là **tương tác**, và nó chính là loại pattern đáng quan tâm nhất.

### 6.2. Phủ định — ngôn ngữ hiện tại không có

Mọi điều kiện đều dạng khẳng định. Không có `NOT(sdist=0)` hay `NOT HAS(role, Agent)`.

Với 6 nhãn lệch mạnh, phủ định có thể mạnh hơn khẳng định: *"không cùng câu VÀ không chung
anchor ⇒ BEFORE"* là loại rule ngôn ngữ hiện tại không biểu diễn được.

### 6.3. Điều kiện quan hệ giữa hai sự kiện

Hiện chỉ có đặc trưng của $a$, của $b$, và vài đặc trưng cặp. Thiếu **so sánh**:
`type_a == type_b`, `\|sent_a - sent_b\| ≤ 2`, `roleset_a ⊇ roleset_b`.

Đo được từ dữ liệu có sẵn, không cần mine lại từ đầu.

---

## 7. Điều đại số **không** bảo đảm

**Wilson lower bound không kiểm định nhân quả.** Nó chỉ nói $\varphi$ liên quan tới $r$.

Đã đo một ví dụ: rule `ev_type=Attack AND sdist=0 → CONTAINS` có wlb cao, nhưng so với chỉ
`sdist=0`:

| Rule | Precision valid | Vượt `sdist=0` |
|---|---:|---:|
| `Use_firearm AND sdist=0` | 90,00% | **+30,71** |
| `Attack AND sdist=0` | 59,42% | **+0,13** |
| `Competition AND sdist=0` | 58,24% | **−1,05** |

Hai rule cuối **không mang thông tin** ngoài `sdist=0`. Đại số không phát hiện được điều này
— phải đo trực tiếp bằng cách so với rule con.

> Cần thêm một phép kiểm: rule $\varphi$ chỉ được giữ nếu
> $\text{wlb}(\varphi) > \max_{\psi \subset \varphi} \text{wlb}(\psi) + \epsilon$.
> Gọi là **kiểm tra đóng góp biên**. Chưa cài.

---

## 8. Ba định lý cắt tỉa — thay brute-force bằng bất đẳng thức

Cài ở `src/mine_mdd.py`. Đo trên 200 document, 1.161 điều kiện, mục tiêu wlb ≥ 0,40.

### 8.1. Định lý 1 — trần theo support

$$\text{wlb}(k,n) \le \text{wlb}(n,n) = \frac{1}{1 + z^2/n}$$

wlb tăng theo $k$ với $n$ cố định, nên cực đại tại $k=n$. Support chặn điểm số: $n=25$ không
bao giờ vượt 0,867.

### 8.2. Định lý 2 — trần theo số đúng (chặt hơn)

$$\text{wlb}(k,n) \le \text{wlb}(k,k)$$

Với $k$ cố định, wlb **giảm** theo $n$: thêm instance phủ mà không đúng chỉ làm giảm
$\hat p$. Nên trần chỉ phụ thuộc $k$, **không phụ thuộc $n$**.

Kết hợp với tính phản đơn điệu của $k$:

$$k(\varphi \wedge \psi, r) \le \min\big(k(\varphi,r),\, k(\psi,r)\big)$$

ta loại được một cặp **chỉ từ số đếm của hai nhánh cha**:

$$\text{wlb}(\varphi \wedge \psi, r) \le \text{wlb}(m,m), \quad m = \min(k_\varphi, k_\psi)$$

Không cần giao bitset, không chạm dữ liệu. Đo được: loại **50,53%** số cặp; loại trừ lẫn
nhau loại thêm **11,49%**; còn **37,98%** phải tính.

| $k$ | $\text{wlb}(k,k)$ |
|---:|---:|
| 1 | 0,207 |
| 2 | 0,342 |
| **3** | **0,439** |
| 5 | 0,566 |
| 10 | 0,723 |
| 20 | 0,839 |

### 8.3. Định lý 3 — sắp xếp rồi dừng sớm

Sắp điều kiện theo $k(\cdot, r)$ **giảm dần**. Với $\varphi$ cố định, cận
$\text{wlb}(\min(k_i,k_j), \min(k_i,k_j))$ **không tăng** theo $j$.

Nên $j$ đầu tiên không đạt ngưỡng thì **mọi** $j' > j$ cũng vậy ⇒ `break`, không `continue`.
Vòng lặp dừng ở biên thay vì quét hết: $O(n\log n + |\text{survivors}|)$ thay vì $O(n^2)$.

### 8.4. Kết quả đo

| Nhãn | Nhánh sống sót | Cặp phải xét | % một lần vét cạn |
|---|---:|---:|---:|
| CONTAINS | 732 | 248.363 | 36,88% |
| SIMULTANEOUS | 409 | 80.302 | 11,93% |
| OVERLAP | 350 | 58.961 | 8,76% |
| BEGINS-ON | 149 | 10.953 | 1,63% |
| **ENDS-ON** | **27** | **351** | **0,05%** |

> **Cả năm quan hệ cộng lại = 0,592× một lần vét cạn duy nhất.** Và cận chặt nhất đúng ở
> **nhãn hiếm nhất** — ENDS-ON giảm **1.918×** — vì Định lý 2 chặn theo $k$, mà nhãn hiếm
> thì $k$ nhỏ.

### 8.5. So với miner cũ

| | Beam (cũ) | **MDD + định lý** |
|---|---:|---:|
| Khám phá không gian | 0,045% | **vét cạn depth-2** |
| Rule giữ lift≥1,5 trên valid | 70,1% | **91,1%** (762/836) |
| wlb cao nhất | 0,598 | **0,925** |
| Rule dùng điều kiện quan hệ | 0 | **75** |

Rule mạnh nhất: `multi_mention_a=True AND type_a=Military_operation → CONTAINS`,
**78,82% precision trên valid, lift 9,23×** ($n=170$, $k=134$).

**91,1% sống sót hold-out** so với 70,1% của miner cũ — vì phép kiểm đóng góp biên đã loại
rule giả **trước** khi báo cáo, thay vì để hold-out phát hiện sau.

### 8.6. Điều định lý **không** làm được

Cả ba định lý đều là **cận trên của wlb**, nên chúng chỉ nói *"nhánh này không thể tốt"*.
Chúng **không** nói nhánh nào tốt — phần đó vẫn phải tính $\text{cov}$ và đếm.

Và chúng không thay được hold-out: rule `etypeset_b=Product AND type_a=Recording` đạt wlb
0,883 trên train nhưng valid chỉ có $n=4$ — quá nhỏ để kết luận. Cận toán học không biết
mẫu sẽ nhỏ đến đâu ở tập khác.

---

## 9. Nhánh dưới (depth-3) — Định lý 4 và giới hạn của nó

### 9.1. Định lý 4 — nâng cận từ tầng dưới

Mở rộng ngây thơ chặn bộ ba bằng ba điều kiện đơn:

$$k(a \wedge b \wedge c) \le \min(k_a, k_b, k_c)$$

**Vô dụng** — min của ba hầu như không nhỏ hơn min của hai. Cận có ích tái dùng tầng dưới,
nơi số đếm **đã biết chính xác**:

$$k(a \wedge b \wedge c) \le \min\big(k(a \wedge b),\; k_c\big)$$

Ví dụ số với $k_a = 200$, $k_b = 180$, $k_c = 150$, $k(a \wedge b) = 12$:

| Cận | Giá trị | Ở ngưỡng 0,80 |
|---|---:|---|
| ngây thơ $\text{wlb}(150,150)$ | 0,975 | không cắt |
| **nâng tầng** $\text{wlb}(12,12)$ | **0,757** | **cắt** |

### 9.2. Đo được — cận cắt sạch 4 nhãn nhưng **không cắt được CONTAINS**

| Nhãn | Depth-2 | Depth-3 |
|---|---:|---:|
| CONTAINS | 159.172 | **364.315** |
| SIMULTANEOUS | 42.813 | **0** |
| OVERLAP | 32.547 | **0** |
| BEGINS-ON | 3.310 | **0** |
| ENDS-ON | 66 | **0** |

Bốn nhãn hiếm bị cắt **hoàn toàn** — không bộ ba nào qua được cận. Nhưng CONTAINS thì tầng 3
còn **lớn hơn** tầng 2, vì $k(a \wedge b)$ của nó vẫn lớn nên $\text{wlb}(k,k)$ luôn trên ngưỡng.

### 9.3. Định lý 5 — đúng về logic, **vô dụng trong thực tế**

Thử chặn bằng chính yêu cầu đóng góp biên. Bộ ba chỉ được báo nếu
$\text{wlb}(abc) > \text{wlb}(ab) + \epsilon$, mà Định lý 2 cho
$\text{wlb}(abc) \le \text{wlb}(k_{ab}, k_{ab})$, nên điều kiện cần là:

$$\text{wlb}(k_{ab}, k_{ab}) > \text{wlb}(k_{ab}, n_{ab}) + \epsilon$$

**Đo trên cặp thật: không bao giờ kích hoạt.** $\text{wlb}(k,k)$ luôn cách xa
$\text{wlb}(k,n)$ ở mọi support quan sát được:

| $k_{ab}$ | $n_{ab}$ | $\text{wlb}$ thực | trần $\text{wlb}(k,k)$ | còn chỗ? |
|---:|---:|---:|---:|---|
| 10 | 12 | 0,552 | 0,722 | có |
| 30 | 35 | 0,706 | 0,886 | có |
| 100 | 110 | 0,841 | 0,963 | có |

Nên **không dùng được** làm cận cắt tỉa. Ghi lại để không ai thử lại.

### 9.4. Kết luận trung thực về tính đầy đủ

> **Depth-2 vét cạn được và chứng minh được. Depth-3 thì không.**
>
> Cài đặt hiện tại giới hạn frontier ở $M$ cặp tốt nhất mỗi quan hệ — đó là **heuristic**,
> không phải chứng minh. Code in cảnh báo này ở mỗi lần chạy depth-3.

Kết quả depth-3 (150 doc, target 0,65, frontier 300): **2.481 rule depth-3**, 92,4% giữ
lift ≥ 1,5 trên valid. Nhưng cột `gain` chỉ **0,026–0,037** — sát ngưỡng $\epsilon = 0{,}02$,
tức đóng góp biên rất mỏng. Phần lớn là `order=fwd` ghép thêm vào cặp đã tốt sẵn.

---

## 10. Kết quả cuối — toàn corpus

`python mine_mdd.py --limit 0 --target-wlb 0.40 --out rules_mdd`

| | Giá trị |
|---|---:|
| Rule tìm được | **2.927** |
| Công so với một lần vét cạn | **0,185×** |
| Loại không chạm dữ liệu (loại trừ lẫn nhau) | 1.553.062 |
| Loại sau khi giao (thin / low-k / no-gain) | 3.039.189 / 177.867 / 1.374 |
| Giữ lift ≥ 1,5 trên valid | **2.099 / 2.927 = 71,7%** |
| Dùng điều kiện quan hệ | 337 |

**Theo nhãn:**

| Nhãn | Nhánh | Cặp xét | % một lần vét cạn |
|---|---:|---:|---:|
| CONTAINS | 2.847 | 2.585.892 | 13,51% |
| SIMULTANEOUS | 1.098 | 548.960 | 2,87% |
| OVERLAP | 888 | 360.521 | 1,88% |
| BEGINS-ON | 272 | 35.996 | 0,19% |
| ENDS-ON | 187 | 17.178 | **0,09%** |

**Cảnh báo về mẫu nhỏ:** 763/2.927 rule (**26,1%**) có $n < 10$ trên valid — không kết luận
được, và chính chúng là các dòng "0,00%" trong bảng top. Trên nhóm $n \ge 10$ (2.164 rule),
**2.143 rule có ít nhất một hit**.

Rule tốt nhất có $n \ge 10$ trên valid:

| Valid P | $n$ | $k$ | Rule |
|---:|---:|---:|---|
| **100,00%** | 10 | 10 | `bucket_a=lead AND type_pair=(Military_operation, Defending)` |
| 92,86% | 14 | 13 | `bucket_a=lead AND type_pair=(Military_operation, Motion)` |
| 92,31% | 13 | 12 | `bucket_a=lead AND type_pair=(Hostile_encounter, Damaging)` |
| 92,00% | 25 | 23 | `bucket_a=lead AND type_pair=(Catastrophe, Attack)` |

Tất cả đều đoán CONTAINS và đều đọc được bằng tiếng người.

---

## 11. Gộp hai bộ rule — macro-F1 **24,61%**, kết quả C2 tốt nhất

`python vote.py --rules families.json,rules_mdd.json --tau-sweep` trên toàn valid
(109.929 cặp).

| Nhãn | Hằng số | families (1.453) | **gộp (4.380)** |
|---|---:|---:|---:|
| BEFORE | 94,70% | 89,70% | 93,72% |
| CONTAINS | 0% | 32,78% | **33,25%** |
| SIMULTANEOUS | 0% | 11,88% | **14,60%** |
| OVERLAP | 0% | 6,55% | 6,09% |
| BEGINS-ON / ENDS-ON | 0% | 0% | 0% |
| **Macro-F1** | **15,78%** | 23,49% | **24,61%** |
| Accuracy | 89,94% | 80,98% | **88,05%** |

**+8,83 điểm so với hằng số**, và **+1,12 điểm** so với `families.json` một mình. Đáng chú ý
là accuracy cũng tăng (80,98% → 88,05%) — thường hai chỉ số này đánh đổi nhau.

### 11.1. Vì sao gộp lại có tác dụng — hai bộ bù nhau

| | `families.json` | `rules_mdd.json` |
|---|---|---|
| Rule | 1.453 | 2.927 |
| CONTAINS | 1.033 | **2.927** (wlb tới 0,947) |
| SIMULTANEOUS | **279** | 0 |
| OVERLAP | **141** | 0 |
| Cách mine | beam, 8 view | vét cạn depth-2, 3 định lý |

`rules_mdd` cho CONTAINS sắc hơn; `families` là nguồn **duy nhất** có SIMULTANEOUS và
OVERLAP. Bỏ bộ nào cũng mất một nửa bài toán.

### 11.2. Hạn chế của bộ MDD: chỉ ra rule CONTAINS

Ở `target-wlb 0.40`, bốn nhãn còn lại xét hàng trăm nghìn cặp nhưng **giữ 0 rule**:

| Nhãn | Nhánh | Cặp xét | Rule giữ |
|---|---:|---:|---:|
| CONTAINS | 2.847 | 2.585.892 | **2.927** |
| SIMULTANEOUS | 1.098 | 548.960 | **0** |
| OVERLAP | 888 | 360.521 | **0** |
| BEGINS-ON | 272 | 35.996 | **0** |
| ENDS-ON | 187 | 17.178 | **0** |

Không phải cận cắt nhầm — chúng được xét đầy đủ rồi **không cặp nào đạt wlb ≥ 0,40**. Đây là
cùng một sự thật đã đo ở §15.1: SIMULTANEOUS có wlb cao nhất 0,141.

### 11.3. Hai sửa đổi cần cho `vote.py`

1. **Sinh điều kiện quan hệ** (`relational_conditions`) — thiếu thì 337 rule chứa `REL:*`
   không bao giờ bắn được
2. **Nhận nhiều file rule** và gộp

### 11.4. Trần oracle vẫn xa

24,61% đóng được **5%** khoảng cách tới oracle 65,85% (từ 22,57%). Vẫn nên nhớ: phần lớn
khoảng cách đó là thông tin chỉ tồn tại khi đã biết nhãn — **đừng trích 65,85% như headroom**.
