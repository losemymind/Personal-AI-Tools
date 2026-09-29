"""Search the upstream skills SQLite index (indexes/upstream.db under the skill dir).

Part of the skill-creator skill. See references/skill-index.md.

Usage:
    python scripts/skill_index_search.py "keyword1 keyword2" [--category devops] [--risk safe] [--limit 10] [--json]
    python scripts/skill_index_search.py --stats
    python scripts/skill_index_search.py --list-categories

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

# Offline keyword aliases, not sentence translation. Unknown CJK qualifiers are
# retained by declining expansion altogether, rather than broadening the query.
QUERY_ALIASES = {
    "代码审查": "code review", "代码评审": "code review",
    "单元测试": "unit testing", "性能优化": "performance optimization",
    "技能创建": "skill creator", "创建技能": "skill creator",
    "调试": "debugging", "重构": "refactoring",
    "安全审计": "security audit", "文档生成": "documentation",
    "无障碍": "accessibility", "数据库": "database",
    "持续集成": "continuous integration", "部署": "deployment",
}


def expand_query(query: str) -> list[str]:
    variants = [query]
    tokens = query.split()
    if tokens and all(not CJK_RE.search(t) or t in QUERY_ALIASES for t in tokens):
        translated = " ".join(QUERY_ALIASES.get(t, t) for t in tokens)
        if translated != query:
            variants.append(translated)
    return variants

# short alias -> repo substring for --source
SOURCE_ALIASES = {
    "aas": "sickn33/agentic-awesome-skills",
    "agentic-awesome-skills": "sickn33/agentic-awesome-skills",
    "sickn33": "sickn33/agentic-awesome-skills",
    "addy": "addyosmani/agent-skills",
    "agent-skills": "addyosmani/agent-skills",
    "addyosmani": "addyosmani/agent-skills",
    "anthropics": "anthropics/skills",
    "anthropic": "anthropics/skills",
    "composiohq": "ComposioHQ/awesome-claude-skills",
    "composio": "ComposioHQ/awesome-claude-skills",
    "awesome-claude-skills": "ComposioHQ/awesome-claude-skills",
    "coevoskills": "Zhang-Henry/CoEvoSkills",
    "coevo": "Zhang-Henry/CoEvoSkills",
    "zhang-henry": "Zhang-Henry/CoEvoSkills",
    "mattpocock": "mattpocock/skills",
    "matt-pocock": "mattpocock/skills",
    "karpathy": "multica-ai/andrej-karpathy-skills",
    "andrej-karpathy": "multica-ai/andrej-karpathy-skills",
    "karpathy-skills": "multica-ai/andrej-karpathy-skills",
    "multica": "multica-ai/andrej-karpathy-skills",
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
        print("   Run: python scripts/skill_index_build.py")
        sys.exit(1)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def build_query(args) -> tuple[str, list]:
    clauses = []
    params = []
    variants = expand_query(args.query) if args.query else []
    fts_query = ""

    if args.query:
        matches = []
        ascii_queries = [q for q in variants if not CJK_RE.search(q)]
        if ascii_queries:
            fts_query = " OR ".join(
                "(" + " ".join('"' + t.replace('"', '""') + '"'
                                 for t in (q.split() or [q])) + ")"
                for q in ascii_queries
            )
            matches.append("skills.id IN (SELECT rowid FROM skills_fts WHERE skills_fts MATCH ?)")
            params.append(fts_query)
        for query in (q for q in variants if CJK_RE.search(q)):
            tokens = query.split()
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
            matches.append("(" + " AND ".join(like_parts) + ")")
        clauses.append("(" + " OR ".join(matches) + ")")

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

    order_parts = []
    if variants:
        normalized = [re.sub(r"[-_\s]+", " ", q.lower()).strip() for q in variants]
        placeholders = ",".join("?" for _ in normalized)
        order_parts.append(
            "CASE WHEN LOWER(REPLACE(REPLACE(skills.name, '-', ' '), '_', ' ')) "
            f"IN ({placeholders}) THEN 0 ELSE 1 END")
        params.extend(normalized)
    if fts_query:
        # BM25 is negative, so ascending puts stronger matches first. The scalar
        # subquery keeps LIKE alternatives possible without MATCH inside an OR.
        order_parts.append(
            "COALESCE((SELECT bm25(skills_fts, 8.0, 1.0, 1.0, 2.0) "
            "FROM skills_fts WHERE rowid=skills.id AND skills_fts MATCH ?), 0)")
        params.append(fts_query)
    elif variants:
        order_parts.append("CASE WHEN INSTR(skills.name, ?) > 0 THEN 0 ELSE 1 END")
        params.append(args.query)
    order_parts.extend(["skills.name", "skills.source_repo", "skills.path"])
    order = ", ".join(order_parts)
    sql = (
        "SELECT skills.id, skills.name, skills.path, skills.description, "
        "skills.category, skills.risk, skills.tags, skills.tools, "
        "skills.source_repo, skills.has_script, skills.has_references, skills.has_examples, "
        "skills.body_lines, skills.file_count "
        f"FROM skills{where} ORDER BY {order} LIMIT ?"
    )
    params.append(args.limit)
    return sql, params


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Search upstream skills index")
    parser.add_argument("query", nargs="?", default="", help="Full-text keywords (name/description/category/tags)")
    parser.add_argument("--source", default=None, help="Filter by upstream source repo (aas / addy / anthropics / composiohq / coevoskills / mattpocock / karpathy / full repo substring; default: all)")
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

    # SQLite treats `LIMIT -1` as "no limit"; reject a negative --limit rather
    # than silently returning the whole table.
    if args.limit is not None and args.limit < 0:
        print(f"Error: --limit must be >= 0 (got {args.limit})", file=sys.stderr)
        return 1

    conn = connect()
    cur = conn.cursor()

    if args.stats:
        cur.execute("SELECT value FROM meta WHERE key='built_at'")
        built_at = cur.fetchone()
        cur.execute("SELECT value FROM meta WHERE key='skill_count'")
        count = cur.fetchone()
        print(f"📊 Index: {DB_PATH}")
        print(f"   Database updated: {built_at['value'] if built_at else 'unknown'} (not all sources)")
        print(f"   Skills: {count['value'] if count else 'unknown'}")
        print("\n   By source:")
        cur.execute("SELECT COALESCE(source_repo,'(unknown)') AS src, COUNT(*) AS n FROM skills GROUP BY src ORDER BY n DESC")
        counts = {row['src']: row['n'] for row in cur.fetchall()}
        states = {row['key'].removeprefix('source_status:'): json.loads(row['value'])
                  for row in conn.execute("SELECT key, value FROM meta WHERE key LIKE 'source_status:%'")}
        for repo in sorted(counts.keys() | states.keys(), key=lambda repo: (-counts.get(repo, 0), repo)):
            print(f"     {counts.get(repo, 0):>6}  {repo}")
            state = states.get(repo, {})
            print(f"             status={state.get('status', 'unknown')} | "
                  f"last_success={state.get('last_success') or 'unknown'} | "
                  f"last_attempt={state.get('last_attempt') or 'unknown'}")
            if state.get("snapshot_sha256"):
                print(f"             snapshot_sha256={state['snapshot_sha256']}")
            print(f"             upstream_commit={state.get('upstream_commit') or 'unknown'} | "
                  f"fetch_mode={state.get('fetch_mode') or 'unknown'} | "
                  f"source_ref={state.get('source_ref') or 'unknown'}")
            if state.get("error"):
                print(f"             error={state['error']}")
        print("   unknown = legacy index; per-source freshness was not recorded.")
        return 0

    if args.list_categories:
        cur.execute("SELECT COALESCE(category,'(none)') AS cat, COUNT(*) AS n FROM skills GROUP BY cat ORDER BY n DESC")
        for row in cur.fetchall():
            print(f"{row['n']:>5}  {row['cat']}")
        return 0

    if not args.query and not args.category and not args.risk and not args.tool and not args.source and not args.only_scripts and not args.only_references:
        print("ℹ️  Usage: skill_index_search.py <keywords> [--category X] [--risk Y] [--source aas|addy|anthropics|composiohq|coevoskills|mattpocock|karpathy] ...")
        print("   Try:  skill_index_search.py \"git push\"  or  --list-categories / --stats")
        return 0

    sql, params = build_query(args)
    rows = cur.execute(sql, params).fetchall()

    if args.json:
        print(json.dumps([dict(r) for r in rows], ensure_ascii=False, indent=2))
        return 0

    variants = expand_query(args.query)
    if len(variants) > 1:
        print(f"Query expansion: {' | '.join(variants)}")
    print(f"🔎 {len(rows)} results (limit {args.limit}):\n")
    if not rows and CJK_RE.search(args.query):
        print("   未命中不代表上游不存在：请提取关键词，并补一次英文/近义词检索。\n")
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
