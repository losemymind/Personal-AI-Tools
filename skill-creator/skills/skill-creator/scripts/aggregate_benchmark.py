#!/usr/bin/env python3
"""Aggregate benchmark run results into summary statistics (benchmark.json + benchmark.md).

Port from Anthropic's official anthropics/skills skill-creator
(aggregate_benchmark.py), kept client-agnostic (pure stdlib).

Reads grading.json / timing.json from a workspace layout and produces:
  - <dir>/benchmark.json  — machine-readable summary with mean/stddev/min/max + delta
  - <dir>/benchmark.md    — human-readable table (pass rate / time / tokens)

Usage:
    python scripts/aggregate_benchmark.py <workspace>/iteration-N --skill-name <name> [--skill-path <path>] [--notes <notes.json>]

Layouts supported:
    <workspace>/iteration-N/
    └── eval-<name>/
        ├── with_skill/run-1/grading.json   (+ optional timing.json)
        └── without_skill/run-1/grading.json

--notes merges analyzer observations (a JSON array of strings produced by the
analyzer subagent, see agents/analyzer.md mode 2) into benchmark.json's notes.
"""

import argparse
import json
import math
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
    if not values:
        return {"mean": 0.0, "stddev": 0.0, "min": 0.0, "max": 0.0}
    n = len(values)
    mean = sum(values) / n
    stddev = 0.0
    if n > 1:
        variance = sum((x - mean) ** 2 for x in values) / (n - 1)
        stddev = math.sqrt(variance)
    return {
        "mean": round(mean, 4),
        "stddev": round(stddev, 4),
        "min": round(min(values), 4),
        "max": round(max(values), 4),
    }


def load_run_results(benchmark_dir: Path) -> dict[str, list[dict]]:
    runs_dir = benchmark_dir / "runs"
    if runs_dir.exists():
        search_dir = runs_dir
    elif list(benchmark_dir.glob("eval-*")):
        search_dir = benchmark_dir
    else:
        print(f"No eval directories found in {benchmark_dir} or {benchmark_dir / 'runs'}")
        return {}

    results: dict[str, list[dict]] = {}
    for eval_dir in sorted(search_dir.glob("eval-*")):
        metadata_path = eval_dir / "eval_metadata.json"
        eval_id: int | str = eval_dir.name
        if metadata_path.exists():
            try:
                eval_id = json.loads(metadata_path.read_text(encoding="utf-8-sig")).get("eval_id", eval_dir.name)
            except (json.JSONDecodeError, OSError):
                pass
        for config_dir in sorted(eval_dir.iterdir()):
            if not config_dir.is_dir() or not list(config_dir.glob("run-*")):
                continue
            config = config_dir.name
            results.setdefault(config, [])
            for run_dir in sorted(config_dir.glob("run-*")):
                grading_file = run_dir / "grading.json"
                if not grading_file.exists():
                    print(f"Warning: grading.json not found in {run_dir}")
                    continue
                try:
                    grading = json.loads(grading_file.read_text(encoding="utf-8-sig"))
                except json.JSONDecodeError as e:
                    print(f"Warning: invalid JSON in {grading_file}: {e}")
                    continue
                run_number = int(run_dir.name.split("-")[1]) if "-" in run_dir.name else 0
                result = {
                    "eval_id": eval_id,
                    "run_number": run_number,
                    "pass_rate": grading.get("summary", {}).get("pass_rate", 0.0),
                    "passed": grading.get("summary", {}).get("passed", 0),
                    "failed": grading.get("summary", {}).get("failed", 0),
                    "total": grading.get("summary", {}).get("total", 0),
                }
                timing = grading.get("timing", {})
                result["time_seconds"] = timing.get("total_duration_seconds", 0.0)
                # Tokens must come from a token field — never from output_chars
                # (characters are not tokens). timing.json / metrics.json may supply them below.
                metrics = grading.get("execution_metrics", {}) or {}
                result["tokens"] = metrics.get("total_tokens", metrics.get("tokens", 0))
                result["tool_calls"] = metrics.get("total_tool_calls", 0)
                # run_scenario.py writes a sibling metrics.json in the run dir (next to
                # timing.json). Use it as the deterministic fallback when the grader's
                # execution_metrics does not carry the counts — the contract documented
                # in references/benchmark-schema.md and agents/grader.md.
                metrics_file = run_dir / "metrics.json"
                if metrics_file.exists():
                    try:
                        mdata = json.loads(metrics_file.read_text(encoding="utf-8-sig"))
                    except json.JSONDecodeError:
                        mdata = {}
                    if not result["tool_calls"]:
                        result["tool_calls"] = mdata.get("total_tool_calls", result["tool_calls"])
                    if not result["tokens"]:
                        result["tokens"] = mdata.get("total_tokens", result["tokens"])
                timing_file = run_dir / "timing.json"
                if timing_file.exists():
                    try:
                        tdata = json.loads(timing_file.read_text(encoding="utf-8-sig"))
                    except json.JSONDecodeError:
                        tdata = {}
                    if result["time_seconds"] == 0.0:
                        result["time_seconds"] = tdata.get("total_duration_seconds", 0.0)
                    result["tokens"] = tdata.get("total_tokens", result["tokens"])
                expectations = grading.get("expectations", [])
                result["expectations"] = [
                    {k: e.get(k) for k in ("text", "passed", "evidence")} for e in expectations
                ]
                notes = []
                notes_summary = grading.get("user_notes_summary", {})
                notes.extend(notes_summary.get("uncertainties", []))
                notes.extend(notes_summary.get("needs_review", []))
                notes.extend(notes_summary.get("workarounds", []))
                result["notes"] = notes
                results[config].append(result)
    return results


