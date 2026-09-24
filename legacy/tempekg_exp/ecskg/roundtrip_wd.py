"""KIEM CHUNG VONG TRON: WD50K -> do thi event-centric CUA TA -> chieu nguoc -> PaTeCon goc.

Y tuong: Wikidata la cho DUY NHAT co ground truth cho PHEP ANH XA — chinh output cua
PaTeCon. Neu di qua bieu dien event-centric roi chieu nguoc ma mining ra DUNG bo constraint
cu, thi phep anh xa dung.

Buoc:
  1. moi fact (h,r,t,ts,te)  ->  REIFY thanh mot Event:
         Event(etype=r) voi vai {subject: h, object: t}, TimeX(eb=ts, le=te)
     Di qua DUNG cac class trong schema.py, khong phai bien doi chuoi.
  2. chieu P2 hai chieu:
         (h, r.s2o, t, ts, te)   va   (t, r.o2s, h, ts, te)
  3. ghi TSV dinh dang PaTeCon
  4. chay Constraint_Mining.py GOC tren ca hai file
  5. so bo constraint

DU DOAN KIEM CHUNG DUOC:
  SP1 tren quan he NGUOC (r.o2s) phai tai tao dung SP2 (inverse functional) cua r.
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecskg.schema import Event, Actor, TimeX, Edge
from ecskg.build import Graph

SRC = 'tempekg_exp/patecon_data/WD50K_official.tsv'
OUT = 'tempekg_exp/patecon/resource/WD50K_proj.tsv'
ORIG = 'tempekg_exp/patecon/resource/WD50K_orig.tsv'

os.makedirs(os.path.dirname(OUT), exist_ok=True)

# ---------- 1. REIFY: moi fact -> mot Event trong schema cua ta ----------
g = Graph()
actors = {}
n_fact = 0
rows_orig = []
for k, line in enumerate(open(SRC, encoding='utf-8')):
    p = line.rstrip('\n').split('\t')
    if len(p) < 5:
        continue
    h, r, t, ts, te = p[0], p[1], p[2], p[3].strip(), p[4].strip()
    n_fact += 1
    rows_orig.append((h, r, t, ts, te))

    ev = Event(nid='F%d' % k, doc_id='wd', etype=r, surface=r, src='reify')
    g.add_node(ev)
    tx = TimeX(nid='F%d:T' % k, doc_id='wd', src='wikidata')
    if ts not in ('', '-1', 'None'):
        tx.eb = int(ts); tx.begin = int(ts)
    if te not in ('', '-1', 'None'):
        tx.le = int(te); tx.end = int(te)
    g.add_node(tx)
    g.add_edge(Edge(ev.nid, tx.nid, 'hasTime', src='wikidata'))

    for role, ent in (('subject', h), ('object', t)):
        if ent not in actors:
            a = Actor(nid='E:%s' % ent, doc_id='wd', surface=ent, canon=ent, src='wikidata')
            g.add_node(a); actors[ent] = a
        g.add_edge(Edge(ev.nid, actors[ent].nid, 'hasActor', role=role, src='wikidata'))

print('reify: %d fact -> %d Event, %d Actor, %d TimeX, %d canh'
      % (n_fact, len(g.of_type(Event)), len(g.of_type(Actor)), len(g.of_type(TimeX)),
         len(g.edges)), flush=True)


# ---------- 2. CHIEU NGUOC pi (P2, hai chieu) ----------
def project(graph):
    """sieu canh -> statement (a, r, b, t1, t2). Doc TU DO THI, khong tu file goc."""
    roles = collections.defaultdict(dict)          # event -> {role: entity}
    times = {}
    for e in graph.edges.values():
        if e.label == 'hasActor':
            roles[e.head][e.role] = graph.nodes[e.tail].canon
        elif e.label == 'hasTime':
            b = graph.nodes[e.tail]
            times[e.head] = (b.eb if b.eb is not None else -1,
                             b.le if b.le is not None else -1)
    out = []
    for ev, rr in roles.items():
        T = graph.nodes[ev].etype
        t1, t2 = times.get(ev, (-1, -1))
        items = list(rr.items())
        for i in range(len(items)):
            for j in range(len(items)):
                if i == j:
                    continue
                r1, x = items[i]; r2, y = items[j]
                out.append((x, '%s.%s2%s' % (T, r1[0], r2[0]), y, t1, t2))
    return out


stmt = project(g)
print('chieu nguoc: %d statement (%.1fx so fact goc)' % (len(stmt), len(stmt)/n_fact))
rels = collections.Counter(s[1] for s in stmt)
print('quan he sinh ra: %d ->' % len(rels), dict(list(rels.items())[:6]))

# ---------- 3. ghi TSV ----------
with open(OUT, 'w', encoding='utf-8') as f:
    for a, r, b, t1, t2 in stmt:
        f.write('%s\t%s\t%s\t%s\t%s\t\n'
                % (a, r, b, t1 if t1 != -1 else '', t2 if t2 != -1 else ''))
with open(ORIG, 'w', encoding='utf-8') as f:
    for h, r, t, ts, te in rows_orig:
        f.write('%s\t%s\t%s\t%s\t%s\t\n' % (h, r, t, ts, te))
print('da ghi:\n  %s (%d dong)\n  %s (%d dong)'
      % (ORIG, len(rows_orig), OUT, len(stmt)))
