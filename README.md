# TempEKG: Event-Centric Temporal Graph Repair for Temporal Relation Prediction

Code and logs behind every number in the paper *Event-Centric Temporal Graph Repair for Temporal Relation
Prediction* (MAVEN-ERE + MAVEN-Arg). The repository keeps only what produces the reported results.

- **Task 1** labels every ordered event/TIMEX pair with one of six temporal relations using mined rules
  (per-edge-kind rules, then cross-layer rules).
- **Task 2** repairs a labelled graph: a pattern-based **auditor** reads graph signatures around each edge, then
  **triangle repair** relabels each document with an energy over PMI-scored triangle configurations and a
  noise channel.

Everything is pure Python 3 (standard library only; developed with Python 3.13). A Vietnamese version of this
file, with more internal notes, is in [`README_vi.md`](README_vi.md); the design documents in `report/` are in
Vietnamese.

## Results and where they come from

Validation set: 710 documents, 188,924 temporal edges.

| Paper | Result | Log |
|---|---|---|
| Table 2 (Task 1) | macro-F1 30.09% (rules per edge kind) → 30.84% (with cross-layer rules) | `experiments/logs/layered_rules_full.log` |
| Table 3 (Task 2 on the Task 1 output) | macro-F1 30.84% → 31.89%, error rate 15.31% → 12.53% | `experiments/logs/bai2_combo_full_subset.log` |
| Table 4 (injected noise, EV→EV 5–20%) | error rate → 0.96 / 2.28 / 2.56 / 3.36% | `experiments/logs/fake_eval_subset.log` |
| Table 4 (injected noise, all edges 10 / 20%) | error rate 9.94 → 1.91%, 19.89 → 4.37% | `experiments/logs/inj_eval_subset.log` |
| Sec. 4.3 (triangle diagnostics) | 75.6% of Task 1 errors and 98.5% of injected errors lie in an unseen configuration | `experiments/logs/triangle_probe.log` |
| Fig. 2 caption (auditor on injected noise) | auditor → triangle raises the error from 2.44 to 3.53% (10%) and 4.11 to 6.75% (20%) | `experiments/logs/inj_audit.log` |
| Fig. 3 (worked example) | *United States occupation of Nicaragua*: auditor and triangle repair edge by edge | `experiments/logs/nic_example.log`, `experiments/logs/nic_audit.log` |
| Table 2 baselines | majority per edge kind 15.30%; logistic regression on the same layer atoms 33.11% | `experiments/logs/detection_breakdown.log`, `experiments/logs/lr_baseline.log` |
| Table 2 (single-layer vs full) | paired bootstrap over documents: −0.08 points, 95% CI [−0.23, 0.06], p = 0.25 | `experiments/logs/bootstrap_single_vs_full.log` |
| Table 3 baselines | prior + noise channel only changes no edge; repair of the logistic regression 33.11 → 34.31%, error 13.81 → 11.72% | `experiments/logs/repair_baselines_task1.log`, `experiments/logs/repair_baselines_lr.log`, `experiments/logs/bai2_combo_lr.log` |
| Table 3 detection | flagged = fixed + wrong→wrong + broken (Audit → triangle: 14,004 = 9,381 + 478 + 4,145) | `experiments/logs/detection_breakdown.log` |
| Table 5 (ablations) | Task 1 scoring, auditor and triangle repair, with per-label F1 | `experiments/rules_full/ablate_score.log`, `experiments/logs/ablate_audit.log`, `experiments/logs/ablate_tri_perlabel.log` |
| Algorithm 1 (sweeps) | repair converges in 9–10 sweeps; after sweep 4 only 0.2–0.5% of label changes remain | `experiments/logs/icm_convergence.log` |
| Task 2 learnt on training data only | full pipeline 30.84 → 31.59%, error 15.31 → 13.47% (not in the paper) | `experiments/logs/bai2_trainside.log` |

## Data (not in the repository)

| What | Where | How |
|---|---|---|
| MAVEN-ERE | `<parent>/MAVEN_ERE/{train,valid,test}.jsonl` | download from the MAVEN-ERE release |
| MAVEN-Arg | `<parent>/MAVEN-Arg.zip` | download from the MAVEN-Arg release |
| EV→EV perturbation files | `<parent>/fake_data/valid_r{05,10,15,20}.{jsonl,manifest.json}` | provided by the authors on request; only needed for the four EV→EV rows of Table 4 |

`<parent>` is the directory that contains this repository. Override with the environment variables
`MAVEN_ERE_DIR` and `FAKE_DATA_DIR`. Generated graphs, rules and predictions are written to `src/graph/` and
`src/artifacts/` (ignored by git).

## Reproducing the paper

Run every command from `src/` with `export PYTHONIOENCODING=utf-8`. Times were measured on a 12-core
(16-thread) workstation with 15.7 GB of memory.

