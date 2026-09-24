"""Tran RECALL: bo do ung vien tu van ban bat duoc bao nhieu % argument vang?

Day la cong quyet dinh. Bo phan loai vai co tot den may cung khong vuot duoc tran nay.
So ba bo sinh ung vien:
   C1  chuoi token viet hoa            (dang dung trong build.py)
   C2  C1 + entity mention cua MAVEN-Arg lam tham chieu tran ly thuyet
   C3  cum danh tu tho: quet tu mao tu/gioi tu den truoc dong tu/dau cau
"""
import json, zipfile, io, collections, re, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecskg.extract import find_entities, find_timex

DET = {'a', 'an', 'the', 'this', 'that', 'these', 'those', 'his', 'her', 'its',
       'their', 'our', 'my', 'some', 'many', 'most', 'several', 'two', 'three'}
STOPEND = {'.', ',', ';', ':', '(', ')', '``', "''", 'and', 'but', 'or', 'which',
           'who', 'that', 'was', 'were', 'is', 'are', 'had', 'has', 'have', 'been'}


def tokenize(doc):
    """document la chuoi da tokenize, noi bang khoang trang -> (tokens, char_start[])"""
    toks, starts, i = [], [], 0
    for t in doc.split(' '):
        if t:
            toks.append(t); starts.append(i)
        i += len(t) + 1
    return toks, starts


def char2tok(starts, toks, lo, hi):
    """span ky tu -> [i, j) token"""
    i = j = None
    for k, s in enumerate(starts):
        e = s + len(toks[k])
        if i is None and e > lo:
            i = k
        if s < hi:
            j = k + 1
    return (i, j) if i is not None and j is not None and j > i else None


def cand_caps(toks):
    return [(a, b) for a, b, _ in find_entities(toks)]


def cand_np(toks):
    """cum danh tu tho: bat dau o mao tu hoac token viet hoa, keo den truoc STOPEND."""
    out = []
    n = len(toks)
    for i in range(n):
        w = toks[i]
        lw = w.lower()
        if not (lw in DET or (w[:1].isupper() and w[:1].isalpha())):
            continue
        j = i + 1
        while j < n and toks[j].lower() not in STOPEND and j - i < 8:
            j += 1
        if j > i:
            out.append((i, j))
            if j - i > 1:
                out.append((i, i+1))
    return out


docs = []
z = zipfile.ZipFile('MAVEN-Arg.zip')
with z.open('valid.jsonl') as f:
    for line in io.TextIOWrapper(f, encoding='utf-8'):
        docs.append(json.loads(line))
print('doc test: %d' % len(docs), flush=True)

stat = collections.Counter()
gold_by_role = collections.Counter()
hit_by_role = {k: collections.Counter() for k in ('caps', 'np', 'ent')}
ncand = collections.Counter()

for d in docs:
    toks, starts = tokenize(d['document'])
    # ung vien
    tcov = set()
    for a, b, _, _ in find_timex(toks):
        tcov |= set(range(a, b))
    caps = {s for s in cand_caps(toks) if not (set(range(*s)) & tcov)}
    nps = {s for s in cand_np(toks) if not (set(range(*s)) & tcov)}
    ents = set()
    for e in d.get('entities', []):
        for m in e['mention']:
            sp = char2tok(starts, toks, m['offset'][0], m['offset'][1])
            if sp:
                ents.add(sp)
    ncand['caps'] += len(caps); ncand['np'] += len(nps); ncand['ent'] += len(ents)

    # argument co the la 'offset' (span van ban) HOAC 'entity_id' (tro toi entity)
    ent_spans = collections.defaultdict(list)
    for e in d.get('entities', []):
        for m in e['mention']:
            sp = char2tok(starts, toks, m['offset'][0], m['offset'][1])
            if sp:
                ent_spans[e['id']].append(sp)

    for e in d['events']:
        for r, vs in (e.get('argument') or {}).items():
            for v in vs:
                if 'offset' in v:
                    sp = char2tok(starts, toks, v['offset'][0], v['offset'][1])
                elif 'entity_id' in v and ent_spans.get(v['entity_id']):
                    sp = ent_spans[v['entity_id']][0]
                else:
                    sp = None
                if not sp:
                    continue
                stat['gold'] += 1
                gold_by_role[r] += 1
                for nm, S in (('caps', caps), ('np', nps), ('ent', ents)):
                    if sp in S:
                        stat[nm+'_exact'] += 1
                        hit_by_role[nm][r] += 1
                    elif any(max(sp[0], a) < min(sp[1], b) for a, b in S):
                        stat[nm+'_overlap'] += 1

g = stat['gold']
print('\nargument vang anh xa duoc sang token: %d' % g)
print('\n%-6s %10s %10s %10s %12s' % ('bo', 'khop dung', '%', 'chong lan', 'so ung vien'))
print('-'*54)
for nm, lab in (('caps', 'C1 caps'), ('np', 'C3 NP tho'), ('ent', 'C2 entity vang')):
    print('%-6s %10d %9.1f%% %10d %12d'
          % (lab, stat[nm+'_exact'], 100*stat[nm+'_exact']/g,
             stat[nm+'_overlap'], ncand[nm]))

print('\ntran recall theo vai (10 vai lon nhat):')
print('  %-20s %8s %8s %8s %8s' % ('vai', 'gold', 'caps', 'NP tho', 'ent vang'))
for r, n in gold_by_role.most_common(10):
    print('  %-20s %8d %7.1f%% %7.1f%% %7.1f%%'
          % (r, n, 100*hit_by_role['caps'][r]/n,
             100*hit_by_role['np'][r]/n, 100*hit_by_role['ent'][r]/n))
