"""Benchmark coverage and pairing must not manufacture evidence from missing runs."""

import importlib.util
import json

import pytest

from conftest import ARTIFACT, run_script


_SPEC = importlib.util.spec_from_file_location("benchmark_integrity", ARTIFACT / "scripts" / "skill_benchmark.py")
benchmark = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(benchmark)


def write_run(root, config, *, scenario="a", run=1, passed=1, metrics=None, timing=None):
    directory = root / f"eval-{scenario}" / config / f"run-{run}"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "grading.json").write_text(json.dumps({
        "summary": {"passed": passed, "failed": 1 - passed, "total": 1, "pass_rate": passed},
        "expectations": [{"text": "correct output", "passed": bool(passed), "evidence": "checked output"}],
    }), encoding="utf-8")
    for name, data in (("metrics", metrics), ("timing", timing)):
        if data is not None:
            (directory / f"{name}.json").write_text(json.dumps(data), encoding="utf-8")
    return directory


@pytest.mark.parametrize("scenario,run", [("b", 1), ("a", 2)])
def test_disjoint_scenarios_or_repetitions_have_no_gain(tmp_path, scenario, run):
    write_run(tmp_path, "with_skill")
    write_run(tmp_path, "without_skill", scenario=scenario, run=run, passed=0)
    report = benchmark.generate_benchmark(tmp_path)
    delta = report["run_summary"]["delta"]
    assert delta["pass_rate"] is None
    assert delta["expected_pairs"] == 2 and delta["paired_samples"] == 0
    assert delta["coverage"] == 0


@pytest.mark.parametrize("artifact,contents,status", [
    ("grading.json", None, "incomplete"),
    ("grading.json", "{", "incomplete"),
    ("metrics.json", "[]", "incomplete"),
    ("metrics.json", '{"returncode": 1}', "error"),
    ("metrics.json", '{"timed_out": true, "returncode": 0}', "error"),
])
def test_missing_invalid_or_failed_attempt_remains_visible(tmp_path, artifact, contents, status):
    write_run(tmp_path, "with_skill", passed=1)
    bad = write_run(tmp_path, "without_skill", passed=0)
    target = bad / artifact
    if contents is None:
        target.unlink()
    else:
        target.write_text(contents, encoding="utf-8")
    report = benchmark.generate_benchmark(tmp_path)
    assert len(report["runs"]) == 2
    record = next(r for r in report["runs"] if r["configuration"] == "without_skill")
    assert record["status"] == status and record["issues"]
    summary = report["run_summary"]["without_skill"]
    assert summary["attempted"] == 1 and summary["completed"] == 0 and summary["coverage"] == 0
    assert summary["pass_rate"]["mean"] is None and summary["pass_rate"]["n"] == 0
    assert report["run_summary"]["delta"]["pass_rate"] is None


def test_partial_pair_coverage_does_not_hide_failed_or_missing_pair(tmp_path):
    write_run(tmp_path, "with_skill")
    write_run(tmp_path, "without_skill", passed=0)
    write_run(tmp_path, "with_skill", scenario="b")
    report = benchmark.generate_benchmark(tmp_path)
    delta = report["run_summary"]["delta"]
    assert delta["paired_samples"] == 1 and delta["coverage"] == 0.5
    assert delta["pass_rate"] is None


def test_zero_is_measured_and_unknown_cost_is_null(tmp_path):
    write_run(tmp_path, "with_skill", metrics={"total_tokens": 0}, timing={"total_duration_seconds": 0})
    write_run(tmp_path, "without_skill", passed=0)
    report = benchmark.generate_benchmark(tmp_path)
    stats = report["run_summary"]
    assert stats["with_skill"]["tokens"]["mean"] == 0 and stats["with_skill"]["tokens"]["n"] == 1
    assert stats["without_skill"]["tokens"]["mean"] is None and stats["without_skill"]["tokens"]["n"] == 0
    assert stats["without_skill"]["time_seconds"]["mean"] is None
    assert stats["delta"]["pass_rate"] == "+1.00"
    assert stats["delta"]["tokens"] is None and stats["delta"]["time_seconds"] is None
    assert "N/A (n=0)" in benchmark.generate_markdown(report)
    assert report["metadata"]["executor_model"] is None
    assert run_script("scripts/skill_benchmark.py", str(tmp_path), "--strict").returncode == 0


def test_complete_pair_retains_identity_sources_and_valid_delta(tmp_path):
    for config, passed, tokens, seconds in (("with_skill", 1, 100, 3), ("without_skill", 0, 80, 2)):
        write_run(tmp_path, config, passed=passed,
                  metrics={"client": "claude", "model": "test-model", "total_tokens": tokens, "returncode": 0},
                  timing={"total_duration_seconds": seconds})
    report = benchmark.generate_benchmark(tmp_path)
    delta = report["run_summary"]["delta"]
    assert (delta["pass_rate"], delta["tokens"], delta["time_seconds"]) == ("+1.00", "+20", "+1.0")
    assert delta["coverage"] == 1 and delta["metric_pairs"]["tokens"] == 1
    assert report["metadata"]["executor_model"] == "test-model"
    assert report["metadata"]["clients"] == ["claude"]
    assert report["runs"][0]["measurement_sources"]["tokens"] == "metrics.json.total_tokens"
    assert run_script("scripts/skill_benchmark.py", str(tmp_path), "--strict").returncode == 0


