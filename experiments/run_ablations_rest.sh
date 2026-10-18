#!/bin/bash
export PYTHONIOENCODING=utf-8
cd /c/Reseach_Quang/tempekg/experiments/rules_full
for a in NOCONF LOWN GLOBAL; do
  d=abl_$(echo $a | tr A-Z a-z)
  mkdir -p $d
  for f in cache_ee.pkl cache_sp0.pkl cache_sp1.pkl cache_sp2.pkl cache_sp3.pkl; do [ -f $d/$f ] || cp $f $d/$f; done
  env NW=3 FIRE_TOP=1 MF_OUT=$d ABL_$a=1 REMINE=1 python mine_full.py > $d.log 2>&1
  rm -f $d/cache_*.pkl
done
cd /c/Reseach_Quang/tempekg/src
env TAG=_full SKIP_CLS=0,1,2 python ../experiments/higher_order/ablate_tri.py cls inj > ../experiments/logs/ablate_tri.log 2>&1
env TAG=_full python ../experiments/higher_order/ablate_audit.py > ../experiments/logs/ablate_audit.log 2>&1
echo ALLDONE > /c/Reseach_Quang/tempekg/experiments/run_ablations_rest.done
cd /c/Reseach_Quang/tempekg/experiments/rules_full
d=abl_nodl; mkdir -p $d
for f in cache_ee.pkl cache_sp0.pkl cache_sp1.pkl cache_sp2.pkl cache_sp3.pkl; do [ -f $d/$f ] || cp $f $d/$f; done
env NW=3 FIRE_TOP=1 MF_OUT=$d ABL_NODL=1 REMINE=1 python mine_full.py > $d.log 2>&1
rm -f $d/cache_*.pkl
echo ALLDONE2 > /c/Reseach_Quang/tempekg/experiments/run_ablations_rest.done2
