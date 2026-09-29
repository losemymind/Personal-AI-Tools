#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Port from Anthropic's official anthropics/skills skill-creator (run_eval.py),
generalized for the four-client skill-creator:

  --mode cli        headless client CLI (`claude -p`, `opencode run`) — same
                    mechanism as upstream; requires the client CLI binary. This is
                    the authoritative signal: opencode triggers are read from the
                    real skill-dispatch event, not from text.
  --mode heuristic  deterministic keyword-overlap classifier (default, no
                    external CLI needed) — CJK-aware, see skill_utils.keyword_tokens.
                    This is explicitly a *lexical-coverage proxy metric* (词面覆盖
                    代理指标), NOT a measurement of real trigger behaviour: it only
                    reports how much wording the query and the description share.
                    It runs offline when no client CLI is available; use `cli` mode
                    for real dispatch. Its false positives/negatives are inherent to
                    overlap and are not regressions.

Reads an eval set (evals.json: query + should_trigger), runs each query, and
reports per-query trigger rate plus summary (passed/total, precision, recall).
Run errors (missing/timeout/failed CLI) are reported separately as `errors`
instead of being silently counted as "did not trigger".

Usage:
    python scripts/skill_eval.py --eval-set <evals.json> --skill-dir <skill> [--mode heuristic|cli] [--client claude|opencode] [--model <id>] [--timeout 60] [--runs-per-query 1] [--threshold 0.5] [--concurrency 1] [--keep-workspace] [--json] [--output-dir <dir>]

