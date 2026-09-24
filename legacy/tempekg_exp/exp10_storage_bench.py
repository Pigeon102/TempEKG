"""EXP10 - Benchmark 3 thiet ke luu tru: thoi gian build, bo nho, thoi gian mining,
va INCREMENTAL (them document moi thi ton bao nhieu).

Dong co: goal doi hoi "luu tru toi uu", "data moi thi sao", "tiet kiem thoi gian".
EXP7 da cho biet cau truc can gi: bac TB 1.11, causal/subevent phang (do sau 1),
closure them 0.2-0.5% -> KHONG can adjacency, bang phang la du.

S1 on-the-fly   : khong cau truc, tinh giao tap moi lan (= code hien tai EXP2-9)
S2 inverted idx : entity -> [event], build 1 lan, mining duyet index
S3 materialized : bang cap (pair) da tinh san kem signature key

Do:
  build_time      - dung structure tu raw
  mem_entries     - so muc luu (uoc luong bo nho)
  mining_time     - 1 luot mining day du (dem phan phoi nhan theo signature)
  incr_time       - them 1 document moi
"""
import json, zipfile, io, collections, time, sys, random

random.seed(20261012)

# ---------- load raw 1 lan (khong tinh vao benchmark) ----------
raw = {}
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
            raw[d['id']] = ev

lab_of = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        R = {}
        for rel, ps in d['temporal_relations'].items():
            for h, t in ps:
                if h.startswith('EVENT') and t.startswith('EVENT'):
                    R[(h, t)] = rel
        lab_of[d['id']] = R

docs = sorted(set(raw) & set(lab_of))
HOLD = docs[-50:]              # 50 doc de test incremental
BASE = docs[:-50]
print('doc base=%d  doc giu lai cho incremental=%d' % (len(BASE), len(HOLD)))
print()


def label(doc, a, b):
    R = lab_of[doc]
    if (a, b) in R:
        return 'F_' + R[(a, b)]
    if (b, a) in R:
        return 'R_' + R[(b, a)]
    return None


# ================= S1: on-the-fly =================
def s1_build(doclist):
    return {'docs': doclist}          # khong lam gi


def s1_mine(store):
    sig = collections.defaultdict(collections.Counter)
    for doc in store['docs']:
        ev = raw[doc]
        ids = sorted(ev, key=lambda i: ev[i]['pos'])
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                if not (ev[a]['ents'] & ev[b]['ents']):
                    continue
                l = label(doc, a, b)
                if l:
                    sig[(ev[a]['type'], ev[b]['type'])][l] += 1
    return sig


def s1_entries(store):
    return 0


def s1_incr(store, doc):
    store['docs'].append(doc)          # mining phai chay lai TOAN BO


# ================= S2: inverted index =================
def s2_build(doclist):
    idx = {}                            # doc -> {entity -> [event]}
    for doc in doclist:
        m = collections.defaultdict(list)
        for eid, e in raw[doc].items():
            for x in e['ents']:
                m[x].append(eid)
        idx[doc] = dict(m)
    return {'idx': idx}


def s2_mine(store):
    sig = collections.defaultdict(collections.Counter)
    for doc, m in store['idx'].items():
        ev = raw[doc]
        seen = set()
        for x, evs in m.items():
            if len(evs) < 2:
                continue
            evs = sorted(evs, key=lambda i: ev[i]['pos'])
            for i in range(len(evs)):
                for j in range(i + 1, len(evs)):
                    a, b = evs[i], evs[j]
                    if (a, b) in seen:
                        continue
                    seen.add((a, b))
                    l = label(doc, a, b)
                    if l:
                        sig[(ev[a]['type'], ev[b]['type'])][l] += 1
    return sig


def s2_entries(store):
    return sum(len(v) for m in store['idx'].values() for v in m.values())


def s2_incr(store, doc):
    m = collections.defaultdict(list)
    for eid, e in raw[doc].items():
        for x in e['ents']:
            m[x].append(eid)
    store['idx'][doc] = dict(m)         # chi them 1 doc


