"""Pattern conflict = HOP THANH nhieu DIEU KIEN, nhieu DANG, tu nhieu TANG.

Ban truoc chi co MOT dang dieu kien (attr == value) tren MOT tang (event). Do cung la
ly do cardinality bi ro ri: gran_set='day|month' bi so bang chuoi, nen "co 2 hat do"
lan vao dieu kien dang thuc.

O day tach ra ba TANG va sau DANG dieu kien:

  TANG            thuoc tinh
  ----            ----------
  T_event         etype, n_role, sent_bucket
  T_entity        etypeset, roleset, has_person/org/loc
  T_anchor        gran[], method[], hull (be rong bao), khoang cach anchor

  DANG dieu kien
  --------------
  EQ    attr == v                    (dang thuc)
  HAS   v thuoc tap attr             (thanh vien — dung cho thuoc tinh tap)
  ALL   moi phan tu attr == v        (pho quat)
  CNT   |distinct attr| >= k         (luc luong — TACH RIENG, khong lan vao EQ)
  MIX   ton tai cap phan tu khac nhau (bat dong nhat)
  NUM   dac trung so >= nguong       (hull, span)

Hop thanh bang beam search den do sau 3, trong TUNG TANG so anchor (tranh ro ri).
Diem = Wilson lower bound tren ti le conflict, so voi nen CUA TANG.
"""
from __future__ import annotations
import json, collections, zipfile, io, sys, os, math, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timex_norm2 import doc_reference_chain


def wilson_lo(k, n, z=1.96):
    if n == 0:
        return 0.0
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n)
    m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return max(0.0, (c-m)/d)


def days(v):
    """YYYYMMDD -> so ngay tho (du de so be rong)."""
    y = v//10000; m = (v//100) % 100; d = v % 100
    return y*365 + max(m-1, 0)*30 + max(d-1, 0)


# ==================================================== nap du lieu
docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line); docs[d['id']] = d

z = zipfile.ZipFile('MAVEN-Arg.zip')
argrec = {}
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            et = {e['id']: e.get('type', 'Other') for e in d.get('entities', [])}
            for e in d['events']:
                rr = collections.defaultdict(list)
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            rr[r].append(et.get(v['entity_id'], 'Other'))
                if rr:
                    argrec[(d['id'], e['id'])] = dict(rr)

EV = []
for doc, d in docs.items():
    tl = [(t['id'], t['mention']) for t in
          sorted(d['TIMEX'], key=lambda x: (x['sent_id'], x['offset'][0]))]
    norm = doc_reference_chain(tl)
    nsent = len(d['tokens'])
    anc = collections.defaultdict(list)
    for h, t in d['temporal_relations'].get('CONTAINS', []):
        if h in norm: anc[t].append(h)
        if t in norm: anc[h].append(t)
    for e in d['events']:
        eid = e['id']
        ms = [m['sent_id'] for m in e['mention'] if 'sent_id' in m]
        s0 = min(ms) if ms else 0
        iv, gr, me = [], [], []
        for tid in anc.get(eid, []):
            r = norm.get(tid)
            if r and r[0] is not None and r[2] != 'duration':
                iv.append((r[0], r[1])); gr.append(r[2])
                me.append(r[3] if len(r) > 3 else 'regex')
        if len(iv) < 2:
            continue                                  # chi xet event xet duoc
        rr = argrec.get((doc, eid), {})
        ets = sorted({x for v in rr.values() for x in v})
        roles = sorted(rr)
        lo = min(a[0] for a in iv); hi = max(a[1] for a in iv)
        conflict = max(a[0] for a in iv) > min(a[1] for a in iv)
        EV.append({
            'y': int(conflict), 'k': len(iv),
            # --- T_event ---
            'etype': e['type'],
            'n_role': min(len(roles), 5),
            'sent_bucket': 'dau' if s0 < nsent*0.33 else ('giua' if s0 < nsent*0.66 else 'cuoi'),
            # --- T_entity ---
            'etypeset': ets, 'roleset': roles,
            'has_person': int('Person' in ets), 'has_org': int('Organization' in ets),
            'has_loc': int('Location' in ets),
            # --- T_anchor ---
            'gran': gr, 'method': me,
            'hull': days(hi)-days(lo),
        })
print('event xet duoc (>=2 anchor): %d | conflict %.1f%%'
      % (len(EV), 100*sum(e['y'] for e in EV)/len(EV)), flush=True)


