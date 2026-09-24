"""TIMEX normaliser v2 — viet lai TRIET DE thay vi va tung manh.

Phan tich toan bo 3,370 TIMEX chua giai duoc cua v1, gom thanh 18 ho, xu ly het.

Tra ve (lo, hi, gran, method) — lo/hi la so ngay proleptic Gregorian (co the AM cho truoc CN).
gran: day|month|year|decade|century|duration|time
method: regex|refprop|gazetteer
"""
import re, datetime, calendar

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})

WD = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
      'friday': 4, 'saturday': 5, 'sunday': 6}

NUMW = {'a': 1, 'an': 1, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11,
        'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16,
        'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'thirty': 30,
        'forty': 40, 'fifty': 50, 'sixty': 60, 'hundred': 100,
        'several': 3, 'few': 3, 'couple': 2, 'many': 5, 'nearly': 1, 'half': 0.5}

UNIT_D = {'second': 1/86400, 'minute': 1/1440, 'hour': 1/24, 'day': 1, 'night': 1,
          'week': 7, 'month': 30.44, 'year': 365.25, 'decade': 3652.5,
          'century': 36525, 'centurie': 36525}

# ho 4: su kien co ten
NAMED = {
    'world war ii': (1939, 1945), 'world war i': (1914, 1918),
    'the great war': (1914, 1918), 'the cold war': (1947, 1991),
    'the vietnam war': (1955, 1975), 'the korean war': (1950, 1953),
    'the civil war': (1861, 1865), 'the american civil war': (1861, 1865),
    'the napoleonic wars': (1803, 1815), 'the seven years war': (1756, 1763),
    "the seven years ' war": (1756, 1763),
    'the french revolutionary wars': (1792, 1802),
    'the french revolution': (1789, 1799),
    'the american revolutionary war': (1775, 1783),
    'the american revolution': (1765, 1783),
    'the iraq war': (2003, 2011), 'the bosnian war': (1992, 1995),
    'the gulf war': (1990, 1991), 'the spanish civil war': (1936, 1939),
    'the boer war': (1899, 1902), 'the crimean war': (1853, 1856),
    'the thirty years war': (1618, 1648), 'the hundred years war': (1337, 1453),
    'the war of 1812': (1812, 1815), 'the second world war': (1939, 1945),
    'the first world war': (1914, 1918),
}


def _o(y, m=1, d=1):
    try:
        return datetime.date(max(y, 1), m, d).toordinal() + (0 if y >= 1 else (y-1)*366)
    except ValueError:
        try:
            return datetime.date(max(y, 1), m, calendar.monthrange(max(y, 1), m)[1]).toordinal()
        except ValueError:
            return datetime.date(max(y, 1), 1, 1).toordinal()


def _yspan(y):
    return _o(y, 1, 1), _o(y, 12, 31)


def _mspan(y, m):
    return _o(y, m, 1), _o(y, m, calendar.monthrange(max(y, 1), m)[1])


def _num(tok):
    tok = tok.strip().lower()
    if tok.isdigit():
        return int(tok)
    return NUMW.get(tok)


