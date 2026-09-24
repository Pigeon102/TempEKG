# Cách construct KG — thiết kế và kết quả build

> Tài liệu cài đặt. Code: `tempekg_kg/build_kg.py`, `verify_kg.py`, `constraint_net.py`.
> Mọi con số trong tài liệu này lấy từ lần chạy thật, không ước lượng.
> Các quyết định định nghĩa (mapping Allen, lattice, ngưỡng) nằm ở `DEFINITIONS.md`;
> tài liệu này chỉ nói **cách dựng** và **đã dựng ra cái gì**.

---

## 0. Kết quả build

| | train | valid |
|---|---:|---:|
| Document | 2.913 | 710 |
| Node event (cluster) | 67.984 | 16.301 |
| Node entity | 55.421 | 13.176 |
| Node span | 71.485 | 17.963 |
| Node timex | 16.688 | 4.139 |
| Edge input (`HAS_ARG`) | 188.584 | 44.966 |
| Edge weak (CAUSE + PRECONDITION + SUBEVENT) | 45.509 | 12.524 |

> **Phân rã weak_edges** (đối chiếu trực tiếp với `MAVEN_ERE/*.jsonl`):
>
> | | train | valid |
> |---|---:|---:|
> | PRECONDITION | 29.519 | 8.075 |
> | SUBEVENT | 9.193 | 2.826 |
> | CAUSE | 6.797 | 1.623 |
> | **tổng** | **45.509** | **12.524** |
>
> Bản trước ghi valid = 10.712. Đó là **số cũ từ trước khi PRECONDITION được thêm vào**
> `CAUSAL_RELS`; không có cạnh nào bị rớt. Build hiện tại khớp nguồn từng con số.
>
> **Lệch temporal so với nguồn là đúng, không phải lỗi.** Nguồn đếm train 792.445 / valid
> 188.928, KG ghi 792.395 / 188.924 — chênh **50** và **4**. Đó là các cạnh BEGINS-ON được
> lưu cả hai chiều trong file gốc rồi gộp lại còn một, đúng như bất biến
> `symmetric_canonical` quy định.
| Edge target (temporal) | 792.395 | 188.924 |
| Anchored pair | 244.687 | 57.925 |
| Kích thước file | 217,7 MB | 51,8 MB |
| Thời gian build | 5,5 s | 1,4 s |

Toàn bộ 9 bất biến đạt trên cả hai split (`verify_kg.py`).

---

## 1. Vì sao hai tầng

Bảng pairwise **không thể** phát hiện mâu thuẫn ba biến. Ví dụ cụ thể, đã kiểm bằng code:

```
BEFORE(a,b) ∧ BEFORE(b,c) ∧ ENDS-ON(a,c)
```

Từng cặp một đều hợp lệ. Cả ba cùng lúc thì mâu thuẫn — nhưng **chỉ dưới mapping
`ENDS-ON = {m}`**. Dưới mapping đã chốt `{b,m}` thì nhất quán.

Đây không phải ví dụ giả định: vòng research trước đã sinh ra 7 "mâu thuẫn cứng" theo
đúng cơ chế này, và chúng biến mất hoàn toàn khi sửa mapping. `constraint_net.py --self-test`
tái lập cả hai chiều để hồi quy không lặp lại.

Hệ quả kiến trúc:

| Tầng | Biểu diễn | Trả lời câu hỏi |
|---|---|---|
| **1. Property graph** | node/edge có nhãn | pattern này xuất hiện bao nhiêu lần |
| **2. Constraint network** | biến điểm mút + bất đẳng thức | tập nhãn này có thoả được không |

Tầng 1 lưu trên đĩa. Tầng 2 sinh theo yêu cầu từ tầng 1 — ánh xạ một chiều, tất định.

---

## 2. Tầng 1 — Property graph

### 2.1. Node

**Event = coreference cluster.** Đo được: **96,4%** cluster là singleton (65.510/67.984),
và chỉ **3,4%** span nhiều hơn một câu. Nên tranh cãi "cluster hay mention" gần như vô nghĩa
với đại đa số dữ liệu.

Chốt: dùng cluster, lưu kèm `n_mentions` và `sent_span` làm thuộc tính. 96,4% trường hợp
không phải nghĩ; 3,4% còn lại có cờ để lọc riêng khi cần. Không xây cơ chế phức tạp cho 3,4%.

