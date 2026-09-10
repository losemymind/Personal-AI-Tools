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
    # Drop non-numeric / non-finite entries so NaN/Infinity never reach the JSON
    # artifact (which the schema calls machine-readable).
    clean: list[float] = []
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError, OverflowError):
            continue
        if math.isfinite(f):
            clean.append(f)
    values = clean
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


def _as_float(value, default: float = 0.0) -> float:
    """Coerce a possibly-string/None/odd/non-finite field to a finite float."""
    if isinstance(value, bool):
        return float(value)
    try:
        x = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    # JSON accepts Infinity/NaN/1e400; rejecting them keeps benchmark.json valid
    # strict JSON and stops inf/nan propagating into stats and int conversion.
    return x if math.isfinite(x) else default


def _as_int(value, default: int = 0) -> int:
    x = _as_float(value, default)
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
        if not eval_dir.is_dir():  # a stray file named eval-* is not an eval
            continue
        metadata_path = eval_dir / "eval_metadata.json"
        eval_id: int | str = eval_dir.name
        if metadata_path.exists():
            try:
                meta = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
                if isinstance(meta, dict):
                    eval_id = _coerce_eval_id(meta.get("eval_id", eval_dir.name), eval_dir.name)
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
                if not isinstance(grading, dict):
                    print(f"Warning: grading.json must be an object: {grading_file}")
                    continue
                try:
                    run_number = int(run_dir.name.split("-")[1]) if "-" in run_dir.name else 0
                except (IndexError, ValueError):
                    run_number = 0
                grading_summary = grading.get("summary", {})
                if not isinstance(grading_summary, dict):
                    grading_summary = {}
                result = {
                    "eval_id": eval_id,
                    "run_number": run_number,
                    "pass_rate": _as_float(grading_summary.get("pass_rate", 0.0)),
                    "passed": _as_int(grading_summary.get("passed", 0)),
                    "failed": _as_int(grading_summary.get("failed", 0)),
                    "total": _as_int(grading_summary.get("total", 0)),
                }
                timing = grading.get("timing", {})
                if not isinstance(timing, dict):
                    timing = {}
                result["time_seconds"] = _as_float(timing.get("total_duration_seconds", 0.0))
                # Tokens must come from a token field — never from output_chars
                # (characters are not tokens). timing.json / metrics.json may supply them below.
                metrics = grading.get("execution_metrics", {}) or {}
                if not isinstance(metrics, dict):
                    metrics = {}
                result["tokens"] = _as_float(metrics.get("total_tokens", metrics.get("tokens", 0)))
                result["tool_calls"] = _as_int(metrics.get("total_tool_calls", 0))
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
                    if not isinstance(mdata, dict):
                        mdata = {}
                    if not result["tool_calls"]:
                        result["tool_calls"] = _as_int(mdata.get("total_tool_calls", result["tool_calls"]))
                    if not result["tokens"]:
                        result["tokens"] = _as_float(mdata.get("total_tokens", result["tokens"]))
                timing_file = run_dir / "timing.json"
                if timing_file.exists():
                    try:
                        tdata = json.loads(timing_file.read_text(encoding="utf-8-sig"))
                    except json.JSONDecodeError:
                        tdata = {}
                    if not isinstance(tdata, dict):
                        tdata = {}
                    if result["time_seconds"] == 0.0:
                        result["time_seconds"] = _as_float(tdata.get("total_duration_seconds", 0.0))
                    result["tokens"] = _as_float(tdata.get("total_tokens", result["tokens"]))
                expectations = grading.get("expectations", [])
                if not isinstance(expectations, list):
                    expectations = []
                result["expectations"] = [
                    {k: e.get(k) for k in ("text", "passed", "evidence")}
                    for e in expectations
                    if isinstance(e, dict)
                ]
                notes = []
                notes_summary = grading.get("user_notes_summary", {})
                if isinstance(notes_summary, dict):
                    # Only list-valued fields; a string would be split into characters.
                    for nkey in ("uncertainties", "needs_review", "workarounds"):
                        nval = notes_summary.get(nkey)
                        if isinstance(nval, list):
                            notes.extend(nval)
                result["notes"] = notes
                results[config].append(result)
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


