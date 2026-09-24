"""EXP16 - MUC C co target that khong?

Y tuong quyet dinh: gold dong kin bac cau 100%, nhung MOI model TRE deu phan loai
TUNG CAP DOC LAP -> output cua no KHONG THE dong kin. Do la nguon conflict that.

Khong can train model moi: dung chinh cascade da build (79.1% accuracy do o EXP9)
lam "model", sinh do thi thoi gian du doan, roi dem vi pham:
  V1 doi xung   : du doan BEFORE(a,b) VA BEFORE(b,a)
  V2 chu trinh  : a<b<...<a
  V3 bac cau    : a<b va b<c nhung KHONG a<c  (gold: 100% dong kin)

So sanh so vi pham tren GOLD (da biet = 0) va tren DU DOAN.
"""
import json, collections, random, math

random.seed(20261012)

ere = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        ere[d['id']] = d

FWD = {'BEFORE': 'BEFORE_FWD', 'CONTAINS': 'CONTAINS_FWD', 'OVERLAP': 'OVERLAP_FWD',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}
REV = {'BEFORE': 'BEFORE_REV', 'CONTAINS': 'CONTAINS_REV', 'OVERLAP': 'OVERLAP_REV',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}


def doc_rows(doc):
    d = ere[doc]
    ev = {}
    for e in d['events']:
        s = [m['sent_id'] for m in e['mention'] if 'sent_id' in m]
        if s:
            ev[e['id']] = {'t': e['type'], 's': min(s)}
    R = {}
    for rel, ps in d['temporal_relations'].items():
        for h, t in ps:
            if h in ev and t in ev:
                R[(h, t)] = rel
    c2 = {}
    for kind, ps in d.get('causal_relations', {}).items():
        for h, t in ps:
            c2[(h, t)] = kind
    for h, t in d.get('subevent_relations', []):
        c2[(h, t)] = 'SUBEVENT'
    return ev, R, c2


# ---- luat 6 dong hoc tren MINE ----
docs = sorted(ere)
random.shuffle(docs)
cut = int(0.8 * len(docs))
MINE, EVAL = docs[:cut], docs[cut:]

rule = collections.defaultdict(collections.Counter)
glob = collections.Counter()
for doc in MINE:
    ev, R, c2 = doc_rows(doc)
    ids = sorted(ev, key=lambda i: ev[i]['s'])
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            lab = FWD.get(R[(a, b)]) if (a, b) in R else (REV.get(R[(b, a)]) if (b, a) in R else None)
            if not lab:
                continue
            glob[lab] += 1
            if (a, b) in c2:
                rule[(c2[(a, b)], 'FWD')][lab] += 1
            elif (b, a) in c2:
                rule[(c2[(b, a)], 'REV')][lab] += 1
MAJ = glob.most_common(1)[0][0]
RULE = {k: c.most_common(1)[0][0] for k, c in rule.items() if sum(c.values()) >= 10}
print('6 luat hoc duoc:', {str(k): v for k, v in sorted(RULE.items())})
print('majority fallback:', MAJ)
print()


def predict(ev, c2, a, b):
    if (a, b) in c2 and (c2[(a, b)], 'FWD') in RULE:
        return RULE[(c2[(a, b)], 'FWD')]
    if (b, a) in c2 and (c2[(b, a)], 'REV') in RULE:
        return RULE[(c2[(b, a)], 'REV')]
    return MAJ


def violations(before_edges):
    """before_edges: set cac cap (u,v) nghia la u BEFORE v"""
    sym = sum(1 for (u, v) in before_edges if (v, u) in before_edges)
    adj = collections.defaultdict(set)
    for u, v in before_edges:
        adj[u].add(v)
    # bac cau: u<v, v<w nhung khong u<w
    trans_miss = 0
    for u in adj:
        for v in adj[u]:
            for w in adj.get(v, ()):
                if w != u and (u, w) not in before_edges:
                    trans_miss += 1
    # chu trinh (DFS mau)
    color = {}
    cyc = 0

    def dfs(u):
        nonlocal cyc
        color[u] = 1
        for v in adj[u]:
            if color.get(v, 0) == 1:
                cyc += 1
            elif color.get(v, 0) == 0:
                dfs(v)
        color[u] = 2
    import sys
    sys.setrecursionlimit(50000)
    for n in list(adj):
        if color.get(n, 0) == 0:
            dfs(n)
    return sym, cyc, trans_miss


tot = {'gold': [0, 0, 0, 0], 'pred': [0, 0, 0, 0]}
docs_with = {'gold': [0, 0, 0], 'pred': [0, 0, 0]}

for doc in EVAL:
    ev, R, c2 = doc_rows(doc)
    ids = sorted(ev, key=lambda i: ev[i]['s'])
    if len(ids) < 3:
        continue
    gold_b, pred_b = set(), set()
    npair = 0
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            lab = FWD.get(R[(a, b)]) if (a, b) in R else (REV.get(R[(b, a)]) if (b, a) in R else None)
            if not lab:
                continue
            npair += 1
            if lab == 'BEFORE_FWD':
                gold_b.add((a, b))
            elif lab == 'BEFORE_REV':
                gold_b.add((b, a))
            p = predict(ev, c2, a, b)
            if p == 'BEFORE_FWD':
                pred_b.add((a, b))
            elif p == 'BEFORE_REV':
                pred_b.add((b, a))
    for tag, edges in (('gold', gold_b), ('pred', pred_b)):
        s, c, t = violations(edges)
        tot[tag][0] += s
        tot[tag][1] += c
        tot[tag][2] += t
        tot[tag][3] += len(edges)
        docs_with[tag][0] += (s > 0)
        docs_with[tag][1] += (c > 0)
        docs_with[tag][2] += (t > 0)

nd = len(EVAL)
print('=== VI PHAM RANG BUOC TREN %d DOCUMENT EVAL ===' % nd)
print('%-22s %14s %14s' % ('', 'GOLD', 'DU DOAN'))
print('-' * 54)
print('%-22s %14d %14d' % ('canh BEFORE', tot['gold'][3], tot['pred'][3]))
print('%-22s %14d %14d' % ('V1 vi pham doi xung', tot['gold'][0], tot['pred'][0]))
print('%-22s %14d %14d' % ('V2 chu trinh', tot['gold'][1], tot['pred'][1]))
print('%-22s %14d %14d' % ('V3 thieu bac cau', tot['gold'][2], tot['pred'][2]))
print()
print('%-22s %13d%% %13d%%' % ('doc co V1', 100*docs_with['gold'][0]//nd, 100*docs_with['pred'][0]//nd))
print('%-22s %13d%% %13d%%' % ('doc co V2', 100*docs_with['gold'][1]//nd, 100*docs_with['pred'][1]//nd))
print('%-22s %13d%% %13d%%' % ('doc co V3', 100*docs_with['gold'][2]//nd, 100*docs_with['pred'][2]//nd))
