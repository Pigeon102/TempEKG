# -*- coding: utf-8 -*-
"""Repair on logically admissible errors vs errors inside a logical conflict.

A triangle (three nodes, three temporal edges) is in a *logical conflict* when its three labels, mapped to
Allen relations as in Sec. 3.4 (BEFORE {b}, CONTAINS {di}, OVERLAP {o}, SIMULTANEOUS {e}, BEGINS-ON {s,si,e},
ENDS-ON {b,m}), fail path consistency on the triangle. The composition table is built by brute force over
integer intervals (as in tempekg_kg/constraint_net.py). An edge that was wrong after Task 1 falls in one group:
  conflict     it lies in at least one triangle in a logical conflict (under the Task 1 labels)
  admissible   it lies in triangles, none of them in a logical conflict
  no triangle  it lies in no triangle
For each Task 2 configuration of the final cross-fitted run (bai2_rows_full.pkl) we report, per group,
how many wrong edges are restored to gold, changed to another wrong label, or left unchanged.
Sanity check: the gold labels must give no triangle in a logical conflict.  Run from src/.
Log: experiments/logs/logic_split.log"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import json, pickle
from collections import Counter, defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"

# ---------------------------------------------------------------- Allen algebra (brute force)
ALL13 = ("b", "bi", "m", "mi", "o", "oi", "s", "si", "d", "di", "f", "fi", "e")
CONVERSE = {"b": "bi", "bi": "b", "m": "mi", "mi": "m", "o": "oi", "oi": "o",
            "s": "si", "si": "s", "d": "di", "di": "d", "f": "fi", "fi": "f", "e": "e"}
ALLEN = {"BEFORE": frozenset({"b"}), "CONTAINS": frozenset({"di"}), "OVERLAP": frozenset({"o"}),
         "SIMULTANEOUS": frozenset({"e"}), "BEGINS-ON": frozenset({"s", "si", "e"}), "ENDS-ON": frozenset({"b", "m"})}

def basic(a, b):
    (s1, e1), (s2, e2) = a, b
    if e1 < s2: return "b"
    if e1 == s2: return "m"
    if s1 == s2 and e1 == e2: return "e"
    if s1 == s2: return "s" if e1 < e2 else "si"
    if e1 == e2: return "f" if s1 > s2 else "fi"
    if s1 < s2 and e2 < e1: return "di"
    if s2 < s1 and e1 < e2: return "d"
    if s1 < s2 < e1 < e2: return "o"
    if s2 < s1 < e2 < e1: return "oi"
    if e2 == s1: return "mi"
    return "bi"

IV = [(s, e) for s in range(7) for e in range(s + 1, 7)]
COMP = defaultdict(set)
for x in IV:
    for y in IV:
        r1 = basic(x, y)
        for z in IV: COMP[(r1, basic(y, z))].add(basic(x, z))
def compose(A, B): return frozenset(r for a in A for b in B for r in COMP[(a, b)])
def conv(A): return frozenset(CONVERSE[r] for r in A)

_cache = {}
def inconsistent(xy, yz, xz):
    """Path consistency on one triangle; arguments are Allen sets oriented x->y, y->z, x->z."""
    key = (xy, yz, xz)
    if key in _cache: return _cache[key]
    while True:
        nxz = xz & compose(xy, yz); nxy = xy & compose(nxz, conv(yz)); nyz = yz & compose(conv(nxy), nxz)
        if not (nxz and nxy and nyz): _cache[key] = True; return True
        if (nxy, nyz, nxz) == (xy, yz, xz): _cache[key] = False; return False
        xy, yz, xz = nxy, nyz, nxz

# ---------------------------------------------------------------- data
R = pickle.load(open(SRC / "artifacts" / "bai2_rows_full.pkl", "rb"))
start = R["start"]
docs = {}
for line in open(SRC / "graph" / "valid.jsonl", encoding="utf-8"):
    d = json.loads(line); nd = d["nodes"]
    es = [e for e in d["target_edges"] if nd[e["s"]]["kind"] in ("event", "timex") and nd[e["t"]]["kind"] in ("event", "timex")]
    docs[d["doc_id"]] = ([(e["s"], e["t"]) for e in es], [e["rel"] for e in es])

def triangles(pairs):
    """Yields ((i, rev), (j, rev), (k, rev)) for edges x->y, y->z, x->z of every triangle x < y < z."""
    at = {}; nbr = defaultdict(set)
    for i, (s, t) in enumerate(pairs):
        at[(s, t)] = (i, False); at[(t, s)] = (i, True); nbr[s].add(t); nbr[t].add(s)
    for x in nbr:
        for y in nbr[x]:
            if not x < y: continue
            for z in nbr[x] & nbr[y]:
                if y < z: yield at[(x, y)], at[(y, z)], at[(x, z)]

def rel(labels, ref):
    i, rev = ref; A = ALLEN[labels[i]]
    return conv(A) if rev else A

group = {}; tri_count = Counter()
for doc, (pairs, gold) in docs.items():
    lab = start[doc]; in_tri = set(); in_conf = set()
    for t in triangles(pairs):
        tri_count["all"] += 1
        if inconsistent(*(rel(gold, r) for r in t)): tri_count["gold_conflict"] += 1
        bad = inconsistent(*(rel(lab, r) for r in t))
        tri_count["task1_conflict"] += bad
        for i, _ in t:
            in_tri.add(i)
            if bad: in_conf.add(i)
    group[doc] = ["conflict" if i in in_conf else ("admissible" if i in in_tri else "no triangle") for i in range(len(pairs))]

print("=" * 110); print("LOGICAL CONFLICTS ON THE VALIDATION GRAPH (triangle path consistency, Allen mapping of Sec. 3.4)"); print("=" * 110)
print("  triangles %d | in a logical conflict: gold labels %d, Task 1 labels %d (%.2f%%)" % (
    tri_count["all"], tri_count["gold_conflict"], tri_count["task1_conflict"], 100 * tri_count["task1_conflict"] / tri_count["all"]))
G = ("conflict", "admissible", "no triangle")
n_wrong = Counter((group[doc][i]) for doc, (pairs, gold) in docs.items() for i in range(len(pairs)) if start[doc][i] != gold[i])
tot = sum(n_wrong.values())
print("  wrong Task 1 edges %d: " % tot + ", ".join("%s %d (%.1f%%)" % (g, n_wrong[g], 100 * n_wrong[g] / tot) for g in G))
print()
print("  %-24s %-12s %7s | %7s %7s %7s | %s" % ("configuration", "group", "wrong", "fixed", "w->w", "kept", "recovered"))
for nm, rows in sorted(R["rows"].items()):
    c = defaultdict(Counter)
    for doc, fin in rows.items():
        gold = docs[doc][1]
        for i, (s, f, g) in enumerate(zip(start[doc], fin, gold)):
            if s == g: continue
            k = group[doc][i]; c[k]["n"] += 1
            c[k]["fix" if f == g else ("ww" if f != s else "kept")] += 1
    for k in G:
        x = c[k]
        print("  %-24s %-12s %7d | %7d %7d %7d | %5.1f%%" % (nm, k, x["n"], x["fix"], x["ww"], x["kept"], 100 * x["fix"] / max(1, x["n"])), flush=True)
