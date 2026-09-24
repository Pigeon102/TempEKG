# -*- coding: utf-8 -*-
"""Bai 1 with a LAYERED graph: mine patterns inside each layer, pool them into one pattern set,
then form rules by combining patterns ACROSS layers.

Every observable piece of information about a target edge is assigned to one layer (predicted
temporal labels are excluded: reading them is circular, measured at +0.25 at best):
  ONT   event type, type pair, same type, role-frame group; TIMEX type / anchorability
  ARG   role sets, entity types, shared anchors and their roles
  DISC  sentence order and distance, position in document, mentions, connectives, prepositions,
        nearest-node relations
  LEX   trigger lemma, learned container lexicon, words inside the TIMEX
  TIME  the TIMEX context of each event (nearest TIMEX: type, granularity, preposition), and the
        calendar comparison of the two sides' nearest dates; for TX-TX the calendar relation

Stage A  per layer: depth <= 2 conjunctions inside the layer, per non-majority label, on
         DISCOVERY; kept if n >= 30, k >= 10, >= 5 docs, lift >= 2 and confirmed on
         CONFIRMATION-1 (cwlb/prior >= 1.5); top 150 per label and layer form the layer's patterns
Stage B  one pooled pattern set; each instance activates its patterns (top 3 per layer by
         confirmation bound). Rules = conjunctions of 2 or 3 patterns from DIFFERENT layers,
         same gates, confirmed on CONFIRMATION-1
Stage C  rules override the stage-1 label (EV-EV: 257 + 719 trigger rules; TIMEX edges:
         bai1_all_edges.py) when the best firing rule's bound clears a per-label floor chosen on
         CONFIRMATION-2 by macro-F1; VALID opened once
The first 400 train documents are excluded from every split (the 257 rules were mined there).
"""
import io, json, re
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = io.open(HERE/"bai1_all_edges.py", encoding="utf-8").read()
exec(SRC[:SRC.index("# ---------------------------------------------------------------- miner")])
exec(SRC[SRC.index("def prf(pred, gold):"):SRC.index("def show(nm, pred, gold):")])
import sys
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from mine_compositional import candidate_conditions, pair_features
from mine_mdd import relational_conditions
import random

import os
TAG = os.environ.get("TAG", "")
first400 = set()
if not TAG or os.environ.get("EXCL400"):   # the 257 rules were selected on these; the full-train rules (TAG=_full) were not
    for i, line in enumerate(io.open(GRAPH/"train.jsonl", encoding="utf-8")):
        if i >= 400: break
        first400.add(json.loads(line)["doc_id"])
TR = [d for d in TR if d["id"] not in first400]
ANCH = {}
for split in ("train", "valid"):
    for line in io.open(GRAPH/f"{split}.jsonl", encoding="utf-8"):
        rec = json.loads(line)
        if rec["doc_id"] in first400: continue
        m = defaultdict(set)
        for pr in rec["anchored_pairs"]:
            for ra, rb in pr["roles"]: m[(pr["a"], pr["b"])].add((ra, rb))
        ANCH[rec["doc_id"]] = m
PRED = json.load(io.open(ART/("pred_all_edges%s.json" % TAG), encoding="utf-8"))
log("train con lai %d doc (bo 400 doc dau)" % len(TR))

# ---------------------------------------------------------------- layer assignment
ARG_ATTR = {"roleset_a", "roleset_b", "roleset_shared", "etypeset_a", "etypeset_b", "etypeset_shared",
            "anchor_roles", "shares_anchor", "nrole_a", "nrole_b", "has_person_a", "has_person_b",
            "has_org_a", "has_org_b", "has_loc_a", "has_loc_b", "role_overlap", "role_subset", "n_anchor"}
ONT_ATTR = {"type_a", "type_b", "type_pair", "same_type"}
def layer_of_base(c):
    attr = c[1]
    if attr in ONT_ATTR: return "ONT"
    if attr in ARG_ATTR: return "ARG"
    return "DISC"

