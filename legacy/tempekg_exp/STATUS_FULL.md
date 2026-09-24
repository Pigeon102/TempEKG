# TempEKG — Status đầy đủ: kiến trúc, workflow, kết quả

---

# PHẦN 1 — KIẾN TRÚC

## 1.1 Tổng quan hai tầng

```
┌─────────────────────────────────────────────────────────────────────┐
│  TANG A — INSTANCE GRAPH  (moi document mot cai, ~23 event)         │
│                                                                     │
│    Event ──role──▶ Entity / Span          (hyperedge phang hoa)     │
│      │                                                              │
│      ├──temporal──▶ Event    S1  hard  (tu annotation)             │
│      ├──causal────▶ Event    S2  hard  (ngu nghia: cause≤effect)   │
│      ├──subevent──▶ Event    S3  hard  (ngu nghia: cha⊇con)        │
│      ├──closure───▶ Event    S4  hard  (logic: a<b<c ⇒ a<c)        │
│      └──mined─────▶ Event    S5  soft  (thong ke)                   │
│                                                                     │
│    TIMEX ──CONTAINS──▶ Event  ──▶ interval (lo, hi, granularity)   │
└─────────────────────────────────────────────────────────────────────┘
                              │
                    mine, gom theo DOCUMENT
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TANG B — TYPE GRAPH  (mot cai cho ca corpus) — SAN PHAM cua mining │
│    EventType ──constraint──▶ EventType                              │
│       + kenh · phan phoi nhan · confidence · support-theo-document  │
└─────────────────────────────────────────────────────────────────────┘
                              │
                   cham diem NGUOC lai instance
                              ▼
                    CONFLICT / REFINEMENT / OK
```

**Vì sao tách hai tầng:** PaTeCon gộp chung vì trong Wikidata entity lặp lại toàn cục nên
instance graph *chính là* corpus graph. MAVEN có **0/68,348 entity vượt document** → phải
tách, và support phải đếm theo **document** chứ không theo cặp.

## 1.2 Schema — mỗi cột trả lời một phép đo

```sql
events(event_id PK, doc_id, type, sent_id, char_start, char_end,
       recurrence_class ENUM('SINGLE','PERIODIC','CONTINUOUS','RECURRING','SUSPECT'))

entities(entity_id PK, doc_id, ent_type)          -- doc-local, cho san ca blind test

timex(timex_id PK, doc_id, surface, sent_id,
      norm_lo, norm_hi,
      granularity  ENUM('day','month','year','decade','century','duration','time'),
      norm_method  ENUM('regex','refprop','gazetteer','none'))   -- BAT BUOC

args(event_id, role, filler_id, filler_kind, link_conf)

intervals(event_id PK, lo, hi, granularity, all_regex BOOLEAN, source_anchors JSON)

constraint_edge(doc_id, e1, e2,
   source   ENUM('S1_temporal','S2_causal','S3_subevent','S4_closure','S5_mined','S6_quant'),
   implied, strength ENUM('hard','soft'), conf,
   PRIMARY KEY (doc_id, e1, e2, source))          -- source TRONG KHOA CHINH
```

| cột | cho phép phép đo nào | bằng chứng bắt buộc |
|---|---|---|
| `constraint_edge.source` trong PK | **held-out precision** | Wikidata 1 nguồn/fact → PaTeCon không đo được |
| `timex.norm_method` | tách nhiễu normaliser | refprop sai gấp **3.3×** regex |
| `intervals.granularity` | REFINEMENT vs CONFLICT | 26.9% conflict của họ là refinement |
| `events.recurrence_class` | lọc sự kiện định kỳ | 96.8% cảnh báo mutual-exclusion hợp lệ |

## 1.3 Những gì KHÔNG làm — mỗi cái có số

