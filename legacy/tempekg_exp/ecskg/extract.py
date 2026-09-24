"""Text tho -> mentions. KHONG dung nhan vang khi suy dien.

Nguyen tac (theo yeu cau): nhan TIMEX vang KHONG bao gio vao do thi. No la tap
KIEM CHUNG. Do thi phai tu tim lay bieu thuc thoi gian trong van ban.

ECS-KG dung spaCy (POS/NER/dep). May nay khong co spaCy nen:
  - THUC THE  : chuoi token viet hoa  (thuan quy tac, khong hoc)
  - THOI GIAN : regex tren token thô  (thuan quy tac, khong hoc)
  - SU KIEN   : tu dien trigger HOC TU SPLIT TRAIN, ap len token tho cua TEST
                (hop le: hoc tu nhan, suy dien khong can nhan)

Chat luong trich xuat la BIEN DO DUOC, khong phai gia dinh.
"""
from __future__ import annotations
import re, collections

MONTH = {m: i+1 for i, m in enumerate(
    ['january', 'february', 'march', 'april', 'may', 'june', 'july',
     'august', 'september', 'october', 'november', 'december'])}
MONTH.update({m[:3]: i+1 for m, i in list(MONTH.items())})
ORD = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5}

YEAR = re.compile(r'^\d{3,4}$')
YEAR_S = re.compile(r'^(\d{3,4})s$')
DAY = re.compile(r'^([0-3]?\d)(st|nd|rd|th)?$')
ISO = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')

REL = {'today', 'yesterday', 'tomorrow', 'now', 'currently', 'recently',
       'later', 'earlier', 'then', 'afterwards', 'previously', 'meanwhile',
       'subsequently', 'eventually', 'simultaneously'}
DUR_UNIT = {'second', 'seconds', 'minute', 'minutes', 'hour', 'hours',
            'day', 'days', 'week', 'weeks', 'month', 'months',
            'year', 'years', 'decade', 'decades', 'century', 'centuries'}
