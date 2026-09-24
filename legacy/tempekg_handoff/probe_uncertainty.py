"""Three probes on the Phase-2 spec + a first test of the graded-uncertainty direction.

E1  G2 gate, measured exactly: how many signatures survive >=10-DOCUMENT support?
E2  Spurious-UNSAT risk: BEFORE(i,j) pairs where both events hang off the SAME TIMEX.
E3  Build a deterministic TIMEX normaliser, then measure:
    (a) granularity CONFLICT base rate on multi-anchor events (intersection emptiness)
    (b) ANCHOR-vs-BEFORE contradictions  <- never measured; the real detection target
    (c) gap distribution by event-type pair -> is MAGNITUDE CONFLICT a real class?
"""
import json, zipfile, io, re, collections, os, statistics
from datetime import date

os.chdir(r'C:/Reseach_Quang')

MON = {m: i + 1 for i, m in enumerate(
    ['January', 'February', 'March', 'April', 'May', 'June', 'July',
     'August', 'September', 'October', 'November', 'December'])}
NEG, POS = -9000000, 9000000


def D(y, m, d):
    try:
        return date(y, m, d).toordinal()
    except ValueError:
        return None


def year_win(y):
    return (D(y, 1, 1), D(y, 12, 31))


def month_win(y, m):
    lo = D(y, m, 1)
    nm_y, nm_m = (y + 1, 1) if m == 12 else (y, m + 1)
    hi = D(nm_y, nm_m, 1) - 1
    return (lo, hi) if lo and hi else (None, None)


def norm(surface, ref_year):
    """-> (lo, hi, precision, resolver) or None. precision: 11=day 10=month 9=year 8=decade 7=century"""
    s = surface.strip()
    m = re.match(r'^(\d{3,4})$', s)
    if m:
        lo, hi = year_win(int(m.group(1)))
        return (lo, hi, 9, 'regex') if lo else None
    m = re.match(r'^(\d{3,4})\s*[-\u2013]\s*(\d{2,4})$', s)
    if m:
        y1 = int(m.group(1)); y2 = int(m.group(2))
        if y2 < 100:
            y2 = y1 - (y1 % 100) + y2
        a, _ = year_win(y1); _, b = year_win(y2)
        return (a, b, 9, 'regex') if a and b and b >= a else None
    m = re.match(r'^([A-Z][a-z]+)\s+(\d{1,2})\s*,\s*(\d{3,4})$', s)
    if m and m.group(1) in MON:
        o = D(int(m.group(3)), MON[m.group(1)], int(m.group(2)))
        return (o, o, 11, 'regex') if o else None
    m = re.match(r'^(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{3,4})$', s)
    if m and m.group(2) in MON:
        o = D(int(m.group(3)), MON[m.group(2)], int(m.group(1)))
        return (o, o, 11, 'regex') if o else None
    m = re.match(r'^([A-Z][a-z]+)\s+(\d{3,4})$', s)
    if m and m.group(1) in MON:
        lo, hi = month_win(int(m.group(2)), MON[m.group(1)])
        return (lo, hi, 10, 'regex') if lo else None
    m = re.match(r'^(\d{3,4})s$', s)
    if m:
        y = int(m.group(1)); a, _ = year_win(y); _, b = year_win(y + 9)
        return (a, b, 8, 'regex') if a and b else None
    # ---- reference-time propagation (year-less) ----
    if ref_year:
        m = re.match(r'^([A-Z][a-z]+)\s+(\d{1,2})$', s)
        if m and m.group(1) in MON:
            o = D(ref_year, MON[m.group(1)], int(m.group(2)))
            return (o, o, 11, 'refprop') if o else None
        m = re.match(r'^(\d{1,2})\s+([A-Z][a-z]+)$', s)
        if m and m.group(2) in MON:
            o = D(ref_year, MON[m.group(2)], int(m.group(1)))
            return (o, o, 11, 'refprop') if o else None
        if s in MON:
            lo, hi = month_win(ref_year, MON[s])
            return (lo, hi, 10, 'refprop') if lo else None
    return None


# ---------------- load ----------------
z = zipfile.ZipFile('MAVEN-Arg.zip')
arg = {}
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            arg[d['id']] = d

