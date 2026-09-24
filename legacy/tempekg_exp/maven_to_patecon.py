"""Chuyen MAVEN sang dung format PaTeCon de chay CODE CUA HO tren DU LIEU CUA MINH.

Phep chieu entity-as-subject (da chung minh la dung o MODEL.md menh de 1-2):
    subject  = entity_id
    property = EventType#Role
    object   = event_id
    start/end= khoang thoi gian cua EVENT, lay tu TIMEX anchor bare-year

Chi giu event co anchor nam giai duoc bang regex (khong can normaliser day du).
"""
import json, zipfile, io, re, collections, sys

OUT = sys.argv[1] if len(sys.argv) > 1 else 'patecon/resource/MAVEN.tsv'

# ---- 1. lay nam neo cho tung event tu MAVEN-ERE ----
ev_year = {}
ev_type = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        yr = {}
        for t in d['TIMEX']:
            m = re.match(r'^(\d{3,4})$', t['mention'].strip())
            if m:
                yr[t['id']] = int(m.group(1))
        ids = {e['id'] for e in d['events']}
        for e in d['events']:
            ev_type[e['id']] = e['type']
        anchor = collections.defaultdict(set)
        for h, t in d['temporal_relations'].get('CONTAINS', []):
            if h in yr and t in ids:
                anchor[t].add(yr[h])
            if t in yr and h in ids:
                anchor[h].add(yr[t])
        for eid, ys in anchor.items():
            if len(ys) == 1:                       # chi giu neo khong mau thuan
                y = next(iter(ys))
                ev_year[eid] = (y * 100 + 1, y * 100 + 12)   # YYYYMM

print('event co neo nam duy nhat: %d' % len(ev_year))

# ---- 2. sinh fact (entity, EventType#Role, event, start, end) ----
z = zipfile.ZipFile('MAVEN-Arg.zip')
rows = []
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            for e in d['events']:
                if e['id'] not in ev_year:
                    continue
                st, en = ev_year[e['id']]
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' not in v:
                            continue
                        prop = e['type'] + '#' + r
                        rows.append('%s\t%s\t%s\t%d\t%d'
                                    % (v['entity_id'], prop, e['id'], st, en))

open(OUT, 'w', encoding='utf-8').write('\n'.join(rows))
props = {r.split('\t')[1] for r in rows}
subj = {r.split('\t')[0] for r in rows}
print('viet %s' % OUT)
print('  facts      : %d' % len(rows))
print('  subjects   : %d' % len(subj))
print('  properties : %d' % len(props))
print('  sample:')
for r in rows[:3]:
    print('    ', r)
