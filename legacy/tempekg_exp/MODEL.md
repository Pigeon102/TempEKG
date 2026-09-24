# TempEKG — Mô hình toán học
**30/08/2026 · nền tảng hình thức cho framework, viết TRƯỚC khi chạy tiếp**

---

## 1. Đối tượng toán học thật sự là gì

### 1.1 Thú nhận: chưa có graph nào được xây

Trong EXP2–EXP4, cấu trúc duy nhất tồn tại là:

```python
ev[eid] = {'type':…, 'ents': set(entity_id), 'roles': {entity_id: set(role)}}
shared  = ev[a]['ents'] & ev[b]['ents']
```

Không adjacency list, không vertex object, không hyperedge object. Đây là **giao tập
thuộc tính**, không phải duyệt đồ thị. Graph đang *ngầm định*. Mục 1.2 nói rõ nó là gì.

### 1.2 Cấu trúc thật: siêu đồ thị có nhãn vai (role-labeled hypergraph)

Với mỗi document $d$:

- $\mathcal{X}_d$ — tập **entity** (đỉnh)
- $\mathcal{E}_d$ — tập **event** (siêu cạnh)
- $R$ — tập vai, $|R| = 143$
- $T$ — tập kiểu event, $|T| = 168$

Hai ánh xạ:

$$\tau : \mathcal{E}_d \to T \qquad\text{(kiểu event)}$$
$$\iota : \mathcal{E}_d \times R \to 2^{\mathcal{X}_d} \qquad\text{(vai → tập entity lấp vai đó)}$$

**Tập tham dự** của một event:
$$P(e) \;=\; \bigcup_{r \in R} \iota(e, r) \;\subseteq\; \mathcal{X}_d$$

Vậy **một event *là* một siêu cạnh có nhãn vai**: nó không chỉ là tập con $P(e)$ của
$\mathcal{X}_d$, mà là một hàm bộ phận $R \rightharpoonup 2^{\mathcal{X}_d}$. Đây chính
là định nghĩa của một **hyper-relational fact** / thể hiện quan hệ n-ngôi.

### 1.3 PaTeCon là trường hợp riêng — phát biểu hình thức

Một statement của PaTeCon là $(s, p, o)$ + khoảng thời gian. Trong ngôn ngữ trên:

$$\text{PaTeCon} \;=\; \text{trường hợp } |P(e)| = 2 \text{ với } R = \{\mathsf{subj}, \mathsf{obj}\}$$

$$\iota(e, \mathsf{subj}) = \{s\}, \quad \iota(e, \mathsf{obj}) = \{o\}, \quad \tau(e) = p$$

> **Mệnh đề 1.** Mô hình reified eVertex/sVertex của PaTeCon là hạn chế của siêu đồ thị
> có nhãn vai xuống **bậc đúng bằng 2** với vai cố định $\{\mathsf{subj},\mathsf{obj}\}$.
> `sVertex` = siêu cạnh; `eVertex` = đỉnh; `hasItem`/`hasValue` = hai incidence.

Đây là phát biểu chính xác của câu "event node = sVertex mở rộng n-ary" đã dùng trước đó.
Hệ quả: **thời gian gắn với siêu cạnh, không gắn với incidence** — nên chiếu event làm
subject làm mọi vị từ suy biến (mọi incidence của một event chia sẻ đúng một khoảng).

### 1.4 Phép chiếu đồng-tham-dự

Định nghĩa đồ thị $G_d^{(k)}$ trên tập đỉnh $\mathcal{E}_d$:

$$(e, f) \in G_d^{(k)} \iff |P(e) \cap P(f)| \ \ge\ k$$

- $k = 1$: **one-mode projection** chuẩn của siêu đồ thị — đúng thứ SP(a) chạm tới
- $k = 2$: chính là SP(c)

Đã đo: $|G^{(1)}| = 212{,}743$, $|G^{(2)}| = 42{,}064$ (19.8%).

### 1.5 Vì sao SP(a)/SP(b) không diễn đạt được $k \ge 2$

Trong đồ thị incidence hai phía (entity ↔ event):

