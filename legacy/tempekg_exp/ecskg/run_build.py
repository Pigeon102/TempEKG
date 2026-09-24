"""Dung do thi event-centric TU TEXT THO tren MAVEN, roi KIEM CHUNG bang nhan vang.

Quy trinh dung yeu cau:
   text tho -> trich xuat -> do thi -> luu tru -> (mining) -> kiem chung tren TIMEX

Nhan vang (TIMEX / event / ERE) KHONG bao gio vao do thi.
Chung chi xuat hien o buoc KIEM CHUNG cuoi cung.
"""
import json, collections, random, sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecskg.extract import TriggerLexicon, extract_doc, find_timex
from ecskg.build import build, Graph

random.seed(20261012)
t0 = time.time()

docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        docs[d['id']] = d
print('nap %d document (%.1fs)' % (len(docs), time.time()-t0), flush=True)

ids = sorted(docs); random.shuffle(ids)
cut = int(0.8*len(ids))
TR, TE = ids[:cut], ids[cut:]

# ---------- HOC tu dien trigger tren TRAIN (dung nhan — hop le) ----------
tok_tr, trig_tr = [], []
for d in (docs[i] for i in TR):
    tok_tr.append(d['tokens'])
    tg = {}
    for e in d['events']:
        for m in e['mention']:
            if 'sent_id' in m:
                tg[(m['sent_id'], m['offset'][0])] = e['type']
    trig_tr.append(tg)
lex = TriggerLexicon().fit(tok_tr, trig_tr)
print('tu dien trigger hoc duoc: %d tu (vd: %s)'
      % (len(lex.lex), ', '.join(list(lex.lex)[:8])), flush=True)

# ---------- TRICH XUAT tren TEST: CHI token tho ----------
ex_by_doc = {}
sents_by_doc = {}
for i in TE:
    sents = docs[i]['tokens']              # <-- chi token, khong nhan
    sents_by_doc[i] = sents
    ex_by_doc[i] = extract_doc(i, sents, lex)
print('trich xuat %d document (%.1fs)' % (len(TE), time.time()-t0), flush=True)

g = build(ex_by_doc, sents_by_doc)
nc, ec = g.stats()
print('\n' + '='*66)
print('DO THI DUNG TU TEXT THO')
print('='*66)
print('node:', dict(nc))
print('canh:', dict(ec))
print('tong: %d node, %d canh (%.1fs)' % (len(g.nodes), len(g.edges), time.time()-t0))

path = 'tempekg_exp/ecskg/graph_test.jsonl'
g.save(path)
sz = os.path.getsize(path)/1024/1024
t1 = time.time(); g2 = Graph.load(path); tl = time.time()-t1
print('luu %s (%.1f MB) | tai lai %.1fs, %d node' % (path, sz, tl, len(g2.nodes)))

# =====================================================================
#  KIEM CHUNG — day la lan DUY NHAT dung nhan vang
# =====================================================================
print('\n' + '='*66)
print('KIEM CHUNG tren nhan vang (khong dung khi dung do thi)')
print('='*66)

# --- 1. span TIMEX ---
tp = fp = fn = 0
tp_part = 0
for i in TE:
    gold = {(t['sent_id'], t['offset'][0], t['offset'][1]) for t in docs[i]['TIMEX']}
    gold_tok = collections.defaultdict(set)
    for s, a, b in gold:
        gold_tok[s] |= set(range(a, b))
    pred = {(s, a, b) for s, a, b, _, _ in ex_by_doc[i].times}
    tp += len(pred & gold)
    fp += len(pred - gold)
    fn += len(gold - pred)
    for s, a, b in pred:
        if set(range(a, b)) & gold_tok[s]:
            tp_part += 1
P = tp/max(tp+fp, 1); R = tp/max(tp+fn, 1)
Pp = tp_part/max(tp+fp, 1)
print('\n[1] SPAN THOI GIAN (tu tim vs vang)')
print('    khop chinh xac : P %.1f%%  R %.1f%%  F1 %.1f%%'
      % (100*P, 100*R, 200*P*R/max(P+R, 1e-9)))
print('    khop chong lan : P %.1f%%' % (100*Pp))
print('    tim duoc %d span | vang co %d' % (tp+fp, tp+fn))

# --- 2. trigger su kien ---
etp = efp = efn = 0
for i in TE:
    gold = set()
    for e in docs[i]['events']:
        for m in e['mention']:
            if 'sent_id' in m:
                gold.add((m['sent_id'], m['offset'][0]))
    pred = {(s, a) for s, a, b, _, _, _ in ex_by_doc[i].events}
    etp += len(pred & gold); efp += len(pred-gold); efn += len(gold-pred)
