# Benchmark summary - iteration-1

> **SYNTHETIC FIXTURE.** Every run record, grade, duration and model name in `inputs/iteration-1` is artificial (see `inputs/README.md`, `inputs/fixture_metadata.json`). Nothing here is a real model call, real grading, or measured cost. This report only records what the fixtures contain and where the evidence stops.

## Design

- Evals: a, b
- Configurations: with_skill, without_skill
- Runs per eval/configuration: 1
- Expected run cells: 4

## Per-run status

| eval | config | run | attempted | status | rc | timed_out | grading | pass_rate | duration_s | incomplete |
|---|---|---|---|---|---|---|---|---|---|---|
| a | with_skill | 1 | yes | completed | 0 | no | yes | 1.0 | 10 | no |
| a | without_skill | 1 | yes | completed | 0 | no | yes | 0.0 | 8 | no |
| b | with_skill | 1 | yes | completed | 0 | no | yes | 1.0 | 12 | no |
| b | without_skill | 1 | yes | error | 1 | no | no | n/a | 5 | yes |

## Per-configuration counts

| config | attempted | completed | errors | incomplete | coverage | valid pass_rate samples | valid duration samples |
|---|---|---|---|---|---|---|---|
| with_skill | 2 | 2 | 0 | 0 | 1.0 | 2 | 2 |
| without_skill | 2 | 1 | 1 | 1 | 0.5 | 1 | 1 |
| **overall** | 4 | 3 | 1 | 1 | 0.75 | 3 | 3 |

`eval-b / without_skill / run-1` is the single gap: `status=error`, `returncode=1`, error "Synthetic execution failure; grading was not produced.", and no `grading.json`. Its 5s duration is recorded but is not a valid performance sample.

## Pairing by eval_id and run

| eval | run | both attempted | both completed | both graded | valid pair | reason |
|---|---|---|---|---|---|---|
| a | 1 | yes | yes | yes | yes | both arms completed with valid synthetic grading |
| b | 1 | yes | no | no | no | not a valid pair: without_skill grading; without_skill not completed (status=error, rc=1) |

Pairing: **1 / 2** valid pairs, paired coverage **0.5**. Valid paired pass_rate samples: **1**.

## Deltas

| eval | metric | with | without | delta | available | note |
|---|---|---|---|---|---|---|
| a | pass_rate | 1.0 | 0.0 | 1.0 | yes | synthetic fixture, n=1; not a real measurement or a statistically supported effect |
| a | duration_seconds | 10 | 8 | 2 | yes | synthetic, n=1; resource metric, not a skill-gain measure |
| b | pass_rate | - | - | n/a | no | without_skill arm is not a valid completed grading sample (status/error or missing grading) |
| b | duration_seconds | - | - | n/a | no | without_skill arm failed and its duration is not a valid performance sample |
| overall | pass_rate | - | - | n/a | no | only 1 of 2 planned pairs has valid grading in both arms; eval-b without_skill is an error with no grading, so pooling or averaging would silently drop a failed cell. An overall skill-gain delta is not supported by the records. |
| overall | tokens | - | - | n/a | no | token_measurements not supplied |
| overall | cost | - | - | n/a | no | cost not supplied; must not be recorded as zero |

The only computable performance difference is `eval-a` pass_rate (1.0 vs 0.0). It rests on a single synthetic pair (`n=1`) and carries no real evidentiary weight. The `eval-b` delta is **unavailable** because its `without_skill` arm failed without producing a grade. No overall skill-gain delta is supported.

## Evidence boundary

- Synthetic fixture: no claim about real model skill, latency or cost can be made.
- n=1 per cell, one iteration: no variance, no statistical test, no confidence interval.
- One of four cells errored and is missing grading; dropping it silently would bias the picture.
- Token and cost measurements were never supplied; they are not zero, they are unknown.
