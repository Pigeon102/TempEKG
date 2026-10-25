# -*- coding: utf-8 -*-
"""Triangle diagnostics quoted in Sec. 4.3 and Sec. 1, re-measured on the CURRENT pipeline.

Replaces the earlier subgraph_probe.py / diag_b.py measurements (tag pre-cleanup), which used an
earlier classifier and gold statistics over all train documents but the first 400.

  statistics   triangle configurations counted on the gold graphs of the DISCOVERY + CONFIRMATION
               parts, exactly the table used by triangle repair (joint_repair.STATS)
  graphs       (a) Task 1 output (pred_layered_full.json)
               (b) all-edge injected noise at 10% (inj_eval.corrupt, seed 37, as in Table 5)
  measures     1. share of wrong edges that lie in at least one triangle whose configuration has
                  count 0 in the gold statistics ("unseen")
               2. clustering: over every triangle that contains a wrong edge, the share of the
                  other two edges that are also wrong (as in diag_b), next to the overall error rate
Run from src/ with TAG=_full.
"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import io, random
from pathlib import Path
from collections import Counter, defaultdict
HERE = Path(__file__).resolve().parent
SRC_J = io.open(HERE/"joint_repair.py", encoding="utf-8").read()
exec(SRC_J[:SRC_J.index("def evaluate(docs, obs_of, fin_of):")])

SYMM_ = {"SIMULTANEOUS", "BEGINS-ON"}
def inv_(l): return l if l in SYMM_ else ("i" + l)
def kinds(d): return {n: ("E" if v.get("kind") == "event" else "T") for n, v in d["nd"].items() if v.get("kind") in ("event", "timex")}

def triangles(d, lab):
    """Yield the three edge indices of every triangle and its configuration under labels lab."""
    K = kinds(d); L = {}; nbr = defaultdict(set); idx = {}
    for i, ((a, b, r, k), q) in enumerate(zip(d["edges"], lab)):
        L[(a, b)] = q; L[(b, a)] = inv_(q); nbr[a].add(b); nbr[b].add(a); idx[(a, b)] = i; idx[(b, a)] = i
    for a in sorted(nbr):
        for b in sorted(nbr[a]):
            if b <= a: continue
            for c in sorted(nbr[a] & nbr[b]):
                if c <= b: continue
                cfg = (K[a], K[b], K[c], L[(a, b)], L[(b, c)], L[(a, c)])
                yield (idx[(a, b)], idx[(b, c)], idx[(a, c)]), cfg

FREQ_P = Counter()
for d in STATS:
    for _, c in triangles(d, [e[2] for e in d["edges"]]): FREQ_P[c] += 1
print("gold statistics: %d documents, %d configurations, %d triangles" % (len(STATS), len(FREQ_P), sum(FREQ_P.values())))

def corrupt(docs, rho, seed):                      # identical to inj_eval.corrupt
    rng = random.Random(seed); out = {}
    for d in docs:
        o = []
        for (a, b, r, k) in d["edges"]:
            if rng.random() < rho:
                labs = [x for x in LABS if x != r and MARG[k][x] > 0]
                o.append(rng.choices(labs, [MARG[k][x] for x in labs])[0])
            else: o.append(r)
        out[d["id"]] = o
    return out

def probe(name, lab_of):
    n = bad = 0; wrong_unseen = 0; nb = nb_bad = 0
    for d in VA:
        lab = lab_of(d); gold = [e[2] for e in d["edges"]]
        wrong = {i for i, (q, g) in enumerate(zip(lab, gold)) if q != g}
        n += len(lab); bad += len(wrong); hit = set()
        for ids, c in triangles(d, lab):
            if FREQ_P.get(c, 0) == 0: hit.update(i for i in ids if i in wrong)
            for i in ids:
                if i in wrong:
                    for j in ids:
                        if j != i: nb += 1; nb_bad += (j in wrong)
        wrong_unseen += len(hit)
    print("%-28s error %5.2f%% | wrong edges in >=1 unseen configuration %6d / %6d = %5.1f%% | "
          "triangle neighbours of wrong edges also wrong %5.1f%%"
          % (name, 100*bad/n, wrong_unseen, bad, 100*wrong_unseen/max(1, bad), 100*nb_bad/max(1, nb)))

probe("Task 1 output", lambda d: [PL.get("%s|%s|%s" % (d["id"], e[0], e[1]), "BEFORE") for e in d["edges"]])
INJ = corrupt(VA, 0.10, 37)
probe("all-edge injected 10%", lambda d: INJ[d["id"]])
log("xong")
