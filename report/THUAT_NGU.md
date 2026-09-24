# Thuật ngữ TempEKG

Tra nhanh. Quyết định thiết kế và lý do đằng sau nằm ở `report/DEFINITIONS.md` (135 KB).

---

## 1. Dữ liệu và đồ thị

| Thuật ngữ | Nghĩa |
|---|---|
| **MAVEN-ERE** | Bộ dữ liệu gốc. Mỗi document có các event, entity, mốc thời gian và quan hệ giữa chúng. |
| **event** | Một sự việc trong văn bản, neo vào một từ kích hoạt (*trigger*). Ví dụ `assaulted`, `departed`. |
| **entity** | Người, tổ chức, địa điểm… tham gia vào event. |
| **timex** | Mốc thời gian dạng văn bản: `"November 11, 1778"`, `"1606"`, `"early 1776"`. |
| **span** | Đoạn văn bản làm tham số cho event nhưng không phải entity định danh. |
| **trigger** | Từ trong câu biểu thị event. |
| **cặp (pair)** | Hai event trong **cùng một document**. Đây là đơn vị mà hệ thống phân loại. |
| **document** | Một bài viết. Quan trọng vì mọi phép chia dữ liệu đều theo document, không theo cặp. |

### Các loại cạnh trong KG

| Loại | Nghĩa |
|---|---|
| **`input_edges`** | Cạnh event→entity/span (vai trò tham số). Được phép dùng làm đặc trưng. |
| **`target_edges`** | Cạnh quan hệ thời gian — thứ **phải dự đoán**. Không bao giờ được làm đặc trưng. |
| **`weak_edges`** | Quan hệ PRECONDITION / CAUSE / SUBEVENT. Không phải bằng chứng thời gian độc lập. |
| **`anchored_pairs`** | Hai event chia sẻ ít nhất một entity. |

## 2. Sáu nhãn quan hệ thời gian

| Nhãn | Nghĩa | Tỷ lệ trong valid |
|---|---|---|
| **BEFORE** | A kết thúc trước khi B bắt đầu | 89,94% |
| **CONTAINS** | A bao trùm B về thời gian | 8,54% |
| **SIMULTANEOUS** | A và B cùng lúc | 0,97% |
| **OVERLAP** | A và B chồng lấn một phần | 0,52% |
| **BEGINS-ON** | A bắt đầu cùng lúc với B | 0,023% |
| **ENDS-ON** | A kết thúc cùng lúc với B | 0,014% |

Mất cân bằng này là khó khăn trung tâm của Bài 1: đoán BEFORE cho mọi cặp đã đạt 89,94%
accuracy.

### Allen interval algebra

Hệ 13 quan hệ đầy đủ giữa hai khoảng thời gian. MAVEN chỉ dùng 7, bỏ các quan hệ nghịch đảo.
Ánh xạ đã chốt:

```
BEFORE       → {b}          CONTAINS  → {di}
OVERLAP      → {o}          SIMULTANEOUS → {e}
BEGINS-ON    → {s, si, e}   ENDS-ON   → {b, m}
```

Chỉ hai chỗ giao nhau: `b` (BEFORE ⊂ ENDS-ON) và `e` (SIMULTANEOUS ⊂ BEGINS-ON). Đây là
nguồn của một sai lầm đo đạc đã sửa (xem *phép kiểm bao hàm*).

## 3. Rule

| Thuật ngữ | Nghĩa |
|---|---|
| **rule** | Một luật dạng `điều kiện → nhãn`. Chỉ bắn khi **mọi** điều kiện đều đúng. |
| **`conds`** | Danh sách điều kiện của rule, nối bằng AND. |
| **depth** | Số điều kiện. Bộ hiện tại toàn depth-2. |
| **`k` / `n`** | Số lần rule đúng / số lần rule bắn, trên tập dùng để mine. |
| **support** | Chính là `n` — rule bắn trên bao nhiêu cặp. |
| **precision** | `k/n` — tỷ lệ đúng khi rule bắn. |
| **bắn (fire)** | Rule khớp với một cặp. |
| **phủ (coverage)** | Tỷ lệ cặp có ít nhất một rule bắn. |
| **fallback** | Nhãn mặc định (BEFORE) khi không đủ bằng chứng để phát nhãn khác. |

### Năm dạng điều kiện

| Dạng | Ví dụ | Nghĩa |
|---|---|---|
| `EQ` | `EQ(type_a, Killing)` | thuộc tính vô hướng bằng đúng giá trị |
| `HAS` | `HAS(roleset_a, Agent)` | tập chứa phần tử này |
| `ALL` | `ALL(roleset_a, Patient)` | tập chỉ gồm đúng phần tử này |
| `CNT` | `CNT(etypeset_a, 3)` | tập có đúng 3 phần tử |
| `MIX` | `MIX(anchor_roles, _)` | tập có nhiều hơn một loại phần tử |
| `REL` | `REL(a_before_b, False)` | so sánh **giữa hai event**, không phải thuộc tính riêng |

