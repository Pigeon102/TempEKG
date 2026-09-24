"""EXP19 - Do DAY DU cac loai temporal conflict tren du lieu cua PaTeCon.

Truoc gio chi do ORDERING + MUTUAL EXCLUSION. De tai nham ca GRANULARITY va cac loai khac.
Do het de co taxonomy co so lieu.

  T1 REPRESENTATION : start > end                       (PaTeCon co do, loai truoc khi mine)
  T2 MUTUAL EXCL    : mot (subject,property) chuc nang co NHIEU gia tri khac nhau
  T3 ORDERING       : vi pham thu tu (sinh truoc chet...)
  T4 DISJOINTNESS   : hai khoang chong nhau o property le ra phai roi nhau
  T5 GRANULARITY    : do chinh xac thoi gian KHONG NHAT QUAN cho cung mot su viec
        5a sai lech giua object literal va start/end
        5b hien tuong YYYY0101 / YYYY0000 (nam-only bi ghi thanh ngay 1/1)
        5c cung (subject,property) nhung cac gia tri o do chinh xac KHAC nhau
"""
import re, collections, sys

PAT = re.compile(r'pinstConf\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]*)",\s*"([^"]*)",')
FUNCTIONAL = {'P569', 'P570'}          # ngay sinh / ngay mat: chi duoc co 1
DISJOINT_P = {'P54', 'P26', 'P108', 'P286'}   # khong the giu 2 cung luc


def prec(v):
    """do chinh xac cua mot gia tri ngay: day / month / year / unknown"""
    v = (v or '').strip()
    if not v.isdigit():
        return 'nonnum'
    if len(v) == 8:
        return 'day'
    if len(v) == 6:
        return 'month'
    if len(v) == 4:
        return 'year'
    return 'other'


def load(path):
    out = []
    for line in open(path, encoding='utf-8', errors='ignore'):
        m = PAT.search(line)
        if m:
            out.append(m.groups())
    return out


def ival(s, e):
    try:
        return int(s[:6]), int(e[:6])
    except Exception:
        return None, None


for path, name in ((sys.argv[1], sys.argv[2]),):
    facts = load(path)
    n = len(facts)
    print('=' * 70)
    print('%s : %d fact' % (name, n))
    print()

    # ---------- T1 representation ----------
    t1 = 0
    for s, p, o, st, en in facts:
        a, b = ival(st, en)
        if a is not None and b is not None and a > b:
            t1 += 1

    # ---------- T2 mutual exclusion ----------
    sp = collections.defaultdict(set)
    for s, p, o, st, en in facts:
        if p in FUNCTIONAL:
            sp[(s, p)].add(o)
    t2 = sum(1 for k, v in sp.items() if len(v) > 1)
    t2_tot = len(sp)

    # ---------- T3 ordering ----------
    ent = collections.defaultdict(dict)
    for s, p, o, st, en in facts:
        a, b = ival(st, en)
        if a is None:
            continue
        ent[s].setdefault(p, []).append((a, b, o))
    t3 = t3_tot = 0
    for s, props in ent.items():
        if 'P569' in props and 'P570' in props:
            for (ba, bb, _) in props['P569']:
                for (da, db, _) in props['P570']:
                    t3_tot += 1
                    if not (bb <= da):
                        t3 += 1

    # ---------- T4 disjointness ----------
    t4 = t4_tot = 0
    for s, props in ent.items():
        for p in DISJOINT_P:
            vs = props.get(p, [])
            for i in range(len(vs)):
                for j in range(i + 1, len(vs)):
                    a1, b1, o1 = vs[i]
                    a2, b2, o2 = vs[j]
                    if o1 == o2:
                        continue
                    t4_tot += 1
                    if a1 <= b2 and a2 <= b1:      # chong nhau
                        t4 += 1

    # ---------- T5 granularity ----------
    prec_o = collections.Counter()
    t5a = t5b = 0
    for s, p, o, st, en in facts:
        po = prec(o)
        prec_o[po] += 1
        ps, pe = prec(st), prec(en)
        # 5a: object min hon start/end la BINH THUONG; nguoc lai la BAT THUONG
        rank = {'year': 1, 'month': 2, 'day': 3}
        if po in rank and ps in rank and rank[po] < rank[ps]:
            t5a += 1
        # 5b: hien tuong 1 thang 1 / ngay 00
        if po == 'day' and (o.endswith('0101') or o.endswith('0000') or o[4:6] == '00'):
            t5b += 1
    # 5c: cung (subject,property) nhung do chinh xac khac nhau
    spp = collections.defaultdict(set)
    for s, p, o, st, en in facts:
        spp[(s, p)].add(prec(o))
    t5c = sum(1 for v in spp.values() if len(v) > 1)

    print('%-42s %8s %10s' % ('LOAI TEMPORAL CONFLICT', 'so luong', 'ti le'))
    print('-' * 64)
    print('%-42s %8d %9.2f%%' % ('T1 REPRESENTATION (start > end)', t1, 100*t1/n))
    print('%-42s %8d %9.2f%%' % ('T2 MUTUAL EXCLUSION (nhieu gia tri)', t2,
                                 100*t2/max(t2_tot, 1)))
    print('     (tren %d cap (subject,property) chuc nang)' % t2_tot)
    print('%-42s %8d %9.2f%%' % ('T3 ORDERING (sinh truoc chet bi vi pham)', t3,
                                 100*t3/max(t3_tot, 1)))
    print('     (tren %d cap sinh-chet)' % t3_tot)
    print('%-42s %8d %9.2f%%' % ('T4 DISJOINTNESS (chong khoang)', t4, 100*t4/max(t4_tot, 1)))
    print('     (tren %d cap cung property)' % t4_tot)
    print()
    print('%-42s %8d %9.2f%%' % ('T5a GRANULARITY object tho hon start', t5a, 100*t5a/n))
    print('%-42s %8d %9.2f%%' % ('T5b GRANULARITY nghi ngo (YYYY0101/00)', t5b, 100*t5b/n))
    print('%-42s %8d %9.2f%%' % ('T5c GRANULARITY lech trong cung (s,p)', t5c,
                                 100*t5c/max(len(spp), 1)))
    print()
    print('  phan bo do chinh xac cua gia tri ngay:',
          {k: '%.1f%%' % (100*v/n) for k, v in prec_o.most_common()})
