# -*- coding: utf-8 -*-
"""Task 2 on injected noise WITH the auditor: does the auditor help when errors are random?

Same cross-fit protocol as bai2_combo.py (valid split in two folds by hash; inside the training
fold MINE / CONFIRM / TUNE), but the graph under audit is the gold validation graph with ALL four
edge kinds corrupted at rate rho by inj_eval.corrupt (seed 37, identical to Table 3 of the paper).
The auditor is re-learnt on these injected errors, so it never sees classifier errors.

Rows (macro-F1 objective, every choice made on TUNE, test fold scored once, both folds summed):
  auditor only
  triangle only, channel known (generator)        -> comparable to the paper's injected-noise row
  triangle only, channel estimated on TUNE
  auditor -> triangle, channel estimated on TUNE  (the auditor changes the noise, so the generator
                                                   no longer describes the auditor's output)
Usage: TAG=_full python inj_audit.py 0.10 0.20
"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import io, os, json, math, random, hashlib, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_J = io.open(HERE/"joint_repair.py", encoding="utf-8").read()
exec(SRC_J[:SRC_J.index("def evaluate(docs, obs_of, fin_of):")])
JR_VA = {d["id"]: d for d in VA}; JR_VALIST = list(VA); JR_repair = repair; JR_conf = chan_confusion; JR_Q = Q
JR_inj = chan_injected; JR_MARG = MARG; JR_LABS = list(LABS)
SRC_B = io.open(HERE/"bai2_layered.py", encoding="utf-8").read()
exec(SRC_B[:SRC_B.index('print("=" * 130)')])
OBS = ("ONT", "ARG", "DISC", "LEX", "TIME")
LAYB = OBS + ("GRAPH",)
def H(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)

def corrupt(docs, rho, seed):                      # identical to inj_eval.corrupt
    rng = random.Random(seed); out = {}
    for d in docs:
        o = []
        for (a, b, r, k) in d["edges"]:
            if rng.random() < rho:
                labs = [x for x in JR_LABS if x != r and JR_MARG[k][x] > 0]
                o.append(rng.choices(labs, [JR_MARG[k][x] for x in labs])[0])
            else: o.append(r)
        out[d["id"]] = o
    return out

JGRID = [("mean", l, a) for l in (0.2, 0.5, 1.0, 2.0) for a in (0.0, 0.5)] + [("sum", l, 0.0) for l in (0.03, 0.1)]
def joint_fit_apply(tune_docs, test_docs, obs_tune, obs_test, C=None):
    """Channel = confusion of the observed labels on TUNE unless C is given; grid on TUNE by macro-F1."""
    if C is None: C = JR_conf([JR_VA[d] for d in tune_docs], lambda dd: obs_tune[dd["id"]])
    best = None
    for mode, lam, alpha in JGRID:
        pred = []; gold = []
        for docid in tune_docs:
            d = JR_VA[docid]; fin = JR_repair(d, obs_tune[docid], C, lam, mode, alpha)
            pred += fin; gold += [e[2] for e in d["edges"]]
        val = prf(pred, gold)[0]
        if best is None or val > best[0]: best = (val, mode, lam, alpha)
    _, mode, lam, alpha = best
    return {docid: JR_repair(JR_VA[docid], obs_test[docid], C, lam, mode, alpha) for docid in test_docs}, (mode, lam, alpha)

def report(nm, start, fin, docs_all):
    c = Counter(); pred = []; gold = []; per = defaultdict(Counter)
    for docid in docs_all:
        d = JR_VA[docid]
        for e, s, f in zip(d["edges"], start[docid], fin[docid]):
            c["n"] += 1; c["b0"] += (s != e[2]); c["b1"] += (f != e[2]); per[e[3]]["n"] += 1; per[e[3]]["b0"] += (s != e[2]); per[e[3]]["b1"] += (f != e[2])
            if f != s:
                c["flag"] += 1
                if s != e[2]: c["hit"] += 1; c["fix"] += (f == e[2])
                else: c["brk"] += 1
            pred.append(f); gold.append(e[2])
    P = c["hit"]/max(1, c["flag"]); R = c["hit"]/max(1, c["b0"]); F = 2*P*R/(P+R) if P+R else 0
    m, perl, acc = prf(pred, gold)
    sp = [(f, e[2]) for docid in docs_all for e, s, f in zip(JR_VA[docid]["edges"], start[docid], fin[docid]) if s != e[2]]
    ms, pl2, acc2 = prf([x[0] for x in sp], [x[1] for x in sp])
    print("  %-34s P %6.2f%% R %6.2f%% F1 %6.2f%%  sua %6d hong %5d rong %+6d  loi %5.2f%% -> %5.2f%%  macro-F1 %6.2f%%  | recovered acc %5.2f%% macro %5.2f%%"
          % (nm, 100*P, 100*R, 100*F, c["fix"], c["brk"], c["b0"]-c["b1"], 100*c["b0"]/c["n"], 100*c["b1"]/c["n"], 100*m, 100*acc2, 100*ms))
    print("      loi theo loai: " + "   ".join("%s %.1f->%.1f" % (k, 100*per[k]["b0"]/per[k]["n"], 100*per[k]["b1"]/per[k]["n"]) for k in ("EE", "ET", "TE", "TT"))
          + "   | F1 nhan: " + "  ".join("%s %.1f" % (r[:4], 100*perl[r][2]) for r in LABS), flush=True)

docs_all = sorted({x["doc"] for x in IVA})
for rho in [float(a) for a in (sys.argv[1:] or ["0.10", "0.20"])]:
    obs_inj = corrupt(JR_VALIST, rho, 37)
    lab = {"%s|%s|%s" % (did, e[0], e[1]): o for did, d in JR_VA.items() for e, o in zip(d["edges"], obs_inj[did])}
    miss = 0
    for x in IVA:
        if x["key"] in lab: x["inj"] = lab[x["key"]]
        else: x["inj"] = x["g"]; miss += 1
    for x in ITR: x["inj"] = x["g"]           # train instances are never audited; set_graph needs the field
    set_graph("inj")
    start = {d: obs_inj[d] for d in docs_all}
    log("rho %.2f: %d instance, %d khong khop canh JR" % (rho, len(IVA), miss))
    rows = defaultdict(dict)
    for k in (0, 1):
        trn = [d for d in docs_all if H("cf" + d) % 2 != k]; tst = [d for d in docs_all if H("cf" + d) % 2 == k]
        part = lambda d: H("in3" + d) % 3
        mine = [x for d in trn if part(d) == 0 for x in BYDOC[d]]
        conf = [x for d in trn if part(d) == 1 for x in BYDOC[d]]
        tune_docs = [d for d in trn if part(d) == 2]; tune_x = [x for d in tune_docs for x in BYDOC[d]]
        test = [x for d in tst for x in BYDOC[d]]
        AR = audit_rules(mine, conf, "inj", LAYB, True); idx = rule_index(AR)
        activate(tune_x + test, AR, "inj", LAYB)
        TH = tune(idx, tune_x, "inj", "macro")
        bt = {x["key"]: v for x, v in zip(tune_x, classify_k(idx, TH, tune_x, "inj"))}
        bs = {x["key"]: v for x, v in zip(test, classify_k(idx, TH, test, "inj"))}
        tolab = lambda d, m: [m.get("%s|%s|%s" % (d, e[0], e[1]), s) for e, s in zip(JR_VA[d]["edges"], start[d])]
        obs_tune_B = {d: tolab(d, bt) for d in tune_docs}; obs_test_B = {d: tolab(d, bs) for d in tst}
        for d in tst: rows["auditor only"][d] = obs_test_B[d]
        fin, cfg1 = joint_fit_apply(tune_docs, tst, obs_tune_B, obs_test_B)
        for d in tst: rows["auditor -> triangle (est. channel)"][d] = fin[d]
        fin, cfg2 = joint_fit_apply(tune_docs, tst, {d: start[d] for d in tune_docs}, {d: start[d] for d in tst})
        for d in tst: rows["triangle only (est. channel)"][d] = fin[d]
        fin, cfg3 = joint_fit_apply(tune_docs, tst, {d: start[d] for d in tune_docs}, {d: start[d] for d in tst}, JR_inj(rho))
        for d in tst: rows["triangle only (known channel)"][d] = fin[d]
        log("  fold %d: %d audit rules; aud->tri %s, tri(est) %s, tri(known) %s" % (k, len(AR), cfg1, cfg2, cfg3))
    print("=" * 130); print("NHIEU BOM %.0f%% MOI LOAI CANH -- auditor hoc lai tren nhieu bom, cross-fit tren valid" % (100*rho)); print("=" * 130)
    m0 = prf([q for d in docs_all for q in start[d]], [e[2] for d in docs_all for e in JR_VA[d]["edges"]])[0]
    print("  %-34s macro-F1 %.2f%%" % ("do thi nhieu (chua sua)", 100*m0))
    for nm in ("auditor only", "triangle only (known channel)", "triangle only (est. channel)", "auditor -> triangle (est. channel)"):
        report(nm, start, rows[nm], docs_all)
log("xong")
