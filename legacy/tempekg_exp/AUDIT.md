# AUDIT — soi lại toàn bộ, tìm lỗi cùng loại vụ ngày âm

Mục đích: không lặp lại sai lầm. Rà từng kết quả đã báo cáo, hỏi **"con số này có thể là
artifact không?"**

---

# 1. BỐN LỖI ĐÃ MẮC (đã sửa)

## L1 — Đo lift bằng nhãn loại trừ lẫn nhau

**Triệu chứng:** `COARSE` có lift **0.0×** với WRONG → kết luận nhầm "T5 vô dụng".

**Nguyên nhân:** nhãn `COARSE`/`DELETED`/`REFINED` **loại trừ lẫn nhau theo định nghĩa**
(một fact chỉ mang một nhãn), nên giao **tất yếu** bằng 0.

**Sửa:** dùng **đặc trưng thô** trong giá trị (`o[4:]=='0101'`) thay vì nhãn → lift **12.4×**.

**Suýt mất:** cả hướng T5.

## L2 — Lift cao nhưng precision triển khai thấp

**Triệu chứng:** `0101` lift 12.4× trên tập đơn-giá-trị → thêm vào hệ thống.

**Thực tế:** khi triển khai trên **toàn bộ** EVAL nó phủ 2,483 fact ở precision **5.03%**
→ F1 tụt từ 0.232 xuống **0.156**.

**Sửa:** loại khỏi cấu hình cuối. **Lift trên tập con ≠ precision khi triển khai.**

## L3 — Vứt bỏ thay vì xếp hạng

**Triệu chứng:** lọc bỏ cặp REFINEMENT → F1 **0.060 < 0.066** của PaTeCon (nhãn chặt).

**Sửa:** xếp hạng, giữ tầng UNDECIDABLE → F1 0.210.

## L4 — ⚠️ NGÀY ÂM phá pipeline gán nhãn (nghiêm trọng nhất)

**Triệu chứng:** detector `entity-obj` đạt precision **24.67%**, đóng góp phần lớn recall.

**Truy vết:**
```python
def norm_time(t):
    return '%04d%02d%02d' % (int(t[1:5]), int(t[6:8]), int(t[9:11]))
#                                ^^^^ voi "-0068-10-01": dau tru lam lech het vi tri
```
→ Fact BC **không bao giờ khớp** → gán nhãn `DELETED` oan → "100% precision".

**Tách ra:**

| nhóm | số | P(sai) | lift |
|---|---|---|---|
| object là entity `Q...` | 355 | **2.82%** | **0.8×** (dưới nền!) |
| ngày ÂM | 103 | **100.00%** | 28.4× ← artifact |

**Tác động:** F1 báo cáo tụt từ **0.283 → 0.235**; mức vượt PaTeCon từ +53.5% → **+29.1%**.

---

# 2. RÀ CÁC KẾT QUẢ CÒN LẠI — có artifact nữa không?

| # | Kết quả đã báo | Rủi ro artifact | Kiểm chứng | Kết luận |
|---|---|---|---|---|
| 1 | Dataset khớp Table 3 (**17,176 entity**) | thấp | khớp con số công bố | ✅ tin được |
| 2 | 12 vs 13 constraint, lệch do $80/89$ | thấp | quét ngưỡng, tất định 3 lần | ✅ tin được |
| 3 | **57.3%** giá trị kết thúc `0101` | **trung bình** — có thể ngày 1/1 thật? | so kỳ vọng 0.27% → **209×**; ngày phổ biến kế tiếp `0303` đúng mức nền | ✅ tin được |
| 4 | **25.5%** conflict thuộc mẫu thô-vs-mịn | thấp | khớp mẫu trực tiếp | ✅ tin được |
| 5 | 18% mẫu `0101` là precision=NĂM | **trung bình** — chỉ 45/60 truy vấn thành công | mẫu nhỏ, 25% lỗi API | ⚠️ **cần mẫu lớn hơn** |
| 6 | Gold MAVEN 100% đóng kín bắc cầu | thấp | 2 đường đo độc lập cùng ra 72 | ✅ tin được |
| 7 | Mining thống kê precision **0.00%** | **cao** — 0% cũng đáng ngờ như 100% | giao **tuyệt đối** bằng 0 giữa 4,874 và 14 | ⚠️ **xem §3** |
| 8 | `m00d00` P **25.17%**, lift 16.7× | **trung bình** | 143 fact, không dính lỗi dấu trừ | ⚠️ **cần kiểm** |
| 9 | T4 chồng nhau **88.1%** | thấp | đo trực tiếp trên interval | ✅ tin được |
| 10 | Mức C: 612 chu trình → 5, ΔF1 ≈ 0 | thấp | đo trực tiếp | ✅ tin được |
| 11 | Latency nhanh **4.6×** | **trung bình** — so không cùng phạm vi | PaTeCon mine constraint, ta không | ⚠️ **xem §4** |
| 12 | Sự kiện lặp lại 96.8% hợp lệ | **trung bình** — không có nhãn vàng | dựa vào heuristic cấu trúc | ⚠️ **chưa kiểm chứng được** |

