"""Independence / standalone operation of the skill-creator artifact.

The shipped artifact must work wherever it is installed, without depending on
the development workspace or host repository layout. These tests copy the
artifact outside the repo and run its own tooling to expose hidden dependencies.
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
    r = _run(dst, "scripts/skill_validate.py", "--strict", "--dir", ".")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "All skills passed" in r.stdout


def test_artifact_index_is_available_outside_repo(tmp_path):
    dst = _copy_artifact(tmp_path)
    r = _run(dst, "scripts/skill_index_search.py", "--stats")
    assert r.returncode == 0, r.stdout + r.stderr
