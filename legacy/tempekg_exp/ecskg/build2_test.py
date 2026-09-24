"""AP CAC PHAT HIEN o §13 vao do thi text, roi do xem do thi CO TOT HON khong.

Chi so quyet dinh: verdict xung dot tu do thi TEXT co khop verdict tren anchor VANG khong.
   - anchor vang -> verdict tham chieu (event nay co that su giao rong khong)
   - do thi text -> verdict du doan
   - do P/R/F1 tren lop CONFLICT

Cau hinh, cong don tung phat hien:
   C0  hien tai      : moi TIMEX cung cau (hoac ca cau truoc), khong loc, giao toan cuc
   C1  + §13.5       : loai SYMBOLIC / DURATION / SET khoi tap anchor
   C2  + §13.1       : giu TOP-K anchor theo diem, thay vi lay het
   C3  + §13.3       : anchor_agg = hull cho kieu su kien KEO DAI
   C4  + §13.2       : gran_src declared vs inferred, chi tin hat do khai bao
"""
import json, collections, random, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from timex_norm2 import normalize, doc_reference_chain
from ecskg.extract import find_timex, TriggerLexicon, REL, DUR_UNIT

random.seed(20261012)

# --- §13.3: kieu su kien KEO DAI -> hull thay vi intersect ---
# CHI hai kieu co bang chung manh o §8.2b (lift 6.98x va 3.74x, CI loai tru 1).
# Ban rong hon (13 kieu) lam recall roi 91.8% -> 53.4%: da thu va that bai.
EXTENDED = {'Military_operation', 'Hostile_encounter'}

docs = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line); docs[d['id']] = d

ids = sorted(docs); random.shuffle(ids)
TRD, TED = ids[:int(.8*len(ids))], ids[int(.8*len(ids)):]

lex = TriggerLexicon().fit(
    [docs[i]['tokens'] for i in TRD],
    [{(m['sent_id'], m['offset'][0]): e['type']
      for e in docs[i]['events'] for m in e['mention'] if 'sent_id' in m} for i in TRD])
print('tu dien trigger: %d' % len(lex.lex), flush=True)

LOC_PREP = {'in', 'on', 'at', 'since', 'until', 'from', 'by', 'during', 'between'}


def gran_src(surface, gran):
    """§13.2: hat do DUOC KHAI BAO neu be mat co du chu so; nguoc lai la SUY DOAN."""
    s = surface.strip()
    digits = sum(c.isdigit() for c in s)
    if gran == 'day' and digits >= 6:
        return 'declared'
    if gran == 'month' and digits >= 4:
        return 'declared'
    if gran == 'year' and digits >= 3:
        return 'declared'
    return 'inferred'


def kind(surface, ttype):
    """§13.5: phan loai ban chat anchor."""
    low = surface.lower()
    if ttype == 'DURATION':
        return 'duration'
    if ttype == 'SET':
        return 'set'
    if low in REL:
        return 'symbolic'
    return 'value'


# ============================================ dung du lieu cho ca hai phia
REF = {}      # (doc, sent, off) -> verdict vang
PRED = {}     # (doc, sent, off) -> danh sach anchor du doan
ETYPE = {}

for i in TED:
    d = docs[i]; toks = d['tokens']

    # ---------- phia VANG ----------
    tl = [(t['id'], t['mention']) for t in
          sorted(d['TIMEX'], key=lambda x: (x['sent_id'], x['offset'][0]))]
    gnorm = doc_reference_chain(tl)
    ganc = collections.defaultdict(list)
    for h, t in d['temporal_relations'].get('CONTAINS', []):
        if h in gnorm: ganc[t].append(h)
        if t in gnorm: ganc[h].append(t)
    for e in d['events']:
        ms = [(m['sent_id'], m['offset'][0]) for m in e['mention'] if 'sent_id' in m]
        if not ms: continue
        key = (i,) + min(ms)
        iv = []
        for tid in ganc.get(e['id'], []):
            r = gnorm.get(tid)
            if r and r[0] is not None and r[2] != 'duration':
                iv.append((r[0], r[1]))
        if len(iv) >= 2:
            REF[key] = int(max(a[0] for a in iv) > min(a[1] for a in iv))
        ETYPE[key] = e['type']

    # ---------- phia TEXT ----------
    tx = []
    ry = rd = None
    for s, tk in enumerate(toks):
        for a, b, surf, tt in find_timex(tk):
            r = normalize(surf, ref_year=ry, ref_date=rd)
            k = kind(surf, tt)
            lo = hi = g = None
            if r and r[0] is not None:
                lo, hi, g = r[0], r[1], r[2]
                if g in ('day', 'month', 'year'):
                    ry = lo//10000
                    if g == 'day': rd = lo
            tx.append({'s': s, 'i': a, 'j': b, 'surf': surf, 'kind': k,
                       'lo': lo, 'hi': hi, 'gran': g,
                       'gsrc': gran_src(surf, g) if g else 'inferred',
                       'prev': tk[a-1].lower() if a > 0 else ''})
    by_sent = collections.defaultdict(list)
    for t in tx: by_sent[t['s']].append(t)

    for s, tk in enumerate(toks):
        for a, b, surf, et, c in lex.find(tk):
            cand = list(by_sent.get(s, []))
            same = True
            if not cand:
                prev = [t for t in tx if t['s'] < s]
                if prev:
                    m = max(t['s'] for t in prev)
                    cand = [t for t in prev if t['s'] == m]
                    same = False
            if not cand: continue
            # diem gan: cung cau + gan trigger + co gioi tu thoi gian dan
            for t in cand:
                d_ = abs(t['i']-a)
                t['score'] = (2.0 if same else 0.0) \
                    + (1.0 if t['prev'] in LOC_PREP else 0.0) \
                    + 1.0/(1+d_/5.0)
            PRED[(i, s, a)] = sorted(cand, key=lambda x: -x['score'])
            ETYPE.setdefault((i, s, a), et)

