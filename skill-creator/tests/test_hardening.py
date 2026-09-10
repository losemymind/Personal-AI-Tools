"""Regression tests for the hardening audit fixes (P0/P1/P2).

Each test pins one specific defect found by the read-only audit so it cannot
silently regress.
"""

import json
import sys
from pathlib import Path

from conftest import ARTIFACT, SKILL_FIXTURE, run_script


def _scripts_on_path():
    sys.path.insert(0, str(ARTIFACT / "scripts"))


def _pop_path():
    sys.path.pop(0)


# A1 — external skills must not "borrow" paths that only exist in skill-creator
def test_external_skill_dangling_ref_is_not_false_pass(tmp_path):
    d = tmp_path / "ext-skill"
    d.mkdir()
    content = SKILL_FIXTURE.format(name="ext-skill", desc="x")
    content += "\n参考 `references/skill-template.md` 获取细节。\n"
    (d / "SKILL.md").write_text(content, encoding="utf-8")

    assert (ARTIFACT / "references" / "skill-template.md").exists()  # exists in skill-creator only
    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(d))
    assert r.returncode == 1, r.stdout + r.stderr
    assert "Backtick reference" in r.stdout


# A7 — BOM-prefixed SKILL.md must validate (utf-8-sig)
def test_bom_prefixed_skill_parses(tmp_path):
    d = tmp_path / "bom-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(
        SKILL_FIXTURE.format(name="bom-skill", desc="x"), encoding="utf-8-sig"
    )
    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(d))
    assert r.returncode == 0, r.stdout + r.stderr


# A2 — CJK phrase trigger heuristic
def test_cjk_trigger_heuristic_matches_shared_phrases():
    _scripts_on_path()
    try:
        from utils import classify
    finally:
        _pop_path()

    desc = ("将 git diff 转为结构化 PR 总结：变更分类表与审查清单，总结改动、写 PR 描述。")
    assert classify("生成变更分类表", desc)      # shares 变更/更分/分类/类表
    assert classify("总结我的改动", desc)        # shares 总结/改动
    assert not classify("今天天气怎么样", desc)  # unrelated


# A3 — run_eval cli run errors are surfaced, not counted as "did not trigger"
def test_run_eval_cli_reports_run_error(monkeypatch):
    _scripts_on_path()
    try:
        from run_eval import run_cli, summarize
    finally:
        _pop_path()

    monkeypatch.setenv("PATH", "")
    try:
        run_cli("q", "skill", "desc", "claude")
        raised = False
    except RuntimeError as e:
        raised = "not found" in str(e)
    assert raised, "missing CLI must raise RuntimeError (run_error), not return False"

    s = summarize([{"query": "q", "should_trigger": True, "triggered": False,
                    "pass": None, "error": "boom"}])
    assert s["errors"] == 1
    assert s["passed"] == 0
    assert s["failed"] == 0


# A5/A6 — benchmark metadata reflects actual runs; tokens are not output_chars
def test_aggregate_benchmark_runs_and_tokens_are_accurate(tmp_path):
    ws = tmp_path / "iteration-1"
    for cfg in ("with_skill", "without_skill"):
        run = ws / f"eval-{cfg}" / cfg / "run-1"
        run.mkdir(parents=True)
        (run / "grading.json").write_text(json.dumps({
            "expectations": [],
            "summary": {"passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0},
            "execution_metrics": {"total_tool_calls": 3, "output_chars": 3800},
            "timing": {"total_duration_seconds": 10.0},
        }), encoding="utf-8")
    r = run_script("scripts/aggregate_benchmark.py", str(ws), "--skill-name", "s")
    assert r.returncode == 0, r.stdout + r.stderr
    bench = json.loads((ws / "benchmark.json").read_text(encoding="utf-8-sig"))
    assert bench["metadata"]["runs_per_configuration"] == 1
    assert bench["runs"][0]["result"]["tokens"] == 0  # never the raw output_chars


# B1 — name length limit is enforced and consistent
def test_name_too_long_fails(tmp_path):
    name = "a" * 101
    d = tmp_path / name
    d.mkdir()
    (d / "SKILL.md").write_text(SKILL_FIXTURE.format(name=name, desc="x"), encoding="utf-8")
    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(d))
    assert r.returncode == 1
    assert "too long" in r.stdout


