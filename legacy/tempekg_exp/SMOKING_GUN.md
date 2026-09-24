# Bằng chứng quyết định: 25.5% conflict của PaTeCon là GIẢ do granularity

**EXP24.** Chạy code gốc PaTeCon trên **bộ dữ liệu chính thức của chính họ** (WD50K.tsv tải
từ Google Drive trong README), rồi phân tích từng conflict.

---

## 1. Xác nhận đúng bộ dữ liệu

| | |
|---|---|
| Nguồn | Google Drive trong README PaTeCon |
| (S,P,O) trùng với bản TeCoRe mình dùng trước | **100%** |
| Kết quả mining | **12 constraint** (paper báo 13 — xem PATECON_VS_OURS §2.2) |
| Conflict phát hiện | **747** |

## 2. Bộ dữ liệu chính thức có 57.3% ĐỘ CHÍNH XÁC GIẢ

```
gia tri thoi gian : 99,698  (TAT CA deu 8 chu so = day-precision)
ket thuc "0101"   : 57,090 = 57.3%
ky vong neu that  :          0.27%
-> gap 209 lan
```

Họ **pad** `YYYY` và `YYYYMM` thành `YYYYMMDD` bằng cách thêm `0101`. Sau khi pad, thuật
toán **không còn phân biệt được** "năm 1638" với "ngày 1 tháng 1 năm 1638".

*(Bản TeCoRe giữ `YYYYMM` nên chỉ 13.35% giả — chính việc chuẩn hoá sang day-precision đã
đẩy tỉ lệ lên 57.3%.)*

## 3. Hệ quả: một phần tư conflict của họ là GIẢ

Phân tích 747 conflict, tìm mẫu **cùng năm + một bên là `0101`**:

| | số | tỉ lệ |
|---|---|---|
| **GIẢ** (cùng năm, một bên là năm-only bị pad) | **185** | **25.5%** |
| còn lại | 541 | 74.5% |

Phân ra: `P570 MutualExclusion` **96 cái**, `P569 MutualExclusion` **89 cái**.

### Ví dụ thật, nguyên văn từ output

```
Q24085, P570, 16380101   vs   Q24085, P570, 16381202
        "mat nam 1638"              "mat 2/12/1638"

Q88706, P570, 18800101   vs   Q88706, P570, 18800525
        "mat nam 1880"              "mat 25/5/1880"

Q89553, P569, 18930101   vs   Q89553, P569, 18930301
        "sinh nam 1893"             "sinh 1/3/1893"
```

**Không cái nào mâu thuẫn.** Mỗi cặp là *một phát biểu thô* và *một phát biểu chính xác hơn*
về **cùng một sự kiện** — đúng định nghĩa **REFINEMENT** trong taxonomy T5, không phải CONFLICT.

Nhưng sau khi pad, `16380101 ≠ 16381202` nên PaTeCon báo là vi phạm MutualExclusion.

### Với constraint `before` thì còn nặng hơn

| constraint | tổng | dính `0101` |
|---|---|---|
| `P569 before P570` | 23 | **17 (74%)** |
| `P569 before P54` | 3 | **3 (100%)** |
| `P108 before P570` | 2 | **2 (100%)** |
| `P569 before P108` | 2 | **2 (100%)** |
| `P26 before P570` | 1 | **1 (100%)** |

**Toàn bộ conflict `before` không phải `P569–P570` đều dính độ chính xác giả.**

---

## 4. Ý nghĩa

> **Xử lý granularity đúng làm giảm số conflict của PaTeCon từ 747 xuống ~541 (−25%).**

Đây là bằng chứng mạnh nhất có thể có cho hướng T5, vì:

1. **Trên chính bộ dữ liệu họ phát hành**, không phải MAVEN — reviewer không thể bác bằng
   "anh chọn dataset thuận lợi"
2. **Bằng chính code của họ**, tham số đúng README
3. **Định lượng được**: 25.5%, với ví dụ nguyên văn kiểm tra tay được
4. Nó **giải thích vì sao** họ không đo precision được: nếu đo, sẽ lộ ra 25.5% này

Và nó khớp với điều họ tự thừa nhận:

