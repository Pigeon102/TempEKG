Mình đã đối chiếu brief mới của bạn với **KG hiện tại + các kết quả đã chạy trong project + PaTeCon + MAVEN-ERE + MAVEN-Arg**. Kết luận quan trọng là:

> **KG hiện tại về cơ bản đúng hướng cho contribution bạn muốn, nhưng contribution C2 hiện tại đang bị đặt sai trọng tâm.**
> Nếu giữ đúng mục tiêu ban đầu của bạn, mình sẽ chuyển thesis/pipeline từ **“rule → predictor”** sang **“rule → relation inference + KG auditing”**, trong đó prediction chỉ là một evaluation protocol để chứng minh rule có khả năng khái quát.

Và mình nghĩ hướng này **mạnh hơn** so với cố ép C2 thành một temporal-relation classifier.

---

# 1. Trước hết: mình hiểu contribution của bạn như thế này

Bạn không đơn thuần muốn làm một temporal relation classifier.

Bạn muốn có một pipeline:

```text
Documents
   │
   ├── MAVEN-ERE
   │      ├── events
   │      ├── temporal relations
   │      ├── causal
   │      └── subevent
   │
   └── MAVEN-Arg
          ├── entities
          └── event arguments
                │
                ▼
       Event-centric KG
                │
                ▼
       ┌─────────────────────┐
       │ Rule / Pattern Miner │
       │      TRAIN ONLY      │
       └──────────┬──────────┘
                  │
             Rule set R
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
 Relation inference       KG auditing
        │                    │
        ▼                    ▼
 hidden VALID relation    suspicious relation
        │                    │
        ▼                    ├── existing label
 evaluate against gold     │      → possible wrong
                             │
                             └── no label
                                    → possible missing
```

Đây là một ý tưởng **hợp lý hơn rất nhiều** so với việc nói:

> “Tôi mine motif rồi dùng motif để classify temporal relations.”

Vì PaTeCon đã làm phần **pattern-based temporal constraint mining + conflict detection** trên temporal KG. PaTeCon tự mô tả mục tiêu là tự động sinh temporal constraints từ graph patterns/statistics thay vì constraint thủ công. ([AAAI Publications][1])

Cái bạn đang cố làm có thể khác ở chỗ:

> **event-centric textual KG + argument structure + temporal relation induction + bidirectional auditing of annotation completeness/correctness.**

Đây mới là phần nên đào sâu.

---

# 2. KG hiện tại có phù hợp không?

## Có — và mình đánh giá architecture hiện tại khá đúng

KG hiện tại:

```text
Document
 ├── Event
 │    ├── type
 │    ├── trigger
 │    ├── sentence
 │    └── arguments
 │
 ├── Entity
 │
 ├── Span
 │
 └── TIMEX
```

và:

```text
event ──HAS_ARG(role)──> entity/span
event ──TEMPORAL───────> event/TIMEX
event ──CAUSAL─────────> event
event ──SUBEVENT───────> event
```

là **đúng abstraction level** cho research question.

MAVEN-ERE vốn đã cung cấp event clusters, TIMEX và 6 temporal relation types, cùng causal/subevent relations. ([GitHub][2])

MAVEN-Arg bổ sung đúng thứ mà KG temporal thông thường thiếu: **event arguments ở document level**, gồm cả entity và non-entity arguments. Dataset có schema rất rộng với 162 event types và 612 argument roles. ([GitHub][3])

Do đó:

```text
MAVEN-ERE
    temporal structure
         +
MAVEN-Arg
    semantic/event structure
         ↓
Event-centric KG
```

là một integration hợp lý.

Đặc biệt, số liệu hiện tại của bạn cho thấy:

* 67,984 event nodes train
* 55,421 entity nodes
* 71,485 span nodes
* 16,688 TIMEX
* 188,584 input edges
* 792,395 temporal target edges

và **59.6% argument filler không có `entity_id`**, nên quyết định giữ `span` node là rất quan trọng. 

Nếu bỏ span, bạn thực sự vứt mất một phần lớn structural information.

---

