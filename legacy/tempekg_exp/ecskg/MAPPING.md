# Ánh xạ constraint PaTeCon sang đồ thị event-centric của MAVEN

**Phạm vi (chốt):**

||
||---|---|
| làm | đồ thị event-centric **thiết kế riêng cho MAVEN**, không copy ECS-KG/SEM | | làm | **ánh xạ** constraint của PaTeCon từ đồ thị reified của họ sang đồ thị của mình |
| không | phát minh thuật toán mining mới | | không | phát minh loại temporal conflict mới |
| không | dùng TIMEX / quan hệ ERE khi **dựng đồ thị** hoặc **mining** — chỉ dùng làm **GT để đánh giá** | Đóng góp = **phép ánh xạ**, không phải thuật toán. --- # 1. Ngôn ngữ constraint của PaTeCon — kiểm kê đầy đủ Lấy trực tiếp từ mã ([Constraint_Mining.py](../patecon/Constraint_Mining.py)), không phải từ bài báo. ## 1.1 Bốn mẫu cấu trúc (thân) | mã | tên trong mã | thân | ràng buộc biến |
|---|---|---|---| | **SP1** | `functional_mining` | `(a,r,b,t1,t2) & (a,r,c,t3,t4)` | cùng đầu `a`, **cùng** quan hệ `r`, hai đuôi |
| **SP2** | `inverse_functional_mining` | `(a,r,b,t1,t2) & (c,r,b,t3,t4)` | cùng đuôi `b`, **cùng** `r`, hai đầu | | **SP3** | `Single_Entity_Temporal_Order` | `(a,r1,b,t1,t2) & (a,r2,c,t3,t4)` | cùng đầu `a`, **khác** quan hệ |
| **SP4** | `Mutiple_Entity_Temporal_Order` | `(a,r1,b) & (a,r_hop,c) & (c,r2,d)` | nối qua thực thể trung gian `c` | ## 1.2 Sáu vị từ (đầu) | vị từ | dùng cho | có dùng thời gian? |
|---|---|---|
| `MutualExclusion` | SP1 | **không** — chỉ đếm `len(values) != 1` |
| `disjoint(t1,t2,t3,t4)` |

SP1, SP2 | có |
| `before` |

SP3, SP4 | có |
| `include` |

SP3, SP4 | có |
| `start` |

SP3, SP4 | có |
| `finish` |

SP3, SP4 | có |

## 1.3 Refinement

Thêm nguyên tử `(b, class, T)` vào thân, thu hẹp phạm vi áp dụng. Cổng:
`0.5 ≤ conf < 0.9` mới được tinh chỉnh; top **10** kiểu entity phổ biến nhất của mỗi quan hệ.

## 1.4 Ngưỡng

`support_threshold = 100` · `candidate_threshold = 0.5` · `confidence_threshold = 0.9` ·
`mutual_exclusion_threshold = 0.96` (≤50k node) hoặc `0.98`

---

# 2. Câu hỏi cốt lõi: cái gì đóng vai `(a, r, b, t1, t2)`?

PaTeCon cần **statement nhị phân có khoảng thời gian**. Đồ thị của ta là **siêu cạnh có nhãn vai**:

$$e:\ \text{kiểu } T,\quad \rho: R \to 2^{\mathcal X},\quad \text{khoảng } [t_1,t_2]$$

Bốn phép chiếu khả dĩ, khác nhau ở **từ vựng quan hệ**:

| mã | dạng statement | quan hệ `r` |
|---|---|---|
| **P1** | `(entity, r, event, t_e)` | `T.role` |
| **P2** | `(entity₁, r, entity₂, t_e)` | `T.role₁role₂` |
| **P3** | `(entity₁, r, entity₂, t_e)` | `role₁role₂` (bỏ kiểu event) |
| **P4** | `(entity₁, r, entity₂, t_e)` | `T` (bỏ vai) |

## Đo trên MAVEN-Arg thật (50,322 event có vai, 162 kiểu, 132 vai)

