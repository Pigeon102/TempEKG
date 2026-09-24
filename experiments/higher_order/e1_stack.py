# -*- coding: utf-8 -*-
"""E1: do three audit layers complement each other, or find the same errors?

Each layer has been measured alone:
    date bridge     precision 100% on the clean gold graph, recall ~1.6%
    closure         repair@k 31.84% on predicted edges
    higher-order    repair@k 93.53%, R_all 26.15%

Standalone numbers do not say whether stacking helps. Three things are measured here:

  INCREMENTAL  what each layer adds once the ones before it have run
  OVERLAP      how much the sets of edges they flag intersect
  ORDER        whether running closure first blocks cases higher-order would have fixed

The graph audited is the classifier's own output, so this is the realistic setting, not
an oracle. Gold is used only to score, never to decide a repair.

Note on the date bridge: its 100% precision was measured on a gold graph. Here it runs
on a predicted graph, where the event-timex edges it depends on are themselves predicted,
so its precision is re-measured rather than assumed.
"""
import sys, io, json, math, re
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
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 150
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

def load(path, limit=0):
    """events, gold EV-EV edges, and the timex pins (which are themselves target edges)."""
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
        dt = {k: v for k, v in dt.items() if v and v[1] and v[2]}   # strict y/m/d
        pin = defaultdict(set); rows = []
        for e in rec["target_edges"]:
            a, b = e["s"], e["t"]
            ka = nd.get(a, {}).get("kind"); kb = nd.get(b, {}).get("kind")
            if ka == "timex" and kb == "event" and e["rel"] in ("CONTAINS", "SIMULTANEOUS") and a in dt:
                pin[b].add(dt[a])
            elif ka == "event" and kb == "timex" and e["rel"] == "SIMULTANEOUS" and b in dt:
                pin[a].add(dt[b])
            elif ka == "event" and kb == "event":
                na, nb = nd[a], nd[b]
                sh = anch.get((a, b)) or anch.get((b, a)) or set()
                f = pair_features(na, nb, sh, bool(sh), frozenset())
                cs = frozenset(list(candidate_conditions(f)) + relational_conditions(na, nb, sh))
                rows.append((a, b, e["rel"], f, cs))
        if rows: out.append((rec["doc_id"], rows, pin))
    return out

TRD = load(GRAPH/"train.jsonl", 400)
VAD = load(GRAPH/"valid.jsonl", LIMIT)
print("train %d doc  valid %d doc" % (len(TRD), len(VAD)), flush=True)

# higher-order rules, mined on train gold
sig = defaultdict(Counter); sd = defaultdict(lambda: defaultdict(set))
for doc, rows, _ in TRD:
    adj = dirnet([(a, b, r) for (a, b, r, _, _) in rows])
    for (a, b, r, _, _) in rows:
        for c in mids_of(adj, a, b):
            k = (adj[a][c], adj[c][b])
            sig[k][r] += 1; sd[k][r].add(doc)
R3 = {}
for k, c in sig.items():
    n = sum(c.values()); top, kk = c.most_common(1)[0]
    if n < 30 or kk < 10 or len(sd[k][top]) < 5: continue
    w = wlb(kk, n)
    if w >= 0.50: R3[k] = (top, w)
print("luat bo 3: %d" % len(R3), flush=True)

# predicted graph
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
nbad0 = sum(1 for _, cur, _ in state for e in cur if e[2] != e[3])
npair = sum(len(cur) for _, cur, _ in state)
print("valid %s cap, %s canh sai ban dau (%.2f%%)"
      % (format(npair, ","), format(nbad0, ","), 100*nbad0/npair), flush=True)

# ---------------------------------------------------------------- layers
def layer_date(doc, cur, pin):
    """(i, proposed) for edges the dates contradict. Both endpoints need one full date."""
    out = []
    for i, (a, b, g, p) in enumerate(cur):
        A, B = pin.get(a), pin.get(b)
        if not A or not B or len(A) > 1 or len(B) > 1: continue
        da, db = next(iter(A)), next(iter(B))
        if da == db: continue
        want = "BEFORE" if da < db else None      # da > db means B before A: no MAVEN label here
        if want and p != want: out.append((i, want))
        elif want is None and p == "BEFORE": out.append((i, None))   # flag, cannot name
    return out

def layer_closure(doc, cur, pin):
    edges = [(a, b, p) for (a, b, _, p) in cur]
    pos = {(a, b): i for i, (a, b, _, _) in enumerate(cur)}
    out = []
    for susp, a, b, carried, prop in score_document(edges):
        if susp <= 0: continue
        i = pos.get((a, b))
        if i is not None and prop != carried: out.append((i, prop))
    return out