# 3. Nhưng có một điểm rất quan trọng: KG hiện tại chưa phải “KG để mine arbitrary graph motifs”

Hiện tại nó gần như:

```text
Event-centric property graph
        +
Allen constraint layer
        +
pair-level feature extraction
        +
rule miner
```

Điều này đủ cho C1/C2/C3 hiện tại.

Nhưng nếu contribution bạn muốn là:

> “tự KG train định nghĩa ra các tập rules trên toàn bộ KG, giống motif, rồi dùng rules để suy ra relation và audit toàn KG”

thì mình nghĩ cần nâng abstraction từ:

### Pair-rule

```text
Event A + Event B
      ↓
features
      ↓
relation
```

thành:

### Graph-rule

```text
Pattern P
   │
   ├── Event type
   ├── Argument role
   ├── Shared entity
   ├── Event-event relation
   ├── TIMEX structure
   ├── local topology
   └── Allen constraints
          ↓
      relation set
```

Tức là **motif không nên chỉ là một feature vector**.

Nó nên trở thành **một executable graph pattern**.

---

# 4. Đây chính là chỗ PaTeCon giúp bạn định vị contribution

PaTeCon đang làm kiểu:

```text
temporal KG
     ↓
graph pattern
     ↓
constraint
     ↓
conflict
```

Ví dụ README của PaTeCon biểu diễn constraint dạng:

```text
(a,P39,b,t1,t2)
∧
(a,P22,c,t3,t4)
∧
(c,P569,d,t5,t6)
→
before(t5,t6,t1,t2)
```

và sau đó dùng constraint để phát hiện fact pair vi phạm. ([GitHub][4])

Cái này rất gần C3 của bạn.

**Vì vậy tuyệt đối không nên claim:**

> “We propose automatic pattern-based temporal constraint mining.”

Câu này PaTeCon đã làm.

Thậm chí paper PaTeCon nói rõ họ tự động xác định graph patterns và statistical information để sinh temporal constraints. ([AAAI Publications][1])

---

# 5. Nhưng KG của bạn có một thứ PaTeCon không có

Đó là:

## Event semantics.

Bạn có:

```text
Event A
   │
   ├── type = Motion
   ├── trigger = landed
   ├── Agent
   ├── Location ───────┐
   └── Patient          │
                        │
Event B                 │
   │                    │
   ├── type = Process_end
   ├── Location ────────┘
   └── ...
```

Và motif:

```text
Motion
  └──Location──> X

Process_end
  └──Location──> X
```

có empirical association với:

```text
BEFORE
```

Trong dataset hiện tại:

```text
support = 25
BEFORE = 24
CONTAINS = 1
```

nên:

```text
P(BEFORE | motif) = 0.96
```

Đây là một **semantic event-argument pattern**, không phải chỉ temporal KG constraint.

Đây là phần mình nghĩ nên giữ làm core.

---

# 6. Và kết quả hiện tại đã chỉ ra một insight rất quan trọng

Bạn đã thử C2:

```text
rule → predicted relation
```

nhưng:

```text
BEFORE base rate ≈ 91%
```

nên classifier bị chết bởi imbalance.

Kết quả hiện tại:

| Method                   | Valid precision |
| ------------------------ | --------------: |
| All rules                |          10.68% |
| 956 generalized families |           8.76% |
| Always BEFORE            |      **89.94%** |

Oracle ceiling chỉ khoảng 12.45%. 

Đây **không phải failure của KG**.

Nó nói rằng:

> **MAVEN temporal relation distribution không phù hợp với mục tiêu “rule-based multiclass prediction” nếu evaluation được đặt trên toàn bộ candidate pairs.**

Và chính paper MAVEN-ERE cũng xác nhận label distribution rất lệch: trên toàn dataset, BEFORE là 1,042,709/1,216,217 temporal relations, trong khi BEGINS-ON và ENDS-ON cực hiếm. Tác giả giữ nguyên phân phối không cân bằng này. ([ACL Anthology][5])

Cho nên mình **không khuyên bạn tiếp tục đốt effort để cứu accuracy C2**.

