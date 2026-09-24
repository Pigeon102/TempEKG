"""Extract the 12 completed agent results from the killed workflow run and emit:
  recovered/recovered.json   - raw results keyed by sweep/angle
  recovered/payload.json     - prompt-ready text blocks
  RECOVERED_RESULTS.md       - human-readable dump of everything recovered
  tempekg_finish.js          - workflow script that runs ONLY the 3 missing agents
  tempekg_full.js            - copy of the original full 15-agent script
"""
import json, os, shutil

JP = r'C:/Users/Phuong Di/.claude/projects/c--Reseach-Quang/121e49c8-a548-4e96-ac26-15a32ec657f0/subagents/workflows/wf_43a75668-138/journal.jsonl'
SP = r'C:/Users/Phuong Di/.claude/projects/c--Reseach-Quang/121e49c8-a548-4e96-ac26-15a32ec657f0/workflows/scripts/tempekg-phase2-lean.js'
OUT = r'C:/Reseach_Quang/tempekg_handoff'
os.makedirs(os.path.join(OUT, 'recovered'), exist_ok=True)

rs = []
for line in open(JP, encoding='utf-8'):
    line = line.strip()
    if not line:
        continue
    d = json.loads(line)
    if d.get('type') == 'result':
        rs.append(d['result'])

research, designs, verdicts = [], [], []
for r in rs:
    if not isinstance(r, dict):
        continue
    if 'findings' in r:
        research.append(r)
    elif 'name' in r:
        designs.append(r)
    elif 'overall' in r:
        verdicts.append(r)


def sweep_key(r):
    # classify on the FIRST finding only - each sweep's lead claim is distinctive,
    # whereas whole-blob matching collides (MaxSAT/AMIE/etc appear in several sweeps).
    lead = (r['findings'][0]['claim'] + ' ' + r['findings'][0]['why_it_matters_for_tempekg']).lower()
    if 'granularity' in lead or 'bettini' in lead:
        return 'time-granularity'
    if 'support' in lead or 'confidence' in lead or 'amie' in lead or 'atomicity' in lead:
        return 'constraint-mining'
    if 'reification' in lead or 'rdf-star' in lead or 'n-ary' in lead:
        return 'representation'
    return 'consistency-benchmark'


research_by = {}
for r in research:
    k = sweep_key(r)
    if k in research_by:            # never silently drop a sweep
        n = 2
        while (k + '-' + str(n)) in research_by:
            n += 1
        k = k + '-' + str(n)
    research_by[k] = r
assert len(research_by) == len(research), (len(research_by), len(research))


def angle_of(d):
    n = d['name'].lower()
    if 'starcast' in n:
        return 'A-projection-faithful'
    if 'hedge' in n or 'hyperedge' in n:
        return 'B-nary-hypergraph'
    if 'constraint network' in n or n.startswith('ecn'):
        return 'C-constraint-network'
    if 'prov-eckg' in n or 'provenance' in n:
        return 'D-provenance-multiversion'
    return 'E-granularity-lattice'


design_by = {angle_of(d): d for d in designs}

vmap = {}
for v in verdicts:
    t = (v['feasibility_45d'], v['novelty_coling'], v['effectiveness'])
    if t == (5, 4, 4):
        vmap['A-projection-faithful'] = v
    elif t == (5, 3, 6):
        vmap['C-constraint-network'] = v
    elif t == (4, 5, 4):
        vmap['E-granularity-lattice'] = v

json.dump({'research_by_sweep': research_by, 'designs_by_angle': design_by, 'verdicts_by_angle': vmap},
          open(os.path.join(OUT, 'recovered', 'recovered.json'), 'w', encoding='utf-8', newline='\n'),
          indent=1, ensure_ascii=False)

src = open(SP, encoding='utf-8').read()
FACTS = src.split('const FACTS = `', 1)[1].split('`\n', 1)[0]


def digest(r):
    return ('FINDINGS:\n'
            + '\n'.join('- ' + f['claim'] + ' [WHY: ' + f['why_it_matters_for_tempekg'] + ']' for f in r['findings'])
            + '\nKEY PAPERS:\n'
            + '\n'.join('- ' + p['title'] + ' (' + str(p.get('venue_year', '?')) + ') ' + str(p.get('url', '')) + ' - ' + p['relevance'] for p in r['key_papers'])
            + '\nREUSABLE: ' + '; '.join(r['reusable_techniques'])
            + '\nNOVELTY GAPS: ' + '; '.join(r['novelty_gaps']))