# ==================================================== dang dieu kien
def gen_conditions(rows):
    """Sinh moi dieu kien ung vien, ghi ro TANG va DANG."""
    C = []
    vals = collections.defaultdict(collections.Counter)
    for r in rows:
        for a in ('etype', 'n_role', 'sent_bucket', 'has_person', 'has_org', 'has_loc'):
            vals[a][r[a]] += 1
        for a in ('etypeset', 'roleset', 'gran', 'method'):
            for v in set(r[a]):
                vals[a][v] += 1

    MIN = max(30, len(rows)//200)
    # EQ tren thuoc tinh don tri
    for a in ('etype', 'n_role', 'sent_bucket', 'has_person', 'has_org', 'has_loc'):
        tier = 'T_event' if a in ('etype', 'n_role', 'sent_bucket') else 'T_entity'
        for v, n in vals[a].items():
            if n >= MIN:
                C.append((tier, 'EQ', a, v, lambda r, a=a, v=v: r[a] == v))
    # HAS / ALL / CNT / MIX tren thuoc tinh tap
    for a in ('etypeset', 'roleset', 'gran', 'method'):
        tier = 'T_anchor' if a in ('gran', 'method') else 'T_entity'
        for v, n in vals[a].items():
            if n >= MIN:
                C.append((tier, 'HAS', a, v, lambda r, a=a, v=v: v in r[a]))
                C.append((tier, 'ALL', a, v,
                          lambda r, a=a, v=v: bool(r[a]) and all(x == v for x in r[a])))
        for k in (2, 3):
            C.append((tier, 'CNT', a, '>=%d' % k,
                      lambda r, a=a, k=k: len(set(r[a])) >= k))
        C.append((tier, 'MIX', a, 'khong dong nhat',
                  lambda r, a=a: len(set(r[a])) >= 2))
    # KHONG dung hull: no la THONG KE cua chinh dai luong dang kiem tra.
    #   k=2, ALL(gran=day) => a_i=b_i => hull=|d1-d2| va conflict <=> d1!=d2
    #   => hull>0 KEO THEO conflict. Tautology, khong phai pattern.
    return C


def score(rows, conds, base):
    """Danh gia mot HOP THANH (danh sach dieu kien)."""
    n = c = 0
    for r in rows:
        if all(f(r) for _, _, _, _, f in conds):
            n += 1; c += r['y']
    if n == 0:
        return None
    w = wilson_lo(c, n)
    return w, c/n, n, w/max(base, 1e-9)


def beam(rows, C, base, depth=3, width=14, min_sup=30):
    """Beam search hop thanh dieu kien."""
    cur = []
    for cd in C:
        s = score(rows, [cd], base)
        if s and s[2] >= min_sup:
            cur.append(([cd], s))
    cur.sort(key=lambda x: -x[1][0])
    best_all = list(cur[:width*3])
    frontier = cur[:width]
    for _ in range(depth-1):
        nxt = []
        for conds, s0 in frontier:
            used = {(cd[1], cd[2], cd[3]) for cd in conds}
            for cd in C:
                if (cd[1], cd[2], cd[3]) in used:
                    continue
                nc = conds+[cd]
                s = score(rows, nc, base)
                if s and s[2] >= min_sup and s[0] > s0[0]:
                    nxt.append((nc, s))
        if not nxt:
            break
        nxt.sort(key=lambda x: -x[1][0])
        seen = set(); ded = []
        for nc, s in nxt:
            k = tuple(sorted((c[1], c[2], str(c[3])) for c in nc))
            if k in seen:
                continue
            seen.add(k); ded.append((nc, s))
        frontier = ded[:width]
        best_all += ded[:width*2]
    best_all.sort(key=lambda x: -x[1][0])
    return best_all


def show(conds):
    return '  AND  '.join('%s:%s(%s=%s)' % (t, f, a, v) for t, f, a, v, _ in conds)


for K in (2, 3):
    rows = [r for r in EV if r['k'] == K]
    if len(rows) < 200:
        continue
    base = sum(r['y'] for r in rows)/len(rows)
    print('\n' + '='*100)
    print('TANG k=%d : %d event | nen conflict %.1f%%' % (K, len(rows), 100*base))
    print('='*100)
    C = gen_conditions(rows)
    print('dieu kien ung vien sinh ra: %d' % len(C), flush=True)
    res = beam(rows, C, base, depth=3, width=14)
    seen = set(); shown = 0
    for conds, (w, r, n, lift) in res:
        k = tuple(sorted((c[1], c[2], str(c[3])) for c in conds))
        if k in seen:
            continue
        seen.add(k)
        tiers = sorted({c[0] for c in conds})
        print('  lift %5.2fx | conf %5.1f%% | sup %4d | %d tang %s' %
              (lift, 100*r, n, len(tiers), ','.join(t.replace('T_', '') for t in tiers)))
        print('        %s' % show(conds))
        shown += 1
        if shown >= 12:
            break
    print('  tong hop thanh vuot nen: %d' % sum(1 for _, s in res if s[3] > 1))