---

# 7. C2 nên đổi thành gì?

Mình đề xuất:

## C2 = Rule induction + relation inference

chứ không phải:

> Rule-based temporal classifier.

Cụ thể:

### Training

```text
KG_train
   ↓
Graph Pattern Miner
   ↓
R = {r1, r2, ..., rn}
```

Mỗi rule:

```text
r_i = (pattern_i, relation-set_i, confidence_i, support_i)
```

Ví dụ:

```text
P1:
Event(type=Motion)
  --Location-->
Entity(x)

Event(type=Process_end)
  --Location-->
Entity(x)

→ BEFORE
```

Nhưng thay vì bắt buộc:

```text
P → BEFORE
```

nên lưu:

```text
P →
{
  BEFORE: 24,
  CONTAINS: 1
}
```

và:

```text
allowed(P) = {BEFORE}
```

nếu statistical threshold đủ mạnh.

Điều này hoàn toàn phù hợp với quyết định hiện tại của bạn rằng **pattern nên map tới allowed-set**, không phải một relation duy nhất. 

---

# 8. Khi sang valid/test

Thay vì:

```text
P → one label
```

làm:

```text
P(event_a,event_b)
       ↓
allowed relations
       ↓
candidate inference
```

Ví dụ:

```text
P1(a,b)
→ BEFORE
```

Nếu valid gold:

```text
a BEFORE b
```

thì:

```text
TRUE POSITIVE
```

Nếu:

```text
a CONTAINS b
```

thì:

```text
FALSE INFERENCE
```

Nếu:

```text
a,b = UNKNOWN
```

thì:

```text
PREDICTED MISSING RELATION
```

Nhưng lưu ý cực kỳ quan trọng:

**MAVEN-ERE không phải complete-link graph theo nghĩa mọi cặp đều được annotate như ground truth.**

Trong architecture hiện tại, bạn đã chốt:

```text
unlabeled = UNKNOWN
```

và chỉ transitive forcing mới được coi là thiếu. 

Do đó:

> `no gold edge` **không được tự động gọi là annotation missing**.

Đây là một điểm reviewer sẽ bắt rất mạnh.

---

# 9. Vì vậy C3 thực ra phải chia thành 2 loại audit

Đây là thay đổi mình nghĩ rất đáng làm.

## C3-A: False-positive audit

Pattern nói:

```text
P → R
```

nhưng KG chứa:

```text
P(a,b)
a --S--> b
```

và:

```text
S ≠ R
```

→ **suspected wrong annotation**

Ví dụ:

```text
P:
Motion(a)
Location(a,x)
Process_end(b)
Location(b,x)

rule:
P → BEFORE
```

nhưng KG:

```text
a CONTAINS b
```

→ flag.

---

# 10. C3-B: Missing-edge audit

Cái này thú vị hơn.

Nếu pattern nói:

```text
P(a,b) → BEFORE(a,b)
```

nhưng KG:

```text
a ----?---- b
```

không có temporal relation.

Thì:

```text
candidate missing edge:
(a,b,BEFORE)
```

Nhưng **chưa được gọi là annotation error**.

Nó phải đi qua:

```text
rule confidence
      ↓
support
      ↓
independent structural evidence
      ↓
Allen consistency
      ↓
possibly transitive closure
      ↓
human validation
```

rồi mới:

```text
suspected missing annotation
```

Đây là chỗ C3 có thể trở thành contribution đáng kể.

---

# 11. Thậm chí bạn có thể làm “bidirectional auditing”

Mình rất thích formulation này cho paper:

```text
                    TRAIN KG
                       │
                 Rule Mining
                       │
             ┌─────────┴─────────┐
             │                   │
       relation rules       constraints
             │                   │
             ▼                   ▼
      hidden-label          existing KG
        inference              audit
             │                   │
             ▼                   ▼
       VALIDATION           ┌─────┴─────┐
                           │           │
                         WRONG       MISSING
```

Tức rule có hai chiều sử dụng:

### Forward

```text
graph structure → relation
```

### Backward

