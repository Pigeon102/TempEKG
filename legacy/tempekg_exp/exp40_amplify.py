"""EXP40 - LUAT KHUECH DAI LOI + tach DETECTION vs MINING.

Quan sat EXP39: T5 precision ~5-9% BAT KE gan-TIMEX P tu 37%->76%.
Gia thuyet: T5 la phep GIAO cua >=2 anchor -> mot anchor sai la lat ket qua.
   P(ca hai dung) = p^2   ->  loi khuech dai BAC HAI.

Du doan:  rate_obs = p^2 * rate_gold + (1-p^2) * q
   voi q = ti le hai moc THOI GIAN NGAU NHIEN trong cung doc khong giao nhau.

Neu dung, thi:
   DETECTION cap-le (T5)  -> hong, khong the bo ERE
   MINING gop (constraint)-> co the song, vi loi TRIET TIEU chu khong khuech dai

Do ca hai.
"""
import json, collections, random, math, sys, zipfile, io
sys.path.insert(0, 'tempekg_exp')
from timex_norm2 import doc_reference_chain

random.seed(20261012)
PREP = {'in','on','at','since','during','by','from','until','till','before','after',
        'between','of','around','about','through','throughout','within'}

docs = {}
for split in ['train','valid']:
    for line in open('MAVEN_ERE/%s.jsonl' % split, encoding='utf-8'):
        d = json.loads(line); docs[d['id']] = d