**TIMEX tách đôi theo `timex_type`.** Đây là chỗ khác `DEFINITIONS.md` A1, vốn chốt TIMEX
là OPAQUE hoàn toàn.

| timex_type | Số lượng | Tỉ lệ | Xử lý |
|---|---:|---:|---|
| DATE | 13.339 | 79,9% | `anchorable = true` |
| DURATION | 2.901 | 17,4% | `anchorable = false` |
| TIME | 432 | 2,6% | `anchorable = true` |
| PREPOSTEXP | 16 | 0,1% | `anchorable = false` |

Lý do tách: DURATION là **độ dài**, không phải vị trí — "14 năm" không có toạ độ trên
timeline, đặt `(s,e)` cho nó là sai ngữ nghĩa. Nhưng DATE thì có, và đó là **neo tuyệt đối
duy nhất** trong toàn hệ, thứ duy nhất không phụ thuộc nhãn annotator. Bỏ cả 13.771 anchor
là vứt đi kênh bằng chứng độc lập duy nhất còn lại sau khi D1 loại causal.

Trường `anchorable` chỉ đánh dấu **khả năng**; việc parse ra giá trị lịch để lười, và thất
bại thì rơi về opaque. Build hiện tại chưa parse.

**Span node — 59,6% argument filler không có `entity_id`.**

Đo được: 113.597/190.479 filler thiếu `entity_id`. Chúng không phải rác:

```json
{"content": "a corps of volunteers led by giuseppe garibaldi", "offset": [137, 184]}
```

Đó là Agent, Patient, Location thật, chỉ không được coref hoá. Bỏ đi là mất quá nửa dữ liệu
argument; giữ nguyên thì không làm anchor được vì không có id để "chung".

Chốt: node `Span`, khoá `md5(offset)` trong phạm vi document. Hai filler cùng offset trong
cùng doc là **cùng một span theo cấu trúc** — kiểm được, không phải đoán. Build sinh ra
71.485 span node từ 112.549 filler, tức trung bình 1,57 filler/span.

Mọi cạnh `HAS_ARG` ghi `strength ∈ {entity, span}`, nên pattern nói rõ mình dựa vào loại
anchor nào. Đây là trục thứ tư của lattice và nó miễn phí.

### 2.2. Cạnh — phân hoạch theo vai trò nhận thức

Không phân theo file nguồn mà theo **detector được thấy gì**:

| Lớp | Nội dung | Số lượng (train) | Detector thấy |
|---|---|---:|---|
| `input_edges` | `HAS_ARG(role, strength)` | 188.584 | Có |
| `weak_edges` | CAUSE, PRECONDITION, SUBEVENT | 45.509 | Có, nhưng không phải bằng chứng độc lập |
| `target_edges` | TEMPORAL | 792.395 | **Không** — đây là thứ đang audit |

Tách vật lý thành ba mảng riêng, không chỉ tách logic. Lý do: đã đo được causal chồng
**95,2%** (PRECONDITION) và **90,7%** (CAUSE) lên temporal, nên nếu để lẫn thì detector đọc
nhãn qua cửa sau mà không ai nhận ra. Ba collection riêng biến rò rỉ thành lỗi cấu trúc
bắt được bằng `verify_kg.py`, thay vì lỗi thầm lặng.

`verify_kg.py` kiểm ba bất biến chống rò rỉ:
- `input_layer_shape` — cạnh input **không bao giờ** nối hai event trực tiếp
- `target_minimal` — cạnh target chỉ mang đúng ba trường `{s, t, rel}`
- `pairs_label_free` — `anchored_pairs` không chứa bất kỳ trường nhãn nào

### 2.3. Anchored pair — materialize lúc build

Pattern key là hàm thuần của cặp node + cạnh input, nên tính một lần lúc build rồi lưu:

```json
{"a": "EVENT_x", "b": "EVENT_y", "anchors": ["ENTITY_z"], "n_anchors": 1,
 "roles": [["Location_final", "Location"]], "strength": "entity",
 "sdist": 3, "torder": "fwd"}
```