```text
relation + graph structure
             ↓
       consistency check
```

Đây là conceptually sạch hơn rất nhiều.

---

# 12. KG hiện tại cần bổ sung gì để support C3?

Mình sẽ **không thay schema hiện tại**.

Chỉ thêm metadata / derived layer.

## Layer 1 — observed KG

Giữ nguyên:

```text
event
entity
span
timex

HAS_ARG
TEMPORAL
CAUSAL
SUBEVENT
```

## Layer 2 — inferred KG

Thêm:

```text
INFERRED_TEMPORAL
```

nhưng **tuyệt đối không merge vào observed TEMPORAL**.

Ví dụ:

```json
{
  "source": "E1",
  "target": "E2",
  "relation": "BEFORE",
  "provenance": {
    "rule_id": "R_017",
    "support": 284,
    "wilson_lb": 0.81,
    "source": "train"
  }
}
```

## Layer 3 — audit

```json
{
  "source": "E1",
  "target": "E2",
  "observed": "CONTAINS",
  "inferred": "BEFORE",
  "status": "CONFLICT",
  "rule_id": "R_017"
}
```

hoặc:

```json
{
  "source": "E1",
  "target": "E2",
  "observed": null,
  "inferred": "BEFORE",
  "status": "MISSING_CANDIDATE"
}
```

Đây sẽ làm KG trở thành **self-auditing event-centric KG**, thay vì chỉ là storage.

---

# 13. Allen constraint layer hiện tại lại càng phù hợp

Đây là một phần mình **không khuyên bỏ**.

Bạn hiện có:

```text
Event graph
     ↓
Allen interval representation
     ↓
13×13 composition
     ↓
PC-2
     ↓
consistency
```

Điều này cho phép bạn phân biệt:

### Case A

```text
rule predicts BEFORE(a,b)
KG says CONTAINS(a,b)
```

→ direct disagreement.

### Case B

```text
a BEFORE b
b BEFORE c
```

rule sinh:

```text
a ENDS-ON c
```

Allen constraint layer có thể kiểm tra xem toàn bộ assignment có khả thi hay không.

Đây là thứ pairwise rule miner đơn thuần không làm được.

Architecture hiện tại của bạn đã có lý do chính xác cho việc tách hai tầng này. 

---

# 14. Một thay đổi mình rất khuyên: rule không chỉ có `relation`

Hãy định nghĩa rule như:

```text
Rule =
    Pattern
  + Scope
  + AllowedRelations
  + ForbiddenRelations
  + Statistics
  + Provenance
```

Ví dụ:

```text
R17

Pattern:
  type_a = Motion
  HAS_ARG(a, Location, x)
  type_b = Process_end
  HAS_ARG(b, Location, x)

Scope:
  EV-EV
  same-document

Observed:
  n = 25

Distribution:
  BEFORE = 24
  CONTAINS = 1

Statistics:
  WilsonLB(BEFORE) = ...
  WilsonUB(non-BEFORE) = ...

Inference:
  allowed = {BEFORE}

Audit:
  forbidden = {CONTAINS, OVERLAP, ...}
```

Đây mới là **rule object** mà cả C2 và C3 dùng chung.

---

# 15. Điều này cũng giải quyết vấn đề “motif”

Bạn hỏi:

> “giống như chỗ motif ấy, có thể xem nó là 1 rule”

Mình đồng ý.

Nhưng mình sẽ định nghĩa:

```text
Motif
=
structural pattern

Rule
=
motif + statistical relation semantics
```

Ví dụ:

```text
Motif M17
────────────────────
Motion --Location--> X
Process_end --Location--> X
```

Sau mining:

```text
Rule R17
────────────────────
M17 → BEFORE
support = 25
P(BEFORE|M17)=.96
```

Sau holdout:

```text
R17
train support = 25
valid support = 17
valid precision = ...
```

Sau audit:

```text
R17
→ detect conflicting edges
→ propose missing edges
```

Đây là decomposition rất đẹp cho paper.

---

# 16. Một điểm cực kỳ quan trọng về “toàn bộ KG”

