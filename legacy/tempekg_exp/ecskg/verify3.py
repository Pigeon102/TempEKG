"""KIEM CHUNG ba dieu kien con thieu o FORMAL.md §8.2.

(a) Pattern do tren anchor ERE VANG -> ap len do thi dung tu TEXT, do lift lai
(b) Nhan E4 la proxy; pattern manh nhat co the chi bat ARTIFACT
    -> tach nhan NGHIEM NGAT: chi giu conflict ma MOI anchor deu tu regex thuan
       (khong co suy dien tham chieu) => conflict "that" trong du lieu vang
(c) Support nho o k=3 -> gop k>=3 thanh mot tang + khoang tin cay
"""
import json, collections, zipfile, io, sys, os, math, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timex_norm2 import doc_reference_chain, normalize
from ecskg.extract import find_timex, find_entities, TriggerLexicon
random.seed(20261012)


def wlo(k, n, z=1.96):
    if n == 0: return 0.0
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n)
    m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)); return max(0.0, (c-m)/d)


def whi(k, n, z=1.96):
    if n == 0: return 1.0
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n)
    m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)); return min(1.0, (c+m)/d)


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
                if rr: argrec[(d['id'], e['id'])] = dict(rr)

# ============================================ do thi VANG
GOLD = []
for doc, d in docs.items():
    tl = [(t['id'], t['mention']) for t in
          sorted(d['TIMEX'], key=lambda x: (x['sent_id'], x['offset'][0]))]
    norm = doc_reference_chain(tl)
    nsent = len(d['tokens'])
    anc = collections.defaultdict(list)
    for h, t in d['temporal_relations'].get('CONTAINS', []):
        if h in norm: anc[t].append(h)
        if t in norm: anc[h].append(t)
    for e in d['events']:
        ms = [m['sent_id'] for m in e['mention'] if 'sent_id' in m]
        s0 = min(ms) if ms else 0
        iv, gr, me = [], [], []
        for tid in anc.get(e['id'], []):
            r = norm.get(tid)
            if r and r[0] is not None and r[2] != 'duration':
                iv.append((r[0], r[1])); gr.append(r[2])
                me.append(r[3] if len(r) > 3 else 'regex')
        if len(iv) < 2: continue
        rr = argrec.get((doc, e['id']), {})
        ets = sorted({x for v in rr.values() for x in v})
        GOLD.append({'y': int(max(a[0] for a in iv) > min(a[1] for a in iv)),
                     'k': len(iv), 'etype': e['type'], 'gran': gr, 'method': me,
                     'etypeset': ets, 'roleset': sorted(rr),
                     'has_person': int('Person' in ets), 'has_org': int('Organization' in ets),
                     'has_loc': int('Location' in ets), 'n_role': min(len(rr), 5),
                     'sent_bucket': 'dau' if s0 < nsent*0.33 else
                                    ('giua' if s0 < nsent*0.66 else 'cuoi')})

# ============================================ do thi TEXT
ids = sorted(docs); random.shuffle(ids)
TRD, TED = ids[:int(.8*len(ids))], ids[int(.8*len(ids)):]
lex = TriggerLexicon().fit(
    [docs[i]['tokens'] for i in TRD],
    [{(m['sent_id'], m['offset'][0]): e['type']
      for e in docs[i]['events'] for m in e['mention'] if 'sent_id' in m} for i in TRD])

TEXT = []
for i in TED:
    d = docs[i]; toks = d['tokens']; nsent = len(toks)
    tx = []                                   # (sent, i, j, lo, hi, gran, method)
    ry = rd = None
    for s, tk in enumerate(toks):
        for a, b, surf, tt in find_timex(tk):
            r = normalize(surf, ref_year=ry, ref_date=rd)
            if r and r[0] is not None and r[2] != 'duration':
                tx.append((s, a, b, r[0], r[1], r[2], r[3] if len(r) > 3 else 'regex'))
                if r[2] in ('day', 'month', 'year'):
                    ry = r[0]//10000
                    if r[2] == 'day': rd = r[0]
    by_sent = collections.defaultdict(list)
    for t in tx: by_sent[t[0]].append(t)
    for s, tk in enumerate(toks):
        for a, b, surf, et, c in lex.find(tk):
            cand = by_sent.get(s, [])
            if not cand:
                prev = [t for t in tx if t[0] < s]
                if prev:
                    m = max(t[0] for t in prev)
                    cand = [t for t in prev if t[0] == m]
            if len(cand) < 2: continue
            iv = [(t[3], t[4]) for t in cand]
            TEXT.append({'y': int(max(x[0] for x in iv) > min(x[1] for x in iv)),
                         'k': len(iv), 'etype': et,
                         'gran': [t[5] for t in cand], 'method': [t[6] for t in cand],
                         'etypeset': [], 'roleset': [], 'has_person': 0,
                         'has_org': 0, 'has_loc': 0, 'n_role': 0,
                         'sent_bucket': 'dau' if s < nsent*0.33 else
                                        ('giua' if s < nsent*0.66 else 'cuoi')})
