# Đồ thị event-centric từ text thô — thiết kế và kết quả

**Quy trình đúng như yêu cầu:**

```
text thô ── trích xuất ── ĐỒ THỊ ── lưu trữ ── mining ── kiểm chứng trên TIMEX

                                       nhãn vàng CHỈ xuất hiện ở đây ┘
```

Nhãn TIMEX/event/ERE **không bao giờ** vào đồ thị. Chúng là **tập kiểm chứng**.

---

# 1. Hai bài đọc và những gì lấy được

## SEM (van Hage 2011)

| thành phần | nội dung |
|---|---| | 4 core class | `sem:Event` `sem:Actor` `sem:Place` `sem:Time` |
| hệ Type | mỗi core class có `sem:XType` tương ứng, mượn từ vocabulary ngoài | | 3 Constraint | `sem:Role` (vai gắn với event) · `sem:Temporary` (khoảng hiệu lực) · `sem:View` (quan điểm) |
| Authority | `sem:accordingTo` → theo ai thì phát biểu này đúng | | **7 timestamp** | point: `hasTimeStamp` · interval: `hasBegin/EndTimeStamp` · **bất định (4 giá trị)**: `hasEarliestBegin` `hasLatestBegin` `hasEarliestEnd` `hasLatestEnd` |

**Hai quyết định thiết kế quan trọng nhất, lấy nguyên:**

1. **Cố ý không khai báo functional property.** Trích nguyên văn: *"you might gather various
  birth dates for a single person… we do not want this to break our system"* và
  *"Conflicting views can exist at the same time and be compared, but they are not
  automatically resolved. Much of the responsibility of enforcing consistency is taken
  from the SEM and given to the application layer."*

  → SEM **giữ nguyên** dữ liệu mâu thuẫn thay vì loại bỏ, và đẩy việc phát hiện lên tầng
  ứng dụng. Đây **chính xác** là nền mà bài toán phát hiện xung đột cần. Một schema có
  ràng buộc cứng sẽ vứt bỏ chính thứ ta muốn tìm.

2. **Thời gian ký hiệu vs giá trị.** Có thể nói "A xảy ra sau B" mà không cần biết khi nào.
  → tương ứng cạnh thứ tự không có mốc, biểu diễn bằng `bounds() = None`.

**SEM không có:** quan hệ event–event (nhân quả, thứ tự) — tự nhận ngoài phạm vi.

## ECS-KG (Lakshika 2025, D&KE 159)

Dựng **trên** SEM. Sáu giai đoạn: tiền xử lý → trích xuất → triple → dựng KG + embedding →
temporal GNN → GAT. Dữ liệu CNN/DailyMail.

| điểm | nội dung |
|---|---| | node | `ArticleX`, `evt_X`, `evt:subject/object/argument/entity`, `evt:namedEntity` (person/org/location), `evt:date_time`, `metadata`, `art_attr:title` |
| quan hệ | `⟨hasEvent⟩` `⟨hasMetaData⟩` `⟨hasTitle⟩` `⟨role:predicate⟩` `⟨role:temp.Data⟩` `⟨similarTopic⟩` | | **role** | lấy từ **nhãn dependency spaCy** (`role:token.dep_`) — không cần ontology vai cố định |
| trích xuất | `en_core_web_sm`: POS + NER + dependency. Toàn bộ từ text thô | | thời gian | DATE/TIME/SET/DURATION; **cả entity và argument đều được gắn thời gian**, không chỉ event |
| node type | one-hot 8 chiều | **Điểm mượn:** role tự do từ cú pháp (không cần vai định trước), node thời gian riêng, tầng article/topic cho liên kết xuyên bài. ## Chỗ trống cả hai để lại SEM giữ mâu thuẫn nhưng **không phát hiện**. ECS-KG **không đụng đến** xung đột. Không bên nào mô hình hoá ngữ nghĩa xung đột có tính bất định. Đó là phần đóng góp. --- # 2. Thuộc tính node kiểu OOP `schema.py` — descriptor `Attr` khai báo ở cấp class, metaclass gom theo thừa kế. ```python class Event(Node): etype    = Attr(str, doc='sem:eventType', index=True) trigger  = Attr(str, doc='tu kich hoat') polarity = Attr(str, default='POS', doc='POS / NEG') modality = Attr(str, default='ACTUAL', doc='ACTUAL / HYPOTHETICAL / REPORTED') topic    = Attr(str, doc='chu de bai bao', index=True) ``` **Thêm một thuộc tính = thêm một dòng.** Sau dòng đó tự động có: default, ép kiểu, chỉ mục tra cứu, serialize khi `save()`, deserialize khi `load()`, và mô tả trong `schema()`. Không phải sửa `build()`, `save()`, `load()`, hay hàm validate nào. Đã kiểm chứng (`demo_oop.py`): ``` gan chuoi "0.8" -> tu ep kieu: 0.8 chan sai kieu  : Event.sent_id can kieu int, nhan 'khong phai so' chan thuoc tinh la: Event khong co thuoc tinh 'mau_sac' ``` Bảy timestamp của SEM quy về `(lo, hi)` bằng **một** phương thức `bounds()`: | khai báo | `bounds()` |
|---|---| | `eb=19470101, le=19471231` | `(19470101, 19471231)` |
| `stamp=19470721` | `(19470721, 19470721)` | | `gran='unknown'` (ký hiệu) | `None` → `is_symbolic() = True` |