stat = collections.Counter()
gran = collections.Counter()
anchor_before_viol = 0
anchor_before_ok = 0
gaps_by_pair = collections.defaultdict(list)
all_gaps = []
same_timex_before = 0
before_pairs_total = 0
sig_docs = collections.defaultdict(set)
sig_pairs = collections.Counter()
norm_hit = collections.Counter()

for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        doc = d['id']
        if doc not in arg:
            continue
        evset = {e['id'] for e in d['events']}
        etype = {e['id']: e['type'] for e in d['events']}
        tx = {t['id']: t for t in d['TIMEX']}

        # reference year = first resolvable year in document order
        ref_year = None
        for t in sorted(d['TIMEX'], key=lambda x: (x['sent_id'], x['offset'][0])):
            r = norm(t['mention'], None)
            if r and r[2] in (9, 10, 11):
                ref_year = date.fromordinal(r[0]).year
                break

        txnorm = {}
        for tid, t in tx.items():
            r = norm(t['mention'], ref_year)
            norm_hit['resolved' if r else 'unresolved'] += 1
            if r:
                txnorm[tid] = r

        # ---- anchors: CONTAINS(timex, event) ----
        anchors = collections.defaultdict(list)
        ev_timex = collections.defaultdict(set)
        for rel, ps in d['temporal_relations'].items():
            if rel not in ('CONTAINS', 'SIMULTANEOUS'):
                continue
            for h, t in ps:
                if h in tx and t in evset:
                    ev_timex[t].add(h)
                    if h in txnorm:
                        anchors[t].append(txnorm[h])
                elif t in tx and h in evset:
                    ev_timex[h].add(t)
                    if t in txnorm:
                        anchors[h].append(txnorm[t])

        # ---- E3a granularity verdict ----
        for ev, ans in anchors.items():
            if len(ans) < 2:
                continue
            lo = max(a[0] for a in ans); hi = min(a[1] for a in ans)
            stat['multianchor_resolved'] += 1
            gran['CONFLICT' if lo > hi else 'COMPAT'] += 1

        # ---- interval per event ----
        iv = {}
        for ev, ans in anchors.items():
            lo = max(a[0] for a in ans); hi = min(a[1] for a in ans)
            if lo <= hi:
                iv[ev] = (lo, hi, max(a[2] for a in ans))

        # ---- E2 + E3b + E3c over BEFORE ----
        for h, t in d['temporal_relations'].get('BEFORE', []):
            if h not in evset or t not in evset:
                continue
            before_pairs_total += 1
            if ev_timex[h] & ev_timex[t]:
                same_timex_before += 1
            if h in iv and t in iv:
                lo_i, hi_i, _ = iv[h]
                lo_j, hi_j, _ = iv[t]
                if hi_j < lo_i:                     # anchors force j entirely before i
                    anchor_before_viol += 1
                else:
                    anchor_before_ok += 1
                    g = lo_j - hi_i                 # guaranteed minimum gap in days
                    all_gaps.append(g)
                    gaps_by_pair[(etype[h], etype[t])].append(g)

        # ---- E1 doc-clustered support ----
        a = arg[doc]
        ent2ev = collections.defaultdict(set)
        roles = collections.defaultdict(set)
        for e in a['events']:
            for r, vs in (e.get('argument') or {}).items():
                for v in vs:
                    if 'entity_id' in v:
                        ent2ev[v['entity_id']].add(e['id'])
                        roles[(e['id'], v['entity_id'])].add(r)
        rel_pairs = set()
        for rel, ps in d['temporal_relations'].items():
            for hh, tt in ps:
                if hh in evset and tt in evset:
                    rel_pairs.add(tuple(sorted([hh, tt])))
        seen = set()
        for ent, evs in ent2ev.items():
            evs = sorted(evs)
            for i in range(len(evs)):
                for j in range(i + 1, len(evs)):
                    p = (evs[i], evs[j])
                    if p not in rel_pairs:
                        continue
                    for ra in sorted(roles[(evs[i], ent)]):
                        for rb in sorted(roles[(evs[j], ent)]):
                            if (evs[i], evs[j], ra, rb) in seen:
                                continue
                            seen.add((evs[i], evs[j], ra, rb))
                            sig = (etype[evs[i]], ra, etype[evs[j]], rb)
                            sig_docs[sig].add(doc)
                            sig_pairs[sig] += 1

