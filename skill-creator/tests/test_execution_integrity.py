"""Structured trigger evidence and retained scenario deliverables (no live model)."""

import hashlib
import importlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import ARTIFACT


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(ARTIFACT / "scripts"))
    return tuple(importlib.import_module(name) for name in ("skill_eval", "skill_scenario", "skill_events"))


def assistant(tool, inputs, identifier="t1"):
    return json.dumps({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "id": identifier, "name": tool, "input": inputs}]}})


@pytest.mark.parametrize("raw", [
    "Do not use skill-creator",
    json.dumps({"type": "result", "result": "skill-creator was not used"}),
    assistant("Skill", {"skill": "skill-creator-other"}),
    assistant("Bash", {"command": "cat .claude/skills/skill-creator/SKILL.md"}),
    assistant("Read", {"file_path": ".claude/skills/skill-creator/SKILL.md.backup"}),
    assistant("Read", {"file_path": "unrelated/skill-creator/SKILL.md"}),
])
def test_claude_requires_target_tool_evidence(modules, raw):
    evaluation, _, _ = modules
    assert not evaluation.detect_triggered("claude", raw, "skill-creator")


def test_claude_dispatch_and_installed_target_read_have_distinct_evidence(modules, tmp_path):
    evaluation, _, _ = modules
    installed = tmp_path / ".claude/skills/folder-name/SKILL.md"
    call = assistant("Read", {"file_path": str(installed)})
    assert evaluation.trigger_evidence("claude", call, "skill-name", installed)[0]["kind"] == "target_read"
    assert not evaluation.detect_triggered("claude", call, "skill-name")
    wrong_folder = assistant("Read", {"file_path": ".claude/skills/skill-name/SKILL.md"})
    assert not evaluation.detect_triggered("claude", wrong_folder, "skill-name", installed)
    dispatch = assistant("Skill", {"skill": "skill-name"})
    assert evaluation.trigger_evidence("claude", dispatch, "skill-name")[0]["kind"] == "skill_dispatch"


def test_partial_claude_input_is_assembled_exactly_and_deduplicated(modules):
    evaluation, _, stream = modules
    fragments = [
        {"type": "content_block_start", "index": 0, "content_block":
         {"type": "tool_use", "id": "t1", "name": "Skill", "input": {}}},
        {"type": "content_block_delta", "index": 0, "delta":
         {"type": "input_json_delta", "partial_json": '{"skill":"skill-'}},
        {"type": "content_block_delta", "index": 0, "delta":
         {"type": "input_json_delta", "partial_json": 'creator"}'}},
    ]
    lines = [json.dumps({"type": "stream_event", "event": event}) for event in fragments]
    assert not evaluation.detect_triggered("claude", "\n".join(lines[:2]), "skill-creator")
    assert evaluation.detect_triggered("claude", "\n".join(lines), "skill-creator")
    lines.append(assistant("Skill", {"skill": "skill-creator"}))
    assert len(stream.tool_calls("\n".join(lines), "claude")) == 1


def test_failed_claude_tool_result_is_not_loading_evidence(modules):
    evaluation, _, _ = modules
    raw = assistant("Skill", {"skill": "skill-creator"}) + "\n" + json.dumps({
        "type": "user", "message": {"content": [
            {"type": "tool_result", "tool_use_id": "t1", "is_error": True, "content": "missing"}]}})
    assert not evaluation.detect_triggered("claude", raw, "skill-creator")


def test_cli_records_partial_loading_evidence_on_timeout(modules, monkeypatch):
    evaluation, _, _ = modules
    raw = assistant("Skill", {"skill": "skill-creator"})

    def fake(*args, **kwargs):
        assert "stream-json" in args[0]
        raise subprocess.TimeoutExpired(args[0], 1, output=raw)

    monkeypatch.setattr(evaluation, "run_client", fake)
    result = evaluation.run_cli_item({"query": "do task", "should_trigger": True},
        "skill-creator", "description", "claude", 1, "", 1, 0.5)
    assert result["pass"]
    evidence = result["trigger_evidence"][0]
    assert evidence["timed_out"] and evidence["evidence"][0]["kind"] == "skill_dispatch"