### Tên thuộc tính

| Tên | Nghĩa |
|---|---|
| `type_a` / `type_b` | loại của event A / event B |
| `type_pair` | cặp loại, ví dụ `(Killing, Bodily_harm)` |
| `same_type` | hai event cùng loại hay không |
| `order` | thứ tự trong văn bản: `fwd` / `rev` / `same` |
| `sdist` | khoảng cách câu, đã gom nhóm: `0`, `1`, `2-3`, `4-7`, `8+` |
| `bucket_a` / `bucket_b` | vị trí trong document: `lead` (câu đầu), `early`, `mid`, `late` |
| `roleset_a` | tập vai trò mà event A gán cho tham số của nó |
| `etypeset_a` | tập loại thực thể tham gia event A |
| `anchor_roles` | cặp vai trò của thực thể mà hai event chia sẻ |
| `nrole_a` | số vai trò của event A |
| `shares_anchor` | hai event có chia sẻ thực thể nào không |
| `multi_mention_a` | event A xuất hiện nhiều lần trong document |

## 4. Thống kê chọn rule

| Thuật ngữ | Công thức / nghĩa |
|---|---|
| **Wilson lower bound (`wlb`)** | Cận dưới khoảng tin cậy 95% của `k/n`. Phạt mẫu nhỏ: `5/5` cho wlb thấp hơn `90/100`. |
| **lift** | `precision / base_rate`. Rule mạnh hơn mức xuất hiện tự nhiên của nhãn bao nhiêu lần. |
| **base rate / prior** | Tỷ lệ nhãn trong toàn corpus. |
| **Δlogit** | `logit(p_rule) − logit(p_parent)`. Điều kiện thêm vào có đóng góp gì ngoài cái parent đã nói. |
| **parent** | Rule chỉ gồm một trong các điều kiện. Dùng để kiểm tra điều kiện kia có thừa không. |
| **BH-FDR** | Benjamini-Hochberg. Hiệu chỉnh khi thử hàng nghìn giả thuyết cùng lúc. |
| **q-value** | p-value sau hiệu chỉnh BH. |
| **block permutation** | Xáo nhãn **trong từng document** để dựng phân phối null. Giữ nguyên cấu trúc document. |
| **stability (π)** | Tỷ lệ lần rule được chọn khi lấy mẫu lại document. |
| **document diversity** | Số document khác nhau cung cấp `k` của rule. Dự báo generalization tốt hơn wlb. |
| **LCB-Lift** | `wlb / base_rate`. Đã thử, thua — nằm ở `experiments/ablations/lcb/`. |

### Vì sao không dùng một ngưỡng chung

`wlb ≥ 0,40` là hợp lý cho CONTAINS nhưng xóa sạch nhãn hiếm: SIMULTANEOUS có wlb tối đa
**0,141**, OVERLAP **0,125**. Với nhãn chiếm 0,97% corpus, precision 14% đã là tín hiệu rất
mạnh. Đó là lý do việc xếp hạng phải làm **riêng trong từng nhãn**.

## 5. Giao thức chia dữ liệu

| Tập | Vai trò |
|---|---|
| **DISCOVERY** (197 doc) | Đề xuất rule. Nhãn ở đây quyết định rule nào tồn tại. |
| **CONFIRMATION** (126 doc) | Chấm lại rule trên nhãn **chưa từng tham gia chọn rule**. |
| **DEV-INNER** (77 doc) | Chọn combiner và ngưỡng. |
| **VALID** (705 doc) | Mở **một lần**, trên cấu hình đã đóng băng. |

| Thuật ngữ | Nghĩa |
|---|---|
| **leakage** | Dùng dữ liệu test để ra quyết định, làm kết quả đẹp giả. |
| **post-selection inference** | Vấn đề: p-value không còn đúng khi giả thuyết được chọn từ chính dữ liệu đó. |
| **confirmation split** | Cách xử lý: tách riêng tập chỉ được phép *xác nhận*, không được phép *tìm*. |
| **freeze / đóng băng** | Chốt cấu hình rồi mới mở valid. Sau đó không tune nữa. |
| **overfit** | Kết quả tốt trên tập dùng để chọn, kém trên dữ liệu mới. |

## 6. Đánh giá