Hai lợi ích. Mining biến từ duyệt đồ thị thành `group by` — nhanh hơn 1–2 bậc độ lớn. Và
key **đóng băng trên đĩa**, nên kết quả tái lập được, không phụ thuộc phiên bản code mining.

Chỉ sinh cặp **có chung anchor**: 244.687 cặp, so với 1.994.647 nếu sinh mọi cặp. Cặp không
chung anchor không bao giờ khớp pattern có anchor, nên sinh ra là lãng phí.

Phân bố theo `strength`:

| | train | Tỉ lệ |
|---|---:|---:|
| entity | 139.628 | 57,1% |
| span | 76.495 | 31,3% |
| mixed | 28.564 | 11,7% |

31,3% cặp chỉ tồn tại nhờ span node — tức nếu bỏ span như thiết kế ban đầu thì mất gần một
phần ba không gian pattern.

---

## 3. Tầng 2 — Constraint network

### 3.1. Ánh xạ

Từ `DEFINITIONS.md` B1, dùng nguyên:

| MAVEN | Allen | Bất đẳng thức điểm mút |
|---|---|---|
| BEFORE | `{b}` | `e_a < s_b` |
| CONTAINS | `{di}` | `s_a < s_b ∧ e_b < e_a` |
| OVERLAP | `{o}` | `s_a < s_b < e_a < e_b` |
| SIMULTANEOUS | `{e}` | `s_a = s_b ∧ e_a = e_b` |
| BEGINS-ON | `{s, si, e}` | `s_a = s_b` |
| ENDS-ON | `{b, m}` | `e_a ≤ s_b` |

### 3.2. Bảng composition sinh bằng brute force

`build_composition_table()` liệt kê mọi interval nguyên không suy biến trong `[0,7)` và
đọc ra quan hệ thực tế. **Không viết tay.** Bảng Allen viết tay là đúng loại hiện vật âm
thầm sinh ra mâu thuẫn giả, và dự án này đã trả giá một lần rồi.

Self-test kiểm bảng bằng các tính chất kiểm tay được: `comp(b,b)={b}`, `comp(e,X)={X}`,
`comp(b,bi)=full`, converse là phép đối hợp, và converse đối xứng với `basic_relation`.

### 3.3. PC-2 không return sớm

`path_consistency()` chạy tới fixpoint và trả về **cả ma trận** kể cả khi phát hiện bất
khả thoả. Đây là sửa lỗi của `D3b` mục 3: bản đặc tả cũ `return INCONSISTENT` rồi vứt ma
trận, làm `H2` không xác định đúng ở những document quan trọng nhất.

`minimal_core()` trích lõi bất khả thoả bằng xoá-một-rồi-thử-lại, `O(|constraints|)` lần
chạy PC. Chỉ gọi trên document đã biết là inconsistent.

### 3.4. Chi phí đo được

Chạy trên 300 document train đầu tiên:

| | |
|---|---|
| Document nhất quán | **300 / 300** |
| Node mỗi mạng | median 27, max 110 |
| Ràng buộc mỗi mạng | median 231, max 5.738 |
| PC runtime | median 0,069 s, max 10,7 s, tổng 111 s |

Phân bố node trên **toàn** train: p50 = 21, p90 = 43, p99 = 73, max = 110. Mạng nhỏ, PC
hoàn toàn khả thi.

Ngoại suy: full train khoảng **18 phút**. Nhưng đã biết gold nhất quán 0/2.913, nên chạy
hết là lãng phí — chốt **dựng tầng 2 lười**, chỉ trên document mà detector gắn cờ. Sau khi
inject ở 0,1% thì chỉ ~13% document thành inconsistent.

---

## 4. Định dạng lưu

Một dòng JSONL một document, tự chứa:

