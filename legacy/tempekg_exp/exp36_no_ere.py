"""EXP36 - Bo ERE khi INFERENCE: mining tu GRAPH, khong dung nhan.

Y kien nguoi dung: ERE chi de MAP ra constraint (giai doan hoc). Khi mining/phat hien
thi chi duoc dung GRAPH (event + argument + TIMEX + vi tri van ban), khong dung nhan ERE.

Do la kich ban trien khai THAT: document moi khong co annotate ERE.

Thay the tung thanh phan:
  ERE CONTAINS(timex, event)  ->  gan TIMEX theo KHOANG CACH VAN BAN
  ERE temporal relation       ->  KHONG dung (chi de danh gia)
  ERE causal/subevent         ->  KHONG dung

Do: mat bao nhieu khi thay?
"""
import json, collections, sys, statistics
sys.path.insert(0, 'tempekg_exp')
from timex_norm2 import doc_reference_chain

docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        docs[d['id']] = d

# =============== GAN TIMEX: gold (ERE) vs suy tu VAN BAN ===============
gold_anchor = collections.defaultdict(set)      # (doc,event) -> {timex}
text_anchor = collections.defaultdict(set)
norm_all = {}

for doc, d in docs.items():
    tl = [(t['id'], t['mention']) for t in
          sorted(d['TIMEX'], key=lambda x: (x['sent_id'], x['offset'][0]))]
    norm = doc_reference_chain(tl)
    norm_all[doc] = norm
    tx_pos = {t['id']: (t['sent_id'], t['offset'][0]) for t in d['TIMEX']}
    ev_pos = {}
    for e in d['events']:
        ms = [(m['sent_id'], m['offset'][0]) for m in e['mention'] if 'sent_id' in m]
        if ms:
            ev_pos[e['id']] = min(ms)
    ids = set(ev_pos)

    # --- GOLD: canh CONTAINS cua ERE ---
    for h, t in d['temporal_relations'].get('CONTAINS', []):
        if h in norm and t in ids:
            gold_anchor[(doc, t)].add(h)
        if t in norm and h in ids:
            gold_anchor[(doc, h)].add(t)

    # --- TU VAN BAN: TIMEX gan nhat trong CUNG CAU, neu khong thi cau truoc do ---
    for eid, (es, eo) in ev_pos.items():
        same = [(tid, p) for tid, p in tx_pos.items() if p[0] == es]
        if same:
            best = min(same, key=lambda x: abs(x[1][1] - eo))
            text_anchor[(doc, eid)].add(best[0])
        else:
            prev = [(tid, p) for tid, p in tx_pos.items() if p[0] < es]
            if prev:
                best = max(prev, key=lambda x: x[1])
                text_anchor[(doc, eid)].add(best[0])

# =============== SO SANH DO PHU & DO CHINH XAC ===============
print('=' * 70)
print('GAN TIMEX CHO EVENT: gold (ERE) vs suy tu VAN BAN')
print('=' * 70)
n_ev = sum(len(set(e['id'] for e in d['events'])) for d in docs.values())
print('tong event                    : %d' % n_ev)
print('co anchor tu GOLD (ERE)       : %d (%.1f%%)' % (len(gold_anchor), 100*len(gold_anchor)/n_ev))
print('co anchor tu VAN BAN          : %d (%.1f%%)' % (len(text_anchor), 100*len(text_anchor)/n_ev))
print()

# do trung khop
both = set(gold_anchor) & set(text_anchor)
exact = sum(1 for k in both if gold_anchor[k] & text_anchor[k])
print('event co CA HAI               : %d' % len(both))
print('  van ban chon DUNG timex gold: %d (%.1f%%)' % (exact, 100*exact/max(len(both), 1)))
print()

