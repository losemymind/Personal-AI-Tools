"""Repository-only live agent-creator evaluation; never synthesizes model responses.

Each phase may be recorded once per attempt. Credentials remain in child process
environment, and all captured text is redacted before it reaches the evidence tree.
Home-directory isolation is a discovery boundary, not an operating-system sandbox.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import zipfile


HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
PRODUCT = REPO / "agent-creator/skills/agent-creator"
SUPPORT = REPO / "skill-creator/skills/skill-creator/scripts"
sys.path.insert(0, str(SUPPORT))
from skill_events import execution_error, stream_metrics, tool_calls
from skill_utils import run_client

EXE = Path("C:/Users/Administrator/AppData/Local/Programs/@openworkdesktop/resources/sidecars/opencode.exe")
MODEL = "deepseek/deepseek-flash"
BASELINE = "f68cfc8"
NAME = "agent-creator"
TRIGGER_TIMEOUT, SCENARIO_TIMEOUT = 90, 360
TRIGGER_STEPS, SCENARIO_STEPS = 8, 32
IGNORE = shutil.ignore_patterns("__pycache__", ".pytest_cache", "*.pyc", "*.pyo")
SECRETS: tuple[str, ...] = ()


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def redact(text):
    value = str(text)
    for secret in SECRETS:
        value = value.replace(secret, "[REDACTED]")
    return value


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(redact(json.dumps(value, ensure_ascii=False, indent=2)) + "\n", encoding="utf-8")


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, bytes):
        value = value.decode("utf-8", "replace")
    path.write_text(redact(value or ""), encoding="utf-8")


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def hashes(root):
    root = Path(root)
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file()
            and not {"__pycache__", ".pytest_cache"}.intersection(p.parts)
            and p.suffix not in (".pyc", ".pyo")}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def set_secrets(provider, source_env):
    """Read only selected-provider values and its declared environment references."""
    global SECRETS
    found = set()

    def visit(value, key=""):
        if isinstance(value, dict):
            for child_key, child in value.items():
                visit(child, child_key)
        elif isinstance(value, list):
            for child in value:
                visit(child, key)
        elif isinstance(value, str):
            if "{file:" in value:
                raise ValueError("Selected provider uses a file reference; environment-only credentials are required")
            references = re.findall(r"\{env:([^}]+)\}", value)
            for name in references:
                resolved = source_env.get(name)
                if not resolved:
                    raise ValueError("A selected-provider environment reference is unavailable")
                found.add(resolved)
            if not references and re.search(r"key|token|secret|password|authorization", key, re.I) and value:
                found.add(value)

    visit(provider)
    SECRETS = tuple(sorted(found, key=len, reverse=True))


def selected_provider():
    path = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".config/opencode/opencode.json"
    config = load(path)
    provider = config.get("provider", {}).get("deepseek")
    if not isinstance(provider, dict):
        raise ValueError("Selected deepseek provider is not configured")
    set_secrets(provider, os.environ)
    return provider


def environment(provider, steps):
    state = Path(tempfile.mkdtemp(prefix="agent-live-env-"))
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("OPENCODE_") and key != "CLAUDECODE"}
    for key, folder in {
        "XDG_CONFIG_HOME": "config", "XDG_DATA_HOME": "data",
        "XDG_STATE_HOME": "state", "XDG_CACHE_HOME": "cache",
        "USERPROFILE": "home", "HOME": "home",
        "APPDATA": "home/AppData/Roaming", "LOCALAPPDATA": "home/AppData/Local",
        "TEMP": "temp", "TMP": "temp",
    }.items():
        target = state / folder
        target.mkdir(parents=True, exist_ok=True)
        env[key] = str(target)
    public = {
        "model": MODEL, "small_model": MODEL, "share": "disabled", "autoupdate": False,
        "mcp": {}, "plugin": [], "agent": {"build": {"steps": steps}},
        "permission": {"*": "allow", "webfetch": "deny", "websearch": "deny",
                       "question": "deny", "task": "deny", "external_directory": "deny",
                       "skill": {"*": "deny", NAME: "allow", "customize-opencode": "deny"}},
    }
    env["OPENCODE_CONFIG_CONTENT"] = json.dumps({**public, "provider": {"deepseek": provider}})
    env["PYTHONUTF8"], env["PYTHONIOENCODING"] = "1", "utf-8"
    env["PATH"] = str(EXE.parent) + os.pathsep + env.get("PATH", "")
    return state, env, public


def command_evidence(path, command, cwd, timeout):
    save(path, {"argv": command, "cwd": str(cwd), "timeout_seconds": timeout,
                "environment": "isolated child; credentials omitted", "started_at": utc_now()})


def discovery(cwd, env, evidence, expected):
    """Check the exact installed entry before any model command is dispatched."""
    evidence = Path(evidence)
    command = [str(EXE), "--pure", "debug", "skill"]
    command_evidence(evidence / "discovery-invocation.json", command, cwd, 40)
    rc, stdout, stderr, error = None, "", "", None
    found = []
    try:
        rc, stdout, stderr = run_client(command, timeout=40, cwd=str(cwd), env=env)
        if rc != 0:
            raise ValueError(f"Skill discovery exited {rc}")
        parsed = json.loads(stdout)
        if not isinstance(parsed, list):
            raise ValueError("Skill discovery did not return an array")
        found = [{key: item.get(key) for key in ("name", "description", "location")}
                 for item in parsed if isinstance(item, dict)]
        target = [item for item in found if item["name"] == NAME]
        if expected is None:
            if target:
                raise ValueError("Target skill is visible in a without-skill workspace")
        elif len(target) != 1 or Path(str(target[0]["location"])).resolve() != Path(expected).resolve():
            raise ValueError("Target discovery does not match the exact isolated SKILL.md")
        for item in found:
            if item["name"] == NAME:
                continue
            if item["name"] == "customize-opencode" and item["location"] == "<built-in>":
                continue
            raise ValueError("Unexpected skill visible in isolated discovery")
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or "", exc.stderr or ""
        error = "Skill discovery timed out"
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        write(evidence / "discovery.stdout.txt", stdout)
        write(evidence / "discovery.stderr.txt", stderr)
        save(evidence / "discovery.json", found)
        save(evidence / "discovery-check.json", {"valid": error is None, "error": error,
             "returncode": rc, "expected_skill_path": str(expected) if expected else None})
    if error:
        raise ValueError(error)
    return found


def observed_models(state, destination):
    """Only assistant message metadata is queried; never account/auth tables."""
    database = Path(state) / "data/opencode/opencode.db"
    evidence = {"source": "opencode_local_session_metadata", "models": [], "messages": [],
                "billing": "unknown; client cost=0 is not a billing statement", "error": None}
    try:
        if not database.is_file():
            raise ValueError("No local session database was created")
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5) as connection:
            for mid, sid, data in connection.execute("SELECT id, session_id, data FROM message"):
                message = json.loads(data)
                if message.get("role") == "assistant":
                    evidence["messages"].append({"message_id": mid, "session_id": sid,
                        "provider": message.get("providerID"), "model": message.get("modelID"),
                        "finish": message.get("finish")})
        evidence["models"] = sorted({f"{item['provider']}/{item['model']}"
                                     for item in evidence["messages"] if item["provider"] and item["model"]})
    except Exception as exc:
        evidence["error"] = f"{type(exc).__name__}: {exc}"
    save(destination, evidence)
    return evidence


def loading_signals(raw, workspace):
    expected = (Path(workspace) / ".opencode/skills" / NAME / "SKILL.md").resolve()
    dispatch, target_read = [], []
    for call in tool_calls(raw, "opencode"):
        # In-flight and failed calls are not completed loading evidence.
        if call.get("status") != "completed":
            continue
        inputs = call["input"]
        evidence = {"tool": call["tool"], "input": inputs,
                    "tool_use_id": call["tool_use_id"], "status": call["status"]}
        if call["tool"] == "skill" and inputs.get("name") == NAME:
            dispatch.append(evidence)
        if call["tool"] == "read" and isinstance(inputs.get("filePath"), str):
            path = Path(inputs["filePath"])
            if not path.is_absolute():
                path = Path(workspace) / path
            if path.resolve() == expected:
                target_read.append(evidence)
    return {"dispatch": bool(dispatch), "target_read": bool(target_read),
            "combined": bool(dispatch or target_read), "combined_rule": "dispatch OR target_read",
            "dispatch_evidence": dispatch, "target_read_evidence": target_read,
            "target_skill_path": str(expected)}


def input_integrity(source, workspace, before):
    current = hashes(source)
    after = hashes(Path(workspace) / "inputs") if workspace else None
    return {"source_path": str(source), "source_before": before, "source": current,
            "after": after, "source_unchanged": before == current,
            "unchanged": after is not None and before == after and before == current}


def runtime_metadata(state, public):
    return {"state_root": str(state), "isolated_user_directories": True,
            "public_config": public, "credential_storage": "child environment only",
            "limitations": "Discovery/home isolation is not an operating-system sandbox"}


def command_run(run, workspace, env, state, prompt, timeout):
    command = [str(EXE), "--pure", "run", "--format", "json", "-m", MODEL, prompt]
    command_evidence(run / "invocation.json", command, workspace, timeout)
    started, rc, stdout, stderr, timed_out, error = time.monotonic(), None, "", "", False, None
    try:
        rc, stdout, stderr = run_client(command, timeout=timeout, cwd=str(workspace), env=env)
        if rc != 0:
            error = f"client exited {rc}"
        error = error or execution_error(stdout + stderr, "opencode")
    except subprocess.TimeoutExpired as exc:
        timed_out, error = True, f"client timed out after {timeout}s"
        stdout, stderr = exc.stdout or "", exc.stderr or ""
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", "replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", "replace")
    write(run / "stdout.jsonl", stdout)
    write(run / "stderr.txt", stderr)
    observed = observed_models(state, run / "observed-models.json")
    metrics = {"client": "opencode", **stream_metrics(stdout + stderr, "opencode"),
               "requested_model": MODEL, "model_source": "client_stream", "returncode": rc,
               "timed_out": timed_out, "status": "error" if error else "completed", "error": error,
               "duration_seconds": round(time.monotonic() - started, 3)}
    if observed["models"]:
        metrics.update(models=observed["models"], model=observed["models"][0] if len(observed["models"]) == 1 else None,
                       model_source="opencode_local_session_metadata")
    elif not metrics["models"]:
        metrics["model_source"] = None
    save(run / "execution.json", metrics)
    return rc, redact(stdout), redact(stderr), metrics


def fixture_path(item, default=None):
    relative = item.get("input_dir", default)
    if not isinstance(relative, str):
        raise ValueError("input_dir must be a fixture-relative path")
    source = (HERE / relative).resolve()
    if not source.is_relative_to((HERE / "fixtures").resolve()) or not source.is_dir():
        raise ValueError("input_dir must select an existing directory below fixtures/")
    return source


def queries():
    items = load(HERE / "queries.json")
    if not isinstance(items, list) or len(items) != 8:
        raise ValueError("The frozen trigger protocol requires exactly eight queries")
    ids = set()
    for item in items:
        if (not isinstance(item, dict) or type(item.get("id")) is not int or item["id"] in ids
                or not isinstance(item.get("query"), str) or not item["query"].strip()
                or type(item.get("should_trigger")) is not bool):
            raise ValueError("Invalid or duplicate trigger query")
        ids.add(item["id"])
        fixture_path(item, "fixtures/trigger")
    return items


def scenario_items():
    items = load(HERE / "scenarios.json")
    if not isinstance(items, list) or len(items) != 2:
        raise ValueError("The frozen task protocol requires exactly two scenarios")
    names, ids = set(), set()
    for item in items:
        if (not isinstance(item, dict) or type(item.get("id")) is not int or item["id"] in ids
                or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", item.get("name", ""))
                or item["name"] in names or not isinstance(item.get("prompt"), str)
                or not isinstance(item.get("assertions"), list)
                or not all(isinstance(text, str) and text for text in item["assertions"])):
            raise ValueError("Invalid or duplicate scenario")
        names.add(item["name"])
        ids.add(item["id"])
        fixture_path(item)
    return items


def old_snapshot(root):
    prefix = "agent-creator/skills/agent-creator/"
    completed = subprocess.run(["git", "archive", "--format=zip", BASELINE, prefix],
                               cwd=REPO, capture_output=True, check=True)
    with zipfile.ZipFile(io.BytesIO(completed.stdout)) as archive:
        destination = (Path(root) / "baseline").resolve()
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if not target.is_relative_to(destination):
                raise ValueError("Unexpected baseline archive path")
        archive.extractall(destination)
    return destination / prefix


def install_workspace(root, source=None, inputs=None):
    workspace = Path(root)
    workspace.mkdir(parents=True, exist_ok=False)
    (workspace / "outputs").mkdir()
    if inputs:
        import skill_scenario
        skill_scenario._copy_inputs(inputs, workspace / "inputs")
    else:
        (workspace / "inputs").mkdir()
    if source:
        destination = workspace / ".opencode/skills" / NAME
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, destination, ignore=IGNORE)
    return workspace


def trigger(out, provider):
    def one(item):
        run = out / "trigger/raw" / f"query-{item['id']:02d}"
        run.mkdir(parents=True, exist_ok=False)
        state, env, public = environment(provider, TRIGGER_STEPS)
        source, workspace = fixture_path(item, "fixtures/trigger"), None
        before = hashes(source)
        save(run / "client-environment.json", runtime_metadata(state, public))
        result = {"id": item["id"], "query": item["query"], "should_trigger": item["should_trigger"],
                  "passed": False, "scorable": False, "dispatch": False, "target_read": False,
                  "combined": False, "status": "error", "error": None}
        try:
            workspace = install_workspace(state / "workspace", PRODUCT, source)
            save(run / "workspace.json", {"path": str(workspace), "kept": True})
            discovery(workspace, env, run, workspace / ".opencode/skills" / NAME / "SKILL.md")
            rc, stdout, stderr, metrics = command_run(run, workspace, env, state, item["query"], TRIGGER_TIMEOUT)
            signals = loading_signals(stdout + stderr, workspace)
            save(run / "signals.json", signals)
            save(run / "metrics.json", metrics)
            result.update(signals)
            result.update(status=metrics["status"], error=metrics["error"], timed_out=metrics["timed_out"],
                          returncode=rc, scorable=metrics["status"] == "completed")
            result["passed"] = result["scorable"] and result["combined"] == item["should_trigger"]
        except Exception as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
            save(run / "metrics.json", {"status": "error", "error": result["error"], "returncode": None,
                 "client": "opencode", "requested_model": MODEL, "model": None, "models": [],
                 "model_source": None, "total_tokens": None, "timed_out": False})
            write(run / "stdout.jsonl", "") if not (run / "stdout.jsonl").exists() else None
            write(run / "stderr.txt", result["error"])
        finally:
            save(run / "input-integrity.json", input_integrity(source, workspace, before))
            save(run / "result.json", result)
            save(run / "evidence-hashes.json", hashes(run))
        print(f"trigger query {item['id']}: {result['status']}, combined={result['combined']}", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(one, queries()))
    completed = [item for item in results if item["scorable"]]
    correct = sum(item["passed"] for item in results)
    report = {"schema_version": 1, "skill_name": NAME, "requested_model": MODEL,
              "signals": "successful structured dispatch OR read.filePath matching installed SKILL.md",
              "results": results, "summary": {"attempted": len(results), "completed": len(completed),
              "errors": len(results) - len(completed), "correct": correct,
              "accuracy_completed": correct / len(completed) if completed else None,
              "pass_rate_all_attempts": correct / len(results) if results else None}}
    save(out / "trigger/evaluation.json", report)
    return report["summary"]["errors"] == 0


def scenario_worker(job_path):
    """Internal subprocess bridge: retain the shared scenario executor's contract."""
    import skill_scenario
    job = load(job_path)
    config = json.loads(os.environ["OPENCODE_CONFIG_CONTENT"])
    set_secrets(config["provider"]["deepseek"], os.environ)
    run, source = Path(job["run_dir"]), Path(job["input_dir"])
    before, workspace = hashes(source), None

    def capture(command, **kwargs):
        nonlocal workspace
        workspace = Path(kwargs["cwd"])
        save(run / "workspace.json", {"path": str(workspace), "kept": True})
        save(run / "client-environment.json", runtime_metadata(job["state_root"], job["public_config"]))
        expected = workspace / ".opencode/skills" / NAME / "SKILL.md" if job["skill_dir"] else None
        discovery(workspace, kwargs["env"], run, expected)
        rc, stdout, stderr, metrics = command_run(run, workspace, kwargs["env"], job["state_root"],
                                                 command[-1], SCENARIO_TIMEOUT)
        if metrics["timed_out"]:
            raise subprocess.TimeoutExpired(command, SCENARIO_TIMEOUT, output=stdout, stderr=stderr)
        if metrics["error"] and rc in (0, None):
            rc = -1
        return rc if rc is not None else -1, stdout, stderr

    skill_scenario.run_client = capture
    sys.argv = [str(SUPPORT / "skill_scenario.py"), "--client", "opencode", "--model", MODEL,
                "--prompt", job["prompt"], "--input-dir", str(source), "--output-dir", "outputs",
                "--run-dir", str(run), "--timeout", str(SCENARIO_TIMEOUT), "--keep"]
    if job["skill_dir"]:
        sys.argv += ["--skill-dir", job["skill_dir"]]
    try:
        return skill_scenario.main()
    finally:
        save(run / "input-integrity.json", input_integrity(source, workspace, before))
        # The executor may lack model IDs in JSONL. Preserve its metrics and save
        # the independent observed-model evidence separately without overwriting it.
        observed_models(job["state_root"], run / "observed-models.json")


