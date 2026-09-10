"""Build a searchable SQLite index of upstream skill catalogs (multi-source).

Part of the skill-creator skill. See references/skill-index.md.

Sources:
  - aas        : sickn33/agentic-awesome-skills      (official skills_index.json + dir scan; ~2100 skills)
  - addy       : addyosmani/agent-skills             (scanned skills/*/SKILL.md; 25 skills, no index file)
  - anthropics : anthropics/skills                   (scanned skills/*/SKILL.md; small official catalog)
  - composiohq : ComposioHQ/awesome-claude-skills    (scanned */SKILL.md at repo root; no index file)

Every row carries a `source_repo` column; `path` is unique per source so the
incremental sync scopes by (source_repo, path).

Usage:
    python scripts/build_index.py                          # all sources, full rebuild
    python scripts/build_index.py --source aas             # only sickn33 (tarball)
    python scripts/build_index.py --source addy            # only addyosmani (scan)
    python scripts/build_index.py --source anthropics      # only anthropics/skills
    python scripts/build_index.py --source composiohq      # only awesome-claude-skills
    python scripts/build_index.py --incremental            # reuse upstream.db
    python scripts/build_index.py --from-extracted <dir>   # use an already-checked-out repo
    python scripts/build_index.py --no-dl                  # scan <repo>/skills locally

Exit code 0 = success.
"""

import argparse
import io
import json
import os
import re
import sqlite3
import sys
import tarfile
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
INDEX_DIR = SCRIPT_DIR.parent / "indexes"
DB_PATH = INDEX_DIR / "upstream.db"
INDEX_VERSION = 4

# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------

SOURCES = {
    "aas": {
        "name": "aas",
        "repo": "sickn33/agentic-awesome-skills",
        "tarball": "https://github.com/sickn33/agentic-awesome-skills/archive/refs/heads/main.tar.gz",
        "index_file": "skills_index.json",
        "skills_root": "skills",
        "note": "official skills_index.json + dir scan",
    },
    "addy": {
        "name": "addy",
        "repo": "addyosmani/agent-skills",
        "tarball": "https://github.com/addyosmani/agent-skills/archive/refs/heads/main.tar.gz",
        "index_file": None,
        "skills_root": "skills",
        "note": "scanned skills/*/SKILL.md (no index file)",
    },
    "anthropics": {
        "name": "anthropics",
        "repo": "anthropics/skills",
        "tarball": "https://github.com/anthropics/skills/archive/refs/heads/main.tar.gz",
        "index_file": None,
        "skills_root": "skills",
        "note": "scanned skills/*/SKILL.md (no index file)",
    },
    "composiohq": {
        "name": "composiohq",
        "repo": "ComposioHQ/awesome-claude-skills",
        "tarball": "https://github.com/ComposioHQ/awesome-claude-skills/archive/refs/heads/master.tar.gz",
        "index_file": None,
        "skills_root": "",
        "note": "scanned */SKILL.md at repo root (no index file)",
    },
}


def configure_utf8_output() -> None:
    if sys.platform != "win32":
        return
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
            continue
        except Exception:
            pass
        buffer = getattr(stream, "buffer", None)
        if buffer is not None:
            setattr(sys, stream_name, io.TextIOWrapper(buffer, encoding="utf-8", errors="backslashreplace"))


# ---------------------------------------------------------------------------
# Fetch / unpack
# ---------------------------------------------------------------------------

