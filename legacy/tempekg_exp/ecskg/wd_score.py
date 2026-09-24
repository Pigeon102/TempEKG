"""So BA cach tren DUNG MOT tap EVAL (24,284 khoa duy nhat, nen 3.06%).

  1. PaTeCon goc                       -> flags tu output/WD50K_orig.all_conflicts
  2. Phan tang uncertainty (ban truoc) -> tai lap tu quy tac da ghi
  3. Event-centric + hop thanh (moi)   -> mine tren train, do tren test

Da bo moi dac trung dan xuat tu nhan (gran_wd, has_prec, is_bc) sau khi bat ro ri.
"""
import collections, math, random, os
random.seed(20261012)
WRONG = {'DELETED', 'CHANGED'}


def wlo(k, n, z=1.96):
    if n == 0: return 0.0
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n)
    m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)); return max(0.0, (c-m)/d)


def num(x):
    x = (x or '').strip()
    if x in ('', '-1', 'None'): return None
    try: return int(x)
    except Exception: return None


# ---------- EVAL: khoa duy nhat, bo NOPROP va bo ngay truoc CN (loi L4) ----------
raw = {}
for line in open('tempekg_exp/patecon_data/wd50k_labeled.tsv', encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) < 6: continue
    lab = p[5].strip(); s = num(p[3]); e = num(p[4])
    if lab == 'NOPROP' or (s or 0) < 0: continue
    raw[(p[0], p[1], p[2])] = (s, e, lab)

deg = collections.Counter(); card = collections.Counter(); death = set()
for (h, r, o) in raw:
    deg[h] += 1; card[(h, r)] += 1
    if r == 'P570': death.add(h)


def gran_guess(v):
    if v is None: return 'null'
    t = str(abs(v)).zfill(8)
    d = int(t[-2:]); m = int(t[-4:-2])
    return ('year' if m == 1 else 'month') if d == 1 else 'day'


EV = []
for (h, r, o), (s, e, lab) in raw.items():
    EV.append({'y': int(lab in WRONG), 'key': (h, r, o), 'lab': lab,
               'etype': r, 'gran_guess': gran_guess(s),
               'card': min(card[(h, r)], 4), 'deg': min(deg[h], 6),
               'closed': int(h in death),
               'is_point': int(s is not None and e is not None and s == e),
               'obj_date': int(o.lstrip('-').isdigit()),
               'pad0101': int(str(o)[-4:] == '0101'),
               'pad00': int('00' in str(o)[-4:]),
               'open_end': int(e is None),
               's': s, 'e': e, 'o': o})
NW = sum(x['y'] for x in EV)
base = NW/len(EV)
print('EVAL %d khoa | WRONG %d | nen %.2f%%' % (len(EV), NW, 100*base))


def score(flagged, universe):
    fl = [r for r in universe if r['key'] in flagged] if isinstance(flagged, set) else flagged
    tp = sum(r['y'] for r in fl)
    tw = sum(r['y'] for r in universe)
    P = tp/max(len(fl), 1); R = tp/max(tw, 1)
    return P, R, 2*P*R/max(P+R, 1e-9), len(fl)


# ---------- 1. PaTeCon ----------
pat = set()
for line in open('tempekg_exp/patecon/output/WD50K_orig.all_conflicts', encoding='utf-8'):
    for fld in line.rstrip('\n').split('\t')[1:]:
        c = fld.split(',')
        if len(c) >= 3 and c[0].startswith('Q'):
            pat.add((c[0], c[1], c[2]))
P1 = score(pat, EV)

