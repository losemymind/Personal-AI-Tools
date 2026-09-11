"""Repo-level independence gate for the two creators (skill-creator / agent-creator).

The repository ships two isomorphic creators that must be mutually independent:
neither may reference, import, or otherwise depend on the other. "成品即源" means
the shipped artifact directory is the source, so the independence contract is
enforced against those directories, not the workspaces around them.

Scan rules:
  - authored text/code files only: .md/.py/.sh/.json/.yaml/.yml/.txt/.template
    (templates/*.json.template and the like ship with the artifact too)
  - token matching is case-insensitive: a cross-reference written as
    "Agent-Creator" couples the artifacts just as much as the exact spelling
  - skip examples/ (upstream learning samples) and evolutions/ (historical
    cross-creator comparison/borrowing records). These DELIBERATELY name the
    sibling — an evolution note exists to record "what we learned from the other
    creator" — so scanning them would be a false-positive storm, not a contract
    violation. This is an intentional exclusion, covered by a regression test.
  - skip indexes/upstream.db (third-party index bytes — an external repo naming
    one creator is data, not our cross-reference)
  - the forbidden set is the sibling's repo-facing name in both languages
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

IMPORT_MODULE_RE = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)")

CREATORS = {
    "skill-creator": REPO_ROOT / "skill-creator" / "skills" / "skill-creator",
    "agent-creator": REPO_ROOT / "agent-creator" / "skills" / "agent-creator",
}

# artifact name -> tokens that must never appear in that artifact.
# Covers the sibling's repo-facing name (both languages) AND the sibling's own
# script/module names: naming the other creator's file is still a cross-reference
# (and a maintenance coupling), even when no code import exists.
FORBIDDEN = {
    "skill-creator": (
        "agent-creator", "代理创建器",
        "adapt_agent", "package_agent", "validate_agents", "security_scan",
        "search_agent_index", "build_agent_index", "compare_agents", "create_agent",
    ),
    "agent-creator": (
        "skill-creator", "技能创建器",
        "package_skill", "validate_skills", "search_index", "build_index",
        "run_eval", "run_loop", "run_scenario", "compare_skills", "create_skill",
        "aggregate_benchmark",
    ),
}

SCAN_EXTS = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt", ".template"}
SKIP_DIRS = {"examples", "evolutions", "__pycache__"}
SKIP_FILES = {"upstream.db"}


def _authored_files(artifact: Path):
    for p in sorted(artifact.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(artifact)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if p.name in SKIP_FILES:
            continue
        if p.suffix.lower() not in SCAN_EXTS:
            continue
        yield p


def _scan_for_tokens(artifact: Path, tokens) -> list[str]:
    """Return one 'relpath: token' problem per authored file that names a token.

    Case-insensitive; the artifact root is arbitrary so tests can point it at a
    fixture dir as well as the real shipped artifact.
    """
    problems = []
    lowered = [(t, t.lower()) for t in tokens]
    for f in _authored_files(artifact):
        text = f.read_text(encoding="utf-8", errors="replace").lower()
        for token, token_lc in lowered:
            if token_lc in text:
                problems.append(f"{f.relative_to(artifact).as_posix()}: {token!r}")
    return problems


def test_each_creator_is_self_contained():
    for name, artifact in CREATORS.items():
        assert artifact.is_dir(), f"artifact missing: {artifact}"


def test_no_cross_references_between_creators():
    problems = []
    for name, artifact in CREATORS.items():
        for p in _scan_for_tokens(artifact, FORBIDDEN[name]):
            problems.append(f"{name}/.../{p}")
    assert not problems, (
        "creators must not cross-reference each other (strict independence):\n"
        + "\n".join(problems)
    )


def test_scan_catches_template_files_and_case_variants(tmp_path):
    """`.template` files are authored artifacts, and a casing variant is still a
    cross-reference — both must be caught (regression: they used to slip)."""
    artifact = tmp_path / "art"
    (artifact / "templates").mkdir(parents=True)
    (artifact / "templates" / "x.json.template").write_text(
        '{"skill_name": "AGENT-CREATOR"}', encoding="utf-8"
    )
    problems = _scan_for_tokens(artifact, FORBIDDEN["skill-creator"])
    assert problems, "a sibling token in a .template file (different case) must be flagged"
    assert any("x.json.template" in p for p in problems)


def test_scan_skips_evolutions_and_examples_by_design(tmp_path):
    """Historical records and upstream samples intentionally name the sibling;
    the scan must not treat them as contract violations."""
    artifact = tmp_path / "art"
    (artifact / "evolutions").mkdir(parents=True)
    (artifact / "examples" / "sample").mkdir(parents=True)
    (artifact / "evolutions" / "2026-01-01-adopt.md").write_text(
        "learned from agent-creator", encoding="utf-8"
    )
    (artifact / "examples" / "sample" / "SKILL.md").write_text(
        "compare against agent-creator", encoding="utf-8"
    )
    assert _scan_for_tokens(artifact, FORBIDDEN["skill-creator"]) == []


def test_no_cross_artifact_imports():
    """No script may import a module that lives in the other creator's scripts/.

    A real cross-artifact import cannot spell the sibling's hyphenated name
    (invalid Python identifier), so the previous substring test was vacuously
    true. This checks imported top-level module names against the sibling's
    script module stems instead (excluding modules the checks' own creator also
    ships, so importing one's local _project_paths.py is not a false positive).
    """
    problems = []
    for name, artifact in CREATORS.items():
        sibling = "agent-creator" if name == "skill-creator" else "skill-creator"
        own_modules = {p.stem for p in (artifact / "scripts").glob("*.py")}
        sibling_modules = (
            {p.stem for p in (CREATORS[sibling] / "scripts").glob("*.py")} - own_modules
        )
        for f in _authored_files(artifact):
            if f.suffix != ".py":
                continue
            for lineno, line in enumerate(
                f.read_text(encoding="utf-8", errors="replace").splitlines(), 1
            ):
                m = IMPORT_MODULE_RE.match(line)
                if not m:
                    continue
                mod = m.group(1).split(".")[0]
                if mod in sibling_modules:
                    problems.append(
                        f"{name}/{f.relative_to(artifact).as_posix()}:{lineno}: "
                        f"imports sibling module {mod!r}"
                    )
    assert not problems, "cross-artifact imports detected:\n" + "\n".join(problems)
