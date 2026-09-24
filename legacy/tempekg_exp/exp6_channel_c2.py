"""EXP6 - Kenh C2: causal / subevent.

EXP7 da cho biet C2 PHANG (do sau 1, closure them 0.2-0.5%) -> chi can bang canh
truc tiep, khong can adjacency. Gio kiem tra C2 co dang lam mot kenh rieng khong.

Q1. DO PHU: C2 cham toi bao nhieu cap? Bao nhieu cap C2 KHONG cham toi duoc bang C1
    (khong chia se participant)? -> C2 co MO RONG do phu that khong?
Q2. SUC DU DOAN: biet CAUSE(a,b) thi doan duoc nhan thoi gian tot hon majority khong?
Q3. RANG BUOC CUNG: gold vi pham bao nhieu?
       CAUSE(a,b)    => khong duoc after(a,b)
       subevent(p,c) => phai contains(p,c)
Q4. Ap dung quy tac da sua (Wilson + BH-FDR) cho signature C2.
"""
import json, zipfile, io, collections, math, random

random.seed(20261012)

arg = {}
z = zipfile.ZipFile('MAVEN-Arg.zip')
for sp in ['train.jsonl', 'valid.jsonl']:
    with z.open(sp) as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            d = json.loads(line)
            ev = {}
            for e in d['events']:
                offs = [m['offset'][0] for m in e['mention'] if m.get('offset')]
                ents = set()
                for r, vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v:
                            ents.add(v['entity_id'])
                ev[e['id']] = {'type': e['type'], 'pos': min(offs) if offs else 10**9,
                               'ents': ents}
            arg[d['id']] = ev

ere = {}
for split in ['train', 'valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line)
        ere[d['id']] = d

docs = sorted(set(arg) & set(ere))
random.shuffle(docs)
cut = int(0.8 * len(docs))
MINE, EVAL = docs[:cut], docs[cut:]

FWD = {'BEFORE': 'BEFORE_FWD', 'CONTAINS': 'CONTAINS_FWD', 'OVERLAP': 'OVERLAP_FWD',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}
REV = {'BEFORE': 'BEFORE_REV', 'CONTAINS': 'CONTAINS_REV', 'OVERLAP': 'OVERLAP_REV',
       'SIMULTANEOUS': 'SIMULTANEOUS', 'BEGINS-ON': 'SIMULTANEOUS', 'ENDS-ON': 'SIMULTANEOUS'}


def temporal_map(d):
    R = {}
    for rel, ps in d['temporal_relations'].items():
        for h, t in ps:
            if h.startswith('EVENT') and t.startswith('EVENT'):
                R[(h, t)] = rel
    return R


def c2_edges(d):
    """tra ve [(head, tail, kind)] - kind in {CAUSE, PRECONDITION, SUBEVENT}"""
    out = []
    for kind, ps in d.get('causal_relations', {}).items():
        for h, t in ps:
            out.append((h, t, kind))
    for h, t in d.get('subevent_relations', []):
        out.append((h, t, 'SUBEVENT'))
    return out


# ================= Q1: DO PHU =================
n_c2 = n_c2_with_temp = n_c2_no_share = n_c2_no_share_with_temp = 0
for doc in docs:
    ev, R = arg[doc], temporal_map(ere[doc])
    for h, t, kind in c2_edges(ere[doc]):
        if h not in ev or t not in ev:
            continue
        n_c2 += 1
        has_temp = (h, t) in R or (t, h) in R
        share = bool(ev[h]['ents'] & ev[t]['ents'])
        if has_temp:
            n_c2_with_temp += 1
        if not share:
            n_c2_no_share += 1
            if has_temp:
                n_c2_no_share_with_temp += 1

print('=== Q1. DO PHU CUA C2 ===')
print('canh C2 (causal + subevent)        : %d' % n_c2)
print('  ...co ca quan he thoi gian       : %d (%.1f%%)' % (n_c2_with_temp, 100*n_c2_with_temp/n_c2))
print('  ...KHONG chia se participant     : %d (%.1f%%)' % (n_c2_no_share, 100*n_c2_no_share/n_c2))
print('  ...KHONG share VA co quan he t/g : %d' % n_c2_no_share_with_temp)
print('  => C2 mo rong them %d cap ma C1 khong cham toi duoc' % n_c2_no_share_with_temp)

# ================= Q3: RANG BUOC CUNG =================
print()
print('=== Q3. VI PHAM RANG BUOC CUNG TREN GOLD ===')
viol = collections.Counter()
tot = collections.Counter()
missing = collections.Counter()
for doc in docs:
    R = temporal_map(ere[doc])
    for h, t, kind in c2_edges(ere[doc]):
        if kind == 'SUBEVENT':
            tot['SUBEVENT'] += 1
            if (h, t) in R and R[(h, t)] == 'CONTAINS':
                pass
            elif (t, h) in R and R[(t, h)] in ('BEFORE',):
                viol['SUBEVENT: con TRUOC cha'] += 1
            elif (h, t) in R and R[(h, t)] == 'BEFORE':
                viol['SUBEVENT: cha TRUOC con'] += 1
            else:
                missing['SUBEVENT thieu CONTAINS'] += 1
        else:
            tot[kind] += 1
            # nguyen nhan khong duoc xay ra SAU ket qua
            if (t, h) in R and R[(t, h)] == 'BEFORE':
                viol['%s: ket qua TRUOC nguyen nhan' % kind] += 1
for k in sorted(tot):
    print('  %-14s tong=%6d' % (k, tot[k]))
for k in sorted(viol):
    print('  VI PHAM  %-34s %d' % (k, viol[k]))
for k in sorted(missing):
    print('  THIEU    %-34s %d' % (k, missing[k]))

# ================= Q2/Q4: SUC DU DOAN =================
def collect(split_docs, shuffle=False):
    sig = collections.defaultdict(collections.Counter)
    sig_docs = collections.defaultdict(set)
    for doc in split_docs:
        ev, R = arg[doc], temporal_map(ere[doc])
        rows = []
        for h, t, kind in c2_edges(ere[doc]):
            if h not in ev or t not in ev:
                continue
            # sap theo thu tu van ban
            if ev[h]['pos'] <= ev[t]['pos']:
                a, b, flip = h, t, False
            else:
                a, b, flip = t, h, True
            if (a, b) in R:
                lab = FWD.get(R[(a, b)])
            elif (b, a) in R:
                lab = REV.get(R[(b, a)])
            else:
                continue
            if not lab:
                continue
            direction = 'REV' if flip else 'FWD'
            rows.append(((ev[a]['type'], kind, direction, ev[b]['type']), lab, doc))
        if shuffle and rows:
            labs = [r[1] for r in rows]
            random.shuffle(labs)
            rows = [(s, l, d) for (s, _, d), l in zip(rows, labs)]
        for s, lab, dd in rows:
            sig[s][lab] += 1
            sig_docs[s].add(dd)
    return sig, sig_docs


def wilson_lo(k, n, z=1.96):
    if n == 0:
        return 0.0
    p = k / n
    d = 1 + z*z/n
    c = p + z*z/(2*n)
    m = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))
    return (c - m) / d


