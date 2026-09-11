"""Tests for adapt_agent.py (per-client frontmatter conversion before install)."""

from conftest import run_script

CANONICAL = """---
name: demo-agent
description: "演示代理，用于单元测试"
mode: subagent
tools: [read, grep, bash, write, customtool]
permission:
  edit: ask
model: anthropic/claude-sonnet-4-6
---

# demo-agent

## 角色定位

演示用

## 职责范围

**必须做：**
- 测试

**拒绝做：**
- 不修改

## 工具与权限

- 允许：read grep bash write

## 协作协议

- **升级路径**：交还用户

## 完成标准

- [ ] 通过

## 限制与边界

- 测试用
"""


def _write_agent(tmp_path, content: str) -> str:
    d = tmp_path / "demo-agent"
    d.mkdir()
    f = d / "AGENT.md"
    f.write_text(content, encoding="utf-8")
    return str(d)


def test_opencode_converts_whitelist_to_permission(tmp_path):
    d = _write_agent(tmp_path, CANONICAL)
    r = run_script("scripts/adapt_agent.py", d, "--client", "opencode")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "tools: [read, grep, bash, write, customtool]" not in r.stdout
    assert "tools:" not in r.stdout  # whitelist must be gone, not left as an array
    assert "edit: ask" in r.stdout  # explicit permission entry always wins
    assert "read: allow" in r.stdout
    assert "bash: allow" in r.stdout
    assert "webfetch: deny" in r.stdout  # tool not whitelisted -> denied
    assert "mode: subagent" in r.stdout


def test_opencode_folds_write_into_edit(tmp_path):
    content = CANONICAL.replace("  edit: ask\n", "")
    d = _write_agent(tmp_path, content)
    r = run_script("scripts/adapt_agent.py", d, "--client", "opencode")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "edit: allow" in r.stdout  # write in whitelist folded to edit


def test_claude_maps_tools_and_model(tmp_path):
    d = _write_agent(tmp_path, CANONICAL)
    r = run_script("scripts/adapt_agent.py", d, "--client", "claude")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "tools: Read, Grep, Bash, Write" in r.stdout
    assert "model: sonnet" in r.stdout
    assert "customtool" not in r.stdout.split("---")[1]  # unmappable dropped
    assert "dropped: customtool" in r.stderr


def test_claude_unmappable_only_tools_fails(tmp_path):
    content = CANONICAL.replace(
        "tools: [read, grep, bash, write, customtool]", "tools: [customtool]"
    )
    d = _write_agent(tmp_path, content)
    r = run_script("scripts/adapt_agent.py", d, "--client", "claude")
    assert r.returncode == 1
    assert "maps to no Claude tool names" in r.stderr


def test_codex_passthrough_verbatim(tmp_path):
    d = _write_agent(tmp_path, CANONICAL)
    r = run_script("scripts/adapt_agent.py", d, "--client", "codex")
    assert r.returncode == 0, r.stdout + r.stderr
    assert r.stdout == CANONICAL
    assert "best-effort" in r.stderr


def test_missing_path_fails(tmp_path):
    r = run_script("scripts/adapt_agent.py", str(tmp_path / "nope"), "--client", "opencode")
    assert r.returncode == 1
    assert "does not exist" in r.stderr


def test_out_writes_adapted_file(tmp_path):
    d = _write_agent(tmp_path, CANONICAL)
    out = tmp_path / "adapted" / "AGENT.md"
    r = run_script("scripts/adapt_agent.py", d, "--client", "opencode", "--out", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    assert out.is_file()
    written = out.read_text(encoding="utf-8")
    assert "read: allow" in written
    assert "tools: [read" not in written


def test_opencode_drops_permission_shorthand_and_materializes(tmp_path):
    content = CANONICAL.replace("permission:\n  edit: ask\n", "permission: allow\n")
    d = _write_agent(tmp_path, content)
    r = run_script("scripts/adapt_agent.py", d, "--client", "opencode")
    assert r.returncode == 0, r.stdout + r.stderr
    assert "permission: allow" not in r.stdout  # global allow must not survive
    assert "read: allow" in r.stdout
    assert "webfetch: deny" in r.stdout          # un-whitelisted tool denied