def test_unstructured_success_is_error_not_a_negative_trigger(modules, monkeypatch):
    evaluation, _, _ = modules
    monkeypatch.setattr(evaluation, "run_client", lambda *a, **k: (0, "No skill used", ""))
    with pytest.raises(RuntimeError, match="structured events"):
        evaluation.run_cli("q", "skill-creator", "d", "claude")


@pytest.mark.parametrize("failure", [None, "exit", "timeout"])
def test_scenario_retains_real_files_and_excludes_inputs_config(modules, monkeypatch, tmp_path, failure):
    _, scenario, _ = modules
    inputs = tmp_path / "fixtures"
    inputs.mkdir()
    (inputs / "source.csv").write_text("source", encoding="utf-8")
    run = tmp_path / "run"
    captured = {}

    def fake(cmd, **kwargs):
        workspace = Path(kwargs["cwd"])
        captured["workspace"] = workspace
        assert (workspace / "inputs/source.csv").read_text() == "source"
        assert kwargs["env"]["SCENARIO_OUTPUT_DIR"] == str(workspace / "deliverables")
        (workspace / "table.csv").write_bytes(b"a,b\n1,2\n")
        (workspace / "deliverables/report.txt").write_text("report", encoding="utf-8")
        (workspace / ".claude").mkdir()
        (workspace / ".claude/settings.json").write_text("private", encoding="utf-8")
        (workspace / "opencode.json").write_text("client config", encoding="utf-8")
        if failure == "timeout":
            raise subprocess.TimeoutExpired(cmd, 1, output="partial reply")
        return (1 if failure else 0), "reply", ""

    monkeypatch.setattr(scenario, "run_client", fake)
    monkeypatch.setattr(sys, "argv", ["skill_scenario.py", "--prompt", "write a table", "--run-dir", str(run),
        "--input-dir", str(inputs), "--output-dir", "deliverables"])
    assert scenario.main() == (1 if failure else 0)
    assert not captured["workspace"].exists()
    manifest = json.loads((run / "artifacts.json").read_text())
    assert {item["source_path"] for item in manifest["files"]} == {"table.csv", "deliverables/report.txt"}
    assert (run / "outputs/artifacts/table.csv").read_bytes() == b"a,b\n1,2\n"
    table = next(item for item in manifest["files"] if item["source_path"] == "table.csv")
    assert table["sha256"] == hashlib.sha256(b"a,b\n1,2\n").hexdigest()
    assert (inputs / "source.csv").read_text() == "source"
    metrics = json.loads((run / "metrics.json").read_text())
    assert metrics["status"] == ("error" if failure else "completed")
    assert metrics["total_tokens"] is None and metrics["model"] is None


def test_scenario_rejects_nonempty_run_without_removing_grading(modules, monkeypatch, tmp_path):
    _, scenario, _ = modules
    run = tmp_path / "run"
    run.mkdir()
    grading = run / "grading.json"
    grading.write_text('{"pass_rate":1}', encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["skill_scenario.py", "--prompt", "p", "--run-dir", str(run)])
    assert scenario.main() == 1
    assert grading.read_text() == '{"pass_rate":1}'
    assert list(run.iterdir()) == [grading]


@pytest.mark.parametrize("output", [".", "../out", "inputs", "inputs/out", ".claude/out", ".opencode",
                                    "exports/node_modules", "exports/__pycache__/nested"])
def test_scenario_rejects_escaping_or_reserved_output(modules, monkeypatch, tmp_path, output):
    _, scenario, _ = modules
    run = tmp_path / "run"
    monkeypatch.setattr(sys, "argv", ["skill_scenario.py", "--prompt", "p", "--run-dir", str(run),
        "--output-dir", output])
    assert scenario.main() == 1
    assert not run.exists()


def test_artifact_collection_does_not_follow_external_links(modules, tmp_path):
    _, scenario, _ = modules
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    outside = tmp_path / "private.txt"
    outside.write_text("private", encoding="utf-8")
    try:
        (workspace / "escape.txt").symlink_to(outside)
        (workspace / "escape-dir").symlink_to(tmp_path, target_is_directory=True)
    except OSError:
        pytest.skip("This host cannot create symlinks")
    result = scenario.collect_artifacts(workspace, tmp_path / "run", set(), Path("outputs"))
    assert not result["files"]
    assert len(result["skipped"]) == 2
    assert not result["errors"]


