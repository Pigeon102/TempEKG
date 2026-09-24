"""EXP29 - He thong ket hop: PHAN TANG (precision) + DINH LUONG (recall).

Muc tieu: P > PaTeCon VA R >= PaTeCon.

Nguon recall moi: fact DON GIA TRI (88% cai PaTeCon bo sot) - khong the bat bang
constraint can >=2 fact. Phai dung rang buoc DINH LUONG va BIEN PHAN BO.
"""
import sys, collections, statistics
sys.path.insert(0, 'tempekg_exp')
from uncertain_time import UTime, classify_pair

label = {}
for l in open('tempekg_exp/patecon_data/wd50k_labeled.tsv', encoding='utf-8'):
    p = l.rstrip('\n').split('\t')
    if len(p) >= 6:
        label[(p[0], p[1], p[2])] = p[5]
EVAL = {k for k, v in label.items() if v != 'NOPROP'}
W = {k for k, v in label.items() if v in ('DELETED', 'CHANGED')} & EVAL
Wn = len(W)


def yr(v):
    return int(v[:4]) if v[:4].isdigit() else None


ent = collections.defaultdict(dict)
for (q, p, o) in EVAL:
    ent[q].setdefault(p, []).append(o)

# ---------- PaTeCon, phan tang theo uncertainty ----------
tiers = collections.defaultdict(set)
for l in open('tempekg_exp/patecon/output/WD50K_off.all_conflicts', encoding='utf-8'):
    p = l.rstrip('\n').split('\t')
    if len(p) < 3:
        continue
    fa, fb = p[1].split(','), p[2].split(',')
    if len(fa) < 5 or len(fb) < 5:
        continue
    c = classify_pair(UTime.from_padded(fa[3]), UTime.from_padded(fb[3]))
    for f in ((fa[0], fa[1], fa[2]), (fb[0], fb[1], fb[2])):
        if f in EVAL:
            tiers[c].add(f)

# ---------- rang buoc DINH LUONG ----------
quant = set()
why = collections.Counter()
for q, props in ent.items():
    b = sorted({yr(x) for x in props.get('P569', []) if yr(x)})
    d = sorted({yr(x) for x in props.get('P570', []) if yr(x)})
    car = sorted({yr(x) for x in props.get('P54', []) if yr(x)})
    sp = sorted({yr(x) for x in props.get('P26', []) if yr(x)})

    def mark(p_, years, tag):
        for o in props.get(p_, []):
            if yr(o) in years:
                quant.add((q, p_, o))
                why[tag] += 1

    if b and d:
        for bb in b:
            for dd in d:
                if dd - bb > 120 or dd - bb < 0:
                    mark('P569', {bb}, 'tuoi tho phi ly'); mark('P570', {dd}, 'tuoi tho phi ly')
    if b and car:
        bad = {c for c in car if c < min(b) or c > min(b) + 70}
        if bad:
            mark('P54', bad, 'su nghiep lech tuoi')
    if b and sp:
        bad = {c for c in sp if c < min(b) + 12 or c > min(b) + 100}
        if bad:
            mark('P26', bad, 'ket hon lech tuoi')
    if d and car:
        bad = {c for c in car if c > max(d) + 1}
        if bad:
            mark('P54', bad, 'thi dau sau khi chet')
    if d and sp:
        bad = {c for c in sp if c > max(d) + 1}
        if bad:
            mark('P26', bad, 'ket hon sau khi chet')

# ---------- bien phan bo theo property (bat fact DON GIA TRI) ----------
dist = collections.defaultdict(list)
for (q, p, o) in EVAL:
    y = yr(o)
    if y:
        dist[p].append(y)
bounds = {}
for p, ys in dist.items():
    if len(ys) < 50:
        continue
    ys = sorted(ys)
    lo = ys[int(0.001 * len(ys))]
    hi = ys[int(0.999 * len(ys)) - 1]
    bounds[p] = (lo, hi)
outlier = set()
for (q, p, o) in EVAL:
    y = yr(o)
    if y and p in bounds and not (bounds[p][0] <= y <= bounds[p][1]):
        outlier.add((q, p, o))
        why['ngoai bien phan bo %s' % p] += 1

print('rang buoc dinh luong gan co: %d fact' % len(quant))
for k, v in why.most_common(8):
    print('   %-28s %d' % (k, v))
print('bien phan bo:', {k: v for k, v in bounds.items()})
print('outlier phan bo: %d fact' % len(outlier))
print()

PATE = set().union(*tiers.values())


def ev(S, nm):
    h = S & W
    P = len(h)/max(len(S), 1)
    R = len(h)/Wn
    F = 2*P*R/(P+R) if P+R else 0
    return nm, len(S), len(h), P, R, F


configs = [
    ('PaTeCon (goc)', PATE),
    ('T1 CONFLICT', tiers['CONFLICT']),
    ('T1+T2 (+UNDECIDABLE)', tiers['CONFLICT'] | tiers['UNDECIDABLE']),
    ('T1+T2 + dinh luong', tiers['CONFLICT'] | tiers['UNDECIDABLE'] | quant),
    ('T1+T2 + dl + outlier', tiers['CONFLICT'] | tiers['UNDECIDABLE'] | quant | outlier),
    ('TAT CA + dl + outlier', PATE | quant | outlier),
]
print('%-24s %7s %7s %9s %9s %7s' % ('cau hinh', 'fact', 'trung', 'PRECISION', 'RECALL', 'F1'))
print('-' * 68)
bp, br, bf = None, None, None
for nm, S in configs:
    n, nf, nh, P, R, F = ev(S, nm)
    star = ''
    if bp is not None and P > bp and R >= br:
        star = '  <<< VUOT CA HAI'
    print('%-24s %7d %7d %8.2f%% %8.2f%% %7.3f%s' % (n, nf, nh, 100*P, 100*R, F, star))
    if bp is None:
        bp, br, bf = P, R, F
