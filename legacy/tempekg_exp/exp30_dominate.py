"""EXP30 - He thong TROI CA HAI chi so, tu THUAT TOAN.

Y tuong: precision va recall den tu HAI CO CHE KHAC NHAU, tac dong len HAI TAP KHAC NHAU:
   PRECISION <- phan tang uncertainty, loai cap REFINEMENT   (tap: cap da-gia-tri cua PaTeCon)
   RECALL    <- detector fact DON GIA TRI                    (tap: PaTeCon KHONG voi toi)

Do duoc (EXP29b): tren fact don gia tri, ty le nen 3.47%, nhung
   thang/ngay = 00 -> P(sai) 58.1%  (lift 16.7x)
   gia tri 0101    -> P(sai) 43.1%  (lift 12.4x)
   object la entity-> P(sai) 24.7%  (lift 7.1x)
"""
import sys, collections
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

sp = collections.defaultdict(set)
for k in EVAL:
    sp[(k[0], k[1])].add(k[2])


def yr(v):
    return int(v[:4]) if v[:4].isdigit() else None


# ---------- 1. PaTeCon, phan tang ----------
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
PATE = set().union(*tiers.values())

# ---------- 2. detector fact DON GIA TRI ----------
def single(k):
    return len(sp[(k[0], k[1])]) == 1


sig = collections.defaultdict(set)
for k in EVAL:
    if not single(k):
        continue
    o = k[2]
    if o.isdigit() and len(o) == 8:
        if o[4:6] == '00' or o[6:] == '00':
            sig['S_m00d00'].add(k)
        elif o[4:] == '0101':
            sig['S_0101'].add(k)
    # object la entity (khong phai ngay) -> quan he bi go
    elif not o.isdigit():
        sig['S_entobj'].add(k)

# ---------- 3. rang buoc dinh luong ----------
ent = collections.defaultdict(dict)
for (q, p, o) in EVAL:
    ent[q].setdefault(p, []).append(o)
quant = set()
for q, props in ent.items():
    b = sorted({yr(x) for x in props.get('P569', []) if yr(x)})
    d = sorted({yr(x) for x in props.get('P570', []) if yr(x)})
    car = sorted({yr(x) for x in props.get('P54', []) if yr(x)})

    def mark(p_, years):
        for o in props.get(p_, []):
            if yr(o) in years:
                quant.add((q, p_, o))
    if b and d:
        for bb in b:
            for dd in d:
                if dd - bb > 120 or dd - bb < 0:
                    mark('P569', {bb}); mark('P570', {dd})
    if b and car:
        bad = {c for c in car if c < min(b) or c > min(b) + 70}
        if bad:
            mark('P54', bad)
    if d and car:
        bad = {c for c in car if c > max(d) + 1}
        if bad:
            mark('P54', bad)


def ev(S):
    h = S & W
    P = len(h)/max(len(S), 1)
    R = len(h)/Wn
    return len(S), len(h), P, R, (2*P*R/(P+R) if P+R else 0)


print('%-34s %7s %6s %9s %9s %7s' % ('cau hinh', 'fact', 'trung', 'PRECISION', 'RECALL', 'F1'))
print('-' * 78)
bn, bh, bP, bR, bF = ev(PATE)
print('%-34s %7d %6d %8.2f%% %8.2f%% %7.3f  <-- BASELINE' % ('PaTeCon (goc)', bn, bh, 100*bP, 100*bR, bF))
print()
for nm in ('S_m00d00', 'S_0101', 'S_entobj'):
    n, h, P, R, F = ev(sig[nm])
    print('%-34s %7d %6d %8.2f%% %8.2f%% %7.3f' % ('  ' + nm + ' (rieng)', n, h, 100*P, 100*R, F))
print()
HIGH = tiers['CONFLICT'] | tiers['UNDECIDABLE']
combos = [
    ('phan tang (P cao)', HIGH),
    ('phan tang + m00d00', HIGH | sig['S_m00d00']),
    ('phan tang + m00d00 + 0101', HIGH | sig['S_m00d00'] | sig['S_0101']),
    ('  ^ + dinh luong', HIGH | sig['S_m00d00'] | sig['S_0101'] | quant),
    ('  ^ + entity-obj', HIGH | sig['S_m00d00'] | sig['S_0101'] | quant | sig['S_entobj']),
    ('TAT CA tang + moi detector', PATE | sig['S_m00d00'] | sig['S_0101'] | quant | sig['S_entobj']),
]
for nm, S in combos:
    n, h, P, R, F = ev(S)
    tag = ''
    if P > bP and R > bR:
        tag = '  *** TROI CA HAI ***'
    elif P > bP and R >= bR:
        tag = '  ** P tot, R bang **'
    print('%-34s %7d %6d %8.2f%% %8.2f%% %7.3f%s' % (nm, n, h, 100*P, 100*R, F, tag))
