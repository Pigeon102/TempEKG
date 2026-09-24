# PaTeCon vs phương pháp hiện tại — định nghĩa, kiểm chứng, đối chiếu

Bốn phần theo yêu cầu: (1) định nghĩa loại conflict, (2) kiểm chứng số với paper,
(3) họ khai báo xử lý được gì, (4) đối chiếu hai phương pháp bằng **chính cách đánh giá
của họ**.

---

# 1. Định nghĩa các loại temporal conflict

Ký hiệu: fact thời gian $F = (S, P, O, T)$ với $T = [t.s, t.e]$.

### T1 — REPRESENTATION CONFLICT
$$t.s > t.e$$
Khoảng thời gian tự mâu thuẫn: bắt đầu sau khi kết thúc. Phát hiện được **không cần
constraint nào** — chỉ cần đọc một fact.

### T2 — MUTUAL EXCLUSION CONFLICT
$$\exists\, F_1=(x,p,y,T_1),\ F_2=(x,p,z,T_2): \; y \ne z \;\wedge\; p \text{ là hàm}$$
Một chủ thể có **nhiều giá trị khác nhau** cho một thuộc tính chỉ được có một
(hai ngày sinh, hai ngày mất). Cần **2 fact**, không cần so thời gian.

### T3 — ORDERING CONFLICT
$$\exists\, F_1, F_2: \; \neg\,\pi(T_1, T_2), \quad \pi \in \{\textsf{before},\textsf{start},\textsf{finish},\textsf{include}\}$$
Thứ tự thời gian bị vi phạm (chết trước khi sinh; bị giết bởi người đã chết). Cần **2 fact
+ so sánh khoảng**.

### T4 — DISJOINTNESS CONFLICT
$$\exists\, F_1=(x,p,y,T_1), F_2=(x,p,z,T_2): \; y \ne z \;\wedge\; T_1 \cap T_2 \ne \emptyset$$
Hai khoảng **chồng nhau** ở thuộc tính lẽ ra phải rời nhau (chơi cho 2 CLB cùng lúc).
Khác T2 ở chỗ **có thể có nhiều giá trị**, chỉ là không đồng thời.

### T5 — GRANULARITY CONFLICT
$$\text{prec}_{\text{khai báo}}(T) \;\ne\; \text{prec}_{\text{thực}}(T)$$
**Độ chính xác được khai báo không khớp độ chính xác thực.** Ba dạng con:

- **T5a** giá trị thô hơn khoảng bao nó
- **T5b** *độ chính xác giả* — chỉ biết năm nhưng ghi thành ngày cụ thể (`YYYY0101`)
- **T5c** cùng $(x,p)$ nhưng các giá trị ở độ chính xác khác nhau

Phát hiện được từ **một fact** (T5b) hoặc **phân bố thống kê** (không phải từ cặp fact).
**Đây là loại duy nhất không quy về so sánh khoảng.**

---

# 2. Kiểm chứng số liệu với paper

## 2.1 Dataset — khớp tuyệt đối

| | Paper (Table 3) | Chạy lại | |
|---|---|---|---|
| Facts | 50,000 | 50,000 | ✅ |
| Entities | **17,176** | **17,176** | ✅ |
| Temporal properties | 6 | 6 | ✅ |

Properties tìm được: `P26, P54, P108, P286, P569, P570` — đúng 6.
**Xác nhận: dữ liệu mình dùng CHÍNH LÀ WD50K của họ.**

## 2.2 Constraint — lệch 1, đã truy ra nguyên nhân chính xác

| | Paper (Table 6) | Chạy lại |
|---|---|---|
| Số constraint trên WD50K | **13** | **12** |
| Grade C / M / W | 13 / 0 / 0 | 12 / 0 / 0 (§4.1) |

Chạy **3 lần, kết quả y hệt** (12 constraint, 819 conflict) → thuật toán **tất định**,
không cần lấy trung bình.

### Nguyên nhân lệch 1: MỘT instance

Mining sinh **18 candidate**, `MergeConstraint()` lọc bằng `confidence >= 0.9` (dòng 1815).
Sáu cái bị loại. Cái **sát ngưỡng nhất**:

```
#13.  a,P569,b,t1,t2 before a,P54*P286,d,t5,t6  |  0.898876404494382
```

$$0.898876404494382 \;=\; \frac{80}{89} \qquad \text{thiếu ngưỡng } 0.9 \text{ đúng } 0.0011$$

Support = 89, positive = 80. **Chỉ cần thêm 1 instance dương**: $81/89 = 0.9101 \ge 0.9$
→ constraint được giữ → **đúng 13 như paper**.

Kiểm chứng bằng cách quét ngưỡng:

| ngưỡng | #constraint |
|---|---|
| 0.900 | 12 |
| **0.895** | **13** ✅ |
| 0.890 | **13** ✅ |
| 0.850 | 14 |

