"""Shared pytest fixtures: temp agent dir and script runner (agent-creator self-tests).

The agent scripts under test live in the artifact (skills/agent-creator), the
single committed source. Tests are dev-only and sit in this workspace root.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Dev workspace root = the directory containing tests/.
REPO_ROOT = Path(__file__).resolve().parents[1]
# Artifact = the skill source under test.
ARTIFACT = REPO_ROOT / "skills" / "agent-creator"

AGENT_FIXTURE = """---
name: {name}
description: "{desc}"
mode: subagent
tools: [read, grep, bash]
permission:
  edit: deny
version: "0.1.0"
---

# {name}

## 角色定位

{desc}

## 职责范围

**必须做：**
- 审查

**拒绝做：**
- 不修改代码

## 工作方式

只读

## 工具与权限

- 允许：read grep bash
- 禁止：edit

## 协作协议

- **何时被调用**：用户请求
- **汇报格式**：清单
- **升级路径**：权限不足时交还用户

## 完成标准

- [ ] 输出清单

## 限制与边界

- 不运行测试
"""


def run_script(script: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run one of the artifact's CLI scripts and capture output.

    `script` is artifact-relative, e.g. "scripts/validate_agents.py".
    """
    return subprocess.run(
        [sys.executable, str(ARTIFACT / script), *args],
        capture_output=True,
        text=True,
        cwd=cwd or REPO_ROOT,
    )


@pytest.fixture
def temp_agent(tmp_path: Path) -> Path:
    d = tmp_path / "test-agent"
    d.mkdir()
    (d / "AGENT.md").write_text(
        AGENT_FIXTURE.format(name="test-agent", desc="测试代理"), encoding="utf-8"
    )
    return d