`UTime(lo,hi)` cũ là trường hợp riêng. Thời gian ký hiệu được biểu diễn tự nhiên thay vì
phải đặt cờ riêng.

---

# 3. Đồ thị dựng được (725 document test, chỉ token thô)

| node | số lượng |
|---|---| | Event | **23,740** |
| Actor | 19,460 | | TimeX | 4,009 |
| cạnh | số lượng |
|---|---| | hasActor | 38,506 |
| hasTime | 29,475 | | NARRATIVE_BEFORE | 21,426 |
| BEFORE / AFTER | 1,455 / 134 | | sameAs (xuyên document) | 7,189 |

**47,209 node · 98,185 cạnh · dựng 1.8s · lưu 30.3 MB · tải lại 1.8s**

## Thay thế từng thành phần khi không có spaCy

| ECS-KG dùng | ở đây dùng | ghi chú |
|---|---|---|
| spaCy NER | chuỗi token viết hoa | thuần quy tắc |
| spaCy dependency (role) | vị trí so với trigger (`agentish`/`patientish`) | **xấp xỉ yếu, đã ghi rõ** |
| spaCy POS (trigger) | từ điển trigger **học từ split train** | hợp lệ: học dùng nhãn, suy diễn không |
| trích xuất thời gian | 12 họ regex trên token thô | tự tìm, không dùng span vàng |

---

# 4. Kiểm chứng trên nhãn vàng

| # | thành phần | P | R | F1 |
|---|---|---|---|---|
| 1 | span thời gian (khớp chính xác) | 61.0% | 60.3% | **60.6%** |
| 1' | span thời gian (khớp chồng lấn) | 75.5% | — | — |
| 2 | trigger sự kiện | 65.6% | 87.6% | **75.0%** |
| 3 | gán thời gian (`hasTime` vs ERE CONTAINS) | 11.4% | 24.4% | — |
| 4 | thứ tự (`BEFORE` vs ERE BEFORE) | 14.2% | 3.0% | — |

Tìm được **4,009** span thời gian, vàng có **4,058** — số lượng gần khớp, sai ở chỗ nào.

## Độ phủ thời gian — điểm mạnh bất ngờ

|| đồ thị này | ERE vàng |
|---|---|---|
| sự kiện có ≥1 anchor |

**93.8%** | 43.8% |
| sự kiện có interval giải được |

**66.5%** (15,795/23,740) | — |
| sự kiện có ≥2 anchor | 12.2% | 0.4% |
| TimeX chuẩn hoá được | 65.6% thô → **84.3%** (xem §4.1) | 82.6% (trên span vàng, cùng tập test) |

## 4.1  ĐÍNH CHÍNH — 65.6% là chẩn đoán SAI

Bản trước ghi "kéo chuẩn hoá TimeX 65.6% → 91.3%" là **việc cần làm**. Sai. Đo tách nguyên
nhân (`diag_norm.py`, `diag_norm2.py`) cho thấy **normaliser không có vấn đề gì**:

