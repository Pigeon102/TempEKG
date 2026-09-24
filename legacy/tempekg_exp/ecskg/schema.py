"""Schema OOP cho do thi event-centric.

Thiet ke bam theo SEM (van Hage 2011) va ECS-KG (Lakshika 2025):

  SEM     4 core class (Event/Actor/Place/Time) + he Type + 3 Constraint (Role/Temporary/View)
          + Authority (provenance). 7 thuoc tinh timestamp, trong do 4 cho interval BAT DINH.
          Co y KHONG khai bao functional property -> du lieu mau thuan duoc GIU LAI,
          viec phat hien day len tang ung dung.  <-- dung cai ta can

  ECS-KG  node la EVENT, role lay tu nhan dependency (khong can ontology vai co dinh),
          node date_time rieng, canh similarTopic noi bai bao.

Diem MOI so voi ca hai: ca hai deu khong mo hinh hoa XUNG DOT. SEM giu mau thuan nhung
khong phat hien; ECS-KG khong dong den. Tang Constraint/Conflict o day la phan bo sung.

--- VI SAO DUNG OOP ---
Thuoc tinh khai bao bang descriptor `Attr` o cap CLASS. Them/sua/bo mot thuoc tinh =
sua MOT dong, khong phai sua ham build, ham serialize, ham validate rieng le.
`Node.schema()` sinh ra mo ta bang tu chinh khai bao do.
"""
from __future__ import annotations
import json


# ============================================================ Attr
class Attr:
    """Mot thuoc tinh node/edge khai bao o cap class.

    Sua thuoc tinh chi can sua dong khai bao — validate, default, serialize,
    va mo ta schema deu tu dong theo.
    """
    __slots__ = ('name', 'kind', 'default', 'doc', 'index', 'required', 'multi')

    def __init__(self, kind=str, default=None, doc='', index=False,
                 required=False, multi=False):
        self.name = None            # __set_name__ dien vao
        self.kind = kind
        self.default = default
        self.doc = doc
        self.index = index          # co dung lam khoa tra cuu khong
        self.required = required
        self.multi = multi          # tap hop nhieu gia tri

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, obj, owner=None):
        if obj is None:
            return self
        try:
            return obj._v[self.name]
        except KeyError:
            d = set() if self.multi else self.default
            obj._v[self.name] = d
            return d

    def __set__(self, obj, value):
        if value is not None and not self.multi:
            if self.kind is not None and not isinstance(value, self.kind):
                try:
                    value = self.kind(value)
                except Exception:
                    raise TypeError('%s.%s can kieu %s, nhan %r'
                                    % (type(obj).__name__, self.name,
                                       self.kind.__name__, value))
        obj._v[self.name] = value


# ============================================================ Node
class NodeMeta(type):
    """Gom cac Attr cua class va toan bo to tien -> _attrs."""
    def __new__(mcls, name, bases, ns):
        cls = super().__new__(mcls, name, bases, ns)
        attrs = {}
        for b in reversed(cls.__mro__[1:]):
            attrs.update(getattr(b, '_attrs', {}))
        attrs.update({k: v for k, v in ns.items() if isinstance(v, Attr)})
        cls._attrs = attrs
        return cls


class Node(metaclass=NodeMeta):
    """Node co so. Moi node deu co id, provenance, va span nguon."""

    nid      = Attr(str,   doc='dinh danh duy nhat', index=True, required=True)
    doc_id   = Attr(str,   doc='bai bao chua node nay', index=True)
    surface  = Attr(str,   doc='chuoi van ban goc')
    sent_id  = Attr(int,   doc='cau xuat hien')
    offset   = Attr(tuple, doc='(bat dau, ket thuc) theo token')
    src      = Attr(str,   default='text', doc='bo trich xuat sinh ra node (provenance)')
    conf     = Attr(float, default=1.0, doc='do tin cay cua bo trich xuat')

    def __init__(self, **kw):
        object.__setattr__(self, '_v', {})
        for k, v in kw.items():
            if k not in self._attrs:
                raise AttributeError('%s khong co thuoc tinh %r. Co: %s'
                                     % (type(self).__name__, k,
                                        ', '.join(sorted(self._attrs))))
            setattr(self, k, v)

    def __setattr__(self, k, v):
        if k not in self._attrs and not k.startswith('_'):
            raise AttributeError('%s khong co thuoc tinh %r' % (type(self).__name__, k))
        object.__setattr__(self, k, v) if k.startswith('_') else \
            type(self)._attrs[k].__set__(self, v)

    # ---- tien ich ----
    def as_dict(self):
        d = {'_cls': type(self).__name__}
        for k in self._attrs:
            v = getattr(self, k)
            if v is None or (isinstance(v, set) and not v):
                continue
            d[k] = sorted(v) if isinstance(v, set) else v
        return d

    @classmethod
    def schema(cls):
        """Mo ta schema sinh tu chinh khai bao — khong viet tay."""
        out = []
        for k, a in sorted(cls._attrs.items()):
            out.append('  %-12s %-8s %-6s %s' % (
                k, getattr(a.kind, '__name__', '?'),
                'idx' if a.index else '', a.doc))
        return '%s\n%s' % (cls.__name__, '\n'.join(out))

    def __repr__(self):
        return '%s(%s %r)' % (type(self).__name__, self.nid, self.surface)


