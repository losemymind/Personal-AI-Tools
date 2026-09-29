"""Behavioral regressions for retrieval and evaluation reliability."""

import importlib
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from conftest import ARTIFACT, run_script


@pytest.fixture
def modules(monkeypatch):
    monkeypatch.syspath_prepend(str(ARTIFACT / "scripts"))
    return SimpleNamespace(**{
        name: importlib.import_module(name)
        for name in ("skill_index_search", "skill_index_build", "skill_eval", "skill_optimize", "skill_compare")
    })


def search_args(query, **overrides):
    args = dict(query=query, category=None, risk=None, tool=None, source=None,
                only_scripts=False, only_references=False, limit=10)
    args.update(overrides)
    return SimpleNamespace(**args)


def make_index(modules, tmp_path):
    entries = [dict(name=f"aaa-{i}", path=f"aaa-{i}", description="code review",
                    source_repo="bulk/repo") for i in range(12)]
    entries += [dict(name="code-review", path="skills/code-review",
                     description="Review Python code", source_repo="author/repo"),
                dict(name="python-review", path="python-review",
                     description="Python code review", source_repo="bulk/repo")]
    db = tmp_path / "index.db"
    modules.skill_index_build.build_db(entries, tmp_path, db)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    return conn


@pytest.mark.parametrize("query", ["code review", "代码审查", "代码评审"])
def test_exact_skill_is_in_first_result(modules, tmp_path, query):
    with make_index(modules, tmp_path) as conn:
        sql, params = modules.skill_index_search.build_query(search_args(query))
        rows = conn.execute(sql, params).fetchall()
    assert rows[0]["name"] == "code-review"
    assert len(rows) == 10


def test_expansion_preserves_qualifiers_and_source_filter(modules, tmp_path):
    with make_index(modules, tmp_path) as conn:
        sql, params = modules.skill_index_search.build_query(
            search_args("代码审查 Python", source="bulk/repo"))
        rows = conn.execute(sql, params).fetchall()
    assert [row["name"] for row in rows] == ["python-review"]
    assert modules.skill_index_search.expand_query("代码审查 未知限定词") == ["代码审查 未知限定词"]


def test_no_valid_evaluations_have_no_precision_or_recall(modules):
    summary = modules.skill_eval.summarize([{"error": "client unavailable"}])
    assert summary["precision"] is None
    assert summary["recall"] is None
    assert summary["coverage"] == 0
    assert summary["attempted"] == 1


def test_partial_evaluation_reports_coverage(modules):
    summary = modules.skill_eval.summarize([
        {"should_trigger": True, "triggered": True, "pass": True},
        {"error": "timeout"},
    ])
    assert summary["coverage"] == 0.5
    assert summary["total"] == 1


def test_strict_eval_exit_still_writes_report(temp_skill, tmp_path):
    evals = tmp_path / "evals.json"
    evals.write_text(json.dumps([{"query": "unrelated", "should_trigger": True}]))
    args = ("--eval-set", str(evals), "--skill-dir", str(temp_skill), "--json")
    normal = run_script("scripts/skill_eval.py", *args)
    strict = run_script("scripts/skill_eval.py", *args, "--fail-on-mismatch")
    assert normal.returncode == 0
    assert strict.returncode == 1
    assert json.loads(strict.stdout)["summary"]["failed"] == 1


def test_cli_error_exit_and_na_display(modules, monkeypatch, temp_skill, tmp_path, capsys):
    evals = tmp_path / "evals.json"
    evals.write_text(json.dumps([{"query": "q", "should_trigger": True}]))
    monkeypatch.setattr(modules.skill_eval, "run_cli_batch", lambda *a, **k: [
        {"query": "q", "should_trigger": True, "pass": None, "error": "offline"}])
    monkeypatch.setattr(sys, "argv", ["skill_eval.py", "--eval-set", str(evals),
        "--skill-dir", str(temp_skill), "--mode", "cli", "--fail-on-error"])
    assert modules.skill_eval.main() == 1
    assert "N/A" in capsys.readouterr().out


def test_cli_evaluates_candidate_copy_without_changing_source(modules, monkeypatch, temp_skill):
    original = (temp_skill / "SKILL.md").read_bytes()
    candidate = "Use for candidate queries: quotes \"and\" punctuation."
    observed = []

    def fake_cli(*args, **kwargs):
        installed = Path(kwargs["workspace"]) / ".opencode/skills" / temp_skill.name
        observed.append(modules.skill_eval.parse_skill_md(installed)[1])
        return True

    monkeypatch.setattr(modules.skill_eval, "run_cli", fake_cli)
    modules.skill_eval.run_cli_batch([{"query": "q", "should_trigger": True}],
        temp_skill.name, candidate, "opencode", 10, "", 1, 0.5, skill_dir=temp_skill)
    assert observed == [candidate]
    assert (temp_skill / "SKILL.md").read_bytes() == original