| nguồn span (cùng normaliser, cùng 725 doc) | chuẩn hoá được |
|---|---| | span **vàng** | 82.6% |
| span ta tìm **đúng biên** |

**83.4%** |
| span ta tìm **sai biên** | 37.7% | Cho span đúng thì normaliser ra **83.4%** — ngang span vàng. Khoảng cách đến từ **bộ dò span**, không phải normaliser. Hơn nữa, mẫu số 65.6% bị tính sai vì gộp cả những span **về bản chất không thể có mốc**: | bản chất span (SEM) | số | tỉ lệ | quy ra mốc được |
|---|---|---|---| | **ABSOLUTE** — cần có mốc | 2,984 | 74.4% | **84.3%** |
| **SYMBOLIC** — chỉ biết thứ tự (`later`, `then`, `subsequently`) | 652 | 16.3% | không thể, theo định nghĩa | | **DURATION** — độ dài (`three days`) | 333 | 8.3% | không thể |
| **SET** — lặp lại (`annually`) | 40 | 1.0% | không thể | **25.6% span không thể có mốc.** SEM gọi chúng là *symbolic time* và schema ở đây **đã hỗ trợ sẵn** qua `bounds() = None` / `is_symbolic() = True` — chỉ là `build()` đang đếm chúng như thất bại thay vì gán đúng loại. ### Việc thật sự cần làm ở tầng thời gian | # | việc | bằng chứng |
|---|---|---|
| 1 |

Gán SYMBOLIC/DURATION/SET đúng loại thay vì coi là hỏng | 1,025 span (25.6%) đang bị tính oan |
| 2 |

Chặn dương tính giả tháng/mùa trần | `may` 17 · `winter` 13 · `march` 12 · `summer` 11 — phần lớn **vàng không annotate** |
| 3 |

Nới chuỗi tham chiếu cho tháng trần **có** trong vàng | `november` 6 · `june` 5 · `september 2` 5 — thiếu năm tham chiếu |

**Không có mục nào là "sửa normaliser".**

> Nền thời gian **rộng hơn hẳn** so với dùng nhãn ERE. Vấn đề là **độ chính xác**, không
> phải độ phủ — ngược hẳn với chẩn đoán trước đây.

---

# 5. Mining trên đồ thị này

19,516 cặp sự kiện có interval · 8,219 chữ ký · **669** đạt sup≥5 và doc≥3.

Mười ràng buộc **chồng lấn** mạnh nhất (Wilson lower bound):

| WLB | chồng lấn | sup | doc | chữ ký |
|---|---|---|---|---|
| 0.981 | 100.0% | 195 | 66 | `Hostile_encounter/patientish × Hostile_encounter/agentish` |
| 0.977 | 100.0% | 164 | 66 | `Hostile_encounter/patientish × Hostile_encounter/patientish` |
| 0.972 | 100.0% | 132 | 53 | `Catastrophe/patientish × Catastrophe/agentish` |
| 0.967 | 100.0% | 112 | 35 | `Competition/patientish × Competition/agentish` |

Đây là **ràng buộc đúng** (hai sự kiện cùng loại chung một actor thì trùng thời gian) —
đúng hướng "mine constraint đúng, mâu thuẫn với nó là sai" đã bàn.

## Xung đột phát hiện được

| loại | số |
|---|---| | T5 hạt độ | 2,432 |
| T4 rời nhau | 638 | | T3 thứ tự | 133 |

---

# 6.  Kiểm chứng xung đột — KHÔNG đạt

| T5 |
||---|---|
| sự kiện gắn cờ | 2,432 | | khớp vị trí sự kiện vàng | 667 |
| vàng thật sự có ≥2 anchor | 347 (52.0%) | | tỉ lệ nền | 47.4% |
| **lift** |

**1.10×** |

Gần như **không có tín hiệu**.

| T3 | số |
|---|---| | cặp gắn cờ | 133 |
| vàng xác nhận **ngược** (ta đúng) | 7 | | vàng nói **cùng chiều** (ta sai) | 23 |
| vàng không nói gì | 103 | | **precision trên phần quyết định được** | **23.3%** |

