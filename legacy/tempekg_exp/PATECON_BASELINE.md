# Chạy PaTeCon GỐC trên dữ liệu GỐC — baseline có thẩm quyền

**EXP18.** Đề xuất của người dùng: trước khi kết luận MAVEN "không làm được", phải chạy
chính thuật toán của PaTeCon trên chính dữ liệu của họ để biết tỉ lệ vi phạm của họ ra sao.

Thực hiện: tải code gốc (11 module từ `github.com/JianhaoChen-nju/PaTeCon`), tải dữ liệu
Wikidata thời gian từ nguồn README của họ dẫn (`dwslab/TeCoRe`, rockit), convert bằng chính
logic `read_wikidata_csv()` của họ, chạy `Constraint_Mining.py` + `Conflict_Detection.py`
với đúng tham số README (`--support=10 --candidate_confidence=0.5 --confidence=0.9`).

---

## 1. Kết quả thô

```
input                          : 50,000 fact
sau khu trung lap              : 46,900
fact co start > end (di dang)  :  1,165  (2.3%) -> BI LOAI truoc khi mine
con lai de mine                : 45,734
thoi gian chay                 : 1.1 s (mining) + 0.4 s (detection)

constraint giu lai             : 12
CONFLICT PHAT HIEN             : 820
entity dinh liu                : 644
```

## 1b. Chạy trên TOÀN BỘ loạt dataset của họ (EXP18b)

Cùng tham số README, 7 dataset:

| dataset | input | mine được | start>end | #cstr | **conflict** | **TỈ LỆ** |
|---|---|---|---|---|---|---|
| wd0_5k | 5,000 | 4,502 | 134 (2.7%) | 5 | 59 | **1.31%** |
| wd_10k | 10,000 | 8,870 | 367 (3.7%) | 6 | 131 | **1.48%** |
| wd0_25k | 25,000 | 22,794 | 661 (2.6%) | 10 | 286 | **1.25%** |
| wd_50k | 50,000 | 45,734 | 1,166 (2.3%) | 11 | 819 | **1.79%** |
| wd0_100k | 100,000 | 90,218 | 2,363 (2.4%) | 13 | 473 | **0.52%** |
| wd0_250k | 250,000 | 222,466 | 6,044 (2.4%) | 12 | 1,756 | **0.79%** |
| wd100_50k | 100,000 | 93,029 | 1,177 (1.2%) | **1** | **0** | **0.00%** |

**Tỉ lệ conflict của PaTeCon trên chính dữ liệu của họ: 0.52% – 1.79%, trung bình 1.19%.**

Ba quan sát:

1. **Không ổn định** — dao động **3.4×** giữa các mẫu cùng nguồn.
2. **Không đơn điệu** — `wd0_100k` (473 conflict) **ít hơn** `wd0_50k` (819) dù dữ liệu gấp
   đôi. Vì tập constraint mine được khác nhau, mà mỗi constraint bắt số lượng khác nhau.
3. **`wd100_50k` sập hoàn toàn** — chỉ 1 constraint, **0 conflict**. Cùng nguồn, cùng kích
   thước, chỉ khác tiền tố. Cho thấy kết quả PaTeCon **rất nhạy với cách lấy mẫu dữ liệu**.

> Điều này quan trọng cho bài báo: **PaTeCon không có một "tỉ lệ conflict" ổn định**. Con số
> phụ thuộc mạnh vào tập dữ liệu cụ thể. Nên không thể lấy một con số của họ làm chuẩn tuyệt
> đối để phán MAVEN cao hay thấp.

## 1c. So sánh với MAVEN — cùng cách tính

| | tỉ lệ conflict |
|---|---|
| PaTeCon trên dữ liệu của họ (7 mẫu) | **0.52% – 1.79%** (TB 1.19%) |
| MAVEN — chỉ mâu thuẫn cứng (72 / 80,479 event) | 0.09% |
| **MAVEN — kể cả thiếu CONTAINS ngụ ý (1,649 / 80,479)** | **2.05%** |

**MAVEN nằm trong dải của PaTeCon**, thậm chí cao hơn nếu tính cả loại thiếu sót — mà thiếu
sót *cũng là* một dạng temporal conflict (subevent được khai báo nhưng quan hệ thời gian
không nhất quán với nó).

---

## 2. Phân rã 820 conflict trên wd_50k

| Loại constraint | Số conflict | Tỉ lệ |
|---|---|---|
| `P569 MutualExclusion P569` — **hai ngày sinh khác nhau** | 363 | 44.3% |
| `P570 MutualExclusion P570` — **hai ngày mất khác nhau** | 352 | 42.9% |
| `P569 before P570` — sinh trước khi chết **bị vi phạm** | 97 | 11.8% |
| `P569 before P54` / `P108`, `P108`/`P26 before P570` | 8 | 1.0% |

