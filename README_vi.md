# TempEKG

Code, log và tài liệu cho bài *Event-Centric Temporal Graph Repair for Temporal Relation Prediction*
(MAVEN-ERE + MAVEN-Arg). Repo này chỉ giữ những gì sinh ra số trong paper.

- **Số liệu chuẩn:** repo [`tempekg-numbers`](../tempekg-numbers). Repo đó chứa bảng LaTeX đã chốt, mọi con số
  trong văn bản kèm log nguồn, và script kiểm bản draft. Khi trích số vào paper, lấy từ đó.
- **Code và tài liệu cũ** (C2/C3, 257 luật, motif, các bản auditor trước…) không còn trong cây hiện tại. Lấy lại
  bằng `git checkout pre-cleanup`.

## Kết quả (valid: 710 document, 188.924 cạnh)

| | Kết quả | Log | Bảng |
|---|---|---|---|
| Task 1, macro-F1 gộp | 30,09% → **30,84%** với luật liên tầng | `experiments/logs/layered_rules_full.log` | Table 2 |
| Task 2 trên đầu ra Task 1 | macro-F1 30,84% → **31,89%**, lỗi 15,31% → **12,53%** | `experiments/logs/bai2_combo_full_subset.log` | Table 4 |
| Task 2, nhiễu EV–EV 5 / 10 / 15 / 20% | lỗi → 0,96 / 2,28 / 2,56 / 3,36% | `experiments/logs/fake_eval_subset.log` | Table 3 |
| Task 2, nhiễu mọi loại cạnh 10 / 20% | lỗi 9,94 → **1,91%**, 19,89 → **4,37%** | `experiments/logs/inj_eval_subset.log` | Table 3 |
| Ablation | xem appendix của paper | `logs/ablate_tri*.log`, `logs/ablate_audit.log`, `rules_full/ablate_score.log`, `rules_full/abl_*.log` | Table 6–8 |

Đã kiểm tra ngày 18/10/2026:
- Table 2 tính lại trực tiếp từ `pred_layered_full.json`: khớp mọi ô.
- Table 4 tính lại từ dự đoán từng cạnh (`bai2_rows_full.pkl`): khớp mọi ô, và đồ thị đầu vào trùng 100% với
  dự đoán cuối của Task 1.

## Pipeline

```
MAVEN-ERE + MAVEN-Arg
  └─ src/build_kg.py ──► src/graph/{train,valid}.jsonl
       ├─ experiments/rules_full/mine_full.py ──► rules_confirmed.pkl, src/artifacts/rules_full.json      (EV–EV 26,99%)
       │    └─ experiments/rules_full/export_full.py ──► pred_all_edges_full.json  (ghi đè mọi dự đoán EV–EV)
       ├─ experiments/higher_order/bai1_all_edges.py ──► pred_all_edges.json        (ba loại cạnh TIMEX)
       │
       └─ experiments/higher_order/layered_rules.py  [TAG=_full] ──► pred_layered_full.json   = KẾT QUẢ TASK 1 (30,84%)
            ├─ bai2_combo.py  [MACRO_ONLY=1] ──► Table 4      (dùng bai2_layered.py = auditor 3.1, joint_repair.py = tam giác 3.2)
            ├─ inj_eval.py, fake_eval.py ──► Table 3
            └─ ablate_tri.py, ablate_audit.py ──► Table 7, 8
```

## Tái tạo

Mọi lệnh chạy trong `tempekg/src`, với `export PYTHONIOENCODING=utf-8`. Thời gian đo trên máy 16 nhân, 15,7 GB.

| # | Lệnh | Ra | Thời gian |
|---|---|---|---|
| 0 | `python build_kg.py --split train --ere-dir ../../MAVEN_ERE --arg-zip ../../MAVEN-Arg.zip` (rồi `--split valid`), `python verify_kg.py --split valid` | `src/graph/` | ~12 s |
| 1 | `NW=4 python ../experiments/rules_full/mine_full.py` | luật EV–EV, `rules_full/mine_full.log` | ~6 phút |
| 2 | `python ../experiments/higher_order/bai1_all_edges.py` | `pred_all_edges.json`, `logs/bai1_all_edges.log` | ~1 phút |
| 3 | `NW=4 python ../experiments/rules_full/export_full.py` | `pred_all_edges_full.json` | ~3,5 phút |
| 4 | `TAG=_full DUMP=1 python ../experiments/higher_order/layered_rules.py` | `pred_layered_full.json`, `logs/layered_rules_full.log` (**Table 2**) | ~8 phút |
| 5 | `TAG=_full MACRO_ONLY=1 python ../experiments/higher_order/bai2_combo.py` | `logs/bai2_combo_full_subset.log` (**Table 4**) | ~26 phút |
| 6 | `TAG=_full python ../experiments/higher_order/inj_eval.py` | `logs/inj_eval_subset.log` (**Table 3**, mọi loại cạnh) | ~25 phút |
| 7 | `TAG=_full python ../experiments/higher_order/fake_eval.py` | `logs/fake_eval_subset.log` (**Table 3**, EV–EV; cần `C:\Reseach_Quang\fake_data`) | ~32 phút |
| 8 | `bash ../experiments/rules_full/run_ablations_b1.sh` | `rules_full/ablate_score.log`, `rules_full/abl_*.log` (**Table 6**) | vài giờ |
| 9 | `bash ../experiments/run_ablations_rest.sh` | `logs/ablate_tri.log`, `logs/ablate_audit.log` (**Table 7, 8**) | ~2 giờ |
| 10 | `python ../experiments/rules_full/compress.py`; `compress_timex.py`; `TAG=_full python ../experiments/rules_full/compress_layered.py` (cần bước 4 chạy với `DUMP=1`); `compact_listing.py` | 378 / 713 luật, `report/RULES_COMPACT.md` | ~5 phút |
| 11 | `TAG=_full python ../experiments/higher_order/nic_example.py`; `python ../experiments/rules_full/appendix_atoms.py` | ví dụ Nicaragua; bảng điều kiện nguyên tử | |