## Chẩn đoán: 23 vs 7 nói lên điều gì

Quy tắc T3 bắn khi cạnh nói `BEFORE(a,b)` nhưng interval nói `a` bắt đầu sau khi `b` kết thúc.

- Vàng **xác nhận** `BEFORE(a,b)` (23 ca) → cạnh đúng, **thời gian ta trích sai**
- Vàng nói **ngược** (7 ca) → thời gian đúng, cạnh sai

**23/30 = 77% xung đột T3 đến từ trích xuất thời gian sai, không phải xung đột thật.**

Khớp với chuẩn hoá TimeX chỉ đạt 65.6% và trùng khớp với kết luận từ luật khuếch đại lỗi
ở [NO_ERE.md](../NO_ERE.md): **nút thắt là chất lượng thời gian, không phải kiến trúc đồ thị.**

---

# 7. Đánh giá

## Được

Toàn tuyến **text thô → đồ thị → lưu → mining → kiểm chứng** chạy thật, 725 document, 2.7s
Nhãn vàng **không** vào đồ thị — không còn vòng luẩn quẩn dùng TIMEX cả để dựng lẫn để đo
Schema OOP: thêm/sửa thuộc tính = một dòng, đã kiểm chứng
Bảy timestamp SEM tổng quát hoá `UTime(lo,hi)`; thời gian ký hiệu biểu diễn tự nhiên
Độ phủ anchor **93.8%** — gấp 2.1× so với dùng nhãn ERE
Trigger F1 **75.0%**, span thời gian F1 **60.6%** — đủ dùng làm nền
Mining ra 669 ràng buộc, nhóm mạnh nhất hợp lý về ngữ nghĩa

## Chưa được

Gán thời gian cho sự kiện P **11.4%** — sinh thừa (29,475 dự đoán vs 13,829 vàng)
Cạnh thứ tự P **14.2%** — thứ tự trần thuật là proxy yếu
T5 lift **1.10×** — gần như không có tín hiệu
T3 precision **23.3%**, và 77% xung đột đến từ thời gian trích sai

## Việc tiếp theo, theo thứ tự tác động

| # | việc | vì sao |
|---|---|---|
| 1 |

Đưa **model gán TIMEX** (exp42, F1 47.5%) vào `build()` làm bộ chấm điểm cạnh `hasTime` | thay quy tắc "mọi TIMEX cùng câu" — P hiện 11.4% |
| 2 |

**Bộ dò span** thời gian (P 61.0%) — chặn dương tính giả tháng/mùa trần | §4.1: normaliser đã đạt 84.3%, nút thắt nằm ở dò span |
| 3 |

Gán SYMBOLIC/DURATION/SET đúng loại (`is_symbolic()` đã có) | 1,025 span đang bị tính oan là hỏng |
| 4 | Thay thứ tự trần thuật bằng model quan hệ thời gian | P 14.2% |
| 5 |

Thêm `sem:View` + `sem:Authority` vào cạnh | đang có chỗ trong schema, chưa dùng |

**Mọi mục dùng lại nguyên thứ đã có** — không cần thư viện mới.

>  **Đính chính so với bản trước:** mục "nâng chuẩn hoá TimeX" đã bị **gỡ** — xem §4.1.
> Normaliser đạt 83.4% trên span đúng, ngang span vàng 82.6%. Chẩn đoán ban đầu sai vì
> so 65.6% (mẫu số gộp cả symbolic/duration) với 91.3% (đo trên tập khác, span vàng).

---

# 8. File

| file | nội dung |
|---|---| | `schema.py` | descriptor `Attr`, metaclass, `Node`/`Event`/`Actor`/`Place`/`TimeX`, `Edge`, `Constraint` |
| `extract.py` | text thô → mention (12 họ regex thời gian, thực thể viết hoa, từ điển trigger) | | `build.py` | mention → đồ thị, lưu/tải JSONL |
| `run_build.py` | chạy toàn tuyến + kiểm chứng 5 mục | | `mine.py` | mining + phát hiện xung đột + kiểm chứng T3/T5 |
| `demo_oop.py` | kiểm chứng phần OOP |