def scenarios(out, provider):
    old = old_snapshot(Path(tempfile.mkdtemp(prefix="agent-live-baseline-")))
    save(out / "old-product-hashes.json", hashes(old))
    versions = {"with_skill": PRODUCT, "old_skill": old, "without_skill": None}
    jobs = []
    for item in scenario_items():
        eval_dir = out / "iteration-1" / f"eval-{item['name']}"
        save(eval_dir / "eval_metadata.json", {"eval_id": item["id"], "eval_name": item["name"],
             "prompt": item["prompt"], "assertions": item["assertions"], "fixture_is_synthetic": True})
        order = ["old_skill", "without_skill", "with_skill"] if item["id"] % 2 else ["with_skill", "old_skill", "without_skill"]
        for variant in order:
            jobs.append((item, variant, versions[variant], eval_dir / variant / "run-1"))

    def one(job):
        item, variant, skill, run = job
        if run.exists():
            raise ValueError("Scenario run directory already exists")
        state, env, public = environment(provider, SCENARIO_STEPS)
        job_path = out / "scenario-jobs" / f"{item['name']}-{variant}.json"
        save(job_path, {"run_dir": str(run), "input_dir": str(fixture_path(item)), "prompt": item["prompt"],
             "skill_dir": str(skill) if skill else None, "state_root": str(state), "public_config": public})
        command = [sys.executable, "-X", "utf8", str(Path(__file__).resolve()), "--_scenario-worker", str(job_path)]
        command_evidence(out / "scenario-jobs" / f"{item['name']}-{variant}-invocation.json", command, state, SCENARIO_TIMEOUT + 120)
        rc, stdout, stderr, error = None, "", "", None
        try:
            rc, stdout, stderr = run_client(command, timeout=SCENARIO_TIMEOUT + 120, cwd=str(state), env=env)
            if rc != 0:
                error = f"Scenario executor exited {rc}"
        except subprocess.TimeoutExpired as exc:
            stdout, stderr, error = exc.stdout or "", exc.stderr or "", "Scenario executor watchdog timed out"
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        run.mkdir(parents=True, exist_ok=True)
        write(run / "executor.stdout.txt", stdout)
        write(run / "executor.stderr.txt", stderr)
        if not (run / "metrics.json").exists():
            error = error or "Scenario executor did not produce metrics"
            save(run / "metrics.json", {"status": "error", "error": error, "client": "opencode",
                 "requested_model": MODEL, "model": None, "models": [], "model_source": None,
                 "returncode": rc, "timed_out": "timed out" in error, "total_tokens": None})
        metrics = load(run / "metrics.json")
        if error and metrics.get("status") == "completed":
            save(run / "metrics-before-executor-error.json", metrics)
            metrics.update(status="error", error=error, executor_returncode=rc)
            save(run / "metrics.json", metrics)
        result = {"eval_id": item["id"], "config": variant, "returncode": rc,
                  "status": "error" if error or metrics.get("status") != "completed" else "completed",
                  "error": error or metrics.get("error")}
        save(run / "executor-status.json", result)
        save(run / "evidence-hashes.json", hashes(run))
        print(f"scenario {item['name']} / {variant}: {result['status']}", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(one, jobs))
    save(out / "scenario-execution.json", results)
    return all(result["status"] == "completed" for result in results)