Một nhóm chỉ **có ích** khi ≥2 statement đến từ **hai event khác nhau** — cùng event thì cùng
khoảng thời gian, mọi vị từ đều tầm thường.

| chiếu | \|R\|
| statement | **SP1 hữu ích** | **SP2 hữu ích** | **r đạt sup≥100** | SP3 entity |
|---|---|---|---|---|---|---|
| P1 `T.role` | 559 | 94,922 | 11,718 | **0** | 30 | 15,873 |
| **P2 `T.r₁r₂`** | 1,672 | 188,764 | 14,604 | **14,604** |

**42** | 15,665 |
| P3 `r₁r₂` | 656 | 188,764 | 19,755 | 19,755 | 27 | 14,997 |
| P4 `T` | 161 | 188,764 | 8,224 | 8,224 | 18 | 10,863 |

## Kết luận: chọn **P2**

**P1 cho SP2 = 0.** Vì đuôi là chính event đó, hai statement cùng đuôi tất yếu cùng khoảng
thời gian → `disjoint` luôn trả `-1` → confidence 0 → constraint không bao giờ được mine.
Chiếu entity→event **làm mất hẳn một trong bốn mẫu cấu trúc**.

**P2 giữ được cả bốn mẫu** và có **nhiều quan hệ đạt ngưỡng support nhất (42)**.

P4 bỏ vai thì mất quá nhiều: chỉ 18 quan hệ đạt ngưỡng, dù cùng số statement.

Định nghĩa chính thức:

$$\pi(e)=\bigl\{\,(x,\ T.r_1{\triangleright}r_2,\ y,\ t_1,\ t_2)\ \bigm|\ x\in\rho(r_1),\ y\in\rho(r_2),\ x\neq y\,\bigr\}$$

---

# 2b.  Ánh xạ NGƯỢC LẠI: cài định nghĩa của họ TRÊN kiến trúc của mình

Chiều đúng là **PaTeCon → chúng ta**, không phải chuyển đồ thị của ta về dạng của họ rồi
chạy mã của họ. `mine_patecon.py` cài **định nghĩa constraint của PaTeCon chạy thẳng trên
đồ thị event-centric**, dùng lại nguyên `Interval_Relations` (FuzzyTime, `comp_time`,
`disjoint/before/include/start/finish`), nguyên cách đếm positive/negative/unknown, nguyên
ngữ nghĩa `break`, nguyên các ngưỡng.

## Ánh xạ khái niệm