Bạn nói:

> “định nghĩa trên toàn bộ KG, toàn bộ doc trong train với các loại relation để ra một bộ rule.”

**Đúng.**

Nhưng đừng mine bằng cách flatten toàn bộ graph thành một giant graph.

KG hiện tại đã chứng minh tại sao:

```text
document = connected component
```

và không có cross-document edges. 

Nên đúng hơn là:

```text
KG_train
=
{G1, G2, ..., G2913}

Mine:

R = Mine(G1 ∪ G2 ∪ ... ∪ G2913)
```

chứ không phải:

```text
GiantGraph(G1,...,G2913)
```

Tức **statistics được aggregate toàn corpus**, nhưng **motif matching vẫn document-local**.

Đây là distinction rất quan trọng.

---

# 17. Còn các paper bạn đưa thì mình thấy vai trò như sau

## PaTeCon

Đây là baseline/related work **bắt buộc phải so trực tiếp**.

PaTeCon:

```text
temporal KG
→ pattern mining
→ temporal constraint
→ conflict detection
```

và đã có refined constraints theo type. ([GitHub][4])

Bạn:

```text
event-centric text KG
→ event/argument motifs
→ relation rules
→ inference
→ bidirectional annotation audit
```

**Khác biệt nằm ở input representation + semantic evidence + missing-edge audit**, không phải ở cụm “pattern-based temporal constraint mining”.

---

## MAVEN-ERE

Nó cung cấp:

```text
Event
TIMEX
Temporal
Causal
Subevent
Coreference
```

và dataset có 6 temporal labels. ([GitHub][2])

Nó là **source KG**, không phải competing rule miner.

---

## MAVEN-Arg

Nó cung cấp:

```text
Event
Entity
Argument role
Non-entity argument
```

với 612 roles và document-level argument annotation. ([GitHub][3])

Đây chính là semantic layer giúp contribution của bạn khác PaTeCon.

---

# 18. Một insight rất đáng chú ý từ chính dataset

MAVEN-ERE được annotation với phân phối temporal rất mất cân bằng. Paper ghi nhận rõ điều này và chủ động giữ nguyên phân phối. ([ACL Anthology][5])

Vì vậy:

```text
rule mining
```

và:

```text
relation classification
```

là **hai bài toán khác nhau**.

Rule có thể cực kỳ hữu ích dù classifier accuracy thấp.

Ví dụ:

```text
P(BEFORE | motif) = 0.96
```

vẫn có giá trị như một **constraint**:

```text
P → NOT {SIMULTANEOUS, OVERLAP, ...}
```

Trong khi nếu bạn bắt nó phải chọn một label trên toàn candidate space thì base-rate BEFORE sẽ phá evaluation.

Đây chính xác là lý do kết quả C3 hiện tại tốt hơn C2:

```text
C2:
rule → relation
        ↓
       8–10%

C3:
rule → forbidden relation
        ↓
0.035% violation
```



---

# 19. Vì vậy mình sẽ chỉnh contribution statement

Thay vì:

### C1

> Event-centric KG.

### C2

> Mine rules and predict temporal labels.

### C3

> Audit annotation.

Mình đề xuất:

### **C1 — Event-centric heterogeneous KG**

> Construct an event-centric heterogeneous KG integrating event semantics, arguments, entities, temporal expressions and inter-event relations, with explicit separation between observed evidence and target temporal relations.

### **C2 — Corpus-level semantic rule induction**

> Automatically mine reusable graph motifs from the training KG and induce relation constraints/statistical semantics from their occurrences, rather than manually specifying temporal rules.

### **C3 — Bidirectional KG auditing**

> Apply the induced rules in two directions: detect observed relations that violate learned constraints, and generate candidate missing relations when structural evidence strongly supports an unobserved relation.

### **C4 — Structural consistency validation**

> Use Allen interval constraints to distinguish genuine relation conflicts from locally plausible but globally inconsistent assignments.

Mình thực sự thích cách chia thành **C1–C4** này hơn 3 contribution cũ.

---

