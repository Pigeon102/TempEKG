"""HOLD-OUT: pattern hop thanh co tong quat hoa khong?

Ban truoc CHON va CHAM pattern tren CUNG mot tap -> lift 6.32x co the la do chon lua
tren hang nghin ung vien (multiple comparisons), khong phai tin hieu that.

Chia document 80/20. Mine tren TRAIN, do lift tren TEST. Neu lift tren test tut ve ~1
thi pattern la overfit.
"""
import sys, os, random, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compose as M

random.seed(20261012)
docs = sorted({r['doc'] for r in M.EV}) if 'doc' in M.EV[0] else None
if docs is None:
    # compose.py khong luu doc -> lay lai tu nid neu co, khong thi chia theo chi so
    docs = None

# compose.EV khong mang doc_id; chia theo chi so on dinh sau khi shuffle co seed
idx = list(range(len(M.EV)))
random.shuffle(idx)
cut = int(0.8*len(idx))
TR = {i for i in idx[:cut]}
train = [M.EV[i] for i in idx[:cut]]
test = [M.EV[i] for i in idx[cut:]]
print('event: train %d | test %d' % (len(train), len(test)), flush=True)

for K in (2, 3):
    rtr = [r for r in train if r['k'] == K]
    rte = [r for r in test if r['k'] == K]
    if len(rtr) < 200 or len(rte) < 100:
        continue
    b_tr = sum(r['y'] for r in rtr)/len(rtr)
    b_te = sum(r['y'] for r in rte)/len(rte)
    print('\n' + '='*96)
    print('TANG k=%d | train %d (nen %.1f%%) | test %d (nen %.1f%%)'
          % (K, len(rtr), 100*b_tr, len(rte), 100*b_te))
    print('='*96)
    C = M.gen_conditions(rtr)
    res = M.beam(rtr, C, b_tr, depth=3, width=14, min_sup=25)

    print('  %-9s %-9s %-9s %-9s %-7s %s'
          % ('lift TR', 'lift TE', 'conf TE', 'sup TE', 'giu?', 'hop thanh'))
    print('  ' + '-'*92)
    seen = set(); shown = 0
    kept = 0; total = 0
    for conds, (w, r, n, lift_tr) in res:
        key = tuple(sorted((c[1], c[2], str(c[3])) for c in conds))
        if key in seen:
            continue
        seen.add(key)
        s = M.score(rte, conds, b_te)
        if s is None or s[2] < 10:
            continue
        total += 1
        lift_te = s[3]
        ok = lift_te > 1.5
        kept += ok
        if shown < 12:
            print('  %8.2fx %8.2fx %8.1f%% %8d %-7s %s'
                  % (lift_tr, lift_te, 100*s[1], s[2], 'CO' if ok else '-',
                     ' & '.join('%s(%s=%s)' % (c[1], c[2], c[3]) for c in conds)))
            shown += 1
    print('\n  hop thanh co lift(test) > 1.5x : %d / %d (%.0f%%)'
          % (kept, total, 100*kept/max(total, 1)))
    # trung binh co trong so
    num = den = 0
    for conds, _ in res:
        s = M.score(rte, conds, b_te)
        if s and s[2] >= 10:
            num += s[3]*s[2]; den += s[2]
    if den:
        print('  lift(test) trung binh co trong so support : %.2fx' % (num/den))
