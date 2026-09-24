"""EXP2 - Kiem chung framework: pattern da mine co du doan duoc quan he thoi gian
khong, va co VUOT baseline tam thuong khong.

Giao thuc (event-level, khong phai edge-level):
  - Chia document 80/20 (MINE / EVAL), seed co dinh, chia THEO DOCUMENT.
  - Mine tren MINE: voi moi signature, phan phoi nhan quan he.
  - Danh gia tren EVAL: du doan nhan cho tung cap event.
  - So voi 2 baseline BAT BUOC:
        B1 majority  - luon doan nhan pho bien nhat
        B2 text-order- event co trigger xuat hien truoc thi BEFORE

Nhan (cho cap (a,b) da sap theo THU TU VAN BAN, a truoc b):
  BEFORE_FWD / BEFORE_REV / CONTAINS_FWD / CONTAINS_REV
  SIMULTANEOUS / OVERLAP_FWD / OVERLAP_REV / NONE
"""
import json, zipfile, io, collections, random, math

random.seed(20261012)

# ---------- 1. Load MAVEN-Arg: event type, trigger offset, participants ----------
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
                roles = collections.defaultdict(set)
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            ents.add(v['entity_id'])
                            roles[v['entity_id']].add(r)
                ev[e['id']] = {
                    'type': e['type'],
                    'pos': min(offs) if offs else 10 ** 9,
                    'ents': ents,
                    'roles': roles,
                }
            arg[d['id']] = ev

# ---------- 2. Load MAVEN-ERE: quan he ----------
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
MINE, EVAL = set(docs[:cut]), set(docs[cut:])
print('docs: total=%d  MINE=%d  EVAL=%d' % (len(docs), len(MINE), len(EVAL)))


def label_of(R, a, b):
    """nhan cho cap da sap theo thu tu van ban (a truoc b)"""
    if (a, b) in R:
        r = R[(a, b)]
        return {'BEFORE': 'BEFORE_FWD', 'CONTAINS': 'CONTAINS_FWD',
                'OVERLAP': 'OVERLAP_FWD', 'SIMULTANEOUS': 'SIMULTANEOUS',
                'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}.get(r, 'NONE')
    if (b, a) in R:
        r = R[(b, a)]
        return {'BEFORE': 'BEFORE_REV', 'CONTAINS': 'CONTAINS_REV',
                'OVERLAP': 'OVERLAP_REV', 'SIMULTANEOUS': 'SIMULTANEOUS',
                'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}.get(r, 'NONE')
    return 'NONE'


def pairs_of(doc, require_share=1):
    """sinh cac cap event trong 1 doc, da sap theo thu tu van ban"""
    ev = arg[doc]
    R = rels[doc]
    ids = sorted(ev, key=lambda i: ev[i]['pos'])
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            shared = ev[a]['ents'] & ev[b]['ents']
            if len(shared) < require_share:
                continue
            yield a, b, shared, label_of(R, a, b)


# ---------- 3. Mine tren MINE ----------
sig_type = collections.defaultdict(collections.Counter)     # (Ta,Tb) -> label dist
sig_role = collections.defaultdict(collections.Counter)     # (Ta,ra,Tb,rb) -> label dist
overall = collections.Counter()

for doc in MINE:
    ev = arg[doc]
    for a, b, shared, lab in pairs_of(doc, 1):
        Ta, Tb = ev[a]['type'], ev[b]['type']
        sig_type[(Ta, Tb)][lab] += 1
        overall[lab] += 1
        for x in shared:
            for ra in sorted(ev[a]['roles'][x]):
                for rb in sorted(ev[b]['roles'][x]):
                    sig_role[(Ta, ra, Tb, rb)][lab] += 1

MAJ = overall.most_common(1)[0][0]
print('nhan pho bien nhat (B1 majority) = %s (%.1f%% tren MINE)'
      % (MAJ, 100 * overall[MAJ] / sum(overall.values())))
print('phan bo nhan tren MINE:', dict(overall.most_common()))
print()

MIN_SUP = 10


def predict(ev, a, b, shared):
    """uu tien signature role-level neu du support, roi den type-level, roi majority"""
    Ta, Tb = ev[a]['type'], ev[b]['type']
    best = None
    bestn = 0
    for x in shared:
        for ra in sorted(ev[a]['roles'][x]):
            for rb in sorted(ev[b]['roles'][x]):
                c = sig_role.get((Ta, ra, Tb, rb))
                if c and sum(c.values()) >= MIN_SUP and sum(c.values()) > bestn:
                    bestn = sum(c.values())
                    best = c.most_common(1)[0][0]
    if best:
        return best, 'role'
    c = sig_type.get((Ta, Tb))
    if c and sum(c.values()) >= MIN_SUP:
        return c.most_common(1)[0][0], 'type'
    return MAJ, 'backoff'


# ---------- 4. Danh gia tren EVAL ----------
def evaluate(require_share):
    n = 0
    hit_model = hit_maj = hit_text = 0
    src = collections.Counter()
    per_label = collections.defaultdict(lambda: [0, 0])
    for doc in EVAL:
        ev = arg[doc]
        for a, b, shared, gold in pairs_of(doc, require_share):
            n += 1
            p, s = predict(ev, a, b, shared)
            src[s] += 1
            hit_model += (p == gold)
            hit_maj += (MAJ == gold)
            hit_text += ('BEFORE_FWD' == gold)
            per_label[gold][1] += 1
            per_label[gold][0] += (p == gold)
    return n, hit_model, hit_maj, hit_text, src, per_label


print('=' * 62)
for req in (1, 2):
    n, hm, hj, ht, src, per_label = evaluate(req)
    if n == 0:
        continue
    tag = 'chia se >=%d participant' % req
    print('--- %s   (n=%d cap tren EVAL) ---' % (tag, n))
    print('  MODEL (pattern)   : %.1f%%' % (100 * hm / n))
    print('  B1 majority       : %.1f%%' % (100 * hj / n))
    print('  B2 text-order     : %.1f%%' % (100 * ht / n))
    delta = 100 * (hm - max(hj, ht)) / n
    print('  => vuot baseline manh nhat: %+.1f diem' % delta)
    print('  nguon du doan     :', dict(src))
    print('  accuracy theo nhan gold:')
    for lab, (c, t) in sorted(per_label.items(), key=lambda kv: -kv[1][1]):
        if t >= 20:
            print('      %-16s n=%-6d acc=%.1f%%' % (lab, t, 100 * c / t))
    print()
