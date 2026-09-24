#!/usr/bin/env bash
# Seed sweep: each seed salts the train split (DISCOVERY / CONF-1 / CONF-2), the valid cross-fit
# folds, and PYTHONHASHSEED. Valid itself never changes. Seed 0 = the existing runs (no SEED).
#   new pipeline: full-train EV-EV rules  -> layered (TAG=_full_sK) -> bai2_combo
#   old pipeline: 257 + 719 EV-EV rules   -> layered (TAG=_sK, first 400 docs excluded) -> bai2_combo
# Steps run SEQUENTIALLY (a layered or combo process needs about 5 GB of RAM) and are skipped when
# their log already ends with "xong". Usage: bash run_seeds.sh 1 2 3 4
set -u
ROOT=/c/Reseach_Quang/tempekg
LOG=$ROOT/experiments/seeds/logs; mkdir -p "$LOG"
ART=$ROOT/src/artifacts
cd "$ROOT/src"
export PYTHONIOENCODING=utf-8
done_log() { [ -f "$1" ] && tail -2 "$1" | grep -q "xong"; }
step() {   # step <log> <command...>
  local log=$1; shift
  if done_log "$log"; then echo "   (bo qua, da co) $(basename "$log")"; return 0; fi
  "$@" > "$log" 2>&1 || { echo "   FAILED $(basename "$log")"; return 1; }
}
for s in "$@"; do
  export SEED=$s PYTHONHASHSEED=$s
  echo "[$(date +%H:%M:%S)] seed $s"
  if [ ! -f "$ART/pred_all_edges_s$s.json" ]; then
    step "$LOG/s${s}_bai1.log" python ../experiments/higher_order/bai1_all_edges.py || continue
  fi
  step "$LOG/s${s}_mine.log" env NW=4 python ../experiments/rules_full/mine_full.py || continue
  if [ ! -f "$ART/pred_all_edges_full_s$s.json" ]; then
    step "$LOG/s${s}_export.log" env NW=4 python ../experiments/rules_full/export_full.py || continue
  fi
  step "$LOG/s${s}_new_layered.log" env TAG=_full_s$s python ../experiments/higher_order/layered_rules.py || continue
  step "$LOG/s${s}_new_combo.log"   env TAG=_full_s$s python ../experiments/higher_order/bai2_combo.py
  step "$LOG/s${s}_old_layered.log" env TAG=_s$s EXCL400=1 python ../experiments/higher_order/layered_rules.py || continue
  step "$LOG/s${s}_old_combo.log"   env TAG=_s$s EXCL400=1 python ../experiments/higher_order/bai2_combo.py
  echo "[$(date +%H:%M:%S)] seed $s: xong"
done
echo "[$(date +%H:%M:%S)] tat ca seed xong"