def _clean(s):
    s = s.strip().lower()
    s = s.replace('‑', '-').replace('–', '-').replace('—', '-')
    s = re.sub(r"\s*'\s*", ' ', s)          # "seven years ' war"
    s = re.sub(r'\s*,\s*', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s


def normalize(surface, ref_year=None, ref_date=None):
    s = _clean(surface)
    if not s:
        return None
    bare = re.sub(r'^the ', '', s)

    # --- H1 su kien co ten -------------------------------------------------
    for k in (s, bare, 'the ' + bare):
        if k in NAMED:
            a, b = NAMED[k]
            return _o(a, 1, 1), _o(b, 12, 31), 'year', 'gazetteer'
    m = re.match(r'^the (end|beginning|start) of (.+)$', s)
    if m and (m.group(2) in NAMED or 'the ' + m.group(2) in NAMED):
        a, b = NAMED.get(m.group(2)) or NAMED['the ' + m.group(2)]
        y = b if m.group(1) == 'end' else a
        return _yspan(y) + ('year', 'gazetteer')

    # --- H2 truoc Cong nguyen ----------------------------------------------
    m = re.match(r'^(\d{1,4})\s*(bc|bce)$', s)
    if m:
        y = -int(m.group(1))
        return _o(y, 1, 1), _o(y, 12, 31), 'year', 'regex'

    # --- H3 the ky (co modifier) -------------------------------------------
    m = re.match(r'^(?:the )?(early|mid|middle|late)?[- ]?(\d{1,2})(?:st|nd|rd|th)[- ]century$', s)
    if m:
        c = int(m.group(2)); lo, hi = (c-1)*100+1, c*100
        mod = m.group(1)
        if mod == 'early':
            hi = lo + 33
        elif mod in ('mid', 'middle'):
            lo, hi = lo+33, lo+66
        elif mod == 'late':
            lo = hi - 33
        return _o(lo, 1, 1), _o(hi, 12, 31), 'century', 'regex'

    # --- H4 thap nien (co modifier) ----------------------------------------
    m = re.match(r'^(?:the )?(early|mid|middle|late)?[- ]?(\d{3,4})s$', s)
    if m:
        y = int(m.group(2)); lo, hi = y, y+9
        mod = m.group(1)
        if mod == 'early':
            hi = y+3
        elif mod in ('mid', 'middle'):
            lo, hi = y+3, y+6
        elif mod == 'late':
            lo = y+6
        return _o(lo, 1, 1), _o(hi, 12, 31), 'decade', 'regex'

    # --- H5 modifier + NAM: "mid-2012", "early 1990" -----------------------
    m = re.match(r'^(?:the )?(early|mid|middle|late|end of|beginning of)[- ](\d{3,4})$', s)
    if m:
        y = int(m.group(2)); mod = m.group(1)
        if mod in ('early', 'beginning of'):
            return _o(y, 1, 1), _o(y, 4, 30), 'month', 'regex'
        if mod in ('mid', 'middle'):
            return _o(y, 5, 1), _o(y, 8, 31), 'month', 'regex'
        return _o(y, 9, 1), _o(y, 12, 31), 'month', 'regex'

    # --- H6 khoang nam -----------------------------------------------------
    m = re.match(r'^(\d{3,4})\s*-\s*(\d{1,4})$', s)
    if m:
        a = int(m.group(1)); b = int(m.group(2))
        if b < 100:
            b = a - a % 100 + b
        if b >= a:
            return _o(a, 1, 1), _o(b, 12, 31), 'year', 'regex'

    # --- H7 ngay day du ----------------------------------------------------
    m = re.match(r'^([a-z]+) (\d{1,2}) (\d{3,4})$', s)
    if m and m.group(1) in MONTHS:
        o = _o(int(m.group(3)), MONTHS[m.group(1)], int(m.group(2)))
        return o, o, 'day', 'regex'
    m = re.match(r'^(\d{1,2}) ([a-z]+) (\d{3,4})$', s)
    if m and m.group(2) in MONTHS:
        o = _o(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)))
        return o, o, 'day', 'regex'

    # --- H8 thang + nam ----------------------------------------------------
    m = re.match(r'^(?:(early|mid|middle|late)[- ])?([a-z]+) (\d{3,4})$', s)
    if m and m.group(2) in MONTHS:
        y, mo = int(m.group(3)), MONTHS[m.group(2)]
        a, b = _mspan(y, mo)
        mod = m.group(1)
        if mod == 'early':
            b = _o(y, mo, 10)
        elif mod in ('mid', 'middle'):
            a, b = _o(y, mo, 11), _o(y, mo, 20)
        elif mod == 'late':
            a = _o(y, mo, 21)
        return a, b, 'month', 'regex'

    # --- H9 nam tran -------------------------------------------------------
    m = re.match(r'^(\d{3,4})$', s)
    if m:
        return _yspan(int(m.group(1))) + ('year', 'regex')

    # ======================= CAN THAM CHIEU =================================
    ry = ref_year
    if ry is None and ref_date is not None:
        ry = datetime.date.fromordinal(max(ref_date, 1)).year

    # --- H10 thang + ngay thieu nam ---------------------------------------
    m = re.match(r'^(?:(early|mid|middle|late)[- ])?([a-z]+) (\d{1,2})$', s)
    if m and m.group(2) in MONTHS and ry:
        o = _o(ry, MONTHS[m.group(2)], int(m.group(3)))
        return o, o, 'day', 'refprop'
    m = re.match(r'^(\d{1,2}) ([a-z]+)$', s)
    if m and m.group(2) in MONTHS and ry:
        o = _o(ry, MONTHS[m.group(2)], int(m.group(1)))
        return o, o, 'day', 'refprop'

    # --- H11 thang tran / modifier + thang --------------------------------
    m = re.match(r'^(?:the )?(?:month of )?(?:(early|mid|middle|late)[- ])?([a-z]+)$', s)
    if m and m.group(2) in MONTHS and ry:
        mo = MONTHS[m.group(2)]
        a, b = _mspan(ry, mo)
        mod = m.group(1)
        if mod == 'early':
            b = _o(ry, mo, 10)
        elif mod in ('mid', 'middle'):
            a, b = _o(ry, mo, 11), _o(ry, mo, 20)
        elif mod == 'late':
            a = _o(ry, mo, 21)
        return a, b, 'month', 'refprop'

    # --- H12 thu trong tuan (ke ca so nhieu) ------------------------------
    m = re.match(r'^(?:the |that |on |every )?(' + '|'.join(WD) + r')s?$', s)
    if m and ref_date:
        want = WD[m.group(1)]
        cur = datetime.date.fromordinal(max(ref_date, 1)).weekday()
        o = ref_date + (want - cur) % 7
        return o, o, 'day', 'refprop'

    # --- H13 moc tuong doi theo NGAY --------------------------------------
    if ref_date:
        if re.match(r'^(the |early |later )?(next|following) (day|morning|afternoon|evening|night)s?$', s):
            return ref_date+1, ref_date+1, 'day', 'refprop'
        if re.match(r'^(the )?(previous|preceding|prior) (day|night|morning)$', s):
            return ref_date-1, ref_date-1, 'day', 'refprop'
        if re.match(r'^(the )?(same|that|this) (day|night|morning|afternoon|evening|time)$', s) \
           or re.match(r'^(later |earlier )?that (day|night|morning)$', s) \
           or s in ('today', 'now', 'currently', 'then', 'overnight', 'midnight', 'noon',
                    'the night', 'the day', 'the morning', 'the time', 'this time'):
            return ref_date, ref_date, 'day', 'refprop'
        m = re.match(r'^(?:the )?(?:next|following|first|second|third|final|last) (\w+)$', s)
        if m and m.group(1) in ('week', 'month', 'year', 'weeks', 'months', 'years'):
            u = m.group(1).rstrip('s')
            n = int(UNIT_D[u])
            return ref_date, ref_date+n, u if u in ('month', 'year') else 'day', 'refprop'
        # "a few days later", "hours later", "twenty years later"
        m = re.match(r'^(?:the )?(?:about |nearly |almost )?(?:a |an )?(?:few |couple of |several |many )?'
                     r'(\w+)?\s*(second|minute|hour|day|week|month|year|decade|centurie|century)s?'
                     r'\s*(later|earlier|after|before|ago)?$', s)
        if m and m.group(2):
            n = _num(m.group(1)) if m.group(1) else 1
            if n is None:
                n = 1
            delta = int(n * UNIT_D[m.group(2)])
            direction = m.group(3)
            if direction in ('later', 'after'):
                return ref_date+delta, ref_date+delta, 'day', 'refprop'
            if direction in ('earlier', 'before', 'ago'):
                return ref_date-delta, ref_date-delta, 'day', 'refprop'
            return None, delta, 'duration', 'regex'
        # gio dong ho -> cung ngay tham chieu
        if re.match(r'^\d{1,2}[:.]\d{2}(\s*(am|pm))?$', s) or re.match(r'^\d{1,2}\s*(am|pm)$', s):
            return ref_date, ref_date, 'time', 'refprop'
        # so tran 1-31 = ngay trong thang tham chieu
        m = re.match(r'^(\d{1,2})$', s)
        if m and 1 <= int(m.group(1)) <= 31:
            rd = datetime.date.fromordinal(max(ref_date, 1))
            try:
                o = _o(rd.year, rd.month, int(m.group(1)))
                return o, o, 'day', 'refprop'
            except Exception:
                pass

    # --- H14 moc tuong doi theo NAM ---------------------------------------
    if ry:
        if re.match(r'^(that|the same|this|the) year$', s):
            return _yspan(ry) + ('year', 'refprop')
        if re.match(r'^(the )?(next|following) year$', s):
            return _yspan(ry+1) + ('year', 'refprop')
        if re.match(r'^(the )?(previous|last|prior) year$', s):
            return _yspan(ry-1) + ('year', 'refprop')
        if re.match(r'^(earlier|later) (that|this) year$', s):
            return _yspan(ry) + ('year', 'refprop')
        if re.match(r'^the end of the year$', s):
            return _o(ry, 10, 1), _o(ry, 12, 31), 'month', 'refprop'
        if re.match(r'^the (beginning|start) of the year$', s):
            return _o(ry, 1, 1), _o(ry, 3, 31), 'month', 'refprop'
        # mua
        SEA = {'spring': (3, 5), 'summer': (6, 8), 'autumn': (9, 11), 'fall': (9, 11)}
        m = re.match(r'^(?:the )?(spring|summer|autumn|fall)(?: of)?\s*(\d{3,4})?$', s)
        if m:
            a, b = SEA[m.group(1)]
            y = int(m.group(2)) if m.group(2) else ry
            return _o(y, a, 1), _o(y, b, calendar.monthrange(max(y, 1), b)[1]), 'month', \
                ('regex' if m.group(2) else 'refprop')
        m = re.match(r'^(?:the )?winter(?: of)?\s*(\d{3,4})?$', s)
        if m:
            y = int(m.group(1)) if m.group(1) else ry
            return _o(y, 12, 1), _o(y+1, 2, 28), 'month', ('regex' if m.group(1) else 'refprop')

    # --- H14b "the end/beginning of <thang>" thieu nam --------------------
    if ry:
        m = re.match(r'^the (end|beginning|start|middle) of (?:the month of )?([a-z]+)$', s)
        if m and m.group(2) in MONTHS:
            mo = MONTHS[m.group(2)]
            last = calendar.monthrange(max(ry, 1), mo)[1]
            if m.group(1) == 'end':
                return _o(ry, mo, max(last-9, 1)), _o(ry, mo, last), 'month', 'refprop'
            if m.group(1) == 'middle':
                return _o(ry, mo, 11), _o(ry, mo, 20), 'month', 'refprop'
            return _o(ry, mo, 1), _o(ry, mo, 10), 'month', 'refprop'
        if re.match(r'^the end of the (month|week|day)$', s) and ref_date:
            u = re.match(r'^the end of the (month|week|day)$', s).group(1)
            n = {'month': 30, 'week': 7, 'day': 0}[u]
            return ref_date + n, ref_date + n, 'day', 'refprop'

    # --- H14c so thu tu ngay trong su kien: "the first/second day" --------
    ORD = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5,
           'sixth': 6, 'seventh': 7, 'eighth': 8, 'ninth': 9, 'tenth': 10}
    m = re.match(r'^(?:the |on the )?(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|final|last)'
                 r' (day|night|morning|week|month|year)$', s)
    if m and ref_date:
        u = m.group(2)
        if m.group(1) in ('final', 'last'):
            return ref_date, ref_date, 'day', 'refprop'
        n = ORD[m.group(1)] - 1
        mult = {'day': 1, 'night': 1, 'morning': 1, 'week': 7, 'month': 30, 'year': 365}[u]
        o = ref_date + n * mult
        return o, o, 'day', 'refprop'

    # --- H15 THOI LUONG thuan (khong can tham chieu) ----------------------
    m = re.match(r'^(?:the )?(?:about |nearly |almost |over |more than |less than )?'
                 r'(?:a |an )?(?:few |couple of |several |many )?(\w+)?[- ]?'
                 r'(second|minute|hour|day|week|month|year|decade|centurie|century)s?$', s)
    if m and m.group(2):
        n = _num(m.group(1)) if m.group(1) else 1
        if n is None:
            n = 1
        return None, int(n * UNIT_D[m.group(2)]), 'duration', 'regex'
    # so nhieu tran: "days", "years", "decades", "centuries"
    m = re.match(r'^(?:the )?(second|minute|hour|day|week|month|year|decade|centurie|century)s$', s)
    if m:
        return None, int(3 * UNIT_D[m.group(1)]), 'duration', 'regex'

    return None


