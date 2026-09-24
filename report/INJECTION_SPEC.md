# Giao thức tiêm xung đột tổng hợp

> Tài liệu cài đặt. Kèm theo `DEFINITIONS.md` mục **E5b**, **C3R**, **INJ**.
> Mọi con số ở đây đến từ code đã chạy. Chỗ nào chưa đo thì ghi **MỞ**; chỗ nào là **lựa chọn thiết kế**
> chứ không phải phép đo thì ghi rõ như vậy — đây là phân biệt quan trọng nhất trong cả tài liệu.
>
> Phạm vi mặc định: **MAVEN-ERE train = 2.913 document, 792.445 temporal relation**. Khi dùng subset
> (EVENT-EVENT, Arg-aligned, 300 doc...) thì ghi tại chỗ.

---

## 0. Tại sao phải tiêm

**Gold corpus có 0 mâu thuẫn cứng, và đó là tính chất cấu trúc, không phải may mắn.**

| Phép đo | Kết quả | Trên |
|---|---|---|
| Cặp ordered mang >1 nhãn khác nhau | **0** | full train, 792.445 quan hệ |
| BEFORE tồn tại theo cả hai chiều | **0** | full train |
| Document bất khả thoả theo PC-2 Allen đầy đủ | **0 / 2.913** | full train, bảng sinh brute force |
| Self-loop | **0** | full train |

Nguyên nhân nằm ở quy trình chú thích, không ở chất lượng dữ liệu: MAVEN-ERE Sec 2.2 cho biết annotator
**không** khẳng định nhãn theo cặp — họ sắp xếp điểm đầu/cuối của event và TIMEX trên **một** timeline, rồi
quan hệ được **suy ra tự động** từ vị trí tương đối. Một read-off từ một timeline đã sắp xếp thì **hiện thực
được theo định nghĩa**, nên không thể tự mâu thuẫn.

**Hệ quả cho đánh giá.** Không tồn tại tập lỗi gold, nên:

- **recall không đo được** trên gold — mẫu số không tồn tại;
- một conflict detector kiểu PaTeCon chạy trên MAVEN-ERE trả về **tập rỗng**, không phải vì constraint kém
  mà vì **không có gì để tìm**;
- mọi con số khác 0 trên gold sạch là **bug**, khả năng cao là coi closure residual không nhãn là xung đột,
  hoặc quên dedupe BEGINS-ON lưu hai chiều.

**Tiêm tổng hợp tạo ra ground truth bằng xây dựng.** Ta biết chính xác cung nào đã bị làm hỏng, nên recall
trở thành đại lượng đo được. Câu hỏi đánh giá đổi từ *"gold có chứa lỗi không"* (trả lời: về mặt cấu trúc là
không) sang *"detector thu hồi được bao nhiêu lỗi đã tiêm, ở precision nào"*.

> **Điều tiêm KHÔNG làm được — nêu ngay từ đầu để không tự lừa mình.** Tiêm không phá được tính vòng tròn:
> constraint vẫn khai thác từ chính chú thích mà chúng kiểm tra. Tiêm cũng không chứng minh được rằng
> candidate gắn cờ trên gold **thật sự** là lỗi annotator — chỉ phán xử người (`DEFINITIONS.md` E2/E4) trả
> lời được câu đó. Hai phép đánh giá này bổ sung nhau, không thay thế nhau.

---

## 1. Các toán tử làm hỏng

Năm toán tử. Mỗi toán tử ghi: định nghĩa, số cung áp dụng được, và **khả phát hiện** — tách bạch
**PAIRWISE** (một ô rỗng ngay lúc ingest, bảng B3 bắt được) với **TRIPLE** (chỉ PC-2 tới fixpoint bắt được)
với **INVISIBLE** (graph hỏng vẫn thoả được hoàn toàn).

Khả phát hiện dưới đây đo với **một** toán tử trên **một** document sạch, để quy trách nhiệm không nhập
nhằng. Đó là trường hợp **thuận lợi nhất**; dưới nhiều injection đồng thời, con số thấp hơn.

### 1.1. `flip` — đổi nhãn tại chỗ

Thay nhãn `r` của một cung bằng `r' ≠ r`, giữ nguyên hướng và endpoint.

Khả phát hiện tổng: **PAIRWISE 0,2% · TRIPLE 73,2% · INVISIBLE 26,6%** (n=400).

Nhưng con số gộp che mất cấu trúc quan trọng: **không phải flip nào cũng phát hiện được về nguyên tắc.**
Phân loại tiên nghiệm 30 flip có thứ tự theo quan hệ tập giữa các tập Allen:

| Lớp | Số flip | Nghĩa | Khả phát hiện thực đo |
|---|---|---|---|
| DISJOINT | 22 | tập Allen mới rời tập cũ | 47,5% – 98,5% |
| **VACUOUS** | **4** | tập mới **chứa** tập cũ ⇒ PC không bao giờ thấy | **đúng 0,0%** |
| STRENGTHEN | 2 | tập mới là con thực sự | 69,2% – 86,5% |
| CROSS | 2 | giao khác rỗng, không bao hàm | 46,2% – 75,5% |

**Bốn flip VACUOUS phải được loại khỏi injector hoặc tính riêng:**
`BEFORE→ENDS-ON`, `ENDS-ON→BEFORE`, `SIMULTANEOUS→CONTAINS`, `SIMULTANEOUS→BEGINS-ON`.

> Hai cái đầu là hệ quả trực tiếp của B1: `MAP[BEFORE] = MAP[ENDS-ON] = {b, m}`. Hai nhãn này **đồng nhất**
> với tầng logic. Đây cũng là lý do detector **không bao giờ** gắn cờ được nhầm lẫn BEFORE↔ENDS-ON — có lẽ
> là nhầm lẫn dễ xảy ra nhất giữa hai nhãn gần nghĩa. Muốn bắt cần **tiên đề loại trừ** riêng (mỗi cặp
> ordered có nhiều nhất một nhãn gold — đã kiểm chứng 0 vi phạm), không thể dựa vào giao tập.

### 1.2. `reverse` — đảo chiều cung

Thay `r(a,b)` bằng `r(b,a)`, **xoá** cung gốc (mô hình REPLACE).

Khả phát hiện: **PAIRWISE 0,0% · TRIPLE 88,8% · INVISIBLE 11,2%** (n=400).

