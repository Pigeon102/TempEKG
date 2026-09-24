"""Do KICH THUOC ba lop pos / neg / unknown trong PaTeCon tren WD50K.

Tai hien DUNG vong lap cua Constraint_Mining.py:184-224 nhung dem ca lop thu ba
(lop ma code goc KHONG dem vao dau — khong tu so, khong mau so).
"""
import sys, collections
sys.path.insert(0, 'tempekg_exp/patecon')
import Interval_Relations

PATH = 'tempekg_exp/patecon_data/WD50K_official.tsv'


def parse_time(x):
    x = (x or '').strip()
    if x in ('', '-1', 'None'):
        return -1
    return x


# (entity, relation) -> [(start, end)]
facts = collections.defaultdict(list)
n = 0
for line in open(PATH, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) < 5:
        continue
    h, r, t, s, e = p[0], p[1], p[2], parse_time(p[3]), parse_time(p[4])
    n += 1
    if s != -1 or e != -1:
        facts[(h, r)].append((s, e))
print('doc %d dong | %d nhom (entity, relation) co fact thoi gian' % (n, len(facts)))

pos = neg = unk = single = 0
unk_pairs = pos_pairs = neg_pairs = 0
for k, lst in facts.items():
    if len(lst) < 2:
        single += 1
        continue
    consistent = True
    negative = False
    for i in range(len(lst)):
        stop = False
        for j in range(i+1, len(lst)):
            r = Interval_Relations.disjoint(lst[i][0], lst[i][1], lst[j][0], lst[j][1])
            if r == 1:
                pos_pairs += 1
            elif r == 0:
                unk_pairs += 1
            else:
                neg_pairs += 1
            if r == -1:
                consistent = False; negative = True; stop = True; break
            if r == 0:
                consistent = False
        if stop:
            break
    if consistent:
        pos += 1
    elif negative:
        neg += 1
    else:
        unk += 1

tot = pos + neg + unk
print()
print('=== BA LOP ENTITY (nhom co >=2 fact thoi gian) ===')
print('  positive (moi cap = 1)          : %6d  (%.1f%%)' % (pos, 100*pos/max(tot, 1)))
print('  negative (co it nhat mot cap=-1): %6d  (%.1f%%)' % (neg, 100*neg/max(tot, 1)))
print('  UNKNOWN  (khong cap nao=-1,     : %6d  (%.1f%%)' % (unk, 100*unk/max(tot, 1)))
print('            nhung co cap=0)')
print('  ---')
print('  tong xet                        : %6d' % tot)
print('  nhom chi co 1 fact (bo qua)     : %6d' % single)
print()
print('  confidence PaTeCon = pos/(pos+neg) = %d/%d = %.4f'
      % (pos, pos+neg, pos/max(pos+neg, 1)))
print('  neu tinh ca unknown vao TU SO    = %d/%d = %.4f'
      % (pos+unk, tot, (pos+unk)/max(tot, 1)))
print('  neu tinh ca unknown vao MAU SO   = %d/%d = %.4f'
      % (pos, tot, pos/max(tot, 1)))
print()
print('=== CAP interval ===')
tp = pos_pairs+neg_pairs+unk_pairs
print('  = 1 (thoa)    : %7d (%.1f%%)' % (pos_pairs, 100*pos_pairs/max(tp, 1)))
print('  = 0 (UNKNOWN) : %7d (%.1f%%)' % (unk_pairs, 100*unk_pairs/max(tp, 1)))
print('  = -1 (vi pham): %7d (%.1f%%)' % (neg_pairs, 100*neg_pairs/max(tp, 1)))
print()
print('  -> %.1f%% entity bi LOAI KHOI CA TU SO LAN MAU SO' % (100*unk/max(tot, 1)))
