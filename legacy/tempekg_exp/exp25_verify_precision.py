"""EXP25 - KIEM CHUNG TRUC TIEP: cac gia tri "0101" trong conflict cua PaTeCon
co that su la DO CHINH XAC NAM khong?

Wikidata luu ma precision: 9=nam, 10=thang, 11=ngay.
PaTeCon pad het ve YYYYMMDD nen MAT thong tin nay.

Truy van Wikidata hien tai cho cac fact trong conflict, doi chieu precision that.
Neu gia tri 0101 co precision=9 -> XAC NHAN la nam-only, conflict la GIA.
"""
import urllib.request, json, time, re, collections, sys

UA = {'User-Agent': 'TempEKG-research/1.0 (academic reproduction study)'}
cache = {}


def get_claims(qid, pid):
    k = (qid, pid)
    if k in cache:
        return cache[k]
    url = ('https://www.wikidata.org/w/api.php?action=wbgetclaims'
           '&entity=%s&property=%s&format=json' % (qid, pid))
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.load(r)
        out = []
        for c in d.get('claims', {}).get(pid, []):
            dv = c['mainsnak'].get('datavalue', {}).get('value', {})
            if 'time' in dv:
                out.append((dv['time'], dv.get('precision')))
    except Exception:
        # thu lai 2 lan voi backoff
        out = None
        for wait in (2, 5):
            time.sleep(wait)
            try:
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=25) as r:
                    d = json.load(r)
                out = []
                for c in d.get('claims', {}).get(pid, []):
                    dv = c['mainsnak'].get('datavalue', {}).get('value', {})
                    if 'time' in dv:
                        out.append((dv['time'], dv.get('precision')))
                break
            except Exception:
                continue
    cache[k] = out
    time.sleep(1.1)
    return out


# ---- lay cac conflict GIA (cung nam, mot ben 0101) ----
rows = [l for l in open('patecon/output/WD50K_off.all_conflicts', encoding='utf-8') if l.strip()]
spurious = []
for l in rows:
    p = l.rstrip('\n').split('\t')
    if len(p) < 3:
        continue
    facts = []
    for f in p[1:3]:
        c = f.split(',')
        if len(c) >= 3:
            facts.append((c[0], c[1], c[2]))
    if len(facts) < 2:
        continue
    d = [f[2] for f in facts]
    if not all(x.isdigit() and len(x) == 8 for x in d):
        continue
    if d[0][:4] == d[1][:4] and ((d[0][4:] == '0101') != (d[1][4:] == '0101')):
        spurious.append(facts)

print('conflict GIA tim duoc: %d' % len(spurious))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
sample = spurious[:N]
print('kiem chung %d mau dau tien qua Wikidata API...' % len(sample))
print()

PREC = {9: 'NAM', 10: 'THANG', 11: 'NGAY'}
verdict = collections.Counter()
shown = 0
for facts in sample:
    qid, pid = facts[0][0], facts[0][1]
    cl = get_claims(qid, pid)
    if cl is None:
        verdict['loi API'] += 1
        continue
    # gia tri 0101 trong cap nay
    jan = [f for f in facts if f[2][4:] == '0101']
    if not jan:
        continue
    y = jan[0][2][:4]
    match = [(t, p) for t, p in cl if re.match(r'^[+-]?0*%s-' % y, t)]
    if not match:
        verdict['fact da BI XOA khoi Wikidata'] += 1
        if shown < 6:
            print('  %s %s %s -> DA BI XOA (ung vien WD-411!)' % (qid, pid, jan[0][2]))
            shown += 1
        continue
    p = match[0][1]
    verdict['precision=%s (%s)' % (p, PREC.get(p, '?'))] += 1
    if shown < 6:
        print('  %s %s %s -> Wikidata: %s precision=%s (%s)'
              % (qid, pid, jan[0][2], match[0][0][:11], p, PREC.get(p, '?')))
        shown += 1

print()
print('=' * 60)
tot = sum(verdict.values())
for k, v in verdict.most_common():
    print('  %-42s %4d %5.0f%%' % (k, v, 100 * v / max(tot, 1)))
yearprec = sum(v for k, v in verdict.items() if 'precision=9' in k)
print()
print('  => %d/%d = %.0f%% gia tri "0101" THUC SU la DO CHINH XAC NAM'
      % (yearprec, tot, 100 * yearprec / max(tot, 1)))
print('     -> conflict tuong ung la GIA, xac nhan bang chinh Wikidata')
