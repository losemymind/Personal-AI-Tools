"""Read-only audit of frozen inputs and live evidence; never invokes a model.

Only the new audit report is written. Existing logs, metrics, grading, manifests,
and observed-model records are never repaired or rewritten by this audit.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3

import run_live_evaluation as live


def relative(path, root):
    try:
        return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    except ValueError:
        return str(path)


def read_json(path, issues, required=True):
    path = Path(path)
    if not path.is_file():
        if required:
            issues.append({"path": str(path), "error": "missing_file"})
        return None
    try:
        return live.load(path)
    except (OSError, ValueError) as error:
        issues.append({"path": str(path), "error": f"invalid_json: {error}"})
        return None


def compare_hashes(expected, actual):
    if not isinstance(expected, dict):
        return [{"path": None, "error": "invalid_hash_mapping"}]
    return [{"path": name, "error": "missing" if name not in actual else
             "unexpected" if name not in expected else "hash_mismatch"}
            for name in sorted(expected.keys() | actual.keys())
            if expected.get(name) != actual.get(name)]


def frozen_audit(issues):
    frozen = read_json(live.HERE / "frozen-inputs.json", issues)
    if not isinstance(frozen, dict):
        return {"valid": False, "errors": [{"error": "missing_or_invalid_frozen_inputs"}]}
    errors = []
    for name, expected in frozen.get("protocol", {}).items():
        path = (live.HERE / name).resolve()
        if not path.is_relative_to(live.HERE) or not path.is_file():
            errors.append({"path": name, "error": "missing_or_invalid_protocol_path"})
        elif live.digest(path) != expected:
            errors.append({"path": name, "error": "protocol_hash_mismatch"})
    errors += [{"scope": "fixtures", **record} for record in
               compare_hashes(frozen.get("fixtures"), live.hashes(live.HERE / "fixtures"))]
    errors += [{"scope": "product", **record} for record in
               compare_hashes(frozen.get("product"), live.hashes(live.PRODUCT))]
    return {"valid": not errors, "errors": errors, "head_at_freeze": frozen.get("head"),
            "protocol_files": len(frozen.get("protocol", {})),
            "fixture_files": len(frozen.get("fixtures", {})), "product_files": len(frozen.get("product", {}))}


def observed_sessions(state_root):
    """Query only message records, selecting only assistant model/role metadata."""
    result = {"source": "opencode_local_session_metadata", "models": [], "messages": [], "error": None}
    if not state_root:
        result["error"] = "state_root_not_recorded"
        return result
    database = Path(state_root) / "data/opencode/opencode.db"
    if not database.is_file():
        result["error"] = "session_database_not_found"
        return result
    try:
        with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=5) as connection:
            for mid, sid, data in connection.execute("SELECT id, session_id, data FROM message"):
                item = json.loads(data)
                if item.get("role") != "assistant":
                    continue
                result["messages"].append({"message_id": mid, "session_id": sid,
                    "provider": item.get("providerID"), "model": item.get("modelID"),
                    "agent": item.get("agent"), "finish": item.get("finish")})
        result["models"] = sorted({f"{item['provider']}/{item['model']}"
                                   for item in result["messages"] if item["provider"] and item["model"]})
    except (OSError, ValueError, sqlite3.Error) as error:
        result["error"] = f"{type(error).__name__}: {error}"
    return result


def phase_hash_audit(attempt, issues):
    errors, checked = [], []
    frozen = live.load(live.HERE / "frozen-inputs.json")
    expected = {"query_sha256": live.digest(live.HERE / "queries.json"),
                "scenario_sha256": live.digest(live.HERE / "scenarios.json"),
                "protocol_sha256": live.digest(live.HERE / "protocol.md"),
                "runtime_sha256": live.digest(live.HERE / "runtime.json"),
                "frozen_inputs_sha256": live.digest(live.HERE / "frozen-inputs.json")}
    for phase in ("preflight", "trigger", "scenarios"):
        record = read_json(attempt / f"{phase}-environment.json", issues, required=False)
        if not isinstance(record, dict):
            continue
        checked.append(phase)
        for key, digest in expected.items():
            if record.get(key) != digest:
                errors.append({"phase": phase, "error": key + "_mismatch"})
        if record.get("fixture_hashes") != frozen.get("fixtures"):
            errors.append({"phase": phase, "error": "phase_fixture_hashes_mismatch"})
        product = read_json(attempt / f"{phase}-product-hashes.json", issues)
        if product != frozen.get("product"):
            errors.append({"phase": phase, "error": "phase_product_hashes_mismatch"})
    return {"phases_checked": checked, "valid": not errors, "errors": errors}


def check_manifest(run, issues):
    manifest = read_json(run / "artifacts.json", issues, required=False)
    checked, errors = 0, []
    if manifest is not None:
        if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
            errors.append({"path": "artifacts.json", "error": "invalid_manifest"})
        else:
            for record in manifest["files"]:
                if not isinstance(record, dict) or not isinstance(record.get("path"), str):
                    errors.append({"path": "artifacts.json", "error": "invalid_file_record"})
                    continue
                path = (run / record["path"]).resolve()
                if not path.is_relative_to(run.resolve()) or not path.is_file():
                    errors.append({"path": record["path"], "error": "missing_or_external_artifact"})
                    continue
                checked += 1
                if live.digest(path) != record.get("sha256"):
                    errors.append({"path": record["path"], "error": "artifact_hash_mismatch"})
    saved = read_json(run / "evidence-hashes.json", issues, required=False)
    evidence_checked = 0
    if isinstance(saved, dict):
        for name, expected in saved.items():
            path = (run / name).resolve()
            if not path.is_relative_to(run.resolve()) or not path.is_file():
                errors.append({"path": name, "error": "missing_or_external_evidence"})
            else:
                evidence_checked += 1
                if live.digest(path) != expected:
                    errors.append({"path": name, "error": "evidence_hash_mismatch"})
    return {"artifact_files_checked": checked, "saved_evidence_files_checked": evidence_checked,
            "saved_evidence_manifest_available": isinstance(saved, dict), "errors": errors,
            "current_file_hashes": live.hashes(run),
            "note": "Current hashes are audit observations; only saved manifests provide an earlier comparison"}


def workspace_path(run, environment, invocation, issues):
    marker = read_json(run / "workspace.json", issues, required=False)
    value = marker.get("path") if isinstance(marker, dict) else None
    value = value or environment.get("workspace") or invocation.get("cwd")
    return Path(value).resolve() if isinstance(value, str) else None


def check_discovery(run, kind, variant, workspace, issues):
    root = run / "skill-discovery" if kind == "runtime" else run
    items = read_json(root / "discovery.json", issues, required=False)
    saved = read_json(root / "discovery-check.json", issues, required=False)
    errors = []
    if items is None:
        return {"recorded": False, "valid": None, "errors": [], "note": "No discovery evidence; execution may have stopped before loading"}
    expected = workspace / ".opencode/skills" / live.NAME / "SKILL.md" if workspace and kind != "runtime" and variant != "without_skill" else None
    if not isinstance(items, list):
        return {"recorded": True, "valid": False, "errors": ["invalid_discovery_array"]}
    target = [item for item in items if isinstance(item, dict) and item.get("name") == live.NAME]
    if expected is None and target:
        errors.append("unexpected_target_skill")
    elif expected is not None and (len(target) != 1 or Path(str(target[0].get("location"))).resolve() != expected.resolve()):
        errors.append("target_skill_not_at_expected_workspace_path")
    for item in items:
        if not isinstance(item, dict):
            errors.append("invalid_discovery_item")
        elif item.get("name") == live.NAME:
            continue
        elif item.get("name") == "customize-opencode" and item.get("location") == "<built-in>":
            continue
        else:
            errors.append("unexpected_discovered_skill")
    if not isinstance(saved, dict) or saved.get("valid") is not True:
        errors.append("discovery_check_did_not_pass")
    return {"recorded": True, "valid": not errors, "errors": errors,
            "expected_skill_path": str(expected) if expected else None,
            "discovered_names": [item.get("name") for item in items if isinstance(item, dict)]}


def check_inputs(run, kind, source, workspace, issues):
    record = read_json(run / "input-integrity.json", issues, required=False)
    if not isinstance(record, dict):
        return {"recorded": False, "valid": None, "errors": [], "note": "No input-integrity record"}
    errors, retained = [], workspace is not None and workspace.is_dir()
    if record.get("unchanged") is not True:
        errors.append("executor_reported_changed_inputs")
    if kind == "runtime":
        before, after = record.get("before"), record.get("after")
        if before != after:
            errors.append("recorded_input_or_sentinel_hashes_differ")
        expected = {name: value for name, value in live.hashes(source).items() if name != "sentinel.txt"}
        if not isinstance(before, dict) or before.get("inputs") != expected or before.get("sentinel") != live.digest(source / "sentinel.txt"):
            errors.append("runtime_before_snapshot_differs_from_fixture")
        if retained:
            now = {"inputs": live.hashes(workspace / "inputs"),
                   "sentinel": live.digest(workspace / "sentinel.txt") if (workspace / "sentinel.txt").is_file() else None}
            if now != after:
                errors.append("retained_runtime_inputs_differ_from_recorded_after")
    else:
        expected = live.hashes(source)
        if record.get("source_before") != expected or record.get("source") != expected or record.get("after") != expected:
            errors.append("recorded_input_hashes_differ_from_fixture")
        if retained and live.hashes(workspace / "inputs") != record.get("after"):
            errors.append("retained_inputs_differ_from_recorded_after")
    return {"recorded": True, "valid": not errors, "errors": errors, "workspace_retained": retained}


def path_outside(value, workspace, state):
    """Resolve recorded path input; unresolved shell expansion is review evidence."""
    if not isinstance(value, str) or not value or "://" in value or value.startswith("<"):
        return None
    if any(token in value for token in ("${", "$env:", "%USERPROFILE%", "$HOME")):
        return {"path": value, "resolution": "requires_shell_expansion_review"}
    workspace = Path(workspace).resolve() if workspace else None
    path = Path(value)
    if value.startswith("~/") or value.startswith("~\\"):
        path = Path(state) / "home" / value[2:] if state else path
    elif not path.is_absolute() and workspace:
        path = workspace / path
    if not workspace:
        return {"path": value, "resolution": "workspace_unknown"}
    try:
        resolved = path.resolve()
    except OSError:
        return {"path": value, "resolution": "unresolved"}
    return {"path": value, "resolved": str(resolved), "resolution": "outside_workspace"} if not resolved.is_relative_to(workspace) else None


def tool_observations(raw, workspace, state):
    calls = live.tool_calls(raw, "opencode")
    findings = []
    path_keys = {"filepath", "file_path", "path", "cwd", "workdir", "workingdirectory", "directory"}
    foreign = re.compile(r"(?<![\w-])(?:skill[-_]creator|skill_(?:validate|create|package|eval|scenario|benchmark)|validate_skills|create_skill|package_skill)(?![\w-])", re.I)
    global_config = re.compile(r"(?:[~$%]|[A-Za-z]:[/\\]).{0,240}(?:[.]config[/\\]opencode|[.]codex|[.]claude)[/\\]", re.I)
    creator_script = re.compile(r"(?:agent_(?:adapt|validate|create|package|compare|security|index_build|index_search)|(?:adapt|create|package)_agent|validate_agents|(?:build|search)_agent_index)[.]py", re.I)
    absolute = re.compile(r"[A-Za-z]:[/\\][^\r\n\"'<>|;]+|(?:~[/\\]|/(?:home|tmp|Users|opt)/)[^\s\"'<>|;]+")

    def paths(inputs, prefix="input"):
        if isinstance(inputs, dict):
            for key, value in inputs.items():
                if key.lower() in path_keys and isinstance(value, str):
                    yield prefix + "." + key, value
                elif isinstance(value, (dict, list)):
                    yield from paths(value, prefix + "." + key)
        elif isinstance(inputs, list):
            for index, value in enumerate(inputs):
                yield from paths(value, f"{prefix}[{index}]")

    for call in calls:
        base = {"tool": call.get("tool"), "status": call.get("status"), "tool_use_id": call.get("tool_use_id"),
                "observation": "completed_call" if call.get("status") == "completed" else "attempt_only_or_incomplete"}
        for field, value in paths(call.get("input", {})):
            outside = path_outside(value, workspace, state)
            if outside:
                findings.append({**base, "reason": "external_path_requires_review", "field": field, **outside})
        if call.get("tool") not in ("bash", "shell", "powershell", "terminal"):
            continue
        command = call.get("input", {}).get("command", "")
        if not isinstance(command, str):
            continue
        reasons = []
        if foreign.search(command):
            reasons.append("other_creator_reference_in_shell")
        if global_config.search(command):
            reasons.append("global_configuration_path_in_shell")
        external = [value for value in (path_outside(match.group(0).strip(), workspace, state)
                                       for match in absolute.finditer(command)) if value]
        if external:
            reasons.append("absolute_or_home_path_outside_workspace_in_shell")
        if creator_script.search(command) and (external or global_config.search(command)):
            reasons.append("creator_script_with_external_path_in_shell")
        if reasons:
            findings.append({**base, "reasons": reasons, "command_excerpt": command[:1200],
                             "command_sha256": hashlib.sha256(command.encode("utf-8")).hexdigest(),
                             "paths": external})
    return {"tool_calls": len(calls), "findings": findings,
            "interpretation": "Review leads, not proof of successful external access; shell paths may be arguments or quoted text. Home/XDG isolation is not an OS sandbox."}


def runtime_role_checks(run, workspace, attempt, spec, issues):
    errors = []
    source = read_json(run / "source.json", issues, required=False)
    if isinstance(source, dict):
        path = Path(source.get("path", "")).resolve()
        if not path.is_relative_to(attempt) or not path.is_file() or live.digest(path) != source.get("sha256"):
            errors.append("generated_source_hash_mismatch_or_invalid_path")
    native = read_json(run / "native-agent.stdout.json", issues, required=False)
    installed = run / "installed-agent.md"
    if isinstance(native, dict):
        if native.get("name") != spec["agent_name"] or native.get("mode") != "primary" or not native.get("prompt"):
            errors.append("native_agent_did_not_resolve_expected_primary_role")
        if installed.is_file():
            text = installed.read_text(encoding="utf-8-sig")
            body = re.sub(r"\A---\s*\n.*?\n---\s*\n?", "", text, count=1, flags=re.S).strip()
            # JSON preserves the loader's original CRLF; read_text normalizes
            # the saved Markdown to LF. Compare the same logical newline form
            # while preserving all non-newline characters and internal spaces.
            normalize_newlines = lambda value: value.replace("\r\n", "\n").replace("\r", "\n").strip()
            if normalize_newlines(str(native.get("prompt", ""))) != normalize_newlines(body):
                errors.append("native_prompt_differs_from_installed_role_body")
    local = workspace / ".opencode/agents" / f"{spec['agent_name']}.md" if workspace else None
    if installed.is_file() and local and local.is_file() and live.digest(installed) != live.digest(local):
        errors.append("retained_native_role_differs_from_saved_role")
    return {"source_recorded": isinstance(source, dict), "native_discovery_recorded": native is not None,
            "installed_role_recorded": installed.is_file(), "errors": errors}


def run_audit(run, kind, variant, fixture, attempt, runtime_spec, issues):
    result = {"run": relative(run, attempt), "kind": kind, "variant": variant, "present": run.is_dir()}
    if not run.is_dir():
        return {**result, "status": "not_recorded", "model_command_recorded": False, "model_observed": False}
    def object_record(name):
        record = read_json(run / name, issues, required=False)
        if record is not None and not isinstance(record, dict):
            issues.append({"path": str(run / name), "error": "expected_json_object"})
        return record if isinstance(record, dict) else {}

    environment = object_record("client-environment.json")
    invocation = object_record("invocation.json")
    metrics = object_record("execution.json" if kind == "runtime" else "metrics.json")
    workspace = workspace_path(run, environment, invocation, issues)
    state = environment.get("state_root")
    observed = observed_sessions(state)
    saved_observed = read_json(run / "observed-models.json", issues, required=False)
    raw = ""
    for filename in ("stdout.jsonl", "stderr.txt"):
        path = run / filename
        if path.is_file():
            raw += path.read_text(encoding="utf-8", errors="replace") + "\n"
    if not raw.strip() and (run / "transcript.md").is_file():
        raw = (run / "transcript.md").read_text(encoding="utf-8", errors="replace")
    public = environment.get("public_config", {})
    config_errors = []
    if environment and (environment.get("isolated_user_directories") is not True or public.get("mcp") != {} or public.get("plugin") != []):
        config_errors.append("isolation_or_mcp_plugin_configuration_mismatch")
    permissions = public.get("permission", {})
    for tool in ("webfetch", "websearch", "task", "question", "external_directory"):
        if environment and permissions.get(tool) != "deny":
            config_errors.append(f"permission_not_denied:{tool}")
    if environment and permissions.get("skill", {}).get("customize-opencode") != "deny":
        config_errors.append("configuration_skill_not_denied")
    result.update(status=metrics.get("status", "not_finalized"), execution_error=metrics.get("error"),
        timed_out=metrics.get("timed_out"), workspace=str(workspace) if workspace else None,
        model_command_recorded=bool(invocation.get("argv")), model_observed=bool(observed["messages"]),
        model_called_flag=metrics.get("model_called"), observed_models=observed,
        saved_models_agree=(saved_observed.get("models") == observed["models"] if isinstance(saved_observed, dict) and observed["error"] is None else None),
        unexpected_models=[model for model in observed["models"] if model != live.MODEL],
        configuration_errors=config_errors,
        artifacts=check_manifest(run, issues),
        discovery=check_discovery(run, kind, variant, workspace, issues),
        input_integrity=check_inputs(run, kind, fixture, workspace, issues),
        tool_observations=tool_observations(raw, workspace, state))
    if kind != "runtime" and workspace:
        installed = workspace / ".opencode/skills" / live.NAME
        expected = (read_json(attempt / "old-product-hashes.json", issues, required=False)
                    if variant == "old_skill" else live.load(live.HERE / "frozen-inputs.json").get("product"))
        if variant == "without_skill":
            result["installed_product"] = {"available": installed.exists(), "errors": ["unexpected_installed_product"] if installed.exists() else []}
        elif installed.is_dir():
            differences = compare_hashes(expected, live.hashes(installed))
            result["installed_product"] = {"available": True, "errors": differences}
        else:
            result["installed_product"] = {"available": False, "errors": [], "note": "Retained workspace may be unavailable"}
    if kind == "runtime":
        result["native_role"] = runtime_role_checks(run, workspace, attempt, runtime_spec, issues)
        tool_audit = read_json(run / "tool-audit.json", issues, required=False)
        if isinstance(tool_audit, dict):
            result["runtime_tool_audit"] = {"calls_recorded": len(tool_audit.get("calls", [])),
                "non_readonly_attempts": len(tool_audit.get("non_readonly_attempts", [])),
                "agrees_with_raw": tool_audit.get("calls") == live.tool_calls(raw, "opencode")}
    return result


def secret_scan(root, output):
    """Report only relative paths and occurrence counts; never secret values."""
    matches, errors = [], []
    needles = [value.encode("utf-8") for value in live.SECRETS if value]
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.resolve() == output or "__pycache__" in path.parts:
            continue
        try:
            content = path.read_bytes()
            count = sum(content.count(secret) for secret in needles)
            if count:
                matches.append({"path": relative(path, root), "matches": count})
        except OSError as error:
            errors.append({"path": relative(path, root), "error": type(error).__name__})
    return {"source": "selected_provider_exact_values_and_declared_environment_references",
            "values_available": len(needles), "matching_files": matches,
            "match_count": sum(item["matches"] for item in matches), "read_errors": errors}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--attempt", required=True, type=Path)
    parser.add_argument("--out", type=Path, help="New report path; default <attempt>/evidence-audit.json")
    args = parser.parse_args()
    attempt = args.attempt.resolve()
    if not attempt.is_dir() or not attempt.is_relative_to(live.HERE):
        parser.error("--attempt must be an existing attempt directory below this evaluation root")
    output = args.out.resolve() if args.out else attempt / "evidence-audit.json"
    if output.exists():
        parser.error("Audit report already exists; choose a new --out path")
    issues, runs = [], []
    secret_error = None
    try:
        live.selected_provider()
    except Exception as error:
        # Do not stringify malformed configuration or arbitrary credential data.
        secret_error = type(error).__name__ + ": selected provider secret values unavailable"
    frozen = frozen_audit(issues)
    phase_hashes = phase_hash_audit(attempt, issues)
    runtime = read_json(live.HERE / "runtime.json", issues) or {}
    query_items = read_json(live.HERE / "queries.json", issues) or []
    tasks = read_json(live.HERE / "scenarios.json", issues) or []
    for item in query_items:
        runs.append(run_audit(attempt / "trigger/raw" / f"query-{item['id']:02d}", "trigger", "with_skill",
                             live.HERE / item.get("input_dir", "fixtures/trigger"), attempt, runtime, issues))
    for item in tasks:
        for variant in ("with_skill", "old_skill", "without_skill"):
            runs.append(run_audit(attempt / "iteration-1" / f"eval-{item['name']}" / variant / "run-1",
                                 "scenario", variant, live.HERE / item["input_dir"], attempt, runtime, issues))
    for variant in runtime.get("variants", []):
        runs.append(run_audit(attempt / "runtime" / variant / "run-1", "runtime", variant,
                             live.HERE / runtime["fixture_dir"], attempt, runtime, issues))
    secrets = secret_scan(live.HERE, output)
    secrets["configuration_error"] = secret_error
    hard_failures = []
    for run in runs:
        if not run["present"]:
            continue
        reasons = list(run.get("configuration_errors", [])) + list(run.get("unexpected_models", []))
        reasons += [item["error"] for item in run.get("artifacts", {}).get("errors", [])]
        reasons += run.get("discovery", {}).get("errors", [])
        reasons += run.get("input_integrity", {}).get("errors", [])
        reasons += run.get("native_role", {}).get("errors", [])
        if run.get("installed_product", {}).get("errors"):
            reasons.append("installed_product_differs_from_group_snapshot")
        if run.get("saved_models_agree") is False:
            reasons.append("saved_model_observation_differs_from_session")
        if run.get("status") == "completed":
            if not run.get("model_command_recorded"):
                reasons.append("completed_run_missing_model_invocation")
            if not run.get("model_observed"):
                reasons.append("completed_run_missing_session_model_observation")
            if not run.get("discovery", {}).get("recorded"):
                reasons.append("completed_run_missing_discovery_evidence")
            if not run.get("input_integrity", {}).get("recorded"):
                reasons.append("completed_run_missing_input_integrity_evidence")
        if reasons:
            hard_failures.append({"run": run["run"], "reasons": reasons})
    counts = {}
    for kind in ("trigger", "scenario", "runtime"):
        subset = [run for run in runs if run["kind"] == kind]
        counts[kind] = {"planned": len(subset), "run_directories": sum(run["present"] for run in subset),
                       "model_commands_recorded": sum(run["model_command_recorded"] for run in subset),
                       "runs_with_assistant_model_metadata": sum(run["model_observed"] for run in subset),
                       "statuses": dict(Counter(run["status"] for run in subset))}
    complete = all(run["present"] and run["status"] not in ("not_recorded", "not_finalized") for run in runs)
    integrity_ok = frozen["valid"] and phase_hashes["valid"] and not hard_failures and not issues and not secrets["match_count"] and not secrets["read_errors"] and secret_error is None
    report = {"schema_version": 1, "audited_at": live.utc_now(), "attempt": str(attempt),
              "read_only_evidence": True, "frozen_inputs": frozen, "phase_hashes": phase_hashes, "counts": counts,
              "planned_total": len(runs), "expected_protocol_total": 17,
              "model_commands_recorded": sum(run["model_command_recorded"] for run in runs),
              "runs_with_assistant_model_metadata": sum(run["model_observed"] for run in runs),
              "evidence_complete": complete, "integrity_ok": integrity_ok,
              "configured_secret_scan": secrets, "evidence_read_errors": issues,
              "integrity_failures": hard_failures, "runs": runs,
              "manual_review_findings": sum(len(run.get("tool_observations", {}).get("findings", [])) for run in runs),
              "limits": ["Invocation records show attempted commands, not successful provider requests.",
                         "Assistant session metadata identifies the client-selected provider/model, not underlying model weights.",
                         "Missing or failed generation/loading may reduce actual model calls; no missing call is fabricated.",
                         "External path and shell findings require manual review; failed tools are attempts, not confirmed access.",
                         "Environment and discovery isolation do not form an operating-system sandbox.",
                         "Billing is unknown; zero client-reported cost does not establish free usage."]}
    live.save(output, report)
    print(json.dumps({"report": str(output), "integrity_ok": integrity_ok, "evidence_complete": complete,
                      "planned": len(runs), "model_commands_recorded": report["model_commands_recorded"],
                      "runs_with_assistant_model_metadata": report["runs_with_assistant_model_metadata"],
                      "secret_matches": secrets["match_count"], "manual_review_findings": report["manual_review_findings"]}, ensure_ascii=False))
    return 0 if integrity_ok and complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
