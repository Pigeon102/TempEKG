"""Recount shared-participant event pairs WITHOUT the per-entity double-count bug.

The earlier count reset its dedup set inside the per-entity loop, so an event pair
sharing two or more participants was counted once per shared entity.
"""
import json, zipfile, io, collections, os

os.chdir(r'C:/Reseach_Quang')

ee_pairs = set()
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        ev = {e['id'] for e in d['events']}
        for rel, ps in d['temporal_relations'].items():
            for h, t in ps:
                if h in ev and t in ev:
                    ee_pairs.add((d['id'],) + tuple(sorted([h, t])))

z = zipfile.ZipFile('MAVEN-Arg.zip')
uniq_shared = set()
inflated = 0
share_count = collections.Counter()
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            doc = d['id']
            ent2ev = collections.defaultdict(set)
            for e in d['events']:
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            ent2ev[v['entity_id']].add(e['id'])
            for ent, evs in ent2ev.items():
                evs = sorted(evs)
                for i in range(len(evs)):
                    for j in range(i + 1, len(evs)):
                        key = (doc, evs[i], evs[j])
                        uniq_shared.add(key)
                        share_count[key] += 1
                        inflated += 1

with_rel = {k for k in uniq_shared if k in ee_pairs}
multi = sum(1 for v in share_count.values() if v > 1)

print('OLD (double-counted) shared-participant pairs :', inflated)
print('CORRECT unique shared-participant pairs       :', len(uniq_shared))
print('  of which share >1 participant               :', multi,
      '(%.1f%%)' % (100 * multi / len(uniq_shared)))
print()
print('OLD (double-counted) with temporal relation   : 139093')
print('CORRECT unique with temporal relation         :', len(with_rel))
print('  as %% of unique shared-participant pairs    : %.1f%%'
      % (100 * len(with_rel) / len(uniq_shared)))
print()
print('unique event-event temporally related pairs   :', len(ee_pairs))
print('reachability ceiling  = %d / %d = %.1f%%'
      % (len(with_rel), len(ee_pairs), 100 * len(with_rel) / len(ee_pairs)))
