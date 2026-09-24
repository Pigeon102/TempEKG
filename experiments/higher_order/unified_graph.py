# -*- coding: utf-8 -*-
"""Bai 1, stage 2: one graph per document with EVERY node (events and TIMEX) and EVERY temporal
edge, labelled by the stage-1 classifiers (EV-EV: 257 + 719 trigger rules; EV->TX, TX->EV,
TX-TX: bai1_all_edges.py). Patterns are mined on this unified graph and used to revise the
stage-1 labels of all four edge types.

For a target edge (a, b) of any kind with current label p, the patterns are the paths through
the unified graph:
    3-node  a - x - b          x an event or a TIMEX
    4-node  a - x - y - b      x, y events or TIMEX          (capped at 4 instances per family)
Signature = kinds of the endpoints and intermediate nodes + the oriented labels on the path.
Rule key = (signature, p): it learns P(true label | what the unified graph shows, what stage 1
said), so it learns the classifiers' own error patterns instead of assuming gold context.

Protocol -- the rules must learn from errors the classifiers make on documents they never saw:
  * the first 400 train documents are excluded (the 257 rules were mined there)
  * stage-1 TIMEX rules were mined on DISCOVERY and confirmed on CONFIRMATION-1, so
      mine    on CONFIRMATION-2 (only per-label floors were tuned there)
      tune    the margin and the number of rounds on CONFIRMATION-1, by pooled macro-F1
      valid   opened once
A ceiling row mines and applies the same rules with GOLD context (every other edge correct,
the target edge's own label still predicted): how much the unified graph could give if the
surrounding edges were right.
"""
import sys, io, json, math, hashlib, time
from collections import Counter, defaultdict
from pathlib import Path

T0 = time.time()
def log(*a): print("[%5.0fs] " % (time.time()-T0) + " ".join(str(x) for x in a), flush=True)
GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph"); ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
SYM = {"SIMULTANEOUS", "BEGINS-ON"}
CAP = 4
Z = 1.959963985
def wlb(k, n):
    if n == 0: return 0.0
    p = k/n
    return (p + Z*Z/(2*n) - Z*math.sqrt(p*(1-p)/n + Z*Z/(4*n*n)))/(1 + Z*Z/n)
def inv(l): return l if l in SYM else ("i" + l)
def h(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)
def split_of(doc):
    if h(doc) % 10 >= 4: return "disc"
    return "conf1" if h("s2" + doc) % 2 == 0 else "conf2"

PRED = json.load(io.open(ART/"pred_all_edges.json", encoding="utf-8"))
def load(split):
    docs = []
    for i, line in enumerate(io.open(GRAPH/f"{split}.jsonl", encoding="utf-8")):
        rec = json.loads(line); nd = rec["nodes"]
        sp = ("first400" if i < 400 else split_of(rec["doc_id"])) if split == "train" else "valid"
        if sp not in ("conf1", "conf2", "valid"): continue
        E = []
        for e in rec["target_edges"]:
            ka = nd.get(e["s"], {}).get("kind"); kb = nd.get(e["t"], {}).get("kind")
            if ka not in ("event", "timex") or kb not in ("event", "timex"): continue
            k = ("E" if ka == "event" else "T") + ("E" if kb == "event" else "T")
            p = PRED.get("%s|%s|%s" % (rec["doc_id"], e["s"], e["t"]), "BEFORE")
            E.append((e["s"], e["t"], e["rel"], k, p))
        if E:
            K = {x: ("E" if v.get("kind") == "event" else "T") for x, v in nd.items() if v.get("kind") in ("event", "timex")}
            docs.append({"id": rec["doc_id"], "sp": sp, "E": E, "K": K})
    return docs
log("nap du lieu ...")
TR = load("train"); VA = load("valid")
C1 = [d for d in TR if d["sp"] == "conf1"]; C2 = [d for d in TR if d["sp"] == "conf2"]
log("mine tren conf2: %d doc, chon tren conf1: %d doc, valid %d doc; canh: %d / %d / %d" % (
    len(C2), len(C1), len(VA), sum(len(d["E"]) for d in C2), sum(len(d["E"]) for d in C1), sum(len(d["E"]) for d in VA)))

def structure(d):
    """Neighbourhood and motif instances per target edge: computed once, labels read later."""
    nbr = defaultdict(set)
    for (a, b, g, k, p) in d["E"]: nbr[a].add(b); nbr[b].add(a)
    K = d["K"]; inst = []
    for (a, b, g, k, p) in d["E"]:
        Na = nbr[a] - {a, b}; Nb = nbr[b] - {a, b}
        byf = defaultdict(list)
        for x in Na & Nb: byf[k + "3" + K[x]].append((x,))
        for x in Na:
            for y in nbr[x] & Nb:
                if y != x: byf[k + "4" + K[x] + K[y]].append((x, y))
        inst.append([(f, nodes) for f, lst in byf.items() for nodes in sorted(lst)[:CAP]])
    d["inst"] = inst
for d in C1 + C2 + VA: structure(d)
log("cau truc motif xong")

def labmap(d, labels, gold_ctx):
    L = {}
    for (a, b, g, k, p), q in zip(d["E"], labels):
        v = g if gold_ctx else q
        L[(a, b)] = v; L[(b, a)] = inv(v)
    return L
