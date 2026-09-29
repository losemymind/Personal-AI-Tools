# Skill Benchmark: synthetic-fixture (not a real skill)

**Model**: synthetic-fixture-model; observed: synthetic-fixture-model
**Clients**: synthetic-client
**Unknown model/client runs**: 0 / 0
**Date**: 2026-09-29T10:23:52Z
**Evals**: a, b (up to 2 runs per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 100% ± 0% (n=2) | 0% ± 0% (n=1) | N/A |
| Time | 11.0s ± 1.4s (n=2) | 6.5s ± 2.1s (n=2) | N/A |
| Tokens | N/A (n=0) | N/A (n=0) | N/A |

## Coverage

| Configuration | Attempted | Completed | Errors | Incomplete | Coverage |
|---|---:|---:|---:|---:|---:|
| with_skill | 2 | 2 | 0 | 0 | 100% |
| without_skill | 2 | 1 | 1 | 0 | 50% |

Paired runs: 1/2; coverage 50%.
Pass rate uses completed runs; observed cost includes failed attempts. Pairing covers discovered run directories, not an external planned test manifest.

> delta unavailable: every observed eval_id + run_number needs one completed run per configuration with no known model/client mismatch

## Notes

- All runs, grades, timings, and model/client names are synthetic fixtures (inputs/README.md, inputs/fixture_metadata.json); they are not real measurements or executed client telemetry.
- eval-b/without_skill run-1 failed (metrics.json: status=error, returncode=1) and produced no grading.json; it is counted as an error attempt, not skipped and not as a zero score.
- Token measurements were not supplied anywhere; token statistics are unavailable (n=0), not zero.
- Only 1 of 2 observed eval_id+run_number pairs (eval-a) has a completed run in both configurations, so pass-rate/time/token deltas are unavailable.
