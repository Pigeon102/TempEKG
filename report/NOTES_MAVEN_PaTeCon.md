# Ghi chú tổng hợp: MAVEN-ERE, MAVEN-Arg, PaTeCon và hướng mining constraint

Toàn bộ số liệu dưới đây đo trực tiếp trên dữ liệu thật (`MAVEN-Arg.zip`, `MAVEN_ERE.zip`), không phải ước lượng.

---

# 1. MAVEN-ERE — có gì

## Cấu trúc top-level

```
{
  id, title,
  tokens,               // list câu, mỗi câu là list token
  sentences,            // list câu dạng string
  events,               // event + coreference chain (KHÔNG có argument/role)
  TIMEX,                // biểu thức thời gian, CHƯA chuẩn hoá thành số
  temporal_relations,   // 6 loại, giữa EVENT và/hoặc TIMEX
  causal_relations,     // CAUSE, PRECONDITION
  subevent_relations    // quan hệ part-whole
}
```

## Event

```json
{
  "id": "EVENT_...",
  "type": "Traveling", "type_id": 26,
  "mention": [ {"trigger_word": "Tour", "sent_id": 1, "offset": [0,1]}, ... ]
}
```

Một event = **một coreference chain**, nhiều mention. Ví dụ event `Publishing` có 4 mention:
`release` / `released` / `release` / `releasing` ở 4 câu khác nhau → cùng **một** `event.id`.

## TIMEX

```json
{"id": "TIME_...", "mention": "1860", "type": "DATE", "sent_id": 0, "offset": [24,25]}
```

Loại: `DATE`, `DURATION`, `TIME`, `SET`, `PREPOSTEXP`. **Chỉ là text thô** — `"November 13 , 2012"`,
không phải `2012-11-13`. Không có trường chuẩn hoá số.

## temporal_relations — 6 loại

`BEFORE`, `BEGINS-ON`, `CONTAINS`, `ENDS-ON`, `OVERLAP`, `SIMULTANEOUS`

Mỗi phần tử là cặp `[id_a, id_b]`, **id có thể là EVENT hoặc TIMEX**.

## Quy mô đo được (train, 2913 doc)

| | số |
|---|---|
| Tổng cặp temporal | **792,445** |
| Có ít nhất 1 đầu là TIMEX | **308,901 (39%)** |
| Cả 2 đầu đều là EVENT | **483,544 (61%)** |

Phân bố theo loại:

| Relation | Tất cả | Chỉ EVENT-EVENT |
|---|---:|---:|
| BEFORE | 683,581 | 440,206 |
| CONTAINS | 95,933 | 35,923 |
| OVERLAP | 6,376 | 2,887 |
| SIMULTANEOUS | 5,821 | 4,170 |
| BEGINS-ON | 453 | 253 |
| ENDS-ON | 281 | 105 |

## causal_relations (train)

| | số |
|---|---|
| Doc có ≥1 causal | 2,828 / 2,913 (**97%**) |
| `CAUSE` | 6,797 |
| `PRECONDITION` | **29,519** (gấp 4.3× CAUSE) |

Kiểm tra 2,131 cặp CAUSE đầu: **89.1%** có kèm nhãn temporal cho cùng cặp, 10.9% không có.
→ causal và temporal là **hai trục độc lập**, không suy ra nhau tự động.

## CONTAINS — phân tích đầy đủ (train+valid, 3623 doc)

| | |
|---|---|
| Doc có ≥1 CONTAINS | **3,539 / 3,623 (97.7%)** |
| Tổng CONTAINS | **121,483** |
| Trung bình/doc | 33.5 · Median 20 · Max **591** |

Phân loại cặp:

| kiểu | số | % |
|---|---:|---:|
| **TIME → EVENT** | 58,691 | **48.3%** |
| EVENT → EVENT | 45,314 | 37.3% |
| TIME → TIME | 9,751 | 8.0% |
| EVENT → TIME | 7,727 | 6.4% |

**Gần một nửa CONTAINS là mốc thời gian chứa sự kiện** — đây là nguồn gán mốc thời gian
cho event tự nhiên nhất, sẵn có, không cần suy luận số.

Event type hay làm container: `Hostile_encounter` (11,359), `Catastrophe` (6,802),
`Competition` (4,467), `Military_operation` (4,394), `Attack` (3,173).
Hay bị chứa: `Attack` (4,709), `Motion` (3,880), `Competition` (3,762), `Conquering` (3,242).

TIME→TIME: `DATE→DATE` 5,300 (granularity lồng nhau), **`DURATION→DATE` 2,397**
(loại PaTeCon không xử lý được vì DURATION không có `(t_start, t_end)` tuyệt đối).

---

# 2. MAVEN-Arg — có gì

## Cấu trúc top-level