---

# 2b. ✅ ĐÃ GIẢI QUYẾT — kết quả kiểm chứng

## #7 — precision 0.00%: **KHÔNG phải artifact** ✅

Đo chồng lấn hai tập **cặp** (không phải tập conflict):

```
cap S5 co the xet   : 593,433
cap nguon CUNG xet  : 493,209
CHONG LAN           : 489,071 = 82.4% cua S5
```

**82.4% chồng lấn** → hai detector cùng xét phần lớn cùng một tập cặp, nhưng gắn cờ hoàn
toàn khác nhau. Kết luận *"mining thống kê không phát hiện lỗi thật"* **đứng vững**.

## #11 — latency 4.6×: **THIÊN VỊ, đã sửa** ⚠️

| phạm vi | PaTeCon | TempEKG | tỉ lệ |
|---|---|---|---|
| đầu-cuối (PaTeCon **mine** constraint, ta dùng luật có sẵn) | 2.002 s | 0.437 s | 4.6× — **không công bằng** |
| **chỉ giai đoạn phát hiện** | **0.819 s** | **0.415 s** | **~2.0×** ✅ |

**Phải báo cáo con số 2.0× kèm phạm vi**, không dùng 4.6×.

---

# 3. ⚠️ Kiểm lại #7 (đã giải quyết ở §2b)

**Lý do nghi:** 0% tuyệt đối giữa 4,874 và 14 mục — cũng bất thường như 100%.

**Kiểm chứng đã làm:** con số 14 conflict cứng trên EVAL khớp với 72 toàn corpus × 20% ≈ 14 ✅
→ tử số đúng.

**Nhưng:** hai detector hoạt động trên **hai loại quan hệ khác nhau**:
- S5 (mine) gắn cờ cặp có quan hệ thời gian **lệch với đa số kiểu event**
- S2/S3/S4 gắn cờ cặp vi phạm **ngữ nghĩa subevent/causal**

Nếu hai tập cặp **gần như không giao nhau ngay từ đầu** (trước cả khi xét đúng/sai) thì
giao bằng 0 là **tất yếu**, không phải phát hiện.

> 🔴 **CHƯA KIỂM: tỉ lệ chồng lấn của hai tập CẶP (không phải tập conflict).**
> Nếu chồng lấn ~0 thì kết luận "mining không phát hiện lỗi thật" là **artifact của thiết
> kế đo**, giống hệt lỗi L1.

**Việc cần làm:** đo `|cặp S5 xét ∩ cặp S2/S3/S4 xét| / |cặp S5 xét|`.

---

# 4. ⚠️ Kiểm lại #11: latency 4.6× có công bằng?

**Không hoàn toàn.** So sánh hiện tại:

| | làm gì |
|---|---|
| PaTeCon 2.002s | **mine constraint từ đầu** + phát hiện conflict |
| TempEKG 0.437s | dùng constraint **có sẵn** + phát hiện |

TempEKG **không mine** — nó dùng 10 luật viết sẵn. Nên so "đầu-cuối" là **thiên vị**.

**So công bằng hơn:** chỉ so giai đoạn *phát hiện*:
- PaTeCon `Conflict_Detection.py`: **0.819s**
- TempEKG (bỏ bước đọc dữ liệu): **0.415s**
- → nhanh hơn **~2.0×**, không phải 4.6×

> **Phải báo cáo cả hai con số và nói rõ phạm vi.**

---

# 5. QUY TẮC RÚT RA — checklist trước khi tin một con số

1. **P = 0% hoặc 100%** trên ≥50 mẫu → **luôn** truy đến pipeline gán nhãn
2. **Lift cao trên tập con** → phải đo lại precision **khi triển khai trên toàn tập**
3. **Nhãn loại trừ lẫn nhau** → không dùng để đo tương quan giữa các nhãn
4. **Giao bằng 0** → kiểm tra hai tập có **chồng lấn về miền** không, trước khi kết luận
5. **So sánh tốc độ** → phải cùng **phạm vi công việc**
6. **Ký tự đặc biệt** (dấu trừ, unicode, `00`) → kiểm parser với chính các giá trị đó
7. **Kết quả đẹp bất ngờ** → giả định là bug cho đến khi chứng minh ngược lại

---

# 6. MỨC ĐỘ TRUNG THỰC HIỆN TẠI

