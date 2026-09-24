"""EXP23 - T4 DISJOINTNESS mo rong: hai nhanh PaTeCon TU KHAI BAO BO.

Trich §2.3: "the disjointness between a pair of time intervals with DIFFERENT PROPERTIES
             is trivial, so we only consider the case of the same property"
Trich §2.4: "to keep the search manageable, we DO NOT extract the disjointness
             relationships between DIFFERENT SUBJECTS"

  T4a KHAC PROPERTY : cung entity, hai event KHAC LOAI, khoang chong nhau
  T4b KHAC CHU THE  : hai entity khac nhau, cung vai trong cung loai event, chong nhau

Bat buoc loc bang confidence (bai hoc tu WD: P54 disjoint conf 0.68 -> PaTeCon loai DUNG,
vi cau thu co the vua o CLB vua o doi tuyen).
"""
import json, zipfile, io, sys, collections, math
sys.path.insert(0, 'tempekg_exp')
from timex_norm import doc_reference_chain


def wilson_lo(k, n, z=1.96):
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z*z/n
    return (p + z*z/(2*n) - z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / d


# ---- khoang thoi gian event, CHI dung anchor regex thuan (dang tin, EXP22) ----
ev_iv, ev_type, ev_doc = {}, {}, {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        tl = [(t['id'], t['mention']) for t in
              sorted(d['TIMEX'], key=lambda x: (x['sent_id'], x['offset'][0]))]
        norm = doc_reference_chain(tl)
        ids = {e['id'] for e in d['events']}
        for e in d['events']:
            ev_type[e['id']] = e['type']
            ev_doc[e['id']] = d['id']
        anc = collections.defaultdict(list)
        for h, t in d['temporal_relations'].get('CONTAINS', []):
            if h in norm and t in ids:
                anc[t].append(h)
            if t in norm and h in ids:
                anc[h].append(t)
        for eid, txs in anc.items():
            vals = [norm[x] for x in dict.fromkeys(txs)]
            vals = [v for v in vals if v and v[3] == 'regex' and v[0] is not None
                    and v[2] != 'duration']
            if not vals:
                continue
            lo = max(v[0] for v in vals)
            hi = min(v[1] for v in vals)
            if lo <= hi:
                ev_iv[eid] = (lo, hi)

print('event co khoang dang tin (regex thuan): %d' % len(ev_iv))

# ---- argument ----
z = zipfile.ZipFile('MAVEN-Arg.zip')
ent_ev = collections.defaultdict(list)      # (doc,ent) -> [(eid, role)]
ev_fillers = collections.defaultdict(list)  # eid -> [(role, ent)]
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            for e in d['events']:
                if e['id'] not in ev_iv:
                    continue
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            ent_ev[(d['id'], v['entity_id'])].append((e['id'], r))
                            ev_fillers[e['id']].append((r, v['entity_id']))


def overlap(a, b):
    return a[0] <= b[1] and b[0] <= a[1]


# =============== T4a: cung entity, KHAC loai event ===============
sig_a = collections.defaultdict(lambda: [0, 0])     # (T1,T2) -> [chong, tong]
for key, lst in ent_ev.items():
    seen = set()
    for i in range(len(lst)):
        for j in range(i+1, len(lst)):
            e1, _ = lst[i]
            e2, _ = lst[j]
            if e1 == e2:
                continue
            t1, t2 = ev_type[e1], ev_type[e2]
            if t1 == t2:
                continue                     # PaTeCon da co nhanh nay
            k = tuple(sorted([e1, e2]))
            if k in seen:
                continue
            seen.add(k)
            s = tuple(sorted([t1, t2]))
            sig_a[s][1] += 1
            if overlap(ev_iv[e1], ev_iv[e2]):
                sig_a[s][0] += 1

# =============== T4b: KHAC entity, cung (loai event, vai) ===============
role_ev = collections.defaultdict(list)     # (doc, type, role) -> [(eid, ent)]
for eid, fl in ev_fillers.items():
    for r, ent in fl:
        role_ev[(ev_doc[eid], ev_type[eid], r)].append((eid, ent))

sig_b = collections.defaultdict(lambda: [0, 0])     # (type,role) -> [chong, tong]
for (doc, typ, role), lst in role_ev.items():
    for i in range(len(lst)):
        for j in range(i+1, len(lst)):
            e1, x1 = lst[i]
            e2, x2 = lst[j]
            if e1 == e2 or x1 == x2:
                continue
            sig_b[(typ, role)][1] += 1
            if overlap(ev_iv[e1], ev_iv[e2]):
                sig_b[(typ, role)][0] += 1


def report(sig, name, minsup=10):
    print()
    print('=' * 66)
    print(name)
    print('=' * 66)
    tot_pair = sum(v[1] for v in sig.values())
    tot_ov = sum(v[0] for v in sig.values())
    print('  cap xet: %d | chong nhau: %d (%.1f%%)' % (tot_pair, tot_ov, 100*tot_ov/max(tot_pair, 1)))
    # constraint DISJOINT = ty le KHONG chong cao
    kept = []
    for s, (ov, n) in sig.items():
        if n < minsup:
            continue
        disj = n - ov
        if wilson_lo(disj, n) >= 0.9:
            kept.append((s, disj, n, disj/n))
    print('  signature co support>=%d : %d' % (minsup, sum(1 for v in sig.values() if v[1] >= minsup)))
    print('  constraint DISJOINT giu lai (Wilson>=0.9): %d' % len(kept))
    viol = sum(n - d for _, d, n, _ in kept)
    cov = sum(n for _, _, n, _ in kept)
    print('  -> phu %d cap | VI PHAM %d (%.2f%%)' % (cov, viol, 100*viol/max(cov, 1)))
    for s, d, n, c in sorted(kept, key=lambda x: -x[2])[:6]:
        print('       %-46s n=%-5d conf=%.3f vi pham=%d' % (str(s)[:46], n, c, n-d))


report(sig_a, 'T4a  KHAC PROPERTY (ho noi "trivial" nhung KHONG chung minh)')
report(sig_b, 'T4b  KHAC CHU THE (ho bo vi CHI PHI tinh toan)')
