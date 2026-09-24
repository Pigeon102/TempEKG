"""Lam lai co PHAN TANG — ban truoc bi RO RI NHAN.

Ro ri: n_anchor bi cap o 4 nen 'n_anchor=4' = ">=4 anchor". Cang nhieu anchor thi giao
cang de rong — TAT DINH VE SO HOC, khong phai pattern ngu nghia. method_set voi 3 phuong
phap va gran_set voi 3 hat do cung ngu y >=3 anchor -> cung mot ro ri.

Sua: PHAN TANG theo so anchor. Trong moi tang (dung k anchor), hoi lai:
     thuoc tinh nao du doan conflict?
Trong tang k=2, gran_set va method_set toi da 2 gia tri nen ban so khong con ro ri.
"""
import json, collections, zipfile, io, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timex_norm2 import doc_reference_chain
from ecskg.views import EventClass, e4_conflict, enumerate_views, mine_view, wilson_lo

docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line); docs[d['id']] = d

z = zipfile.ZipFile('MAVEN-Arg.zip')
argrec = {}
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            et = {e['id']: e.get('type', 'Other') for e in d.get('entities', [])}
            for e in d['events']:
                rr = collections.defaultdict(list)
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            rr[r].append(et.get(v['entity_id'], 'Other'))
                if rr:
                    argrec[(d['id'], e['id'])] = dict(rr)

events = []
for doc, d in docs.items():
    tl = [(t['id'], t['mention']) for t in
          sorted(d['TIMEX'], key=lambda x: (x['sent_id'], x['offset'][0]))]
    norm = doc_reference_chain(tl)
    nsent = len(d['tokens'])
    anchors = collections.defaultdict(list)
    for h, t in d['temporal_relations'].get('CONTAINS', []):
        if h in norm: anchors[t].append(h)
        if t in norm: anchors[h].append(t)
    for e in d['events']:
        eid = e['id']
        ms = [m['sent_id'] for m in e['mention'] if 'sent_id' in m]
        s0 = min(ms) if ms else 0
        av = []; grans = []; meths = []
        for tid in anchors.get(eid, []):
            r = norm.get(tid)
            if r and r[0] is not None and r[2] != 'duration':
                av.append((r[0], r[1])); grans.append(r[2])
                meths.append(r[3] if len(r) > 3 else 'regex')
        rr = argrec.get((doc, eid), {})
        ets = sorted({x for v in rr.values() for x in v})
        roles = sorted(rr)
        events.append(EventClass(
            nid='%s:%s' % (doc, eid), doc=doc, anchors=av,
            etype=e['type'], n_role=min(len(roles), 5),
            roleset='|'.join(roles[:3]), top_role=roles[0] if roles else '-',
            etypeset='|'.join(ets),
            has_person=int('Person' in ets), has_org=int('Organization' in ets),
            has_loc=int('Location' in ets),
            n_anchor=len(av),
            # trong tang k, hai truc nay KHONG con la proxy cua so anchor
            gran_set='|'.join(sorted(set(grans))),
            method_set='|'.join(sorted(set(meths))),
            anchor_src='ere',
            sent_bucket='dau' if s0 < nsent*0.33 else ('giua' if s0 < nsent*0.66 else 'cuoi'),
        ))

# ---------- kiem chung ro ri: conflict theo so anchor ----------
print('='*80)
print('RO RI NHAN: ti le conflict tang theo so anchor (tat dinh ve so hoc)')
print('='*80)
by_k = collections.defaultdict(lambda: [0, 0])
for e in events:
    y = e4_conflict(e)
    if y is None: continue
    k = min(e.n_anchor, 6)
    by_k[k][1] += 1; by_k[k][0] += y
print('  %-10s %8s %10s' % ('so anchor', 'so event', 'conflict'))
for k in sorted(by_k):
    c, n = by_k[k]
    print('  %-10s %8d %9.1f%%' % ('%d' % k if k < 6 else '>=6', n, 100*c/n))
print('\n  -> day la ly do ban truoc chon toan pattern chua n_anchor=4. Da loai.')

POOL = ['etype', 'n_role', 'roleset', 'top_role', 'etypeset',
        'has_person', 'has_org', 'has_loc', 'gran_set', 'method_set', 'sent_bucket']

for K in (2, 3):
    strat = [e for e in events if e.n_anchor == K]
    base_n = len(strat)
    base_c = sum(1 for e in strat if e4_conflict(e) is True)
    if base_n < 100:
        continue
    base = base_c/base_n
    print('\n' + '='*80)
    print('TANG k=%d anchor: %d event | conflict nen %.1f%%' % (K, base_n, 100*base))
    print('='*80)
    allp = []
    for axes in enumerate_views(POOL, max_dim=2):
        res, b2, gt = mine_view(strat, axes, e4_conflict,
                                min_sup=max(30, base_n//200))
        for lift, r, n, s in res:
            w = wilson_lo(int(round(r*n)), n)
            if w > base:
                allp.append((w/base, w, r, n, axes, s))
    allp.sort(reverse=True)
    seen = set(); shown = 0
    for wl, w, r, n, axes, s in allp:
        key = tuple(sorted(zip(axes, s)))
        if key in seen: continue
        seen.add(key)
        print('  lift(WLB) %5.2fx | conflict %5.1f%% | sup %5d | %s'
              % (wl, 100*r, n, ' & '.join('%s=%s' % (a, v) for a, v in zip(axes, s))))
        shown += 1
        if shown >= 14: break
    print('  ... tong chu ky vuot nen: %d' % len(allp))
    if not allp:
        print('  KHONG co chu ky nao vuot nen -> trong tang nay thuoc tinh KHONG du doan duoc')
