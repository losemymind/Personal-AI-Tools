"""Tests for the agent-creator review loop (ai reviewer subagent, no-human review).

The shipped reviewer
subagent exposes a `review.json` verdict contract and SKILL.md routes review to
it instead of a human step.
"""

from conftest import ARTIFACT


def test_reviewer_subagent_and_contract_present():
    reviewer = (ARTIFACT / "agents" / "agent_reviewer.md").read_text(encoding="utf-8")
    for token in ("review.json", "verdict", "pass", "revise", "issues",
                  "previous_review_path", "fixes_verified", "review_target"):
        assert token in reviewer, f"agents/agent_reviewer.md must define '{token}'"

    skill = (ARTIFACT / "SKILL.md").read_text(encoding="utf-8")
    assert "agents/agent_reviewer.md" in skill, "SKILL.md must route review to agents/agent_reviewer.md"
    assert "AI 评审闭环" in skill


def test_agent_review_evolution_recorded():
    summary = (ARTIFACT / "evolutions" / "methodology.md").read_text(encoding="utf-8")
    for decision in ('id="review"', "review.json", "max-iterations", "授权与高风险"):
        assert decision in summary