# ---------- 2. phan tang uncertainty (ban truoc) ----------
# quy tac: xep hang cap theo tang CONFLICT > PARTIAL_OVERLAP > REFINEMENT > IDENTICAL,
# chi gan co cac cap o tang CONFLICT, cong rang buoc dinh luong (start > end).
def utime(v, gg):
    if v is None: return None
    if gg == 'year': return (v//10000*10000+101, v//10000*10000+1231)
    if gg == 'month': return (v//100*100+1, v//100*100+31)
    return (v, v)


by_hr = collections.defaultdict(list)
for r in EV:
    by_hr[(r['key'][0], r['key'][1])].append(r)
tier = set()
for k, lst in by_hr.items():
    if len(lst) < 2: continue
    for i in range(len(lst)):
        for j in range(i+1, len(lst)):
            a = utime(lst[i]['s'], lst[i]['gran_guess'])
            b = utime(lst[j]['s'], lst[j]['gran_guess'])
            if not a or not b: continue
            if a[1] < b[0] or b[1] < a[0]:            # tang CONFLICT
                tier.add(lst[i]['key']); tier.add(lst[j]['key'])
for r in EV:                                          # rang buoc dinh luong
    if r['s'] is not None and r['e'] is not None and r['s'] > r['e']:
        tier.add(r['key'])
P2 = score(tier, EV)

# ---------- 3. event-centric + hop thanh ----------
SETS = ['etype', 'gran_guess', 'card', 'deg', 'closed',
        'is_point', 'obj_date', 'pad0101', 'pad00', 'open_end']


def gen(rows):
    C = []; vals = collections.defaultdict(collections.Counter)
    for r in rows:
        for a in SETS: vals[a][r[a]] += 1
    MIN = max(40, len(rows)//400)
    for a in SETS:
        for v, n in vals[a].items():
            if n >= MIN:
                C.append((a, v, lambda r, a=a, v=v: r[a] == v))
    return C


def sc(rows, cs):
    n = c = 0
    for r in rows:
        if all(f(r) for _, _, f in cs): n += 1; c += r['y']
    return (c, n) if n else None


def beam(rows, C, depth=3, width=16, min_sup=30):
    cur = []
    for cd in C:
        s = sc(rows, [cd])
        if s and s[1] >= min_sup: cur.append(([cd], s))
    cur.sort(key=lambda x: -wlo(*x[1]))
    best = list(cur[:width*3]); front = cur[:width]
    for _ in range(depth-1):
        nxt = []
        for cs, s0 in front:
            used = {c[0] for c in cs}
            for cd in C:
                if cd[0] in used: continue
                s = sc(rows, cs+[cd])
                if s and s[1] >= min_sup and wlo(*s) > wlo(*s0):
                    nxt.append((cs+[cd], s))
        if not nxt: break
        nxt.sort(key=lambda x: -wlo(*x[1]))
        seen = set(); ded = []
        for cs, s in nxt:
            k = tuple(sorted((c[0], str(c[1])) for c in cs))
            if k in seen: continue
            seen.add(k); ded.append((cs, s))
        front = ded[:width]; best += ded[:width*2]
    best.sort(key=lambda x: -wlo(*x[1]))
    return best


idx = list(range(len(EV))); random.shuffle(idx)
cut = int(0.7*len(idx))
TR = [EV[i] for i in idx[:cut]]; TE = [EV[i] for i in idx[cut:]]
res = beam(TR, gen(TR))
b_tr = sum(x['y'] for x in TR)/len(TR)

print('\ntop pattern (train -> test):')
seen = set(); shown = 0
for cs, (c, n) in res:
    k = tuple(sorted((x[0], str(x[1])) for x in cs))
    if k in seen: continue
    seen.add(k)
    st = sc(TE, cs)
    if not st or st[1] < 15: continue
    print('  TR %5.1f%% (%4d) | TE %5.1f%% (%4d) | %s'
          % (100*c/n, n, 100*st[0]/st[1], st[1],
             ' & '.join('%s=%s' % (x[0], x[1]) for x in cs)))
    shown += 1
    if shown >= 8: break

print('\ndetector tren TEST:')
print('  %-7s %-7s %-9s %-9s %-9s' % ('theta', 'so pat', 'P', 'R', 'F1'))
best3 = None
for theta in (0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25):
    ded = []; seen2 = set()
    for cs, (c, n) in res:
        if n < 30 or c/n < theta: continue
        k = tuple(sorted((x[0], str(x[1])) for x in cs))
        if k in seen2: continue
        seen2.add(k); ded.append(cs)
    if not ded: continue
    fl = [r for r in TE if any(all(f(r) for _, _, f in cs) for cs in ded)]
    s = score(fl, TE)
    print('  %-7.2f %-7d %8.2f%% %8.2f%% %9.4f' % (theta, len(ded), 100*s[0], 100*s[1], s[2]))
    if best3 is None or s[2] > best3[2]: best3 = s + (theta, len(ded))

# so tren TEST cho cong bang
P1t = score(pat, TE); P2t = score(tier, TE)
print('\n' + '='*76)
print('SO SANH tren TAP TEST (%d khoa, nen %.2f%%)'
      % (len(TE), 100*sum(x['y'] for x in TE)/len(TE)))
print('='*76)
print('  %-38s %9s %9s %9s' % ('phuong phap', 'P', 'R', 'F1'))
print('  ' + '-'*68)
print('  %-38s %8.2f%% %8.2f%% %9.4f' % ('1. PaTeCon goc', 100*P1t[0], 100*P1t[1], P1t[2]))
print('  %-38s %8.2f%% %8.2f%% %9.4f' % ('2. Phan tang uncertainty', 100*P2t[0], 100*P2t[1], P2t[2]))
if best3:
    print('  %-38s %8.2f%% %8.2f%% %9.4f' % ('3. Event-centric + hop thanh',
                                             100*best3[0], 100*best3[1], best3[2]))
print('\n  (tren TOAN EVAL: PaTeCon F1 %.4f | phan tang F1 %.4f)' % (P1[2], P2[2]))
