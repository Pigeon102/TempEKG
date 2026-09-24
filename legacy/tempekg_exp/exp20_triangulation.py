"""EXP20 - DO DUOC PRECISION KHONG? Do muc DU THUA giua cac lop annotation.

Ly do PaTeCon khong do duoc precision: Wikidata KHONG CO DU THUA. Moi fact duoc khang
dinh MOT lan. Constraint bao no sai thi khong co nguon thu hai de doi chieu.

MAVEN CO du thua: cung mot cap event bi rang buoc boi NHIEU nguon DOC LAP:
   S1 quan he thoi gian truc tiep      (annotate task 1)
   S2 quan he nhan qua CAUSE/PRECOND   (annotate task 2)  => ngu nghia: nguyen nhan khong sau ket qua
   S3 quan he subevent                 (annotate task 3)  => ngu nghia: con nam trong cha
   S4 bac cau tu cac canh thoi gian khac (suy ra)

Cap co >=2 nguon = do duoc PRECISION khong can annotate:
   - cac nguon DONG Y  -> nhat quan
   - cac nguon MAU THUAN -> conflict DUOC XAC NHAN CHEO (do tin cay cao)
"""
import json, collections

ere = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        ere[d['id']] = d

n_src = collections.Counter()
agree = collections.Counter()
conflict_by_src = collections.Counter()
tot_pairs = 0
examples = []

for doc, d in ere.items():
    ev = {e['id'] for e in d['events']}
    # S1 quan he thoi gian truc tiep
    T = {}
    for rel, ps in d['temporal_relations'].items():
        for h, t in ps:
            if h in ev and t in ev:
                T[(h, t)] = rel
    # S2 nhan qua
    C = {}
    for kind, ps in d.get('causal_relations', {}).items():
        for h, t in ps:
            if h in ev and t in ev:
                C[(h, t)] = kind
    # S3 subevent
    S = {}
    for h, t in d.get('subevent_relations', []):
        if h in ev and t in ev:
            S[(h, t)] = 'SUBEVENT'
    # S4 bac cau: a<b<c => a<c
    before = {(h, t) for (h, t), r in T.items() if r == 'BEFORE'}
    adj = collections.defaultdict(set)
    for h, t in before:
        adj[h].add(t)
    implied = set()
    for u in adj:
        for v in adj[u]:
            for w in adj.get(v, ()):
                if w != u:
                    implied.add((u, w))

    seen = set()
    for (a, b) in set(list(T) + list(C) + list(S) + list(implied)):
        key = tuple(sorted([a, b]))
        if key in seen:
            continue
        seen.add(key)
        tot_pairs += 1

        srcs = []
        # nguon 1: quan he thoi gian truc tiep
        if (a, b) in T:
            srcs.append(('S1', T[(a, b)]))
        elif (b, a) in T:
            inv = {'BEFORE': 'AFTER', 'CONTAINS': 'CONTAINED', 'OVERLAP': 'OVERLAP',
                   'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS',
                   'ENDS-ON': 'SIMULTANEOUS'}
            srcs.append(('S1', inv.get(T[(b, a)], T[(b, a)])))
        # nguon 2: nhan qua => nguyen nhan KHONG sau ket qua (tuc BEFORE hoac CONTAINS/OVERLAP)
        if (a, b) in C:
            srcs.append(('S2', 'NOT_AFTER'))
        elif (b, a) in C:
            srcs.append(('S2', 'NOT_BEFORE'))
        # nguon 3: subevent => cha CONTAINS con
        if (a, b) in S:
            srcs.append(('S3', 'CONTAINS'))
        elif (b, a) in S:
            srcs.append(('S3', 'CONTAINED'))
        # nguon 4: bac cau
        if (a, b) in implied:
            srcs.append(('S4', 'BEFORE'))
        elif (b, a) in implied:
            srcs.append(('S4', 'AFTER'))

        k = len(srcs)
        n_src[k] += 1
        if k < 2:
            continue

        # kiem tra mau thuan giua cac nguon
        lab = dict(srcs)
        bad = False
        why = ''
        s1 = lab.get('S1')
        if 'S3' in lab and s1 is not None:
            want = lab['S3']
            if s1 not in (want, 'SIMULTANEOUS'):
                bad = True
                why = 'S1=%s vs subevent doi %s' % (s1, want)
        if 'S2' in lab and s1 is not None:
            if lab['S2'] == 'NOT_AFTER' and s1 == 'AFTER':
                bad = True
                why = 'nhan qua nhung ket qua TRUOC nguyen nhan'
            if lab['S2'] == 'NOT_BEFORE' and s1 == 'BEFORE':
                bad = True
                why = 'nhan qua nguoc chieu'
        if 'S4' in lab and s1 is not None:
            if lab['S4'] == 'BEFORE' and s1 in ('AFTER',):
                bad = True
                why = 'bac cau doi BEFORE nhung annotate AFTER'
        if bad:
            conflict_by_src[k] += 1
            if len(examples) < 5:
                examples.append((doc[:8], k, why, [s for s, _ in srcs]))
        else:
            agree[k] += 1

print('=== DO DU THUA: bao nhieu NGUON DOC LAP rang buoc moi cap event ===')
print('tong cap co it nhat 1 nguon: %d' % tot_pairs)
print()
print('%-14s %10s %8s'%('so nguon','so cap','ti le'))
for k in sorted(n_src):
    print('  %-12d %10d %7.1f%%' % (k, n_src[k], 100*n_src[k]/tot_pairs))
multi = sum(v for k, v in n_src.items() if k >= 2)
print()
print('cap co >=2 nguon (DO DUOC precision): %d = %.1f%%' % (multi, 100*multi/tot_pairs))
print()
print('=== TRONG SO CAP CO >=2 NGUON ===')
for k in sorted(set(list(agree) + list(conflict_by_src))):
    tot = agree[k] + conflict_by_src[k]
    if tot:
        print('  %d nguon: dong y %6d | MAU THUAN %5d (%.2f%%)'
              % (k, agree[k], conflict_by_src[k], 100*conflict_by_src[k]/tot))
tt = sum(agree.values()) + sum(conflict_by_src.values())
cc = sum(conflict_by_src.values())
print()
print('TONG: %d cap duoc doi chieu cheo | %d MAU THUAN (%.2f%%)' % (tt, cc, 100*cc/max(tt, 1)))
print()
print('vi du mau thuan duoc XAC NHAN CHEO:')
for doc, k, why, ss in examples:
    print('   doc %s | %d nguon %s | %s' % (doc, k, ss, why))
