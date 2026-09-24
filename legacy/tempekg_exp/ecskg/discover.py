"""BOTTOM-UP: danh dau conflict tren MAVEN roi TRUY RA pattern.

Dao chieu PaTeCon:
   PaTeCon : liet ke pattern (SP1..SP4) truoc  ->  tim conflict
   o day   : danh dau conflict truoc           ->  PHAT HIEN pattern nao mang conflict

Dinh nghia conflict giu nguyen cua ho (trivalent, chung minh duong tinh). Nhan conflict o
day la E4 — intra-event anchor giao rong — vi no dinh nghia duoc KHONG CAN mine constraint
truoc (khong vong tron), va la pattern PaTeCon khong bieu dien duoc.

Buoc HOC dung anchor ERE vang (hop le: hoc dung nhan, suy dien khong dung — y nhu
TriggerLexicon). Pattern tim duoc sau do ap len graph dung tu text.
"""
import json, collections, zipfile, io, sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timex_norm2 import doc_reference_chain
from ecskg.views import EventClass, e4_conflict, enumerate_views, mine_view, wilson_lo

# ---------- doc MAVEN-ERE: anchor + hat do ----------
docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        docs[d['id']] = d

# ---------- doc MAVEN-Arg: vai + kieu entity ----------
z = zipfile.ZipFile('MAVEN-Arg.zip')
argrec = {}          # (doc, eid) -> {role: [entity_type]}
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
print('event co argument: %d' % len(argrec), flush=True)

# ---------- dung event node co day du thuoc tinh ----------
events = []
for doc, d in docs.items():
    tl = [(t['id'], t['mention']) for t in
          sorted(d['TIMEX'], key=lambda x: (x['sent_id'], x['offset'][0]))]
    norm = doc_reference_chain(tl)
    nsent = len(d['tokens'])
    anchors = collections.defaultdict(list)
    for h, t in d['temporal_relations'].get('CONTAINS', []):
        if h in norm:
            anchors[t].append(h)
        if t in norm:
            anchors[h].append(t)
    for e in d['events']:
        eid = e['id']
        ms = [m['sent_id'] for m in e['mention'] if 'sent_id' in m]
        s0 = min(ms) if ms else 0
        av = []
        grans = set(); meths = set()
        for tid in anchors.get(eid, []):
            r = norm.get(tid)
            if r and r[0] is not None and r[2] != 'duration':
                av.append((r[0], r[1]))
                grans.add(r[2])
                meths.add(r[3] if len(r) > 3 else 'regex')
        rr = argrec.get((doc, eid), {})
        ets = sorted({x for v in rr.values() for x in v})
        roles = sorted(rr)
        events.append(EventClass(
            nid='%s:%s' % (doc, eid), doc=doc, anchors=av,
            etype=e['type'],
            n_role=min(len(roles), 5),
            roleset='|'.join(roles[:3]),
            top_role=roles[0] if roles else '-',
            etypeset='|'.join(ets),
            has_person=int('Person' in ets),
            has_org=int('Organization' in ets),
            has_loc=int('Location' in ets),
            n_anchor=min(len(av), 4),
            gran_set='|'.join(sorted(grans)),
            method_set='|'.join(sorted(meths)),
            anchor_src='ere',
            sent_bucket='dau' if s0 < nsent*0.33 else ('giua' if s0 < nsent*0.66 else 'cuoi'),
        ))

n_multi = sum(1 for e in events if e4_conflict(e) is not None)
n_conf = sum(1 for e in events if e4_conflict(e) is True)
print('event: %d | da-anchor (xet duoc): %d | CONFLICT E4: %d (%.1f%%)'
      % (len(events), n_multi, n_conf, 100*n_conf/max(n_multi, 1)), flush=True)

# ---------- quet DAN VIEW ----------
POOL = ['etype', 'n_role', 'roleset', 'top_role', 'etypeset',
        'has_person', 'has_org', 'has_loc', 'n_anchor',
        'gran_set', 'method_set', 'sent_bucket']

print('\n' + '='*88)
print('QUET DAN VIEW — view nao mang tin hieu conflict?')
print('='*88)
print('%-34s %8s %8s %8s %10s' % ('view (truc thuoc tinh)', '|sig|', 'sup>=30', 'lift max', 'WLB tot nhat'))
print('-'*88)

rows = []
for axes in enumerate_views(POOL, max_dim=2):
    res, base, gt = mine_view(events, axes, e4_conflict, min_sup=30)
    if not res:
        continue
    best = max(res, key=lambda x: wilson_lo(int(x[1]*x[2]), x[2]))
    wlb = wilson_lo(int(best[1]*best[2]), best[2])
    rows.append((wlb/max(base, 1e-9), res[0][0], len(res), axes, best, base))
rows.sort(reverse=True)
for wlift, lmax, nsig, axes, best, base in rows[:18]:
    print('%-34s %8d %8s %8.2fx %9.2fx'
          % ('+'.join(axes), nsig, '', lmax, wlift))

print('\n(ti le nen conflict E4 = %.3f)' % rows[0][5] if rows else '')

print('\n' + '='*88)
print('PATTERN PHAT HIEN DUOC — 20 chu ky manh nhat (Wilson LB, sup>=30)')
print('='*88)
allp = []
for axes in enumerate_views(POOL, max_dim=2):
    res, base, gt = mine_view(events, axes, e4_conflict, min_sup=30)
    for lift, r, n, s in res:
        w = wilson_lo(int(r*n), n)
        if w > base:
            allp.append((w/base, w, r, n, axes, s))
allp.sort(reverse=True)
seen = set()
shown = 0
for wl, w, r, n, axes, s in allp:
    key = tuple(sorted(zip(axes, s)))
    if key in seen:
        continue
    seen.add(key)
    print('  lift(WLB) %5.2fx | conflict %5.1f%% | sup %5d | %s'
          % (wl, 100*r, n, ' & '.join('%s=%s' % (a, v) for a, v in zip(axes, s))))
    shown += 1
    if shown >= 20:
        break
print('\ntong chu ky vuot nen: %d' % len(allp))
