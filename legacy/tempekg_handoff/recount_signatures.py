"""Recompute type-level mining power with pairs deduplicated ACROSS entities.

Earlier counts reset the dedup set per entity, inflating support for any event pair
that shares more than one participant (19.8% of pairs).
"""
import json, zipfile, io, collections, os

os.chdir(r'C:/Reseach_Quang')

rel_of = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        ev = {e['id'] for e in d['events']}
        for rel, ps in d['temporal_relations'].items():
            for h, t in ps:
                if h in ev and t in ev:
                    rel_of[(d['id'],) + tuple(sorted([h, t]))] = rel

z = zipfile.ZipFile('MAVEN-Arg.zip')
pair_typesig = collections.Counter()
full_sig = collections.Counter()

for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            doc = d['id']
            etype = {e['id']: e['type'] for e in d['events']}
            ent2ev = collections.defaultdict(set)
            roles = collections.defaultdict(set)   # (event, entity) -> roles
            for e in d['events']:
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            ent2ev[v['entity_id']].add(e['id'])
                            roles[(e['id'], v['entity_id'])].add(r)

            seen_pairs = set()                      # <-- deduped ACROSS entities
            seen_sigs = set()
            for ent, evs in ent2ev.items():
                evs = sorted(evs)
                for i in range(len(evs)):
                    for j in range(i + 1, len(evs)):
                        a, b = evs[i], evs[j]
                        key = (doc, a, b)
                        if key not in rel_of:
                            continue
                        if key not in seen_pairs:
                            seen_pairs.add(key)
                            pair_typesig[(etype[a], etype[b])] += 1
                        # role signature is entity-specific, dedup on (pair, roles)
                        for ra in sorted(roles[(a, ent)]):
                            for rb in sorted(roles[(b, ent)]):
                                sk = (doc, a, b, ra, rb)
                                if sk in seen_sigs:
                                    continue
                                seen_sigs.add(sk)
                                full_sig[(etype[a], ra, etype[b], rb)] += 1


def tally(c, name, old_at_10):
    tot = sum(c.values())
    print('  %s  (total instances %d, distinct %d)' % (name, tot, len(c)))
    for th in (5, 10, 25, 50):
        n = sum(1 for v in c.values() if v >= th)
        cov = sum(v for v in c.values() if v >= th)
        mark = '   <-- OLD said %s' % old_at_10 if th == 10 else ''
        print('    >=%-3d : %5d signatures, %7d instances (%.0f%%)%s'
              % (th, n, cov, 100 * cov / tot, mark))


print('CORRECTED mining power (pairs deduped across entities):')
print()
tally(pair_typesig, '(T1,T2) type pairs', '2,708')
print()
tally(full_sig, '(T1,r1,T2,r2) role signatures', '2,688')
