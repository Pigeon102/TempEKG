"""Quet TOAN BO WD50K qua Wikidata API -> dung tap gan nhan kieu WD-411,
nhung TACH duoc ERROR khoi REFINEMENT (dieu WD-411 khong lam duoc).

Nhan dau ra cho moi fact:
  ALIVE       fact con nguyen (khop chinh xac)      -> DUNG
  COARSE      gia tri that co precision NAM/THANG   -> do chinh xac GIA trong dataset
  REFINED     0101 bi thay bang ngay chinh xac      -> THO HON, khong sai
  CHANGED     doi ngay trong cung nam               -> nghi ngo
  DELETED     bien mat hoan toan                    -> UNG VIEN SAI
  NOPROP      entity/property khong con
"""
import urllib.request, json, time, collections, os, sys

UA = {'User-Agent': 'TempEKG-research/1.0 (academic reproduction study)'}
CACHE = 'patecon_data/wd_claims_cache.json'
OUT = 'patecon_data/wd50k_labeled.tsv'

rows = [l.strip().split('\t') for l in open('patecon_data/WD50K_official.tsv', encoding='utf-8') if l.strip()]
rows = [r for r in rows if len(r) >= 5]
props = sorted({r[1] for r in rows})
uniq = sorted({r[0] for r in rows})
print('fact %d | entity %d | property %s' % (len(rows), len(uniq), props), flush=True)

cache = {}
if os.path.exists(CACHE):
    cache = json.load(open(CACHE, encoding='utf-8'))
    print('cache co san: %d entity' % len(cache), flush=True)


def fetch(qids):
    url = ('https://www.wikidata.org/w/api.php?action=wbgetentities&ids=%s'
           '&props=claims&format=json' % '|'.join(qids))
    for a in range(4):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r).get('entities', {})
        except Exception:
            time.sleep(3 * (a + 1))
    return {}


def norm_time(t):
    try:
        return '%04d%02d%02d' % (int(t[1:5]), int(t[6:8]), int(t[9:11]))
    except Exception:
        return None


todo = [q for q in uniq if q not in cache]
print('can lay them: %d entity (~%.0f phut)' % (len(todo), len(todo)/50*3.3/60), flush=True)
t0 = time.time()
for i in range(0, len(todo), 50):
    ents = fetch(todo[i:i+50])
    for q in todo[i:i+50]:
        e = ents.get(q, {})
        slim = {}
        for p in props:
            vals = []
            for c in e.get('claims', {}).get(p, []):
                ms = c['mainsnak']
                dv = ms.get('datavalue', {}).get('value', {})
                if isinstance(dv, dict) and 'time' in dv:
                    nt = norm_time(dv['time'])
                    if nt:
                        vals.append([nt, dv.get('precision')])
                elif isinstance(dv, dict) and 'id' in dv:
                    vals.append([dv['id'], None])
            if vals:
                slim[p] = vals
        cache[q] = slim
    if (i // 50) % 20 == 0:
        done = i + 50
        el = time.time() - t0
        print('  %d/%d  %.0fs  (con ~%.0f phut)'
              % (done, len(todo), el, (len(todo)-done)/max(done, 1)*el/60), flush=True)
        json.dump(cache, open(CACHE, 'w', encoding='utf-8'))
    time.sleep(0.25)
json.dump(cache, open(CACHE, 'w', encoding='utf-8'))
print('lay xong %d entity trong %.0f phut' % (len(cache), (time.time()-t0)/60), flush=True)

# ---------- gan nhan ----------
stat = collections.Counter()
out = []
for r in rows:
    q, p, o = r[0], r[1], r[2]
    cl = cache.get(q, {}).get(p)
    if not cl:
        lab = 'NOPROP'
    else:
        exact = [v for v in cl if v[0] == o]
        if exact:
            pr = exact[0][1]
            lab = 'COARSE' if pr in (9, 10) else 'ALIVE'
        else:
            sy = [v for v in cl if str(v[0])[:4] == o[:4]] if o[:4].isdigit() else []
            if sy:
                lab = 'REFINED' if o[4:] == '0101' else 'CHANGED'
            else:
                lab = 'DELETED'
    stat[lab] += 1
    out.append('\t'.join(r[:5]) + '\t' + lab)

open(OUT, 'w', encoding='utf-8', newline='\n').write('\n'.join(out))
tot = sum(stat.values())
print()
print('=' * 60)
print('TAP GAN NHAN WD50K (%d fact) -> %s' % (tot, OUT))
print('=' * 60)
for k, v in stat.most_common():
    print('  %-10s %7d %6.1f%%' % (k, v, 100*v/tot))
print()
print('  UNG VIEN SAI (DELETED+NOPROP) : %d = %.1f%%'
      % (stat['DELETED']+stat['NOPROP'], 100*(stat['DELETED']+stat['NOPROP'])/tot))
print('  DO CHINH XAC GIA (COARSE)     : %d = %.1f%%' % (stat['COARSE'], 100*stat['COARSE']/tot))
print('  THO HON, KHONG SAI (REFINED)  : %d = %.1f%%' % (stat['REFINED'], 100*stat['REFINED']/tot))