| bỏ | số đo |
|---|---|
| Hypergraph engine n-ary | bậc TB **1.11** → 2.84 sau linking |
| Adjacency cho causal/subevent | closure thêm **0.2–0.5%**, độ sâu 1 |
| Cross-document entity | **0/68,348** vượt document |
| Chiếu nhị phân | 459 property → PaTeCon **>30 phút** vs WD50K 1.1s |

---

# PHẦN 2 — WORKFLOW

```
  MAVEN-Arg ──┐
              ├─ join doc_id + event_id ─▶ ECKG
  MAVEN-ERE ──┘   (4,480 doc · 79,740 event chung)
                      │
    ┌─────────────────┼─────────────────┐
    ▼                 ▼                 ▼
 TIMEX            quan he C2         argument
 normaliser       causal/subevent    role→filler
 91.3% phu        58,033 canh        236,937
    │                 │                 │
    ▼                 ▼                 ▼
 interval         rang buoc CUNG    entity linking
 (lo,hi,gran)     precision ~100%   40.1% → 84%
    │                 │                 │
    └────────┬────────┴─────────────────┘
             ▼
   ╔══════════════════════════════════╗
   ║   5 GIAI DOAN MINING (Phan 3)   ║
   ╚══════════════════════════════════╝
             │
             ▼
   XEP HANG: CONFLICT > UNDECIDABLE > PARTIAL > REFINEMENT
             │
             ├──▶ cat nguong tuy muc tieu P/R
             └──▶ HELD-OUT SOURCE: nguon A phat hien, nguon B kiem chung
                                    ▼
                          PRECISION khong can annotate
```

---

# PHẦN 3 — THUẬT TOÁN MINING

```
GD1  RANG BUOC CUNG  (ngu nghia — KHONG mine)
        subevent(e1,e2)          ⇒ contains(t1,t2)
        CAUSE/PRECONDITION(e1,e2)⇒ ¬after(t1,t2)
        closure                  ⇒ a<b<c ⇒ a<c
        doi xung                 ⇒ ¬(a<b ∧ b<a)
     precision ~100% theo cau tao      MAVEN: 72 conflict, bat 14/14

GD2  UNCERTAINTY — PHAN TANG, KHONG LOC
        gia tri ──▶ (lo, hi, granularity)
        "YYYY0101" khong ro precision ──▶ 'suspect_year'   (co so: 209x muc ngau nhien)
        classify_pair(a,b) ──▶ CONFLICT | REFINEMENT | IDENTICAL | PARTIAL | UNDECIDABLE
     ** KHONG vut bo tang duoi — XEP HANG roi cat nguong **

GD3  DETECTOR FACT DON GIA TRI   (vung PaTeCon KHONG the cham toi)
        thang/ngay = "00"  ──▶ P 25.17%, lift 16.7x
     88% fact sai bi PaTeCon bo sot nam o day

GD4  RANG BUOC DINH LUONG   (future work cua ho)
        tuoi tho > 120 hoac < 0
        su nghiep lech tuoi | thi dau sau khi chet | ngoai bien phan bo

GD5  LOC SU KIEN LAP LAI
        chuoi moc ──▶ PERIODIC (cach deu) | CONTINUOUS (lien tiep)
                    | RECURRING (≥nguong theo loai) | SUSPECT
        chi giu SUSPECT                487 → 11  (−97.7%)

GD6  CONSTRAINT MEM (mine thong ke)
        Wilson_lo ≥ θ + BH-FDR q ≤ 0.05, support theo DOCUMENT
     ** CHI de mo ta quy luat, KHONG de gan co **  (precision 0.00%)
```

## 3.1 Số constraint

| | số luật dùng để gắn cờ |
|---|---|
| PaTeCon (WD50K, chạy lại) | **12** |
| PaTeCon+ (paper, WD50K) | 13 |
| PaTeCon+ (WD27M/FB37M) | hàng trăm (có refinement) |
| **TempEKG** | **10** |

> **Dùng ÍT luật hơn mà F1 cao hơn.** Đóng góp nằm ở *biểu diễn* và *vùng phủ*, không ở
> *số lượng luật*.