| PaTeCon | event-centric của ta |
|---|---| | statement `(a, r, b, t1, t2)` | **tham gia**: `(entity x, khoá κ=(T, vai), event e, khoảng I)` |
| `eVertex a` | `Actor x` | | relation `r` | khoá `κ = (kiểu event T, vai)` |
| thời gian của statement | khoảng của **event** — dùng chung cho mọi vai | ## Hai mẫu cấu trúc gộp làm một PaTeCon cần **hai hàm mining riêng**: `functional_mining` gộp theo **đầu** `(a,r)`, `inverse_functional_mining` gộp theo **đuôi** `(b,r)`. Trong thế giới nhị phân, "đầu"/"đuôi" chính là hai **vai** subject/object. Trên đồ thị có nhãn vai, cả hai là **cùng một phép**: gộp theo `(entity, (T, vai))`. $$\text{SP1} \cup \text{SP2} \;=\; \mathbf{C1}:\ \text{gộp theo } (x,\ \kappa)$$ Từ vựng **559 khoá** thay vì 1,672 quan hệ ở phép chiếu P2 — và không có nổ statement bậc hai (94,922 thay vì 188,764). ## Kiểm chứng trên Wikidata Wikidata là chỗ **duy nhất** có ground truth cho phép ánh xạ — chính output của PaTeCon. ``` WD50K ──reify── đồ thị event-centric ── mine_patecon.py (miner CỦA TA) │ WD50K ───────── PaTeCon gốc ────────────────┴── so sánh ``` Reify: mỗi fact → một `Event(etype=r)` với vai `{subject: h, object: t}` và `TimeX(eb, le)`. Đi qua **đúng các class trong `schema.py`**, không phải biến đổi chuỗi. ### Kết quả trên `.all_constraints` (bản cuối, `conf ≥ 0.9`) | constraint | PaTeCon | miner của ta | ||---|---|---|---| | `P569` MutualExclusion | 0.97663325267888 | 0.9766332526788800 | || `P570` MutualExclusion | 0.9627085377821394 | 0.9627085377821394 |
|| `P569 before P570` | 0.9974486966167498 | 0.9974486966167498 | || `P569 before P26` | 0.9977876106194691 | 0.9977876106194691 |
|| `P569 before P54` | 0.9984126984126984 | 0.9984126984126984 | || `P26 before P570` | 0.9935897435897436 | 0.9935897435897436 |
| **6/6 khớp đến chữ số cuối. Lệch 0. Thiếu 0.** ### Một chỗ phải sửa để khớp: khử trùng lặp Lần chạy đầu lệch nhẹ (`14122/14465` vs `14127/14465`). Nguyên nhân: WD50K có **3,112 dòng trùng**; reader của PaTeCon có bước khử trùng riêng ("duplicate running time"), còn `reify` tạo Event riêng cho mỗi dòng. Sửa bằng **ngữ nghĩa của chính mô hình event**: cùng người tham gia + cùng kiểu + cùng thời gian = **một** event. Trong mô hình fact-list đây phải là một bước tiền xử lý riêng; trong mô hình event nó là hệ quả của định nghĩa node. ### Ở mức `.rules` (trước khi lọc 0.9): 6/8 khớp, 2 chỗ lệch — đã truy nguyên || PaTeCon | ta |
|---|---|---|
| `P26` SP1 functional | 344/451 = 0.762749 | 345/452 = 0.763274 |
| `P26` SP2 inverse functional | 148/168 = **0.880952** | 607/627 = **0.968102** |

Nguyên nhân chính là **bất đối xứng trong chính mã của PaTeCon**:

```python
# inverse_functional_mining, dòng 278
if len(v.bePointedTo) < 2:
   continue                    # LOAI nhom don tri khoi mau so

# functional_mining — KHONG co dieu kien tuong ung: nhom don tri VAN duoc dem
```

Hai mẫu là ảnh gương của nhau nhưng **đếm mẫu số khác nhau**. Trong công thức event-centric
chúng là **cùng một phép chạy trên hai vai**, nên bất đối xứng này không thể xảy ra.

Hệ quả trên WD50K: `P26` inverse functional được 0.968 thay vì 0.881, **vượt ngưỡng 0.9**,
nên miner của ta xuất **7** constraint thay vì 6. Đây không phải "hơn họ" mà là hệ quả cấu
trúc của phép ánh xạ — và nó nhất quán với chính SP1 của họ.

*(Còn một khác biệt dư: 168 vs 177 nhóm, do thêm bộ lọc trong reader của họ. Cả hai
constraint này đều dưới 0.9 trong lần chạy của họ nên không ảnh hưởng `.all_constraints`.)*

---

# 3. Bảng ánh xạ — mỗi template PaTeCon nghĩa là gì trên đồ thị event

| PaTeCon | trên đồ thị event-centric | ví dụ MAVEN |
|---|---|---|
| **SP1** `(a,r,b) & (a,r,c) ⟹ disjoint` | `x` giữ vai `r₁` trong **hai event cùng kiểu `T`**, với hai `r₂`-filler khác nhau | `Military_operation.AgentPatient`: một Agent không đánh hai Patient trong hai chiến dịch chồng thời gian |
| **SP2** `(a,r,b) & (c,r,b) ⟹ disjoint` |

**hai `r₁`-filler khác nhau** cùng chia một `r₂`-filler qua hai event | `Attack.AgentPatient`: hai bên tấn công cùng một mục tiêu thì hai cuộc tấn công không chồng nhau |
| **SP3** `(a,r1,b) & (a,r2,c) ⟹ before` | `x` tham gia hai event **khác kiểu / khác vai** | `Competition.Participant…` trước `Competition.Winner…` |
| **SP4** one-hop | chuỗi `x →(e₁) y →(e₂) w` qua entity trung gian | lan truyền thứ tự qua thực thể chung |
| **MutualExclusion** | `x` chỉ giữ vai `r₁` trong **đúng một** event kiểu `T` | `Competition.Winner`: một giải chỉ một người thắng |
| **Refinement** `(b,class,T)` | kiểu entity của `y` | MAVEN có sẵn **7 kiểu**: `Person` `Organization` `Location` `Product` `Art` `Building` `Other` |

