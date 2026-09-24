# TempEKG — Báo cáo toán học

*Cập nhật 24/09/2026. Mọi định nghĩa bám đúng code trong `tempekg/`; mọi con số là số đo, kèm nguồn
log. Ký hiệu toán viết bằng LaTeX (hiển thị trong VS Code / GitHub).*

Tài liệu này hình thức hoá toàn bộ pipeline: dữ liệu và cách chia tập (§1), tầng ràng buộc Allen
(§2), ngôn ngữ luật (§3), thống kê chọn luật (§4), combiner (§5), rút gọn luật có chứng minh (§6),
thiết kế theo tầng (§7), auditor Bài 2 (§8), mô hình năng lượng tam giác (§9), cấu trúc bậc cao bộ
3/4/5 (§10), thước đo (§11), kết quả (§12), và những điều chưa chứng minh được (§13).

---

## 1. Dữ liệu, ký hiệu, chia tập

**Document và đồ thị.** Mỗi document $d$ cho một đồ thị $G_d = (V_d, E_d)$. $V_d = V_d^{E} \cup V_d^{T}$
gồm node sự kiện (cụm đồng tham chiếu) và node TIMEX. Cạnh đích $e = (a, b) \in E_d$ mang nhãn

$$y(e) \in \mathcal{L} = \{\textsf{BEFORE}, \textsf{CONTAINS}, \textsf{SIMULTANEOUS}, \textsf{OVERLAP}, \textsf{BEGINS-ON}, \textsf{ENDS-ON}\}$$

và loại cạnh $\tau(e) \in \{\textsf{EE}, \textsf{ET}, \textsf{TE}, \textsf{TT}\}$, xác định bởi loại hai node.

| | Train | Valid |
|---|---|---|
| Document | 2.913 | 710 |
| Cạnh đích (4 loại) | 792.395 | 188.924 (EE 109.929 · ET 26.573 · TE 39.935 · TT 12.487) |
| Cặp EV–EV | 483.504 | 109.929 |

Prior EV–EV trên train: BEFORE 91,04%, CONTAINS 7,43%, SIMULTANEOUS 0,86%, OVERLAP 0,60%, BEGINS-ON
0,04%, ENDS-ON 0,02%. Trên valid, BEFORE chiếm 84,8% của cả bốn loại cạnh.

**Chia tập theo document.** Với $h(s) = \mathrm{md5}(s)$ hiểu như số nguyên:

$$\mathrm{split}(d) = \begin{cases} \text{DISCOVERY} & h(d) \bmod 10 \ge 4 \\ \text{CONF-1} & h(d) \bmod 10 < 4,\ h(\text{"s2"}\Vert d) \bmod 2 = 0 \\ \text{CONF-2} & \text{còn lại} \end{cases}$$

Cặp EV–EV: DISCOVERY 292.719 · CONF-1 95.352 · CONF-2 95.433. **Quy tắc phân quyền:** DISCOVERY đề xuất
luật; CONF-1 chỉ chấm lại luật; CONF-2 chỉ chọn ngưỡng và tham số; valid mở một lần cho mỗi cấu hình.

**Cross-fit trên valid** (cho những bước phải học từ lỗi *out-of-sample* của classifier, tức Bài 2 và
suy luận tam giác): chia document valid thành hai fold $F_k = \{d : h(\text{"cf"}\Vert d) \bmod 2 = k\}$;
trong fold học chia ba theo $h(\text{"in3"}\Vert d) \bmod 3$ (mine / xác nhận / chỉnh); chấm trên fold còn
lại, rồi đổi vai. Mỗi document valid được chấm đúng một lần.

**Bất biến chống rò rỉ.** Ở Bài 1, không nhãn thời gian nào (kể cả của cạnh khác) được dùng làm đặc
trưng. KG tách ba lớp cạnh: vai trò (quan sát được), nhân quả / sự kiện con (chỉ làm trần), thời gian
(đích).

## 2. Tầng ràng buộc Allen

Mỗi sự kiện hay TIMEX là một khoảng $[s, e]$. Mỗi nhãn MAVEN được ánh xạ sang một tập quan hệ Allen
$\mu : \mathcal{L} \to 2^{\mathcal{A}_{13}}$:

| Nhãn | $\mu$ | Ràng buộc điểm mút |
|---|---|---|
| BEFORE | $\{b\}$ | $e_a < s_b$ |
| CONTAINS | $\{di\}$ | $s_a < s_b \wedge e_b < e_a$ |
| OVERLAP | $\{o\}$ | $s_a < s_b < e_a < e_b$ |
| SIMULTANEOUS | $\{e\}$ | $s_a = s_b \wedge e_a = e_b$ |
| BEGINS-ON | $\{s, si, e\}$ | $s_a = s_b$ |
| ENDS-ON | $\{b, m\}$ | $e_a \le s_b$ |