RESEARCH_DIGEST = '\n\n'.join('### Sweep ' + k + '\n' + digest(v) for k, v in research_by.items())

FIELDS = [
    ('CORE IDEA', 'core_idea', 2600),
    ('NODE/EDGE MODEL', 'node_and_edge_model', 1800),
    ('SCHEMA', 'concrete_schema', 2200),
    ('INTERVALS', 'interval_representation', 1800),
    ('ORDERING CONFLICT', 'how_ordering_conflict_works', 1500),
    ('GRANULARITY CONFLICT', 'how_granularity_conflict_works', 1500),
    ('INTERFACE TO P3/P4', 'interface_to_phase3_and_phase4', 1500),
    ('NOVELTY CLAIM', 'novelty_claim', 1400),
]


def design_text(d, limit=None):
    out = ['DESIGN: ' + d['name'], d['one_line']]
    for label, key, cap in FIELDS:
        v = d.get(key) or ''
        if limit and len(v) > cap:
            v = v[:cap] + ' ...[truncated]'
        out.append('\n' + label + ': ' + v)
    out.append('\nEFFORT (person-days): ' + str(d['effort_days_for_one_person']))
    bs = ' | '.join(d['build_steps'])
    rk = ' | '.join(d['risks'])
    gu = d['what_it_gives_up']
    if limit:
        bs, rk, gu = bs[:1400], rk[:1200], gu[:900]
    out.append('\nBUILD STEPS: ' + bs)
    out.append('\nRISKS: ' + rk)
    out.append('\nGIVES UP: ' + gu)
    return '\n'.join(out)


def verdict_text(v):
    return ('HOSTILE VERDICT (feasibility ' + str(v['feasibility_45d']) + '/10, novelty '
            + str(v['novelty_coling']) + '/10, effectiveness ' + str(v['effectiveness'])
            + '/10, OVERALL ' + str(v['overall']) + '/10)\n' + v['verdict']
            + '\n  FATAL: ' + (' | '.join(v['fatal_flaws']) or 'none')
            + '\n  FIXABLE: ' + (' | '.join(v['fixable_issues']) or 'none')
            + '\n  PRIOR WORK UNDERCUTTING NOVELTY: ' + (' | '.join(v['prior_work_that_undercuts_novelty']) or 'none named')
            + '\n  STRONGEST SURVIVING CLAIM: ' + v['strongest_defensible_claim'])


