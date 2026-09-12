"""Interactive agent scaffold generator (part of agent-creator tooling).

Creates a complete agent skeleton: AGENT.md with valid frontmatter,
identity/boundary/permission/collaboration sections. Output validates with
validate_agents.py.

Usage:
    python scripts/create_agent.py                          # interactive
    python scripts/create_agent.py --name my-reviewer --mode subagent --out ./agents  # non-interactive
    python scripts/create_agent.py --name my-reviewer --mode subagent --color "#DC2626" --out ./agents  # 可选 UI 色
"""

import argparse
import io
import json
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "templates" / "AGENT.template.md"

VALID_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MODES = ["primary", "subagent", "all"]
# Optional UI display color; mirrors validate_agents.py / adapt_agent.py. In YAML
# a `#` starts a comment, so hex values MUST be quoted (`--color "#DC2626"`).
DEFAULT_COLOR = "#DC2626"
VALID_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
COLOR_THEMES = ("primary", "secondary", "accent", "success", "warning", "error", "info")
# Tool names that grant state-changing edits. The scaffold's permission matrix
# derives from the whitelist via TOOL_TO_PERMISSION_KEY (write/patch fold to edit).
EDIT_TOOL_ALIASES = {"edit", "write", "patch"}
TOOL_TO_PERMISSION_KEY = {"edit": "edit", "write": "edit", "patch": "edit"}

# Canonical FULL permission matrix keys (opencode permission model, the shape used
# by this repo's academic agents and the UEGameStudio qa/security-engineer example):
# `"*": deny` default-rejects everything, then every concrete key is declared
# explicitly (allow for whitelisted tools, deny otherwise) so the face is always
# complete — least privilege with never a silent gap.
PERMISSION_ORDER = [
    "read", "glob", "grep", "list", "skill", "webfetch", "websearch",
    "question", "edit", "bash", "task", "lsp", "external_directory",
]

# Central creation-record ledger (provenance/author/date live here, not in
# AGENT.md frontmatter — an agent is client-neutral before packaging, and
# version/tools_clients are not carried in frontmatter either).
RECORDS_HEADER = (
    "# 代理创建记录（AGENTS-RECORDS）\n\n"
    "> 由 agent-creator 在创建/导入代理时追加（`create_agent.py --records <本文件>`）。\n"
    "> 记录各代理的来源与创建元数据；`AGENT.md` frontmatter 只保留 "
    "`name`/`description`/`mode` 等运行时字段（**不含** `version`/`tools_clients`/`tags`）。\n\n"
    "| 代理 | mode | created | author | source | source_repo | method | evolutions |\n"
    "|---|---|---|---|---|---|---|---|\n"
)


def append_record(records_path, name, mode, author, source, source_repo, method) -> None:
    """Append one provenance row to the creation-record ledger (create if absent)."""
    records_path = Path(records_path)
    records_path.parent.mkdir(parents=True, exist_ok=True)
    if not records_path.exists():
        records_path.write_text(RECORDS_HEADER, encoding="utf-8")
    cells = [name, mode, date.today().isoformat(), author, source,
             source_repo or "-", method, "-"]
    row = "| " + " | ".join(str(c).replace("|", "\\|") for c in cells) + " |\n"
    with records_path.open("a", encoding="utf-8") as f:
        f.write(row)


def _yaml_str(value: str) -> str:
    """Render a value as a JSON double-quoted scalar (valid YAML), safely escaped."""
    return json.dumps(value, ensure_ascii=False)


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


def ask(prompt: str, default: str = "", choices: list | None = None) -> str:
    suffix = f" ({choices and '/'.join(choices)} | 默认: {default})" if default or choices else ""
    while True:
        try:
            value = input(f"{prompt}{suffix}: ").strip()
        except EOFError:
            # Redirected/closed stdin: fall back to the default or exit cleanly
            # instead of crashing with a traceback.
            if default:
                return default
            print("\n❌ 无交互输入（stdin 已结束）；请用 --no-interactive 或补齐参数")
            raise SystemExit(1)
        if not value and default:
            return default
        if choices and value not in choices:
            print(f"❌ 必须是: {', '.join(choices)}")
            continue
        if value:
            return value


