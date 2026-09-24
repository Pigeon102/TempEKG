"""EXP31 - MUC C: model TRE + tang sua rang buoc tren MAVEN.

Muc tieu: gold co 72 conflict; do thi DU DOAN co 85,243 vi pham bac cau.
Cau hoi: dung rang buoc de SUA output model co tang F1 khong?

Pipeline:
  1. Train classifier quan he thoi gian (dac trung, khong can GPU)
  2. Decode DOC LAP tung cap  -> do thi KHONG nhat quan
  3. Do vi pham: doi xung, chu trinh, bac cau
  4. Tang SUA: closure + pha chu trinh theo confidence thap nhat
  5. Do F1 TRUOC/SAU sua
"""
import json, collections, random, math, sys

random.seed(20261012)

# ---------------- 1. DU LIEU ----------------
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
            kind = c2.get((a, b)) or c2.get((b, a))
            rev = (b, a) in c2
            out.append((a, b, ev[a], ev[b], kind, rev, y))
    return out


def featurize(ea, eb, kind, rev):
    """dac trung roi rac -> chi so"""
    f = []
    f.append(('sd', min(eb['sent'] - ea['sent'], 5)))
    f.append(('same_sent', int(ea['sent'] == eb['sent'])))
    f.append(('ta', ea['t']))
    f.append(('tb', eb['t']))
    f.append(('tpair', ea['t'] + '|' + eb['t']))
    f.append(('kind', str(kind) + ('_R' if rev else '_F')))
    f.append(('kind_ta', str(kind) + '|' + ea['t']))
    f.append(('bias', 1))
    return f


# ---------------- 2. TRAIN ----------------
docs = sorted(docs_data)
random.shuffle(docs)
cut = int(0.8 * len(docs))
TR, TE = docs[:cut], docs[cut:]
print('doc train %d | test %d' % (len(TR), len(TE)), flush=True)

# perceptron trung binh (nhanh, khong can thu vien)
W = collections.defaultdict(lambda: [0.0]*len(LABELS))
Wa = collections.defaultdict(lambda: [0.0]*len(LABELS))
c = 1


def score(feats):
    s = [0.0]*len(LABELS)
    for f in feats:
        w = W.get(f)
        if w:
            for i in range(len(LABELS)):
                s[i] += w[i]
    return s


train_rows = []
for doc in TR:
    for a, b, ea, eb, kind, rev, y in doc_pairs(doc):
        train_rows.append((featurize(ea, eb, kind, rev), L2I[y]))
print('mau train: %d' % len(train_rows), flush=True)

for ep in range(3):
    random.shuffle(train_rows)
    err = 0
    for feats, gold in train_rows:
        s = score(feats)
        pred = max(range(len(LABELS)), key=lambda i: s[i])
        if pred != gold:
            err += 1
            for f in feats:
                W[f][gold] += 1.0
                W[f][pred] -= 1.0
                Wa[f][gold] += c
                Wa[f][pred] -= c
        c += 1
    print('  epoch %d: loi %.1f%%' % (ep+1, 100*err/len(train_rows)), flush=True)
for f in W:
    for i in range(len(LABELS)):
        W[f][i] -= Wa[f][i]/c

# ---------------- 3. DECODE DOC LAP ----------------
INV = {'BEFORE': 'AFTER', 'AFTER': 'BEFORE', 'CONTAINS': 'CONTAINED',
       'CONTAINED': 'CONTAINS', 'OVERLAP': 'OVERLAP',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'NONE': 'NONE'}


def decode(doc):
    preds = {}
    for a, b, ea, eb, kind, rev, y in doc_pairs(doc):
        s = score(featurize(ea, eb, kind, rev))
        mx = max(s)
        ex = [math.exp(v-mx) for v in s]
        Z = sum(ex)
        i = max(range(len(LABELS)), key=lambda k: s[k])
        preds[(a, b)] = (LABELS[i], ex[i]/Z, y)
    return preds


def violations(preds):
    bef = {(a, b) for (a, b), (p, _, _) in preds.items() if p == 'BEFORE'}
    bef |= {(b, a) for (a, b), (p, _, _) in preds.items() if p == 'AFTER'}
    sym = sum(1 for (u, v) in bef if (v, u) in bef)
    adj = collections.defaultdict(set)
    for u, v in bef:
        adj[u].add(v)
    trans = 0
    for u in adj:
        for v in adj[u]:
            for w in adj.get(v, ()):
                if w != u and (u, w) not in bef:
                    trans += 1
    color = {}
    cyc = [0]

    def dfs(u):
        color[u] = 1
        for v in adj[u]:
            if color.get(v, 0) == 1:
                cyc[0] += 1
            elif color.get(v, 0) == 0:
                dfs(v)
        color[u] = 2
    sys.setrecursionlimit(100000)
    for n in list(adj):
        if color.get(n, 0) == 0:
            dfs(n)
    return sym, cyc[0], trans, len(bef)