- SP(a) khớp một **cherry** gốc tại $x$: $e_1 \leftarrow x \rightarrow e_2$
- SP(b) khớp hai cherry nối nhau bởi một cạnh phi thời gian $x \to y$
- SP(c) đòi $\{x,y\} \times \{e_1,e_2\}$ — tức một **$K_{2,2}$ đầy đủ** trong đồ thị incidence

> **Mệnh đề 2.** Ngôn ngữ pattern chỉ ràng buộc **một** biến subject (SP(a)) hoặc một cặp
> subject *nối với nhau* (SP(b)) không thể diễn đạt $K_{2,2}$, vì $K_{2,2}$ đòi hai biến
> subject **độc lập** (không có cạnh giữa chúng) cùng incident tới **cùng** hai siêu cạnh.

Đây là lý do hình thức để giữ biểu diễn hyperedge — không phải sở thích kỹ thuật.

---

## 2. Bài toán mining, phát biểu hình thức

### 2.1 Nhãn và signature

$\rho : \mathcal{E}_d \times \mathcal{E}_d \to L \cup \{\bot\}$ — quan hệ thời gian gold,
$\bot$ = không có quan hệ. Cặp luôn sắp theo **thứ tự văn bản**, nên $L$ có hướng:
$L = \{\textsf{BEFORE\_FWD}, \textsf{BEFORE\_REV}, \textsf{CONTAINS\_FWD}, \dots\}$, $|L| = 7$.

Hai hàm signature:
$$\sigma_{\text{type}}(a,b) = (\tau(a), \tau(b))$$
$$\sigma_{\text{role}}(a,b,x) = (\tau(a),\, r_a,\, \tau(b),\, r_b), \quad x \in \iota(a,r_a) \cap \iota(b,r_b)$$

### 2.2 Mining = ước lượng phân phối có điều kiện

