"""EXP5 - Ap dung QUY TAC CONSTRAINT DA SUA (suy ra tu EXP4) va kiem chung du doan.

Quy tac cu (PaTeCon mac dinh):      p_hat >= 0.9  AND  support >= 10
Quy tac moi (MODEL.md muc 6):       Wilson_lo(p_hat) >= theta
                                AND BH-FDR q <= 0.05
                                AND so document >= 5

DU DOAN CAN KIEM CHUNG: loc chat hon -> SO LUONG GIAM, DO CHINH XAC TREN EVAL TANG.
Neu do chinh xac KHONG tang, nghia la signature "that" va "may rui" khong phan biet
duoc bang thong ke -> phai doi huong.

Cung uoc luong lai FDR sau khi loc (permutation null tren quy tac moi).
"""
import json, zipfile, io, collections, random, math

random.seed(20261012)

# ---------- load ----------
arg = {}
z = zipfile.ZipFile('MAVEN-Arg.zip')
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            ev = {}
            for e in d['events']:
                offs = [m['offset'][0] for m in e['mention'] if m.get('offset')]
                ents = set()
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            ents.add(v['entity_id'])
                ev[e['id']] = {'type': e['type'], 'pos': min(offs) if offs else 10**9,
                               'ents': ents}
            arg[d['id']] = ev

rels = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        R = {}
        for rel, ps in d['temporal_relations'].items():
            for h, t in ps:
                if h.startswith('EVENT') and t.startswith('EVENT'):
                    R[(h, t)] = rel
        rels[d['id']] = R

docs = sorted(set(arg) & set(rels))
random.shuffle(docs)
cut = int(0.8 * len(docs))
MINE, EVAL = docs[:cut], docs[cut:]

FWD = {'BEFORE': 'BEFORE_FWD', 'CONTAINS': 'CONTAINS_FWD', 'OVERLAP': 'OVERLAP_FWD',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}
REV = {'BEFORE': 'BEFORE_REV', 'CONTAINS': 'CONTAINS_REV', 'OVERLAP': 'OVERLAP_REV',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}


def rel_pairs(doc):
    ev, R = arg[doc], rels[doc]
    ids = sorted(ev, key=lambda i: ev[i]['pos'])
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            if not (ev[a]['ents'] & ev[b]['ents']):
                continue
            if (a, b) in R:
                lab = FWD.get(R[(a, b)])
            elif (b, a) in R:
                lab = REV.get(R[(b, a)])
            else:
                continue
            if lab:
                yield a, b, lab


def collect(split_docs, shuffle_labels=False):
    sig = collections.defaultdict(collections.Counter)
    sig_docs = collections.defaultdict(set)
    for doc in split_docs:
        ev = arg[doc]
        rows = list(rel_pairs(doc))
        if shuffle_labels and rows:
            labs = [r[2] for r in rows]
            random.shuffle(labs)
            rows = [(a, b, l) for (a, b, _), l in zip(rows, labs)]
        for a, b, lab in rows:
            s = (ev[a]['type'], ev[b]['type'])
            sig[s][lab] += 1
            sig_docs[s].add(doc)
    return sig, sig_docs


def wilson_lo(k, n, z=1.96):
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - m) / d


def binom_sf(k, n, p):
    """P(X >= k | n, p) - exact, n nho nen re"""
    if k <= 0:
        return 1.0
    return sum(math.comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))


def bh(pvals, alpha=0.05):
    """Benjamini-Hochberg -> tra ve nguong p toi da duoc chap nhan"""
    m = len(pvals)
    sp = sorted(pvals)
    thr = 0.0
    for i, p in enumerate(sp, 1):
        if p <= i / m * alpha:
            thr = p
    return thr


mine_sig, mine_docs = collect(MINE)
eval_sig, _ = collect(EVAL)

base = collections.Counter()
for c in mine_sig.values():
    base.update(c)
BASE_RATE = {l: n / sum(base.values()) for l, n in base.items()}
print('ty le nen tren MINE:', {k: round(v, 3) for k, v in
                               sorted(BASE_RATE.items(), key=lambda kv: -kv[1])})
print()


def select(sig, sig_docs, rule, theta=0.9, min_sup=10, min_docs=5, alpha=0.05):
    cands = []
    for s, c in sig.items():
        n = sum(c.values())
        if n < min_sup:
            continue
        lab, k = c.most_common(1)[0]
        cands.append((s, lab, n, k, len(sig_docs[s])))

    if rule == 'old':
        return [(s, lab, n, k, nd) for s, lab, n, k, nd in cands if k / n >= theta]

    # rule == 'new'
    step1 = [(s, lab, n, k, nd) for s, lab, n, k, nd in cands
             if wilson_lo(k, n) >= theta and nd >= min_docs]
    if not step1:
        return []
    pv = [binom_sf(k, n, BASE_RATE.get(lab, 0.5)) for _, lab, n, k, _ in step1]
    thr = bh(pv, alpha)
    return [x for x, p in zip(step1, pv) if p <= thr]


def evaluate(sel):
    hit = tot = 0
    macro = []
    for s, lab, n, k, nd in sel:
        c = eval_sig.get(s)
        if not c:
            continue
        t = sum(c.values())
        hit += c[lab]; tot += t
        macro.append(c[lab] / t)
    if tot == 0:
        return 0, 0, float('nan'), float('nan')
    return len(sel), tot, 100 * hit / tot, 100 * sum(macro) / len(macro)


print('=' * 70)
for theta in (0.9, 0.8, 0.7):
    print('theta = %.1f' % theta)
    for rule in ('old', 'new'):
        sel = select(mine_sig, mine_docs, rule, theta=theta)
        nsig, cov, micro, macro = evaluate(sel)
        print('  %-4s: %4d signature | phu %5d cap EVAL | micro %.1f%% | macro %.1f%%'
              % (rule.upper(), nsig, cov, micro, macro))
    print()

print('=' * 70)
print('FDR sau khi ap dung quy tac MOI (permutation null, theta=0.9):')
real = len(select(mine_sig, mine_docs, 'new', theta=0.9))
nulls = []
for it in range(5):
    ns, nd_ = collect(MINE, shuffle_labels=True)
    nulls.append(len(select(ns, nd_, 'new', theta=0.9)))
    print('  lan %d: %d' % (it + 1, nulls[-1]))
mn = sum(nulls) / len(nulls)
print()
print('quan sat that : %d' % real)
print('ky vong NULL  : %.1f' % mn)
print('FDR uoc luong : %.1f%%  (truoc khi sua: 34.7%%)' % (100 * mn / real if real else float('nan')))
