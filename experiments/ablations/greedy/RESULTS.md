# Greedy forward selection: a rule-SELECTION ablation

Distinct from `../lcb/`, which varies the *statistic* that scores a rule. This varies
the *selection strategy*: instead of ranking by any statistic, add whichever rule raises
dev-inner macro-F1 most, until none does.

It answers a specific hypothesis: if five scoring statistics all lose to c70, perhaps
rule selection is not a scoring problem at all but a downstream decision problem,
`max F_macro(classifier(R))` subject to a size budget. This tests that directly.

**Not used by the default pipeline.** The frozen configuration is
`rules/final/rules_rx_c70.json`.

## Result

| Rule set | #rules | dev | conf | valid | dev - valid |
|---|---|---|---|---|---|
| rules_greedy | 23 | **27,16%** | 26,00% | 25,40% | **1,77** |
| rules_rx_c70 | 257 | 25,75% | **26,56%** | **25,60%** | **0,15** |
| rules_relaxed | 861 | 25,32% | 25,81% | 25,14% | 0,19 |

Greedy scores highest on the split it optimised and lowest of the three on valid.
The degradation appears on CONFIRMATION -- 126 documents greedy never saw -- before
valid is opened at all, so this is not "valid happens to be harder":

```
greedy   dev 27,16%  ->  conf 26,00%   (-1,16)
c70      dev 25,75%  ->  conf 26,56%   (+0,81)
```

Stated precisely: **greedy exhibited substantially larger selection-to-confirmation
degradation, consistent with overfitting to the small DEV-INNER selection set** (77
documents, 18.389 pairs, against a pool of 861 candidates and 23 rounds of choice).
This is an observed generalization gap, not a proof of the mechanism.

## The marginal-utility curve does NOT show a concentrated core

Replaying greedy's own ordering, prefix by prefix, on all three splits:

| k | dev | conf | valid | d(valid) |
|---|---|---|---|---|
| 1 | 19,18% | 18,74% | 19,40% | |
| 5 | 20,82% | 20,62% | 21,21% | +1,22 |
| 7 | 21,32% | 21,32% | 21,64% | +0,06 |
| 10 | 22,65% | 21,44% | 22,13% | +0,35 |
| 15 | 22,88% | 21,57% | 22,16% | -0,02 |
| 19 | 23,04% | 21,83% | 22,23% | +0,01 |
| **20** | 24,98% | 23,52% | 23,47% | **+1,24** |
| 21 | 25,45% | 25,29% | 24,03% | +0,56 |
| **23** | 27,16% | 26,00% | 25,40% | **+1,26** |

This **refutes** the long-tail reading that the dev trace alone suggested. On dev the
first 7 rules reach 21,32 of an eventual 27,16 and the middle looks like diminishing
returns -- but the two largest valid gains are the **20th** (+1,24) and the **23rd**
(+1,26) rules, and rules 13-19 contribute essentially nothing on valid (+0,01 each).

So utility is not concentrated in a small prefix. It is concentrated in a few rules
scattered through the ordering, and greedy's ordering is not the order of transferable
value -- it is the order of dev-inner gain. Truncating this set at k=7 or k=10 would
discard the two rules that matter most.

## What this ablation supports

> Direct downstream optimisation of the selection set does not produce better
> generalization than a simpler evidence-based policy, when the selection split is
> small relative to the candidate space.

A secondary observation worth keeping: 23 rules reach 25,40% on valid, 0,20 below the
257-rule set and **0,79 above** the 4.380-rule set this line of work started from. A
rule library small enough to print in a paper is not far off the operating set --
but the curve above shows you cannot find that small set by truncating greedy.

## Files

- `rules_greedy.json` -- the 23 rules, in the order greedy added them
  (CONTAINS 19, SIMULTANEOUS 2, OVERLAP 2)
- `trace.json` -- dev macro-F1, accuracy and per-label F1 after each addition

Greedy picked SIMULTANEOUS 2nd and OVERLAP 5th and 6th: optimising macro-F1 directly
reaches for the rare labels early, since each counts for a sixth of the objective.
