"""Shared utilities for skill-creator scripts.

Two groups of helpers live here so the CLI scripts never drift apart:

1. **Section-header patterns** (`WHEN_TO_USE_PATTERNS` / `EXAMPLES_PATTERNS` /
   `LIMITATIONS_PATTERNS` + `has_*_section`) — the single source of truth used by
   both `validate_skills.py` and `compare_skills.py`.
2. **Frontmatter / trigger helpers** — `parse_frontmatter` (PyYAML, imported
   lazily so stdlib-only callers such as `run_eval.py` stay dependency-free),
   `parse_skill_md`, `eval_query`, and the CJK-aware `keyword_tokens` / `classify`
   heuristic that `run_eval.py` reuses.

Port of the parse utility from Anthropic's official anthropics/skills
skill-creator, generalized for the four-client SKILL.md format used by this
repository (frontmatter keys name/description are common across
claude/opencode/codex/deepseek).
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Section-header patterns (single source of truth)
# ---------------------------------------------------------------------------
# English + Chinese variants accepted across the ecosystem. Keeping them in one
# module is why the validator and the comparison scorer can never disagree about
# whether a skill "has" a section.

WHEN_TO_USE_PATTERNS = [
    re.compile(r"^##\s+When\s+to\s+Use", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+When\s+to\s+Use\s+This\s+Skill", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+Use\s+this\s+skill\s+when", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+When\s+to\s+activate\s+this\s+skill", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+何时使用(?:此|这|本)*技能", re.MULTILINE),
]

EXAMPLES_PATTERNS = [
    re.compile(r"^##\s+Examples?", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+示例", re.MULTILINE),
]

LIMITATIONS_PATTERNS = [
    re.compile(r"^##\s+Limitations?", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+限制", re.MULTILINE),
]


def has_when_to_use_section(content: str) -> bool:
    return any(pattern.search(content) for pattern in WHEN_TO_USE_PATTERNS)


def has_examples_section(content: str) -> bool:
    return any(pattern.search(content) for pattern in EXAMPLES_PATTERNS)


def has_limitations_section(content: str) -> bool:
    return any(pattern.search(content) for pattern in LIMITATIONS_PATTERNS)


# ---------------------------------------------------------------------------
# Eval-item helper
# ---------------------------------------------------------------------------


def eval_query(item: dict) -> str:
    """Return an eval item's prompt text.

    Canonical key is ``query`` (see references/benchmark-schema.md). Legacy eval
    sets written from an older template may use ``prompt``; accept it as a
    fallback so those files keep working instead of raising KeyError.
    """
    return item.get("query") or item.get("prompt") or ""


# ---------------------------------------------------------------------------
# Frontmatter parsing (PyYAML imported lazily)
# ---------------------------------------------------------------------------


def _normalize_yaml_value(value):
    from collections.abc import Mapping
    from datetime import date, datetime

    if isinstance(value, Mapping):
        return {key: _normalize_yaml_value(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_normalize_yaml_value(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def parse_frontmatter(content: str):
    """Parse a SKILL.md frontmatter block with PyYAML.

    Returns ``(metadata, error_messages)``. ``metadata`` is a plain dict on
    success or ``None`` on failure. PyYAML is imported lazily so stdlib-only
    callers (e.g. run_eval.py) never require the dependency.
    """
    import yaml

    fm_match = re.search(r"^---\s*\n(.*?)\n?---(?:\s*\n|$)", content, re.DOTALL)
    if not fm_match:
        return None, ["Missing or malformed YAML frontmatter"]

    fm_errors: list[str] = []
    try:
        metadata = yaml.safe_load(fm_match.group(1)) or {}
        metadata = _normalize_yaml_value(metadata)
        if not isinstance(metadata, dict):
            return None, ["Frontmatter must be a YAML mapping/object."]

        if "description" in metadata:
            desc = metadata["description"]
            if not desc or (isinstance(desc, str) and not desc.strip()):
                fm_errors.append("description field is empty or whitespace only.")
            elif desc == "|":
                fm_errors.append(
                    "description contains only the YAML block indicator '|', "
                    "likely due to a parsing regression."
                )

        return dict(metadata), fm_errors
    except yaml.YAMLError as e:
        return None, [f"YAML Syntax Error: {e}"]


# ---------------------------------------------------------------------------
# Line-based skill parser (no PyYAML; used by run_eval / run_loop)
# ---------------------------------------------------------------------------


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a skill's SKILL.md, returning (name, description, full_content).

    Handles single-line and YAML-block-scalar descriptions (> / | / >- / |-).
    """
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8-sig")
    lines = content.split("\n")

    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    name = ""
    description = ""
    fm_lines = lines[1:end_idx]
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(fm_lines) and (
                    fm_lines[i].startswith("  ") or fm_lines[i].startswith("\t")
                ):
                    continuation_lines.append(fm_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            description = value.strip().strip('"').strip("'")
        i += 1

    return name, description, content


# ---------------------------------------------------------------------------
# CJK-aware trigger heuristic (deterministic, no external CLI)
# ---------------------------------------------------------------------------
#
# The heuristic is a keyword-overlap proxy, not an authoritative trigger test
# (real client runs are authoritative — see SKILL.md stage 7). CJK text has no
# spaces, so a word-based tokenizer collapses an entire Chinese phrase into one
# token and overlap can never reach the threshold. We therefore emit CJK
# bigrams (and latin words) as the comparable tokens.

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

_TRIGGER_STOP = {
    "skill", "使用", "技能", "when", "use", "this", "user", "should", "the", "a",
}


def keyword_tokens(text: str) -> list[str]:
    """Tokenize for trigger overlap: latin words + CJK unigrams/bigrams.

    CJK is split into bigrams so Chinese phrases share tokens with a description
    (e.g. 总结我的改动 vs a description containing 总结/改动). Bigrams are what
    `classify` compares; unigrams are emitted for callers that want them.
    """
    text = text.lower()
    tokens = re.findall(r"[a-z0-9][a-z0-9-]*", text)
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(run) == 1:
            tokens.append(run)
            continue
        tokens.extend(run)  # unigrams
        tokens.extend(run[i:i + 2] for i in range(len(run) - 1))  # bigrams
    return tokens


def classify(prompt: str, description: str) -> bool:
    """Deterministic heuristic: does the prompt share >=2 distinct meaningful tokens?

    Meaningful tokens are latin words (len >= 2) and CJK bigrams (len == 2);
    CJK unigrams are intentionally excluded to avoid single-common-character
    false positives. Tokens are compared as *sets*: a term repeated in the
    description (e.g. 创建 appearing three times) is one shared token, not three —
    counting occurrences would let any single-word overlap cross the threshold.
    """
    tokens = keyword_tokens(description)
    meaningful = {t for t in tokens if t not in _TRIGGER_STOP and len(t) >= 2}
    prompt_tokens = set(keyword_tokens(prompt))
    return len(meaningful & prompt_tokens) >= 2
