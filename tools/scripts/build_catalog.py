"""Generate machine-readable capability catalogs from skills//agents frontmatter.

Design: each SKILL.md / AGENT.md is the single source of truth; the generated
CATALOG.md files are derived artifacts that must never be edited by hand. AI
agents (claude/opencode/codex/deepseek) read these files to match a natural
language need to an installable local capability.

Adapted from the external personal-workflow repo's
tools/scripts/build_catalog.py, which originally produced this repository's
CATALOG.md files.
Two deliberate deviations for this repo's conventions:
  - install semantics are "copy dir into the target client's skills/agents
    directory" (this repo has no install_*.py launcher, unlike the upstream);
  - output header/grouping match this repo's library READMEs.

Usage:
    python tools/scripts/build_catalog.py                 # rewrite both CATALOG.md files
    python tools/scripts/build_catalog.py --check         # verify only (no writes)
    python tools/scripts/build_catalog.py --verbose       # log per-entry sources

Exit code 0 = ok. --check returns 1 if the on-disk catalog is stale.
"""

import argparse
import io
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
CATALOG_NAME = "CATALOG.md"

# Order matters: an entry is the canonical form of a directory holding
# SKILL.md / AGENT.md. agents//agents may nest (agents/<layer>/<id>/AGENT.md).
KIND_FILES = {
    "skills": ("SKILL.md", "skill"),
    "agents": ("AGENT.md", "agent"),
}

# Readme/catalog/resource files that are NOT capability entries.
EXCLUDED_NAMES = {"README.md", "CATALOG.md"}
# Sub-dirs that must never be scanned as capability entries (reference/template/examples material).
EXEMPT_DIRS = {"examples", "references", "templates"}

