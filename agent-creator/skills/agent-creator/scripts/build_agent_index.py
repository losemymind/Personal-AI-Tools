"""Build a searchable SQLite index of upstream agent catalogs (multi-source).

Part of the agent-creator skill. See references/agent-index.md.

Sources (agent definitions, all scanned from on-disk frontmatter):
  - agency    : msitarzewski/agency-agents   (division dirs of *.md agent files; ~270)
  - ccgs      : Donchitos/Claude-Code-Game-Studios (.claude/agents/*.md; ~50)
  - agency-zh : jnMetaCode/agency-agents-zh  (Chinese translation of agency-agents; ~280)

Unlike skills, upstream agent repos have no unified official index file, so every
source is discovered by scanning its layout for frontmatter agent definitions.
Each row carries `source_repo`; `path` is unique per source so incremental sync
scopes by (source_repo, path).

Usage:
    python scripts/build_agent_index.py                       # all sources, full rebuild
    python scripts/build_agent_index.py --source agency       # only one source
    python scripts/build_agent_index.py --incremental         # reuse upstream.db
    python scripts/build_agent_index.py --from-extracted <dir> # use an already-checked-out repo (single source)
    python scripts/build_agent_index.py --no-dl               # scan local checkout

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
INDEX_VERSION = 1

# Repos whose subdirectories mirror agency-agents layout: each top-level non-noise
# dir is a "division" holding agent *.md files directly.
DIVISION_LAYOUT_SOURCES = {"agency", "agency-zh"}
# Dirs that exist at top-level of division-layout repos but are NOT agent divisions.
NON_DIVISION_DIRS = {
    "assets", "examples", "integrations", "scripts", "strategy", ".github", "docs", "tests", "CCGS Skill Testing Framework",
}

# ---------------------------------------------------------------------------
# Source registry
# ---------------------------------------------------------------------------

SOURCES = {
    "agency": {
        "name": "agency",
        "repo": "msitarzewski/agency-agents",
        "tarball": "https://github.com/msitarzewski/agency-agents/archive/refs/heads/main.tar.gz",
        "agents_root": ".",  # division dirs at repo top level
        "note": "scanned division dirs of *.md agent files",
    },
    "ccgs": {
        "name": "ccgs",
        "repo": "Donchitos/Claude-Code-Game-Studios",
        "tarball": "https://github.com/Donchitos/Claude-Code-Game-Studios/archive/refs/heads/main.tar.gz",
        "agents_root": ".claude/agents",
        "note": "scanned .claude/agents/*.md (Claude Code subagents)",
    },
    "agency-zh": {
        "name": "agency-zh",
        "repo": "jnMetaCode/agency-agents-zh",
        "tarball": "https://github.com/jnMetaCode/agency-agents-zh/archive/refs/heads/main.tar.gz",
        "agents_root": ".",
        "note": "scanned division dirs of *.md agent files (Chinese)",
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
    import time

    last_err: Exception | None = None
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(source["tarball"], headers={"User-Agent": "agent-creator-index/1.0"})
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
# Frontmatter parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(content: str) -> dict:
    """Line-based frontmatter parser for agent files.

    Handles both YAML-ish key: value lines (including inline flow arrays kept as
    raw strings) and skips nested/indented structures. Same parser family as the
    capability-catalog generator so agent metadata reads consistently.
    """
    m = re.match(r"^---\s*\n(.*?)\n?---(?:\s*\n|$)", content, re.DOTALL)
    if not m:
        return {}
    data: dict = {}
    for line in m.group(1).splitlines():
        if not line.strip() or line.startswith((" ", "\t", "#")):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        if not key:
            continue
        val = val.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in ("'", '"'):
            val = val[1:-1]
        if val in ("", "null", "~"):
            val = ""
        data[key] = val
    return data


def division_of(rel_path: str) -> str:
    """First path segment (division/category) for a repo-relative agent path."""
    parts = rel_path.replace("\\", "/").split("/")
    return parts[0] if parts else ""


# ---------------------------------------------------------------------------
# Entry discovery (per source layout)
# ---------------------------------------------------------------------------

def is_agent_definition(f: Path) -> bool:
    if f.suffix.lower() != ".md" or f.name.lower().startswith(("readme", "license", "changelog", "contribut")):
        return False
    try:
        content = f.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return bool(re.match(r"^---\s*\n", content))


def discover_division_layout(repo_root: Path) -> list[Path]:
    """agency / agency-zh: top-level division dirs hold agent *.md directly."""
    found = []
    for d in sorted(repo_root.iterdir()):
        if not d.is_dir() or d.name.startswith(".") or d.name in NON_DIVISION_DIRS:
            continue
        for f in sorted(d.glob("*.md")):
            if is_agent_definition(f):
                found.append(f)
    return found


def discover_claude_agents_layout(repo_root: Path) -> list[Path]:
    """ccgs: .claude/agents/*.md are the real Claude Code subagents."""
    agents_dir = repo_root / ".claude" / "agents"
    if not agents_dir.is_dir():
        return []
    return [f for f in sorted(agents_dir.glob("*.md")) if is_agent_definition(f)]


def extract_entries(repo_root: Path, source: dict) -> list[dict]:
    if source["name"] in DIVISION_LAYOUT_SOURCES:
        files = discover_division_layout(repo_root)
    elif source["name"] == "ccgs":
        files = discover_claude_agents_layout(repo_root)
    else:
        files = []
    entries = []
    for f in files:
        rel = f.relative_to(repo_root).as_posix()
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        fm = parse_frontmatter(content)
        name = fm.get("name") or f.stem
        category = division_of(rel) if source["name"] in DIVISION_LAYOUT_SOURCES else ""
        entries.append(
            {
                "id": f.stem,
                "name": name,
                "path": rel,
                "description": fm.get("description"),
                "category": category,
                "tools": fm.get("tools"),
                "model": fm.get("model"),
                "source_repo": source["repo"],
                "_root": str(repo_root),
                "body_lines": content.count("\n") + 1,
            }
        )
    print(f"🗂️  {source['repo']}: discovered {len(entries)} agent definitions")
    return entries


# ---------------------------------------------------------------------------
# DB schema / build
# ---------------------------------------------------------------------------

AGENTS_COLUMNS = """(name, path, description, category, tools, model, source_repo, body_lines)"""


def extract_fields(e: dict) -> tuple:
    return (
        e.get("name") or e.get("id"),
        e.get("path"),
        e.get("description"),
        e.get("category"),
        e.get("tools"),
        e.get("model"),
        e.get("source_repo"),
        e.get("body_lines", 0),
    )


def fts_args(e: dict) -> tuple:
    return (
        e.get("name") or e.get("id"),
        e.get("description") or "",
        e.get("category") or "",
        e.get("tools") or "",
    )


def create_schema(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE agents (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            description TEXT,
            category TEXT,
            tools TEXT,
            model TEXT,
            source_repo TEXT,
            body_lines INTEGER DEFAULT 0
        )
        """
    )
    cur.execute("CREATE VIRTUAL TABLE agents_fts USING fts5(name, description, category, tools)")
    cur.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")


def build_db(entries: list[dict], db_path: Path) -> int:
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    create_schema(conn)
    cur = conn.cursor()
    placeholder = ",".join(["?"] * 8)
    count = 0
    for e in entries:
        cur.execute("INSERT INTO agents " + AGENTS_COLUMNS + " VALUES (" + placeholder + ")", extract_fields(e))
        rowid = cur.lastrowid
        cur.execute(
            "INSERT INTO agents_fts(rowid, name, description, category, tools) VALUES (?,?,?,?,?)",
            (rowid, *fts_args(e)),
        )
        count += 1
    cur.execute("INSERT INTO meta VALUES ('version', ?)", (str(INDEX_VERSION),))
    cur.execute(
        "INSERT INTO meta VALUES ('sources', ?)",
        (json.dumps([s["repo"] for s in SOURCES.values()], ensure_ascii=False),),
    )
    cur.execute("INSERT INTO meta VALUES ('built_at', ?)", (datetime.now().isoformat(timespec="seconds"),))
    cur.execute("INSERT INTO meta VALUES ('agent_count', ?)", (str(count),))
    conn.commit()
    conn.close()
    return count


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Build upstream agents SQLite index (multi-source)")
    parser.add_argument("--source", choices=["all", *SOURCES.keys()], default="all", help="Which upstream source to index (default: all)")
    parser.add_argument("--keep", action="store_true", help="Keep downloaded tarballs")
    parser.add_argument("--from-extracted", default=None, help="Build from an already-checked-out single source dir (must pair --source)")
    parser.add_argument("--no-dl", action="store_true", help="Scan local repo root instead of downloading")
    args = parser.parse_args()

    tmp = Path(tempfile.gettempdir()) / "pw-upstream-agent-index"
    tmp.mkdir(parents=True, exist_ok=True)

    selected = SOURCES.keys() if args.source == "all" else [args.source]

    # --from-extracted requires a single --source
    if args.from_extracted and len(selected) != 1:
        print("❌ --from-extracted must be paired with a single --source")
        return 1

    all_entries = []
    for name in selected:
        source = SOURCES[name]
        if args.from_extracted:
            root = Path(args.from_extracted)
            print(f"🗂️  {source['repo']}: using extracted checkout {root}")
        else:
            tar_path = download_tarball(source, tmp)
            root = unpack_tarball(tar_path, tmp / f"unpack-{source['name']}")
        entries = extract_entries(root, source)
        if not entries:
            print(f"❌ {source['repo']}: no agent definitions found; aborting this source.")
            continue
        all_entries.extend(entries)

    if not all_entries:
        print("❌ No entries loaded from any source.")
        return 1

    count = build_db(all_entries, DB_PATH)
    print(f"✅ Indexed {count} agents -> {DB_PATH}")

    if not args.no_dl and not args.from_extracted:
        for p in tmp.rglob("*"):
            try:
                if p.is_file():
                    p.unlink()
            except OSError:
                pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
