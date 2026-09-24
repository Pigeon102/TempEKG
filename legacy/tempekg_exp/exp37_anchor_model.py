"""EXP37 - MODEL GAN TIMEX: ERE chi de HOC, inference chi dung GRAPH.

Kien truc nguoi dung de xuat:
   HOC      : dung ERE CONTAINS lam nhan giam sat
   INFERENCE: chi dung event + TIMEX + vi tri van ban (KHONG dung ERE)

Day la thanh phan con thieu — hai heuristic tho deu that bai:
   1 timex/event   -> khong co T5 (can >=2 anchor)
   tat ca timex    -> 77.3% conflict (nhieu)

Bai toan: phan loai nhi phan CONTAINS(timex, event)? tren cac cap (event, timex) cung doc.
"""
import json, collections, random, math, sys
sys.path.insert(0, 'tempekg_exp')
from timex_norm2 import doc_reference_chain

random.seed(20261012)
docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        docs[d['id']] = d

norm_all = {}
pairs_by_doc = {}
for doc, d in docs.items():
    tl = [(t['id'], t['mention']) for t in
          sorted(d['TIMEX'], key=lambda x: (x['sent_id'], x['offset'][0]))]
    norm_all[doc] = doc_reference_chain(tl)
    tx = {t['id']: (t['sent_id'], t['offset'][0], t['type']) for t in d['TIMEX']}
    ev = {}
    for e in d['events']:
        ms = [(m['sent_id'], m['offset'][0]) for m in e['mention'] if 'sent_id' in m]
        if ms:
            ev[e['id']] = (min(ms)[0], min(ms)[1], e['type'])
    gold = set()
    for h, t in d['temporal_relations'].get('CONTAINS', []):
        if h in tx and t in ev:
            gold.add((t, h))
        if t in tx and h in ev:
            gold.add((h, t))
    rows = []
    for eid, (es, eo, et) in ev.items():
        for tid, (ts, to, tt) in tx.items():
            gap = ts - es
            if abs(gap) > 3:            # cua so +-3 cau
                continue
            rows.append((eid, tid, {
                'gap': max(-3, min(3, gap)),
                'same': int(gap == 0),
                'dir': 'after' if gap > 0 else ('before' if gap < 0 else 'same'),
                'tt': tt,
                'et': et,
                'et_gap': '%s|%d' % (et, max(-3, min(3, gap))),
                'tt_gap': '%s|%d' % (tt, max(-3, min(3, gap))),
                'tokdist': min(abs(to-eo)//20, 5) if gap == 0 else 9,
                'bias': 1,
            }, int((eid, tid) in gold)))
    pairs_by_doc[doc] = rows

allpairs = sum(len(v) for v in pairs_by_doc.values())
pos = sum(1 for v in pairs_by_doc.values() for r in v if r[2])
print('cap (event,timex) trong cua so +-3 cau: %d | duong: %d (%.1f%%)'
      % (allpairs, pos, 100*pos/allpairs), flush=True)

dl = sorted(docs)
random.shuffle(dl)
cut = int(0.8*len(dl))
TR, TE = dl[:cut], dl[cut:]

# perceptron nhi phan trung binh
W = collections.defaultdict(float)
Wa = collections.defaultdict(float)
c = 1


def sc(f):
    return sum(W.get((k, v), 0.0) for k, v in f.items())


rows = [(r[2], r[3]) for doc in TR for r in [(None, None, x[2], x[3]) for x in pairs_by_doc[doc]]]
rows = [(x[2], x[3]) for doc in TR for x in pairs_by_doc[doc]]
for ep in range(5):
    random.shuffle(rows)
    for f, y in rows:
        p = 1 if sc(f) > 0 else 0
        if p != y:
            s = 1 if y == 1 else -1
            for k, v in f.items():
                W[(k, v)] += s
                Wa[(k, v)] += s*c
        c += 1
for k in list(W):
    W[k] -= Wa[k]/c

# danh gia gan TIMEX
tp = fp = fn = 0
pred_anchor = collections.defaultdict(set)
gold_anchor = collections.defaultdict(set)
for doc in TE:
    for eid, tid, f, y in pairs_by_doc[doc]:
        p = 1 if sc(f) > 0 else 0
        if p:
            pred_anchor[(doc, eid)].add(tid)
        if y:
            gold_anchor[(doc, eid)].add(tid)
        tp += (p and y); fp += (p and not y); fn += ((not p) and y)
P = tp/max(tp+fp, 1); R = tp/max(tp+fn, 1)
print()
print('=== MODEL GAN TIMEX (tren %d doc test) ===' % len(TE))
print('  precision %.1f%% | recall %.1f%% | F1 %.1f%%' % (100*P, 100*R, 200*P*R/max(P+R, 1e-9)))

ne = sum(len({e['id'] for e in docs[d]['events']}) for d in TE)
print('  event co anchor: GOLD %.1f%% | MODEL %.1f%%'
      % (100*len(gold_anchor)/ne, 100*len(pred_anchor)/ne))


def t5(am, nm):
    v = collections.Counter()
    s = set()
    for (doc, eid), txs in am.items():
        vals = [norm_all[doc].get(t) for t in txs]
        vals = [x for x in vals if x and x[0] is not None and x[2] != 'duration']
        if len(vals) < 2:
            continue
        lo = max(x[0] for x in vals); hi = min(x[1] for x in vals)
        if lo > hi:
            v['CONFLICT'] += 1; s.add((doc, eid))
        else:
            v['OK'] += 1
    tot = v['CONFLICT']+v['OK']
    print('  %-22s multi=%5d | CONFLICT %4d (%.1f%%)'
          % (nm, tot, v['CONFLICT'], 100*v['CONFLICT']/max(tot, 1)))
    return s


print()
print('T5 tren tap test:')
cg = t5(gold_anchor, 'GOLD (ERE)')
cp = t5(pred_anchor, 'MODEL (khong ERE)')
if cg:
    print()
    print('  conflict GOLD %d | MODEL %d | GIAO %d' % (len(cg), len(cp), len(cg & cp)))
    print('  -> precision cua MODEL so voi GOLD: %.1f%%' % (100*len(cg & cp)/max(len(cp), 1)))
    print('  -> recall    cua MODEL so voi GOLD: %.1f%%' % (100*len(cg & cp)/max(len(cg), 1)))