Không đổi một dòng nào trong thuật toán mining. Chỉ đổi cách sinh statement.

---

# 4. Ba chỗ MAVEN khác Wikidata — nơi phải thiết kế riêng

|| Wikidata (PaTeCon) | MAVEN | hệ quả |
|---|---|---|---| | **entity** | toàn cục, dùng lại khắp nơi |

**document-local**, 0 entity vượt document | support mỗi `(entity, r)` bị chặn trong một bài. Cần cạnh `sameAs` xuyên document để gộp — đồ thị hiện có **7,189** cạnh |
| **từ vựng quan hệ** |

**6** property | 162 kiểu × 132 vai → **1,672** quan hệ ở P2 | support loãng. Đây là lý do phải đo để chọn chiếu, không copy được |
| **thời gian** | mọi fact có khoảng | phải **tự trích từ text** | xem §5 | ## Từ vựng loãng — dùng chính refinement của họ để giải PaTeCon đã có sẵn cơ chế **thô → mịn**: mine ở mức thô, cái nào conf rơi vào `[0.5, 0.9)` thì tinh chỉnh. Áp đúng vào bài toán từ vựng của MAVEN: ``` mine ở P4 (T, 161 quan hệ)          -> support dày, conf thô └─ conf ∈ [0.5, 0.9)  →  refine sang P3 (r₁r₂, 656) └─ conf ∈ [0.5, 0.9)  →  refine sang P2 (T.r₁r₂, 1672) └─ vẫn chưa đạt  →  refine bằng class_type entity (7 kiểu) ``` Đây là **thang refinement bốn tầng**, dùng nguyên cơ chế của PaTeCon, chỉ thay trục tinh chỉnh từ "kiểu entity" sang "độ đặc thù của quan hệ". Không phải thuật toán mới. --- # 5. Thời gian đến từ đâu (vì TIMEX là GT) ``` token thô ── bộ dò span thời gian (regex)  ── normaliser  ── khoảng của event │ nhãn TIMEX vàng ────────────────────────────────│ CHỈ để đánh giá ``` Trạng thái hiện tại (§4 của [README.md](README.md)): || ||---|---| | span thời gian tự tìm | P 61.0% · R 60.3% |
| normaliser trên span đúng |

**84.3%** (span vàng: 82.6%) |
| event có ≥1 anchor | 93.8% | --- # 6. Việc phải làm, theo thứ tự | # | việc | đầu ra |
|---|---|---|
| 1 |

Cài `π` (P2) vào `build.py` — sinh statement từ siêu cạnh | bảng `statement(a, r, b, t1, t2, src)` |
| 2 |

**Nối** bảng đó vào PaTeCon gốc, không sửa mã của họ | chạy `Constraint_Mining.py` như trên WD50K |
| 3 |

Đo bao nhiêu trong 42 quan hệ đạt support **còn** đủ support **sau khi lọc theo event có khoảng thời gian** | go / no-go |
| 4 |

Cài thang refinement bốn tầng §4 | constraint mịn dần |
| 5 | Đánh giá bằng ERE + TIMEX vàng | P / R |

**Mục 3 là cổng quyết định.** 42 quan hệ đạt support tính trên **cấu trúc**; nếu chỉ một
phần nhỏ event có khoảng thời gian giải được thì support thật sẽ thấp hơn nhiều. Phải đo
trước khi cài phần còn lại.

---

# 7. File

`proj_study.py` — bốn phép chiếu, đếm thô ·
`proj_study2.py` — đếm đúng (yêu cầu ≥2 event khác nhau) ·
`schema.py` `extract.py` `build.py` — đồ thị hiện có
