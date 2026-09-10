"""Tests for the evals.json schema contract (query vs legacy prompt).

Regression guard for the template/script key drift: the canonical eval key is
`query` (references/benchmark-schema.md, run_eval.py, run_loop.py). The template
once shipped `prompt`, which made run_eval.py raise KeyError. These tests pin
the canonical key and keep a legacy fallback working.
"""

import json

from conftest import ARTIFACT


def _skill_with_evals(root, evals):
    skill = root / "test-skill"
    (skill / "evals").mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: pr-summarizer\ndescription: \"总结 git 改动，写 PR 描述，pr 摘要\"\n"
        "category: git\nrisk: safe\n---\n\n# pr-summarizer\n\n## 概述\n\n总结改动\n",
        encoding="utf-8",
    )
    (skill / "evals" / "evals.json").write_text(
        json.dumps({"skill_name": "pr-summarizer", "evals": evals}, ensure_ascii=False),
        encoding="utf-8",
    )
    return skill


def test_template_uses_canonical_query_key():
    """The shipped template must use `query`, never legacy `prompt`."""
    template = json.loads(
        (ARTIFACT / "templates" / "evals.json.template").read_text(encoding="utf-8")
    )
    for item in template["evals"]:
        assert "query" in item, "evals.json.template must key the prompt as 'query'"
        assert "prompt" not in item, "evals.json.template must not use the legacy 'prompt' key"


def test_eval_query_helper_prefers_query_and_falls_back():
    import sys

    sys.path.insert(0, str(ARTIFACT / "scripts"))
    try:
        from utils import eval_query
    finally:
        sys.path.pop(0)

    assert eval_query({"query": "canonical"}) == "canonical"
    assert eval_query({"prompt": "legacy"}) == "legacy"
    assert eval_query({"query": "canonical", "prompt": "legacy"}) == "canonical"
    assert eval_query({}) == ""


def test_run_eval_accepts_legacy_prompt_key(tmp_path):
    """Legacy eval files keyed `prompt` must not crash run_eval.py."""
    from conftest import run_script

    skill = _skill_with_evals(tmp_path, [
        {"id": 1, "prompt": "帮我总结今天的改动写 PR", "should_trigger": True},
        {"id": 2, "prompt": "这个函数有什么 bug？", "should_trigger": False},
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
    assert out["results"][0]["query"] == "帮我总结今天的改动写 PR"


def test_run_trigger_tests_reads_query_and_emits_query(tmp_path):
    from conftest import run_script

    skill = _skill_with_evals(tmp_path, [
        {"id": 1, "query": "总结 git 改动写 PR", "should_trigger": True},
        {"id": 2, "query": "今天天气怎么样", "should_trigger": False},
    ])
    r = run_script(
        "scripts/run_trigger_tests.py", str(skill),
        "--evals", str(skill / "evals" / "evals.json"),
        "--json",
    )
    assert r.returncode == 0, r.stdout + r.stderr
    out = json.loads(r.stdout)
    assert out["results"][0]["query"] == "总结 git 改动写 PR"
    assert "prompt" not in out["results"][0]