def download_tarball(source: dict, dest: Path) -> Path:
    print(f"⬇️  Downloading {source['repo']} tarball: {source['tarball']}")
    tmp = dest / f"{source['name']}.tgz"
    # chunked download with retries (urlretrieve can die on large files)
    import time

    last_err: Exception | None = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(source["tarball"], headers={"User-Agent": "skill-creator-index/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp, open(tmp, "wb") as fh:
                while True:
                    block = resp.read(1024 * 256)
                    if not block:
                        break
                    fh.write(block)
            break
        except Exception as e:  # noqa: BLE001 - retry transient network errors
            last_err = e
            print(f"⚠️  attempt {attempt} failed: {e}")
            time.sleep(3 * attempt)
    else:
        raise RuntimeError(f"download failed after 3 attempts: {last_err}")
    size_mb = tmp.stat().st_size / (1024 * 1024)
    print(f"✅ Downloaded {size_mb:.1f} MB -> {tmp}")
    return tmp


def unpack_tarball(tar_path: Path, dest: Path) -> Path:
    print(f"📦 Unpacking tarball -> {dest}")
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(dest, filter="data")
    tops = [p for p in dest.iterdir() if p.is_dir()]
    return tops[0] if tops else dest


# ---------------------------------------------------------------------------
# Entry extraction (per source)
# ---------------------------------------------------------------------------

def frontmatter_of(skill_md: Path) -> dict:
    try:
        content = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    m = re.match(r"^---\s*\n(.*?)\n?---(?:\s*\n|$)", content, re.DOTALL)
    if not m:
        return {}
    try:
        data = json.loads(m.group(1))  # not yaml; fall back below
    except Exception:
        data = {}
    if not isinstance(data, dict) or not data:
        # minimal yaml-ish parse for name/description lines
        for line in m.group(1).splitlines():
            if line.startswith("name:"):
                data["name"] = line.split(":", 1)[1].strip().strip('"')
            elif line.startswith("description:"):
                data["description"] = line.split(":", 1)[1].strip().strip('"')
    return data


def load_official_index(repo_root: Path, source: dict) -> list[dict]:
    f = repo_root / source["index_file"]
    data = json.loads(f.read_text(encoding="utf-8"))
    print(f"🗂️  {source['repo']}: using official {source['index_file']} ({len(data)} entries)")
    return data


def scan_skill_dir(repo_root: Path, source: dict) -> list[dict]:
    """Scan <skills_root>/<name>/SKILL.md (used when a source has no official index file).

    ``skills_root`` may be empty for sources that keep skills at the repo root
    (e.g. ComposioHQ/awesome-claude-skills); in that case ``path`` is just the
    directory name (no leading slash).
    """
    root_rel = source["skills_root"].strip("/")
    skills_root = repo_root / root_rel if root_rel else repo_root
    entries = []
    if not skills_root.is_dir():
        return entries
    for d in sorted(skills_root.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            continue
        fm = frontmatter_of(skill_md)
        entries.append(
            {
                "id": d.name,
                "path": f"{root_rel}/{d.name}" if root_rel else d.name,
                "name": fm.get("name") or d.name,
                "description": fm.get("description"),
                "category": fm.get("category"),
                "risk": fm.get("risk"),
                "source": "community",
            }
        )
    print(f"🗂️  {source['repo']}: scanned {root_rel or '.'}/*/SKILL.md ({len(entries)} entries)")
    return entries


def extract_entries(repo_root: Path, source: dict) -> list[dict]:
    """Return entries (with their source_repo tagged) for one source checkout."""
    if source["index_file"] and (repo_root / source["index_file"]).exists():
        entries = load_official_index(repo_root, source)
    else:
        entries = scan_skill_dir(repo_root, source)
    for e in entries:
        e["source_repo"] = source["repo"]
        e["_root"] = str(repo_root)  # each entry remembers its own checkout root
    return entries


def entry_root(e: dict, fallback: Path) -> Path:
    """Each entry remembers its own checkout root (set in extract_entries)."""
    r = e.get("_root")
    return Path(r) if r else fallback


def enrich_structure(repo_root: Path, entry: dict) -> dict:
    rel = entry.get("path", "").removesuffix("/")
    skill_dir = repo_root / rel
    result = {
        "has_script": 0,
        "has_references": 0,
        "has_examples": 0,
        "has_templates": 0,
        "body_lines": 0,
        "file_count": 0,
        "subdirs": "",
    }
    if not skill_dir.is_dir():
        return result
    try:
        content = (skill_dir / "SKILL.md").read_text(encoding="utf-8", errors="replace")
        result["body_lines"] = content.count("\n") + 1
    except (OSError, FileNotFoundError):
        result["body_lines"] = 0
    subdirs = [d for d in os.listdir(skill_dir) if (skill_dir / d).is_dir() and not d.startswith(".")]
    result["subdirs"] = ",".join(subdirs)
    result["has_script"] = int("scripts" in subdirs)
    result["has_references"] = int("references" in subdirs)
    result["has_examples"] = int("examples" in subdirs)
    result["has_templates"] = int("templates" in subdirs)
    result["file_count"] = sum(1 for _, _, fs in os.walk(skill_dir) for f in fs if not f.startswith("."))
    return result


# (source_repo moved right after source for readability)
SKILLS_COLUMNS = """(name, path, description, category, risk, source, source_repo, date_added, author,
     tags, tools, client_targets, has_script, has_references, has_examples,
     has_templates, body_lines, file_count, subdirs)"""


def extract_fields(e: dict, repo_root: Path) -> tuple:
    tags = e.get("tags") or []
    plugin = e.get("plugin") or {}
    targets = plugin.get("targets") or {}
    tools = json.dumps(list(targets.keys()), ensure_ascii=False) if targets else None
    st = enrich_structure(entry_root(e, repo_root), e)
    return (
        e.get("name") or e.get("id"),
        e.get("path") or (e.get("id") and "skills/" + e["id"]),
        e.get("description"),
        e.get("category"),
        e.get("risk"),
        e.get("source"),
        e.get("source_repo"),
        e.get("date_added"),
        e.get("author"),
        json.dumps(tags, ensure_ascii=False) if tags else None,
        tools,
        json.dumps(targets, ensure_ascii=False) if targets else None,
        st["has_script"],
        st["has_references"],
        st["has_examples"],
        st["has_templates"],
        st["body_lines"],
        st["file_count"],
        st["subdirs"],
    )


def fts_args(e: dict) -> tuple:
    tags = e.get("tags") or []
    return (
        e.get("name") or e.get("id"),
        e.get("description") or "",
        e.get("category") or "",
        " ".join(tags) if tags else "",
    )


def create_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE skills (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            description TEXT,
            category TEXT,
            risk TEXT,
            source TEXT,
            source_repo TEXT,
            date_added TEXT,
            author TEXT,
            tags TEXT,
            tools TEXT,
            client_targets TEXT,
            has_script INTEGER DEFAULT 0,
            has_references INTEGER DEFAULT 0,
            has_examples INTEGER DEFAULT 0,
            has_templates INTEGER DEFAULT 0,
            body_lines INTEGER DEFAULT 0,
            file_count INTEGER DEFAULT 0,
            subdirs TEXT
        )
        """
    )
    cur.execute("CREATE VIRTUAL TABLE skills_fts USING fts5(name, description, category, tags)")
    cur.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")


def build_placeholder() -> str:
    return ",".join(["?"] * 19)


def source_summary(source: dict) -> str:
    """Short 'official+scan' / 'scan' tag used in the meta data_source note."""
    return "official+scan" if source.get("index_file") else "scan"


def data_source_note() -> str:
    parts = [f"{s['name']}({source_summary(s)})" for s in SOURCES.values()]
    return "multi-source: " + " + ".join(parts)


def sources_meta() -> str:
    return json.dumps([s["repo"] for s in SOURCES.values()], ensure_ascii=False)


def build_db(entries: list[dict], repo_root: Path, db_path: Path) -> int:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    create_schema(conn)
    cur = conn.cursor()
    count = 0
    for e in entries:
        cur.execute(
            "INSERT INTO skills " + SKILLS_COLUMNS + " VALUES (" + build_placeholder() + ")",
            extract_fields(e, repo_root),
        )
        rowid = cur.lastrowid
        cur.execute(
            "INSERT INTO skills_fts(rowid, name, description, category, tags) VALUES (?,?,?,?,?)",
            (rowid, *fts_args(e)),
        )
        count += 1
    cur.execute("INSERT INTO meta VALUES ('version', ?)", (str(INDEX_VERSION),))
    cur.execute("INSERT INTO meta VALUES ('sources', ?)", (sources_meta(),))
    cur.execute("INSERT INTO meta VALUES ('built_at', ?)", (datetime.now().isoformat(timespec="seconds"),))
    cur.execute("INSERT INTO meta VALUES ('skill_count', ?)", (str(count),))
    cur.execute("INSERT INTO meta VALUES ('data_source', ?)", (data_source_note(),))
    conn.commit()
    conn.close()
    return count


def update_db_incremental(entries: list[dict], repo_root: Path, db_path: Path, source_repo: str | None = None) -> dict:
    """Incremental sync: reuse the existing db, only diff by (source_repo, path)."""
    if not db_path.exists():
        print("ℹ️  No existing index; falling back to full build.")
        count = build_db(entries, repo_root, db_path)
        return {"added": count, "updated": 0, "removed": 0}

    if source_repo is None and entries:
        source_repo = entries[0].get("source_repo")

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='meta'")
    if cur.fetchone() is None:
        cur.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")

    # existing paths for this source
    if source_repo:
        cur.execute("SELECT path FROM skills WHERE source_repo=?", (source_repo,))
    else:
        cur.execute("SELECT path FROM skills")
    known = {row[0] for row in cur.fetchall() if row[0]}

    incoming = set()
    for e in entries:
        path = e.get("path") or (e.get("id") and "skills/" + e["id"])
        if path:
            incoming.add(path)

    added = updated = 0
    for e in entries:
        path = e.get("path") or (e.get("id") and "skills/" + e["id"])
        if not path:
            continue
        fields = extract_fields(e, repo_root)
        if path in known:
            cur.execute(
                """
                UPDATE skills SET
                  name=?, description=?, category=?, risk=?, source=?, source_repo=?,
                  date_added=?, author=?, tags=?, tools=?, client_targets=?, has_script=?,
                  has_references=?, has_examples=?, has_templates=?, body_lines=?,
                  file_count=?, subdirs=?
                WHERE source_repo=? AND path=?
                """,
                fields[:1] + fields[2:] + (e.get("source_repo"), path),
            )
            cur.execute(
                "INSERT OR REPLACE INTO skills_fts(rowid, name, description, category, tags)"
                " SELECT id, name, description, category, tags FROM skills WHERE source_repo=? AND path=?",
                (e.get("source_repo"), path),
            )
            updated += 1
        else:
            cur.execute(
                "INSERT INTO skills " + SKILLS_COLUMNS + " VALUES (" + build_placeholder() + ")",
                fields,
            )
            rowid = cur.lastrowid
            cur.execute(
                "INSERT INTO skills_fts(rowid, name, description, category, tags) VALUES (?,?,?,?,?)",
                (rowid, *fts_args(e)),
            )
            added += 1

    vanished = known - incoming
    removed = len(vanished)
    for path in sorted(vanished):
        if source_repo:
            cur.execute(
                "DELETE FROM skills_fts WHERE rowid = (SELECT id FROM skills WHERE source_repo=? AND path=?)",
                (source_repo, path),
            )
            cur.execute("DELETE FROM skills WHERE source_repo=? AND path=?", (source_repo, path))
        else:
            cur.execute("DELETE FROM skills_fts WHERE rowid = (SELECT id FROM skills WHERE path=?)", (path,))
            cur.execute("DELETE FROM skills WHERE path=?", (path,))

    cur.execute("INSERT OR REPLACE INTO meta VALUES ('built_at', ?)", (datetime.now().isoformat(timespec="seconds"),))
    # Total across all sources (not just the synced one); refresh source provenance too.
    total = cur.execute("SELECT COUNT(*) FROM skills").fetchone()[0]
    cur.execute("INSERT OR REPLACE INTO meta VALUES ('skill_count', ?)", (str(total),))
    cur.execute("INSERT OR REPLACE INTO meta VALUES ('sources', ?)", (sources_meta(),))
    cur.execute("INSERT OR REPLACE INTO meta VALUES ('data_source', ?)", (data_source_note(),))
    conn.commit()
    conn.close()
    return {"added": added, "updated": updated, "removed": removed}


def load_source_checkout(source: dict, args, tmp: Path) -> tuple[Path, list[dict]]:
    """Resolve one source's checkout dir + entries."""
    if args.from_extracted:
        root = Path(args.from_extracted)
        print(f"🗂️  {source['repo']}: using extracted checkout {root}")
    elif args.no_dl:
        root = Path(__file__).resolve().parents[2]
        print(f"🗂️  {source['repo']}: using local repo root {root}")
    else:
        tar_path = download_tarball(source, tmp)
        root = unpack_tarball(tar_path, tmp / f"unpack-{source['name']}")
    entries = extract_entries(root, source)
    if not entries:
        print(f"❌ {source['repo']}: no entries found; aborting this source.")
        return root, []
    return root, entries


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Build upstream skills SQLite index (multi-source)")
    parser.add_argument("--source", choices=["all", *SOURCES.keys()], default="all", help="Which upstream source to index (default: all)")
    parser.add_argument("--incremental", action="store_true", help="Reuse upstream.db; sync only added/updated/removed")
    parser.add_argument("--keep", action="store_true", help="Keep downloaded tarballs")
    parser.add_argument("--no-dl", action="store_true", help="Scan local repo root instead of downloading")
    parser.add_argument("--from-extracted", default=None, help="Build from an already-extracted checkout dir")
    args = parser.parse_args()

    tmp = Path(tempfile.gettempdir()) / "pw-upstream-index"
    tmp.mkdir(parents=True, exist_ok=True)

    selected = SOURCES.keys() if args.source == "all" else [args.source]
    all_entries = []
    all_roots = []
    for name in selected:
        source = SOURCES[name]
        root, entries = load_source_checkout(source, args, tmp)
        if entries:
            all_entries.extend(entries)
            all_roots.append(root)

    if not all_entries:
        print("❌ No entries loaded from any source.")
        return 1

    # structure enrichment happens against each source's own root — pass per-entry root
    if args.incremental:
        # group entries by source so incremental diff is scoped per (source_repo, path)
        by_source: dict[str, list[dict]] = {}
        for e in all_entries:
            by_source.setdefault(e.get("source_repo") or "?", []).append(e)
        totals = {"added": 0, "updated": 0, "removed": 0}
        for repo, group in by_source.items():
            print(f"🔍 Incremental sync: {len(group)} entries from {repo} vs existing {DB_PATH}")
            result = update_db_incremental(group, Path(by_source and (group[0].get('_root') or all_roots[0])), DB_PATH)
            totals = {k: totals[k] + result[k] for k in totals}
            print(f"✅   [{repo}] +{result['added']} added, ~{result['updated']} updated, -{result['removed']} removed")
        print(f"✅ Incremental total: +{totals['added']} added, ~{totals['updated']} updated, -{totals['removed']} removed")
    else:
        print(f"🔍 Enriching structure for {len(all_entries)} skills (dir scan)...")
        count = build_db(all_entries, all_roots[0], DB_PATH)
        print(f"✅ Indexed {count} skills -> {DB_PATH}")

    if not args.no_dl:
        cleanup_tmp(tmp, args.keep)
    return 0


def cleanup_tmp(tmp: Path, keep: bool) -> None:
    """Best-effort removal of the download/unpack scratch dir.

    Never raises: a tarball may contain read-only files, reparse points, or
    dirs Windows refuses to stat/remove mid-walk. Cleanup is housekeeping, so a
    stuck path is skipped rather than failing an otherwise successful build.
    """
    if keep:
        return

    def _safe(p: Path, predicate) -> bool:
        try:
            return predicate()
        except OSError:
            return False

    try:
        entries = list(tmp.rglob("*"))
    except OSError:
        return
    for p in entries:
        if _safe(p, p.is_file):
            try:
                p.unlink()
            except OSError:
                pass
    for p in sorted(entries, key=lambda x: -len(x.parts)):
        if not _safe(p, p.is_dir):
            continue
        try:
            for child in p.rglob("*"):
                if _safe(child, child.is_file):
                    try:
                        child.chmod(0o644)
                    except OSError:
                        pass
            p.rmdir()
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main())