> **Phải phân biệt hai mô hình cùng tên `reverse`, chúng cho kết quả khác hẳn:**
>
> | Mô hình | Cơ chế | Khả phát hiện |
> |---|---|---|
> | **REPLACE** (dùng cái này) | xoá cung gốc, thêm cung ngược | **95%** — cần chu trình |
> | ADD (không dùng) | **giữ** cung gốc, thêm cung ngược | **100% — nhưng tầm thường** |
>
> Dưới ADD, document chứa BEFORE theo **cả hai chiều** trên cùng một cặp. Verified ground fact: gold có
> **0** cấu hình như vậy. `{b} ∩ {bi} = ∅` nên ô rỗng **ngay lúc ingest**, không cần Allen, không cần PC,
> không cần trích lõi — một vòng `for (a,b) in BEFORE: if (b,a) in BEFORE` bắt 200/200. Dùng ADD rồi khoe
> "PC + QuickXplain thu hồi 100%" là **đo một baseline tra-từ-điển** và gán công cho cả bộ máy.
> **Dùng REPLACE. Nếu vì lý do nào đó dùng ADD, bắt buộc in baseline 2-cycle cạnh mọi con số.**

`reverse` là **no-op ngữ nghĩa** trên hai quan hệ đối xứng: `MAP[SIMULTANEOUS] = {e}` và
`MAP[BEGINS-ON] = {e,s,si}` đều tự nghịch đảo. Chúng chiếm 753/82.088 = 0,92% cung.
**Injector phải từ chối và rút lại mẫu**, không được ghi nhận rồi tính vào mẫu số FN — một corruption chứng
minh được là không đổi gì thì không thể là "phát hiện trượt".

### 1.3. `delete` — xoá cung

Xoá một cung gold. Khả phát hiện: **0,0% PAIRWISE · 0,0% TRIPLE · 100% INVISIBLE** (n=400) — và điều này
**đúng theo cấu trúc**, không phải yếu kém của detector: xoá làm **yếu** hệ ràng buộc, nên không thể sinh
mâu thuẫn.

Câu hỏi đúng cho `delete` không phải "có phát hiện được không" mà "closure có **khôi phục** được nhãn đã xoá
không". Đo trên 600 lần xoá:

| Kết quả | Số | Tỉ lệ |
|---|---|---|
| EXACT (chiếu về đúng `{gold}`) | 22 | **3,67%** |
| PARTIAL (gold nằm trong tập, tập lớn hơn) | 541 | 90,17% |
| NONE (vẫn FULL 13) | 37 | 6,17% |
| WRONG | **0** | 0% |

3,67% thấp **dù** PC chốt cặp về **một** nguyên tử Allen duy nhất ở 504/600 trường hợp. Lý do là B1 **không
phải antichain** — tính theo nguyên tử Allen độc quyền:

| Nhãn | Nguyên tử độc quyền | Định danh được? |
|---|---|---|
| CONTAINS | `{di, fi}` | **CÓ** (đạt 64,7%) |
| OVERLAP | `{o}` | CÓ |
| BEGINS-ON | `{s}` | CÓ |
| BEFORE | — | **KHÔNG** (đạt 0,0%) |
| SIMULTANEOUS | — | **KHÔNG** |
| ENDS-ON | — | **KHÔNG** |

BEFORE chiếm 86,26% corpus và **không bao giờ** khôi phục được, nên tổng thể là 3,67%.

**Hệ quả cho trọng số:** `delete` đóng góp **0** vào recall **theo định nghĩa**. Trọng số của nó là thứ
**trực tiếp** quyết định trần phát hiện — xem mục 4. Đó là lựa chọn thiết kế, phải khai báo, không được
trình bày như phép đo.

### 1.4. `insert` — thêm nhãn lên cặp chưa có nhãn

Khả phát hiện: **PAIRWISE 0,0% · TRIPLE 8,2% · INVISIBLE 91,8%** (n=400).

Gần như vô hình, và lý do có ý nghĩa: cặp chưa có nhãn thì chưa có nhãn **chính vì** nó bị ràng buộc yếu —
MAVEN-ERE Sec 2.2 nói rõ đó là **sub-timeline, UNKNOWN có tài liệu**, không phải annotator quên. Hầu như
nhãn nào cũng vừa.

### 1.5. `cycle` — tạo chu trình BEFORE

> **CẢNH BÁO: toán tử này như đã cài là TẦM THƯỜNG, và con số "100% PAIRWISE" của nó là định nghĩa tuần
> hoàn.** Graph BEFORE của MAVEN **đóng bắc cầu** — đo được: **279.124/279.124** đường BEFORE 2-hop đều có
> cạnh trực tiếp head→tail. Nên hễ tồn tại đường a→…→b thì cạnh trực tiếp `(a,b,BEFORE)` **cũng tồn tại**,
> và việc thêm `(b,a,BEFORE)` luôn va vào một nhãn sẵn có **trên đúng cặp đó** — tức nó suy biến thành đúng mô
> hình ADD ở mục 1.2, bắt được bằng một lần tra từ điển. Đo: 400/400 trial ở mọi độ dài đường 1/2/3 đều có
> cạnh trực tiếp.
>
> **Hai lựa chọn, phải chọn một và ghi rõ:**
> 1. **Bỏ `cycle`** khỏi bộ toán tử (khuyến nghị) — nó không thêm gì mà `reverse` chưa có.
> 2. Định nghĩa lại: **xoá** cạnh trực tiếp `(a,b)` **trước**, rồi mới thêm `(b,a)`. Đó là cách duy nhất tạo
>    được chu trình nhiều bước thật trên một graph đóng bắc cầu. Khả phát hiện của biến thể này **MỞ**.

---

## 2. Tính hiện thực

### 2.1. Sự thật nền: không toán tử nào ở trên là chế độ lỗi thật

