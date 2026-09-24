"""EXP39 - Model gan TIMEX v2: dac trung TU VUNG + logistic regression.

EXP37/38 that bai vi dac trung chi co VI TRI (gap, dir, type). Khong co mot dac trung
tu vung nao -> diem don quanh 0, nguong khong tach duoc.

Them:
  - gioi tu ngay truoc TIMEX ('in','on','since','during','by','from','until')
  - trigger word cua event
  - cac tu GIUA trigger va TIMEX
  - HANG khoang cach cua TIMEX nay trong so cac TIMEX cua cau  (dac trung CANH TRANH)
  - so TIMEX doi thu trong cung cau
  - co dau phay / dau ngoac chen giua khong

Logistic regression (SGD) -> co xac suat that -> nguong hoat dong dung.
"""
import json, collections, random, math, sys
sys.path.insert(0, 'tempekg_exp')
from timex_norm2 import doc_reference_chain

random.seed(20261012)
PREP = {'in', 'on', 'at', 'since', 'during', 'by', 'from', 'until', 'till', 'before',
        'after', 'between', 'of', 'around', 'about', 'through', 'throughout', 'within'}

docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        docs[d['id']] = d

norm_all = {}
by_doc = {}
for doc, d in docs.items():
    toks = d['tokens']
    tl = [(t['id'], t['mention']) for t in
          sorted(d['TIMEX'], key=lambda x: (x['sent_id'], x['offset'][0]))]
    norm_all[doc] = doc_reference_chain(tl)

    tx = {t['id']: (t['sent_id'], t['offset'][0], t['offset'][1], t['type'], t['mention'])
          for t in d['TIMEX']}
    tx_by_sent = collections.defaultdict(list)
    for tid, v in tx.items():
        tx_by_sent[v[0]].append(tid)

    ev = {}
    for e in d['events']:
        ms = [(m['sent_id'], m['offset'][0], m.get('trigger_word', '')) for m in e['mention']
              if 'sent_id' in m]
        if ms:
            m = min(ms)
            ev[e['id']] = (m[0], m[1], e['type'], m[2].lower())

    gold = set()
    for h, t in d['temporal_relations'].get('CONTAINS', []):
        if h in tx and t in ev: gold.add((t, h))
        if t in tx and h in ev: gold.add((h, t))

    rows = []
    for eid, (es, eo, et, trig) in ev.items():
        cand = [(tid, tx[tid]) for tid in tx if abs(tx[tid][0] - es) <= 3]
        # HANG khoang cach: xep cac ung vien theo do gan
        def dist(v):
            return abs(v[0]-es)*1000 + abs(v[1]-eo)
        order = sorted(cand, key=lambda x: dist(x[1]))
        rank = {tid: i for i, (tid, _) in enumerate(order)}
        n_same = len(tx_by_sent.get(es, []))

        for tid, (ts, t0, t1, tt, surf) in cand:
            gap = ts - es
            g = max(-3, min(3, gap))
            prev_tok = toks[ts][t0-1].lower() if t0 > 0 else '<S>'
            f = {
                'bias': 1,
                'gap': g,
                'dir': 'A' if gap > 0 else ('B' if gap < 0 else 'S'),
                'tt': tt,
                'et': et,
                'et_gap': '%s|%d' % (et, g),
                'rank': min(rank[tid], 4),
                'rank0': int(rank[tid] == 0),
                'ncand': min(len(cand), 6),
                'nsame': min(n_same, 4),
                # --- TU VUNG ---
                'prep': prev_tok if prev_tok in PREP else '_',
                'prep_gap': '%s|%d' % (prev_tok if prev_tok in PREP else '_', g),
                'trig': trig,
                'trig_prep': '%s>%s' % (trig, prev_tok if prev_tok in PREP else '_'),
                'surf_dig': int(surf.strip().isdigit()),
                'surf_len': min(len(surf.split()), 4),
            }
            if gap == 0:
                d_ = t0 - eo
                f['tokd'] = max(-4, min(4, d_//3))
                f['tafter'] = int(d_ > 0)
                lo, hi = (eo, t0) if d_ > 0 else (t0, eo)
                mid = [w.lower() for w in toks[es][lo:hi]]
                f['ncomma'] = min(mid.count(','), 2)
                f['nmid'] = min(len(mid), 6)
                f['midprep'] = next((w for w in mid if w in PREP), '_')
            else:
                f['tokd'] = 9; f['tafter'] = 9; f['ncomma'] = 9
                f['nmid'] = 9; f['midprep'] = '#'
            rows.append((eid, tid, f, int((eid, tid) in gold)))
    by_doc[doc] = rows

n_all = sum(len(v) for v in by_doc.values())
n_pos = sum(1 for v in by_doc.values() for r in v if r[3])
print('cap: %d | duong: %d (%.1f%%)' % (n_all, n_pos, 100*n_pos/n_all), flush=True)

dl = sorted(docs); random.shuffle(dl)
n = len(dl); TR, DV, TE = dl[:int(.7*n)], dl[int(.7*n):int(.8*n)], dl[int(.8*n):]

# ---- logistic regression, SGD + L2 ----
W = collections.defaultdict(float)
LR, L2 = 0.10, 1e-6
tr = [(x[2], x[3]) for doc in TR for x in by_doc[doc]]
print('train %d cap tren %d doc' % (len(tr), len(TR)), flush=True)
for ep in range(12):
    random.shuffle(tr)
    ll = 0.0
    for f, y in tr:
        z = sum(W[kv] for kv in f.items())
        z = max(-30, min(30, z))
        p = 1/(1+math.exp(-z))
        e = y - p
        ll += -(y*math.log(max(p, 1e-12)) + (1-y)*math.log(max(1-p, 1e-12)))
        for kv in f.items():
            W[kv] += LR*(e - L2*W[kv])
    LR *= 0.85
    if ep % 3 == 2:
        print('  ep%2d  loss %.4f  |W|=%d' % (ep+1, ll/len(tr), len(W)), flush=True)


def prob(f):
    z = max(-30, min(30, sum(W.get(kv, 0.0) for kv in f.items())))
    return 1/(1+math.exp(-z))


def t5set(am):
    s = set(); tot = 0
    for (doc, eid), txs in am.items():
        vals = [norm_all[doc].get(t) for t in txs]
        vals = [x for x in vals if x and x[0] is not None and x[2] != 'duration']
        if len(vals) < 2: continue
        tot += 1
        if max(x[0] for x in vals) > min(x[1] for x in vals): s.add((doc, eid))
    return s, tot


def evaluate(split, thetas, verbose=True):
    scored = collections.defaultdict(list); ga = collections.defaultdict(set)
    for doc in split:
        for eid, tid, f, y in by_doc[doc]:
            scored[(doc, eid)].append((prob(f), tid, y))
            if y: ga[(doc, eid)].add(tid)
    cg, tg = t5set(ga)
    if verbose:
        print('\nGOLD: multi=%d CONFLICT %d (%.1f%%)' % (tg, len(cg), 100*len(cg)/max(tg, 1)))
        print('\n%-6s %-3s | %-20s | %-22s' % ('theta', 'K', 'GAN TIMEX P/R/F1', 'T5 vs GOLD P/R/F1'))
        print('-'*70)
    best = None
    for th in thetas:
        for K in [2, 3, 5, 99]:
            pa = collections.defaultdict(set); tp = fp = fn = 0
            for key, lst in scored.items():
                keep = sorted([x for x in lst if x[0] >= th], reverse=True)[:K]
                kt = {x[1] for x in keep}
                if kt: pa[key] = kt
                for _, tid, y in lst:
                    p = int(tid in kt)
                    tp += (p and y); fp += (p and not y); fn += ((not p) and y)
            P = tp/max(tp+fp, 1); R = tp/max(tp+fn, 1); F = 2*P*R/max(P+R, 1e-9)
            cp, _ = t5set(pa)
            ov = len(cg & cp)
            tP = ov/max(len(cp), 1); tR = ov/max(len(cg), 1); tF = 2*tP*tR/max(tP+tR, 1e-9)
            if verbose:
                print('%-6.2f %-3s | %5.1f%% %5.1f%% %5.1f%% | %5.1f%% %5.1f%% %5.1f%% (n=%d)'
                      % (th, K if K < 99 else '-', 100*P, 100*R, 100*F,
                         100*tP, 100*tR, 100*tF, len(cp)))
            if best is None or F > best[0]:
                best = (F, th, K, P, R, tP, tR, tF)
    return best


print('\n' + '='*70); print('DEV (chon sieu tham so)'); print('='*70)
b = evaluate(DV, [0.20, 0.30, 0.40, 0.50, 0.60, 0.70])
print('-'*70)
print('DEV tot nhat theo F1 gan-TIMEX: theta=%.2f K=%s -> F1 %.1f%%'
      % (b[1], b[2] if b[2] < 99 else '-', 100*b[0]))

print('\n' + '='*70); print('TEST (chi cau hinh chon tu DEV)'); print('='*70)
bt = evaluate(TE, [b[1]], verbose=False)
scored = collections.defaultdict(list); ga = collections.defaultdict(set)
for doc in TE:
    for eid, tid, f, y in by_doc[doc]:
        scored[(doc, eid)].append((prob(f), tid, y))
        if y: ga[(doc, eid)].add(tid)
pa = collections.defaultdict(set); tp = fp = fn = 0
for key, lst in scored.items():
    keep = sorted([x for x in lst if x[0] >= b[1]], reverse=True)[:b[2]]
    kt = {x[1] for x in keep}
    if kt: pa[key] = kt
    for _, tid, y in lst:
        p = int(tid in kt)
        tp += (p and y); fp += (p and not y); fn += ((not p) and y)
P = tp/max(tp+fp, 1); R = tp/max(tp+fn, 1)
cg, tg = t5set(ga); cp, tpn = t5set(pa)
ov = len(cg & cp)
ne = sum(len({e['id'] for e in docs[d]['events']}) for d in TE)
print('cau hinh: theta=%.2f K=%s' % (b[1], b[2] if b[2] < 99 else '-'))
print('GAN TIMEX : P %.1f%% R %.1f%% F1 %.1f%%   (EXP37: 54.0/24.1/33.4)'
      % (100*P, 100*R, 200*P*R/max(P+R, 1e-9)))
print('event co anchor: GOLD %.1f%% | MODEL %.1f%%' % (100*len(ga)/ne, 100*len(pa)/ne))
print('T5 conflict rate: GOLD %.1f%% (%d/%d) | MODEL %.1f%% (%d/%d)'
      % (100*len(cg)/max(tg, 1), len(cg), tg, 100*len(cp)/max(tpn, 1), len(cp), tpn))
print('T5 vs GOLD: P %.1f%% R %.1f%% F1 %.1f%%   (EXP37: 6.8/10.6/8.3)'
      % (100*ov/max(len(cp), 1), 100*ov/max(len(cg), 1),
         200*(ov/max(len(cp), 1))*(ov/max(len(cg), 1)) /
         max(ov/max(len(cp), 1)+ov/max(len(cg), 1), 1e-9)))

top = sorted(W.items(), key=lambda x: -abs(x[1]))[:15]
print('\n15 dac trung manh nhat:')
for (k, v), w in top:
    print('  %-12s = %-14s %+7.3f' % (k, v, w))