> *"only conflicting pairs are detected and no resolution is performed, so **precision is
> not calculated**"* — §6.1.2

## 4b. KIỂM CHỨNG TRỰC TIẾP qua Wikidata API — và điều chỉnh diễn giải

Truy vấn `wbgetclaims` cho 60 giá trị `0101` trong tập conflict (45 thành công, 15 lỗi API):

| trạng thái hiện tại trên Wikidata | số | tỉ lệ |
|---|---|---|
| precision=11 (NGÀY) — giá trị `0101` **đã bị thay** bằng ngày chính xác | 36 | 80% |
| **precision=9 (NĂM)** — vẫn là năm ⇒ **xác nhận độ chính xác giả** | **8** | **18%** |
| precision=10 (THÁNG) | 1 | 2% |

### Điều chỉnh: hai diễn giải, phải phân biệt

**Nhóm 18% (precision=9)** — chắc chắn: giá trị chỉ có độ chính xác **năm**, nhưng dataset
của PaTeCon ghi thành `YYYY0101`. Conflict sinh ra từ đó là **giả hoàn toàn**.

**Nhóm 80% (precision=11 hiện tại)** — tinh tế hơn. Trong dump 2019 có **hai** claim
(`16380101` và `16381202`); hôm nay Wikidata **chỉ còn** `1638-12-02`. Nghĩa là:

- PaTeCon gắn cờ cặp này → **và Wikidata quả thật đã gỡ bỏ một giá trị**
- Nên **việc phát hiện là HỮU ÍCH**, nhưng **cách gọi tên thì SAI**

> Đây là vấn đề **dư thừa / độ chính xác**, không phải **mâu thuẫn**. `1638` và `1638-12-02`
> **không mâu thuẫn** — cái sau làm mịn cái trước. Xử lý đúng là **REFINEMENT: hợp nhất về
> giá trị chính xác hơn**, không phải **CONFLICT: báo mâu thuẫn**.

### Phát biểu chính xác cho bài báo

| Tuyên bố | Mức chắc chắn |
|---|---|
| 57.3% giá trị thời gian trong WD50K chính thức kết thúc `0101` (209× mức ngẫu nhiên) | ✅ **đo trực tiếp** |
| 25.5% conflict khớp mẫu "cùng năm + một bên `0101`" | ✅ **đo trực tiếp** |
| 18% giá trị `0101` được xác nhận là precision=NĂM qua Wikidata API | ✅ **kiểm chứng mẫu** |
| Các conflict đó là *dư thừa độ chính xác*, không phải *mâu thuẫn* | ⚠️ **lập luận**, có Wikidata gỡ bỏ giá trị thô làm chứng cứ hỗ trợ |
| Không thể tách hai nhóm nếu không có trường `precision` của dump 2019 | ✅ giới hạn đã biết |

**Không nên nói:** "25.5% conflict của PaTeCon là sai".
**Nên nói:** "25.5% conflict của PaTeCon thuộc mẫu độ-chính-xác-thô-vs-mịn; 18% mẫu kiểm
chứng được xác nhận là năm-only bị pad; chúng cần được xử lý như REFINEMENT chứ không phải
CONTRADICTION — và PaTeCon không có cơ chế nào để phân biệt."

---

## 5. Ghi chú công bằng

- Con số 25.5% là **cận dưới**: chỉ đếm mẫu *cùng năm + một bên `0101`*. Các mẫu khác
  (cùng tháng khác ngày do pad `YYYYMM`) chưa tính.
- `FuzzyTime` của họ **có** logic ba trị cho granularity khác nhau (Table 2: `2022-01` vs
  `2022` → `unknown`). Nhưng nó **không kích hoạt được** vì bộ dữ liệu đã pad hết về
  day-precision **trước khi** vào thuật toán. Lỗi nằm ở **khâu chuẩn bị dữ liệu**, không phải
  ở logic so sánh.
- Đây chính là lý do phải giữ cột `norm_method` và `granularity` trong schema (FINAL.md §4.2):
  **mất thông tin granularity ở khâu nhập liệu thì không cứu được ở khâu mining.**
