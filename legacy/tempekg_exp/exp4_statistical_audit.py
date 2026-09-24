"""EXP4 - Audit thong ke ket qua EXP3 truoc khi tin vao no.

Ba nghi van ma mo hinh toan chi ra:
  A. SUPPORT THAP: conf>=0.9 tai support=10 nghia la 9/10. Wilson CI 95% cua no
     rong den muc nao? Bao nhieu signature "qua nguong" thuc chat la nhieu?
  B. MULTIPLE TESTING: test ~12,000 signature, 403 qua nguong. Neu nhan la ngau
     nhien thi bao nhieu cai qua nguong do MAY RUI? -> permutation null.
  C. PHU THUOC TRONG DOCUMENT: cac cap trong cung 1 document KHONG doc lap.
     1 bai viet 30 event sinh ~400 cap tuong quan. Effective sample size << n.
     -> dem support theo DOCUMENT thay vi theo CAP.
"""
import json, zipfile, io, collections, random, math

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
                roles = collections.defaultdict(set)
                ents = set()
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            ents.add(v['entity_id']); roles[v['entity_id']].add(r)
                ev[e['id']] = {'type': e['type'], 'pos': min(offs) if offs else 10**9,
                               'ents': ents, 'roles': roles}
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
    """sig -> Counter(label);  sig -> set(doc)  de dem support theo document"""
    sig = collections.defaultdict(collections.Counter)
    sig_docs = collections.defaultdict(set)
    for doc in split_docs:
        ev = arg[doc]
        rows = list(rel_pairs(doc))
        if shuffle_labels and rows:
            labs = [r[2] for r in rows]
            random.shuffle(labs)                       # hoan vi TRONG document
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


mine_sig, mine_docs = collect(MINE)
eval_sig, _ = collect(EVAL)

THETA, MIN_SUP = 0.9, 10
passing = []
for s, c in mine_sig.items():
    n = sum(c.values())
    if n < MIN_SUP:
        continue
    lab, k = c.most_common(1)[0]
    if k / n >= THETA:
        passing.append((s, lab, n, k, len(mine_docs[s])))

print('=== A. SUPPORT & DO RONG KHOANG TIN CAY ===')
print('signature qua nguong (conf>=0.9, sup>=10):', len(passing))
sups = sorted(p[2] for p in passing)
print('support: min=%d  median=%d  max=%d' % (sups[0], sups[len(sups)//2], sups[-1]))
print('  so signature co support <= 15 :', sum(1 for x in sups if x <= 15),
      '(%.0f%%)' % (100*sum(1 for x in sups if x <= 15)/len(sups)))
print('  so signature co support <= 30 :', sum(1 for x in sups if x <= 30),
      '(%.0f%%)' % (100*sum(1 for x in sups if x <= 30)/len(sups)))
lo = [wilson_lo(k, n) for _, _, n, k, _ in passing]
print('Wilson 95%% lower bound cua conf: median=%.2f' % sorted(lo)[len(lo)//2])
print('  so signature co lower bound >= 0.9 :', sum(1 for x in lo if x >= 0.9))
print('  so signature co lower bound >= 0.7 :', sum(1 for x in lo if x >= 0.7))
print('  so signature co lower bound <  0.6 :', sum(1 for x in lo if x < 0.6))

print()
print('=== C. PHU THUOC TRONG DOCUMENT ===')
nd = sorted(p[4] for p in passing)
print('so DOCUMENT dong gop cho moi signature: min=%d median=%d max=%d'
      % (nd[0], nd[len(nd)//2], nd[-1]))
print('  signature chi den tu 1 document  :', sum(1 for x in nd if x == 1),
      '(%.0f%%)' % (100*sum(1 for x in nd if x == 1)/len(nd)))
print('  signature chi den tu <=3 document:', sum(1 for x in nd if x <= 3),
      '(%.0f%%)' % (100*sum(1 for x in nd if x <= 3)/len(nd)))
print('  => support theo CAP thoi phong so voi support theo DOCUMENT')

print()
print('=== B. PERMUTATION NULL (multiple testing) ===')
print('hoan vi nhan TRONG tung document, dem so signature van qua nguong:')
null_counts = []
for it in range(5):
    ns, _ = collect(MINE, shuffle_labels=True)
    cnt = 0
    for s, c in ns.items():
        n = sum(c.values())
        if n < MIN_SUP:
            continue
        if c.most_common(1)[0][1] / n >= THETA:
            cnt += 1
    null_counts.append(cnt)
    print('  lan %d: %d signature qua nguong duoi NULL' % (it + 1, cnt))
mean_null = sum(null_counts) / len(null_counts)
print()
print('quan sat that : %d' % len(passing))
print('ky vong NULL  : %.1f' % mean_null)
if mean_null > 0:
    print('=> FDR uoc luong ~ %.1f%%' % (100 * mean_null / len(passing)))
    print('=> so signature THAT (uoc luong) ~ %d' % (len(passing) - mean_null))

print()
print('=== D. MACRO vs MICRO tren EVAL ===')
micro_hit = micro_tot = 0
macro = []
for s, lab, n, k, ndoc in passing:
    c = eval_sig.get(s)
    if not c:
        continue
    t = sum(c.values())
    micro_hit += c[lab]; micro_tot += t
    macro.append(c[lab] / t)
print('micro (co trong so theo do phu) : %.1f%%' % (100 * micro_hit / micro_tot))
print('macro (trung binh tren signature): %.1f%%' % (100 * sum(macro) / len(macro)))
print('so signature xuat hien lai tren EVAL: %d / %d' % (len(macro), len(passing)))