Nghịch đảo $\mu(y)^{-1}$ dùng cho chiều ngược. Phép hợp thành $\circ : \mathcal{A}_{13} \times \mathcal{A}_{13} \to 2^{\mathcal{A}_{13}}$ **sinh bằng
vét cạn** trên mọi cặp khoảng nguyên trong $[0, 7)$, mở rộng lên tập bằng hợp.

**Định nghĩa (tam giác nhất quán).** Với ba node $a, b, c$ có đủ ba cạnh:

$$\mu(y(a,b)) \cap \big(\mu(y(a,c)) \circ \mu(y(c,b))\big) \neq \emptyset .$$

**Đo được:** 0 vi phạm trên 585.078 tam giác gold. Ánh xạ của BEGINS-ON / ENDS-ON được chọn bằng dữ liệu:
cách đọc "cùng kết thúc" $\{f, fi, e\}$ cho ENDS-ON sinh 812 bộ ba mâu thuẫn trên train; $\{m\}$ sinh 42;
$\{b, m\}$ sinh 0.

**Định nghĩa gốc.** MAVEN-ERE theo hướng dẫn RED (O'Gorman et al., 2016). Bảng đại số điểm của RED cho
ENDS-ON: $e_a = s_b$ (Allen $m$), tức **meets**. Vì $\{b, m\} \supseteq \{m\}$, đếm mâu thuẫn không bao giờ ưu tiên
$\{m\}$. Phép thử phân biệt: một cạnh $(a, b)$ có **nhân chứng khoảng hở** nếu tồn tại $x$ với
$\mu(y(a,x)) \circ \mu(y(x,b)) \subseteq \{b\}$. Nhân chứng có ở 91,1–97,8% cạnh BEFORE nhưng chỉ ở 5 / 315 cạnh ENDS-ON. Dữ
liệu vì vậy hành xử như $\{m\}$; $\{b, m\}$ là bản nới lỏng hấp thụ 7 tam giác nhiễu trong 3 document. Với BEGINS-ON,
cách đọc $\{mi\}$ trong bảng của RED sinh 1.141–3.374 tam giác mâu thuẫn; "cùng bắt đầu" $\{s, si, e\}$ không bị nhân chứng
nào bác.

## 3. Ngôn ngữ luật

**Nguyên tử.** Hàm $\phi$ ánh xạ mỗi cặp $x$ sang tập nguyên tử $\mathcal{A}(x)$ (trung bình 40,9 nguyên tử
mỗi cặp EV–EV). Hàm này không đọc nhãn của $x$ hay của cạnh nào khác. Có sáu dạng nguyên tử:

| Dạng | Ý nghĩa | Ví dụ |
|---|---|---|
| $\mathrm{EQ}(f, v)$ | $f(x) = v$ | $\mathrm{EQ}(\texttt{type\_b}, \textsf{Bodily\_harm})$ |
| $\mathrm{HAS}(F, v)$ | $v \in F(x)$ | $\mathrm{HAS}(\texttt{roleset\_a}, \textsf{Cause})$ |
| $\mathrm{ALL}(F, v)$ | $F(x) = \{v\}$ | $\mathrm{ALL}(\texttt{roleset\_a}, \textsf{Location})$ |
| $\mathrm{CNT}(F, k)$ | $|F(x)| = k$ | $\mathrm{CNT}(\texttt{anchor\_roles}, 3)$ |
| $\mathrm{MIX}(F)$ | $F(x)$ có ≥ 2 loại | |
| $\mathrm{REL}(g, v)$ | so sánh giữa hai đầu | $\mathrm{REL}(\texttt{a\_before\_b}, \textsf{False})$ |

**View.** Một view $v$ là hàm phân lớp $\sigma_v : X \to S_v$. Tám view được dùng: `global`, `sdist`,
`order`, `anchor`, `bucket_a`, `etype_a`, `sdist×order`, `anchor×sdist`.

**Luật.** Một luật là bộ $\rho = (v, s, B, \ell)$ với $B \subseteq$ nguyên tử, $|B| \le 2$, và $\ell \in \mathcal{L}$. Luật
bắn trên $x$ khi

$$\mathrm{fire}_\rho(x) \iff \sigma_v(x) = s \ \wedge\ B \subseteq \mathcal{A}(x).$$

Phần mở rộng trên tập $Y$ là $\mathrm{ext}_Y(\rho) = \{x \in Y : \mathrm{fire}_\rho(x)\}$. Số đếm: $n_Y(\rho) = |\mathrm{ext}_Y(\rho)|$,
$k_Y(\rho) = |\{x \in \mathrm{ext}_Y(\rho) : y(x) = \ell\}|$. Tỷ lệ nền của lớp: $\pi_{v,s}(\ell) = \Pr[y = \ell \mid \sigma_v = s]$
trên DISCOVERY.

**Tính toán.** Trong mỗi lớp $(v, s)$, mỗi nguyên tử là một bitset (số nguyên Python) $\beta_c$ trên các cặp
của lớp. Khi đó $n(\{c, c'\}) = \mathrm{popcount}(\beta_c \wedge \beta_{c'})$ và
$k = \mathrm{popcount}(\beta_c \wedge \beta_{c'} \wedge \beta_\ell)$. Nhờ vậy duyệt **mọi** luật độ sâu ≤ 2 trong mọi lớp.

## 4. Thống kê chọn luật

**Cận dưới Wilson** ($z = 1{,}96$, $\hat p = k/n$):

$$\mathrm{wlb}(k, n) = \frac{\hat p + \frac{z^2}{2n} - z\sqrt{\frac{\hat p(1-\hat p)}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}} .$$

*Tính chất dùng đến:* $\mathrm{wlb}(k, n) \le k/n$; $\mathrm{wlb}$ tăng theo $k$ khi $n$ cố định; và
$\mathrm{wlb}(k, n) \le \mathrm{wlb}(n, n)$. Tính chất cuối là cơ sở cắt tỉa của nhánh vét cạn cũ.

**Bốn cổng trên DISCOVERY** (EV–EV, `mine_full.py`), với $\pi = \pi_{v,s}(\ell)$:

1. $n \ge 25$ và $k \ge 8$.
2. Lift trong lớp: $k/n \ge 1{,}5\,\pi$.
3. Số document chứa các lần bắn **đúng** $\ge 5$.
4. Với luật hai điều kiện: $\Delta\mathrm{logit} = \mathrm{logit}(k, n) - \max_{c \in B}\mathrm{logit}(k_c, n_c) \ge 0{,}5$, trong đó
   $\mathrm{logit}(k, n) = \log\frac{p}{1-p}$ với $p = \frac{k + 0{,}5}{n + 1}$.

**Kiểm soát FDR.** Với mỗi ứng viên, tính $p$-value một phía $p_j = \Pr[\mathrm{Bin}(n, \pi) \ge k]$. Benjamini–Hochberg ở
mức $q = 0{,}05$ giữ $j$ ứng viên đầu, với $j = \max\{i : p_{(i)} \le q\, i / m\}$. Bước này bảo đảm tỷ lệ phát hiện sai
kỳ vọng $\le q$ **khi các $p_j$ độc lập hoặc phụ thuộc dương**; các cặp cùng document không độc lập, và
cổng 3 chỉ bù một phần. Thiết kế gốc dùng 200 hoán vị theo khối document; ở đây thay bằng kiểm định nhị thức
vì chi phí.

**Xác nhận trên CONF-1:** giữ $\rho$ nếu $n_{C1} \ge 10$ và $\mathrm{wlb}(k_{C1}, n_{C1}) > \pi$. Trọng số của luật là
$w(\rho) = \mathrm{wlb}(k_{C1}, n_{C1})$.

Số luật qua từng bước (EV–EV): 106.242 (qua bốn cổng) → 92.773 (qua BH) → **54.719** sau xác nhận
(CONTAINS 29.049, SIMULTANEOUS 20.538, OVERLAP 4.583, BEGINS-ON 523, ENDS-ON 26).

**Lời nguyền người thắng.** $w(\rho)$ được đo trên CONF-1 với $n_{C1}$ nhỏ, sau khi đã chọn trong hàng chục nghìn
ứng viên, nên $\mathbb{E}[w(\rho) \mid \rho \text{ được chọn}]$ lệch lên. Ví dụ: `type_pair = (Catastrophe,
Motion_directional)` đúng 11/32 trên DISCOVERY nhưng 12/12 trên CONF-1, cho $w = 0{,}758$. Đây là điểm yếu còn
mở (§13).

**Ablation (K-fold cross-fitting).** Thay 60/20/20 bằng $K = 5$ fold: với mỗi fold $j$, tìm luật trên
$\bigcup_{i \ne j} F_i$ và đếm trên $F_j$; trọng số là cận Wilson của bằng chứng ngoài fold gộp lại; ngưỡng chọn trên dự đoán
ngoài fold của toàn bộ train. Valid: 26,32% (hợp luật) và 26,39% (chỉ luật được cả 5 fold chọn), so với 26,99% của
cách tách 60/20/20. Cách tách 60/20/20 với một cách chia khác cho 26,51%, nên chênh lệch nằm trong dao động do cách
chia. Pipeline giữ cách tách 60/20/20.

## 5. Combiner

Gọi $\mathcal{R}$ là tập luật, $\theta : \mathcal{L} \to [0, 1] \cup \{\infty\}$ là ngưỡng theo nhãn, $A(x) = \{\rho \in \mathcal{R} :
\mathrm{fire}_\rho(x),\ w(\rho) \ge \theta(\ell_\rho)\}$ là tập luật **hoạt động** bắn trên $x$, và
$\kappa(\rho) = (w(\rho), -\mathrm{id}(\rho))$ là thứ tự toàn phần. Khi đó

$$\hat y(x) = \begin{cases} \ell\big(\arg\max_{\rho \in A(x)} \kappa(\rho)\big) & A(x) \neq \emptyset \\ \mathrm{fb}(x) & A(x) = \emptyset \end{cases}$$

Nhãn dự phòng $\mathrm{fb}$ tuỳ bộ luật:
- BEFORE (EV–EV);
- nhãn đa số (cạnh TIMEX);
- nhãn đang có (luật liên tầng ghi đè, auditor Bài 2).

**Chọn ngưỡng:** leo toạ độ trên lưới $\{0{,}1; 0{,}15; 0{,}2; \dots; 0{,}8; \infty\}$, tối đa hoá macro-F1 trên CONF-2.
Với EV–EV được $\theta = (\textsf{CONT}\ 0{,}5;\ \textsf{SIMU}\ 0{,}15;\ \textsf{OVER}\ 0{,}1;\ \text{còn lại } \infty)$, macro-F1
CONF-2 26,36%.

Combiner cũ `max-norm` chấm luật bằng $w(\rho)/\pi(\ell_\rho)$ và chỉ được 25,88%. Lý do: với prior BEGINS-ON
0,044%, luật BEGINS-ON tốt nhất chỉ có $w = 0{,}0035$ nhưng vẫn được $\approx 8$ điểm, vượt $\tau = 5$.

*Lưu ý cài đặt:* combiner gốc `pred_floor` phá hoà theo thứ tự bắn; các chứng minh ở §6 dùng $\kappa$. Hai
bản cho cùng macro-F1 trên CONF-2 (26,36%) và valid (26,99%, accuracy 87,90%).

## 6. Rút gọn luật có chứng minh

Mọi mệnh đề dưới đây chỉ dùng công thức của §5.

**Mệnh đề 6.1 (luật không bao giờ bỏ phiếu).** Nếu $w(\rho) < \theta(\ell_\rho)$ thì $\rho \notin A(x)$ với mọi $x$, nên
xoá $\rho$ không đổi $\hat y$ ở bất kỳ cặp nào, kể cả cặp chưa gặp. $\square$

**Mệnh đề 6.2 (tương đương phần mở rộng).** Giả sử $\ell_\rho = \ell_{\rho'}$ và $\mathrm{ext}_Y(\rho) = \mathrm{ext}_Y(\rho')$, với $Y$ là toàn bộ train.
Khi đó $k, n$ trên DISCOVERY và trên CONF-1 của hai luật trùng nhau, nên $w(\rho) = w(\rho')$. Thay $\rho'$ bằng $\rho$
không đổi $\hat y$ trên $Y$: hai luật bắn cùng chỗ, cùng nhãn, cùng trọng số. Trên dữ liệu mới, điều này chỉ
chắc chắn nếu hai điều kiện tương đương logic; vì vậy nó được **đo**: 0 / 593.433 dự đoán thay đổi trên
train + valid. Quan hệ tương đương được so bằng dấu vân tay
$\big(|\mathrm{ext}|, \sum_{x \in \mathrm{ext}} h(x) \bmod (2^{61}-1)\big)$ (EV–EV) hoặc bằng chính tập chỉ số (các bộ khác). $\square$

**Định lý 6.3 (set cover giữ đầu ra).** Với cặp $x$, đặt $o = \hat y(x)$ và
$M(x) = \max\{\kappa(\rho) : \rho \in A(x),\ \ell_\rho \ne o\}$ (bằng $-\infty$ nếu rỗng). Định nghĩa

$$C(x) = \{\rho \in A(x) : \ell_\rho = o,\ \kappa(\rho) > M(x)\},$$

và $U = \{x : A(x) \ne \emptyset\} \setminus \{x : o = \mathrm{fb}(x) \wedge \forall \rho \in A(x),\ \ell_\rho = o\}$.
Nếu $K \subseteq \mathcal{R}$ thoả $K \cap C(x) \ne \emptyset$ với mọi $x \in U$, thì $\hat y_K(x) = \hat y(x)$ với mọi $x$.

*Chứng minh.* Xét ba trường hợp.
- $A(x) = \emptyset$: xoá luật không làm luật nào bắn thêm, nên $A_K(x) = \emptyset$ và $\hat y_K(x) = \mathrm{fb}(x)$.
- $x \notin U$ và $A(x) \ne \emptyset$: mọi luật bắn đều mang nhãn $o = \mathrm{fb}(x)$. Luật còn lại (nếu có) cho $o$; không
  còn luật nào thì cho $\mathrm{fb}(x) = o$.
- $x \in U$: có $\rho^\ast \in K \cap C(x)$ vẫn bắn. Mọi luật khác nhãn còn trong $K$ có $\kappa < \kappa(\rho^\ast)$, nên argmax mang
  nhãn $o$. $\square$

Bài toán tìm $K$ nhỏ nhất là **set cover**, NP-khó. Cách giải:
1. Luật bắt buộc: nếu $|C(x)| = 1$ thì luật duy nhất đó thuộc mọi phủ.
2. Greedy lười trên phần còn lại.
3. Xoá ngược: bỏ lần lượt luật mà mọi $x$ nó phủ còn luật khác phủ. Kết quả là phủ **tối giản** (không bỏ được luật nào).

**Mệnh đề 6.4 (hai cận).**
- Greedy cho $|K| \le H(d)\cdot \mathrm{OPT}$, với $d = \max_\rho |\{x : \rho \in C(x)\}|$ và $H(d) = \sum_{i \le d} 1/i$ (Chvátal, 1979). Bước
  bắt buộc và bước xoá ngược không làm hỏng cận này.
- Nếu $P \subseteq U$ gồm các cặp có $C(x)$ đôi một rời nhau, thì $\mathrm{OPT} \ge |P|$: mỗi luật thuộc tối đa một $C(x)$ với
  $x \in P$ (đối ngẫu yếu giữa packing và covering).

Chặn dưới dùng trong kết quả là $|P|$, với $P$ xếp tham lam theo $|C(x)|$ tăng dần. $\square$

**Mệnh đề 6.5 (biến thể B).** Đặt $U_B = \{x \in U : \hat y(x) = y(x)\}$. Mọi $K$ phủ $U_B$ giữ đúng mọi cặp đã đoán đúng
trên dữ liệu dựng phủ. Cặp đúng nằm ngoài $U$ thì rơi vào hai trường hợp đầu của 6.3. Hệ quả: accuracy trên dữ
liệu dựng không giảm. Macro-F1 thì không được bảo đảm, vì cặp sai có thể chuyển sang một nhãn sai khác. $\square$

**Kết quả** (phủ dựng trên DISCOVERY + CONF-1; kiểm trên CONF-2; valid mở một lần):

| Bộ luật | Sau xác nhận / qua cổng | Hoạt động | Phát biểu khác nhau | **Phủ A** | Chặn dưới | Valid: giữ nguyên / macro-F1 |
|---|---|---|---|---|---|---|
| EV–EV (2.1) | 54.719 | 2.794 | 1.621 | **378** | 377 | 99,979% / 26,99% |
| EV→TIMEX (2.1) | 1.412 | 134 | 125 | **45** | 45 | 100% / 29,74% |
| TIMEX→EV (2.1) | 1.710 | 598 | 583 | **93** | 93 | 99,997% / 24,29% |
| TIMEX–TIMEX (2.1) | 416 | 100 | 90 | **16** | 16 | 100% / 32,98% |
| Liên tầng EV–EV (2.2) | 7.856 | 1.595 | 1.015 | **152** | 152 | 99,979% / 27,41% |
| Liên tầng EV→TIMEX | 959 | 273 | 217 | **12** | 12 | 99,989% / 30,58% |
| Liên tầng TIMEX→EV | 875 | 6 | 6 | **5** | 5 | 100% / 26,24% |
| Liên tầng TIMEX–TIMEX | 548 | 221 | 121 | **12** | 12 | 100% / 34,93% |
| **Bài 1 tổng** | **68.495** | **5.721** | | **713** | 712 | |
| Auditor Bài 2 (mỗi fold · mục tiêu) | 1.433–1.559 | 87–287 | | **42–83** | 42–83 | 99,985–99,993% |

Tất cả các phủ A, trừ EV–EV, đạt đúng chặn dưới, **tức là tối ưu**; phủ EV–EV cách tối ưu tối đa 1 luật. Biến thể B:
EV–EV 279 (chặn dưới 278, valid macro-F1 27,02%, accuracy 88,11%); liên tầng 141; TIMEX 38 / 84 / 16.

## 7. Thiết kế theo tầng (bước 2.2)

Nguyên tử được phân hoạch theo nguồn: $\mathcal{A}(x) = \bigsqcup_{\lambda \in \Lambda} \mathcal{A}_\lambda(x)$, với $\Lambda = \{\textsf{ONT}, \textsf{ARG},
\textsf{DISC}, \textsf{LEX}, \textsf{TIME}\}$.

- **Pattern:** luật độ sâu ≤ 2 chỉ dùng nguyên tử của một tầng. Mine trên DISCOVERY với cổng $n \ge 30$, $k \ge 10$,
  ≥ 5 document, $\frac{k/n}{\pi} \ge 2$, $\frac{\mathrm{wlb}}{\pi} \ge 1{,}5$; xác nhận $\frac{w}{\pi} \ge 1{,}5$ trên CONF-1. Giữ tối đa 150 pattern mỗi
  (nhãn, tầng).
- **Pattern hoạt động của một cặp:** mỗi tầng giữ tối đa 3 pattern có $w$ cao nhất.
- **Luật liên tầng:** hội của 2–3 pattern hoạt động thuộc các tầng **khác nhau**, qua cùng cổng và cùng xác nhận.
- **Combiner:** như §5 với $\mathrm{fb}(x)$ là nhãn bước 2.1 và ngưỡng theo nhãn chọn trên CONF-2.

Vì luật có thể đề xuất đúng nhãn đang có (để chặn nhãn khác), $U$ của Định lý 6.3 gồm cả những cặp mà đầu ra
không đổi nhưng có luật khác nhãn cùng bắn.

## 8. Auditor Bài 2 (bước 3.1)

Đồ thị cần kiểm toán gán nhãn $\tilde y(e)$ cho mỗi cạnh. Nhóm $g = (\tau(e), \tilde y(e))$; 8 nhóm có đủ dữ liệu.
Trong nhóm $g$, một luật đề xuất nhãn $\ell \ne \tilde y$. Với $\pi_g(\ell)$ là tỷ lệ nền của nhóm:

- **Cổng thích ứng:** $n \ge 30$, $k \ge 10$, ≥ 5 document, $k/n \ge \min\big(2\pi_g(\ell), \frac{1 + \pi_g(\ell)}{2}\big)$, và
  $\mathrm{wlb}(k, n) > \pi_g(\ell)$. Xác nhận: $n_{C} \ge 10$, $\mathrm{wlb} > \pi_g(\ell)$.
- **Vì sao cần $\min$:** khi nhãn cần khôi phục là đa số của nhóm (57% cạnh EV–EV bị đoán CONTAINS thật ra là
  BEFORE), cổng $2\pi$ đòi precision trên 100%.
- **Tầng GRAPH:** nguyên tử là chữ ký đường đi $a$–$x$–$b$ và $a$–$x$–$y$–$b$ trên đồ thị đang kiểm toán, gồm (loại
  node trung gian, các nhãn có hướng trên đường).
- **Combiner:** §5 với $\mathrm{fb} = \tilde y$ và ngưỡng theo $(\tau, \ell)$.

## 9. Mô hình năng lượng tam giác (Bài 2, bước 3.2)

**Tam giác và cấu hình.** Tam giác $t = \{a, b, c\}$ có đủ ba cạnh. Cấu hình $\gamma(t)$ = (loại ba node, ba nhãn *có hướng*);
nhãn của cạnh lưu ngược chiều được thay bằng nghịch đảo.

**Tần suất làm trơn** (gold của DISCOVERY + CONF-1, 2.326 document, 6.306.908 tam giác):

$$\tilde p(\gamma) = \frac{N(\gamma) + \beta \prod_{e \in t} q_{\tau(e)}(l_e)}{N(\text{kinds}) + \beta}, \qquad \beta = 10,$$

với $q_\tau(l) = \frac{N_\tau(l) + 1}{N_\tau + 6}$ là prior theo loại cạnh.

**PMI của tam giác:**

$$\mathrm{PMI}(\gamma) = \log \tilde p(\gamma) - \sum_{e \in t} \log q_{\tau(e)}(l_e).$$

**Năng lượng** của một cách gán $L$ cho document:

$$E(L) = \sum_{e} U_e(l_e) + \lambda \sum_{t} W_t\, T_t(L), \qquad T_t = -\mathrm{PMI}(\gamma_t(L)),$$

$$U_e(l) = -(1 - \alpha)\log q_{\tau(e)}(l) - \log P(\tilde y_e \mid l).$$

**Kênh nhiễu:**
- nhiễu bơm: $P(p \mid l) = 1 - \rho$ nếu $p = l$, ngược lại $\rho\, q(p) / (1 - q(l))$;
- nhiễu classifier: $P(p \mid l) = \frac{N(p, l) + 0{,}5}{N(l) + 3}$, ước lượng trên tập chỉnh.

**Vì sao PMI mà không dùng $-\log \tilde p$:** tần suất thô thưởng cho việc đổi mọi cạnh thành BEFORE. PMI trừ đi phần
chỉ do prior. **Vai trò của $\alpha$:** $\alpha = 0$ là hậu nghiệm Bayes đầy đủ, tự nó đã kéo nhãn hiếm về BEFORE, vì precision
SIMULTANEOUS của classifier chỉ 28,8% (EV–EV 17,9%).

**Tối ưu bằng ICM.** Khởi đầu từ $\tilde y$. Hàng đợi ban đầu gồm các cạnh nằm trong một tam giác có PMI < 0. Với mỗi
cạnh, chọn nhãn cực tiểu hoá năng lượng cục bộ; khi một cạnh đổi nhãn thì đẩy hàng xóm vào hàng đợi; tối đa 4
lượt.

**Mệnh đề 9.1.** Ở chế độ `sum` ($W_t = 1$), năng lượng cục bộ của cạnh $e$ bằng $E(L)$ trừ đi một hằng số không phụ
thuộc $l_e$. Vì vậy mỗi bước ICM được chấp nhận giảm $E$ ngặt, và thuật toán dừng tại một cực tiểu địa phương theo
từng toạ độ (hoặc khi hết số lượt tối đa). Ở chế độ `mean` ($W_t = 1/|\{t \ni e\}|$ tính theo *từng cạnh*), trọng số
phụ thuộc cạnh đang xét, nên không tồn tại năng lượng toàn cục nào mà các bước là hạ toạ độ. Chế độ này là
một heuristic cục bộ, và chỉ dừng nhờ giới hạn 4 lượt. $\square$

Tham số $(\text{mode}, \lambda, \alpha)$ được chọn trên lưới $\{\texttt{mean}\} \times \{0{,}2; 0{,}5; 1; 2\} \times \{0; 0{,}5\} \cup
\{\texttt{sum}\} \times \{0{,}03; 0{,}1\} \times \{0\}$ ở tập chỉnh của mỗi fold. Cả hai fold đều chọn `mean`: $(0{,}5; 0)$ khi tối
ưu theo số lỗi và $(1{,}0; 0{,}5)$ khi tối ưu theo macro-F1 (tam giác một mình).

## 10. Cấu trúc bậc cao: bộ 3, bộ 4, bộ 5

Với cạnh đích $(a, b)$, gọi $N(a, b)$ là tập hàng xóm chung (sự kiện hoặc TIMEX), sắp theo id, bỏ $a, b$, rồi lấy 6
phần tử đầu. Nhãn cạnh $L(x, y) = y(x, y)$ nếu cạnh lưu theo chiều $(x, y)$, ngược lại là nhãn nghịch đảo. Nguyên tử
của hàng xóm $c$ là $\alpha(c) = (\text{loại } c, L(a, c), L(c, b))$.

| Cấu trúc | Chữ ký (kèm $\tau(a, b)$) |
|---|---|
| Bộ 3 | $\alpha(c)$ — một tam giác |
| Bộ 4 | multiset $\{\alpha(c), \alpha(d)\}$ — hai tam giác chung cạnh $ab$ |
| Bộ 4K | thêm $L(c, d)$ — đủ 6 cạnh của 4 node |
| Bộ 5 | multiset $\{\alpha(c), \alpha(d), \alpha(e)\}$ |

Protocol như §4–5: cổng thích ứng của §8, xác nhận trên CONF-1, ngưỡng theo (loại cạnh, nhãn) chọn trên CONF-2, valid
mở một lần. Nhãn hàng xóm có hai nguồn: gold (trần, không đạt được khi triển khai) hoặc dự đoán của classifier hiện
tại (thực tế). Dưới đây là chế độ ghi đè lên classifier bước 2.2 (30,84%), `motif345.py`:

| Cấu hình | Hàng xóm gold | Hàng xóm dự đoán |
|---|---|---|
| Bộ 3 | 46,47% (+15,63) | 31,53% (+0,69) |
| Bộ 4 | 45,98% | 31,57% |
| Bộ 5 | 44,47% | 31,42% |
| Bộ 3 + 4 | **47,34% (+16,50)** | 31,60% (+0,76) |
| Bộ 3 + 4 + 5 | 47,21% | **31,62% (+0,78)**, cũng là cấu hình tốt nhất trên CONF-2 |

Khi biết nhãn thật xung quanh, bộ 4 thêm +0,87 so với bộ 3 và bộ 5 không thêm gì. Trong thực tế, cả bộ 4 và bộ 5 chỉ
thêm +0,09. Kết luận cũ "bộ 4, 5 làm tệ đi" đến từ `quint.py`, script có lỗi hướng cạnh; kết luận đó bị bác bỏ.

## 11. Thước đo

Với mỗi nhãn $\ell$: $P_\ell = \frac{TP_\ell}{TP_\ell + FP_\ell}$, $R_\ell = \frac{TP_\ell}{TP_\ell + FN_\ell}$, $F_\ell = \frac{2 P_\ell R_\ell}{P_\ell + R_\ell}$, và
$\text{macro-F1} = \frac{1}{6}\sum_{\ell} F_\ell$. Nhãn không xuất hiện trong một loại cạnh vẫn tính $F = 0$.

Ở Bài 2, với đồ thị trước kiểm toán $\tilde y$ và sau kiểm toán $\hat y$:
- $P = \frac{|\{e : \hat y_e \ne \tilde y_e,\ \tilde y_e \ne y_e\}|}{|\{e : \hat y_e \ne \tilde y_e\}|}$;
- $R = \frac{|\{e : \hat y_e \ne \tilde y_e,\ \tilde y_e \ne y_e\}|}{|\{e : \tilde y_e \ne y_e\}|}$;
- giảm lỗi ròng $= |\{\tilde y \ne y\}| - |\{\hat y \ne y\}|$.

## 12. Kết quả (valid)

**Bài 1** (macro-F1, 188.924 cạnh):

| Bước | Pipeline hiện tại | Pipeline cũ (257 luật, 400 document) |
|---|---|---|
| Luôn BEFORE | 15,30% | 15,30% |
| 2.1 Luật 4 loại cạnh | 30,09% (EE 26,99) | 29,87% (EE 26,15) |
| 2.2 Liên tầng | 30,84% (EE 27,44) | 30,83% (EE 26,50) |
| *Tham khảo: Bài 2 chỉ tam giác trên đồ thị 2.2* | *31,36%* | *31,70%* |
| *Ghi đè bộ 3+4+5 lên 2.2 (§10)* | *31,62%* | — |

**Bài 2:**

| Nhiễu | Trước | Sau |
|---|---|---|
| Classifier, tối ưu số lỗi | lỗi 15,31% | 11,62% (P/R/F1 69,78 / 47,04 / 56,20) — cũ 11,81% |
| Classifier, tối ưu macro-F1 | macro-F1 30,84% | 31,89% — cũ 32,25% |
| Bơm 10% | lỗi 9,94% | 1,94% |
| Bơm 20% | lỗi 19,89% | 4,16% |

## 13. Những điều chưa chứng minh hoặc còn mở

1. **BEGINS-ON / ENDS-ON:** $F = 0$ trong pipeline. Mine lại theo định nghĩa RED (`experiments/begins_ends/`): tín
   hiệu trong văn bản có ("since/from X" → BEGINS-ON, "from A to B", "until X" → ENDS-ON), nhưng nhãn chỉ được
   chọn ở 1–10% số lần tín hiệu xuất hiện, vì CONTAINS (với "cùng bắt đầu") và BEFORE (với "meets") cũng tương
   thích Allen. Thêm luật vào pipeline: macro-F1 30,84% → 31,65% (cổng chặt) hoặc 32,36% (cổng nới, cũng tốt hơn
   trên CONF-2). Nhưng cái giá là 6–7 cạnh được sửa đúng đổi lấy 163–216 cạnh đúng bị làm hỏng, nên chưa đưa vào
   pipeline.
2. **Lời nguyền người thắng** của $w(\rho)$ (§4). Cần gộp bằng chứng hai phần hoặc co về tiên nghiệm.
3. **Tái lập:** chạy lại bước liên tầng cho 30,83% thay vì 30,84% (207 / 981.319 dự đoán khác nhau), vì thứ tự
   duyệt set trong Python phụ thuộc hash seed. Chưa đo dao động theo seed; các chênh lệch 0,2–0,4 giữa pipeline
   cũ và mới chưa được kết luận.
4. **BH-FDR** giả định độc lập hoặc phụ thuộc dương; các cặp cùng document vi phạm giả định này.
5. **Chế độ `mean` của ICM** không có bảo đảm hội tụ theo năng lượng (Mệnh đề 9.1).
6. **Bước 2.2 và Bài 2** chưa chạy lại với các bộ gọn; các bộ gọn lệch tối đa 0,021% dự đoán trên valid.

**Nguồn số liệu:**
- `experiments/rules_full/mine_full.log`, `compress.log`, `compress_timex.log`, `compress_layered.log`;
- `experiments/logs/layered_rules_full.log`, `bai2_combo_full.log`, `bai2_compress.log`, `motif345_gold.log`,
  `motif345_pred.log`, `real_examples_full.log`.