def layer_ho(doc, cur, pin):
    adj = dirnet([(a, b, p) for (a, b, _, p) in cur])
    out = []
    for i, (a, b, g, p) in enumerate(cur):
        agg = Counter()
        for c in mids_of(adj, a, b):
            t = R3.get((adj[a][c], adj[c][b]))
            if t: agg[t[0]] += t[1]
        if not agg: continue
        best, bw = agg.most_common(1)[0]
        if best != p: out.append((i, best))
    return out

LAYERS = [("date bridge", layer_date), ("closure", layer_closure), ("higher-order", layer_ho)]

print()
print("=" * 98)
print("E1a — TUNG TANG RIENG LE tren cung do thi du doan")
print("=" * 98)
print("  %-16s%10s%12s%12s%12s%10s" % ("tang", "gan co", "dung", "precision", "sua dung", "R_all"))
print("  " + "-" * 74)
sets = {}
for nm, fn in LAYERS:
    flag = set(); fixed = 0; hit = 0
    for di, (doc, cur, pin) in enumerate(state):
        for i, prop in fn(doc, cur, pin):
            key = (di, i)
            flag.add(key)
            a, b, g, p = cur[i]
            if g != p:
                hit += 1
                if prop == g: fixed += 1
    sets[nm] = flag
    n = len(flag)
    print("  %-16s%10s%12s%11.2f%%%12s%9.2f%%"
          % (nm, format(n, ","), format(hit, ","), 100*hit/n if n else 0,
             format(fixed, ","), 100*fixed/nbad0))

print()
print("=" * 98)
print("E1b — CHONG LAN giua cac tap canh bi gan co")
print("=" * 98)
ks = [nm for nm, _ in LAYERS]
print("  %-18s" % "" + "".join("%16s" % k for k in ks))
for a_ in ks:
    row = "  %-18s" % a_
    for b_ in ks:
        inter = len(sets[a_] & sets[b_])
        row += "%16s" % (format(inter, ",") if a_ != b_ else ("(%s)" % format(len(sets[a_]), ",")))
    print(row)
allf = sets[ks[0]] | sets[ks[1]] | sets[ks[2]]
only = {k: len(sets[k] - set().union(*[sets[x] for x in ks if x != k])) for k in ks}
print()
print("  hop cua ba tang: %s canh" % format(len(allf), ","))
for k in ks:
    print("    chi %-14s tim duoc rieng: %s" % (k, format(only[k], ",")))
tri = len(sets[ks[0]] & sets[ks[1]] & sets[ks[2]])
print("    ca ba cung gan co: %s" % format(tri, ","))

print()
print("=" * 98)
print("E1c — INCREMENTAL: chay noi tiep, moi tang chi xet canh chua ai sua")
print("=" * 98)
for order in ([0, 1, 2], [2, 1, 0]):
    nm_order = " -> ".join(LAYERS[i][0] for i in order)
    print("  thu tu: %s" % nm_order)
    cur_state = [(doc, [list(e) for e in cur], pin) for doc, cur, pin in state]
    done = set(); cum = 0
    for oi in order:
        nm, fn = LAYERS[oi]
        newflag = 0; newfix = 0
        for di, (doc, cur, pin) in enumerate(cur_state):
            for i, prop in fn(doc, cur, pin):
                if (di, i) in done: continue
                done.add((di, i)); newflag += 1
                a, b, g, p = cur[i]
                if g != p and prop == g:
                    newfix += 1
                if prop: cur[i][3] = prop
        cum += newfix
        print("    + %-14s gan co moi %7s   sua dung moi %6s   R_all luy ke %6.2f%%"
              % (nm, format(newflag, ","), format(newfix, ","), 100*cum/nbad0))
    left = sum(1 for _, cur, _ in cur_state for e in cur if e[2] != e[3])
    print("    canh sai con lai: %s / %s  (%.2f%% -> %.2f%%)"
          % (format(left, ","), format(nbad0, ","), 100*nbad0/npair, 100*left/npair))
    print()

print("=" * 98)
print("E1d — DATE BRIDGE tren do thi DU DOAN co con 100% precision khong?")
print("=" * 98)
n = tp = 0
for di, (doc, cur, pin) in enumerate(state):
    for i, (a, b, g, p) in enumerate(cur):
        A, B = pin.get(a), pin.get(b)
        if not A or not B or len(A) > 1 or len(B) > 1: continue
        da, db = next(iter(A)), next(iter(B))
        if da >= db: continue
        n += 1
        if g == "BEFORE": tp += 1
print("  'd1<d2 => BEFORE' tren %s cap co du ngay y/m/d: %s dung = %.2f%%"
      % (format(n, ","), format(tp, ","), 100*tp/n if n else 0))
print("  (pin lay tu target_edges gold cua timex; tren he that chung cung phai du doan)")
