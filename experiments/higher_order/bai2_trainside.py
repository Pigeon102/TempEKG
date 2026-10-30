# -*- coding: utf-8 -*-
"""Task 2 learnt entirely on the training split, evaluated once on the whole validation set.

Instead of cross-fitting on validation (bai2_combo.py), everything Task 2 learns comes from the Task 1
predictions on the TUNING part of the training split (587 documents). Those documents took no part in
proposing or re-scoring the Task 1 rules (only in choosing its per-label thresholds), so their errors are
out of sample for the rules. The tuning documents are divided by hash into three thirds:
  MINE      mines the audit rules
  CONFIRM   confirms them
  TUNE      selects the audit thresholds, then estimates the noise channel on the auditor's output and
            selects triangle weight, gamma and mode, all by macro-F1
PMI statistics stay on the gold graphs of the DISCOVERY + CONFIRMATION parts. The 710 validation
documents are used only for the final score.  Run from src/ with TAG=_full.
"""
import os as _os, sys as _sys
if _os.environ.get("PYTHONHASHSEED") != "0":   # set iteration order must not depend on the hash seed
    import subprocess as _sp; _os.environ["PYTHONHASHSEED"] = "0"
    _sys.exit(_sp.call([_sys.executable] + _sys.argv))

import io, os, json, math, hashlib
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC_J = io.open(HERE/"joint_repair.py", encoding="utf-8").read()
exec(SRC_J[:SRC_J.index("def evaluate(docs, obs_of, fin_of):")])
JR = {d["id"]: d for d in VA}; JR.update({d["id"]: d for d in TUNE})
JR_repair = repair; JR_conf = chan_confusion
SRC_B = io.open(HERE/"bai2_layered.py", encoding="utf-8").read()
exec(SRC_B[:SRC_B.index('print("=" * 130)')])
OBS = ("ONT", "ARG", "DISC", "LEX", "TIME"); LAYB = OBS + ("GRAPH",)
set_graph("n1")
def H(s): return int(hashlib.md5(s.encode()).hexdigest(), 16)

def to_doc_labels(docid, labmap):
    return [labmap.get("%s|%s|%s" % (docid, e[0], e[1]), "BEFORE") for e in JR[docid]["edges"]]

JGRID = [("mean", l, a) for l in (0.2, 0.5, 1.0, 2.0) for a in (0.0, 0.5)] + [("sum", l, 0.0) for l in (0.03, 0.1)]
def joint_fit_apply(tune_docs, test_docs, obs_tune, obs_test):
    C = JR_conf([JR[d] for d in tune_docs], lambda dd: obs_tune[dd["id"]])
    best = None
    for mode, lam, alpha in JGRID:
        pred, gold = [], []
        for d in tune_docs:
            pred += JR_repair(JR[d], obs_tune[d], C, lam, mode, alpha); gold += [e[2] for e in JR[d]["edges"]]
        v = prf(pred, gold)[0]
        if best is None or v > best[0]: best = (v, mode, lam, alpha)
    _, mode, lam, alpha = best
    return {d: JR_repair(JR[d], obs_test[d], C, lam, mode, alpha) for d in test_docs}, (mode, lam, alpha)

learn = sorted(d["id"] for d in TUNE if d["id"] in BYDOC)
valid = sorted({x["doc"] for x in IVA})
part = lambda d: H("in3" + d) % 3
mine = [x for d in learn if part(d) == 0 for x in BYDOC[d]]
conf = [x for d in learn if part(d) == 1 for x in BYDOC[d]]
tune_docs = [d for d in learn if part(d) == 2]; tune_x = [x for d in tune_docs for x in BYDOC[d]]
test_x = [x for d in valid for x in BYDOC[d]]
log("learn on %d training documents (mine %d, confirm %d, tune %d); test on %d validation documents"
    % (len(learn), len({x['doc'] for x in mine}), len({x['doc'] for x in conf}), len(tune_docs), len(valid)))
AR = audit_rules(mine, conf, "n1", LAYB, True); idx = rule_index(AR)
activate(tune_x + test_x, AR, "n1", LAYB)
TH = tune(idx, tune_x, "n1", "macro")
bt = {x["key"]: v for x, v in zip(tune_x, classify_k(idx, TH, tune_x, "n1"))}
bs = {x["key"]: v for x, v in zip(test_x, classify_k(idx, TH, test_x, "n1"))}
start_t = {d: to_doc_labels(d, {x["key"]: x["n1"] for x in BYDOC[d]}) for d in tune_docs}
start_v = {d: to_doc_labels(d, {x["key"]: x["n1"] for x in BYDOC[d]}) for d in valid}
aud_t = {d: to_doc_labels(d, bt) for d in tune_docs}; aud_v = {d: to_doc_labels(d, bs) for d in valid}
rows = {"auditor only": aud_v}
rows["auditor -> triangle"], c1 = joint_fit_apply(tune_docs, valid, aud_t, aud_v)
rows["triangle only"], c2 = joint_fit_apply(tune_docs, valid, start_t, start_v)
log("configs: aud->tri %s, tri only %s" % (c1, c2))

print("=" * 130); print("TASK 2 LEARNT ON THE TRAINING TUNING PART, SCORED ONCE ON THE VALIDATION SET"); print("=" * 130)
gold = [e[2] for d in valid for e in JR[d]["edges"]]
m0 = prf([s for d in valid for s in start_v[d]], gold)[0]
print("  %-22s macro-F1 %.2f%%  error %.2f%%" % ("unrepaired", 100 * m0, 100 * sum(s != g for s, g in zip([s for d in valid for s in start_v[d]], gold)) / len(gold)))
for nm, fin in rows.items():
    c = Counter(); pred = []
    for d in valid:
        for e, s, f in zip(JR[d]["edges"], start_v[d], fin[d]):
            g = e[2]; c["n"] += 1; c["b0"] += (s != g); c["b1"] += (f != g)
            if f != s:
                c["flag"] += 1
                if s != g: c["hit"] += 1; c["fix"] += (f == g)
                else: c["brk"] += 1
            pred.append(f)
    P = c["hit"] / max(1, c["flag"]); R = c["hit"] / max(1, c["b0"]); F = 2 * P * R / (P + R) if P + R else 0
    m, per, acc = prf(pred, gold)
    print("  %-22s macro-F1 %.2f%%  error %.2f%% -> %.2f%% | P %.1f R %.1f F1 %.1f | fixed %d broken %d net %+d | %s"
          % (nm, 100 * m, 100 * c["b0"] / c["n"], 100 * c["b1"] / c["n"], 100 * P, 100 * R, 100 * F, c["fix"], c["brk"], c["fix"] - c["brk"],
             "  ".join("%s %.1f" % (r[:4], 100 * per[r][2]) for r in LABS)), flush=True)
log("xong")