```json
{
  "doc_id": "...", "title": "...", "has_arg": true,
  "nodes": {
    "EVENT_x": {"kind":"event","type":"Motion","type_id":46,"n_mentions":1,
                "sent_span":1,"sent_first":3,"tok_first":57,"trigger":"Expedition",
                "in_arg":true},
    "TIME_y":  {"kind":"timex","timex_type":"DATE","anchorable":true,"text":"1860"},
    "ENTITY_z":{"kind":"entity","ent_type":"Location","mentions":["quarto"]},
    "SPAN_a3f":{"kind":"span","offset":[137,184],"content":"a corps of volunteers..."}
  },
  "input_edges":  [{"s":"EVENT_x","t":"ENTITY_z","role":"Location_final","strength":"entity"}],
  "weak_edges":   [{"s":"EVENT_x","t":"EVENT_w","kind":"PRECONDITION"}],
  "target_edges": [{"s":"EVENT_x","t":"EVENT_w","rel":"BEFORE"}],
  "anchored_pairs":[{"a":"EVENT_x","b":"EVENT_w","anchors":["ENTITY_z"],"n_anchors":1,
                     "roles":[["Location_final","Location"]],"strength":"entity",
                     "sdist":2,"torder":"fwd"}]
}
```

Vì sao JSONL chứ không phải Neo4j/RDF:

- per-document tự chứa → song song hoá theo dòng, không cần server
- 2.913 doc / 838k cạnh → vừa RAM, không cần DB
- diff được bằng git, reproduce được
- **inject conflict = sửa `target_edges` của một dòng**, phần còn lại giữ nguyên bit-identical

Cần query đồ thị phức tạp thì import sang Neo4j từ định dạng này mất khoảng 20 dòng. Chiều
ngược lại khó hơn nhiều.

---

## 5. Bất biến được kiểm

`verify_kg.py` chạy 9 kiểm tra, mỗi cái ứng với một cách build có thể sai âm thầm:

| Bất biến | Bắt lỗi gì |
|---|---|
| `no_dangling` | cạnh trỏ tới node không tồn tại |
| `input_layer_shape` | **rò rỉ nhãn** — cạnh input nối hai event |
| `target_minimal` | cạnh target mang thêm thuộc tính có thể lộ thông tin |
| `pairs_label_free` | `anchored_pairs` chứa nhãn |
| `symmetric_canonical` | SIMULTANEOUS/BEGINS-ON chưa canonical hoá |
| `one_label_per_pair` | một cặp ordered mang hai nhãn khác nhau |
| `no_self_loop` | cạnh tự vòng |
| `node_invariants` | `anchorable` sai, event không mention, span thiếu offset |
| `pairs_consistent` | `anchored_pairs` không khớp `input_edges` |

Ba cái đầu là chống rò rỉ. Nếu một trong ba fail thì mọi con số downstream vô nghĩa.

---

## 6. Hai chỗ khác với `DEFINITIONS.md`

Ghi rõ để không âm thầm trôi khỏi tài liệu quyết định:

**A1 — TIMEX.** Tài liệu chốt OPAQUE hoàn toàn. Build này tách `anchorable` theo
`timex_type`. Lý do: 13.771 DATE/TIME là kênh bằng chứng độc lập duy nhất còn lại sau khi
D1 loại causal. Chưa parse giá trị lịch, chỉ đánh dấu khả năng — nên thay đổi này **không
tốn gì** nếu sau cùng quyết định không dùng.

**Span node.** Tài liệu chưa bàn tới 59,6% filler thiếu `entity_id`. Build này giữ chúng
làm node riêng với `strength='span'`. Đo được: chúng đóng góp 31,3% số anchored pair.
Nếu muốn loại thì lọc `strength == 'entity'` lúc mining — **không cần build lại**.

Cả hai đều thiết kế để có thể bỏ bằng một bộ lọc, không phải build lại.

---

## 7. Chạy

```bash
python tempekg_kg/build_kg.py --split train        # 5,5 s  -> graph/train.jsonl
python tempekg_kg/build_kg.py --split valid        # 1,4 s  -> graph/valid.jsonl
python tempekg_kg/verify_kg.py --split train       # 9 bất biến
python tempekg_kg/constraint_net.py --self-test    # bảng Allen + PC
python tempekg_kg/constraint_net.py --split train --limit 300
```

---

## 8. Chưa làm

| | Vì sao chưa |
|---|---|
| Parse giá trị lịch cho DATE anchor | Chưa cần cho mining; cần khi dùng TIMEX làm neo tuyệt đối |
| Dựng tầng 2 cho full corpus | Lãng phí — gold nhất quán 0/2.913; để lười |
| Mining pattern trên KG này | Bước sau; key đã materialize sẵn |
| Injector | `INJECTION_SPEC.md`; định dạng đã thiết kế để sửa `target_edges` là đủ |
