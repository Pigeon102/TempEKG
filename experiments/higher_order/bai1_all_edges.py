# -*- coding: utf-8 -*-
"""Bai 1 over ALL FOUR edge types, not only event-event.

Target edges on valid: EV-EV 109,929 | EV->TX 26,573 | TX->EV 39,935 | TX-TX 12,487.
Until now only EV-EV had a real classifier. The EV-TIMEX classifier used as context in the
motif study reached 79.84% accuracy where always-BEFORE already gets 77.4% -- so the TIMEX
layer the motifs read was close to uninformative. This script builds proper rule classifiers
for the three TIMEX edge types, with the same machinery and protocol as the EV-EV rules:

  features   event side: type, trigger lemma, sentence position, role/entity profile
             timex side: timex_type, anchorable, calendar granularity, content words
             geometry:   same sentence, sentence / token distance, textual order, whether
                         this timex is the event's nearest one, words right before the timex
                         (in / on / during / since / until / after ...)
             TX-TX:      calendar comparison of the two values, containment of a coarse date
                         in a finer one, types, order, distance
  mining     depth <= 2 conjunctions, per non-majority label, positive-only enumeration +
             posting-list support, on DISCOVERY
  gates      n >= 30, k >= 10, >= 5 documents, lift >= 2, wlb/prior >= 1.5 on DISCOVERY;
             cwlb/prior >= 1.5 on CONFIRMATION-1
  selection  fraction kept per label and threshold tau chosen on CONFIRMATION-2
  combiner   max over firing rules of cwlb/prior; argmax if >= tau, else the majority label
  valid      opened once

EV-EV uses the frozen classifier (257 + 719 trigger rules, 26.15%). Everything is reported
per edge type and pooled over all 188,924 valid edges. Predictions of every type are saved for
the unified-graph step.
"""
import sys, io, json, math, re, hashlib, time
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path

T0 = time.time()
def log(*a): print("[%5.0fs] " % (time.time()-T0) + " ".join(str(x) for x in a), flush=True)
GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph"); RAW = Path(r"C:\Reseach_Quang\MAVEN_ERE")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
Z = 1.959963985
def wlb(k, n):
    if n == 0: return 0.0
    p = k/n
    return (p + Z*Z/(2*n) - Z*math.sqrt(p*(1-p)/n + Z*Z/(4*n*n)))/(1 + Z*Z/n)
def h(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)
NOARG = __import__("os").environ.get("NOARG", "")
SEED = __import__("os").environ.get("SEED", "")      # seed sweep: salts the document split ("" = original)
def split_of(doc):
    if h(SEED + doc) % 10 >= 4: return "disc"
    return "conf1" if h(SEED + "s2" + doc) % 2 == 0 else "conf2"
MON = {m: i+1 for i, m in enumerate("january february march april may june july august september october november december".split())}
def parse_date(t):
    s = (t or "").lower().replace(",", " ")
    y = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", s)
    if not y: return None
    yr = int(y.group(1)); mo = dy = 0
    for nm, num in MON.items():
        if nm[:3] in s.split() or nm in s: mo = num; break
    d = re.search(r"\b([0-3]?[0-9])\b(?!\d)", s)
    if d and mo:
        v = int(d.group(1))
        if 1 <= v <= 31: dy = v
    return (yr, mo, dy)
