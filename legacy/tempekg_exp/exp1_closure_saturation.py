"""EXP1 - Kiem chung loi cua T3 phien ban edge-level holdout.

Gia thuyet can kiem chung: vi gold da transitively closed 100%, giau mot canh BEFORE
ngau nhien thi closure tren phan con lai VAN suy ra duoc no => baseline bao hoa,
constraint da mine dong gop ~0 do duoc.

Neu ty le khoi phuc bang closure cao (>80%), edge-level holdout la VO NGHIA
va phai chuyen sang event-level holdout (EXP2).
"""
import json, collections, random

random.seed(20261012)

tot_hidden = 0
recovered = 0
per_doc = []

for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        ev = {e['id'] for e in d['events']}
        before = [(h, t) for h, t in d['temporal_relations'].get('BEFORE', [])
                  if h in ev and t in ev]
        if len(before) < 5:
            continue

        # giau 10% canh (toi thieu 1)
        k = max(1, len(before) // 10)
        hidden = set(random.sample(before, k))
        kept = [e for e in before if e not in hidden]

        adj = collections.defaultdict(set)
        for h, t in kept:
            adj[h].add(t)

        def reachable(src, dst):
            """co duong src -> dst trong do thi con lai khong"""
            seen = {src}
            stack = [src]
            while stack:
                u = stack.pop()
                if u == dst:
                    return True
                for v in adj[u]:
                    if v not in seen:
                        seen.add(v)
                        stack.append(v)
            return False

        r = sum(1 for h, t in hidden if reachable(h, t))
        tot_hidden += len(hidden)
        recovered += r
        per_doc.append(r / len(hidden))

print('=== EXP1: closure saturation tren edge-level holdout ===')
print('so canh BEFORE bi giau      :', tot_hidden)
print('khoi phuc duoc bang CLOSURE :', recovered)
print('ty le                        : %.1f%%' % (100 * recovered / tot_hidden))
print()
import statistics
print('trung binh theo document     : %.1f%%' % (100 * statistics.mean(per_doc)))
print()
if recovered / tot_hidden > 0.8:
    print('=> KET LUAN: edge-level holdout BAO HOA. T3 ban dau VO NGHIA.')
    print('   Phai dung event-level holdout (EXP2).')
else:
    print('=> KET LUAN: edge-level holdout van con cho cho constraint dong gop.')