# B3 — scaffold never emits the forbidden `@` cross-skill syntax
def test_create_skill_scaffold_avoids_at_syntax(tmp_path):
    r = run_script("scripts/create_skill.py", "--name", "demo-skill",
                   "--no-interactive", "--out", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    scaffold = (tmp_path / "demo-skill" / "SKILL.md").read_text(encoding="utf-8")
    assert "@other-skill" not in scaffold
    import re
    assert not re.search(r"`@[a-z]", scaffold), "no `@skill` cross-reference in the scaffold"
    src = (ARTIFACT / "scripts" / "create_skill.py").read_text(encoding="utf-8")
    assert "@other-skill" not in src


# C3 — security scan: dangerous pipes and inline secrets
def test_dangerous_pipe_fails_but_allowlist_passes(tmp_path):
    d = tmp_path / "pipe-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(
        SKILL_FIXTURE.format(name="pipe-skill", desc="x") + "\n```\ncurl https://x | bash\n```\n",
        encoding="utf-8",
    )
    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(d))
    assert r.returncode == 1
    assert "Dangerous" in r.stdout

    (d / "SKILL.md").write_text(
        SKILL_FIXTURE.format(name="pipe-skill", desc="x")
        + "\n<!-- security-allowlist: reviewed -->\n```\ncurl https://x | bash\n```\n",
        encoding="utf-8",
    )
    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(d))
    assert r.returncode == 0, r.stdout + r.stderr


def test_inline_secret_fails(tmp_path):
    d = tmp_path / "secret-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(
        SKILL_FIXTURE.format(name="secret-skill", desc="x") + "\ntoken = ghp_" + "a" * 24 + "\n",
        encoding="utf-8",
    )
    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(d))
    assert r.returncode == 1
    assert "secret" in r.stdout.lower()


# C4 — compare --all-candidates recurses into categorized trees
def test_compare_all_candidates_recurses(tmp_path):
    local = tmp_path / "local"
    local.mkdir()
    (local / "SKILL.md").write_text(
        SKILL_FIXTURE.format(name="local", desc="x"), encoding="utf-8")
    cand = tmp_path / "up" / "category" / "cand"
    cand.mkdir(parents=True)
    (cand / "SKILL.md").write_text(
        SKILL_FIXTURE.format(name="cand", desc="y"), encoding="utf-8")
    r = run_script("scripts/compare_skills.py", str(local), str(tmp_path / "up"), "--all-candidates")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "cand" in r.stdout


# C1 — scenario executor writes benchmark-ready artifacts
def test_run_scenario_records_artifacts(tmp_path):
    stub = tmp_path / "stub.py"
    stub.write_text(
        "import json\n"
        "print(json.dumps({'type':'text','part':{'type':'text','text':'HELLO'}}))\n"
        "print(json.dumps({'type':'step_finish','part':{}}))\n",
        encoding="utf-8",
    )
    exe = sys.executable.replace("\\", "/")
    stub_path = str(stub).replace("\\", "/")
    cmd = f'"{exe}" "{stub_path}" {{prompt}}'
    run_dir = tmp_path / "run-1"
    r = run_script("scripts/run_scenario.py", "--client", "opencode",
                   "--prompt", "do x", "--run-dir", str(run_dir), "--client-cmd", cmd)
    assert r.returncode == 0, r.stdout + r.stderr
    assert (run_dir / "outputs" / "response.txt").read_text(encoding="utf-8").strip() == "HELLO"
    assert (run_dir / "transcript.md").exists()
    timing = json.loads((run_dir / "timing.json").read_text(encoding="utf-8"))
    assert "total_duration_seconds" in timing