def test_stream_metrics_use_result_totals_without_double_counting_messages(modules):
    _, _, stream = modules
    raw = "\n".join(json.dumps(event) for event in [
        {"type": "assistant", "message": {"model": "actual-model", "usage": {"input_tokens": 9, "output_tokens": 3}}},
        {"type": "result", "usage": {"input_tokens": 9, "output_tokens": 3, "cache_read_input_tokens": 2}},
    ])
    metrics = stream.stream_metrics(raw, "claude")
    assert metrics["total_tokens"] == 14
    assert metrics["model"] == "actual-model"
    assert metrics["tokens_source"] == "claude_result_usage"
    assert stream.stream_metrics("plain reply", "claude")["total_tokens"] is None


def test_failed_opencode_dispatch_does_not_trigger(modules):
    evaluation, _, _ = modules
    raw = json.dumps({"type": "tool_use", "part": {"tool": "skill", "state":
                     {"input": {"name": "skill-creator"}, "status": "error"}}})
    assert not evaluation.detect_triggered("opencode", raw, "skill-creator")


@pytest.mark.parametrize("client,event", [
    ("claude", {"type": "result", "is_error": True}),
    ("opencode", {"type": "error", "error": {"name": "provider missing"}}),
])
def test_scenario_records_structured_error_despite_zero_exit(modules, monkeypatch, tmp_path, client, event):
    _, scenario, _ = modules
    monkeypatch.setattr(scenario, "run_client", lambda *a, **k: (0, json.dumps(event), ""))
    run = tmp_path / "run"
    monkeypatch.setattr(sys, "argv", ["skill_scenario.py", "--prompt", "p", "--run-dir", str(run),
        "--client", client])
    assert scenario.main() == 1
    metrics = json.loads((run / "metrics.json").read_text())
    assert metrics["returncode"] == 0 and metrics["status"] == "error"
    assert metrics["error"]


def test_scenario_rejects_linked_input_without_copying_target(modules, monkeypatch, tmp_path):
    _, scenario, _ = modules
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    private = tmp_path / "private.txt"
    private.write_text("private", encoding="utf-8")
    try:
        (inputs / "linked.txt").symlink_to(private)
    except OSError:
        pytest.skip("This host cannot create symlinks")
    run = tmp_path / "run"
    monkeypatch.setattr(sys, "argv", ["skill_scenario.py", "--prompt", "p", "--run-dir", str(run),
        "--input-dir", str(inputs)])
    assert scenario.main() == 1
    assert not json.loads((run / "artifacts.json").read_text())["files"]
    assert "linked input" in json.loads((run / "metrics.json").read_text())["error"]


def test_opencode_error_after_text_is_run_error_for_negative_query(modules, monkeypatch):
    evaluation, _, _ = modules
    raw = '\n'.join(json.dumps(event) for event in [
        {"type": "text", "part": {"text": "Cannot do that"}}, {"type": "error"}])
    monkeypatch.setattr(evaluation, "run_client", lambda *a, **k: (0, raw, ""))
    result = evaluation.run_cli_item({"query": "q", "should_trigger": False},
        "skill-creator", "d", "opencode", 1, "", 1, 0.5)
    assert result["pass"] is None and result["error"]


def test_multiple_observed_models_are_not_replaced_by_requested_model(modules, monkeypatch, tmp_path):
    _, scenario, _ = modules
    raw = json.dumps({"type": "result", "modelUsage": {"a": {}, "b": {}},
                      "usage": {"input_tokens": 1, "output_tokens": 2}})
    monkeypatch.setattr(scenario, "run_client", lambda *a, **k: (0, raw, ""))
    run = tmp_path / "run"
    monkeypatch.setattr(sys, "argv", ["skill_scenario.py", "--prompt", "p", "--run-dir", str(run),
        "--client", "claude", "--model", "a"])
    assert scenario.main() == 0
    metrics = json.loads((run / "metrics.json").read_text())
    assert metrics["model"] is None
    assert metrics["models"] == ["a", "b"]
    assert metrics["requested_model"] == "a" and metrics["model_source"] == "client_stream"