NUMWORD = {'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6,
           'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10, 'eleven': 11, 'twelve': 12}
SEASON = {'spring': 3, 'summer': 6, 'autumn': 9, 'fall': 9, 'winter': 12}
STOPCAP = {'The', 'A', 'An', 'In', 'On', 'At', 'It', 'He', 'She', 'They', 'This',
           'That', 'These', 'Those', 'But', 'And', 'However', 'After', 'Before',
           'During', 'When', 'While', 'His', 'Her', 'Their', 'Its', 'As', 'By',
           'For', 'From', 'To', 'With', 'Of', 'Although', 'Because', 'Since',
           'Also', 'Then', 'There', 'Both', 'Some', 'Many', 'Most', 'One', 'Two'}


# =============================================================== THOI GIAN
def find_timex(tokens):
    """Tim span thoi gian trong MOT cau token. -> [(i, j, surface, ttype)]"""
    out = []
    n = len(tokens)
    i = 0
    while i < n:
        w = tokens[i]
        lw = w.lower()

        # ISO 1999-01-31
        if ISO.match(w):
            out.append((i, i+1, w, 'DATE')); i += 1; continue

        # "12 January 1999" / "January 12 , 1999" / "January 1999"
        if lw.rstrip('.') in MONTH:
            j = i + 1
            # ngay theo sau
            if j < n and DAY.match(tokens[j]):
                j += 1
                if j < n and tokens[j] == ',':
                    j += 1
            if j < n and YEAR.match(tokens[j]):
                j += 1
            # ngay dung TRUOC thang
            k = i
            if i > 0 and DAY.match(tokens[i-1]) and not YEAR.match(tokens[i-1]):
                k = i - 1
            out.append((k, j, ' '.join(tokens[k:j]), 'DATE')); i = j; continue

        # thap nien 1990s
        if YEAR_S.match(w):
            out.append((i, i+1, w, 'DATE')); i += 1; continue

        # nam tran, phai co ngu canh thoi gian de tranh nham so
        if YEAR.match(w) and 1000 <= int(w) <= 2100:
            prev = tokens[i-1].lower() if i > 0 else ''
            if prev in ('in', 'by', 'since', 'until', 'from', 'to', 'of',
                        'before', 'after', 'during', ',', 'between', 'around'):
                out.append((i, i+1, w, 'DATE')); i += 1; continue
            if i+1 < n and tokens[i+1] in (',', '.', ')'):
                out.append((i, i+1, w, 'DATE')); i += 1; continue

        # mua: "summer of 1944", "the winter"
        if lw in SEASON:
            j = i+1
            if j+1 < n and tokens[j].lower() == 'of' and YEAR.match(tokens[j+1]):
                j += 2
            elif j < n and YEAR.match(tokens[j]):
                j += 1
            out.append((i, j, ' '.join(tokens[i:j]), 'DATE')); i = j; continue

        # thoi luong: "three years", "18 months"
        if (lw in NUMWORD or w.isdigit()) and i+1 < n and tokens[i+1].lower() in DUR_UNIT:
            out.append((i, i+2, ' '.join(tokens[i:i+2]), 'DURATION')); i += 2; continue

        # the ky: "the 19th century"
        if lw == 'century' and i > 0:
            k = i-1
            if k > 0 and tokens[k-1].lower() == 'the':
                k -= 1
            out.append((k, i+1, ' '.join(tokens[k:i+1]), 'DATE')); i += 1; continue

        # tuong doi
        if lw in REL:
            out.append((i, i+1, w, 'DATE')); i += 1; continue

        # lap: "every year", "annually"
        if lw in ('annually', 'monthly', 'weekly', 'daily', 'yearly'):
            out.append((i, i+1, w, 'SET')); i += 1; continue
        if lw == 'every' and i+1 < n and tokens[i+1].lower() in DUR_UNIT:
            out.append((i, i+2, ' '.join(tokens[i:i+2]), 'SET')); i += 2; continue

        i += 1
    return out


# =============================================================== THUC THE
def find_entities(tokens, sent_start=True):
    """Chuoi token viet hoa -> ung vien thuc the. Thuan quy tac."""
    out = []
    n = len(tokens)
    i = 0
    while i < n:
        w = tokens[i]
        if not (w[:1].isupper() and w[:1].isalpha()):
            i += 1; continue
        if i == 0 and w in STOPCAP:
            i += 1; continue
        if w in STOPCAP and i > 0 and tokens[i-1] in ('.', '!', '?'):
            i += 1; continue
        j = i
        while j < n and tokens[j][:1].isupper() and tokens[j][:1].isalpha():
            j += 1
            # cho phep "of"/"the" o giua: "University of X"
            if j < n and tokens[j] in ('of', 'the', 'and') and \
               j+1 < n and tokens[j+1][:1].isupper():
                j += 1
        surf = ' '.join(tokens[i:j])
        if len(surf) > 1:
            out.append((i, j, surf))
        i = max(j, i+1)
    return out


# =============================================================== SU KIEN
class TriggerLexicon:
    """Hoc tu dien trigger tu split TRAIN, ap len token tho cua TEST.

    Hop le voi rang buoc cua bai: HOC dung nhan, SUY DIEN khong dung nhan.
    """

    def __init__(self):
        self.lex = {}          # tu (thuong) -> (etype pho bien nhat, ti le kich hoat)
        self.min_rate = 0.25
        self.min_count = 3

    def fit(self, docs_tokens, docs_triggers):
        """docs_tokens: [[[tok]]]  docs_triggers: [{(sent,i): etype}]"""
        cnt = collections.Counter()
        pos = collections.Counter()
        typ = collections.defaultdict(collections.Counter)
        for toks, trig in zip(docs_tokens, docs_triggers):
            for s, sent in enumerate(toks):
                for i, w in enumerate(sent):
                    lw = w.lower()
                    cnt[lw] += 1
                    if (s, i) in trig:
                        pos[lw] += 1
                        typ[lw][trig[(s, i)]] += 1
        for w, c in cnt.items():
            if pos[w] >= self.min_count and pos[w]/c >= self.min_rate:
                self.lex[w] = (typ[w].most_common(1)[0][0], pos[w]/c)
        return self

    def find(self, tokens):
        """-> [(i, i+1, surface, etype, conf)]"""
        out = []
        for i, w in enumerate(tokens):
            e = self.lex.get(w.lower())
            if e:
                out.append((i, i+1, w, e[0], e[1]))
        return out


# =============================================================== gop
class Extraction:
    __slots__ = ('doc_id', 'events', 'entities', 'times')

    def __init__(self, doc_id):
        self.doc_id = doc_id
        self.events = []     # (sent, i, j, surface, etype, conf)
        self.entities = []   # (sent, i, j, surface)
        self.times = []      # (sent, i, j, surface, ttype)


def extract_doc(doc_id, sentences, lexicon):
    """sentences: [[token]] — CHI token tho, khong nhan."""
    ex = Extraction(doc_id)
    for s, toks in enumerate(sentences):
        for i, j, surf, ttype in find_timex(toks):
            ex.times.append((s, i, j, surf, ttype))
        tspans = {(i, j) for i, j, _, _ in find_timex(toks)}
        tcov = {k for i, j, _, _ in find_timex(toks) for k in range(i, j)}
        for i, j, surf in find_entities(toks):
            if not (set(range(i, j)) & tcov):
                ex.entities.append((s, i, j, surf))
        for i, j, surf, et, c in lexicon.find(toks):
            if i not in tcov:
                ex.events.append((s, i, j, surf, et, c))
    return ex
