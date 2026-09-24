# LCB-Lift ablation: failed alternatives to the c70 policy

These rule sets are **negative results**. They are kept so the comparison can be
reproduced, and they are **not used by the default pipeline**. The rule set the
pipeline loads is `rules/final/rules_rx_c70.json`.

## What was tested

`LCB-Lift` combines the two properties the earlier experiments each supplied
separately -- Wilson's treatment of sample size, and lift's normalisation by the
relation's own base rate:

```
LCB-Lift_r(P) = WilsonLB(P(r | P)) / P(r)
```

Read as: *even at the lower confidence bound, this rule is at least LCB-Lift times
more likely to carry relation r than the corpus base rate for r.* Unlike an absolute
`WLB >= 0.25` gate, one threshold means the same thing for CONTAINS (base rate 5,88%)
and for OVERLAP (0,469%).

Base rates are computed on DISCOVERY documents, never on valid.

## Results

Every threshold was chosen on DEV-INNER. VALID stayed untouched until one frozen
configuration was evaluated, which is why only the selected policy has a valid number.

| Policy | #rules | Dev macro-F1 | Valid macro-F1 | CONT | SIM | OVL | Purpose |
|---|---|---|---|---|---|---|---|
| **rx_c70** | **257** | **25,75%** | **25,60%** | 37,5% | 20,4% | 2,3% | **selected** |
| relaxed | 861 | 25,32% | - | 34,3% | 19,7% | 4,7% | earlier policy |
| lcb5c | 806 | 24,35% | - | 34,9% | 18,4% | 3,0% | failed alternative |
| lcb3k5 | 1.777 | 24,28% | - | 34,7% | 18,3% | 3,0% | failed alternative |
| lcb5k5 | 1.142 | 24,28% | - | 34,7% | 18,3% | 3,0% | failed alternative |
| lcb10c | 107 | 23,75% | - | 26,6% | 18,8% | 3,0% | failed alternative |
| lcb10k5 | 220 | 23,72% | - | 26,8% | 18,4% | 3,0% | failed alternative |

Naming: `lcb<lambda>k<k_min>` is the threshold pair; a trailing `c` adds the
confirmation requirement `cn >= 10`.

## What the numbers support, and what they do not

The claim these files support is narrow:

> In the TempEKG experimental setting, the LCB-Lift policies tested did not improve
> downstream temporal classification over c70.

They do **not** support "LCB-Lift is theoretically worse". A different candidate pool,
a different combiner, or a different corpus could reverse this.

Two observations are worth keeping:

**Statistical interpretability is not downstream utility.** `LCB-Lift >= 5` states
something precise about a rule; c70 ("keep the top 30% by confirmation evidence within
each relation") states almost nothing. The one without semantics scored higher.

**More rare-class rules did not mean better rare-class F1.** At lambda=10 the LCB-Lift
sets keep 14 SIMULTANEOUS and 9 OVERLAP rules against c70's 2 and 1, and still score
lower on both labels (SIM 18,4% vs 20,4%).

## Distribution of surviving rules

| lambda | k_min=1 | k_min=5 | k_min=10 |
|---|---|---|---|
| 1,5 | 2.339 (SIM 48, OVL 25) | 2.338 (SIM 47, OVL 25) | 2.236 (SIM 33, OVL 16) |
| 3 | 1.778 (SIM 32, OVL 11) | 1.777 (SIM 31, OVL 11) | 1.747 (SIM 18, OVL 2) |
| 5 | 1.143 (SIM 26, OVL 10) | 1.142 (SIM 25, OVL 10) | 1.120 (SIM 12, OVL 1) |
| 10 | 220 (SIM 14, OVL 9) | 220 (SIM 14, OVL 9) | 202 (SIM 5, OVL 0) |

`k_min` barely moves the count from 1 to 5 because the `n >= 25` support floor already
removes nearly every rule with fewer than 5 correct instances. It bites only at 10.

## BEGINS-ON and ENDS-ON

Neither label appears in any row above, at any threshold. On DISCOVERY (197 documents)
**no candidate for either label clears `n >= 25`** -- zero, not few. So the statement
is not "the gates are too strict for these labels" but "the corpus does not supply
enough support to form a single candidate". BEGINS-ON has 25 gold instances in valid's
109.929 pairs, ENDS-ON has 15.

## Reproducing

```bash
python src/vote.py --rules rules_lcb5c.json --tau-sweep    # from src/artifacts/
```

The scoring script is `scratchpad/devpick.py` in the session that produced these
(policy chosen on dev-inner, valid not opened).
