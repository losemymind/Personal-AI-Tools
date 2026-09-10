"""Tests for build_index.py multi-source registry and helpers.

Pins the source registry (aas/addy/anthropics/composiohq), root-scoped dir
scanning (skills_root may be empty), derived provenance meta, and best-effort
temp cleanup.
"""

import importlib.util
import sqlite3
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BUILD_INDEX = REPO_ROOT / "skills" / "skill-creator" / "scripts" / "build_index.py"

SKILL_MD = """---
name: {name}
description: "a test skill"
category: testing
risk: safe
---

# {name}
"""


def _load_module():
    spec = importlib.util.spec_from_file_location("build_index", BUILD_INDEX)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def test_sources_registry_has_four_sources():
    mod = _load_module()
    assert set(mod.SOURCES) == {"aas", "addy", "anthropics", "composiohq"}
    assert mod.SOURCES["anthropics"]["repo"] == "anthropics/skills"
    assert mod.SOURCES["anthropics"]["skills_root"] == "skills"
    assert "refs/heads/main.tar.gz" in mod.SOURCES["anthropics"]["tarball"]
    assert mod.SOURCES["composiohq"]["repo"] == "ComposioHQ/awesome-claude-skills"
    assert mod.SOURCES["composiohq"]["skills_root"] == ""
    assert "refs/heads/master.tar.gz" in mod.SOURCES["composiohq"]["tarball"]


def test_scan_skill_dir_nested_root():
    mod = _load_module()
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        (repo / "skills" / "my-skill").mkdir(parents=True)
        (repo / "skills" / "my-skill" / "SKILL.md").write_text(
            SKILL_MD.format(name="my-skill"), encoding="utf-8"
        )
        (repo / "skills" / "not-a-skill").mkdir()
        entries = mod.scan_skill_dir(repo, mod.SOURCES["anthropics"])
        assert [e["path"] for e in entries] == ["skills/my-skill"]


def test_scan_skill_dir_empty_root_has_no_leading_slash():
    mod = _load_module()
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        (repo / "artifacts-builder").mkdir()
        (repo / "artifacts-builder" / "SKILL.md").write_text(
            SKILL_MD.format(name="artifacts-builder"), encoding="utf-8"
        )
        (repo / "README.md").write_text("not a skill", encoding="utf-8")
        (repo / "no-skill").mkdir()
        (repo / ".github").mkdir()
        entries = mod.scan_skill_dir(repo, mod.SOURCES["composiohq"])
        assert [e["path"] for e in entries] == ["artifacts-builder"]
        assert not entries[0]["path"].startswith("/")


def test_provenance_meta_covers_all_sources():
    mod = _load_module()
    note = mod.data_source_note()
    for name in ("aas", "addy", "anthropics", "composiohq"):
        assert f"{name}(" in note
    meta = mod.sources_meta()
    assert "anthropics/skills" in meta
    assert "ComposioHQ/awesome-claude-skills" in meta


def _entry(name, repo):
    return {
        "name": name,
        "path": name,
        "description": "d",
        "category": None,
        "risk": None,
        "source": "community",
        "source_repo": repo,
    }


def test_incremental_refreshes_total_and_sources_meta():
    mod = _load_module()
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "index.db"
        mod.build_db([_entry("one", "sickn33/agentic-awesome-skills")], Path(d), db)
        mod.update_db_incremental(
            [_entry("two", "ComposioHQ/awesome-claude-skills")], Path(d), db
        )
        conn = sqlite3.connect(db)
        meta = dict(conn.execute("SELECT key, value FROM meta"))
        assert meta["skill_count"] == "2"  # total, not per-source
        assert "composiohq(" in meta["data_source"]
        assert "ComposioHQ/awesome-claude-skills" in meta["sources"]
        conn.close()


def test_cleanup_tmp_removes_normal_dir():
    mod = _load_module()
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "scratch"
        (tmp / "a").mkdir(parents=True)
        (tmp / "a" / "f.txt").write_text("x", encoding="utf-8")
        mod.cleanup_tmp(tmp, keep=False)  # must not raise
        assert not (tmp / "a" / "f.txt").exists()


def test_cleanup_tmp_keep_is_noop():
    mod = _load_module()
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "scratch"
        tmp.mkdir()
        (tmp / "f.txt").write_text("x", encoding="utf-8")
        mod.cleanup_tmp(tmp, keep=True)
        assert (tmp / "f.txt").exists()
