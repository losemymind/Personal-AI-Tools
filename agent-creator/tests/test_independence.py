"""Independence / standalone operation of the agent-creator artifact.

The shipped artifact must work wherever it is installed: no dependency on this
workspace, the sibling creator, or the host repository layout. These tests copy
the artifact to a temp dir OUTSIDE the repo and run its own toolchain there:
index stats + scaffold -> validate round trip.
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = REPO_ROOT / "skills" / "agent-creator"

IGNORE = shutil.ignore_patterns(
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"
)


def _copy_artifact(tmp_path: Path) -> Path:
    dst = tmp_path / "elsewhere" / "agent-creator"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ARTIFACT, dst, ignore=IGNORE)
    return dst


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(cwd),
    )


def test_artifact_index_is_available_outside_repo(tmp_path):
    dst = _copy_artifact(tmp_path)
    r = _run(dst, "scripts/search_agent_index.py", "--stats")
    assert r.returncode == 0, r.stdout + r.stderr


def test_artifact_scaffold_and_validate_round_trip_outside_repo(tmp_path):
    dst = _copy_artifact(tmp_path)
    out = dst / "iso-check-tmp"
    r1 = _run(dst, "scripts/create_agent.py", "--name", "iso-check",
              "--mode", "subagent", "--no-interactive", "--out", str(out))
    assert r1.returncode == 0, r1.stdout + r1.stderr
    r2 = _run(dst, "scripts/validate_agents.py", "--strict", "--dir", str(out))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "All agents passed" in r2.stdout


def test_artifact_has_no_sibling_reference():
    """No authored artifact file may name the sibling creator's scripts/name."""
    forbidden = (
        "skill-creator", "技能创建器", "package_skill", "validate_skills",
        "search_index", "build_index", "run_eval", "run_loop", "run_scenario",
        "compare_skills", "create_skill", "aggregate_benchmark",
    )
    skip_dirs = {"examples", "evolutions", "__pycache__"}
    problems = []
    for p in ARTIFACT.rglob("*"):
        if not p.is_file() or p.name == "upstream.db":
            continue
        rel = p.relative_to(ARTIFACT)
        if any(part in skip_dirs for part in rel.parts):
            continue
        if p.suffix.lower() not in {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt"}:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for token in forbidden:
            if token in text:
                problems.append(f"{rel.as_posix()}: {token!r}")
    assert not problems, "agent-creator artifact references its sibling:\n" + "\n".join(problems)