P2 = etp/max(etp+efp, 1); R2 = etp/max(etp+efn, 1)
print('\n[2] TRIGGER SU KIEN (tu dien hoc tu train)')
print('    P %.1f%%  R %.1f%%  F1 %.1f%%'
      % (100*P2, 100*R2, 200*P2*R2/max(P2+R2, 1e-9)))

# --- 3. gan thoi gian cho su kien: so voi ERE CONTAINS ---
gold_pair = set()
for i in TE:
    tx = {t['id']: (t['sent_id'], t['offset'][0]) for t in docs[i]['TIMEX']}
    ev = {}
    for e in docs[i]['events']:
        ms = [(m['sent_id'], m['offset'][0]) for m in e['mention'] if 'sent_id' in m]
        if ms: ev[e['id']] = min(ms)
    for h, t in docs[i]['temporal_relations'].get('CONTAINS', []):
        if h in tx and t in ev: gold_pair.add((i, ev[t], tx[h]))
        if t in tx and h in ev: gold_pair.add((i, ev[h], tx[t]))

pred_pair = set()
pos = {n.nid: (n.doc_id, n.sent_id, n.offset[0]) for n in g.nodes.values()}
for e in g.edges.values():
    if e.label == 'hasTime' and e.head in pos and e.tail in pos:
        d, s1, o1 = pos[e.head]; _, s2, o2 = pos[e.tail]
        pred_pair.add((d, (s1, o1), (s2, o2)))
ov = len(pred_pair & gold_pair)
print('\n[3] GAN THOI GIAN CHO SU KIEN (canh hasTime vs ERE CONTAINS)')
print('    du doan %d | vang %d | giao %d' % (len(pred_pair), len(gold_pair), ov))
print('    P %.1f%%  R %.1f%%'
      % (100*ov/max(len(pred_pair), 1), 100*ov/max(len(gold_pair), 1)))

# --- 4. thu tu su kien: canh NARRATIVE/BEFORE vs ERE ---
gold_ord = set()
for i in TE:
    ev = {}
    for e in docs[i]['events']:
        ms = [(m['sent_id'], m['offset'][0]) for m in e['mention'] if 'sent_id' in m]
        if ms: ev[e['id']] = min(ms)
    for rel in ('BEFORE', 'OVERLAP', 'CONTAINS'):
        for h, t in docs[i]['temporal_relations'].get(rel, []):
            if h in ev and t in ev and rel == 'BEFORE':
                gold_ord.add((i, ev[h], ev[t]))
pred_ord = set()
for e in g.edges.values():
    if e.label in ('BEFORE', 'NARRATIVE_BEFORE') and e.head in pos and e.tail in pos:
        d, s1, o1 = pos[e.head]; _, s2, o2 = pos[e.tail]
        pred_ord.add((d, (s1, o1), (s2, o2)))
ov2 = len(pred_ord & gold_ord)
print('\n[4] THU TU SU KIEN (canh BEFORE vs ERE BEFORE)')
print('    du doan %d | vang %d | giao %d' % (len(pred_ord), len(gold_ord), ov2))
print('    P %.1f%%  R %.1f%%'
      % (100*ov2/max(len(pred_ord), 1), 100*ov2/max(len(gold_ord), 1)))

# --- 5. do phu thoi gian cua su kien ---
nev = len(g.of_type(type(next(iter(g.of_type(__import__('ecskg.schema', fromlist=['Event']).Event)))))) \
    if g.of_type(__import__('ecskg.schema', fromlist=['Event']).Event) else 0
from ecskg.schema import Event as _E, TimeX as _T
evs = g.of_type(_E)
withT = {e.head for e in g.edges.values() if e.label == 'hasTime'}
multi = collections.Counter()
for e in evs:
    ts = [t for t in g.times_of(e.nid) if t.bounds()]
    multi[min(len(ts), 3)] += 1
print('\n[5] DO PHU THOI GIAN')
print('    su kien: %d | co >=1 anchor: %d (%.1f%%)'
      % (len(evs), len(withT), 100*len(withT)/max(len(evs), 1)))
print('    co >=2 anchor giai duoc: %d (%.1f%%)'
      % (multi[2]+multi[3], 100*(multi[2]+multi[3])/max(len(evs), 1)))
tn = g.of_type(_T)
solved = sum(1 for t in tn if t.bounds())
print('    TimeX: %d | chuan hoa duoc: %d (%.1f%%)'
      % (len(tn), solved, 100*solved/max(len(tn), 1)))
print('\ntong thoi gian %.1fs' % (time.time()-t0))
