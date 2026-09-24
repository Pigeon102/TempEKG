"""EXP27 - Bieu dien uncertainty co SUA duoc 747 conflict cua PaTeCon khong?

Ap dung UTime (khoang + do chinh xac) len chinh tap conflict PaTeCon sinh ra tren
bo du lieu CHINH THUC cua ho, roi phan loai lai.
"""
import sys, collections
sys.path.insert(0, 'tempekg_exp')
from uncertain_time import UTime, classify_pair, same_event, disjoint

rows = [l.rstrip('\n') for l in open('tempekg_exp/patecon/output/WD50K_off.all_conflicts',
                                     encoding='utf-8') if l.strip()]

by_kind = collections.defaultdict(collections.Counter)
overall = collections.Counter()
examples = collections.defaultdict(list)

for l in rows:
    p = l.split('\t')
    if len(p) < 3:
        continue
    kind = p[0].split('|')[0]
    ktag = ('MutualExclusion' if 'MutualExclusion' in kind
            else 'disjoint' if 'disjoint' in kind else 'before')
    fa, fb = p[1].split(','), p[2].split(',')
    if len(fa) < 5 or len(fb) < 5:
        continue
    # cot 3,4 la start,end -> lay start lam moc (PaTeCon dung diem)
    a = UTime.from_padded(fa[3])
    b = UTime.from_padded(fb[3])
    cls = classify_pair(a, b)
    by_kind[ktag][cls] += 1
    overall[cls] += 1
    if len(examples[cls]) < 3:
        examples[cls].append((ktag[:16], fa[0], fa[3], str(a), fb[3], str(b)))

tot = sum(overall.values())
print('=' * 70)
print('AP DUNG BIEU DIEN UNCERTAINTY LEN %d CONFLICT CUA PaTeCon' % tot)
print('=' * 70)
for k, v in overall.most_common():
    print('  %-18s %5d %6.1f%%' % (k, v, 100*v/tot))
print()
print('%-18s %10s %12s %10s %10s' % ('loai constraint', 'CONFLICT', 'REFINEMENT',
                                     'IDENTICAL', 'khac'))
print('-' * 66)
for kt, c in by_kind.items():
    other = sum(v for k, v in c.items() if k not in ('CONFLICT', 'REFINEMENT', 'IDENTICAL'))
    print('%-18s %10d %12d %10d %10d'
          % (kt, c['CONFLICT'], c['REFINEMENT'], c['IDENTICAL'], other))

real = overall['CONFLICT']
spur = overall['REFINEMENT'] + overall['IDENTICAL']
print()
print('  CONFLICT THAT (giao rong)          : %d = %.1f%%' % (real, 100*real/tot))
print('  GIA (refinement/trung nhau)        : %d = %.1f%%' % (spur, 100*spur/tot))
print('  => giam tu %d xuong %d  (-%.1f%%)' % (tot, real, 100*(tot-real)/tot))
print()
for cls in ('REFINEMENT', 'IDENTICAL', 'CONFLICT'):
    if examples[cls]:
        print('vi du %s:' % cls)
        for kt, q, sa, ra, sb, rb in examples[cls]:
            print('   [%s] %s' % (kt, q))
            print('       %s -> %s' % (sa, ra))
            print('       %s -> %s' % (sb, rb))
