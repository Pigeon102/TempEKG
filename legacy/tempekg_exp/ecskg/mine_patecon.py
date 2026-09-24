"""Dinh nghia constraint cua PaTeCon, CAI TREN kien truc event-centric cua ta.

Chieu dung: PaTeCon --> chung ta. Khong chuyen do thi ta ve dang cua ho roi chay ma cua ho.

--- ANH XA KHAI NIEM ---
   PaTeCon                          |  event-centric cua ta
   statement (a, r, b, t1, t2)      |  THAM GIA: (entity x, khoa k=(T,role), event e, khoang I)
   eVertex a                        |  Actor x
   relation r                       |  khoa k = (kieu event T, vai role)
   thoi gian cua statement          |  khoang cua EVENT (dung chung cho moi vai)

--- HAI MAU CAU TRUC GOP LAM MOT ---
   PaTeCon can HAI ham mining rieng:
      SP1 functional          : gom theo DAU  (a, r)
      SP2 inverse functional  : gom theo DUOI (b, r)
   Trong the gioi nhi phan, "dau"/"duoi" chinh la hai VAI subject/object.
   Tren do thi co nhan vai, ca hai la CUNG MOT phep: gom theo (entity, (T,role)).
   -> C1 duy nhat, chay tren moi vai. Tu vung 559 khoa thay vi 1672 quan he.

--- GIU NGUYEN ---
   Interval_Relations (FuzzyTime, comp_time, disjoint/before/include/start/finish)
   cach dem positive/negative/unknown, ngu nghia break, va toan bo nguong.
"""
from __future__ import annotations
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), 'patecon'))
import Interval_Relations as IR
from ecskg.schema import Event, Actor, TimeX

# nguong GIU NGUYEN cua PaTeCon
SUPPORT_THRESHOLD = 100
CANDIDATE_THRESHOLD = 0.5
CONFIDENCE_THRESHOLD = 0.9


def participations(g, skip_literal=True):
    """Do thi -> {entity: [(khoa, e_nid, start, end)]}.

    Day la don vi tuong duong 'statement' cua PaTeCon, nhung khoa la (T, vai)
    chu khong phai mot quan he nhi phan.
    """
    iv = {}
    for e in g.edges.values():
        if e.label == 'hasTime':
            t = g.nodes.get(e.tail)
            if t is None:
                continue
            s = t.eb if t.eb is not None else (t.begin if t.begin is not None else t.stamp)
            en = t.le if t.le is not None else (t.end if t.end is not None else t.stamp)
            iv[e.head] = (s if s is not None else -1, en if en is not None else -1)

    out = collections.defaultdict(list)
    for e in g.edges.values():
        if e.label != 'hasActor':
            continue
        ev = g.nodes.get(e.head)
        x = g.nodes.get(e.tail)
        if ev is None or x is None:
            continue
        if skip_literal and (x.canon or '').replace('-', '').isdigit():
            continue                      # tuong duong isLiteral cua PaTeCon
        s, en = iv.get(e.head, (-1, -1))
        if s == -1 and en == -1:
            continue                      # PaTeCon: chi xet fact co thoi gian
        out[x.nid].append(('%s\x1f%s' % (ev.etype, e.role), e.head, s, en))
    return out


def _key(k):
    T, r = k.split('\x1f')
    return '%s.%s' % (T, r)


# ============================================================ C0 MutualExclusion
def mine_mutual_exclusion(parts, n_entity):
    """PaTeCon: mau so = moi (entity, quan he) ton tai; tu so = nhom co DUNG 1 gia tri.
    Khong dung thoi gian."""
    thr = 0.96 if n_entity <= 50000 else 0.98
    num = collections.Counter(); den = collections.Counter()
    for x, ps in parts.items():
        by = collections.defaultdict(list)
        for k, ev, s, e in ps:
            by[k].append(ev)
        for k, evs in by.items():
            den[k] += 1
            if len(evs) == 1:
                num[k] += 1
    out = []
    for k in den:
        conf = num[k]/den[k]
        if conf > thr and num[k] > SUPPORT_THRESHOLD:
            out.append((_key(k), 'MutualExclusion', None, conf, num[k], den[k]))
    return out


