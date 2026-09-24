"""TIMEX normaliser cho MAVEN.

MAVEN-ERE cho SPAN nhung KHONG cho gia tri chuan hoa. Do truoc day:
  62.1% xu ly duoc bang regex thuan
  37.9% can ngu canh, gom 4 ho: ngay tuong doi, ngay thieu nam, thoi ky co ten, thu trong tuan

Ket qua: (lo, hi, granularity) voi lo/hi la so ngay proleptic Gregorian.
granularity in {day, month, year, decade, century, duration, unknown}
"""
import re, datetime, calendar

MONTHS = {m.lower(): i for i, m in enumerate(calendar.month_name) if m}
MONTHS.update({m.lower(): i for i, m in enumerate(calendar.month_abbr) if m})

NAMED = {   # gazetteer thoi ky co ten (do duoc: WWII x70, WWI x30...)
    'world war ii': (1939, 1945), 'the second world war': (1939, 1945),
    'second world war': (1939, 1945), 'wwii': (1939, 1945),
    'world war i': (1914, 1918), 'the first world war': (1914, 1918),
    'first world war': (1914, 1918), 'wwi': (1914, 1918),
    'the great war': (1914, 1918), 'the cold war': (1947, 1991),
    'cold war': (1947, 1991), 'the vietnam war': (1955, 1975),
    'the korean war': (1950, 1953), 'the civil war': (1861, 1865),
    'the american civil war': (1861, 1865),
}

UNITS = {'second': 1/86400, 'minute': 1/1440, 'hour': 1/24, 'day': 1, 'week': 7,
         'month': 30.44, 'year': 365.25, 'decade': 3652.5, 'century': 36525}
NUMW = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7,
        'eight': 8, 'nine': 9, 'ten': 10, 'a': 1, 'an': 1, 'several': 3, 'few': 3}


def _ord(y, m=1, d=1):
    try:
        return datetime.date(y, m, d).toordinal()
    except ValueError:
        return datetime.date(y, m, 1).toordinal()


def _year_span(y):
    return _ord(y, 1, 1), _ord(y, 12, 31)


def _month_span(y, m):
    return _ord(y, m, 1), _ord(y, m, calendar.monthrange(y, m)[1])