# 20. Nhưng có một “bẫy” rất lớn với Missing Relation

Bạn phải cực kỳ cẩn thận:

```text
no edge
≠
wrong annotation
```

MAVEN-ERE có temporal relations nhưng không thể mặc định rằng tất cả cặp không được annotate là “negative”.

Bạn đã chốt điều này trong `DEFINITIONS`:

> absent label = UNKNOWN; chỉ transitive forcing mới được gọi là missing. 

Vậy C3 nên có hierarchy:

```text
Rule evidence
      │
      ▼
Candidate missing
      │
      ├── Allen impossible? → reject
      │
      ├── weak evidence? → unknown
      │
      ├── strong structural evidence
      │
      ▼
Transitive / constraint forced
      │
      ▼
High-confidence missing candidate
      │
      ▼
Human verification
```

Đây là cách tránh claim quá mức.

---

# 21. Và đây là nơi injector bạn đang chuẩn bị rất quan trọng

Trong `STATUS`, bạn đã có:

```text
P8 Inject conflict tổng hợp
P9 Human validation
```

và `DEFINITIONS` đã chuyển evaluation sang:

> “Detector thu hồi được bao nhiêu lỗi đã tiêm?”

thay vì:

> “Gold có bao nhiêu lỗi?”



Mình nghĩ đây là **đường đúng**.

Bởi vì gold của MAVEN-ERE có vấn đề circularity:

```text
gold
 ↓
mine rules
 ↓
detect errors in gold
```

Nếu không có ground-truth error set, bạn không thể tính recall của error detector.

Injector giải quyết:

```text
clean KG
 ↓
inject known error
 ↓
detector
 ↓
did detector recover injected error?
```

Đây là experiment cực kỳ cần thiết cho contribution C3.

---

# 22. Research pipeline mình đề xuất cuối cùng

Nếu mình đóng architecture cho paper ngay bây giờ, mình sẽ dùng:

```text
                     MAVEN-ERE
                         │
                  temporal / event
                         │
                         ▼
MAVEN-Arg ─────────► Event-centric KG
                         │
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
       Graph Pattern Miner     Allen Constraint
              │                     │
              ▼                     │
       Rule / Motif Library         │
              │                     │
       ┌──────┴────────┐            │
       │               │            │
       ▼               ▼            ▼
 Relation inference   Constraint-based
       │               │             reasoning
       │               │              │
       └───────┬───────┘              │
               ▼                      │
        ┌──────────────┐              │
        │ KG Audit     │◄─────────────┘
        └──────┬───────┘
               │
       ┌───────┴────────┐
       ▼                ▼
   Wrong edge       Missing candidate
       │                │
       └───────┬────────┘
               ▼
        Human validation
```

---

# 23. Và evaluation sẽ thành 4 phần rất sạch

### E1 — Rule quality

Train → valid:

```text
support
Wilson LB
lift
coverage
rule diversity
```

Không cần cố biến thành multiclass accuracy.

---

### E2 — Relation inference

Trên subset mà rule thực sự có evidence:

```text
Precision
Recall
F1
```

hoặc tốt hơn:

```text
P@k
MRR
Hits@k
```

nhưng phải report **conditional on rule coverage**.

---

### E3 — Error detection

Inject:

```text
wrong temporal edge
```

→ đo:

```text
Precision
Recall
F1
```

với ground truth biết trước.

---

### E4 — Missing-edge detection

Inject:

```text
delete existing temporal edge
```

→ xem rule có recover được không.

Đây là một experiment rất đẹp:

```text
Gold KG
   │
   ├── DELETE edge → missing annotation simulation
   │
   └── CHANGE label → wrong annotation simulation
                 │
                 ▼
              detector
                 │
                 ▼
           Precision / Recall
```

Nó biến C3 từ một claim khó kiểm chứng thành một **controlled evaluation**.

---

# 24. Một điều nữa: đừng bỏ 956 rule families

Kết quả hiện tại cho thấy:

```text
155,467 raw rules
        ↓
956 generalized families
```

và abstraction giữ được signal trong khi type-specific explosion không giúp prediction. 

