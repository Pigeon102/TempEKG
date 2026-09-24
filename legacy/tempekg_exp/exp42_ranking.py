"""EXP42 - Gan TIMEX bang RANKING LOSS (softmax tren tap ung vien) thay vi phan loai doc lap.

Van de EXP39: moi cap (event,timex) cham diem DOC LAP -> model khong biet cac ung vien
CANH TRANH nhau. Thuc te moi event chon anchor TU MOT TAP.

Doi sang softmax tren {ung vien} u {NULL}:
   P(t | e) = exp(s(e,t)) / (exp(s_NULL) + sum_t' exp(s(e,t')))

Muc tieu: day p tu 0.514 len gan 0.841 (nguong tu luat khuech dai EXP40).
Chi dung Python thuan (may khong co torch/numpy/sklearn).
"""
import json, collections, random, math, sys
sys.path.insert(0, 'tempekg_exp')
from timex_norm2 import doc_reference_chain

random.seed(20261012)
PREP = {'in','on','at','since','during','by','from','until','till','before','after',
        'between','of','around','about','through','throughout','within'}
REPORT = {'said','says','reported','announced','according'}

docs = {}
for split in ['train','valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line); docs[d['id']] = d

norm_all = {}; groups = {}       # doc -> [ (eid, [(tid,feat,y)...]) ]
for doc, d in docs.items():
    toks = d['tokens']
    tsorted = sorted(d['TIMEX'], key=lambda x:(x['sent_id'],x['offset'][0]))
    tl = [(t['id'],t['mention']) for t in tsorted]
    norm_all[doc] = doc_reference_chain(tl)
    first_tid = tsorted[0]['id'] if tsorted else None
    tx = {t['id']:(t['sent_id'],t['offset'][0],t['offset'][1],t['type'],t['mention'])
          for t in d['TIMEX']}
    tbs = collections.defaultdict(list)
    for tid,v in tx.items(): tbs[v[0]].append(tid)
    ev = {}
    for e in d['events']:
        ms = [(m['sent_id'],m['offset'][0],m.get('trigger_word','')) for m in e['mention'] if 'sent_id' in m]
        if ms: m = min(ms); ev[e['id']] = (m[0],m[1],e['type'],m[2].lower())
    gold = set()
    for h,t in d['temporal_relations'].get('CONTAINS',[]):
        if h in tx and t in ev: gold.add((t,h))
        if t in tx and h in ev: gold.add((h,t))

    g = []
    for eid,(es,eo,et,trig) in ev.items():
        cand = [(tid,tx[tid]) for tid in tx if abs(tx[tid][0]-es) <= 3]
        if not cand: continue
        order = sorted(cand, key=lambda x: abs(x[1][0]-es)*1000+abs(x[1][1]-eo))
        rank = {tid:i for i,(tid,_) in enumerate(order)}
        ns = len(tbs.get(es,[]))
        sent = [w.lower() for w in toks[es]]
        has_rep = int(any(w in REPORT for w in sent))
        items = []
        for tid,(ts,t0,t1,tt,surf) in cand:
            gap = ts-es; gg = max(-3,min(3,gap))
            pv = toks[ts][t0-1].lower() if t0>0 else '<S>'
            pp = pv if pv in PREP else '_'
            nx = toks[ts][t1].lower() if t1 < len(toks[ts]) else '</S>'
            f = {'gap':gg,'dir':'A' if gap>0 else ('B' if gap<0 else 'S'),'tt':tt,'et':et,
                 'et_gap':'%s|%d'%(et,gg),'rank':min(rank[tid],4),'rank0':int(rank[tid]==0),
                 'ncand':min(len(cand),6),'nsame':min(ns,4),'prep':pp,
                 'prep_gap':'%s|%d'%(pp,gg),'trig':trig,'trig_prep':'%s>%s'%(trig,pp),
                 'et_prep':'%s>%s'%(et,pp),'surf_dig':int(surf.strip().isdigit()),
                 'surf_len':min(len(surf.split()),4),'nexttok':nx if nx in {',','.',')','-'} else '_',
                 'isfirst':int(tid==first_tid),'rep':has_rep,
                 'rank_prep':'%d>%s'%(min(rank[tid],2),pp)}
            if gap == 0:
                d_ = t0-eo
                f['tokd']=max(-4,min(4,d_//3)); f['tafter']=int(d_>0)
                lo,hi=(eo,t0) if d_>0 else (t0,eo)
                mid=[w.lower() for w in toks[es][lo:hi]]
                f['ncomma']=min(mid.count(','),2); f['nmid']=min(len(mid),6)
                f['midprep']=next((w for w in mid if w in PREP),'_')
                f['midverb']=int(any(w in REPORT for w in mid))
                f['clause']=int(',' not in mid and 'and' not in mid and 'which' not in mid)
            else:
                f['tokd']=9; f['tafter']=9; f['ncomma']=9; f['nmid']=9
                f['midprep']='#'; f['midverb']=9; f['clause']=9
            items.append((tid,f,int((eid,tid) in gold)))
        g.append((eid,items))
    groups[doc] = g

dl = sorted(docs); random.shuffle(dl); n = len(dl)
TR,DV,TE = dl[:int(.7*n)], dl[int(.7*n):int(.8*n)], dl[int(.8*n):]

NULLK = ('__NULL__',1)
W = collections.defaultdict(float)


def score(f):
    return sum(W[kv] for kv in f.items())


def softmax_probs(items):
    ss = [score(f) for _,f,_ in items] + [W[NULLK]]
    m = max(ss)
    ex = [math.exp(min(30, s-m)) for s in ss]
    Z = sum(ex)
    return [e/Z for e in ex]          # do dai len(items)+1


LR = 0.30
train_groups = [it for doc in TR for _, it in groups[doc]]
print('nhom huan luyen: %d | nhom co it nhat 1 anchor: %d'
      % (len(train_groups), sum(1 for it in train_groups if any(y for _,_,y in it))), flush=True)

for ep in range(20):
    random.shuffle(train_groups)
    loss = 0.0
    for items in train_groups:
        ps = softmax_probs(items)
        ys = [y for _,_,y in items]
        npos = sum(ys)
        if npos:
            tgt = [y/npos for y in ys] + [0.0]
        else:
            tgt = [0.0]*len(items) + [1.0]
        loss += -sum(t*math.log(max(p,1e-12)) for t,p in zip(tgt,ps))
        for i,(_,f,_) in enumerate(items):
            gr = tgt[i]-ps[i]
            if gr:
                for kv in f.items(): W[kv] += LR*gr
        W[NULLK] += LR*(tgt[-1]-ps[-1])
    LR *= 0.88
    if ep % 4 == 3:
        print('  ep%2d loss %.4f |W|=%d' % (ep+1, loss/len(train_groups), len(W)), flush=True)


def eval_split(split, theta, K):
    tp=fp=fn=0
    pa = collections.defaultdict(set); ga = collections.defaultdict(set)
    for doc in split:
        for eid, items in groups[doc]:
            ps = softmax_probs(items)
            keep = sorted(((ps[i], items[i][0]) for i in range(len(items))), reverse=True)
            kt = {t for p,t in keep[:K] if p >= theta}
            if kt: pa[(doc,eid)] = kt
            for i,(tid,_,y) in enumerate(items):
                p = int(tid in kt)
                tp+=(p and y); fp+=(p and not y); fn+=((not p) and y)
                if y: ga[(doc,eid)].add(tid)
    P = tp/max(tp+fp,1); R = tp/max(tp+fn,1)
    return P, R, 2*P*R/max(P+R,1e-9), pa, ga


print('\n%-7s %-3s | %-7s %-7s %-7s' % ('theta','K','P','R','F1'))
print('-'*40)
best=None
for th in [0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80]:
    for K in [1,2,3]:
        P,R,F,_,_ = eval_split(DV, th, K)
        print('%-7.2f %-3d | %6.1f%% %6.1f%% %6.1f%%' % (th,K,100*P,100*R,100*F))
        if best is None or F > best[0]: best = (F,th,K,P,R)
print('-'*40)
print('DEV tot nhat: theta=%.2f K=%d -> P %.1f%% R %.1f%% F1 %.1f%%'
      % (best[1],best[2],100*best[3],100*best[4],100*best[0]))

P,R,F,pa,ga = eval_split(TE, best[1], best[2])
print('\n=== TEST ===')
print('RANKING  : P %.1f%% R %.1f%% F1 %.1f%%' % (100*P,100*R,100*F))
print('EXP39 LR : P 46.5%% R 45.1%% F1 45.8%%')
print('EXP37    : P 54.0%% R 24.1%% F1 33.4%%')

# nguong tu luat khuech dai
r_gold, q = 0.161, 0.712
need = math.sqrt(max((q-2*r_gold)/(q-r_gold),0))
print('\nnguong can (luat EXP40): p >= %.3f | dat duoc: p = %.3f -> %s'
      % (need, P, 'DAT' if P >= need else 'CHUA DAT (thieu %.3f)' % (need-P)))

pred_rate = P*P*r_gold + (1-P*P)*q
print('du doan ti le conflict T5: %.3f (gold %.3f)' % (pred_rate, r_gold))


def cr(am):
    c=t=0
    for (doc,eid),txs in am.items():
        v=[norm_all[doc].get(x) for x in txs]
        v=[x for x in v if x and x[0] is not None and x[2]!='duration']
        if len(v)<2: continue
        t+=1
        if max(x[0] for x in v)>min(x[1] for x in v): c+=1
    return c,t
cg,tg = cr(ga); cp,tp_ = cr(pa)
print('quan sat thuc te          : %.3f (%d/%d) | gold %.3f (%d/%d)'
      % (cp/max(tp_,1),cp,tp_, cg/max(tg,1),cg,tg))