# DUR lexicon and role-frame groups from DISCOVERY / train input edges (as in semantic_tracks)
deg = Counter(); src = Counter(); tgt = Counter()
for d in TR:
    if d["sp"] != "disc": continue
    nd = d["nd"]
    for (a, b, r, k) in d["edges"]:
        if k != "EE": continue
        la, lb = lemma(nd[a].get("trigger")), lemma(nd[b].get("trigger"))
        deg[la] += 1; deg[lb] += 1
        if r == "CONTAINS": src[la] += 1; tgt[lb] += 1
GS = sum(src.values())/max(1, sum(deg.values())); GT = sum(tgt.values())/max(1, sum(deg.values()))
def dur(node):
    l = lemma(node.get("trigger"))
    if deg[l] < 20: return None, None
    s = (src[l] + 20*GS)/(deg[l] + 20); t = (tgt[l] + 20*GT)/(deg[l] + 20)
    b = lambda x, g: "hi" if x > 2*g else ("lo" if x < 0.5*g else "mid")
    return b(s, GS), b(t, GT)
CONN = set("""after before during while when whilst until till since following then later afterwards
subsequently meanwhile as amid prior eventually finally previously earlier once upon throughout and but thereafter soon""".split())

def nearest_tx(d, e):
    nd = d["nd"]; se, ke = pos(nd[e])
    if not d["txs"]: return None
    t = min(d["txs"], key=lambda x: (abs(pos(nd[x])[0] - se), abs(pos(nd[x])[1] - ke)))
    return t if abs(pos(nd[t])[0] - se) <= 1 else None

def layered_EE(d, a, b):
    nd = d["nd"]; A, B = nd[a], nd[b]
    m = ANCH.get(d["id"], {}); sh = m.get((a, b)) or m.get((b, a)) or set()
    f = pair_features(A, B, sh, bool(sh), frozenset())
    base = list(candidate_conditions(f)) + relational_conditions(A, B, sh)
    L = defaultdict(list)
    for c in base: L[layer_of_base(c)].append(c)
    L["LEX"] += [("lem_a", lemma(A.get("trigger"))), ("lem_b", lemma(B.get("trigger")))]
    for side, node in (("a", A), ("b", B)):
        s_, t_ = dur(node)
        if s_: L["LEX"] += [("dur_src_" + side, s_), ("dur_tgt_" + side, t_)]
    (s1, t1), (s2, t2) = pos(A), pos(B); tok = d["tok"]
    if tok and 0 <= s1 < len(tok) and 0 <= s2 < len(tok):
        if s1 == s2:
            lo, hi = sorted((t1, t2))
            for x in {w.lower() for w in tok[s1][lo+1:hi] if w.lower() in CONN}: L["DISC"].append(("conn_btw", x))
        for nm, s, t in (("pre_a", s1, t1), ("pre_b", s2, t2)):
            for x in tok[s][max(0, t-3):t]:
                if x.lower() in CONN: L["DISC"].append(("conn_" + nm, x.lower()))
    ta, tb = nearest_tx(d, a), nearest_tx(d, b)
    for side, t in (("a", ta), ("b", tb)):
        if t:
            T = nd[t]; L["TIME"] += [("ntx_type_" + side, T.get("timex_type")), ("ntx_gran_" + side, gran(parse_date(T.get("text"))))]
            for p in prep_before(d, t): L["TIME"].append(("ntx_prep_" + side, p))
        else: L["TIME"].append(("ntx_" + side, "none"))
    if ta and tb:
        if ta == tb: L["TIME"].append(("ntx_same", True))
        x, y = parse_date(nd[ta].get("text")), parse_date(nd[tb].get("text"))
        if x and y: L["TIME"].append(("ntx_cal", "lt" if x < y else ("gt" if x > y else "eq")))
    return L

def layered_ET(d, e, t, kind):
    L = defaultdict(list)
    for c in conds_ET(d, e, t, kind):
        n = c[0]
        if n in ("lem", "txw"): L["LEX"].append(c)
        elif n in ("etype", "ttype", "anch", "dir"): L["ONT"].append(c)
        elif n in ("gran", "first_date"): L["TIME"].append(c)
        elif n == "role": L["ARG"].append(c)
        else: L["DISC"].append(c)
    return L

