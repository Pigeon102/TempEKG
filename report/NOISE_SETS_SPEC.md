# Đặc tả hai bộ đồ thị nhiễu dùng ở Bài 2

Bài 2 được đo trên ba loại đồ thị cần sửa: đầu ra của Bài 1, **đồ thị bơm nhiễu**, và **fake_data**. Hai loại sau
đều lấy nhãn đúng (gold) của tập valid rồi cố ý đổi một phần nhãn, nhưng là **hai bộ khác nhau**. Bảng dưới là
đặc tả của từng bộ.

| | Đồ thị bơm nhiễu | fake_data |
|---|---|---|
| Ai tạo | sinh trong code của dự án, mỗi lần chạy (`joint_repair.py`, hàm `corrupt`) | file có sẵn do nhóm cung cấp: `C:\Reseach_Quang\fake_data\valid_rXX.jsonl` + `valid_rXX.manifest.json` |
| Nguồn nhãn đúng | MAVEN-ERE valid (KG của dự án) | `phase1/MAVEN_ERE/valid.jsonl` (ghi trong manifest) |
| Loại cạnh bị đổi | **cả 4 loại**: EV–EV, EV→TIMEX, TIMEX→EV, TIMEX–TIMEX (188.924 cạnh) | **chỉ EV–EV** (109.933 cạnh theo manifest); cạnh có TIMEX giữ nguyên |
| Mức nhiễu | 10%, 20% | 5%, 10%, 15%, 20% |
| Seed | valid: 37; tập chỉnh tham số (CONFIRMATION-2 của train): 51 | 0 |
| Cách đổi một cạnh | với xác suất ρ, thay nhãn đúng bằng một nhãn khác, chọn theo tỷ lệ của nhãn đó trong loại cạnh (phân phối biên trên gold train, bỏ nhãn đúng) | giống về bản chất: nhãn thay thế theo phân phối biên (suy ra từ manifest, ví dụ ở mức 10%: BEFORE đổi thành CONTAINS 84,6%, SIMULTANEOUS 10,0%, OVERLAP 5,1%) |
| Số cạnh bị đổi | khoảng 18.780 (10%) và 37.580 (20%); tỷ lệ cạnh sai thực tế 9,94% / 19,89% | 5.482 / 11.044 / 16.555 / 22.012 (4,99 / 10,05 / 15,06 / 20,02%) |
| Số bài bị chạm tới | gần như mọi bài | 597 / 667 / 674 / 688 trên 710 bài |
| Nhãn đúng của các cạnh bị đổi (mức 10%) | theo phân phối gold của từng loại cạnh | BEFORE 9.908 · CONTAINS 972 · SIMULTANEOUS 101 · OVERLAP 60 · BEGINS-ON 3 |
| Mô hình nhiễu dùng khi sửa | biết chính xác: giữ với xác suất 1 − ρ, đổi theo phân phối biên với xác suất ρ | như bên trái, chỉ cho cạnh EV–EV; cạnh TIMEX coi như quan sát đúng |
| Tham số λ, α chọn trên | CONFIRMATION-2 của train, bơm nhiễu cùng cách (seed 51) | CONFIRMATION-2 của train, đổi nhãn EV–EV cùng cách |
| Script và log | `experiments/higher_order/inj_eval.py`, `experiments/logs/inj_eval_subset.log` | `experiments/higher_order/fake_eval.py`, `experiments/logs/fake_eval_subset.log` |

**Ghi chú khi đọc số fake_data.** Trong file, một cặp có thể được lưu theo chiều ngược với chiều trong KG của dự
án. Khi nhãn bị đổi là nhãn không đối xứng (ví dụ CONTAINS), không đổi được chiều một cách an toàn, nên 23–106
cạnh như vậy được giữ nhãn đúng. Vì thế tỷ lệ lỗi ban đầu khi chấm (4,97 / 10,00 / 14,98 / 19,93%) thấp hơn
tỷ lệ trong file một chút.

**Chấm trên riêng các cạnh bị đổi.** Trước khi sửa, mọi cạnh bị đổi đều mang nhãn sai, nên accuracy và macro-F1
trên tập con này đều bằng 0. Sau khi sửa, báo: accuracy và macro-F1 trên tập con, số cạnh sửa đúng, số cạnh
đúng bị làm hỏng, giảm lỗi ròng = sửa đúng − làm hỏng.
