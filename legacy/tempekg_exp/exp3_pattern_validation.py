"""EXP3 - Kiem chung dung y tuong "mine pattern DUNG roi tim contradiction".

Sua 2 loi cua EXP2:
  1. BO nhan NONE - chi xet cac cap THUC SU co quan he. Constraint mining khong
     du doan su ton tai cua quan he, no rang buoc quan he DA co.
  2. Bo argmax tren MOI signature. PaTeCon chi giu signature co confidence >= 0.9.
     Do la che do that su can danh gia.

Cau hoi chinh: signature dat conf >= theta tren MINE co GIU duoc conf do tren
EVAL khong? Do la dinh nghia "pattern dung", va la dieu kien de suy ra contradiction.
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
                roles = collections.defaultdict(set)
                ents = set()
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            ents.add(v['entity_id'])
                            roles[v['entity_id']].add(r)
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
MINE, EVAL = set(docs[:cut]), set(docs[cut:])

FWD = {'BEFORE': 'BEFORE_FWD', 'CONTAINS': 'CONTAINS_FWD', 'OVERLAP': 'OVERLAP_FWD',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}
REV = {'BEFORE': 'BEFORE_REV', 'CONTAINS': 'CONTAINS_REV', 'OVERLAP': 'OVERLAP_REV',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}


def rel_pairs(doc, require_share=1):
    """CHI sinh cac cap CO quan he (bo NONE)"""
    ev, R = arg[doc], rels[doc]
    ids = sorted(ev, key=lambda i: ev[i]['pos'])
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            shared = ev[a]['ents'] & ev[b]['ents']
            if len(shared) < require_share:
                continue
            if (a, b) in R:
                lab = FWD.get(R[(a, b)])
            elif (b, a) in R:
                lab = REV.get(R[(b, a)])
            else:
                continue
            if lab:
                yield a, b, shared, lab


def build(split_docs, require_share, level):
    sig = collections.defaultdict(collections.Counter)
    for doc in split_docs:
        ev = arg[doc]
        for a, b, shared, lab in rel_pairs(doc, require_share):
            Ta, Tb = ev[a]['type'], ev[b]['type']
            if level == 'type':
                sig[(Ta, Tb)][lab] += 1
            else:
                for x in shared:
                    for ra in sorted(ev[a]['roles'][x]):
                        for rb in sorted(ev[b]['roles'][x]):
                            sig[(Ta, ra, Tb, rb)][lab] += 1
    return sig


def run(level, require_share, MIN_SUP=10):
    mine_sig = build(MINE, require_share, level)
    eval_sig = build(EVAL, require_share, level)

    base = collections.Counter()
    for c in mine_sig.values():
        base.update(c)
    maj_lab, maj_n = base.most_common(1)[0]
    maj_rate = maj_n / sum(base.values())

    print('  baseline majority (%s) tren MINE = %.1f%%' % (maj_lab, 100 * maj_rate))

    for theta in (0.9, 0.8, 0.7):
        kept = []
        for s, c in mine_sig.items():
            n = sum(c.values())
            if n < MIN_SUP:
                continue
            lab, k = c.most_common(1)[0]
            if k / n >= theta:
                kept.append((s, lab, n, k / n))

        # kiem chung tren EVAL
        hit = tot = 0
        covered_sigs = 0
        for s, lab, n, conf in kept:
            c = eval_sig.get(s)
            if not c:
                continue
            covered_sigs += 1
            hit += c[lab]
            tot += sum(c.values())

        held = 100 * hit / tot if tot else float('nan')
        print('    theta=%.1f : %4d signature qua nguong | phu %6d cap tren EVAL '
              '| GIU duoc %.1f%%  (majority=%.1f%%, delta=%+.1f)'
              % (theta, len(kept), tot, held, 100 * maj_rate, held - 100 * maj_rate))


print('=== EXP3: pattern validation (bo NONE, loc theo confidence) ===')
print('docs MINE=%d EVAL=%d' % (len(MINE), len(EVAL)))
print()
for level in ('type', 'role'):
    for req in (1, 2):
        print('--- level=%s, chia se >=%d participant ---' % (level, req))
        run(level, req)
        print()
