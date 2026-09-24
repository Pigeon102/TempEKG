export const meta = {
  name: 'tempekg-phase2-lean',
  description: 'Research event-graph design space, generate 5 competing ECKG designs for TempEKG Phase 2, judge adversarially, synthesize a 45-day plan',
  phases: [
    { title: 'Research', detail: '4 parallel sweeps: representation, temporal uncertainty + granularity, constraint mining, NLP consistency + benchmark design' },
    { title: 'Design', detail: '5 competing ECKG architectures, each adversarially judged as it completes' },
    { title: 'Synthesize', detail: 'hostile novelty review folded into the final decision document' },
  ],
}

const FACTS = `
HARD MEASURED FACTS (computed directly from the local data — do NOT contradict, do NOT re-derive, do NOT restate back):

SCALE
- MAVEN-Arg: 4,480 docs; 80,479 events; 236,937 arguments; 143 argument roles; 168 event types; 7 entity types (Location, Other, Organization, Person, Product, Building, Art).
- train+valid = 3,623 docs with gold arguments. test.jsonl is BLIND ('event_mentions', no gold arguments).
- MAVEN-ERE covers the SAME documents: doc-id overlap 4,480/4,480 = 100%. Shared event ids = 79,740.
- MAVEN-ERE temporal relations: BEFORE 1.04M, CONTAINS 152K, SIMULTANEOUS 9.9K, OVERLAP 9.9K, BEGINS-ON 639, ENDS-ON 380.

ENTITIES / ARGUMENTS
- Only 40.1% of arguments carry 'entity_id'; 59.9% are bare {content, offset} spans with no coreference.
- ZERO entities appear in >1 document (0 of 68,348). Entities are strictly document-local; no cross-doc linking exists.
- Entities (ids, 7 types, mention offsets) ARE PROVIDED as input in EVERY split including blind test.
- 16,284 entities participate in >=2 events; mean 3.15 events/entity, max 59.
- Shared-participant event pairs: 274,525; of those 139,093 (50.7%) also carry a MAVEN-ERE temporal relation.

TIME
- TIMEX spans ARE PROVIDED in every split including blind test. TIMEX DETECTION IS NOT A TASK.
- TIMEX has NO normalised value field, only surface strings. Normalisation is unbuilt, zero gold supervision.
- 20,827 gold TIMEX spans (9,287 distinct surfaces) in train+valid. Types: DATE, DURATION, TIME, PREPOSTEXP.
- MEASURED normalisation difficulty: 62.1% deterministic regex (bare year 29.9%, day-month-year 9.1%, month+year 6.9%, N+unit 6.1% (a DURATION - constrains width not position), month+day+year 4.6%, ranges/decades/centuries/deictic 5.6%). 37.9% needs document context, dominated by four tractable families: relative dates ("the next day" x91, "the following day" x62, "the same day" x21), year-less dates ("September 11" x24, "August 31" x17), named periods ("World War II" x70, typed DURATION), weekdays ("Sunday" x21). Realistic build: regex (~2d) + TimeML-style document reference-time propagation (~2d) + ~50-entry gazetteer (~0.5d) => ~85-90% coverage in about a week.
- Event-TIMEX anchors: CONTAINS 66,418; SIMULTANEOUS 496; BEGINS-ON 122; ENDS-ON 39. CONTAINS is ~99% of anchoring mass; BEGINS-ON/ENDS-ON too rare to learn.
- Events with a TIGHT TIMEX anchor: 37,852 = 44.9% (10.4/doc). Loose bound only: 27.2%. No TIMEX link: 27.9%.
- Events with >=2 CONTAINS anchors: 17,102 (2 anchors: 10,653; 3: 3,707; >=4: 2,742). Usually NESTED granularity ("in 1778" + "on November 11").
- MAVEN-Arg's 143 roles contain NO Time/Date/When role. Only 'Duration': 33 instances, 1 event type (Prison), values like "life", "21 years".
- Only 4.97% of argument spans overlap any TIMEX; only 13.8% of TIMEX are covered by any argument span. EAE structurally cannot supply event time.

GOLD CONSISTENCY AUDIT (critical)
- Gold temporal graph is essentially CONFLICT-FREE: 0 BEFORE cycles across 843,808 pairs; 0 symmetric violations; BEFORE is 100.0% transitively closed (7 missing of 6,718,279 chains).
- CAUSE contradicted by BEFORE: 11/46,014 (0.02%). subevent contradicted: 61/12,019 (0.5%). subevent lacking implied CONTAINS: 1,638/12,019 (13.6%, incompleteness not contradiction).
- TOTAL genuine contradictions in the whole gold corpus: ~72. Mining conflicts FROM gold has almost no target.

MINING POWER
- (EventType1, EventType2) signatures with support >=10: 2,708 (81% instance coverage). (T1,role1,T2,role2) >=10: 2,688 (59%).
- Projected property vocabulary "EventType#Role" = 652 distinct (623 with >=10). PaTeCon's |R|^2 index = 425,104 entries ~0.1 GB. Scales fine.

PATECON REFERENCE (AAAI 2023 + arXiv 2312.11053 PaTeCon+; github.com/JianhaoChen-nju/PaTeCon)
- REIFIED statement-node graph: eVertex (entity) + sVertex (statement carrying start/end/weight/truth). Indexes: eVertexList (subject->statements), sVertexList (property->statements), temporalRelationList, entityType.
- Two hand-fixed structural patterns: SP(a) one subject two temporal statements; SP(b) two subjects joined by an atemporal property.
- Three constraint families: temporal disjointness, temporal ordering, mutual exclusion. Head predicates: start, finish, before, disjoint, include (+ 'false' for mutex, + span bounds).
- TRIVALENT logic over uncertain time: positive/negative/UNKNOWN; unknown discarded from support and confidence.
- Fact-level vs ENTITY-level support/confidence (entity positive only if ALL its subgraphs positive) - their headline contribution.
- PaTeCon+ adds two-stage pruning via law of large numbers. Defaults: support=10, candidate_conf=0.5, conf=0.9.

THE PROJECT (TempEKG, URA Lab, HCMUT)
- Target COLING 2027 (CORE B). Deadline 12 Oct 2026. Today 28 Aug 2026 => 45 DAYS.
- Team of 3: Vinh (Phase 3 Graph Projection + annotation tooling), Nhut (Phase 2 GRAPH CONSTRUCTION - THIS IS THE USER), Nhan (Phase 4 Constraint Mining).
- Phases: P1 Event Extraction (PAIE/SCPRG/DEEIA on MAVEN-Arg, DONE); P2 Graph Construction from GOLD labels, events with time anchors, split train/test, build ECKG; P3 Projection ECKG->Temporal KG to reuse PaTeCon; P4 Constraint Mining per PaTeCon + FAKE conflicts by perturbing times; P5 Conflict Detection on test graph.
- Two targeted conflict types: (1) ORDERING CONFLICT - contradictory temporal ordering between related event pairs, relations {start, finish, before, disjoint, include}; (2) GRANULARITY CONFLICT - inconsistent temporal precision for the SAME event.
- PROBLEMS ALREADY DIAGNOSED: (a) the fake-conflict evaluation is CIRCULAR (conflicts generated by violating mined constraints then detected with those same constraints); (b) Phase 1 is orphaned - extractors never feed the graph since P2 uses gold; (c) projecting event-as-subject makes all predicates degenerate (all statements of one event share one interval) so projection MUST be entity-as-subject: (entity_x, "EventType#Role", event_e, T_e); (d) train/test must split BY DOCUMENT or entity-sharing leaks across the split.
- Their repos (PAIE_Maven, DEEIA_Maven, SCPRG, TSAR_Maven, MAVEN_Arg_Pipeline) contain NO temporal component whatsoever.
`