def test_mixed_models_preserved_and_mismatched_pair_not_compared(tmp_path):
    write_run(tmp_path, "with_skill", metrics={"model": "a", "client": "claude"})
    write_run(tmp_path, "without_skill", metrics={"model": "b", "client": "claude"})
    report = benchmark.generate_benchmark(tmp_path)
    assert report["metadata"]["executor_model"] is None
    assert report["metadata"]["executor_models"] == ["a", "b"]
    assert report["run_summary"]["delta"]["pass_rate"] is None
    assert report["run_summary"]["delta"]["identity_mismatches"][0]["fields"] == ["models"]


@pytest.mark.parametrize("summary", [
    {"passed": 2, "failed": 0, "total": 1, "pass_rate": 1},
    {"passed": 1, "failed": 0, "total": 1, "pass_rate": 0},
    {"passed": True, "failed": 0, "total": 1, "pass_rate": 1},
    {"passed": 1, "failed": 0, "total": 1, "pass_rate": float("nan")},
    {"passed": 0, "failed": 1, "total": 1, "pass_rate": 0},  # disagrees with the expectation
])
def test_invalid_grading_not_aggregated_as_success(tmp_path, summary):
    directory = write_run(tmp_path, "with_skill")
    path = directory / "grading.json"
    grading = json.loads(path.read_text(encoding="utf-8"))
    grading["summary"] = summary
    path.write_text(json.dumps(grading), encoding="utf-8")
    report = benchmark.generate_benchmark(tmp_path)
    assert report["runs"][0]["status"] == "incomplete"
    assert report["run_summary"]["with_skill"]["pass_rate"]["mean"] is None
    json.dumps(report, allow_nan=False)


def test_duplicate_eval_ids_are_ambiguous_not_double_counted_pairs(tmp_path):
    for scenario in ("a", "b"):
        for config in ("with_skill", "without_skill"):
            write_run(tmp_path, config, scenario=scenario)
        (tmp_path / f"eval-{scenario}" / "eval_metadata.json").write_text('{"eval_id": 1}', encoding="utf-8")
    delta = benchmark.generate_benchmark(tmp_path)["run_summary"]["delta"]
    assert delta["pass_rate"] is None and len(delta["duplicate_keys"]) == 1


def test_strict_retains_report_before_failure_and_default_remains_reporting(tmp_path):
    write_run(tmp_path, "with_skill")
    normal = run_script("scripts/skill_benchmark.py", str(tmp_path))
    strict = run_script("scripts/skill_benchmark.py", str(tmp_path), "--strict")
    assert normal.returncode == 0 and strict.returncode == 1
    assert (tmp_path / "benchmark.json").is_file() and (tmp_path / "benchmark.md").is_file()


def test_failed_execution_cannot_be_overridden_by_grader_and_cost_is_visible(tmp_path):
    directory = write_run(tmp_path, "with_skill", metrics={"returncode": 5, "total_tokens": 12})
    grading_path = directory / "grading.json"
    grading = json.loads(grading_path.read_text(encoding="utf-8"))
    grading["execution_metrics"] = {"returncode": 0, "total_tokens": 999}
    grading_path.write_text(json.dumps(grading), encoding="utf-8")
    report = benchmark.generate_benchmark(tmp_path)
    assert report["runs"][0]["status"] == "error"
    assert report["run_summary"]["with_skill"]["pass_rate"]["mean"] is None
    assert report["run_summary"]["with_skill"]["tokens"]["mean"] == 12


def test_zero_source_value_not_overwritten_by_grader_fallback(tmp_path):
    directory = write_run(tmp_path, "with_skill", metrics={"total_tokens": 0},
                          timing={"total_duration_seconds": 0})
    path = directory / "grading.json"
    grading = json.loads(path.read_text(encoding="utf-8"))
    grading["execution_metrics"] = {"total_tokens": 999}
    grading["timing"] = {"total_duration_seconds": 10}
    path.write_text(json.dumps(grading), encoding="utf-8")
    result = benchmark.generate_benchmark(tmp_path)["runs"][0]["result"]
    assert result["tokens"] == 0 and result["time_seconds"] == 0


def test_large_finite_cost_values_remain_serializable(tmp_path):
    for run in (1, 2):
        write_run(tmp_path, "with_skill", run=run, metrics={"total_tokens": 1e308})
    report = benchmark.generate_benchmark(tmp_path)
    assert report["run_summary"]["with_skill"]["tokens"]["mean"] == 1e308
    json.dumps(report, allow_nan=False)


def test_observed_model_set_and_metric_provenance_survive_aggregation(tmp_path):
    for config in ("with_skill", "without_skill"):
        write_run(tmp_path, config, metrics={"models": ["a", "b"], "model": "requested-a",
                  "model_source": "client_stream", "requested_model": "requested-a",
                  "total_tokens": 12, "tokens_source": "claude_result_usage"})
    report = benchmark.generate_benchmark(tmp_path)
    assert report["metadata"]["executor_model"] is None
    assert report["metadata"]["executor_models"] == ["a", "b"]
    assert report["metadata"]["unknown_model_runs"] == 0
    record = report["runs"][0]
    assert record["model"] is None and record["models"] == ["a", "b"]
    assert record["requested_model"] == "requested-a" and record["model_source"] == "client_stream"
    assert record["tokens_source"] == "claude_result_usage"
