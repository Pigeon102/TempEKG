# Event-Centric Temporal Constraint Mining on MAVEN-Arg
### Adapting PaTeCon's graph store & constraint mining from entity KGs to an event graph
_Research note — 2026-08-28_

---

## 1. What PaTeCon actually stores (verified against paper + source)

Sources: AAAI'23 paper (arXiv 2304.09015), extended journal version (arXiv 2312.11053 = **PaTeCon+**),
and the reference implementation `github.com/JianhaoChen-nju/PaTeCon` (`Graph_Structure.py`,
`Constraint_Mining.py`, `Interval_Relations.py`).

### 1.1 Data model — a *reified* (statement-node) graph, not a plain triple store

A temporal fact is a quadruple `TF = (S, P, O, T)` with `T = (t.s, t.e)`.
The store splits this into **two vertex kinds**:

| Class | Fields | Meaning |
|---|---|---|
| `eVertex` | `id`, `label`, `isLiteral`, `hasStatement[]`, `bePointedTo[]` | an entity (or literal) |
| `sVertex` | `id` (= the **property**), `hasItem` (subject), `hasValue` (object), `start`, `end`, `weight`, `truth` | one *statement* = one temporal fact |

`Graph` holds exactly three indexes, and they are the whole reason the mining loop is cheap:

```python
eVertexList : dict[entity_id] -> eVertex        # subject-centric adjacency
sVertexList : dict[property]  -> list[sVertex]  # relation-centric inverted index
temporalRelationList : list[property]           # properties that ever carry a time value
entityType  : dict[entity_id] -> list[class]    # for the refinement stage
```

Two consequences worth internalising:

1. **Time lives on the statement node, never on the entity.** The statement node is a
   first-class vertex precisely so it can carry an interval — this is the Wikidata
   qualifier/statement model.
2. **The mining unit is the subject's star.** `Single_Entity_Temporal_Order` iterates
   `for i in graph.eVertexList`, skips literals and any entity with `len(hasStatement) < 2`,
   then enumerates *pairs* of that entity's statements. Cost = `sum_v d(v)^2`. The relation index
   is used only for support/pruning bookkeeping, not for traversal.

Input format is deliberately dumb: TSV `S \t P \t O \t start \t end` (nulls allowed) plus a
separate entity-to-type file. There is no database, no Neo4j, no RDF engine.

### 1.2 Structural patterns

Only two, both fixed by hand (Fig. 3 of the paper):

- **SP(a)** — one subject, two temporal statements: `(x,p1,y,t1), (x,p2,z,t2)`
- **SP(b)** — two subjects joined by an *atemporal* property: `(x,p1,z,t1), (x,p0,y), (y,p2,w,t2)`