def ask_name() -> str:
    while True:
        value = ask("代理名称（kebab-case）")
        if not VALID_NAME.match(value):
            print("❌ 名称必须是小写字母/数字+连字符，如 code-reviewer")
            continue
        return value


def _render_body_tools(tools) -> tuple[str, str, bool]:
    """Derive the body's allowed/forbidden tool prose from the whitelist.

    Returns (allowed, forbidden, editing_allowed). The body must never show a
    hard-coded tool list: it previously said ``read grep bash`` regardless of
    ``--tools``, so a scaffold could list a tool it was not granted (or omit one
    it was) — a contradiction between frontmatter and body.
    """
    editing_allowed = any(t in EDIT_TOOL_ALIASES for t in tools)
    allowed = " ".join(f"`{t}`" for t in tools) if tools else "（无）"
    if editing_allowed:
        forbidden = "（无——编辑类工具已显式列入白名单，请自行界定边界）"
    else:
        forbidden = "`edit`（除非职责需要，否则默认拒绝）"
    return allowed, forbidden, editing_allowed


def _render_permission(tools) -> str:
    """Render the full permission matrix: `"*": deny` default + explicit per-key
    allow/deny derived from the whitelist (write/patch fold to edit)."""
    allowed = {TOOL_TO_PERMISSION_KEY.get(t, t) for t in tools}
    lines = ["permission:", '  "*": deny']
    for key in PERMISSION_ORDER:
        lines.append(f"  {key}: {'allow' if key in allowed else 'deny'}")
    for key in sorted(allowed - set(PERMISSION_ORDER)):
        lines.append(f"  {key}: allow")
    return "\n".join(lines) + "\n"