Đây thực ra là một phần rất đẹp của contribution:

> **The system does not merely memorize individual motifs; it discovers reusable structural rule families.**

Ví dụ:

```text
Motion --Location--> X
Process_end --Location--> X
```

thay vì:

```text
Motion
Process_end
```

bị khóa vào từng type literal cụ thể.

---

# 25. Nhưng mình sẽ đổi tên “rule” một chút

Có ba level:

```text
Motif
  ↓
Pattern
  ↓
Rule
```

### Motif

Graph structure:

```text
A --role--> X <--role-- B
```

### Pattern

Motif + attributes:

```text
A.type = Motion
B.type = Process_end
```

### Rule

Pattern + statistical relation semantics:

```text
P → allowed temporal relations
```

### Constraint

Rule chuyển thành:

```text
P → forbidden relations
```

### Audit finding

Constraint áp lên KG:

```text
KG instance violates constraint
```

Architecture này cực kỳ dễ explain.

---

# 26. Kết luận của mình

**KG hiện tại không cần redesign lớn.**

Nó đã có gần như toàn bộ foundation cần thiết:

* event/entity/span/TIMEX node;
* argument-role edges;
* temporal target isolation;
* multi-view pattern mining;
* generalized rule families;
* Wilson-based statistics;
* Allen 13×13;
* PC-2;
* audit constraint;
* injection protocol.

Cái cần thay đổi chủ yếu là **research framing**:

```diff
- KG → rule → temporal classifier
+ KG → motif/pattern → rule induction
+                  ↓
+          relation inference
+                  ↓
+             KG auditing
+              ↙      ↘
+        wrong edge   missing edge
```

Và khi đặt cạnh PaTeCon, contribution nên nhấn vào:

> **PaTeCon mines temporal constraints from temporal KGs; your system mines semantic event-argument patterns from an event-centric textual KG and uses the induced rules both for relation inference and bidirectional annotation auditing, with Allen-based global consistency checking.**

PaTeCon rõ ràng là related work gần nhất và phải benchmark trực tiếp; nó dùng pattern-based temporal constraint mining trên Wikidata/Freebase. ([GitHub][4]) Trong khi MAVEN-ERE cung cấp unified event relation graph và MAVEN-Arg cung cấp argument semantics ở document level. ([GitHub][2])

**Một điểm mình sẽ ưu tiên làm tiếp ngay:** formalize `Rule`/`Motif`/`Constraint` thành một schema thống nhất và thiết kế **2 loại audit: wrong-edge injection + missing-edge deletion**. Nếu làm xong hai cái này, contribution của bạn sẽ khớp rất sát với mục tiêu ban đầu và không còn bị kết quả C2 “8–10% prediction accuracy” kéo cả project xuống.

[1]: https://ojs.aaai.org/index.php/AAAI/article/view/25533?utm_source=chatgpt.com "PaTeCon: A Pattern-Based Temporal Constraint Mining Method for Conflict Detection on Knowledge Graphs | Proceedings of the AAAI Conference on Artificial Intelligence"
[2]: https://github.com/thu-keg/maven-ere?utm_source=chatgpt.com "GitHub - THU-KEG/MAVEN-ERE: Source code and dataset for EMNLP 2022 paper \"MAVEN-ERE: A Unified Large-scale Dataset for Event Coreference, Temporal, Causal, and Subevent Relation Extraction\". · GitHub"
[3]: https://github.com/THU-KEG/MAVEN-Argument?utm_source=chatgpt.com "GitHub - THU-KEG/MAVEN-Argument: Completing the Puzzle of All-in-One Event Understanding Benchmark with Event Arguments · GitHub"
[4]: https://github.com/JianhaoChen-nju/PaTeCon?utm_source=chatgpt.com "GitHub - JianhaoChen-nju/PaTeCon · GitHub"
[5]: https://aclanthology.org/anthology-files/pdf/emnlp/2022.emnlp-main.60.pdf?utm_source=chatgpt.com "MAVEN-ERE: A Unified Large-scale Dataset for Event Coreference,"