print('event co verdict VANG: %d | event co anchor TEXT: %d' % (len(REF), len(PRED)), flush=True)


# ============================================ cac cau hinh
def verdict(anchors, etype, cfg):
    """-> 1 conflict, 0 khong, None khong xet duoc"""
    a = anchors
    if cfg >= 1:                                  # §13.5 loai symbolic/duration/set
        a = [t for t in a if t['kind'] == 'value']
    a = [t for t in a if t['lo'] is not None]
    if cfg >= 4:                                  # §13.2 chi tin hat do khai bao
        decl = [t for t in a if t['gsrc'] == 'declared']
        if len(decl) >= 2:
            a = decl
    if cfg >= 2:                                  # §13.1 top-k
        a = a[:2]
    if len(a) < 2:
        return None
    if cfg >= 5:                                  # siet: doi CA HAI anchor CUNG CAU
        ss = collections.Counter(t['s'] for t in a)
        top = ss.most_common(1)[0]
        if top[1] < 2:
            return None
        a = [t for t in a if t['s'] == top[0]][:2]
    if cfg >= 6:                                  # siet: doi ca hai hat do KHAI BAO
        if not all(t['gsrc'] == 'declared' for t in a):
            return None
    if cfg >= 3 and etype in EXTENDED:            # §13.3 hull, tap HEP
        return 0
    lo = max(t['lo'] for t in a); hi = min(t['hi'] for t in a)
    return int(lo > hi)


NAMES = {0: 'C0 hien tai', 1: 'C1 + loai symbolic (§13.5)',
         2: 'C2 + top-k=2 (§13.1)', 3: 'C3 + hull, tap HEP (§13.3)',
         4: 'C4 + uu tien hat do khai bao (§13.2)',
         5: 'C5 + doi hai anchor CUNG CAU',
         6: 'C6 + doi ca hai hat do KHAI BAO'}

print()
print('='*94)
print('DO THI TEXT CO TOT HON KHONG — verdict so voi anchor VANG')
print('='*94)
print('%-32s %8s %9s %9s %9s %9s %9s'
      % ('cau hinh', 'xet duoc', 'nen text', 'nen vang', 'P', 'R', 'F1'))
print('-'*94)

for cfg in (0, 1, 2, 3, 4, 5, 6):
    tp = fp = fn = tn = 0
    n_pred = n_conf = 0
    for key, anc in PRED.items():
        et = ETYPE.get(key, '?')
        v = verdict(anc, et, cfg)
        if v is None: continue
        n_pred += 1; n_conf += v
        if key not in REF: continue
        g = REF[key]
        if v and g: tp += 1
        elif v and not g: fp += 1
        elif not v and g: fn += 1
        else: tn += 1
    dec = tp+fp+fn+tn
    P = tp/max(tp+fp, 1); R = tp/max(tp+fn, 1)
    print('%-32s %8d %8.1f%% %8.1f%% %8.1f%% %8.1f%% %9.4f'
          % (NAMES[cfg], dec, 100*n_conf/max(n_pred, 1),
             100*(tp+fn)/max(dec, 1), 100*P, 100*R, 2*P*R/max(P+R, 1e-9)))

print()
print('  "nen text" = ti le event bi do thi text gan co (truoc la 80.3%)')
print('  "nen vang" = ti le conflict that tren cac event doi chieu duoc')
print('  P/R/F1 = do tren lop CONFLICT, doi chieu voi verdict vang')
