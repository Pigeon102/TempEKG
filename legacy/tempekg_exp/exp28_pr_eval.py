"""EXP28 - Do PRECISION/RECALL cua PaTeCon vs TempEKG tren tap gan nhan tu dung.

Giao thuc CUA HO (§6.1.2): "a wrong fact contained in a conflicting pair is considered
a successfully recalled example". Ta dung dung cach do, NHUNG them PRECISION (ho khong tinh).

Nhan su that:
   WRONG = DELETED   (fact bien mat hoan toan khoi Wikidata) - chat che nhat
   phu    = DELETED + CHANGED
   NOPROP bi LOAI vi mo ho (ca property bien mat, co the do tai cau truc entity)
"""
import sys, collections
sys.path.insert(0, 'tempekg_exp')
from uncertain_time import UTime, classify_pair

# ---------- nhan su that ----------
label = {}
for l in open('tempekg_exp/patecon_data/wd50k_labeled.tsv', encoding='utf-8'):
    p = l.rstrip('\n').split('\t')
    if len(p) >= 6:
        label[(p[0], p[1], p[2])] = p[5]

WRONG_STRICT = {k for k, v in label.items() if v == 'DELETED'}
WRONG_WIDE = {k for k, v in label.items() if v in ('DELETED', 'CHANGED')}
EVALUABLE = {k for k, v in label.items() if v != 'NOPROP'}
print('fact co nhan: %d | EVALUABLE (bo NOPROP): %d' % (len(label), len(EVALUABLE)))
print('  WRONG chat che (DELETED)        : %d' % len(WRONG_STRICT))
print('  WRONG rong (DELETED+CHANGED)    : %d' % len(WRONG_WIDE))
print()

# ---------- doc conflict cua PaTeCon ----------
pate_pairs = []
for l in open('tempekg_exp/patecon/output/WD50K_off.all_conflicts', encoding='utf-8'):
    p = l.rstrip('\n').split('\t')
    if len(p) < 3:
        continue
    fa, fb = p[1].split(','), p[2].split(',')
    if len(fa) >= 5 and len(fb) >= 5:
        pate_pairs.append(((fa[0], fa[1], fa[2]), (fb[0], fb[1], fb[2]), fa[3], fb[3]))
print('conflict PaTeCon: %d cap' % len(pate_pairs))

# ---------- TempEKG: loc bang uncertainty ----------
temp_pairs = []
for a, b, ta, tb in pate_pairs:
    ua, ub = UTime.from_padded(ta), UTime.from_padded(tb)
    if classify_pair(ua, ub) == 'CONFLICT':
        temp_pairs.append((a, b, ta, tb))
print('conflict TempEKG (sau loc uncertainty): %d cap' % len(temp_pairs))
print()


def evaluate(pairs, wrong_set, name):
    flagged = set()
    for a, b, _, _ in pairs:
        for f in (a, b):
            if f in EVALUABLE:
                flagged.add(f)
    hit = flagged & wrong_set
    prec = len(hit) / len(flagged) if flagged else 0.0
    rec = len(hit) / len(wrong_set & EVALUABLE) if wrong_set & EVALUABLE else 0.0
    f1 = 2*prec*rec/(prec+rec) if prec+rec else 0.0
    return name, len(pairs), len(flagged), len(hit), prec, rec, f1


print('=' * 78)
print('KET QUA — giao thuc cua ho (fact sai nam trong cap conflict = recall duoc)')
print('=' * 78)
for wname, ws in (('WRONG=DELETED', WRONG_STRICT), ('WRONG=DELETED+CHANGED', WRONG_WIDE)):
    print()
    print('--- nhan su that: %s (%d fact) ---' % (wname, len(ws & EVALUABLE)))
    print('%-14s %8s %9s %7s %9s %9s %8s' %
          ('phuong phap', 'cap', 'fact gan co', 'trung', 'PRECISION', 'RECALL', 'F1'))
    print('-' * 74)
    base = None
    for nm, pr in (('PaTeCon', pate_pairs), ('TempEKG', temp_pairs)):
        n, np_, nf, nh, p, r, f = evaluate(pr, ws, nm)
        print('%-14s %8d %9d %7d %8.2f%% %8.2f%% %7.3f' % (n, np_, nf, nh, 100*p, 100*r, f))
        if base is None:
            base = (p, r, f)
        else:
            print('%-14s %8s %9s %7s %+7.2f%% %+8.2f%% %+7.3f'
                  % ('  chenh lech', '', '', '', 100*(p-base[0]), 100*(r-base[1]), f-base[2]))

# ---------- ty le nen ----------
print()
print('ty le nen (random): %.2f%%' % (100*len(WRONG_STRICT & EVALUABLE)/len(EVALUABLE)))
