"""Mining tren do thi dung tu TEXT THO, roi KIEM CHUNG bang nhan vang.

Vong khep kin theo yeu cau:
   text tho -> do thi -> luu -> MINING -> kiem chung tren TIMEX vang

Mining KHONG dung nhan nao. Nhan vang chi xuat hien o phan cuoi.

Ba loai xung dot do duoc tren do thi nay:
   T1 bieu dien : interval co lo > hi
   T3 thu tu    : canh BEFORE nhung moc thoi gian nguoc lai
   T5 hat do    : mot su kien co >=2 anchor giao rong
"""
import json, collections, sys, os, time, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecskg.build import Graph
from ecskg.schema import Event, TimeX

t0 = time.time()
g = Graph.load('tempekg_exp/ecskg/graph_test.jsonl')
print('tai do thi: %d node, %d canh (%.1fs)' % (len(g.nodes), len(g.edges), time.time()-t0),
      flush=True)

evs = {n.nid: n for n in g.of_type(Event)}
txs = {n.nid: n for n in g.of_type(TimeX)}

# interval cua su kien: giao cac anchor giai duoc, giu ca cac anchor de xet T5
anchors = collections.defaultdict(list)
for e in g.edges.values():
    if e.label == 'hasTime' and e.head in evs and e.tail in txs:
        b = txs[e.tail].bounds()
        if b:
            anchors[e.head].append((b, e.conf, e.tail))

def interval(eid):
    a = anchors.get(eid)
    if not a: return None
    lo = max(x[0][0] for x in a); hi = min(x[0][1] for x in a)
    return (lo, hi)

print('su kien co interval: %d / %d' % (sum(1 for k in evs if interval(k)), len(evs)))

# =============================================================== MINING
print('\n' + '='*66); print('MINING (khong dung nhan)'); print('='*66)

# cap su kien chia chung mot actor -> chu ky (etype1, role1, etype2, role2)
actor_ev = collections.defaultdict(list)
for e in g.edges.values():
    if e.label == 'hasActor' and e.head in evs:
        actor_ev[e.tail].append((e.head, e.role))

sig = collections.defaultdict(lambda: [0, 0, 0])   # roi nhau, tong, so doc
sig_docs = collections.defaultdict(set)
npair = 0
for a, lst in actor_ev.items():
    lst = list(dict.fromkeys(lst))
    for i in range(len(lst)):
        for j in range(i+1, len(lst)):
            e1, r1 = lst[i]; e2, r2 = lst[j]
            if e1 == e2: continue
            iv1, iv2 = interval(e1), interval(e2)
            if not iv1 or not iv2: continue
            if iv1[0] > iv1[1] or iv2[0] > iv2[1]: continue
            npair += 1
            k = (evs[e1].etype, r1, evs[e2].etype, r2)
            sig[k][1] += 1
            sig_docs[k].add(evs[e1].doc_id)
            if iv1[1] < iv2[0] or iv2[1] < iv1[0]:
                sig[k][0] += 1

def wilson_lo(k, n, z=1.96):
    if n == 0: return 0.0
    p = k/n
    d = 1+z*z/n
    c = p+z*z/(2*n)
    m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return max(0.0, (c-m)/d)

MINSUP, MINDOC = 5, 3
cons = []
for k, (d, n, _) in sig.items():
    if n >= MINSUP and len(sig_docs[k]) >= MINDOC:
        rate = 1 - d/n                      # ti le CHONG LAN
        cons.append((wilson_lo(n-d, n), rate, n, len(sig_docs[k]), k))
cons.sort(reverse=True)
print('cap co interval: %d | chu ky: %d | dat sup>=%d & doc>=%d: %d'
      % (npair, len(sig), MINSUP, MINDOC, len(cons)))
print('\n10 rang buoc CHONG LAN manh nhat (Wilson lower bound):')
for w, r, n, nd, k in cons[:10]:
    print('  %.3f  chong lan %5.1f%%  sup %3d  doc %2d  %s' % (w, 100*r, n, nd, k))

# =============================================================== XUNG DOT
print('\n' + '='*66); print('PHAT HIEN XUNG DOT'); print('='*66)
C = collections.defaultdict(set)

# T1: interval nguoc
for eid in evs:
    a = anchors.get(eid)
    if not a or len(a) < 2: continue
    lo = max(x[0][0] for x in a); hi = min(x[0][1] for x in a)
    if lo > hi:
        C['T5_granularity'].add(eid)

