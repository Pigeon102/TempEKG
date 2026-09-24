"""Check the two headline denominators the final plan puts in the abstract."""
import json, zipfile, io, collections, os

os.chdir(r'C:/Reseach_Quang')

# ---- MAVEN-ERE: unique event-event temporally related pairs ----
ee_pairs = set()
before_all = 0
ere_events = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        ev = {e['id'] for e in d['events']}
        ere_events[d['id']] = ev
        for rel, ps in d['temporal_relations'].items():
            for h, t in ps:
                if rel == 'BEFORE':
                    before_all += 1
                if h.startswith('EVENT') and t.startswith('EVENT'):
                    ee_pairs.add((d['id'],) + tuple(sorted([h, t])))

print('BEFORE relation instances (ALL endpoint kinds, incl. TIMEX):', before_all)
print('UNIQUE event-event temporally related pairs               :', len(ee_pairs))

# ---- MAVEN-Arg: shared-participant pairs that also carry a temporal relation ----
z = zipfile.ZipFile('MAVEN-Arg.zip')
shared_with_rel = set()
arity0_with_rel = 0
events_with_rel = collections.Counter()
for (doc, a, b) in ee_pairs:
    events_with_rel[(doc, a)] += 1
    events_with_rel[(doc, b)] += 1

for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            doc = d['id']
            ent2ev = collections.defaultdict(set)
            arity = {}
            for e in d['events']:
                n = 0
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        n += 1
                        if 'entity_id' in v:
                            ent2ev[v['entity_id']].add(e['id'])
                arity[e['id']] = n
            for ent, evs in ent2ev.items():
                evs = sorted(evs)
                for i in range(len(evs)):
                    for j in range(i + 1, len(evs)):
                        key = (doc, evs[i], evs[j])
                        if key in ee_pairs:
                            shared_with_rel.add(key)
            for eid, n in arity.items():
                if n == 0 and events_with_rel.get((doc, eid), 0) > 0:
                    arity0_with_rel += 1

print()
print('shared-participant pairs WITH a temporal relation         :', len(shared_with_rel))
print()
print('PLAN CLAIM   : 139,093 / 843,808 = 16.5%')
print('CORRECT      : %d / %d = %.1f%%  (denominator must be event-event pairs,'
      % (len(shared_with_rel), len(ee_pairs), 100 * len(shared_with_rel) / len(ee_pairs)))
print('               not BEFORE instances, which include TIMEX endpoints)')
print()
print('PLAN CLAIM   : 3,649 (5.4%) arity-0 ERE events carrying temporal relations')
print('MEASURED     : %d events with 0 arguments that carry >=1 event-event temporal relation' % arity0_with_rel)