Phải nói thẳng, vì nó là điều kiện trung thực của cả paper. MAVEN-ERE **không cho phép** annotator khẳng
định một nhãn theo cặp (`ere.txt:307-343`, verbatim: *"we ask the annotators to sort the beginnings and
endings of events and TIMEXs on a timeline… the relations can be automatically inferred from their relative
positions"*). Giao diện cho phép đúng hai loại sai:

1. **Đặt sai vị trí một event trong một timeline** ("trượt timeline");
2. **Gán sai sub-timeline** — paper cho phép tạo sub-timeline và coi event trên hai timeline khác nhau là
   không có quan hệ. Chế độ này **chưa được mô hình hoá**; tuyên bố rõ là ngoài phạm vi.

Một lần trượt viết lại **nhiều** nhãn cùng lúc: bậc độ lớn là bậc của **bậc node**, đo được mean 22,4 /
median 18 / max 95 trên 7.335 node.

### 2.2. Trượt timeline có phát hiện được không — câu trả lời đã được sửa

> **Kết quả cũ "PC phát hiện 0/80 ⇒ chế độ lỗi thật bất khả phát hiện" KHÔNG ĐỨNG VỮNG.** Ghi lại ở đây vì
> nó suýt thành câu trung tâm của paper.
>
> Thí nghiệm cũ dựng timeline bằng topological sort trên graph BEFORE, gán các khoảng **đơn vị rời nhau**,
> rồi **đọc lại mọi nhãn** từ toạ độ đã nhiễu. Ba lỗi:
> - Output là read-off của một timeline **hiện thực được** ⇒ thoả được **theo cấu trúc**, bất kể có tiêm hay
>   không. **Control xác nhận: PC trên bản dựng chưa trượt cũng cho 0/80.** Một thủ tục trả 0 dù có hay không
>   có corruption thì không phân biệt được gì.
> - Bản dựng (khoảng đơn vị rời nhau) **không thể biểu diễn** CONTAINS / SIMULTANEOUS / OVERLAP, nên nó phá
>   huỷ **1.718/1.718** nhãn non-BEFORE **trước** khi trượt. "27,3 nhãn đổi" đo so với gold; so với đúng
>   baseline (bản dựng chưa trượt) chỉ là **6,6**.
> - "80 document" là một `break` cứng trong vòng lặp, không phải tỉ lệ lọc: **238/238** document trong nhóm
>   10–45 node đều dùng được.

**Mô hình đúng: trượt cục bộ.** Annotator dời **một** event, nên chỉ các cung **kề event đó** được đọc lại;
các cung còn lại giữ nhãn annotator đã ghi. Đo lại như vậy:

| | Đọc lại toàn bộ (sai) | **Trượt cục bộ (đúng)** |
|---|---|---|
| Nhãn đổi / lần trượt | 27,3 (so gold) / 6,6 (so control) | mean **7,4**, median 5, max 34 |
| PC phát hiện | 0/80 = 0% — **và control cũng 0%** | **32,5%** (và 35,0 / 36,2 / 43,8 / 37,5% trên 4 seed khác) |

**Phát biểu đúng cho paper:** tiêm theo cặp **không đồng dạng** với trượt timeline, nên recall từ tiêm là
**cận trên** của recall thực tế. Nhưng **không** được viết rằng chế độ lỗi thật là bất khả phát hiện — đo
được 32–44%.

### 2.3. Trọng số bộ toán tử — đây là LỰA CHỌN THIẾT KẾ

| Toán tử | Trọng số | Biện minh |
|---|---|---|
| `flip` | **0,60** | Gần nhất với hệ quả cục bộ của một lần trượt: event vẫn ở đó, quan hệ với láng giềng đổi loại |
| `reverse` | **0,15** | Trượt qua một láng giềng đảo thứ tự cặp đó |
| `delete` | **0,15** | Xấp xỉ việc gán sai sub-timeline (quan hệ biến mất) |
| `insert` | **0,07** | Gộp hai sub-timeline nhầm |
| `cycle` | **0,03** | Xem cảnh báo 1.5 — **khuyến nghị đặt 0,00** |

> **Bộ trọng số này là tham số khai báo, KHÔNG phải đại lượng đo được.** Nó phải xuất hiện trong paper như
> một tham số, và trần phát hiện phải báo cáo như **hàm của nó** (mục 4), không như một con số vô hướng.
> Kiểm tra độ nhạy là **bắt buộc**, vì `delete` có khả phát hiện 0% theo định nghĩa nên trọng số của nó
> dịch trần một-đổi-một.

### 2.4. Phân bố nhãn hỏng — ràng buộc quan trọng nhất trong cả tài liệu

**Không tồn tại injector flip bảo toàn phân bố biên.** Chứng minh một dòng: flip đòi `r' ≠ r`, nên
`P(new = r) ≤ 1 − p[r]`. Với `p[BEFORE] = 0,9104` (EE toàn train; 0,8626 trên mọi node), trần là **0,0896**,
còn mục tiêu là 0,9104. Bất khả.

**Hệ quả: mọi injector dựa trên flip đều tặng không lợi thế cho quy tắc "gắn cờ nhãn hiếm".** Dưới rút đều,
5/6 số lần rút rơi vào nhãn non-BEFORE vốn chỉ chiếm ~1,6% corpus. Đo được: cung được tiêm là **77,31%**
non-BEFORE so với **7,91%** của cung sạch.

Điều này **đảo ngược thứ hạng** giữa phương pháp và baseline — bảng quyết định, out-of-sample trên valid
(109.929 instance, family mine trên train, τ là ngưỡng C3R):

| Detector | FP sạch | R uniform | **R gold-marginal** | F1@ε=0,01 uniform | **F1@ε=0,01 gold-marginal** |
|---|---|---|---|---|---|
| family τ=0,05 | 0,673% | 0,388 | 0,170 | 0,378 | **0,185** |
| family τ=0,10 | 1,869% | 0,613 | 0,397 | 0,354 | **0,245** |
| B3 (mọi non-BEFORE) | 10,064% | 0,980 | 0,902 | 0,164 | 0,152 |
| B3' (ngoài {BEFORE,CONTAINS}) | 1,521% | 0,797 | 0,138 | 0,483 | 0,104 |
| **Brare** ({BEGINS-ON,ENDS-ON}) | 0,036% | 0,400 | 0,003 | **0,557** | **0,006** |

Dưới **uniform**, `Brare` — hai dòng code, không mining — **thắng** family. Dưới **gold-marginal**, `Brare`
sụp 93× còn family thắng baseline tốt nhất **1,6×**.

> **CHỐT: mô hình hỏng headline là gold-marginal** — rút `r'` từ phân bố nhãn của chính corpus, hạn chế trên
> `r' ≠ r`, chuẩn hoá lại. Uniform chỉ được in như **cột đối chiếu**, kèm câu giải thích rằng ưu thế của
> `Brare` ở cột đó là hiện vật của sampler.
>
> **MỞ — cải tiến đáng làm:** mô hình **confusion-weighted** (đổi trong cụm {BEFORE, CONTAINS} và trong cụm
> {OVERLAP, SIMULTANEOUS}, cộng đảo chiều), ước lượng từ một nghiên cứu bất đồng annotator thật. Nó vừa bảo
> toàn biên vừa nhắm đúng cặp dễ nhầm. Chưa đo.

---

## 3. Tỉ lệ tiêm

### 3.1. Đường cong mất kết dính

Tỉ lệ được đo qua năm mức, mỗi mức trên 300 document (mẫu số = **mọi** document đủ điều kiện, lấy mẫu
`k ~ Binomial(|E|, p)` để tỉ lệ theo cung đồng đều):

| Tỉ lệ | Doc bất khả thoả | Quy được trách nhiệm |
|---|---|---|
| **0,1%** | 13,1% | **61,5%** |
| 0,5% | 40,1% | 30,3% |
| 1% | 57,9% | 19,2% |
| 2% | 73,7% | 12,8% |
| 5% | 87,9% | 3,8% |

Control: **0/297** document sạch bất khả thoả.

> **Sửa hai lỗi của vòng đo trước.** (a) Mẫu số cũ chỉ đếm document **đã nhận** injection, cho 65,2% ở mức
> 0,1% và tạo ấn tượng "metric bão hoà ngay, vô dụng" — sai, với mẫu số đúng nó đi từ 13,1% tới 87,9%, phân
> biệt rất tốt. (b) `k = round(p·|E|)` khiến mọi document ≥500 cung **luôn** bị tiêm ở mức 0,1% trong khi
> document nhỏ rơi vào nhánh Bernoulli — tức mẫu ở tỉ lệ thấp bị **nạp đầy** những document to nhất, dễ vỡ
> nhất (mean 968 cung so với 276 toàn corpus). Dùng Binomial.
>
> Cũng lưu ý: "quy được trách nhiệm" như định nghĩa cũ (document bất khả thoả mang **đúng một** injection)
> phần lớn chỉ **phát biểu lại lịch tiêm** — ở tỉ lệ thấp gần như mọi document bị chạm đều nhận đúng một
> injection theo xây dựng. Đại lượng có nội dung là **có điều kiện**: trong số document có **đúng một**
> injection, bao nhiêu phần trăm có lõi tối tiểu **nêu đích danh** cung đó.

### 3.2. Tỉ lệ khuyến nghị

**CHỐT: 0,1%**, chạy kèm **0,5%** làm phân tích độ nhạy.

Ba lý do độc lập cùng chỉ về đây: quy trách nhiệm còn 61,5% (mức cao nhất trong năm mức); trôi pattern nhỏ
nhất (Jaccard 0,9815, mục 5); và document bất khả thoả còn 13,1%, tức đa số document vẫn sạch nên FP trên
gold sạch vẫn đo được trong cùng một lần chạy.

---

## 4. Trần phát hiện được

**Con số này phải in cạnh mọi con số recall trong paper.** Không có nó, recall là vô nghĩa.

> **Phân biệt hai đại lượng mà vòng đo trước đã nhập làm một:**
>
> | | Nghĩa | Giá trị |
> |---|---|---|
> | **Trần theo nguyên tắc** | có tồn tại mâu thuẫn PC phát hiện được không | **60,9%** |
> | Recall đạt được | một extractor cụ thể, dưới cap MAXE=400, thực sự nêu tên | ~26% |
>
> Con số 26,1% ± 2,1 **không phải trần** — nó là recall của một lần chạy QuickXplain có cap. Gọi nó là trần
> hạ thấp trần thật **2,3×** và quy một giới hạn cài đặt thành một giới hạn cấu trúc.

Trần theo nguyên tắc tính từ khả phát hiện từng toán tử (mục 1) nhân trọng số (mục 2.3):

```
0,60 × 0,734 (flip)    = 0,4404
0,15 × 0,888 (reverse) = 0,1332
0,15 × 0,000 (delete)  = 0,0000
0,07 × 0,082 (insert)  = 0,0057
0,03 × 1,000 (cycle)   = 0,0300
                        --------
trần PC (hard track)    = 0,6093  →  60,9%
```

**Độ nhạy theo trọng số `delete`** — phải in, vì đây là tham số ta tự chọn:

| trọng số `delete` | Trần |
|---|---|
| 0,00 | 29,7% *(dùng số recall đạt được)* / cao hơn nếu dùng trần nguyên tắc |
| 0,05 | 28,1% |
| **0,15 (khai báo)** | **25,3%** |
| 0,30 | 22,0% |

(Bảng trên tính trên **recall đạt được** theo từng toán tử ở tỉ lệ 0,5%; bảng trần-nguyên-tắc ở trên dùng
khả phát hiện single-injection. Phải in **cả hai** và nói rõ cái nào là cái nào.)

**Trần của tầng phân bố (family C3R)** là đại lượng riêng và **thấp hơn nhiều**, vì nó mù với BEFORE:

| Nhãn bị tiêm vào | Recall của family |
|---|---|
| BEFORE | **0,000%** — cấu trúc, xem dưới |
| CONTAINS | ~1,2% |
| OVERLAP | ~31% |
| SIMULTANEOUS | ~33% |
| BEGINS-ON | ~58% |
| ENDS-ON | ~61% |

> **BEFORE bất khả cấm — phải ghi vào paper.** 0/8.156 pattern trên cả năm level có `WilsonUB(BEFORE) < τ`,
> và **min WilsonUB(BEFORE) = 0,446**. Nên phát biểu đúng là *BEFORE bất khả cấm với mọi τ < 0,446, tức ở
> mọi điểm vận hành dùng được* — không phải "bất khả cấm vô điều kiện", vì reviewer bác được câu sau bằng
> một dòng.
>
> **Hệ quả bắt buộc: báo recall TÁCH THEO nhãn được tiêm, không bao giờ gộp.** Một con số recall gộp sẽ
> **giấu hoàn toàn** một điểm mù cấu trúc. Lưu ý dưới uniform, nhãn tiêm là BEFORE chỉ chiếm ~2% census
> (không phải ~1/6: phải đúng là non-BEFORE **rồi** rút trúng BEFORE, tức 0,10 × 0,20).

---

## 5. Chống rò rỉ

**CHỐT: mine trên corpus ĐÃ HỎNG, out-of-fold. Không bao giờ mine trên bản sạch.**

Lý do: trong bối cảnh triển khai thật **không tồn tại** bản sạch — ta mine constraint từ chính corpus đang
audit, vốn đã chứa lỗi. Mine trên bản sạch là đưa cho detector thông tin mà bối cảnh thật không thể cung cấp,
tức đúng dạng vòng tròn mà E5 đã cảnh báo.

> **Luật này đã bị vi phạm trong chính code của vòng đo trước.** `inj_strat2.py` và `inj_c5.py` mine ở dòng
> 52–53 từ `docs` **sạch**, chỉ làm hỏng fold held-out **sau đó**, trong vòng lặp đánh giá. Sửa lại (làm hỏng
> toàn corpus **trước**, rồi mine out-of-fold trên bản hỏng) hạ lift từ **1,36× xuống 1,22×**. Hiệu ứng sống
> sót về hướng, nhưng con số headline đã sinh ra dưới cấu hình bị cấm. **Chia out-of-fold KHÔNG khắc phục rò
> rỉ này** — nó chặn document tự chấm chính nó, chuyện khác hẳn.

**Chi phí mine trên dữ liệu hỏng — đã đo, và nhỏ ở tỉ lệ khuyến nghị.** Jaccard giữa family mine-hỏng và
family mine-sạch (1.000 document, family L1, 427 thành viên sạch từ 6.261 giả thuyết):

| Tỉ lệ | Jaccard | Mất | Thêm |
|---|---|---|---|
| **0,1%** | **0,9815** | 3 | 5 |
| 0,5% | 0,9402 – 0,9493 (3 seed) | 15–18 | 5–8 |
| 1% | 0,8973 | 34 | 11 |
| 2% | 0,8458 | 54 | 14 |
| 5% | 0,7494 | 98 | 12 |

Trôi đơn điệu theo tỉ lệ, và **độc lập củng cố** khuyến nghị 0,1% ở mục 3.

> **MỞ:** đây là family L1 type-pair, không phải lattice 5 level đầy đủ. Tỉ số trôi là đại lượng chuyển giao
> được; **liệu level cao hơn có trôi nhanh hơn không thì chưa đo.**

**Rò rỉ thứ hai, tinh vi hơn — leave-one-out dùng nhãn thật.** Nếu thủ tục LOO trừ đi đóng góp của instance
bằng cách tra **nhãn gold** của nó, thì detector được cho biết đâu là nhãn hỏng — chính là bit mà bối cảnh
thật không có. Phiên bản trung thực: tính thống kê pattern **trên corpus đã hỏng**, rồi trừ đi **nhãn quan
sát được** của instance (`cc[observed] -= 1`), không bao giờ chạm nhãn thật. Đo được: hai biến thể cho kết
quả **giống nhau tới ba chữ số có nghĩa** ở mức support này — nhưng vẫn phải cài bản trung thực và **công bố
đẳng thức đó như bằng chứng**, thay vì cài bản rò rỉ rồi tuyên bố đã làm đúng.

---

## 6. Giao thức thực nghiệm

### 6.1. Seed và fold

- **Seed**: công bố tường minh. Mọi con số headline chạy tối thiểu **5 seed**, báo mean ± sd. Vòng đo trước
  chạy một seed cho nhiều kết quả chính — không đủ.
- **Fold**: 5-fold, **chia theo DOCUMENT**, gộp train+valid (3.623 doc) theo E1. Chia trong document sẽ rò
  rỉ timeline qua ranh giới fold, vì nhãn là read-off tất định từ **một** timeline toàn cục.
- **Thứ tự bắt buộc**: `(1)` làm hỏng **toàn** corpus → `(2)` mine out-of-fold **trên bản hỏng** →
  `(3)` chấm trên fold held-out. Đảo thứ tự (1) và (2) là rò rỉ ở mục 5.
- **Tách tập chọn mô hình**: valid đã bị **đốt** cho việc chọn key L4 (C1c) và chọn τ (C3R, 14 cấu hình).
  Con số cuối **không** được báo trên valid như "out-of-sample". Dùng pool out-of-fold 7.755 của E1, hoặc
  chia valid làm hai nửa theo document (một nửa chọn, một nửa báo). `test.jsonl` **không dùng được**: 857
  document, không có key `events`, 0 quan hệ.

### 6.2. Metric

Với `I` = tập cung bị tiêm (ground truth), `F` = tập cung detector nêu tên:

```
TP = |F ∩ I|        FP = |F \ I|        FN = |I \ F|
precision = TP / |F|            recall = TP / |I|            F1 = 2PR/(P+R)
```

**Bốn luật bắt buộc:**

1. **`|I|` là mẫu số vô điều kiện** — gồm cả `delete` (không nêu tên được theo định nghĩa) và cả injection
   nằm trong document PC không bao giờ gắn cờ. Báo thêm recall **có điều kiện** (loại `delete`) như số phụ,
   **có nhãn rõ ràng**, không bao giờ thay cho số vô điều kiện.
2. **`reverse` trên quan hệ đối xứng không vào mẫu số** — đó là no-op chứng minh được (mục 1.2).
3. **Recall tách theo nhãn được tiêm.** Số gộp giấu điểm mù BEFORE 0,000% (mục 4).
4. **In trần phát hiện cạnh recall**, kèm mix toán tử đã dùng.

**Precision phải đo, không được suy ra bằng công thức trên hai tỉ lệ.** Công thức
`P = εN·recall / (εN·recall + (1−ε)N·fpr)` hợp lệ về số học nhưng trộn hai quần thể khác nhau (census kiểm
nhãn ~98% non-BEFORE; FP đo trên quần thể ~90% BEFORE). Dùng nó để **vẽ đường cong**, còn con số headline
phải đến từ một lần chạy tiêm thật ở tỉ lệ đã công bố.

### 6.3. Baseline — bắt buộc, chạy qua CÙNG census

| Baseline | Quy tắc | Vì sao bắt buộc |
|---|---|---|
| **random** | gắn cờ ngẫu nhiên cùng thể tích | sàn tuyệt đối |
| **B3** | gắn cờ mọi nhãn non-BEFORE | baseline reviewer sẽ dựng đầu tiên |
| **B3'** | gắn cờ mọi nhãn ngoài {BEFORE, CONTAINS} | chặt hơn B3, thường mạnh hơn |
| **Brare** | gắn cờ {BEGINS-ON, ENDS-ON} | **thắng family dưới uniform** — bỏ sót nó là để lại lỗ hổng chí mạng |
| **constant-CONTAINS** | luôn đoán CONTAINS | baseline của use case dự đoán |
| **majority theo type-pair** | gắn cờ `r` nếu `r` không phải argmax của cặp type | dùng cấu trúc pattern, không cần Wilson/BH/lattice |
| **2-cycle** | `(a,b,BEFORE) ∧ (b,a,BEFORE)` | chỉ khi dùng mô hình ADD — bắt 100% bằng một lần tra từ điển |

> **So sánh phải ở cùng ngân sách, không ở cùng tên gọi.** So precision của hai detector ở recall khác nhau
> (0,358 vs 0,980) là vô nghĩa — detector nào cũng mua được precision bằng cách bắn ít đi. Báo **đường cong
> precision–recall đầy đủ**, hoặc so ở **cùng số cờ**, hoặc dùng một đại lượng không phụ thuộc ε:
> **likelihood ratio = recall / FP-rate** (family τ=0,05 đạt 57,6 so với B3 9,74 — gấp 5,9×).

### 6.4. Danh mục kiểm tra trước khi công bố bất kỳ bảng nào

- [ ] **Control rỗng**: đường ống chạy với 0 corruption có trả về 0 không? (Bắt được vụ timeline slip.)
- [ ] **Null khớp biên**: mọi tuyên bố "đặc trưng X có ích" đối chứng bằng nhãn ngẫu nhiên khớp biên của X.
- [ ] **Cả bảy baseline** qua **cùng** census.
- [ ] **Cả hai mô hình hỏng** (uniform + gold-marginal), gold-marginal là cột headline.
- [ ] Recall **tách theo nhãn tiêm**; trần in kèm.
- [ ] Mẫu số của mọi tỉ lệ được nêu tường minh (tập node? có thứ tự? sau alignment?).
- [ ] Bảng Allen được **sinh** và assert lúc import (đã có **hai** bảng chép tay hỏng trong dự án).
- [ ] Tối ưu FULL-skip **đã tắt** trong mọi lần chạy injection (`comp(FULL, ∅) = ∅`, không phải FULL).
- [ ] B2 dedupe đã áp dụng (SIMULTANEOUS và BEGINS-ON, `motif_key = (min, r, max)`).
- [ ] ≥5 seed cho mọi con số headline.

---

## 7. Rủi ro

Xếp theo nghiêm trọng × xác suất. Mỗi mục kèm **cách phát hiện sớm**.

### RI-1 — "Bạn chỉ tìm thấy đúng cái bạn đã trồng" (NGHIÊM TRỌNG · CHẮC CHẮN BỊ HỎI)

**Phản biện của reviewer:** *Các anh tự tạo lỗi rồi tự tìm lại chúng. Điều đó không nói gì về lỗi thật.*

**Câu trả lời trung thực — bốn phần, và phần cuối là một nhượng bộ:**

1. **Đây đúng là điều chúng tôi tuyên bố, không hơn.** Chúng tôi **không** tuyên bố phát hiện lỗi trong
   MAVEN-ERE; chúng tôi đã kiểm tra và corpus **không chứa** mâu thuẫn logic (0/2.913 document theo Allen
   closure đầy đủ), vì lý do cấu trúc mà chúng tôi nêu rõ. Tiêm đo **độ nhạy của detector**, giống như đo
   độ nhạy của một test chẩn đoán trên mẫu đã biết. Không ai phản đối việc hiệu chuẩn thiết bị bằng mẫu chuẩn.
2. **Detector không được xem lịch tiêm.** Constraint mine trên corpus **đã hỏng**, out-of-fold, và chưa bao
   giờ nhìn thấy cung nào bị làm hỏng. Cấu hình rò rỉ (mine sạch) đo được cho lift cao hơn — **1,36× so với
   1,22×** — và chúng tôi báo con số **thấp hơn**, đúng con số hợp lệ.
3. **Trồng cái gì được quyết định TRƯỚC, và bị ràng buộc bởi phép đo.** Mô hình hỏng bảo toàn phân bố biên
   nhãn của corpus. Chúng tôi chỉ ra rằng mô hình rút-đều dễ dãi hơn sẽ **tự động** cho baseline hai dòng
   `Brare` thắng phương pháp (F1 0,557 vs 0,378) — và chúng tôi báo cả hai cột để reviewer tự thấy hiệu ứng.
   Đó là bằng chứng chúng tôi không chọn injector để mình thắng: chúng tôi chọn injector **khó hơn** và công
   bố cái dễ hơn ở ngay bên cạnh.
4. **Nhượng bộ, viết trong limitations:** chế độ lỗi thật của MAVEN-ERE là **trượt timeline**, không đồng
   dạng với tiêm theo cặp. Đo được: một trượt cục bộ viết lại trung bình **7,4** nhãn và PC bắt được
   **32,5–43,8%**, so với recall cao hơn trên tiêm theo cặp. **Mọi con số recall của chúng tôi là cận trên**
   của recall thực tế, và chúng tôi ghi đúng như vậy.

**Phát hiện sớm:** nếu recall trên tiêm **cao hơn nhiều** so với recall trên trượt timeline cục bộ, khoảng
cách đó chính là mức độ paper đang tự chấm điểm dễ. Đo cả hai, in cả hai.

### RI-2 — Mô hình hỏng sai làm đảo kết luận (NGHIÊM TRỌNG · ĐÃ XẢY RA BỐN LẦN)

Đây là chế độ hỏng thực nghiệm số một của dự án. Đã xảy ra: injector uniform (`Brare` thắng giả); trượt
timeline không control (kết luận "bất khả phát hiện" sai); `cycle` trên graph đóng bắc cầu ("100%" tuần
hoàn); "FPR" chia cho toàn bộ parent ("giảm 47×" trong khi FDP thật giảm 2,8–5,4×).

**Phát hiện sớm:** ba phép kiểm ở mục 6.4 — control rỗng, baseline tầm thường qua cùng census, null khớp
biên. Cả ba đều rẻ và cả ba đều đã bắt được ít nhất một lỗi thật ở vòng trước.

### RI-3 — Recall báo gộp giấu điểm mù cấu trúc (CAO · dễ vô tình phạm)

Family có recall **đúng 0,000%** trên nhãn tiêm BEFORE, và BEFORE là 86–91% corpus. Một con số recall gộp
làm điểm mù này biến mất khỏi paper.

**Phát hiện sớm:** nếu bảng kết quả không có cột "theo nhãn tiêm", bảng chưa xong. Kiểm tra cứng: recall
trên BEFORE **phải** in ra 0,000% — nếu khác 0, có bug ở đâu đó.

### RI-4 — Trần phát hiện bị trình bày như phép đo (CAO)

Trần là **hàm của trọng số toán tử**, mà trọng số do ta chọn. Đặc biệt `delete` có khả phát hiện 0% **theo
định nghĩa**, nên trọng số của nó dịch trần một-đổi-một (22% ↔ 30% chỉ do một tham số).

**Phát hiện sớm:** nếu trần xuất hiện trong paper như một số vô hướng không kèm mix, sai. In bảng độ nhạy.

### RI-5 — Luật hợp thành ràng buộc không đúng đắn (TRUNG BÌNH · hỏng âm thầm)

Nếu hai ràng buộc hợp lệ cùng áp lên một cặp (cha và con, hoặc hai level), phép hợp thành đúng là **GIAO**.
Để con "đặc thù hơn" **ghi đè** cha là vứt đi một ràng buộc chặt hơn còn hiệu lực. Đo được: dưới ghi đè,
thêm child làm **mất** 75–170 lỗi đã tiêm; dưới giao, **không mất gì** (TP 1.164 so với 1.163).

**Phát hiện sớm:** bất biến — thêm một tầng constraint **không bao giờ** được làm giảm TP. Nếu giảm, luật
hợp thành sai, không phải tầng sai.

### RI-6 — Lan truyền tính rỗng bị chặn bởi tối ưu hoá (TRUNG BÌNH · chỉ hiện dưới injection)

`comp(FULL, ∅) = ∅`, không phải FULL. Tối ưu "bỏ qua cung còn FULL" vì thế **chặn lan truyền của tính rỗng**.
Trên gold sạch vô hại (không ô nào rỗng); dưới injection nó hạ blast radius từ 99,9% xuống 67,5% và làm lõi
tối tiểu **không tìm được** mâu thuẫn 2 cung thật.

**Phát hiện sớm:** với một document đã tiêm, kiểm `∅` lan tới ~99,9% số ô. Nếu chỉ ~2/3, tối ưu đang bật nhầm.

### RI-7 — Tập chọn mô hình bị đốt hai lần (TRUNG BÌNH · vô hình nếu không kiểm)

Valid đã dùng để chọn key L4 **và** chọn τ trên 14 cấu hình. Báo hiệu suất của cấu hình thắng cuộc trên
chính tập đó là ước lượng **lạc quan do chọn lọc**, không phải out-of-sample. `test.jsonl` không cứu được:
nó không có quan hệ nào.

**Phát hiện sớm:** đếm xem mỗi split đã được chạm mấy lần và vì mục đích gì. Nếu >1 mục đích, cần chia tiếp.

### RI-8 — Phương sai seed chưa đo (THẤP · dễ sửa)

Nhiều con số headline của vòng trước chạy **một** seed. Với recall ~0,13–0,39, phương sai giữa các seed có
thể cùng bậc với hiệu số giữa các cấu hình đang so.

**Phát hiện sớm:** chạy 5 seed. Nếu sd cùng bậc với hiệu số đang tuyên bố, tuyên bố đó chưa có.

---

## 8. Bổ sung — tiêm HAI CHIỀU cho C3-A và C3-B

> Bản trên chỉ có toán tử **đổi nhãn**, phục vụ C3-A (annotator đánh sai). Mục này thêm
> toán tử **xoá cạnh** cho C3-B (annotator đánh thiếu), và đo trần của nó.
> Proof: `python tempekg_kg/proof_feedback.py`.

### 8.1. Hai toán tử, hai bài toán

```
ĐỔI nhãn   r → r'     mô phỏng annotator đánh SAI    → đo C3-A
XOÁ cạnh   (a,b,r) → ∅  mô phỏng annotator đánh THIẾU → đo C3-B
```

Khác biệt then chốt: sau khi **đổi** nhãn, đồ thị vẫn đủ cạnh nên có thể mâu thuẫn; sau khi
**xoá**, đồ thị vẫn nhất quán nhưng **nghèo đi**. Nên hai phép đo khác nhau hẳn:

| | C3-A (đổi nhãn) | C3-B (xoá cạnh) |
|---|---|---|
| Ground truth | cặp nào bị đổi và đổi thành gì | cặp nào bị xoá và nhãn gốc |
| Detector báo | vi phạm constraint | cặp không nhãn mà rule/closure ép ra nhãn |
| Đo được | precision **và** recall | precision **và** recall |
| Trên gold sạch | mọi lần bắn là false positive | không áp dụng |

Trước khi có toán tử xoá, recall của C3-B **không đo được** vì không có ground-truth về
"cạnh đáng lẽ phải có".

### 8.2. Thang closure — **4,9%**, và vì sao closure sâu hơn vô ích

Đo trực tiếp (`proof_ceiling.py`, 200 document, 948 cạnh): lấy một cạnh ra khỏi document,
hỏi suy luận logic có ép lại **đúng một nhãn** và đúng nhãn đó không.

| Phương pháp | Khôi phục chính xác | Mẫu |
|---|---:|---:|
| 1-step closure | 46 = **4,9%** | 948 |
| 2-step closure | 46 = **4,9%** | 948 |
| PC-2 tới fixpoint | 40 = **5,0%** | 808 |

**Closure sâu hơn không thêm gì** — PC-2 khôi phục đúng **0 cạnh** mà 1-step bỏ sót. So sánh
trên **cùng một population** (808 case mà PC-2 chạy được).

#### Vì sao bản trước báo 80,4%

Bản trước dùng phép kiểm **bao hàm** `implied ⊆ allen(gold)` — "mọi khả năng còn lại đều thoả
gold" — thay vì hỏi closure có chỉ ra được **một** nhãn không. Ba phép kiểm khác nhau, đừng lẫn:

| Phép kiểm | Câu hỏi | Kết quả |
|---|---|---:|
| `allen(gold) ∩ implied = ∅` | có mâu thuẫn không | 0 / 164.803 |
| `implied ⊆ allen(gold)` | có bị ràng buộc đủ không | 81,2% |
| **`len(compat(implied)) = 1`** | **có đoán ra được một nhãn không** | **4,9%** |

Phân rã con số 81,2%:

| | Case | Tỉ lệ |
|---|---:|---:|
| bao hàm thành công | 770 | 81,2% |
| — trong đó **thực sự quyết định được** | 46 | **4,9%** |
| — trong đó vẫn còn mơ hồ | 724 | 76,4% |

| Gold | Nhãn còn tương thích | Case |
|---|---|---:|
| BEFORE | BEFORE, ENDS-ON | **701** |
| SIMULTANEOUS | BEGINS-ON, SIMULTANEOUS | 21 |
| BEGINS-ON | BEGINS-ON, SIMULTANEOUS | 2 |

**97% độ lạm phát là đúng một case: BEFORE vs ENDS-ON.** Ánh xạ MAVEN→Allen chỉ chồng lấn ở
`b` (BEFORE ⊂ ENDS-ON) và `e` (SIMULTANEOUS ⊂ BEGINS-ON). Khi closure thu về `{b}` nó đã loại
CONTAINS/OVERLAP/SIMULTANEOUS nhưng **không tách được BEFORE khỏi ENDS-ON** — mà BEFORE chiếm
89,94% corpus, nên phép bao hàm gần như chỉ đang đo lại base rate.

**Không gọi 4,9% là "trần logic".** Đó là trần của **1-step closure dưới protocol xoá cạnh
hiện tại**, không phải cận trên toán học. Tên residual: *closure-undetermined under the 1-step
protocol*.

#### Hệ quả cho thiết kế thí nghiệm — đảo chiều so với bản trước

Nỗi lo cũ là "closure ăn mất 80,4%, recall của ta trông như của nó". Thực tế ngược lại:

> Closure thuần tuý chỉ khôi phục **4,9%**. **95,1% cạnh bị xoá** là population mà bằng chứng
> ngữ nghĩa — vai, entity chung, vị trí diễn ngôn — là nguồn thông tin duy nhất.

**Vẫn phải báo cáo tách**, nhưng lý do đổi: không phải để tránh khoe công của closure, mà để
cho thấy residual là *gần như toàn bộ bài toán*. `R_all` và `R_beyond` giờ gần bằng nhau.

**Phân tầng cạnh xoá** thành closure-recoverable (4,9%) và residual (95,1%) vẫn cần, nhưng
tầng dễ nhỏ đến mức xoá ngẫu nhiên hầu như luôn rơi vào tầng khó.

**Đừng dùng PC-2 làm baseline mạnh hơn.** Nó không hơn 1-step mà tốn hơn nhiều. Baseline logic
đúng là 1-step closure.

### 8.3. Giao thức bổ sung

```
KG sạch
   │
   ├── ĐỔI nhãn ε% cạnh          → KG_wrong
   │      ground truth: {(a,b,r_gốc,r_mới)}
   │      detector → vi phạm constraint
   │      đo: precision, recall, F1
   │
   └── XOÁ ε% cạnh                → KG_missing
          ground truth: {(a,b,r_gốc)}
          phân tầng: closure-recoverable vs không
          detector → cặp không nhãn bị ép ra nhãn
          đo: precision, recall, F1 THEO TỪNG TẦNG
```

Tỉ lệ ε dùng chung với mục 3 (khuyến nghị 0,1%, sensitivity 0,5%).

**Rò rỉ:** mine rule trên KG **sạch** hay KG **đã hỏng**? Với phép xoá, câu trả lời rõ hơn
phép đổi — phải mine trên KG đã xoá, vì trong thực tế annotator thiếu cạnh nào thì rule cũng
không thấy cạnh đó. Mine trên KG sạch là cho detector thông tin thực tế không có.

### 8.4. Điều phải nêu trong bài

Baseline closure **phải công bố cùng recall**. Phát biểu đúng:

> Transitive closure một mình khôi phục **4,9%** cạnh bị xoá. Trên **95,1%** còn lại — nhóm
> *closure-undetermined under the 1-step protocol* — bộ rule đạt recall X% với precision Y%.

Hai điều phải nói kèm, nếu không con số bị đọc sai theo hai hướng ngược nhau:

1. **Đừng báo phép bao hàm (81,2%) như tỉ lệ khôi phục.** 97% của nó là case BEFORE mà closure
   không tách được khỏi ENDS-ON — xem 8.2.
2. **Đừng nói "hệ thống khôi phục Z% cạnh thiếu" mà không tách tầng.** Ở đây tầng closure nhỏ
   (4,9%) nên rủi ro thấp, nhưng phép tách vẫn phải có để người đọc kiểm được.

---

## 9. Kết quả injection & detection — đã đo

> Chạy `inject.py` rồi `detect.py`, train split, gold-marginal, rate 0,001, seed 0,
> 300 document, 82.064 cặp, 60 lỗi bơm. Đây là lần đầu C3 có recall đo được.

### 9.1. Kiểm chứng bộ bơm trước khi tin bất kỳ số nào

| Phép kiểm | Kết quả | Spec dự đoán |
|---|---:|---:|
| RELABEL → document PC-inconsistent | 14,3% | 13,1% |
| … quy được về đúng 1 lỗi | 83,7% | — |
| DELETE → document PC-inconsistent | 0% | 0% (đúng theo lý thuyết) |
| Lỗi rơi vào {BEGINS-ON, ENDS-ON} | **0%** | uniform sẽ là 40% |

Bốn con số khớp spec. Bộ bơm hành xử đúng như đã tiên đoán **trước khi** chạy.

### 9.2. C3-A — quét τ

| Detector | P | R | F1 | tp/60 | gắn cờ | lift vs ngẫu nhiên |
|---|---:|---:|---:|---:|---:|---:|
| constraint τ=0,001 | 0,65% | 1,67% | 0,94% | 1 | 153 | 8,9× |
| **constraint τ=0,005** | **1,84%** | 31,67% | **3,47%** | 19 | 1.034 | **25,1×** |
| constraint τ=0,01 | 1,49% | 36,67% | 2,87% | 22 | 1.472 | 20,4× |
| baseline *all non-BEFORE* | 0,78% | **91,67%** | 1,55% | 55 | 7.015 | 10,7× |
| baseline *Brare* | 0% | 0% | 0% | 0 | 90 | 0× |

**τ=0,005 là điểm vận hành**: F1 gấp 2,2× baseline, precision gấp 2,4×. τ=0,01 bắt thêm 3 lỗi
nhưng precision tụt.

### 9.3. Vì sao τ=0,001 hỏng, và vì sao nới τ sửa được

| τ | constraint | cấm CONTAINS | cấm OVERLAP | cấm SIMULTANEOUS |
|---|---:|---:|---:|---:|
| 0,001 | 13.589 | **0** | 37 | 85 |
| 0,005 | 47.323 | 44 | 7.495 | 5.270 |
| 0,01 | 67.672 | 315 | 24.945 | 13.477 |

Ở τ=0,001, 19.927/13.589 constraint cấm ENDS-ON và BEGINS-ON — hai nhãn chiếm 0,09% corpus mà
sampler gold-marginal **không bao giờ** bơm. Constraint canh một cửa lỗi không đi qua. Nới τ
khiến chúng chạm tới nhãn thực sự bị bơm; recall nhảy 1,67% → 31,67%.

### 9.4. Bắt buộc báo cột lift

Bơm 60 lỗi vào 82.064 cặp đặt prior ngẫu nhiên ở **0,073%**. Ở mật độ đó không detector nào
đạt precision tuyệt đối cao. 1,84% đọc như thất bại nhưng là **25× ngẫu nhiên**; baseline
0,78% chỉ là 10,7×. **Trích precision trần mà bỏ prior là xuyên tạc cả hai phía.**

Nhưng vẫn phải nói thẳng: recall 31,67% **thấp hơn nhiều** so với 91,67% của baseline. Claim
đúng là **độ chọn lọc**, không phải độ phủ — baseline gắn cờ 7.015 cặp để bắt 55 lỗi, C3-A gắn
cờ 1.034 cặp để bắt 19.

### 9.5. C3-B

| Detector | P | R_all | tp | fp | residual |
|---|---:|---:|---:|---:|---:|
| closure 1-step | **100,00%** | 1,79% | 1 | 0 | 55 = **98,2%** |

Precision tuyệt đối, độ phủ gần bằng không — khi closure dám quyết thì nó đúng, nó chỉ hiếm khi
dám. Nhất quán với baseline 4,9% ở mục 8.2 (khác do cỡ mẫu 56 vs 948).


### 9.6b. 68 rule minimal làm detector — kết quả âm

| Detector | P | R | gắn cờ | lift |
|---|---:|---:|---:|---:|
| constraint τ=0,005 | 1,84% | 31,67% | 1.034 | 25,1× |
| 68 rule minimal (cờ khi `rel ≠ rule.rel`) | 0,08% | 6,67% | 5.142 | **1,1×** |

**Lỗi cấu trúc, không phải tinh chỉnh.** Cả 68 rule đoán CONTAINS, nên "rule bất đồng" rút gọn
thành `rel ≠ CONTAINS` — đúng với **93,13%** cạnh. Detector thừa hưởng base rate.

**Giới hạn ý nghĩa của 93,40%:** đó là precision trên cặp rule *có bắn* và *đoán CONTAINS*.
Không chuyển sang chiều bất đồng, vì biết một cạnh không phải CONTAINS không nói gì về nhãn
đúng của nó. **Predictor dương trên lớp áp đảo không lật được thành detector âm** — constraint
làm được vì nó nêu nhãn *bị cấm*, không nêu nhãn *kỳ vọng*.

### 9.7. Còn lại

| Việc | Vì sao | Trạng thái |
|---|---|---|
| Bộ đề xuất cạnh thiếu bằng rule | 98,2% residual chưa ai chạm | chưa có |
| Sweep nhiều seed | 60 lỗi là mẫu nhỏ, cần khoảng tin cậy | chưa chạy |
