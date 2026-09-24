"""EXP13 - Do gia tri THAT cua constraint: do chinh xac tren TAP BAT DONG voi majority.

EXP12 cho thay accuracy tong khong doi du kenh tot len. Ly do: constraint phan lon
DONG Y voi majority. Gia tri that chi nam o noi chung BAT DONG.

Voi moi tang, tren cac cap ma tang do BAN va du doan KHAC majority:
   - tang dung bao nhieu?
   - majority dung bao nhieu?
   - LAI RONG = (tang dung - majority dung)
"""
import json, zipfile, io, collections, random, math, re

random.seed(20261012)
STOP = re.compile(r'^(the|a|an|his|her|its|their|our|this|that|these|those)\s+', re.I)


def norm(s):
    s = re.sub(r'[^a-z0-9 ]+', ' ', s.strip().lower())
    s = re.sub(r'\s+', ' ', s).strip()
    prev = None
    while prev != s:
        prev, s = s, STOP.sub('', s)
    return s


arg = {}
z = zipfile.ZipFile('MAVEN-Arg.zip')
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            surf2ent = {}
            for en in d['entities']:
                for m in en['mention']:
                    k = norm(m['mention'])
                    if k:
                        surf2ent.setdefault(k, en['id'])
            ev = {}
            for e in d['events']:
                offs = [m['offset'][0] for m in e['mention'] if m.get('offset')]
                ents = set()
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            ents.add(v['entity_id'])
                        else:
                            k = norm(v.get('content', ''))
                            if k:
                                ents.add(surf2ent.get(k, 'PSEUDO::' + k))
                ev[e['id']] = {'type': e['type'], 'pos': min(offs) if offs else 10**9,
                               'ents': ents}
            arg[d['id']] = ev

ere = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        ere[d['id']] = d

FWD = {'BEFORE': 'BEFORE_FWD', 'CONTAINS': 'CONTAINS_FWD', 'OVERLAP': 'OVERLAP_FWD',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}
REV = {'BEFORE': 'BEFORE_REV', 'CONTAINS': 'CONTAINS_REV', 'OVERLAP': 'OVERLAP_REV',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}


def wilson_lo(k, n, z=1.96):
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z*z/n
    return (p + z*z/(2*n) - z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / d


def instances(doc):
    ev, d = arg[doc], ere[doc]
    R = {}
    for rel, ps in d['temporal_relations'].items():
        for h, t in ps:
            if h.startswith('EVENT') and t.startswith('EVENT'):
                R[(h, t)] = rel
    c2 = {}
    for kind, ps in d.get('causal_relations', {}).items():
        for h, t in ps:
            c2[(h, t)] = kind
    for h, t in d.get('subevent_relations', []):
        c2[(h, t)] = 'SUBEVENT'
    ids = sorted(ev, key=lambda i: ev[i]['pos'])
    out = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            lab = FWD.get(R[(a, b)]) if (a, b) in R else (REV.get(R[(b, a)]) if (b, a) in R else None)
            if not lab:
                continue
            kind = dr = None
            if (a, b) in c2:
                kind, dr = c2[(a, b)], 'FWD'
            elif (b, a) in c2:
                kind, dr = c2[(b, a)], 'REV'
            out.append({'ta': ev[a]['type'], 'tb': ev[b]['type'], 'lab': lab,
                        'kind': kind, 'dir': dr,
                        'nshare': len(ev[a]['ents'] & ev[b]['ents'])})
    return out


TIERS = [
    ('T1 C2+kind+huong+types', lambda r: (r['kind'], r['dir'], r['ta'], r['tb']) if r['kind'] else None),
    ('T2 C2+kind+huong',       lambda r: (r['kind'], r['dir']) if r['kind'] else None),
    ('T3 C1+types',            lambda r: (r['ta'], r['tb']) if r['nshare'] >= 1 else None),
]

docs = sorted(set(arg) & set(ere))
random.shuffle(docs)
cut = int(0.8 * len(docs))
MINE, EVAL = docs[:cut], docs[cut:]

models = [collections.defaultdict(collections.Counter) for _ in TIERS]
glob = collections.Counter()
for doc in MINE:
    for r in instances(doc):
        glob[r['lab']] += 1
        for ti, (_, kf) in enumerate(TIERS):
            k = kf(r)
            if k is not None:
                models[ti][k][r['lab']] += 1
MAJ = glob.most_common(1)[0][0]

rows = []
for doc in EVAL:
    rows += instances(doc)

print('majority label = %s  (%.1f%% tren MINE)' % (MAJ, 100*glob[MAJ]/sum(glob.values())))
print('tong cap EVAL  = %d' % len(rows))
print()
print('%-24s %8s %10s %9s %9s %9s' %
      ('TANG', 'ban', 'bat dong', 'tang dung', 'maj dung', 'LAI RONG'))
print('-' * 76)

for theta in (0.7, 0.9):
    print('theta = %.1f' % theta)
    for ti, (name, kf) in enumerate(TIERS):
        fire = dis = tier_ok = maj_ok = 0
        for r in rows:
            k = kf(r)
            if k is None:
                continue
            c = models[ti].get(k)
            if not c:
                continue
            n = sum(c.values())
            if n < 10:
                continue
            lab, kk = c.most_common(1)[0]
            if wilson_lo(kk, n) < theta:
                continue
            fire += 1
            if lab != MAJ:
                dis += 1
                tier_ok += (lab == r['lab'])
                maj_ok += (MAJ == r['lab'])
        if dis:
            print('  %-22s %8d %10d %8.1f%% %8.1f%% %+8d'
                  % (name, fire, dis, 100*tier_ok/dis, 100*maj_ok/dis, tier_ok - maj_ok))
        else:
            print('  %-22s %8d %10d  (khong bao gio bat dong)' % (name, fire, dis))
    print()
