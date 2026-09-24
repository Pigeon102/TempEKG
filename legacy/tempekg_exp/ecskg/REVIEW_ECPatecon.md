# Đánh giá tài liệu `Event-Centric-PaTeCon` — đo bằng số thật

Tài liệu dùng **số giả định** cho ví dụ Pattern B và tự ghi rõ như vậy. Tính khả thi phụ thuộc
hoàn toàn vào số thật, nên đây là phần đo (`patternB_measure.py`).

---

# 1. Những chỗ tài liệu làm ĐÚNG

**Định nghĩa Event Graph sạch**: node = coreference chain (không phải mention lẻ), mang
`EventType` (168) + `TimeAnchor` + `Argument(x, ρ)` (612 role), cạnh dùng **đúng 9 nhãn thật**
của MAVEN-ERE. Không bịa nhãn.

**Giới hạn Pattern A về within-document là đúng** — MAVEN-ERE chỉ annotate coreference
trong cùng tài liệu. Việc tự sửa lại điểm này và yêu cầu nêu trong Limitations là chính xác.

**Bỏ audit trên gold MAVEN-ERE** vì gold gần như nhất quán theo thiết kế annotation —
kết luận này khớp với đo lường độc lập: MAVEN gold **đóng kín bắc cầu 100%**, và chỉ **12**
cạnh vi phạm hard constraint trên toàn bộ 1.1M cạnh ràng buộc.

**Phải trích AMIE cho PCA-confidence** — đúng, và reviewer rành rule-mining sẽ bắt ngay.

**Nhận diện rủi ro Chambers & Jurafsky** — đúng chỗ nguy hiểm nhất về novelty.

**Registry là ground-truth độc lập, không suy lại từ graph** — thiết kế thí nghiệm đúng.

**Baseline random-perturbation kiểu AnoT** — ý hay, cần thiết.

---

# 2.  Pattern B đo bằng số thật

## 2.1 Quy mô

414,582 cặp `(e1, e2)` chia sẻ argument (từ 50,322 event có argument, 162 kiểu):

|| số | tỉ lệ |
|---|---|---|
| có nhãn ERE | 107,112 | **25.8%** |
| **Pairs_unk** (bị PCA loại khỏi mẫu số) | **307,470** | **74.2%** |

## 2.2 Số rule mine được

| mức chữ ký | \|sig\|
| sup≥10 | sup≥50 | sup≥100 |

**conf≥0.9 & sup≥10** |
|---|---|---|---|---|---| | L0 `(T1,T2)` | 17,943 | 2,274 | 331 | 121 | 1,425 |
| **L1 `(T1,T2,ρ)`** | 17,635 | 1,612 | 232 | 83 |

**848** |
| L2 `(T1,T2,ρ1,ρ2)` | 58,857 | 2,728 | 347 | 118 | 1,365 | Rule mạnh nhất trông rất hợp lý về ngữ nghĩa: ``` conf 0.991  sup 108  Process_start | Process_end | Agent      => BEFORE conf 0.978  sup  91  Process_end | Military_operation | Location => BEFORE conf 0.961  sup 103  Arriving | Motion | Agent                 => BEFORE ``` ## 2.3  Nhưng phân bố nhãn phá kết quả | nhãn | số | tỉ lệ |
|---|---|---|
| **BEFORE** | 88,382 | **82.5%** |
| CONTAINS | 14,187 | 13.2% |
| SIMULTANEOUS | 2,436 | 2.3% |
| OVERLAP | 1,189 | 1.1% |
| PRECONDITION | 481 | 0.4% |
| CAUSE | 272 | 0.3% |
| BEGINS-ON / ENDS-ON | 165 | 0.1% |

**Tỉ lệ nền của nhãn đa số là 82.5%.** Nên:

$$\text{lift}\bigl(\text{conf}=0.9\bigr)=\frac{0.90}{0.825}=\mathbf{1.09\times}$$

Ví dụ giả định trong tài liệu (conf 0.968) cho lift **1.17×**.

## 2.4 Lọc lại 848 rule bằng ngưỡng nền

|| số |
|---|---| | rule conf ≥ 0.9, sup ≥ 10 | 848 |
| trong đó hệ quả **không** phải `BEFORE` |

**2** |
| conf ≥ 0.95 | 554 | | **Wilson lower bound > 0.825** (thật sự vượt nền) | **183** |
| vừa vượt nền **và** hệ quả không phải `BEFORE` |

**0** | > Pattern B, đo đúng cách, cho **183 rule vượt tỉ lệ nền — và cả 183 đều dự đoán `BEFORE`**.
> Nói cách khác nó học được "với 183 cặp loại sự kiện này, `BEFORE` đúng chắc hơn mức trung
> bình của corpus". Có giá trị, nhưng yếu hơn nhiều so với cách tài liệu trình bày.

## 2.5 Pattern B_role — ablation mà tài liệu đề xuất, đo luôn

Tài liệu đề nghị đo "bao nhiêu % luật confidence trung bình được đẩy lên ngưỡng cao nhờ role
refinement". Câu trả lời:

||
||---|---|
| chữ ký L0 có conf ∈ [0.5, 0.9) và sup ≥ 10 | 821 | | refine sang **L1** vượt 0.9 | **69 (8.4%)** |
| refine sang **L2** vượt 0.9 |

**131 (16.0%)** |

Yếu, nhưng là con số thật và báo cáo được.

---

# 3.  Ba vấn đề cấu trúc

## 3.1 Xung đột với phạm vi đã chốt

|| dùng gì | có ở text thô? |
|---|---|---|
| Pattern A | coreference chain **vàng** + TimeAnchor **vàng** | || Pattern B | nhãn quan hệ ERE **vàng** (cả đầu vào mining lẫn **hệ quả**) | |