const RESEARCH_SCHEMA = {
  type: 'object',
  properties: {
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          claim: { type: 'string' },
          why_it_matters_for_tempekg: { type: 'string' },
          sources: { type: 'array', items: { type: 'string' } },
        },
        required: ['claim', 'why_it_matters_for_tempekg'],
      },
    },
    key_papers: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          venue_year: { type: 'string' },
          url: { type: 'string' },
          relevance: { type: 'string' },
        },
        required: ['title', 'relevance'],
      },
    },
    reusable_techniques: { type: 'array', items: { type: 'string' } },
    novelty_gaps: { type: 'array', items: { type: 'string' } },
  },
  required: ['findings', 'key_papers', 'reusable_techniques', 'novelty_gaps'],
}

const DESIGN_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    one_line: { type: 'string' },
    core_idea: { type: 'string' },
    node_and_edge_model: { type: 'string' },
    concrete_schema: { type: 'string' },
    interval_representation: { type: 'string' },
    how_ordering_conflict_works: { type: 'string' },
    how_granularity_conflict_works: { type: 'string' },
    interface_to_phase3_and_phase4: { type: 'string' },
    novelty_claim: { type: 'string' },
    effort_days_for_one_person: { type: 'number' },
    build_steps: { type: 'array', items: { type: 'string' } },
    risks: { type: 'array', items: { type: 'string' } },
    what_it_gives_up: { type: 'string' },
  },
  required: ['name', 'one_line', 'core_idea', 'node_and_edge_model', 'concrete_schema', 'interval_representation', 'how_ordering_conflict_works', 'how_granularity_conflict_works', 'interface_to_phase3_and_phase4', 'novelty_claim', 'effort_days_for_one_person', 'build_steps', 'risks', 'what_it_gives_up'],
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    feasibility_45d: { type: 'number' },
    novelty_coling: { type: 'number' },
    effectiveness: { type: 'number' },
    overall: { type: 'number' },
    fatal_flaws: { type: 'array', items: { type: 'string' } },
    fixable_issues: { type: 'array', items: { type: 'string' } },
    prior_work_that_undercuts_novelty: { type: 'array', items: { type: 'string' } },
    strongest_defensible_claim: { type: 'string' },
    verdict: { type: 'string' },
  },
  required: ['feasibility_45d', 'novelty_coling', 'effectiveness', 'overall', 'fatal_flaws', 'fixable_issues', 'prior_work_that_undercuts_novelty', 'strongest_defensible_claim', 'verdict'],
}

