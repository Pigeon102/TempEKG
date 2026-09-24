# Phương pháp mình có tốt hơn PaTeCon không, và làm sao để tốt hơn

Suy luận dựa trên toàn bộ số đã đo (EXP1–19 + tái lập PaTeCon gốc).

---

# 1. Trả lời thẳng: HIỆN TẠI CHƯA TỐT HƠN

Không nên tự lừa. Bảng đối chiếu thật:

| | PaTeCon | Mình |
|---|---|---|
| Loại conflict bao phủ | T2, T3, T4(hẹp) | **chỉ T3** |
| Constraint trên WD50K | **12** (12C/0M/0W) | 5 (5C/0M/0W) |
| Mutual exclusion | ✅ cài đặt | ❌ chưa |
| Disjointness | ✅ cài đặt | ❌ chưa |
| Structural pattern | SP(a) + SP(b) | chỉ SP(a) |
| Logic ba trị FuzzyTime | ✅ đầy đủ | ❌ so sánh số trực tiếp |
| Tốc độ WD50K | 1.1 s | ~2 s |
| Đã công bố, được kiểm chứng | ✅ AAAI 2023 | ❌ |

**Về độ bao phủ và độ chín, họ hơn.** 5 constraint của mình là **tập con** của 12 cái họ tìm.

---

# 2. Nhưng có ba chỗ mình HƠN — đều có bằng chứng đo được

## 2.1 Ngưỡng cứng 0.9 của họ mong manh — đã chứng minh

Constraint thứ 13 của họ:

$$\text{conf} = \frac{80}{89} = 0.898876 \quad\text{vs ngưỡng } 0.9$$

**Một instance duy nhất** quyết định constraint này có được giữ hay không. Ở $n=89$, cận
dưới Wilson 95% của $80/89$ chỉ khoảng **0.82** — tức bằng chứng thực sự **chưa đủ** cho
tuyên bố "conf ≥ 0.9", dù điểm ước lượng gần chạm.

→ **Thay điểm ước lượng bằng cận dưới Wilson.** Đây là cải tiến có cơ sở toán học, và
lỗi mà nó sửa xuất hiện **ngay trong kết quả chính của paper họ**.

## 2.2 Họ không kiểm soát false discovery — đã đo

Trên MAVEN với ngưỡng kiểu họ (support≥10, conf≥0.9): hoán vị nhãn trong document cho
**139.8/403 constraint vẫn qua ngưỡng do may rủi** → **FDR ≈ 34.7%**.

Sau khi thêm Wilson + BH-FDR: **FDR → 0.0%**.

Họ **không có** bước này. Với 234 property trên WD27M, số phép thử lớn hơn nhiều lần
WD50K, nên rủi ro này ở dữ liệu lớn của họ **còn cao hơn**.

## 2.3 Họ không kiểm chứng constraint trên dữ liệu chưa thấy

PaTeCon mine trên toàn bộ KG rồi dùng luôn. **Không có held-out.**

Mình đo: constraint đạt conf ≥ 0.9 trên MINE giữ được **86.1%** trên document chưa từng
thấy (macro 84.8%). Đó là con số họ **không hề báo cáo** và không thể báo cáo với thiết kế
hiện tại.

---

# 3. Lỗ hổng SÂU NHẤT của họ — và là chỗ novelty lớn nhất

## 3.1 PaTeCon không phân biệt được "vi phạm" với "ngoại lệ hợp lệ"

Đây là vấn đề gốc, sâu hơn mọi thứ ở §2.

Phương pháp của họ là **thống kê tần suất** nhưng được dùng như **logic**:

1. Mine constraint có conf ≥ 0.9
2. conf = 0.9 nghĩa là **10% dữ liệu vi phạm nó**
3. Báo cáo 10% đó là "conflict"
4. **Không bao giờ kiểm** xem chúng là **lỗi thật** hay **ngoại lệ hợp lệ**

Chính họ thừa nhận trong §6.1.2:

> *"only conflicting pairs are detected and no resolution is performed, so **precision is
> not calculated**"*

Ví dụ cụ thể từ output chạy lại: `P569 MutualExclusion` conf **0.9766** → 363 conflict.
Nhưng 2.3% người có hai ngày sinh — đó là **lỗi dữ liệu**, hay là **nguồn sử liệu thật sự
mâu thuẫn** (Washington sinh 11/2 lịch Julian hay 22/2 lịch Gregory)? Họ không phân biệt được.

> **PaTeCon đo được RECALL (bắt được bao nhiêu fact sai đã biết) nhưng KHÔNG đo được
> PRECISION (bao nhiêu cái nó báo là thật sự sai).**

## 3.2 MAVEN có lợi thế cấu trúc mà Wikidata KHÔNG có

Đây là lập luận mạnh nhất và mình mới nhận ra khi so hai substrate.

