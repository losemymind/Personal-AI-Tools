"""Interactive skill scaffold generator (part of skill-creator tooling).

Creates a complete skill skeleton: SKILL.md with valid frontmatter (+ version field),
optional scripts/ references/ examples/ templates/ dirs. Output validates with
validate_skills.py.

Usage:
    python scripts/create_skill.py                          # interactive
    python scripts/create_skill.py --name foo --category productivity --risk safe --out ./skills  # non-interactive
"""

import argparse
import io
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "templates" / "SKILL.template.md"

CATEGORIES = [
    "development", "frontend", "backend", "mobile", "testing", "devops",
    "architecture", "design", "database", "api",
    "security", "pen-testing", "compliance", "cryptography",
    "ai", "machine-learning", "prompt-engineering", "data-science",
    "git", "productivity", "documentation", "deployment",
    "product", "planning", "communication", "research",
]
RISKS = ["none", "safe", "critical", "offensive", "unknown"]
TOOLS = ["claude", "opencode", "codex", "deepseek"]
VALID_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


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
        value = ask("技能名称（kebab-case）")
        if not VALID_NAME.match(value):
            print("❌ 名称必须是小写字母/数字+连字符，如 code-review")
            continue
        return value


def build_skill_md(name, description, category, risk, tools, author, version) -> str:
    if TEMPLATE_PATH.exists():
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        content = content.replace("your-skill-name", name)
        content = content.replace('[tag-one, tag-two]', '[]')
        import re as _re
        content = _re.sub(
            r'^category: .*$',
            f"category: {category}",
            content,
            count=1,
            flags=_re.MULTILINE,
        )
        content = _re.sub(
            r'^risk: .*$',
            f"risk: {risk}",
            content,
            count=1,
            flags=_re.MULTILINE,
        )
        content = _re.sub(
            r'^description: ".*?"$',
            f'description: "{description}"',
            content,
            count=1,
            flags=_re.MULTILINE,
        )
        content = _re.sub(
            r'^date_added: "YYYY-MM-DD"$',
            f'date_added: "{date.today().isoformat()}"',
            content,
            count=1,
            flags=_re.MULTILINE,
        )
        content = _re.sub(
            r'^author: your-name-or-handle$',
            f"author: {author}",
            content,
            count=1,
            flags=_re.MULTILINE,
        )
        content = _re.sub(
            r'^tools: \[.*\]$',
            f"tools: [{', '.join(tools)}]",
            content,
            count=1,
            flags=_re.MULTILINE,
        )
        content = _re.sub(
            r'^version: .*$',
            f'version: "{version}"',
            content,
            count=1,
            flags=_re.MULTILINE,
        )
        return content
    # fallback minimal skeleton
    tools_str = ", ".join(tools)
    return f"""---
name: {name}
description: "{description}"
category: {category}
risk: {risk}
source: self
version: "{version}"
date_added: "{date.today().isoformat()}"
author: {author}
tags: []
tools: [{tools_str}]
---

# {name.replace('-', ' ').title()}

## 概述

简要说明这个技能的作用以及为什么存在。2-4 句话最合适。

## 何时使用此技能

- 当用户需要[场景 1]时使用
- 在处理[场景 2]时使用

## 工作原理

### 步骤 1：[操作]

详细、可执行的步骤说明。

## 示例

### 示例 1：[用例]

```text
输入 → 输出说明或可直接运行的示例
```

## 最佳实践

- ✅ 推荐的做法
- ❌ 避免的做法

## 相关技能

- `@other-skill` — 什么时候用它更合适

## 限制和注意事项

- 在这个环境下不工作的情况
- 已知边界与做不到的事情
"""


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Create a skill scaffold")
    parser.add_argument("--name", default=None)
    parser.add_argument("--description", default=None)
    parser.add_argument("--category", default=None, choices=CATEGORIES)
    parser.add_argument("--risk", default=None, choices=RISKS)
    parser.add_argument("--tools", default="opencode", help="逗号分隔的客户端列表")
    parser.add_argument("--author", default=None)
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
            description = ask("一句话描述（做什么+何时触发，≤1024 字符）")
        else:
            description = f"{name} 工作流技能。"

    category = args.category
    if not category:
        if interactive:
            category = ask("分类", "productivity", CATEGORIES)
        else:
            category = "productivity"

    risk = args.risk
    if not risk:
        if interactive:
            risk = ask("风险级别", "safe", RISKS)
        else:
            risk = "safe"

    tools = [t.strip() for t in args.tools.split(",") if t.strip()]
    author = args.author or (ask("作者标识", "losemymind") if interactive else "losemymind")

    out_dir = Path(args.out) if args.out else Path.cwd()
    skill_dir = out_dir / name
    if skill_dir.exists():
        print(f"❌ 目录已存在: {skill_dir}")
        return 1
    skill_dir.mkdir(parents=True, exist_ok=True)

    body = build_skill_md(name, description, category, risk, tools, author, args.version)
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")
    print(f"✅ 创建骨架: {skill_dir}")
    print(f"   下一步: python scripts/validate_skills.py --dir {skill_dir}")
    print(f"   然后按本技能 SKILL.md 阶段 4-6 完善内容与测试")
    return 0


if __name__ == "__main__":
    sys.exit(main())