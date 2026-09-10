#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Port from Anthropic's official anthropics/skills skill-creator (run_eval.py),
generalized for the four-client skill-creator:

  --mode cli        headless client CLI (`claude -p`, `opencode run`) — same
                    mechanism as upstream; requires the client CLI binary.
  --mode heuristic  deterministic keyword-overlap classifier (default, no
                    external CLI needed) — CJK-aware, see utils.keyword_tokens.

Reads an eval set (evals.json: query + should_trigger), runs each query, and
reports per-query trigger rate plus summary (passed/total, precision, recall).
Run errors (missing/timeout/failed CLI) are reported separately as `errors`
instead of being silently counted as "did not trigger".

Usage:
    python scripts/run_eval.py --eval-set <evals.json> --skill-dir <skill> [--mode heuristic|cli] [--client claude|opencode] [--model <id>] [--timeout 60] [--runs-per-query 1] [--threshold 0.5] [--json] [--output-dir <dir>]

Exit code 0 = evaluation produced; 1 if error.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from utils import classify, eval_query, parse_skill_md

SCRIPT_DIR = Path(__file__).resolve().parent

# client -> argv builder for one headless run of `query` (optionally with --model).
# A model override is required on machines whose client default model is unset or
# misconfigured (e.g. opencode's config `model` pointing at a non-existent provider),
# otherwise every cli run fails with a provider/model error — a run_error, not a miss.
CLI_COMMANDS = {
    "claude": lambda query, model: (
        ["claude", "-p", query, "--output-format", "json"] + (["--model", model] if model else [])
    ),
    "opencode": lambda query, model: (
        ["opencode", "run", "--format", "json"] + (["-m", model] if model else []) + [query]
    ),
}


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


def detect_triggered(client: str, raw: str, skill_name: str) -> bool:
    """Decide whether the skill was actually *invoked*, from the raw client output.

    A real trigger is the client dispatching its skill tool for this skill. For
    opencode that is a JSON line `{"type":"tool_use","part":{"tool":"skill",
    "state":{"input":{"name":"<skill>"}}}}`. Substring-matching the whole
    transcript is wrong: a workspace listing (`Get-ChildItem` showing
    `.opencode/skills/<name>`), the model merely *mentioning* the skill, or a
    failed attempt would all count as a trigger — a false-positive source that
    only shows up against a real client.

    Clients whose stream format we don't model (e.g. claude) fall back to a
    best-effort substring check.
    """
    target = skill_name.lower()
    if client == "opencode":
        for line in raw.splitlines():
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            part = ev.get("part") or {}
            if ev.get("type") == "tool_use" and part.get("tool") == "skill":
                name = ((part.get("state") or {}).get("input") or {}).get("name")
                if isinstance(name, str) and name.lower() == target:
                    return True
        return False
    return target in raw.lower()


def run_cli(query: str, skill_name: str, description: str, client: str, timeout: int = 60,
            model: str = "") -> bool:
    """Run one query via the client's headless CLI; return whether it triggered.

    Raises RuntimeError when the CLI cannot be run or fails — such run_error
    cases are surfaced separately and must not be counted as "did not trigger"
    (see SKILL.md stage 7 attribution).
    """
    if client not in CLI_COMMANDS:
        raise RuntimeError(f"--mode cli not available for client '{client}'; use --mode heuristic")
    cmd = CLI_COMMANDS[client](query, model)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"cli timeout after {timeout}s ({client})") from e
    except FileNotFoundError as e:
        raise RuntimeError(f"cli not found: {cmd[0]} ({client})") from e
    if proc.returncode != 0:
        raise RuntimeError(f"cli exited {proc.returncode} ({client}): {(proc.stderr or '')[-300:]}")
    output = (proc.stdout or "") + (proc.stderr or "")
    return detect_triggered(client, output, skill_name)


def run_heuristic(evals, description: str) -> list[dict]:
    """Classify each query by keyword overlap (no external CLI)."""
    results = []
    for item in evals:
        query = eval_query(item)
        triggered = classify(query, description)
        results.append({
            "query": query,
            "should_trigger": bool(item.get("should_trigger")),
            "triggered": triggered,
            "pass": triggered == bool(item.get("should_trigger")),
        })
    return results


def _is_triggered(r: dict, threshold: float) -> bool | None:
    """Normalize the two result shapes to a boolean trigger verdict.

    heuristic results carry `triggered` (bool); cli results carry `trigger_rate`
    (float, over runs) with no `triggered` key — derive it from the same threshold.
    Returns None when neither is available.
    """
    if "triggered" in r:
        return bool(r["triggered"])
    rate = r.get("trigger_rate")
    return None if rate is None else (rate >= threshold)


def summarize(results: list[dict], threshold: float = 0.5) -> dict:
    errors = sum(1 for r in results if r.get("error"))
    scored = [r for r in results if not r.get("error")]
    passed = sum(1 for r in scored if r["pass"])
    # total counts scored queries only, so passed + failed == total; run errors are
    # reported separately and never inflate the denominator (see stage 7 attribution).
    total = len(scored)
    tp = fp = fn = 0
    for r in scored:
        triggered = _is_triggered(r, threshold)
        if triggered is None:
            continue
        should = bool(r["should_trigger"])
        if should and triggered:
            tp += 1
        elif not should and triggered:
            fp += 1
        elif should and not triggered:
            fn += 1
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    return {
        "passed": passed,
        "failed": len(scored) - passed,
        "errors": errors,
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
    parser.add_argument("--client", default="claude", choices=sorted(CLI_COMMANDS),
                        help="CLI client for --mode cli")
    parser.add_argument("--model", default="",
                        help="Model id passed to the client CLI (--model/-m); required when the "
                             "client default model is unset/misconfigured")
    parser.add_argument("--runs-per-query", type=int, default=1, help="Runs per query (cli mode)")
    parser.add_argument("--threshold", type=float, default=0.5, help="Trigger rate threshold (cli mode)")
    parser.add_argument("--timeout", type=int, default=60, help="Per-query CLI timeout in seconds (cli mode)")
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
            query = eval_query(item)
            should = bool(item.get("should_trigger"))
            try:
                triggers = 0
                for _ in range(max(1, args.runs_per_query)):
                    if run_cli(query, name, description, args.client, timeout=args.timeout, model=args.model):
                        triggers += 1
                rate = triggers / max(1, args.runs_per_query)
            except RuntimeError as e:
                results.append({
                    "query": query,
                    "should_trigger": should,
                    "trigger_rate": None,
                    "pass": None,
                    "error": str(e),
                })
                continue
            results.append({
                "query": query,
                "should_trigger": should,
                "trigger_rate": rate,
                "pass": (rate >= args.threshold) if should else (rate < args.threshold),
            })

    output = {
        "skill_name": name,
        "description": description,
        "mode": args.mode,
        "results": results,
        "summary": summarize(results, threshold=args.threshold),
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
              f"precision={s['precision']:.0%} recall={s['recall']:.0%}"
              + (f", {s['errors']} run errors" if s["errors"] else ""))
        for r in results:
            if r.get("error"):
                print(f"  [ERROR] :: {r['query'][:70]} — {r['error']}")
                continue
            status = "PASS" if r["pass"] else "FAIL"
            expected = "Y" if r["should_trigger"] else "N"
            print(f"  [{status}] expect={expected} :: {r['query'][:70]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