| | Nguồn constraint | Vi phạm nghĩa là gì |
|---|---|---|
| **Wikidata** | **chỉ tần suất** — mine ra từ dữ liệu | mơ hồ: lỗi *hoặc* ngoại lệ |
| **MAVEN** | tần suất **+ NGỮ NGHĨA QUAN HỆ** | với constraint ngữ nghĩa: **chắc chắn là lỗi** |

MAVEN có loại constraint mà Wikidata **về cấu tạo không có**:

$$\textsf{subevent}(e_1,e_2) \;\Rightarrow\; \textsf{contains}(t_1,t_2)$$
$$\textsf{CAUSE}(e_1,e_2) \;\Rightarrow\; \neg\,\textsf{after}(t_1,t_2)$$

Đây **không phải quy luật thống kê** — chúng đúng **theo định nghĩa** của quan hệ subevent
và quan hệ nhân quả. Một sự kiện con **không thể** nằm ngoài sự kiện cha. Vi phạm chúng là
**lỗi chắc chắn**, không phải ngoại lệ.

Wikidata không có gì tương đương: `P569 before P570` đúng vì sinh học, nhưng KG không
*khai báo* mối quan hệ ngữ nghĩa nào giữa hai property đó — phải mine ra từ tần suất.

**Hệ quả:** MAVEN cho phép làm điều Wikidata không cho — **tách constraint CỨNG (ngữ nghĩa,
vi phạm = lỗi chắc chắn) khỏi constraint MỀM (thống kê, vi phạm = có thể là ngoại lệ)**,
và dùng lớp cứng làm **chuẩn vàng để đo precision của lớp mềm**.

---

# 4. Kế hoạch để tốt hơn họ — xếp theo sức mạnh bằng chứng

## Trụ 1 — Tách CỨNG / MỀM và đo precision _(novelty cao nhất)_

Điều họ tuyên bố không làm được ("precision is not calculated"), substrate của mình cho phép:

- **Constraint cứng**: từ ngữ nghĩa quan hệ (subevent⇒contains, cause⇒¬after). Đo được:
  **72 vi phạm** trên gold, xác nhận độc lập 2 lần.
- **Constraint mềm**: mine theo tần suất, có Wilson + FDR.
- **Đo chéo**: trong số conflict mà constraint mềm báo, bao nhiêu % trùng với vi phạm
  constraint cứng? Đó là **ước lượng precision không cần annotate**.

Đây là thứ **không thể làm trên Wikidata** vì không có lớp cứng.

## Trụ 2 — T5 GRANULARITY _(khoảng trống rõ nhất)_

| | |
|---|---|
| Trên chính dữ liệu của PaTeCon | **13.35%** giá trị day-precision là `01-01` |
| Mức kỳ vọng nếu là ngày thật | 0.27% |
| **Bội số** | **49×** |
| PaTeCon phát hiện được | **0 — không có cơ chế** |
| Paper có nhắc tới không | **không, một lần nào** |

Trên MAVEN: **17,102 event mang ≥2 anchor** — quần thể tương ứng, cơ chế khác (anchor lồng
nhau thay vì `0101`).

Lập luận này mạnh vì nó **không dựa vào MAVEN để chứng minh** — bằng chứng đến từ dữ liệu
gốc của chính bài mình kế thừa.

## Trụ 3 — Chặt chẽ thống kê _(dễ làm, rõ ràng)_

| Cải tiến | Sửa lỗi gì | Bằng chứng |
|---|---|---|
| Cận dưới Wilson thay điểm ước lượng | ngưỡng lật vì 1 instance | constraint #13 = 80/89 |
| BH-FDR | 34.7% khám phá giả | permutation null |
| Held-out validation | không ai kiểm constraint | 86.1% giữ được |
| Support đếm theo document | cặp trong doc không độc lập | trung vị 10 doc/signature |

## Trụ 4 — Mức C: conflict trên đồ thị dự đoán _(target lớn nhất)_

Gold có 72 conflict. Đồ thị **dự đoán** có **85,243** vi phạm bắc cầu + **735** chu trình
(77% / 26% document). PaTeCon **không chạm tới kịch bản này** — họ chỉ audit KG tĩnh.

---

# 5. Điều KHÔNG nên tuyên bố

Trung thực để tránh bị bác:

- ❌ "Phương pháp của chúng tôi mine tốt hơn PaTeCon" — **sai**, họ bao phủ nhiều loại hơn
- ❌ "MAVEN nhiều conflict hơn Wikidata" — tỉ lệ cùng bậc (0.12% vs 0.23% ordering)
- ❌ "Constraint mining khám phá tri thức mới" — trên **cả hai** substrate nó chủ yếu tái
  khám phá cái con người viết tay được
- ✅ "Chúng tôi bổ sung loại conflict họ không xử lý, thêm kiểm soát thống kê họ thiếu, và
  khai thác lớp constraint ngữ nghĩa mà substrate của họ không có"