print('gold: %d event xet duoc | text: %d' % (len(GOLD), len(TEXT)), flush=True)

# ============================================ pattern can kiem chung
P = [
    ('ALL(method=refprop)', lambda r: bool(r['method']) and all(m == 'refprop' for m in r['method'])),
    ('ALL(method=refprop) & ALL(gran=day)',
     lambda r: bool(r['method']) and all(m == 'refprop' for m in r['method'])
     and bool(r['gran']) and all(g == 'day' for g in r['gran'])),
    ('ALL(gran=day)', lambda r: bool(r['gran']) and all(g == 'day' for g in r['gran'])),
    ('HAS(method=refprop)', lambda r: 'refprop' in r['method']),
    ('CNT(gran>=2)', lambda r: len(set(r['gran'])) >= 2),
    ('etype=Hostile_encounter', lambda r: r['etype'] == 'Hostile_encounter'),
    ('etype=Military_operation', lambda r: r['etype'] == 'Military_operation'),
    ('sent_bucket=dau', lambda r: r['sent_bucket'] == 'dau'),
    ('ALL(method=refprop) & has_loc=1', lambda r: bool(r['method'])
     and all(m == 'refprop' for m in r['method']) and r['has_loc'] == 1),
]


def report(rows, title, k_filter, note=''):
    sub = [r for r in rows if k_filter(r['k'])]
    if len(sub) < 50:
        print('  %s: chi %d event, bo qua' % (title, len(sub))); return
    base = sum(r['y'] for r in sub)/len(sub)
    print('\n  %s — %d event, nen %.1f%% %s' % (title, len(sub), 100*base, note))
    print('  %-40s %8s %8s %8s %14s' % ('pattern', 'sup', 'conf', 'lift', 'CI 95% lift'))
    for nm, fn in P:
        m = [r for r in sub if fn(r)]
        if len(m) < 10:
            print('  %-40s %8s' % (nm, 'sup<10')); continue
        c = sum(r['y'] for r in m)
        lo, hi = wlo(c, len(m))/base, whi(c, len(m))/base
        print('  %-40s %8d %7.1f%% %7.2fx  [%.2f, %.2f]'
              % (nm, len(m), 100*c/len(m), (c/len(m))/base, lo, hi))


print('\n' + '='*88)
print('(a) AP PATTERN LEN DO THI DUNG TU TEXT')
print('='*88)
report(GOLD, 'anchor VANG, k=2', lambda k: k == 2)
report(TEXT, 'do thi TEXT, k=2', lambda k: k == 2,
       '(cac pattern dung etypeset/has_* KHONG ap duoc: text graph khong co kieu entity)')

print('\n' + '='*88)
print('(b) NHAN NGHIEM NGAT: chi conflict ma MOI anchor tu REGEX THUAN')
print('='*88)
strict = [dict(r) for r in GOLD if all(m == 'regex' for m in r['method'])]
n_all = sum(1 for r in GOLD if r['k'] == 2)
n_st = sum(1 for r in strict if r['k'] == 2)
print('  k=2: %d event -> %d event chi dung regex (%.1f%%)'
      % (n_all, n_st, 100*n_st/max(n_all, 1)))
c_all = sum(r['y'] for r in GOLD if r['k'] == 2)
c_st = sum(r['y'] for r in strict if r['k'] == 2)
print('  conflict: %d (tat ca) -> %d chi regex (%.1f%% cua tong conflict)'
      % (c_all, c_st, 100*c_st/max(c_all, 1)))
print('  ti le conflict: %.1f%% (tat ca) vs %.1f%% (chi regex)'
      % (100*c_all/max(n_all, 1), 100*c_st/max(n_st, 1)))
report(strict, 'NHAN NGHIEM NGAT, k=2', lambda k: k == 2,
       '(pattern refprop tat yeu bien mat)')

print('\n' + '='*88)
print('(c) GOP k>=3 de tang support + khoang tin cay')
print('='*88)
report(GOLD, 'anchor VANG, k>=3', lambda k: k >= 3)
report(GOLD, 'anchor VANG, k=3', lambda k: k == 3)