print('=' * 78)
print('NORMALISER (deterministic regex + reference-time propagation)')
tot = sum(norm_hit.values())
print('  TIMEX resolved: %d / %d = %.1f%%' % (norm_hit['resolved'], tot, 100 * norm_hit['resolved'] / tot))
print()
print('=' * 78)
print('E1  G2 GATE, MEASURED (plan estimated 600-1,200 surviving)')
for th in (5, 10, 20):
    n = sum(1 for s, ds in sig_docs.items() if len(ds) >= th)
    print('  (T1,r1,T2,r2) signatures with >= %2d DOCUMENTS : %5d' % (th, n))
n10p = sum(1 for s, c in sig_pairs.items() if c >= 10)
print('  ...for reference, >= 10 PAIRS                   : %5d' % n10p)
print()
print('=' * 78)
print('E2  SPURIOUS-UNSAT RISK (strict BEFORE at zero days)')
print('  event-event BEFORE pairs                        : %d' % before_pairs_total)
print('  ...where BOTH events hang off the SAME TIMEX    : %d (%.1f%%)'
      % (same_timex_before, 100 * same_timex_before / before_pairs_total))
print('  -> every one of these becomes UNSAT if a day-precision anchor')
print('     collapses both events to the same point.')
print()
print('=' * 78)
print('E3a GRANULARITY CONFLICT BASE RATE (multi-anchor, both resolved)')
mt = gran['CONFLICT'] + gran['COMPAT']
if mt:
    print('  multi-anchor events with all anchors resolved   : %d' % mt)
    print('  intersection EMPTY (CONFLICT)                   : %d (%.1f%%)'
          % (gran['CONFLICT'], 100 * gran['CONFLICT'] / mt))
    print('  intersection non-empty (COMPAT/REFINEMENT)      : %d (%.1f%%)'
          % (gran['COMPAT'], 100 * gran['COMPAT'] / mt))
print()
print('=' * 78)
print('E3b ANCHOR-vs-BEFORE CONTRADICTIONS  <-- never measured before')
tt = anchor_before_viol + anchor_before_ok
if tt:
    print('  BEFORE pairs with both events anchored          : %d' % tt)
    print('  anchors CONTRADICT the BEFORE edge              : %d (%.2f%%)'
          % (anchor_before_viol, 100 * anchor_before_viol / tt))
    print('  -> compare with ~72 total contradictions found by BEFORE-only closure')
print()
print('=' * 78)
print('E3c GAP DISTRIBUTION -> is MAGNITUDE CONFLICT a real class?')
if all_gaps:
    g = sorted(all_gaps)
    def q(p):
        return g[min(len(g) - 1, int(p * len(g)))]
    print('  BEFORE pairs with a computable minimum gap     : %d' % len(g))
    print('  quantiles (days): q10=%d q25=%d q50=%d q75=%d q90=%d q99=%d max=%d'
          % (q(.10), q(.25), q(.50), q(.75), q(.90), q(.99), g[-1]))
    print('  gap > 1 year  : %d (%.1f%%)' % (sum(1 for x in g if x > 366), 100 * sum(1 for x in g if x > 366) / len(g)))
    print('  gap > 10 years: %d (%.1f%%)' % (sum(1 for x in g if x > 3653), 100 * sum(1 for x in g if x > 3653) / len(g)))
    print('  gap > 50 years: %d (%.1f%%)' % (sum(1 for x in g if x > 18262), 100 * sum(1 for x in g if x > 18262) / len(g)))
    big = [(k, v) for k, v in gaps_by_pair.items() if len(v) >= 30]
    print()
    print('  type pairs with >=30 observations              : %d' % len(big))
    print('  --- widest-spread type pairs (candidate MAGNITUDE constraints) ---')
    rows = []
    for k, v in big:
        vs = sorted(v)
        rows.append((vs[min(len(vs) - 1, int(.9 * len(vs)))], k, len(vs),
                     vs[min(len(vs) - 1, int(.5 * len(vs)))]))
    rows.sort(reverse=True)
    for q90, k, n, med in rows[:12]:
        print('    %-46s n=%4d  median=%6d  q90=%7d days' % (k[0] + ' -> ' + k[1], n, med, q90))
