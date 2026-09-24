# Event = node có cấu trúc class → dàn view → khám phá pattern bottom-up

**Kiến trúc:** mọi event là một node mang đầy đủ thuộc tính kiểu OOP. Mỗi **tập thuộc tính**
sinh một **view** (subgraph theo chữ ký). Pattern được mine trong từng view.

```
EventClass.ATTRS = [etype, n_role, roleset, top_role, etypeset,
                   has_person, has_org, has_loc,
                   n_anchor, gran_set, method_set, anchor_src, sent_bucket]

view V_A  :  chữ ký của event = (getattr(ev, a) for a in A)
```

P1/P2/P3/P4 trước đây chỉ là **bốn điểm** trong dàn này:

| phép chiếu cũ | = view |
|---|---| | P4 `T` | `V{etype}` |
| P3 `r₁r₂` | `V{roleset}` | | P2 `T.r₁r₂` | `V{etype, roleset}` |
| — | `V{etype, etypeset}`, `V{etype, gran_set}`, … (mới) | → **Refinement của PaTeCon = phép tìm kiếm đi lên trong dàn.** Có nguyên tắc, không ad-hoc. ## Đảo chiều so với PaTeCon || ||---|---| | PaTeCon | liệt kê pattern (SP1–SP4) **trước** → tìm conflict |
| ở đây |

**đánh dấu conflict trước** → phát hiện pattern nào *thật sự* mang conflict |

Định nghĩa conflict **giữ nguyên của họ** (trivalent, chứng minh dương tính). Nhãn dùng để
khám phá là **E4** — intra-event anchor giao rỗng — vì nó định nghĩa được **không cần mine
constraint trước** (không vòng tròn), và là pattern PaTeCon **không biểu diễn được**.

---

# 1.  Lần quét đầu bị RÒ RỈ NHÃN — đã bắt và sửa

Lần đầu quét cả `n_anchor` vào dàn, ra toàn pattern lift 5.5× với conflict 100%:

```
lift 5.49x | conflict 100.0% | sup 62 | n_anchor=4 & gran_set=day
lift 5.21x | conflict  93.7% | sup 205 | etype=Hostile_encounter & n_anchor=4
```

**Đây là tautology số học, không phải pattern.** `n_anchor` bị cap ở 4 nên `n_anchor=4`
nghĩa là "≥4 anchor"; càng nhiều anchor thì giao càng dễ rỗng:

| số anchor | event | conflict |
|---|---|---|
| 2 | 8,963 | **8.7%** |
| 3 | 2,836 | 21.6% |
| 4 | 955 | 34.0% |
| 5 | 441 | 52.2% |
| ≥6 | 472 | **84.5%** | `method_set=gazetteer|refprop|regex` (3 phương pháp) và `gran_set=day|month|year` (3 hạt độ)
cũng **ngụ ý ≥3 anchor** → cùng một rò rỉ.

**Sửa:** phân tầng theo số anchor. Trong tầng `k=2`, `gran_set`/`method_set` tối đa 2 giá trị
nên bản số không còn rò rỉ.