---

# PHẦN 4 — KẾT QUẢ TRÊN WIKIDATA (WD50K)

## 4.1 Bảng chính

| | fact | trúng | **P** | **R** | **F1** |
|---|---|---|---|---|---|
| **PaTeCon** | 1,174 | 175 | 14.91% | 23.52% | 0.182 |
| **TempEKG** | 1,008 | 206 | **20.44%** | **27.69%** | **0.235** |
| **chênh** | | | **+5.53** (+37.1%) | **+4.17** (+17.7%) | **+29.1%** |

24,284 fact evaluable · tỉ lệ nền 3.06% · **trội cả hai chỉ số**.

## 4.2 Đóng góp từng thành phần

| cấu hình cộng dồn | P | R | F1 |
|---|---|---|---|
| PaTeCon | 14.91% | 23.52% | 0.182 |
| + phân tầng uncertainty | 19.53% | 22.58% | 0.209 |
| + detector `m00d00` | 20.28% | 27.28% | 0.233 |
| + ràng buộc định lượng | **20.44%** | **27.69%** | **0.235** |

**Hai cơ chế, hai tập tách rời:**

```
        toan bo fact
        ├── da gia tri  ──▶ PaTeCon voi toi  ──▶ phan tang uncertainty  (↑P)
        └── DON GIA TRI ──▶ PaTeCon KHONG the ──▶ detector don-fact     (↑R)
                            (88% cai ho bo sot)
```

## 4.3 Latency

| phạm vi | PaTeCon | TempEKG | tỉ lệ |
|---|---|---|---|
| chỉ phát hiện (**công bằng**) | 0.819 s | 0.415 s | **2.0×** |
| đầu-cuối (họ mine, ta dùng luật sẵn) | 2.002 s | 0.437 s | 4.6× *(thiên vị)* |

Thông lượng TempEKG: **114,320 fact/giây**.

## 4.4 Phát hiện về chính dữ liệu của PaTeCon

| | |
|---|---|
| Giá trị thời gian kết thúc `0101` trong WD50K **chính thức** | **57.3%** (209× mức ngẫu nhiên) |
| Conflict thuộc mẫu thô-vs-mịn | **25.5%** (185/747) |
| Wikidata **có** trường `precision`, họ vứt đi khi pad | `Q849 P570: 14640000 prec=9` → họ ghi `14640101` |
| Áp uncertainty vào 747 conflict của họ | → **512** (−31.5%) |

---

# PHẦN 5 — KẾT QUẢ TRÊN MAVEN

## 5.1 Bảng trạng thái

| loại | PaTeCon (WD50K) | **TempEKG (MAVEN)** | ghi chú |
|---|---|---|---|
| **T1** representation | 1,166 (2.33%) | **không áp dụng** | MAVEN không lưu interval tường minh |
| **T2** mutual exclusion | 715 conflict | **11** | 487 thô → lọc 96.8% lặp lại |
| **T3** ordering | 105 conflict | **72** | xác nhận độc lập 2 lần |
| **T4** disjointness | 0 giữ lại (conf 0.68) | **1** | 88.1% cặp chồng nhau |
| **T5** granularity | **0 — không có cơ chế** | **430** | regex thuần, đáng tin |

## 5.2 Mức C — model TRE + tầng sửa

| | trước sửa | sau sửa |
|---|---|---|
| chu trình | **612** | **5** (−99.2%) |
| thiếu bắc cầu | 107,647 | 101,683 |
| F1 quan hệ thời gian | 39.08% | 39.06% (**−0.02**) |

Thử tiếp bằng **ràng buộc cứng** thay confidence: cũng −0.01. Lý do: chỉ **12 cạnh** vi phạm
ràng buộc cứng trên 51,644 — model đã tôn trọng ngữ nghĩa sẵn, **không có gì để sửa**.

