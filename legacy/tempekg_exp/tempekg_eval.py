"""Sua giao thuc HELD-OUT cho dung y nghia.

Loi o ban truoc: "kiem chung" chi kiem nguon B CO CANH khong, chu khong phai B co
MAU THUAN khong. Va detector dung ca A lan B.

Thiet ke DUNG:
   DETECTOR = S5 (constraint MINE duoc, thong ke, mem)  <- cai can validate
   VERIFIER = S2/S3/S4 (ngu nghia + logic, CUNG)        <- chuan vang doc lap

   Precision = trong so cap S5 gan co, bao nhieu % duoc nguon CUNG xac nhan la co van de
   Recall    = trong so cap nguon CUNG gan co, S5 bat duoc bao nhieu %

S5 KHONG dung S2/S3/S4 de mine -> khong vong lap.
"""
import collections, math, random
from tempekg import build, INV, NORM

random.seed(20261012)


def wilson_lo(k, n, z=1.96):
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z*z/n
    return (p + z*z/(2*n) - z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / d


g = build()
print('event %d | canh %d' % (len(g.events), len(g.cedge)))

# ---------- gom quan he S1 theo cap ----------
S1 = {}
for (doc, a, b, s), (imp, _) in g.cedge.items():
    if s == 'S1':
        S1[(doc, a, b)] = imp

# ---------- chia document ----------
docs = sorted({g.events[e]['doc'] for e in g.events})
random.shuffle(docs)
cut = int(0.8 * len(docs))
MINE, EVAL = set(docs[:cut]), set(docs[cut:])

# ---------- S5: mine constraint tu (type1,type2) tren MINE, CHI dung S1 ----------
sig = collections.defaultdict(collections.Counter)
for (doc, a, b), imp in S1.items():
    if doc not in MINE:
        continue
    ta, tb = g.events[a]['type'], g.events[b]['type']
    sig[(ta, tb)][imp] += 1

S5_RULES = {}
for k, c in sig.items():
    n = sum(c.values())
    if n < 10:
        continue
    lab, kk = c.most_common(1)[0]
    if wilson_lo(kk, n) >= 0.7:
        S5_RULES[k] = lab
print('S5: %d luat mine duoc (Wilson>=0.7, sup>=10)' % len(S5_RULES))

# ---------- DETECTOR S5: cap tren EVAL ma quan he thuc KHAC luat ----------
s5_flag = set()
for (doc, a, b), imp in S1.items():
    if doc not in EVAL:
        continue
    r = S5_RULES.get((g.events[a]['type'], g.events[b]['type']))
    if r is not None and r != imp:
        s5_flag.add((doc,) + tuple(sorted([a, b])))

# ---------- VERIFIER: nguon CUNG S2/S3/S4 mau thuan voi S1 ----------
def implied(doc, a, b, s):
    if (doc, a, b, s) in g.cedge:
        return g.cedge[(doc, a, b, s)][0]
    if (doc, b, a, s) in g.cedge:
        return INV.get(g.cedge[(doc, b, a, s)][0], g.cedge[(doc, b, a, s)][0])
    return None


def contradicts(x, y):
    """x = quan he thoi gian S1, y = rang buoc suy ra tu nguon cung"""
    if x is None or y is None:
        return False
    if y == 'NOT_AFTER' and x == 'AFTER':
        return True
    if y == 'NOT_BEFORE' and x == 'BEFORE':
        return True
    # subevent: cha CHUA con (ca hai chieu)
    if y == 'CONTAINS' and x not in ('CONTAINS', 'SIMULTANEOUS'):
        return True
    if y == 'CONTAINED' and x not in ('CONTAINED', 'SIMULTANEOUS'):
        return True
    if {x, y} == {'BEFORE', 'AFTER'}:
        return True
    return False


hard_flag = set()
for (doc, a, b), imp in S1.items():
    if doc not in EVAL:
        continue
    for s in ('S2', 'S3', 'S4'):
        if contradicts(imp, implied(doc, a, b, s)):
            hard_flag.add((doc,) + tuple(sorted([a, b])))
            break

inter = s5_flag & hard_flag
prec = len(inter) / len(s5_flag) if s5_flag else float('nan')
rec = len(inter) / len(hard_flag) if hard_flag else float('nan')

print()
print('=' * 66)
print('HELD-OUT SOURCE EVALUATION (tren %d document EVAL)' % len(EVAL))
print('=' * 66)
print('  DETECTOR  S5 (mine, mem)  gan co : %6d cap' % len(s5_flag))
print('  VERIFIER  S2/S3/S4 (cung) gan co : %6d cap' % len(hard_flag))
print('  giao nhau                        : %6d cap' % len(inter))
print()
print('  PRECISION cua S5 (nguon CUNG xac nhan) : %.2f%%' % (100 * prec))
print('  RECALL    cua S5 (bat duoc bao nhieu)  : %.2f%%' % (100 * rec))
print()
base = len(hard_flag) / max(len({(d,)+tuple(sorted([a,b])) for (d,a,b) in S1 if d in EVAL}), 1)
print('  ty le nen (random baseline precision)  : %.4f%%' % (100 * base))
if prec == prec and base > 0:
    print('  => S5 tot hon ngau nhien %.0f lan' % (prec / base))
