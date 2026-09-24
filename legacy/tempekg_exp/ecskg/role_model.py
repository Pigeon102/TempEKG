"""Bo phan loai VAI: hoc tu MAVEN-Arg, suy dien chi tu TEXT THO.

Thay quy tac vi tri hien tai (truoc trigger -> agentish, sau -> patientish) — quy tac do
BO HAN Location, dung vai chiem 20.1% argument va nhieu nhat trong nghien cuu phep chieu.

Nhan: top-K vai cua MAVEN-Arg + NONE.  top-3 phu 62.8%, top-20 phu 85.7%.
Dac trung: CHI tu van ban (gioi tu, trigger, khoang cach, huong, hinh thai) — khong nhan.
Hoc dung nhan (hop le), suy dien khong dung nhan.

Softmax tren tap vai, mot phan loai cho moi cap (event, ung vien thuc the).
"""
from __future__ import annotations
import json, collections, math, random, zipfile, io, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ecskg.extract import find_entities, find_timex

random.seed(20261012)

LOC_PREP = {'in', 'at', 'near', 'outside', 'inside', 'across', 'around', 'along',
            'throughout', 'within', 'from', 'to', 'toward', 'towards', 'into', 'onto'}
AGT_PREP = {'by'}
PREP = LOC_PREP | AGT_PREP | {'of', 'for', 'with', 'against', 'between', 'among',
                              'on', 'over', 'under', 'about'}
TOPK = 20


def load(split):
    z = zipfile.ZipFile('MAVEN-Arg.zip')
    out = []
    with z.open(split + '.jsonl') as f:
        for line in io.TextIOWrapper(f, encoding='utf-8'):
            out.append(json.loads(line))
    return out


def sentences(d):
    """MAVEN-Arg luu document dang chuoi; dung 'tokens' neu co, khong thi tu tach."""
    if 'tokens' in d:
        return d['tokens']
    return [s.split() for s in d.get('sentences', [])]