// ---------------- RESEARCH ----------------
phase('Research')

const SWEEPS = [
  {
    key: 'representation',
    prompt: `Research how EVENT-CENTRIC knowledge graphs are represented and stored, focusing on 2024-2026. Cover: n-ary event representation (reification, RDF-star, named graphs, property graphs, hypergraphs, event-as-hyperedge); event KG schemas (EventKG, ECKG construction surveys, Event Logic Graph, event evolutionary graphs); whether time sits on nodes or edges; bitemporal and provenance-carrying graph models; practical storage engines for graphs of this size (DuckDB, kuzu, Neo4j, RDF stores) and when each is justified. Report which concrete representation choices are defensible and citable for a COLING paper building an event-centric temporal KG from MAVEN-Arg + MAVEN-ERE.`,
  },
  {
    key: 'time-granularity',
    prompt: `Research formalisms for UNCERTAIN and MULTI-GRANULAR time, and specifically whether "granularity conflict" is already taken as a contribution. Cover: (1) Allen interval algebra and tractable subalgebras; point algebra and path consistency; Temporal Constraint Networks (TCSP, STP, STNU); imprecise intervals (four-endpoint bounds, convex/fuzzy intervals). (2) Granularity calculi and granularity systems (Bettini/Jajodia/Wang), glb/lub on granularity lattices, granularity conversion in temporal databases. (3) ISO-TimeML / TIMEX3 normalisation semantics: value, granularity, anchoring, underspecification, narrative containers. (4) NOVELTY VERDICT: has anyone formally defined and detected conflicts arising from an event or entity being anchored at multiple INCOMPATIBLE temporal precisions? Search temporal databases, KG quality management, temporal IE, and semantic web literature. Be rigorous and explicit about the novelty verdict - the team wants to claim this and must know if it is already taken. Answer concretely: which formalism should represent an event known only as "contained in 1778" AND "contained in November 11", and how do you decide those anchors are incompatible?`,
  },
  {
    key: 'constraint-mining',
    prompt: `Research CONSTRAINT AND RULE MINING over knowledge graphs beyond PaTeCon, 2023-2026. Cover: AMIE/AMIE3/MiniAMIE and rule confidence measures (PCA confidence, head coverage); SHACL/ShEx constraint induction and validation; functional dependency and DENIAL CONSTRAINT discovery (FASTDC, Hydra), including numerical and temporal denial constraints; KG/data error detection and cleaning (HoloClean, Raha/Baran); temporal rule learning over temporal KGs (TLogic, TILP, StreamLearner, sequential support with time constraints). Report which of these give a stronger, more citable formal footing than PaTeCon's ad-hoc support/confidence, and which could be adapted cheaply to EVENT-level constraints in 45 days.`,
  },
  {
    key: 'consistency-benchmark',
    prompt: `Research two connected things. (A) TEMPORAL CONSISTENCY in NLP information extraction 2023-2026: global inference for temporal relation extraction (ILP, weighted MaxSAT, SSVM, structured perceptron); joint constrained learning; transitivity/symmetry enforcement; document- and discourse-level temporal RE; timeline construction; LLM temporal reasoning and consistency in 2025-2026 (Allen-algebra prompting, self-consistency, reflection); datasets beyond MAVEN-ERE (TimeBank-Dense, MATRES, TDDiscourse, TORQUE, TRACIE). (B) How to build and evaluate an ERROR/CONFLICT DETECTION BENCHMARK credibly: synthetic error injection methodology that avoids circularity (realistic vs random corruption); evaluation under extreme class imbalance (precision@k, PR-AUC); annotation protocols and IAA for adjudicating flagged conflicts; LLM-as-judge reliability 2025-2026; what reviewers demand of new resource/benchmark papers at ACL/EMNLP/COLING. Deliver a concrete NON-CIRCULAR evaluation protocol for a temporal-conflict-detection benchmark whose gold data is already consistent.`,
  },
]

