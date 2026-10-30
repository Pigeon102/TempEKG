#!/bin/bash
# Runs for the advisor's feedback (2026-10-28). From the repo root: bash experiments/run_feedback.sh
REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO/src"; export PYTHONIOENCODING=utf-8 TAG=_full PYTHONHASHSEED=0
L=../experiments/logs
DUMP=1 DUMP_SINGLE=1 python ../experiments/higher_order/layered_rules.py > $L/layered_rules_full_single.log 2>&1
python ../experiments/higher_order/lr_baseline.py > $L/lr_baseline.log 2>&1
python ../experiments/higher_order/repair_baselines.py > $L/repair_baselines_task1.log 2>&1
PL_FILE=pred_layered_lr.json python ../experiments/higher_order/repair_baselines.py > $L/repair_baselines_lr.log 2>&1
PL_FILE=pred_layered_lr.json MACRO_ONLY=1 python ../experiments/higher_order/bai2_combo.py > $L/bai2_combo_lr.log 2>&1
python ../experiments/higher_order/ablate_tri.py cls > $L/ablate_tri_perlabel.log 2>&1
python ../experiments/higher_order/detection_breakdown.py > $L/detection_breakdown.log 2>&1
python ../experiments/higher_order/bootstrap_single_vs_full.py > $L/bootstrap_single_vs_full.log 2>&1
python ../experiments/higher_order/bai2_trainside.py > $L/bai2_trainside.log 2>&1
python ../experiments/higher_order/icm_convergence.py > $L/icm_convergence.log 2>&1
python ../experiments/rules_full/ablate_score.py > ../experiments/rules_full/ablate_score.log 2>&1
echo ALLDONE
