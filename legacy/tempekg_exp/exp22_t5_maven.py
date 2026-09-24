"""EXP22 - T5 GRANULARITY CONFLICT tren MAVEN (loai PaTeCon khong xu ly).

Dinh nghia: mot event co NHIEU anchor TIMEX. Neu GIAO cua chung RONG -> mau thuan.
Neu long nhau (nam chua thang chua ngay) -> HOP LE, chi la nhieu do chinh xac.

4 phan loai (theo dung tinh than logic ba tri cua PaTeCon):
  REFINEMENT      : anchor long nhau -> hop le, lay giao lam khoang chinh xac hon
  COMPAT_NONCHAIN : giao khac rong nhung khong long nhau -> hop le nhung dang chu y
  CONFLICT        : giao RONG -> MAU THUAN
  UNDECIDABLE     : co anchor khong chuan hoa duoc -> khong ket luan (bo khoi thong ke)
"""
import json, sys, collections, datetime
sys.path.insert(0, 'tempekg_exp')
from timex_norm import doc_reference_chain

verdict = collections.Counter()
conflict_ex = []
gran_pairs = collections.Counter()
n_multi = 0

for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        tl = [(t['id'], t['mention']) for t in
              sorted(d['TIMEX'], key=lambda x: (x['sent_id'], x['offset'][0]))]
        norm = doc_reference_chain(tl)
        ids = {e['id'] for e in d['events']}
        etype = {e['id']: e['type'] for e in d['events']}

        anchors = collections.defaultdict(list)
        for h, t in d['temporal_relations'].get('CONTAINS', []):
            if h in norm and t in ids:
                anchors[t].append(h)
            if t in norm and h in ids:
                anchors[h].append(t)

        for eid, txs in anchors.items():
            txs = list(dict.fromkeys(txs))
            if len(txs) < 2:
                continue
            n_multi += 1
            vals = [norm[x] for x in txs]
            if any(v is None or v[2] == 'duration' or v[0] is None for v in vals):
                verdict['UNDECIDABLE'] += 1
                continue
            lo = max(v[0] for v in vals)
            hi = min(v[1] for v in vals)
            grans = tuple(sorted({v[2] for v in vals}))
            if lo > hi:
                verdict['CONFLICT'] += 1
                gran_pairs[grans] += 1
                if len(conflict_ex) < 8:
                    conflict_ex.append((
                        d['id'][:8], etype.get(eid, '?'),
                        [(dict(tl).get(x, '?')[:22],
                          str(datetime.date.fromordinal(norm[x][0])),
                          str(datetime.date.fromordinal(norm[x][1]))) for x in txs][:3]))
            else:
                # long nhau? = mot khoang chua het cac khoang kia
                nested = any(v[0] <= lo and hi <= v[1] for v in vals)
                verdict['REFINEMENT' if nested else 'COMPAT_NONCHAIN'] += 1

print('=' * 66)
print('T5 GRANULARITY CONFLICT tren MAVEN')
print('=' * 66)
print('event co >=2 anchor TIMEX: %d' % n_multi)
print()
dec = n_multi - verdict['UNDECIDABLE']
for k in ('REFINEMENT', 'COMPAT_NONCHAIN', 'CONFLICT', 'UNDECIDABLE'):
    base = n_multi if k == 'UNDECIDABLE' else max(dec, 1)
    tag = ' (tren tong)' if k == 'UNDECIDABLE' else ' (tren so KET LUAN duoc)'
    print('  %-16s %6d  %5.1f%%%s' % (k, verdict[k], 100*verdict[k]/base, tag))
print()
print('  ket luan duoc: %d / %d = %.1f%%' % (dec, n_multi, 100*dec/max(n_multi, 1)))
print('  => TY LE CONFLICT: %.2f%%' % (100*verdict['CONFLICT']/max(dec, 1)))
print()
print('cap granularity hay mau thuan:', gran_pairs.most_common(5))
print()
print('vi du CONFLICT that:')
for doc, typ, anc in conflict_ex:
    print('  doc %s [%s]' % (doc, typ))
    for surf, a, b in anc:
        print('      "%-22s" -> %s .. %s' % (surf, a, b))