Mining = fill the `property` slots from structures actually observed in the KG, then attach a
temporal predicate. The paper explicitly declines to model 3-subject patterns ("we can create
them by combining the constraints of simpler patterns").

### 1.3 Constraint language — three families

```
disjoint(t1,t2) := (x,p,y,t1), (x,p,z,t2), y!=z             # temporal disjointness (same property)
order(t1,t2)    := (x,p1,y,t1), (x,p2,z,t2)                 # SP(a) ordering
order(t1,t2)    := (x,p1,z,t1), (x,p0,y), (y,p2,w,t2)       # SP(b) ordering
false           := (x,p,y,t1), (x,p,z,t2), y!=z             # mutual exclusion (functionality)
```

Head predicates used: `start, finish, before, disjoint, include` (a deliberate subset of Allen's 13),
plus `false` for mutex, plus span bounds (`validSpanBelow/Above`, `relationsSpanBelow/Above` in
`Interval_Relations.py`).

### 1.4 Trivalent logic over uncertain time — the part most people miss

Real KGs have mixed granularity and missing endpoints, so every predicate evaluates to
**positive / negative / unknown** (`FuzzyTime` class). Their Table 2:

| t1 | t2 | t1 < t2 | t1 = t2 |
|---|---|---|---|
| 2021-12 | 2022 | Positive | Negative |
| 2022-01 | 2022 | **Unknown** | **Unknown** |
| – | 2022 | Unknown | Unknown |

`unknown` instances are **discarded** from both support and confidence. This is the single most
transferable idea for your setting, where most events have no clock time at all.

### 1.5 Support & confidence — fact-level vs entity-level

```
support_fact   = #F_positive
conf_fact      = #F_positive / (#F_positive + #F_negative)

entities       = union over F in G(tc) of subject(F)
support_entity = #entities_pos
conf_entity    = #entities_pos / (#entities_pos + #entities_neg)
```

An entity is **positive** only if *all* its matched subgraphs are positive; **negative** if *any* is
negative. Entity-level is strictly harsher and is their headline contribution. Their motivating
failure: "two people cannot play for a team at the same time" scores **0.94** fact-level, because
pairs drawn from a veteran team's whole roster are usually disjoint. Entity-level kills it.

### 1.6 Algorithm & PaTeCon+ pruning

Algorithm 1: instantiate graph patterns -> match subgraphs -> generate constraints for every temporal
predicate -> drop if `support < theta_freq` -> compute confidence -> keep if `c > theta_c1`; if
`theta_c2 < c <= theta_c1`, **refine by attaching class restrictions** to the variables and re-test.
Defaults in the repo: `--support=10 --candidate_confidence=0.5 --confidence=0.9`.

PaTeCon+ adds two-stage pruning justified by Bernoulli's law of large numbers: once a candidate has
been seen `alpha * theta_freq` times and its running confidence is below `beta * theta_c2`, stop
scoring it; once a *property* has appeared `gamma * theta_freq` times and never yielded a promising
candidate, delete that edge type from subgraph matching entirely.

---

## 2. Data reality check — measured on your local copies

All numbers below I computed directly from `MAVEN-Arg.zip` and `MAVEN_ERE/*.jsonl` in
`c:\Reseach_Quang`, not quoted from papers.

| Quantity | Value |
|---|---|
| MAVEN-Arg documents | 4,480 (train 3,623 + valid; `test.jsonl` has `event_mentions` only — no gold args) |
| Events / arguments | 80,479 / 236,937 |
| Argument roles | 143 (type-specific) |
| Entity types | 7: Location, Other, Organization, Person, Product, Building, Art |
| Event types | 168 |
| **MAVEN-ERE ∩ MAVEN-Arg doc ids** | **4,480 / 4,480 — 100 % overlap** |
| MAVEN-ERE temporal relations | BEFORE 1.04 M · CONTAINS 152 K · SIMULTANEOUS 9.9 K · OVERLAP 9.9 K · BEGINS-ON 639 · ENDS-ON 380 |
| TIMEX | DATE / DURATION / TIME / PREPOSTEXP; **no normalised value field**, only surface string |
| Relation endpoints (train+valid) | EE 593 K · TE 200 K · ET 129 K · TT 59 K |
| Events with >=1 TIMEX link | 72.1 % |
| Events with a **tight** TIMEX anchor (CONTAINS/SIMULTANEOUS/BEGINS-ON/ENDS-ON/OVERLAP) | **44.9 %** (10.4 per doc) |
| Events with only a loose TIMEX bound (BEFORE/AFTER) | 27.2 % |
| Events with no TIMEX link at all | 27.9 % |
| **Arguments carrying `entity_id`** | **40.1 %** — the other 59.9 % are bare `{content, offset}` spans |
| **Entities appearing in >1 document** | **0 of 68,348** |
| Entities in >=2 events | 16,284 (mean 3.15 events/entity, max 59) |

### 2.1 Consistency audit of the gold annotation — the finding that changes the objective

Measured over all 3,623 train+valid documents:

| Check | Result |
|---|---|
| BEFORE cycles | **0** (across 843,808 BEFORE pairs) |
| BEFORE symmetric violations `a<b ∧ b<a` | **0** |
| BEFORE transitive closure `a<b<c ⇒ a<c` | **100.0 %** closed (7 missing of 6,718,279) |
| CAUSE contradicted by BEFORE | **11 of 46,014 (0.02 %)** |
| subevent contradicted by BEFORE | **61 of 12,019 (0.5 %)** |
| subevent lacking the implied CONTAINS | 1,638 of 12,019 (13.6 %) — *incompleteness, not contradiction* |

**The gold data is essentially conflict-free: ~72 genuine contradictions in the entire corpus.**
Mining constraints in order to detect conflicts *in the dataset* therefore has almost no target.

This is not a reason to abandon the project — it is a reason to **re-aim it**. A perfectly closed,
consistent gold corpus is a poor audit target but an *excellent* constraint source: mined confidence
is not polluted by annotation noise, so constraints learned here are high-precision by construction.
The conflicts live in **model predictions**, not in the annotation. See 6.

### Statistical power for type-level mining (measured)

Over the 40 % entity-linked arguments only:

| Quantity | Value |
|---|---|
| Shared-participant event pairs | **212,743** ~~274,525~~ |
| ...that also carry a MAVEN-ERE temporal relation (i.e. evaluable, not `unknown`) | **106,340 (50.0 %)** ~~139,093 (50.7 %)~~ |
| Unique event-event temporally related pairs (the mining universe) | **593,433** |
| Distinct `(T1,T2)` type pairs | 12,047 |
| Distinct `(T1,r1,T2,r2)` role signatures | 30,539 |
| `(T1,T2)` signatures with support >= 10 | **2,303**, covering 74 % of instances |
| `(T1,r1,T2,r2)` signatures with support >= 10 | **2,707**, covering 58 % of instances |

> **Corrected 28 Aug 2026.** The struck-through figures were inflated by ~29 %: the original count
> reset its dedup set inside the per-entity loop, so an event pair sharing two or more participants
> was counted once per shared entity, and **19.8 % of pairs share more than one participant**. The
> ratio (50.0 % vs 50.7 %) and the conclusion below are unaffected. Recount:
> `tempekg_handoff/recount_pairs.py`, `tempekg_handoff/recount_signatures.py`.

At PaTeCon's own `theta_freq = 10` there is ample power at both granularities — and pseudo-entity
clustering of the unlinked 60 % can only increase it. Statistical power is **not** the bottleneck.

### The four gaps between PaTeCon's world and yours

1. **No wall-clock intervals on events.** PaTeCon compares numeric endpoints. You have a *qualitative*
   temporal graph (Allen-ish relations) plus un-normalised date strings. ~45 % of events can get a
   real interval; the rest only have order relations.
2. **Entities are document-local.** Zero cross-document entity identity. PaTeCon's whole statistical
   engine depends on one entity accumulating facts across the KG. Here the maximum evidence per
   entity is ~3 events. **You cannot mine at the instance level — you must mine at the *type* level.**
3. **Arguments are only 40 % entity-linked.** The `{content, offset}` form gives you no coreference,
   so the "two events share a participant" join — your SP(a) — silently loses ~60 % of its edges
   unless you cluster the raw spans yourself.
4. **Time is on the node, not the edge.** An event is n-ary (many roles) and carries the interval;
   a PaTeCon statement is binary and carries the interval.

Gap 4 is actually good news: **a MAVEN event node *is* PaTeCon's `sVertex`, generalised from binary
to n-ary.** You keep their bipartite entity/statement architecture verbatim and just widen the
statement node. Do not flatten events into `(subject, predicate, object)` triples — you would be
re-deriving the reification they already chose.

---

## 3. Recommended storage design

### 3.1 Canonical store: DuckDB + Parquet, not a graph database

Rationale: at 80 K events / 237 K argument edges / 1.2 M temporal relations the whole graph is
tens of MB. Mining is group-by/join aggregation, which is exactly what a columnar engine does well,
and SQL makes support/confidence auditable and reproducible. `sum_v d(v)^2` for SP(a) here is on the
order of 10^5 pairs — **seconds, not hours**. Neo4j/kuzu buys you nothing at this scale and costs you
a service dependency. Keep an in-memory adjacency only for per-document closure.

**Corollary: skip PaTeCon+'s two-stage pruning entirely.** It exists to make 27 M-fact Wikidata
tractable. Spend that engineering budget on temporal semantics instead — that is where your
difficulty actually is.

### 3.2 Schema

```sql
-- nodes
events        (event_id PK, doc_id, type, type_id, n_mentions)
event_mentions(mention_id PK, event_id, doc_id, trigger, sent_id, char_start, char_end)
entities      (entity_id PK, doc_id, ent_type)
entity_mentions(mention_id PK, entity_id, doc_id, surface, char_start, char_end)
timex         (timex_id PK, doc_id, tx_type, surface, sent_id, char_start, char_end,
               norm_lo, norm_hi, granularity)      -- norm_* filled by 3.4

-- edges
args          (event_id, role, arg_kind ENUM('entity','span'), entity_id NULL,
               surface NULL, char_start NULL, char_end NULL)
trel          (doc_id, head_id, tail_id, rel, head_kind, tail_kind)   -- 6 MAVEN-ERE types
crel          (doc_id, head_id, tail_id, rel)                        -- CAUSE | PRECONDITION
subevent      (doc_id, parent_id, child_id)
-- event coreference is implicit: events.event_id already clusters its mentions

-- derived
intervals     (event_id, s_lo, s_hi, e_lo, e_hi, source ENUM('timex','propagated','none'))
pointrel      (doc_id, x, y, op)   -- x,y in {ev.s, ev.e, tx.s, tx.e}; op in {<, =, <=, ?}

-- outputs
constraints   (tc_id, family, head_pred, body_json, support, conf_type, conf, refined_by_json)
conflicts     (tc_id, doc_id, witness_json, severity)
```

Two schema decisions to make deliberately:

- **`args.arg_kind`.** Keep both forms rather than dropping the 60 % unlinked spans. Then add a
  *pseudo-entity* pass: within a document, cluster raw spans by normalised string / head-noun match
  and mint `PSEUDO_ENTITY_*` ids. Measure recovered join edges before and after — this number
  directly bounds how much evidence your SP(a) mining sees.
- **`intervals` uses four endpoint bounds, not two.** `[s_lo, s_hi] x [e_lo, e_hi]` is how you
  represent "started somewhere in 1778" without lying. This is `FuzzyTime` generalised, and it
  degrades gracefully to PaTeCon's exact case when `s_lo = s_hi`.

### 3.3 In-memory mirror (for closure and matching)

Mirror `Graph_Structure.py` but bipartite and n-ary:

```python
class EntityVertex:  id; ent_type; doc_id; in_roles: list[(role, EventVertex)]
class EventVertex:   id; ev_type; doc_id; roles: dict[role, list[EntityVertex|Span]]
                     interval: Interval4        # s_lo, s_hi, e_lo, e_hi
class Doc:           events; entities; timex; point_graph

Index:  by_event_type: dict[type] -> list[EventVertex]
        by_type_pair : dict[(t1,t2)] -> list[(EventVertex, EventVertex, shared_role_sig)]
        by_entity    : dict[entity_id] -> list[EventVertex]     # <- the SP(a) star
```

`by_type_pair` is the index PaTeCon does *not* have and you need: because your instances are
document-local, **the aggregation key is the type signature, not the entity.**

### 3.4 Building `intervals` — the real work

Three tiers, in order:

- **Tier 1 (44.9 % of events) — anchored.** For each `CONTAINS(tx, ev)` / `SIMULTANEOUS` /
  `BEGINS-ON` / `ENDS-ON`, normalise the TIMEX surface string to `[norm_lo, norm_hi]` with an explicit
  granularity, then set the event's endpoint bounds. **MAVEN-ERE ships no normalised TIMEX values.**

  **Measured difficulty of that normalisation** (20,827 TIMEX instances, 9,287 distinct surfaces):

  | Class | Share |
  |---|---|
  | bare year (`1778`) | 29.9 % |
  | day-month-year (`11 November 1778`) | 9.1 % |
  | month + year | 6.9 % |
  | N + unit (`three years`) — a **duration**, constrains width not position | 6.1 % |
  | month + day + year | 4.6 % |
  | year range, month-only, decade, century, deictic | 5.6 % |
  | **deterministic regex subtotal** | **62.1 %** |
  | **needs document context** | **37.9 %** |

  The 37.9 % is not evenly hard — it is dominated by four tractable families:
  **relative dates** (`"the next day"` ×91, `"the following day"` ×62, `"the same day"` ×21,
  `"later that day"`, `"the previous year"`), **year-less dates** (`"September 11"` ×24,
  `"September 16"`, `"August 31"`), **named periods** (`"World War II"` ×70, `"the Second World War"`
  ×32, `"World War I"` ×30 — typed DURATION), and **weekdays** (`"Sunday"` ×21).

  So the realistic build is: regex normaliser (~2 days) + **document-level reference-time
  propagation** in TimeML narrative-container style (~2 days) + a ~50-entry gazetteer for named wars
  and periods (~half a day). That should reach roughly 85-90 % coverage, with an LLM pass reserved
  for the tail. **This is materially cheaper than "run HeidelTime and hope"** — and it means the
  critical path is ~1 week, not ~3.
- **Tier 2 (27.2 %) — bounded.** `BEFORE(tx, ev)` gives `ev.s >= tx.e`. Propagate through the
  document's point graph.
- **Tier 3 (27.9 %) — qualitative only.** No numeric bound. Never guess; leave `source='none'` and
  let the predicate return `unknown`.

### 3.5 Evaluate predicates in the **point algebra**, not by numeric comparison

Give each event two endpoint variables `ev.s, ev.e` and translate every MAVEN-ERE relation into
point constraints (`BEFORE(a,b) => a.e < b.s`; `CONTAINS(a,b) => a.s <= b.s and b.e <= a.e`;
`SIMULTANEOUS => a.s = b.s and a.e = b.e`; `OVERLAP(a,b) => a.s < b.s < a.e < b.e`; etc.).
Run path-consistency / transitive closure per document (documents average 23.3 events — closure is
trivial). Then:

```
eval(pred, e1, e2) = positive  if closure entails pred
                     negative  if closure entails not-pred
                     unknown   otherwise
```

This is the clean generalisation of PaTeCon's Table 2: it subsumes both the numeric case (Tier 1)
and the purely qualitative case (Tier 3) in **one** trivalent operator, which is exactly what their
support/confidence formulas already expect. Anchored numeric bounds enter as additional point
constraints, so the two tiers compose instead of competing.

> **Confirmed by measurement (see 2.1): the released BEFORE annotation is 100.0 % transitively
> closed** — of 6,718,279 `a<b<c` chains checked across 3,623 documents, only **7** lacked the implied
> `a<c` edge. Do not recompute closure over gold relations or you will double-count support; treat the
> gold temporal graph as already closed and compute closure only for *predicted* graphs. Also note the
> documented convention that all types except SIMULTANEOUS and BEGINS-ON are unidirectional (head
> starts first) — encode direction explicitly rather than assuming symmetry.

---

## 4. Recommended constraint language (event-centric)

Transposition table:

| PaTeCon | Your version |
|---|---|
| entity (subject) | **event type t** (aggregation) / event instance (matching) |
| property `p` | **argument role** `r` (143) or event-event relation |
| statement node `sVertex` | **event node** (n-ary, carries interval) |
| class restriction | event type t + entity type (7) + role |
| `T` on the statement | `Interval4` on the event node |
| entity-level grouping | **document-level** grouping (entities don't cross docs) |

### Family A — Type-level ordering (the SP(a) analogue, your workhorse)

```
before(t1,t2) := (e1, r1, x, t1), type(e1)=T1,
                 (e2, r2, x, t2), type(e2)=T2,  e1!=e2
```

Mined over the 16,284 entities that participate in >=2 events. Candidates: `Process_start` before
`Process_end`; `Attack` before `Surrendering`; `Being_born` before everything with the same Person.
This is *exactly* PaTeCon SP(a) with role-for-property and event-type-for-class.

### Family B — Participant exclusivity (the disjointness analogue)

```
disjoint(t1,t2) := (e1, r, x, t1), type(e1)=T,
                   (e2, r, x, t2), type(e2)=T,  e1!=e2
```

"An `Agent` cannot be in two `Hostile_encounter`s at overlapping times."

### Family C — Once-only events (the mutex analogue)

```
false := (e1, r, x), type(e1)=T, (e2, r, x), type(e2)=T, e1!=e2
```

"A Person is `Victim` of at most one `Death`." **Must be evaluated modulo event coreference** —
MAVEN's `event_id` already clusters mentions, so use `event_id`, never `mention_id`, or every
repeated mention becomes a false conflict.

### Family D — Event-specific families with **no entity-KG analogue** (your novelty)

These do not exist in PaTeCon and are where an event-centric paper earns its place:

1. **Subevent containment.** `subevent(e1,e2) => contains(t1,t2)`. Hard, logically necessary,
   and MAVEN-ERE hands you the supervision for free.
2. **Causal-temporal coherence.** `CAUSE(e1,e2) => not after(t1,t2)`;
   `PRECONDITION(e1,e2) => before(t1,t2) or overlap(t1,t2)`. A cause that starts after its effect is
   an unambiguous conflict. This is the event analogue of PaTeCon's `killed_by`/`place_of_death`
   SP(b) example — and unlike SP(b), it needs no 2-hop path because MAVEN annotates the link directly.
3. **Coreference identity.** Coreferent event mentions must receive identical intervals.
4. **Type-conditioned duration bounds.** Mine `max_span(T)` from Tier-1 anchored events
   (`Bombing` ~ hours; `War` ~ years), mirroring `validSpanBelow/Above`. Then any extracted event
   whose induced interval violates its type's bound is a conflict.
5. **Intra-event role coherence.** e.g. for `Motion`, `Location_original` precedes `Location_final`.

Families D1-D3 are **hard constraints** (confidence 1.0 by construction — do not mine them, assert
them). Families A, B, C, D4, D5 are **soft/mined**. Keeping that distinction explicit will save you
from reporting mined-confidence numbers on constraints that are actually definitional.

### Scoring — what replaces entity-level confidence

Because entities are document-local, run **three** confidence variants and report all three:

- `conf_pair` — fact-level over event pairs (the naive baseline; expect it to be inflated, exactly as
  the "veteran team" example predicts).
- `conf_entity_doc` — PaTeCon entity-level, grouping by `(doc_id, entity_id)`. Positive only if *all*
  that entity's matched pairs are positive.
- `conf_doc` — group by `doc_id`. Positive only if the constraint is violated nowhere in the document.

`conf_doc` is the closest structural analogue of their entity-level metric (the document is your
"one entity's career") and I expect it to be the one that separates real regularities from
co-occurrence artefacts. Discard `unknown` from all three, per 1.4.

---

## 5. Mining loop (adapted Algorithm 1)

```
for each doc:
    build point graph, run path consistency          # 3.5
    materialise intervals (3 tiers)                  # 3.4
    emit pseudo-entities for unlinked arg spans      # 3.2

for each (T1, r1, T2, r2) signature over shared-participant event pairs:   # by_type_pair index
    for each temporal predicate tp in {before, disjoint, include, start, finish, false}:
        tc = (tp, signature)
        accumulate pos / neg / unknown at pair, (doc,entity) and doc granularity
        drop if support < theta_freq

for each candidate:
    if conf > theta_c1: accept
    elif conf > theta_c2: refine by <entity type, role, event subtype> and re-test
```

Start with PaTeCon's own defaults (`theta_freq=10, theta_c2=0.5, theta_c1=0.9`) so your first table
is directly comparable, then tune. Given 168 event types the signature space is large but sparse —
most `(T1,T2)` pairs never co-occur, so index only observed pairs.

---

## 6. Conflict detection & evaluation plan

> **Revised after the 2.1 audit.** The original plan here — "mine constraints, then apply them to gold
> data to surface conflicts", mirroring how PaTeCon+ built WD27M/FB37M — does not survive contact with
> the measurements. MAVEN-Arg/ERE gold is 100 % transitively closed, cycle-free, and contains ~72 total
> contradictions. There is no conflict benchmark to harvest. The plan below points the same machinery
> at *predicted* graphs instead, which is where the conflicts actually are.

1. **Sanity pass on gold (small, cheap, one table).** Apply the hard constraints (D1-D3) to gold and
   report the ~72 contradictions + 1,638 missing-CONTAINS as an annotation-quality footnote. Useful,
   honest, and explicitly *not* a main contribution.
2. **Measure the violation rate of an unconstrained model.** Train/obtain a MAVEN-ERE temporal
   relation baseline, decode it without constraints, and count cycles, symmetry violations and
   transitivity violations in its output. **This number is the premise of the whole project — measure
   it in week 1.** If predicted graphs are also near-consistent, stop and re-scope.
3. **Downstream use — this is the payoff, and it connects straight to your existing pipeline.**
   Your repos (`MAVEN_Arg_Pipeline` CLEVE->PAIE, `DEEIA`, `SCPRG`, `TSAR`) all produce *unconstrained*
   predictions. Feed mined constraints in as global inference:
   - ILP / weighted-MaxSAT over predicted temporal relations with mined constraints as soft clauses
     and D1-D3 as hard clauses — the classical structured-prediction recipe (Ning et al.;
     *Joint Constrained Learning for Event-Event Relation Extraction*), still the standard in 2025
     work such as *Consistent Discourse-level Temporal Relation Extraction Using LLMs*
     (Findings of EMNLP 2025), which uses Allen-algebra prompting + reflection-based consistency.
   - or as a re-ranker / consistency-regularisation term on ED and EAE output.

   Report delta-F1 with and without constraints. **A constraint set that mines cleanly but changes no
   downstream number is a weak paper; plan this experiment first, not last.**

---

## 7. Honest risks

- **The temporal grounding is the project.** 55 % of events never get a numeric interval, and TIMEX
  normalisation is unshipped. If Tier 1 is weak, every mined constraint collapses to `unknown` and
  support vanishes. De-risk this in week 1 with a 50-document manual check of normalised TIMEX values.
- ~~**Document-locality caps your statistics.**~~ **Retired — measured and refuted.** Type-level
  aggregation yields 2,708 `(T1,T2)` and 2,688 `(T1,r1,T2,r2)` signatures at `theta_freq=10`
  (2.1). Instance-level evidence is thin (3.15 events/entity) but type-level power is ample.
- **The objective, not the data, is the main risk.** Gold is conflict-free (2.1), so the project
  only has a subject if *predicted* event graphs are measurably inconsistent. Validate that premise
  before building the mining infrastructure.
- **Scope cost: you do not currently have a temporal RE model.** Your repos (`PAIE_Maven`, `DEEIA`,
  `SCPRG`, `TSAR_Maven`, `MAVEN_Arg_Pipeline`) are all trigger/argument extraction. Constraining
  temporal relations means standing up a MAVEN-ERE baseline first — a new component, not a
  modification of existing code. Budget for it explicitly.
- **60 % of arguments are unlinked spans.** Your pseudo-entity clustering quality directly gates
  Family A/B/C recall. Measure and report it as a component, not a footnote.
- **MAVEN-ERE relations are model-usable but annotation-noisy**, and probably pre-closed. Constraints
  mined from closed annotations partly re-derive the closure rules you already know. Guard against
  this by reporting how many mined constraints are *not* consequences of Allen transitivity.
- **Novelty framing.** "PaTeCon on events" alone is thin. The defensible contributions are:
  (i) the trivalent point-algebra evaluation that unifies anchored and qualitative time,
  (ii) constraint families D1-D5 which have no entity-KG counterpart, and
  (iii) the first event-graph conflict benchmark + downstream gains on MAVEN-Arg extraction.

---

## Sources

- [PaTeCon (AAAI 2023) — arXiv:2304.09015](https://arxiv.org/abs/2304.09015) · [AAAI proceedings](https://ojs.aaai.org/index.php/AAAI/article/view/25533)
- [PaTeCon+ — Conflict Detection for Temporal KGs: A Fast Constraint Mining Algorithm and New Benchmarks, arXiv:2312.11053](https://arxiv.org/abs/2312.11053)
- [PaTeCon reference implementation](https://github.com/JianhaoChen-nju/PaTeCon)
- [MAVEN-ERE — arXiv:2211.07342](https://arxiv.org/abs/2211.07342v1)
- [Consistent Discourse-level Temporal Relation Extraction Using LLMs (Findings of EMNLP 2025)](https://aclanthology.org/2025.findings-emnlp.1010.pdf)
- [Joint Constrained Learning for Event-Event Relation Extraction](https://arxiv.org/pdf/2010.06727)
- [Event-Centric Temporal Knowledge Graph Construction: A Survey (Mathematics, MDPI)](https://www.mdpi.com/2227-7390/11/23/4852)
- [Respecting Temporal-Causal Consistency: Entity-Event KGs for RAG, arXiv:2506.05939](https://arxiv.org/abs/2506.05939)
- [Explainable Temporal Fact Validation Through Constraints Discovery in KGs (ESWC 2025)](https://link.springer.com/chapter/10.1007/978-3-031-94575-5_13)
- [EventFull: Complete and Consistent Event Relation Annotation, arXiv:2412.12733](https://arxiv.org/abs/2412.12733)
- [Rethinking TKG Representation Learning: From Entities to Evolutionary Event-Centric Clusters (KDD 2026)](https://dl.acm.org/doi/10.1145/3770854.3780173)

---

# 8. Design for a **predicted** event graph (no gold graph at build time)

_Added 2026-08-28, second pass. This section supersedes 3.2/3.3 whenever the graph is built from
pipeline output rather than gold annotation._

## 8.1 What the pipeline actually gives you — audited

| Layer | Available from your pipeline? | Notes |
|---|---|---|
| Event nodes (trigger span + type) | **Yes** — ED model, or gold triggers | two noise conditions, by design |
| Argument edges (role + span) | **Yes** — PAIE / DEEIA / SCPRG / TSAR | but see 8.2 |
| **Entity clusters (id, type, mention offsets)** | **Yes — GIVEN as input, even in blind `test.jsonl`** | the single most important fact in this section |
| Event coreference | **No** at test (`event_mentions` is flat) | only 3.6 % of train events are multi-mention — low cost |
| **Temporal relations (event-event, event-TIMEX)** | **NO — absent from every repo** | must be built |
| **TIMEX spans + normalised values** | **NO** | must be built |

Verified by grep across `MAVEN_Arg_Pipeline`, `PAIE_Maven_1`, `DEEIA_Maven`, `SCPRG_20th7_3`,
`TSAR_Maven`: the only match for `temporal_relations|TIMEX|BEFORE` is a code comment in
`PAIE_Maven_1/engine.py:82`. **There is no temporal component anywhere in your codebase.**

### 8.1.1 Why EAE cannot supply the time — it is the ontology, not the model

Measured on **gold** MAVEN-Arg train+valid (i.e. this is the *ceiling* a perfect EAE model reaches):

| Check | Result |
|---|---|
| Roles named Time / Date / When / Start / End | **none of the 143** |
| Only explicitly temporal role: `Duration` | **33 instances, in exactly 1 event type (`Prison`)** — values are `"life"`, `"21 years"`, i.e. sentence lengths, not timestamps |
| Argument spans overlapping any TIMEX span | 7,057 of 142,015 = **4.97 %** |
| **TIMEX expressions covered by any argument span** | **2,877 of 20,827 = 13.8 %** |

Per-role overlap rates confirm the overlap is incidental, not temporal: `Name` 46.5 % (event names
like *"the 1972 Munich massacre"* happen to contain a date), `Cause` 8.4 %, `Patient` 5.1 %,
`Agent` 3.6 %, `Location` 1.4 %.

So even where an argument span does touch a time expression, you receive the *surface string* under a
role (`Patient`, `Name`) that carries **no temporal semantics** — no normalised value, and no
assertion that the event occurred then. **86 % of the time expressions in these documents are never
touched by MAVEN-Arg's argument annotation at all.**

> An EAE model can only predict roles that exist in the ontology. MAVEN-Arg's ontology has no
> temporal role. A *perfect* PAIE/DEEIA/SCPRG/TSAR at 100 % F1 would still yield zero event
> timestamps. This is not a model-quality problem and no amount of EAE improvement addresses it.

### Consequence

> A graph built from ED -> EAE alone has **no time dimension at all**. Temporal constraint mining on
> it is not merely hard, it is undefined. The temporal layer is not a refinement of this plan — it is
> a prerequisite, and it is the largest single item of new work.

### 8.1.2 The temporal layer is smaller than it looks — TIMEX spans are GIVEN

**Correction to an earlier draft of this section:** you do *not* need to build a TIMEX tagger.
`MAVEN_ERE/test.jsonl` — the blind split, with `temporal_relations` absent and `event_mentions`
flat — still ships a populated `TIMEX` field. TIMEX spans are an **input** in MAVEN-ERE, exactly as
`entities` are an input in MAVEN-Arg. TIMEX detection is not a task in this benchmark.

What remains, with the gold supervision available for each:

| Component | Still needed? | Supervision (train+valid) |
|---|---|---|
| TIMEX detection | **No — spans are given in every split** | 20,827 spans, provided |
| TIMEX **normalisation** (surface -> interval) | **Yes — unavoidable** | **none** — MAVEN-ERE has no value field |
| Event-TIMEX linking | **Yes** | 66,418 `CONTAINS` (see 8.9) |
| Event-event temporal RE | **Yes**, for the ~55 % of events with no anchor | 593 K relations |

So the temporal layer reduces to *normalisation + linking + event-event RE*. Section 8.9 argues that
the linking half can be folded into your existing EAE model at near-zero cost.

### The good news

`entities` (ids, 7 types, mention offsets) ships with **every** split including blind test. So the
**join key that makes Families A/B/C minable survives into the predicted setting** — you do not have
to predict coreference. This was my main worry and it is resolved. Link predicted argument spans to
these given clusters by **maximal character-offset overlap (IoU)**, not exact match: predicted spans
will not respect entity mention boundaries. Store the IoU as `link_conf`.

## 8.2 Blocking engineering item

`pipeline/export_paie_preds.py::dump_features` currently emits

```json
{"doc_key": "...", "event_type": "...", "roles": {"Agent": ["British forces"]}}
```

— role -> **surface text only**. The span offsets exist internally as `feat.pred_dict_word` but are
discarded. **You cannot build a graph from this**: no offsets means no entity linking, no sentence
position, no alignment to TIMEX. Fix the exporter to emit char spans alongside the text before
anything else in this section is possible.

## 8.3 The circularity trap — the central methodological risk

If you mine constraints from predicted graphs and then detect conflicts in predicted graphs, the
constraints absorb the model's **systematic** biases. Any error the model makes *consistently*
becomes a high-confidence "constraint" and is thereby rendered permanently invisible. The method
will look excellent (few conflicts) precisely where the model is most reliably wrong.

Ranked mitigations:

1. **Mine on gold train, detect on predicted dev/test.** Cleanest, and the 2.1 audit argues for it
   directly: gold is 100 % transitively closed and cycle-free, so mined confidences carry no
   annotation noise. Zero circularity. **This is the recommended default.**
2. **If mining must run on predictions** (the genuine no-GT deployment story): use **K-fold
   cross-fitting** — partition documents into K folds, mine on K-1, detect on the held-out fold,
   rotate. Never let a document contribute to both the constraints and the conflicts tested against
   them.
3. **Confidence-weighted support.** PaTeCon's `sVertex.weight` field exists and is hardcoded to 1.
   Now use it: weight each instance by ED x EAE x temporal-model confidence so that shaky
   predictions move the statistics less.

Report (1) as the main result and (2) as an ablation. **The gap between them is itself a finding** —
it quantifies how much a constraint miner degrades when it loses access to gold, which is exactly the
question a deployment reader has.

## 8.4 Exploit the noise dial — the strongest experimental design available to you

Your pipeline already produces two trigger conditions. That gives three graphs over *the same
documents*, with monotonically increasing noise:

| Graph | Triggers | Arguments | Role |
|---|---|---|---|
| `G_gold` | gold | gold | ceiling / constraint source |
| `G_trig` | **gold** | predicted | isolates *argument* noise |
| `G_pred` | predicted (ED) | predicted | full pipeline noise |

Mine on `G_gold` (train), then detect on all three. Two payoffs:

- **Conflict rate should rise monotonically** `G_gold < G_trig < G_pred`. If it does not, your
  constraints are not tracking real errors — a cheap, early, falsifiable check.
- **Because MAVEN gold exists, you can verify conflict-flagging precision directly**: for every event
  or argument flagged by a violated constraint, check against gold whether it is *actually* wrong.
  This yields a real precision number for conflict detection — something a true no-GT setting can
  never measure, and the main reason to do this work on MAVEN rather than on raw documents.

That measured precision is what licenses the method's use on genuinely unlabelled text later.

## 8.5 Schema deltas from 3.2

Everything in 3.2 stands; add provenance and confidence throughout, and make identity explicit.

```sql
-- every node/edge gains provenance + score
events (event_id, doc_id, type, type_id,
        trigger_start, trigger_end,
        source ENUM('gold','pred'), ed_score, type_score,
        graph_variant ENUM('G_gold','G_trig','G_pred'))     -- 8.4

args   (event_id, role, char_start, char_end, surface,
        entity_id NULL, link_conf,          -- IoU against given entity mentions
        eae_score, source, graph_variant)

trel   (doc_id, head_id, tail_id, rel, model_score, source, graph_variant)

timex  (timex_id, doc_id, surface, char_start, char_end,
        norm_lo, norm_hi, granularity, norm_conf, norm_source ENUM('rule','llm','none'))

-- alignment to gold, for evaluation only (8.4)
align  (pred_event_id, gold_event_id, match ENUM('exact','span_only','type_only','none'))

-- a conflict must name its suspects, not just its constraint
conflicts (tc_id, doc_id, graph_variant,
           witness_events JSON, witness_args JSON, witness_trels JSON,
           min_conf_element, min_conf,      -- the repair candidate
           severity)
```

Three deliberate choices:

- **Identity.** A predicted event has no id. Key it by `(doc_id, trigger_start, trigger_end)` and keep
  `type` as an attribute, so a type error does not silently create a *different* node. Your
  `scripts/03b_eval_ed.sh` already does exact offset+type matching — reuse that logic for `align`.
- **`min_conf_element`.** When a constraint fires, the useful output is not "this document is
  inconsistent" but "*this* edge is the weakest link in the violated witness". That field turns the
  system from a diagnostic into a repair mechanism, and it is what feeds 6.3's MaxSAT layer.
- **`graph_variant`** as a first-class column, so all three graphs live in one store and the noise
  dial is a `GROUP BY`.

## 8.6 The temporal layer you have to build

Ranked by leverage per unit of work:

1. **TIMEX detection + normalisation** (highest leverage, least glamorous). Gold MAVEN-ERE ships TIMEX
   *spans* but **no normalised values** — so this component is unbuilt even in the gold setting, and
   you need it in both. HeidelTime/SUTime/`dateparser` over the surface string with the Wikipedia
   article's inferred date as reference, or a schema-constrained LLM pass. Gets you Tier-1 anchoring
   for ~45 % of events.
2. **Event-TIMEX linking.** Predict `CONTAINS(tx, ev)` — a much easier, more local task than full
   event-event temporal RE, and it is what actually produces intervals.
3. **Event-event temporal RE.** The full MAVEN-ERE task. Heaviest item; train on gold train split.

> **Compounding-error warning.** A temporal RE model trained on *gold* event mentions and run over
> *predicted* triggers is off-distribution — pipeline error compounds multiplicatively across
> ED -> EAE -> temporal RE. Measure the degradation explicitly (train-on-gold/test-on-pred vs
> train-on-pred/test-on-pred); do not assume MAVEN-ERE reported F1 transfers to `G_pred`.

## 8.7 What changes in the mining itself

- **`unknown` dominates.** On gold, 50.7 % of shared-participant event pairs carry an evaluable
  temporal relation (2.1). On predicted graphs, recall losses push this down hard. PaTeCon's
  trivalent logic already handles it correctly by discarding unknowns — but **re-measure support at
  every noise tier**, because `theta_freq = 10` may stop being reachable for role-level signatures on
  `G_pred`. Back off from `(T1,r1,T2,r2)` to `(T1,T2)` when support collapses.
- **A conflict indicts a set, not an element.** A hallucinated `Killing` sharing a Victim produces a
  Family-C mutex violation in which the *gold* event is equally implicated. Never auto-delete the
  flagged element; rank by `min_conf` and let the MaxSAT layer decide globally.
- **Spurious-event asymmetry.** ED precision errors *create* conflicts; ED recall errors *hide* them.
  Report conflict counts against ED precision and recall separately, or the trend in 8.4 will be
  uninterpretable.

## 8.8 Recommended build order

1. Fix `export_paie_preds.py` to emit char spans (8.2). *Blocking, ~hours.*
2. Build `G_gold` / `G_trig` / `G_pred` with entity linking by offset IoU. *No temporal layer yet.*
3. TIMEX detection + normalisation; validate on 50 documents by hand (3.4).
4. Event-TIMEX `CONTAINS` linker -> Tier-1 intervals.
5. Mine Families A/B/C + D4/D5 on gold train; assert D1-D3.
6. Detect on all three variants; check monotonicity (8.4) and measure flagging precision against gold.
7. Only then: event-event temporal RE and the MaxSAT repair layer (6.3).

Steps 1-2 are cheap and de-risk everything. Step 6 is the go/no-go gate: if conflict rate does not
increase with noise, or flagging precision is near chance, stop before step 7.

---

## 8.9 Should the EAE model extract time itself? — merge vs separate model

### The enabling facts (measured)

| Fact | Value |
|---|---|
| Event ids shared between MAVEN-Arg and MAVEN-ERE | **79,740** (4,545 ERE-only; MAVEN-Arg subsamples events) |
| `CONTAINS(timex, event)` anchors | **66,418** (58,691 + 7,727 reversed) |
| `SIMULTANEOUS` anchors | 496 |
| `BEGINS-ON` anchors | **122** |
| `ENDS-ON` anchors | **39** |
| PAIE prompt file | `eae/data/prompts/prompts_mavenarg_concat.csv`, **162 lines**, format `Type:prompt start, Role ( and Role ) ( and Role ) ... ,end` |

The merge is a **join on `event_id`** plus an append to two CSVs. Adding a role to all 162 event
types is a ~10-line script, not a manual edit. Engineering effort is not the deciding factor.

### Add ONE role, not three

An earlier draft of this note suggested `Time_Start` / `Time_End` / `Time_Within` to preserve interval
semantics. **The data refutes that**: BEGINS-ON (122) and ENDS-ON (39) are too rare to learn, and
CONTAINS carries 99 % of the anchoring mass. Add a single role — `Time_Within`.

This also dissolves the main objection against merging. The worry was "a `Time` role throws away the
relation type, so you still need a linker." There *is* effectively only one relation type here, so
**the role is the relation**. And because PAIE predicts arguments *conditioned on the trigger*,
"which event does this time attach to" is answered by construction. **Merging solves extraction and
linking together.**

### What merging does and does not buy

| | |
|---|---|
| Solves | event-TIMEX linking, in the existing architecture, one inference pass |
| Solves | span selection over contiguous text — precisely what PAIE already does |
| Does **not** solve | **normalisation**: `"November 11 , 1778"` is a string, not an interval (3.4) |
| Does **not** solve | the **~55 % of events with no TIMEX anchor** — needs event-event temporal RE, which an EAE model structurally cannot emit (it predicts arguments per event, never relations between events) |

### Costs to price in

- **Leaderboard comparability.** Your README targets MAVEN-Arg paper Table 3 + CodaLab submission.
  Changing the role inventory makes those outputs non-comparable. **Keep the baseline run untouched
  and make the merged model a second run** — then you have both.
- **Argument-F1 regression risk.** A longer prompt and an extra role on every template may cost
  accuracy on the original 143 roles. Measure it; do not assume it is free.
- **Cardinality.** 46 % of anchored events carry >=2 CONTAINS TIMEX (nested granularity — *"in 1778"*
  plus *"on November 11"*). PAIE's concat template gives 3 slots per role; 2,742 events have >=4 and
  will truncate. Multiple anchors are a *feature* — **intersect** them for a tighter interval.

### Recommendation

**Merge for the linking half; keep separate components for the rest.** Concretely:

1. Inject `Time_Within` into MAVEN-Arg training data by joining MAVEN-ERE `CONTAINS` on `event_id`;
   append the role to `prompts_mavenarg_concat.csv` and `description_mavenarg.csv`. Retrain PAIE as a
   **second** run alongside the untouched baseline.
2. Build the **normaliser** separately (rule-based or schema-constrained LLM). Unavoidable either way.
3. Build **event-event temporal RE** separately, for the unanchored majority. Unavoidable either way.

So the answer to "merge or new model" is *both, but merging covers more than expected*: it removes
one of the three components outright and needs no new architecture.

---

# 9. Review of the TempEKG plan (URA Lab, COLING 2027)

_Against the 28 Aug 2026 slide deck. Deadline **12 Oct 2026 = 45 days**. That budget drives every
recommendation below._

## 9.1 The blocking issue: the fake-conflict evaluation is circular

> Phase 4: *"Dùng tập constraint thu được để fake dữ liệu conflict temporal bằng cách thay đổi thời gian."*
> Phase 5: *"Dùng tập constraint đã mining trên graph train, áp dụng lên graph test để phát hiện conflict và benchmark."*

Conflicts are **generated by violating the mined constraints**, then **detected with those same
constraints**. Recall is ~100 % by construction and measures nothing. A COLING reviewer will see this
immediately; it is the single largest risk to acceptance.

**Fix — three evaluation tiers, none circular:**

| Tier | Conflict source | Measures |
|---|---|---|
| 1 | **Random** time perturbation, *not* constraint-guided | recall, controlled, non-circular |
| 2 | **Predicted graphs** from Phase-1 models (`G_trig`, `G_pred`, 8.4) | realistic conflicts, real distribution |
| 3 | Untouched gold graph | **false-positive rate** (2.1 says it should be ~0) |

Tier 2 is the important one, and it is nearly free — the models are already trained.

## 9.2 Phase 1 is currently orphaned — Tier 2 reconnects it

Phase 1 trains PAIE / SCPRG / DEEIA, but Phase 2 builds the graph *"Từ Gold Label của tập MAVEN-ARG"*.
So the extractors never feed the graph. The slide says Phase 1 results are used to evaluate the
pipeline *"về sau"*, but no mechanism is given.

Using predicted graphs as the Tier-2 conflict source fixes the circularity **and** connects Phase 1 to
Phases 2-5 in one move. Without it, the paper is two disconnected halves and the Event Extraction
benchmark is decoration.

## 9.3 Phase 3 — get the projection *direction* right, or Phase 4 returns nothing

This is the highest-value technical detail in this review.

**Wrong projection (event as subject):** `(event, role, entity, T)`. Every statement of one event
shares the same interval `T`, so `before` / `disjoint` are trivially false for every pair. **Phase 4
mines nothing.** Weeks lost discovering this empirically.

**Correct projection (entity as subject):**

```
(entity_x , "EventType#Role" , event_e , T_e)
```

PaTeCon's `Single_Entity_Temporal_Order` then iterates entity stars and enumerates pairs of *events
sharing a participant* — exactly Families A/B/C. Measured feasibility:

| | |
|---|---|
| distinct `EventType#Role` properties | **652** (623 with >=10 instances) |
| PaTeCon's `|R|^2` relation-pair index | 425,104 entries, **~0.1 GB** — fits comfortably |
| shared-participant event pairs | 274,525 |
| `(T1,T2)` signatures at support >= 10 | 2,708 |

The property vocabulary is small enough that PaTeCon's code runs unmodified. **Projection is a valid
engineering shortcut** — but keep the ECKG as the system of record, because the constraint families
in Section 4 (D1-D5) cannot be expressed in the projected binary form.

## 9.4 Granularity Conflict is the best asset in the plan and is under-developed

It has **no PaTeCon analogue**, it is event-specific, and it is cheap. Measured population:

| CONTAINS anchors per event | events |
|---|---|
| 1 | 19,802 |
| 2 | 10,653 |
| 3 | 3,707 |
| >= 4 | 2,742 |

**17,102 events carry >= 2 time anchors** — the population where a granularity conflict is even
definable. Typical cases are nested (*"in 1778"* + *"on November 11"*), which should **intersect**;
a conflict is an event whose anchors have **empty intersection** at their coarsest common
granularity.

Two properties make this the highest-ROI item for a 45-day budget:

- **No mining required.** It is a consistency check over PaTeCon's trivalent `FuzzyTime` logic, not a
  statistical pattern search. Implementable in days.
- **It may yield *real* conflicts in gold**, which the ordering side does not (2.1 shows gold ordering
  is 100 % consistent). Run this first — it is a genuine finding either way.

**Week-1 experiment:** normalise TIMEX, intersect each event's anchors, count empty intersections.
One number, high information, cheap.

## 9.5 Phase 2 (Nhựt) — two concrete warnings

1. **Split by DOCUMENT, not by event.** Constraints are mined over event pairs sharing a participant
   *within a document*, and entities never cross documents (2). An event-level split puts co-document
   events in both train and test — direct leakage through shared entities, shared TIMEX and shared
   temporal relations. Inflated numbers, and a reviewer will ask.
2. **"Sự kiện có mốc thời gian" needs a precise definition.** Recommend the *tight-anchored* set:
   events with `CONTAINS` / `SIMULTANEOUS` / `BEGINS-ON` / `ENDS-ON` to a TIMEX = **37,852 events
   (44.9 %)**, 10.4 per document. Adding BEFORE/AFTER-only events (27.2 %) gives bounds, not
   intervals, and will mostly evaluate to `unknown`.

## 9.6 Scope triage for 45 days

| Keep | Cut / defer |
|---|---|
| Gold-based ECKG (Phase 2) | Training an event-event temporal RE model |
| Entity-subject projection (Phase 3) | MaxSAT / ILP repair layer (6.3) |
| Constraint mining (Phase 4) | Tier-2/Tier-3 interval induction (3.4) |
| **Granularity conflict** (9.4) | The `Time_Within` EAE merge (8.9) — elegant, but not on the critical path |
| Tiers 1-3 evaluation (9.1) | |

**Critical path: TIMEX normalisation.** It is unbuilt, unglamorous, has no gold supervision
(8.1.2), and *everything* — intervals, ordering conflicts, granularity conflicts — is blocked behind
it. It should start immediately, not after Phase 3.

## 9.7 Novelty check

A search for prior event-level temporal conflict detection turned up event-centric TKG
*construction* surveys, EventKG, and EventFull (annotation consistency) — **but no existing
event-level temporal conflict detection benchmark**. The gap is real. The contribution is strongest
framed as:

1. the first event-level temporal conflict formulation + benchmark,
2. **granularity conflict** as a conflict type with no entity-KG counterpart,
3. the empirical finding that gold event graphs are consistent while *predicted* ones are not —
   which is what makes the task matter for IE rather than for KG curation.

Framing it as "PaTeCon applied to events" is the weakest available option and invites a
novelty rejection.
