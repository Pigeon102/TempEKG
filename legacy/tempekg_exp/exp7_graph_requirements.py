"""EXP7 - Do YEU CAU CAU TRUC truoc khi build graph.

Cau hoi: graph phai ho tro nhung truy van gi, va chi so nao la BAT BUOC?
Khong do cai nay thi build graph la doan mo.

Q1. Bac (degree): bao nhieu event / entity, bao nhieu entity / event?
Q2. Causal/subevent la CHUOI hay CAY? Sau bao nhieu?
Q3. Transitive closure cua subevent co them thong tin khong?
    -> neu co, BAT BUOC co adjacency; neu khong, bang canh la du
Q4. Event khong co participant chiem bao nhieu? (kenh C1 khong cham toi duoc)
Q5. Chi so K_2,2 (SP(c)) to co nao?
"""
import json, zipfile, io, collections, statistics

arg = {}
z = zipfile.ZipFile('MAVEN-Arg.zip')
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            ev = {}
            for e in d['events']:
                ents = set()
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            ents.add(v['entity_id'])
                ev[e['id']] = ents
            arg[d['id']] = ev

ere = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        ere[d['id']] = d

docs = sorted(set(arg) & set(ere))

# ---------- Q1 ----------
ev_per_ent, ent_per_ev = [], []
for doc in docs:
    ent2ev = collections.defaultdict(int)
    for eid, ents in arg[doc].items():
        ent_per_ev.append(len(ents))
        for x in ents:
            ent2ev[x] += 1
    ev_per_ent.extend(ent2ev.values())

print('=== Q1. BAC ===')
print('entity / event : mean=%.2f median=%d max=%d  | =0: %.1f%%'
      % (statistics.mean(ent_per_ev), statistics.median(ent_per_ev), max(ent_per_ev),
         100 * sum(1 for x in ent_per_ev if x == 0) / len(ent_per_ev)))
print('event / entity : mean=%.2f median=%d max=%d'
      % (statistics.mean(ev_per_ent), statistics.median(ev_per_ent), max(ev_per_ent)))


# ---------- Q2/Q3 ----------
def topo(rel_getter, name):
    depths, n_edges, extra, multi_parent = [], 0, 0, 0
    for doc in docs:
        edges = rel_getter(ere[doc])
        n_edges += len(edges)
        adj = collections.defaultdict(list)
        rev = collections.defaultdict(list)
        for h, t in edges:
            adj[h].append(t)
            rev[t].append(h)
        multi_parent += sum(1 for hs in rev.values() if len(hs) > 1)
        direct = {(h, t) for h, t in edges}
        clo = set()
        for src in list(adj):
            seen = {src}
            stack = [src]
            depth = {src: 0}
            while stack:
                u = stack.pop()
                for v in adj[u]:
                    if v not in seen:
                        seen.add(v)
                        depth[v] = depth[u] + 1
                        stack.append(v)
                        clo.add((src, v))
            if len(depth) > 1:
                depths.append(max(depth.values()))
        extra += len(clo - direct)
    print('--- %s ---' % name)
    print('  canh truc tiep        : %d' % n_edges)
    print('  canh THEM tu closure  : %d  (%.1f%% so voi truc tiep)'
          % (extra, 100 * extra / max(n_edges, 1)))
    if depths:
        print('  do sau chuoi          : mean=%.2f median=%d max=%d'
              % (statistics.mean(depths), statistics.median(depths), max(depths)))
        print('  chuoi sau >=2         : %.1f%%'
              % (100 * sum(1 for x in depths if x >= 2) / len(depths)))
    print('  node co >1 cha (khong phai cay): %d' % multi_parent)


print()
print('=== Q2/Q3. TOPO CAUSAL & SUBEVENT ===')
topo(lambda d: [tuple(p) for ps in d.get('causal_relations', {}).values() for p in ps],
     'CAUSAL (CAUSE + PRECONDITION)')
topo(lambda d: [tuple(p) for p in d.get('subevent_relations', [])], 'SUBEVENT')

# ---------- Q4 ----------
iso = tot = iso_with_rel = 0
for doc in docs:
    has_rel = set()
    for rel, ps in ere[doc]['temporal_relations'].items():
        for h, t in ps:
            has_rel.add(h)
            has_rel.add(t)
    for eid, ents in arg[doc].items():
        tot += 1
        if not ents:
            iso += 1
            if eid in has_rel:
                iso_with_rel += 1

print()
print('=== Q4. EVENT KHONG CO PARTICIPANT ===')
print('tong event                     : %d' % tot)
print('khong co participant nao       : %d (%.1f%%)' % (iso, 100 * iso / tot))
print('  ...nhung VAN co quan he t/g  : %d' % iso_with_rel)
print('  => kenh C1 KHONG THE cham toi nhung event nay')

# ---------- Q5 ----------
k1 = k2 = 0
share = collections.Counter()
for doc in docs:
    ev = arg[doc]
    ids = [e for e in ev if ev[e]]
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            s = len(ev[ids[i]] & ev[ids[j]])
            if s >= 1:
                k1 += 1
                share[min(s, 5)] += 1
            if s >= 2:
                k2 += 1

print()
print('=== Q5. KICH THUOC INDEX DONG-THAM-DU ===')
print('cap k>=1 : %d' % k1)
print('cap k>=2 : %d (%.1f%%)' % (k2, 100 * k2 / max(k1, 1)))
print('phan bo so participant chung:', dict(sorted(share.items())))
