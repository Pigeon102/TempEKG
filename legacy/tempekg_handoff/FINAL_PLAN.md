# TempEKG — Final decision document

Produced by workflow run `wf_504d3def-763` (2 hostile judges + synthesis) over the 12 recovered
results of run `wf_43a75668-138`. All five designs are now judged.

---

## ⚠ ERRATA — read before using any number from §0–§8

Two headline figures the plan puts **in the proposed abstract** are wrong. One is my fault: the
"shared-participant event pairs" counts I supplied in the FACTS block were inflated by a
double-count, and the plan inherited them.

**The bug.** My original count reset its dedup set inside the per-entity loop, so an event pair
sharing two or more participants was counted once per shared entity. **19.8 % of pairs share more
than one participant**, so the inflation was ~29 %.

| Quantity | Reported (wrong) | **Corrected** |
|---|---|---|
| Shared-participant event pairs | 274,525 | **212,743** |
| …that also carry a temporal relation | 139,093 | **106,340** |
| …as a share of shared-participant pairs | 50.7 % | **50.0 %** (conclusion unchanged) |
| Unique event–event temporally related pairs | — | **593,433** |
| `(T1,T2)` signatures at support ≥10 | 2,708 | **2,303** |
| `(T1,r1,T2,r2)` signatures at support ≥10 | 2,688 | **2,707** |

**Independent of my bug, the plan's reachability ceiling is computed against the wrong
denominator.** It states *"139,093 of 843,808 temporally-related event pairs (16.5 %)"*. But
843,808 is the count of **BEFORE relation instances including TIMEX endpoints** — not event–event
pairs. The correct statement is:

> **106,340 of 593,433 unique event–event temporally related pairs = 17.9 %**

Use 17.9 %, not 16.5 %. The qualitative claim (the entity-star projection reaches under a fifth of
the temporally-related pairs) is unaffected and if anything slightly stronger.

**Third figure, unverified.** The plan claims *"3,649 (5.4 %) arity-0 ERE events carry BEFORE/CONTAINS
edges"*. Measuring events with zero annotated arguments that carry ≥1 event–event temporal relation,
I get **2,974**, not 3,649. The definitions may differ (ERE events absent from MAVEN-Arg entirely vs
present-but-argument-less). **Recompute and pin the definition before this goes in the abstract.**

**What survives unchanged:** every consistency-audit number (0 BEFORE cycles, 100.0 % transitive
closure, ~72 contradictions, 1,638 subevent gaps), every TIMEX figure, the 44.9 % / 27.2 % / 27.9 %
anchoring split, the 17,102 multi-anchor events, the 652 projected properties, and the conclusion
that **type-level mining power is not the bottleneck** (2,303 and 2,707 signatures still clear
`θ_freq = 10` comfortably).

Verification scripts: `recount_pairs.py`, `recount_signatures.py`, `verify_plan_numbers.py`.

---

## Part 1 — The two late verdicts

### D-provenance-multiversion (PROV-ECKG)

```
feasibility_45d=4  novelty_coling=4  effectiveness=4  OVERALL=4

VERDICT:
MAJOR REVISION — descope hard. The schema work is the most competent Phase-2 engineering I have seen for this project, and two of its detectors (D1 STP, GRAN_EMPTY) are genuinely non-circular. But the design buys its headline contribution (the derivation axis / differential evaluation) with the two riskiest build steps (layer-2 trel_clf and a 4-day TIMEX normaliser measured at ~1 week), and its own cut line deletes exactly the thing the novelty claim rests on. As written it is a 35-40 person-day plan sold at 25, for one person, and the paper it produces is a resource/error-analysis paper whose method delta over Fan & Strube (Findings EMNLP 2025) is bookkeeping. Recommendation: ship L0 + L1 only, kill MaxSAT/SHACL/RDF/L2-trel_clf on day 1 rather than day 18, reinvest ~8 days into the granularity adjudication study and a measured L0 STP satisfiability audit, and make granularity the paper. That version is a plausible COLING short/resource accept; this version is a reject on either incompleteness (didn't land) or thin novelty (did land).

FATAL FLAWS:
- The audit's '0 conflicts in gold' is a BEFORE-cycle-only result over 843,808 pairs; the design's own translation (SIMULTANEOUS -> s=s AND f=f, OVERLAP -> a.s<b.s<a.f<b.f, plus absolute bounds b_lo<=e.s<=b_hi from 66,418 CONTAINS anchors) has never been run as a full STP on L0. With 9.9K SIMULTANEOUS + 9.9K OVERLAP annotated loosely and ~10-15% normalisation error on the anchors, a nontrivial fraction of L0 document-graphs will come back UNSATISFIABLE. The moment that happens, gold_status='gold_clean' stops being a free label and the entire differential evaluation column becomes noise. This is not hedged anywhere in the design and it is the single load-bearing untested assumption.
- The whole ordering track's signal exists only at layer 2. D1/D2 on L0 return, by the design's own measured facts, exactly zero rows (0 cycles, 0 symmetry violations, BEFORE 100% closed). Layer 2 requires a temporal-relation classifier trained from scratch (D17-20, 3.5d, no existing temporal component in any of the five repos) and is the FIRST item on the stated cut line. So the design's dominant conflict type is contingent on the step most likely to be cut, and the fallback (layer 3 blind, gold-free violation rates) is precisely Fan & Strube's published setting with no gold to compare against.
- The 'free labels' label extraction disagreement, not contradiction. gold_status='gold_clean' presumes gold completeness, which the design's own numbers refute: 1,638/12,019 subevent pairs (13.6%) lack the implied CONTAINS, and gold argument/relation recall is unmeasured. An L2 relation absent from L0 is scored SPURIOUS whether it is wrong or merely unannotated. The design names this risk and then builds the primary results table on it anyway.
- GRAN_EMPTY precision is structurally unfalsifiable at scale: there is zero gold TIMEX value supervision, so every flagged conflict is indistinguishable from a normalisation error by construction. The proposed 200 hand-labelled TIMEX values measure per-span normalisation accuracy (+/- ~6% CI), not conflict-level precision, and cannot support the headline claim that the flagged set contains genuine data conflicts.

FIXABLE:
- Move a full-point-graph STP satisfiability audit of L0 (with anchors, SIMULTANEOUS, OVERLAP) to day 3, before any layer-2 code. Report the per-document unsat rate. If it is above a few percent, relax SIMULTANEOUS/OVERLAP to non-strict and re-audit.
- Cut layer 2 and the trel_clf on day 1, not day 18. Keep L0 + L1 (gold triggers + predicted arguments) — L1 needs only inference on existing checkpoints and is the only noise level whose error process is genuinely low-risk.
- Cut D24 MaxSAT, the SHACL shape, the RDF 1.2 / qualifier serialisation, PseudoEntity clustering as a research component, and DuckPGQ. None carries a claim that survives review; together they are ~4-5 days.
- Rebudget TIMEX normalisation to the measured 7 days (not 4) and put stage 1 persistence before the offset bridge is fully green so the two can slip independently.
- Expand the TIMEX hand-label set to ~500 stratified by normalisation family (regex / refprop / gazetteer / unresolved) and report per-family accuracy with CIs; then report GRAN_EMPTY counts as 'flagged / adjudicated-genuine / normalisation-artefact / unknown' rather than as conflicts.
- Report all differential numbers restricted to align_method='trigger_offset_exact' only — as the risk section already says — and drop the overlap-matched rows entirely rather than as a sensitivity analysis.
- Collapse interval4 to (lo, hi, precision_set): with CONTAINS at 99% of anchoring mass, b_lo=f_lo and b_hi=f_hi for almost every event, so the four-endpoint quadruple is ornamental and costs schema surface across four layers.
- Separate the contradiction and incompleteness columns in every table from the first draft, and gate every conflict row on a temporal detector, never on the argument diff.
- Write the Fan & Strube / Kontrast differentiation paragraph in week 1 as the design says, and be prepared to move the angle if it reads thin — because it does.

PRIOR WORK UNDERCUTTING NOVELTY:
- Fan & Strube, Findings of EMNLP 2025 — Allen-algebra consistency over predicted MAVEN-ERE temporal relations. Same corpus, same relation family, same consistency notion. The stated delta ('a differential query between co-resident layers with per-statement provenance') is a storage and bookkeeping difference, not a method or a finding.
- Standard gold-vs-system alignment scoring in event extraction (ACE/ERE/RichERE scorers, gold-mention vs predicted-mention evaluation settings in coreference and relation extraction). The L0-vs-L2 diff with SPURIOUS/MISSING/ROLE_SWAP labels is an evaluation scorer materialised as a table; calling its output 'automatically labelled naturally distributed errors' does not make it new.
- PROV-O, nanopublications, and named-graph-per-extractor provenance in IE pipelines (and EventKG's own named-graph-per-source design, ESWC 2018 / SWJ 2019). Attaching (source, method, confidence) to extracted statements is fifteen-year-old practice; framing it as 'repurposing the bitemporal transaction axis' (ADBIS 2025, AeonG PVLDB 2024, Gradoop TPGM) is rebranding, and the bitemporal citations are decorative since no transaction-time semantics are used.
- PaTeCon / PaTeCon+ (AAAI 2023; arXiv 2312.11053) — reified statement store, trivalent logic over uncertain time, the three constraint families, and the support/confidence machinery are all adopted wholesale. What remains for Phase 2 is the projection and the indexes.
- Kontrast (arXiv 2607.25959) already names and quantifies granularity mismatch at 18.6%; the contribution reduces to inverting its recommendation, which is a stance, not a result, until the adjudication study is actually run.
- Bettini/Wang/Jajodia (AMAI 1998; AI 140, 2002), Euzenat (Comp. Intelligence 2001), Bettini & Mascetti (minimal periodic sets), Dyreson & Snodgrass (TODS 1998), Dechter/Meiri/Pearl (1991) — the entire temporal formalism is borrowed, as the design honestly states. Nothing in the interval/periodic-set/STP layer is claimable.
- HeidelTime CIR + narrative-domain reference-time propagation, and gold-span value-only normalisation (arXiv 2205.10399) — the normaliser is an acknowledged reimplementation, i.e. ~7 of 25 person-days buy zero novelty.
- WikiConflict (K-CAP 2025) and Wikidata edit-history refinement (arXiv 2210.15495) already establish 'errors from an independent error process' as the accepted design; co-residence in one store is an implementation detail of that idea.

STRONGEST DEFENSIBLE CLAIM:
Restricted to gold (plus, if it lands, gold-trigger/predicted-argument L1): an operational, trivalent adjudication of MULTI-ANCHOR TEMPORAL GRANULARITY in a text-grounded event KG. Concretely — on the 17,102 MAVEN events carrying >=2 CONTAINS anchors, define compatibility as periodic-set / precision-expanded intersection emptiness rather than precision difference, and report the measured three-way split into benign nested refinement, genuine empty-intersection conflict, and unknown, with each residual conflict attributed to the normalisation strategy that produced it (regex / reference-time propagation / gazetteer / unresolved) and validated against a stratified hand-labelled TIMEX sample. Two supporting claims come cheaply and are also defensible: (i) a measured audit showing that mining temporal constraint VIOLATIONS from a gold event corpus has almost no target (0 BEFORE cycles / 0 symmetry violations across 843,808 pairs; ~72 corpus-wide contradictions against 1,638 subevent incompleteness gaps), which reframes the task from contradiction detection to incompleteness detection and is a genuinely useful negative result for this literature; and (ii) an explicit statement of which tractable subalgebra the PaTeCon head-predicate set occupies — that `disjoint` puts it outside ORD-Horn, so dropping it yields a complete O(n^3) decision procedure — which, as the design notes, essentially no KG-conflict paper states. Everything involving the derivation axis, the multi-version store, and 'differential' evaluation should be demoted to a design section, not a claim.
```