# ============================================================ 4 core class SEM
class Event(Node):
    """sem:Event — don vi luu tru tri thuc (Rospocher, dan trong ECS-KG)."""
    etype    = Attr(str, doc='sem:eventType — kieu su kien', index=True)
    trigger  = Attr(str, doc='tu kich hoat')
    polarity = Attr(str, default='POS', doc='POS / NEG (phu dinh)')
    modality = Attr(str, default='ACTUAL', doc='ACTUAL / HYPOTHETICAL / REPORTED')
    topic    = Attr(str, doc='chu de bai bao (ECS-KG §3.3)', index=True)


class Actor(Node):
    """sem:Actor — nguoi/to chuc/vat tham gia."""
    atype    = Attr(str, doc='sem:actorType — PERSON / ORG / MISC', index=True)
    canon    = Attr(str, doc='dang chuan hoa sau khi gop dong tham chieu', index=True)


class Place(Node):
    """sem:Place."""
    ptype    = Attr(str, doc='sem:placeType')
    canon    = Attr(str, index=True)


class TimeX(Node):
    """sem:Time. Bon moc bat dinh cua SEM tong quat hon UTime(lo,hi).

    SEM co 7 thuoc tinh timestamp; day la ca 7:
      point                                   -> stamp
      interval xac dinh                       -> begin, end
      interval BAT DINH (4 gia tri)           -> eb, lb, ee, le
    """
    stamp    = Attr(int, doc='sem:hasTimeStamp — moc don (YYYYMMDD)')
    begin    = Attr(int, doc='sem:hasBeginTimeStamp')
    end      = Attr(int, doc='sem:hasEndTimeStamp')
    eb       = Attr(int, doc='sem:hasEarliestBeginTimeStamp')
    lb       = Attr(int, doc='sem:hasLatestBeginTimeStamp')
    ee       = Attr(int, doc='sem:hasEarliestEndTimeStamp')
    le       = Attr(int, doc='sem:hasLatestEndTimeStamp')
    gran     = Attr(str, doc='day / month / year / decade / century / unknown', index=True)
    ttype    = Attr(str, doc='DATE / TIME / DURATION / SET')
    method   = Attr(str, doc='cach chuan hoa: regex / refprop / gazetteer', index=True)

    def bounds(self):
        """Quy ve (lo, hi) — hop cac moc da biet. None neu khong xac dinh."""
        lo = self.eb if self.eb is not None else (
            self.begin if self.begin is not None else self.stamp)
        hi = self.le if self.le is not None else (
            self.end if self.end is not None else self.stamp)
        if lo is None or hi is None:
            return None
        return (lo, hi) if lo <= hi else (hi, lo)

    def is_symbolic(self):
        """SEM: thoi gian ky hieu — chi biet thu tu, khong biet gia tri."""
        return self.bounds() is None


# ============================================================ canh
class Edge:
    """Canh co provenance. `src` nam trong khoa chinh -> cho phep held-out source.

    ECS-KG dung nhan dependency lam role; day giu nguyen y do: `role` la chuoi tu do.
    """
    __slots__ = ('head', 'tail', 'label', 'role', 'src', 'conf', 'authority')

    def __init__(self, head, tail, label, role=None, src='text', conf=1.0, authority=None):
        self.head = head
        self.tail = tail
        self.label = label          # hasActor / hasPlace / hasTime / BEFORE / CAUSES / ...
        self.role = role            # nhan dependency hoac vai ngu nghia
        self.src = src              # bo trich xuat — nam trong khoa chinh
        self.conf = conf
        self.authority = authority  # sem:Authority — theo ai thi dieu nay dung

    def key(self):
        return (self.head, self.tail, self.label, self.src)

    def as_dict(self):
        return {'head': self.head, 'tail': self.tail, 'label': self.label,
                'role': self.role, 'src': self.src, 'conf': self.conf,
                'authority': self.authority}

    def __repr__(self):
        return '%s -[%s%s]-> %s' % (self.head, self.label,
                                    '/'+self.role if self.role else '', self.tail)


# ============================================================ rang buoc SEM
class Constraint:
    """sem:Constraint — Role / Temporary / View.

    SEM dat rang buoc LEN THUOC TINH, khong len node. Day la cho SEM manh hon
    do thi phang: cung mot canh hasActor co the mang hai roleType khac nhau
    theo hai Authority khac nhau (vd. giai phong quan vs quan chiem dong).
    """
    __slots__ = ('kind', 'edge_key', 'value', 'authority', 'valid_from', 'valid_to')

    def __init__(self, kind, edge_key, value, authority=None,
                 valid_from=None, valid_to=None):
        assert kind in ('Role', 'Temporary', 'View')
        self.kind = kind
        self.edge_key = edge_key
        self.value = value
        self.authority = authority
        self.valid_from = valid_from
        self.valid_to = valid_to


NODE_CLASSES = {c.__name__: c for c in (Event, Actor, Place, TimeX)}


def describe():
    return '\n\n'.join(c.schema() for c in (Node, Event, Actor, Place, TimeX))


if __name__ == '__main__':
    print(describe())