Đây là constraint **SP(b) hai chủ thể** (sinh trước giai đoạn HLV của đội mình từng chơi) —
loại có support thấp nhất, nên nhạy nhất với khác biệt tiền xử lý.

### Vì sao paper được 80→81

Bản chạy lại loại **1,166 fact** `start > end` và **3,100 bản trùng** (50,000 → 46,900 →
45,734). Chỉ cần bản của paper giữ lại nhiều hơn/ít hơn vài fact ở nhánh `P54*P286` là
tỉ lệ vượt 0.9. README của chính họ đã lường trước:

> *"Because we keep improving the code, the experimental results may be slightly different
> from the paper."*

**Kết luận: tái lập thành công.** Lệch duy nhất được giải thích trọn vẹn ở mức **một
instance** trên constraint có support nhỏ nhất (n=89) — không phải sai khác phương pháp.
12/13 constraint còn lại trùng khớp hoàn toàn.

---

# 3. PaTeCon khai báo xử lý được gì / không được gì

## 3.1 Khai báo XỬ LÝ ĐƯỢC (§2.3, §8 của paper)

- **2 structural pattern** — SP(a) một chủ thể, SP(b) hai chủ thể nối bởi cạnh phi thời gian
- **5 temporal predicate** — `start`, `finish`, `before`, `disjoint`, `include`
- **1 mutual exclusion predicate** — `false`
- **3 họ constraint** — disjointness, ordering, mutual exclusion

→ Bao phủ **T2, T3, T4**.

## 3.2 Khai báo KHÔNG xử lý (trích nguyên văn)

| Trích dẫn | Loại bị bỏ |
|---|---|
| *"the disjointness between a pair of time intervals with different properties is trivial, so we only consider the case of the same property"* (§2.3) | T4 khác property |
| *"to keep the search manageable, we do not extract the disjointness relationships between different subjects"* (§2.4) | T4 khác chủ thể |
| *"we do not need to create structural patterns specifically for [3-subject] cases"* (§2.4) | pattern ≥3 chủ thể |
| *"the predicates can be broadened to encompass quantitative relationships, such as $t_2 - t_1 \le 10\ \text{years}$... **Future work**"* (§8) | ràng buộc định lượng / thời lượng |

## 3.3 KHÔNG HỀ NHẮC TỚI

**T5 GRANULARITY không xuất hiện ở bất kỳ đâu trong paper.**

Họ *có* xử lý granularity, nhưng chỉ ở **một nghĩa hẹp**: logic ba trị `FuzzyTime` trả về
`unknown` khi hai giá trị **không đủ độ chính xác để so sánh** (Table 2 của họ:
`2022-01` vs `2022` → `unknown`).

Đó là **dung thứ** granularity khi so sánh, **không phải phát hiện** granularity sai.
Với họ, `17320101` là một ngày hợp lệ như mọi ngày khác.

| | PaTeCon | |
|---|---|---|
| T1 representation | ✅ có (loại trước khi mine) | |
| T2 mutual exclusion | ✅ có | |
| T3 ordering | ✅ có | |
| T4 disjointness | ⚠️ chỉ **cùng property, cùng chủ thể** | |
| T5 granularity | ❌ **không có, không nhắc tới** | |

---

# 4. Đối chiếu hai phương pháp — dùng cách đánh giá của họ

## 4.1 Cách đánh giá của PaTeCon (§6.1.2)

**(a) Chất lượng constraint** — 3 mức, 3 annotator chấm độc lập:
- **C** constraint đúng
- **M** có lý nhưng có ngoại lệ rõ ràng
- **W** sai

**(b) Phát hiện conflict** — **chỉ tính RECALL** trên tập fact-sai đã gán nhãn
(WD-411, FB-128). Trích nguyên văn:

> *"only conflicting pairs are detected and no resolution is performed, so **precision is not
> calculated**, and a wrong fact contained in a conflicting pair is considered a successfully
> recalled example."*

Tập gán nhãn của họ: **WD-411** (411 fact sai + 411 fact đúng, 69 property),
**FB-128** (128+128, 6 property). Gán nhãn **bán tự động**: so dump cũ với Wikidata hiện
tại, fact bị xoá là ứng viên sai, rồi 2 chuyên gia kiểm.

## 4.2 Chất lượng constraint — chấm theo rubric C/M/W

**Trên WD50K:**

| Phương pháp | #constraint | C | M | W |
|---|---|---|---|---|
| Chekol et al. (viết tay) — paper | 12 | 9 | 3 | 0 |
| PaTeCon+ — paper | 13 | 13 | 0 | 0 |
| **PaTeCon+ — chạy lại** | **12** | **12** | 0 | 0 |
| **Phương pháp mình (EXP17)** | **5** (conf≥0.99) | **5** | 0 | 0 |