# ============================================================ C1 = SP1 + SP2
def mine_c1_disjoint(parts):
    """Gom theo (entity, khoa). Moi cap event -> disjoint(). Dem y het PaTeCon."""
    num = collections.Counter(); den = collections.Counter()
    for x, ps in parts.items():
        by = collections.defaultdict(list)
        for k, ev, s, e in ps:
            by[k].append((s, e))
        for k, lst in by.items():
            consistent, negative = True, False
            for i in range(len(lst)):
                stop = False
                for j in range(i+1, len(lst)):
                    r = IR.disjoint(lst[i][0], lst[i][1], lst[j][0], lst[j][1])
                    if r == -1:
                        consistent, negative, stop = False, True, True
                        break
                    if r == 0:
                        consistent = False
                if stop:
                    break
            if consistent:
                num[k] += 1; den[k] += 1
            elif negative:
                den[k] += 1
    out = []
    for k in den:
        conf = num[k]/den[k] if den[k] else 0
        if conf > CANDIDATE_THRESHOLD and num[k] > SUPPORT_THRESHOLD:
            out.append((_key(k), 'disjoint', None, conf, num[k], den[k]))
    return out


# ============================================================ C2 = SP3
PREDS = (('before', IR.before), ('include', IR.include),
         ('start', IR.start), ('finish', IR.finish))


def mine_c2_order(parts):
    """Cap khoa co thu tu, moi vi tu co tu/mau rieng — y het ZH_relations_statistics."""
    num = {p: collections.Counter() for p, _ in PREDS}
    den = {p: collections.Counter() for p, _ in PREDS}
    for x, ps in parts.items():
        if len(ps) < 2:
            continue
        buckets = collections.defaultdict(list)
        for a in range(len(ps)):
            for b in range(a+1, len(ps)):
                s1, s2 = ps[a], ps[b]
                if s1[0] == s2[0]:
                    continue
                buckets[(s1[0], s2[0])].append((s1, s2))
                buckets[(s2[0], s1[0])].append((s2, s1))
        for kk, pairs in buckets.items():
            cons = {p: True for p, _ in PREDS}
            neg = {p: False for p, _ in PREDS}
            flag = {p: True for p, _ in PREDS}
            for u, v in pairs:
                for p, fn in PREDS:
                    r = fn(u[2], u[3], v[2], v[3])
                    if r == -1:
                        cons[p] = False; neg[p] = True; flag[p] = False
                    elif r == 0:
                        cons[p] = False
                if not any(flag.values()):
                    break
            for p, _ in PREDS:
                if cons[p]:
                    num[p][kk] += 1; den[p][kk] += 1
                elif neg[p]:
                    den[p][kk] += 1
    out = []
    for p, _ in PREDS:
        for kk in den[p]:
            c = num[p][kk]/den[p][kk] if den[p][kk] else 0
            if c > CANDIDATE_THRESHOLD and num[p][kk] > SUPPORT_THRESHOLD:
                out.append((_key(kk[0]), p, _key(kk[1]), c, num[p][kk], den[p][kk]))
    return out


def mine(g, verbose=True):
    parts = participations(g)
    n_ent = len(parts)
    if verbose:
        print('tham gia (statement tuong duong): %d | entity: %d'
              % (sum(len(v) for v in parts.values()), n_ent))
    cs = []
    cs += mine_mutual_exclusion(parts, n_ent)
    me_keys = {c[0] for c in cs}
    # filter_mutual_functional cua PaTeCon: MutualExclusion loai bo disjoint cung quan he
    cs += [c for c in mine_c1_disjoint(parts) if c[0] not in me_keys]
    cs += mine_c2_order(parts)
    return cs


def fmt(c):
    a, p, b, conf, n, d = c
    if p == 'MutualExclusion':
        return 'x:%-16s MutualExclusion                      | %.16f  (%d/%d)' % (a, conf, n, d)
    if p == 'disjoint':
        return 'x:%-16s disjoint                             | %.16f  (%d/%d)' % (a, conf, n, d)
    return 'x:%-16s %-8s x:%-16s | %.16f  (%d/%d)' % (a, p, b, conf, n, d)