| Thuật ngữ | Nghĩa |
|---|---|
| **precision (P)** | Trong số lần đoán nhãn X, bao nhiêu phần đúng. |
| **recall (R)** | Trong số nhãn X thật, bắt được bao nhiêu phần. |
| **F1** | Trung bình điều hòa của P và R. |
| **macro-F1** | Trung bình F1 của **6 nhãn**, mỗi nhãn tính như nhau. Thước đo chính. |
| **accuracy** | Tỷ lệ đoán đúng trên tổng số cặp. **Không phải thước đo tốt ở đây.** |
| **baseline hằng số** | Đoán BEFORE cho mọi cặp: accuracy 89,94% mà macro-F1 chỉ 15,78%. |
| **oracle** | Trần lý thuyết: giả sử luôn chọn đúng rule trong số các rule đang bắn. |

**Vì sao accuracy gây hiểu nhầm:** BEFORE chiếm 89,94% dữ liệu, nên mọi hệ thống cố gọi
tên năm nhãn còn lại đều **giảm** accuracy. Bộ 257 rule đạt accuracy 87,87% — thấp hơn
baseline — nhưng macro-F1 25,60% so với 15,78%.

## 7. Kết hợp rule

| Thuật ngữ | Nghĩa |
|---|---|
| **combiner** | Cách hợp nhiều rule cùng bắn trên một cặp thành một dự đoán. |
| **`max-norm`** | Combiner đang dùng: `score[rel] = max(wlb / prior[rel])`. |
| **`norm-wlb`** | Biến thể cộng dồn: `score[rel] += wlb / prior[rel]`. |
| **`argmax-wlb`** | Lấy rule có wlb cao nhất. Đơn giản nhất, thua hai cái trên. |
| **τ (tau)** | Ngưỡng phát nhãn. Dưới ngưỡng thì rơi về fallback BEFORE. |
| **chuẩn hóa prior** | Chia điểm cho base rate của nhãn. Bắt buộc, nếu không CONTAINS luôn thắng. |

## 8. Khai phá rule

| Thuật ngữ | Nghĩa |
|---|---|
| **beam search** | Duyệt có cắt tỉa, giữ lại `k` nhánh tốt nhất mỗi bước. Không vét cạn. |
| **vét cạn depth-2** | Xét **mọi** cặp điều kiện. Ba định lý cắt tỉa giúp chi phí còn 0,185× một lượt quét. |
| **MDD** | Multi-valued Decision Diagram. 19 biến đa trị thay vì 1.143 biến nhị phân. |
| **view** | Một cách nhìn đồ thị con. Bản cũ mine trên 8 view khác nhau. |
| **family** | Rule đã trừu tượng hóa, gom nhiều rule cụ thể. |
| **subsumption** | Loại rule bị rule khác bao hàm. Đã thử — phá tín hiệu. |
| **greedy forward selection** | Mỗi vòng thêm rule tăng điểm nhiều nhất. Đã thử — overfit. |

## 9. Bài 2 — noise-aware reasoning

| Thuật ngữ | Nghĩa |
|---|---|
| **injection** | Cố ý làm hỏng một tỷ lệ cạnh để đo khả năng phát hiện. |
| **closure** | Suy ra quan hệ mới từ quan hệ đã có, bằng đại số Allen. |
| **date bridge** | Nếu cả hai event neo được vào ngày thật và `d₁ < d₂` thì A BEFORE B. Đúng **100%** trên 12.946 suy luận. |
| **conflict** | Cạnh mâu thuẫn với những gì suy ra được. |
| **repair@k** | Trong `k` cạnh bị gắn cờ, bao nhiêu phần sửa đúng. |
| **R_all** | Trong **toàn bộ** cạnh hỏng, bắt được bao nhiêu phần. Khác hẳn repair@k. |
| **wrong-repair** | Sửa một cạnh vốn đã đúng. Đo được 0,44%. |

**Chú ý mẫu số:** `repair@k` và `R_all` từng cho hai con số lệch nhau 13 lần, cả hai đều
đúng — chúng trả lời hai câu hỏi khác nhau.

## 10. Tên file hay gặp

| File | Là gì |
|---|---|
| `rules/final/rules_rx_c70.json` | **Bộ rule đang dùng** — 257 rule |
| `src/vote.py` | Chấm điểm bộ rule, chạy `--tau-sweep` |
| `src/mine_mdd.py` | Vét cạn depth-2 với ba định lý cắt tỉa |
| `src/mine_views.py` | Beam search trên 8 view |
| `report/BAI1_C2_FINAL.md` | Báo cáo đóng Bài 1 |
| `report/RULESET.md` | Bộ rule là gì, biểu diễn ra sao |
| `report/DEFINITIONS.md` | Quyết định thiết kế đầy đủ (135 KB) |
| `experiments/ablations/` | Các hướng đã thử mà thất bại |
