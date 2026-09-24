"""EXP26 - TAI LAP quy trinh sinh ung vien WD-411 cua PaTeCon.

Quy trinh cua ho (§6.1.1): so dump 2019 voi Wikidata hien tai, fact BI XOA = ung vien sai.
Ta co WD50K (trich tu dump 2019) + API Wikidata cong khai -> tai lap duoc buoc 1-3.

Dong thoi do luon DO CHINH XAC THAT (truong precision) de tach:
   - fact bi xoa vi SAI          (error)
   - fact bi xoa vi THO HON      (refinement)  <- tieu chi cua ho GOP CHUNG hai cai nay
"""
import urllib.request, json, time, collections, random, sys

random.seed(20261012)
UA = {'User-Agent': 'TempEKG-research/1.0 (academic reproduction study)'}
N = int(sys.argv[1]) if len(sys.argv) > 1 else 600

rows = [l.strip().split('\t') for l in open('patecon_data/WD50K_official.tsv', encoding='utf-8') if l.strip()]
by = collections.defaultdict(list)
for r in rows:
    if len(r) >= 5:
        by[r[1]].append(r)

# lay mau theo dung phan bo property cua WD-411 (Table 5)
WD411_DIST = {'P569': 159, 'P570': 103, 'P54': 55}
total = sum(WD411_DIST.values())
sample = []
for p, k in WD411_DIST.items():
    take = min(len(by[p]), int(N * k / total))
    sample += random.sample(by[p], take)
random.shuffle(sample)
print('mau: %d fact  %s' % (len(sample), collections.Counter(r[1] for r in sample)))


def fetch(qids):
    url = ('https://www.wikidata.org/w/api.php?action=wbgetentities&ids=%s'
           '&props=claims&format=json' % '|'.join(qids))
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.load(r).get('entities', {})
        except Exception:
            time.sleep(2 * (attempt + 1))
    return {}


def norm_time(t):
    """+1732-02-22T00:00:00Z -> 17320222"""
    try:
        y = int(t[1:5]); m = int(t[6:8]); d = int(t[9:11])
        return '%04d%02d%02d' % (y, m, d)
    except Exception:
        return None


ents = {}
uniq = sorted({r[0] for r in sample})
t0 = time.time()
for i in range(0, len(uniq), 50):
    ents.update(fetch(uniq[i:i+50]))
    time.sleep(0.3)
print('lay %d entity trong %.0fs' % (len(ents), time.time() - t0))
print()

stat = collections.Counter()
prec_all = collections.Counter()
refine_ex, gone_ex = [], []

for r in sample:
    q, p, o = r[0], r[1], r[2]
    cl = ents.get(q, {}).get('claims', {}).get(p, [])
    vals = []
    for c in cl:
        dv = c['mainsnak'].get('datavalue', {}).get('value', {})
        if 'time' in dv:
            nt = norm_time(dv['time'])
            if nt:
                vals.append((nt, dv.get('precision')))
    if not cl:
        stat['entity/property KHONG con'] += 1
        continue
    exact = [v for v in vals if v[0] == o]
    if exact:
        stat['CON NGUYEN (khop chinh xac)'] += 1
        prec_all[exact[0][1]] += 1
        continue
    same_year = [v for v in vals if v[0][:4] == o[:4]]
    if same_year:
        if o[4:] == '0101':
            stat['THO HON -> da lam min (refinement)'] += 1
            if len(refine_ex) < 4:
                refine_ex.append((q, p, o, same_year[0]))
        else:
            stat['doi ngay trong cung nam'] += 1
    else:
        stat['BI XOA hoan toan (ung vien SAI)'] += 1
        if len(gone_ex) < 4:
            gone_ex.append((q, p, o, vals[:1]))

tot = sum(stat.values())
print('=' * 68)
print('TAI LAP SINH UNG VIEN WD-411 (mau %d fact tu WD50K)' % tot)
print('=' * 68)
for k, v in stat.most_common():
    print('  %-42s %5d %6.1f%%' % (k, v, 100*v/tot))
print()
print('  phan bo precision cua fact CON NGUYEN:',
      {('nam' if k == 9 else 'thang' if k == 10 else 'ngay' if k == 11 else k): v
       for k, v in prec_all.most_common()})
fake = prec_all[9] + prec_all[10]
tp = sum(prec_all.values())
print('  -> %d/%d = %.1f%% fact CON NGUYEN thuc su la do chinh xac NAM/THANG'
      % (fake, tp, 100*fake/max(tp, 1)))
print('     (dataset PaTeCon ghi tat ca thanh YYYYMMDD)')
print()
if refine_ex:
    print('vi du THO HON -> LAM MIN (tieu chi cua ho se coi la "sai"):')
    for q, p, o, v in refine_ex:
        print('   %s %s: dump2019=%s  ->  nay=%s (precision=%s)' % (q, p, o, v[0], v[1]))
if gone_ex:
    print()
    print('vi du BI XOA hoan toan (ung vien SAI that su):')
    for q, p, o, v in gone_ex:
        print('   %s %s: dump2019=%s  ->  nay=%s' % (q, p, o, v))
