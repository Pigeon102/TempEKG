#!/bin/bash
cd "$(dirname "$0")"
export PYTHONHASHSEED=0
export PYTHONIOENCODING=utf-8 NW=4
python ablate_score.py > ablate_score.log 2>&1
for a in NODOC NOBH NODL NOCONF LOWN GLOBAL; do
  d=abl_$(echo $a | tr A-Z a-z)
  mkdir -p $d
  for f in cache_ee.pkl cache_sp0.pkl cache_sp1.pkl cache_sp2.pkl cache_sp3.pkl; do [ -f $d/$f ] || cp $f $d/$f; done
  env MF_OUT=$d ABL_$a=1 REMINE=1 python mine_full.py > $d.log 2>&1
  rm -f $d/cache_*.pkl
done
echo ALLDONE > run_ablations_b1.done
