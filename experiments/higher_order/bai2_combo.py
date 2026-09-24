# -*- coding: utf-8 -*-
"""Bai 2, classifier noise: layered auditor B FIRST (per-edge rules), THEN document-level joint
repair over triangles on B's output -- cross-fitted on valid.

Why cross-fit: the classifier's errors are only out-of-sample on valid; audit rules and the
joint model's noise channel must be learnt on errors of the same kind. Valid documents are split
in two folds by hash; inside the training fold, three parts by another hash: MINE (audit rules),
CONFIRM (audit rules' confirmation), TUNE (audit floors, then the joint model's channel =
confusion of B's output, lambda, alpha, mode). The test fold is scored once; both folds summed.

Rows (all against the layered classifier's graph, error 15.11%, macro-F1 30.83%):
  B only, joint only (channel = classifier confusion on TUNE), B -> joint
each with the objective 'net errors' and 'macro-F1' used for every choice made on TUNE.
"""
import io, os, json, math, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_J = io.open(HERE/"joint_repair.py", encoding="utf-8").read()
exec(SRC_J[:SRC_J.index("def evaluate(docs, obs_of, fin_of):")])
JR_VA = {d["id"]: d for d in VA}; JR_repair = repair; JR_conf = chan_confusion; JR_Q = Q
SRC_B = io.open(HERE/"bai2_layered.py", encoding="utf-8").read()
exec(SRC_B[:SRC_B.index('print("=" * 130)')])
OBS = ("ONT", "ARG", "DISC", "LEX", "TIME")
LAYB = OBS + ("GRAPH",)
set_graph("n1")
def H(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)
KEY = {x["key"]: x for x in IVA}

def to_doc_labels(docid, labmap):
    d = JR_VA[docid]
    return [labmap.get("%s|%s|%s" % (docid, e[0], e[1]), "BEFORE") for e in d["edges"]]

JGRID = [("mean", l, a) for l in (0.2, 0.5, 1.0, 2.0) for a in (0.0, 0.5)] + [("sum", l, 0.0) for l in (0.03, 0.1)]
def joint_fit_apply(tune_docs, test_docs, obs_tune, obs_test, objective):
    """Channel = confusion of the observed labels on TUNE; grid on TUNE; apply to test."""
    C = JR_conf([JR_VA[d] for d in tune_docs], lambda dd: obs_tune[dd["id"]])
    best = None
    for mode, lam, alpha in JGRID:
        pred = []; gold = []; c = Counter()
        for docid in tune_docs:
            d = JR_VA[docid]; fin = JR_repair(d, obs_tune[docid], C, lam, mode, alpha)
            for e, s, f in zip(d["edges"], obs_tune[docid], fin):
                c["b0"] += (s != e[2]); c["b1"] += (f != e[2]); pred.append(f); gold.append(e[2])
        val = (c["b0"] - c["b1"]) if objective == "net" else prf(pred, gold)[0]
        if best is None or val > best[0]: best = (val, mode, lam, alpha)
    _, mode, lam, alpha = best
    return {docid: JR_repair(JR_VA[docid], obs_test[docid], C, lam, mode, alpha) for docid in test_docs}, (mode, lam, alpha)

rows = defaultdict(dict)          # row name -> docid -> final labels (list, JR edge order)
docs_all = sorted({x["doc"] for x in IVA})
start = {docid: to_doc_labels(docid, {x["key"]: x["n1"] for x in BYDOC[docid]}) for docid in docs_all}
for k in (0, 1):
    S_ = os.environ.get("SEED", "")
    trn = [d for d in docs_all if H(S_ + "cf" + d) % 2 != k]; tst = [d for d in docs_all if H(S_ + "cf" + d) % 2 == k]
    part = lambda d: H(S_ + "in3" + d) % 3
    mine = [x for d in trn if part(d) == 0 for x in BYDOC[d]]
    conf = [x for d in trn if part(d) == 1 for x in BYDOC[d]]
    tune_docs = [d for d in trn if part(d) == 2]; tune_x = [x for d in tune_docs for x in BYDOC[d]]
    test = [x for d in tst for x in BYDOC[d]]
    log("fold %d: mine %d, confirm %d, tune %d doc, test %d doc" % (k, len({x['doc'] for x in mine}), len({x['doc'] for x in conf}), len(tune_docs), len(tst)))
    AR = audit_rules(mine, conf, "n1", LAYB, True); idx = rule_index(AR)
    activate(tune_x + test, AR, "n1", LAYB)
    for obj in ("net", "macro"):
        TH = tune(idx, tune_x, "n1", obj)
        b_tune = classify_k(idx, TH, tune_x, "n1"); b_test = classify_k(idx, TH, test, "n1")
        bt = {x["key"]: v for x, v in zip(tune_x, b_tune)}; bs = {x["key"]: v for x, v in zip(test, b_test)}
        obs_tune_B = {d: to_doc_labels(d, bt) for d in tune_docs}; obs_test_B = {d: to_doc_labels(d, bs) for d in tst}
        for d in tst: rows["B | " + obj][d] = obs_test_B[d]
        fin, cfg_ = joint_fit_apply(tune_docs, tst, obs_tune_B, obs_test_B, obj)
        for d in tst: rows["B -> tam giac | " + obj][d] = fin[d]
        fin2, cfg2 = joint_fit_apply(tune_docs, tst, {d: start[d] for d in tune_docs}, {d: start[d] for d in tst}, obj)
        for d in tst: rows["chi tam giac | " + obj][d] = fin2[d]
        log("  fold %d %s: B->joint %s, joint-only %s" % (k, obj, cfg_, cfg2))

print()
print("=" * 130)
print("BAI 2 -- NHIEU CLASSIFIER, CROSS-FIT TREN VALID: auditor tang B, sua chung tam giac, va ghep ca hai")
print("=" * 130)
def report(nm, fin):
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
    print("  %-26s P %6.2f%% R %6.2f%% F1 %6.2f%%  sua %6d hong %5d rong %+6d  loi %5.2f%% -> %5.2f%%  macro-F1 %6.2f%%"
          % (nm, 100*P, 100*R, 100*F, c["fix"], c["brk"], c["b0"]-c["b1"], 100*c["b0"]/c["n"], 100*c["b1"]/c["n"], 100*m))
    print("      loi theo loai: " + "   ".join("%s %.1f->%.1f" % (k, 100*per[k]["b0"]/per[k]["n"], 100*per[k]["b1"]/per[k]["n"]) for k in ("EE", "ET", "TE", "TT"))
          + "   | F1 nhan: " + "  ".join("%s %.1f" % (r[:4], 100*perl[r][2]) for r in LABS))
m0 = prf([q for d in docs_all for q in start[d]], [e[2] for d in docs_all for e in JR_VA[d]["edges"]])[0]
print("  %-26s loi %.2f%%  macro-F1 %.2f%%" % ("do thi classifier tang", 100*sum(1 for d in docs_all for e, q in zip(JR_VA[d]["edges"], start[d]) if q != e[2])/sum(len(JR_VA[d]["edges"]) for d in docs_all), 100*m0))
for nm in ("B | net", "chi tam giac | net", "B -> tam giac | net", "B | macro", "chi tam giac | macro", "B -> tam giac | macro"):
    report(nm.replace("net", "giam loi").replace("macro", "macro-F1") if nm.endswith(("net", "macro")) else nm, rows[nm])
log("xong")