norm_all = {}; by_doc = {}
for doc, d in docs.items():
    toks = d['tokens']
    tl = [(t['id'], t['mention']) for t in sorted(d['TIMEX'], key=lambda x:(x['sent_id'],x['offset'][0]))]
    norm_all[doc] = doc_reference_chain(tl)
    tx = {t['id']:(t['sent_id'],t['offset'][0],t['offset'][1],t['type'],t['mention']) for t in d['TIMEX']}
    tx_by_sent = collections.defaultdict(list)
    for tid,v in tx.items(): tx_by_sent[v[0]].append(tid)
    ev = {}
    for e in d['events']:
        ms = [(m['sent_id'],m['offset'][0],m.get('trigger_word','')) for m in e['mention'] if 'sent_id' in m]
        if ms:
            m = min(ms); ev[e['id']] = (m[0],m[1],e['type'],m[2].lower())
    gold = set()
    for h,t in d['temporal_relations'].get('CONTAINS',[]):
        if h in tx and t in ev: gold.add((t,h))
        if t in tx and h in ev: gold.add((h,t))
    rows = []
    for eid,(es,eo,et,trig) in ev.items():
        cand = [(tid,tx[tid]) for tid in tx if abs(tx[tid][0]-es) <= 3]
        order = sorted(cand, key=lambda x: abs(x[1][0]-es)*1000+abs(x[1][1]-eo))
        rank = {tid:i for i,(tid,_) in enumerate(order)}
        n_same = len(tx_by_sent.get(es,[]))
        for tid,(ts,t0,t1,tt,surf) in cand:
            gap = ts-es; g = max(-3,min(3,gap))
            pv = toks[ts][t0-1].lower() if t0 > 0 else '<S>'
            pp = pv if pv in PREP else '_'
            f = {'bias':1,'gap':g,'dir':'A' if gap>0 else ('B' if gap<0 else 'S'),'tt':tt,'et':et,
                 'et_gap':'%s|%d'%(et,g),'rank':min(rank[tid],4),'rank0':int(rank[tid]==0),
                 'ncand':min(len(cand),6),'nsame':min(n_same,4),'prep':pp,
                 'prep_gap':'%s|%d'%(pp,g),'trig':trig,'trig_prep':'%s>%s'%(trig,pp),
                 'surf_dig':int(surf.strip().isdigit()),'surf_len':min(len(surf.split()),4)}
            if gap == 0:
                d_ = t0-eo
                f['tokd']=max(-4,min(4,d_//3)); f['tafter']=int(d_>0)
                lo,hi = (eo,t0) if d_>0 else (t0,eo)
                mid = [w.lower() for w in toks[es][lo:hi]]
                f['ncomma']=min(mid.count(','),2); f['nmid']=min(len(mid),6)
                f['midprep']=next((w for w in mid if w in PREP),'_')
            else:
                f['tokd']=9; f['tafter']=9; f['ncomma']=9; f['nmid']=9; f['midprep']='#'
            rows.append((eid,tid,f,int((eid,tid) in gold)))
    by_doc[doc] = rows

dl = sorted(docs); random.shuffle(dl); n = len(dl)
TR, TE = dl[:int(.8*n)], dl[int(.8*n):]
W = collections.defaultdict(float); LR = 0.10
tr = [(x[2],x[3]) for doc in TR for x in by_doc[doc]]
for ep in range(12):
    random.shuffle(tr)
    for f,y in tr:
        z = max(-30,min(30,sum(W[kv] for kv in f.items())))
        e = y-1/(1+math.exp(-z))
        for kv in f.items(): W[kv] += LR*(e-1e-6*W[kv])
    LR *= 0.85
def prob(f):
    return 1/(1+math.exp(-max(-30,min(30,sum(W.get(kv,0.0) for kv in f.items())))))

THETA = 0.30
pred_a = collections.defaultdict(set); gold_a = collections.defaultdict(set)
tp=fp=fn=0
for doc in TE:
    for eid,tid,f,y in by_doc[doc]:
        p = int(prob(f) >= THETA)
        if p: pred_a[(doc,eid)].add(tid)
        if y: gold_a[(doc,eid)].add(tid)
        tp+=(p and y); fp+=(p and not y); fn+=((not p) and y)
p_att = tp/max(tp+fp,1)
print('gan TIMEX: P %.3f  R %.3f' % (p_att, tp/max(tp+fn,1)), flush=True)

# ============ 1. LUAT KHUECH DAI LOI ============
print('\n'+'='*72); print('1. LUAT KHUECH DAI LOI cho T5'); print('='*72)

def conflict_rate(am):
    c = t = 0
    for (doc,eid),txs in am.items():
        v = [norm_all[doc].get(x) for x in txs]
        v = [x for x in v if x and x[0] is not None and x[2]!='duration']
        if len(v) < 2: continue
        t += 1
        if max(x[0] for x in v) > min(x[1] for x in v): c += 1
    return c, t

cg,tg = conflict_rate(gold_a); cp,tpn = conflict_rate(pred_a)
r_gold = cg/max(tg,1); r_obs = cp/max(tpn,1)

# q thuc nghiem: hai TIMEX NGAU NHIEN trong cung doc co roi nhau khong
qc = qt = 0
for doc in TE:
    vs = [v for v in norm_all[doc].values() if v and v[0] is not None and v[2]!='duration']
    if len(vs) < 2: continue
    for _ in range(min(30,len(vs)*2)):
        a,b = random.sample(vs,2); qt += 1
        if max(a[0],b[0]) > min(a[1],b[1]): qc += 1
q = qc/max(qt,1)
pred = p_att**2*r_gold + (1-p_att**2)*q
print('  ti le conflict GOLD (r)          : %.3f' % r_gold)
print('  ti le hai moc NGAU NHIEN roi (q) : %.3f  (tren %d cap ngau nhien)' % (q,qt))
print('  gan-TIMEX precision (p)          : %.3f' % p_att)
print()
print('  DU DOAN  p^2*r + (1-p^2)*q       : %.3f' % pred)
print('  QUAN SAT thuc te                 : %.3f' % r_obs)
print('  sai lech                         : %.3f' % abs(pred-r_obs))
print()
print('  -> can p >= %.3f de ti le conflict <= 2x gold (%.3f)'
      % (math.sqrt(max((q-2*r_gold)/max(q-r_gold,1e-9),0)), 2*r_gold))

# ============ 2. MINING co song sot khong ============
print('\n'+'='*72); print('2. MINING GOP: loi TRIET TIEU hay KHUECH DAI?'); print('='*72)
z = zipfile.ZipFile('MAVEN-Arg.zip')
ent_ev = collections.defaultdict(list); ev_type = {}
TEs = set(TE)
for sp in ['train.jsonl','valid.jsonl']:
    with z.open(sp) as fh:
        for line in io.TextIOWrapper(fh, encoding='utf-8'):
            d = json.loads(line)
            if d['id'] not in TEs: continue
            for e in d['events']:
                ev_type[(d['id'],e['id'])] = e['type']
                for r,vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v: ent_ev[(d['id'],v['entity_id'])].append((e['id'],r))

def iv(am,doc,eid):
    v = [norm_all[doc].get(t) for t in am.get((doc,eid),())]
    v = [x for x in v if x and x[0] is not None and x[2]!='duration']
    if not v: return None
    lo,hi = max(x[0] for x in v), min(x[1] for x in v)
    return (lo,hi) if lo <= hi else None

def mine(am):
    sig = collections.defaultdict(lambda:[0,0])
    for (doc,ent),lst in ent_ev.items():
        lst = list(dict.fromkeys(lst))
        for i in range(len(lst)):
            for j in range(i+1,len(lst)):
                e1,r1 = lst[i]; e2,r2 = lst[j]
                if e1 == e2: continue
                a,b = iv(am,doc,e1), iv(am,doc,e2)
                if a is None or b is None: continue
                k = (ev_type[(doc,e1)],r1,ev_type[(doc,e2)],r2)
                sig[k][1] += 1
                if a[1] < b[0] or b[1] < a[0]: sig[k][0] += 1
    return sig

sg, sp_ = mine(gold_a), mine(pred_a)
for nm,s in (('GOLD',sg),('MODEL',sp_)):
    n_ = sum(v[1] for v in s.values())
    print('  %-6s: %6d cap co interval | %5d signature | %4d sup>=5'
          % (nm,n_,len(s),sum(1 for v in s.values() if v[1]>=5)))

common = [k for k in sg if k in sp_ and sg[k][1] >= 5 and sp_[k][1] >= 5]
print('\n  signature chung (sup>=5 ca hai): %d' % len(common))
if len(common) >= 3:
    xs = [sg[k][0]/sg[k][1] for k in common]; ys = [sp_[k][0]/sp_[k][1] for k in common]
    mx,my = sum(xs)/len(xs), sum(ys)/len(ys)
    num = sum((a-mx)*(b-my) for a,b in zip(xs,ys))
    den = math.sqrt(sum((a-mx)**2 for a in xs)*sum((b-my)**2 for b in ys))
    r = num/den if den else 0
    mae = sum(abs(a-b) for a,b in zip(xs,ys))/len(xs)
    print('  tuong quan ti le roi-nhau GOLD vs MODEL: r = %.3f' % r)
    print('  sai so tuyet doi trung binh (MAE)      : %.3f' % mae)
    # thu hang
    rk1 = {k:i for i,k in enumerate(sorted(common,key=lambda k:-sg[k][0]/sg[k][1]))}
    rk2 = {k:i for i,k in enumerate(sorted(common,key=lambda k:-sp_[k][0]/sp_[k][1]))}
    m_ = len(common)
    dd = sum((rk1[k]-rk2[k])**2 for k in common)
    print('  Spearman tren thu hang                 : %.3f' % (1-6*dd/(m_*(m_*m_-1))))
    for TOPN in (10,20,50):
        if m_ >= TOPN:
            t1 = set(sorted(common,key=lambda k:-sg[k][0]/sg[k][1])[:TOPN])
            t2 = set(sorted(common,key=lambda k:-sp_[k][0]/sp_[k][1])[:TOPN])
            print('  trung top-%-2d                            : %d/%d (%.0f%%)'
                  % (TOPN,len(t1&t2),TOPN,100*len(t1&t2)/TOPN))
