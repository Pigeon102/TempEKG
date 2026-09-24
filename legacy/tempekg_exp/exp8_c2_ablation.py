"""EXP8 - Ablation: dieu kien theo KIEU EVENT co them gi so voi luat tran khong?

Nghi van: "CAUSE(a,b) => BEFORE(a,b)" gan nhu la dinh nghia. Neu luat tran nay
da dat ~96% thi 401 signature dieu kien theo type KHONG them gi, va dong gop
that chi con la DO LUONG chu khong phai MINING.

Thang do tang dan do chi tiet, danh gia tren CUNG mot tap cap EVAL:
  L0  majority              - bo qua tat ca
  L1  kind                  - chi CAUSE / PRECONDITION / SUBEVENT
  L2  kind + huong van ban  - them FWD/REV
  L3  kind + huong + 2 kieu event  - signature day du cua EXP6
"""
import json, zipfile, io, collections, random

random.seed(20261012)

arg = {}
z = zipfile.ZipFile('MAVEN-Arg.zip')
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            ev = {}
            for e in d['events']:
                offs = [m['offset'][0] for m in e['mention'] if m.get('offset')]
                ev[e['id']] = {'type': e['type'], 'pos': min(offs) if offs else 10**9}
            arg[d['id']] = ev

ere = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        ere[d['id']] = d

docs = sorted(set(arg) & set(ere))
random.shuffle(docs)
cut = int(0.8 * len(docs))
MINE, EVAL = docs[:cut], docs[cut:]

FWD = {'BEFORE': 'BEFORE_FWD', 'CONTAINS': 'CONTAINS_FWD', 'OVERLAP': 'OVERLAP_FWD',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}
REV = {'BEFORE': 'BEFORE_REV', 'CONTAINS': 'CONTAINS_REV', 'OVERLAP': 'OVERLAP_REV',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}


def rows_of(doc):
    """tra ve [(kind, direction, type_a, type_b, label)] cho moi canh C2 co nhan"""
    ev = arg[doc]
    d = ere[doc]
    R = {}
    for rel, ps in d['temporal_relations'].items():
        for h, t in ps:
            if h.startswith('EVENT') and t.startswith('EVENT'):
                R[(h, t)] = rel
    edges = []
    for kind, ps in d.get('causal_relations', {}).items():
        edges += [(h, t, kind) for h, t in ps]
    edges += [(h, t, 'SUBEVENT') for h, t in d.get('subevent_relations', [])]

    out = []
    for h, t, kind in edges:
        if h not in ev or t not in ev:
            continue
        if ev[h]['pos'] <= ev[t]['pos']:
            a, b, flip = h, t, False
        else:
            a, b, flip = t, h, True
        if (a, b) in R:
            lab = FWD.get(R[(a, b)])
        elif (b, a) in R:
            lab = REV.get(R[(b, a)])
        else:
            continue
        if lab:
            out.append((kind, 'REV' if flip else 'FWD', ev[a]['type'], ev[b]['type'], lab))
    return out


LEVELS = {
    'L0 majority': lambda k, dr, ta, tb: (),
    'L1 kind': lambda k, dr, ta, tb: (k,),
    'L2 kind+huong': lambda k, dr, ta, tb: (k, dr),
    'L3 kind+huong+types': lambda k, dr, ta, tb: (k, dr, ta, tb),
}

# ---- hoc tren MINE ----
models = {name: collections.defaultdict(collections.Counter) for name in LEVELS}
for doc in MINE:
    for k, dr, ta, tb, lab in rows_of(doc):
        for name, keyf in LEVELS.items():
            models[name][keyf(k, dr, ta, tb)][lab] += 1

MIN_SUP = 10
pred = {}
for name, m in models.items():
    pred[name] = {key: c.most_common(1)[0][0] for key, c in m.items()
                  if sum(c.values()) >= MIN_SUP}

# ---- danh gia tren CUNG tap cap EVAL ----
eval_rows = []
for doc in EVAL:
    eval_rows += rows_of(doc)

print('so cap C2 co nhan tren EVAL: %d' % len(eval_rows))
print()
print('%-22s %8s %8s %9s' % ('MUC', 'phu', 'acc', 'so key'))
print('-' * 52)
prev = None
for name, keyf in LEVELS.items():
    hit = cov = 0
    for k, dr, ta, tb, lab in eval_rows:
        key = keyf(k, dr, ta, tb)
        if key in pred[name]:
            cov += 1
            hit += (pred[name][key] == lab)
    acc = 100 * hit / cov if cov else float('nan')
    delta = '' if prev is None else ('  (%+.1f so voi muc tren)' % (acc - prev))
    print('%-22s %8d %7.1f%% %9d%s' % (name, cov, acc, len(pred[name]), delta))
    prev = acc

# ---- chi tiet tung kind ----
print()
print('=== CHI TIET: luat tran theo tung kind (hoc tren MINE) ===')
m1 = models['L1 kind']
for key, c in sorted(m1.items()):
    n = sum(c.values())
    lab, k = c.most_common(1)[0]
    print('  %-14s n=%-6d  luat: -> %-14s conf=%.1f%%'
          % (key[0], n, lab, 100 * k / n))
    print('      phan bo: %s' % dict(c.most_common(4)))

print()
print('=== CHI TIET: L3 vs L1 tren tung kind (EVAL) ===')
for kind in ('CAUSE', 'PRECONDITION', 'SUBEVENT'):
    sub = [r for r in eval_rows if r[0] == kind]
    if not sub:
        continue
    h1 = c1 = h3 = c3 = 0
    for k, dr, ta, tb, lab in sub:
        if (k,) in pred['L1 kind']:
            c1 += 1; h1 += (pred['L1 kind'][(k,)] == lab)
        key3 = (k, dr, ta, tb)
        if key3 in pred['L3 kind+huong+types']:
            c3 += 1; h3 += (pred['L3 kind+huong+types'][key3] == lab)
    a1 = 100*h1/c1 if c1 else float('nan')
    a3 = 100*h3/c3 if c3 else float('nan')
    print('  %-14s L1: %5.1f%% (phu %5d)   L3: %5.1f%% (phu %5d)   delta %+.1f'
          % (kind, a1, c1, a3, c3, a3 - a1))