```
{
  id, title,
  document,            // TOÀN VĂN dạng string (tokenize sẵn, nối bằng space)
  events,              // event + ARGUMENT (khác ERE)
  entities,            // entity đã coref trong-document
  negative_triggers    // token đã xét nhưng KHÔNG phải trigger
}
```

**Khác biệt toạ độ quan trọng:** MAVEN-Arg dùng **offset ký tự** trên `document`;
MAVEN-ERE dùng **(sent_id, token offset)**. Đã căn được (`role_ceiling.py` map 46,458 span).

## Event + argument

```json
{
  "id": "EVENT_...", "type": "Publishing", "type_id": 141,
  "mention": [...],
  "argument": {
    "Author":   [ {"entity_id": "ENTITY_..."} ],          // đã coref
    "Category": [ {"content": "album", "offset": [53,58]} ], // CHƯA coref, chỉ text span
    "Publisher": []                                        // rỗng nhưng key vẫn tồn tại
  }
}
```

**Quy tắc schema:** mỗi `event.type` có **bộ role cố định khai báo sẵn** (kiểu FrameNet).
Dù rỗng, key vẫn xuất hiện. Không event nào thiếu key so với type của nó.

Ba dạng filler của một role:
- `{"entity_id": ...}` — đã coref, dùng được ngay
- `{"content": ..., "offset": ...}` — text span thô, **không** nằm trong `entities` list
- `[]` — rỗng

**Một role có thể là mảng nhiều filler, và trộn cả hai dạng trong cùng role.**

## Entity

```json
{
  "id": "ENTITY_...",   // hash, CHỈ hợp lệ trong 1 document
  "type": "Location",   // 7 loại: Person, Organization, Location, Art, Product, Building, Other
  "mention": [ {"mention": "quarto", "offset": [197,203]}, ... ]
}
```

Coreference **trong-document**, không link ra Wikidata/DBpedia.

## Role — 143 loại

Top: `Agent` 43,775 (23.0%) · `Location` 38,244 (20.1%) · `Patient` 37,637 (19.8%)
→ **top-3 phủ 62.8%**, top-10 phủ 76.4%, top-20 phủ 85.7%, top-30 phủ 90.4%

**Không có role thời gian.** Trong 143 role không có `Time`/`Date`/`When`; chỉ có
`Duration` với **33 instance** toàn dataset.

Chỉ **40.4%** argument có `entity_id`; 59.6% còn lại chỉ là `content`+`offset`.

## Số entity trên mỗi event (64,923 event, train)

| số entity/event | số event | % |
|---|---:|---:|
| **0** | 24,092 | **37.1%** |
| **1** | 20,505 | **31.6%** |
| 2 | 12,257 | 18.9% |
| 3 | 5,042 | 7.8% |
| ≥4 | 3,027 | 4.6% |

Max quan sát: **59 entity trong 1 event** (role dạng danh sách như `Participants`).

**Chỉ 31.3% (20,326/64,923) event có ≥2 role mang `entity_id`** → đủ điều kiện tối thiểu
tạo statement PaTeCon-shape. **68.7% bị loại ngay từ đầu.**

Số role khai báo/event: trung bình 3–4 slot, nhưng phần lớn rỗng hoặc chỉ text thô.

Max type distinct trong 1 event: **4** (toàn dataset, không có event nào đạt 5).

---

# 3. PaTeCon — có gì

Statement phẳng: `(subject_QID, property, object, t_start, t_end)`.

| | PaTeCon (Wikidata) | MAVEN |
|---|---|---|
| đơn vị | fact nhị phân | event n-ary có vai |
| entity | **QID toàn cục**, lặp khắp KB | `entity_id` chỉ trong 1 document |
| vai | **cố định 2**: subject, object | 143 role, thay đổi theo event type |
| vai có luôn là entity | có | **không** — nhiều role chỉ là text span |
| thời gian | **khoảng số tường minh** `[t1,t2]` | TIMEX text thô, chưa chuẩn hoá |
| quan hệ temporal | **không có sẵn** — tự mine bằng so khoảng số | **có sẵn** nhãn, nhưng là nhãn cặp instance |

Cỗ máy suy luận: `Interval_Relations.py` so sánh số học (`comp_time`, `disjoint`) trên
khoảng số. **Không chạy được trực tiếp trên MAVEN** vì TIMEX chưa thành số.

---

# 4. Bất cập khi dựng MAVEN theo khuôn PaTeCon

## Tầng Entity
`entity_id` không xuyên document → support cực thấp nếu mine trong-doc.
**Bằng chứng:** `ENTITY_ea69516a...` (Elbow, ban nhạc) chỉ tồn tại ở 1 doc; doc khác có
`"Elbow"` là **sông Elbow River** với ID khác, type khác (Organization vs Location).
→ String-match xuyên document **phải kèm ràng buộc `type`**, nếu không sẽ trộn nhầm.

