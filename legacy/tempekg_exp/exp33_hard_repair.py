"""EXP33 - Tang sua dung RANG BUOC CUNG thay vi confidence cua model.

EXP31: sua bang confidence -> chu trinh -99.2% nhung dF1 = -0.02 (khong cai thien).
Gia thuyet: confidence cua model KHONG dang tin de quyet dinh go canh nao.
Thay bang lop CUNG (subevent/causal, precision ~100% do duoc).

Co che: khi chu trinh chua canh MAU THUAN voi rang buoc cung -> go DUNG canh do.
"""
import json, collections, random, math, sys

random.seed(20261012)
docs_data = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        docs_data[d['id']] = d

FWD = {'BEFORE': 'BEFORE', 'CONTAINS': 'CONTAINS', 'OVERLAP': 'OVERLAP',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}
LABELS = ['BEFORE', 'AFTER', 'CONTAINS', 'CONTAINED', 'OVERLAP', 'SIMULTANEOUS', 'NONE']
L2I = {l: i for i, l in enumerate(LABELS)}


def doc_pairs(doc):
    d = docs_data[doc]
    ev = {}
    for e in d['events']:
        s = [m['sent_id'] for m in e['mention'] if 'sent_id' in m]
        o = [m['offset'][0] for m in e['mention'] if 'offset' in m]
        if s:
            ev[e['id']] = {'t': e['type'], 'sent': min(s), 'off': min(o) if o else 0}
    R = {}
    for rel, ps in d['temporal_relations'].items():
        for h, t in ps:
            if h in ev and t in ev and rel in FWD:
                R[(h, t)] = FWD[rel]
    c2 = {}
    for kind, ps in d.get('causal_relations', {}).items():
        for h, t in ps:
            c2[(h, t)] = kind
    for h, t in d.get('subevent_relations', []):
        c2[(h, t)] = 'SUBEVENT'
    ids = sorted(ev, key=lambda i: (ev[i]['sent'], ev[i]['off']))
    out = []
    for i in range(len(ids)):
        for j in range(i+1, len(ids)):
            a, b = ids[i], ids[j]
            if (a, b) in R:
                y = R[(a, b)]
            elif (b, a) in R:
                y = {'BEFORE': 'AFTER', 'CONTAINS': 'CONTAINED'}.get(R[(b, a)], R[(b, a)])
            else:
                y = 'NONE'
            out.append((a, b, ev[a], ev[b], c2.get((a, b)), c2.get((b, a)), y))
    return out


def featurize(ea, eb, kf, kr):
    return [('sd', min(eb['sent']-ea['sent'], 5)), ('same', int(ea['sent'] == eb['sent'])),
            ('ta', ea['t']), ('tb', eb['t']), ('tp', ea['t']+'|'+eb['t']),
            ('kf', str(kf)), ('kr', str(kr)), ('kfta', str(kf)+'|'+ea['t']), ('bias', 1)]


docs = sorted(docs_data)
random.shuffle(docs)
cut = int(0.8*len(docs))
TR, TE = docs[:cut], docs[cut:]

W = collections.defaultdict(lambda: [0.0]*len(LABELS))
Wa = collections.defaultdict(lambda: [0.0]*len(LABELS))
c = 1
rows = []
for doc in TR:
    for a, b, ea, eb, kf, kr, y in doc_pairs(doc):
        rows.append((featurize(ea, eb, kf, kr), L2I[y]))
print('train %d mau' % len(rows), flush=True)


def score(fs):
    s = [0.0]*len(LABELS)
    for f in fs:
        w = W.get(f)
        if w:
            for i in range(len(LABELS)):
                s[i] += w[i]
    return s


for ep in range(3):
    random.shuffle(rows)
    for fs, g in rows:
        s = score(fs)
        pr = max(range(len(LABELS)), key=lambda i: s[i])
        if pr != g:
            for f in fs:
                W[f][g] += 1; W[f][pr] -= 1
                Wa[f][g] += c; Wa[f][pr] -= c
        c += 1
for f in W:
    for i in range(len(LABELS)):
        W[f][i] -= Wa[f][i]/c
print('train xong', flush=True)


def decode(doc):
    pr = {}
    hard = {}
    for a, b, ea, eb, kf, kr, y in doc_pairs(doc):
        s = score(featurize(ea, eb, kf, kr))
        mx = max(s); ex = [math.exp(v-mx) for v in s]; Z = sum(ex)
        i = max(range(len(LABELS)), key=lambda k: s[k])
        pr[(a, b)] = (LABELS[i], ex[i]/Z, y)
        # RANG BUOC CUNG tu ngu nghia quan he
        if kf == 'SUBEVENT':
            hard[(a, b)] = 'CONTAINS'
        elif kr == 'SUBEVENT':
            hard[(a, b)] = 'CONTAINED'
        elif kf in ('CAUSE', 'PRECONDITION'):
            hard[(a, b)] = 'NOT_AFTER'
        elif kr in ('CAUSE', 'PRECONDITION'):
            hard[(a, b)] = 'NOT_BEFORE'
    return pr, hard