| # | Command | Output | Time |
|---|---|---|---|
| 0 | `python build_kg.py --split train --ere-dir ../../MAVEN_ERE --arg-zip ../../MAVEN-Arg.zip`, then the same with `--split valid`; `python verify_kg.py --split valid` | `src/graph/` | ~12 s |
| 1 | `NW=4 python ../experiments/rules_full/mine_full.py` | EV→EV rules, `experiments/rules_full/mine_full.log` | ~6 min |
| 2 | `python ../experiments/higher_order/semantic_export.py`; `python ../experiments/higher_order/bai1_all_edges.py` | rules and predictions for the three TIMEX edge kinds | ~1 min |
| 3 | `NW=4 python ../experiments/rules_full/export_full.py` | `pred_all_edges_full.json` | ~3.5 min |
| 4 | `TAG=_full DUMP=1 python ../experiments/higher_order/layered_rules.py` | Task 1 predictions, **Table 2** | ~8 min (up to 18) |
| 5 | `TAG=_full MACRO_ONLY=1 DUMP_ROWS=1 python ../experiments/higher_order/bai2_combo.py` | **Table 3** | ~26 min |
| 6 | `TAG=_full python ../experiments/higher_order/inj_eval.py` | **Table 4**, all edges | ~29 min |
| 7 | `TAG=_full python ../experiments/higher_order/fake_eval.py` | **Table 4**, EV→EV (needs the perturbation files) | ~32 min |
| 8 | `python ../experiments/rules_full/compress.py`; `python ../experiments/rules_full/compress_timex.py`; `TAG=_full python ../experiments/rules_full/compress_layered.py`; `python ../experiments/rules_full/compact_listing.py` | the 713-rule cover (378 EV→EV), `report/RULES_COMPACT.md` | ~5 min |

Additional analyses quoted in the paper (run after steps 4–5):

| Command | Produces |
|---|---|
| `TAG=_full python ../experiments/higher_order/triangle_probe.py` | unseen-configuration and error-clustering diagnostics |
| `TAG=_full python ../experiments/higher_order/inj_audit.py 0.10 0.20` | auditor re-learnt on injected noise (~46 min) |
| `TAG=_full python ../experiments/higher_order/nic_example.py`; `python ../experiments/higher_order/nic_audit.py` | the Nicaragua worked example |
| `python ../experiments/rules_full/per_label_table.py` | per-label F1 by edge kind |
| `python ../experiments/rules_full/simul_base_rate.py` | SIMULTANEOUS base rates (0.9% → 5.4% in same-sentence pairs) |

Ablation scripts (`experiments/rules_full/run_ablations_b1.sh`, `experiments/run_ablations_rest.sh`) and their
logs are kept for reference.

## Determinism

Several steps iterate over Python sets, so their order depends on the hash seed. Every entry script therefore
re-executes itself with `PYTHONHASHSEED=0` if the variable is not already set. With this guard, two consecutive
runs are byte-identical, and every log behind Tables 2–4 was produced (or re-checked) under seed 0: the Task 1
predictions (981,319 pairs), the Task 2 outputs behind Table 3, and both injected-noise logs behind Table 4
are reproduced exactly. The ablation logs behind Table 5 (`experiments/rules_full/ablate_score.log`,
`experiments/logs/ablate_tri_perlabel.log`) were rerun under seed 0 and match the earlier logs; the other ablation
logs (`experiments/logs/ablate_audit.log`, `experiments/rules_full/abl_*.log`) were produced before the guard was
added and may differ by a few edges on a rerun. The Task 1 ablation in Table 5 is run with `PIPE_GRID=1`, the
pipeline's own threshold grid, so its first row equals Table 2 (26.99% for `EV→EV`); lift keeps a quantile grid since
its weights exceed 1. `ablate_score_finegrid.log` is the earlier run on a finer grid (fixed steps plus quantiles).
`experiments/logs/icm_convergence.log` was run on a rented server and copied from its terminal output (see its header).

On Windows, `src/graph` and `src/artifacts` may be directory junctions to a data folder outside the
repository; switching branches can replace a junction with a plain folder, so recreate it afterwards.

## Repository layout

```
src/                       graph construction (build_kg, verify_kg) and the condition / rule library
experiments/rules_full/    EV→EV rule mining on the full training set, rule compression, Task 1 analyses
experiments/higher_order/  TIMEX and cross-layer rules, auditor, triangle repair, injected noise, Task 2 analyses
experiments/begins_ends/   analysis of BEGINS-ON / ENDS-ON
experiments/seeds/         one redrawn training split
experiments/logs/          logs of every number in the paper
rules/final/               an earlier 257-rule set, only used to build pred_lex_d05.json in step 2
report/                    design documents (Vietnamese)
```

Parameter names differ between the code and the paper:

| Code | Paper |
|---|---|
| `beta` | λ (PMI smoothing) |
| `lambda` | β (triangle weight) |
| `alpha` | γ (prior damping) |
| "Bai 1" / "Bai 2" in logs | Task 1 / Task 2 |
