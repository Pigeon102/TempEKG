"""EXP21 - SU KIEN LAP LAI: mutual exclusion tren do thi event co hop le khong?

Nguoi dung chi ra: hop thuong nien, giai dau hang nam... cung entity, cung LOAI event,
thoi gian KHAC nhau -> KHONG phai loi. Nhung PaTeCon se gan co la conflict.

Doi chieu voi Wikidata: P569 (ngay sinh) THAT SU la ham - chi mot gia tri.
                        MAVEN Competition thi KHONG - lap lai la binh thuong.

Do: trong cac cap (entity, event_type) co >=2 event, bao nhieu la LAP LAI HOP LE?
Dau hieu lap lai: cac lan xay ra o cac NAM KHAC NHAU va cach deu / rai rac.
"""
import json, zipfile, io, re, collections

# nam neo cho tung event
ev_year, ev_type = {}, {}
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
        anc = collections.defaultdict(set)
        for h, t in d['temporal_relations'].get('CONTAINS', []):
            if h in yr and t in ids:
                anc[t].add(yr[h])
            if t in yr and h in ids:
                anc[h].add(yr[t])
        for eid, ys in anc.items():
            if len(ys) == 1:
                ev_year[eid] = next(iter(ys))

# (entity, event_type) -> cac nam
z = zipfile.ZipFile('MAVEN-Arg.zip')
key2years = collections.defaultdict(list)
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            for e in d['events']:
                if e['id'] not in ev_year:
                    continue
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            key2years[(v['entity_id'], e['type'])].append(ev_year[e['id']])

multi = {k: sorted(set(v)) for k, v in key2years.items() if len(set(v)) >= 2}
print('cap (entity, event_type) co >=2 NAM khac nhau: %d' % len(multi))
print('  -> PaTeCon se coi TAT CA la vi pham MutualExclusion')
print()

# phan loai
span = collections.Counter()
by_type = collections.Counter()
for (ent, typ), ys in multi.items():
    s = max(ys) - min(ys)
    if s == 0:
        span['cung nam'] += 1
    elif s <= 2:
        span['cach <=2 nam'] += 1
    elif s <= 10:
        span['cach 3-10 nam'] += 1
    else:
        span['cach >10 nam'] += 1
    by_type[typ] += 1

tot = len(multi)
print('%-20s %8s %8s' % ('khoang cach nam', 'so cap', 'ti le'))
for k in ('cung nam', 'cach <=2 nam', 'cach 3-10 nam', 'cach >10 nam'):
    print('  %-18s %8d %7.1f%%' % (k, span[k], 100 * span[k] / tot))
print()
print('LOAI EVENT hay lap lai nhat (dau hieu su kien dinh ky):')
for t, n in by_type.most_common(12):
    ex = [k for k in multi if k[1] == t][:1]
    yrs = multi[ex[0]] if ex else []
    print('   %-26s %4d cap   vd nam: %s' % (t, n, yrs[:6]))
print()
rec = span['cach 3-10 nam'] + span['cach >10 nam']
print('=> Cap cach nhau >=3 nam: %d (%.1f%%) - RAT KHO la loi annotation,'
      % (rec, 100 * rec / tot))
print('   nhieu kha nang la SU KIEN LAP LAI hop le.')
