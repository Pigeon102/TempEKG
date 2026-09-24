"""TempEKG - he thong phat hien temporal conflict tren do thi event.

Thiet ke theo FRAMEWORK.md:
  - Do thi multi-layer: `source` nam trong KHOA CHINH -> hold-out duoc
  - 5 loai conflict T1..T5
  - HELD-OUT SOURCE PRECISION: dung nguon A phat hien, nguon B kiem chung
  - RECURRENCE-AWARE: khong gan co su kien lap lai hop le (EXP21: 54.6% cach >=3 nam)
"""
import json, zipfile, io, re, collections, math

# ============================ 1. XAY DO THI ============================

class ECKG:
    def __init__(self):
        self.events = {}                      # eid -> dict
        self.args = collections.defaultdict(list)   # eid -> [(role, filler)]
        self.ent_events = collections.defaultdict(list)  # (doc,ent) -> [eid]
        # canh rang buoc: (doc,e1,e2,source) -> (implied, strength)
        self.cedge = {}

    def add_cedge(self, doc, a, b, source, implied, strength):
        self.cedge[(doc, a, b, source)] = (implied, strength)

    def sources_for(self, doc, a, b):
        out = {}
        for s in ('S1', 'S2', 'S3', 'S4'):
            if (doc, a, b, s) in self.cedge:
                out[s] = self.cedge[(doc, a, b, s)]
        return out


INV = {'BEFORE': 'AFTER', 'AFTER': 'BEFORE', 'CONTAINS': 'CONTAINED',
       'CONTAINED': 'CONTAINS', 'OVERLAP': 'OVERLAP', 'SIMULTANEOUS': 'SIMULTANEOUS'}
