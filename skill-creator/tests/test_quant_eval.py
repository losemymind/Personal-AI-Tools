"""Tests for the quantitative eval tooling (run_eval / aggregate_benchmark / run_loop)."""

import json


def _build_workspace(root, configs=("with_skill", "without_skill")):
    ws = root / "iteration-1"
    for cfg in configs:
        run = ws / f"eval-{cfg}"
        (run / cfg / "run-1").mkdir(parents=True)
        grading = {
            "expectations": [{"text": "x", "passed": True, "evidence": "ok"}],
            "summary": {
                "passed": 6 if cfg == "with_skill" else 2,
                "failed": 1,
                "total": 7,
                "pass_rate": 0.8571 if cfg == "with_skill" else 0.2857,
            },
            "execution_metrics": {"total_tool_calls": 18, "errors_encountered": 0, "output_chars": 3800},
            "timing": {"total_duration_seconds": 45.0 if cfg == "with_skill" else 30.0},
            "user_notes_summary": {"uncertainties": [], "needs_review": [], "workarounds": []},
        }
        (run / cfg / "run-1" / "grading.json").write_text(
            json.dumps(grading), encoding="utf-8-sig"
        )
    return ws


def _skill_with_evals(root, queries):
    skill = root / "test-skill"
    (skill / "evals").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: pr-summarizer\ndescription: \"总结 git 改动，写 PR 描述，pr 摘要\"\ncategory: git\nrisk: safe\n---\n\n# pr-summarizer\n\n## 概述\n\n总结改动\n", encoding="utf-8"
    )
    (skill / "evals" / "evals.json").write_text(
        json.dumps({"skill_name": "pr-summarizer", "evals": queries}, ensure_ascii=False),
        encoding="utf-8",
    )
    return skill


def test_aggregate_benchmark_produces_json_and_md(tmp_path):
    from conftest import run_script

    ws = _build_workspace(tmp_path)
    r = run_script(
        "scripts/aggregate_benchmark.py", str(ws), "--skill-name", "pr-summarizer"
    )
    assert r.returncode == 0, r.stdout + r.stderr

    bench = json.loads((ws / "benchmark.json").read_text(encoding="utf-8-sig"))
    assert bench["metadata"]["skill_name"] == "pr-summarizer"
    assert bench["run_summary"]["with_skill"]["pass_rate"]["mean"] >= 0.8
    assert bench["run_summary"]["without_skill"]["pass_rate"]["mean"] <= 0.4
    assert bench["run_summary"]["delta"]["pass_rate"].startswith("+")

    md = (ws / "benchmark.md").read_text(encoding="utf-8")
    assert "Pass Rate" in md and "Delta" in md


def test_aggregate_benchmark_merges_analyzer_notes(tmp_path):
    from conftest import run_script

    ws = _build_workspace(tmp_path)
    notes_file = tmp_path / "notes.json"
    notes_file.write_text(
        json.dumps(
            ["断言'输出为 PDF'在两配置均 100% 通过——可能不区分技能价值", "eval 3 方差大，疑似 flaky"],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    r = run_script(
        "scripts/aggregate_benchmark.py", str(ws),
        "--skill-name", "pr-summarizer", "--notes", str(notes_file),
    )
    assert r.returncode == 0, r.stdout + r.stderr
    bench = json.loads((ws / "benchmark.json").read_text(encoding="utf-8-sig"))
    assert len(bench["notes"]) == 2
    assert "flaky" in bench["notes"][1]

    bad = tmp_path / "bad-notes.json"
    bad.write_text(json.dumps({"not": "an array"}), encoding="utf-8")
    r = run_script(
        "scripts/aggregate_benchmark.py", str(ws),
        "--skill-name", "pr-summarizer", "--notes", str(bad),
    )
    assert r.returncode == 1


def test_run_eval_heuristic_reports_summary(tmp_path):
    from conftest import run_script

    skill = _skill_with_evals(tmp_path, [
        {"id": 1, "query": "帮我总结今天的改动写 PR", "should_trigger": True},
        {"id": 2, "query": "这个函数有什么 bug？", "should_trigger": False},
    ])
    r = run_script(
        "scripts/run_eval.py",
        "--eval-set", str(skill / "evals" / "evals.json"),
        "--skill-dir", str(skill),
        "--json",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    out = json.loads(r.stdout)
    assert out["summary"]["total"] == 2
    assert out["summary"]["passed"] == 2


def test_run_eval_output_dir_writes_results(tmp_path):
    from conftest import run_script

    skill = _skill_with_evals(tmp_path, [
        {"id": 1, "query": "帮我总结今天的改动写 PR", "should_trigger": True},
        {"id": 2, "query": "这个函数有什么 bug？", "should_trigger": False},
    ])
    out_dir = tmp_path / "eval-out"
    r = run_script(
        "scripts/run_eval.py",
        "--eval-set", str(skill / "evals" / "evals.json"),
        "--skill-dir", str(skill),
        "--output-dir", str(out_dir),
    )
    assert r.returncode == 0, r.stdout + r.stderr
    payload = json.loads((out_dir / "eval-results-pr-summarizer.json").read_text(encoding="utf-8"))
    assert payload["summary"]["total"] == 2
    assert payload["mode"] == "heuristic"
    assert payload["skill_name"] == "pr-summarizer"


def test_run_loop_manual_selects_best_by_test(tmp_path, monkeypatch):
    from conftest import run_script

    # Holdout 0.4 over these 6 items -> train=3 trigger+1 non (original misses
    # "改成文件分类表" in train, so iteration 1 must fail and trigger improve);
    # test=1 trigger+1 non picks the improved description by test score.
    skill = _skill_with_evals(tmp_path, [
        {"id": 1, "query": "总结今天的 git 改动写 PR 描述", "should_trigger": True},
        {"id": 2, "query": "这个 SQL 查询有什么问题？", "should_trigger": False},
        {"id": 3, "query": "这次改动改成按文件分类的表格并标注风险", "should_trigger": True},
        {"id": 4, "query": "帮我写一个 pr summary", "should_trigger": True},
        {"id": 5, "query": "当前版本号是多少", "should_trigger": False},
        {"id": 6, "query": "把 diff 变成结构化的 review 清单", "should_trigger": True},
    ])
    report = tmp_path / "loop-report.json"
    stdin_text = tmp_path / "reply.txt"
    stdin_text.write_text(
        "<new_description>总结 git 或代码改动（diff），用于写 PR 描述、PR 摘要、pr summary、review 前梳理 diff，按文件分类并标注风险</new_description>\nEOF\n",
        encoding="utf-8",
    )

    from conftest import ARTIFACT

    with open(stdin_text) as f:
        import subprocess
        import sys

        r = subprocess.run(
            [sys.executable, str(ARTIFACT / "scripts" / "run_loop.py"),
             "--eval-set", str(skill / "evals" / "evals.json"),
             "--skill-dir", str(skill),
             "--max-iterations", "2",
             "--improve-mode", "manual",
             "--report", str(report)],
            capture_output=True, text=True, stdin=f,
            cwd=str(ARTIFACT),
        )
    assert r.returncode == 0, r.stdout + r.stderr
    out = json.loads(report.read_text(encoding="utf-8"))
    # Iteration 1 must FAIL on train (original misses the classify/risk query), which
    # triggers the improve path; then the improved description is evaluated.
    assert out["iterations_run"] >= 2
    assert out["history"][0]["train_total"] - out["history"][0]["train_passed"] >= 1
    # Best is selected by TEST score (never empty on a valid split).
    assert out["best_score"]
    assert out["exit_reason"]
