# Vì sao F1 cao hơn 53.5% — và nó KHÔNG đến từ mining nhiều constraint hơn

| | PaTeCon | TempEKG |
|---|---|---|
| Số constraint dùng để gắn cờ | **12** | **10** |
| P | 15.91% | **22.41%** |
| R | 22.00% | **38.53%** |
| F1 | 0.185 | **0.283** (+53.5%) |

> **Ta dùng ÍT constraint hơn mà kết quả cao hơn.** Nên nguồn gốc không nằm ở số lượng luật.

---

# 1. Ba nguồn, tác động lên BA TẬP TÁCH RỜI

Đây là điểm mấu chốt. Không phải đánh đổi trên một đường cong — mà là **cộng thêm vùng phủ**.

```
        toan bo fact WD50K (24,399 EVALUABLE)
        │
        ├── da gia tri (entity co >=2 gia tri cho 1 property)
        │      └── PaTeCon voi toi duoc  ──► NGUON 1: phan tang uncertainty  (↑P)
        │
        └── DON GIA TRI  (88% cai PaTeCon bo sot)
               └── PaTeCon KHONG THE voi toi ──► NGUON 2: detector don-fact  (↑R)
                                              ──► NGUON 3: rang buoc dinh luong (↑R)
```

## Nguồn 1 — Phân tầng uncertainty: **tăng P**

**Cơ chế:** PaTeCon so sánh **điểm** `YYYYMMDD`. Ta so sánh **khoảng + granularity**.

```
16380101 -> [1638-01-01 .. 1638-12-31] suspect_year
16381202 -> [1638-12-02 .. 1638-12-02] day
                    ↓
             LONG NHAU -> REFINEMENT, khong phai mau thuan
```

**Đóng góp đo được:** loại 201/747 cặp (26.9%) là REFINEMENT giả → P 15.91% → **20.82%**.

**Vì sao PaTeCon không làm được:** dữ liệu của họ pad hết về day-precision (57.3% giá trị
kết thúc `0101`, gấp 209× mức ngẫu nhiên). Thông tin granularity **bị mất ở khâu nhập liệu**,
không cứu được ở khâu mining.

## Nguồn 2 — Detector fact đơn giá trị: **tăng R**

**Cơ chế:** mọi họ constraint của PaTeCon cần **≥2 fact** để so sánh:
- MutualExclusion cần 2 giá trị cho cùng (entity, property)
- `before`/`disjoint` cần 2 fact

⇒ Fact đơn lẻ **về cấu trúc không thể bị gắn cờ**. Đo được: **88% (591/670)** fact sai bị
bỏ sót là đơn giá trị. Tỉ lệ bỏ sót theo property: `P54` **100%**, `P26` **100%**,
`P108` **100%**, `P286` **100%**.

**Tín hiệu tìm được** (tỉ lệ nền 3.47%):

| đặc trưng | P(sai) | lift |
|---|---|---|
| tháng/ngày = `00` | **58.1%** | **16.7×** |
| object là entity (quan hệ bị gỡ) | 24.7% | 7.1× |

**Đóng góp đo được:** R 21.19% → **38.18%**.

## Nguồn 3 — Ràng buộc định lượng: **tăng R nhẹ**

Tuổi thọ >120 hoặc <0 · thi đấu sau khi chết · sự nghiệp lệch tuổi · ngoài biên phân bố.

Đây là **future work PaTeCon tuyên bố** (§8: *"quantitative relationships, such as
$t_2-t_1 \le 10$ years... Future work"*).

**Đóng góp đo được:** R 38.18% → **38.53%**, P 22.31% → **22.41%**.

---

# 2. Bảng cộng dồn — thấy rõ từng nguồn

| cấu hình | P | R | F1 | nguồn thêm vào |
|---|---|---|---|---|
| PaTeCon | 15.91% | 22.00% | 0.185 | — |
| phân tầng | 20.82% | 21.19% | 0.210 | **N1** ↑P |
| + `m00d00` | 21.38% | 25.26% | 0.232 | **N2a** ↑R |
| + `entity-obj` | 22.31% | 38.18% | 0.282 | **N2b** ↑R |
| + định lượng | **22.41%** | **38.53%** | **0.283** | **N3** ↑R |

---

# 3. Quyết định thiết kế mang tính sống còn

## 3.1 XẾP HẠNG, không LỌC

Bản đầu **vứt bỏ** cặp REFINEMENT:

| | P | R | F1 |
|---|---|---|---|
| PaTeCon | 15.91% | 22.00% | **0.185** |
| lọc bỏ REFINEMENT | 19.55% | 19.09% | **0.193** |
| lọc bỏ (nhãn chặt DELETED) | 4.65% | 8.52% | **0.060 < 0.066** ❌ |

Dưới nhãn chặt, **lọc còn TỆ HƠN PaTeCon**. Bản xếp hạng (giữ tầng UNDECIDABLE) → 0.210.

> **Uncertainty temporal là HÀM XẾP HẠNG, không phải BỘ LỌC NHỊ PHÂN.**

## 3.2 Lift cao KHÔNG đủ — phải xét precision ở mức triển khai

Đặc trưng `0101` có lift **12.4×** trên tập đơn-giá-trị. Nhưng khi triển khai trên **toàn bộ**
EVAL, nó phủ **2,483 fact ở precision chỉ 5.03%**:

| thêm `0101` vào | P | R | F1 |
|---|---|---|---|
| không | 21.38% | 25.26% | **0.232** |
| có | 9.73% | 39.23% | **0.156** ❌ |

**Loại nó khỏi cấu hình cuối.** Lift đo trên tập con ≠ precision khi triển khai.

## 3.3 Nhãn loại trừ lẫn nhau làm hỏng phép đo

Lần đầu mình đo "COARSE có dự đoán lỗi không" → **lift 0.0×**, kết luận nhầm là T5 vô dụng.

Sai ở đâu: nhãn `COARSE`/`DELETED`/`REFINED` **loại trừ lẫn nhau theo định nghĩa**, nên giao
tất yếu bằng 0. Phải dùng **đặc trưng thô** trong giá trị (`o[4:]=='0101'`), không phải nhãn.

Sửa xong → lift **12.4×**. **Đây là lỗi phương pháp suýt làm mất cả hướng đi.**

---

# 4. Tóm tắt một câu

> F1 tăng 53.5% vì hệ thống **phủ được một quần thể mà PaTeCon về cấu trúc không thể chạm
> tới** (fact đơn giá trị, 88% cái họ bỏ sót), đồng thời **sửa cách biểu diễn thời gian**
> để loại 26.9% cảnh báo giả — chứ **không phải** vì mine ra nhiều luật hơn (10 so với 12).