def aggregate_results(results: dict[str, list[dict]]) -> dict:
    run_summary: dict = {}
    for config, runs in results.items():
        if not runs:
            run_summary[config] = {
                "pass_rate": calculate_stats([]),
                "time_seconds": calculate_stats([]),
                "tokens": calculate_stats([]),
            }
            continue
        run_summary[config] = {
            "pass_rate": calculate_stats([r["pass_rate"] for r in runs]),
            "time_seconds": calculate_stats([r["time_seconds"] for r in runs]),
            "tokens": calculate_stats([float(r["tokens"]) for r in runs]),
        }
    configs = list(results.keys())
    if len(configs) >= 2:
        primary = run_summary.get(configs[0], {})
        baseline = run_summary.get(configs[1], {})
    else:
        primary = run_summary.get(configs[0], {}) if configs else {}
        baseline = {}
    delta = {
        "pass_rate": f"{primary.get('pass_rate', {}).get('mean', 0) - baseline.get('pass_rate', {}).get('mean', 0):+.2f}",
        "time_seconds": f"{primary.get('time_seconds', {}).get('mean', 0) - baseline.get('time_seconds', {}).get('mean', 0):+.1f}",
        "tokens": f"{primary.get('tokens', {}).get('mean', 0) - baseline.get('tokens', {}).get('mean', 0):+.0f}",
    }
    run_summary["delta"] = delta
    return run_summary


def generate_benchmark(benchmark_dir: Path, skill_name: str = "", skill_path: str = "") -> dict:
    results = load_run_results(benchmark_dir)
    run_summary = aggregate_results(results)
    # Report the actual observed runs per configuration (never a hard-coded 3).
    runs_per_configuration = max((len(runs) for runs in results.values()), default=0)
    runs = []
    for config in results:
        for r in results[config]:
            runs.append({
                "eval_id": r["eval_id"],
                "configuration": config,
                "run_number": r["run_number"],
                "result": {
                    "pass_rate": r["pass_rate"],
                    "passed": r["passed"],
                    "failed": r["failed"],
                    "total": r["total"],
                    "time_seconds": r["time_seconds"],
                    "tokens": r["tokens"],
                    "tool_calls": r["tool_calls"],
                },
                "expectations": r["expectations"],
                "notes": r["notes"],
            })
    eval_ids = sorted({r["eval_id"] for config in results.values() for r in config})
    return {
        "metadata": {
            "skill_name": skill_name or "<skill-name>",
            "skill_path": skill_path or "<path/to/skill>",
            "executor_model": "<model-name>",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": eval_ids,
            "runs_per_configuration": runs_per_configuration,
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
        f"**Model**: {metadata['executor_model']}",
        f"**Date**: {metadata['timestamp']}",
        f"**Evals**: {', '.join(map(str, metadata['evals_run']))} ({metadata['runs_per_configuration']} runs each per configuration)",
        "",
        "## Summary",
        "",
        f"| Metric | {la} | {lb} | Delta |",
        "|--------|------------|---------------|-------|",
    ]
    delta = run_summary.get("delta", {})
    a_pr, b_pr = run_summary.get(a, {}).get("pass_rate", {}), run_summary.get(b, {}).get("pass_rate", {})
    lines.append(f"| Pass Rate | {a_pr.get('mean', 0)*100:.0f}% ± {a_pr.get('stddev', 0)*100:.0f}% | "
                 f"{b_pr.get('mean', 0)*100:.0f}% ± {b_pr.get('stddev', 0)*100:.0f}% | {delta.get('pass_rate', '—')} |")
    a_t, b_t = run_summary.get(a, {}).get("time_seconds", {}), run_summary.get(b, {}).get("time_seconds", {})
    lines.append(f"| Time | {a_t.get('mean', 0):.1f}s ± {a_t.get('stddev', 0):.1f}s | "
                 f"{b_t.get('mean', 0):.1f}s ± {b_t.get('stddev', 0):.1f}s | {delta.get('time_seconds', '—')}s |")
    a_tok, b_tok = run_summary.get(a, {}).get("tokens", {}), run_summary.get(b, {}).get("tokens", {})
    lines.append(f"| Tokens | {a_tok.get('mean', 0):.0f} ± {a_tok.get('stddev', 0):.0f} | "
                 f"{b_tok.get('mean', 0):.0f} ± {b_tok.get('stddev', 0):.0f} | {delta.get('tokens', '—')} |")
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
    args = parser.parse_args()

    if not args.benchmark_dir.exists():
        print(f"Directory not found: {args.benchmark_dir}")
        return 1

    benchmark = generate_benchmark(args.benchmark_dir, args.skill_name, args.skill_path)
    if args.notes:
        if not args.notes.exists():
            print(f"Notes file not found: {args.notes}")
            return 1
        try:
            benchmark["notes"] = benchmark.get("notes", []) + load_notes(args.notes)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Invalid notes file {args.notes}: {e}")
            return 1
    output_json = args.output or (args.benchmark_dir / "benchmark.json")
    output_md = output_json.with_suffix(".md")
    output_json.write_text(json.dumps(benchmark, indent=2, ensure_ascii=False), encoding="utf-8")
    output_md.write_text(generate_markdown(benchmark), encoding="utf-8")
    print(f"Generated: {output_json}")
    print(f"Generated: {output_md}")
    for config, stat in benchmark["run_summary"].items():
        if config == "delta":
            continue
        print(f"  {config.replace('_', ' ').title()}: {stat['pass_rate']['mean']*100:.1f}% pass rate")
    print(f"  Delta: {benchmark['run_summary'].get('delta', {}).get('pass_rate', '—')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())