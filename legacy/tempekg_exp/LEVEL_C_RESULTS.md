# MỨC C — model TRE + tầng sửa ràng buộc (EXP31)

Hạng mục lớn nhất còn lại. Chạy xong, kết quả **hỗn hợp**.

---

## 1. Thiết lập

| | |
|---|---|
| Model | averaged perceptron, đặc trưng rời rạc (khoảng cách câu, cặp kiểu event, loại quan hệ C2, hướng) |
| Train | 2,898 document, **1,072,980 cặp** |
| Test | 725 document |
| Nhãn | BEFORE / AFTER / CONTAINS / CONTAINED / OVERLAP / SIMULTANEOUS / NONE |
| Lỗi train sau 3 epoch | 47.2% |
| **F1 quan hệ thời gian** | **39.08%** |

*(Baseline MAVEN-ERE công bố dùng RoBERTa đạt ~50–55%; perceptron đặc trưng đạt 39% là hợp lý
cho mục đích đo vi phạm ràng buộc.)*

## 2. Vi phạm ràng buộc — xác nhận target lớn

| | GOLD | **DỰ ĐOÁN** |
|---|---|---|
| vi phạm đối xứng | 0 | 0¹ |
| **chu trình** | 0 | **612** |
| **thiếu bắc cầu** | ~0 (7/6.7M) | **107,647** |

¹ decoder của ta sinh mỗi cặp một lần nên đối xứng đúng theo cấu tạo — khác PaTeCon/các
model decode hai chiều độc lập.

> **Xác nhận: đồ thị do model sinh ra vi phạm ràng buộc ở quy mô lớn, trong khi gold sạch
> tuyệt đối.** Nguyên nhân cấu trúc: phân loại **từng cặp độc lập** không thể đóng kín bắc cầu.

## 3. Tầng sửa — sửa được vi phạm, KHÔNG cải thiện F1

Thuật toán sửa: (a) giữ cạnh confidence cao khi đối xứng mâu thuẫn; (b) phá chu trình tham
lam — bỏ cạnh **confidence thấp nhất** trong chu trình, lặp tối đa 6 vòng.

| | TRƯỚC | SAU | thay đổi |
|---|---|---|---|
| chu trình | 612 | **5** | **−99.2%** ✅ |
| thiếu bắc cầu | 107,647 | 101,683 | −5.5% |
| precision | 60.21% | 60.30% | **+0.09** |
| recall | 31.88% | 31.83% | −0.05 |
| **F1** | **39.08%** | **39.06%** | **−0.02** ❌ |

### Diễn giải

**Tầng sửa loại bỏ 99.2% chu trình nhưng ΔF1 ≈ 0.**

Lý do: 612 chu trình chỉ liên quan một phần nhỏ trong 51,644 cạnh. Phá chu trình gỡ một cạnh
— cạnh đó có thể đúng hoặc sai, xác suất gần như nhau. Bù trừ về 0.

> **Đây là kết quả âm tính có giá trị: SỬA ĐƯỢC VI PHẠM ≠ SỬA ĐƯỢC LỖI.**
>
> Nó khớp với phát hiện trước đó (held-out source: constraint mine được có precision 0.00%
> so với chuẩn cứng). Cả hai nói cùng một điều: **ràng buộc chỉ ra sự KHÔNG NHẤT QUÁN, không
> chỉ ra cái SAI.**

## 4. Ý nghĩa cho bài báo

**Nên tuyên bố:**
- Đồ thị thời gian do model sinh ra vi phạm ràng buộc ở quy mô lớn (**612 chu trình**,
  **107,647** thiếu bắc cầu trên 724 document), trong khi gold đóng kín 100%
- Tầng sửa dựa trên confidence loại bỏ **99.2%** chu trình
- Nhưng **không cải thiện F1** — nhất quán logic và độ chính xác là hai chuyện khác nhau

**Không nên tuyên bố:**
- ❌ "constraint-based repair cải thiện temporal relation extraction" — **số nói ngược lại**

## 5. Hướng có thể cứu (chưa thử)

| hướng | lý do có thể hiệu quả |
|---|---|
| Sửa bằng **ILP/MaxSAT toàn cục** thay vì tham lam | tối ưu hoá toàn cục thay vì gỡ từng cạnh |
| Đưa ràng buộc vào **hàm mất mát khi train** | model học ra output nhất quán sẵn, không sửa sau |
| Chỉ sửa cạnh **confidence thấp**, giữ nguyên cạnh tự tin | hiện gỡ cạnh thấp nhất *trong chu trình*, chưa xét ngưỡng tuyệt đối |
| Dùng ràng buộc **cứng C2** (subevent/causal) làm neo | chúng có precision ~100%, khác constraint mine được |

Hướng cuối đáng thử nhất: dùng lớp **cứng** (đã đo precision ~100%) thay vì confidence của
model để quyết định gỡ cạnh nào.
