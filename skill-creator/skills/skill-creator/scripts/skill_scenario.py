#!/usr/bin/env python3
"""Run one eval scenario via a client CLI and record a benchmark-ready run directory.

Closes the gap in the quantitative loop: `skill_benchmark.py` can read a
workspace layout, but nothing produced one. This executor runs a real task
prompt with the skill available (`--skill-dir`) or without it, and writes the
per-run artifacts the grader / aggregator expect:

    <run-dir>/
    ├── transcript.md      # prompt + raw client output
    ├── outputs/
    │   ├── response.txt   # extracted assistant text
    │   └── artifacts/     # generated files with workspace-relative paths
    ├── artifacts.json     # retained files, hashes, exclusions, collection errors
    ├── metrics.json       # execution status, usage when available, provenance
    └── timing.json        # total_duration_seconds

metrics.json lives in the run-dir root (sibling of timing.json / grading.json).
The grader merges it into grading.json execution_metrics, and
skill_benchmark.py reads it directly as a fallback.

The skill (when given) is copied into a throwaway client workspace, so the
"without_skill" run never sees it. `--client-cmd` overrides the invoked command
for clients whose CLI differs or for testing; `{prompt}` is substituted.
Inputs are copied with --input-dir into inputs/; --output-dir names a relative
workspace directory (default outputs/). Generated cwd files are retained too.
Run directories must be empty, so prior grading cannot leak into another run.

Usage:
    python scripts/skill_scenario.py --client opencode --prompt "<task>" \
        --run-dir <workspace>/iteration-1/eval-x/with_skill/run-1 \
        [--skill-dir <skill>] [--model M] [--timeout 300] [--keep]

Exit code 0 = run recorded; 1 = error.
"""

import argparse
import hashlib
import json
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from skill_events import assistant_text, execution_error, stream_metrics, tool_calls
from skill_utils import run_client

SCRIPT_DIR = Path(__file__).resolve().parent