const research = (await parallel(
  SWEEPS.map(function (s) {
    return function () {
      return agent(
        s.prompt + '\n\nCONTEXT (the project this research serves):\n' + FACTS +
        '\n\nUse WebSearch and WebFetch aggressively; prefer 2025-2026 sources. Return dense, specific, citable findings with source URLs. Do NOT restate the facts above - add NEW information.',
        { label: 'research:' + s.key, phase: 'Research', schema: RESEARCH_SCHEMA, effort: 'medium' }
      )
    }
  })
)).filter(Boolean)

log('Research complete: ' + research.length + '/4 sweeps')

const researchDigest = research.map(function (r, i) {
  return '### Sweep ' + SWEEPS[i].key + '\n' +
    'FINDINGS:\n' + r.findings.map(function (f) { return '- ' + f.claim + ' [WHY: ' + f.why_it_matters_for_tempekg + ']' }).join('\n') +
    '\nKEY PAPERS:\n' + r.key_papers.map(function (p) { return '- ' + p.title + ' (' + (p.venue_year || '?') + ') ' + (p.url || '') + ' - ' + p.relevance }).join('\n') +
    '\nREUSABLE: ' + r.reusable_techniques.join('; ') +
    '\nNOVELTY GAPS: ' + r.novelty_gaps.join('; ')
}).join('\n\n')

// ---------------- DESIGN -> JUDGE (pipelined) ----------------

const ANGLES = [
  {
    key: 'A-projection-faithful',
    brief: `ANGLE A - PaTeCon-faithful, projection-first, minimum risk. Design the ECKG so Phase 3's projection to a binary temporal KG is trivial and PaTeCon's existing code runs nearly unmodified. Optimise for 45-day feasibility, maximum code reuse, and low integration risk across the 3-person team. Accept lower representational novelty and locate novelty elsewhere (conflict types, evaluation). Be concrete about the entity-as-subject projection and about exactly what information the projection LOSES.`,
  },
  {
    key: 'B-nary-hypergraph',
    brief: `ANGLE B - Native n-ary event hypergraph, no projection. Design the ECKG as a true hypergraph where an event is a single time-bearing hyperedge over typed role-slots, and constraint mining operates natively on n-ary patterns rather than binary triples. Argue why projecting to binary triples destroys information that matters, and design an n-ary pattern language plus mining procedure that PaTeCon structurally cannot express. Optimise for representational novelty and expressiveness.`,
  },
  {
    key: 'C-constraint-network',
    brief: `ANGLE C - The graph IS a temporal constraint network. Design the ECKG so its temporal core is a formal constraint network (point algebra / STP / Allen subalgebra) over event endpoints, with TIMEX anchors as unary constraints and MAVEN-ERE relations as binary constraints. Conflict detection becomes UNSATISFIABILITY / path-consistency failure rather than pattern matching; mined constraints become additional network constraints. Optimise for formal rigour and for unifying ordering conflict and granularity conflict under one mechanism.`,
  },
  {
    key: 'D-provenance-multiversion',
    brief: `ANGLE D - Provenance-first, multi-version graph. Design the ECKG as a multi-version store holding gold, gold-trigger+predicted-argument, and fully-predicted variants of the SAME documents simultaneously, every node and edge carrying source and model confidence. Conflict detection becomes differential and confidence-weighted; the noise dial (G_gold < G_trig < G_pred) is a first-class query. Optimise for solving the circular-evaluation problem and reconnecting orphaned Phase 1 to the pipeline.`,
  },
  {
    key: 'E-granularity-lattice',
    brief: `ANGLE E - Granularity-lattice-centric. Design the ECKG around multi-granular time as the PRIMARY modelling concern: every event carries a set of anchors at possibly different granularities organised on a granularity lattice, and granularity conflict is first-class rather than an afterthought. Ordering constraints are derived from a granularity-aware interval algebra. Optimise for making GRANULARITY CONFLICT the paper's headline contribution, exploiting the measured 17,102 events with >=2 anchors.`,
  },
]