# ================= S3: materialized pair table =================
def s3_build(doclist):
    rows = []
    for doc in doclist:
        ev = raw[doc]
        m = collections.defaultdict(list)
        for eid, e in raw[doc].items():
            for x in e['ents']:
                m[x].append(eid)
        seen = set()
        for x, evs in m.items():
            if len(evs) < 2:
                continue
            evs = sorted(evs, key=lambda i: ev[i]['pos'])
            for i in range(len(evs)):
                for j in range(i + 1, len(evs)):
                    a, b = evs[i], evs[j]
                    if (a, b) in seen:
                        continue
                    seen.add((a, b))
                    l = label(doc, a, b)
                    if l:
                        rows.append(((ev[a]['type'], ev[b]['type']), l))
    return {'rows': rows}


def s3_mine(store):
    sig = collections.defaultdict(collections.Counter)
    for k, l in store['rows']:
        sig[k][l] += 1
    return sig


def s3_entries(store):
    return len(store['rows'])


def s3_incr(store, doc):
    ev = raw[doc]
    m = collections.defaultdict(list)
    for eid, e in ev.items():
        for x in e['ents']:
            m[x].append(eid)
    seen = set()
    for x, evs in m.items():
        if len(evs) < 2:
            continue
        evs = sorted(evs, key=lambda i: ev[i]['pos'])
        for i in range(len(evs)):
            for j in range(i + 1, len(evs)):
                a, b = evs[i], evs[j]
                if (a, b) in seen:
                    continue
                seen.add((a, b))
                l = label(doc, a, b)
                if l:
                    store['rows'].append(((ev[a]['type'], ev[b]['type']), l))


SCHEMES = [
    ('S1 on-the-fly', s1_build, s1_mine, s1_entries, s1_incr),
    ('S2 inverted-index', s2_build, s2_mine, s2_entries, s2_incr),
    ('S3 materialized-pairs', s3_build, s3_mine, s3_entries, s3_incr),
]

print('%-24s %10s %12s %11s %14s %10s' %
      ('THIET KE', 'build(s)', 'muc luu', 'mining(s)', 'incr 50doc(s)', 'tong sig'))
print('-' * 88)

results = {}
for name, build, mine, entries, incr in SCHEMES:
    t0 = time.perf_counter()
    store = build(list(BASE))
    t_build = time.perf_counter() - t0

    t0 = time.perf_counter()
    sig = mine(store)
    t_mine = time.perf_counter() - t0

    n_entries = entries(store)

    # incremental: them 50 doc, roi mining lai (do TONG chi phi cap nhat)
    t0 = time.perf_counter()
    for doc in HOLD:
        incr(store, doc)
    sig2 = mine(store)
    t_incr = time.perf_counter() - t0

    results[name] = (t_build, n_entries, t_mine, t_incr, len(sig2))
    print('%-24s %10.2f %12d %11.2f %14.2f %10d'
          % (name, t_build, n_entries, t_mine, t_incr, len(sig2)))

print()
print('=== KIEM TRA TINH DUNG DAN: 3 thiet ke phai cho CUNG ket qua ===')
outs = []
for name, build, mine, _, _ in SCHEMES:
    s = mine(build(list(BASE)))
    outs.append((name, {k: dict(v) for k, v in s.items()}))
ref_name, ref = outs[0]
for name, o in outs[1:]:
    same = (o == ref)
    print('  %-24s == %s ? %s' % (name, ref_name, 'DUNG' if same else '*** KHAC ***'))
    if not same:
        only_ref = set(ref) - set(o)
        only_o = set(o) - set(ref)
        print('      chi co trong ref: %d | chi co trong o: %d' % (len(only_ref), len(only_o)))

print()
print('=== INCREMENTAL: chi phi THEM 1 doc (khong mining lai) ===')
for name, build, mine, _, incr in SCHEMES:
    store = build(list(BASE))
    t0 = time.perf_counter()
    for doc in HOLD:
        incr(store, doc)
    dt = time.perf_counter() - t0
    print('  %-24s %.4f s cho 50 doc  = %.2f ms/doc' % (name, dt, 1000*dt/len(HOLD)))