NORM = {'BEFORE': 'BEFORE', 'CONTAINS': 'CONTAINS', 'OVERLAP': 'OVERLAP',
        'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}


def build():
    g = ECKG()
    ere = {}
    for split in ['train', 'valid']:
        for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
            d = json.loads(line)
            ere[d['id']] = d

    # --- event + neo nam ---
    for doc, d in ere.items():
        yr = {}
        for t in d['TIMEX']:
            m = re.match(r'^(\d{3,4})$', t['mention'].strip())
            if m:
                yr[t['id']] = int(m.group(1))
        ids = {e['id'] for e in d['events']}
        anc = collections.defaultdict(set)
        for h, t in d['temporal_relations'].get('CONTAINS', []):
            if h in yr and t in ids:
                anc[t].add(yr[h])
            if t in yr and h in ids:
                anc[h].add(yr[t])
        for e in d['events']:
            sids = [m['sent_id'] for m in e['mention'] if 'sent_id' in m]
            ys = anc.get(e['id'], set())
            g.events[e['id']] = {'doc': doc, 'type': e['type'],
                                 'sent': min(sids) if sids else 10**9,
                                 'years': sorted(ys)}

        # --- S1: quan he thoi gian truc tiep (hard, tu annotation) ---
        for rel, ps in d['temporal_relations'].items():
            for h, t in ps:
                if h in ids and t in ids and rel in NORM:
                    g.add_cedge(doc, h, t, 'S1', NORM[rel], 'hard')
        # --- S2: nhan qua (hard, ngu nghia) ---
        for kind, ps in d.get('causal_relations', {}).items():
            for h, t in ps:
                if h in ids and t in ids:
                    g.add_cedge(doc, h, t, 'S2', 'NOT_AFTER', 'hard')
        # --- S3: subevent (hard, ngu nghia) ---
        for h, t in d.get('subevent_relations', []):
            if h in ids and t in ids:
                g.add_cedge(doc, h, t, 'S3', 'CONTAINS', 'hard')
        # --- S4: bac cau (hard, logic) ---
        before = {(h, t) for h, t in d['temporal_relations'].get('BEFORE', [])
                  if h in ids and t in ids}
        adj = collections.defaultdict(set)
        for h, t in before:
            adj[h].add(t)
        for u in adj:
            for v in adj[u]:
                for w in adj.get(v, ()):
                    if w != u:
                        g.add_cedge(doc, u, w, 'S4', 'BEFORE', 'hard')

    # --- argument tu MAVEN-Arg ---
    z = zipfile.ZipFile('MAVEN-Arg.zip')
    for sp in ['train.jsonl', 'valid.jsonl']:
        with z.open(sp) as f:
            for line in io.TextIOWrapper(f, encoding='utf-8'):
                d = json.loads(line)
                for e in d['events']:
                    if e['id'] not in g.events:
                        continue
                    for r, vs in (e.get('argument') or {}).items():
                        for v in vs:
                            if 'entity_id' in v:
                                g.args[e['id']].append((r, v['entity_id']))
                                g.ent_events[(d['id'], v['entity_id'])].append(e['id'])
    return g


# ============================ 2. PHAT HIEN CONFLICT ============================

def check_pair(implied_a, implied_b):
    """hai rang buoc co MAU THUAN khong"""
    if implied_a is None or implied_b is None:
        return False
    if implied_b == 'NOT_AFTER' and implied_a == 'AFTER':
        return True
    if implied_b == 'CONTAINS' and implied_a not in ('CONTAINS', 'SIMULTANEOUS'):
        return True
    if implied_a == 'CONTAINS' and implied_b not in ('CONTAINS', 'SIMULTANEOUS'):
        return True
    if {implied_a, implied_b} == {'BEFORE', 'AFTER'}:
        return True
    return False


def detect(g, use_sources):
    """gan co conflict CHI dung cac nguon trong use_sources"""
    flagged = set()
    pairs = collections.defaultdict(dict)
    for (doc, a, b, s), (imp, _) in g.cedge.items():
        if s not in use_sources:
            continue
        key = (doc,) + tuple(sorted([a, b]))
        rev = (a != key[1])
        pairs[key][s] = INV.get(imp, imp) if rev else imp
    for key, srcs in pairs.items():
        ss = list(srcs.items())
        for i in range(len(ss)):
            for j in range(i + 1, len(ss)):
                if check_pair(ss[i][1], ss[j][1]):
                    flagged.add(key)
    return flagged


# ============================ 3. HELD-OUT SOURCE PRECISION ============================

def heldout_eval(g):
    ALL = ['S1', 'S2', 'S3', 'S4']
    print('=' * 68)
    print('HELD-OUT SOURCE PRECISION  (khong can annotate)')
    print('=' * 68)
    print('%-16s %-16s %9s %9s %9s %9s' %
          ('PHAT HIEN', 'KIEM CHUNG', 'gan co', 'xac nhan', 'PREC', 'REC'))
    print('-' * 74)
    rows = []
    for held in ALL:
        A = [s for s in ALL if s != held]
        B = [held]
        fa = detect(g, set(A) | set(B))          # conflict can it nhat 2 nguon
        # tap A phat hien: cap co mau thuan trong A
        fa_only = detect(g, set(A))
        # tap B xac nhan: cap ma B mau thuan voi bat ky nguon nao trong A
        fb = set()
        for key in fa:
            doc, x, y = key
            has_b = any((doc, x, y, s) in g.cedge or (doc, y, x, s) in g.cedge for s in B)
            if has_b:
                fb.add(key)
        inter = fa_only & fb
        prec = len(inter) / len(fa_only) if fa_only else float('nan')
        rec = len(inter) / len(fb) if fb else float('nan')
        rows.append((held, len(fa_only), len(fb), len(inter), prec, rec))
        print('%-16s %-16s %9d %9d %8.1f%% %8.1f%%'
              % ('+'.join(A), held, len(fa_only), len(inter),
                 100 * prec if prec == prec else 0, 100 * rec if rec == rec else 0))
    return rows


# ============================ 4. T2 CO XET LAP LAI ============================

def t2_recurrence_aware(g, gap_years=3):
    """MutualExclusion nhung LOAI TRU su kien lap lai hop le"""
    naive = recurring = flagged = 0
    by_type = collections.Counter()
    for (doc, ent), eids in g.ent_events.items():
        bytype = collections.defaultdict(list)
        for e in set(eids):
            bytype[g.events[e]['type']].append(e)
        for typ, es in bytype.items():
            if len(es) < 2:
                continue
            years = sorted({y for e in es for y in g.events[e]['years']})
            if len(years) < 2:
                continue
            naive += 1
            if max(years) - min(years) >= gap_years:
                recurring += 1
                by_type[typ] += 1
            else:
                flagged += 1
    return naive, recurring, flagged, by_type


if __name__ == '__main__':
    print('dang xay do thi...')
    g = build()
    ns = collections.Counter(k[3] for k in g.cedge)
    print('event: %d | canh rang buoc: %d  %s' % (len(g.events), len(g.cedge), dict(ns)))
    print()
    heldout_eval(g)
    print()
    print('=' * 68)
    print('T2 MUTUAL EXCLUSION - co xet SU KIEN LAP LAI')
    print('=' * 68)
    n, r, f, bt = t2_recurrence_aware(g)
    print('  ung vien tho (PaTeCon se gan co het) : %d' % n)
    print('  loai vi LAP LAI hop le (cach >=3 nam): %d (%.1f%%)' % (r, 100*r/max(n, 1)))
    print('  con lai thuc su dang ngo              : %d' % f)
    print('  -> tran precision cua T2 tho: %.1f%%' % (100*f/max(n, 1)))
    print('  loai event bi loai nhieu nhat:', bt.most_common(5))
