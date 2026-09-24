"""EXP14 - Khai thac sau C2: mining theo type co thang duoc luat PER-KIND khong?

EXP13 do bat dong voi GLOBAL majority (BEFORE_FWD) - nhung SUBEVENT co majority rieng
la CONTAINS_FWD, nen no "bat dong" mot cach tam thuong. Cau hoi cong bang hon:

   TRONG tung kind, dieu kien theo kieu event co thang LUAT PER-KIND khong?

Do lai ronrg tren tap bat dong VOI LUAT PER-KIND (khong phai global majority).
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
                ev[e['id']] = {'type': e['type'], 'pos': min(offs) if offs else 10**9}
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


def c2_rows(doc):
    ev, d = arg[doc], ere[doc]
    R = {}
    for rel, ps in d['temporal_relations'].items():
        for h, t in ps:
            if h.startswith('EVENT') and t.startswith('EVENT'):
                R[(h, t)] = rel
    edges = []
    for kind, ps in d.get('causal_relations', {}).items():
        edges += [(h, t, kind) for h, t in ps]
    edges += [(h, t, 'SUBEVENT') for h, t in d.get('subevent_relations', [])]
    out = []
    for h, t, kind in edges:
        if h not in ev or t not in ev:
            continue
        if ev[h]['pos'] <= ev[t]['pos']:
            a, b, flip = h, t, False
        else:
            a, b, flip = t, h, True
        lab = FWD.get(R[(a, b)]) if (a, b) in R else (REV.get(R[(b, a)]) if (b, a) in R else None)
        if lab:
            out.append((kind, 'REV' if flip else 'FWD', ev[a]['type'], ev[b]['type'], lab))
    return out


docs = sorted(set(arg) & set(ere))
random.shuffle(docs)
cut = int(0.8 * len(docs))
MINE, EVAL = docs[:cut], docs[cut:]

perkind = collections.defaultdict(collections.Counter)      # (kind,dir) -> labels
bytype = collections.defaultdict(collections.Counter)       # (kind,dir,ta,tb) -> labels
for doc in MINE:
    for k, dr, ta, tb, lab in c2_rows(doc):
        perkind[(k, dr)][lab] += 1
        bytype[(k, dr, ta, tb)][lab] += 1

rows = []
for doc in EVAL:
    rows += c2_rows(doc)

print('tong cap C2 co nhan tren EVAL: %d' % len(rows))
print()
print('=== LUAT PER-KIND (baseline cong bang) ===')
for key in sorted(perkind):
    c = perkind[key]
    n = sum(c.values())
    lab, k = c.most_common(1)[0]
    print('  %-22s n=%-6d -> %-14s conf=%.1f%%' % (str(key), n, lab, 100*k/n))

print()
print('=== TYPE-CONDITIONING co thang LUAT PER-KIND khong? ===')
print('%-16s %7s %10s %10s %10s %9s' %
      ('KIND', 'ban', 'bat dong', 'type dung', 'perkind', 'LAI RONG'))
print('-' * 70)

for theta in (0.7, 0.9):
    print('theta=%.1f' % theta)
    tot_gain = 0
    for kind in ('CAUSE', 'PRECONDITION', 'SUBEVENT'):
        fire = dis = t_ok = p_ok = 0
        for k, dr, ta, tb, lab in rows:
            if k != kind:
                continue
            base = perkind.get((k, dr))
            if not base:
                continue
            blab = base.most_common(1)[0][0]
            c = bytype.get((k, dr, ta, tb))
            if not c:
                continue
            n = sum(c.values())
            if n < 10:
                continue
            tlab, kk = c.most_common(1)[0]
            if wilson_lo(kk, n) < theta:
                continue
            fire += 1
            if tlab != blab:
                dis += 1
                t_ok += (tlab == lab)
                p_ok += (blab == lab)
        gain = t_ok - p_ok
        tot_gain += gain
        if dis:
            print('  %-14s %7d %10d %9.1f%% %9.1f%% %+9d'
                  % (kind, fire, dis, 100*t_ok/dis, 100*p_ok/dis, gain))
        else:
            print('  %-14s %7d %10d  (khong bat dong)' % (kind, fire, dis))
    print('  %-14s %36s %+9d' % ('TONG', '', tot_gain))
    print()
