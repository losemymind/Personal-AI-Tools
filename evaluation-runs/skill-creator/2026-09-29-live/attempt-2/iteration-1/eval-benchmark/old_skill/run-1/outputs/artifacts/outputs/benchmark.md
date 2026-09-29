# Skill Benchmark: incomplete-benchmark-v1

**Synthetic fixture** — records are artificial, not real measurements.
**Generated**: 2026-09-29T10:24:23Z
**Configurations**: with_skill (primary) vs without_skill (baseline)

## Per-run status

| eval_id | config | run | status | returncode | grading | valid grade | pass_rate | time_s | tokens |
|---|---|---|---|---|---|---|---|---|---|
| a | with_skill | 1 | completed | 0 | yes | yes | 1.0 | 10.0 |  |
| a | without_skill | 1 | completed | 0 | yes | yes | 0.0 | 8.0 |  |
| b | with_skill | 1 | completed | 0 | yes | yes | 1.0 | 12.0 |  |
| b | without_skill | 1 | error | 1 | no | no |  | 5.0 |  |

Missing values are blank, never 0. Tokens were never supplied.

## Per-configuration accounting

| config | attempted | completed | errors | incomplete | graded (valid) | grade coverage |
|---|---|---|---|---|---|---|
| with_skill | 2 | 2 | 0 | 0 | 2 | 1.0 |
| without_skill | 2 | 1 | 1 | 0 | 1 | 0.5 |

## Valid metric samples

| metric | with_skill | without_skill |
|---|---|---|
| pass_rate | 2 | 1 |
| time_seconds | 2 | 2 |
| tokens | 0 | 0 |

## Pairing

- planned pairs: 2
- complete graded pairs: 1
- pair coverage: 0.5

| eval_id | run | with_skill grade | without_skill grade | paired |
|---|---|---|---|---|
| a | 1 | True | True | True |
| b | 1 | True | False | False |

## Deltas

**Evidence-supported (paired only)**:

- pass_rate: n_pairs=1, mean_delta=1.0
- time_seconds: n_pairs=1, mean_delta=2.0

**Not evidence-supported (unpaired aggregate, shown only as cross-check)**:

- pass_rate: primary_mean=1.0, baseline_mean=0.0, delta=1.0 — unbalanced sample counts and non-paired eval coverage; not a valid gain estimate
- time_seconds: primary_mean=11.0, baseline_mean=6.5, delta=4.5 — unbalanced sample counts and non-paired eval coverage; not a valid gain estimate
- tokens: primary_mean=None, baseline_mean=None, delta=None — token measurements not supplied by fixture; unavailable (not zero)

**delta_available = False**

> Overall skill gain cannot be computed: only 1/2 eval(s) form a complete graded pair; the baseline run for eval b errored and produced no grading; token measurements were not supplied.

## Conclusion

- synthetic: True
- comparable: False
- delta_available: False
- overall_skill_gain_inferable: False
- reason: Only 1 of 2 planned eval pairs has a valid grade on both sides: eval b's without_skill run failed (returncode 1, status=error) and produced no grading.json. Aggregated (unpaired) means compare 2 with_skill runs against 1 without_skill run and therefore cannot establish a gain. Token measurements were not supplied. The single complete pair (eval a) shows with_skill 1.0 vs without_skill 0.0 on a 1-assertion synthetic check, which is insufficient to infer an overall skill gain.

### Limitations

- All inputs are synthetic fixtures, not real model runs or measured telemetry.
- 1 of 2 planned baseline runs errored, so coverage is incomplete and the groups are unbalanced.
- Each eval has 1 assertion and 1 run; no variance estimate or statistical power.
- Token/cost measurements were not supplied; missing costs are unavailable, not zero.
- Aggregated means from unequal sample counts are not an evidence-supported delta.

### Tool cross-check

- Dropped the errored, ungraded eval-b/without_skill run instead of counting it as an attempt/error.
- Reported runs_per_configuration=2, masking that the baseline only had 1 graded run.
- Computed a +1.00 delta from 2 vs 1 unpaired runs, implying a gain not supported by the records.
- Reported tokens as 0.0 although token measurements were not supplied (missing cost treated as zero).
