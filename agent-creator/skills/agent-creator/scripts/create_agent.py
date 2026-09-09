"""Interactive agent scaffold generator (part of agent-creator tooling).

Creates a complete agent skeleton: AGENT.md with valid frontmatter,
identity/boundary/permission/collaboration sections. Output validates with
validate_agents.py.

Usage:
    python scripts/create_agent.py                          # interactive
    python scripts/create_agent.py --name my-reviewer --mode subagent --out ./agents  # non-interactive
"""

import argparse
import io
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "templates" / "AGENT.template.md"

VALID_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
MODES = ["primary", "subagent", "all"]


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
        value = input(f"{prompt}{suffix}: ").strip()
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


def build_agent_md(name, description, mode, tools, version) -> str:
    if TEMPLATE_PATH.exists():
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        content = content.replace("your-agent-name", name)
        content = content.replace("subagent", mode, 1)
        content = re.sub(
            r"^description: \".*?\"$",
            f'description: "{description}"',
            content,
            count=1,
            flags=re.MULTILINE,
        )
        content = re.sub(
            r"^version: \".*?\"$",
            f'version: "{version}"',
            content,
            count=1,
            flags=re.MULTILINE,
        )
        content = re.sub(
            r"^tools: \[.*?\]$",
            f"tools: [{', '.join(tools)}]",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        return content
    tools_str = ", ".join(tools)
    return f"""---
name: {name}
description: "{description}"
mode: {mode}
tools: [{tools_str}]
permission:
  edit: deny
version: "{version}"
tools_clients: [claude, opencode, codex, deepseek]
---

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

- 允许：{tools_str}
- 禁止：edit（默认拒绝，除非职责明确要求）

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
    parser.add_argument("--version", default="0.1.0")
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

    mode = args.mode or ("subagent" if not interactive else ask("模式", "subagent", MODES))

    tools = [t.strip() for t in args.tools.split(",") if t.strip()]

    out_dir = Path(args.out) if args.out else Path.cwd()
    agent_dir = out_dir / name
    if agent_dir.exists():
        print(f"❌ 目录已存在: {agent_dir}")
        return 1
    agent_dir.mkdir(parents=True, exist_ok=True)

    body = build_agent_md(name, description, mode, tools, args.version)
    (agent_dir / "AGENT.md").write_text(body, encoding="utf-8")
    print(f"✅ 创建骨架: {agent_dir}")
    print(f"   下一步: python scripts/validate_agents.py --dir {agent_dir}")
    print("   然后按本技能 SKILL.md 阶段 4-6 完善内容与测试")
    return 0


if __name__ == "__main__":
    sys.exit(main())