# -*- coding: utf-8 -*-
"""Bai 2 ablations of the auditor (step 3.1, run alone, chosen by macro-F1), cross-fitted on valid exactly as
bai2_combo's 'B | macro-F1' row:
  pipeline        all observed layers + GRAPH, cross-layer rules, adaptive gate, partition (edge type, current label)
  no GRAPH        observed layers only
  no cross-layer  per-layer patterns only
  gate lift >= 2  k/n >= 2 * prior instead of min(2 * prior, (1 + prior) / 2)
  one partition   rules learnt per edge type only, not per (edge type, current label)
Run from src/ with TAG=_full. Log: experiments/logs/ablate_audit.log"""
import io, os
from pathlib import Path
HERE = Path(__file__).resolve().parent
SRC = io.open(HERE/"bai2_combo.py", encoding="utf-8").read()
SRC = SRC.replace("        need = min(2*pr_, (1 + pr_)/2)",
                  "        need = (2*pr_) if globals().get('GATE_LIFT2') else min(2*pr_, (1 + pr_)/2)")
SRC = SRC.replace("    for x in mine_set: parts[(x[\"k\"], x[field])].append(x)\n    for x in conf_set: cparts[(x[\"k\"], x[field])].append(x)",
                  "    for x in mine_set: parts[(x[\"k\"], 'ALL' if globals().get('ONE_PART') else x[field])].append(x)\n"
                  "    for x in conf_set: cparts[(x[\"k\"], 'ALL' if globals().get('ONE_PART') else x[field])].append(x)")
BL = io.open(HERE/"bai2_layered.py", encoding="utf-8").read()
assert "need = min(2*pr_, (1 + pr_)/2)" in BL
BL = BL.replace("        need = min(2*pr_, (1 + pr_)/2)",
                "        need = (2*pr_) if globals().get('GATE_LIFT2') else min(2*pr_, (1 + pr_)/2)")
BL = BL.replace('    for x in mine_set: parts[(x["k"], x[field])].append(x)\n    for x in conf_set: cparts[(x["k"], x[field])].append(x)',
                '    for x in mine_set: parts[(x["k"], "ALL" if globals().get("ONE_PART") else x[field])].append(x)\n'
                '    for x in conf_set: cparts[(x["k"], "ALL" if globals().get("ONE_PART") else x[field])].append(x)')
BL = BL.replace('        part = (x["k"], x[field]); pr_ = AR.get(part)',
                '        part = (x["k"], "ALL" if globals().get("ONE_PART") else x[field]); pr_ = AR.get(part)')
BL = BL.replace("        cur = part[1]", "        cur = part[1] if part[1] != 'ALL' else Counter(x['g'] for x in disc_).most_common(1)[0][0]")
# bai2_combo execs bai2_layered from disk: point it at the patched text instead
SRC = SRC.replace('SRC_B = io.open(HERE/"bai2_layered.py", encoding="utf-8").read()', "SRC_B = BL")
CSRC = SRC
exec(CSRC[:CSRC.index("rows = defaultdict(dict)")])
exec(CSRC[CSRC.index("def report(nm, fin):"):CSRC.index("m0 = prf(")])

docs_all = sorted({x["doc"] for x in IVA})
start = {docid: to_doc_labels(docid, {x["key"]: x["n1"] for x in BYDOC[docid]}) for docid in docs_all}
VARIANTS = [("pipeline (moi tang + GRAPH, lien tang, cong thich ung, theo nhom)", LAYB, True, {}),
            ("khong tang GRAPH", OBS, True, {}),
            ("khong luat lien tang", LAYB, False, {}),
            ("cong lift >= 2", LAYB, True, {"GATE_LIFT2": 1}),
            ("mot nhom cho moi loai canh (khong theo nhan hien tai)", LAYB, True, {"ONE_PART": 1})]
print("=" * 130); print("ABLATION AUDITOR (buoc 3.1 mot minh, chon theo macro-F1, cross-fit tren valid)"); print("=" * 130)
for name, layers, cross, flags in VARIANTS:
    for k_ in ("GATE_LIFT2", "ONE_PART"): globals()[k_] = flags.get(k_, 0)
    fin = {}
    for k in (0, 1):
        trn = [d for d in docs_all if H("cf" + d) % 2 != k]; tst = [d for d in docs_all if H("cf" + d) % 2 == k]
        part = lambda d: H("in3" + d) % 3
        mine = [x for d in trn if part(d) == 0 for x in BYDOC[d]]
        conf = [x for d in trn if part(d) == 1 for x in BYDOC[d]]
        tune_x = [x for d in trn if part(d) == 2 for x in BYDOC[d]]
        test = [x for d in tst for x in BYDOC[d]]
        AR = audit_rules(mine, conf, "n1", layers, cross); idx = rule_index(AR)
        activate(tune_x + test, AR, "n1", layers)
        TH = tune(idx, tune_x, "n1", "macro")
        b_test = classify_k(idx, TH, test, "n1")
        bs = {x["key"]: v for x, v in zip(test, b_test)}
        for d in tst: fin[d] = to_doc_labels(d, bs)
    rows = {name: fin}
    report(name, fin)
log("xong")
