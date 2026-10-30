# -*- coding: utf-8 -*-
"""How many sweeps does triangle repair need? Same repair as joint_repair.repair, but run for up to 20
sweeps, recording after every sweep the labels, the number of label changes and whether the work list
is empty. Three settings, each with its configuration chosen exactly as in the paper (4 sweeps):
  Task 1 output   cross-fit on valid (two hash folds; channel and config from the TUNE third)
  all edges 10%   injected noise, known channel, config chosen on the training tuning part
  all edges 20%   same
Run from src/ with TAG=_full.  Log: experiments/logs/icm_convergence.log"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import io, math, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
JSRC = io.open(HERE/"joint_repair.py", encoding="utf-8").read()
exec(JSRC[:JSRC.index("def evaluate(docs, obs_of, fin_of):")])
exec(JSRC[JSRC.index("def corrupt(docs, rho, seed):"):JSRC.index("print()\nprint(\"=\" * 130)")])
def H(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)
MAXS = 20

def repair_trace(d, obs, C, lam, mode, alpha):
    """joint_repair.repair with snapshots: returns ([labels after sweep 1..MAXS], [changes per sweep])."""
    lab = list(obs); edges = d["edges"]; tris = d["tris"]; inc = d["inc"]
    def local(j, l):
        k = edges[j][3]
        u = -(1 - alpha) * math.log(Q[k][l]) - C[(k, obs[j], l)]
        ts = inc.get(j, ())
        if not ts: return u
        s = 0.0
        for tid, pos_ in ts:
            kinds, parts = tris[tid]
            ol = [olab(lab[jj], rev) for jj, rev in parts]
            ol[pos_] = olab(l, parts[pos_][1])
            s -= tri_pmi(kinds, tuple(ol))
        if mode == "mean": s /= len(ts)
        return u + lam * s
    queue = []
    for tid, (kinds, parts) in enumerate(tris):
        if tri_pmi(kinds, tuple(olab(lab[j], rev) for j, rev in parts)) < 0:
            queue += [j for j, _ in parts]
    todo = set(queue); snaps = []; changes = []
    for _ in range(MAXS):
        nxt = set(); n = 0
        for j in todo:
            cur = lab[j]; best, bv = cur, local(j, cur)
            for l in LABS:
                if l == cur or Q[edges[j][3]][l] < 1e-4: continue
                v = local(j, l)
                if v < bv - 1e-9: best, bv = l, v
            if best != cur:
                lab[j] = best; n += 1
                for tid, _ in inc.get(j, ()):
                    for jj, _ in tris[tid][1]:
                        if jj != j: nxt.add(jj)
        todo = nxt; snaps.append(list(lab)); changes.append(n)
    return snaps, changes

JGRID = [("mean", l, a) for l in (0.2, 0.5, 1.0, 2.0) for a in (0.0, 0.5)] + [("sum", l, 0.0) for l in (0.03, 0.1)]
def pick(docs, obs, C):
    best = None
    for mode, lam, alpha in JGRID:
        pred = [l for d in docs for l in repair(d, obs[d["id"]], C, lam, mode, alpha)]
        m = prf(pred, [e[2] for d in docs for e in d["edges"]])[0]
        if best is None or m > best[0]: best = (m, mode, lam, alpha)
    return best[1:]

def report(title, runs):
    """runs: list of (doc, snaps, changes)."""
    print("=" * 110); print(title); print("=" * 110)
    gold = [e[2] for d, _, _ in runs for e in d["edges"]]
    tot = [sum(ch[s] for _, _, ch in runs) for s in range(MAXS)]
    print("  sweep | label changes | docs still changing | error after sweep | macro-F1 after sweep")
    for s in range(MAXS):
        pred = [l for _, sn, _ in runs for l in sn[s]]
        err = sum(p != g for p, g in zip(pred, gold)) / len(gold)
        live = sum(1 for _, _, ch in runs if ch[s] > 0)
        print("  %5d | %13d | %19d | %16.2f%% | %18.2f%%" % (s + 1, tot[s], live, 100 * err, 100 * prf(pred, gold)[0]), flush=True)
        if s >= 5 and tot[s] == 0 and all(t == 0 for t in tot[s:]): break
    after4 = sum(tot[4:]); total = sum(tot)
    print("  changes after sweep 4: %d of %d (%.2f%%)" % (after4, total, 100 * after4 / max(1, total)), flush=True)

# 1. Task 1 output, cross-fit exactly as the 'triangle only' row
START = {d["id"]: [PL.get("%s|%s|%s" % (d["id"], e[0], e[1]), "BEFORE") for e in d["edges"]] for d in VA}
runs = []
for k in (0, 1):
    trn = [d for d in VA if H("cf" + d["id"]) % 2 != k]; tst = [d for d in VA if H("cf" + d["id"]) % 2 == k]
    tune = [d for d in trn if H("in3" + d["id"]) % 3 == 2]
    C = chan_confusion(tune, lambda dd: START[dd["id"]])
    mode, lam, alpha = pick(tune, START, C); log("fold %d: %s %.2f %.1f" % (k, mode, lam, alpha))
    for d in tst: runs.append((d,) + repair_trace(d, START[d["id"]], C, lam, mode, alpha))
report("TASK 1 OUTPUT, triangle only (cross-fit)", runs)

# 2. injected noise on all four edge kinds
for rho in (0.10, 0.20):
    C = chan_injected(rho); tune_obs = corrupt(TUNE, rho, 51); obs = corrupt(VA, rho, 37)
    mode, lam, alpha = pick(TUNE, tune_obs, C); log("rho %.2f: %s %.2f %.1f" % (rho, mode, lam, alpha))
    report("ALL EDGES %.0f%% injected (%s, beta %.2f, gamma %.1f)" % (100 * rho, mode, lam, alpha),
           [(d,) + repair_trace(d, obs[d["id"]], C, lam, mode, alpha) for d in VA])
log("xong")