In `cli` mode each query runs in its own throwaway workspace (skill installed
under the client's discovery path), so default file writes have a separate cwd.
This is file isolation, not a security sandbox: client permissions and global
configuration are still inherited. `--keep-workspace` retains it for debugging.

Exit code 0 = report produced; 1 on input/output errors or a requested gate
(--fail-on-error / --fail-on-mismatch) failing.
"""

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from skill_events import events, execution_error, tool_calls
from skill_utils import classify, eval_query, load_eval_set, parse_skill_md, run_client

SCRIPT_DIR = Path(__file__).resolve().parent

# client -> argv builder for one headless run of `query` (optionally with --model).
# A model override is required on machines whose client default model is unset or
# misconfigured (e.g. opencode's config `model` pointing at a non-existent provider),
# otherwise every cli run fails with a provider/model error — a run_error, not a miss.
CLI_COMMANDS = {
    "claude": lambda query, model: (
        ["claude", "-p", query, "--output-format", "stream-json", "--verbose",
         "--include-partial-messages"] + (["--model", model] if model else [])
    ),
    "opencode": lambda query, model: (
        ["opencode", "run", "--format", "json"] + (["-m", model] if model else []) + [query]
    ),
}

# client -> workspace subpath the client discovers skills from (mirrors skill_scenario).
SKILL_SUBPATHS = {
    "opencode": ".opencode/skills",
    "claude": ".claude/skills",
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


def build_workspace(skill_dir: Path, client: str) -> Path:
    """Create a throwaway client workspace with `skill_dir` installed; return its root.

    cli trigger evaluation must NOT run in the caller's real workspace. A real
    trigger lets the client actually execute the skill, which can create files
    (eval outputs, indexes) and even spawn long-lived child processes — observed
    against opencode, where a triggered skill-creator ran its own eval tooling and
    mutated the repository. Copying the skill into a temp dir and running the
    client there directs default file writes to a directory deleted afterwards.
    Global settings and filesystem permissions remain in effect. The skill is placed at the client's
    discovery subpath so the run still exercises a real install.
    """
    tmp = Path(tempfile.mkdtemp(prefix="eval-"))
    try:
        subpath = SKILL_SUBPATHS.get(client)
        if subpath:
            dest = tmp / subpath / skill_dir.resolve().name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(skill_dir, dest)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise
    return tmp


def set_workspace_description(workspace: Path, skill_dir: Path, client: str,
                              description: str) -> None:
    """Change only the installed copy so CLI evaluation measures the candidate."""
    import yaml

    target = workspace / SKILL_SUBPATHS[client] / skill_dir.resolve().name / "SKILL.md"
    content = target.read_text(encoding="utf-8-sig")
    match = re.match(r"\A---[^\S\n]*\n(.*?)\n---[^\S\n]*(?:\n|$)", content, re.DOTALL)
    if not match:
        raise ValueError("candidate skill has no YAML frontmatter")
    try:
        metadata = yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        raise ValueError(f"candidate frontmatter is invalid: {e}") from e
    if not isinstance(metadata, dict):
        raise ValueError("candidate skill frontmatter must be a mapping")
    metadata["description"] = description
    frontmatter = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False, width=4096)
    target.write_text("---\n" + frontmatter + "---\n" + content[match.end():], encoding="utf-8")


def trigger_evidence(client: str, raw: str, skill_name: str,
                     skill_path: str | os.PathLike | None = None) -> list[dict]:
    """Match exact skill dispatch or a Read of the installed target SKILL.md.

    A name mentioned in text or in another tool's input is never evidence. With
    no installed path supplied, Read must use the exact discovery-relative path;
    normal evaluation supplies the installed absolute path to avoid global-skill
    or same-name-file false positives.
    """
    def normalized(value):
        return os.path.normcase(os.path.normpath(value.replace("\\", "/"))).replace("\\", "/")

    relative = f"{SKILL_SUBPATHS.get(client, '')}/{skill_name}/SKILL.md"
    allowed = {normalized(relative)} if skill_path is None else set()
    if skill_path is not None:
        allowed.add(normalized(str(skill_path)))
        # The installed folder can differ from frontmatter name.
        path = Path(skill_path)
        allowed.add(normalized(f"{SKILL_SUBPATHS.get(client, '')}/{path.parent.name}/SKILL.md"))
    evidence = []
    for call in tool_calls(raw, client):
        if call["status"] in ("error", "failed"):
            continue
        inputs = call["input"]
        kind = None
        name = inputs.get("name" if client == "opencode" else "skill")
        if call["tool"] == ("skill" if client == "opencode" else "Skill") and name == skill_name:
            kind = "skill_dispatch"
        file_path = inputs.get("file_path")
        if client == "claude" and call["tool"] == "Read" and isinstance(file_path, str):
            if normalized(file_path) in allowed:
                kind = "target_read"
        if kind:
            evidence.append({"kind": kind, "tool": call["tool"], "input": inputs,
                             "tool_use_id": call["tool_use_id"], "event": call["event"]})
    return evidence


def detect_triggered(client: str, raw: str, skill_name: str,
                     skill_path: str | os.PathLike | None = None) -> bool:
    """Compatibility boolean wrapper around structured loading evidence."""
    return bool(trigger_evidence(client, raw, skill_name, skill_path))


def _partial_text(e: subprocess.TimeoutExpired) -> str:
    """Best-effort text of whatever the timed-out process had emitted so far.

    `run_client` (skill_utils) attaches the partial capture to the TimeoutExpired it
    raises. Fields are str in text mode; decode defensively for bytes.
    """
    chunks = []
    for chunk in (e.stdout, e.stderr):
        if chunk is None:
            continue
        chunks.append(chunk.decode("utf-8", "replace") if isinstance(chunk, bytes) else chunk)
    return "".join(chunks)


def run_cli(query: str, skill_name: str, description: str, client: str, timeout: int = 60,
            model: str = "", workspace: str | os.PathLike | None = None,
            evidence: dict | None = None, skill_path: str | os.PathLike | None = None) -> bool:
    """Run one query via the client's headless CLI; return whether it triggered.

    Raises RuntimeError when the CLI cannot be run or fails — such run_error
    cases are surfaced separately and must not be counted as "did not trigger"
    (see SKILL.md stage 7 attribution).

    A timeout is different: the skill tool may already have fired before the
    client got stuck on the (often long) task the skill kicked off. Discarding
    that partial stream would silently convert a real trigger into a run_error
    and systematically under-count recall, so a timeout that already shows the
    skill dispatch is a trigger; a timeout with no trigger evidence stays a
    run_error.

    `workspace` is the cwd for the client process. Callers pass a throwaway
    workspace (see `build_workspace`) to separate default file writes;
    when omitted the client inherits the current directory.
    """
    if client not in CLI_COMMANDS:
        raise RuntimeError(f"--mode cli not available for client '{client}'; use --mode heuristic")
    cmd = CLI_COMMANDS[client](query, model)
    if skill_path is None and workspace is not None:
        skill_path = Path(workspace) / SKILL_SUBPATHS[client] / skill_name / "SKILL.md"

    def detect(output, timed_out=False):
        found = trigger_evidence(client, output, skill_name, skill_path)
        if evidence is not None:
            evidence.update({"triggered": bool(found), "evidence": found,
                             "timed_out": timed_out, "signal": "structured_tool_events"})
        return bool(found)

    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    try:
        returncode, out, err = run_client(
            cmd, timeout=timeout, env=env,
            cwd=str(workspace) if workspace is not None else None,
        )
    except subprocess.TimeoutExpired as e:
        if detect(_partial_text(e), timed_out=True):
            return True
        raise RuntimeError(f"cli timeout after {timeout}s ({client})") from e
    except FileNotFoundError as e:
        raise RuntimeError(f"cli not found: {cmd[0]} ({client})") from e
    output = (out or "") + (err or "")
    found = detect(output)
    if returncode != 0:
        raise RuntimeError(f"cli exited {returncode} ({client}): {(err or '')[-300:]}")
    # A successful process with an unrecognized/plain stream cannot establish a
    # negative trigger result. Keep protocol failure separate from a real miss.
    parsed = events(output)
    recognized = {"assistant", "result", "stream_event"} if client == "claude" else {
        "text", "tool_use", "tool", "step_start", "step_finish"}
    if not any(ev.get("type") in recognized for ev in parsed):
        raise RuntimeError(f"cli emitted no supported structured events ({client})")
    error = execution_error(output, client)
    if error:
        raise RuntimeError(error)
    return found


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


def run_cli_item(item: dict, skill_name: str, description: str, client: str,
                 timeout: int, model: str, runs_per_query: int, threshold: float,
                 workspace: str | os.PathLike | None = None,
                 skill_path: str | os.PathLike | None = None) -> dict:
    """Run one eval query (possibly N times) and return its result record.

    Module-level and side-effect-free over shared state so it is safe to call
    from a ThreadPoolExecutor worker. RuntimeError (missing CLI / timeout /
    non-zero exit) becomes an `error` record — a run_error, never a silent miss.
    """
    query = eval_query(item)
    should = bool(item.get("should_trigger"))
    attempts = []
    try:
        triggers = 0
        for _ in range(max(1, runs_per_query)):
            attempt = {}
            attempts.append(attempt)
            if run_cli(query, skill_name, description, client, timeout=timeout, model=model,
                       workspace=workspace, evidence=attempt, skill_path=skill_path):
                triggers += 1
        rate = triggers / max(1, runs_per_query)
    except RuntimeError as e:
        return {
            "query": query,
            "should_trigger": should,
            "trigger_rate": None,
            "pass": None,
            "error": str(e),
            "trigger_evidence": attempts,
        }
    return {
        "query": query,
        "should_trigger": should,
        "trigger_rate": rate,
        "pass": (rate >= threshold) if should else (rate < threshold),
        "trigger_evidence": attempts,
    }


def run_cli_batch(evals, skill_name: str, description: str, client: str, timeout: int,
                  model: str, runs_per_query: int, threshold: float,
                  concurrency: int = 1, skill_dir: str | os.PathLike | None = None,
                  keep_workspace: bool = False) -> list[dict]:
    """Run every eval query through the client CLI, in result order.

    Each query is an independent client process and each may take tens of
    seconds, so a full real-machine run is serial-bound by default. Bounded
    concurrency cuts wall time without touching result shape or ordering
    (ThreadPoolExecutor.map preserves input order).

    When `skill_dir` is given, every query gets its OWN throwaway workspace (skill
    installed at the client discovery path, used as cwd, deleted afterwards).
    Per-query isolation — not one shared dir — is required because concurrent
    queries would otherwise write to the same cwd. `keep_workspace` disables the
    cleanup for debugging.
    """
    base_kwargs = dict(skill_name=skill_name, description=description, client=client,
                       timeout=timeout, model=model, runs_per_query=runs_per_query,
                       threshold=threshold)

    def _one(item: dict) -> dict:
        workspace = None
        try:
            if skill_dir is not None:
                workspace = build_workspace(Path(skill_dir), client)
                set_workspace_description(workspace, Path(skill_dir), client, description)
            installed = (workspace / SKILL_SUBPATHS[client] / Path(skill_dir).resolve().name / "SKILL.md"
                         if workspace is not None else None)
            return run_cli_item(item, workspace=workspace, skill_path=installed, **base_kwargs)
        except (OSError, ValueError) as e:
            return {"query": eval_query(item), "should_trigger": item["should_trigger"],
                    "pass": None, "error": f"workspace preparation failed: {e}"}
        finally:
            if workspace is not None:
                if keep_workspace:
                    print(f"kept workspace: {workspace}", file=sys.stderr)
                else:
                    shutil.rmtree(workspace, ignore_errors=True)

    workers = max(1, concurrency)
    if workers == 1 or len(evals) <= 1:
        return [_one(item) for item in evals]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(_one, evals))


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
    precision = tp / (tp + fp) if (tp + fp) else None
    recall = tp / (tp + fn) if (tp + fn) else None
    return {
        "passed": passed,
        "failed": len(scored) - passed,
        "errors": errors,
        "total": total,
        "attempted": len(results),
        "coverage": round(total / len(results), 3) if results else 0.0,
        "precision": round(precision, 3) if precision is not None else None,
        "recall": round(recall, 3) if recall is not None else None,
    }


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to evals.json")
    parser.add_argument("--skill-dir", required=True, help="Path to skill directory containing SKILL.md")
    parser.add_argument("--mode", choices=["heuristic", "cli"], default="heuristic",
                        help="heuristic=offline lexical-coverage proxy (词面覆盖代理指标, "
                             "default), cli=headless client CLI real-dispatch signal")
    parser.add_argument("--client", default="claude", choices=sorted(CLI_COMMANDS),
                        help="CLI client for --mode cli")
    parser.add_argument("--model", default="",
                        help="Model id passed to the client CLI (--model/-m); required when the "
                             "client default model is unset/misconfigured")
    parser.add_argument("--runs-per-query", type=int, default=1, help="Runs per query (cli mode)")
    parser.add_argument("--threshold", type=float, default=0.5, help="Trigger rate threshold (cli mode)")
    parser.add_argument("--timeout", type=int, default=60, help="Per-query CLI timeout in seconds (cli mode)")
    parser.add_argument("--concurrency", type=int, default=1,
                        help="Eval queries to run in parallel in cli mode (default 1 = serial). "
                             "Each query is an independent client process; raise it to cut wall time.")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("--output-dir", default=None,
                        help="Write results JSON (eval-results-<skill>.json) into this directory")
    parser.add_argument("--keep-workspace", action="store_true",
                        help="Keep the throwaway cli workspace (for debugging); default deletes it")
    parser.add_argument("--fail-on-error", action="store_true",
                        help="Exit 1 after reporting if any query could not be evaluated")
    parser.add_argument("--fail-on-mismatch", action="store_true",
                        help="Exit 1 after reporting if a scored query has the wrong trigger result")
    args = parser.parse_args()

    if (args.runs_per_query < 1 or args.concurrency < 1 or args.timeout < 1
            or not math.isfinite(args.threshold) or not 0 < args.threshold <= 1):
        print("Error: runs/concurrency/timeout must be positive; threshold must be in (0, 1]", file=sys.stderr)
        return 1

    eval_set_path = Path(args.eval_set)
    skill_dir = Path(args.skill_dir)
    if not eval_set_path.exists():
        print(f"Error: eval set not found: {eval_set_path}", file=sys.stderr)
        return 1
    if not (skill_dir / "SKILL.md").exists():
        print(f"Error: no SKILL.md at {skill_dir}", file=sys.stderr)
        return 1

    try:
        eval_list = load_eval_set(eval_set_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    try:
        name, description, _ = parse_skill_md(skill_dir)
    except (ValueError, OSError) as e:
        print(f"Error: cannot read SKILL.md at {skill_dir}: {e}", file=sys.stderr)
        return 1

    results = []
    if args.mode == "heuristic":
        results = run_heuristic(eval_list, description)
    else:
        # Each query runs in its own throwaway install: a real trigger executes the
        # skill, which would otherwise create files in (and spawn processes from)
        # the caller's repository, and concurrent queries would share a cwd.
        results = run_cli_batch(
            eval_list, name, description, args.client, args.timeout, args.model,
            args.runs_per_query, args.threshold, args.concurrency,
            skill_dir=skill_dir, keep_workspace=args.keep_workspace,
        )

    output = {
        "skill_name": name,
        "description": description,
        "mode": args.mode,
        "trigger_signal": "structured_tool_events" if args.mode == "cli" else "lexical_proxy",
        "client": args.client if args.mode == "cli" else None,
        "model": args.model if args.mode == "cli" else None,
        "threshold": args.threshold,
        "runs_per_query": args.runs_per_query if args.mode == "cli" else 1,
        "results": results,
        "summary": summarize(results, threshold=args.threshold),
    }
    if args.output_dir:
        out_dir = Path(args.output_dir)
        if out_dir.exists() and not out_dir.is_dir():
            print(f"Error: --output-dir is not a directory: {out_dir}", file=sys.stderr)
            return 1
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / f"eval-results-{name}.json"
            out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as e:
            print(f"Error: cannot write results: {e}", file=sys.stderr)
            return 1
        print(f"Results written to: {out_path}", file=sys.stderr)
    if args.json:
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        s = output["summary"]
        precision = f"{s['precision']:.0%}" if s['precision'] is not None else "N/A"
        recall = f"{s['recall']:.0%}" if s['recall'] is not None else "N/A"
        print(f"Evaluating: {name} ({args.mode} mode)  —  {s['passed']}/{s['total']} passed, "
              f"precision={precision} recall={recall} coverage={s['coverage']:.0%}"
              + (f", {s['errors']} run errors" if s["errors"] else ""))
        for r in results:
            if r.get("error"):
                print(f"  [ERROR] :: {r['query'][:70]} — {r['error']}")
                continue
            status = "PASS" if r["pass"] else "FAIL"
            expected = "Y" if r["should_trigger"] else "N"
            print(f"  [{status}] expect={expected} :: {r['query'][:70]}")
    summary = output["summary"]
    return int((args.fail_on_error and summary["errors"] > 0)
               or (args.fail_on_mismatch and summary["failed"] > 0))


if __name__ == "__main__":
    sys.exit(main())
