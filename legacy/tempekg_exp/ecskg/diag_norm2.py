"""Do lai cho dung: tach SYMBOLIC TIME ra khoi "that bai chuan hoa".

SEM phan biet ro:
   thoi gian GIA TRI  -> co moc, quy ra (lo,hi)
   thoi gian KY HIEU  -> chi biet thu tu ('later', 'then'), KHONG co moc

'later' khong quy ra ngay duoc KHONG PHAI loi normaliser. Do la symbolic time.
DURATION ('three days') cung vay: no la do dai, khong phai vi tri.
"""
import json, collections, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from timex_norm2 import normalize
from ecskg.extract import find_timex, REL, DUR_UNIT

random.seed(20261012)
docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line); docs[d['id']] = d
ids = sorted(docs); random.shuffle(ids)
TE = ids[int(0.8*len(ids)):]

cat = collections.Counter()
ok = collections.Counter()
fail_abs = collections.Counter()

for i in TE:
    d = docs[i]
    gold_spans = {(t['sent_id'], t['offset'][0], t['offset'][1]) for t in d['TIMEX']}
    ry = rd = None
    for s, toks in enumerate(d['tokens']):
        for a, b, surf, tt in find_timex(toks):
            low = surf.lower()
            if tt == 'DURATION':
                c = 'DURATION (do dai)'
            elif tt == 'SET':
                c = 'SET (lap lai)'
            elif low in REL:
                c = 'SYMBOLIC (chi thu tu)'
            else:
                c = 'ABSOLUTE (can co moc)'
            cat[c] += 1
            r = normalize(surf, ref_year=ry, ref_date=rd)
            good = bool(r and r[0] is not None)
            ok[c] += good
            if good and r[2] in ('day', 'month', 'year'):
                ry = r[0]//10000
                if r[2] == 'day': rd = r[0]
            if c.startswith('ABSOLUTE') and not good:
                fail_abs[(low[:26], (s, a, b) in gold_spans)] += 1

print('='*70)
print('PHAN LOAI span ta tim duoc theo BAN CHAT (SEM)')
print('='*70)
tot = sum(cat.values())
for c in sorted(cat, key=lambda x: -cat[x]):
    print('  %-24s %5d (%4.1f%%) | quy ra moc duoc %5d (%.1f%%)'
          % (c, cat[c], 100*cat[c]/tot, ok[c], 100*ok[c]/max(cat[c], 1)))
print('  %-24s %5d          | %5d (%.1f%%)'
      % ('TONG', tot, sum(ok.values()), 100*sum(ok.values())/tot))
print()
a_n = cat['ABSOLUTE (can co moc)']; a_ok = ok['ABSOLUTE (can co moc)']
sym = cat['SYMBOLIC (chi thu tu)'] + cat['DURATION (do dai)'] + cat['SET (lap lai)']
print('  -> tren rieng nhom CAN co moc: %d/%d = %.1f%%' % (a_ok, a_n, 100*a_ok/max(a_n, 1)))
print('  -> nhom KHONG the co moc (symbolic/duration/set): %d span = %.1f%% tong'
      % (sym, 100*sym/tot))
print()
print('20 span ABSOLUTE that su hong (T = vang cung annotate span nay):')
for (s, m), c in fail_abs.most_common(20):
    print('    %4d  %-28r  vang-co-span=%s' % (c, s, 'T' if m else 'F'))