def build_agent_md(name, description, mode, tools, color=DEFAULT_COLOR) -> str:
    allowed, forbidden, editing_allowed = _render_body_tools(tools)
    if TEMPLATE_PATH.exists():
        content = TEMPLATE_PATH.read_text(encoding="utf-8-sig")
        content = content.replace("your-agent-name", name)
        # Target the `mode:` line specifically — a blanket replace would rewrite
        # the first "subagent" occurrence, which may sit inside the description.
        # Use lambda replacements, never f-strings: a string replacement is passed
        # through `re`'s backslash-escape processing, so a JSON-escaped description
        # (e.g. a Windows path `C:\Users`, or an embedded newline `\n`) would be
        # collapsed and emit invalid YAML.
        content = re.sub(r"^mode:\s*\S+$", lambda m: f"mode: {mode}", content, count=1, flags=re.MULTILINE)
        content = re.sub(
            r"^description: .*$",
            lambda m: f"description: {_yaml_str(description)}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        content = re.sub(
            r"^tools: \[.*?\]",
            lambda m: f"tools: [{', '.join(tools)}]",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        # The scaffold always carries a color (UEGameStudio-style UI display);
        # un-comment the template's optional line with the picked value.
        content = re.sub(
            r"^#?\s*color:.*$",
            lambda m: f"color: {_yaml_str(color)}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        # Replace the template's permission block with the full matrix derived
        # from the whitelist (`"*": deny` + explicit allow/deny per key).
        content = re.sub(
            r"^permission:[^\n]*\n(?:[ \t]+[^\n]*\n)*",
            _render_permission(tools),
            content,
            count=1,
            flags=re.MULTILINE,
        )
        content = content.replace("{{ALLOWED_TOOLS}}", allowed)
        content = content.replace("{{FORBIDDEN_TOOLS}}", forbidden)
        return content
    return f"""---
name: {name}
description: {_yaml_str(description)}
mode: {mode}
color: {_yaml_str(color)}
tools: [{', '.join(tools)}]
{_render_permission(tools)}---

# {name.replace('-', ' ').title()}

## 角色定位

1-2 句：这个代理是谁、为什么存在。

## 职责范围

**必须做：**
- 职责 1
- 职责 2

**拒绝做：**
- 职责之外的请求
- 破坏性操作 / 未授权操作

## 工作方式

判断标准与流程要点。

## 工具与权限

- 允许：{allowed}
- 禁止：{forbidden}

## 协作协议

- **何时被调用**：
- **汇报格式**：
- **升级路径**：遇到不确定或高风险情况时停下，交还用户决策。

## 完成标准

产出如何验收：
- [ ] 可验证标准 1
- [ ] 可验证标准 2

## 限制与边界

- 在这个环境下不工作的情况
- 已知边界与做不到的事情
"""


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Create an agent scaffold")
    parser.add_argument("--name", default=None)
    parser.add_argument("--description", default=None)
    parser.add_argument("--mode", default=None, choices=MODES)
    parser.add_argument("--tools", default="read,grep,glob,bash", help="逗号分隔的工具列表")
    parser.add_argument("--color", default=None,
                        help="可选：UI 显示色（如 \"#DC2626\" 或主题名；脚本自动加引号）")
    parser.add_argument("--author", default=None, help="作者标识（仅写入创建记录账本，不进 frontmatter）")
    parser.add_argument("--source", default="self", help="来源：self/community/official/external/URL（仅记录账本）")
    parser.add_argument("--source-repo", default="", dest="source_repo", help="上游仓库 OWNER/REPO 或本地来源名（仅记录账本）")
    parser.add_argument("--method", default="created", help="创建方式：created/imported/migrated（仅记录账本）")
    parser.add_argument("--records", default=None, help="创建记录账本文件；提供则在创建后追加一行")
    parser.add_argument("--out", default=None, help="输出目录（默认当前目录）")
    parser.add_argument("--no-interactive", action="store_true", help="缺省字段使用默认值，不询问")
    args = parser.parse_args()

    interactive = not args.no_interactive

    if args.name:
        name = args.name
    elif interactive:
        name = ask_name()
    else:
        print("❌ --no-interactive 模式需要 --name")
        return 1

    if not VALID_NAME.match(name):
        print(f"❌ 无效名称: {name}（需 kebab-case）")
        return 1

    description = args.description
    if not description:
        if interactive:
            description = ask("一句话描述（做什么+何时被调用，≤200 字符）")
        else:
            description = f"{name} 角色代理。"

    # validate_agents.py rejects an empty/whitespace-only description and one
    # longer than 300 chars; the scaffold promises its output validates, so refuse
    # up front instead of emitting a file that immediately fails its own gate.
    if not description.strip():
        print("❌ 描述不能为空白（validate_agents.py 会拒绝）")
        return 1
    if len(description) > 300:
        print(f"❌ 描述超长: {len(description)} 字符（validate_agents.py 上限 300）")
        return 1

    mode = args.mode or ("subagent" if not interactive else ask("模式", "subagent", MODES))

    tools = [t.strip().lower() for t in args.tools.split(",") if t.strip()]

    # The scaffold always carries a UI display color (the field is optional in
    # general, but agents created via agent-creator include it). Interactive mode
    # asks with a default; non-interactive uses the default unless --color given.
    color = (args.color or "").strip() or (
        ask("UI 显示色（#RRGGBB 或主题名）", DEFAULT_COLOR) if interactive else DEFAULT_COLOR
    )
    if not (VALID_COLOR.match(color) or color in COLOR_THEMES):
        print(f"❌ 无效 color: {color}（需 #RRGGBB 十六进制或主题名 {'/'.join(COLOR_THEMES)}）")
        return 1

    author = args.author or (ask("作者标识", "losemymind") if interactive else "losemymind")

    out_dir = Path(args.out) if args.out else Path.cwd()
    if out_dir.exists() and not out_dir.is_dir():
        print(f"❌ --out 不是目录: {out_dir}")
        return 1
    agent_dir = out_dir / name
    if agent_dir.exists():
        print(f"❌ 目录已存在: {agent_dir}")
        return 1
    try:
        agent_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"❌ 无法创建目录: {e}")
        return 1

    body = build_agent_md(name, description, mode, tools, color)
    (agent_dir / "AGENT.md").write_text(body, encoding="utf-8")
    print(f"✅ 创建骨架: {agent_dir}")
    if args.records:
        append_record(args.records, name, mode, author,
                      args.source, args.source_repo, args.method)
        print(f"   已登记创建记录: {args.records}")
    else:
        print("   提示: 传 --records <账本文件> 可追加创建/来源记录")
    print(f"   下一步: python scripts/validate_agents.py --dir {agent_dir}")
    print("   然后按本技能 SKILL.md 阶段 4-6 完善内容与测试")
    return 0


if __name__ == "__main__":
    sys.exit(main())