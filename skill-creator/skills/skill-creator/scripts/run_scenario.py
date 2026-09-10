#!/usr/bin/env python3
"""Run one eval scenario via a client CLI and record a benchmark-ready run directory.

Closes the gap in the quantitative loop: `aggregate_benchmark.py` can read a
workspace layout, but nothing produced one. This executor runs a real task
prompt with the skill available (`--skill-dir`) or without it, and writes the
per-run artifacts the grader / aggregator expect:

    <run-dir>/
    ├── transcript.md      # prompt + raw client output
    ├── outputs/
    │   └── response.txt   # extracted assistant text
    ├── metrics.json       # output_chars, total_tool_calls, client, model, skill
    └── timing.json        # total_duration_seconds

metrics.json lives in the run-dir root (sibling of timing.json / grading.json).
The grader merges it into grading.json execution_metrics, and
aggregate_benchmark.py reads it directly as a fallback.

The skill (when given) is copied into a throwaway client workspace, so the
"without_skill" run never sees it. `--client-cmd` overrides the invoked command
for clients whose CLI differs or for testing; `{prompt}` is substituted.

Usage:
    python scripts/run_scenario.py --client opencode --prompt "<task>" \
        --run-dir <workspace>/iteration-1/eval-x/with_skill/run-1 \
        [--skill-dir <skill>] [--model M] [--timeout 300] [--keep]

Exit code 0 = run recorded; 1 = error.
"""

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

# client -> (workspace subpath for a skill, argv builder)
CLIENTS = {
    "opencode": (".opencode/skills", lambda prompt, model: ["opencode", "run", "--format", "json", prompt]),
    "claude": (".claude/skills", lambda prompt, model: ["claude", "-p", prompt]),
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


def extract_text(raw: str) -> str:
    """Extract assistant text from a client's output (opencode JSON stream or plain)."""
    texts = []
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            part = ev.get("part") or {}
            if ev.get("type") == "text" and part.get("text"):
                texts.append(part["text"])
    return "\n".join(texts).strip() if texts else raw.strip()


def count_tool_calls(raw: str) -> int:
    """Count tool invocations in a client's JSON event stream.

    Parses each JSON line instead of substring-counting a serialized key, so the
    count is independent of the client's whitespace/formatting. Plain-text output
    (e.g. `claude -p`) yields 0.
    """
    count = 0
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(ev, dict) and ev.get("type") == "tool":
            count += 1
    return count


def build_command(client: str, prompt: str, model: str, override: str | None) -> list[str]:
    if override:
        parts = shlex.split(override)
        return [p.replace("{prompt}", prompt).replace("{model}", model) for p in parts]
    if client not in CLIENTS:
        raise RuntimeError(f"unknown client '{client}'")
    return CLIENTS[client][1](prompt, model)


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Run one eval scenario and record a run directory")
    parser.add_argument("--client", default="opencode", choices=sorted(CLIENTS))
    parser.add_argument("--prompt", required=True, help="The task prompt for this scenario")
    parser.add_argument("--run-dir", required=True, type=Path, help="Where to write the run artifacts")
    parser.add_argument("--skill-dir", type=Path, default=None,
                        help="Skill to install for this run (omit for the without_skill baseline)")
    parser.add_argument("--model", default="", help="Optional model id passed to the client")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--client-cmd", default=None,
                        help="Override command; {prompt}/{model} substituted (for testing)")
    parser.add_argument("--keep", action="store_true", help="Keep the throwaway workspace")
    args = parser.parse_args()

    run_dir = args.run_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    skill_name = None
    tmp = Path(tempfile.mkdtemp(prefix="scenario-"))
    try:
        if args.skill_dir:
            if not (args.skill_dir / "SKILL.md").exists():
                print(f"Error: no SKILL.md at {args.skill_dir}", file=sys.stderr)
                return 1
            skill_name = args.skill_dir.resolve().name
            rel = CLIENTS[args.client][0]
            dest = tmp / rel / skill_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(args.skill_dir, dest)

        cmd = build_command(args.client, args.prompt, args.model, args.client_cmd)
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        if args.model:
            env["OPENCODE_MODEL"] = args.model
        print(f"▶ [{args.client}] skill={skill_name or '(none)'} :: {args.prompt[:60]}", file=sys.stderr)
        start = time.time()
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tmp),
                                  env=env, timeout=args.timeout)
        except subprocess.TimeoutExpired:
            print(f"Error: client timed out after {args.timeout}s", file=sys.stderr)
            return 1
        except FileNotFoundError:
            print(f"Error: command not found: {cmd[0]}", file=sys.stderr)
            return 1
        duration = round(time.time() - start, 3)
        raw = (proc.stdout or "") + (proc.stderr or "")
        text = extract_text(raw)
    finally:
        if not args.keep:
            shutil.rmtree(tmp, ignore_errors=True)

    (run_dir / "outputs").mkdir(exist_ok=True)
    (run_dir / "outputs" / "response.txt").write_text(text, encoding="utf-8")
    (run_dir / "transcript.md").write_text(
        f"# Scenario run\n\n**Client**: {args.client}\n**Skill**: {skill_name or '(none)'}\n"
        f"**Timestamp**: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n"
        f"## Prompt\n\n{args.prompt}\n\n## Raw output\n\n```\n{raw}\n```\n",
        encoding="utf-8",
    )
    (run_dir / "timing.json").write_text(
        json.dumps({"total_duration_seconds": duration}, indent=2), encoding="utf-8")
    (run_dir / "metrics.json").write_text(
        json.dumps({
            "client": args.client,
            "model": args.model,
            "skill": skill_name,
            "returncode": proc.returncode,
            "output_chars": len(raw),
            "total_tool_calls": count_tool_calls(raw),
        }, indent=2), encoding="utf-8")

    print(f"✅ wrote run artifacts to {run_dir} ({duration}s, rc={proc.returncode})", file=sys.stderr)
    if proc.returncode != 0:
        print(f"Error: client exited {proc.returncode} — artifacts recorded, run marked as error", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
