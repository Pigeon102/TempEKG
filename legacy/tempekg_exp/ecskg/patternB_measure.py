"""DO THAT Pattern B cua tai lieu Event-Centric-PaTeCon.

Tai lieu dung SO GIA DINH ("1.500 cap Attack/Injury, 1.380 BEFORE, conf 0,968") va tu ghi ro
la gia dinh. Tinh kha thi phu thuoc hoan toan vao so THAT. Do o day.

Pattern B:  (T1, T2, rho) => P    voi P thuoc {BEFORE, CONTAINS, OVERLAP, CAUSE, PRECONDITION}
    support    = so cap co nhan
    confidence = nhan da so / tong cap CO nhan   (Pairs_unk bi loai — PCA-confidence)

Do ba muc chu ky de danh gia luon Pattern B_role (refinement):
    L0  (T1, T2)              tho
    L1  (T1, T2, rho)         chia se role rho (cung role o hai ben)
    L2  (T1, T2, rho1, rho2)  cap role co huong
"""
import json, collections, zipfile, io, itertools

TEMPORAL = ['BEFORE', 'OVERLAP', 'CONTAINS', 'SIMULTANEOUS', 'ENDS-ON', 'BEGINS-ON']
CAUSAL = ['CAUSE', 'PRECONDITION']

# ---------- MAVEN-Arg: argument entity theo role ----------
args = {}          # (doc, eid) -> {role: {entity}}
etype = {}
z = zipfile.ZipFile('MAVEN-Arg.zip')
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            for e in d['events']:
                etype[(d['id'], e['id'])] = e['type']
                rr = collections.defaultdict(set)
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            rr[r].add(v['entity_id'])
                if rr:
                    args[(d['id'], e['id'])] = dict(rr)
print('event co argument entity: %d | kieu: %d' % (len(args), len(set(etype.values()))), flush=True)

# ---------- MAVEN-ERE: nhan quan he ----------
docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        docs[d['id']] = d

sig = {0: collections.defaultdict(collections.Counter),
       1: collections.defaultdict(collections.Counter),
       2: collections.defaultdict(collections.Counter)}
n_pair = n_lab = n_unk = 0

for doc, d in docs.items():
    lab = {}
    for rel in TEMPORAL:
        for h, t in d['temporal_relations'].get(rel, []):
            lab[(h, t)] = rel
    for rel in CAUSAL:
        for h, t in d['causal_relations'].get(rel, []):
            lab.setdefault((h, t), rel)

    ids = [e['id'] for e in d['events'] if (doc, e['id']) in args]
    for e1, e2 in itertools.permutations(ids, 2):
        a1, a2 = args[(doc, e1)], args[(doc, e2)]
        shared = []
        for r1, s1 in a1.items():
            for r2, s2 in a2.items():
                if s1 & s2:
                    shared.append((r1, r2))
        if not shared:
            continue
        T1, T2 = etype[(doc, e1)], etype[(doc, e2)]
        P = lab.get((e1, e2))
        n_pair += 1
        if P is None:
            n_unk += 1
        else:
            n_lab += 1
        key = '__UNK__' if P is None else P
        sig[0][(T1, T2)][key] += 1
        for r1, r2 in shared:
            sig[2][(T1, T2, r1, r2)][key] += 1
            if r1 == r2:
                sig[1][(T1, T2, r1)][key] += 1

print('cap (e1,e2) chia se argument: %d | co nhan %d (%.1f%%) | Pairs_unk %d (%.1f%%)'
      % (n_pair, n_lab, 100*n_lab/n_pair, n_unk, 100*n_unk/n_pair))
print()

NAMES = {0: 'L0  (T1,T2)', 1: 'L1  (T1,T2,rho)', 2: 'L2  (T1,T2,r1,r2)'}
print('%-20s %8s %10s %10s %10s %10s %10s' %
      ('muc chu ky', '|sig|', 'sup>=10', 'sup>=20', 'sup>=50', 'sup>=100', 'conf>=.9&s>=10'))
print('-'*88)
best = {}
for L in (0, 1, 2):
    tot = len(sig[L])
    cnt = {}
    rules = []
    for k, c in sig[L].items():
        lab_n = sum(v for kk, v in c.items() if kk != '__UNK__')
        if lab_n == 0:
            continue
        top, topn = max(((kk, v) for kk, v in c.items() if kk != '__UNK__'), key=lambda x: x[1])
        conf = topn/lab_n
        for s in (10, 20, 50, 100):
            if lab_n >= s:
                cnt[s] = cnt.get(s, 0)+1
        if lab_n >= 10 and conf >= 0.9:
            rules.append((conf, lab_n, k, top, topn))
    best[L] = rules
    print('%-20s %8d %10d %10d %10d %10d %10d'
          % (NAMES[L], tot, cnt.get(10, 0), cnt.get(20, 0), cnt.get(50, 0),
             cnt.get(100, 0), len(rules)))

print()
print('=== L1: 12 rule manh nhat (conf>=0.9, sup>=10) ===')
for conf, n, k, top, topn in sorted(best[1], key=lambda x: -x[1])[:12]:
    print('  conf %.3f  sup %4d  %-58s => %-12s (%d)'
          % (conf, n, '%s | %s | %s' % k, top, topn))

print()
print('=== phan bo confidence o L1 (sup>=10) ===')
h = collections.Counter()
for k, c in sig[1].items():
    lab_n = sum(v for kk, v in c.items() if kk != '__UNK__')
    if lab_n < 10:
        continue
    topn = max(v for kk, v in c.items() if kk != '__UNK__')
    h[min(int(topn/lab_n*10), 9)] += 1
for b in range(9, -1, -1):
    if h[b]:
        print('  %.1f-%.1f : %4d  %s' % (b/10, (b+1)/10, h[b], '#'*min(h[b]//2, 60)))

# ---------- Pattern B_role: refinement co day conf len khong ----------
print()
print('=== Pattern B_role: L0 conf trung binh -> L1/L2 co vuot 0.9 khong ===')
def conf_of(L, k):
    c = sig[L][k]
    lab_n = sum(v for kk, v in c.items() if kk != '__UNK__')
    if lab_n < 10:
        return None
    return max(v for kk, v in c.items() if kk != '__UNK__')/lab_n, lab_n

mid = []
for k, c in sig[0].items():
    r = conf_of(0, k)
    if r and 0.5 <= r[0] < 0.9:
        mid.append((k, r))
lifted1 = lifted2 = 0
for (T1, T2), (c0, n0) in mid:
    ok1 = any(conf_of(1, kk) and conf_of(1, kk)[0] >= 0.9
              for kk in sig[1] if kk[0] == T1 and kk[1] == T2)
    ok2 = any(conf_of(2, kk) and conf_of(2, kk)[0] >= 0.9
              for kk in sig[2] if kk[0] == T1 and kk[1] == T2)
    lifted1 += ok1; lifted2 += ok2
print('  L0 co conf thuoc [0.5,0.9) va sup>=10 : %d' % len(mid))
print('  trong do refine sang L1 vuot 0.9      : %d (%.1f%%)'
      % (lifted1, 100*lifted1/max(len(mid), 1)))
print('  trong do refine sang L2 vuot 0.9      : %d (%.1f%%)'
      % (lifted2, 100*lifted2/max(len(mid), 1)))