Đầu vào phụ của bước 2: `src/artifacts/pred_lex_d05.json`, do `experiments/higher_order/semantic_export.py` sinh từ
bộ 257 luật cũ (`rules/final/rules_rx_c70.json`). Dự đoán EV–EV trong file này bị bước 3 ghi đè toàn bộ, nên không
ảnh hưởng số cuối; file chỉ cần tồn tại để bước 2 chạy.

### Lưu ý về tái lập

- **Kết quả tất định.** Một số bước duyệt `set`, nên thứ tự phụ thuộc hash seed của Python. Mọi script entry có
  guard ở đầu file: nếu `PYTHONHASHSEED` khác `0`, script tự chạy lại chính nó với `PYTHONHASHSEED=0`.
  - Đã kiểm ngày 18/10/2026: chạy hai lần liên tiếp cho kết quả trùng từng byte.
  - Seed 0 tái tạo **chính xác** file dự đoán của paper: 0 trên 981.319 dự đoán Task 1 khác nhau, 0 cạnh khác ở
    cả ba cấu hình Bài 2.
  - Trước khi có guard, các lần chạy lệch nhau ±0,1 điểm (ví dụ EV→TX 30,51 / 30,61).
- **Con số 713 luật** = 378 (EV–EV) + 154 (ba loại cạnh TIMEX) + 181 (luật liên tầng). Bộ rút gọn và file dự đoán
  giờ đến từ cùng một lần chạy (`logs/layered_rules_full.log` với `DUMP=1`).
- **Ablation** (`logs/ablate_tri*.log`, `logs/ablate_audit.log`, `rules_full/abl_*.log`) chạy trước khi có guard.
  Chạy lại dưới seed 0 có thể lệch 1–2 cạnh ở mô hình tam giác.
- **Số đo trên classifier cũ.** Hai số 74,6% (cạnh sai nằm trong cấu hình tam giác chưa gặp) và 32,9% / 10,1% (cạnh
  kề cũng sai) đo bằng `subgraph_probe.py` và `diag_b.py` trên một phiên bản classifier trước. Script và log của
  chúng nằm ở tag `pre-cleanup`. Paper phải ghi "an earlier version of the classifier".
- **Dao động khi chia lại train:** `experiments/seeds/logs/` (seed 1) cho Task 1 30,42% (so với 30,84%) và EV–EV
  26,51% (so với 26,99%). Lần sweep chỉ chạy xong seed 1; phần Bài 2 của nó lỗi.

## Dữ liệu (ngoài git)

| Đường dẫn | Nội dung | Sinh bởi |
|---|---|---|
| `C:\Reseach_Quang\MAVEN_ERE`, `C:\Reseach_Quang\MAVEN-Arg.zip` | dữ liệu gốc | tải về |
| `src/graph/` | đồ thị đã dựng (834 MB) | bước 0 |
| `src/artifacts/` | luật và dự đoán; symlink tới `C:\Reseach_Quang\tempekg_kg\artifacts` | bước 1–4 |
| `experiments/rules_full/cache_*.pkl` | bitset điều kiện | bước 1 (tự dựng nếu chưa có) |
| `C:\Reseach_Quang\fake_data` | file nhiễu EV–EV do nhóm cung cấp | — |

## Cấu trúc

```
src/                      dựng KG (build_kg, verify_kg) và thư viện điều kiện/luật (mine_compositional, mine_mdd, mine_views, vote)
experiments/rules_full/   luật EV–EV trên toàn train, ablation Bài 1, rút gọn có chứng minh
experiments/higher_order/ Task 1 TIMEX + liên tầng, Task 2 (auditor, tam giác), nhiễu bơm, ablation Bài 2
experiments/begins_ends/  phân tích BEGINS-ON / ENDS-ON theo định nghĩa RED
experiments/seeds/        sweep seed (dao động khi chia lại train)
experiments/logs/         log của mọi số trong paper
rules/final/              bộ 257 luật cũ (chỉ để sinh pred_lex_d05.json)
report/                   tài liệu (bắt đầu từ TEMPEKG_TONG_QUAN.md)
```

## Tài liệu

| Muốn hiểu | Đọc |
|---|---|
| Toàn cảnh | `report/TEMPEKG_TONG_QUAN.md` |
| Kiến trúc, chia tập, chống rò rỉ | `report/TEMPEKG_KIEN_TRUC.md` |
| Task 1 / Task 2 chi tiết | `report/TEMPEKG_BAI1.md`, `report/TEMPEKG_BAI2.md` |
| Ablation, từng ô đối chiếu log | `report/ABLATION_TONG_HOP.md` |
| Định nghĩa toán | `report/TEMPEKG_TOAN_HOC.md` |
| Luật thật, 378 luật gọn | `report/RULESET.md`, `report/RULES_COMPACT.md` |
| Đặc tả nhiễu, điều kiện nguyên tử | `report/NOISE_SETS_SPEC.md`, `report/APPENDIX_DIEU_KIEN_NGUYEN_TU.md` |
| Dàn ý phần thực nghiệm | `report/EXPERIMENTS_DAN_Y.md` |

Tên tham số trong code khác trong paper:

| Code | Paper |
|---|---|
| `beta` | λ (làm trơn PMI) |
| `lambda` | β (trọng số tam giác) |
| `alpha` | γ (giảm prior) |

Các phần mô tả "classifier cũ" hoặc "bộ cũ" trong tài liệu là lịch sử, chỉ để so sánh.
