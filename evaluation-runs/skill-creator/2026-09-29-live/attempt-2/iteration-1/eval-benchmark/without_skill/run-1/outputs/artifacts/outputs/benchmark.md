# Benchmark review - iteration-1 (synthetic fixtures)

Source: `inputs/iteration-1`. **All records are synthetic fixtures, not real model runs, telemetry, or costs.**
Tooling: the skill-provided `aggregate_benchmark.py` was located but could not be read/executed (sandbox `external_directory` deny); an equivalent Python 3.11 standard-library aggregator was used.

## Planned vs. observed

- Planned: 2 scenarios x 2 configurations x 1 run = 4 runs, 2 paired comparisons.
- Observed run directories: 4 (missing: none).

## Per-run status

| eval | config | run | exec status | returncode | error | grading | pass_rate | duration_s |
|---|---|---|---|---|---|---|---|---|
| a | with_skill | run-1 | completed | 0 |  | yes | 1.0 | 10 |
| a | without_skill | run-1 | completed | 0 |  | yes | 0.0 | 8 |
| b | with_skill | run-1 | completed | 0 |  | yes | 1.0 | 12 |
| b | without_skill | run-1 | error | 1 | Synthetic execution failure; grading was not produced. | MISSING | n/a (missing) | 5 |

## Per-configuration aggregates

| config | attempted | completed | errors | incomplete | coverage | valid metric samples | valid grading samples |
|---|---|---|---|---|---|---|---|
| with_skill | 2 | 2 | 0 | 0 | 1.0 | 2 | 2 |
| without_skill | 2 | 1 | 1 | 0 | 0.5 | 1 | 1 |

- Valid metric samples total: 3/4. Valid grading samples total: 3/4 (missing 1).

## Pairing (by eval_id and run)

| eval | run | with_skill | without_skill | paired | delta | delta available |
|---|---|---|---|---|---|---|
| a | run-1 | completed | completed | yes | 1.0 | yes |
| b | run-1 | completed | error | no |  | no |

- Paired: 1/2 (coverage 0.5).

## Deltas

- eval-a: delta = 1.0 (with_skill - without_skill); paired within synthetic fixture (n=1 per arm).
- eval-b: delta UNAVAILABLE (unpaired: missing without_skill score).
- Overall skill gain: UNAVAILABLE. Only 1 of 2 planned with_skill/without_skill pairs has a valid score, each arm has n=1, all records are synthetic, and one arm is missing entirely for eval-b. No overall skill-gain delta can be estimated.

## Measurements not supplied (NOT zero)

- Tokens: unavailable (not supplied).
- Cost: unavailable (not supplied); missing cost is not zero.
- Timing: synthetic durations only; descriptive, not measured wall time.

## Limitations

- All records are synthetic fixtures; no real model performance, telemetry, or cost.
- Each scenario/configuration has a single run (n=1); no variance or significance can be computed.
- eval-b/without_skill failed (status=error, returncode=1) and produced no grading; its score is missing, not zero.
- Only 1 of 2 planned eval pairs has valid scores (eval-a); pairing coverage is 0.5.
- No token or cost measurements are supplied; they are treated as unavailable, never zero.
- Overall skill-gain delta is therefore not estimable from these records.