def violates_hard(p, h):
    if h is None:
        return False
    if h == 'NOT_AFTER' and p == 'AFTER':
        return True
    if h == 'NOT_BEFORE' and p == 'BEFORE':
        return True
    if h == 'CONTAINS' and p not in ('CONTAINS', 'SIMULTANEOUS'):
        return True
    if h == 'CONTAINED' and p not in ('CONTAINED', 'SIMULTANEOUS'):
        return True
    return False


def f1(pp):
    tp = fp = fn = 0
    for (a, b), (p, cf, y) in pp.items():
        if p != 'NONE' and y != 'NONE':
            if p == y: tp += 1
            else: fp += 1; fn += 1
        elif p != 'NONE': fp += 1
        elif y != 'NONE': fn += 1
    P = tp/max(tp+fp, 1); R = tp/max(tp+fn, 1)
    return P, R, 2*P*R/max(P+R, 1e-9)


def repair(pr, hard, mode):
    """mode='conf'  : go canh confidence thap nhat (EXP31)
       mode='hard'  : UU TIEN sua canh vi pham rang buoc CUNG -> gan theo rang buoc"""
    out = dict(pr)
    if mode == 'hard':
        for k, h in hard.items():
            if k not in out:
                continue
            p, cf, y = out[k]
            if violates_hard(p, h):
                # ap dat theo rang buoc cung
                newp = {'CONTAINS': 'CONTAINS', 'CONTAINED': 'CONTAINED',
                        'NOT_AFTER': 'BEFORE', 'NOT_BEFORE': 'AFTER'}[h]
                out[k] = (newp, 1.0, y)
    # pha chu trinh (chung cho ca hai)
    edges = {}
    for (a, b), (p, cf, y) in out.items():
        if p == 'BEFORE': edges[(a, b)] = cf
        elif p == 'AFTER': edges[(b, a)] = cf
    for (u, v) in list(edges):
        if (v, u) in edges:
            if edges[(u, v)] <= edges[(v, u)]: edges.pop((u, v), None)
            else: edges.pop((v, u), None)
    for _ in range(6):
        adj = collections.defaultdict(set)
        for (u, v) in edges: adj[u].add(v)
        color = {}; stack = []; found = []
        def dfs(u):
            color[u] = 1; stack.append(u)
            for v in list(adj[u]):
                if color.get(v, 0) == 1:
                    if v in stack: found.append(stack[stack.index(v):]+[v])
                elif color.get(v, 0) == 0: dfs(v)
            stack.pop(); color[u] = 2
        sys.setrecursionlimit(100000)
        for n in list(adj):
            if color.get(n, 0) == 0: dfs(n)
        if not found: break
        for cyc in found:
            ce = [(cyc[i], cyc[i+1]) for i in range(len(cyc)-1) if (cyc[i], cyc[i+1]) in edges]
            if ce: edges.pop(min(ce, key=lambda e: edges[e]), None)
    for (a, b) in list(out):
        p, cf, y = out[(a, b)]
        if p in ('BEFORE', 'AFTER'):
            if (a, b) in edges: out[(a, b)] = ('BEFORE', cf, y)
            elif (b, a) in edges: out[(a, b)] = ('AFTER', cf, y)
            else: out[(a, b)] = ('NONE', cf, y)
    return out


agg = collections.defaultdict(float)
nd = 0
nhard = 0
for doc in TE:
    pr, hard = decode(doc)
    if len(pr) < 3: continue
    nd += 1
    nhard += sum(1 for k, h in hard.items() if k in pr and violates_hard(pr[k][0], h))
    for nm, pp in (('goc', pr), ('sua-conf', repair(pr, hard, 'conf')),
                   ('sua-CUNG', repair(pr, hard, 'hard'))):
        P, R, F = f1(pp)
        agg[nm+'_P'] += P; agg[nm+'_R'] += R; agg[nm+'_F'] += F

print()
print('=' * 62)
print('SUA BANG RANG BUOC CUNG vs CONFIDENCE (%d document)' % nd)
print('=' * 62)
print('canh vi pham rang buoc CUNG trong output model: %d' % nhard)
print()
print('%-14s %10s %10s %10s' % ('', 'precision', 'recall', 'F1'))
print('-' * 48)
base = None
for nm in ('goc', 'sua-conf', 'sua-CUNG'):
    P, R, F = agg[nm+'_P']/nd, agg[nm+'_R']/nd, agg[nm+'_F']/nd
    d = '' if base is None else '  (%+.2f)' % (100*(F-base))
    print('%-14s %9.2f%% %9.2f%% %9.2f%%%s' % (nm, 100*P, 100*R, 100*F, d))
    if base is None: base = F