Cả hai pattern **không chạy được** trên tài liệu chưa annotate. Nhưng phạm vi đã chốt là
*"mining và dựng graph không được dựa trên TIMEX và relation của ERE vì nó xem như GT để
đánh giá thôi"*. Tài liệu này đi ngược lại.

## 3.2 Pairs_unk 74.2% — nặng hơn PaTeCon 5 lần

PCA-confidence loại 74.2% dữ liệu khỏi mẫu số. Để so:

|| tỉ lệ bị loại |
|---|---| | lớp `unknown` của PaTeCon trên WD50K | **14.7%** |
| **Pairs_unk ở Pattern B** |

**74.2%** |

Và các cặp bị loại **không** ngẫu nhiên: chúng là những cặp annotator **không chọn để gán
quan hệ**. Cặp thật sự có liên hệ thời gian thì dễ được annotate hơn. Nên confidence được đo
trên mẫu **thiên lệch về phía các cặp có liên hệ** — làm conf cao lên theo cấu trúc.

Giả định PCA của AMIE là giả định **đầy đủ** ("biết một object thì biết hết"). Ở đây nó không
đúng: thiếu nhãn không có nghĩa là không có quan hệ.

## 3.3 Đây không phải temporal conflict

Không một giá trị TIMEX nào đi vào Pattern B. "Xung đột" ở đây = cặp có nhãn ERE khác nhãn đa
số của chữ ký = **nhiễu nhãn**, không phải mâu thuẫn giữa hai giá trị thời gian. Đề tài là
temporal conflict.

---

# 4.  Recall của Rule-Guided Noise Injection gần như tất định

Bước 2 chọn cặp **khớp antecedent và đang mang nhãn đúng theo rule**; bước 3 đổi nhãn
`BEFORE → AFTER/CONTAINS`. Chính rule đó sẽ gắn cờ chúng **theo cấu trúc**:

```
rule:  (T1,T2,ρ) => BEFORE  với conf 0.97
tiêm:  lấy cặp khớp (T1,T2,ρ), đổi BEFORE -> CONTAINS
đo  :  rule phát hiện cặp đó  <-- tất yếu, vì nhãn mới trái với hệ quả của rule
```

→ **Recall ≈ 100% do thiết kế**, không mang thông tin. Chỉ **precision / false-alarm** trên
các cặp *không* bị tiêm mới có ý nghĩa. Baseline "không tiêm nhiễu" ở §8.3 đúng là chỗ xử lý
việc này, nhưng phải nói rõ recall không được dùng làm kết quả chính, nếu không reviewer sẽ bắt.

---

# 5. Kết luận: khả thi ở phần nào

## Dùng được ngay

||
||---|---|
||

Định nghĩa Event Graph (node = coref chain, 9 nhãn thật) |
||

Trích AMIE cho PCA-confidence · differentiate Chambers & Jurafsky |
||

Registry độc lập + baseline random-perturbation kiểu AnoT |
||

Số ablation Pattern B_role: **8.4% (L1) / 16.0% (L2)** |

## Phải sửa

| # | vấn đề | cách sửa cụ thể |
|---|---|---|
| 1 |

**Hệ quả là nhãn ERE** → không phải temporal conflict, và vi phạm phạm vi | đổi hệ quả sang **vị từ trên khoảng thời gian** (`disjoint`/`before`/`include`) tính từ TIMEX **tự trích**, đúng như [`mine_patecon.py`](mine_patecon.py) đã làm — bản đó tái tạo PaTeCon **6/6 chính xác** trên Wikidata |
| 2 |

**lift chỉ 1.09×** | báo cáo **lift trên tỉ lệ nền**, không báo conf thô. Headline trung thực: **183 rule có Wilson LB > 0.825** |
| 3 |

**846/848 rule đều `=> BEFORE`** | nhắm vào nhãn thiểu số (`CONTAINS` 13.2%, `SIMULTANEOUS` 2.3%) — ở đó lift mới lớn; hoặc bỏ hẳn hệ quả nhãn (mục 1) |
| 4 |

**Pairs_unk 74.2%** | nêu thẳng trong Limitations; báo cáo cả hai cách tính (loại và không loại `unk`), như đã làm với lớp `unknown` 14.7% của PaTeCon |
| 5 |

**recall injection tất định** | nêu rõ recall không phải kết quả chính; chuyển sang tiêm nhiễu vào **giá trị thời gian** (làm giao rỗng) thay vì vào nhãn — chính §8.5 của tài liệu đã gợi ý cho Pattern A |
| 6 |

**Pattern A cần coref + TIMEX vàng** | giữ Pattern A nhưng chạy trên TIMEX **tự trích** (bộ dò hiện có: P 61.0% / R 60.3%), gold TIMEX làm đánh giá |

## Nhận định

Hướng **khả thi về mặt kỹ thuật** — mine được 848 rule, có rule đẹp về ngữ nghĩa. Nhưng ở dạng
hiện tại nó là **bài toán khác**: phát hiện nhiễu nhãn quan hệ thời gian, dựa hoàn toàn vào
annotation vàng, với lift 1.09× trên tỉ lệ nền.

Muốn thành temporal conflict và khớp phạm vi đã chốt thì mục **1** là bắt buộc: đổi hệ quả từ
*nhãn ERE* sang *vị từ khoảng thời gian*. Khi đó Pattern B trở thành đúng SP3
(`Single_Entity_Temporal_Order`) của PaTeCon, mà `mine_patecon.py` đã cài và đã kiểm chứng.

## File

`patternB_measure.py` — đo Pattern B ba mức chữ ký + ablation B_role