## Tầng Vai
- Không có trục vai chung (subject/object) — mỗi event type có bộ role riêng
- Không phải role nào cũng có `entity_id` (59.6% chỉ là text)
- 68.7% event không đủ 2 entity-role để tạo statement

Ba chính sách chọn cặp vai:
- **A. Vét cạn** — nổ tổ hợp (event 59 entity → 1,711 statement), nhiều cặp vô nghĩa
- **B. Bảng ưu tiên theo event type** — cần lập tay ~168 type, nhưng ngữ nghĩa sạch nhất
- **C. Lấy 2 role đầu theo thứ tự JSON** — đơn giản nhất, nhưng cặp vô nghĩa

**Khuyến nghị: B.**

## Tầng Thời gian
TIMEX chưa chuẩn hoá → `Interval_Relations.py` không chạy trực tiếp.
`DURATION` không quy được về `(t_start, t_end)` tuyệt đối.

## Bất cập về đơn vị đánh giá
PaTeCon chấm điểm ở mức **constraint/rule**; MAVEN-ERE cho nhãn ở mức **cặp instance**.
Cần quyết định chấm theo constraint-level hay instance-level.

## Bất cập về coreference chưa triệt để
Sự kiện thật giống nhau có thể tách thành nhiều event_id, nối bằng `CONTAINS`/`SUBEVENT`
chứ không coref gộp. **Phải dùng `subevent_relations` để dedupe theo phân cấp**, không
phải theo trùng lặp bề mặt.

## Lỗi NER trong dữ liệu
- `the United Kingdom` gán type `Organization` (đúng ra Location)
- `OBS`, `VGTRK` (đài truyền hình) gán type `Art` (đúng ra Organization)
→ `entity.type` **không đáng tin tuyệt đối** nếu dùng làm điều kiện lọc.

---

# 5. Ba cách build để mining constraint (không cần fake data)

**Cách 1 — Chuẩn hoá TIMEX, giữ nguyên Interval_Relations**
Parse `"1860"` → `(1860-01-01, 1860-12-31)`. Chạy PaTeCon nguyên bản.
Được: đúng cơ chế 100%. Mất: granularity thô → nhiều overlap giả.

**Cách 2 — Bỏ Interval_Relations, dùng `temporal_relations` làm nhãn trực tiếp**
Mine constraint `(eventType_A, role) → BEFORE (eventType_B, role)`, đếm support/confidence
trên nhãn có sẵn. Được: sạch hơn. Mất: phải tự viết miner, không dùng lại code họ.

**Cách 3 — Kết hợp: build theo Cách 1, đánh giá bằng nhãn ERE** ← khuyến nghị
Giữ cơ chế mining của PaTeCon, nhưng dùng `temporal_relations` gold làm ground truth
độc lập để chấm P/R/F1.

Hai chỗ "suy luận có kiểm soát" cần chấp nhận: chuẩn hoá TIMEX thô, và entity string-match
xuyên document. Cả hai là kỹ thuật NLP chuẩn, không phải bịa số liệu.

---

# 6. Review: `graph_mining_review_report.md` — 4 vấn đề

Script `generate_graph_mining_review_report.py` **chạy đúng như viết** (đã tái tạo:
430,118 retained / 360,418 excluded / 1,909 mismatch). Nhưng có 4 vấn đề:

## V1 — Diễn giải sai con số alignment (nghiêm trọng nhất)

Report ghi *"Excluded because an endpoint is absent from MAVEN-Arg event clusters: 360,418"*
→ ngụ ý MAVEN-Arg thiếu event. **Sự thật:**

| | |
|---|---:|
| Tổng bị loại | 360,418 |
| **Do một đầu là TIMEX** | **308,901 (85.7%)** |
| Do event thật sự thiếu | 51,517 (14.3%) |

Bảng "Temporal-label distribution" cũng sai lệch — cột "All MAVEN-ERE pairs" trộn TIMEX vào.

Với mẫu số đúng (chỉ EVENT-EVENT): retention = **430,118/483,544 = 89%**, không phải 54%.

## V2 — Motif không có sức phân biệt

| | |
|---|---|
| `BEFORE` **baseline** trên toàn tập retained | **90.86%** |
| Motif confidence | 96% |
| **LIFT** | **1.057×** |

Đoán `BEFORE` cho mọi cặp đã đúng 90.86%. Report **không nêu baseline** nên con số 0.96
trông ấn tượng hơn thực tế.

Hơn nữa: **có 121 motif khác** cũng đạt support≥25 & conf≥0.96, nhiều cái support gấp 4 lần:

