"""EXP9 - CASCADE BACKOFF tren toan bo he thong.

Y tuong tu MODEL.md muc 2.4 (dan tinh chinh): dung muc CHI TIET nhat o noi du bang
chung, LUI ve muc tho hon o noi thua. Thu tu uu tien lay tu do chinh xac da do:

  T1  C2 + kind + huong + 2 kieu event   (SUBEVENT dat 99.7%)
  T2  C2 + kind + huong                  (90.0%, phu day du tren cap C2)
  T3  C1 + 2 kieu event                  (86.4% voi quy tac Wilson)
  T4  text-order / majority              (~62-69%)

MAU SO TRUNG THUC: TAT CA cap event co quan he thoi gian tren EVAL - khong chi cap
C2 hay cap chia se participant. Chi khi do moi thay DO PHU THAT.

So sanh 2 che do cong don:
  naive   - dung mot muc neu key co support >= 10
  wilson  - chi dung neu Wilson lower bound >= theta, neu khong thi LUI
"""
import json, zipfile, io, collections, random, math

random.seed(20261012)

arg = {}
z = zipfile.ZipFile('MAVEN-Arg.zip')
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            ev = {}
            for e in d['events']:
                offs = [m['offset'][0] for m in e['mention'] if m.get('offset')]
                ents = set()
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            ents.add(v['entity_id'])
                ev[e['id']] = {'type': e['type'], 'pos': min(offs) if offs else 10**9,
                               'ents': ents}
            arg[d['id']] = ev

ere = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        ere[d['id']] = d

docs = sorted(set(arg) & set(ere))
random.shuffle(docs)
cut = int(0.8 * len(docs))
MINE, EVAL = docs[:cut], docs[cut:]

FWD = {'BEFORE': 'BEFORE_FWD', 'CONTAINS': 'CONTAINS_FWD', 'OVERLAP': 'OVERLAP_FWD',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}
REV = {'BEFORE': 'BEFORE_REV', 'CONTAINS': 'CONTAINS_REV', 'OVERLAP': 'OVERLAP_REV',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}


def wilson_lo(k, n, z=1.96):
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z*z/n
    c = p + z*z/(2*n)
    m = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return (c - m) / d


def instances(doc):
    """TAT CA cap co quan he thoi gian, kem thong tin C1/C2"""
    ev = arg[doc]
    d = ere[doc]
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

    ids = sorted([e for e in ev], key=lambda i: ev[i]['pos'])
    out = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            if (a, b) in R:
                lab = FWD.get(R[(a, b)])
            elif (b, a) in R:
                lab = REV.get(R[(b, a)])
            else:
                continue
            if not lab:
                continue
            # kenh C2?
            kind = direction = None
            if (a, b) in c2:
                kind, direction = c2[(a, b)], 'FWD'
            elif (b, a) in c2:
                kind, direction = c2[(b, a)], 'REV'
            shared = ev[a]['ents'] & ev[b]['ents']
            out.append({'ta': ev[a]['type'], 'tb': ev[b]['type'], 'lab': lab,
                        'kind': kind, 'dir': direction, 'nshare': len(shared)})
    return out


TIERS = [
    ('T1 C2+kind+huong+types', lambda r: (r['kind'], r['dir'], r['ta'], r['tb']) if r['kind'] else None),
    ('T2 C2+kind+huong',       lambda r: (r['kind'], r['dir']) if r['kind'] else None),
    ('T3 C1+types',            lambda r: (r['ta'], r['tb']) if r['nshare'] >= 1 else None),
    ('T4 majority',            lambda r: ()),
]

# ---- hoc tren MINE ----
models = [collections.defaultdict(collections.Counter) for _ in TIERS]
for doc in MINE:
    for r in instances(doc):
        for ti, (_, keyf) in enumerate(TIERS):
            k = keyf(r)
            if k is not None:
                models[ti][k][r['lab']] += 1

eval_rows = []
for doc in EVAL:
    eval_rows += instances(doc)
print('TONG cap co quan he thoi gian tren EVAL: %d' % len(eval_rows))
print()


def run(mode, theta=0.7, min_sup=10):
    used = collections.Counter()
    hit_by = collections.Counter()
    tot_hit = 0
    for r in eval_rows:
        for ti, (name, keyf) in enumerate(TIERS):
            k = keyf(r)
            if k is None:
                continue
            c = models[ti].get(k)
            if not c:
                continue
            n = sum(c.values())
            if n < min_sup:
                continue
            lab, kk = c.most_common(1)[0]
            if mode == 'wilson' and wilson_lo(kk, n) < theta:
                continue          # bang chung yeu -> LUI xuong muc tho hon
            used[name] += 1
            ok = (lab == r['lab'])
            hit_by[name] += ok
            tot_hit += ok
            break
    print('  che do = %s%s' % (mode, '' if mode == 'naive' else ' (theta=%.1f)' % theta))
    for name, _ in TIERS:
        if used[name]:
            print('      %-24s dung %6d lan (%.1f%%)  acc %.1f%%'
                  % (name, used[name], 100*used[name]/len(eval_rows),
                     100*hit_by[name]/used[name]))
    print('      %-24s %6d / %d = %.1f%%'
          % ('TONG', tot_hit, len(eval_rows), 100*tot_hit/len(eval_rows)))
    print()
    return 100*tot_hit/len(eval_rows)


print('=== CASCADE ===')
a = run('naive')
b = run('wilson', 0.7)
c = run('wilson', 0.8)

print('=== DOI CHIEU: tung muc DON LE, khong cascade (phu day du bang majority) ===')
for ti, (name, keyf) in enumerate(TIERS):
    hit = cov = 0
    for r in eval_rows:
        k = keyf(r)
        if k is None or k not in models[ti] or sum(models[ti][k].values()) < 10:
            continue
        cov += 1
        hit += (models[ti][k].most_common(1)[0][0] == r['lab'])
    if cov:
        print('  %-24s phu %6d (%.1f%%)  acc %.1f%%'
              % (name, cov, 100*cov/len(eval_rows), 100*hit/cov))