# --- 2026-09-10 metrics.json contract audit (D1/D2) ---


def _stub_cmd(stub: Path) -> str:
    exe = sys.executable.replace("\\", "/")
    stub_path = str(stub).replace("\\", "/")
    return f'"{exe}" "{stub_path}" {{prompt}}'


# D2 — tool-call counting is JSON-parse based, not whitespace-sensitive substring count
def test_run_scenario_counts_tool_calls_from_json_stream(tmp_path):
    stub = tmp_path / "stub.py"
    stub.write_text(
        "import json\n"
        "print(json.dumps({'type':'tool','part':{}}))\n"
        "print(json.dumps({'type': 'tool', 'part': {}}))\n"
        "print(json.dumps({'type':'text','part':{'type':'text','text':'HI'}}))\n",
        encoding="utf-8",
    )
    run_dir = tmp_path / "run-1"
    r = run_script("scripts/run_scenario.py", "--client", "opencode",
                   "--prompt", "do x", "--run-dir", str(run_dir), "--client-cmd", _stub_cmd(stub))
    assert r.returncode == 0, r.stdout + r.stderr
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["total_tool_calls"] == 2


# D1 — aggregate falls back to the run-root metrics.json when execution_metrics is absent
def test_aggregate_reads_run_metrics_json_fallback(tmp_path):
    ws = tmp_path / "iteration-1"
    run = ws / "eval-x" / "with_skill" / "run-1"
    run.mkdir(parents=True)
    (run / "grading.json").write_text(json.dumps({
        "expectations": [],
        "summary": {"passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0},
        "timing": {"total_duration_seconds": 5.0},
    }), encoding="utf-8")
    (run / "metrics.json").write_text(
        json.dumps({"total_tool_calls": 7, "output_chars": 100}), encoding="utf-8")

    r = run_script("scripts/aggregate_benchmark.py", str(ws), "--skill-name", "s")
    assert r.returncode == 0, r.stdout + r.stderr
    bench = json.loads((ws / "benchmark.json").read_text(encoding="utf-8-sig"))
    assert bench["runs"][0]["result"]["tool_calls"] == 7


# D1 — grader's documented metrics.json path is the run root, not outputs/
def test_grader_docs_metrics_json_at_run_root():
    src = (ARTIFACT / "agents" / "grader.md").read_text(encoding="utf-8")
    assert "{outputs_dir}/../metrics.json" in src
    assert "{outputs_dir}/metrics.json" not in src


# D4 — run_eval summary counts scored queries only; run errors never inflate total
def test_run_eval_summary_run_errors_excluded_from_total():
    _scripts_on_path()
    try:
        from run_eval import summarize
    finally:
        _pop_path()

    s = summarize([
        {"query": "a", "should_trigger": True, "triggered": True, "pass": True},
        {"query": "b", "should_trigger": False, "triggered": False, "pass": True},
        {"query": "c", "should_trigger": True, "pass": None, "error": "boom"},
    ])
    assert s["errors"] == 1
    assert s["total"] == 2
    assert s["passed"] == 2


# D5 — run_loop ranks candidate descriptions by test pass rate, then passed count
def test_run_loop_ranks_by_test_rate():
    _scripts_on_path()
    try:
        from run_loop import _test_rank
    finally:
        _pop_path()

    # 3/3 (1.0) must outrank 4/5 (0.8) even though 4 > 3 in raw count
    assert _test_rank({"test_passed": 3, "test_total": 3}) > _test_rank({"test_passed": 4, "test_total": 5})
    # tie on rate -> higher passed count wins
    assert _test_rank({"test_passed": 3, "test_total": 6}) > _test_rank({"test_passed": 2, "test_total": 4})