| | trạng thái |
|---|---|
| Đã tự phát hiện và sửa 4 lỗi | ✅ ghi lại đầy đủ, không giấu |
| Đã đính chính con số đã công bố (0.283 → 0.235) | ✅ ghi rõ trong `DESIGN_FINAL.md` |
| Còn 2 kết quả **chưa kiểm chứng đủ** (#7, #11) | ⚠️ đã nêu ở §3, §4 |
| Còn 2 kết quả dựa trên heuristic không có nhãn vàng (#8, #12) | ⚠️ đã đánh dấu |
| Mọi kết quả chỉ trên **một** dataset | ⚠️ đang chạy kiểm chứng WD27M |

**Đánh giá:** trung thực về những gì đã phát hiện, nhưng **chưa kiểm chứng đủ** ở 4 chỗ.
Phải xong §3 và §4 trước khi đưa con số vào bài.


---

# L5 — `r[2]` thay vì `r[3]`: thống kê in ra 100% dương (exp37)

`exp37_anchor_model.py` in *"cap duong: 248074 (100.0%)"*. Nguyên nhân: hàng là tuple
4 phần tử `(eid, tid, features_dict, label)`, code đếm `if r[2]` — tức **dict đặc trưng**,
luôn truthy. Tỉ lệ dương thật là **15.5%**.

**Ảnh hưởng:** chỉ dòng in; huấn luyện và đánh giá dùng đúng `x[3]`. Không có kết quả nào
phải rút lại.

**Bắt được nhờ** quy tắc #1 (*số đẹp bất ngờ → giả định là bug*) — 100% dương là bất khả thi.

**Quy tắc bổ sung:**

> **9. Truy cập tuple theo chỉ số thì phải đặt tên biến, hoặc dùng namedtuple/dataclass.**
> `r[2]` không nói lên điều gì; `row.label` thì không sai được.

---

# L6 — Cứu detection bằng xếp hạng confidence: lift < 1 (exp41)

Áp bài học L3 (*xếp hạng thay vì lọc*) cho T5 ERE-free: chấm điểm
`p1 * p2 * 1[giao rỗng]` rồi xếp hạng. Kết quả **top-25 lift 0.57×** — tệ hơn ngẫu nhiên.

**Vì sao:** model tự tin cao ⇒ anchor **đúng** ⇒ anchor đúng thì hiếm khi xung đột
(gold chỉ 16.1%). Điểm số bị **đảo chiều** so với giả định.

**Bài học:** L3 (*xếp hạng thay vì lọc*) **không phải quy tắc phổ quát**. Nó chỉ đúng khi
điểm số **tương quan thuận** với nhãn. Phải kiểm tra chiều tương quan trước, đừng áp máy móc.

> **10. Trước khi xếp hạng theo một điểm số, kiểm tra lift ở top-k. Lift < 1 nghĩa là
> điểm số đảo chiều — đừng dùng, và cũng đừng đảo ngược nó mà không có lý do cơ chế.**


---

# L7 — Đặc trưng dẫn xuất từ nhãn: `n_anchor` rồi `hull` (hai lần trong một mạch việc)

Khi khám phá pattern bottom-up trên dàn view, hai lần liên tiếp bắt được cùng một lớp lỗi:

**Lần 1 — `n_anchor`.** Quét ra toàn pattern `n_anchor=4 & …` với lift 5.5×, conflict 100%.
`n_anchor` bị cap ở 4 nên `=4` nghĩa là "≥4 anchor"; càng nhiều anchor thì giao càng dễ rỗng:
8.7% (k=2) → 21.6% → 34.0% → 52.2% → 84.5% (k≥6). Tautology số học.
**Sửa:** phân tầng theo số anchor, mine trong từng tầng.

**Lần 2 — `hull`.** Sau khi phân tầng vẫn ra `ALL(gran=day) & hull≥30` lift 11.16×,
conflict 100%. Chứng minh: ở k=2, conflict ⟺ max(aᵢ) > min(bᵢ) và hull = max(bᵢ) − min(aᵢ);
nếu cả hai anchor hạt độ ngày thì aᵢ=bᵢ nên hull = |d₁−d₂| và **hull > 0 ⟺ conflict**.
**Sửa:** bỏ `hull` khỏi tập điều kiện.

**Điểm chung:** cả hai đều là **hàm của chính các đầu mút khoảng dùng để định nghĩa nhãn**.
Không phải thuộc tính độc lập của đối tượng.

> **11. Trước khi đưa một đặc trưng vào miner, hỏi: nó có tính được TỪ nhãn hoặc từ
> chính các đại lượng dùng để định nghĩa nhãn không? Nếu có thì nó rò rỉ.**
> Kiểm tra bằng đại số, không bằng trực giác — `hull` trông như một thuộc tính vật lý
> vô hại cho đến khi viết ra công thức.

Sau khi sửa cả hai, lift thật là **6.32×** (k=2) và **3.12×** (k=3), không phải 11×.
