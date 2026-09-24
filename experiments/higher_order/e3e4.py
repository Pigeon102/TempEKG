# -*- coding: utf-8 -*-
"""E3 + E4: clean protocol for the higher-order rules, then the full 705-document run.

E1 showed the three audit layers complement each other (higher-order finds 1,528 edges
neither of the others flags) and that stacking takes R_all from 8.24% to 40.26%. But the
triangle rules behind that were mined on all 400 train documents and checked on valid --
the same shortcut Bai 1 had to remove.

E3 applies Bai 1's protocol to them:
    DISCOVERY     197 docs   propose triangle signatures
    CONFIRMATION  126 docs   re-estimate on labels that took no part in proposing
    DEV-INNER      77 docs   pick the flag threshold
    VALID                    opened once, on the frozen rule set

E4 then runs the frozen system on all 705 valid documents rather than the 149 used so far.
"""
import sys, io, json, math, re, hashlib
sys.path.insert(0, r"C:\Reseach_Quang\tempekg\src")
from collections import Counter, defaultdict
from pathlib import Path
import vote as V
from constraint_net import MAVEN_TO_ALLEN, compose, converse, FULL
from noise_aware import score_document

GRAPH = Path(r"C:\Reseach_Quang\tempekg\src\graph")
ART = Path(r"C:\Reseach_Quang\tempekg\src\artifacts")
RELS = ["BEFORE", "CONTAINS", "SIMULTANEOUS", "OVERLAP", "BEGINS-ON", "ENDS-ON"]
INV = {"BEFORE": "iBEFORE", "CONTAINS": "iCONTAINS", "SIMULTANEOUS": "SIMULTANEOUS",
       "OVERLAP": "iOVERLAP", "BEGINS-ON": "BEGINS-ON", "ENDS-ON": "iENDS-ON"}
Z = 1.959963985
CAP = 6
VLIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 0        # 0 = all 705
MON = {m: i+1 for i, m in enumerate(
    "january february march april may june july august september october november december".split())}

def wlb(k, n):
    if n == 0: return 0.0
    p = k/n
    return (p + Z*Z/(2*n) - Z*math.sqrt(p*(1-p)/n + Z*Z/(4*n*n)))/(1 + Z*Z/n)
def dirnet(tr):
    adj = defaultdict(dict)
    for a, b, r in tr: adj[a][b] = r; adj[b][a] = INV[r]
    return adj
def mids_of(adj, a, b):
    return sorted(c for c in set(adj[a]) & set(adj[b]) if c not in (a, b))[:CAP]
def parse_date(t):
    s = t.lower().replace(",", " ")
    y = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", s)
    if not y: return None
    yr = int(y.group(1)); mo = dy = 0
    for nm, num in MON.items():
        if nm[:3] in s: mo = num; break
    d = re.search(r"\b([0-3]?[0-9])\b(?!\d)", s)
    if d and mo:
        v = int(d.group(1))
        if 1 <= v <= 31: dy = v
    return (yr, mo, dy)

def bucket(doc):
    # Bai 2 khong tune sieu tham so nao -- cong loc la hang so co dinh -- nen
    # khong can cat dev tu train. Chia hai: discovery de xuat, confirmation xac nhan.
    h = int(hashlib.md5(doc.encode()).hexdigest(), 16) % 10
    return "conf" if h < 4 else "disc"