def gran(dt): return "none" if not dt else ("ymd" if dt[2] else ("ym" if dt[1] else "y"))
def lemma(w):
    w = (w or "").lower().strip()
    for suf, rep in (("ies", "y"), ("ied", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("s", "")):
        if len(w) > len(suf) + 3 and w.endswith(suf): return w[:-len(suf)] + rep
    return w
PREP = set("in on at during since until till by after before from to between throughout within for of around early late mid following prior about when while as".split())
def bkt(d): return "0" if d == 0 else ("1" if d == 1 else ("2-3" if d <= 3 else "4+"))
def tbkt(d): return "<=3" if d <= 3 else ("<=8" if d <= 8 else ("<=15" if d <= 15 else ">15"))

# ---------------------------------------------------------------- load
def load(split):
    raw = {}
    for line in io.open(RAW/f"{split}.jsonl", encoding="utf-8"):
        r = json.loads(line); raw[r["id"]] = r["tokens"]
    docs = []
    for line in io.open(GRAPH/f"{split}.jsonl", encoding="utf-8"):
        rec = json.loads(line); nd = rec["nodes"]
        evs = [k for k, v in nd.items() if v.get("kind") == "event"]
        txs = [k for k, v in nd.items() if v.get("kind") == "timex"]
        d = {"id": rec["doc_id"], "nd": nd, "tok": raw.get(rec["doc_id"], []), "evs": evs, "txs": txs,
             "edges": [], "sp": split_of(rec["doc_id"]) if split == "train" else "valid"}
        for e in rec["target_edges"]:
            ka = nd.get(e["s"], {}).get("kind"); kb = nd.get(e["t"], {}).get("kind")
            if ka not in ("event", "timex") or kb not in ("event", "timex"): continue
            d["edges"].append((e["s"], e["t"], e["rel"], ("E" if ka == "event" else "T") + ("E" if kb == "event" else "T")))
        docs.append(d)
    return docs
log("nap du lieu ...")
TR = load("train"); VA = load("valid")
log("train %d doc, valid %d doc" % (len(TR), len(VA)))

def pos(n): return (n.get("sent_first") if n.get("sent_first") is not None else -1, n.get("tok_first") if n.get("tok_first") is not None else -1)

def prep_before(d, t):
    s, k = pos(d["nd"][t]); tok = d["tok"]
    if s < 0 or s >= len(tok): return []
    return [x.lower() for x in tok[s][max(0, k-3):k] if x.lower() in PREP]

def tx_words(n):
    return [w for w in re.findall(r"[a-z]+", (n.get("text") or "").lower()) if w not in MON and len(w) > 2][:4]

# ---------------------------------------------------------------- per-pair conditions
def conds_ET(d, e, t, kind):
    nd = d["nd"]; E, T = nd[e], nd[t]
    c = [("dir", kind), ("etype", E.get("type")), ("lem", lemma(E.get("trigger"))), ("ebkt", E.get("sent_bucket")),
         ("ttype", T.get("timex_type")), ("anch", bool(T.get("anchorable"))), ("gran", gran(parse_date(T.get("text"))))]
    for w in tx_words(T): c.append(("txw", w))
    (se, ke), (st, kt) = pos(E), pos(T)
    c.append(("sdist", bkt(abs(se - st))))
    c.append(("order", "e<t" if (se, ke) < (st, kt) else "t<e"))
    if se == st: c.append(("tdist", tbkt(abs(ke - kt))))
    near = min(d["txs"], key=lambda x: (abs(pos(nd[x])[0] - se), abs(pos(nd[x])[1] - ke)))
    c.append(("nearest_tx", near == t))
    nearev = min(d["evs"], key=lambda x: (abs(pos(nd[x])[0] - st), abs(pos(nd[x])[1] - kt)))
    c.append(("nearest_ev", nearev == e))
    for p in prep_before(d, t): c.append(("prep", p))
    if not NOARG:                                     # NOARG=1: MAVEN-Arg ablation, no role atoms
        for r in (E.get("roleset") or [])[:4]: c.append(("role", r))
    first_date = min((x for x in d["txs"] if nd[x].get("timex_type") == "DATE"), key=lambda x: pos(nd[x]), default=None)
    c.append(("first_date", first_date == t))
    return c

def conds_TT(d, a, b):
    nd = d["nd"]; A, B = nd[a], nd[b]
    x, y = parse_date(A.get("text")), parse_date(B.get("text"))
    c = [("ta", A.get("timex_type")), ("tb", B.get("timex_type")), ("ga", gran(x)), ("gb", gran(y)),
         ("anch", (bool(A.get("anchorable")), bool(B.get("anchorable"))))]
    if x and y:
        if x[0] != y[0]: c.append(("cal", "lt" if x[0] < y[0] else "gt"))
        else:
            fx, fy = (x[1], x[2]), (y[1], y[2])
            if not x[1] and y[1]: c.append(("cal", "a_contains_b"))
            elif x[1] and not y[1]: c.append(("cal", "b_contains_a"))
            elif x[1] != y[1] and x[1] and y[1]: c.append(("cal", "lt" if x[1] < y[1] else "gt"))
            elif x[2] and y[2] and x[2] != y[2]: c.append(("cal", "lt" if x[2] < y[2] else "gt"))
            elif not x[2] and y[2]: c.append(("cal", "a_contains_b"))
            elif x[2] and not y[2]: c.append(("cal", "b_contains_a"))
            else: c.append(("cal", "eq"))
    else: c.append(("cal", "unk"))
    (sa, ka), (sb, kb) = pos(A), pos(B)
    c.append(("order", "a<b" if (sa, ka) < (sb, kb) else "b<a")); c.append(("sdist", bkt(abs(sa - sb))))
    for w in tx_words(A): c.append(("wa", w))
    for w in tx_words(B): c.append(("wb", w))
    for p in prep_before(d, a): c.append(("pa", p))
    for p in prep_before(d, b): c.append(("pb", p))
    return c

def instances(docs, kinds):
    out = []
    for d in docs:
        for (a, b, r, k) in d["edges"]:
            if k not in kinds: continue
            if k == "ET": cs = conds_ET(d, a, b, "ET")
            elif k == "TE": cs = conds_ET(d, b, a, "TE")
            else: cs = conds_TT(d, a, b)
            out.append((d["id"], d["sp"], a, b, r, k, frozenset(cs)))
    return out

# ---------------------------------------------------------------- miner
def mine(inst, majority):
    disc = [x for x in inst if x[1] == "disc"]; c1 = [x for x in inst if x[1] == "conf1"]
    prior = Counter(x[4] for x in disc); N = len(disc); prior = {r: prior[r]/N for r in RELS if prior[r]}
    post = defaultdict(set); kpos = defaultdict(Counter); kdoc = defaultdict(lambda: defaultdict(set))
    for j, (doc, sp, a, b, r, k, cs) in enumerate(disc):
        for c in cs: post[c].add(j)
        if r != majority:
            L = sorted(cs, key=repr)
            keys = [(c,) for c in L] + [(L[i], L[j2]) for i in range(len(L)) for j2 in range(i+1, len(L))]
            for key in keys: kpos[r][key] += 1; kdoc[r][key].add(doc)
    def supp(key, P):
        S = P.get(key[0], set())
        return S if len(key) == 1 else (S & P.get(key[1], set()))
    cand = []
    for r in kpos:
        if r not in prior: continue
        for key, kk in kpos[r].items():
            if kk < 10 or len(kdoc[r][key]) < 5: continue
            n = len(supp(key, post))
            if n < 30: continue
            w = wlb(kk, n)
            if (kk/n)/prior[r] >= 2 and w/prior[r] >= 1.5: cand.append((key, r))
    cpost = defaultdict(set); need = {c for key, _ in cand for c in key}
    for j, (doc, sp, a, b, r, k, cs) in enumerate(c1):
        for c in cs:
            if c in need: cpost[c].add(j)
    R = defaultdict(list)
    for key, r in cand:
        S = supp(key, cpost)
        if len(S) < 10: continue
        cw = wlb(sum(1 for q in S if c1[q][4] == r), len(S))
        if cw/prior[r] >= 1.5: R[r].append((cw, key))
    for r in R: R[r].sort(key=lambda t: -t[0])
    return R, prior

def classify(R, TH, majority, inst):
    """Each label r has its own precision floor TH[r]: a rule may vote for r only if its
    confirmation Wilson bound is at least TH[r]; the pair takes the firing rule with the highest
    bound, else the majority label. Per-label floors replace the prior-normalised threshold,
    which cannot work when one label's prior is 0.3% and another's 30%."""
    rules = defaultdict(list)
    for r, lst in R.items():
        for cw, key in lst:
            if cw >= TH.get(r, 9): rules[key[0]].append((key, r, cw))
    out = []
    for x in inst:
        cs = x[6]; best = None
        for c in cs:
            for key, r, v in rules.get(c, ()):
                if (len(key) == 1 or key[1] in cs) and (best is None or v > best[1]): best = (r, v)
        out.append(best[0] if best else majority)
    return out

GRID = (0.15, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 9)
def tune(R, majority, inst):
    """Coordinate ascent on macro-F1 over per-label floors, on CONFIRMATION-2."""
    gold = [x[4] for x in inst]
    TH = {r: 0.5 for r in R}
    best = prf(classify(R, TH, majority, inst), gold)[0]
    for _ in range(3):
        for r in R:
            for t in GRID:
                T2 = dict(TH); T2[r] = t
                m = prf(classify(R, T2, majority, inst), gold)[0]
                if m > best: best, TH = m, T2
    return TH, best

def prf(pred, gold):
    tp, fp, fn = Counter(), Counter(), Counter()
    for p, g in zip(pred, gold):
        if p == g: tp[g] += 1
        else: fp[p] += 1; fn[g] += 1
    per = {}
    for r in RELS:
        P = tp[r]/(tp[r]+fp[r]) if tp[r]+fp[r] else 0.0; Rr = tp[r]/(tp[r]+fn[r]) if tp[r]+fn[r] else 0.0
        per[r] = (P, Rr, 2*P*Rr/(P+Rr) if P+Rr else 0.0, tp[r]+fn[r])
    return sum(v[2] for v in per.values())/6, per, sum(tp.values())/max(1, len(gold))

def show(nm, pred, gold):
    m, per, acc = prf(pred, gold)
    print("  %-34s n=%6d  acc %6.2f%%  macro-F1 %6.2f%%" % (nm, len(gold), 100*acc, 100*m))
    print("      " + "  ".join("%s P%.1f R%.1f F%.1f (n=%d)" % (r[:4], 100*v[0], 100*v[1], 100*v[2], v[3]) for r, v in per.items() if v[3]))
    return m

SAVE = {}
print()
print("=" * 110)
print("BAI 1 -- BON LOAI CANH (valid mo mot lan cho moi loai)")
print("=" * 110)
for grp, kinds in (("EV->TIMEX", ("ET",)), ("TIMEX->EV", ("TE",)), ("TIMEX-TIMEX", ("TT",))):
    log("dung dieu kien %s ..." % grp)
    tr = instances(TR, kinds); va = instances(VA, kinds)
    maj = Counter(x[4] for x in tr if x[1] == "disc").most_common(1)[0][0]
    R, prior = mine(tr, maj)
    log("%s: %s luat qua cong (%s)" % (grp, sum(len(v) for v in R.values()), {r: len(v) for r, v in R.items()}))
    c2 = [x for x in tr if x[1] == "conf2"]
    TH, mc = tune(R, maj, c2)
    print()
    print(" %s -- nguong precision moi nhan chon tren CONFIRMATION-2 (macro %.2f%%): %s" % (grp, 100*mc, {r[:4]: t for r, t in TH.items()}))
    gv = [x[4] for x in va]
    show("luon %s" % maj, [maj]*len(va), gv)
    if grp == "TIMEX-TIMEX":
        cal = []
        for x in va:
            cc = dict(c for c in x[6] if c[0] == "cal")
            cal.append({"lt": "BEFORE", "eq": "SIMULTANEOUS", "a_contains_b": "CONTAINS"}.get(cc.get("cal"), maj))
        show("chi so lich", cal, gv)
    pv = classify(R, TH, maj, va)
    show("luat (%s)" % grp, pv, gv)
    for x, p in zip(va, pv): SAVE["%s|%s|%s" % (x[0], x[2], x[3])] = p
    ptr = classify(R, TH, maj, tr)
    for x, p in zip(tr, ptr): SAVE["%s|%s|%s" % (x[0], x[2], x[3])] = p
    top = sorted(((cw, r, key) for r, lst in R.items() for cw, key in lst[:2] if cw >= TH.get(r, 9)), reverse=True)[:8]
    for v, r, key in top: print("        %-80s -> %-12s cwlb %.3f" % (str(key)[:80], r, v))

# ---------------------------------------------------------------- pooled over all four types
EEP = json.load(io.open(ART/"pred_lex_d05.json", encoding="utf-8"))
allp = []; allg = []; allc = []
for d in VA:
    for (a, b, r, k) in d["edges"]:
        key = "%s|%s|%s" % (d["id"], a, b)
        p = EEP.get(key) if k == "EE" else SAVE.get(key)
        allp.append(p or "BEFORE"); allg.append(r); allc.append("BEFORE")
print()
print(" GOP TOAN BO CANH VALID (EV-EV dung 257 + 719 luat trigger):")
show("luon BEFORE", allc, allg)
show("classifier theo tung loai", allp, allg)
SAVE.update(EEP)
json.dump(SAVE, io.open(ART/("pred_all_edges%s%s.json" % ("_s" + SEED if SEED else "", "_noarg" if NOARG else "")), "w", encoding="utf-8"))
log("da luu %d du doan -> pred_all_edges.json" % len(SAVE))