def sigs(d, labels, gold_ctx):
    L = labmap(d, labels, gold_ctx); out = []
    for (a, b, g, k, p), inst in zip(d["E"], d["inst"]):
        s = set()
        for f, nodes in inst:
            if len(nodes) == 1: s.add(f + "|" + L[(a, nodes[0])] + "|" + L[(nodes[0], b)])
            else: s.add(f + "|" + L[(a, nodes[0])] + "|" + L[(nodes[0], nodes[1])] + "|" + L[(nodes[1], b)])
        out.append(s)
    return out

def mine(docs, gold_ctx):
    cnt = defaultdict(Counter); dd = defaultdict(lambda: defaultdict(set))
    for d in docs:
        labels = [x[4] for x in d["E"]]
        for (a, b, g, k, p), s in zip(d["E"], sigs(d, labels, gold_ctx)):
            for x in s: cnt[(x, p)][g] += 1; dd[(x, p)][g].add(d["id"])
    R = {}
    for key, c in cnt.items():
        n = sum(c.values())
        if n < 20: continue
        p = key[1]; t = {p: wlb(c[p], n)}
        alts = {r: wlb(kk, n) for r, kk in c.items() if r != p and kk >= 5 and len(dd[key][r]) >= 3}
        if alts: t.update(alts); R[key] = t
    return R

def statistic(R, d, labels, gold_ctx):
    """Per edge: (best alternative label, its bound minus the best bound for the current label)."""
    out = []
    for (a, b, g, k, p0), s, q in zip(d["E"], sigs(d, labels, gold_ctx), labels):
        keep = 0.0; best = None
        for x in s:
            t = R.get((x, q))
            if not t: continue
            keep = max(keep, t[q])
            for r, w in t.items():
                if r != q and (best is None or w > best[1]): best = (r, w)
        out.append((best[0], best[1] - keep) if best else (None, -9))
    return out

def run(R, docs, margin, rounds, gold_ctx):
    labs = [[x[4] for x in d["E"]] for d in docs]
    for _ in range(rounds):
        new = []
        for d, L in zip(docs, labs):
            st = statistic(R, d, L, gold_ctx)
            new.append([r if (r and v > margin) else q for q, (r, v) in zip(L, st)])
        labs = new
    return labs

def prf(docs, labs, kinds=None):
    tp, fp, fn = Counter(), Counter(), Counter(); n = ok = 0
    for d, L in zip(docs, labs):
        for (a, b, g, k, p), q in zip(d["E"], L):
            if kinds and k not in kinds: continue
            n += 1; ok += (q == g)
            if q == g: tp[g] += 1
            else: fp[q] += 1; fn[g] += 1
    per = {}
    for r in RELS:
        P = tp[r]/(tp[r]+fp[r]) if tp[r]+fp[r] else 0.0; Rr = tp[r]/(tp[r]+fn[r]) if tp[r]+fn[r] else 0.0
        per[r] = (P, Rr, 2*P*Rr/(P+Rr) if P+Rr else 0.0, tp[r]+fn[r])
    return sum(v[2] for v in per.values())/6, per, ok/max(1, n), n

def report(nm, docs, labs):
    m, per, acc, n = prf(docs, labs)
    print("  %-44s acc %6.2f%%  macro-F1 %6.2f%%   " % (nm, 100*acc, 100*m) +
          "  ".join("%s %.1f" % (r[:4], 100*per[r][2]) for r in RELS[:4]))
    cells = []
    for kinds, lab in ((("EE",), "EV-EV"), (("ET",), "EV>TX"), (("TE",), "TX>EV"), (("TT",), "TX-TX")):
        mk, _, ak, nk = prf(docs, labs, kinds); cells.append("%s %.2f%%" % (lab, 100*mk))
    print("      theo loai (macro-F1): " + "   ".join(cells))
    return m

print()
print("=" * 118)
print("BAI 1 -- DO THI HOP NHAT (moi su kien, moi TIMEX, moi canh) -- valid mo mot lan")
print("=" * 118)
base = report("giai doan 1 (classifier tung loai)", VA, [[x[4] for x in d["E"]] for d in VA])
for gold_ctx, nm in ((False, "THUC TE: ngu canh = nhan du doan"), (True, "TRAN: ngu canh = gold (khong dat duoc)")):
    log("mine %s ..." % nm)
    R = mine(C2, gold_ctx)
    log("  %d khoa (chu ky, nhan hien tai) co nhan thay the" % len(R))
    best = None
    for rounds in (1, 2):
        for m in (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 9.0):
            mc, _, _, _ = prf(C1, run(R, C1, m, rounds, gold_ctx))
            if best is None or mc > best[0]: best = (mc, m, rounds)
    _, M, RD = best
    print()
    print(" %s -- chon tren conf1: margin %.2f, %d vong (conf1 macro %.2f%%)" % (nm, M, RD, 100*best[0]))
    labs = run(R, VA, M, RD, gold_ctx)
    changed = sum(1 for d, L in zip(VA, labs) for x, q in zip(d["E"], L) if q != x[4])
    good = sum(1 for d, L in zip(VA, labs) for x, q in zip(d["E"], L) if q != x[4] and q == x[2])
    bad = sum(1 for d, L in zip(VA, labs) for x, q in zip(d["E"], L) if q != x[4] and x[4] == x[2])
    m = report("sau do thi hop nhat", VA, labs)
    print("      doi %d nhan: sua dung %d, lam hong %d   ->  macro-F1 %+.2f" % (changed, good, bad, 100*(m - base)))
    fams = Counter()
    for (x, p), t in R.items():
        fams[x.split("|", 1)[0][2:]] += 1
    print("      khoa theo ho motif: %s" % dict(fams.most_common()))
log("xong")
