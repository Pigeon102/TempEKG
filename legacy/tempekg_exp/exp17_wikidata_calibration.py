"""EXP17 - HIEU CHUAN: chay CHINH phuong phap cua minh tren CHINH du lieu cua PaTeCon.

Van de phuong phap luan (nguoi dung chi ra dung): moi ket qua am tinh tren MAVEN co the
la LOI CODE chu khong phai tinh chat cua MAVEN. Chua bao gio kiem chung implementation
tren du lieu goc.

Phep thu: dung du lieu Wikidata thoi gian (TeCoRe/rockit, cung nguon PaTeCon dan),
chay dung pipeline SP(a) + danh gia theo BAT DONG nhu EXP13.

  - Neu tren Wikidata co bat dong voi majority  -> code DUNG, khac biet la do SUBSTRATE
  - Neu tren Wikidata cung khong bat dong        -> code SAI, phai sua truoc khi ket luan

Doi chieu them: cac rang buoc VIET TAY cua TeCoRe (mln_wiki.cstr) - vd "sinh truoc khi chet",
"khong the choi 2 CLB cung luc" - phuong phap cua minh co tim lai duoc khong?
"""
import re, collections, math, random

random.seed(20261012)

PAT = re.compile(r'pinstConf\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)",\s*"([^"]*)",\s*"([^"]*)",')


def load(path):
    facts = []
    for line in open(path, encoding='utf-8', errors='ignore'):
        m = PAT.search(line)
        if not m:
            continue
        s, p, o, st, en = m.groups()
        facts.append((s, p, o, st, en))
    return facts


def to_int(t):
    """YYYYMM hoac YYYYMMDD -> so sanh duoc; tra ve None neu khong hop le"""
    if not t or t == 'null':
        return None
    t = t.strip()
    if not t.isdigit():
        return None
    # chuan hoa ve YYYYMM
    if len(t) >= 6:
        return int(t[:6])
    if len(t) == 4:
        return int(t) * 100 + 1
    return None


def predicate(s1, e1, s2, e2):
    """tra ve nhan quan he thoi gian giua hai khoang, hoac None neu khong xac dinh"""
    if None in (s1, e1, s2, e2):
        return None
    if e1 < s2:
        return 'BEFORE'
    if e2 < s1:
        return 'AFTER'
    if s1 <= s2 and e2 <= e1:
        return 'INCLUDE'
    if s2 <= s1 and e1 <= e2:
        return 'INCLUDED_BY'
    return 'OVERLAP'


for path, name in (('tempekg_exp/wikidata/wd_10k.csv', 'WD-10k'),
                   ('tempekg_exp/wikidata/wd_50k.csv', 'WD-50k')):
    facts = load(path)
    ent = collections.defaultdict(list)
    for s, p, o, st, en in facts:
        a, b = to_int(st), to_int(en)
        if a is None and b is None:
            continue
        if a is None:
            a = b
        if b is None:
            b = a
        ent[s].append((p, o, a, b))

    print('=' * 66)
    print('%s : %d fact | %d entity | %d entity co >=2 fact co thoi gian'
          % (name, len(facts), len(ent), sum(1 for v in ent.values() if len(v) >= 2)))

    sig = collections.defaultdict(collections.Counter)
    glob = collections.Counter()
    npair = 0
    for e, sts in ent.items():
        if len(sts) < 2:
            continue
        sts = sorted(sts, key=lambda x: (x[2], x[3]))
        for i in range(len(sts)):
            for j in range(i + 1, len(sts)):
                p1, o1, s1, e1 = sts[i]
                p2, o2, s2, e2 = sts[j]
                lab = predicate(s1, e1, s2, e2)
                if lab is None:
                    continue
                npair += 1
                sig[(p1, p2)][lab] += 1
                glob[lab] += 1

    if not glob:
        print('  (khong co cap nao)')
        continue
    MAJ, mn = glob.most_common(1)[0]
    print('  cap co nhan : %d | majority = %s (%.1f%%)' % (npair, MAJ, 100*mn/sum(glob.values())))
    print('  phan bo     :', {k: round(v/sum(glob.values()), 3) for k, v in glob.most_common()})

    def wlo(k, n, z=1.96):
        p = k/n
        d = 1 + z*z/n
        return (p + z*z/(2*n) - z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)))/d

    for sup in (10, 30):
        tot = dis = disw = 0
        examples = []
        for k, c in sig.items():
            n = sum(c.values())
            if n < sup:
                continue
            tot += 1
            lab, kk = c.most_common(1)[0]
            if lab != MAJ:
                dis += 1
                if wlo(kk, n) >= 0.7:
                    disw += 1
                    examples.append((k, lab, n, kk/n))
        print('  support>=%-3d : %4d signature | argmax != majority: %3d (%.1f%%) | qua Wilson>=0.7: %3d'
              % (sup, tot, dis, 100*dis/max(tot, 1), disw))
        if sup == 10 and examples:
            print('     vi du constraint BAT DONG (day la thu MAVEN KHONG HE co):')
            for k, lab, n, cf in sorted(examples, key=lambda x: -x[2])[:8]:
                print('        %-16s -> %-12s n=%-5d conf=%.2f' % (str(k), lab, n, cf))

    # doi chieu rang buoc viet tay
    print('  --- doi chieu rang buoc VIET TAY cua TeCoRe ---')
    for pair, desc in ((('P569', 'P570'), 'sinh truoc khi chet'),
                       (('P569', 'P54'), 'sinh truoc khi choi cho CLB'),
                       (('P569', 'P26'), 'sinh truoc khi ket hon'),
                       (('P54', 'P54'), 'khong choi 2 CLB cung luc'),
                       (('P26', 'P26'), 'khong cuoi 2 nguoi cung luc')):
        c = sig.get(pair)
        if not c:
            print('     %-14s %-32s (khong du du lieu)' % (str(pair), desc))
            continue
        n = sum(c.values())
        lab, kk = c.most_common(1)[0]
        print('     %-14s %-32s n=%-5d -> %-11s conf=%.2f' % (str(pair), desc, n, lab, kk/n))
    print()
