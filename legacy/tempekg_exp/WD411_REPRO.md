# WD-411: tái tạo được không, và phát hiện về chính phương pháp gán nhãn của họ

---

## 1. WD-411 KHÔNG được phát hành

| Nguồn kiểm tra | Có WD-411? |
|---|---|
| GitHub repo (`resource/`, `output/`, `dataset_build/`) | ❌ |
| Google Drive trong README | ❌ — chỉ có `WD50K.tsv`, `WD27M.tsv`, `FB37M.tsv`, 2 file type-info |
| Notebook `build_dataset_wikidata.ipynb` | ❌ — chỉ dựng WD27M/FB37M |

Notebook truy vấn **SPARQL endpoint riêng của lab** (`http://114.212.81.217:8890/sparql/`),
không truy cập được từ ngoài.

> **Hệ quả: đánh giá recall của PaTeCon KHÔNG tái lập được.** Tập gán nhãn duy nhất cho phép
> tính recall (WD-411, FB-128) không có công khai.

---

## 2. Nhưng phương pháp gán nhãn của họ thì tái tạo được

Trích §6.1.1:

> *"as the KG is continuously updated, wrong facts may have been corrected. Therefore, as long
> as the old version of KG is compared with the new version and the facts that are deleted are
> counted, the facts with high error probability can be obtained."*

Quy trình:
1. Lấy fact từ dump Wikidata **2019-01-28**
2. So với Wikidata **hiện tại**
3. Fact **bị xoá/đổi** = ứng viên sai xác suất cao
4. 2 chuyên gia kiểm từng ứng viên → gán nhãn đúng/sai
5. Thêm fact đúng theo tỉ lệ 1:1

**Bước 1–3 tái tạo được:** WD50K chính là trích từ dump 2019 đó, và Wikidata hiện tại truy
vấn được qua API công khai (`wbgetclaims`). Chỉ bước 4 (chuyên gia) là không tái tạo được.

---

## 3. Phát hiện: Wikidata CÓ lưu độ chính xác — PaTeCon vứt đi

Truy vấn `wbgetclaims` trả về trường **`precision`**:

| mã | nghĩa |
|---|---|
| 9 | năm |
| 10 | tháng |
| **11** | **ngày** |

```
Q23 P569 -> time=+1732-02-22T00:00:00Z  precision=11
```

Nhưng `WD50K.tsv` của họ chỉ có `17320222` — **không còn trường precision**. Mọi giá trị bị
pad về 8 chữ số, nên `1966` (precision=9) và `1966-01-01` (precision=11) trở thành **cùng
một chuỗi** `19660101`.

> Đây là bằng chứng cuối cùng cho luận điểm ở SMOKING_GUN.md: thông tin granularity **có sẵn
> trong nguồn**, bị mất ở **khâu chuẩn bị dữ liệu**, và không thể cứu ở khâu mining.

---

## 4. Phát hiện thứ hai: tiêu chí gán nhãn của họ lẫn "SAI" với "THÔ HƠN"

Kiểm chứng các giá trị `0101` trong conflict của họ qua Wikidata hiện tại:

```
Q24085  P570 16380101  ->  hien tai: +1638-12-02  precision=11 (NGAY)
Q88706  P570 18800101  ->  hien tai: +1880-05-25  precision=11
Q89553  P569 18930101  ->  hien tai: +1893-03-01  precision=11
Q67873  P569 17560101  ->  hien tai: +1756-10-20  precision=11
Q113285 P569 19660101  ->  hien tai: +1966-01-01  precision=9  (NAM)
```

Bốn dòng đầu: giá trị 2019 **đã bị thay** bằng ngày chính xác. Theo tiêu chí của họ, đó là
**ứng viên fact sai**.

Nhưng đọc kỹ: `1638` → `1638-12-02` **không phải sửa lỗi**, mà là **làm mịn độ chính xác**.
Giá trị cũ không sai — nó chỉ **thô hơn**.

> **Tiêu chí "fact bị xoá giữa hai phiên bản = fact sai" của họ gộp chung hai hiện tượng
> khác bản chất: SỬA LỖI và LÀM MỊN ĐỘ CHÍNH XÁC.**

Hệ quả cho WD-411: một phần tập gán nhãn của họ có thể là các **refinement** bị dán nhãn
"wrong", trừ khi hai chuyên gia đã phân biệt được — mà paper không nói rõ họ có phân biệt hay không.

Dòng cuối (`Q113285`) là trường hợp khác: giá trị **vẫn là precision=9 (năm)** trong Wikidata
hiện tại, nhưng dataset của họ ghi `19660101`. **Xác nhận trực tiếp độ chính xác giả.**

---

## 5. Hướng đi cho recall

| Cách | Khả thi | Ghi chú |
|---|---|---|
| Dùng WD-411 gốc | ❌ | không phát hành |
| Tái tạo ứng viên bằng API Wikidata | ✅ | tái lập bước 1–3 của họ |
| Gán nhãn chuyên gia | ⚠️ | ~3 person-day cho 300 mục |
| **Dùng `precision` của Wikidata làm nhãn granularity** | ✅ **miễn phí** | chuẩn vàng cho T5, không cần chuyên gia |

**Cách thứ tư là quan trọng nhất:** trường `precision` của Wikidata là **nhãn vàng có sẵn**
cho conflict granularity. Không cần gán nhãn thủ công, không cần WD-411. Cho phép tính
**precision VÀ recall của T5** trên chính dữ liệu của PaTeCon.

Đây là con đường sạch nhất để có bảng so sánh đầy đủ với họ.