# do sai lech thoi gian
diffs = []
for k in both:
    gv = [norm_all[k[0]][t] for t in gold_anchor[k] if norm_all[k[0]].get(t)]
    tv = [norm_all[k[0]][t] for t in text_anchor[k] if norm_all[k[0]].get(t)]
    gv = [v for v in gv if v and v[0] is not None]
    tv = [v for v in tv if v and v[0] is not None]
    if gv and tv:
        diffs.append(abs(min(v[0] for v in tv) - min(v[0] for v in gv)))
if diffs:
    diffs.sort()
    print('sai lech ngay giua hai cach gan (tren %d event):' % len(diffs))
    print('  = 0 ngay      : %.1f%%' % (100*sum(1 for x in diffs if x == 0)/len(diffs)))
    print('  <= 31 ngay    : %.1f%%' % (100*sum(1 for x in diffs if x <= 31)/len(diffs)))
    print('  <= 365 ngay   : %.1f%%' % (100*sum(1 for x in diffs if x <= 365)/len(diffs)))
    print('  trung vi      : %d ngay' % diffs[len(diffs)//2])

# =============== T5 voi hai cach gan ===============
def t5(anchor_map, name):
    v = collections.Counter()
    for (doc, eid), txs in anchor_map.items():
        txs = list(txs)
        if len(txs) < 2:
            continue
        vals = [norm_all[doc].get(t) for t in txs]
        vals = [x for x in vals if x and x[0] is not None and x[2] != 'duration']
        if len(vals) < 2:
            v['UNDECIDABLE'] += 1
            continue
        lo = max(x[0] for x in vals); hi = min(x[1] for x in vals)
        v['CONFLICT' if lo > hi else 'OK'] += 1
    tot = v['CONFLICT'] + v['OK']
    print('  %-26s multi=%5d | CONFLICT %4d (%.1f%%)'
          % (name, tot + v['UNDECIDABLE'], v['CONFLICT'], 100*v['CONFLICT']/max(tot, 1)))


print()
print('T5 granularity voi hai cach gan:')
t5(gold_anchor, 'GOLD (ERE CONTAINS)')
t5(text_anchor, 'TU VAN BAN')

# =============== C1 mining khong can ERE ===============
print()
print('=' * 70)
print('MINING C1 tu GRAPH (khong dung quan he ERE)')
print('=' * 70)
import zipfile, io
z = zipfile.ZipFile('MAVEN-Arg.zip')
ent_ev = collections.defaultdict(list)
ev_type = {}
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            for e in d['events']:
                ev_type[(d['id'], e['id'])] = e['type']
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            ent_ev[(d['id'], v['entity_id'])].append((e['id'], r))


def iv(anchor_map, doc, eid):
    txs = anchor_map.get((doc, eid), ())
    vals = [norm_all[doc].get(t) for t in txs]
    vals = [x for x in vals if x and x[0] is not None and x[2] != 'duration']
    if not vals:
        return None
    return max(x[0] for x in vals), min(x[1] for x in vals)


for anchor_map, nm in ((gold_anchor, 'anchor GOLD'), (text_anchor, 'anchor VAN BAN')):
    sig = collections.defaultdict(lambda: [0, 0])
    for (doc, ent), lst in ent_ev.items():
        lst = list(dict.fromkeys(lst))
        for i in range(len(lst)):
            for j in range(i+1, len(lst)):
                e1, r1 = lst[i]; e2, r2 = lst[j]
                if e1 == e2:
                    continue
                a, b = iv(anchor_map, doc, e1), iv(anchor_map, doc, e2)
                if a is None or b is None or a[0] > a[1] or b[0] > b[1]:
                    continue
                k = (ev_type[(doc, e1)], r1, ev_type[(doc, e2)], r2)
                sig[k][1] += 1
                if a[1] < b[0] or b[1] < a[0]:
                    sig[k][0] += 1
    n = sum(v[1] for v in sig.values())
    d_ = sum(v[0] for v in sig.values())
    big = sum(1 for v in sig.values() if v[1] >= 10)
    print('  %-16s: %6d cap co interval | %d signature sup>=10 | roi nhau %.1f%%'
          % (nm, n, big, 100*d_/max(n, 1)))
