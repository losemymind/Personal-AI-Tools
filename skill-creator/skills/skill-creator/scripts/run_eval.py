#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Port from Anthropic's official anthropics/skills skill-creator
(run_eval.py), generalized for the four-client skill-creator:

  --mode cli        headless client CLI (`claude -p`) — same mechanism as
                    upstream; requires the client CLI binary.
  --mode heuristic  deterministic keyword-overlap classifier (default, no
                    external CLI needed) — reuses the trigger heuristic from
                    run_trigger_tests.py.

Reads an eval set (evals.json: query + should_trigger), runs each query, and
reports per-query trigger rate plus summary (passed/total, precision, recall).

Usage:
    python scripts/run_eval.py --eval-set <evals.json> --skill-dir <skill> [--mode heuristic|cli] [--client claude] [--runs-per-query 1] [--threshold 0.5] [--json] [--output-dir <dir>]

Exit code 0 = evaluation produced; 1 if error.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from utils import parse_skill_md
from run_trigger_tests import classify, keyword_tokens  # noqa: F401 (reused heuristic)

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


def run_cli(query: str, skill_name: str, description: str, client: str, timeout: int = 60) -> bool:
    """Run one query via the client's headless CLI; return whether it triggered.

    Implements the upstream `claude -p` trigger harness for `--client claude`.
    Other clients map to their native headless run commands if available.
    """
    cmd_map = {"claude": ["claude", "-p"]}
    if client not in cmd_map:
        raise RuntimeError(f"--mode cli not available for client '{client}'; use --mode heuristic")
    cmd = cmd_map[client]
    cmd_parts = cmd + [query, "--output-format", "json"]
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    try:
        proc = subprocess.run(cmd_parts, capture_output=True, text=True, timeout=timeout, env=env)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
    output = (proc.stdout or "") + (proc.stderr or "")
    return skill_name.lower() in output.lower()


def run_heuristic(evals, description: str) -> list[dict]:
    """Classify each query by keyword overlap (no external CLI)."""
    results = []
    for item in evals:
        triggered = classify(item["query"], description)
        results.append({
            "query": item["query"],
            "should_trigger": bool(item.get("should_trigger")),
            "triggered": triggered,
            "pass": triggered == bool(item.get("should_trigger")),
        })
    return results


def summarize(results: list[dict]) -> dict:
    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    tp = sum(1 for r in results if r["should_trigger"] and r["triggered"])
    fp = sum(1 for r in results if not r["should_trigger"] and r["triggered"])
    fn = sum(1 for r in results if r["should_trigger"] and not r["triggered"])
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    return {
        "passed": passed,
        "failed": total - passed,
        "total": total,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
    }


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to evals.json")
    parser.add_argument("--skill-dir", required=True, help="Path to skill directory containing SKILL.md")
    parser.add_argument("--mode", choices=["heuristic", "cli"], default="heuristic",
                        help="heuristic=keyword classifier (default), cli=headless client CLI")
    parser.add_argument("--client", default="claude", help="CLI client for --mode cli")
    parser.add_argument("--runs-per-query", type=int, default=1, help="Runs per query (cli mode)")
    parser.add_argument("--threshold", type=float, default=0.5, help="Trigger rate threshold (cli mode)")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--output-dir", default=None,
                        help="Write results JSON (eval-results-<skill>.json) into this directory")
    args = parser.parse_args()

    eval_set_path = Path(args.eval_set)
    skill_dir = Path(args.skill_dir)
    if not eval_set_path.exists():
        print(f"Error: eval set not found: {eval_set_path}", file=sys.stderr)
        return 1
    if not (skill_dir / "SKILL.md").exists():
        print(f"Error: no SKILL.md at {skill_dir}", file=sys.stderr)
        return 1

    evals = json.loads(eval_set_path.read_text(encoding="utf-8-sig"))
    eval_list = evals.get("evals", evals) if isinstance(evals, dict) else evals
    name, description, _ = parse_skill_md(skill_dir)

    results = []
    if args.mode == "heuristic":
        results = run_heuristic(eval_list, description)
    else:
        for item in eval_list:
            query = item["query"]
            triggers = 0
            for _ in range(max(1, args.runs_per_query)):
                if run_cli(query, name, description, args.client):
                    triggers += 1
            rate = triggers / max(1, args.runs_per_query)
            results.append({
                "query": query,
                "should_trigger": bool(item.get("should_trigger")),
                "trigger_rate": rate,
                "pass": (rate >= args.threshold) if item.get("should_trigger") else (rate < args.threshold),
            })

    output = {
        "skill_name": name,
        "description": description,
        "mode": args.mode,
        "results": results,
        "summary": summarize(results),
    }
    if args.output_dir:
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"eval-results-{name}.json"
        out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Results written to: {out_path}", file=sys.stderr)
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        s = output["summary"]
        print(f"Evaluating: {name} ({args.mode} mode)  —  {s['passed']}/{s['total']} passed, "
              f"precision={s['precision']:.0%} recall={s['recall']:.0%}")
        for r in results:
            status = "PASS" if r["pass"] else "FAIL"
            expected = "Y" if r["should_trigger"] else "N"
            print(f"  [{status}] expect={expected} :: {r['query'][:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())