"""Kieu ENTITY thay duoc VAI khong? — va no co phai truc dung cua PaTeCon khong.

Ly do can do:
  1. kieu entity de lay tu text hon vai rat nhieu (NER << SRL)
  2. MAVEN-Arg cho san 7 kieu
  3. `class_type` trong refinement cua PaTeCon CHINH LA kieu entity
     -> dung kieu entity la DUNG TRUC cua ho, khong phai xap xi

Do ba viec:
  A. kieu entity xac dinh vai den muc nao (cho truoc kieu event)
  B. so khoa va support: (T, vai) so voi (T, kieu_entity)
  C. support cho phep chieu P2 tuong ung
"""
import json, zipfile, io, collections, itertools, math

z = zipfile.ZipFile('MAVEN-Arg.zip')
ent_type = {}          # (doc, entity_id) -> type
recs = []              # (doc, eid, T, role, entity_id, etype)
events = collections.defaultdict(dict)   # (doc,eid) -> {role: [(ent, etype)]}
ev_type = {}

for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            for e in d.get('entities', []):
                ent_type[(d['id'], e['id'])] = e.get('type', 'Other')
            for e in d['events']:
                ev_type[(d['id'], e['id'])] = e['type']
                rr = collections.defaultdict(list)
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' not in v:
                            continue
                        et = ent_type.get((d['id'], v['entity_id']), 'Other')
                        rr[r].append((v['entity_id'], et))
                        recs.append((d['id'], e['id'], e['type'], r, v['entity_id'], et))
                if rr:
                    events[(d['id'], e['id'])] = dict(rr)

print('argument co entity_id: %d | event: %d' % (len(recs), len(events)))
ETS = collections.Counter(r[5] for r in recs)
print('kieu entity:', dict(ETS))
print()

# ---------- A. kieu entity xac dinh vai den dau ----------
print('='*74)
print('A. Kieu entity xac dinh VAI den muc nao')
print('='*74)
by_et = collections.defaultdict(collections.Counter)
by_T_et = collections.defaultdict(collections.Counter)
for doc, eid, T, r, ent, et in recs:
    by_et[et][r] += 1
    by_T_et[(T, et)][r] += 1

n = len(recs)
acc_et = sum(c.most_common(1)[0][1] for c in by_et.values())
acc_T_et = sum(c.most_common(1)[0][1] for c in by_T_et.values())
base = collections.Counter(r[3] for r in recs).most_common(1)[0][1]
print('  doan VAI bang nhan da so (khong dieu kien) : %.1f%%' % (100*base/n))
print('  doan VAI tu KIEU ENTITY                    : %.1f%%' % (100*acc_et/n))
print('  doan VAI tu (KIEU EVENT, KIEU ENTITY)      : %.1f%%' % (100*acc_T_et/n))
print()
print('  %-14s %8s  %s' % ('kieu entity', 'so', 'vai pho bien nhat'))
for et, c in sorted(by_et.items(), key=lambda x: -sum(x[1].values())):
    tot = sum(c.values())
    top = ', '.join('%s %.0f%%' % (r, 100*v/tot) for r, v in c.most_common(3))
    print('  %-14s %8d  %s' % (et, tot, top))

# ---------- B. so khoa ----------
print()
print('='*74)
print('B. So khoa: (T, vai)  so voi  (T, kieu_entity)')
print('='*74)
k_role = collections.Counter()
k_et = collections.Counter()
for doc, eid, T, r, ent, et in recs:
    k_role[(T, r)] += 1
    k_et[(T, et)] += 1
for nm, k in (('(T, vai)', k_role), ('(T, kieu_entity)', k_et)):
    print('  %-20s |R| %5d | sup>=10 %5d | sup>=50 %4d | sup>=100 %4d'
          % (nm, len(k), sum(1 for v in k.values() if v >= 10),
             sum(1 for v in k.values() if v >= 50),
             sum(1 for v in k.values() if v >= 100)))

# ---------- C. support cho phep chieu P2 ----------
print()
print('='*74)
print('C. Support cho phep chieu P2 (entity -> entity qua event)')
print('   nhom co ich = (entity, khoa) xuat hien o >=2 EVENT khac nhau')
print('='*74)


def study(mode):
    g1 = collections.defaultdict(set)
    rels = collections.Counter()
    for (doc, eid), rr in events.items():
        T = ev_type[(doc, eid)]
        items = [(r, ent, et) for r, lst in rr.items() for ent, et in lst]
        for i in range(len(items)):
            for j in range(len(items)):
                if i == j:
                    continue
                r1, x, t1 = items[i]; r2, y, t2 = items[j]
                if x == y:
                    continue
                if mode == 'role':
                    rel = '%s.%s>%s' % (T, r1, r2)
                elif mode == 'etype':
                    rel = '%s.%s>%s' % (T, t1, t2)
                else:
                    rel = '%s.%s.%s>%s.%s' % (T, r1, t1, r2, t2)
                rels[rel] += 1
                g1[('%s:%s' % (doc, x), rel)].add(eid)
    useful = collections.defaultdict(set)
    for (x, rel), evs in g1.items():
        if len(evs) >= 2:
            useful[rel].add(x)
    return len(rels), sum(len(v) for v in useful.values()), \
        sum(1 for r in useful if len(useful[r]) >= 100), \
        sum(1 for r in useful if len(useful[r]) >= 20), useful


print('  %-26s %7s %10s %10s %10s' % ('khoa quan he', '|R|', 'nhom co ich', 'r>=20', 'r>=100'))
print('  ' + '-'*68)
out = {}
for mode, nm in (('role', 'T.vai1>vai2'), ('etype', 'T.kieu1>kieu2'),
                 ('both', 'T.vai.kieu>vai.kieu')):
    nr, nu, big100, big20, useful = study(mode)
    out[mode] = useful
    print('  %-26s %7d %10d %10d %10d' % (nm, nr, nu, big20, big100))

print()
print('  T.kieu1>kieu2 — 10 quan he co nhieu nhom co ich nhat:')
u = out['etype']
for r, s in sorted(u.items(), key=lambda x: -len(x[1]))[:10]:
    print('    %5d entity | %s' % (len(s), r))