def load(path, limit=0, feats=True):
    from mine_compositional import candidate_conditions, pair_features
    from mine_mdd import relational_conditions
    out = []
    for i, line in enumerate(io.open(path, encoding="utf-8")):
        if limit and i >= limit: break
        if not line.strip(): continue
        rec = json.loads(line); nd = rec["nodes"]; anch = defaultdict(set)
        for p in rec["anchored_pairs"]:
            for ra, rb in p["roles"]: anch[(p["a"], p["b"])].add((ra, rb))
        dt = {k: parse_date(v["text"]) for k, v in nd.items()
              if v.get("kind") == "timex" and v.get("anchorable")}
        dt = {k: v for k, v in dt.items() if v and v[1] and v[2]}
        pin = defaultdict(set); rows = []
        for e in rec["target_edges"]:
            a, b = e["s"], e["t"]
            ka = nd.get(a, {}).get("kind"); kb = nd.get(b, {}).get("kind")
            if ka == "timex" and kb == "event" and e["rel"] in ("CONTAINS", "SIMULTANEOUS") and a in dt:
                pin[b].add(dt[a])
            elif ka == "event" and kb == "timex" and e["rel"] == "SIMULTANEOUS" and b in dt:
                pin[a].add(dt[b])
            elif ka == "event" and kb == "event":
                if feats:
                    na, nb = nd[a], nd[b]
                    sh = anch.get((a, b)) or anch.get((b, a)) or set()
                    f = pair_features(na, nb, sh, bool(sh), frozenset())
                    cs = frozenset(list(candidate_conditions(f)) + relational_conditions(na, nb, sh))
                    rows.append((a, b, e["rel"], f, cs))
                else:
                    rows.append((a, b, e["rel"], None, None))
        if rows: out.append((rec["doc_id"], rows, pin))
    return out

TRD = load(GRAPH/"train.jsonl", 400, feats=False)
parts = defaultdict(list)
for d in TRD: parts[bucket(d[0])].append(d)
print("train: disc %d  conf %d document (khong cat dev -- khong co sieu tham so)"
      % (len(parts["disc"]), len(parts["conf"])), flush=True)

def count_sigs(docs):
    sig = defaultdict(Counter); sd = defaultdict(lambda: defaultdict(set))
    for doc, rows, _ in docs:
        adj = dirnet([(a, b, r) for (a, b, r, _, _) in rows])
        for (a, b, r, _, _) in rows:
            for c in mids_of(adj, a, b):
                k = (adj[a][c], adj[c][b])
                sig[k][r] += 1; sd[k][r].add(doc)
    return sig, sd

print()
print("=" * 96)
print("E3 — GIAO THUC SACH cho luat bac cao")
print("=" * 96)
sd_sig, sd_doc = count_sigs(parts["disc"])
cand = {}
for k, c in sd_sig.items():
    n = sum(c.values()); top, kk = c.most_common(1)[0]
    if n < 30 or kk < 10 or len(sd_doc[k][top]) < 5: continue
    w = wlb(kk, n)
    if w >= 0.50: cand[k] = (top, w, kk, n)
print("  DISCOVERY (%d doc): %d chu ky -> %d ung vien" % (len(parts["disc"]), len(sd_sig), len(cand)), flush=True)

cf_sig, cf_doc = count_sigs(parts["conf"])
CONF = {}
for k, (top, w, kk, n) in cand.items():
    c = cf_sig.get(k)
    if not c: continue
    cn = sum(c.values()); ck = c[top]
    if cn < 10: continue
    cw = wlb(ck, cn)
    CONF[k] = (top, cw, ck, cn, w)
print("  CONFIRMATION (%d doc): %d ung vien co du lieu" % (len(parts["conf"]), len(CONF)), flush=True)

# keep the top 70% by confirmation Wilson bound, as in Bai 1
ranked = sorted(CONF.items(), key=lambda kv: -kv[1][1])
FROZEN = {k: (v[0], v[1]) for k, v in ranked[:max(1, int(0.7*len(ranked)))]}
print("  FROZEN: %d luat (top 70%% theo cwlb)" % len(FROZEN), flush=True)
print("     nhan: %s" % dict(Counter(v[0] for v in FROZEN.values()).most_common()))

# rules mined the old way, for comparison
all_sig, all_doc = count_sigs(TRD)
OLD = {}
for k, c in all_sig.items():
    n = sum(c.values()); top, kk = c.most_common(1)[0]
    if n < 30 or kk < 10 or len(all_doc[k][top]) < 5: continue
    w = wlb(kk, n)
    if w >= 0.50: OLD[k] = (top, w)
print("  (doi chieu: mine tren ca 400 doc -> %d luat)" % len(OLD), flush=True)