# T3: canh BEFORE nhung thoi gian nguoc
for e in g.edges.values():
    if e.label not in ('BEFORE', 'AFTER'): continue
    a, b = (e.head, e.tail) if e.label == 'BEFORE' else (e.tail, e.head)
    ia, ib = interval(a), interval(b)
    if ia and ib and ia[0] > ib[1]:
        C['T3_ordering'].add((a, b))

# T4: rang buoc chong lan bi vi pham
top = {k for w, r, n, nd, k in cons if r >= 0.95}
for a, lst in actor_ev.items():
    lst = list(dict.fromkeys(lst))
    for i in range(len(lst)):
        for j in range(i+1, len(lst)):
            e1, r1 = lst[i]; e2, r2 = lst[j]
            if e1 == e2: continue
            if (evs[e1].etype, r1, evs[e2].etype, r2) not in top: continue
            iv1, iv2 = interval(e1), interval(e2)
            if iv1 and iv2 and (iv1[1] < iv2[0] or iv2[1] < iv1[0]):
                C['T4_disjoint'].add((e1, e2))

for k in sorted(C):
    print('  %-18s %d' % (k, len(C[k])))

# =============================================================== KIEM CHUNG
print('\n' + '='*66)
print('KIEM CHUNG tren TIMEX vang (lan duy nhat dung nhan)')
print('='*66)
docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line); docs[d['id']] = d

# anh xa node su kien cua ta -> su kien vang theo offset trigger
gold_iv = {}
gold_multi = {}
for did in {n.doc_id for n in evs.values()}:
    d = docs.get(did)
    if not d: continue
    tx = {}
    for t in d['TIMEX']:
        tx[t['id']] = (t['sent_id'], t['offset'][0])
    ev_pos = {}
    for e in d['events']:
        for m in e['mention']:
            if 'sent_id' in m:
                ev_pos.setdefault(e['id'], (m['sent_id'], m['offset'][0]))
    anc = collections.defaultdict(list)
    for h, t in d['temporal_relations'].get('CONTAINS', []):
        if h in tx and t in ev_pos: anc[t].append(h)
        if t in tx and h in ev_pos: anc[h].append(t)
    for eid, tl in anc.items():
        gold_multi[(did, ev_pos[eid])] = len(tl)

hit = tot = 0
for eid in C['T5_granularity']:
    n = evs[eid]
    k = (n.doc_id, (n.sent_id, n.offset[0]))
    if k in gold_multi:
        tot += 1
        if gold_multi[k] >= 2: hit += 1
print('\n[T5] su kien ta gan co xung dot hat do: %d' % len(C['T5_granularity']))
print('     trong so do khop vi tri su kien vang: %d' % tot)
print('     va su kien vang do that su co >=2 anchor: %d (%.1f%%)'
      % (hit, 100*hit/max(tot, 1)))
base = sum(1 for v in gold_multi.values() if v >= 2)/max(len(gold_multi), 1)
print('     ti le nen (moi su kien vang co anchor): %.1f%%' % (100*base))
print('     lift: %.2fx' % ((hit/max(tot, 1))/max(base, 1e-9)))

# T3 kiem chung: cap BEFORE cua ta co bi vang xac nhan nguoc khong
gold_before = collections.defaultdict(set)
for did in {n.doc_id for n in evs.values()}:
    d = docs.get(did)
    if not d: continue
    ev_pos = {}
    for e in d['events']:
        for m in e['mention']:
            if 'sent_id' in m: ev_pos.setdefault(e['id'], (m['sent_id'], m['offset'][0]))
    for h, t in d['temporal_relations'].get('BEFORE', []):
        if h in ev_pos and t in ev_pos:
            gold_before[did].add((ev_pos[h], ev_pos[t]))
ok = bad = unk = 0
for a, b in C['T3_ordering']:
    na, nb = evs[a], evs[b]
    if na.doc_id != nb.doc_id: continue
    pa, pb = (na.sent_id, na.offset[0]), (nb.sent_id, nb.offset[0])
    gb = gold_before[na.doc_id]
    if (pa, pb) in gb: bad += 1        # vang noi a truoc b -> ta bao xung dot la SAI
    elif (pb, pa) in gb: ok += 1       # vang noi b truoc a -> xung dot la DUNG
    else: unk += 1
print('\n[T3] cap ta bao xung dot thu tu: %d' % len(C['T3_ordering']))
print('     vang xac nhan NGUOC (ta dung): %d' % ok)
print('     vang noi cung chieu (ta sai) : %d' % bad)
print('     vang khong noi gi            : %d' % unk)
if ok+bad:
    print('     precision tren phan quyet dinh duoc: %.1f%%' % (100*ok/(ok+bad)))
print('\ntong %.1fs' % (time.time()-t0))