*(Bắt được nhờ quy tắc AUDIT #1: kết quả đẹp bất ngờ → giả định là bug.)*

---

# 2. Pattern phát hiện được sau phân tầng

## Tầng k=2 (8,963 event, nền 8.7%) — trục **provenance** thắng

| lift (WLB) | conflict | sup | chữ ký |
|---|---|---|---| | **5.18×** | 57.9% | 57 | `has_org=1 & method_set=refprop` |
| 4.67× | 50.0% | 104 | `has_loc=1 & method_set=refprop` | | 4.29× | 45.0% | 151 | `gran_set=day & method_set=refprop` |
| 4.04× | 43.9% | 114 | `method_set=refprop & sent_bucket=dau` | | **3.63×** | 37.3% | 249 | `method_set=refprop` (một mình) | 212 chữ ký vượt nền.

**`method_set=refprop` là tín hiệu mạnh nhất** — và nó **khớp với một phép đo độc lập trước
đó**: anchor có suy diễn tham chiếu cho conflict 23.75%, anchor regex thuần 7.27%, chênh
**3.3×**. Hai đường đo khác nhau ra cùng kết luận.

→ Nghĩa là: **một phần lớn "conflict" ở tầng này là artifact của suy diễn chuỗi tham chiếu,
không phải xung đột thật.** Đây là kết quả dùng được ngay — nó nói chỗ nào cần siết.

## Tầng k=3 (2,836 event, nền 21.6%) — trục **ngữ nghĩa** thắng

| lift (WLB) | conflict | sup | chữ ký |
|---|---|---|---| | 2.74× | 71.4% | 63 | `gran_set=day & sent_bucket=dau` |
| **2.51×** | 70.3% | 37 | `etype=Military_operation` | | 2.45× | 66.1% | 56 | `etype=Hostile_encounter & method_set=regex` |
| 2.40× | 62.2% | 90 | `etype=Hostile_encounter & sent_bucket=dau` | | 2.23× | 63.4% | 41 | `etype=Hostile_encounter & n_role=3` | 177 chữ ký vượt nền.

**`Military_operation` và `Hostile_encounter` là sự kiện KÉO DÀI, nhiều pha.** Nhiều anchor
của chúng trải trên một quãng dài là **đúng**, không phải lỗi — nhưng phép **giao** cho ra
rỗng.

→ Phát hiện thiết kế: **ngữ nghĩa giao là SAI cho sự kiện kéo dài.** Với chúng phép đúng là
**bao (hull/union)**, không phải giao. Và `etype` chính là thứ nhận diện được nhóm này.

Đây đúng vấn đề đã nêu từ đầu về sự kiện lặp/kéo dài ("lịch họp thường niên… cùng loại thì
cũng không gọi là sai") — nhưng lần này **tìm ra bằng dữ liệu**, không phải bằng trực giác.

---

# 2b.  Pattern HỢP THÀNH — nhiều tầng, nhiều dạng điều kiện

Bản §2 chỉ có **một dạng** điều kiện (`attr == value`) trên **một tầng** (event). Đó cũng
chính là lý do lực lượng bị rò rỉ: `gran_set='day|month'` bị so bằng chuỗi, nên "có 2 hạt độ"
lẫn vào điều kiện dạng thức.

Tách ra **ba tầng** × **năm dạng điều kiện** (`compose.py`):

| tầng | thuộc tính |
|---|---| | `T_event` | `etype`, `n_role`, `sent_bucket` |
| `T_entity` | `etypeset`, `roleset`, `has_person/org/loc` | | `T_anchor` | `gran[]`, `method[]` |
| dạng | nghĩa |
|---|---| | `EQ` | `attr == v` — dạng thức |
| `HAS` | `v ∈ attr` — thành viên (cho thuộc tính tập) | | `ALL` | mọi phần tử `attr == v` — phổ quát |
| `CNT` | `\|distinct attr\| ≥ k` — **lực lượng, tách riêng** | | `MIX` | tồn tại cặp phần tử khác nhau — bất đồng nhất |

Hợp thành bằng **beam search** đến độ sâu 3, trong từng tầng số anchor, chấm bằng Wilson LB.

##  Rò rỉ nhãn lần thứ HAI — `hull`, và lần này có chứng minh

Lần đầu chạy có thêm trục `hull` (bề rộng bao) và ra:

```
lift 11.16x | conf 100.0% | sup 125 |

ALL(gran=day) AND hull>=30 ngày
```

**Tautology.** Ở tầng $k=2$ với hai anchor $[a_1,b_1],[a_2,b_2]$:

$$\text{conflict} \iff \max(a_i) > \min(b_i), \qquad \texttt{hull} = \max(b_i)-\min(a_i)$$

Nếu **cả hai** anchor hạt độ ngày thì $a_i=b_i$, nên $\texttt{hull}=|d_1-d_2|$ và

$$\texttt{hull} > 0 \iff d_1 \neq d_2 \iff \text{conflict}$$

`hull ≥ 30` **kéo theo** conflict. `hull` là **thống kê của chính đại lượng đang được kiểm
tra**, không phải thuộc tính độc lập. Đã bỏ khỏi tập điều kiện.

*(Đây là lần thứ hai trong cùng mạch việc: trước là `n_anchor`, giờ là `hull`. Cùng một lớp
lỗi — đặc trưng dẫn xuất từ nhãn. Quy tắc bổ sung ở cuối.)*

## Kết quả sau khi bỏ `hull`

### Tầng k=2 (8,963 event, nền 8.7%)

| lift | conf | sup | tầng | hợp thành |
|---|---|---|---|---|
| **6.32×** | 71.4% | 35 | 2 | `ALL(method=refprop)` ∧ `CNT(etypeset≥2)` ∧ `has_org=1` |
| 6.16× | 69.2% | 39 | 2 | `ALL(method=refprop)` ∧ `CNT(etypeset≥2)` |
| 6.07× | 65.1% | 63 | 2 | `ALL(method=refprop)` ∧ `has_loc=1` ∧ `ALL(gran=day)` |

**So với điều kiện đơn:** `method=refprop` một mình cho **3.63×** (§2). Hợp thành đẩy lên
**6.32×** — **gần gấp đôi**.

Đọc được: *cả hai anchor đều do suy diễn tham chiếu sinh ra* **và** *event có ≥2 kiểu entity
khác nhau* → 71.4% giao rỗng. Hai tầng khác nhau cùng góp.

### Tầng k=3 (2,836 event, nền 21.6%)

| lift | conf | sup | tầng | hợp thành |
|---|---|---|---|---|
| **3.12×** | 83.9% | 31 | 2 | `etype=Hostile_encounter` ∧ `HAS(gran=month)` ∧ `sent_bucket=dau` |
| 3.04× | 78.2% | 55 |

**3** | `ALL(gran=day)` ∧ `sent_bucket=dau` ∧ `has_person=0` |
| 2.90× | 80.0% | 30 | 2 | `etype=Military_operation` ∧ `HAS(gran=day)` |
| 2.85× | 76.9% | 39 |

**3** | `etype=Hostile_encounter` ∧ `ALL(method=regex)` ∧ `HAS(roleset=Location)` |

**Pattern 3 tầng xuất hiện trong top** — hợp thành không chỉ là cộng dồn, nó bắt được tương
tác giữa tầng anchor, tầng entity và tầng event.

72 hợp thành vượt nền ở k=2, 76 ở k=3.

## Vì sao đây là dạng đúng của "constraint mining algorithm"

Ngôn ngữ pattern của PaTeCon chỉ có **một dạng**: đồng nhất biến trên đồ thị nhị phân
(`a` xuất hiện ở hai statement). Không có `ALL`, không có `CNT`, không có tầng.

Ở đây pattern là **công thức hội** trên ba tầng với năm dạng vị từ — SP1–SP4 của họ là
trường hợp riêng (chỉ dạng `EQ`, chỉ tầng quan hệ). Thuật toán mining là **beam search trên
dàn hợp thành**, chấm bằng Wilson LB so với nền của tầng.

Định nghĩa conflict vẫn **vay nguyên vẹn**.

---

# 3. Vì sao cách này đúng hơn "dịch constraint"

|| dịch constraint (bản trước) | khám phá trên dàn view (bản này) |
|---|---|---|
| không gian pattern | cố định = SP1–SP4 của họ | sinh bởi thuộc tính class, **SP1–SP4 là tập con** |
| chiều làm việc | pattern → conflict | **conflict → pattern** |
| refinement | ad-hoc chọn P4→P3→P2 | **đi lên trong dàn**, có nguyên tắc |
| pattern PaTeCon không có | phải nêu bằng lập luận | **tìm được bằng số** (E4 + hai trục trên) |

Định nghĩa conflict vẫn **vay nguyên vẹn**, kiểm chứng **6/6 chính xác** trên Wikidata
(`mine_patecon.py`). Cái mới là **loại đồ thị** và **cách tìm pattern trên đó**.

---

# 4. Việc tiếp theo

| # | việc | vì sao |
|---|---|---|
| 1 |

Thêm ngữ nghĩa **hull** cho `etype` kéo dài, cạnh ngữ nghĩa **giao** | tầng k=3 cho thấy giao sai với `Military_operation`/`Hostile_encounter` |
| 2 |

Siết anchor `refprop` (hoặc hạ conf) | tầng k=2: refprop lift 3.63× — artifact, không phải conflict |
| 3 |

Mở dàn lên 3 chiều + tìm kiếm có cắt tỉa | hiện chỉ quét max 2 chiều, đã ra 212+177 chữ ký |
| 4 |

Áp pattern đã học lên graph **dựng từ text** | hiện học trên anchor ERE vàng (hợp lệ: học dùng nhãn, suy diễn không) |
| 5 |

Lặp lại cho E5 (đồng tham gia n-ary) và E6 (tập vai) | chưa đo |

## File

`views.py` — `EventClass` + dàn view + `e4_conflict` + Wilson ·
`discover.py` — quét lần đầu (có rò rỉ, giữ làm chứng cứ) ·
`discover2.py` — bản phân tầng, đúng
