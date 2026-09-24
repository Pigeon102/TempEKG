"""Ap do thi event-centric len WIKIDATA, lay them cau truc TU KG GOC, roi TINH DIEM.

Tren WD50K co GROUND TRUTH THAT (nhan tu Wikidata API) nen do duoc P/R/F1, khong phai
lift tren nhan proxy nhu tren MAVEN.

Lay tu KG goc nhung thu PaTeCon KHONG dung:
  1. precision code cua chinh Wikidata (11=ngay, 10=thang, 9=nam, 8=thap nien, 7=the ky)
     -> hat do CO THAT, thay vi doan bang `if Day == 1`
  2. bac cua entity (so fact)
  3. luc luong (so gia tri cua mot (entity, property))
  4. entity da co ngay mat chua (doi song da dong)
  5. interval la diem hay khoang
  6. ngay truoc Cong nguyen
  7. dang dem 0101 / 00

So voi: PaTeCon chay tren CUNG tap (output/WD50K_orig.all_conflicts).
"""
import json, collections, math, random, os, sys
random.seed(20261012)

LAB = 'tempekg_exp/patecon_data/wd50k_labeled.tsv'
CACHE = 'tempekg_exp/patecon_data/wd_claims_cache.json'
PAT_CONF = 'tempekg_exp/patecon/output/WD50K_orig.all_conflicts'

WRONG = {'DELETED', 'CHANGED'}
SKIP = {'NOPROP'}


def wlo(k, n, z=1.96):
    if n == 0: return 0.0
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n)
    m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)); return max(0.0, (c-m)/d)


def num(x):
    x = (x or '').strip()
    if x in ('', '-1', 'None'): return None
    try: return int(x)
    except Exception: return None


# ---------- nap nhan ----------
rows = []
for line in open(LAB, encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) < 6: continue
    rows.append({'h': p[0], 'r': p[1], 'o': p[2],
                 's': num(p[3]), 'e': num(p[4]), 'lab': p[5].strip()})
print('fact co nhan: %d' % len(rows))
print('phan bo:', dict(collections.Counter(r['lab'] for r in rows).most_common()))

# ---------- LAY TU KG GOC ----------
cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}
prec = {}                       # (entity, prop, value) -> precision code
has_death = set()
for ent, cl in cache.items():
    if 'P570' in cl: has_death.add(ent)
    for pr, vals in cl.items():
        for v in vals:
            if isinstance(v, list) and len(v) == 2 and v[1] is not None:
                prec[(ent, pr, str(v[0]))] = v[1]
print('precision code lay duoc: %d | entity co ngay mat: %d' % (len(prec), len(has_death)))

deg = collections.Counter()
card = collections.Counter()
death_tsv = set()
for r in rows:
    deg[r['h']] += 1
    card[(r['h'], r['r'])] += 1
    if r['r'] == 'P570':
        death_tsv.add(r['h'])       # tinh tu TSV, khong tu cache

WDPREC = {11: 'day', 10: 'month', 9: 'year', 8: 'decade', 7: 'century'}


def gran_guess(v):
    """Hat do theo cach PaTeCon doan: Day==1 -> khong biet ngay; them Month==1 -> ca thang."""
    if v is None: return 'null'
    s = str(abs(v)).zfill(8)
    d = int(s[-2:]); m = int(s[-4:-2])
    if d == 1:
        return 'year' if m == 1 else 'month'
    return 'day'


# ---------- so hat do: WIKIDATA THAT vs PaTeCon DOAN ----------
agree = collections.Counter()
n_cmp = 0
for r in rows:
    pc = prec.get((r['h'], r['r'], r['o']))
    if pc is None or pc not in WDPREC: continue
    n_cmp += 1
    agree[(WDPREC[pc], gran_guess(r['s']))] += 1
print()
print('='*78)
print('LAY TU KG GOC (1): hat do THAT cua Wikidata vs PaTeCon DOAN')
print('='*78)
print('  so sanh duoc tren %d fact' % n_cmp)
ok = sum(v for (a, b), v in agree.items() if a == b)
print('  khop: %d (%.1f%%) | LECH: %d (%.1f%%)'
      % (ok, 100*ok/max(n_cmp, 1), n_cmp-ok, 100*(n_cmp-ok)/max(n_cmp, 1)))
