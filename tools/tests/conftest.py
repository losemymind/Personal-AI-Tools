"""Shared fixtures for the tools-layer tests (install.py orchestrator).

install.py is a dev-only tool; its tests live here so they do not depend on the
creator workspaces' conftest. Tests run the CLI as a subprocess (stable contract)
and import the module for pure-function unit tests.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# tools/tests/conftest.py -> tools/tests -> tools -> repo root
REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALL = REPO_ROOT / "tools" / "scripts" / "install.py"


def run_install(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(INSTALL), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(cwd) if cwd else str(REPO_ROOT),
    )


SKILL_MD = """---
name: {name}
description: "{desc}"
category: testing
risk: safe
---

# {name}

## 何时使用此技能

- 测试

## 示例

```text
a -> b
```

## 限制和注意事项

- 无
"""

AGENT_MD = """---
name: {name}
description: "{desc}"
mode: subagent
tools: [read]
permission:
  edit: deny
---

# {name}

## 角色定位

测试

## 职责范围

**必须做：** 审查

**拒绝做：** 不改码

## 工具与权限

- 允许：read
- 禁止：edit

## 协作协议

- **何时被调用**：用户请求
- **汇报格式**：清单
- **升级路径**：权限不足时交还用户

## 完成标准

- [ ] 输出清单

## 限制与边界

- 无
"""


@pytest.fixture
def make_skill(tmp_path: Path):
    def _make(name: str = "demo-skill") -> Path:
        d = tmp_path / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(SKILL_MD.format(name=name, desc="测试技能"), encoding="utf-8")
        return d
    return _make


@pytest.fixture
def make_agent(tmp_path: Path):
    def _make(name: str = "demo-agent") -> Path:
        d = tmp_path / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "AGENT.md").write_text(AGENT_MD.format(name=name, desc="测试代理"), encoding="utf-8")
        return d
    return _make