def binom_sf(k, n, p):
    if k <= 0:
        return 1.0
    return sum(math.comb(n, i) * p**i * (1-p)**(n-i) for i in range(k, n+1))


def bh(pv, alpha=0.05):
    m = len(pv)
    thr = 0.0
    for i, p in enumerate(sorted(pv), 1):
        if p <= i/m*alpha:
            thr = p
    return thr


mine_sig, mine_docs = collect(MINE)
eval_sig, _ = collect(EVAL)
base = collections.Counter()
for c in mine_sig.values():
    base.update(c)
BR = {l: n/sum(base.values()) for l, n in base.items()}
maj_lab, maj_n = base.most_common(1)[0]
maj = maj_n / sum(base.values())

print()
print('=== Q2/Q4. SUC DU DOAN CUA C2 ===')
print('so cap C2 co nhan (MINE): %d' % sum(base.values()))
print('phan bo nhan:', {k: round(v, 3) for k, v in sorted(BR.items(), key=lambda kv: -kv[1])})
print('majority baseline = %s  %.1f%%' % (maj_lab, 100*maj))
print()


def select(sig, sdocs, rule, theta, min_sup=10, min_docs=5):
    cands = []
    for s, c in sig.items():
        n = sum(c.values())
        if n < min_sup:
            continue
        lab, k = c.most_common(1)[0]
        cands.append((s, lab, n, k, len(sdocs[s])))
    if rule == 'old':
        return [x for x in cands if x[3]/x[2] >= theta]
    st = [x for x in cands if wilson_lo(x[3], x[2]) >= theta and x[4] >= min_docs]
    if not st:
        return []
    pv = [binom_sf(k, n, BR.get(lab, .5)) for _, lab, n, k, _ in st]
    thr = bh(pv)
    return [x for x, p in zip(st, pv) if p <= thr]


for theta in (0.9, 0.8, 0.7):
    print('theta=%.1f' % theta)
    for rule in ('old', 'new'):
        sel = select(mine_sig, mine_docs, rule, theta)
        hit = t = 0
        macro = []
        for s, lab, n, k, nd in sel:
            c = eval_sig.get(s)
            if not c:
                continue
            tt = sum(c.values())
            hit += c[lab]; t += tt
            macro.append(c[lab]/tt)
        if t:
            print('  %-4s: %3d signature | phu %5d cap EVAL | micro %.1f%% | macro %.1f%% | vs majority %+.1f'
                  % (rule.upper(), len(sel), t, 100*hit/t, 100*sum(macro)/len(macro),
                     100*hit/t - 100*maj))
        else:
            print('  %-4s: %3d signature | phu 0' % (rule.upper(), len(sel)))
    print()
