# THIẾT KẾ CUỐI — đồ thị + thuật toán mining

Suy ra từ 29 thí nghiệm. Mọi lựa chọn đều có số chống lưng.

---

# PHẦN A — KẾT QUẢ ĐẠT ĐƯỢC

## A.0 ⭐ TRỘI CẢ HAI CHỈ SỐ (EXP30, **đã sửa sau kiểm định EXP32b**)

> ⚠️ **ĐÍNH CHÍNH.** Bản đầu báo P 22.41% / R 38.53% / F1 0.283. Con số đó **sai** vì
> detector `entity-obj` vô tình gộp **150 fact ngày ÂM (trước CN)**, mà pipeline gán nhãn
> của tôi **không xử lý được dấu trừ** (`norm_time` dùng `t[1:5]` nên `-0068-10-01` bị cắt
> thành `0069`). Mọi fact BC do đó bị gán nhãn `DELETED` oan → detector đạt "100% precision"
> **hoàn toàn là artifact**. Đã loại 150 fact đó và tính lại.

| | fact | trúng | **PRECISION** | **RECALL** | **F1** |
|---|---|---|---|---|---|
| **PaTeCon** | 1,174 | 175 | 14.91% | 23.52% | 0.182 |
| **TempEKG** | 1,008 | 206 | **20.44%** | **27.69%** | **0.235** |
| **chênh lệch** | | | **+5.53 điểm** (+37.1%) | **+4.17 điểm** (+17.7%) | **+29.1%** |

Trên 24,284 fact evaluable, tỉ lệ nền 3.06%.

### Cấu hình: `phân tầng + m00d00 + định lượng`

**Đã BỎ detector `entity-obj`:** đo riêng cho `P(sai) = 2.82%` — **thấp hơn tỉ lệ nền**
(lift 0.8×), tức vô dụng hoặc có hại. Toàn bộ "hiệu quả" của nó đến từ 103 fact ngày âm
bị gán nhãn sai.

**Vì sao trội được cả hai: hai cơ chế tác động lên HAI TẬP TÁCH RỜI.**

| cơ chế | tác động lên | hiệu quả |
|---|---|---|
| **Phân tầng uncertainty** | cặp **đa giá trị** của PaTeCon | ↑ P: loại 26.9% cặp REFINEMENT giả |
| **Detector fact đơn giá trị** | fact PaTeCon **không với tới** | ↑ R: 88% cái họ bỏ sót nằm ở đây |

Không phải đánh đổi trên một đường cong — mà là **cộng thêm vùng phủ mới**.

### Tín hiệu tìm được cho fact đơn giá trị

Tỉ lệ nền 3.47%. Đo trên 599 fact sai / 16,662 fact đúng:

| đặc trưng | P(sai) | **lift** | recall riêng |
|---|---|---|---|
| **tháng/ngày = `00`** | **58.1%** | **16.7×** | 4.19% |
| **object là entity** (quan hệ bị gỡ) | 24.7% | **7.1×** | 13.15% |
| `0101` | 43.1% | 12.4× | 14.55% |
| năm < 1800 | 8.4% | 2.4× | — |

⚠️ **`0101` bị LOẠI khỏi cấu hình cuối** dù lift 12.4×: nó phủ 2,483 fact ở precision chỉ
**5.03%** (do đo trên toàn bộ EVAL chứ không riêng đơn-giá-trị), kéo precision tổng xuống
9.73%. Bài học: **lift cao không đủ — phải xét precision ở mức triển khai thật.**

### Đóng góp từng thành phần

| cấu hình cộng dồn | P | R | F1 |
|---|---|---|---|
| PaTeCon | 15.91% | 22.00% | 0.185 |
| phân tầng | 20.82% | 21.19% | 0.210 |
| + `m00d00` | 21.38% | 25.26% | 0.232 |
| + `entity-obj` | 22.31% | 38.18% | 0.282 |
| **+ định lượng** | **22.41%** | **38.53%** | **0.283** |

---

## A.1 Đường cong P/R vs điểm đơn của PaTeCon

