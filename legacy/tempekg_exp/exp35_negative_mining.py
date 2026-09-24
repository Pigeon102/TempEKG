"""EXP35 - Mine constraint DUNG roi lay PHU DINH lam constraint SAI.

Y tuong nguoi dung: thay vi mine "cai gi hay xay ra", mine "cai gi LUON DUNG"
roi bat ky vi pham nao cua no deu la SAI.

Khac voi PaTeCon o cho: ho mine constraint conf>=0.9 (tuc 10%% du lieu vi pham,
va ho goi 10%% do la conflict). Ta mine constraint conf ~= 1.0 (gan nhu KHONG co
ngoai le), roi vi pham cua no moi la tin hieu manh.

Ba muc nguong:
   theta=1.00  tuyet doi khong ngoai le    -> vi pham = rat co the SAI
   theta=0.99
   theta=0.95
"""
import collections, math, sys

label = {}
for l in open('patecon_data/wd50k_labeled.tsv', encoding='utf-8'):
    p = l.rstrip('\n').split('\t')
    if len(p) >= 6:
        label[(p[0], p[1], p[2])] = p[5]
# loai ngay am (loi pipeline da biet)
BAD = {k for k in label if k[2].startswith('-')}
EVAL = {k for k, v in label.items() if v != 'NOPROP'} - BAD
W = {k for k, v in label.items() if v in ('DELETED', 'CHANGED')} & EVAL
Wn = len(W)
print('EVAL %d | WRONG %d | ty le nen %.2f%%' % (len(EVAL), Wn, 100*Wn/len(EVAL)))


def yr(v):
    return int(v[:4]) if v[:4].isdigit() else None


ent = collections.defaultdict(dict)
for (q, p, o) in EVAL:
    ent[q].setdefault(p, []).append(o)


def wilson_lo(k, n, z=1.96):
    if n == 0:
        return 0.0
    p = k/n
    d = 1 + z*z/n
    return (p + z*z/(2*n) - z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)))/d


# ---------- 1. MINE constraint THU TU giua cac property ----------
# voi moi cap property (p1,p2), dem xem p1 co LUON truoc p2 khong
order = collections.defaultdict(lambda: [0, 0])   # (p1,p2) -> [dung, tong]
for q, props in ent.items():
    ps = [p for p in props if any(yr(x) for x in props[p])]
    for p1 in ps:
        for p2 in ps:
            if p1 >= p2:
                continue
            y1 = [yr(x) for x in props[p1] if yr(x)]
            y2 = [yr(x) for x in props[p2] if yr(x)]
            for a in y1:
                for b in y2:
                    order[(p1, p2)][1] += 1
                    if a <= b:
                        order[(p1, p2)][0] += 1

print()
print('=== CONSTRAINT THU TU mine duoc ===')
print('%-16s %8s %8s %9s %9s' % ('cap property', 'tong', 'thoa', 'conf', 'Wilson_lo'))
print('-' * 56)
rules = {}
for (p1, p2), (ok, n) in sorted(order.items(), key=lambda x: -x[1][1]):
    if n < 30:
        continue
    conf = ok/n
    wl = wilson_lo(ok, n)
    # ca hai chieu: p1<=p2 hoac p2<=p1
    conf_r = (n-ok)/n
    wl_r = wilson_lo(n-ok, n)
    best = max((conf, wl, 'FWD'), (conf_r, wl_r, 'REV'))
    print('%-16s %8d %8d %8.4f %8.4f  %s' % ('%s->%s' % (p1, p2), n, ok, conf, wl,
                                             'FWD' if conf > conf_r else 'REV'))
    if best[1] >= 0.90:
        rules[(p1, p2)] = (best[2], best[0], best[1], n)

print()
print('=== AP DUNG: vi pham constraint gan-tuyet-doi = SAI ===')
print('%-10s %8s %8s %9s %9s %7s' % ('theta', 'so luat', 'fact', 'PRECISION', 'RECALL', 'F1'))
print('-' * 60)
for theta in (1.00, 0.999, 0.99, 0.95, 0.90):
    keep = {k: v for k, v in rules.items() if v[2] >= theta}
    flag = set()
    for q, props in ent.items():
        for (p1, p2), (dirn, cf, wl, n) in keep.items():
            if p1 not in props or p2 not in props:
                continue
            y1 = [(x, yr(x)) for x in props[p1] if yr(x)]
            y2 = [(x, yr(x)) for x in props[p2] if yr(x)]
            for o1, a in y1:
                for o2, b in y2:
                    bad = (a > b) if dirn == 'FWD' else (b > a)
                    if bad:
                        flag.add((q, p1, o1)); flag.add((q, p2, o2))
    flag &= EVAL
    h = flag & W
    P = len(h)/max(len(flag), 1)
    R = len(h)/Wn
    F = 2*P*R/(P+R) if P+R else 0
    print('%-10.3f %8d %8d %8.2f%% %8.2f%% %7.3f' % (theta, len(keep), len(flag), 100*P, 100*R, F))
