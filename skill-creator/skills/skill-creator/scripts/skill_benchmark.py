#!/usr/bin/env python3
"""Aggregate benchmark run results into summary statistics (benchmark.json + benchmark.md).

Port from Anthropic's official anthropics/skills skill-creator
(aggregate_benchmark.py), kept client-agnostic (pure stdlib).

Reads grading.json / timing.json / metrics.json from a workspace layout and produces:
  - <dir>/benchmark.json  — machine-readable summary with mean/stddev/min/max + delta
  - <dir>/benchmark.md    — human-readable table (pass rate / time / tokens)

Usage:
    python scripts/skill_benchmark.py <workspace>/iteration-N --skill-name <name> [--skill-path <path>] [--notes <notes.json>]

Layouts supported:
    <workspace>/iteration-N/
    └── eval-<name>/
        ├── with_skill/run-1/grading.json   (+ optional timing.json)
        └── without_skill/run-1/grading.json

--notes merges analyzer observations (a JSON array of strings produced by the
analyzer subagent, see agents/skill_analyzer.md mode 2) into benchmark.json's notes.
"""

import argparse
import json
import math
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def configure_utf8_output() -> None:
    if sys.platform != "win32":
        return
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if not stream:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass


def calculate_stats(values: list[float]) -> dict:
    # Drop non-numeric / non-finite entries so NaN/Infinity never reach the JSON
    # artifact (which the schema calls machine-readable).
    clean: list[float] = []
    for v in values:
        if isinstance(v, bool):
            continue
        try:
            f = float(v)
        except (TypeError, ValueError, OverflowError):
            continue
        if math.isfinite(f):
            clean.append(f)
    values = clean
    if not values:
        return {"n": 0, "mean": None, "stddev": None, "min": None, "max": None}
    n = len(values)
    mean = statistics.mean(values)
    stddev = statistics.stdev(values) if n > 1 else 0.0
    return {
        "n": n,
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def _as_float(value, default=None):
    """Coerce a possibly-string/None/odd/non-finite field to a finite float."""
    if isinstance(value, bool):
        return default
    try:
        x = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    # JSON accepts Infinity/NaN/1e400; rejecting them keeps benchmark.json valid
    # strict JSON and stops inf/nan propagating into stats and int conversion.
    return x if math.isfinite(x) else default


def _as_int(value, default=None):
    x = _as_float(value, default)
    if x is None or x != int(x):
        return default
    try:
        return int(x)
    except (OverflowError, ValueError):
        return default


def _coerce_eval_id(value, default):
    """Only hashed-safe, JSON-safe scalars may become an eval_id (feeds set/sort)."""
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else default
    if isinstance(value, (str, int)):
        return value
    return default


def _load_object(path: Path, issues: list[dict], required: bool = False) -> dict:
    if not path.exists():
        if required:
            issues.append({"code": "missing_artifact", "path": path.name})
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(data, dict):
            return data
    except (ValueError, OSError, UnicodeError):
        pass
    issues.append({"code": "invalid_artifact", "path": path.name})
    return {}


def _grading_result(grading: dict, issues: list[dict]) -> dict:
    summary = grading.get("summary")
    if not isinstance(summary, dict):
        issues.append({"code": "invalid_grading", "detail": "missing summary object"})
        summary = {}
    counts = {key: _as_int(summary.get(key)) for key in ("passed", "failed", "total")}
    passed, failed, total = (counts[key] for key in ("passed", "failed", "total"))
    valid_counts = (all(v is not None and v >= 0 for v in counts.values())
                    and total > 0 and passed + failed == total)
    rate = _as_float(summary.get("pass_rate"))
    if "pass_rate" not in summary and valid_counts:
        rate = passed / total
    valid_rate = (rate is not None and 0 <= rate <= 1
                  and valid_counts and abs(rate - passed / total) <= 0.0051)
    if not valid_counts or not valid_rate:
        issues.append({"code": "invalid_grading", "detail": "inconsistent counts or pass_rate"})
    expectations = grading.get("expectations", [])
    valid_expectations = isinstance(expectations, list) and all(
        isinstance(e, dict) and isinstance(e.get("passed"), bool)
        and isinstance(e.get("text"), str) and isinstance(e.get("evidence"), str)
        for e in expectations
    )
    if valid_expectations and expectations:
        valid_expectations = (len(expectations) == total
                              and sum(e["passed"] for e in expectations) == passed)
    if not valid_expectations:
        issues.append({"code": "invalid_grading", "detail": "expectations disagree with summary"})
    return {**counts, "pass_rate": rate if valid_rate and valid_expectations else None,
            "expectations": [{k: e[k] for k in ("text", "passed", "evidence")}
                             for e in expectations] if valid_expectations else []}


def _measurement(sources: list[tuple[str, dict, str]], name: str,
                 issues: list[dict], origins: dict, integer: bool = False):
    for origin, data, key in sources:
        if key not in data or data[key] is None:
            continue
        value = _as_int(data[key]) if integer else _as_float(data[key])
        if value is None or value < 0:
            issues.append({"code": "invalid_measurement", "detail": f"{origin}.{key}"})
            continue
        origins[name] = f"{origin}.{key}"
        return value
    origins[name] = None
    return None


def load_run_results(benchmark_dir: Path) -> dict[str, list[dict]]:
    search_dir = benchmark_dir / "runs"
    if not search_dir.is_dir():
        search_dir = benchmark_dir
    results: dict[str, list[dict]] = {}
    for eval_dir in sorted(search_dir.glob("eval-*")):
        if not eval_dir.is_dir():
            continue
        metadata_issues: list[dict] = []
        meta = _load_object(eval_dir / "eval_metadata.json", metadata_issues)
        eval_id = _coerce_eval_id(meta.get("eval_id"), eval_dir.name)
        for config_dir in sorted(eval_dir.iterdir()):
            if not config_dir.is_dir():
                continue
            run_dirs = [p for p in sorted(config_dir.glob("run-*")) if p.is_dir()]
            if not run_dirs:
                continue
            config_runs = results.setdefault(config_dir.name, [])
            for run_dir in run_dirs:
                issues = list(metadata_issues)
                grading = _load_object(run_dir / "grading.json", issues, required=True)
                result = _grading_result(grading, issues)
                run_suffix = run_dir.name.removeprefix("run-")
                run_number = int(run_suffix) if run_suffix.isdecimal() else run_suffix
                result.update(eval_id=eval_id, run_number=run_number,
                              run_path=run_dir.relative_to(benchmark_dir).as_posix())
                metrics = _load_object(run_dir / "metrics.json", issues)
                timing = _load_object(run_dir / "timing.json", issues)
                embedded_metrics = grading.get("execution_metrics", {})
                embedded_timing = grading.get("timing", {})
                for key, data in (("execution_metrics", embedded_metrics), ("timing", embedded_timing)):
                    if not isinstance(data, dict):
                        issues.append({"code": "invalid_artifact", "path": f"grading.json.{key}"})
                embedded_metrics = embedded_metrics if isinstance(embedded_metrics, dict) else {}
                embedded_timing = embedded_timing if isinstance(embedded_timing, dict) else {}
                origins: dict = {}
                # Deterministic run artifacts take precedence over a grader's copied values.
                metric_sources = [("metrics.json", metrics), ("timing.json", timing),
                                  ("grading.execution_metrics", embedded_metrics)]
                result["tokens"] = _measurement(
                    [(label, data, key) for label, data in metric_sources
                     for key in ("total_tokens", "tokens")], "tokens", issues, origins)
                result["tool_calls"] = _measurement(
                    [(label, data, "total_tool_calls") for label, data in metric_sources],
                    "tool_calls", issues, origins, integer=True)
                result["time_seconds"] = _measurement(
                    [("timing.json", timing, "total_duration_seconds"),
                     ("grading.timing", embedded_timing, "total_duration_seconds")],
                    "time_seconds", issues, origins)
                result["measurement_sources"] = origins
                for field in ("client", "model"):
                    value = metrics.get(field, embedded_metrics.get(field))
                    result[field] = value.strip() if isinstance(value, str) and value.strip() else None
                observed_models = metrics.get("models", embedded_metrics.get("models", []))
                observed_models = (sorted({v.strip() for v in observed_models
                                           if isinstance(v, str) and v.strip()})
                                   if isinstance(observed_models, list) else [])
                result["models"] = observed_models or ([result["model"]] if result["model"] else [])
                result["model"] = result["models"][0] if len(result["models"]) == 1 else None
                for field in ("model_source", "requested_model", "tokens_source", "tool_calls_source"):
                    value = metrics.get(field, embedded_metrics.get(field))
                    result[field] = value if isinstance(value, str) else None
                execution_errors = []
                for label, data in [("metrics.json", metrics), ("timing.json", timing),
                                    ("grading.execution_metrics", embedded_metrics),
                                    ("grading.timing", embedded_timing)]:
                    if "timed_out" in data and not isinstance(data["timed_out"], bool):
                        issues.append({"code": "invalid_execution_status", "path": label})
                    if data.get("timed_out") is True:
                        execution_errors.append({"code": "execution_timeout", "path": label})
                    if "returncode" in data:
                        rc = _as_int(data["returncode"])
                        if rc is None:
                            issues.append({"code": "invalid_execution_status", "path": label})
                        elif rc != 0:
                            execution_errors.append({"code": "execution_failed", "path": label,
                                                     "returncode": rc})
                    if data.get("status") in ("error", "failed", "timeout") or data.get("error"):
                        execution_errors.append({"code": "execution_failed", "path": label})
                recorded_rc = metrics.get("returncode", embedded_metrics.get("returncode"))
                result["execution_status"] = ("error" if execution_errors else
                    "completed" if _as_int(recorded_rc) == 0 else "unknown")
                result["status"] = "error" if execution_errors else "incomplete" if issues else "completed"
                result["issues"] = issues + execution_errors
                notes_summary = grading.get("user_notes_summary", {})
                result["notes"] = [note for key in ("uncertainties", "needs_review", "workarounds")
                                   for note in (notes_summary.get(key) if isinstance(notes_summary, dict)
                                                and isinstance(notes_summary.get(key), list) else [])
                                   if isinstance(note, str)]
                config_runs.append(result)
    return results


def _ordered_configs(results: dict, primary: str, baseline: str) -> list[str]:
    """Order config names as (primary, baseline, *rest) with graceful fallbacks.

    Delta direction must not depend on directory-name sort order: with two
    configs named `baseline`/`skill`, alphabetic order silently flips the sign of
    the reported gain. Prefer the configured roles, then any known aliases, then
    input order.
    """
    aliases = {
        "with_skill": ["with_skill", "skill", "treatment"],
        "without_skill": ["without_skill", "baseline", "control", "no_skill"],
    }
    names = list(results.keys())
    nameset = set(names)

    def _resolve(role: str) -> str | None:
        """Resolve a role to an actual config name (exact first, then aliases)."""
        if role in nameset:
            return role
        for alias in aliases.get(role, []):
            if alias in nameset:
                return alias
        return None

    ordered: list[str] = []
    # Resolve each role INDEPENDENTLY before ordering. Resolving them in one pass
    # let a baseline alias land in slot 0 when the primary was absent by exact
    # name (e.g. configs `skill`/`without_skill`: `without_skill` matched first,
    # becoming the "primary"), silently flipping the delta sign.
    for role in (primary, baseline):
        resolved = _resolve(role)
        if resolved and resolved not in ordered:
            ordered.append(resolved)
    for name in names:
        if name not in ordered:
            ordered.append(name)
    return ordered


def _resolve_role(results: dict, role: str) -> str | None:
    aliases = {"with_skill": ("skill", "treatment"),
               "without_skill": ("baseline", "control", "no_skill")}
    return next((name for name in (role, *aliases.get(role, ())) if name in results), None)


def aggregate_results(results: dict[str, list[dict]], primary: str = "with_skill",
                      baseline: str = "without_skill") -> dict:
    run_summary: dict = {}
    for config in _ordered_configs(results, primary, baseline):
        runs = results[config]
        completed = [r for r in runs if r.get("status") == "completed"]
        run_summary[config] = {
            "runs": len(runs), "attempted": len(runs), "completed": len(completed),
            "errors": sum(r.get("status") == "error" for r in runs),
            "incomplete": sum(r.get("status") == "incomplete" for r in runs),
            "coverage": len(completed) / len(runs) if runs else 0.0,
            "pass_rate": calculate_stats([r.get("pass_rate") for r in completed]),
            # Cost includes every observed attempt, including failed executions.
            "time_seconds": calculate_stats([r.get("time_seconds") for r in runs]),
            "tokens": calculate_stats([r.get("tokens") for r in runs]),
        }
    p_name, b_name = _resolve_role(results, primary), _resolve_role(results, baseline)
    def indexed(name):
        entries: dict[tuple, list] = {}
        for run in results.get(name, []):
            key = (json.dumps(run["eval_id"], ensure_ascii=False), str(run["run_number"]))
            entries.setdefault(key, []).append(run)
        return entries
    p_runs, b_runs = indexed(p_name), indexed(b_name)
    keys = p_runs.keys() | b_runs.keys()
    paired = []
    duplicate_keys, identity_mismatches = [], []
    for key in sorted(keys):
        left, right = p_runs.get(key, []), b_runs.get(key, [])
        if len(left) > 1 or len(right) > 1:
            duplicate_keys.append({"eval_id": json.loads(key[0]), "run_number": key[1]})
        if len(left) != 1 or len(right) != 1:
            continue
        p, b = left[0], right[0]
        if p.get("status") != "completed" or b.get("status") != "completed":
            continue
        mismatched = [field for field in ("models", "client")
                      if p.get(field) and b.get(field) and p[field] != b[field]]
        if mismatched:
            identity_mismatches.append({"eval_id": p["eval_id"], "run_number": p["run_number"],
                                        "fields": mismatched})
            continue
        paired.append((p, b))
    complete = bool(keys) and p_name != b_name and len(paired) == len(keys)
    delta = {"primary": p_name, "baseline": b_name,
             "expected_pairs": len(keys), "paired_samples": len(paired),
             "coverage": len(paired) / len(keys) if keys else 0.0,
             "duplicate_keys": duplicate_keys, "identity_mismatches": identity_mismatches,
             "metric_pairs": {}}
    for metric, precision in (("pass_rate", 2), ("time_seconds", 1), ("tokens", 0)):
        differences = [p[metric] - b[metric] for p, b in paired
                       if p.get(metric) is not None and b.get(metric) is not None]
        delta["metric_pairs"][metric] = len(differences)
        delta[metric] = (f"{statistics.mean(differences):+.{precision}f}"
                         if complete and len(differences) == len(keys) else None)
    if not complete:
        delta["note"] = ("delta unavailable: every observed eval_id + run_number needs one completed "
                         "run per configuration with no known model/client mismatch")
    elif any(delta[m] is None for m in ("time_seconds", "tokens")):
        delta["note"] = "cost delta unavailable where any paired measurement is missing"
    run_summary["delta"] = delta
    return run_summary


def generate_benchmark(benchmark_dir: Path, skill_name: str = "", skill_path: str = "",
                       primary: str = "with_skill", baseline: str = "without_skill") -> dict:
    results = load_run_results(benchmark_dir)
    run_summary = aggregate_results(results, primary=primary, baseline=baseline)
    # Report the actual observed runs per configuration (never a hard-coded 3).
    runs_per_configuration = max((len(runs) for runs in results.values()), default=0)
    runs = []
    for config, config_runs in results.items():
        for r in config_runs:
            runs.append({
                **{key: r[key] for key in ("eval_id", "run_number", "run_path", "status", "issues",
                                          "execution_status", "client", "model", "models", "model_source",
                                          "requested_model", "tokens_source", "tool_calls_source", "measurement_sources",
                                          "expectations", "notes")},
                "configuration": config,
                "result": {key: r[key] for key in ("pass_rate", "passed", "failed", "total",
                                                   "time_seconds", "tokens", "tool_calls")},
            })
    eval_ids = sorted({r["eval_id"] for config in results.values() for r in config}, key=str)
    models = sorted({model for r in runs for model in r["models"]})
    clients = sorted({r["client"] for r in runs if r["client"]})
    return {
        "schema_version": 2,
        "metadata": {
            "skill_name": skill_name or None,
            "skill_path": skill_path or None,
            "executor_model": models[0] if len(models) == 1 and all(r["model"] for r in runs) else None,
            "executor_models": models,
            "clients": clients,
            "unknown_model_runs": sum(not r["models"] for r in runs),
            "unknown_client_runs": sum(r["client"] is None for r in runs),
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": eval_ids,
            "runs_per_configuration": runs_per_configuration,
            "primary_configuration": run_summary["delta"]["primary"],
            "baseline_configuration": run_summary["delta"]["baseline"],
        },
        "runs": runs,
        "run_summary": run_summary,
        "notes": [],
    }


def generate_markdown(benchmark: dict) -> str:
    metadata = benchmark["metadata"]
    run_summary = benchmark["run_summary"]
    configs = [k for k in run_summary if k != "delta"]
    a = configs[0] if len(configs) >= 1 else "config_a"
    b = configs[1] if len(configs) >= 2 else "config_b"
    la, lb = a.replace("_", " ").title(), b.replace("_", " ").title()
    lines = [
        f"# Skill Benchmark: {metadata['skill_name']}",
        "",
        f"**Model**: {metadata.get('executor_model') or 'N/A'}; observed: {', '.join(metadata.get('executor_models', [])) or 'N/A'}",
        f"**Clients**: {', '.join(metadata.get('clients', [])) or 'N/A'}",
        f"**Unknown model/client runs**: {metadata.get('unknown_model_runs', 'N/A')} / {metadata.get('unknown_client_runs', 'N/A')}",
        f"**Date**: {metadata['timestamp']}",
        f"**Evals**: {', '.join(map(str, metadata['evals_run']))} (up to {metadata['runs_per_configuration']} runs per configuration)",
        "",
        "## Summary",
        "",
        f"| Metric | {la} | {lb} | Delta |",
        "|--------|------------|---------------|-------|",
    ]
    delta = run_summary.get("delta", {})

    def _delta_pct(value):
        # Delta is stored as a fraction (e.g. "+0.60"); render it in the same
        # percent units as the columns so "+0.60" does not read as +0.6%.
        if value is None:
            return "N/A"
        try:
            return f"{float(value) * 100:+.0f}%"
        except (TypeError, ValueError):
            return str(value)

    def _delta_raw(value, unit=""):
        if value is None:
            return "N/A"
        return f"{value}{unit}"

    def format_stat(config, metric, precision, scale=1, unit=""):
        stat = run_summary.get(config, {}).get(metric, {})
        if stat.get("mean") is None:
            return "N/A (n=0)"
        return (f"{stat['mean'] * scale:.{precision}f}{unit} ± "
                f"{(stat.get('stddev') or 0) * scale:.{precision}f}{unit} (n={stat.get('n', 'N/A')})")
    for metric, label, precision, scale, unit in (("pass_rate", "Pass Rate", 0, 100, "%"),
                                                 ("time_seconds", "Time", 1, 1, "s"),
                                                 ("tokens", "Tokens", 0, 1, "")):
        change = _delta_pct(delta.get(metric)) if metric == "pass_rate" else _delta_raw(delta.get(metric), unit)
        lines.append(f"| {label} | {format_stat(a, metric, precision, scale, unit)} | "
                     f"{format_stat(b, metric, precision, scale, unit)} | {change} |")
    lines.extend(["", "## Coverage", "",
                  "| Configuration | Attempted | Completed | Errors | Incomplete | Coverage |",
                  "|---|---:|---:|---:|---:|---:|"])
    for config in configs:
        stat = run_summary[config]
        lines.append(f"| {config} | {stat.get('attempted', 0)} | {stat.get('completed', 0)} | "
                     f"{stat.get('errors', 0)} | {stat.get('incomplete', 0)} | {stat.get('coverage', 0):.0%} |")
    lines.extend(["", f"Paired runs: {delta.get('paired_samples', 0)}/{delta.get('expected_pairs', 0)}; "
                  f"coverage {delta.get('coverage', 0):.0%}.",
                  "Pass rate uses completed runs; observed cost includes failed attempts. "
                  "Pairing covers discovered run directories, not an external planned test manifest."])
    if delta.get("note"):
        lines.extend(["", f"> {delta['note']}"])
    if benchmark.get("notes"):
        lines.extend(["", "## Notes", ""])
        lines.extend(f"- {n}" for n in benchmark["notes"])
    return "\n".join(lines) + "\n"


def load_notes(notes_path: Path) -> list[str]:
    """Load analyzer notes: a JSON array of strings, or an object with a notes array."""
    data = json.loads(notes_path.read_text(encoding="utf-8-sig"))
    if isinstance(data, dict):
        if "notes" not in data or not isinstance(data["notes"], list):
            raise ValueError("object-shaped notes file must contain a 'notes' array")
        data = data["notes"]
    if not isinstance(data, list) or not all(isinstance(n, str) for n in data):
        raise ValueError("notes file must be a JSON array of strings")
    return data


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Aggregate benchmark run results into summary statistics")
    parser.add_argument("benchmark_dir", type=Path, help="Path to the workspace iteration directory")
    parser.add_argument("--skill-name", default="", help="Name of the skill being benchmarked")
    parser.add_argument("--skill-path", default="", help="Path to the skill being benchmarked")
    parser.add_argument("--notes", type=Path, help="Analyzer notes file (JSON array of strings) merged into benchmark.json notes")
    parser.add_argument("--output", "-o", type=Path, help="Output path for benchmark.json (default: <dir>/benchmark.json)")
    parser.add_argument("--primary", default="with_skill",
                        help="Primary (skill) configuration name for delta; also recognizes known aliases")
    parser.add_argument("--baseline", default="without_skill",
                        help="Baseline configuration name for delta; also recognizes known aliases")
    parser.add_argument("--strict", action="store_true",
                        help="Write reports, then fail on incomplete/error runs or unavailable paired pass-rate delta")
    args = parser.parse_args()

    if not args.benchmark_dir.exists():
        print(f"Directory not found: {args.benchmark_dir}")
        return 1
    if not args.benchmark_dir.is_dir():
        print(f"Not a directory: {args.benchmark_dir}")
        return 1

    benchmark = generate_benchmark(args.benchmark_dir, args.skill_name, args.skill_path,
                                   args.primary, args.baseline)
    if args.notes:
        if not args.notes.exists():
            print(f"Notes file not found: {args.notes}")
            return 1
        if not args.notes.is_file():
            print(f"Notes path is not a file: {args.notes}")
            return 1
        try:
            benchmark["notes"] = benchmark.get("notes", []) + load_notes(args.notes)
        except (json.JSONDecodeError, ValueError, OSError) as e:
            print(f"Invalid notes file {args.notes}: {e}")
            return 1
    output_json = args.output or (args.benchmark_dir / "benchmark.json")
    if output_json.exists() and output_json.is_dir():
        print(f"Output path is a directory: {output_json}")
        return 1
    output_md = output_json.with_suffix(".md")
    try:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(benchmark, indent=2, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        output_md.write_text(generate_markdown(benchmark), encoding="utf-8")
    except OSError as e:
        print(f"Cannot write output: {e}")
        return 1
    print(f"Generated: {output_json}")
    print(f"Generated: {output_md}")
    for config, stat in benchmark["run_summary"].items():
        if config == "delta":
            continue
        mean = stat['pass_rate']['mean']
        rate = f"{mean * 100:.1f}%" if mean is not None else "N/A"
        print(f"  {config.replace('_', ' ').title()}: {rate} pass rate; "
              f"{stat['completed']}/{stat['attempted']} completed")
    print(f"  Delta: {benchmark['run_summary'].get('delta', {}).get('pass_rate') or '—'}")
    if args.strict and (benchmark['run_summary']['delta']['pass_rate'] is None
                        or any(r['status'] != 'completed' for r in benchmark['runs'])):
        print("Error: benchmark incomplete or unpaired; reports retained")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
