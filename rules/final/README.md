# Final rule library

`rules_rx_c70.json` -- 257 rules, the set the pipeline uses.

| | Value |
|---|---|
| Rules | 257 (CONTAINS 254, SIMULTANEOUS 2, OVERLAP 1) |
| Combiner | `max-norm`, tau=5 |
| Dev-inner macro-F1 | 25,75% |
| **Valid macro-F1** | **25,60%** |
| Valid accuracy | 87,87% |
| Valid macro-F1 (4 labels >=100 instances) | 38,40% |
| Non-BEFORE F1 | 37,12% |

## How it was selected

Train documents split three ways by hash, never by pair:

```
DISCOVERY     197 docs   proposes rules; its labels decide which rules exist
CONFIRMATION  126 docs   re-estimates each rule on labels that took no part in selection
DEV-INNER      77 docs   picks the combiner and threshold
VALID         705 docs   opened once, on the frozen configuration
```

Gates applied on train-inner: `n >= 25`, `dlogit >= 0,5` vs the best single-condition
parent, `q < 0,05` (Benjamini-Hochberg over 200 document-block permutations), and
`docs >= 5`. That leaves 861. Ranking those by confirmation Wilson bound **within each
relation** and keeping the top 30% gives these 257.

Ranking within each relation rather than across all of them is what keeps the rare
labels alive: SIMULTANEOUS tops out at Wilson 0,141 and OVERLAP at 0,125, so any
absolute threshold that CONTAINS can pass erases both.

## Per-label performance on valid

| Label | n_gold | n_pred | TP | P | R | F1 |
|---|---|---|---|---|---|---|
| BEFORE | 98.866 | 99.047 | 92.525 | 93,42% | 93,59% | 93,50% |
| CONTAINS | 9.391 | 9.787 | 3.894 | 39,79% | 41,47% | 40,61% |
| SIMULTANEOUS | 1.062 | 1.055 | 168 | 15,92% | 15,82% | 15,87% |
| OVERLAP | 570 | 40 | 11 | 27,50% | 1,93% | 3,61% |
| BEGINS-ON | 25 | 0 | 0 | 0% | 0% | 0% |
| ENDS-ON | 15 | 0 | 0 | 0% | 0% | 0% |

Accuracy is lower than the constant-BEFORE baseline's 89,94%, and that is the intended
trade: BEFORE is 89,94% of valid, so any system that tries to name the other five
labels loses accuracy. Macro-F1 rises 15,78% -> 25,60%.

## Alternatives that lost

See `experiments/ablations/lcb/RESULTS.md`. Four selection statistics with clearer
theoretical grounding -- parent delta-logit, conditional effect against a baseline
stratum, stability selection, and LCB-Lift -- all scored below this policy on dev-inner.
