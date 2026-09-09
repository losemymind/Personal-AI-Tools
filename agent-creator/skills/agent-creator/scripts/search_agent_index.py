"""Search the upstream agents SQLite index (indexes/upstream.db under the skill dir).

Part of the agent-creator skill. See references/agent-index.md.

Usage:
    python scripts/search_agent_index.py "keyword1 keyword2" [--source agency|ccgs|agency-zh] [--category X] [--limit 10] [--json]
    python scripts/search_agent_index.py --stats
    python scripts/search_agent_index.py --list-categories

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

# Short alias -> repo substring for --source.
SOURCE_ALIASES = {
    "agency": "msitarzewski/agency-agents",
    "msitarzewski": "msitarzewski/agency-agents",
    "ccgs": "Donchitos/Claude-Code-Game-Studios",
    "game-studios": "Donchitos/Claude-Code-Game-Studios",
    "donchitos": "Donchitos/Claude-Code-Game-Studios",
    "agency-zh": "jnMetaCode/agency-agents-zh",
    "zh": "jnMetaCode/agency-agents-zh",
    "jnmetacode": "jnMetaCode/agency-agents-zh",
}

# FTS5 (unicode61) cannot tokenize CJK, so a MATCH on Chinese returns nothing
# even when the index contains Chinese descriptions. Fall back to substring LIKE.
CJK_RE = re.compile(r"[\u4e00-\u9fff]")
TEXT_COLUMNS = ("agents.name", "agents.description", "agents.category", "agents.tools")


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
        print("   Run: python scripts/build_agent_index.py")
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
                escaped = token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
                pattern = f"%{escaped}%"
                column_matches = " OR ".join(f"{col} LIKE ? ESCAPE '\\'" for col in TEXT_COLUMNS)
                like_parts.append(f"({column_matches})")
                params.extend([pattern] * len(TEXT_COLUMNS))
            clauses.append("(" + " AND ".join(like_parts) + ")")
        else:
            clauses.append("agents.id IN (SELECT rowid FROM agents_fts WHERE agents_fts MATCH ?)")
            params.append(args.query)

    if args.category:
        clauses.append("LOWER(COALESCE(agents.category,'')) = ?")
        params.append(args.category.lower())

    if args.source:
        clauses.append("agents.source_repo LIKE ?")
        params.append(f"%{args.source}%")

    where = ""
    if clauses:
        where = " WHERE " + " AND ".join(clauses)

    sql = (
        "SELECT agents.id, agents.name, agents.path, agents.description, "
        "agents.category, agents.tools, agents.model, agents.source_repo, agents.body_lines "
        f"FROM agents{where} ORDER BY agents.name LIMIT ?"
    )
    params.append(args.limit)
    return sql, params


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Search upstream agents index")
    parser.add_argument("query", nargs="?", default="", help="Full-text keywords (name/description/category/tools)")
    parser.add_argument("--source", default=None, help="Filter by upstream source (agency / ccgs / agency-zh)")
    parser.add_argument("--category", default=None, help="Filter by category/division (exact)")
    parser.add_argument("--limit", type=int, default=10, help="Max results (default 10)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--stats", action="store_true", help="Show index statistics")
    parser.add_argument("--list-categories", action="store_true", help="List all categories with counts")
    args = parser.parse_args()

    if args.source:
        alias = SOURCE_ALIASES.get(args.source.lower(), args.source)
        args.source = alias

    conn = connect()
    cur = conn.cursor()

    if args.stats:
        cur.execute("SELECT value FROM meta WHERE key='built_at'")
        built_at = cur.fetchone()
        cur.execute("SELECT value FROM meta WHERE key='agent_count'")
        count = cur.fetchone()
        print(f"📊 Index: {DB_PATH}")
        print(f"   Built: {built_at['value'] if built_at else 'unknown'}")
        print(f"   Agents: {count['value'] if count else 'unknown'}")
        print("\n   By source:")
        cur.execute(
            "SELECT COALESCE(source_repo,'(unknown)') AS src, COUNT(*) AS n FROM agents GROUP BY src ORDER BY n DESC"
        )
        for row in cur.fetchall():
            print(f"     {row['n']:>6}  {row['src']}")
        return 0

    if args.list_categories:
        cur.execute(
            "SELECT COALESCE(category,'(none)') AS cat, COUNT(*) AS n FROM agents GROUP BY cat ORDER BY n DESC"
        )
        for row in cur.fetchall():
            print(f"{row['n']:>5}  {row['cat']}")
        return 0

    if not args.query and not args.category and not args.source:
        print("ℹ️  Usage: search_agent_index.py <keywords> [--source agency|ccgs|agency-zh] [--category X]")
        print("   Try:  search_agent_index.py \"code review\"  or  --stats / --list-categories")
        return 0

    sql, params = build_query(args)
    rows = cur.execute(sql, params).fetchall()

    if args.json:
        print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
        return 0

    print(f"🔎 {len(rows)} results (limit {args.limit}):\n")
    for r in rows:
        print(f"  {r['name']:<48} [{r['category'] or '-'}] {r['source_repo']}")
        print(f"    {r['description'] or '(no description)'}")
        print(f"    path: {r['path']} | lines: {r['body_lines']}" + (f" | tools: {r['tools']}" if r["tools"] else ""))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
