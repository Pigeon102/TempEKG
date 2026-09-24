"""Tach nguyen nhan: normaliser yeu, hay SPAN dua vao sai?

91.3% do tren span VANG. 65.6% do tren span TA TU TIM.
Chay CUNG normaliser tren ca hai loai span, tren CUNG tap document.
"""
import json, collections, random, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from timex_norm2 import normalize, doc_reference_chain
from ecskg.extract import find_timex

random.seed(20261012)
docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line); docs[d['id']] = d
ids = sorted(docs); random.shuffle(ids)
TE = ids[int(0.8*len(ids)):]

gold_ok = gold_n = 0
our_ok = our_n = 0
matched_ok = matched_n = 0        # span TA tim DUNG khop vang
wrong_ok = wrong_n = 0            # span TA tim SAI bien
bysrc = collections.Counter()

for i in TE:
    d = docs[i]
    gold_spans = {(t['sent_id'], t['offset'][0], t['offset'][1]): t['mention']
                  for t in d['TIMEX']}

    # --- normaliser tren span VANG (co chuoi tham chieu nhu cu) ---
    tl = [(t['id'], t['mention']) for t in
          sorted(d['TIMEX'], key=lambda x: (x['sent_id'], x['offset'][0]))]
    nm = doc_reference_chain(tl)
    for t in d['TIMEX']:
        gold_n += 1
        r = nm.get(t['id'])
        if r and r[0] is not None:
            gold_ok += 1

    # --- normaliser tren span TA TU TIM ---
    ry = rd = None
    for s, toks in enumerate(d['tokens']):
        for a, b, surf, tt in find_timex(toks):
            our_n += 1
            r = normalize(surf, ref_year=ry, ref_date=rd)
            ok = bool(r and r[0] is not None)
            our_ok += ok
            if ok and r[2] in ('day', 'month', 'year'):
                ry = r[0]//10000
                if r[2] == 'day': rd = r[0]
            if (s, a, b) in gold_spans:
                matched_n += 1; matched_ok += ok
            else:
                wrong_n += 1; wrong_ok += ok
                if not ok:
                    bysrc[surf.lower()[:28]] += 1

print('='*66)
print('CUNG normaliser, KHAC nguon span (%d document test)' % len(TE))
print('='*66)
print('  span VANG           : %5d span | chuan hoa %5d (%.1f%%)'
      % (gold_n, gold_ok, 100*gold_ok/max(gold_n, 1)))
print('  span TA TU TIM      : %5d span | chuan hoa %5d (%.1f%%)'
      % (our_n, our_ok, 100*our_ok/max(our_n, 1)))
print()
print('  ta tim DUNG bien    : %5d span | chuan hoa %5d (%.1f%%)'
      % (matched_n, matched_ok, 100*matched_ok/max(matched_n, 1)))
print('  ta tim SAI bien     : %5d span | chuan hoa %5d (%.1f%%)'
      % (wrong_n, wrong_ok, 100*wrong_ok/max(wrong_n, 1)))
print()
print('  -> chenh giua "dung bien" va "sai bien": %.1f diem'
      % (100*matched_ok/max(matched_n, 1) - 100*wrong_ok/max(wrong_n, 1)))
print()
print('20 surface ta tim SAI ma normaliser cung chiu:')
for s, c in bysrc.most_common(20):
    print('    %4d  %r' % (c, s))