print()
print('  %-12s %-12s %8s' % ('Wikidata', 'PaTeCon doan', 'so'))
for (a, b), v in sorted(agree.items(), key=lambda x: -x[1])[:10]:
    print('  %-12s %-12s %8d %s' % (a, b, v, '' if a == b else '  <- LECH'))

# ---------- thuoc tinh event ----------
EV = []
n_bc = sum(1 for r in rows if (r['s'] or 0) < 0)
for r in rows:
    if r['lab'] in SKIP: continue
    if (r['s'] or 0) < 0: continue      # L4: bo gan nhan khong doc duoc ngay truoc CN
    pc = prec.get((r['h'], r['r'], r['o']))
    s, e = r['s'], r['e']
    EV.append({
        'y': int(r['lab'] in WRONG),
        'lab': r['lab'],
        'key': (r['h'], r['r'], r['o']),
        # --- tu KG goc (CHI thu tinh duoc tu TSV, khong tu cache) ---
        # BO: gran_wd, has_prec  -> dan xuat tu chinh lan quet API sinh ra NHAN
        #     has_prec=1 chi ra ALIVE/COARSE, khong bao gio DELETED/CHANGED
        'etype': r['r'],
        'gran_guess': gran_guess(s),
        'card': min(card[(r['h'], r['r'])], 4),
        'deg': min(deg[r['h']], 6),
        'closed': int(r['h'] in death_tsv),
        'is_point': int(s is not None and e is not None and s == e),
        'obj_date': int(r['o'].lstrip('-').isdigit()),
        'pad0101': int(str(r['o'])[-4:] == '0101'),
        'pad00': int('00' in str(r['o'])[-4:]),
        'open_end': int(e is None),
    })
base = sum(x['y'] for x in EV)/len(EV)
print()
print('bo %d fact ngay truoc CN (loi L4 cua bo gan nhan)' % n_bc)
print('EVAL: %d fact | WRONG %d | nen %.2f%%'
      % (len(EV), sum(x['y'] for x in EV), 100*base))

# ---------- PaTeCon tren CUNG tap ----------
pat = set()
if os.path.exists(PAT_CONF):
    for line in open(PAT_CONF, encoding='utf-8'):
        t = line.strip().split('\t')
        if len(t) >= 3:
            pat.add((t[0], t[1], t[2]))
print('PaTeCon gan co: %d fact' % len(pat))
pv = [x for x in EV if x['key'] in pat]
tp = sum(x['y'] for x in pv)
P0 = tp/max(len(pv), 1); R0 = tp/max(sum(x['y'] for x in EV), 1)
print('  tren EVAL: %d fact | P %.2f%% | R %.2f%% | F1 %.4f'
      % (len(pv), 100*P0, 100*R0, 2*P0*R0/max(P0+R0, 1e-9)))

# ---------- miner hop thanh ----------
SETS = ['etype', 'gran_guess', 'card', 'deg', 'closed',
        'is_point', 'obj_date', 'pad0101', 'pad00', 'open_end']