const judged = await pipeline(
  ANGLES,
  function (angle) {
    return agent(
      'You are designing the Event-Centric Knowledge Graph for the TempEKG project. Produce ONE complete, concrete, buildable design following this angle:\n\n' +
      angle.brief +
      '\n\n' + FACTS +
      '\n\nRESEARCH GATHERED BY THE TEAM (use it; cite specific techniques and papers by name):\n' + researchDigest +
      '\n\nRequirements:\n' +
      '- Be CONCRETE: actual table/class definitions, actual field names, worked examples using real MAVEN event types (Killing, Attack, Process_start, Military_operation, Hostile_encounter) and the real numbers above.\n' +
      '- Phase 2 is owned by ONE person and must hand a clean interface to Phase 3 (projection, Vinh) and Phase 4 (constraint mining, Nhan). Specify that interface precisely.\n' +
      '- Address BOTH conflict types: ordering and granularity.\n' +
      '- Be honest about person-days and about what this design gives up versus the other angles.\n' +
      '- Your novelty claim must be specific and defensible against NAMED prior work, not generic.',
      { label: 'design:' + angle.key, phase: 'Design', schema: DESIGN_SCHEMA, effort: 'high' }
    )
  },
  function (design, angle) {
    if (!design) return null
    const designText =
      'DESIGN: ' + design.name + '\n' + design.one_line +
      '\n\nCORE IDEA: ' + design.core_idea +
      '\n\nNODE/EDGE MODEL: ' + design.node_and_edge_model +
      '\n\nSCHEMA: ' + design.concrete_schema +
      '\n\nINTERVALS: ' + design.interval_representation +
      '\n\nORDERING CONFLICT: ' + design.how_ordering_conflict_works +
      '\n\nGRANULARITY CONFLICT: ' + design.how_granularity_conflict_works +
      '\n\nINTERFACE TO P3/P4: ' + design.interface_to_phase3_and_phase4 +
      '\n\nNOVELTY CLAIM: ' + design.novelty_claim +
      '\n\nEFFORT (person-days): ' + design.effort_days_for_one_person +
      '\n\nBUILD STEPS: ' + design.build_steps.join(' | ') +
      '\n\nRISKS: ' + design.risks.join(' | ') +
      '\n\nGIVES UP: ' + design.what_it_gives_up
    return agent(
      'You are a hostile reviewer judging one candidate design on THREE lenses. Score each 1-10; a score above 7 must be earned. Default to skepticism.\n\n' +
      'LENS 1 FEASIBILITY IN 45 DAYS: 3 grad students; the user (Nhut) owns Phase 2 alone; TIMEX normalisation is unbuilt and blocks everything (though measured at ~1 week, see facts). Penalise unbuilt infrastructure, new model training, scale annotation, and anything forcing the other two members to change approach. Name which build steps will slip.\n\n' +
      'LENS 2 NOVELTY FOR COLING 2027 (CORE B): you are a skeptical area chair. Attack the novelty claim directly and name specific prior work that undercuts it. Would this survive review, or does it reduce to "we applied PaTeCon to events" / "yet another event KG"? State the strongest defensible claim that remains.\n\n' +
      'LENS 3 EFFECTIVENESS AND SOUNDNESS: gold is 100% transitively closed with ~72 genuine contradictions; only 44.9% of events have a tight TIMEX anchor; ~55% will evaluate to unknown; entities are document-local; 59.9% of arguments are unlinked spans. Will this design produce enough evaluable instances? Will its conflicts be real or artefacts of TIMEX normalisation error? Is the evaluation non-circular? Be quantitative.\n\n' +
      FACTS + '\n\nTHE DESIGN UNDER REVIEW:\n' + designText,
      { label: 'judge:' + angle.key, phase: 'Design', schema: VERDICT_SCHEMA, effort: 'medium' }
    ).then(function (v) {
      return { angle: angle.key, design: design, designText: designText, verdict: v }
    })
  }
)

