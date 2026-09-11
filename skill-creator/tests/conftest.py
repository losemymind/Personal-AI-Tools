"""Shared pytest fixtures: temp skill dir and script runner (skill-creator self-tests).

The skill scripts under test live in the artifact (skills/skill-creator), the
single committed source. Tests are dev-only and sit in this workspace root.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# Dev workspace root = the directory containing tests/.
REPO_ROOT = Path(__file__).resolve().parents[1]
# Artifact = the skill source under test.
ARTIFACT = REPO_ROOT / "skills" / "skill-creator"

SKILL_FIXTURE = """---
name: {name}
description: "{desc}"
category: testing
risk: safe
---

# {name}

## 概述

{desc}

## 何时使用此技能

- 测试时使用

## 工作原理

1. 执行

## 示例

```text
输入 → 输出
```

## 最佳实践

- ✅ 这样做

## 限制和注意事项

- 无
"""


def run_script(script: str, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run one of the artifact's CLI scripts and capture output.

    `script` is artifact-relative, e.g. "scripts/validate_skills.py".
    """
    return subprocess.run(
        [sys.executable, str(ARTIFACT / script), *args],
        capture_output=True,
        text=True,
        cwd=cwd or REPO_ROOT,
    )


@pytest.fixture
def temp_skill(tmp_path: Path) -> Path:
    d = tmp_path / "test-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(
        SKILL_FIXTURE.format(name="test-skill", desc="测试技能"), encoding="utf-8"
    )
    return d