def layered_TT(d, a, b):
    L = defaultdict(list)
    for c in conds_TT(d, a, b):
        n = c[0]
        if n in ("cal", "ga", "gb"): L["TIME"].append(c)
        elif n in ("ta", "tb", "anch"): L["ONT"].append(c)
        elif n in ("wa", "wb"): L["LEX"].append(c)
        else: L["DISC"].append(c)
    return L

def build(docs):
    out = []
    for d in docs:
        for (a, b, r, k) in d["edges"]:
            if k == "EE": L = layered_EE(d, a, b)
            elif k == "ET": L = layered_ET(d, a, b, "ET")
            elif k == "TE": L = layered_ET(d, b, a, "TE")
            else: L = layered_TT(d, a, b)
            p = PRED.get("%s|%s|%s" % (d["id"], a, b), "BEFORE")
            out.append({"doc": d["id"], "a": a, "b": b, "sp": d["sp"], "k": k, "g": r, "p": p,
                        "L": {ly: frozenset(v) for ly, v in L.items()}})
    return out
log("dung dieu kien theo tang ...")
ITR = build(TR); IVA = build(VA)
log("instance: train %d, valid %d" % (len(ITR), len(IVA)))
LAYERS = ("ONT", "ARG", "DISC", "LEX", "TIME")

# ---------------------------------------------------------------- stage A: per-layer patterns
def mine_keys(disc, c1, keyfun, prior, majority):
    kpos = defaultdict(Counter); kdoc = defaultdict(lambda: defaultdict(set)); post = defaultdict(set)
    for j, x in enumerate(disc):
        atoms, keys = keyfun(x)
        for c in atoms: post[c].add(j)
        if x["g"] != majority:
            for key in keys: kpos[x["g"]][key] += 1; kdoc[x["g"]][key].add(x["doc"])
    def supp(key, P):
        S = P.get(key[0], set())
        for c in key[1:]: S = S & P.get(c, set())
        return S
    cand = []
    for r in kpos:
        if prior.get(r, 0) == 0: continue
        for key, kk in kpos[r].items():
            if kk < 10 or len(kdoc[r][key]) < 5: continue
            n = len(supp(key, post))
            if n < 30: continue
            w = wlb(kk, n)
            if (kk/n)/prior[r] >= 2 and w/prior[r] >= 1.5: cand.append((key, r))
    need = {c for key, _ in cand for c in key}; cpost = defaultdict(set)
    for j, x in enumerate(c1):
        atoms, _ = keyfun(x, need_only=need)
        for c in atoms: cpost[c].add(j)
    out = defaultdict(list)
    for key, r in cand:
        S = supp(key, cpost)
        if len(S) < 10: continue
        cw = wlb(sum(1 for q in S if c1[q]["g"] == r), len(S))
        if cw/prior[r] >= 1.5: out[r].append((cw, key))
    for r in out: out[r].sort(key=lambda t: -t[0])
    return out

def layer_keyfun(ly):
    def f(x, need_only=None):
        atoms = x["L"].get(ly, frozenset())
        if need_only is not None: return [c for c in atoms if c in need_only], []
        A = sorted(atoms, key=repr)
        keys = [(c,) for c in A] + [(A[i], A[j]) for i in range(len(A)) for j in range(i+1, len(A))]
        return A, keys
    return f

GROUPS = (("EV-EV", ("EE",)), ("EV->TIMEX", ("ET",)), ("TIMEX->EV", ("TE",)), ("TIMEX-TIMEX", ("TT",)))
def classify_override(rules_by_first, TH, inst_active, starts):
    out = []
    for act, p in zip(inst_active, starts):
        best = None
        for c in act:
            for key, r, cw in rules_by_first.get(c, ()):
                if cw >= TH.get(r, 9) and all(z in act for z in key[1:]) and (best is None or cw > best[1]): best = (r, cw)
        out.append(best[0] if best else p)
    return out

