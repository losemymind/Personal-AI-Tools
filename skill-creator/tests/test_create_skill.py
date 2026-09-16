"""Tests for create_skill.py scaffold generator."""

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR.parent / "skills" / "skill-creator" / "scripts"))

from create_skill import main


def test_out_dir_name_matches_skill_name(tmp_path, monkeypatch):
    """--out 已指向目标目录时应 fails loudly."""
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [
        "create_skill.py",
        "--name", "test-skill",
        "--category", "productivity",
        "--risk", "safe",
        "--out", str(skill_dir),
        "--no-interactive"
    ])
    
    result = main()
    assert result == 1


def test_normal_out_dir_with_subdir_name(tmp_path, monkeypatch):
    """--out 指向父目录且 name 不同应成功。"""
    out_dir = tmp_path / "skills"
    out_dir.mkdir()
    
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", [
        "create_skill.py",
        "--name", "test-skill",
        "--category", "productivity",
        "--risk", "safe",
        "--out", str(out_dir),
        "--no-interactive"
    ])
    
    result = main()
    assert result == 0
    assert (out_dir / "test-skill" / "SKILL.md").exists()