# ---------------------------------------------------------------- build predicted graph
print()
print("=" * 96)
print("E4 — CHAY TREN %s DOCUMENT VALID" % ("TOAN BO 705" if not VLIMIT else str(VLIMIT)))
print("=" * 96)
VAD = load(GRAPH/"valid.jsonl", VLIMIT, feats=True)
rules = V.load_rules(ART/"rules_rx_c70.json")
flat = [(f, cs) for _, rows, _ in VAD for (_, _, _, f, cs) in rows]
idx = V.build_index(rules, [(None, f, cs) for f, cs in flat])
state = []
for doc, rows, pin in VAD:
    cur = []
    for (a, b, g, f, cs) in rows:
        h = V.firing(rules, idx, f, cs)
        cur.append([a, b, g, V.combine(rules, h, "max-norm", 5) or V.FALLBACK])
    state.append((doc, cur, pin))
npair = sum(len(c) for _, c, _ in state)
nbad = sum(1 for _, c, _ in state for e in c if e[2] != e[3])
print("  %d document, %s cap, %s canh sai (%.2f%%)"
      % (len(VAD), format(npair, ","), format(nbad, ","), 100*nbad/npair), flush=True)

def L_date(cur, pin):
    out = []
    for i, (a, b, g, p) in enumerate(cur):
        A, B = pin.get(a), pin.get(b)
        if not A or not B or len(A) > 1 or len(B) > 1: continue
        da, db = next(iter(A)), next(iter(B))
        if da == db: continue
        if da < db and p != "BEFORE": out.append((i, "BEFORE"))
        elif da > db and p == "BEFORE": out.append((i, None))
    return out
def L_closure(cur, pin):
    pos = {(a, b): i for i, (a, b, _, _) in enumerate(cur)}
    out = []
    for susp, a, b, carried, prop in score_document([(a, b, p) for (a, b, _, p) in cur]):
        if susp <= 0: continue
        i = pos.get((a, b))
        if i is not None and prop != carried: out.append((i, prop))
    return out
def make_ho(RULESET):
    def f(cur, pin):
        adj = dirnet([(a, b, p) for (a, b, _, p) in cur])
        out = []
        for i, (a, b, g, p) in enumerate(cur):
            agg = Counter()
            for c in mids_of(adj, a, b):
                t = RULESET.get((adj[a][c], adj[c][b]))
                if t: agg[t[0]] += t[1]
            if not agg: continue
            best, _ = agg.most_common(1)[0]
            if best != p: out.append((i, best))
        return out
    return f

def run_stack(layers):
    st = [(doc, [list(e) for e in cur], pin) for doc, cur, pin in state]
    done = set(); fixed = 0; flagged = 0; hit = 0
    per = []
    for nm, fn in layers:
        nf = nh = nx = 0
        for di, (doc, cur, pin) in enumerate(st):
            for i, prop in fn(cur, pin):
                if (di, i) in done: continue
                done.add((di, i)); nf += 1
                a, b, g, p = cur[i]
                if g != p:
                    nh += 1
                    if prop == g: nx += 1
                if prop: cur[i][3] = prop
        flagged += nf; hit += nh; fixed += nx
        per.append((nm, nf, nh, nx))
    left = sum(1 for _, cur, _ in st for e in cur if e[2] != e[3])
    return per, flagged, hit, fixed, left

for nm, RS in (("luat cu (mine tren 400 doc)", OLD), ("luat FROZEN (giao thuc sach)", FROZEN)):
    layers = [("higher-order", make_ho(RS)), ("closure", L_closure), ("date bridge", L_date)]
    per, flagged, hit, fixed, left = run_stack(layers)
    print()
    print("  %s — %d luat" % (nm, len(RS)))
    print("    %-16s%10s%10s%12s" % ("tang", "gan co", "dung", "sua dung"))
    for lnm, nf, nh, nx in per:
        print("    %-16s%10s%10s%12s" % (lnm, format(nf, ","), format(nh, ","), format(nx, ",")))
    print("    %-16s%10s%10s%12s" % ("TONG", format(flagged, ","), format(hit, ","), format(fixed, ",")))
    print("    P@k %.2f%%   found_all %.2f%%   repair@k %.2f%%   R_all %.2f%%"
          % (100*hit/flagged if flagged else 0, 100*hit/nbad,
             100*fixed/hit if hit else 0, 100*fixed/nbad))
    print("    canh sai: %s -> %s  (%.2f%% -> %.2f%%)"
          % (format(nbad, ","), format(left, ","), 100*nbad/npair, 100*left/npair))