| cấu hình | fact | trúng | **P** | **R** | **F1** |
|---|---|---|---|---|---|
| **PaTeCon (gốc)** | 1,188 | 189 | 15.91% | 22.00% | 0.185 |
| T1 CONFLICT | 839 | 164 | 19.55% | 19.09% | 0.193 |
| T1+T2 (+UNDECIDABLE) | 874 | 182 | 20.82% | 21.19% | 0.210 |
| **T1+T2 + định lượng** ⭐ | 888 | 185 | **20.83%** | 21.54% | **0.212** |
| T1+T2 + dl + outlier | 904 | 186 | 20.58% | 21.65% | 0.211 |
| **TẤT CẢ + dl + outlier** ⭐ | 1,218 | 193 | 15.85% | **22.47%** | 0.186 |

**Hai điểm vận hành:**

| | so với PaTeCon |
|---|---|
| ⭐ **Ưu tiên precision** | P **+4.92 điểm** (+30.9% tương đối), R −0.46, **F1 +14.6%** |
| ⭐ **Ưu tiên recall** | R **+0.47 điểm** (22.47% > 22.00%), P −0.06 (ngang), F1 +0.5% |

> PaTeCon chỉ có **một điểm**; ta có **đường cong** — và chọn được điểm **đạt hoặc vượt
> recall của họ**, đúng yêu cầu.

## A.2 Vì sao PaTeCon bỏ sót 78% — điểm mù cấu trúc

| | |
|---|---|
| WRONG fact | 859 |
| PaTeCon bắt | 189 (22.0%) |
| **bỏ sót** | **670** |
| ├ **đơn giá trị** (entity chỉ có 1 giá trị cho property) | **591 = 88%** |
| └ đa giá trị | 79 = 12% |

**Mọi họ constraint của PaTeCon đều cần ≥2 fact để so sánh.** Fact đơn lẻ **không thể bị bắt**
— MutualExclusion cần 2 giá trị, `before`/`disjoint` cần 2 fact.

Tỉ lệ bỏ sót theo property: `P54` **100%**, `P26` **100%**, `P108` **100%**, `P286` **100%**,
`P569` 78%, `P570` 72%.

> **Đây là nguồn recall duy nhất còn lại, và cần loại constraint hoàn toàn khác:
> ràng buộc DỰA TRÊN MỘT FACT hoặc ĐỊNH LƯỢNG.**

---

# PHẦN B — ĐỒ THỊ

## B.1 Nguyên tắc: mọi cột đều phải trả lời một phép đo

| Cột | Phép đo nó cho phép | Bằng chứng bắt buộc |
|---|---|---|
| `constraint_edge.source` **trong PK** | held-out precision | Wikidata 1 nguồn/fact → PaTeCon không đo được |
| `timex.norm_method` | tách nhiễu normaliser | refprop có conflict gấp **3×** regex |
| `intervals.granularity` | phân biệt REFINEMENT vs CONFLICT | 26.9% conflict của họ là refinement |
| `events.recurrence_class` | lọc sự kiện định kỳ | 96.8% cảnh báo mutual-exclusion là hợp lệ |

## B.2 Schema

```sql
-- NODE
events(event_id PK, doc_id, type, sent_id, char_start, char_end,
       recurrence_class ENUM('SINGLE','PERIODIC','CONTINUOUS','RECURRING','SUSPECT'))
entities(entity_id PK, doc_id, ent_type)
timex(timex_id PK, doc_id, surface, sent_id,
      norm_lo, norm_hi, granularity ENUM('day','month','year','decade','century','duration'),
      norm_method ENUM('regex','refprop','gazetteer','none'))

-- HYPEREDGE phang hoa
args(event_id, role, filler_id, filler_kind, link_conf)

-- KHOANG CO DO KHONG CHAC CHAN
intervals(event_id PK, lo, hi, granularity, all_regex BOOLEAN, source_anchors JSON)

-- RANG BUOC, TACH THEO NGUON
constraint_edge(doc_id, e1, e2,
   source   ENUM('S1_temporal','S2_causal','S3_subevent','S4_closure','S5_mined','S6_quant'),
   implied, strength ENUM('hard','soft'), conf,
   PRIMARY KEY (doc_id, e1, e2, source))
```

