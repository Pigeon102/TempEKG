"""Mentions -> do thi event-centric. Luu tru + tai lai.

Cau truc theo SEM/ECS-KG:
  node   Event | Actor | Place | TimeX
  canh   hasActor(role) | hasTime | BEFORE/AFTER | sameAs | similarTopic

ECS-KG lay role tu nhan dependency spaCy. Khong co parser nen dung xap xi vi tri:
  token dung TRUOC trigger  -> vai 'agentish'   (gan chu ngu)
  token dung SAU  trigger  -> vai 'patientish' (gan tan ngu)
Day la xap xi YEU va duoc ghi ro — chat luong role la bien do duoc, khong phai gia dinh.
"""
from __future__ import annotations
import json, collections, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecskg.schema import Event, Actor, Place, TimeX, Edge, NODE_CLASSES
from timex_norm2 import normalize


class Graph:
    def __init__(self):
        self.nodes = {}                              # nid -> Node
        self.edges = {}                              # key -> Edge
        self.by_doc = collections.defaultdict(list)
        self.idx = collections.defaultdict(lambda: collections.defaultdict(list))

    # ---------- xay ----------
    def add_node(self, node):
        self.nodes[node.nid] = node
        self.by_doc[node.doc_id].append(node.nid)
        for k, a in type(node)._attrs.items():
            if a.index:
                v = getattr(node, k)
                if v is not None:
                    self.idx[k][v].append(node.nid)
        return node

    def add_edge(self, e):
        self.edges[e.key()] = e
        return e

    # ---------- truy van ----------
    def of_type(self, cls):
        return [n for n in self.nodes.values() if isinstance(n, cls)]

    def out(self, nid, label=None):
        return [e for e in self.edges.values()
                if e.head == nid and (label is None or e.label == label)]

    def times_of(self, eid):
        return [self.nodes[e.tail] for e in self.out(eid, 'hasTime')
                if e.tail in self.nodes]

    def stats(self):
        c = collections.Counter(type(n).__name__ for n in self.nodes.values())
        el = collections.Counter(e.label for e in self.edges.values())
        return c, el

    # ---------- luu tru ----------
    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(json.dumps({'v': 1, 'n': len(self.nodes), 'e': len(self.edges)})+'\n')
            for n in self.nodes.values():
                f.write('N\t'+json.dumps(n.as_dict(), ensure_ascii=False)+'\n')
            for e in self.edges.values():
                f.write('E\t'+json.dumps(e.as_dict(), ensure_ascii=False)+'\n')

    @classmethod
    def load(cls, path):
        g = cls()
        with open(path, encoding='utf-8') as f:
            f.readline()
            for line in f:
                t, _, payload = line.partition('\t')
                d = json.loads(payload)
                if t == 'N':
                    kls = NODE_CLASSES[d.pop('_cls')]
                    if 'offset' in d:
                        d['offset'] = tuple(d['offset'])
                    g.add_node(kls(**d))
                else:
                    g.add_edge(Edge(**d))
        return g


# ============================================================ chuan hoa thoi gian
def make_timex(nid, doc, s, i, j, surf, ttype, ref_year, ref_date):
    """Chuan hoa surface -> bon moc SEM. Tra ve (TimeX, ref_year, ref_date) moi."""
    t = TimeX(nid=nid, doc_id=doc, surface=surf, sent_id=s, offset=(i, j),
              ttype=ttype, src='regex')
    r = normalize(surf, ref_year=ref_year, ref_date=ref_date)
    if r and r[0] is not None:
        lo, hi, gran = r[0], r[1], r[2]
        t.gran = gran
        t.method = r[3] if len(r) > 3 else 'regex'
        if lo == hi:
            t.stamp = lo
        else:
            t.eb, t.le = lo, hi          # SEM: interval bat dinh
            t.begin, t.end = lo, hi
        if gran in ('day', 'month', 'year'):
            ref_year = lo // 10000
            if gran == 'day':
                ref_date = lo
    else:
        t.gran = 'unknown'
        t.method = 'none'
    return t, ref_year, ref_date


# ============================================================ dung do thi
CUE_BEFORE = {'before', 'prior', 'earlier', 'previously', 'until', 'preceding'}
CUE_AFTER = {'after', 'later', 'subsequently', 'then', 'afterwards', 'following',
             'since', 'once'}


