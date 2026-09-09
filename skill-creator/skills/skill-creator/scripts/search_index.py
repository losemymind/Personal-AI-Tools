"""Search the upstream skills SQLite index (indexes/upstream.db under the skill dir).

Part of the skill-creator skill. See references/skill-index.md.

Usage:
    python scripts/search_index.py "keyword1 keyword2" [--category devops] [--risk safe] [--limit 10] [--json]
    python scripts/search_index.py --stats
    python scripts/search_index.py --list-categories

Exit code 0 = success.
"""

import argparse
import io
import json
import re
import sqlite3
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR.parent / "indexes" / "upstream.db"

# FTS5 (unicode61) does not tokenize CJK, so a MATCH on Chinese returns nothing
# even when the index contains Chinese descriptions. Detect CJK queries and fall
# back to substring LIKE matching on the indexed text columns.
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
TEXT_COLUMNS = ("skills.name", "skills.description", "skills.tags", "skills.category")

# short alias -> repo substring for --source
SOURCE_ALIASES = {
    "aas": "sickn33/agentic-awesome-skills",
    "agentic-awesome-skills": "sickn33/agentic-awesome-skills",
    "sickn33": "sickn33/agentic-awesome-skills",
    "addy": "addyosmani/agent-skills",
    "agent-skills": "addyosmani/agent-skills",
    "addyosmani": "addyosmani/agent-skills",
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
            setattr(
                sys,
                stream_name,
                io.TextIOWrapper(buffer, encoding="utf-8", errors="backslashreplace"),
            )


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        print(f"❌ Index not found: {DB_PATH}")
        print("   Run: python scripts/build_index.py")
        sys.exit(1)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def build_query(args) -> tuple[str, list]:
    clauses = []
    params = []

    if args.query:
        if CJK_RE.search(args.query):
            tokens = [t for t in args.query.split() if t]
            like_parts = []
            for token in tokens:
                escaped = (
                    token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                )
                pattern = f"%{escaped}%"
                column_matches = " OR ".join(
                    f"{col} LIKE ? ESCAPE '\\'" for col in TEXT_COLUMNS
                )
                like_parts.append(f"({column_matches})")
                params.extend([pattern] * len(TEXT_COLUMNS))
            clauses.append("(" + " AND ".join(like_parts) + ")")
        else:
            clauses.append(
                "skills.id IN (SELECT rowid FROM skills_fts WHERE skills_fts MATCH ?)"
            )
            params.append(args.query)

    if args.category:
        clauses.append("LOWER(COALESCE(skills.category,'')) = ?")
        params.append(args.category.lower())

    if args.risk:
        clauses.append("LOWER(COALESCE(skills.risk,'')) = ?")
        params.append(args.risk.lower())

    if args.tool:
        clauses.append("COALESCE(skills.tools,'') LIKE ?")
        params.append(f"%{args.tool}%")

    if args.source:
        clauses.append("skills.source_repo LIKE ?")
        params.append(f"%{args.source}%")

    if args.only_scripts:
        clauses.append("skills.has_script = 1")
    if args.only_references:
        clauses.append("skills.has_references = 1")

    where = ""
    if clauses:
        where = " WHERE " + " AND ".join(clauses)

    order = "skills.name"
    sql = (
        "SELECT skills.id, skills.name, skills.path, skills.description, "
        "skills.category, skills.risk, skills.tags, skills.tools, "
        "skills.source_repo, skills.has_script, skills.has_references, skills.has_examples, "
        "skills.body_lines, skills.file_count "
        f"FROM skills{where} ORDER BY skills.name LIMIT ?"
    )
    params.append(args.limit)
    return sql, params


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Search upstream skills index")
    parser.add_argument("query", nargs="?", default="", help="Full-text keywords (name/description/category/tags)")
    parser.add_argument("--source", default=None, help="Filter by upstream source repo (aas / addy / full repo substring; default: all)")
    parser.add_argument("--category", default=None, help="Filter by category (exact)")
    parser.add_argument("--risk", default=None, help="Filter by risk level (none/safe/critical/offensive/unknown)")
    parser.add_argument("--tool", default=None, help="Filter by tool (claude/opencode/codex/deepseek...)")
    parser.add_argument("--only-scripts", action="store_true", help="Only skills with scripts/")
    parser.add_argument("--only-references", action="store_true", help="Only skills with references/")
    parser.add_argument("--limit", type=int, default=10, help="Max results (default 10)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--stats", action="store_true", help="Show index statistics")
    parser.add_argument("--list-categories", action="store_true", help="List all categories with counts")
    args = parser.parse_args()

    # resolve source alias (aas/addy/...) to a repo substring
    if args.source:
        alias = SOURCE_ALIASES.get(args.source.lower(), args.source)
        args.source = alias

    conn = connect()
    cur = conn.cursor()

    if args.stats:
        cur.execute("SELECT value FROM meta WHERE key='built_at'")
        built_at = cur.fetchone()
        cur.execute("SELECT value FROM meta WHERE key='skill_count'")
        count = cur.fetchone()
        print(f"📊 Index: {DB_PATH}")
        print(f"   Built: {built_at['value'] if built_at else 'unknown'}")
        print(f"   Skills: {count['value'] if count else 'unknown'}")
        print("\n   By source:")
        cur.execute("SELECT COALESCE(source_repo,'(unknown)') AS src, COUNT(*) AS n FROM skills GROUP BY src ORDER BY n DESC")
        for row in cur.fetchall():
            print(f"     {row['n']:>6}  {row['src']}")
        return 0

    if args.list_categories:
        cur.execute("SELECT COALESCE(category,'(none)') AS cat, COUNT(*) AS n FROM skills GROUP BY cat ORDER BY n DESC")
        for row in cur.fetchall():
            print(f"{row['n']:>5}  {row['cat']}")
        return 0

    if not args.query and not args.category and not args.risk and not args.tool and not args.source and not args.only_scripts and not args.only_references:
        print("ℹ️  Usage: search_index.py <keywords> [--category X] [--risk Y] [--source aas|addy] ...")
        print("   Try:  search_index.py \"git push\"  or  --list-categories / --stats")
        return 0

    sql, params = build_query(args)
    rows = cur.execute(sql, params).fetchall()

    if args.json:
        print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
        return 0

    print(f"🔎 {len(rows)} results (limit {args.limit}):\n")
    for r in rows:
        flags = []
        if r["has_script"]:
            flags.append("scripts")
        if r["has_references"]:
            flags.append("references")
        if r["has_examples"]:
            flags.append("examples")
        print(f"  {r['name']:<48} [{r['risk'] or '?'}] {r['category'] or '-'}")
        print(f"    {r['description'] or '(no description)'}")
        print(f"    path: {r['path']} | src: {r['source_repo'] or '-'} | lines: {r['body_lines']} | files: {r['file_count']}"
              + (f" | dirs: {','.join(flags)}" if flags else ""))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())