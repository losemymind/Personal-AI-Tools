"""Tests for the agent review loop (ai reviewer subagent + gold-standard injection).

Pins the no-human review-loop contract: the shipped reviewer subagent exposes a
`review.json` verdict contract, SKILL.md routes review to it (no human/UI loop),
and run_loop.py injects the best-so-far description as a gold-standard precedent.
"""

from conftest import ARTIFACT


def test_reviewer_subagent_and_contract_present():
    reviewer = (ARTIFACT / "agents" / "reviewer.md").read_text(encoding="utf-8")
    for token in ("review.json", "verdict", "pass", "revise", "issues",
                  "previous_review_path", "fixes_verified", "review_target"):
        assert token in reviewer, f"agents/reviewer.md must define '{token}'"

    skill = (ARTIFACT / "SKILL.md").read_text(encoding="utf-8")
    assert "agents/reviewer.md" in skill, "SKILL.md must route review to agents/reviewer.md"
    assert "AI 评审闭环" in skill


def test_no_human_review_loop_leftovers():
    skill = (ARTIFACT / "SKILL.md").read_text(encoding="utf-8")
    assert "人审闭环" not in skill, "the human review loop must be replaced by the agent loop"
    assert "带反馈 UI" not in skill, "no UI-based human review should remain"

    evolutions = ARTIFACT / "evolutions"
    assert (evolutions / "2026-09-10-adopt-agent-review-loop.md").is_file()
    assert not (evolutions / "2026-09-09-adopt-human-review-ui-loop.md").exists()


def test_build_improve_prompt_injects_gold_standard():
    import sys

    sys.path.insert(0, str(ARTIFACT / "scripts"))
    try:
        from run_loop import build_improve_prompt
    finally:
        sys.path.pop(0)

    train = [{"query": "x", "should_trigger": True, "pass": False}]
    with_precedent = build_improve_prompt("s", "body", "current-desc", train, "best-desc")
    assert "best-desc" in with_precedent
    assert "best_so_far" in with_precedent

    same = build_improve_prompt("s", "body", "current-desc", train, "current-desc")
    assert "best_so_far" not in same

    none = build_improve_prompt("s", "body", "current-desc", train, "")
    assert "best_so_far" not in none
