# TempEKG

Event-centric temporal knowledge graph construction, rule mining, and noise-aware audit
over MAVEN-ERE.

## Trạng thái — mọi con số dưới đây đều đã đo

| Đóng góp | Kết quả | File |
|---|---|---|
| **C1** dựng KG | 9/9 bất biến, 3 chống rò rỉ nhãn | `src/build_kg.py`, `src/verify_kg.py` |
| **C2** mine rule | 68 rule, macro-F1 22,62% vs 15,78% của hằng số | `src/minimise.py` |
| **C3-A** audit nhãn sai | τ=0,005: F1 gấp 2,2× baseline | `src/detect.py` |
| **C3-B** audit cạnh thiếu | **89,3% recall, F1 gấp 118× baseline** | `src/propose_missing.py` |
| **Sửa nhãn** dưới nhiễu | **96,7%** (58/60) ở mức nhiễu 0,1% | `src/detect.py` |

### Kết quả mạnh nhất: C3-B

| Phương pháp | Đề xuất | P | R | F1 |
|---|---:|---:|---:|---:|
| luôn đoán BEFORE | 199.918 | 0,026% | 92,9% | 0,052% |
| closure strict (đòi 1 nhãn) | 1 | 100% | 1,8% | 3,509% |
| **closure + majority, `|compat|≤2`** | **1.572** | **3,181%** | 89,3% | **6,143%** |

Ý chính: **giá trị của closure là ở chỗ biết im lặng, không phải ở chỗ quyết định.** Nó từ
chối 191.752/199.918 cặp (95,9%).

## Đối chiếu với nguồn MAVEN-ERE

`src/verify_kg.py` giờ so thẳng KG đã dựng với corpus gốc. Hai chênh lệch là **đúng**, không phải lỗi:

| | nguồn | KG | ghi chú |
|---|---:|---:|---|
| weak train | 45.509 | 45.509 | khớp |
| weak valid | 12.524 | 12.524 | khớp |
| temporal train | 792.445 | 792.395 | chênh **50** — BEGINS-ON lưu hai chiều, gộp còn một |
| temporal valid | 188.928 | 188.924 | chênh **4** — cùng lý do |

Chênh temporal là hành vi đúng của bất biến `symmetric_canonical`. Weak edges thì copy thẳng
nên **mọi chênh lệch đều là bug** — vì thế mới thêm phép đối chiếu này.

Tài liệu trước ghi valid weak = 10.712; đó là **số cũ từ trước khi PRECONDITION vào**
`CAUSAL_RELS`, không phải cạnh bị rớt. Đã sửa ở mọi tài liệu.

## Bốn cảnh báo phải đọc trước khi trích số

1. **Gold không có conflict nào để tìm.** Bốn phép đo độc lập: 0 cặp hai nhãn, 0/2.913
   document PC-inconsistent, **0/164.803** cặp closure loại nhãn gold, 0 BEFORE hai chiều.
   Nhãn MAVEN là đọc ra từ một timeline đã sắp xếp nên nhất quán theo cấu trúc. Recall về
   conflict **chỉ đo được bằng bơm lỗi**.

2. **93,40% ≠ 35,25%.** 93,40% là precision *trên các cặp rule bắn và đoán CONTAINS*, sau khi
   đã bỏ BEFORE khỏi mẫu số. Chấm như classifier thật trên valid: CONTAINS **P 35,25% /
   R 56,07% / F1 43,29%**. Đặt vào bảng classifier thì dùng 35,25%.

3. **Accuracy che mất tất cả.** Base rate BEFORE 89,94%, nên phải báo macro-F1:

   | | Accuracy | Macro-F1 |
   |---|---:|---:|
   | luôn đoán BEFORE | **89,94%** | 15,78% |
   | 68 rule | 86,27% | **22,62%** |

   Rule thua accuracy 3,67 điểm nhưng thắng macro-F1 6,84 điểm. **3/6 nhãn vẫn F1 = 0.**

4. **Closure sụp nhanh khi nhiễu tăng** — không phải giảm dần đều:

   | Nhiễu | Sửa đúng | Im lặng |
   |---:|---:|---:|
   | 1% | 75,83% | 23,19% |
   | 10% | 22,94% | 76,26% |
   | 30% | **5,55%** | **93,86%** |

   Nó **từ chối** chứ không sai (đồng ý với nhãn sai chỉ 0,40–0,61%). Nhiễu tương quan
   *không* tệ hơn nhiễu độc lập — nhỉnh hơn chút, vì nó để lại nhiều vùng hoàn toàn sạch.

## Bốn hướng rule đã thử cho C3 — đều âm

| Hướng | lift | Vì sao hỏng |
|---|---:|---|
| 68 rule minimal làm detector | 1,1× | cả 68 đoán CONTAINS ⇒ "bất đồng" = 93,13% số cạnh |
| 1.073 families | 0,9× | wlb median 0,107, gắn cờ 93,8% số cặp |
| 341 non-CONTAINS | 0,9× | không phải vấn đề nhãn mà là wlb thấp |
| family đọc lại thành claim nhị phân | 10,1× | đạt 93% trần nhưng là baseline trá hình (siết 30× mà lift đứng yên) |

**Nguyên tắc rút ra: predictor dương trên lớp áp đảo không lật được thành detector âm.**
Constraint làm được vì nó nêu nhãn *bị cấm*, không nêu nhãn *kỳ vọng*.

C3-A thuộc về constraint τ=0,005 (25,1× lift). C3-B thuộc về closure + prior tần suất.

## Cấu trúc

```
src/       23 script — dựng KG, mine, minimise, inject, detect, propose
report/    tài liệu + artifact HTML 7 trang (mở tempekg_report_offline.html)
scripts/   make_standalone.py — build bản HTML offline
legacy/    139 file code thăm dò cũ, giữ để tra cứu
data/      README — dữ liệu 834 MB nằm ngoài git, xem cách dựng lại
```

## Chạy

```bash
python src/build_kg.py && python src/verify_kg.py    # dựng + kiểm 9 bất biến
python src/inject.py --rate 0.001 --seed 0           # bơm lỗi đã biết
python src/detect.py --tau 0.005 --limit 300         # C3-A
python src/propose_missing.py --limit 300 --sweep    # C3-B
python src/proof_ceiling.py --docs 200 --per-doc 4   # trần closure
```

Xem `report/STATUS.md` cho toàn bộ số liệu, `report/DEFINITIONS.md` cho định nghĩa hình thức.

## Việc chưa làm

- Sweep nhiều seed — 56/60 lỗi là mẫu nhỏ, cần khoảng tin cậy
- Nối bài 1 → bài 2: chạy noise-aware trên **cạnh model dự đoán**, không phải gold đã bơm
- Bộ rule phủ đủ SIMULTANEOUS/OVERLAP (greedy hiện loại sạch, 3/6 nhãn F1 = 0)
