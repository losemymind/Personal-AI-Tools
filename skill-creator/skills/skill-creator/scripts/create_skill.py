"""Interactive skill scaffold generator (part of skill-creator tooling).

Creates a complete skill skeleton: SKILL.md with valid frontmatter,
optional scripts/ references/ examples/ templates/ dirs. Output validates with
validate_skills.py.

Usage:
    python scripts/create_skill.py                          # interactive
    python scripts/create_skill.py --name foo --category productivity --risk safe --out ./skills  # non-interactive
"""

import argparse
import io
import json
import re
import sys
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "templates" / "SKILL.template.md"
EVALS_TEMPLATE_PATH = SCRIPT_DIR.parent / "templates" / "evals.json.template"

CATEGORIES = [
    "development", "frontend", "backend", "mobile", "testing", "devops",
    "architecture", "design", "database", "api",
    "security", "pen-testing", "compliance", "cryptography",
    "ai", "machine-learning", "prompt-engineering", "data-science",
    "git", "productivity", "documentation", "deployment",
    "product", "planning", "communication", "research",
]
RISKS = ["none", "safe", "critical", "offensive", "unknown"]
VALID_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Central creation-record ledger (provenance/author/date live here, not in
# SKILL.md frontmatter — a skill is client-neutral before packaging).
RECORDS_HEADER = (
    "# 技能创建记录（SKILL-RECORDS）\n\n"
    "> 由 skill-creator 在创建/导入技能时追加（`create_skill.py --records <本文件>`）。\n"
    "> 记录各技能的来源与创建元数据；`SKILL.md` frontmatter 只保留 "
    "`name`/`description`/`risk`/`category`。\n\n"
    "| 技能 | category | created | author | source | source_repo | method | evolutions |\n"
    "|---|---|---|---|---|---|---|---|\n"
)


def append_record(records_path, name, category, author, source, source_repo, method) -> None:
    """Append one provenance row to the creation-record ledger (create if absent)."""
    records_path = Path(records_path)
    records_path.parent.mkdir(parents=True, exist_ok=True)
    if not records_path.exists():
        records_path.write_text(RECORDS_HEADER, encoding="utf-8")
    cells = [name, category, date.today().isoformat(), author, source,
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
            setattr(sys, stream_name, io.TextIOWrapper(buffer, encoding="utf-8", errors="backslashreplace"))


def ask(prompt: str, default: str = "", choices: list | None = None) -> str:
    hint_parts = []
    if choices:
        hint_parts.append("/".join(choices))
    if default:
        hint_parts.append(f"默认: {default}")
    suffix = f" ({' | '.join(hint_parts)})" if hint_parts else ""
    while True:
        try:
            value = input(f"{prompt}{suffix}: ").strip()
        except EOFError:
            # Non-interactive/redirected stdin: fall back to the default or exit cleanly.
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
        value = ask("技能名称（kebab-case）")
        if not VALID_NAME.match(value):
            print("❌ 名称必须是小写字母/数字+连字符，如 code-review")
            continue
        return value


def build_skill_md(name, description, category, risk) -> str:
    if TEMPLATE_PATH.exists():
        content = TEMPLATE_PATH.read_text(encoding="utf-8")
        content = content.replace("your-skill-name", name)
        content = re.sub(
            r'^category: .*$',
            f"category: {category}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        content = re.sub(
            r'^risk: .*$',
            f"risk: {risk}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        content = re.sub(
            r'^description: ".*?"$',
            lambda m: f"description: {_yaml_str(description)}",
            content,
            count=1,
            flags=re.MULTILINE,
        )
        return content
    # fallback minimal skeleton
    return f"""---
name: {name}
description: {_yaml_str(description)}
category: {category}
risk: {risk}
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

- `other-skill` — 什么时候用它更合适（用纯技能名；禁止 `@` 语法）

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
    parser.add_argument("--author", default=None, help="作者标识（仅写入创建记录账本，不进 frontmatter）")
    parser.add_argument("--source", default="self", help="来源：self/community/official/URL（仅记录账本）")
    parser.add_argument("--source-repo", default="", dest="source_repo", help="上游仓库 OWNER/REPO（仅记录账本）")
    parser.add_argument("--method", default="created", help="创建方式：created/imported/adapted（仅记录账本）")
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

    author = args.author or (ask("作者标识", "losemymind") if interactive else "losemymind")

    if not description.strip():
        print("❌ 描述不能为空白（validate_skills.py 会拒绝）")
        return 1
    if len(description) > 1024:
        print(f"❌ 描述超长: {len(description)} 字符（上限 1024）")
        return 1

    out_dir = Path(args.out) if args.out else Path.cwd()
    if out_dir.exists() and not out_dir.is_dir():
        print(f"❌ --out 不是目录: {out_dir}")
        return 1
    skill_dir = out_dir / name
    if skill_dir.exists():
        print(f"❌ 目录已存在: {skill_dir}")
        return 1
    try:
        skill_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"❌ 无法创建目录: {e}")
        return 1

    body = build_skill_md(name, description, category, risk)
    (skill_dir / "SKILL.md").write_text(body, encoding="utf-8")

    # Ship trigger tests with the skill (quality-bar item 8 / release discipline):
    # a scaffolded skill must not immediately trip the "No evals.json" advisory.
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir(exist_ok=True)
    if EVALS_TEMPLATE_PATH.exists():
        evals_body = EVALS_TEMPLATE_PATH.read_text(encoding="utf-8").replace(
            "your-skill-name", name
        )
    else:
        evals_body = (
            "{\n"
            f'  "skill_name": "{name}",\n'
            '  "evals": [\n'
            '    {"id": 1, "query": "应当触发本技能的真实用户说法", "should_trigger": true, "expected_output": ""},\n'
            '    {"id": 2, "query": "近似干扰项：不应触发", "should_trigger": false, "expected_output": ""}\n'
            "  ]\n"
            "}\n"
        )
    (evals_dir / "evals.json").write_text(evals_body, encoding="utf-8")

    print(f"✅ 创建骨架: {skill_dir}")
    print(f"   含 evals/evals.json（触发用例，随技能回归）")
    if args.records:
        append_record(args.records, name, category, author,
                      args.source, args.source_repo, args.method)
        print(f"   已登记创建记录: {args.records}")
    else:
        print("   提示: 传 --records <账本文件> 可追加创建/来源记录")
    print(f"   下一步: python scripts/validate_skills.py --dir {skill_dir}")
    print(f"   然后按本技能 SKILL.md 阶段 4-6 完善内容与测试")
    return 0


if __name__ == "__main__":
    sys.exit(main())