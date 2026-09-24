"""EXP34 - KIEM CHUNG tren WD27M (dataset THU HAI, doc lap voi WD50K).

Moi ket qua truoc chi tren WD50K. Day la kiem chung tong quat hoa.
WD27M: 27 trieu fact, 93 temporal property (WD50K chi 6).

Lay mau ~12k entity KHONG co trong WD50K, gan nhan qua Wikidata API,
roi so PaTeCon vs TempEKG.
"""
import collections, random, json, os, sys, time, urllib.request

random.seed(20261012)
UA = {'User-Agent': 'TempEKG-research/1.0 (academic reproduction study)'}
CACHE = 'patecon_data/wd27m_cache.json'
N_ENT = int(sys.argv[1]) if len(sys.argv) > 1 else 12000

wd50 = {l.split('\t')[0] for l in open('patecon_data/WD50K_official.tsv', encoding='utf-8')}
print('WD50K: %d entity' % len(wd50), flush=True)

# ---- doc WD27M, chi giu property co trong WD50K de so sanh cong bang ----
KEEP = {'P569', 'P570', 'P54', 'P26', 'P108', 'P286'}
by_ent = collections.defaultdict(list)
n = 0
with open('patecon_data/WD27M.tsv', encoding='utf-8', errors='ignore') as f:
    for line in f:
        p = line.rstrip('\n').split('\t')
        if len(p) < 5 or p[1] not in KEEP:
            continue
        if p[0] in wd50:
            continue
        n += 1
        by_ent[p[0]].append(p)
print('WD27M (6 property, khong trung WD50K): %d fact | %d entity' % (n, len(by_ent)), flush=True)

ents = sorted(by_ent)
random.shuffle(ents)
sample_ents = ents[:N_ENT]
rows = [r for e in sample_ents for r in by_ent[e]]
print('mau: %d entity | %d fact' % (len(sample_ents), len(rows)), flush=True)
print('property:', dict(collections.Counter(r[1] for r in rows).most_common()), flush=True)
open('patecon_data/WD27M_sample.tsv', 'w', encoding='utf-8', newline='\n').write(
    '\n'.join('\t'.join(r[:5]) for r in rows))

# ---- gan nhan qua API ----
cache = json.load(open(CACHE, encoding='utf-8')) if os.path.exists(CACHE) else {}


def fetch(qids):
    url = ('https://www.wikidata.org/w/api.php?action=wbgetentities&ids=%s'
           '&props=claims&format=json' % '|'.join(qids))
    for a in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r).get('entities', {})
        except Exception:
            time.sleep(3*(a+1))
    return {}


def norm_time(t):
    """SUA LOI NGAY AM: giu dau, khong dung t[1:5] mu quang"""
    try:
        neg = t.startswith('-')
        body = t[1:] if t[0] in '+-' else t
        y = int(body[0:4]); mo = int(body[5:7]); d = int(body[8:10])
        return ('-' if neg else '') + '%04d%02d%02d' % (y, mo, d)
    except Exception:
        return None


todo = [q for q in sample_ents if q not in cache]
print('can lay: %d entity (~%.0f phut)' % (len(todo), len(todo)/50*3.3/60), flush=True)
t0 = time.time()
for i in range(0, len(todo), 50):
    e = fetch(todo[i:i+50])
    for q in todo[i:i+50]:
        slim = {}
        for p in KEEP:
            vals = []
            for c in e.get(q, {}).get('claims', {}).get(p, []):
                dv = c['mainsnak'].get('datavalue', {}).get('value', {})
                if isinstance(dv, dict) and 'time' in dv:
                    nt = norm_time(dv['time'])
                    if nt:
                        vals.append([nt, dv.get('precision')])
                elif isinstance(dv, dict) and 'id' in dv:
                    vals.append([dv['id'], None])
            if vals:
                slim[p] = vals
        cache[q] = slim
    if (i//50) % 20 == 0:
        json.dump(cache, open(CACHE, 'w', encoding='utf-8'))
        print('  %d/%d  %.0fs' % (i+50, len(todo), time.time()-t0), flush=True)
    time.sleep(0.25)
json.dump(cache, open(CACHE, 'w', encoding='utf-8'))
print('lay xong %.0f phut' % ((time.time()-t0)/60), flush=True)

# ---- gan nhan ----
stat = collections.Counter()
out = []
for r in rows:
    q, p, o = r[0], r[1], r[2]
    cl = cache.get(q, {}).get(p)
    if not cl:
        lab = 'NOPROP'
    else:
        exact = [v for v in cl if str(v[0]) == o]
        if exact:
            lab = 'COARSE' if exact[0][1] in (9, 10) else 'ALIVE'
        else:
            sy = [v for v in cl if str(v[0])[:4] == o[:4]] if o[:4].isdigit() else []
            lab = ('REFINED' if o[4:] == '0101' else 'CHANGED') if sy else 'DELETED'
    stat[lab] += 1
    out.append('\t'.join(r[:5]) + '\t' + lab)
open('patecon_data/WD27M_labeled.tsv', 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
tot = sum(stat.values())
print()
print('NHAN (%d fact):' % tot)
for k, v in stat.most_common():
    print('  %-10s %6d %6.1f%%' % (k, v, 100*v/tot))