## B.3 Những gì KHÔNG làm (đều có số)

| Bỏ | Số đo |
|---|---|
| Hypergraph engine n-ary | bậc TB 1.11 → 2.84 sau linking |
| Adjacency cho causal/subevent | closure thêm **0.2–0.5%**, độ sâu 1 |
| Cross-document entity | **0/68,348** vượt document |
| Chiếu nhị phân | 459 property → PaTeCon **>30 phút** vs WD50K 1.1s |

## B.4 Hiệu năng

| | build | mining | incremental |
|---|---|---|---|
| **materialized pairs** | 0.20s | **0.04s** | **0.03 ms/doc** |

Ba thiết kế cho **cùng** 11,817 signature (đã kiểm chứng).

---

# PHẦN C — THUẬT TOÁN MINING

```
GD1  RANG BUOC CUNG (ngu nghia, khong mine)
       subevent => contains  |  CAUSE => not after  |  closure
       precision ~100% theo cau tao          -> MAVEN: 72 conflict, bat 14/14

GD2  UNCERTAINTY — PHAN TANG, KHONG LOC
       moi gia tri -> (lo, hi, granularity)
       YYYY0101 khong ro precision -> 'suspect_year'   (co so: 209x muc ngau nhien)
       classify_pair -> CONFLICT | REFINEMENT | IDENTICAL | PARTIAL | UNDECIDABLE
       XEP HANG: CONFLICT > UNDECIDABLE > PARTIAL > REFINEMENT
       ** KHONG vut bo tang duoi — cat nguong tuy muc tieu P/R **

GD3  RANG BUOC DINH LUONG  (future work cua ho)
       tuoi tho > 120 hoac < 0
       su nghiep lech tuoi | ket hon sau khi chet | ngoai bien phan bo
       -> bat duoc fact DON GIA TRI ma GD1-2 khong the

GD4  LOC SU KIEN LAP LAI
       phan loai chuoi moc: PERIODIC | CONTINUOUS | RECURRING | SUSPECT
       chi giu SUSPECT              -> 487 -> 11 (giam 97.7%)

GD5  CONSTRAINT MEM (mine thong ke)
       Wilson_lo >= theta + BH-FDR q <= 0.05, support theo DOCUMENT
       ** CHI de mo ta quy luat, KHONG de gan co **
       (precision 0.00% so voi chuan cung — do bang held-out source)
```

## C.1 Bài học thiết kế quan trọng nhất

> **Uncertainty temporal là HÀM XẾP HẠNG, không phải BỘ LỌC NHỊ PHÂN.**

Bản đầu vứt bỏ REFINEMENT → mất recall mà không được precision (F1 **0.060 < 0.066** của
PaTeCon). Bản xếp hạng → F1 **0.212 > 0.185**.

---

# PHẦN D — SO SÁNH TỔNG

| | PaTeCon | TempEKG |
|---|---|---|
| Nguồn constraint | chỉ tần suất | tần suất + **ngữ nghĩa** + **định lượng** |
| Biểu diễn thời gian | **điểm** `YYYYMMDD` | **khoảng + granularity** |
| Ngưỡng | điểm ước lượng ≥0.9 | **cận dưới Wilson** |
| Kiểm soát bội | ❌ | **BH-FDR** (34.7% → 0%) |
| Đơn vị support | cặp | **document** |
| Held-out validation | ❌ | ✅ 86.1% |
| **Đo precision** | ❌ **không thể** | ✅ **held-out source** |
| Sự kiện lặp lại | gắn cờ hết | ✅ lọc 96.8% |
| Fact đơn giá trị | ❌ **không bắt được** | ✅ định lượng |
| Đầu ra | 1 điểm | **đường cong P/R** |
| **F1 tốt nhất** | **0.185** | **0.212 (+14.6%)** |