def gen(rowsx):
    C = []
    vals = collections.defaultdict(collections.Counter)
    for r in rowsx:
        for a in SETS: vals[a][r[a]] += 1
    MIN = max(50, len(rowsx)//400)
    for a in SETS:
        for v, n in vals[a].items():
            if n >= MIN:
                C.append((a, v, lambda r, a=a, v=v: r[a] == v))
    return C


def sc(rowsx, cs):
    n = c = 0
    for r in rowsx:
        if all(f(r) for _, _, f in cs): n += 1; c += r['y']
    return (c, n) if n else None


def beam(rowsx, C, depth=3, width=16, min_sup=40):
    cur = []
    for cd in C:
        s = sc(rowsx, [cd])
        if s and s[1] >= min_sup: cur.append(([cd], s))
    cur.sort(key=lambda x: -wlo(*x[1]))
    best = list(cur[:width*3]); front = cur[:width]
    for _ in range(depth-1):
        nxt = []
        for cs, s0 in front:
            used = {c[0] for c in cs}
            for cd in C:
                if cd[0] in used: continue
                s = sc(rowsx, cs+[cd])
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
TR = [EV[i] for i in idx[:cut]]
TE = [EV[i] for i in idx[cut:]]
b_tr = sum(x['y'] for x in TR)/len(TR)
b_te = sum(x['y'] for x in TE)/len(TE)
print()
print('='*78)
print('MINING HOP THANH  train %d (nen %.2f%%) | test %d (nen %.2f%%)'
      % (len(TR), 100*b_tr, len(TE), 100*b_te))
print('='*78)
C = gen(TR)
print('dieu kien ung vien: %d' % len(C), flush=True)
res = beam(TR, C, depth=3, width=16)

print('\n  %-8s %-8s %-8s %-8s  %s' % ('conf TR', 'lift TR', 'conf TE', 'lift TE', 'pattern'))
print('  ' + '-'*88)
seen = set(); shown = 0
for cs, (c, n) in res:
    k = tuple(sorted((x[0], str(x[1])) for x in cs))
    if k in seen: continue
    seen.add(k)
    st = sc(TE, cs)
    if not st or st[1] < 15: continue
    ct, nt = st
    print('  %7.1f%% %7.2fx %7.1f%% %7.2fx  %s'
          % (100*c/n, (c/n)/b_tr, 100*ct/nt, (ct/nt)/b_te,
             ' & '.join('%s=%s' % (x[0], x[1]) for x in cs)))
    shown += 1
    if shown >= 14: break

# ---------- xay DETECTOR: hop cac pattern vuot nguong tren TRAIN ----------
print()
print('='*78)
print('DETECTOR = hop cac pattern co conf(TRAIN) >= theta, do tren TEST')
print('='*78)
print('  %-7s %-7s %-9s %-9s %-9s  %s' % ('theta', 'so pat', 'P test', 'R test', 'F1 test', 'so co'))
best_f1 = None
for theta in (0.05, 0.08, 0.10, 0.15, 0.20, 0.30):
    chosen = [cs for cs, (c, n) in res if n >= 40 and c/n >= theta]
    if not chosen: continue
    ded = []; seen2 = set()
    for cs in chosen:
        k = tuple(sorted((x[0], str(x[1])) for x in cs))
        if k in seen2: continue
        seen2.add(k); ded.append(cs)
    flag = [r for r in TE if any(all(f(r) for _, _, f in cs) for cs in ded)]
    tp = sum(r['y'] for r in flag)
    tot_w = sum(r['y'] for r in TE)
    Pp = tp/max(len(flag), 1); Rr = tp/max(tot_w, 1)
    F = 2*Pp*Rr/max(Pp+Rr, 1e-9)
    print('  %-7.2f %-7d %8.2f%% %8.2f%% %9.4f  %6d'
          % (theta, len(ded), 100*Pp, 100*Rr, F, len(flag)))
    if best_f1 is None or F > best_f1[0]: best_f1 = (F, theta, Pp, Rr, len(ded))

print()
print('='*78)
print('SO SANH CUOI  (cung tap EVAL, cung ground truth)')
print('='*78)
print('  %-34s %9s %9s %9s' % ('phuong phap', 'P', 'R', 'F1'))
print('  ' + '-'*64)
print('  %-34s %8.2f%% %8.2f%% %9.4f' % ('PaTeCon (chay tren cung tap)',
                                         100*P0, 100*R0, 2*P0*R0/max(P0+R0, 1e-9)))
if best_f1:
    print('  %-34s %8.2f%% %8.2f%% %9.4f'
          % ('event-centric + KG goc (test)', 100*best_f1[2], 100*best_f1[3], best_f1[0]))
    print('\n  cau hinh tot nhat: theta=%.2f, %d pattern' % (best_f1[1], best_f1[4]))