def f1(preds):
    tp = fp = fn = 0
    for (a, b), (p, cf, y) in preds.items():
        if p != 'NONE' and y != 'NONE':
            if p == y:
                tp += 1
            else:
                fp += 1; fn += 1
        elif p != 'NONE':
            fp += 1
        elif y != 'NONE':
            fn += 1
    P = tp/max(tp+fp, 1); R = tp/max(tp+fn, 1)
    return P, R, 2*P*R/max(P+R, 1e-9)


# ---------------- 4. TANG SUA ----------------
def repair(preds):
    """pha chu trinh: bo canh BEFORE co confidence THAP NHAT trong chu trinh,
       roi ap closure de bo sung canh bac cau con thieu."""
    out = dict(preds)
    edges = {}
    for (a, b), (p, cf, y) in preds.items():
        if p == 'BEFORE':
            edges[(a, b)] = cf
        elif p == 'AFTER':
            edges[(b, a)] = cf
    # 1. doi xung: giu canh confidence cao hon
    for (u, v) in list(edges):
        if (v, u) in edges:
            if edges[(u, v)] <= edges[(v, u)]:
                edges.pop((u, v), None)
            else:
                edges.pop((v, u), None)
    # 2. pha chu trinh tham lam
    for _ in range(6):
        adj = collections.defaultdict(set)
        for (u, v) in edges:
            adj[u].add(v)
        color = {}; stack = []; found = []

        def dfs(u):
            color[u] = 1; stack.append(u)
            for v in list(adj[u]):
                if color.get(v, 0) == 1:
                    i = stack.index(v) if v in stack else 0
                    found.append(stack[i:] + [v])
                elif color.get(v, 0) == 0:
                    dfs(v)
            stack.pop(); color[u] = 2
        for n in list(adj):
            if color.get(n, 0) == 0:
                dfs(n)
        if not found:
            break
        for cyc in found:
            ce = [(cyc[i], cyc[i+1]) for i in range(len(cyc)-1) if (cyc[i], cyc[i+1]) in edges]
            if ce:
                worst = min(ce, key=lambda e: edges[e])
                edges.pop(worst, None)
    # 3. ghi lai
    for (a, b) in preds:
        p, cf, y = preds[(a, b)]
        if p in ('BEFORE', 'AFTER'):
            if (a, b) in edges:
                out[(a, b)] = ('BEFORE', cf, y)
            elif (b, a) in edges:
                out[(a, b)] = ('AFTER', cf, y)
            else:
                out[(a, b)] = ('NONE', cf, y)
    return out


print()
print('=' * 74)
tot = collections.Counter()
sumP = collections.defaultdict(float)
nd = 0
for doc in TE:
    pr = decode(doc)
    if len(pr) < 3:
        continue
    nd += 1
    s, c_, t, ne = violations(pr)
    tot['sym_before'] += s; tot['cyc_before'] += c_; tot['trans_before'] += t; tot['edges'] += ne
    rp = repair(pr)
    s2, c2_, t2, ne2 = violations(rp)
    tot['sym_after'] += s2; tot['cyc_after'] += c2_; tot['trans_after'] += t2
    for nm, pp in (('before', pr), ('after', rp)):
        P, R, F = f1(pp)
        sumP[nm+'_P'] += P; sumP[nm+'_R'] += R; sumP[nm+'_F'] += F

print('MUC C: vi pham rang buoc tren do thi DU DOAN (%d document test)' % nd)
print('=' * 74)
print('%-24s %14s %14s' % ('', 'TRUOC sua', 'SAU sua'))
print('-' * 56)
print('%-24s %14d %14d' % ('canh BEFORE', tot['edges'], tot['edges']))
print('%-24s %14d %14d' % ('vi pham doi xung', tot['sym_before'], tot['sym_after']))
print('%-24s %14d %14d' % ('chu trinh', tot['cyc_before'], tot['cyc_after']))
print('%-24s %14d %14d' % ('thieu bac cau', tot['trans_before'], tot['trans_after']))
print()
print('%-24s %14s %14s' % ('F1 quan he thoi gian', 'TRUOC', 'SAU'))
print('-' * 56)
for m in ('P', 'R', 'F'):
    nmm = {'P': 'precision', 'R': 'recall', 'F': 'F1'}[m]
    b = sumP['before_'+m]/nd; a = sumP['after_'+m]/nd
    print('%-24s %13.2f%% %13.2f%%   (%+.2f)' % (nmm, 100*b, 100*a, 100*(a-b)))
