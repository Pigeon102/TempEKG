"""Vet MOT vi du that di het duong: text -> fact -> do thi -> vong lap -> phan quyet.

Chon tu WD50K that ba nhom minh hoa ba lop pos / neg / unknown.
"""
import sys, collections, json
sys.path.insert(0, 'tempekg_exp/patecon')
from Interval_Relations import FuzzyTime, comp_time, disjoint

PROP = {'P26': 'vo/chong', 'P54': 'thi dau cho doi', 'P39': 'giu chuc vu',
        'P569': 'ngay sinh', 'P570': 'ngay mat', 'P108': 'lam viec cho'}

facts = collections.defaultdict(list)
for line in open('tempekg_exp/patecon_data/WD50K_official.tsv', encoding='utf-8'):
    p = line.rstrip('\n').split('\t')
    if len(p) < 5:
        continue
    s = p[3].strip() or '-1'
    e = p[4].strip() or '-1'
    s = int(s) if s not in ('', '-1', 'None') else -1
    e = int(e) if e not in ('', '-1', 'None') else -1
    if s != -1 or e != -1:
        facts[(p[0], p[1])].append((p[2], s, e))


def classify(lst, verbose=False):
    consistent, negative = True, False
    trace = []
    for k in range(len(lst)):
        stop = False
        for l in range(k+1, len(lst)):
            a, b = lst[k], lst[l]
            r = disjoint(a[1], a[2], b[1], b[2])
            trace.append((a, b, r))
            if r == -1:
                consistent, negative, stop = False, True, True
                break
            if r == 0:
                consistent = False
        if stop:
            break
    cls = 'positive' if consistent else ('negative' if negative else 'unknown')
    return cls, trace


buckets = {'negative': [], 'unknown': [], 'positive': []}
for k, lst in facts.items():
    if len(lst) < 2 or len(lst) > 3:
        continue
    c, _ = classify(lst)
    if len(buckets[c]) < 3:
        buckets[c].append((k, lst))


def show(key, lst):
    ent, rel = key
    cls, trace = classify(lst)
    print('='*74)
    print('ENTITY %s   RELATION %s (%s)   -> lop: %s'
          % (ent, rel, PROP.get(rel, '?'), cls.upper()))
    print('='*74)
    print('\n[1] FACT tho trong TSV')
    for t, s, e in lst:
        print('    %s\t%s\t%s\t%-10s %-10s' % (ent, rel, t, s if s != -1 else '(trong)',
                                               e if e != -1 else '(trong)'))
    print('\n[2] DO THI reified cua PaTeCon')
    print('    eVertex(%s)' % ent)
    for i, (t, s, e) in enumerate(lst):
        print('      +-- sVertex_%d : %s --> eVertex(%s)   [start=%s end=%s]'
              % (i, rel, t, s, e))
    print('\n[3] FuzzyTime phan ra (nho: Day==1 -> "##"; them Month==1 -> "##")')
    for i, (t, s, e) in enumerate(lst):
        print('      sVertex_%d  start %-10s -> %-24s  prec=%s'
              % (i, s, FuzzyTime(s), FuzzyTime(s).get_precision()))
        print('      %s          end   %-10s -> %-24s  prec=%s'
              % (' '*len(str(i)), e, FuzzyTime(e), FuzzyTime(e).get_precision()))
    print('\n[4] VONG LAP moi cap -> disjoint()')
    for a, b, r in trace:
        t1, t2 = FuzzyTime(a[1]), FuzzyTime(a[2])
        t3, t4 = FuzzyTime(b[1]), FuzzyTime(b[2])
        c23 = comp_time(t2, t3)
        c41 = comp_time(t4, t1)
        print('    cap (%s , %s)' % (a[0], b[0]))
        print('      comp_time(end1=%s, start2=%s) = %-4s' % (t2, t3, c23))
        print('      comp_time(end2=%s, start1=%s) = %-4s' % (t4, t1, c41))
        verdict = {1: '+1  ROI NHAU (thoa)', 0: ' 0  KHONG QUYET DUOC',
                   -1: '-1  CHONG LAN (vi pham)'}[r]
        print('      -> disjoint = %s' % verdict)
        if r == -1:
            print('         vi CA HAI deu "gt": end1>start2 VA end2>start1')
        elif r == 0:
            print('         vi co "unk" -> khong the ket luan')
    print('\n[5] PHAN QUYET')
    if cls == 'positive':
        print('    consistent=True  -> tu so +1, mau so +1')
    elif cls == 'negative':
        print('    negative=True    -> CHI mau so +1  (tu so khong tang)')
    else:
        print('    khong -1 nao, co it nhat mot 0')
        print('    -> KHONG vao tu so, KHONG vao mau so.  BI LOAI HOAN TOAN.')
    print()


for c in ('negative', 'unknown', 'positive'):
    if buckets[c]:
        k, lst = buckets[c][0]
        show(k, lst)