DEFAULTS = {
    "category": "uncategorized",
    "risk": "unknown",
    "mode": "-",
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


def parse_frontmatter(content: str) -> dict:
    """Minimal line-based frontmatter parser (no PyYAML dependency).

    Handles flat scalars and inline flow arrays kept verbatim; ignores nested /
    indented structures (the catalog only needs scalars). Returns {} when there
    is no well-formed frontmatter block.
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


def first_when_to_use(content: str, head: list[str]) -> str:
    """Extract the first non-empty content line after a 'when to use' heading."""
    for h in head:
        pat = re.compile(r"^##\s*" + re.escape(h) + r"\s*\n(.*?)(?=\n##\s|\Z)", re.DOTALL | re.MULTILINE)
        m = pat.search(content)
        if not m:
            continue
        for line in m.group(1).splitlines():
            line = line.strip().lstrip("-• ")
            if line and not line.startswith(("```", "|")):
                return line[:160]
    return ""


def discover(library: Path, kind: str, entry_file: str, verbose: bool) -> list[dict]:
    """Recursively scan a library dir (skills/ or agents/) for capability entries."""
    entries = []
    for sub in sorted(library.rglob("*")):
        if not sub.is_dir():
            continue
        rel = sub.relative_to(library)
        if any(part.startswith(".") or part in EXCLUDED_NAMES | EXEMPT_DIRS for part in rel.parts):
            continue
        if not (sub / entry_file).exists():
            continue
        content = (sub / entry_file).read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(content)
        if not fm:
            if verbose:
                print(f"  · skip {sub.name}: no frontmatter in {entry_file}")
            continue
        rel_path = rel.as_posix()
        path = f"{library.name}/{rel_path}"
        entry = {
            "kind": kind,
            "name": fm.get("name") or sub.name,
            "dir": rel_path,
            "path": path,
            "description": fm.get("description") or "",
            "trigger": first_when_to_use(
                content,
                ["When to Use This Skill", "When to Use", "Use this skill when", "何时使用此技能", "何时使用", "When to activate this skill"],
            )
            or "",
        }
        if kind == "skill":
            # Skill frontmatter schema: name/description/risk/category only.
            # Provenance (source/author/date/version) lives in the library's
            # creation-record ledger (SKILL-RECORDS.md), NOT in frontmatter.
            entry["category"] = fm.get("category") or DEFAULTS["category"]
            entry["risk"] = fm.get("risk") or DEFAULTS["risk"]
            entry["install"] = f"复制 `{path}` → 客户端 skills/ 目录"
        else:
            # Agent frontmatter schema: name/description/mode + maturity (+ tools/permission).
            # No category/source/date_added/version/tags; layer comes from the directory path.
            entry["mode"] = fm.get("mode") or DEFAULTS["mode"]
            entry["maturity"] = fm.get("maturity") or "-"
            entry["install"] = f"复制 `{path}` → 客户端 agents/ 目录"
        entries.append(entry)
    return entries


def render_entry(e: dict) -> str:
    """Render a single catalog entry (heading anchor + table + prose)."""
    kind = e["kind"]
    if kind == "skill":
        rows = [
            ("category", e["category"]),
            ("risk", e["risk"]),
        ]
    else:
        rows = [("mode", e["mode"])]
        if e.get("maturity"):
            rows.append(("maturity", e["maturity"]))
    # install already carries markdown backticks around the copy source path.
    rows.append(("install", e["install"]))

    table = "\n".join(f"| {k} | {v} |" for k, v in rows)
    head = f"## {e['name']}\n\n"
    body = f"{table}\n"
    if e["description"]:
        body += f"\n**用途**：{e['description']}\n"
    if e["trigger"]:
        body += f"\n**触发器**：{e['trigger']}\n"
    return head + body


def header(kind: str) -> str:
    repo = "skills" if kind == "skill" else "agents"
    label = "技能（Skill）" if kind == "skill" else "代理（Agent）"
    script = "python tools/scripts/build_catalog.py"
    lines = [
        f"# {repo}/ — 已验证{label}能力目录\n",
        f"> 本文件由 `{script}` 自动生成，**禁止手改**。事实源 = 各 `SKILL.md` / `AGENT.md` 的 frontmatter。\n",
        f"> 新增/删除/改进能力后重跑 `{script}`；发布门可用 `{script} --check` 校验目录是否过期。\n",
        f"> 检索：让 LLM 读本文件匹配需求 → 命中即复制对应 `{repo}/<name>` 目录到目标客户端对应目录，人类确认后执行。\n",
    ]
    if kind == "agent":
        lines.append(
            "> 落地前转换：仓库规范形 frontmatter 复制到 claude/opencode 前，先用 "
            "`python agent-creator/skills/agent-creator/scripts/adapt_agent.py <目录> --client <claude|opencode> --out <落点>` 转换。\n"
        )
    return "\n".join(lines) + "\n"


def render_catalog(library: Path, kind: str, entry_file: str, verbose: bool) -> str:
    """Render the catalog, grouping agents entries by top-level category dir;
    single-category (flat) libraries render without group headers."""
    entries = discover(library, kind, entry_file, verbose)
    parts = [header(kind)]
    if not entries:
        parts.append("_（暂无能力）_\n")
        return "\n".join(parts) + "\n"

    if kind == "skill":
        for e in entries:
            parts.append(render_entry(e))
        return "\n".join(parts) + "\n"

    groups: dict[str, list[dict]] = {}
    for e in entries:
        top = e["dir"].split("/", 1)[0]
        groups.setdefault(top, []).append(e)

    def _order_key(g: str) -> tuple:
        # Top-level agents first (no category dir), then category dirs alphabetically.
        return (0 if g == "" else 1, g)

    for group in sorted(groups, key=_order_key):
        g_entries = groups[group]
        g_entries.sort(key=lambda x: x["name"])
        if group == "":
            parts.append("## 顶层通用代理\n")
        else:
            parts.append(f"## 分组：{group}\n")
            parts.append(f"_共 {len(g_entries)} 个代理，安装路径位于 `agents/{group}/` 下。_\n")
        for e in g_entries:
            parts.append(render_entry(e))
    return "\n".join(parts) + "\n"


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Generate skills//agents capability catalogs from frontmatter")
    parser.add_argument("--root", default=str(REPO_ROOT), help="Repo root to scan (default: derived from script location)")
    parser.add_argument("--check", action="store_true", help="Verify on-disk catalogs are up to date (no writes)")
    parser.add_argument("--verbose", action="store_true", help="Log per-entry data sources")
    args = parser.parse_args()
    root = Path(args.root).resolve()

    changed = False
    for lib_name, (entry_file, kind) in KIND_FILES.items():
        library = root / lib_name
        catalog_path = library / CATALOG_NAME
        if not library.is_dir():
            # Fail loudly on a bad/typo'd --root instead of rewriting an empty catalog.
            print(f"❌ [{lib_name}] library directory does not exist: {library}")
            changed = True
            continue
        rendered = render_catalog(library, kind, entry_file, args.verbose)
        if args.check:
            if not catalog_path.exists():
                print(f"❌ [{lib_name}] missing {catalog_path.name}. Run build_catalog.py")
                changed = True
                continue
            if catalog_path.read_text(encoding="utf-8") != rendered:
                print(f"❌ [{lib_name}] catalog is stale. Run build_catalog.py")
                changed = True
            else:
                print(f"✅ [{lib_name}] catalog up to date")
        else:
            catalog_path.parent.mkdir(parents=True, exist_ok=True)
            catalog_path.write_text(rendered, encoding="utf-8")
            print(f"✅ [{lib_name}] wrote {catalog_path.relative_to(root)} ({len(discover(library, kind, entry_file, False))} entries)")

    return 1 if changed else 0


if __name__ == "__main__":
    sys.exit(main())
