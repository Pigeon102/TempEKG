# Do the mined rules beat a plain classifier on the same KG features?

The reviewer question this answers: *is rule mining doing anything a softmax
regression on event types and roles would not?*

Four feature sets of growing richness, trained on TRAIN-INNER (discovery +
confirmation documents -- dev-inner and valid are never touched), evaluated on the
same valid split as the rule library.

## Result

| Feature set | #params | macro-F1 | acc | per-label F1 |
|---|---|---|---|---|
| A: event types only | 15.557 | 18,81% | 62,66% | BEFO 77 CONT 31 SIMU 2 OVER 2 |
| B: + position | 15.573 | 19,44% | 56,06% | BEFO 71 CONT 36 SIMU 7 OVER 3 |
| C: + roles | 17.823 | 16,48% | 47,26% | BEFO 63 CONT 28 SIMU 6 OVER 2 |
| D: all KG features | 18.076 | **20,07%** | 60,79% | BEFO 76 CONT 35 SIMU 6 OVER 4 |
| **E: 257 mined rules** | **257** | **25,60%** | **87,87%** | BEFO 94 CONT 41 SIMU 16 OVER 4 |

**The rules win by 5,53 macro-F1 points using 70x fewer parameters.** In the framing
the question came with, this is the `F1(E) > F1(D)` case: rule mining has a
justification beyond interpretability.

## Convergence was checked, because a weak baseline proves nothing

| Setting | macro-F1 |
|---|---|
| 3 epochs, lr 0,25 | 19,59% |
| **10 epochs, lr 0,25** | **20,07%** |
| 10 epochs, lr 0,05 | 19,83% |
| 20 epochs, lr 0,05 | 6,94% (diverged) |

Gains flatten by 10 epochs; the 20-epoch run diverged and is not a result. So 20,07%
is the honest ceiling for this model class, not an undertrained number.

## Caveats that limit how far this generalises

1. **One model class.** Softmax regression is linear in one-hot features. A gradient-
   boosted tree or an MLP could close part of the gap by modelling exactly the feature
   interactions that a depth-2 rule encodes explicitly. This experiment does not rule
   that out; it rules out the *simplest* alternative a reviewer would name.
2. **No numpy or sklearn in this environment**, so the model is hand-written SGD.
   Optimiser quality is a plausible part of the gap, which is why convergence was
   swept rather than assumed.
3. **The comparison is not parameter-matched.** 18.076 weights against 257 rules is a
   point in the rules' favour on compactness, but it also means the two systems have
   very different capacity, and neither was tuned for the other's regime.

## Why C (roles) scores *below* B

Adding role features drops macro-F1 from 19,44% to 16,48% and accuracy from 56,06% to
47,26%. Roles arrive as many sparse one-hot indicators; under class-balanced loss they
pull the linear model toward the rare labels faster than the signal supports. The
full set D recovers because the remaining features restore enough constraint. A rule
conjunction does not have this failure mode -- it fires only where both conditions
hold, so a weak role feature cannot drag the whole decision surface.

## Reproducing

```bash
python experiments/ablations/features/ablate.py
```

Class weights are `n / (6 * count(class))` so the loss targets macro-F1 rather than
accuracy -- the same objective the rule library is scored on.
