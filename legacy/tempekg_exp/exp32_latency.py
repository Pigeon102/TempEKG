"""EXP32 - Do LATENCY dau-cuoi tren WD50K: PaTeCon vs TempEKG.

Do tung giai doan de biet nut that o dau.
"""
import sys, time, collections, subprocess, os
sys.path.insert(0, 'tempekg_exp')
from uncertain_time import UTime, classify_pair

WD = 'tempekg_exp/patecon_data/WD50K_official.tsv'
N_REP = 3


def timeit(fn, rep=N_REP):
    ts = []
    for _ in range(rep):
        t0 = time.perf_counter()
        r = fn()
        ts.append(time.perf_counter() - t0)
    return min(ts), r


print('=' * 72)
print('LATENCY TREN WD50K (50,000 fact, 17,176 entity, 6 property)')
print('lay MIN cua %d lan chay' % N_REP)
print('=' * 72)
print()

# ---------- TempEKG tung giai doan ----------
def load():
    rows = []
    for l in open(WD, encoding='utf-8'):
        p = l.strip().split('\t')
        if len(p) >= 5:
            rows.append(p)
    return rows


t_load, rows = timeit(load)
print('%-42s %8.3f s' % ('1. Doc du lieu (50k dong)', t_load))


def build_intervals():
    out = {}
    for r in rows:
        out[(r[0], r[1], r[2])] = UTime.from_padded(r[3])
    return out


t_iv, ivs = timeit(build_intervals)
print('%-42s %8.3f s' % ('2. Dung khoang + granularity (100k gia tri)', t_iv))


def index_entity():
    sp = collections.defaultdict(list)
    for r in rows:
        sp[(r[0], r[1])].append(r)
    return sp


t_idx, sp = timeit(index_entity)
print('%-42s %8.3f s' % ('3. Index (entity,property)', t_idx))


def detect_pairs():
    """so cap trong cung (entity,property) — tuong duong MutualExclusion"""
    res = collections.Counter()
    for k, lst in sp.items():
        if len(lst) < 2:
            continue
        for i in range(len(lst)):
            for j in range(i+1, len(lst)):
                a = ivs[(lst[i][0], lst[i][1], lst[i][2])]
                b = ivs[(lst[j][0], lst[j][1], lst[j][2])]
                res[classify_pair(a, b)] += 1
    return res


t_pair, cls = timeit(detect_pairs)
print('%-42s %8.3f s   %s' % ('4. Phan tang uncertainty', t_pair, dict(cls.most_common(3))))


def single_detect():
    flag = set()
    for r in rows:
        k = (r[0], r[1], r[2])
        if len(sp[(r[0], r[1])]) != 1:
            continue
        o = r[2]
        if o.isdigit() and len(o) == 8 and (o[4:6] == '00' or o[6:] == '00'):
            flag.add(k)
        elif not o.isdigit():
            flag.add(k)
    return flag


t_sing, sgl = timeit(single_detect)
print('%-42s %8.3f s   %d fact' % ('5. Detector fact don gia tri', t_sing, len(sgl)))


def quant():
    ent = collections.defaultdict(dict)
    for r in rows:
        ent[r[0]].setdefault(r[1], []).append(r[2])
    q = set()

    def yr(v):
        return int(v[:4]) if v[:4].isdigit() else None
    for e, props in ent.items():
        b = [yr(x) for x in props.get('P569', []) if yr(x)]
        d = [yr(x) for x in props.get('P570', []) if yr(x)]
        if b and d:
            for bb in b:
                for dd in d:
                    if dd-bb > 120 or dd-bb < 0:
                        q.add((e, 'P569', str(bb)))
    return q


t_q, qq = timeit(quant)
print('%-42s %8.3f s' % ('6. Rang buoc dinh luong', t_q))

tempekg_total = t_load + t_iv + t_idx + t_pair + t_sing + t_q
print('-' * 62)
print('%-42s %8.3f s' % ('TEMPEKG TONG (dau-cuoi)', tempekg_total))
print()

# ---------- PaTeCon ----------
print('PaTeCon (code goc, cung may):')
os.chdir('tempekg_exp/patecon')
pate_times = []
for i in range(2):
    t0 = time.perf_counter()
    subprocess.run([sys.executable, 'Constraint_Mining.py', '--dataset=resource/WD50K_off.tsv',
                    '--knowledgegraph=wikidata', '--support=10',
                    '--candidate_confidence=0.5', '--confidence=0.9'],
                   capture_output=True)
    t_mine = time.perf_counter() - t0
    t0 = time.perf_counter()
    subprocess.run([sys.executable, 'Conflict_Detection.py', '--dataset=resource/WD50K_off.tsv',
                    '--knowledgegraph=wikidata',
                    '--constraint=output/WD50K_off.all_constraints'], capture_output=True)
    t_det = time.perf_counter() - t0
    pate_times.append((t_mine, t_det))
os.chdir('../..')
tm = min(t[0] for t in pate_times)
td = min(t[1] for t in pate_times)
print('%-42s %8.3f s' % ('  Constraint_Mining.py', tm))
print('%-42s %8.3f s' % ('  Conflict_Detection.py', td))
print('-' * 62)
print('%-42s %8.3f s' % ('PATECON TONG', tm+td))
print()
print('=' * 62)
print('%-42s %8.3f s' % ('TempEKG', tempekg_total))
print('%-42s %8.3f s' % ('PaTeCon', tm+td))
print('%-42s %8.1fx' % ('  TempEKG nhanh hon', (tm+td)/tempekg_total))
print()
print('thong luong TempEKG: %.0f fact/giay' % (50000/tempekg_total))