def normalize(surface, ref_year=None, ref_date=None):
    """tra ve (lo, hi, gran, method) hoac None"""
    s = surface.strip().lower()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s*,\s*', ' ', s)

    # ---- 1. thoi ky co ten (gazetteer) ----
    key = re.sub(r'^the ', '', s)
    for k in (s, key):
        if k in NAMED:
            a, b = NAMED[k]
            return _ord(a, 1, 1), _ord(b, 12, 31), 'year', 'gazetteer'

    # ---- 2. the ky ----
    m = re.match(r'^(?:the )?(\d{1,2})(?:st|nd|rd|th) century$', s)
    if m:
        c = int(m.group(1))
        return _ord((c-1)*100+1, 1, 1), _ord(c*100, 12, 31), 'century', 'regex'

    # ---- 3. thap nien: 1970s ----
    m = re.match(r'^(?:the )?(\d{3,4})s$', s)
    if m:
        y = int(m.group(1))
        return _ord(y, 1, 1), _ord(y+9, 12, 31), 'decade', 'regex'

    # ---- 4. khoang nam: 1778-1780 ----
    m = re.match(r'^(\d{3,4})\s*[-–]\s*(\d{2,4})$', s)
    if m:
        a = int(m.group(1)); b = int(m.group(2))
        if b < 100:
            b = a - a % 100 + b
        return _ord(a, 1, 1), _ord(b, 12, 31), 'year', 'regex'

    # ---- 5. ngay thang nam day du ----
    m = re.match(r'^([a-z]+) (\d{1,2}) (\d{3,4})$', s)          # November 11 1778
    if m and m.group(1) in MONTHS:
        y, mo, d = int(m.group(3)), MONTHS[m.group(1)], int(m.group(2))
        o = _ord(y, mo, d)
        return o, o, 'day', 'regex'
    m = re.match(r'^(\d{1,2}) ([a-z]+) (\d{3,4})$', s)          # 11 November 1778
    if m and m.group(2) in MONTHS:
        y, mo, d = int(m.group(3)), MONTHS[m.group(2)], int(m.group(1))
        o = _ord(y, mo, d)
        return o, o, 'day', 'regex'

    # ---- 6. thang + nam ----
    m = re.match(r'^([a-z]+) (\d{3,4})$', s)
    if m and m.group(1) in MONTHS:
        y, mo = int(m.group(2)), MONTHS[m.group(1)]
        a, b = _month_span(y, mo)
        return a, b, 'month', 'regex'

    # ---- 7. nam tran ----
    m = re.match(r'^(\d{3,4})$', s)
    if m:
        a, b = _year_span(int(m.group(1)))
        return a, b, 'year', 'regex'

    # ---- 8. THIEU NAM: "September 11" -> dung nam tham chieu ----
    m = re.match(r'^([a-z]+) (\d{1,2})$', s)
    if m and m.group(1) in MONTHS and ref_year:
        o = _ord(ref_year, MONTHS[m.group(1)], int(m.group(2)))
        return o, o, 'day', 'refprop'
    m = re.match(r'^([a-z]+)$', s)
    if m and m.group(1) in MONTHS and ref_year:
        a, b = _month_span(ref_year, MONTHS[m.group(1)])
        return a, b, 'month', 'refprop'

    # ---- 8b. NGAY TRUOC THANG, thieu nam: "1 july" ----
    m = re.match(r'^(\d{1,2}) ([a-z]+)$', s)
    if m and m.group(2) in MONTHS and ref_year:
        o = _ord(ref_year, MONTHS[m.group(2)], int(m.group(1)))
        return o, o, 'day', 'refprop'

    # ---- 8c. SO TRAN 1-31 = ngay trong thang tham chieu ----
    m = re.match(r'^(\d{1,2})$', s)
    if m and ref_date:
        dd = int(m.group(1))
        if 1 <= dd <= 31:
            rd = datetime.date.fromordinal(ref_date)
            try:
                o = _ord(rd.year, rd.month, dd)
                return o, o, 'day', 'refprop'
            except Exception:
                pass

    # ---- 8d. MODIFIER + thang: "early September" ----
    m = re.match(r'^(early|mid|middle of|late|the end of|the beginning of|beginning of|end of)\s+([a-z]+)$', s)
    if m and m.group(2) in MONTHS and ref_year:
        mo = MONTHS[m.group(2)]
        last = calendar.monthrange(ref_year, mo)[1]
        mod = m.group(1)
        if mod in ('early', 'the beginning of', 'beginning of'):
            return _ord(ref_year, mo, 1), _ord(ref_year, mo, 10), 'month', 'refprop'
        if mod in ('mid', 'middle of'):
            return _ord(ref_year, mo, 11), _ord(ref_year, mo, 20), 'month', 'refprop'
        return _ord(ref_year, mo, 21), _ord(ref_year, mo, last), 'month', 'refprop'

    # ---- 8e. MODIFIER + nam: "early 1945" ----
    m = re.match(r'^(early|mid|middle of|late|the end of|the beginning of)\s+(\d{3,4})$', s)
    if m:
        y = int(m.group(2)); mod = m.group(1)
        if mod in ('early', 'the beginning of'):
            return _ord(y, 1, 1), _ord(y, 4, 30), 'month', 'regex'
        if mod in ('mid', 'middle of'):
            return _ord(y, 5, 1), _ord(y, 8, 31), 'month', 'regex'
        return _ord(y, 9, 1), _ord(y, 12, 31), 'month', 'regex'

    # ---- 8f. MUA ----
    SEASON = {'spring': (3, 5), 'summer': (6, 8), 'autumn': (9, 11), 'fall': (9, 11), 'winter': (12, 2)}
    m = re.match(r'^(?:the )?(spring|summer|autumn|fall|winter)(?:\s+of)?\s*(\d{3,4})?$', s)
    if m:
        a, b = SEASON[m.group(1)]
        y = int(m.group(2)) if m.group(2) else ref_year
        if y:
            if a > b:      # mua dong vat nam
                return _ord(y, 12, 1), _ord(y + 1, 2, 28), 'month', 'refprop'
            last = calendar.monthrange(y, b)[1]
            return _ord(y, a, 1), _ord(y, b, last), 'month', 'refprop' if not m.group(2) else 'regex'

    # ---- 9. NGAY TUONG DOI: "the next day", "the following day" ----
    if ref_date:
        if re.match(r'^(the )?(next|following) day$', s):
            return ref_date+1, ref_date+1, 'day', 'refprop'
        if re.match(r'^(the )?(previous|preceding) day$', s):
            return ref_date-1, ref_date-1, 'day', 'refprop'
        if re.match(r'^(the )?same day$', s) or re.match(r'^(later )?that day$', s):
            return ref_date, ref_date, 'day', 'refprop'
        if re.match(r'^(the )?(next|following) year$', s):
            y = datetime.date.fromordinal(ref_date).year + 1
            a, b = _year_span(y)
            return a, b, 'year', 'refprop'
        if re.match(r'^(the )?previous year$', s):
            y = datetime.date.fromordinal(ref_date).year - 1
            a, b = _year_span(y)
            return a, b, 'year', 'refprop'

    # ---- 9b. moc tuong doi bam theo NAM tham chieu ----
    if ref_year:
        if re.match(r'^(that|the same|the) year$', s):
            a, b = _year_span(ref_year)
            return a, b, 'year', 'refprop'
    # ---- 9c. thu trong tuan -> ngay gan nhat tu ref_date ----
    WD = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
          'friday': 4, 'saturday': 5, 'sunday': 6}
    m = re.match(r'^(?:the |that |on )?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)$', s)
    if m and ref_date:
        want = WD[m.group(1)]
        cur = datetime.date.fromordinal(ref_date).weekday()
        delta = (want - cur) % 7
        o = ref_date + delta
        return o, o, 'day', 'refprop'
    # ---- 9d. dem / buoi trong ngay tham chieu ----
    if ref_date and re.match(r'^(the |that )?(night|morning|afternoon|evening|day)$', s):
        return ref_date, ref_date, 'day', 'refprop'
    if ref_date and re.match(r'^(that|the) time$', s):
        return ref_date, ref_date, 'day', 'refprop'

    # ---- 10. THOI LUONG: "three years", "21 years" ----
    m = re.match(r'^(?:a|an|\d+|one|two|three|four|five|six|seven|eight|nine|ten|several|few)[- ]'
                 r'(second|minute|hour|day|week|month|year|decade|centur)', s)
    if m:
        num = s.split()[0].split('-')[0]
        n = NUMW.get(num, None)
        if n is None:
            try:
                n = int(num)
            except ValueError:
                n = 1
        unit = m.group(1)
        unit = 'century' if unit == 'centur' else unit
        return None, int(n * UNITS[unit]), 'duration', 'regex'

    return None


def doc_reference_chain(timex_list, normalize_fn=normalize):
    """Truyen thoi gian tham chieu theo THU TU VAN BAN (kieu narrative container TimeML).

    Duyet cac TIMEX theo thu tu xuat hien; moi khi giai duoc mot moc TUYET DOI thi
    cap nhat ref, de cac moc TUONG DOI phia sau bam vao.
    """
    out = {}
    ref_date = None
    ref_year = None
    for tid, surface in timex_list:
        r = normalize_fn(surface, ref_year=ref_year, ref_date=ref_date)
        out[tid] = r
        if r and r[3] == 'regex' and r[2] in ('day', 'month', 'year') and r[0]:
            ref_date = r[0]
            ref_year = datetime.date.fromordinal(r[0]).year
    return out