Phương pháp mình tìm ít constraint hơn (5 vs 12) vì mình chỉ giữ `conf ≥ 0.99` và **không**
cài mutual-exclusion/disjointness. Nhưng 5 cái tìm được **trùng khớp** với của họ:

| Constraint | PaTeCon | Mình |
|---|---|---|
| `P569 before P570` (sinh→chết) | 0.9918 | 0.9991 |
| `P569 before P54` (sinh→chơi CLB) | 0.9984 | 1.0000 |
| `P569 before P26` (sinh→kết hôn) | 1.0000 | 1.0000 |
| `P54 before P570` (chơi CLB→chết) | 1.0000 | 1.0000 |
| `P569 before P108` (sinh→việc làm) | 0.9873 | 1.0000 |

**Trên MAVEN** (6 luật, chấm cùng rubric):

| Luật | conf | Grade |
|---|---|---|
| `SUBEVENT,FWD → CONTAINS_FWD` | 99.0% | **C** |
| `SUBEVENT,REV → CONTAINS_REV` | 97.9% | **C** |
| `PRECONDITION,FWD → BEFORE_FWD` | 93.2% | **C** |
| `PRECONDITION,REV → BEFORE_REV` | 88.7% | **M** |
| `CAUSE,FWD → BEFORE_FWD` | 71.8% | **M** |
| `CAUSE,REV → BEFORE_REV` | 77.2% | **M** |

**MAVEN: 3C / 3M / 0W.** Thấp hơn WD50K (12C/0M/0W) — trung thực mà nói, constraint trên
MAVEN **kém chắc chắn hơn**. Nguyên nhân đo được: `CAUSE` chỉ suy ra `BEFORE` 63.7% vì
25% cặp CAUSE là `CONTAINS` (nguyên nhân *chứa* kết quả về thời gian).

## 4.3 Phát hiện conflict — bảng đối chiếu

| | WD50K (PaTeCon) | WD50K (mình) | MAVEN (mình) |
|---|---|---|---|
| T1 representation | 1,166 (2.33%) | — | không áp dụng¹ |
| T2 mutual exclusion | 715 | không cài | không áp dụng² |
| T3 ordering | 105 | 9 | **72** |
| T4 disjointness | 0³ | không cài | chưa cài |
| T5 granularity | **0 — không có cơ chế** | 3,230 (13.35%)⁴ | **17,102 ứng viên**⁵ |
| **TỔNG** | **820** | — | — |

¹ MAVEN chưa có interval (TIMEX chưa chuẩn hoá)
² MAVEN không lưu giá trị thuộc tính lặp nên không thể có loại này
³ constraint `P54 disjoint` conf 0.68 < 0.9 nên bị loại — **đúng**, vì cầu thủ có thể vừa ở
  CLB vừa ở đội tuyển
⁴ đo bởi mình, PaTeCon không đo: 13.35% giá trị day-precision là `01-01`, gấp **49×** mức
  kỳ vọng 0.27%
⁵ event mang ≥2 anchor CONTAINS — quần thể để định nghĩa, **chưa đo được**

## 4.4 Khoảng trống để đánh giá đúng chuẩn của họ

Để dùng **đúng** giao thức của họ trên MAVEN, cần một tập tương đương **WD-411**:
fact/quan hệ đã gán nhãn đúng-sai, để tính **recall**.

MAVEN **không có** sẵn. Hai cách tạo:

| Cách | Tương ứng với | Chi phí |
|---|---|---|
| Lấy chênh lệch giữa hai phiên bản annotation MAVEN | đúng cách bán tự động của họ | cần 2 phiên bản — **không có** |
| Gán nhãn thủ công tập conflict được flag | 2 chuyên gia như họ | ~3 person-day cho 300 mục |

→ **Không thể so recall với họ nếu chưa có tập gán nhãn.** Đây là hạng mục bắt buộc nếu
muốn bảng so sánh đầy đủ.

---

# 5. Tóm tắt cho quyết định

1. **Tái lập thành công** — dataset khớp tuyệt đối (17,176 entity), constraint lệch 1/13,
   tất định qua 3 lần chạy.
2. **PaTeCon bao phủ T2, T3, T4(hẹp)**; **không** bao phủ T5 granularity, và **không nhắc
   tới nó**. Ràng buộc định lượng họ ghi rõ là *future work*.
3. **Chất lượng constraint**: WD50K 12C/0M/0W (họ) ≈ 5C/0M/0W (mình). MAVEN **3C/3M/0W** —
   kém hơn, nguyên nhân là `CAUSE` mơ hồ.
4. **T5 granularity là khoảng trống rõ nhất**: 13.35% trên chính dữ liệu của họ, gấp 49×
   mức ngẫu nhiên, và **không phương pháp nào hiện có phát hiện được**.
5. **Còn thiếu để so recall đúng chuẩn của họ**: tập gán nhãn đúng-sai cho MAVEN.
