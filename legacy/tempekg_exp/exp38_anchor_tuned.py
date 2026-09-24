"""EXP38 - Sua model gan TIMEX: NGUONG CONFIDENCE + TOP-K anchor.

EXP37 cho T5 conflict 72.5% (gold 16.1%) -> dau hieu GAN TRAN.
Sua hai cho:
  1. cat o nguong tau (theta) thay vi 0
  2. moi event giu toi da K anchor diem cao nhat
Quet (theta, K) va do T5 so voi gold.
"""
import json, collections, random, sys
sys.path.insert(0, 'tempekg_exp')
from timex_norm2 import doc_reference_chain

random.seed(20261012)
docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        docs[d['id']] = d

norm_all = {}
by_doc = {}
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
        if h in tx and t in ev: gold.add((t, h))
        if t in tx and h in ev: gold.add((h, t))
    rows = []
    for eid, (es, eo, et) in ev.items():
        for tid, (ts, to, tt) in tx.items():
            gap = ts - es
            if abs(gap) > 3: continue
            g = max(-3, min(3, gap))
            rows.append((eid, tid, {
                'gap': g, 'same': int(gap == 0),
                'dir': 'after' if gap > 0 else ('before' if gap < 0 else 'same'),
                'tt': tt, 'et': et,
                'et_gap': '%s|%d' % (et, g), 'tt_gap': '%s|%d' % (tt, g),
                'tokdist': min(abs(to-eo)//20, 5) if gap == 0 else 9,
                'bias': 1,
            }, int((eid, tid) in gold)))
    by_doc[doc] = rows

n_pos = sum(1 for v in by_doc.values() for r in v if r[3])
n_all = sum(len(v) for v in by_doc.values())
print('cap trong cua so +-3 cau: %d | duong: %d (%.1f%%)' % (n_all, n_pos, 100*n_pos/n_all), flush=True)

dl = sorted(docs); random.shuffle(dl)
cut = int(0.8*len(dl)); TR, TE = dl[:cut], dl[cut:]

W = collections.defaultdict(float); Wa = collections.defaultdict(float); c = 1
def sc(f): return sum(W.get(kv, 0.0) for kv in f.items())

rows = [(x[2], x[3]) for doc in TR for x in by_doc[doc]]
for ep in range(5):
    random.shuffle(rows)
    for f, y in rows:
        p = 1 if sc(f) > 0 else 0
        if p != y:
            s = 1 if y else -1
            for kv in f.items(): W[kv] += s; Wa[kv] += s*c
        c += 1
for k in list(W): W[k] -= Wa[k]/c

# diem cho moi cap trong tap test
scored = collections.defaultdict(list)   # (doc,eid) -> [(score,tid,y)]
gold_anchor = collections.defaultdict(set)
for doc in TE:
    for eid, tid, f, y in by_doc[doc]:
        scored[(doc, eid)].append((sc(f), tid, y))
        if y: gold_anchor[(doc, eid)].add(tid)


def t5set(am):
    s = set(); tot = 0
    for (doc, eid), txs in am.items():
        vals = [norm_all[doc].get(t) for t in txs]
        vals = [x for x in vals if x and x[0] is not None and x[2] != 'duration']
        if len(vals) < 2: continue
        tot += 1
        if max(x[0] for x in vals) > min(x[1] for x in vals): s.add((doc, eid))
    return s, tot


cg, tg = t5set(gold_anchor)
print('\nGOLD (ERE): multi=%d | CONFLICT %d (%.1f%%)' % (tg, len(cg), 100*len(cg)/max(tg, 1)))
print('\n%-6s %-3s | %-18s | %-24s' % ('theta', 'K', 'GAN TIMEX P/R/F1', 'T5 vs GOLD  P/R/F1'))
print('-'*70)

best = None
for theta in [0, 1, 2, 4, 8, 16, 32]:
    for K in [2, 3, 5, 99]:
        pa = collections.defaultdict(set)
        tp = fp = fn = 0
        for key, lst in scored.items():
            keep = sorted([x for x in lst if x[0] > theta], reverse=True)[:K]
            kt = {x[1] for x in keep}
            if kt: pa[key] = kt
            for s_, tid, y in lst:
                p = int(tid in kt)
                tp += (p and y); fp += (p and not y); fn += ((not p) and y)
        P = tp/max(tp+fp, 1); R = tp/max(tp+fn, 1); F = 2*P*R/max(P+R, 1e-9)
        cp, tpn = t5set(pa)
        ov = len(cg & cp)
        tP = ov/max(len(cp), 1); tR = ov/max(len(cg), 1); tF = 2*tP*tR/max(tP+tR, 1e-9)
        print('%-6d %-3s | %5.1f%% %5.1f%% %5.1f%% | %5.1f%% %5.1f%% %5.1f%%  (n=%d)'
              % (theta, K if K < 99 else '-', 100*P, 100*R, 100*F, 100*tP, 100*tR, 100*tF, len(cp)))
        if best is None or tF > best[0]: best = (tF, theta, K, tP, tR, F)

print('-'*70)
print('TOT NHAT theo T5-F1: theta=%d K=%s | T5 P %.1f%% R %.1f%% F1 %.1f%% | gan-TIMEX F1 %.1f%%'
      % (best[1], best[2] if best[2] < 99 else '-', 100*best[3], 100*best[4], 100*best[0], 100*best[5]))
