"""Independence / standalone operation of the skill-creator artifact.

The shipped artifact must work wherever it is installed: no dependency on this
workspace, the sibling creator, or the host repository layout. These tests copy
the artifact to a temp dir OUTSIDE the repo and run its own tooling there, so a
hidden dependency on the repo tree (or on the other creator) would surface as a
failure.
"""

import shutil
import subprocess
import sys
from pathlib import Path

from conftest import ARTIFACT

IGNORE = shutil.ignore_patterns(
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"
)


def _copy_artifact(tmp_path: Path) -> Path:
    dst = tmp_path / "elsewhere" / "skill-creator"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ARTIFACT, dst, ignore=IGNORE)
    return dst


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(cwd),
    )


def test_artifact_self_validates_outside_repo(tmp_path):
    dst = _copy_artifact(tmp_path)
    r = _run(dst, "scripts/validate_skills.py", "--strict", "--dir", ".")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "All skills passed" in r.stdout


def test_artifact_index_is_available_outside_repo(tmp_path):
    dst = _copy_artifact(tmp_path)
    r = _run(dst, "scripts/search_index.py", "--stats")
    assert r.returncode == 0, r.stdout + r.stderr


def test_artifact_has_no_sibling_reference():
    """No authored artifact file may name the sibling creator's scripts/name.

    Case-insensitive, and `.template` files count (they ship too). Historical
    `evolutions/` and upstream `examples/` are excluded by design: they
    deliberately name the sibling when recording what was borrowed.
    """
    forbidden = (
        "agent-creator", "代理创建器", "adapt_agent", "package_agent",
        "validate_agents", "security_scan", "search_agent_index",
        "build_agent_index", "compare_agents", "create_agent",
    )
    skip_dirs = {"examples", "evolutions", "__pycache__"}
    problems = []
    for p in ARTIFACT.rglob("*"):
        if not p.is_file() or p.name == "upstream.db":
            continue
        rel = p.relative_to(ARTIFACT)
        if any(part in skip_dirs for part in rel.parts):
            continue
        if p.suffix.lower() not in {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt", ".template"}:
            continue
        text = p.read_text(encoding="utf-8", errors="replace").lower()
        for token in forbidden:
            if token.lower() in text:
                problems.append(f"{rel.as_posix()}: {token!r}")
    assert not problems, "skill-creator artifact references its sibling:\n" + "\n".join(problems)
