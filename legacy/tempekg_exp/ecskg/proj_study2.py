"""Do lai: nhom chi CO ICH khi >=2 statement den tu >=2 EVENT KHAC NHAU.

Hai statement cung mot event thi cung mot khoang thoi gian -> disjoint()/before()
luon tam thuong. Support cau truc khong dong nghia voi support thoi gian.
"""
import json, collections, zipfile, io

SUP = 100
z = zipfile.ZipFile('MAVEN-Arg.zip')
events = []
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            for e in d['events']:
                roles = collections.defaultdict(list)
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            roles[r].append('%s:%s' % (d['id'], v['entity_id']))
                if roles:
                    events.append((d['id'], e['id'], e['type'], dict(roles)))


def project(mode):
    out = []
    for doc, eid, T, roles in events:
        ev = '%s:%s' % (doc, eid)
        if mode == 'P1':
            for r, xs in roles.items():
                for x in xs:
                    out.append((x, '%s.%s' % (T, r), ev, ev))
        else:
            items = [(r, x) for r, xs in roles.items() for x in xs]
            for i in range(len(items)):
                for j in range(len(items)):
                    if i == j: continue
                    r1, x = items[i]; r2, y = items[j]
                    if x == y: continue
                    rel = {'P2': '%s.%s>%s' % (T, r1, r2),
                           'P3': '%s>%s' % (r1, r2), 'P4': T}[mode]
                    out.append((x, rel, y, ev))
    return out


print('%-4s %-24s | %6s %8s | %-19s | %-19s | %8s'
      % ('', 'tu vung r', '|R|', 'stmt', 'SP1 (a,r) >=2 event', 'SP2 (b,r) >=2 event', 'SP3 ent'))
print('-'*106)
detail = {}
for mode, desc in [('P1', 'T.role  entity->event'),
                   ('P2', 'T.r1>r2 entity->entity'),
                   ('P3', 'r1>r2   bo kieu event'),
                   ('P4', 'T       bo vai')]:
    st = project(mode)
    rels = collections.Counter(r for _, r, _, _ in st)
    g1 = collections.defaultdict(set)      # (a,r) -> {event}
    g2 = collections.defaultdict(set)      # (b,r) -> {event}
    er = collections.defaultdict(set)
    r_ev1 = collections.defaultdict(set)   # r -> so nhom SP1 co ich
    for a, r, b, ev in st:
        g1[(a, r)].add(ev)
        g2[(b, r)].add(ev)
        er[a].add(r)
    sp1 = sum(1 for v in g1.values() if len(v) >= 2)
    sp2 = sum(1 for v in g2.values() if len(v) >= 2)
    sp3 = sum(1 for v in er.values() if len(v) >= 2)
    for (a, r), v in g1.items():
        if len(v) >= 2:
            r_ev1[r].add(a)
    big = sum(1 for r in r_ev1 if len(r_ev1[r]) >= SUP)
    detail[mode] = (rels, r_ev1)
    print('%-4s %-24s | %6d %8d | %8d nhom      | %8d nhom      | %8d'
          % (mode, desc, len(rels), len(st), sp1, sp2, sp3, ))
    print('%-4s %-24s | %6s %8s | %8d quan he dat sup>=%d          |'
          % ('', '', '', '', big, SUP))

print()
print('SP1 = (entity, r) xuat hien o >=2 EVENT khac nhau  -> functional co nghia')
print('SP2 = (entity duoi, r) o >=2 EVENT khac nhau       -> inverse functional co nghia')
print()
for mode in ('P1', 'P2'):
    rels, r_ev1 = detail[mode]
    print('%s — 10 quan he co nhieu nhom SP1 co ich nhat:' % mode)
    for r, s in sorted(r_ev1.items(), key=lambda x: -len(x[1]))[:10]:
        print('    %5d entity | %s' % (len(s), r))
    print()