def macro(pred, gold):
    return prf(pred, gold)[0]

def tune_floors(labels, rules_by_first, act, starts, gold):
    TH = {r: 9 for r in labels}; best = macro(starts, gold)
    for _ in range(2):
        for r in labels:
            for t in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 9):
                T2 = dict(TH); T2[r] = t
                m = macro(classify_override(rules_by_first, T2, act, starts), gold)
                if m > best: best, TH = m, T2
    return TH

FINAL = {}
DUMPD = {}
SAVE_L = {}
print()
print("=" * 118)
print("BAI 1 -- DO THI THEO TANG: pattern tung tang -> bo pattern chung -> luat lien tang (valid mo mot lan)")
print("=" * 118)
for gname, kinds in GROUPS:
    tr = [x for x in ITR if x["k"] in kinds]; va = [x for x in IVA if x["k"] in kinds]
    disc = [x for x in tr if x["sp"] == "disc"]; c1 = [x for x in tr if x["sp"] == "conf1"]; c2 = [x for x in tr if x["sp"] == "conf2"]
    pr = Counter(x["g"] for x in disc); maj = pr.most_common(1)[0][0]; prior = {r: pr[r]/len(disc) for r in RELS if pr[r]}
    log("%s: stage A ..." % gname)
    PAT = {}                                  # pattern id -> (layer, key, label, cwlb)
    per_layer = {}
    for ly in LAYERS:
        if not any(x["L"].get(ly) for x in disc[:2000]): continue
        res = mine_keys(disc, c1, layer_keyfun(ly), prior, maj)
        kept = 0
        for r, lst in res.items():
            for cw, key in lst[:150]:
                PAT[(ly,) + key] = (ly, key, r, cw); kept += 1
        per_layer[ly] = kept
    log("  pattern theo tang: %s" % per_layer)
    # active patterns per instance (top 3 per layer by bound)
    def active(x):
        byl = defaultdict(list)
        for pid, (ly, key, r, cw) in PAT.items():
            atoms = x["L"].get(ly, frozenset())
            if all(c in atoms for c in key): byl[ly].append((cw, pid))
        out = []
        for ly, lst in byl.items():
            lst.sort(key=lambda t: -t[0]); out += [pid for cw, pid in lst[:3]]
        return out
    # index patterns by their first atom for speed
    byatom = defaultdict(list)
    for pid, (ly, key, r, cw) in PAT.items(): byatom[(ly, key[0])].append(pid)
    def active_fast(x):
        byl = defaultdict(list)
        for ly, atoms in x["L"].items():
            for c in atoms:
                for pid in byatom.get((ly, c), ()):
                    key = PAT[pid][1]
                    if all(z in atoms for z in key): byl[ly].append((PAT[pid][3], pid))
        out = []
        for ly, lst in byl.items():
            lst = sorted(set(lst), key=lambda t: -t[0]); out += [pid for cw, pid in lst[:3]]
        return frozenset(out)
    for x in tr + va: x["act"] = active_fast(x)
    log("  stage B ...")
    def cross_keyfun(x, need_only=None):
        A = sorted(x["act"], key=repr)
        if need_only is not None: return [c for c in A if c in need_only], []
        keys = []
        for i in range(len(A)):
            for j in range(i+1, len(A)):
                if A[i][0] == A[j][0]: continue
                keys.append((A[i], A[j]))
                for l in range(j+1, len(A)):
                    if A[l][0] in (A[i][0], A[j][0]): continue
                    keys.append((A[i], A[j], A[l]))
        return A, keys
    CROSS = mine_keys(disc, c1, cross_keyfun, prior, maj)
    ncross = sum(len(v) for v in CROSS.values())
    log("  luat lien tang: %d (%s)" % (ncross, {r: len(v) for r, v in CROSS.items()}))
    # rule sets: (a) patterns alone, (b) patterns + cross-layer rules. A pattern rule's "atom" is its pid.
    def index(rulelist):
        byf = defaultdict(list)
        for key, r, cw in rulelist: byf[key[0]].append((key, r, cw))
        return byf
    pat_rules = [((pid,), PAT[pid][2], PAT[pid][3]) for pid in PAT]
    cross_rules = [(key, r, cw) for r, lst in CROSS.items() for cw, key in lst]
    labels = sorted({r for _, r, _ in pat_rules + cross_rules})
    gv = [x["g"] for x in va]; s1 = [x["p"] for x in va]
    print()
    print(" %s -- %d pattern (%s), %d luat lien tang" % (gname, len(PAT), per_layer, ncross))
    m0, per0, a0 = prf(s1, gv)
    print("   giai doan 1:                     macro %6.2f%%  acc %6.2f%%" % (100*m0, 100*a0))
    for nm, rl in (("+ pattern tung tang", pat_rules), ("+ pattern + luat lien tang", pat_rules + cross_rules)):
        idx = index(rl)
        TH = tune_floors(labels, idx, [x["act"] for x in c2], [x["p"] for x in c2], [x["g"] for x in c2])
        pv = classify_override(idx, TH, [x["act"] for x in va], s1)
        m, per, acc = prf(pv, gv)
        ch = sum(1 for a, b in zip(pv, s1) if a != b); ok = sum(1 for a, b, g in zip(pv, s1, gv) if a != b and a == g)
        print("   %-32s macro %6.2f%% (%+.2f)  acc %6.2f%%  doi %5d dung %5.1f%%  nguong %s" %
              (nm, 100*m, 100*(m-m0), 100*acc, ch, 100*ok/max(1, ch), {r[:4]: t for r, t in TH.items() if t < 9}))
        print("      " + "  ".join("%s %.1f" % (r[:4], 100*per[r][2]) for r in RELS if per[r][3]))
        if nm.startswith("+ pattern +"):
            for x, p in zip(va, pv): FINAL[id(x)] = p
            ptr = classify_override(idx, TH, [x["act"] for x in tr], [x["p"] for x in tr])
            for x, p in zip(tr, ptr): SAVE_L["%s|%s|%s" % (x["doc"], x["a"], x["b"])] = p
            for x, p in zip(va, pv): SAVE_L["%s|%s|%s" % (x["doc"], x["a"], x["b"])] = p
            if os.environ.get("DUMP"):        # rules, floors and rows for experiments/rules_full/compress_layered.py
                DUMPD[gname] = {"rules": rl, "TH": TH, "rows": {sp: [(x["act"], x["p"], x["g"]) for x in part]
                                for sp, part in (("disc", disc), ("conf1", c1), ("conf2", c2), ("valid", va))}}
    for cw, key in sorted(((cw, key) for r, lst in CROSS.items() for cw, key in lst[:2]), key=lambda t: -t[0])[:4]:
        r = next(rr for rr, lst in CROSS.items() if any(k2 == key for _, k2 in lst))
        print("        lien tang -> %-12s cwlb %.3f  %s" % (r, cw, " & ".join("%s:%s" % (pid[0], pid[1:]) for pid in key)[:150]))

gv = [x["g"] for x in IVA]; s1 = [x["p"] for x in IVA]; fv = [FINAL.get(id(x), x["p"]) for x in IVA]
print()
m0, _, a0 = prf(s1, gv); m1, per1, a1 = prf(fv, gv)
print(" GOP 188.924 CANH: giai doan 1 macro %.2f%% acc %.2f%%  ->  theo tang %.2f%% (%+.2f) acc %.2f%%" % (100*m0, 100*a0, 100*m1, 100*(m1-m0), 100*a1))
print("      " + "  ".join("%s %.1f" % (r[:4], 100*per1[r][2]) for r in RELS))
json.dump(SAVE_L, io.open(ART/("pred_layered%s.json" % TAG), "w", encoding="utf-8"))
if os.environ.get("DUMP"):
    import pickle
    with open(ART/("layered_dump%s.pkl" % TAG), "wb") as fh: pickle.dump(DUMPD, fh)
log("da luu %d du doan -> pred_layered.json" % len(SAVE_L))
log("xong")
