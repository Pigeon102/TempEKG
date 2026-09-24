"""EXP41 - Cuu DETECTION bang diem CO TRONG SO thay vi giao CUNG.

Tu EXP40: rate = p^2*r + (1-p^2)*q. Loi khuech dai vi phep giao la BOOLEAN.
Neu thay boolean bang XAC SUAT thi lat duoc:

   score(e) = P(moi anchor deu dung) * [giao rong]
            = (prod_i pi) * 1[conflict]

Roi XEP HANG thay vi cat cung -> precision@k phai cao hon nhieu o dau bang.
Day dung bai hoc L3 trong AUDIT.md (xep hang thay vi loc).

Ngoai ra: kiem chung MINING khong-ERE bang cach ap constraint da mine len GRAPH GOLD.
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
    tl = [(t['id'],t['mention']) for t in sorted(d['TIMEX'],key=lambda x:(x['sent_id'],x['offset'][0]))]
    norm_all[doc] = doc_reference_chain(tl)
    tx = {t['id']:(t['sent_id'],t['offset'][0],t['offset'][1],t['type'],t['mention']) for t in d['TIMEX']}
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
    rows = []
    for eid,(es,eo,et,trig) in ev.items():
        cand = [(tid,tx[tid]) for tid in tx if abs(tx[tid][0]-es)<=3]
        order = sorted(cand,key=lambda x:abs(x[1][0]-es)*1000+abs(x[1][1]-eo))
        rank = {tid:i for i,(tid,_) in enumerate(order)}
        ns = len(tbs.get(es,[]))
        for tid,(ts,t0,t1,tt,surf) in cand:
            gap = ts-es; g = max(-3,min(3,gap))
            pv = toks[ts][t0-1].lower() if t0>0 else '<S>'
            pp = pv if pv in PREP else '_'
            f = {'bias':1,'gap':g,'dir':'A' if gap>0 else ('B' if gap<0 else 'S'),'tt':tt,'et':et,
                 'et_gap':'%s|%d'%(et,g),'rank':min(rank[tid],4),'rank0':int(rank[tid]==0),
                 'ncand':min(len(cand),6),'nsame':min(ns,4),'prep':pp,'prep_gap':'%s|%d'%(pp,g),
                 'trig':trig,'trig_prep':'%s>%s'%(trig,pp),'surf_dig':int(surf.strip().isdigit()),
                 'surf_len':min(len(surf.split()),4)}
            if gap == 0:
                d_ = t0-eo
                f['tokd']=max(-4,min(4,d_//3)); f['tafter']=int(d_>0)
                lo,hi=(eo,t0) if d_>0 else (t0,eo)
                mid=[w.lower() for w in toks[es][lo:hi]]
                f['ncomma']=min(mid.count(','),2); f['nmid']=min(len(mid),6)
                f['midprep']=next((w for w in mid if w in PREP),'_')
            else:
                f['tokd']=9; f['tafter']=9; f['ncomma']=9; f['nmid']=9; f['midprep']='#'
            rows.append((eid,tid,f,int((eid,tid) in gold)))
    by_doc[doc] = rows

dl = sorted(docs); random.shuffle(dl); n=len(dl)
TR,TE = dl[:int(.8*n)], dl[int(.8*n):]
W = collections.defaultdict(float); LR=0.10
tr = [(x[2],x[3]) for doc in TR for x in by_doc[doc]]
for ep in range(12):
    random.shuffle(tr)
    for f,y in tr:
        z=max(-30,min(30,sum(W[kv] for kv in f.items())))
        e=y-1/(1+math.exp(-z))
        for kv in f.items(): W[kv]+=LR*(e-1e-6*W[kv])
    LR*=0.85
def prob(f): return 1/(1+math.exp(-max(-30,min(30,sum(W.get(kv,0.0) for kv in f.items())))))

# --- anchor voi XAC SUAT ---
pa = collections.defaultdict(dict)     # (doc,eid) -> {tid: p}
ga = collections.defaultdict(set)
for doc in TE:
    for eid,tid,f,y in by_doc[doc]:
        p = prob(f)
        if p >= 0.30: pa[(doc,eid)][tid] = p
        if y: ga[(doc,eid)].add(tid)

def gold_conf():
    s=set(); t=0
    for k,txs in ga.items():
        v=[norm_all[k[0]].get(x) for x in txs]
        v=[x for x in v if x and x[0] is not None and x[2]!='duration']
        if len(v)<2: continue
        t+=1
        if max(x[0] for x in v)>min(x[1] for x in v): s.add(k)
    return s,t
CG,TG = gold_conf()

# --- ung vien conflict co diem ---
cands=[]
for k,tp in pa.items():
    items=[(t,p) for t,p in tp.items()
           if norm_all[k[0]].get(t) and norm_all[k[0]][t][0] is not None
           and norm_all[k[0]][t][2]!='duration']
    if len(items)<2: continue
    v=[norm_all[k[0]][t] for t,_ in items]
    if max(x[0] for x in v)<=min(x[1] for x in v): continue
    ps=sorted((p for _,p in items),reverse=True)
    conf=ps[0]*ps[1]                       # P(hai anchor manh nhat deu dung)
    cands.append((conf,k))
cands.sort(reverse=True)

print('='*72); print('DETECTION: giao CUNG vs diem CO TRONG SO'); print('='*72)
print('gold conflict %d / %d event multi-anchor (%.1f%%)' % (len(CG),TG,100*len(CG)/max(TG,1)))
print('ung vien model: %d' % len(cands))
base = sum(1 for _,k in cands if k in CG)/max(len(cands),1)
print('\nCAT CUNG (lay het)      : P %.1f%%  R %.1f%%'
      % (100*base, 100*sum(1 for _,k in cands if k in CG)/max(len(CG),1)))
print('\nXEP HANG theo conf:')
print('  %-8s %-8s %-8s %-8s' % ('top-k','P','R','lift'))
for kk in [25,50,100,200,400,len(cands)]:
    if kk > len(cands): continue
    sel = cands[:kk]
    hit = sum(1 for _,k in sel if k in CG)
    P = hit/kk; R = hit/max(len(CG),1)
    print('  %-8d %-7.1f%% %-7.1f%% %-7.2fx' % (kk,100*P,100*R,P/max(base,1e-9)))

# =========== MINING khong-ERE, AP len graph GOLD ===========
print('\n'+'='*72); print('MINING khong-ERE -> AP len graph GOLD'); print('='*72)
z=zipfile.ZipFile('MAVEN-Arg.zip')
ent_ev=collections.defaultdict(list); ev_type={}
TEs=set(TE)
for sp in ['train.jsonl','valid.jsonl']:
    with z.open(sp) as fh:
        for line in io.TextIOWrapper(fh,encoding='utf-8'):
            d=json.loads(line)
            if d['id'] not in TEs: continue
            for e in d['events']:
                ev_type[(d['id'],e['id'])]=e['type']
                for r,vs in (e.get('argument') or {}).items():
                    for v in vs:
                        if 'entity_id' in v: ent_ev[(d['id'],v['entity_id'])].append((e['id'],r))

def iv_set(am,doc,eid):
    txs = am.get((doc,eid),())
    v=[norm_all[doc].get(t) for t in txs]
    v=[x for x in v if x and x[0] is not None and x[2]!='duration']
    if not v: return None
    lo,hi=max(x[0] for x in v),min(x[1] for x in v)
    return (lo,hi) if lo<=hi else None

def mine(am):
    sig=collections.defaultdict(lambda:[0,0])
    for (doc,ent),lst in ent_ev.items():
        lst=list(dict.fromkeys(lst))
        for i in range(len(lst)):
            for j in range(i+1,len(lst)):
                e1,r1=lst[i]; e2,r2=lst[j]
                if e1==e2: continue
                a,b=iv_set(am,doc,e1),iv_set(am,doc,e2)
                if a is None or b is None: continue
                k=(ev_type[(doc,e1)],r1,ev_type[(doc,e2)],r2)
                sig[k][1]+=1
                if a[1]<b[0] or b[1]<a[0]: sig[k][0]+=1
    return sig

pa_set = {k:set(v) for k,v in pa.items()}
S_gold, S_model = mine(ga), mine(pa_set)

def constraints(sig, minsup=5, minconf=0.90):
    return {k for k,v in sig.items() if v[1]>=minsup and v[0]/v[1]<=1-minconf}

for msup,mconf in [(5,0.90),(5,0.95),(10,0.90),(10,0.95)]:
    Cg,Cm = constraints(S_gold,msup,mconf), constraints(S_model,msup,mconf)
    ov=len(Cg&Cm)
    print('  sup>=%-2d conf>=%.2f | GOLD %4d | MODEL %4d | GIAO %4d | P %.1f%% R %.1f%%'
          % (msup,mconf,len(Cg),len(Cm),ov,100*ov/max(len(Cm),1),100*ov/max(len(Cg),1)))

# ap constraint MODEL len graph GOLD -> co bat duoc gi khong
Cg,Cm = constraints(S_gold,5,0.90), constraints(S_model,5,0.90)
def apply_on_gold(C):
    hit=0; tot=0
    for (doc,ent),lst in ent_ev.items():
        lst=list(dict.fromkeys(lst))
        for i in range(len(lst)):
            for j in range(i+1,len(lst)):
                e1,r1=lst[i]; e2,r2=lst[j]
                if e1==e2: continue
                a,b=iv_set(ga,doc,e1),iv_set(ga,doc,e2)
                if a is None or b is None: continue
                if (ev_type[(doc,e1)],r1,ev_type[(doc,e2)],r2) not in C: continue
                tot+=1
                if a[1]<b[0] or b[1]<a[0]: hit+=1
    return hit,tot
hg=apply_on_gold(Cg); hm=apply_on_gold(Cm)
print('\n  ap len GRAPH GOLD (cap vi pham / cap phu):')
print('    constraint mine tu GOLD  : %d/%d  (%.2f%% vi pham)' % (hg[0],hg[1],100*hg[0]/max(hg[1],1)))
print('    constraint mine KHONG-ERE: %d/%d  (%.2f%% vi pham)' % (hm[0],hm[1],100*hm[0]/max(hm[1],1)))