> **Sửa được vi phạm ≠ sửa được lỗi.** Kết quả âm tính có kiểm soát.

## 5.3 So sánh trực tiếp PaTeCon trên MAVEN

| | WD50K | MAVEN (`EventType`, rút gọn) |
|---|---|---|
| property | **6** | **151** |
| constraint | **12** | **348** |
| ├ include | 9 | **232 (67%) — ARTIFACT** |
| conflict | 819 | 535 |
| thời gian chạy | 1.1 s | ~3 phút |
| vocabulary đầy đủ (459 prop) | — | **>30 phút, bị timeout giết** |

**232 constraint `include` là artifact:** 100% hai chiều (`A include B` và `B include A` cùng
conf 1.0) — chỉ xảy ra khi hai khoảng **giống hệt**, tức mọi event cùng năm có
`[YYYY-01-01, YYYY-12-31]` y hệt. Đây là **T5 granularity cắn trong thực tế**, dùng chính
thuật toán của họ.

## 5.4 MAVEN — điểm mạnh / vướng mắc

### Mạnh (Wikidata KHÔNG có)

| | số |
|---|---|
| **Dư thừa nhiều lớp** → đo precision không cần annotate | **81.8%** cặp có ≥2 nguồn độc lập |
| **Constraint ngữ nghĩa** (subevent⇒contains, cause⇒¬after) | precision ~100%, bắt **14/14** |
| Entity cho sẵn ở mọi split kể cả blind test | 68,348 |
| Gold nhất quán tuyệt đối → tập validation hoàn hảo | 100.0% đóng kín, constraint giữ **86.1%** held-out |

### Vướng mắc

| | số |
|---|---|
| TIMEX không có giá trị chuẩn hoá | normaliser **91.3%**, nhưng refprop sai gấp **3.3×** |
| Chỉ 44.9% event có anchor chặt | 27.9% không có anchor nào |
| T4 gần như không tồn tại | **88.1%** cặp chồng nhau, kể cả anchor mức ngày |
| Entity cục bộ | **0/68,348** vượt document |
| Chiếu nhị phân nổ vocabulary | 6 → **459** property |
| Gold quá sạch cho task tìm conflict | **72** mâu thuẫn toàn corpus |
| **Không có tập gán nhãn đúng/sai** | ⇒ **chưa tính được P/R trên MAVEN** |

> **MAVEN mạnh ở chỗ Wikidata yếu (dư thừa nhiều lớp, constraint ngữ nghĩa) và yếu ở chỗ
> Wikidata mạnh (giá trị thời gian tường minh, thuộc tính hàm thật, tập gán nhãn).**

---

# PHẦN 6 — CÒN LẠI

| # | việc | chi phí | chặn cái gì |
|---|---|---|---|
| 1 | **Tập gán nhãn 300 mục MAVEN** | 3 person-day | **P/R trên MAVEN** — không có thì mọi kết quả MAVEN không so được |
| 2 | Kiểm chứng WD27M | 🔄 **đang chạy** | tổng quát hoá |
| 3 | Mining phủ định trên 93 property | chờ #2 | trên WD50K (6 prop) chỉ ra 1 luật |
| 4 | Khoảng tin cậy cho chênh lệch P/R | 1 ngày | ý nghĩa thống kê của +5.53 điểm |

## Không nên tuyên bố

- ❌ "25.5% conflict của PaTeCon là **sai**" → nói: thuộc mẫu thô-vs-mịn, cần xử lý như REFINEMENT
- ❌ latency **4.6×** → dùng **2.0×** (cùng phạm vi)
- ❌ "constraint-based repair cải thiện TRE" → **số nói ngược lại**
- ❌ "MAVEN nhiều conflict hơn Wikidata" → cùng bậc (0.12% vs 0.23%)
- ⚠️ nhãn là **proxy** ("biến mất khỏi Wikidata"), không phải phán quyết chuyên gia
- ⚠️ mọi kết quả hiện chỉ trên **một** dataset