def loop_files(tmp_path):
    train = tmp_path / "development.json"
    train.write_text(json.dumps([
        {"query": f"dev-{i}", "should_trigger": i % 2 == 0} for i in range(8)]))
    final = tmp_path / "final.json"
    final.write_text(json.dumps([
        {"query": "unseen-final-positive", "should_trigger": True},
        {"query": "unseen-final-negative", "should_trigger": False}]))
    return train, final


def test_final_set_evaluated_once_after_selection(modules, monkeypatch, temp_skill, tmp_path, capsys):
    train, final = loop_files(tmp_path)
    prompts = []
    calls = []

    def improve(prompt):
        prompts.append(prompt)
        return "Improved candidate"

    def evaluate(items, description):
        calls.append(([e["query"] for e in items], description))
        return [{**e, "triggered": e["should_trigger"] if description == "Improved candidate"
                 else not e["should_trigger"], "pass": description == "Improved candidate"}
                for e in items]

    monkeypatch.setattr(modules.skill_optimize, "call_improver_manual", improve)
    monkeypatch.setattr(modules.skill_optimize, "run_heuristic", evaluate)
    monkeypatch.setattr(sys, "argv", ["skill_optimize.py", "--eval-set", str(train),
        "--skill-dir", str(temp_skill), "--max-iterations", "1",
        "--final-eval-set", str(final), "--final-mode", "heuristic"])
    assert modules.skill_optimize.main() == 0
    report = json.loads(capsys.readouterr().out)
    assert report["best_description"] == "Improved candidate"
    assert report["selection_set"] == "validation"
    assert report["confirmation"] == "proxy_only"
    final_calls = [c for c in calls if "unseen-final-positive" in c[0]]
    assert final_calls == [(["unseen-final-positive", "unseen-final-negative"], "Improved candidate")]
    assert "unseen-final" not in "".join(prompts)
    assert report["history"][0]["validation_total"] > 0


def test_final_queries_must_not_overlap_development_set(modules, monkeypatch, temp_skill, tmp_path, capsys):
    train, _ = loop_files(tmp_path)
    monkeypatch.setattr(sys, "argv", ["skill_optimize.py", "--eval-set", str(train),
        "--skill-dir", str(temp_skill), "--final-eval-set", str(train)])
    assert modules.skill_optimize.main() == 1
    assert "overlap" in capsys.readouterr().err


def test_final_cli_failure_is_reported_and_fails(modules, monkeypatch, temp_skill, tmp_path, capsys):
    train, final = loop_files(tmp_path)
    calls = []
    monkeypatch.setattr(modules.skill_optimize, "run_heuristic", lambda items, description: [
        {**e, "triggered": e["should_trigger"], "pass": True} for e in items])

    def final_cli(items, name, description, *args, **kwargs):
        calls.append((items, description, kwargs["skill_dir"]))
        return [{**e, "trigger_rate": None, "pass": None, "error": "offline"} for e in items]

    monkeypatch.setattr(modules.skill_optimize, "run_cli_batch", final_cli)
    monkeypatch.setattr(sys, "argv", ["skill_optimize.py", "--eval-set", str(train),
        "--skill-dir", str(temp_skill), "--final-eval-set", str(final), "--client", "opencode"])
    assert modules.skill_optimize.main() == 1
    report = json.loads(capsys.readouterr().out)
    assert len(calls) == 1
    assert calls[0][1] == report["best_description"]
    assert calls[0][2] == temp_skill
    assert report["confirmation"] == "error"
    assert report["final_evaluation"]["summary"]["coverage"] == 0


def test_loop_cli_errors_do_not_become_description_failures(modules, monkeypatch, temp_skill, tmp_path, capsys):
    train, _ = loop_files(tmp_path)
    monkeypatch.setattr(modules.skill_optimize, "run_cli_batch", lambda items, *a, **k: [
        {**e, "error": "offline", "pass": None} for e in items])
    monkeypatch.setattr(modules.skill_optimize, "call_improver_manual", lambda prompt: pytest.fail("must not improve run errors"))
    monkeypatch.setattr(sys, "argv", ["skill_optimize.py", "--eval-set", str(train),
        "--skill-dir", str(temp_skill), "--eval-mode", "cli"])
    assert modules.skill_optimize.main() == 1
    report = json.loads(capsys.readouterr().out)
    assert "evaluation_error" in report["exit_reason"]
    assert report["confirmation"] == "error"


def test_empty_resource_directories_do_not_gain_points(modules, temp_skill):
    before = modules.skill_compare.score_skill(modules.skill_compare.read_skill(temp_skill))
    for name in ("scripts", "references", "templates"):
        (temp_skill / name).mkdir()
    after = modules.skill_compare.score_skill(modules.skill_compare.read_skill(temp_skill))
    assert after["total_score"] == before["total_score"]