# client -> (workspace subpath for a skill, argv builder).
# --model is appended only when given: a machine whose client default model is
# unset/misconfigured needs it, otherwise every scenario run fails.
CLIENTS = {
    "opencode": (
        ".opencode/skills",
        lambda prompt, model: ["opencode", "run", "--format", "json"] + (["-m", model] if model else []) + [prompt],
    ),
    "claude": (
        ".claude/skills",
        lambda prompt, model: ["claude", "-p", "--output-format", "stream-json", "--verbose",
                               "--include-partial-messages"] + (["--model", model] if model else []) + [prompt],
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


def extract_text(raw: str) -> str:
    """Extract assistant text from opencode or Claude; plain overrides still work."""
    return assistant_text(raw)


def count_tool_calls(raw: str) -> int:
    """Count tool invocations in a client's JSON event stream.

    Parses each JSON line instead of substring-counting a serialized key, so the
    count is independent of the client's whitespace/formatting. opencode emits
    tool events as `{"type":"tool_use","part":{"type":"tool",...}}`; accept both
    that and a top-level `type == "tool"` (older/simplified streams). Claude
    partial/final events are deduplicated. This compatibility helper returns 0
    for plain output; metrics.json records unavailable stream metrics as null.
    """
    return len(tool_calls(raw))


def _split_override(override: str) -> list[str]:
    """Split a --client-cmd template, preserving Windows paths.

    POSIX shlex eats backslashes (`C:\\x` → `C:x`) and, in non-posix mode, keeps
    the surrounding quotes as literal characters — either breaks the command. Use
    platform-appropriate splitting and strip the quotes non-posix mode retains.
    """
    try:
        if os.name == "nt":
            parts = shlex.split(override, posix=False)
            parts = [
                p[1:-1] if len(p) >= 2 and p[0] == p[-1] and p[0] in "\"'" else p
                for p in parts
            ]
            return parts
        return shlex.split(override, posix=True)
    except ValueError as e:
        raise RuntimeError(f"--client-cmd is not parseable: {e}") from e


def build_command(client: str, prompt: str, model: str, override: str | None) -> list[str]:
    if override:
        parts = _split_override(override)
        if not parts:
            raise RuntimeError("--client-cmd is empty")
        return [p.replace("{prompt}", prompt).replace("{model}", model) for p in parts]
    if client not in CLIENTS:
        raise RuntimeError(f"unknown client '{client}'")
    return CLIENTS[client][1](prompt, model)


def _linked(path: Path) -> bool:
    """Include Windows junctions/reparse points; os.walk must not traverse them."""
    info = path.lstat()
    return path.is_symlink() or bool(getattr(info, "st_file_attributes", 0)
                                    & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _copy_inputs(source: Path, destination: Path) -> None:
    """Copy declared fixture files without following links out of the input tree."""
    if _linked(source) or not source.is_dir():
        raise ValueError("--input-dir must be an ordinary directory")
    source = source.resolve()
    for directory, dirs, files in os.walk(source, followlinks=False):
        root = Path(directory)
        for name in dirs + files:
            path = root / name
            if _linked(path):
                raise ValueError(f"linked input is not supported: {path.relative_to(source)}")
        target = destination / root.relative_to(source)
        target.mkdir(parents=True, exist_ok=True)
        for name in files:
            path = root / name
            if not stat.S_ISREG(path.stat().st_mode):
                raise ValueError(f"input is not a regular file: {path.relative_to(source)}")
            shutil.copy2(path, target / name)


def collect_artifacts(workspace: Path, run_dir: Path, initial_files: set[str],
                      output_dir: Path) -> dict:
    """Preserve new regular files, excluding inputs, client config, and links.

    Keep source-relative paths under outputs/artifacts to avoid colliding with
    the executor's response.txt. Hidden top-level folders are client metadata
    unless explicitly chosen as outputs (the CLI disallows that ambiguity).
    """
    manifest = {"schema_version": 1, "output_dir": output_dir.as_posix(),
                "files": [], "skipped": [], "errors": []}
    workspace = workspace.resolve()

    def skip(relative, reason):
        manifest["skipped"].append({"source_path": relative, "reason": reason})

    def walk_error(error):
        manifest["errors"].append(str(error))

    for directory, dirs, files in os.walk(workspace, followlinks=False, onerror=walk_error):
        root = Path(directory)
        for name in list(dirs):
            path = root / name
            relative = path.relative_to(workspace)
            try:
                if _linked(path):
                    dirs.remove(name)
                    skip(relative.as_posix(), "link_or_reparse_point")
                elif relative.parts[0] == "inputs" or relative.parts[0].startswith(".") \
                        or name in ("__pycache__", "node_modules"):
                    dirs.remove(name)
                    skip(relative.as_posix(), "input_or_runtime_metadata")
            except OSError as error:
                dirs.remove(name)
                manifest["errors"].append(f"{relative}: {error}")
        for name in files:
            path = root / name
            relative = path.relative_to(workspace)
            key = relative.as_posix()
            try:
                if _linked(path) or not path.resolve().is_relative_to(workspace):
                    skip(key, "link_or_reparse_point")
                    continue
                if (key in initial_files or relative.parts[0].startswith(".")
                        or key in ("opencode.json", "opencode.jsonc", "CLAUDE.md")):
                    skip(key, "input_or_runtime_metadata")
                    continue
                if not stat.S_ISREG(path.stat().st_mode):
                    skip(key, "not_regular_file")
                    continue
                target = run_dir / "outputs" / "artifacts" / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                digest = hashlib.sha256()
                size = 0
                with path.open("rb") as source, target.open("xb") as destination:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        destination.write(chunk)
                        digest.update(chunk)
                        size += len(chunk)
                manifest["files"].append({"source_path": key,
                    "path": target.relative_to(run_dir).as_posix(), "bytes": size,
                    "sha256": digest.hexdigest(),
                    "declared_output": relative.is_relative_to(output_dir)})
            except OSError as error:
                manifest["errors"].append(f"{key}: {error}")
    manifest["files"].sort(key=lambda item: item["source_path"])
    return manifest


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Run one eval scenario and record a run directory")
    parser.add_argument("--client", default="opencode", choices=sorted(CLIENTS))
    parser.add_argument("--prompt", required=True, help="The task prompt for this scenario")
    parser.add_argument("--run-dir", required=True, type=Path, help="Where to write the run artifacts")
    parser.add_argument("--input-dir", type=Path,
                        help="Fixture directory copied to the temporary workspace inputs/")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"),
                        help="Relative output directory inside the temporary workspace (default outputs)")
    parser.add_argument("--skill-dir", type=Path, default=None,
                        help="Skill to install for this run (omit for the without_skill baseline)")
    parser.add_argument("--model", default="", help="Optional model id passed to the client")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--client-cmd", default=None,
                        help="Override command; {prompt}/{model} substituted (for testing)")
    parser.add_argument("--keep", action="store_true", help="Keep the throwaway workspace")
    args = parser.parse_args()

    if args.timeout < 1:
        print("Error: --timeout must be positive", file=sys.stderr)
        return 1
    output_dir = args.output_dir
    if (output_dir.is_absolute() or output_dir.drive or output_dir.root
            or not output_dir.parts or ".." in output_dir.parts
            or output_dir.parts[0].startswith(".")
            or output_dir.parts[0] == "inputs"
            or {"__pycache__", "node_modules"}.intersection(output_dir.parts)):
        print("Error: --output-dir must be a relative workspace directory outside inputs/config", file=sys.stderr)
        return 1
    run_dir = args.run_dir.absolute()
    try:
        if run_dir.exists() and (not run_dir.is_dir() or _linked(run_dir)):
            raise ValueError(f"--run-dir is not an ordinary directory: {run_dir}")
        if run_dir.exists() and any(run_dir.iterdir()):
            raise ValueError("--run-dir must be empty; use a new run directory to avoid stale grading/artifacts")
        run_dir.mkdir(parents=True, exist_ok=True)
    except (OSError, ValueError) as e:
        print(f"Error: cannot create --run-dir: {e}", file=sys.stderr)
        return 1

    skill_name = None
    tmp = Path(tempfile.mkdtemp(prefix="scenario-"))
    timed_out = False
    returncode = -1
    duration = 0.0
    raw = ""
    error = None
    initial_files = set()
    manifest = {"schema_version": 1, "files": [], "skipped": [], "errors": []}
    effective_prompt = (args.prompt + "\n\n[Scenario files]\n"
                        "Declared input files are in inputs/ (read-only fixtures). "
                        f"Write deliverables under {output_dir.as_posix()}/. "
                        "The executor will retain deliverables after the run.")
    try:
        (tmp / "inputs").mkdir()
        (tmp / output_dir).mkdir(parents=True)
        if args.input_dir:
            _copy_inputs(args.input_dir, tmp / "inputs")
        if args.skill_dir:
            if not (args.skill_dir / "SKILL.md").exists():
                raise ValueError(f"no SKILL.md at {args.skill_dir}")
            skill_name = args.skill_dir.resolve().name
            rel = CLIENTS[args.client][0]
            dest = tmp / rel / skill_name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(args.skill_dir, dest)

        try:
            cmd = build_command(args.client, effective_prompt, args.model, args.client_cmd)
        except RuntimeError as e:
            # A bad/empty --client-cmd is still a run attempt: record it (the
            # benchmark contract says every run dir carries artifacts) instead of
            # returning with an empty directory.
            print(f"Error: {e}", file=sys.stderr)
            raw = f"[client command error: {e}]"
            error = str(e)
            returncode = -1
            duration = 0.0
            text = raw
        else:
            env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
            env.update({"SCENARIO_INPUT_DIR": str(tmp / "inputs"),
                        "SCENARIO_OUTPUT_DIR": str(tmp / output_dir)})
            print(f"▶ [{args.client}] skill={skill_name or '(none)'} :: {args.prompt[:60]}", file=sys.stderr)
            start = time.time()
            try:
                returncode, out, err = run_client(cmd, timeout=args.timeout, cwd=str(tmp), env=env)
                raw = (out or "") + (err or "")
                if returncode != 0:
                    error = f"client exited {returncode}"
            except subprocess.TimeoutExpired as te:
                # Record the partial output and mark the run — a timed-out scenario must
                # still land in the benchmark layout, not vanish (skill_benchmark
                # expects every run dir to carry artifacts).
                timed_out = True
                error = f"client timed out after {args.timeout}s"
                returncode = -1
                partial = []
                for chunk in (te.stdout, te.stderr):
                    if chunk:
                        partial.append(chunk.decode("utf-8", "replace") if isinstance(chunk, bytes) else chunk)
                raw = "".join(partial)
                print(f"Error: client timed out after {args.timeout}s — artifacts recorded", file=sys.stderr)
            except FileNotFoundError:
                # Same contract: a missing client binary is a recorded failed run.
                print(f"Error: command not found: {cmd[0]} — artifacts recorded", file=sys.stderr)
                returncode = -1
                raw = f"[command not found: {cmd[0]}]"
                error = f"command not found: {cmd[0]}"
            duration = round(time.time() - start, 3)
            text = extract_text(raw)
    except (OSError, ValueError) as e:
        error = str(e)
        raw += f"\n[scenario error: {e}]"
    finally:
        manifest = collect_artifacts(tmp, run_dir, initial_files, output_dir)
        if args.keep:
            print(f"kept workspace: {tmp}", file=sys.stderr)
        else:
            shutil.rmtree(tmp, ignore_errors=True)

    text = extract_text(raw)
    error = error or execution_error(raw, args.client)
    if manifest["errors"]:
        error = error or "artifact collection failed"
    metrics = stream_metrics(raw, args.client)
    (run_dir / "outputs").mkdir(exist_ok=True)
    (run_dir / "outputs" / "response.txt").write_text(text, encoding="utf-8")
    (run_dir / "transcript.md").write_text(
        f"# Scenario run\n\n**Client**: {args.client}\n**Skill**: {skill_name or '(none)'}\n"
        f"**Timestamp**: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        f"**Timed out**: {timed_out}\n\n"
        f"## Prompt\n\n{effective_prompt}\n\n## Raw output\n\n```\n{raw}\n```\n",
        encoding="utf-8",
    )
    (run_dir / "timing.json").write_text(
        json.dumps({"total_duration_seconds": duration, "timed_out": timed_out}, indent=2),
        encoding="utf-8")
    (run_dir / "metrics.json").write_text(
        json.dumps({
            "client": args.client,
            **metrics,
            "model": metrics["model"] if metrics["models"] else args.model or None,
            "model_source": "client_stream" if metrics["models"] else "requested" if args.model else None,
            "requested_model": args.model or None,
            "skill": skill_name,
            "returncode": returncode,
            "timed_out": timed_out,
            "output_chars": len(raw),
            "status": "error" if error else "completed",
            "error": error,
            "artifact_count": len(manifest["files"]),
            "artifact_collection_errors": len(manifest["errors"]),
        }, indent=2), encoding="utf-8")
    (run_dir / "artifacts.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"✅ wrote run artifacts to {run_dir} ({duration}s, rc={returncode})", file=sys.stderr)
    if error or timed_out or returncode != 0:
        print("Error: run marked as error — artifacts recorded", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
