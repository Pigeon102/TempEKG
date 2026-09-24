"""Bieu dien THOI GIAN CO DO KHONG CHAC CHAN.

Van de goc (SMOKING_GUN.md): PaTeCon bieu dien thoi gian bang DIEM (YYYYMMDD).
"nam 1638" bi pad thanh 16380101, khong phan biet duoc voi "ngay 1/1/1638".
Hau qua: 25.5% conflict cua ho thuoc mau tho-vs-min.

Loi giai: bieu dien bang KHOANG + DO CHINH XAC.
   "nam 1638"      -> [1638-01-01, 1638-12-31]  gran=year
   "1/1/1638"      -> [1638-01-01, 1638-01-01]  gran=day
   "2/12/1638"     -> [1638-12-02, 1638-12-02]  gran=day

Khi do:
   1638 vs 2/12/1638  ->  khoang thu hai NAM TRONG khoang thu nhat  ->  REFINEMENT
   1/1/1638 vs 2/12/1638 -> hai diem KHAC nhau, cung gran=day       ->  CONFLICT that

Vi tu tra ve BA GIA TRI (giu tinh than FuzzyTime cua PaTeCon):
   TRUE / FALSE / UNKNOWN
"""
import datetime, calendar

TRUE, FALSE, UNKNOWN = 'TRUE', 'FALSE', 'UNKNOWN'
GRAN_RANK = {'day': 3, 'month': 2, 'year': 1, 'decade': 0, 'century': -1}


class UTime:
    """Khoang thoi gian co do chinh xac. lo/hi la so ngay proleptic Gregorian."""

    __slots__ = ('lo', 'hi', 'gran', 'src')

    def __init__(self, lo, hi, gran, src='?'):
        self.lo, self.hi, self.gran, self.src = lo, hi, gran, src

    @classmethod
    def from_padded(cls, s, declared_precision=None):
        """Doc gia tri kieu PaTeCon (YYYYMMDD) va do chinh xac THAT neu biet.

        Neu khong biet precision: SUY LUAN — '0101' rat co the la nam-only bi pad
        (do duoc: 57.3% vs ky vong 0.27%, tuc 209x).
        """
        if not (s and str(s).isdigit() and len(str(s)) == 8):
            return None
        s = str(s)
        y, m, d = int(s[:4]), int(s[4:6]), int(s[6:8])
        if declared_precision is not None:
            gran = {9: 'year', 10: 'month', 11: 'day'}.get(declared_precision, 'year')
        elif m == 0 or d == 0:
            gran = 'year' if m == 0 else 'month'
        elif m == 1 and d == 1:
            gran = 'suspect_year'      # <- diem mau chot: KHONG khang dinh la ngay
        else:
            gran = 'day'
        if gran in ('year', 'suspect_year') or m == 0:
            return cls(cls._o(y, 1, 1), cls._o(y, 12, 31), gran, s)
        if gran == 'month' or d == 0:
            last = calendar.monthrange(y, m)[1]
            return cls(cls._o(y, m, 1), cls._o(y, m, last), 'month', s)
        o = cls._o(y, m, d)
        return cls(o, o, 'day', s)

    @staticmethod
    def _o(y, m, d):
        try:
            return datetime.date(y, m, d).toordinal()
        except ValueError:
            return datetime.date(y, m, 1).toordinal()

    def __repr__(self):
        f = datetime.date.fromordinal
        return '[%s..%s]%s' % (f(self.lo), f(self.hi), self.gran)


# ---------------- VI TU BA GIA TRI ----------------

def before(a, b):
    """a ket thuc truoc khi b bat dau"""
    if a is None or b is None:
        return UNKNOWN
    if a.hi < b.lo:
        return TRUE
    if b.hi < a.lo:
        return FALSE
    return UNKNOWN                     # chong lan -> khong ket luan duoc


def disjoint(a, b):
    if a is None or b is None:
        return UNKNOWN
    if a.hi < b.lo or b.hi < a.lo:
        return TRUE
    # chi khang dinh FALSE khi CA HAI deu chinh xac den ngay
    if a.gran == 'day' and b.gran == 'day':
        return FALSE
    return UNKNOWN


def same_event(a, b):
    """Hai gia tri co the chi CUNG MOT su viec khong (mutual exclusion)?

    Day la vi tu THAY THE cho phep so sanh diem cua PaTeCon.
    Tra ve FALSE nghia la MAU THUAN THAT (hai su viec khac nhau).
    """
    if a is None or b is None:
        return UNKNOWN
    # giao rong -> chac chan khac nhau -> MAU THUAN
    if a.hi < b.lo or b.hi < a.lo:
        return FALSE
    # mot khoang chua khoang kia -> LAM MIN, khong mau thuan
    if (a.lo <= b.lo and b.hi <= a.hi) or (b.lo <= a.lo and a.hi <= b.hi):
        return TRUE
    return UNKNOWN


def classify_pair(a, b):
    """Phan loai quan he giua hai gia tri thoi gian cho CUNG mot thuoc tinh."""
    if a is None or b is None:
        return 'UNDECIDABLE'
    if a.hi < b.lo or b.hi < a.lo:
        return 'CONFLICT'                      # giao rong
    if a.lo == b.lo and a.hi == b.hi:
        return 'IDENTICAL'
    if (a.lo <= b.lo and b.hi <= a.hi) or (b.lo <= a.lo and a.hi <= b.hi):
        return 'REFINEMENT'                    # mot cai lam min cai kia
    return 'PARTIAL_OVERLAP'
