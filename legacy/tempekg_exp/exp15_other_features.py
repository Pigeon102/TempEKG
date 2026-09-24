"""EXP15 - Co dac trung nao THOAT khoi 6 luat khong?

Tap trung vao QUAN THE LON NHAT: ~90% cap KHONG co lien ket C2, roi xuong majority
(~78%). Do la noi 22% loi con lai nam. Neu co dac trung nao thang majority o day thi
no dang gia hon moi thu da thu.

Dac trung thu:
  F1 (ta,tb)          - cap kieu event (tren TOAN BO cap, khong chi cap chia se participant)
  F2 sentdist         - khoang cach cau (0,1,2,3+)
  F3 (ta,tb,sentdist) - ket hop
  F4 co TIMEX anchor  - mot/ca hai event co gan TIMEX khong

Do lai rong tren tap BAT DONG voi majority.
"""
import json, collections, random, math

random.seed(20261012)

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


def rows_of(doc):
    d = ere[doc]
    ev = {}
    for e in d['events']:
        sids = [m['sent_id'] for m in e['mention'] if 'sent_id' in m]
        if not sids:
            continue
        ev[e['id']] = {'type': e['type'], 'sent': min(sids)}
    tx_anchor = set()
    txids = {t['id'] for t in d['TIMEX']}
    R = {}
    for rel, ps in d['temporal_relations'].items():
        for h, t in ps:
            if h in txids and t in ev:
                tx_anchor.add(t)
            if t in txids and h in ev:
                tx_anchor.add(h)
            if h in ev and t in ev:
                R[(h, t)] = rel
    c2 = set()
    for kind, ps in d.get('causal_relations', {}).items():
        for h, t in ps:
            c2.add((h, t)); c2.add((t, h))
    for h, t in d.get('subevent_relations', []):
        c2.add((h, t)); c2.add((t, h))

    ids = sorted(ev, key=lambda i: ev[i]['sent'])
    out = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            lab = FWD.get(R[(a, b)]) if (a, b) in R else (REV.get(R[(b, a)]) if (b, a) in R else None)
            if not lab:
                continue
            if (a, b) in c2:
                continue                      # BO cap co C2 - chi xet phan con lai
            sd = min(abs(ev[a]['sent'] - ev[b]['sent']), 3)
            out.append({'ta': ev[a]['type'], 'tb': ev[b]['type'], 'sd': sd,
                        'tx': (a in tx_anchor) + (b in tx_anchor), 'lab': lab})
    return out


FEATS = [
    ('F1 (ta,tb)',            lambda r: (r['ta'], r['tb'])),
    ('F2 sentdist',           lambda r: (r['sd'],)),
    ('F3 (ta,tb,sentdist)',   lambda r: (r['ta'], r['tb'], r['sd'])),
    ('F4 timex-anchor',       lambda r: (r['tx'],)),
    ('F5 (sentdist,timex)',   lambda r: (r['sd'], r['tx'])),
]

docs = sorted(ere)
random.shuffle(docs)
cut = int(0.8 * len(docs))
MINE, EVAL = docs[:cut], docs[cut:]

models = [collections.defaultdict(collections.Counter) for _ in FEATS]
glob = collections.Counter()
for doc in MINE:
    for r in rows_of(doc):
        glob[r['lab']] += 1
        for fi, (_, kf) in enumerate(FEATS):
            models[fi][kf(r)][r['lab']] += 1
MAJ = glob.most_common(1)[0][0]

rows = []
for doc in EVAL:
    rows += rows_of(doc)

print('QUAN THE: cap KHONG co lien ket C2')
print('  MINE=%d cap | EVAL=%d cap' % (sum(glob.values()), len(rows)))
print('  majority = %s  %.1f%% (tren MINE)' % (MAJ, 100*glob[MAJ]/sum(glob.values())))
maj_acc = sum(1 for r in rows if r['lab'] == MAJ) / len(rows)
print('  majority tren EVAL = %.1f%%' % (100*maj_acc))
print()
print('%-24s %8s %10s %10s %10s %9s' %
      ('DAC TRUNG', 'ban', 'bat dong', 'feat dung', 'maj dung', 'LAI RONG'))
print('-' * 76)

for theta in (0.7, 0.8):
    print('theta=%.1f' % theta)
    for fi, (name, kf) in enumerate(FEATS):
        fire = dis = f_ok = m_ok = 0
        for r in rows:
            c = models[fi].get(kf(r))
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
                f_ok += (lab == r['lab'])
                m_ok += (MAJ == r['lab'])
        if dis:
            print('  %-22s %8d %10d %9.1f%% %9.1f%% %+9d'
                  % (name, fire, dis, 100*f_ok/dis, 100*m_ok/dis, f_ok - m_ok))
        else:
            print('  %-22s %8d %10d  (khong bat dong)' % (name, fire, dis))
    print()
