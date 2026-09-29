# Benchmark Audit: skill-creator (iteration-1)

**Synthetic**: yes - all records are artificial fixtures, not real measurements.
**Source**: `inputs/iteration-1/` (read-only). **Generated**: 2026-09-29T10:30:47Z

## Configuration status

| Config | Attempted | Completed | Errors | Incomplete | Valid scored runs | Coverage |
|--------|-----------|-----------|--------|------------|-------------------|----------|
| with_skill | 2 | 2 | 0 | 0 | 2 | 100% |
| without_skill | 2 | 1 | 1 | 1 | 1 | 50% |

Errors and incomplete overlap: the eval-b `without_skill` run is both errored
(returncode 1, status=error) and incomplete (no `grading.json`).

## Per-run status

| Eval | Config | Run | Status | Returncode | Completed | Errored | Incomplete | Pass rate | Time | Tokens |
|------|--------|-----|--------|-----------|-----------|---------|------------|-----------|------|--------|
| a | with_skill | 1 | completed | 0 | yes | no | no | 1.00 | 10.0s | — |
| a | without_skill | 1 | completed | 0 | yes | no | no | 0.00 | 8.0s | — |
| b | with_skill | 1 | completed | 0 | yes | no | no | 1.00 | 12.0s | — |
| b | without_skill | 1 | error | 1 | no | yes | yes | — | 5.0s | — |

## Valid metric samples

| Metric | with_skill | without_skill |
|--------|-----------|---------------|
| pass_rate | 2 | 1 |
| time_seconds | 2 | 1 |
| tokens | 0 (not supplied) | 0 (not supplied) |
| tool_calls | 0 (not supplied) | 0 (not supplied) |

Tokens/cost are **not zero** - the fixture supplies no token measurements.

## Pairing (by eval_id + run_number)

Valid pairs: **1 / 2** (coverage 50%)

| Eval | Run | Valid pair | with_skill | without_skill | pass_rate delta | Note |
|------|-----|------------|-----------|---------------|-----------------|------|
| a | 1 | yes | 1.00 | 0.00 | 1.00 |  |
| b | 1 | no | — | — | — | without_skill run is error (returncode=1), no valid grading; missing score is not a zero score |

## Evidence-supported deltas

| Metric | Delta | Available | Basis |
|--------|-------|-----------|-------|
| pass_rate | 1.0 | True | completed runs only: with_skill n=2 vs without_skill n=1; baseline covers eval-a only, eval-b baseline errored |
| time_seconds | 3.0 | True | completed runs only (errored eval-b timing excluded) |
| tokens | — | False | token_measurements = 'not supplied'; no run record carries total_tokens. Missing cost is not zero. |
| tool_calls | — | False | metrics.json records no total_tool_calls. |

## Conclusion

Cannot infer an overall skill gain from these records:
Records are synthetic fixtures, not real measurements. Only eval-a has valid scores on both arms (1 valid pair of 2 possible). The eval-b without_skill run errored (returncode 1, status=error) and produced no grading.json, so its score is missing, not 0; with 1 run per configuration and 50% pairing coverage the single +1.00 pass-rate difference is consistent with a benefit but insufficient to infer an overall skill gain.