$$\hat p(\ell \mid \sigma) \;=\; \frac{\#\{(a,b) \in \mathcal{D}_{\text{mine}} : \sigma(a,b)=\sigma,\ \rho(a,b)=\ell\}}{\#\{(a,b) \in \mathcal{D}_{\text{mine}} : \sigma(a,b)=\sigma,\ \rho(a,b) \ne \bot\}}$$

**Constraint** = signature $\sigma$ thoả:
$$\operatorname{supp}(\sigma) \ge \theta_{\text{freq}} \quad\wedge\quad \max_{\ell} \hat p(\ell \mid \sigma) \ \ge\ \theta_{\text{conf}}$$

### 2.3 "Pattern đúng" — định nghĩa hình thức

Ý tưởng *"mine pattern đúng rồi tìm contradiction"* trở thành một mệnh đề tổng quát hoá:

> Signature $\sigma$ **được xác nhận** nếu $\hat p$ ước lượng trên $\mathcal{D}_{\text{mine}}$
> giữ được trên $\mathcal{D}_{\text{eval}}$ độc lập, tức
> $$\hat p_{\text{eval}}(\ell^\star \mid \sigma) \ \ge\ \theta_{\text{hold}}, \qquad \ell^\star = \arg\max_\ell \hat p_{\text{mine}}(\ell \mid \sigma)$$

**Contradiction** khi đó có định nghĩa chặt: instance $(a,b)$ với $\sigma(a,b)=\sigma$ đã
xác nhận, nhưng $\rho(a,b) \ne \ell^\star$.

Đo được (EXP3): $\theta_{\text{conf}}=0.9 \Rightarrow \hat p_{\text{eval}} = 86.1\%$ so với
lớp đa số $69.3\%$.

### 2.4 Dàn tinh chỉnh (refinement lattice)

Không gian signature là **tích của hai trục tinh chỉnh**, sắp thứ tự bộ phận bởi quan hệ
"tổng quát hơn" $\sqsupseteq$:

$$(\tau_a, \tau_b) \ \sqsupseteq\ (\tau_a, r_a, \tau_b, r_b) \qquad \text{[trục vai]}$$
$$k=1 \ \sqsupseteq\ k=2 \qquad \text{[trục đồng-tham-dự]}$$

> **Mệnh đề 3.** PaTeCon tinh chỉnh theo **một** trục (class restriction trên biến). Ở đây
> trục đó gần vô dụng vì $|{\text{entity type}}| = 7$ và rất thô. Trục đồng-tham-dự ($k$)
> chỉ tồn tại khi bậc siêu cạnh không bị chặn ở 2 — tức **chỉ có ở mô hình n-ary**.

Mining = tìm trong dàn này những nút mà phân phối có điều kiện **tập trung**. Đo bằng
entropy chuẩn hoá $H_{\text{norm}}(\sigma) = H(\hat p(\cdot\mid\sigma)) / \log_2 |{\rm supp}|$.

Đã đo: $H_{\text{norm}}(k{=}1) = 0.524 \to H_{\text{norm}}(k{=}2) = 0.455$. Tinh chỉnh theo
$k$ **làm giảm entropy** → đúng hướng, đúng thứ dàn cần.

---

## 3. Học được gì từ PaTeCon — ánh xạ chính xác

| Thành phần PaTeCon | Vai trò hình thức | Có dùng lại? |
|---|---|---|
| **Logic ba trị** pos/neg/**unknown**, bỏ unknown | Làm ước lượng có điều kiện trên *tính đo được*: $\hat p(\ell \mid \sigma, \text{measurable})$. Ngăn instance không đo được làm bẩn thống kê. | ✅ **Dùng nguyên** — thiết yếu vì 55% event thiếu anchor |
| **support/confidence + refinement ladder** | Kiểm định giả thuyết phân tầng: mine thô, chuyên biệt hoá khi ước lượng chưa kết luận được | ✅ **Dùng khung, đổi dàn** (§2.4) |
| **Cấu trúc pattern → predicate → score** | Kiến trúc pipeline | ✅ Dùng lại |
| **entity-level confidence** | Gom subgraph theo entity; entity dương chỉ khi *mọi* subgraph dương | ❌ **Suy biến** — 0/68,348 entity vượt document nên nó bằng fact-level |
| **PaTeCon+ two-stage pruning** | Cắt tỉa theo luật số lớn để chạy trên 27M fact | ❌ **Không cần** — $\lvert R\rvert^2 = 425{,}104 \approx 0.1$ GB |
| **SP(a)** | cherry gốc tại subject | ✅ = $k{=}1$ |
| **SP(b)** | hai subject nối bởi cạnh phi thời gian | ✅ → **kênh C2** (causal/subevent chính là "cạnh phi thời gian" nối hai event) |

**Điều PaTeCon dạy mà dễ bỏ sót:** giá trị cốt lõi không nằm ở năm vị từ hay hai structural
pattern, mà ở **việc tách rời "đo được" khỏi "đúng/sai"** (logic ba trị). Trên substrate
thiếu thời gian như MAVEN, đó là thứ giữ cho toàn bộ thống kê không sụp.

---

## 4. Mô hình chỉ ra ba lỗ hổng trong kết quả hiện tại

Viết mô hình xong thì lộ ra ba điểm mà EXP3 **chưa** kiểm soát. EXP4 kiểm tra cả ba.

### 4.1 Ước lượng plug-in không có khoảng tin cậy

$\hat p$ là MLE cắm thẳng. Với $\text{supp} = 10$ và $\hat p = 0.9$ (tức 9/10), khoảng tin
cậy Wilson 95% xấp xỉ $[0.60,\ 0.98]$ — **gần như vô giá trị**. Ngưỡng $\theta_{\text{freq}}=10$
của PaTeCon quá lỏng cho tuyên bố "pattern đúng".

→ Phải thay $\hat p \ge \theta$ bằng **cận dưới Wilson** $\ge \theta$.

### 4.2 Kiểm định bội (multiple testing)

Ta test $\approx 12{,}047$ signature ở mức type. 403 cái qua $\theta = 0.9$. Nếu nhãn hoàn
toàn ngẫu nhiên thì **bao nhiêu cái vẫn qua do may rủi**? Chưa biết.

→ Cần **permutation null**: hoán vị nhãn *trong từng document*, đếm số signature qua ngưỡng.
Cho ước lượng FDR trực tiếp.

### 4.3 Phụ thuộc trong document — nghiêm trọng nhất

Các cặp trong cùng một document **không độc lập**. Một bài về chiến tranh với 30 event sinh
~400 cặp, tất cả tương quan (cùng timeline, cùng nhân vật). Nên **effective sample size $\ll$
support danh nghĩa**, và mọi khoảng tin cậy tính theo số cặp đều **hẹp giả tạo**.

> **Mệnh đề 4.** Đơn vị độc lập trên substrate này là **document**, không phải cặp event.
> Support phải đếm theo document.

Đây cũng là điều mà entity-locality đã ngụ ý: vì entity không vượt document, mọi phụ thuộc
thống kê bị chặn trong document → document là khối độc lập tự nhiên.

---

## 5. Thí nghiệm tiếp theo, suy ra từ mô hình

| # | Suy ra từ | Nội dung |
|---|---|---|
| EXP4 | §4.1–4.3 | Audit: phân phối support · Wilson lower bound · permutation null · support theo document · macro vs micro |
| EXP5 | §1.3, C2 | Kênh C2: ràng buộc **cứng** trên causal/subevent — phủ 58,033 cặp, không cần ngưỡng |
| EXP6 | §2.4 | Tìm kiếm trên dàn tinh chỉnh: có luật đơn điệu nào để cắt tỉa không (kiểu Apriori) |

---

## 6. Kết quả EXP4 — mô hình đoán đúng 2/3

### §4.1 Khoảng tin cậy: ✅ **vấn đề có thật, nghiêm trọng**

```
support: min=10  median=14  max=150
  58% signature co support <= 15
  87% signature co support <= 30
Wilson 95% lower bound: median = 0.74
  chi 4 / 403 signature co lower bound >= 0.9
  33 signature co lower bound < 0.6
```

Ngưỡng $\theta_{\text{freq}}=10$ của PaTeCon **quá lỏng**. Tuyên bố "conf ≥ 0.9" hầu như
không signature nào chống đỡ được ở mức 95%.

### §4.2 Kiểm định bội: ✅ **vấn đề có thật, đây là phát hiện lớn nhất**

```
quan sat that : 403 signature qua nguong
ky vong NULL  : 139.8   (hoan vi nhan trong document, 5 lan: 142/157/141/128/131)
=> FDR ~ 34.7%
=> so signature THAT ~ 263
```

**Một phần ba "constraint" là ngẫu nhiên.** Không có bước này thì 403 con số đó bị báo cáo
như thể đều là quy luật.

### §4.3 Phụ thuộc document: ❌ **lo hão**

```
so DOCUMENT dong gop / signature: min=1  median=10  max=97
  chi 1 signature den tu 1 document  (0%)
  chi 7 signature den tu <=3 document (2%)
```

Signature rút từ trung vị 10 document khác nhau. Mệnh đề 4 vẫn đúng về nguyên tắc, nhưng
**thực nghiệm không bị ảnh hưởng** — hiệu ứng thổi phồng nhỏ.

### §D Độ vững của 86.1%: ✅ **vững**

```
micro (trong so theo do phu) : 86.1%
macro (trung binh signature) : 84.8%
351 / 403 signature xuat hien lai tren EVAL
```

Macro ≈ micro → kết quả **không** do vài signature phủ rộng kéo lên.

### Điều hoà hai kết quả nghịch nhau

Vì sao FDR 35% mà held-out vẫn 84.8%? Vì hoán vị **giữ nguyên phân phối nhãn trong
document**, nên signature "ngẫu nhiên" qua ngưỡng vẫn dự đoán lớp đa số và vẫn được ~69%
trên EVAL. Nên 84.8% là **trung bình của signature thật (cao hơn) và signature may rủi (~69%)**.

> **Hệ quả:** lọc bằng Wilson lower bound + BH-FDR sẽ **giảm số lượng nhưng nâng độ chính xác**.
> Đây là dự đoán kiểm chứng được, và là nội dung EXP5.

---

## 7. Vì sao substrate này bị majority áp đảo — đặc trưng hoá toán học

Sau EXP13–15 và kiểm tra null, đây là lời giải thích hình thức cho kết quả âm tính.

### 7.1 Hai rào cản độc lập

Để một đặc trưng $\sigma$ **thay đổi quyết định**, cần tồn tại bucket mà mode có điều kiện
khác mode biên:

$$\exists\, \ell \ne \ell_{\text{maj}} : \; \hat p(\ell \mid \sigma) > \hat p(\ell_{\text{maj}} \mid \sigma)$$

**Rào cản 1 — quyết định.** Với tỉ lệ nền đo được $p_0 = 0.773$ (BEFORE_FWD) và á quân
$p_1 = 0.154$ (BEFORE_REV), tỉ lệ odds tiên nghiệm là $p_0/p_1 \approx 5.0$. Đặc trưng phải
cung cấp bằng chứng log-odds $> \log 5.0 \approx 1.61$ nats **chỉ để hoà**.

**Rào cản 2 — bằng chứng.** Vượt rào 1 trên mẫu hữu hạn chưa đủ; phải vượt được cận dưới
Wilson để loại khả năng do dao động lấy mẫu.

### 7.2 Số đo cho từng rào cản

| | support ≥10 | ≥30 | ≥100 |
|---|---|---|---|
| bucket vượt rào 1 (mode ≠ majority) | 5.11% | 2.17% | 1.04% |
| **kỳ vọng dưới NULL (mô phỏng)** | **0.30%** | **0.00%** | **0.00%** |
| bucket còn lại sau rào 2 (Wilson ≥0.7) | **0** | **0** | **0** |

Tỉ lệ vượt rào 1 cao hơn null **17×** ở $n \ge 10$, và null cho **0.00%** ở $n \ge 30$.
Vậy bất đồng **không phải nhiễu** — có liên hệ thống kê thật giữa đặc trưng và nhãn.

### 7.3 Nhưng liên hệ thật ≠ dự đoán được

Bỏ rào 2, dùng thẳng các bucket bất đồng để dự đoán trên EVAL:

| support ≥ | bất đồng | feature đúng | majority đúng | lãi ròng |
|---|---|---|---|---|
| 10 | 1,905 | 31.9% | 42.2% | **−196** |
| 30 | 656 | 28.7% | 35.5% | −45 |
| 50 | 368 | 29.1% | 28.3% | +3 |
| 100 | 211 | 29.4% | 16.6% | **+27** |

> **Nghịch lý được giải:** bucket bất đồng mang liên hệ thống kê thật, nhưng ở đó **cả hai
> bên đều đoán sai** (29–32% vs 17–42%). Đó là những cặp **bản chất mơ hồ**, không phải nơi
> chứa tri thức khai thác được. Lãi tốt nhất **+27 / 109,666 = +0.02%**.

**Hệ quả:** cổng Wilson làm đúng chức năng — nó loại chính những bucket có bất đồng thật
nhưng không đáng tin. Kết quả âm tính đứng vững, và giờ được đặc trưng hoá chính xác:

$$I(\rho;\sigma) > 0 \quad\text{nhưng}\quad \mathbb{E}[\text{lãi quyết định}] \approx 0$$

*Có thông tin tương hỗ, nhưng không có giá trị quyết định.* Đây là phân biệt mà support/
confidence của PaTeCon **không thể hiện được** — và là lý do hình thức khiến việc port
thất bại trên substrate này.

---

### Cập nhật quy tắc quyết định constraint

$$\sigma \text{ là constraint} \iff \underbrace{\text{Wilson}_{\text{lo}}(\hat p) \ge \theta_{\text{conf}}}_{\text{thay cho } \hat p \ge \theta} \ \wedge\ \underbrace{q_\sigma \le 0.05}_{\text{BH-FDR}} \ \wedge\ \underbrace{|\text{docs}(\sigma)| \ge 5}_{\text{đơn vị độc lập}}$$