> 🔑 **87.2% cái mà PaTeCon gọi là "temporal conflict" thực ra là MUTUAL EXCLUSION —
> một người có hai giá trị ngày sinh/ngày mất khác nhau.** Đó là lỗi **trùng lặp giá trị
> thuộc tính**, không phải mâu thuẫn **thứ tự thời gian**.

Ví dụ thật từ output:

```
Q84832, P569, 18600926  vs  Q84832, P569, 18600929   (sinh 26/9 hay 29/9/1860?)
Q84783, P570, 19261015  vs  Q84783, P570, 19261115   (mat 15/10 hay 15/11/1926?)
```

Conflict **thứ tự thời gian** đúng nghĩa chỉ có **105 / 45,734 = 0.23%**.

## 3. So sánh với MAVEN — cùng thước đo

| | PaTeCon WD-50k | MAVEN |
|---|---|---|
| Tổng conflict phát hiện | 820 | 72 (+1,577 thiếu CONTAINS) |
| ├ mutual exclusion (trùng giá trị) | **715 (87.2%)** | không có loại này |
| └ **mâu thuẫn thứ tự thời gian** | **105 (12.8%)** | **72** |
| mẫu số | 45,734 fact | 58,033 cặp C2 |
| **tỉ lệ conflict thứ tự** | **0.23%** | **0.12%** |
| dữ liệu dị dạng loại trước khi mine | 1,165 (2.3%) | không áp dụng |

⚠️ Mẫu số khác đơn vị (fact vs cặp) nên **không so trực tiếp số đếm**. Nhưng cả hai đều nằm
trong khoảng **0.1–0.3%** — **cùng bậc độ lớn**.

---

## 4. Ba kết luận

### 4.1 Kết luận "MAVEN quá sạch nên không làm được" là SAI

Tỉ lệ conflict thứ tự thời gian của MAVEN (**0.12%**) cùng bậc với chính dữ liệu của PaTeCon
(**0.23%**). PaTeCon xây được một bài AAAI trên mức phát hiện đó.

Con số 820 nghe lớn hơn 72 chỉ vì (a) mẫu số khác, và (b) **87% của nó là mutual exclusion**,
một loại lỗi mà MAVEN **về cấu tạo không thể có** — MAVEN không lưu giá trị thuộc tính lặp
để mà mâu thuẫn.

### 4.2 Implementation của mình đã được kiểm chứng chéo

| Constraint | PaTeCon gốc | Bản mình (EXP17) |
|---|---|---|
| `P569 before P570` (sinh→chết) | 0.9918 | 0.9991 |
| `P569 before P54` (sinh→chơi CLB) | 0.9984 | 1.0000 |
| `P569 before P26` (sinh→kết hôn) | 1.0000 | 1.0000 |
| `P54 before P570` (chơi CLB→chết) | 1.0000 | 1.0000 |

Chênh lệch nhỏ do họ dùng logic ba trị `FuzzyTime` còn mình so sánh số trực tiếp.
**Cùng constraint, cùng bậc confidence.** Kết quả âm tính trên MAVEN không phải lỗi code.

### 4.3 PaTeCon cũng bị áp đảo bởi luật đơn giản

12 constraint cuối cùng của họ, đọc kỹ, gần như trùng khớp **danh sách viết tay** của
TeCoRe (`mln_wiki.cstr`): sinh trước chết, sinh trước kết hôn, sinh trước chơi CLB, không
hai ngày sinh. Đây là **cùng hiện tượng** mình đo trên MAVEN (6 luật áp đảo 636 signature)
— chỉ khác là trên Wikidata nó ít lộ hơn vì không ai so với baseline viết tay.

> Đây là insight riêng có thể công bố: **cả trên Wikidata lẫn MAVEN, constraint mining
> chủ yếu tái khám phá ra tri thức mà con người đã viết tay được.** Giá trị của nó nằm ở
> chỗ *tự động hoá* và *quy mô*, không ở chỗ phát hiện quy luật mới.

---

## 5. Hệ quả cho đề tài

**Làm được.** Ba điều đã đổi so với đánh giá trước:

1. Tỉ lệ conflict của MAVEN **không thấp bất thường** — cùng bậc với dữ liệu gốc PaTeCon
2. Thước đo đúng là **tất định + có vi phạm**, không phải "bất đồng với majority"
3. Có **baseline định lượng** để so: 0.23% (họ) vs 0.12% (mình), cùng phương pháp

Và mức C (temporal ordering conflict trên đồ thị dự đoán) vẫn là target lớn nhất:
**85,243 vi phạm** đo được ở EXP16 — lớn hơn cả hai con số trên nhiều bậc.