| motif | support | conf | lift |
|---|---:|---:|---:|
| `Coming_to_be\|Location → Motion\|Location_original` | 106 | 1.000 | 1.101 |
| `Arriving\|Agent → Motion\|Agent` | 83 | 0.964 | 1.061 |
| `Process_end\|Location → Military_operation\|Location` | 73 | 0.973 | 1.070 |
| `Process_start\|Location → Supporting\|Location` | 71 | 1.000 | 1.101 |
| `Killing\|Killer → Legal_rulings\|Patient` | 54 | 1.000 | 1.101 |

→ Motif support-25 được chọn là mẫu **yếu, không đại diện**.

## V3 — Motif có hướng nhưng không nói rõ

```
Motion|Location_final → Process_end|Location  : support 25
Process_end|Location  → Motion|Location_final : support  4
```
Đảo thứ tự cho motif khác. Không sai (vì `BEFORE(a,b) ≠ BEFORE(b,a)`), nhưng report
không nêu → dễ hiểu nhầm là đối xứng.

## V4 — Lỗi logic nhỏ trong code

```python
if event_1_id not in ere_events or event_2_id not in ere_events:
    # In the current train data this is covered by the previous condition.
    excluded_missing_arg_event += 1   # cộng nhầm vào biến sai
```
Comment không đúng; nên tách biến riêng hoặc `raise`.
Dòng 104 `next(...)` sẽ `StopIteration` nếu motif không có occurrence `BEFORE` nào.

## Không gian motif tổng thể (đo được)

| | |
|---|---|
| Tổng motif phân biệt | **25,829** |
| support ≥ 10 | 2,415 |
| support ≥ 25 | 755 |
| support ≥ 100 | 104 |

→ Dữ liệu **rất thưa**: chỉ 2.9% motif đạt support≥25.

## Đề xuất sửa report

**Bắt buộc:**
1. Tách thống kê thành 3 nhóm: `EVENT-EVENT`, `EVENT-TIME`, `TIME-TIME`; nói rõ chỉ nhóm 1
   dùng được với MAVEN-Arg
2. Thêm cột **baseline + lift** cho mọi motif — confidence 0.96 vô nghĩa khi baseline 0.91

**Nên có:**
3. Thay motif support-25 bằng bảng top-N theo lift (đã có 121 ứng viên)
4. Ghi rõ motif **có hướng**, báo cáo cả support chiều ngược
5. Nêu tổng không gian 25,829 motif / 755 đạt support≥25 để thấy độ thưa thật

---

# 7. File đã tạo

| file | nội dung |
|---|---|
| `report/maven-vs-patecon.html` | Artifact đối chiếu MAVEN vs PaTeCon (cũng ở https://claude.ai/artifact/2yDukEFmHGa4kAt1uXGCNP) |
| `report/CONTAINS_all_docs.txt` | 105 MB — toàn bộ 121,483 CONTAINS của 3,539 doc, có text gốc + vị trí `@câuN:tok[a-b]` + ARG; nhóm EVENT↔TIME lên trên, phần còn lại xuống dưới |
| `report/CONTAINS_statistics.txt` | Thống kê tổng hợp CONTAINS |
| `report/CONTAINS_analysis.txt` | Phân tích chi tiết 3 doc mẫu |
| `report/json_samples/*.json` | 6 file JSON gốc (ERE+ARG) của 3 doc: Elbow Tour, Elton John Tour, ZZ Top Tour |

---

# 8. Ba document mẫu để tra cứu

| | Elbow Tour | Elton John Tour | ZZ Top Tour |
|---|---|---|---|
| doc_id | `b9d9626c...` | `fcdcfa26...` | `00cb5962...` |
| số event Traveling | 1 | 2 | **3** |
| Agent type | Organization | Person | Organization |
| CONTAINS | 12 | 8 | **1** |
| SUBEVENT | 1 cặp | 3 cặp | **rỗng** |
| PRECONDITION | 2 | 1 | 2 |
| BEGINS-ON/ENDS-ON | rỗng | rỗng | **có giá trị** |

Ba doc này phủ đủ dải biến thiên để test logic build statement ở các trường hợp biên.

## Lỗi đã mắc khi đọc dữ liệu (để tránh lặp lại)

1. Bỏ sót phần tử `content` khi liệt kê Location của event `tour` (Elton John) — chỉ nêu
   4 entity, thực tế là **6 phần tử** (4 entity + 2 content)
2. Kết luận sai "promote BEFORE tour" tạo mâu thuẫn chiều với PRECONDITION — thực tế
   **không có cặp BEFORE nào giữa tour và promote**; đã rút lại
3. Kết luận sai "2 event Traveling là trùng lặp cần khử" — thực tế chúng có quan hệ
   `CONTAINS` + `SUBEVENT` rõ ràng, là **phân cấp thật** không phải trùng lặp

→ Luôn đối chiếu nguyên JSON trước khi kết luận.
