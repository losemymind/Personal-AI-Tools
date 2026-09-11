"""Repo-level independence gate for the two creators (skill-creator / agent-creator).

The repository ships two isomorphic creators that must be mutually independent:
neither may reference, import, or otherwise depend on the other. "成品即源" means
the shipped artifact directory is the source, so the independence contract is
enforced against those directories, not the workspaces around them.

Scan rules:
  - authored text/code files only: .md/.py/.sh/.json/.yaml/.yml/.txt
  - skip examples/ (upstream learning samples) and evolutions/ (historical)
  - skip indexes/upstream.db (third-party index bytes — an external repo naming
    one creator is data, not our cross-reference)
  - the forbidden set is the sibling's repo-facing name in both languages
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

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

SCAN_EXTS = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt"}
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


def test_each_creator_is_self_contained():
    for name, artifact in CREATORS.items():
        assert artifact.is_dir(), f"artifact missing: {artifact}"


def test_no_cross_references_between_creators():
    problems = []
    for name, artifact in CREATORS.items():
        tokens = FORBIDDEN[name]
        for f in _authored_files(artifact):
            text = f.read_text(encoding="utf-8", errors="replace")
            for token in tokens:
                if token in text:
                    rel = f.relative_to(artifact).as_posix()
                    problems.append(f"{name}/.../{rel}: references sibling token {token!r}")
    assert not problems, (
        "creators must not cross-reference each other (strict independence):\n"
        + "\n".join(problems)
    )


def test_no_cross_artifact_imports():
    """No script may import a module that lives in the other creator.

    Each artifact's local modules are its own scripts/*.py; an import of a sibling
    module (or a sibling name) would be a runtime dependency.
    """
    problems = []
    for name, artifact in CREATORS.items():
        sibling = "agent-creator" if name == "skill-creator" else "skill-creator"
        for f in _authored_files(artifact):
            if f.suffix != ".py":
                continue
            for lineno, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith(("import ", "from ")) and sibling in stripped:
                    problems.append(f"{name}/{f.relative_to(artifact).as_posix()}:{lineno}: {stripped}")
    assert not problems, "cross-artifact imports detected:\n" + "\n".join(problems)