const alive = judged.filter(function (d) { return d && d.verdict })
log('Judged ' + alive.length + '/5 designs. Overall: ' + alive.map(function (d) { return d.angle + '=' + d.verdict.overall }).join(', '))

// ---------------- SYNTHESIS ----------------
phase('Synthesize')

const allDesignsText = alive.map(function (d) {
  const v = d.verdict
  return '===== ' + d.angle + ' =====\n' + d.designText +
    '\n\n--- HOSTILE VERDICT (feasibility ' + v.feasibility_45d + '/10, novelty ' + v.novelty_coling + '/10, effectiveness ' + v.effectiveness + '/10, OVERALL ' + v.overall + '/10) ---\n' +
    v.verdict +
    '\n  FATAL: ' + (v.fatal_flaws.length ? v.fatal_flaws.join(' | ') : 'none') +
    '\n  FIXABLE: ' + (v.fixable_issues.length ? v.fixable_issues.join(' | ') : 'none') +
    '\n  PRIOR WORK UNDERCUTTING NOVELTY: ' + (v.prior_work_that_undercuts_novelty.length ? v.prior_work_that_undercuts_novelty.join(' | ') : 'none named') +
    '\n  STRONGEST SURVIVING CLAIM: ' + v.strongest_defensible_claim
}).join('\n\n')

const synthesis = await agent(
  'You are the senior advisor to the TempEKG team. Produce the FINAL DECISION DOCUMENT for Nhut, who owns Phase 2 (Graph Construction), with 45 days to the COLING 2027 deadline.\n\n' +
  FACTS +
  '\n\nRESEARCH GATHERED:\n' + researchDigest +
  '\n\nFIVE CANDIDATE DESIGNS WITH HOSTILE VERDICTS:\n' + allDesignsText +
  '\n\nBefore writing, do your own hostile novelty pass: across all five designs, identify which single novelty claim you could NOT undercut with named prior work, and why it survives.\n\n' +
  'Then write the document with these sections:\n' +
  '1. COMPARISON TABLE of the five designs: feasibility(45d) / novelty / effectiveness / effort-days / what it gives up.\n' +
  '2. RECOMMENDED DESIGN - pick ONE as primary, justify against the hostile verdicts, and explicitly graft the best surviving ideas from the runners-up into it. Say exactly what is grafted and why.\n' +
  '3. CONCRETE PHASE-2 SPEC for Nhut: exact schema with field names, exact interval representation, exact interface handed to Phase 3 (Vinh) and Phase 4 (Nhan), with worked examples using real MAVEN event types.\n' +
  '4. THE NOVELTY CLAIM that survives hostile review, written as it would appear in the paper abstract, plus two backup claims.\n' +
  '5. NON-CIRCULAR EVALUATION PROTOCOL replacing the broken fake-conflict plan.\n' +
  '6. 45-DAY SCHEDULE week by week, naming who does what across the 3 people, with explicit go/no-go gates.\n' +
  '7. ALTERNATIVE OPTIONS if the user disagrees with the primary recommendation - at least 2 fully-specified fallbacks with trade-offs.\n' +
  '8. WHAT TO CUT - ruthless and explicit.\n\n' +
  'Be concrete, quantitative and opinionated. This is a decision document, not a survey. Use the measured numbers throughout. Do not hedge.',
  { label: 'final-plan', phase: 'Synthesize', effort: 'high' }
)

return {
  scores: alive.map(function (d) {
    return {
      angle: d.angle,
      feasibility: d.verdict.feasibility_45d,
      novelty: d.verdict.novelty_coling,
      effectiveness: d.verdict.effectiveness,
      overall: d.verdict.overall,
    }
  }),
  designs: alive.map(function (d) { return d.design }),
  verdicts: alive.map(function (d) { return d.verdict }),
  research: research,
  plan: synthesis,
}
