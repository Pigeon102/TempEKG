"""Chon PHEP CHIEU tu do thi event-centric sang dang statement cua PaTeCon.

PaTeCon can (a, r, b, t1, t2). Do thi cua ta la sieu canh co nhan vai:
    event e  kieu T  vai rho: R -> entities  khoang [t1,t2]

Bon phep chieu ung vien, khac nhau o TU VUNG QUAN HE r:

  P1  entity -> event      r = T.role              (a=entity, b=event)
  P2  entity -> entity     r = T.role1>role2       (a,b la hai entity trong cung event)
  P3  entity -> entity     r = role1>role2         (bo kieu event)
  P4  entity -> entity     r = T                   (bo vai)

Do cho tung phep chieu:
   - |R| : kich thuoc tu vung quan he
   - so statement
   - so nhom (a, r) co >=2 statement  <- DON VI SUPPORT cua PaTeCon (SP1)
   - so quan he vuot support_threshold=100
   - SP2: nhom (b, r) co >=2
   - SP3: entity xuat hien o >=2 quan he KHAC nhau

Day la cau hoi CAU TRUC, chua dinh den thoi gian.
"""
import json, collections, zipfile, io, sys

SUP = 100          # support_threshold cua PaTeCon

z = zipfile.ZipFile('MAVEN-Arg.zip')
events = []        # (doc, eid, etype, {role: [entity]})
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

n_ev = len(events)
n_role_types = len({r for _, _, _, rr in events for r in rr})
n_etypes = len({t for _, _, t, _ in events})
print('event co it nhat 1 vai co entity : %d' % n_ev)
print('kieu event                       : %d' % n_etypes)
print('vai                              : %d' % n_role_types)
print('tich ly thuyet T x vai           : %d' % (n_etypes*n_role_types))
print()


def project(mode):
    """-> list of (a, r, b, key_event)"""
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
                    if i == j:
                        continue
                    r1, x = items[i]; r2, y = items[j]
                    if x == y:
                        continue
                    if mode == 'P2':
                        rel = '%s.%s>%s' % (T, r1, r2)
                    elif mode == 'P3':
                        rel = '%s>%s' % (r1, r2)
                    else:
                        rel = T
                    out.append((x, rel, y, ev))
    return out


print('%-4s %-26s %9s %10s %9s %8s %8s %8s'
      % ('', 'tu vung r', '|R|', 'statement', 'SP1>=2', 'r>=100', 'SP2>=2', 'SP3 ent'))
print('-'*94)

rows = {}
for mode, desc in [('P1', 'T.role  (entity->event)'),
                   ('P2', 'T.r1>r2 (entity->entity)'),
                   ('P3', 'r1>r2   (bo kieu event)'),
                   ('P4', 'T       (bo vai)')]:
    st = project(mode)
    rels = collections.Counter(r for _, r, _, _ in st)
    # SP1: nhom (a, r) co >=2 statement khac nhau
    g1 = collections.defaultdict(set)
    g2 = collections.defaultdict(set)
    ent_rels = collections.defaultdict(set)
    for a, r, b, ev in st:
        g1[(a, r)].add(b)
        g2[(b, r)].add(a)
        ent_rels[a].add(r)
    sp1 = sum(1 for v in g1.values() if len(v) >= 2)
    sp2 = sum(1 for v in g2.values() if len(v) >= 2)
    sp3 = sum(1 for v in ent_rels.values() if len(v) >= 2)
    big = sum(1 for c in rels.values() if c >= SUP)
    rows[mode] = (len(rels), len(st), sp1, big, sp2, sp3)
    print('%-4s %-26s %9d %10d %9d %8d %8d %8d'
          % (mode, desc, len(rels), len(st), sp1, big, sp2, sp3))

print()
print('SP1>=2  : so nhom (entity, r) co >=2 event  -> don vi support cua constraint functional')
print('r>=100  : so quan he dat support_threshold cua PaTeCon')
print('SP2>=2  : so nhom (entity_duoi, r) co >=2 dau  -> inverse functional')
print('SP3 ent : so entity nam trong >=2 quan he khac nhau -> zero-hop order')

# ---- phan bo support cua P1 va P3 ----
for mode in ('P1', 'P3'):
    st = project(mode)
    rels = collections.Counter(r for _, r, _, _ in st)
    print('\n10 quan he lon nhat cua %s:' % mode)
    for r, c in rels.most_common(10):
        print('    %6d  %s' % (c, r))