def aggregate_results(results: dict[str, list[dict]], primary: str = "with_skill",
                      baseline: str = "without_skill") -> dict:
    ordered = _ordered_configs(results, primary, baseline)
    run_summary: dict = {}
    for config in ordered:
        runs = results[config]
        if not runs:
            run_summary[config] = {
                "runs": 0,
                "pass_rate": calculate_stats([]),
                "time_seconds": calculate_stats([]),
                "tokens": calculate_stats([]),
            }
            continue
        run_summary[config] = {
            "runs": len(runs),
            "pass_rate": calculate_stats([r["pass_rate"] for r in runs]),
            "time_seconds": calculate_stats([r["time_seconds"] for r in runs]),
            "tokens": calculate_stats([float(r["tokens"]) for r in runs]),
        }
    p_name = ordered[0] if ordered else None
    b_name = ordered[1] if len(ordered) > 1 else None
    p = run_summary.get(p_name, {}) if p_name else {}
    b = run_summary.get(b_name, {}) if b_name else {}
    # A delta needs real observations on BOTH sides; comparing against a zero-run
    # config would report a full gain where there is simply no baseline data.
    comparable = bool(p.get("runs")) and bool(b.get("runs"))
    if comparable:
        delta = {
            "primary": p_name,
            "baseline": b_name,
            "pass_rate": f"{p.get('pass_rate', {}).get('mean', 0) - b.get('pass_rate', {}).get('mean', 0):+.2f}",
            "time_seconds": f"{p.get('time_seconds', {}).get('mean', 0) - b.get('time_seconds', {}).get('mean', 0):+.1f}",
            "tokens": f"{p.get('tokens', {}).get('mean', 0) - b.get('tokens', {}).get('mean', 0):+.0f}",
        }
    else:
        delta = {
            "primary": p_name,
            "baseline": b_name,
            "pass_rate": None,
            "time_seconds": None,
            "tokens": None,
            "note": "delta unavailable: need >=1 run in both primary and baseline",
        }
    run_summary["delta"] = delta
    return run_summary


def generate_benchmark(benchmark_dir: Path, skill_name: str = "", skill_path: str = "",
                       primary: str = "with_skill", baseline: str = "without_skill") -> dict:
    results = load_run_results(benchmark_dir)
    run_summary = aggregate_results(results, primary=primary, baseline=baseline)
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
    eval_ids = sorted({r["eval_id"] for config in results.values() for r in config}, key=str)
    return {
        "metadata": {
            "skill_name": skill_name or "<skill-name>",
            "skill_path": skill_path or "<path/to/skill>",
            "executor_model": "<model-name>",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "evals_run": eval_ids,
            "runs_per_configuration": runs_per_configuration,
            "primary_configuration": run_summary.get("delta", {}).get("primary"),
            "baseline_configuration": run_summary.get("delta", {}).get("baseline"),
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
            return "—"
        try:
            return f"{float(value) * 100:+.0f}%"
        except (TypeError, ValueError):
            return str(value)

    def _delta_raw(value, unit=""):
        if value is None:
            return "—"
        return f"{value}{unit}"

    a_pr, b_pr = run_summary.get(a, {}).get("pass_rate", {}), run_summary.get(b, {}).get("pass_rate", {})
    lines.append(f"| Pass Rate | {a_pr.get('mean', 0)*100:.0f}% ± {a_pr.get('stddev', 0)*100:.0f}% | "
                 f"{b_pr.get('mean', 0)*100:.0f}% ± {b_pr.get('stddev', 0)*100:.0f}% | {_delta_pct(delta.get('pass_rate'))} |")
    a_t, b_t = run_summary.get(a, {}).get("time_seconds", {}), run_summary.get(b, {}).get("time_seconds", {})
    lines.append(f"| Time | {a_t.get('mean', 0):.1f}s ± {a_t.get('stddev', 0):.1f}s | "
                 f"{b_t.get('mean', 0):.1f}s ± {b_t.get('stddev', 0):.1f}s | {_delta_raw(delta.get('time_seconds'), 's')} |")
    a_tok, b_tok = run_summary.get(a, {}).get("tokens", {}), run_summary.get(b, {}).get("tokens", {})
    lines.append(f"| Tokens | {a_tok.get('mean', 0):.0f} ± {a_tok.get('stddev', 0):.0f} | "
                 f"{b_tok.get('mean', 0):.0f} ± {b_tok.get('stddev', 0):.0f} | {_delta_raw(delta.get('tokens'))} |")
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
                        help="Primary (skill) configuration name for delta; falls back to a known alias then input order")
    parser.add_argument("--baseline", default="without_skill",
                        help="Baseline configuration name for delta; falls back to a known alias then input order")
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
        output_json.write_text(json.dumps(benchmark, indent=2, ensure_ascii=False), encoding="utf-8")
        output_md.write_text(generate_markdown(benchmark), encoding="utf-8")
    except OSError as e:
        print(f"Cannot write output: {e}")
        return 1
    print(f"Generated: {output_json}")
    print(f"Generated: {output_md}")
    for config, stat in benchmark["run_summary"].items():
        if config == "delta":
            continue
        print(f"  {config.replace('_', ' ').title()}: {stat['pass_rate']['mean']*100:.1f}% pass rate")
    print(f"  Delta: {benchmark['run_summary'].get('delta', {}).get('pass_rate') or '—'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())