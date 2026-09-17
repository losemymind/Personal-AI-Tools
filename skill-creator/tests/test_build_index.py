"""Tests for build_index.py multi-source registry and helpers.

Pins the source registry (aas/addy/anthropics/composiohq/coevoskills),
root-scoped dir scanning (skills_root may be empty), the sparse API fetch used
by repos whose tarball is huge, derived provenance meta, and best-effort temp
cleanup.
"""

import importlib.util
import sqlite3
import sys
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


def test_sources_registry_has_expected_sources():
    mod = _load_module()
    assert set(mod.SOURCES) == {"aas", "addy", "anthropics", "composiohq", "coevoskills"}
    assert mod.SOURCES["anthropics"]["repo"] == "anthropics/skills"
    assert mod.SOURCES["anthropics"]["skills_root"] == "skills"
    assert "refs/heads/main.tar.gz" in mod.SOURCES["anthropics"]["tarball"]
    assert mod.SOURCES["composiohq"]["repo"] == "ComposioHQ/awesome-claude-skills"
    assert mod.SOURCES["composiohq"]["skills_root"] == ""
    assert "refs/heads/master.tar.gz" in mod.SOURCES["composiohq"]["tarball"]


def test_coevoskills_source_uses_sparse_subtree():
    """CoEvoSkills is ~600MB of task data around a 200KB skill subtree: sparse."""
    mod = _load_module()
    src = mod.SOURCES["coevoskills"]
    assert src["repo"] == "Zhang-Henry/CoEvoSkills"
    assert src["skills_root"] == "meta_skills"
    assert src["api_subtree"] == "meta_skills"
    assert src["branch"] == "main"
    assert src["index_file"] is None


def test_sparse_subtree_paths_scopes_and_prefixes(monkeypatch):
    mod = _load_module()
    calls = []

    def fake_api(url, timeout=60):
        calls.append(url)
        if "/contents/" in url:
            return [
                {"name": "tasks", "type": "dir", "sha": "TASKS"},
                {"name": "meta_skills", "type": "dir", "sha": "META"},
            ]
        return {
            "truncated": False,
            "tree": [
                {"path": "skill-creator/SKILL.md", "type": "blob"},
                {"path": "skill-creator/scripts", "type": "tree"},
                {"path": "skill-creator/scripts/run.py", "type": "blob"},
            ],
        }

    monkeypatch.setattr(mod, "_api_json", fake_api)
    paths = mod.sparse_subtree_paths("Zhang-Henry/CoEvoSkills", "main", "meta_skills")
    assert paths == ["meta_skills/skill-creator/SKILL.md", "meta_skills/skill-creator/scripts/run.py"]
    # scoped: the subtree's tree SHA is used, not a recursive listing of the repo
    tree_calls = [c for c in calls if "recursive=1" in c]
    assert tree_calls and all("META" in c for c in tree_calls)


def test_sparse_subtree_paths_missing_dir_is_unavailable(monkeypatch):
    mod = _load_module()
    monkeypatch.setattr(mod, "_api_json", lambda url, timeout=60: [{"name": "tasks", "type": "dir", "sha": "T"}])
    try:
        mod.sparse_subtree_paths("owner/repo", "main", "meta_skills")
    except mod.SourceUnavailable as e:
        assert "meta_skills" in str(e)
    else:  # pragma: no cover - the call must raise
        raise AssertionError("expected SourceUnavailable")


def test_fetch_sparse_checkout_writes_subtree_files(monkeypatch, tmp_path):
    mod = _load_module()
    monkeypatch.setattr(
        mod,
        "sparse_subtree_paths",
        lambda repo, branch, subtree: ["meta_skills/skill-creator/SKILL.md"],
    )
    monkeypatch.setattr(mod, "_read_url", lambda url, timeout=60: b"---\nname: skill-creator\n---\n")
    src = {"repo": "Zhang-Henry/CoEvoSkills", "branch": "main", "api_subtree": "meta_skills"}
    root = mod.fetch_sparse_checkout(src, tmp_path / "sparse")
    assert (root / "meta_skills" / "skill-creator" / "SKILL.md").is_file()
    # returned root is shaped like the repo root, so skills_root resolves
    assert (root / "meta_skills").is_dir()


