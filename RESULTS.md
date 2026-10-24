# Results

Reported batch: docker mode, non-sham runs. Local and sham runs are listed for completeness.

## H2-I

| Mode | Run | Baseline | Post | Predicted post | Outcome | Restored | Reported |
|------|-----|----------|------|----------------|---------|----------|----------|
| docker | 02 | (1, 1, 1, 1) | (0, 1, 1, 0) | (0, 1, 1, 0) | PASS | PASS | yes |
| docker | 03 | (1, 1, 1, 1) | (0, 1, 1, 0) | (0, 1, 1, 0) | PASS | PASS | yes |
| docker | 04 | (1, 1, 1, 1) | (0, 1, 1, 0) | (0, 1, 1, 0) | PASS | PASS | yes |
| docker | 05 | (1, 1, 1, 1) | (0, 1, 1, 0) | (0, 1, 1, 0) | PASS | PASS | yes |
| docker | 06 | (1, 1, 1, 1) | (0, 1, 1, 0) | (0, 1, 1, 0) | PASS | PASS | yes |
| docker-sham | 01 | (1, 1, 1, 1) | (1, 1, 1, 1) | (0, 1, 1, 0) | FAIL | PASS | no |
| docker-sham | 02 | (1, 1, 1, 1) | (1, 1, 1, 1) | (0, 1, 1, 0) | FAIL | PASS | no |

Reported batch for H2-I: PASS 5, FAIL 0, AMBIGUOUS 0.

## H2-X

| Mode | Run | Baseline | Post | Predicted post | Outcome | Restored | Reported |
|------|-----|----------|------|----------------|---------|----------|----------|
| docker | 01 | (1, 1, 1, 1) | (1, 0, 1, 0) | (1, 0, 1, 0) | PASS | PASS | yes |
| docker | 02 | (1, 1, 1, 1) | (1, 0, 1, 0) | (1, 0, 1, 0) | PASS | PASS | yes |
| docker | 03 | (1, 1, 1, 1) | (1, 0, 1, 0) | (1, 0, 1, 0) | PASS | PASS | yes |
| docker | 04 | (1, 1, 1, 1) | (1, 0, 1, 0) | (1, 0, 1, 0) | PASS | PASS | yes |
| docker | 05 | (1, 1, 1, 1) | (1, 0, 1, 0) | (1, 0, 1, 0) | PASS | PASS | yes |
| docker-sham | 01 | (1, 1, 1, 1) | (1, 1, 1, 1) | (1, 0, 1, 0) | FAIL | PASS | no |
| docker-sham | 02 | (1, 1, 1, 1) | (1, 1, 1, 1) | (1, 0, 1, 0) | FAIL | PASS | no |

Reported batch for H2-X: PASS 5, FAIL 0, AMBIGUOUS 0.

## H2-A

| Mode | Run | Baseline | Post | Predicted post | Outcome | Restored | Reported |
|------|-----|----------|------|----------------|---------|----------|----------|
| docker | 01 | (1, 1, 1, 1) | (1, 1, 0, 0) | (1, 1, 0, 0) | PASS | PASS | yes |
| docker | 02 | (1, 1, 1, 1) | (1, 1, 0, 0) | (1, 1, 0, 0) | PASS | PASS | yes |
| docker | 03 | (1, 1, 1, 1) | (1, 1, 0, 0) | (1, 1, 0, 0) | PASS | PASS | yes |
| docker | 04 | (1, 1, 1, 1) | (1, 1, 0, 0) | (1, 1, 0, 0) | PASS | PASS | yes |
| docker | 05 | (1, 1, 1, 1) | (1, 1, 0, 0) | (1, 1, 0, 0) | PASS | PASS | yes |
| docker-sham | 01 | (1, 1, 1, 1) | (1, 1, 1, 1) | (1, 1, 0, 0) | FAIL | PASS | no |
| docker-sham | 02 | (1, 1, 1, 1) | (1, 1, 1, 1) | (1, 1, 0, 0) | FAIL | PASS | no |

Reported batch for H2-A: PASS 5, FAIL 0, AMBIGUOUS 0.

## H2-P

| Mode | Run | Baseline | Post | Predicted post | Outcome | Restored | Reported |
|------|-----|----------|------|----------------|---------|----------|----------|
| docker | 01 | (1, 1, 1, 1) | (1, 1, 1, 0) | (1, 1, 1, 0) | PASS | PASS | yes |
| docker | 02 | (1, 1, 1, 1) | (1, 1, 1, 0) | (1, 1, 1, 0) | PASS | PASS | yes |
| docker | 03 | (1, 1, 1, 1) | (1, 1, 1, 0) | (1, 1, 1, 0) | PASS | PASS | yes |
| docker | 04 | (1, 1, 1, 1) | (1, 1, 1, 0) | (1, 1, 1, 0) | PASS | PASS | yes |
| docker | 05 | (1, 1, 1, 1) | (1, 1, 1, 0) | (1, 1, 1, 0) | PASS | PASS | yes |

Reported batch for H2-P: PASS 5, FAIL 0, AMBIGUOUS 0.

## H2-N

| Mode | Run | Baseline | Post | Predicted post | Outcome | Restored | Reported |
|------|-----|----------|------|----------------|---------|----------|----------|
| docker | 01 | (1, 1, 1, 1) | (1, 1, 1, 1) | (1, 1, 1, 1) | PASS | PASS | yes |
| docker | 02 | (1, 1, 1, 1) | (1, 1, 1, 1) | (1, 1, 1, 1) | PASS | PASS | yes |
| docker | 03 | (1, 1, 1, 1) | (1, 1, 1, 1) | (1, 1, 1, 1) | PASS | PASS | yes |
| docker | 04 | (1, 1, 1, 1) | (1, 1, 1, 1) | (1, 1, 1, 1) | PASS | PASS | yes |
| docker | 05 | (1, 1, 1, 1) | (1, 1, 1, 1) | (1, 1, 1, 1) | PASS | PASS | yes |

Reported batch for H2-N: PASS 5, FAIL 0, AMBIGUOUS 0.
