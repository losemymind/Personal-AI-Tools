"""Independence / standalone operation of the agent-creator artifact.

The shipped artifact must work wherever it is installed: no dependency on this
workspace or the host repository layout. These tests copy
the artifact to a temp dir OUTSIDE the repo and run its own toolchain there:
index stats + scaffold -> validate round trip.
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

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
    r = _run(dst, "scripts/agent_index_search.py", "--stats")
    assert r.returncode == 0, r.stdout + r.stderr


def test_artifact_scaffold_and_validate_round_trip_outside_repo(tmp_path):
    dst = _copy_artifact(tmp_path)
    out = dst / "iso-check-tmp"
    r1 = _run(dst, "scripts/agent_create.py", "--name", "iso-check",
              "--mode", "subagent", "--no-interactive", "--out", str(out))
    assert r1.returncode == 0, r1.stdout + r1.stderr
    r2 = _run(dst, "scripts/agent_validate.py", "--strict", "--dir", str(out))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert "All agents passed" in r2.stdout
    packaged = tmp_path / "packages"
    r3 = _run(tmp_path, str(dst / "scripts" / "agent_package.py"),
              str(out / "iso-check.md"), "--client", "codex",
              "--out", str(packaged), "--zip")
    assert r3.returncode == 0, r3.stdout + r3.stderr
    assert (packaged / "codex" / "iso-check" / "AGENT.md").is_file()
    assert (packaged / "codex" / "iso-check.zip").is_file()


@pytest.mark.parametrize("entrypoint", [
    "agent_adapt.py", "agent_index_build.py", "agent_compare.py",
    "agent_create.py", "agent_package.py", "agent_index_search.py",
    "agent_validate.py",
])
def test_cli_help_from_unrelated_working_directory(tmp_path, entrypoint):
    """An installed entrypoint must resolve its local imports from any cwd."""
    dst = _copy_artifact(tmp_path)
    cwd = tmp_path / "caller"
    cwd.mkdir()
    result = _run(cwd, str(dst / "scripts" / entrypoint), "--help")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "usage:" in result.stdout.lower()
    assert entrypoint in result.stdout