payload = {
    'FACTS': FACTS,
    'RESEARCH_DIGEST': RESEARCH_DIGEST,
    'DESIGNS_FULL': {k: design_text(v) for k, v in design_by.items()},
    'DESIGNS_CONDENSED': {k: design_text(v, limit=True) for k, v in design_by.items()},
    'VERDICTS_DONE': {k: verdict_text(v) for k, v in vmap.items()},
}
json.dump(payload, open(os.path.join(OUT, 'recovered', 'payload.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False)

# The embedded script must stay under the 512 KB Workflow limit. Full design text is
# only needed for the two designs still awaiting a judge; the synthesis reads condensed.
MISSING_ANGLES = [a for a in design_by if a not in vmap]
embed = dict(payload)
embed['DESIGNS_FULL'] = {k: v for k, v in payload['DESIGNS_FULL'].items() if k in MISSING_ANGLES}

# ---- human-readable dump ----
md = ['# Recovered results from workflow run wf_43a75668-138',
      '',
      '12 of 15 agents completed before the session limit killed the run.',
      'Missing: `judge:B-nary-hypergraph`, `judge:D-provenance-multiversion`, `final-plan`.',
      '',
      '## Judge scores (completed)', '',
      '| Design | Feasibility 45d | Novelty COLING | Effectiveness | Overall |',
      '|---|---|---|---|---|']
for k, v in vmap.items():
    md.append('| ' + k + ' | ' + str(v['feasibility_45d']) + ' | ' + str(v['novelty_coling'])
              + ' | ' + str(v['effectiveness']) + ' | **' + str(v['overall']) + '** |')
md += ['| B-nary-hypergraph | — | — | — | *not judged* |',
       '| D-provenance-multiversion | — | — | — | *not judged* |', '']
md += ['## The five designs', '']
for k in sorted(design_by):
    md += ['### ' + k, '', '```', design_text(design_by[k]), '```', '']
md += ['## Hostile verdicts (3 of 5)', '']
for k in sorted(vmap):
    md += ['### ' + k, '', '```', verdict_text(vmap[k]), '```', '']
md += ['## Research digest (all 4 sweeps)', '', '```', RESEARCH_DIGEST, '```', '']
open(os.path.join(OUT, 'RECOVERED_RESULTS.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(md))

# ---- emit the finish script ----
DATA = json.dumps(embed, ensure_ascii=True)
js = '''export const meta = {
  name: 'tempekg-finish',
  description: 'Finish the killed TempEKG design panel: judge the 2 unjudged designs, then synthesize the final 45-day decision document',
  phases: [
    { title: 'Judge', detail: 'hostile 3-lens verdicts for the 2 designs that were never judged' },
    { title: 'Synthesize', detail: 'final decision document over all 5 designs and 5 verdicts' },
  ],
}

// All 12 recovered agent results from run wf_43a75668-138, inlined so nothing is recomputed.
const DATA = %s

const FACTS = DATA.FACTS
const RESEARCH_DIGEST = DATA.RESEARCH_DIGEST

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

const JUDGE_PREAMBLE =
  'You are a hostile reviewer judging one candidate design on THREE lenses. Score each 1-10; a score above 7 must be earned. Default to skepticism.\\n\\n' +
  'LENS 1 FEASIBILITY IN 45 DAYS: 3 grad students; the user (Nhut) owns Phase 2 alone; TIMEX normalisation is unbuilt and blocks everything (measured at ~1 week, see facts). Penalise unbuilt infrastructure, new model training, scale annotation, and anything forcing the other two members to change approach. Name which build steps will slip.\\n\\n' +
  'LENS 2 NOVELTY FOR COLING 2027 (CORE B): you are a skeptical area chair. Attack the novelty claim directly and name specific prior work that undercuts it. Would this survive review, or does it reduce to "we applied PaTeCon to events" / "yet another event KG"? State the strongest defensible claim that remains.\\n\\n' +
  'LENS 3 EFFECTIVENESS AND SOUNDNESS: gold is 100%% transitively closed with ~72 genuine contradictions; only 44.9%% of events have a tight TIMEX anchor; ~55%% will evaluate to unknown; entities are document-local; 59.9%% of arguments are unlinked spans. Will this design produce enough evaluable instances? Will its conflicts be real or artefacts of TIMEX normalisation error? Is the evaluation non-circular? Be quantitative.\\n\\n'

// ---------------- JUDGE the 2 missing ----------------
phase('Judge')

const MISSING = ['B-nary-hypergraph', 'D-provenance-multiversion']

const fresh = await parallel(MISSING.map(function (angle) {
  return function () {
    return agent(
      JUDGE_PREAMBLE + FACTS + '\\n\\nTHE DESIGN UNDER REVIEW:\\n' + DATA.DESIGNS_FULL[angle],
      { label: 'judge:' + angle, phase: 'Judge', schema: VERDICT_SCHEMA, effort: 'medium' }
    )
  }
}))

const freshMap = {}
MISSING.forEach(function (a, i) { if (fresh[i]) freshMap[a] = fresh[i] })
log('New verdicts: ' + Object.keys(freshMap).join(', '))

function verdictText(v) {
  return 'HOSTILE VERDICT (feasibility ' + v.feasibility_45d + '/10, novelty ' + v.novelty_coling +
    '/10, effectiveness ' + v.effectiveness + '/10, OVERALL ' + v.overall + '/10)\\n' + v.verdict +
    '\\n  FATAL: ' + (v.fatal_flaws.join(' | ') || 'none') +
    '\\n  FIXABLE: ' + (v.fixable_issues.join(' | ') || 'none') +
    '\\n  PRIOR WORK UNDERCUTTING NOVELTY: ' + (v.prior_work_that_undercuts_novelty.join(' | ') || 'none named') +
    '\\n  STRONGEST SURVIVING CLAIM: ' + v.strongest_defensible_claim
}

const ANGLES = ['A-projection-faithful', 'B-nary-hypergraph', 'C-constraint-network', 'D-provenance-multiversion', 'E-granularity-lattice']
const allText = ANGLES.map(function (a) {
  const v = DATA.VERDICTS_DONE[a] || (freshMap[a] ? verdictText(freshMap[a]) : 'NOT JUDGED')
  return '===== ' + a + ' =====\\n' + DATA.DESIGNS_CONDENSED[a] + '\\n\\n--- ' + v
}).join('\\n\\n')

// ---------------- SYNTHESIZE ----------------
phase('Synthesize')

const plan = await agent(
  'You are the senior advisor to the TempEKG team. Produce the FINAL DECISION DOCUMENT for Nhut, who owns Phase 2 (Graph Construction), with 45 days to the COLING 2027 deadline.\\n\\n' +
  FACTS +
  '\\n\\nRESEARCH GATHERED (4 sweeps):\\n' + RESEARCH_DIGEST +
  '\\n\\nFIVE CANDIDATE DESIGNS WITH HOSTILE VERDICTS:\\n' + allText +
  '\\n\\nNote: every design scored 4-4.5/10 overall from the hostile judges. Do NOT simply pick the highest scorer and declare victory - the judges are telling you the whole framing needs repair. Your job is to build the best achievable plan from these parts, including rejecting a design outright if warranted.\\n\\n' +
  'Before writing, do your own hostile novelty pass: across all five designs, identify which single novelty claim you could NOT undercut with named prior work, and why it survives.\\n\\n' +
  'Then write the document with these sections:\\n' +
  '1. COMPARISON TABLE of the five designs: feasibility(45d) / novelty / effectiveness / effort-days / what it gives up.\\n' +
  '2. RECOMMENDED DESIGN - pick ONE as primary, justify against the hostile verdicts, and explicitly graft the best surviving ideas from the runners-up into it. Say exactly what is grafted and why.\\n' +
  '3. CONCRETE PHASE-2 SPEC for Nhut: exact schema with field names, exact interval representation, exact interface handed to Phase 3 (Vinh) and Phase 4 (Nhan), with worked examples using real MAVEN event types.\\n' +
  '4. THE NOVELTY CLAIM that survives hostile review, written as it would appear in the paper abstract, plus two backup claims.\\n' +
  '5. NON-CIRCULAR EVALUATION PROTOCOL replacing the broken fake-conflict plan.\\n' +
  '6. 45-DAY SCHEDULE week by week, naming who does what across the 3 people, with explicit go/no-go gates.\\n' +
  '7. ALTERNATIVE OPTIONS if the user disagrees with the primary recommendation - at least 2 fully-specified fallbacks with trade-offs.\\n' +
  '8. WHAT TO CUT - ruthless and explicit.\\n\\n' +
  'Be concrete, quantitative and opinionated. This is a decision document, not a survey. Use the measured numbers throughout. Do not hedge.',
  { label: 'final-plan', phase: 'Synthesize', effort: 'high' }
)

return { new_verdicts: freshMap, plan: plan }
''' % DATA

open(os.path.join(OUT, 'tempekg_finish.js'), 'w', encoding='utf-8', newline='\n').write(js)
shutil.copyfile(SP, os.path.join(OUT, 'tempekg_full.js'))

print('research sweeps :', list(research_by))
print('designs         :', list(design_by))
print('verdicts done   :', list(vmap))
print('MISSING judges  :', [a for a in design_by if a not in vmap])
print()
print('FACTS chars           :', len(FACTS))
print('RESEARCH_DIGEST chars :', len(RESEARCH_DIGEST))
print('DESIGNS_FULL chars    :', sum(len(v) for v in payload['DESIGNS_FULL'].values()))
print('DESIGNS_COND chars    :', sum(len(v) for v in payload['DESIGNS_CONDENSED'].values()))
print('VERDICTS chars        :', sum(len(v) for v in payload['VERDICTS_DONE'].values()))
print('finish.js chars       :', len(js))