def test_fetch_sparse_checkout_retries_then_raises(monkeypatch, tmp_path):
    mod = _load_module()
    monkeypatch.setattr(mod, "sparse_subtree_paths", lambda repo, branch, subtree: ["meta_skills/a/SKILL.md"])

    def boom(url, timeout=60):
        raise OSError("simulated network error")

    monkeypatch.setattr(mod, "_read_url", boom)
    src = {"repo": "owner/repo", "branch": "main", "api_subtree": "meta_skills"}
    try:
        mod.fetch_sparse_checkout(src, tmp_path / "sparse")
    except mod.SourceUnavailable as e:
        assert "SKILL.md" in str(e)
    else:  # pragma: no cover - the call must raise
        raise AssertionError("expected SourceUnavailable")


def test_load_source_checkout_uses_sparse_when_api_subtree(monkeypatch, tmp_path):
    """api_subtree sources never touch the tarball path."""
    mod = _load_module()

    def boom(source, dest):  # pragma: no cover - must not be called
        raise AssertionError("tarball download used for a sparse source")

    monkeypatch.setattr(mod, "download_tarball", boom)
    sparse_calls = []

    def fake_sparse(source, dest):
        sparse_calls.append(source["name"])
        return tmp_path

    monkeypatch.setattr(mod, "fetch_sparse_checkout", fake_sparse)
    monkeypatch.setattr(mod, "extract_entries", lambda root, source: [_entry("skill-creator", source["repo"])])

    class Args:
        from_extracted = None
        no_dl = False

    root, entries = mod.load_source_checkout(mod.SOURCES["coevoskills"], Args(), tmp_path)
    assert sparse_calls == ["coevoskills"]
    assert [e["name"] for e in entries] == ["skill-creator"]


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
    for name in ("aas", "addy", "anthropics", "composiohq", "coevoskills"):
        assert f"{name}(" in note
    meta = mod.sources_meta()
    assert "anthropics/skills" in meta
    assert "ComposioHQ/awesome-claude-skills" in meta
    assert "Zhang-Henry/CoEvoSkills" in meta


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


def test_offline_keeps_existing_db_and_exits_zero(monkeypatch, tmp_path):
    """Download failure + existing DB => keep committed rows, exit 0 (no fail)."""
    mod = _load_module()
    db = tmp_path / "upstream.db"
    mod.build_db([_entry("keep-me", "sickn33/agentic-awesome-skills")], tmp_path, db)
    before = db.read_bytes()

    monkeypatch.setattr(mod, "DB_PATH", db)

    def boom(source, dest):
        raise mod.SourceUnavailable("simulated offline")

    monkeypatch.setattr(mod, "download_tarball", boom)
    monkeypatch.setattr(sys, "argv", ["build_index.py", "--source", "aas"])

    rc = mod.main()
    assert rc == 0
    conn = sqlite3.connect(db)
    names = {r[0] for r in conn.execute("SELECT name FROM skills")}
    conn.close()
    assert names == {"keep-me"}  # untouched
    assert db.read_bytes() == before


def test_offline_without_db_fails(monkeypatch, tmp_path):
    """Download failure + no DB => hard failure (nothing to fall back on)."""
    mod = _load_module()
    db = tmp_path / "upstream.db"
    monkeypatch.setattr(mod, "DB_PATH", db)

    def boom(source, dest):
        raise mod.SourceUnavailable("simulated offline")

    monkeypatch.setattr(mod, "download_tarball", boom)
    monkeypatch.setattr(sys, "argv", ["build_index.py", "--source", "aas"])

    rc = mod.main()
    assert rc == 1
    assert not db.exists()


def test_multi_source_degrade_preserves_offline_rows(monkeypatch, tmp_path):
    """One offline source degrades per source: its rows survive while others sync."""
    mod = _load_module()
    db = tmp_path / "upstream.db"
    mod.build_db(
        [
            _entry("aas-skill", "sickn33/agentic-awesome-skills"),
            _entry("addy-old", "addyosmani/agent-skills"),
        ],
        tmp_path,
        db,
    )
    monkeypatch.setattr(mod, "DB_PATH", db)

    def fake_load(source, args, tmp):
        if source["name"] == "aas":
            raise mod.SourceUnavailable("simulated offline")
        return tmp_path, [_entry(source["name"] + "-new", source["repo"])]

    monkeypatch.setattr(mod, "load_source_checkout", fake_load)
    monkeypatch.setattr(sys, "argv", ["build_index.py", "--source", "all"])

    rc = mod.main()
    assert rc == 0
    conn = sqlite3.connect(db)
    names = {r[0] for r in conn.execute("SELECT name FROM skills")}
    conn.close()
    assert "aas-skill" in names      # offline source rows preserved
    assert "addy-new" in names       # reachable source re-synced
    assert "addy-old" not in names   # vanished row removed for the reachable source