### B-nary-hypergraph (HEDGE)

```
feasibility_45d=3  novelty_coling=4  effectiveness=4  OVERALL=3

VERDICT:
REJECT AS SCOPED; SALVAGEABLE ONLY BY AMPUTATION. The design is the most intellectually serious of the plausible Phase 2 options and its honesty (two-tier loss claim, resolve-then-STP complexity decision, refusal of the first-to-formalise claim, explicit gives-up list) is above the norm for this venue. But it fails all three lenses as written. Feasibility: 38 pd is really 55-60 for one person who also writes the paper; D13-D15, D16-D18, D24-D27 and the annotation study will each slip, the D21 teammate-unblocking gate goes with them, and the plan silently rewrites Vinh's phase. Novelty: the headline reduces to a dataset-specific loss count on a point (binarisation loses information) that StarE and the hyper-relational KG line settled, with the frame-and-null insight already implemented inside the team's own PAIE/DEEIA code, and the 'theorem' is Helly 1923. Effectiveness: gold supplies zero granularity positives by construction, the ordering side has ~72 and no producer for the predicted layer that was supposed to fix that, and the flagship 7,235-event width family looks like a misreading of CONTAINS. The surviving path is narrow: build T1-T7 plus T11 plus token_index, generate the PaTeCon view and the projection_loss table, ship ONE null-slot constraint family, and publish the loss audit plus the two substrate findings as an analysis/resource paper -- roughly 18-22 pd, which fits. Everything from D24 onward except the null family, and all of D31-D35, should be cut today rather than at day 25 when the design itself concedes the choice is irreversible.

FATAL FLAWS:
- THE METRIC_WIDTH FAMILY IS PROBABLY A SEMANTIC ARTEFACT, AND IT IS THE FALLBACK THE WHOLE DESIGN RESTS ON. The design turns a DURATION TIMEX linked to an event by CONTAINS into a two-sided width constraint (f-b in [3650,3653] for 'ten years'). CONTAINS(timex, event) means the temporal extent named by the TIMEX CONTAINS the event, i.e. it licenses only w <= 3653, an UPPER bound. Under the correct reading, the flagship second witness ('1778' gives w<=364; 'ten years' gives w in [3650,3653]) is trivially SAT, not UNSAT, and the 7,235-event 'non-interval width constraint' family collapses to a set of loose upper bounds that are (a) intervals in disguise for satisfiability purposes and (b) almost never jointly violated. The design's own stated risk gate ('if periodic sets slip, the Helly claim survives on width alone') therefore has no floor. Nothing in the 45-day plan validates the CONTAINS/DURATION semantics against annotation guidelines or a sample; a reviewer who checks the MAVEN-ERE guideline kills the headline in one paragraph.
- THE k-WISE DETECTOR HAS NO GOLD POSITIVES AND CANNOT HAVE ANY. Gold is 100% transitively closed with ~72 corpus-wide contradictions; multi-anchor events are Stubbs-Pustejovsky nested containers that the design itself mandates be adjudicated BENIGN. A genuine three-way-empty periodic core requires the annotators to have attached mutually unsatisfiable anchors to one event in one document -- exactly the error MAVEN's consistency-enforcing annotation excludes. Of the periodic families the design cites, the 909 (year, yearless) events resolve pairwise to a singleton and need no k-wise test at all; only the 448 three-kind events could in principle fire, and only when the weekday disagrees with the resolved date, which under correct gold happens ~never and under an unsupervised normaliser happens ~6/7 of the time. Net: every UNSAT the detector emits on gold is a normalisation error. The paper's positives are therefore 100% synthetic, produced by the same author's perturbation script, and the Helly theorem's operationalisation is demonstrated on zero naturally occurring instances.
- THE 'DE-ORPHANING PHASE 1' CLAIM IS A SCHEMA COLUMN WITH NO PRODUCER. The layer axis is presented as the mechanism that (i) rescues Phase 1 and (ii) supplies the ordering detector's evaluation substrate, because gold offers ~72 targets. But no build step in D1-D38 runs PAIE/DEEIA/SCPRG over the eval documents, reconciles predicted spans to entity ids or TIMEX links, or populates a single pred:% row. The ordering half of the paper thus has, by the design's own admission, no evaluable data and no plan to create it. This is not a risk item; it is a missing 4-6 person-day subproject.
- 38 PERSON-DAYS IS A FICTION, AND THE D21 GATE THAT PROTECTS TWO TEAMMATES IS INSIDE IT. D1-D20 alone is 20.5 pd and must land in 21 calendar days at 100% utilisation, with zero allowance for paper writing (8-10 pd for a first author), zero for the two-annotator Krippendorff study D10-D12 assumes (which pulls Vinh or Nhan, forbidden by the brief), and zero for the integration debugging the plan itself reserves at the far end. Realistic total is 55-60 pd. The gate slips to ~day 27-30, at which point Nhan's baseline track starts with under two weeks left and the HyPaL matcher (D32) is useless.

FIXABLE:
- Cut D31-D33 entirely (RDF 1.2 / pyoxigraph / htkg.jsonl / named graphs per layer). It is ~3 pd of serialisation with no experiment attached; the design already concedes no released model consumes the native store and that exporting reintroduces the confound. Same for D34-D35's Croissant/HuggingFace/Datasheet package -- ship Parquet plus a MANIFEST and move on.
- Cut DuckPGQ. BEFORE-closure over ~18 events/doc is a 30-line transitive closure; the design already says so. Declaring an incomplete engine dependency buys nothing but a reviewer question.
- Reduce HyPaL from a language to one atom family. The null() family is the only one that is both Tier-1 and cheap (the bitmask is already computed at D5-D7). card/sdisj/ssub/seq/kwise cost the matcher's complexity and inflate the candidate space to ~1e7, gutting FDR power precisely where the novelty lives. One family, exact counts, honest denominator = a defensible table; four families at 1e7 candidates = nothing survives BH.
- Fix the three support denominators down to two (event, document). supp_activation is only meaningful if the activation semantics are pinned to a DECLARE template, and the design never states which templates; a reviewer will ask and there is no answer in 45 days.
- Validate the DURATION/CONTAINS reading in week 1, before D13-D15 is scheduled, and re-derive the non-Helly prevalence from the corrected semantics. If it collapses (likely), reframe the contribution around Tier-1 nullity plus arity-0 invisibility, which do not depend on time semantics at all.
- The numbers in the Helly section are not independently sourced and one is suspicious: '15.9% (2,742 events) carry a yearless-date or weekday anchor' is exactly the fact sheet's count of events with >=4 CONTAINS anchors. Either the derivation coincidentally matched or it was recycled. Recompute and report the query, or a reviewer who reads both tables will treat the whole prevalence section as unverified.
- Budget the annotation study properly or drop the Krippendorff claim. 200 anchors x 2 annotators, guideline writing, and adjudication of k-wise cores (which the design admits is harder than pairwise) is 3-4 pd across two people, and the brief forbids conscripting them.
- Stop advertising 'Phase 3 becomes serialisation-plus-baseline-generation'. That is a unilateral rewrite of Vinh's phase, which the brief explicitly penalises. If the projection view is generated by Phase 2, Vinh needs a different owned contribution negotiated now, not a demotion discovered on day 21.
- Replace 'perturbation recall' with a precision-first protocol. Shifting a year so the intersection empties is detected by construction; recall will be ~100% and carries no information. The only informative numbers are (a) false-positive rate on the 17,102 naturally nested events and (b) human-adjudicated precision on flagged cores. Lead with those.

PRIOR WORK UNDERCUTTING NOVELTY:
- Template-based EAE (PAIE, Ma et al. ACL 2022; DEEIA; TSAR) -- the team's own Phase 1 code. These models are handed the declared role frame per event type as a prompt template and explicitly emit 'None' for unfilled slots. 'MAVEN-Arg ships a per-type arity signature' and 'a declared-but-empty slot is a positive fact' are both operating assumptions of the extractors already in the repo, not discoveries. This is the single most damaging undercut because it is inside the project.
- StarE (Galkin et al. EMNLP 2020), HINGE, NaLP, m-TransH, HypE, and the RAM/GRAN line -- ten years of results establishing that binarising n-ary facts loses information and costs accuracy. The design cites StarE's +25 MRR as its own licence, which concedes the general point is settled; what remains is a dataset-specific loss count.
- HTKG (Ding et al. Findings EMNLP 2024), Wiki-hy / YAGO-hy, HyperMLN, and n-ary/hyper-relational rule learning (e.g. Ho et al. RuLES; AnyBURL/AMIE+ variants over qualifier graphs) -- 'a pattern language over sorted, labelled n-ary slots with cardinality and set atoms' is a recognisable point in this space, not a first. HyPaL reads as AMIE with sorted slots plus a satisfiability oracle.
- Graph Entity/Generating Dependencies (Fan & Lu; GGDs, arXiv 2403.17082) and denial constraints / conformance constraints (SIGMOD 2021) -- the design cites all three, which makes REQUIRE-heads and cardinality atoms adopted machinery rather than a new language.
- Euzenat (Computational Intelligence 2001) and Bettini, Wang & Jajodia (AMAI 1998; AI 2002) -- multi-granularity temporal reasoning, periodic sets, and the NP-hardness boundary are all theirs. Helly number 2 for intervals is a textbook fact (Helly 1923); presenting 'intervals are Helly-2, periodic sets and metric width are not' as a theorem invites the response that the paper proved nothing and only counted rows.
- Stubbs & Pustejovsky narrative containers; TimeML/HeidelTime (Strotgen & Gertz) narrative reference-time rule; TIMEX3 -- the entire normalisation and nesting story is a reimplementation, correctly framed as such by the design, which leaves it as infrastructure not contribution.
- PaTeCon / PaTeCon+ (AAAI 2023; arXiv 2312.11053) and Soulard, Sais & Raad (ESWC 2025) -- an area chair will read 'declared frames + precision codes + PaTeCon-style trivalent support, run on MAVEN' as 'we applied PaTeCon to events with a richer store', and the design's own baseline design (their code, unchanged, on our generated view) makes that framing easy.
- Fan & Strube (Findings EMNLP 2025) on the same dataset -- Allen consistency over MAVEN-ERE. The design reuses their point decomposition and concedes the contrast is 'pairwise logical closure vs type-level statistical constraints'. Since the type-level constraints have ~72 gold targets, the reviewer's likely conclusion is that the existing instance-level approach is the one that fits this data.
- EventKG / SEM, ECS-KG (DKE 2025), ChronoGrapher (SWJ 2025), ASER -- event-centric temporal KGs with time on the event resource. 'Time hangs on the event, not on each statement' is EventKG's design, cited as such.

STRONGEST DEFENSIBLE CLAIM:
A measured, per-event audit of what the project's own mandated entity-as-subject binary projection of MAVEN destroys, shipped as an automatically generated loss table alongside a generated PaTeCon-compatible view: ~143K declared-but-empty role slots (37.7% of declared slots) that projection cannot distinguish from unannotated slots, 3,649 (5.4%) arity-0 ERE events that carry BEFORE/CONTAINS edges yet emit no (entity, EventType#Role, event) statement and are invisible to a projected miner, and 17,102 events whose multi-anchor sets are collapsed to one interval. Paired with two structural findings about the substrate that no prior MAVEN paper states -- that EAE structurally cannot supply event time (4.97% argument/TIMEX overlap, no When role), and that with 0/68,348 entities crossing documents all constraints are necessarily type-level and all matching is intra-document -- this is a defensible resource-and-analysis contribution. It does not depend on the Helly argument, on DURATION semantics, on any mined constraint reaching significance, or on a single detected conflict.
```