def preflight(out, provider):
    queries()
    scenario_items()
    old = old_snapshot(Path(tempfile.mkdtemp(prefix="agent-preflight-baseline-")))
    save(out / "preflight/old-product-hashes.json", hashes(old))
    for variant, source in (("with_skill", PRODUCT), ("old_skill", old), ("without_skill", None)):
        state, env, public = environment(provider, SCENARIO_STEPS)
        evidence = out / "preflight" / variant
        save(evidence / "client-environment.json", runtime_metadata(state, public))
        workspace = install_workspace(state / "workspace", source)
        discovery(workspace, env, evidence, workspace / ".opencode/skills" / NAME / "SKILL.md" if source else None)
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase_pos", nargs="?", choices=("preflight", "trigger", "scenarios"))
    parser.add_argument("--phase", choices=("preflight", "trigger", "scenarios"))
    parser.add_argument("--out", type=Path, help="New attempt directory; each phase may run only once")
    parser.add_argument("--_scenario-worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args._scenario_worker:
        return scenario_worker(args._scenario_worker)
    phase = args.phase or args.phase_pos
    if not phase or not args.out or (args.phase and args.phase_pos and args.phase != args.phase_pos):
        parser.error("Specify one phase and --out <new-attempt-path>")
    out = args.out.resolve()
    target = out / {"preflight": "preflight", "trigger": "trigger", "scenarios": "iteration-1"}[phase]
    if target.exists() or (out / f"{phase}-status.json").exists():
        parser.error("Refusing to overwrite an existing phase; use a new attempt path")
    marker = out / "attempt.json"
    if out.exists() and any(out.iterdir()) and not marker.is_file():
        parser.error("Nonempty output directory is not an evaluation attempt")
    if marker.exists() and load(marker).get("runner") != str(Path(__file__).resolve()):
        parser.error("Output directory belongs to another runner")
    target.mkdir(parents=True, exist_ok=False)
    if not marker.exists():
        save(marker, {"schema_version": 1, "runner": str(Path(__file__).resolve()),
                      "baseline": BASELINE, "created_at": utc_now()})
    success, error = False, None
    try:
        provider = selected_provider()
        state, env, public = environment(provider, TRIGGER_STEPS if phase == "trigger" else SCENARIO_STEPS)
        rc, version, stderr = run_client([str(EXE), "--version"], timeout=30, cwd=str(state), env=env)
        write(out / f"{phase}-client-version.stdout.txt", version)
        write(out / f"{phase}-client-version.stderr.txt", stderr)
        if rc != 0:
            raise ValueError(f"Client version preflight exited {rc}")
        initial = discovery(state, env, out / f"{phase}-baseline-discovery", None)
        save(out / f"{phase}-environment.json", {**runtime_metadata(state, public), "started_at": utc_now(),
             "exe": str(EXE), "client_version": version.strip(), "requested_model": MODEL,
             "baseline_commit": BASELINE, "baseline_discovery": initial, "concurrency": 2,
             "trigger_timeout": TRIGGER_TIMEOUT, "scenario_timeout": SCENARIO_TIMEOUT,
             "trigger_steps": TRIGGER_STEPS, "scenario_steps": SCENARIO_STEPS,
             "query_sha256": digest(HERE / "queries.json"), "scenario_sha256": digest(HERE / "scenarios.json"),
             "protocol_sha256": digest(HERE / "protocol.md"), "runtime_sha256": digest(HERE / "runtime.json"),
             "frozen_inputs_sha256": digest(HERE / "frozen-inputs.json"),
             "fixture_hashes": hashes(HERE / "fixtures")})
        save(out / f"{phase}-product-hashes.json", hashes(PRODUCT))
        success = {"preflight": preflight, "trigger": trigger, "scenarios": scenarios}[phase](out, provider)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        save(out / f"{phase}-status.json", {"status": "completed" if success else "error", "error": error,
                                           "finished_at": utc_now()})
    print(json.dumps({"phase": phase, "status": "completed" if success else "error",
                      "error": redact(error) if error else None}, ensure_ascii=False))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