def build(extractions, sentences_by_doc, topic_by_doc=None):
    """extractions: {doc_id: Extraction}"""
    g = Graph()
    canon_index = collections.defaultdict(list)

    for doc, ex in extractions.items():
        sents = sentences_by_doc[doc]
        topic = (topic_by_doc or {}).get(doc)

        # --- TimeX (tu tim, chuoi tham chieu trong document) ---
        ref_year = ref_date = None
        tnodes = []
        for k, (s, i, j, surf, ttype) in enumerate(ex.times):
            nid = '%s:T%d' % (doc, k)
            t, ref_year, ref_date = make_timex(nid, doc, s, i, j, surf, ttype,
                                               ref_year, ref_date)
            g.add_node(t); tnodes.append(t)

        # --- Actor ---
        anodes = []
        for k, (s, i, j, surf) in enumerate(ex.entities):
            nid = '%s:A%d' % (doc, k)
            a = Actor(nid=nid, doc_id=doc, surface=surf, sent_id=s, offset=(i, j),
                      canon=surf.lower(), src='caps')
            g.add_node(a); anodes.append(a)
            canon_index[surf.lower()].append(nid)

        # --- Event ---
        enodes = []
        for k, (s, i, j, surf, et, c) in enumerate(ex.events):
            nid = '%s:E%d' % (doc, k)
            e = Event(nid=nid, doc_id=doc, surface=surf, sent_id=s, offset=(i, j),
                      etype=et, trigger=surf.lower(), conf=c, src='lexicon',
                      topic=topic)
            g.add_node(e); enodes.append(e)

        # --- hasActor: cung cau, vai theo vi tri (xap xi dependency cua ECS-KG) ---
        by_sent_a = collections.defaultdict(list)
        for a in anodes:
            by_sent_a[a.sent_id].append(a)
        for e in enodes:
            for a in by_sent_a.get(e.sent_id, []):
                role = 'agentish' if a.offset[1] <= e.offset[0] else 'patientish'
                dist = min(abs(a.offset[0]-e.offset[0]), abs(a.offset[1]-e.offset[1]))
                if dist <= 12:
                    g.add_edge(Edge(e.nid, a.nid, 'hasActor', role=role,
                                    src='pos', conf=1.0/(1+dist)))

        # --- hasTime: cung cau, hoac cau truoc neu cau nay khong co ---
        by_sent_t = collections.defaultdict(list)
        for t in tnodes:
            by_sent_t[t.sent_id].append(t)
        for e in enodes:
            cands = by_sent_t.get(e.sent_id, [])
            src = 'same_sent'
            if not cands:
                prev = [t for t in tnodes if t.sent_id < e.sent_id]
                if prev:
                    m = max(t.sent_id for t in prev)
                    cands = [t for t in prev if t.sent_id == m]
                    src = 'prev_sent'
            for t in cands:
                d = abs(t.offset[0]-e.offset[0]) if src == 'same_sent' else 50
                g.add_edge(Edge(e.nid, t.nid, 'hasTime', src=src,
                                conf=1.0/(1+d/10.0)))

        # --- event-event: thu tu tran thuat + tu noi ---
        order = sorted(enodes, key=lambda e: (e.sent_id, e.offset[0]))
        for a, b in zip(order, order[1:]):
            lab, src = 'NARRATIVE_BEFORE', 'order'
            if b.sent_id < len(sents):
                head = [w.lower() for w in sents[b.sent_id][:4]]
                if any(w in CUE_BEFORE for w in head):
                    lab, src = 'AFTER', 'cue'
                elif any(w in CUE_AFTER for w in head):
                    lab, src = 'BEFORE', 'cue'
            g.add_edge(Edge(a.nid, b.nid, lab, src=src,
                            conf=0.9 if src == 'cue' else 0.5))

    # --- sameAs xuyen document theo dang chuan ---
    for canon, ids in canon_index.items():
        docs = {i.split(':')[0] for i in ids}
        if len(docs) > 1 and len(canon) > 3:
            base = ids[0]
            for other in ids[1:]:
                g.add_edge(Edge(base, other, 'sameAs', src='string'))
    return g
