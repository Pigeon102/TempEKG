# Taxonomy temporal conflict — đo đủ 5 loại trên dữ liệu của PaTeCon

**EXP19.** Trước đó chỉ đo ordering + mutual exclusion rồi kết luận — thiếu. Đề tài nhắm cả
**granularity**. Đo đủ để có taxonomy có số.

---

## Bảng tổng hợp

| Loại | WD-50k | WD-250k | PaTeCon phát hiện? |
|---|---|---|---|
| **T1 REPRESENTATION** `start > end` | 2.50% | 2.60% | ✅ loại **trước khi** mine |
| **T2 MUTUAL EXCLUSION** nhiều giá trị cho property chức năng | 2.88% | 2.16% | ✅ **87%** conflict của họ |
| **T3 ORDERING** sinh trước chết bị vi phạm | 0.24% | 0.58% | ✅ **13%** conflict của họ |
| **T4 DISJOINTNESS** khoảng chồng nhau (đo thô) | 30.2% | 28.5% | ❌ **bị loại** — xem §T4 |
| **T5 GRANULARITY** độ chính xác giả | **13.35%** dates | **12.13%** | ❌ **không có cơ chế** |

---

## T4 — vì sao 30% không phải là conflict

Đo thô cho 274,145 cặp khoảng chồng nhau trên WD-50k. **Nhưng đây là cận trên, không phải
số conflict.** Lý do: `P54` (thành viên đội thể thao) — một cầu thủ **hoàn toàn có thể**
đồng thời ở CLB và đội tuyển quốc gia. Chồng khoảng ở đây là hợp lệ.

PaTeCon xử lý đúng: constraint `P54 disjoint P54` mine ra **confidence 0.68**, dưới ngưỡng
0.9 nên **bị loại**. Đó chính là chức năng của bộ lọc confidence.

> Bài học: không thể giả định disjointness theo property. Phải để dữ liệu quyết định — và
> PaTeCon làm đúng chỗ này.

---

## T5 GRANULARITY — lỗ hổng lớn nhất của PaTeCon

### Bằng chứng định lượng

Phân bố ngày-tháng của các giá trị **day-precision**:

| | WD-50k | WD-250k |
|---|---|---|
| tổng giá trị day-precision | 24,189 | 75,439 |
| **ngày 01-01** | **3,230 = 13.35%** | **9,150 = 12.13%** |
| kỳ vọng nếu là ngày thật | 0.27% | 0.27% |
| **bội số** | **49×** | **44×** |
| tháng 00 (không rõ) | 195 = 0.81% | 1,051 = 1.39% |

Ngày-tháng phổ biến thứ ba trở đi (`0303`: 85, `0516`: 84, `0510`: 83) đều nằm **đúng mức
kỳ vọng ~0.35%**. Chỉ `0101` bị thổi lên 49×.

### Diễn giải

**~13% giá trị "chính xác đến ngày" của Wikidata là ĐỘ CHÍNH XÁC GIẢ** — thực chất chỉ biết
năm, nhưng được ghi thành 1 tháng 1. Cộng thêm `0000` (tháng/ngày khai báo là không rõ).

Ví dụ: một người sinh năm 1732 nhưng không rõ ngày → ghi `17320101`. Hệ thống đọc thành
"sinh ngày 1/1/1732", không phân biệt được với người **thật sự** sinh ngày 1/1/1732.

### Vì sao PaTeCon không bắt được

Ba loại constraint của họ — mutual exclusion, ordering, disjointness — **đều thao tác trên
khoảng thời gian**. Với chúng, `17320101` là một ngày hợp lệ như mọi ngày khác. Không có
cơ chế nào biểu diễn được *"độ chính xác được khai báo không khớp độ chính xác thực"*.

Logic ba trị `FuzzyTime` của họ xử lý **thiếu** giá trị (`null`) và **granularity khác nhau
khi so sánh**, nhưng không xử lý **granularity bị khai man**.

---

## Ý nghĩa cho đề tài

Slide dự án nhắm **2 loại**: Ordering Conflict và Granularity Conflict. Số liệu nói:

| | Ordering | Granularity |
|---|---|---|
| PaTeCon có làm? | ✅ có (13% conflict của họ) | ❌ **không** |
| Tỉ lệ trên chính data của họ | 0.24–0.58% | **12–13%** |
| Có chỗ đóng góp mới? | ít — họ đã làm | **nhiều — chưa ai làm** |

> **Granularity conflict phổ biến hơn ordering conflict khoảng 20–50 lần, ngay trên chính
> dữ liệu mà PaTeCon dùng — và PaTeCon không phát hiện được cái nào.**

Đây là lập luận mạnh nhất cho hướng granularity, và nó **không dựa vào MAVEN** — nó đến từ
dữ liệu gốc của bài báo mình đang kế thừa.

### Đối chiếu MAVEN

MAVEN có **17,102 event mang ≥2 anchor CONTAINS**, thường lồng nhau theo granularity
("trong năm 1778" + "ngày 11 tháng 11"). Đó là **quần thể để định nghĩa granularity conflict
ở cấp event** — tương ứng nhưng khác cơ chế với hiện tượng `0101` của Wikidata.

**Chưa đo được** vì TIMEX của MAVEN chưa có giá trị chuẩn hoá. Đó là việc tiếp theo:
normaliser (~1 tuần, 62.1% regex + reference-time propagation) rồi giao các anchor.
