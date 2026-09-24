import json, os

JP = r'C:/Users/Phuong Di/.claude/projects/c--Reseach-Quang/121e49c8-a548-4e96-ac26-15a32ec657f0/subagents/workflows/wf_504d3def-763/journal.jsonl'
OUT = r'C:/Reseach_Quang/tempekg_handoff'

rs = []
for line in open(JP, encoding='utf-8'):
    line = line.strip()
    if not line:
        continue
    d = json.loads(line)
    if d.get('type') == 'result':
        rs.append(d['result'])

plan = None
verdicts = []
for r in rs:
    if isinstance(r, str):
        plan = r
    elif isinstance(r, dict) and 'overall' in r:
        verdicts.append(r)

print('results:', len(rs), '| verdicts:', len(verdicts), '| plan chars:', len(plan) if plan else 0)


def vtext(v):
    return ('feasibility_45d=' + str(v['feasibility_45d'])
            + '  novelty_coling=' + str(v['novelty_coling'])
            + '  effectiveness=' + str(v['effectiveness'])
            + '  OVERALL=' + str(v['overall'])
            + '\n\nVERDICT:\n' + v['verdict']
            + '\n\nFATAL FLAWS:\n' + '\n'.join('- ' + x for x in v['fatal_flaws'])
            + '\n\nFIXABLE:\n' + '\n'.join('- ' + x for x in v['fixable_issues'])
            + '\n\nPRIOR WORK UNDERCUTTING NOVELTY:\n' + '\n'.join('- ' + x for x in v['prior_work_that_undercuts_novelty'])
            + '\n\nSTRONGEST DEFENSIBLE CLAIM:\n' + v['strongest_defensible_claim'])


md = ['# TempEKG — Final decision document', '',
      'Produced by workflow run `wf_504d3def-763` (2 hostile judges + synthesis) over the 12 recovered',
      'results of run `wf_43a75668-138`. All five designs are now judged.', '',
      '---', '', '## Part 1 — The two late verdicts', '']
for v in verdicts:
    ov = v['overall']
    md += ['### ' + ('B-nary-hypergraph (HEDGE)' if ov == 3 else 'D-provenance-multiversion (PROV-ECKG)'),
           '', '```', vtext(v), '```', '']
md += ['---', '', '## Part 2 — Final plan', '', plan or '(no plan returned)']
open(os.path.join(OUT, 'FINAL_PLAN.md'), 'w', encoding='utf-8', newline='\n').write('\n'.join(md))
print('wrote FINAL_PLAN.md')

# also dump the plan alone for quick reading
open(os.path.join(OUT, 'FINAL_PLAN_only.md'), 'w', encoding='utf-8', newline='\n').write(plan or '')
for v in verdicts:
    print()
    print('=== overall', v['overall'], '===')
    print('claim:', v['strongest_defensible_claim'][:400])
