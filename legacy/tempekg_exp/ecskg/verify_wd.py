"""KIEM CHUNG: miner CUA TA tren do thi CUA TA co tai tao dung ket qua PaTeCon khong.

Wikidata la cho duy nhat co ground truth cho PHEP ANH XA — chinh output cua PaTeCon.
   WD50K --reify--> do thi event-centric --> mine_patecon.py (miner CUA TA)
                                             |
   WD50K --------> PaTeCon goc  ------------>+--> so sanh
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecskg.schema import Event, Actor, TimeX, Edge
from ecskg.build import Graph
from ecskg.mine_patecon import mine, fmt

SRC = 'tempekg_exp/patecon_data/WD50K_official.tsv'

g = Graph()
actors = {}
seen = set()
for k, line in enumerate(open(SRC, encoding='utf-8')):
    p = line.rstrip('\n').split('\t')
    if len(p) < 5:
        continue
    h, r, t, ts, te = p[0], p[1], p[2], p[3].strip(), p[4].strip()
    # NGU NGHIA EVENT: cung nguoi tham gia + cung kieu + cung thoi gian = MOT event.
    # Trong mo hinh fact-list cua PaTeCon dieu nay phai lam bang buoc khu trung rieng
    # trong reader ("duplicate running time"); o day no la he qua cua mo hinh.
    if (h, r, t, ts, te) in seen:
        continue
    seen.add((h, r, t, ts, te))
    ev = Event(nid='F%d' % k, doc_id='wd', etype=r, src='reify')
    g.add_node(ev)
    tx = TimeX(nid='F%d:T' % k, doc_id='wd', src='wikidata')
    if ts not in ('', '-1', 'None'):
        tx.eb = int(ts)
    if te not in ('', '-1', 'None'):
        tx.le = int(te)
    g.add_node(tx)
    g.add_edge(Edge(ev.nid, tx.nid, 'hasTime', src='wikidata'))
    for role, ent in (('subject', h), ('object', t)):
        if ent not in actors:
            a = Actor(nid='E:%s' % ent, doc_id='wd', surface=ent, canon=ent, src='wikidata')
            g.add_node(a); actors[ent] = a
        g.add_edge(Edge(ev.nid, actors[ent].nid, 'hasActor', role=role, src='wikidata'))

print('do thi event-centric: %d Event, %d Actor, %d canh'
      % (len(g.of_type(Event)), len(g.of_type(Actor)), len(g.edges)), flush=True)

cs = mine(g)
print('\n' + '='*80)
print('MINER CUA TA tren DO THI CUA TA  -> %d constraint' % len(cs))
print('='*80)
for c in sorted(cs, key=lambda x: (x[1], -x[3])):
    print(' ', fmt(c))

# ---- doi chieu voi output PaTeCon goc ----
ref = 'tempekg_exp/patecon/output/WD50K_orig.all_constraints'
print('\n' + '='*80)
print('PaTeCon GOC (%s)' % ref)
print('='*80)
gold = []
if os.path.exists(ref):
    for line in open(ref, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        body, conf = line.rsplit('|', 1)
        el = body.split(' ')
        r1 = el[0].split(',')[1]
        pred = el[1]
        r2 = el[2].split(',')[1] if len(el) > 2 else None
        if pred == 'MutualExclusion':
            r2 = None
        gold.append((r1, pred, r2, float(conf)))
        print('  %-8s %-16s %-8s | %s' % (r1, pred, r2 or '', conf))

# ---- so ----
print('\n' + '='*80)
print('SO SANH  (khoa cua ta .subject  <=>  quan he cua ho)')
print('='*80)


def norm_ours(c):
    a, p, b, conf, n, d = c
    a2 = a[:-8] if a.endswith('.subject') else a
    b2 = (b[:-8] if b and b.endswith('.subject') else b)
    return (a2, p, b2), conf, a.endswith('.subject') and (b is None or b.endswith('.subject'))


ours = {}
extra = []
for c in cs:
    k, conf, is_subj = norm_ours(c)
    if is_subj:
        ours[k] = conf
    else:
        extra.append((c, conf))

ok = miss = diff = 0
for r1, p, r2, conf in gold:
    k = (r1, p, r2)
    if k in ours:
        if abs(ours[k]-conf) < 1e-12:
            print('  KHOP CHINH XAC  %-8s %-16s %-8s  %.16f' % (r1, p, r2 or '', conf))
            ok += 1
        else:
            print('  LECH            %-8s %-16s %-8s  ho %.10f | ta %.10f'
                  % (r1, p, r2 or '', conf, ours[k]))
            diff += 1
    else:
        print('  THIEU           %-8s %-16s %-8s  %.10f' % (r1, p, r2 or '', conf))
        miss += 1

print('\n  khop chinh xac %d / %d   |  lech %d  |  thieu %d' % (ok, len(gold), diff, miss))
print('\n  constraint CUA TA khong co doi ung o vai subject (%d):' % len(extra))
for c, conf in sorted(extra, key=lambda x: -x[1])[:12]:
    print('   ', fmt(c))