---

## Part 2 — Final plan

# TempEKG — FINAL DECISION DOCUMENT
**For: Nhut (Phase 2, Graph Construction) · Date: 28 Aug 2026 · 45 days to COLING 2027 (12 Oct 2026)**

---

## 0. HOSTILE NOVELTY PASS (done first, as instructed)

I tried to kill every novelty claim in all five designs with named prior work. Nineteen of twenty died. Here is the one that survived, and why the others did not.

**SURVIVOR — the entity-level→fact-level degeneracy proof.**

> On a graph where 0 of 68,348 entities appear in more than one document, PaTeCon's headline contribution — ENTITY-level support/confidence, where an entity counts as positive only if *all* of its subgraphs are positive — provably collapses to fact-level confidence. Every entity's statement set lies inside one document, under one annotated timeline, with mean 3.15 statements (max 59). PaTeCon+ reports that fact-level confidence yields ~1.8× the constraints and ~38× the conflicts of entity-level on WD27M; that ratio is their central empirical contribution. On our substrate the ratio is bounded near 1 by construction.

Why this survives:

- **No prior paper can have stated it.** PaTeCon/PaTeCon+ (WD27M, FB37M), Soulard/Saïs/Raad (ESWC 2025, Wikidata entity timelines), TISCO, TeCre all operate on globally-recurring encyclopaedic entities. The degeneracy is a property of document-local entities, and nobody has run this family of miner on a document-local graph.
- **It is not a representation claim, a formalism claim, or a stance.** It is a theorem about the substrate plus a measured ratio. Bettini/Euzenat/Dechter/Nebel/Krokhin cannot touch it — it is not about time. Kontrast cannot touch it — it is not about granularity. Fan & Strube cannot touch it — it is not about Allen consistency.
- **It contradicts, rather than extends, the parent paper's headline.** That is the strongest possible position: a reviewer who knows PaTeCon well is the reviewer most likely to find it interesting.
- **It requires zero conflicts to exist, zero normalisation, zero annotation, zero perturbation.** It is computable on gold in one afternoon. Every other design's headline was contingent on a component the hostile judges showed would not land.

Why the others failed:

| Claim | Killed by |
|---|---|
| A1: first document-grounded HTKG with gold n-ary roles | MAVEN-Arg + MAVEN-ERE themselves; RED (O'Gorman et al. 2016) has all four layers *with* normalised TIMEX3 values |
| A2: first release with (interval, precision, layer, confidence) | Schema assembly; every component off-the-shelf (EventKG, HTKG, Wikibase, ADBIS 2025) |
| B: Helly argument / k-wise granularity | Helly 1923; and the DURATION-width family that carries it rests on a misreading of `CONTAINS` (see §3.4) |
| B: HyPaL n-ary constraint language | StarE/HINGE/NaLP/GRAN line; GGDs; and PAIE/DEEIA already consume declared role frames with `None` slots — inside the team's own repo |
| C: lexicographic (day, ε) weight group | Dutertre & de Moura, CAV 2006 — delta-rationals. Standard in every QF_IDL solver, including the Z3 the design delegates to |
| C: STP over event endpoints | Bramsen 2006, Chambers & Jurafsky 2008, Denis & Muller 2011, Do/Lu/Roth 2012, Leeuwenberg & Moens 2018, CAEVO 2014 |
| D: derivation axis / multi-version store | PROV-O, nanopublications, EventKG named-graph-per-source; the L0/L2 diff *is* an ACE/ERE scorer materialised as a table |
| E: ordering-conflict factorisation through the join granularity | Euzenat 2001 upward conversion + a consistency re-check. Two lines of a 25-year-old operator |
| All: "granularity as signal, not noise" (inverting Kontrast) | A stance, not a finding, until the adjudication is shown to be *accurate* — and with zero gold TIMEX values it cannot be |

**The consequence for the plan is structural, and all five designs missed it:** every design bet its headline on detecting conflicts in a corpus measured to contain ~72 of them. The survivor does not. **Build the paper on a result that does not require conflicts to exist.**

---

## 1. COMPARISON TABLE

| | A · StarCast-ECKG | B · HEDGE/HyPaL | C · ECN (STP) | D · PROV-ECKG | E · GLANCE |
|---|---|---|---|---|---|
| **Feasibility (45d)** | 5/10 — 18d sold, 26–30d real; day-15 freeze with 1d buffer against 3 slip sources | 3/10 — 38d sold, 55–60d real; D21 unblock gate inside the fiction | 5/10 — 20d sold, 28–32d real; normaliser 4d vs measured 7d, on critical path | 4/10 — 25d sold, 35–40d real; L2 trel_clf is new model training at the tail | 4/10 — 26d sold, ~34d real; S2+S7 under-scoped by ~5d, buffer spent twice |
| **Novelty** | 4/10 — 1 repackaging, 1 schema-assembly, 1 disclaimed, 1 real measurement | 4/10 — Helly is 1923; frame/null insight is inside own repo | 3/10 — ε device is CAV 2006; endpoint consistency is a 20-yr NLP line | 4/10 — provenance layering is PROV-O + a scorer | 5/10 — most honest; factorisation is Euzenat applied once |
| **Effectiveness** | 4/10 — non-circular arm predicted by the design itself to yield ~0 positives | 4/10 — k-wise detector has *no* gold positives possible; flagship family probably an artefact | 6/10 — best; two genuinely non-circular detectors, but signal lives only at the unbuilt L2 | 4/10 — free labels label extraction disagreement, not contradiction | 4/10 — S/N ~1:20 (≈1,450 normaliser artefacts vs ≈70 genuine) |
| **Effort (sold / real)** | 18 / 26–30 | 38 / 55–60 | 20 / 28–32 | 25 / 35–40 | 26 / 34 |
| **Gives up** | Representational novelty (deliberately); hollows out Vinh's phase | Any evaluation-protocol improvement; the free ride on PaTeCon's code | Data-description/resource framing; Nhan contributes to no reported number | Temporal semantics depth; its own cut line deletes its novelty claim | 99% of the data mass (1.04M BEFORE + 152K CONTAINS vs ≥38K anchor pairs); splits into two papers |
| **Overall** | **4.0** | **3.0** | **4.5** | **4.0** | **4.0** |

Read the column of judges' *surviving claims*, not the column of scores: four of five judges independently landed on **measurement/audit**, and A's judge named the exact survivor from §0.

---

## 2. RECOMMENDED DESIGN

### Primary: **A, amputated to ~55% of its scope, retitled around Claim 4.** Call it `eckg/v1` + **the Port Audit**.

**Why A and not C** (which scored highest). C is better engineering and has two genuinely non-circular detectors, but (i) its two advertised novelties are both dead — ε is Dutertre & de Moura, endpoint consistency is 20 years of NLP — (ii) every headline number lives at layer L2, which requires training a MAVEN-ERE temporal-relation classifier that does not exist in any of the five repos, and (iii) it quarantines Nhan's mined constraints in a completeness-free Tier 2 so Phase 4 contributes to no reported result. A is the only design whose surviving claim is the one that cannot be undercut, and A is the only design that keeps PaTeCon in the critical path — which is what makes Nhan's phase load-bearing.

**Why not simply "A as written."** A's own value proposition — that the granularity arm buys a non-circular evaluation — is false, and A's judge is right: A pre-commits to predicting that CONFLICT is near-empty, then makes it the headline. The amputation is: **move the headline off conflict detection and onto the constraint-mining port audit.** Then granularity becomes a secondary section whose emptiness is a *reported characterisation*, not a failed experiment.

### The retitled paper

> **Porting Mined Temporal Constraints to Document-Local Event Graphs: A Transferability Audit with Soundness Testing**

Three results, in order of robustness:

1. **The pruning ladder** (gold-only, no conflicts needed): how many PaTeCon-style temporal constraints on an event KG survive (a) document-clustered support, (b) BH-FDR ≤ 0.05, (c) the Martin et al. (PVLDB 2025) atomicity/soundness test. Reported as N₁→N₄ with the survival fraction.
2. **The degeneracy + reachability ceiling** (§0's survivor): entity-level ≡ fact-level on this substrate, measured ratio vs PaTeCon+'s 38×; and the entity-star projection structurally reaches only 139,093 of 843,808 temporally-related pairs (16.5%), with 59.9% of arguments degree-1 bare spans generating no mineable subject and 3,649 (5.4%) arity-0 ERE events invisible to any projected miner.
3. **Two substrate audits** nobody has run: the **full-STP satisfiability rate of gold** (the published "0 BEFORE cycles" is BEFORE-only; nobody has closed the network *with* the 66,418 anchor bounds + 9.9K SIMULTANEOUS + 9.9K OVERLAP), and the **4-verdict granularity characterisation** of the 17,102 multi-anchor events with a human-audited normaliser.

### Grafts, and exactly why

**From B (2 grafts, ~1.5d):**
- `null_signature` / `slot_signature` bitmasks + the **arity-0 event count**. Rationale: these are computed free at build time and they *quantify* the reachability ceiling, which is result #2. Take the measurement, discard HyPaL, Helly, and the language.
- **The DURATION correction as a stated finding.** B compiles `CONTAINS(timex_DURATION, e)` into a two-sided width constraint. That is wrong: `CONTAINS(t,e)` means *t's extent contains e*, so "ten years" licenses only `w(e) ≤ 3653`, an upper bound. Ship `width_lo=0, width_hi=hi` and say so in a footnote. This kills B's flagship 7,235-event family and is worth one honest sentence.

**From C (3 grafts, ~3.5d):**
- **The compilation table** (relation → difference constraints) and **Floyd-Warshall over day-chronon endpoints** as the exact, mining-free, fully-explainable baseline detector. This is the fairest floor for Nhan's mined-constraint claim and costs ~4.4×10⁸ integer ops corpus-wide.
- **The explicit ORD-Horn positioning paragraph** — that `disjoint` is `(f_i<b_j) ∨ (f_j<b_i)`, a genuine disjunction, hence outside ORD-Horn, hence dropping it yields a *complete* O(n³) procedure (Nebel & Bürckert JACM 1995; Krokhin/Jeavons/Jonsson JACM 2003). One paragraph, cheap rigour, essentially no KG-conflict paper writes it.
- **Strict-inequality handling** via packed `(days, ε)` int64 — kept as an *implementation note citing Dutertre & de Moura CAV 2006*, never as a claim.

**From D (1 graft, ~2d):**
- **The `layer` column, populated with L0 (gold) and L1 (gold triggers + PAIE/DEEIA-predicted arguments) only.** L1 needs inference on existing checkpoints, not new training. It un-orphans Phase 1 at real cost of 2 days and gives an argument-side error track that feeds the property-vocabulary and reachability results. **L2 (predicted temporal relations) is cut on day 1, not day 18.**

**From E (4 grafts, ~1d of writing + discipline):**
- The **explicit non-claims paragraph** (we do *not* claim to be first to formalise multi-granularity inconsistency — Bettini/Wang/Jajodia AMAI 1998, AI 2002; Euzenat 2001).
- **Trivalent discipline with a mandatory UNDECIDABLE verdict whose rate is reported.**
- **Frozen constraint set + SHA-256 committed before any error exists** (holdout rule mining, arXiv 1110.6652).
- The **"Claims Supported / Claims Not Supported"** subsection (NeurIPS 2026 E&D reviewing guidelines) — one page that pre-empts the strongest rejection reason.

**From the research sweeps (3 grafts, Nhan-owned, ~6d):**
- **Atomicity/soundness test** (Martin et al., PVLDB 18, 2025): Beta-Bernoulli log-odds conditional-independence test at α=0.01. Reported effect in the source domain: >95% false-DC reduction with essentially no true-constraint loss.
- **BH-FDR ≤ 0.05** replacing `support=10 / conf=0.9` as a *reported* threshold.
- **Document-clustered support** — support counted over documents, not over subject-pairs. This is forced by the substrate (a war article yields dozens of correlated Attack/Killing stars) and it maps onto DECLARE/MINERful's trace-vs-activation denominator, giving a 20-year-old citable definition for the denominator PaTeCon fudges.

**Nobody is demoted.** Vinh gains a real owned contribution (projection *ablation* producing the degeneracy measurement + the annotation protocol + the LLM baseline). Nhan gains the paper's spine.

---

## 3. CONCRETE PHASE-2 SPEC FOR NHUT

### 3.0 Non-negotiable facts to announce on day 1

- **The blind test split cannot be a graph.** Both `EE/MAVEN-Arg/test.jsonl` and `MAVEN_ERE/test.jsonl` carry `event_mentions` (mention-level ids), not `events` (EVENT_ cluster ids). No EVENT_ ids ⇒ no Arg↔ERE join ⇒ no event nodes. The MINE/EVAL split is **document-disjoint inside the 3,623 gold docs: 2,900 MINE / 723 EVAL**, seed 20261012, hashed into the manifest on day 3. The 857 blind docs get `split='BLIND'` and are used **only** for gold-free consistency metrics after L1.
- **Corpus-level counts are ASSERTED; split-level counts are REPORTED.** "652 distinct properties" holds corpus-wide and *will fail* on an 80% document split. Same for 44.9% tight / 27.2% loose / 27.9% none, which are properties of the gold anchor graph and change after an 85–90%-coverage normaliser. Two separate assertion classes in the manifest.

### 3.1 Schema — 7 core tables + 2 derived (down from A's 10)

Physical layout: `C:\Reseach_Quang\tempekg\out\v1\*.parquet` + `manifest.json` (per-file SHA-256, row counts, git commit, split hash) + `eckg.duckdb` (views only). Day chronon = proleptic Gregorian ordinal (`date.toordinal`); `NEG_INF = -9000000`, `POS_INF = 9000000` (real ordinals span 1..3652059).

```sql
-- 1
documents(doc_id PK, title, n_tokens, n_sent,
          split VARCHAR,            -- 'MINE'|'EVAL'|'BLIND'
          has_gold_args BOOLEAN, ref_time_chain VARCHAR)  -- JSON [[sent_id, timex_id],...]

-- 2
events(event_id PK, doc_id, event_type, event_type_id, n_mentions,
       first_sent_id, first_tok_start, first_tok_end, trigger_words,
       in_arg BOOLEAN, in_ere BOOLEAN,     -- 739 ARG-only; 3,649 ERE-only arity-0
       frame_arity TINYINT, filled_arity TINYINT,
       slot_signature BIGINT, null_signature BIGINT)   -- GRAFT FROM B

-- 3
entities(entity_id PK, doc_id, entity_type, n_mentions, canonical_mention,
         mention_offsets, n_events INT)     -- 16,284 rows have n_events>=2

-- 4  the sVertex payload; NO time of its own
participations(stmt_id PK, doc_id, event_id, event_type, role, role_id,
               filler_kind VARCHAR,          -- 'entity' | 'span'
               filler_id, filler_type,
               span_content, span_char_start, span_char_end, overlaps_timex BOOLEAN,
               property VARCHAR,             -- event_type||'#'||role, PRE-MATERIALISED
               layer VARCHAR DEFAULT 'L0',   -- 'L0'|'L1'   (GRAFT FROM D)
               conf DOUBLE DEFAULT 1.0)

-- 5
timex(timex_id PK, doc_id, sent_id, tok_start, tok_end, surface, timex_type,
      cir_value VARCHAR,        -- HeidelTime-style: '1815','UNDEF-year-08-29','UNDEF-REF-plus-1-day'
      value VARCHAR,            -- TIMEX3/ISO-8601 profile with x/X: '1815','1815-08-29','XXXX-08-29'
      precision SMALLINT,       -- Wikibase: 7 cent, 8 dec, 9 yr, 10 mo, 11 day; 0 = unresolved
      lo_day BIGINT, hi_day BIGINT,
      width_lo BIGINT, width_hi BIGINT,   -- DURATION only; width_lo ALWAYS 0 (see 3.4)
      resolver VARCHAR,         -- 'regex'|'refprop'|'gazetteer'|'unresolved'
      anchor_timex_id VARCHAR)  -- ISO-TimeML anchorTimeID for the refprop family

-- 6  1:1 with events
event_time(event_id PK, doc_id, layer,
           b_lo BIGINT, b_hi BIGINT, f_lo BIGINT, f_hi BIGINT,
           width_lo BIGINT, width_hi BIGINT,
           precision_set VARCHAR,     -- sorted JSON list, e.g. '[9,11]'  <- MAKE-OR-BREAK COLUMN
           precision_eff SMALLINT, n_anchors SMALLINT,
           anchor_class VARCHAR,      -- 'TIGHT'|'LOOSE'|'NONE'
           gran_verdict VARCHAR,      -- 'REFINEMENT'|'COMPAT_NONCHAIN'|'CONFLICT'|'UNDECIDABLE'
           gran_witness VARCHAR,      -- JSON proof a human checks in 10s
           multi_day_flag BOOLEAN,    -- durative-event artefact candidate
           stp_status VARCHAR)        -- 'SAT'|'UNSAT'|'UNKNOWN' from the document network

-- 7
event_relations(doc_id, layer, src_event_id, dst_event_id, rel_type, rel_family,
                src_kind, dst_kind,   -- 'event'|'timex'
                in_core BOOLEAN)      -- FALSE for the 1,638 subevent-implied CONTAINS

-- DERIVED (regenerable by SQL, but released)
pair_signatures(property_1, property_2, event_type_1, event_type_2,
                n_pairs, n_docs INT,          -- <-- n_docs IS THE SUPPORT DENOMINATOR
                n_with_temporal_rel, n_both_timed, n_either_unknown,
                cnt_before, cnt_contains, cnt_simultaneous, cnt_overlap,
                cnt_begins_on, cnt_ends_on, cnt_none)

projection_loss(event_id, doc_id, n_declared_empty_slots, n_span_fillers,
                is_arity0, n_anchors_collapsed, reaches_entity_star BOOLEAN)
```

**Cut from A:** `unlinked_spans` (folded into `participations`), `property_marginals` (a view over `pair_signatures`), `token_index` (built lazily, half a day, only for the 4.97%/13.8% overlap report).

### 3.2 Interval representation — exact

Four-endpoint quadruple over a day chronon, per event and per layer:

```
E(e) = ⟨[b_lo, b_hi], [f_lo, f_hi]⟩,  all int64 day ordinals
```
Semantics (Dyreson & Snodgrass, TODS 23(1) 1998; IE precedent Reimers et al. ACL 2016, arXiv 2008.06452): the event began somewhere in `[b_lo,b_hi]` and ended somewhere in `[f_lo,f_hi]`. A determinate day-level event has `b_lo=b_hi=f_lo=f_hi`. This one form subsumes all three measured populations — TIGHT (44.9%), LOOSE (27.2%), NONE (27.9%, all four sentinels) — with no special-casing, and degrades to PaTeCon's `(start, finish)` by a rename.

Construction rules (deterministic, ~120 lines):

| Anchor | Effect |
|---|---|
| `CONTAINS(t,e)`, t window `[lo,hi]` | `b_lo ← max(b_lo,lo)`; `f_hi ← min(f_hi,hi)`. **Outer bound only** — never touches `b_hi` or `f_lo`. This is why 66,418 CONTAINS anchors (≈99% of mass) give LOOSE unless the anchor is day-precision. |
| `SIMULTANEOUS(t,e)` (496) | `b_lo=b_hi=lo`, `f_lo=f_hi=hi` |
| `BEGINS-ON` (122) / `ENDS-ON` (39) | set the b- or f-pair. Recorded, never mined — too rare to learn. |
| DURATION via CONTAINS | `width_hi ← min(width_hi, hi)`, **`width_lo` stays 0**. Endpoints untouched. |
| Coarse anchor after fine | intersected, never overwritten |

**Granularity is stored separately and is never recoverable from the interval.** `'1815'` → `(value='1815', precision=9, lo=662907, hi=663271)`; `'29 August'` unresolved → `(cir_value='UNDEF-year-08-29', value='XXXX-08-29', precision=11, resolver='refprop')`. If you normalise `'1815'` to `[1815-01-01,1815-12-31]` and keep nothing else, granularity conflict becomes ordinary interval containment and the second conflict type ceases to exist. `precision_set='[9,11]'` is what survives that collapse.

**CUT: the minimal-periodic-set library.** All three designs that included it (B, C, E) had their judges flag it as the highest-variance item (3d budgeted, 5–6d real, no reference implementation). It buys handling for ~100 surfaces out of 20,827: yearless dates ("September 11" ×24, "August 31" ×17), weekdays ("Sunday" ×21). Replace with **single-candidate reference-time resolution**: propagate the last-mentioned DATE, instantiate the missing field, done. If more than one candidate year is plausible, emit `resolver='unresolved', precision=0` → UNDECIDABLE. **Saves 4–5 days and removes the correctness time-bomb.** Bettini & Mascetti is cited as the general formalism we deliberately restrict away from.

### 3.3 STP compilation (the mining-free baseline detector)

Two point variables per event (`b_e`, `f_e`), per document, per layer. Every constraint is a difference constraint ⇒ Simple Temporal Problem (Dechter/Meiri/Pearl AI 1991) ⇒ Floyd-Warshall decides consistency **completely** in O(n³); conflict = negative cycle.

```
AXIOM(e)          : b_e ≤ f_e
BEFORE(i,j)       : f_i − b_j ≤ (0,−1)        -- strict at ε, ZERO days
CONTAINS(i,j)     : b_i − b_j ≤ 0 ; f_j − f_i ≤ 0
SIMULTANEOUS(i,j) : b_i=b_j ; f_i=f_j
OVERLAP(i,j)      : b_i − f_j ≤ 0 ; b_j − f_i ≤ 0     -- INTERSECTION NON-EMPTY ONLY
BEGINS-ON / ENDS-ON : b or f pair equality
ANCHOR CONTAINS(t,e) : b_e ≥ lo ; f_e ≤ hi
SUBEVENT-implied CONTAINS : in_core = FALSE     -- 1,638/12,019 = INCOMPLETENESS, ablatable
```

Two rulings, both taken from the hostile verdicts:
- **`OVERLAP` is compiled as intersection-non-empty, not `b_i<b_j<f_i<f_j`.** MAVEN's OVERLAP is vaguer than Allen `o`; over-committing manufactures conflicts. (E's reading; C's was wrong.)
- **Strictness lives in the ε component only.** Non-strict makes every BEFORE cycle sum to zero and be satisfied by point collapse — a systematic false negative on the target class. Strict-at-day-resolution makes BEFORE pairs sharing a day-level anchor spuriously UNSAT, and there are 1.04M BEFORE edges against 66,418 anchors. Implement as packed `int64 = d·2²¹ + k`, `|k| < 2²⁰`; **cite Dutertre & de Moura, CAV 2006. Do not claim it.**

`disjoint` is excluded from the head language; the paragraph explaining why (ORD-Horn) is in §2's graft list.

### 3.4 Granularity adjudication — 4 verdicts, one flag

Substrate: 17,102 events with ≥2 CONTAINS anchors (2:10,653 · 3:3,707 · ≥4:2,742). All anchors of one event in one document are **CONJUNCTIVE** — that is what keeps the class well-posed. Cross-layer disagreement is disjunctive and produces a `layer_disagreement` row, never a conflict.

| Verdict | Condition |
|---|---|
| `REFINEMENT` | anchors form a ⊆-chain by precision and `⋂ ≠ ∅` — **the normal case**, Stubbs & Pustejovsky narrative containers |
| `COMPAT_NONCHAIN` | `⋂ ≠ ∅` but not a chain (e.g. "November 1778" + "the winter") |
| `CONFLICT` | `⋂ = ∅`, all contributing anchors resolved |
| `UNDECIDABLE` | any contributing anchor has `precision=0` / `resolver='unresolved'` |

**Never flag on precision difference.** That rule would be almost pure false positive — the failure Kontrast quantified at 18.6%.

`multi_day_flag = TRUE` when two disjoint day-precision anchors sit on an event whose type is in a curated durative set (`Military_operation`, `Hostile_encounter`, `Process_start`, `Besieging`, …). A's judge is right that CONFLICT will be dominated by three artefact populations — durative events, over-merged MAVEN coreference clusters, and loose narrative-container attachment. **100% of the CONFLICT set is hand-adjudicated into {genuine, normalisation error, coreference error, durative artefact} with a witness table.** That is the only defensible precision number this arm can produce, and it is a deliverable, not a mitigation.

**Worked example (real, verified).** Doc `79e2767b814f136745e35123957316b3` ("1815 North Carolina hurricane"), `EVENT_a0b68c8ac4f38c6bcfafdab518b24bd8`, type `Arriving`, trigger "arriving". Anchors: `'29 August'` (`cir_value='UNDEF-year-08-29'`, precision 11) and `'1815'` (precision 9). Reference-time propagation resolves the year-less date against the last-mentioned DATE (`1815`) → `1815-08-29`. Intersection with `[1815-01-01, 1815-12-31]` = singleton `{1815-08-29}` ⇒ **`gran_verdict='REFINEMENT'`**, `precision_set='[9,11]'`, `b_lo=b_hi=f_lo=f_hi=D(1815-08-29)`, `anchor_class='TIGHT'`. Note this example needs no periodic-set machinery whatsoever — it validates §3.2's cut.

### 3.5 Interface to Phase 3 (Vinh)

Phase 2 **owns and ships** the projection function; Phase 3 consumes and *ablates* it.

```python
tempekg.project.to_patecon(
    conn, split='MINE', layer='L0', subject_mode='entity',   # 'entity' | 'event'
    out_dir=..., include_unknown=True, min_subject_degree=2) -> ProjectionReport
```
writes exactly three files:

```
{split}.facts.tsv      S \t P \t O \t start \t end                    # PaTeCon native, unchanged
{split}.types.tsv      entity_id \t type                              # PaTeCon entityType, unchanged
{split}.facts.ext.tsv  S \t P \t O \t b_lo \t b_hi \t f_lo \t f_hi
                       \t precision_set \t gran_verdict \t stp_status \t layer \t conf
```

Hard guarantees, enforced in `tests/contract_p3.py`:
- **C1 — direction is entity-as-subject:** `(entity_x, "EventType#Role", event_e, T_e)`. Event-as-subject is available only as `subject_mode='event'`, exists solely for Vinh's degeneracy ablation, and is refused by default.
- **C2 — `ev_i ≠ ev_j` is enforced inside the projector.** Two participations of one event share one interval by construction; any head predicate on them is a tautology with confidence 1.0. This single line is the difference between a miner and 425,104 degenerate constraints. The skipped-pair count is written to the manifest.
- **C3 — `property` is pre-materialised** by Phase 2 from `property_vocab_v1.tsv` (652 strings). Vinh never builds the string, so the vocabulary cannot drift.
- **C4 — `split` is exactly document-disjoint.** Not approximately: 0 of 68,348 entities cross documents, so there is no leak channel.

**Vinh's owned contributions** (this is not serialisation work): (i) the `subject_mode='event'` vs `'entity'` **ablation**, which is the experiment that *demonstrates* the degeneracy rather than arguing it; (ii) the annotation tooling + pooled blinded adjudication protocol + Krippendorff's α; (iii) the LLM baseline (Allen-algebra prompting + reflection, Fan & Strube 2025) on the 300-item pooled adjudication task, with chance-corrected judge-vs-human κ.

### 3.6 Interface to Phase 4 (Nhan)

Nhan receives `pair_signatures` and the three TSVs, and runs `Graph_Structure.py` / `Constraint_Mining.py` **unchanged**. Only `Interval_Relations.py` is replaced by `tempekg.intervals` — identical function names and signatures, reads `b_hi`/`f_lo`, returns PaTeCon's existing trivalent `{True, False, UNKNOWN}` instead of guessing. ~200 lines; zero changes to the mining loop.

Nhan then adds the four things that are the paper's spine:

1. **Document-clustered support.** `supp(σ) = pair_signatures.n_docs`, not `n_pairs`. Threshold ≥10 **documents**.
2. **BH-FDR ≤ 0.05** over the candidate space via exact binomial tests against a null built from marginal predicate frequencies.
3. **Atomicity** (Martin et al., PVLDB 18, 2025): for predicate set φ and each `p_i`, test `P(p_j | φ\{p_i,p_j}) = P(p_j | φ\{p_j})`. Estimate each conditional as `Beta(successes+1, failures+1)`, compute `P(log-odds ratio ≥ 0)`, reject if below α=0.01. ~3 days.
4. **Entity-level vs fact-level confidence contrast** — the §0 survivor, one afternoon.

**Worked ordering example with real types.** Subject `x` = a `Person` entity. `p₁ = 'Attack#Patient'`, `p₂ = 'Killing#Victim'`. Candidate constraint: *for any subject x filling `Attack#Patient` in eᵢ and `Killing#Victim` in eⱼ, `start(eᵢ) ≤ start(eⱼ)`.* It will pass support and confidence easily. Then the atomicity test asks whether `P(before | Attack#Patient ∧ Killing#Victim)` differs from `P(before | Killing#Victim)` alone — i.e. whether `Killing` events are simply late in MAVEN documents regardless of the Attack. If not, the constraint is a conjunction of independent marginals and is **rejected as non-atomic**. That is the mechanism, on real types, in one paragraph — and Martin et al. report >95% of relational DCs fail exactly this test.

**Projected support arithmetic (compute this before day 8, do not guess).** 274,525 shared-participant event pairs → 139,093 (50.7%) carry a MAVEN-ERE temporal relation, so the head predicate is gold-determined and no anchor is required → ~111K in MINE → spread over 2,688 `(T1,r1,T2,r2)` signatures at ≥10-pair support, mean ≈41 pairs/signature. Under document clustering with ~3,623 documents contributing ~38 pairs each, expect **600–1,200 of the 2,688 signatures to survive ≥10-document support**. That number *is* a result. G2 (day 8) turns it into the go/no-go.

---

## 4. THE NOVELTY CLAIM (abstract form)

> **Primary.** Constraint-based conflict detection for temporal knowledge graphs was developed on encyclopaedic KGs in which every statement carries an explicit validity interval and entities recur across the whole graph. We port it to a document-local event graph — 4,480 Wikipedia documents, 80,479 events over 168 types, 236,937 role-typed arguments over 143 roles, and 1.22M gold temporal relations, joined across MAVEN-Arg and MAVEN-ERE on 79,740 shared event ids — and audit what the port costs. We show that PaTeCon's headline contribution, entity-level support and confidence, **provably degenerates to fact-level confidence** on this substrate, because 0 of 68,348 entities appear in more than one document and every entity's statement set (mean 3.15, max 59) lies inside a single annotated timeline; where PaTeCon+ reports a 38× conflict gap between the two regimes on WD27M, we measure a ratio of ⟨R⟩. We further show that the mandated entity-as-subject projection structurally reaches only 139,093 of 843,808 temporally-related event pairs (16.5%), that 59.9% of arguments are degree-1 unlinked spans generating no mineable subject, and that 3,649 events (5.4%) carry temporal relations yet emit no projected statement at all. Constraint mining must therefore be **type-level with document-clustered support**; under that reformulation we apply the first soundness test for temporal constraints — atomicity via a Beta-Bernoulli conditional-independence criterion — together with BH-FDR control in place of hand-tuned thresholds, and report that only ⟨N₄/N₁⟩ of PaTeCon-default constraints survive. We release the event knowledge graph, a rule-based TIMEX normaliser with per-family human-audited accuracy for MAVEN's value-less TIMEX layer, and a frozen, hashed constraint set.

**Backup claim 1 (substrate audit).** *The gold temporal layer of MAVEN-ERE is conflict-free by annotation construction, not by accident, and mining violations from it has almost no target.* We report the first full Simple Temporal Problem closure of the corpus — the published result of 0 BEFORE cycles across 843,808 pairs is BEFORE-only; we close the network with all 66,418 CONTAINS anchor bounds, 9.9K SIMULTANEOUS and 9.9K OVERLAP edges — and give the per-document satisfiability rate under two annotation readings. Against ~72 genuine contradictions corpus-wide stand 1,638 of 12,019 subevent pairs (13.6%) lacking their implied CONTAINS: the actionable defect is **incompleteness, not contradiction**, and we score the two separately, penalising detectors that flag incompleteness as conflict. We also state which of Allen's 18 maximal tractable subalgebras the head-predicate language occupies — `disjoint` puts `{start, finish, before, disjoint, include}` outside ORD-Horn, so dropping it yields a *complete* O(n³) decision procedure — which essentially no KG-conflict paper does.

**Backup claim 2 (granularity characterisation).** *The first quantitative adjudication of multi-granularity temporal anchoring in a text-grounded event corpus.* Over the 17,102 MAVEN events carrying ≥2 gold CONTAINS anchors (≥38,226 anchor pairs), we adjudicate by intersection-emptiness — never by precision difference — into REFINEMENT / COMPAT_NONCHAIN / CONFLICT / UNDECIDABLE, with 100% of the CONFLICT set hand-labelled into {genuine, normalisation error, coreference error, durative artefact}. This inverts Kontrast (arXiv 2607.25959), which measures granularity mismatch at 18.6% of flagged conflicts and recommends normalising it away before labelling; we keep it, label it, and report what fraction is genuine. **The claim is true whether the CONFLICT bucket holds 700 events or 7.**

**Explicit non-claims, stated in §2 of the paper.** We are not first to formalise inconsistency across temporal granularities (Bettini/Wang/Jajodia AMAI 1998, AI 140 2002; Euzenat, Computational Intelligence 17(4) 2001). We are not first to notice granularity mismatch empirically (Kontrast 2026). We are not first to enforce Allen consistency on MAVEN-ERE (Fan & Strube, Findings EMNLP 2025). Strict-inequality handling by lexicographic (value, infinitesimal) pairs is Dutertre & de Moura (CAV 2006). The TIMEX normaliser is a reimplementation of the HeidelTime recipe.

---

## 5. NON-CIRCULAR EVALUATION PROTOCOL

**Design principle, and the whole point of the amputation: Track 0 requires no conflicts to exist. If everything else fails, the paper still has its headline.**

**STEP 0 — Freeze and hash.** Mine on MINE only. Serialise the full constraint set (pattern, head, support-in-documents, confidence, FDR q, atomicity p). Commit the SHA-256 to the repo and state the commit in the paper, **before any error exists**. Cite arXiv 1110.6652 (holdout rule mining) and AMIE held-out fact counting.

**TRACK 0 — The pruning ladder (primary, gold-only, zero labels).**

| Stage | Constraints |
|---|---|
| PaTeCon defaults (support ≥10 pairs, conf ≥0.9) | N₁ |
| + support ≥10 **documents** | N₂ |
| + BH-FDR ≤ 0.05 | N₃ |
| + atomicity, α = 0.01 | N₄ |

Report `N₄/N₁`, plus the entity-level:fact-level constraint and conflict ratios against PaTeCon+'s 1.8× / 38×. No conflict, no annotation, no perturbation, no normaliser dependency.

**TRACK 1 — Substrate audit.** Full-STP satisfiability rate on L0 under two OVERLAP/SIMULTANEOUS readings; the ~72 native contradictions reported as exact counts (not as a recall set with fake CIs); contradiction vs incompleteness scored in separate columns from the first draft.

**TRACK 2 — Gold-free consistency metrics (no circularity objection is even formulable).** Uniqueness-violation, symmetry-violation, and conjunction/transitivity-violation rates (Joint Constrained Learning vocabulary; Kougia et al. BioNLP 2024 methodology) computed on the L1 layer and on the **857 blind documents**, where no gold arguments or relations exist at all. Note the sanity check: gold has 0 symmetry violations, so symmetry is a validity test of the pipeline, not a task.

**TRACK 3 — Human-authored perturbation (300 items).** Annotators edit one temporal fact per document to create an error they would expect a human or a system to make, **without ever seeing the frozen constraint file** (injector firewall: written and run by a team member with no read access; manifest sealed until detection results exist). Exactly one perturbation per document; never cascade; replacement surfaces sampled from the 9,287 observed TIMEX surfaces. Report the **blindness audit**: fraction of injected conflicts on which any single mined constraint fires, vs fraction reachable only through multi-hop closure. ReFACT (arXiv 2509.25868) is the precedent for human authorship; CECOR (arXiv 2605.02277) for one-step-at-a-time discipline.

**TRACK 4 — Rule-negating injection, run ONLY to measure the circularity gap.** Generate conflicts by violating mined constraints, detect with those same constraints, and report `gap = P@k(Track 4) − P@k(Track 3)` as **a result**. The KGED literature documents a ~30%-scale synthetic→real recall drop; predict and measure it. This is the sole legitimate use of the original fake-conflict plan.

**Adjudication.** Pool top-k from all detectors including a random baseline; shuffle; strip system identity; annotate the union (TREC pooling). Four-way label set: `{GENUINE | SPURIOUS: constraint wrong | SPURIOUS: graph incomplete, not contradictory | UNDECIDABLE}` — the incompleteness class is non-negotiable given 13.6%, and KONTRAST's taxonomy is the citable justification. Annotate **culprit localisation**, not just detection; report set-level F1 and culprit-accuracy@1 separately (ReFACT precedent). 3 annotators on a ≥300-item overlap, 4th-person adjudication, **Krippendorff's α** overall and per class (not Fleiss κ — the pool is imbalanced and incompletely annotated, arXiv 2603.06865). Pilot round, guideline v1→v2 with a released diff, annotator error rate on a seeded gold subset.

**LLM baseline.** Fan & Strube-style Allen prompting + reflection, run on the 300 pooled items only (not 843k pairs). Report chance-corrected judge-vs-human κ against the extraction-domain reference band 0.72–0.80; target ≥0.6. LLM labels never enter the gold set. Exact-match agreement is not acceptable validation (arXiv 2606.19544).

**Metrics.** Base rate stated explicitly as the random-baseline precision (~8.5×10⁻⁵ on the natural graph). Report **P@50/100/500/1000, R-Precision, AUPRC**. Tier-A exact recall on injected/system-error sets; Tier-B recall on the natural graph only as a score-stratified Horvitz-Thompson interval estimate with CIs, never presented as corpus recall. **Report no accuracy and no ROC-AUC anywhere.**

**Normaliser validation is a first-class deliverable, not a mitigation.** 250 dev surfaces (used for development) + **150 blind held-out surfaces**, stratified by family (regex / refprop / gazetteer / unresolved), with a 100-item two-annotator overlap for IAA. Report per-family value accuracy with CIs. Every granularity number is then reported as `flagged / adjudicated-genuine / normalisation-artefact / undecidable`, never as "conflicts".

**"Claims Supported / Claims Not Supported"** subsection, one page: ranking detectors by top-k precision on realistic errors (yes); absolute corpus recall (interval estimate only); generalisation beyond news/Wikipedia MAVEN documents (no); detection of errors whose generating process resembles the constraint language (measured and reported as the circularity gap, never claimed as capability).

---

## 6. 45-DAY SCHEDULE

Build window is **days 1–32**. Days 33–45 are paper. Anyone who plans to build past day 32 has planned to not submit.

### Week 1 · 28 Aug – 3 Sep (days 1–7)

**Nhut** — D1–D2 ingest + join on `doc_id`/`EVENT_` id (no offset alignment needed for the core join; log the 739 ARG-only events). Emit tables 1–4, 7. **Assign and hash the document-disjoint split.** Regression-assert corpus counts: 80,479 events, 236,937 participations, 68,348 entities, 652 properties, 0 BEFORE cycles, 1,638 subevent gaps, ~72 contradictions. D3–D5 interval builder + STP compiler + Floyd-Warshall + **the full-STP L0 audit**. D6–D7 start the normaliser (stage 1, regex families covering the 62.1% deterministic mass).
**Vinh** — annotation tooling v0; write annotation guideline v1 for the 4-way conflict label set + TIMEX value labelling.
**Nhan** — clone PaTeCon, run it end-to-end on a synthetic 3-column TSV so the loader path is proven before real data arrives; write `tempekg.intervals` against the frozen signature list.
**GATE G0 (day 3):** split frozen + hashed, all corpus assertions green. If ingest counts disagree, ingestion is wrong — stop and fix.
**GATE G1 (day 5):** L0 full-STP satisfiability rate reported. **Decision made and written down** on the OVERLAP/SIMULTANEOUS reading. If unsat >5%, relax to the non-strict reading and report both.

### Week 2 · 4–10 Sep (days 8–14)

**Nhut** — D8 `pair_signatures` **with `n_docs`** + `projection_loss` + the projection function + `tests/contract_p3.py`. D9–D12 normaliser stage 2 (narrative reference-time propagation, ~50-entry gazetteer, single-candidate year-less resolution). D13–D14 `event_time` population + granularity adjudication (4 verdicts + `multi_day_flag`).
**Vinh** — L1 layer: smoke-run PAIE/DEEIA inference on 20 documents in week 1's tail, then full inference over MINE+EVAL; populate `participations` with `layer='L1'`.
**Nhan** — atomicity test implementation against synthetic Bernoulli data with known dependence structure (validate before real data).
**GATE G2 (day 8) — THE PIVOTAL GATE.** Compute, from `pair_signatures`, the count of `(T1,r1,T2,r2)` signatures surviving ≥10-**document** support with non-UNKNOWN head predicates. Projected 600–1,200. **If <400, the ordering-constraint arm is demoted to a reported measurement and the paper is Track 0 + reachability only** — which is still the headline. Announce the decision to Vinh and Nhan the same day.
**GATE G3 (day 12): `eckg/v1.0.0` frozen + hashed + handed over.** Three days earlier than design A's day-15 freeze, achievable because we cut the periodic-set library and three tables.

### Week 3 · 11–17 Sep (days 15–21)

**Nhut** — D15–D16 normaliser validation: hand-label 250 dev + 150 blind surfaces, report per-family accuracy with CIs. D17–D18 perturbation generator (normaliser-level families, one edit per document, no cascade) + the human-authoring harness for Vinh. D19–D21 buffer / the char↔token map for the overlap report.
**Vinh** — projection ablation `subject_mode='event'` vs `'entity'`; run the pilot annotation round; guideline v1→v2 from disagreement analysis.
**Nhan** — PaTeCon unchanged on `MINE.facts.tsv` → **N₁**. Then document-clustered support → **N₂**. BH-FDR → **N₃**.
**GATE G4 (day 18):** constraint set mined, serialised, SHA-256 committed. Nothing downstream may be generated before this hash exists.

### Week 4 · 18–24 Sep (days 22–28)

**Nhut** — CONFLICT-set hand adjudication, 100%, into {genuine / normalisation / coreference / durative}, with witness table. Gold-free consistency metrics on L1 + the 857 blind docs.
**Vinh** — 300 human-authored perturbations (annotators blind to the constraint hash); LLM Allen+reflection baseline on the pooled set.
**Nhan** — atomicity → **N₄**; entity-level vs fact-level contrast; LOFO ablation over the three constraint families; detection runs; P@k tables.
**GATE G5 (day 25) — SUBMIT/NO-SUBMIT.** The pruning ladder N₁→N₄ and the entity/fact ratio exist. **If yes, we submit.** Everything after this is upside.

### Week 5 · 25 Sep – 1 Oct (days 29–35)

Days 29–32: Track 4 circularity gap; pooled blinded adjudication (3 annotators × ≥300 items ≈ 1 day each); Krippendorff's α; judge-vs-human κ. **Day 32: code freeze, no exceptions.**
Days 33–35: paper skeleton, all tables populated with real numbers, Limitations section drafted **first** (ARR/EACL 2026 desk-reject without it).

### Week 6 · 2–8 Oct (days 36–42)

Full draft. Related-work section leads with Kontrast, Fan & Strube, Soulard et al., PaTeCon+, Bettini/Euzenat — the non-claims paragraph goes in the first draft, not the revision. "Claims Supported / Not Supported" subsection. Release engineering: Parquet + manifest + guidelines + frozen constraint hash on HuggingFace.
**GATE G7 (day 40):** complete draft with Limitations circulating to all three.

### Week 7 · 9–12 Oct (days 43–45)

Internal review, figure polish, submission. **Day 44 is the submission day; day 45 is slack.**

**Person-day totals:** Nhut 24 (in ~27 effective, 0.85 duty cycle) · Nhan 13.5 · Vinh 14.5. This is the first honest budget in the set.

---

## 7. ALTERNATIVES IF YOU DISAGREE

### Fallback A — **The granularity resource paper** (E, descoped). Trigger: G2 fails (<400 signatures).
Deliverable: the released normaliser + normalised values for all 20,827 TIMEX spans + the 4-verdict characterisation of 17,102 multi-anchor events + a 400-item human audit with per-family CIs + the released granularity/precision schema. Drop constraint mining entirely.
**Trade-offs.** Pro: unblocked by G2, and true whether CONFLICT holds 700 events or 7; ARR reviewer guidelines explicitly instruct reviewers to value resources for under-resourced settings. Con: no method contribution; the headline depends entirely on an unsupervised normaliser (S/N ≈1:20 on the natural conflict set, per E's judge); Kontrast owns the phenomenon and you own only the inversion of its stance; **Nhan's phase contributes nothing**. Venue: COLING resource track, LREC 2027, or *ACL Findings. Cost: ~16 person-days for Nhut, redistributes 10 from Nhan to annotation.

### Fallback B — **The mining-free detector paper** (C, descoped). Trigger: PaTeCon proves unrunnable on the projection, or Nhan is unavailable.
Deliverable: the day-chronon STP with the compilation table; complete O(n³) detection with negative-cycle witnesses; the ORD-Horn/tractability positioning; MaxSMT culprit localisation as a *minimal correction set* (never "exact minimal hitting set" — that is NP-hard as specified); gold-free consistency metrics on L1 and the blind split; the LLM Allen+reflection baseline.
**Trade-offs.** Pro: two genuinely non-circular detectors; no constraint mining, so no circularity objection is formulable; cleanest engineering. Con: goes head-to-head with Fan & Strube (Findings EMNLP 2025) on the same dataset with the same start/end decomposition, and loses the comparison on method novelty; abandons the PaTeCon lineage the project is built on; **kills Phase 4 outright**; the ε device you would want to lead with is CAV 2006. Cost: ~20 person-days.

### Fallback C — **The 4-page short** (emergency). Trigger: G5 slips past day 28.
Track 0 only: the pruning ladder, the entity/fact degeneracy, the 16.5% reachability ceiling, the arity-0 and null-slot loss counts, plus a mandatory Limitations section. No normaliser, no granularity, no perturbation, no annotation study.
**Trade-offs.** Pro: highest acceptance probability of the three; ~10 person-days; every number is gold-only and computable by day 20. Con: lowest ceiling, reads as a workshop paper, and leaves the released graph as an appendix. **Keep this in your pocket from day 1 and do not be ashamed of it** — a true short paper beats an ambitious paper with an empty headline table on day 40.

---

## 8. WHAT TO CUT

Cut on **day 1**, in writing, not at day 25 when the designs themselves concede the choice is irreversible.

| Cut | From | Days saved | Why |
|---|---|---|---|
| **Minimal-periodic-set library** | B, C, E | **4–5** | Highest-variance code in every plan, no reference implementation, buys ~100 of 20,827 surfaces. Replaced by single-candidate reference-time resolution (§3.2). |
| **L2 predicted-temporal-relation layer / `trel_clf`** | C, D | **8–12** | New model training on ~1.2M pairs, no temporal component in any of the five repos, scheduled at the tail. Both C and D bet their headline on it. Replaced by L1 (inference only, 2d). |
| **Z3 / MaxSAT / MaxSMT** | A, C, D, E | **2–3** | Zero mined constraints does not make it a headline; culprit localisation is deliverable from the negative-cycle witness. Keep as future work. |
| **SHACL-SPARQL baseline** | A, D, E | **1–1.5** | SHACL-core cannot compare interval endpoints across nodes — i.e. it cannot express the ordering family at all. A baseline that cannot express the task is not a baseline. |
| **RDF 1.2 / pyoxigraph / named-graph serialisation** | A, D, E | **3** | Pure serialisation with no experiment attached. Ship Parquet + manifest. |
| **DuckPGQ** | A, B, C, E | **0.5** | BEFORE-closure over ~18 events/document is a 30-line transitive closure. Declaring an engine documented as incomplete only invites a reviewer question. |
| **Kuzu** | any plan naming it | — | Repository archived 10 Oct 2025 after the Apple acquisition. A reviewer can check the banner in ten seconds. |
| **HyPaL beyond one atom family** | B | **9.5** | Four families push the candidate space to ~10⁷ and gut BH-FDR power exactly where the novelty was supposed to live. |
| **Helly / k-wise granularity claim** | B | **2** | Helly 1923, and the DURATION-width family carrying it rests on a misreading of `CONTAINS` (§3.2). |
| **Lexicographic (day, ε) as a novelty claim** | C | 0 (writing) | Dutertre & de Moura, CAV 2006. Keep the code, cite the paper, delete the claim. |
| **Factorisation-through-join-granularity as headline** | E | 0 (writing) | Euzenat 2001 upward conversion + a re-check. Demote to a diagnostic instrument with a worked example. |
| **`unlinked_spans` as a node table** | A | 0.5 | Degree-1 by construction, contributes nothing to SP(a). A column, not a table. |
| **`property_marginals`, `token_index` as core tables** | A | 0.5 | A view and a lazy half-day script. |
| **`entailed_at_gran` over all 1.22M edges** | E | **2–3** | ~10¹⁰ integer ops for a column nobody reads. Compute only on conflict-participating edges. |
| **WEEK / WEEK_OF_YEAR / TIME_OF_DAY lattice nodes** | E | 1 | Tiny surface share, primary source of week-numbering bugs. 22 lattice nodes → ~14. |
| **Croissant metadata + full Datasheet + HF hosting polish** | A, E | **1.5** | Keep a one-page manifest with hashes and a released guideline. The rest is post-acceptance. |
| **Extrinsic downstream arm ("does cleaning help?")** | A, sweeps | **2** | arXiv 2506.12367: bias is near zero within a band of extraction quality. A pre-registered null result you do not have time to earn. |
| **Cross-document coreference** | all | — | 0 of 68,348 entities cross documents. Deferred with a citation (xCoRe EMNLP 2025), and the deferral is itself a framing asset: all constraints here are necessarily type-level. |
| **Fuzzy / vague interval algebras** | all | — | No supervision exists for membership functions, and fuzziness destroys the crisp emptiness test that makes granularity decidable. One inoculating paragraph in related work. |

**Total recovered: ~35–40 person-days across the team.** Reinvest exactly here: 6 days on the TIMEX normaliser (measured ~1 week, every plan budgeted 4), 2 days on its blind validation set, 3 days on 100% adjudication of the CONFLICT set, 3 days on the atomicity test, 3 days on pooled blinded adjudication with Krippendorff's α, and the rest as declared buffer against G2 and G3.

---

### The one-sentence version

Stop trying to detect conflicts in a corpus you have already measured to contain 72 of them; publish instead the measured cost of porting PaTeCon-style mined-constraint conflict detection from a globally-linked entity KG to a document-local event graph — a result that needs no conflicts, no perturbations, no annotations, and no TIMEX normaliser to be true — and let granularity, the STP baseline, and the released graph be the supporting sections they can actually be in 45 days.