"""Immutable fetch revisions and honest provenance across sync modes."""

import importlib
import json
import sqlite3
import sys
from types import SimpleNamespace

import pytest

from conftest import ARTIFACT


@pytest.fixture
def index(monkeypatch):
    monkeypatch.syspath_prepend(str(ARTIFACT / "scripts"))
    return importlib.import_module("skill_index_build")


def test_sparse_download_keeps_revision_when_branch_moves(index, monkeypatch, tmp_path):
    sha = "a" * 40
    calls = []

    def api(url, **kw):
        calls.append(url)
        if "/commits/" in url:
            return {"sha": sha}
        if "/contents/" in url:
            assert url.endswith("ref=" + sha)
            return [{"name": "meta_skills", "type": "dir", "sha": "b" * 40}]
        return {"tree": [{"type": "blob", "path": "sample/SKILL.md"}], "truncated": False}

    def read(url, **kw):
        calls.append(url)
        assert "/" + sha + "/meta_skills/" in url  # never moving main
        return b"---\nname: sample\ndescription: sample\n---\nbody\n"

    monkeypatch.setattr(index, "_api_json", api)
    monkeypatch.setattr(index, "_read_url", read)
    source = dict(index.SOURCES["coevoskills"])
    _, entries = index.load_source_checkout(source, SimpleNamespace(from_extracted=None, no_dl=False), tmp_path)
    assert len([url for url in calls if "/commits/" in url]) == 1
    assert entries[0]["_provenance"]["upstream_commit"] == sha
    assert "upstream_commit" not in source  # registry remains reusable


def test_archive_url_and_metadata_share_commit(index, monkeypatch, tmp_path):
    monkeypatch.setattr(index, "_api_json", lambda *a, **kw: {"sha": "c" * 40})
    seen = []
    monkeypatch.setattr(index, "download_tarball", lambda source, dest: seen.append(source) or tmp_path / "archive.tgz")
    monkeypatch.setattr(index, "unpack_tarball", lambda *a: tmp_path)
    monkeypatch.setattr(index, "extract_entries", lambda root, src: [{"name": "x", "source_repo": src["repo"]}])
    _, entries = index.load_source_checkout(index.SOURCES["composiohq"], SimpleNamespace(from_extracted=None, no_dl=False), tmp_path)
    assert seen[0]["tarball"].endswith("/" + "c" * 40 + ".tar.gz")
    assert entries[0]["_provenance"] == {"upstream_commit": "c" * 40, "source_ref": "master", "fetch_mode": "archive"}


@pytest.mark.parametrize("payload", [{}, {"sha": "short"}, [], {"sha": "z" * 40}])
def test_invalid_remote_revision_rejected(index, monkeypatch, payload):
    monkeypatch.setattr(index, "_api_json", lambda *a, **kw: payload)
    with pytest.raises(index.SourceUnavailable):
        index.pin_source(index.SOURCES["addy"])


def test_revision_preserved_on_failure_and_cleared_for_local(index, monkeypatch, tmp_path):
    repo = "owner/repo"
    provenance = {"upstream_commit": "a" * 40, "source_ref": "main", "fetch_mode": "sparse"}
    entries = [{"name": "x", "path": "x", "source_repo": repo, "_provenance": provenance}]
    db = tmp_path / "index.db"
    index.build_db(entries, tmp_path, db)

    def state():
        with sqlite3.connect(db) as conn:
            return json.loads(conn.execute("SELECT value FROM meta WHERE key=?", ("source_status:" + repo,)).fetchone()[0])

    before = state()
    index.record_source_failure(db, repo, "offline")
    assert state()["upstream_commit"] == provenance["upstream_commit"]
    assert state()["snapshot_sha256"] == before["snapshot_sha256"]
    monkeypatch.setattr(index, "_api_json", lambda *a, **kw: pytest.fail("local checkout must not fetch remote HEAD"))
    monkeypatch.setattr(index, "extract_entries", lambda *a: [{"name": "x", "path": "x", "source_repo": repo}])
    _, local = index.load_source_checkout({"repo": repo}, SimpleNamespace(from_extracted=str(tmp_path), no_dl=False), tmp_path)
    index.update_db_incremental(local, tmp_path, db, repo)
    assert state()["upstream_commit"] is None
    assert state()["fetch_mode"] == "local"


def test_repeated_builds_use_fresh_scratch(index, monkeypatch, tmp_path):
    scratch = []
    def checkout(source, args, work):
        scratch.append(work)
        assert not (work / "old-skill").exists()
        (work / "old-skill").write_text("old", encoding="utf-8")
        return tmp_path, []
    monkeypatch.setattr(index, "load_source_checkout", checkout)
    monkeypatch.setattr(index, "DB_PATH", tmp_path / "absent.db")
    monkeypatch.setattr(sys, "argv", ["skill_index_build.py", "--source", "addy"])
    assert index.main() == index.main() == 1
    assert scratch[0] != scratch[1]
    assert not any(path.exists() for path in scratch)
