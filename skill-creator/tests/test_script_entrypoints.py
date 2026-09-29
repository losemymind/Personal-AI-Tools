"""CLI migration: every public tool runs from an isolated product copy."""

import shutil
import subprocess
import sys

import pytest

from conftest import ARTIFACT


CLI_NAMES = (
    "skill_validate", "skill_create", "skill_package", "skill_compare",
    "skill_eval", "skill_optimize", "skill_scenario", "skill_benchmark",
    "skill_index_build", "skill_index_search",
)


@pytest.fixture(scope="module")
def isolated_product(tmp_path_factory):
    root = tmp_path_factory.mktemp("renamed-product")
    product = root / "skill-creator"
    shutil.copytree(ARTIFACT, product, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return product


@pytest.mark.parametrize("name", CLI_NAMES)
def test_public_cli_help_from_unrelated_cwd(name, isolated_product, tmp_path):
    result = subprocess.run(
        [sys.executable, str(isolated_product / "scripts" / f"{name}.py"), "--help"],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert f"{name}.py" in result.stdout


def test_product_exposes_only_current_entrypoints_and_helpers():
    assert {p.stem for p in (ARTIFACT / "scripts").glob("*.py")} == {
        *CLI_NAMES, "skill_utils", "skill_events", "_project_paths",
    }