def feats(toks, es, eo, trig, et, s, i, j, surf, rank, ncand):
    """Dac trung cho cap (event o cau es vi tri eo, ung vien o cau s span [i,j))."""
    gap = s - es
    g = max(-2, min(2, gap))
    prev = toks[s][i-1].lower() if i > 0 else '<S>'
    prev2 = toks[s][i-2].lower() if i > 1 else '<S>'
    nxt = toks[s][j].lower() if j < len(toks[s]) else '</S>'
    pp = prev if prev in PREP else '_'
    f = {
        'bias': 1,
        'gap': g,
        'dir': 'A' if gap > 0 else ('B' if gap < 0 else 'S'),
        'et': et,
        'trig': trig,
        'prep': pp,
        'prep_loc': int(prev in LOC_PREP),
        'prep_by': int(prev in AGT_PREP),
        'et_prep': '%s>%s' % (et, pp),
        'trig_prep': '%s>%s' % (trig, pp),
        'prev': prev,
        'prev2': prev2,
        'next': nxt if nxt in (',', '.', 'of', 'in', 'on') else '_',
        'rank': min(rank, 4),
        'rank0': int(rank == 0),
        'ncand': min(ncand, 6),
        'len': min(j-i, 4),
        'allcap': int(surf.isupper()),
        'head': surf.split()[-1].lower() if surf.split() else '_',
    }
    if gap == 0:
        d_ = i - eo
        f['tokd'] = max(-4, min(4, d_//3))
        f['after'] = int(d_ > 0)
        lo, hi = (eo, i) if d_ > 0 else (j, eo)
        mid = [w.lower() for w in toks[s][max(lo, 0):max(hi, 0)]]
        f['nmid'] = min(len(mid), 6)
        f['midprep'] = next((w for w in mid if w in PREP), '_')
        f['midcomma'] = int(',' in mid)
        f['et_after'] = '%s|%d' % (et, int(d_ > 0))
    else:
        f['tokd'] = 9; f['after'] = 9; f['nmid'] = 9
        f['midprep'] = '#'; f['midcomma'] = 9; f['et_after'] = '%s|9' % et
    return f


def build_examples(docs, labels=None, use_gold_events=True):
    """-> [(nhom ung vien, nhan)] . nhom = danh sach (feat, role) cho mot event."""
    ex = []
    for d in docs:
        toks = sentences(d)
        if not toks:
            continue
        # span cua argument vang -> role  (CHI dung khi HOC)
        gold = {}
        for e in d['events']:
            for r, vs in (e.get('argument') or {}).items():
                for v in vs:
                    if 'offset' in v and 'sent_id' in v:
                        gold[(e['id'], v['sent_id'], v['offset'][0], v['offset'][1])] = r
        # ung vien thuc the tu VAN BAN
        cands = []
        tcov = collections.defaultdict(set)
        for s, tk in enumerate(toks):
            for a, b, _, _ in find_timex(tk):
                tcov[s] |= set(range(a, b))
            for a, b, surf in find_entities(tk):
                if not (set(range(a, b)) & tcov[s]):
                    cands.append((s, a, b, surf))
        for e in d['events']:
            m = min(((mm['sent_id'], mm['offset'][0], mm.get('trigger_word', ''))
                     for mm in e['mention'] if 'sent_id' in mm), default=None)
            if m is None:
                continue
            es, eo, trig = m[0], m[1], m[2].lower()
            near = [c for c in cands if abs(c[0]-es) <= 1]
            if not near:
                continue
            near = sorted(near, key=lambda c: abs(c[0]-es)*1000+abs(c[1]-eo))[:12]
            grp = []
            for rank, (s, a, b, surf) in enumerate(near):
                f = feats(toks, es, eo, trig, e['type'], s, a, b, surf, rank, len(near))
                r = gold.get((e['id'], s, a, b))
                grp.append((f, r, (e['id'], s, a, b, surf)))
            ex.append(grp)
    return ex


def fit(train_ex, roles, epochs=8, lr=0.2):
    W = {r: collections.defaultdict(float) for r in roles}
    flat = [(f, r if r in roles else 'NONE') for grp in train_ex for f, r, _ in grp]
    print('  vi du huan luyen: %d | co vai: %d'
          % (len(flat), sum(1 for _, r in flat if r != 'NONE')), flush=True)
    for ep in range(epochs):
        random.shuffle(flat)
        loss = 0.0
        for f, y in flat:
            sc = {}
            for r in roles:
                w = W[r]
                sc[r] = sum(w[kv] for kv in f.items())
            m = max(sc.values())
            ex_ = {r: math.exp(min(30, sc[r]-m)) for r in roles}
            Z = sum(ex_.values())
            p = {r: ex_[r]/Z for r in roles}
            loss += -math.log(max(p[y], 1e-12))
            for r in roles:
                gr = (1.0 if r == y else 0.0) - p[r]
                if abs(gr) > 1e-6:
                    w = W[r]
                    for kv in f.items():
                        w[kv] += lr*gr
        lr *= 0.85
        if ep % 2 == 1:
            print('    ep%2d loss %.4f' % (ep+1, loss/len(flat)), flush=True)
    return W


def predict(W, roles, f):
    sc = {r: sum(W[r].get(kv, 0.0) for kv in f.items()) for r in roles}
    m = max(sc.values())
    ex_ = {r: math.exp(min(30, sc[r]-m)) for r in roles}
    Z = sum(ex_.values())
    best = max(sc, key=sc.get)
    return best, ex_[best]/Z


if __name__ == '__main__':
    tr_docs = load('train')
    te_docs = load('valid')
    print('doc: train %d | test %d' % (len(tr_docs), len(te_docs)), flush=True)

    rc = collections.Counter()
    for d in tr_docs:
        for e in d['events']:
            for r, vs in (e.get('argument') or {}).items():
                rc[r] += len(vs)
    roles = ['NONE'] + [r for r, _ in rc.most_common(TOPK)]
    print('tap nhan: NONE + top-%d vai (%s ...)' % (TOPK, ', '.join(roles[1:6])), flush=True)

    print('sinh vi du...', flush=True)
    TR = build_examples(tr_docs[:2500])
    TE = build_examples(te_docs)
    print('nhom: train %d | test %d' % (len(TR), len(TE)), flush=True)

    W = fit(TR, roles)

    # ---- danh gia ----
    print('\n%s' % ('='*66))
    print('DANH GIA tren test (%d doc)' % len(te_docs))
    print('='*66)
    tp = fp = fn = 0
    per = collections.defaultdict(lambda: [0, 0, 0])
    conf_tp = conf_fp = 0
    for grp in TE:
        for f, y, meta in grp:
            yy = y if y in roles else ('NONE' if y is None else 'OTHER')
            pr, pc = predict(W, roles, f)
            if pr != 'NONE':
                if pr == yy:
                    tp += 1; per[pr][0] += 1
                else:
                    fp += 1; per[pr][1] += 1
            if yy not in ('NONE',):
                if pr != yy:
                    fn += 1
                if yy in per or yy in roles:
                    per[yy][2] += 1
    P = tp/max(tp+fp, 1); R = tp/max(tp+fn, 1)
    print('  gan VAI (moi vai, bo NONE): P %.1f%%  R %.1f%%  F1 %.1f%%'
          % (100*P, 100*R, 200*P*R/max(P+R, 1e-9)))
    print('\n  %-20s %8s %8s %8s' % ('vai', 'P', 'R', 'sup'))
    for r in roles[1:]:
        c, w, s = per[r]
        if s == 0 and c+w == 0:
            continue
        print('  %-20s %7.1f%% %7.1f%% %8d'
              % (r, 100*c/max(c+w, 1), 100*c/max(s, 1), s))

    # ---- so voi quy tac vi tri hien tai ----
    print('\n  --- so voi quy tac vi tri (agentish/patientish) ---')
    btp = bfp = bfn = 0
    for grp in TE:
        for f, y, meta in grp:
            yy = y if y in roles else ('NONE' if y is None else 'OTHER')
            rule = 'Agent' if f.get('after') in (0,) else 'Patient'
            if f.get('gap') != 0:
                rule = 'Agent' if f.get('dir') == 'B' else 'Patient'
            if rule == yy:
                btp += 1
            else:
                bfp += 1
                if yy != 'NONE':
                    bfn += 1
    bP = btp/max(btp+bfp, 1)
    print('  quy tac vi tri: accuracy tren moi ung vien %.1f%%' % (100*bP))
    print('  (quy tac nay KHONG BAO GIO doan Location — %.1f%% argument that)'
          % (100*rc['Location']/sum(rc.values())))