def doc_reference_chain(timex_list, normalize_fn=normalize):
    """Truyen tham chieu HAI LUOT.

    LUOT 1: giai cac moc TUYET DOI (khong can tham chieu) -> tim moc mac dinh cua tai lieu
    LUOT 2: giai lai tat ca, cac moc tuong doi nam TRUOC moc tuyet doi dau tien
            se bam vao moc mac dinh do (thay vi that bai — day la loi cold-start cua v1)
    """
    # --- luot 1: chi cac moc tuyet doi ---
    abs_first = None
    abs_year = None
    for tid, surface in timex_list:
        r = normalize_fn(surface, ref_year=None, ref_date=None)
        if r and r[0] is not None and r[2] in ('day', 'month', 'year', 'decade', 'century'):
            if abs_first is None:
                abs_first = r[0]
                try:
                    abs_year = datetime.date.fromordinal(max(r[0], 1)).year
                except Exception:
                    pass

    # --- luot 2: truyen xuoi, khoi tao bang moc mac dinh cua tai lieu ---
    out = {}
    ref_date = abs_first
    ref_year = abs_year
    for tid, surface in timex_list:
        r = normalize_fn(surface, ref_year=ref_year, ref_date=ref_date)
        out[tid] = r
        if r and r[0] is not None and r[2] in ('day', 'month', 'year', 'time'):
            ref_date = r[0]
            try:
                ref_year = datetime.date.fromordinal(max(r[0], 1)).year
            except Exception:
                pass
    return out
