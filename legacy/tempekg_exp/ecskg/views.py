"""Event = node co CAU TRUC CLASS; thuoc tinh class sinh ra HO CAC VIEW (subgraph).

Y tuong (theo huong nguoi dung de xuat):
  - dua MOI event vao node, mang day du thuoc tinh kieu OOP
  - moi TAP THUOC TINH A sinh ra mot VIEW V_A: chu ky cua event = gia tri cac thuoc tinh A
  - pattern duoc mine TRONG tung view
  - P1/P2/P3/P4 truoc day chi la 4 diem trong DAN view nay:
        P4 = V{etype}      P3 = V{role}
        P2 = V{etype,role}  moi: V{etype,entity_type}, V{etype,gran}, ...
  - refinement cua PaTeCon = di len trong dan  ->  co nguyen tac, khong ad-hoc

Dinh nghia conflict GIU NGUYEN cua PaTeCon (trivalent, chung minh duong tinh).
"""
from __future__ import annotations
import collections, itertools


class EventClass:
    """Thuoc tinh cua mot event node. Khai bao o CAP CLASS -> them/bo mot dong.

    Moi ten trong ATTRS co the dung lam TRUC cua view.
    """
    ATTRS = [
        'etype',          # kieu su kien                       162 gia tri
        'n_role',         # so vai co filler                   0..k
        'roleset',        # tap vai co mat (sap xep)
        'top_role',       # vai pho bien nhat trong event
        'etypeset',       # tap KIEU ENTITY co mat  <- truc class_type cua PaTeCon
        'has_person', 'has_org', 'has_loc',
        'n_anchor',       # so anchor thoi gian giai duoc
        'gran_set',       # tap hat do cua cac anchor
        'method_set',     # tap phuong phap chuan hoa
        'anchor_src',     # nguon anchor: same_sent / prev_sent / ere
        'sent_bucket',    # vi tri cau trong document (dau/giua/cuoi)
    ]

    __slots__ = tuple(ATTRS) + ('nid', 'doc', 'anchors')

    def __init__(self, nid, doc, **kw):
        self.nid = nid; self.doc = doc; self.anchors = kw.pop('anchors', [])
        for a in self.ATTRS:
            setattr(self, a, kw.get(a))

    def sig(self, axes):
        """Chu ky cua event trong view V_axes."""
        return tuple(getattr(self, a) for a in axes)


# ============================================================ conflict E4
def e4_conflict(ev):
    """PaTeCon's conflict definition ap cho INTRA-EVENT:
       >=2 anchor cua CUNG mot event phai co giao khac rong.
       Day la pattern PaTeCon KHONG BIEU DIEN DUOC (moi fact cua ho co dung 1 khoang)."""
    v = [a for a in ev.anchors if a is not None]
    if len(v) < 2:
        return None                      # khong xet duoc
    lo = max(a[0] for a in v); hi = min(a[1] for a in v)
    return lo > hi                       # True = CONFLICT


# ============================================================ dan view
def enumerate_views(axes_pool, max_dim=2):
    for k in range(1, max_dim+1):
        for c in itertools.combinations(axes_pool, k):
            yield c


def mine_view(events, axes, label_fn, min_sup=30):
    """Trong view V_axes: chu ky nao GIAU conflict hon muc nen?

    Day la chieu BOTTOM-UP: khong gia dinh truoc pattern nao, do lift cua tung chu ky.
    """
    pos = collections.Counter(); tot = collections.Counter()
    gp = gt = 0
    for ev in events:
        y = label_fn(ev)
        if y is None:
            continue
        s = ev.sig(axes)
        tot[s] += 1; pos[s] += y
        gt += 1; gp += y
    base = gp/max(gt, 1)
    out = []
    for s, n in tot.items():
        if n < min_sup:
            continue
        r = pos[s]/n
        out.append((r/max(base, 1e-9), r, n, s))
    return sorted(out, reverse=True), base, gt


def wilson_lo(k, n, z=1.96):
    import math
    if n == 0:
        return 0.0
    p = k/n; d = 1+z*z/n; c = p+z*z/(2*n)
    m = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return max(0.0, (c-m)/d)