def test_comparison_is_screening_not_adoption_verdict(temp_skill, tmp_path):
    result = run_script("scripts/skill_compare.py", str(temp_skill), str(temp_skill), "--json")
    payload = json.loads(result.stdout)
    assert payload["meta"]["assessment_kind"] == "structural_screening"
    assert payload["meta"]["adoption_verdict"] == "requires_task_evidence"


def test_source_failure_preserves_previous_success_and_snapshot(modules, tmp_path):
    conn = make_index(modules, tmp_path)
    conn.close()
    db = tmp_path / "index.db"
    key = "source_status:author/repo"
    with sqlite3.connect(db) as conn:
        before = json.loads(conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()[0])
    modules.skill_index_build.record_source_failure(db, "author/repo", "offline")
    with sqlite3.connect(db) as conn:
        after = json.loads(conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()[0])
    assert after["status"] == "unavailable"
    assert after["last_success"] == before["last_success"]
    assert after["snapshot_sha256"] == before["snapshot_sha256"]


def test_partial_update_does_not_refresh_other_source(modules, tmp_path):
    conn = make_index(modules, tmp_path)
    conn.close()
    db = tmp_path / "index.db"
    with sqlite3.connect(db) as conn:
        before = conn.execute("SELECT value FROM meta WHERE key='source_status:author/repo'").fetchone()[0]
    modules.skill_index_build.update_db_incremental([
        dict(name="new", path="new", source_repo="bulk/repo")], tmp_path, db)
    with sqlite3.connect(db) as conn:
        after = conn.execute("SELECT value FROM meta WHERE key='source_status:author/repo'").fetchone()[0]
    assert before == after


def test_source_recovery_changes_snapshot_and_clears_failure(modules, tmp_path):
    conn = make_index(modules, tmp_path)
    conn.close()
    db = tmp_path / "index.db"
    modules.skill_index_build.record_source_failure(db, "author/repo", "offline")
    with sqlite3.connect(db) as conn:
        old = json.loads(conn.execute("SELECT value FROM meta WHERE key='source_status:author/repo'").fetchone()[0])
    modules.skill_index_build.update_db_incremental([
        dict(name="changed", path="skills/code-review", source_repo="author/repo")], tmp_path, db)
    with sqlite3.connect(db) as conn:
        state = json.loads(conn.execute("SELECT value FROM meta WHERE key='source_status:author/repo'").fetchone()[0])
    assert state["status"] == "ready"
    assert state["error"] is None
    assert state["snapshot_sha256"] != old["snapshot_sha256"]


def test_stats_of_legacy_index_does_not_invent_source_freshness(modules, tmp_path, monkeypatch, capsys):
    conn = make_index(modules, tmp_path)
    conn.execute("DELETE FROM meta WHERE key LIKE 'source_status:%'")
    conn.commit()
    conn.close()
    monkeypatch.setattr(modules.skill_index_search, "DB_PATH", tmp_path / "index.db")
    monkeypatch.setattr(sys, "argv", ["skill_index_search.py", "--stats"])
    assert modules.skill_index_search.main() == 0
    output = capsys.readouterr().out
    assert "last_success=unknown" in output
    assert "status=unknown" in output


def test_stats_includes_failed_source_without_rows(modules, tmp_path, monkeypatch, capsys):
    conn = make_index(modules, tmp_path)
    conn.close()
    db = tmp_path / "index.db"
    modules.skill_index_build.record_source_failure(db, "never-loaded/repo", "offline")
    monkeypatch.setattr(modules.skill_index_search, "DB_PATH", db)
    monkeypatch.setattr(sys, "argv", ["skill_index_search.py", "--stats"])
    assert modules.skill_index_search.main() == 0
    output = capsys.readouterr().out
    assert "never-loaded/repo" in output
    assert "status=unavailable" in output
    assert "error=offline" in output


def test_empty_scan_preserves_existing_source_snapshot(modules, tmp_path, monkeypatch):
    db = tmp_path / "index.db"
    modules.skill_index_build.build_db([
        dict(name="keep", path="keep", source_repo=modules.skill_index_build.SOURCES["aas"]["repo"])], tmp_path, db)
    monkeypatch.setattr(modules.skill_index_build, "DB_PATH", db)
    monkeypatch.setattr(modules.skill_index_build, "load_source_checkout", lambda *args: (tmp_path, []))
    monkeypatch.setattr(sys, "argv", ["skill_index_build.py", "--source", "aas"])
    assert modules.skill_index_build.main() == 0
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT name FROM skills").fetchone()[0] == "keep"
        state = json.loads(conn.execute("SELECT value FROM meta WHERE key LIKE 'source_status:%'").fetchone()[0])
    assert state["status"] == "unavailable"
