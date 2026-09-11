"""Tests for package_agent.py (per-client agent packaging).

Covers the opencode permission/whitelist merge (fixes the privilege widening in
adapt_agent.py: a bare permission string must not discard the tools whitelist or
widen it to a global rule), the write->edit alias, client-label tools metadata,
claude tool/model adaptation, per-client post-checks, the copied tree, zip
output, bare AGENT.md input, and argument/input errors.
"""

import importlib.util
import re
import zipfile
from pathlib import Path

import yaml
from conftest import ARTIFACT, run_script

PACKAGE_AGENT = ARTIFACT / "scripts" / "package_agent.py"

AGENT_MD = """---
name: pkg-demo
description: "打包测试代理"
mode: subagent
version: "0.1.0"
{extra}
---

# pkg-demo

## 角色定位

测试用代理。

## 职责范围

**必须做：**
- 测试

**拒绝做：**
- 不修改

## 工具与权限

- 允许：read

## 协作协议

- **升级路径**：交还用户

## 完成标准

- [ ] 通过

## 限制与边界

- 仅测试
"""


def _load():
    spec = importlib.util.spec_from_file_location("package_agent", PACKAGE_AGENT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _frontmatter_of(text: str) -> dict:
    m = re.match(r"^---\s*\n(.*?)\n?---", text, re.DOTALL)
    assert m, text[:200]
    return yaml.safe_load(m.group(1))


def _adapted(extra: str, client: str):
    mod = _load()
    content = AGENT_MD.format(extra=extra)
    out, _notes = mod.adapt_agent_markdown(content, client, origin="AGENT.md")
    return _frontmatter_of(out)


# --- opencode permission merge ---------------------------------------------


def test_opencode_drops_shorthand_and_merges_whitelist():
    fm = _adapted("tools: [read, grep, write]\npermission: allow", "opencode")
    # The whitelist must not be dropped, and the global shorthand must not survive.
    assert "tools" not in fm
    perm = fm["permission"]
    assert isinstance(perm, dict) and not isinstance(perm, str)
    assert perm["read"] == "allow"
    assert perm["grep"] == "allow"
    assert perm["edit"] == "allow"   # write aliases edit
    assert perm["bash"] == "deny"
    assert perm["webfetch"] == "deny"


def test_opencode_explicit_permission_entry_wins_over_whitelist_default():
    fm = _adapted("tools: [read]\npermission:\n  edit: allow", "opencode")
    perm = fm["permission"]
    assert perm["read"] == "allow"
    assert perm["edit"] == "allow"      # explicit wins
    assert perm["bash"] == "deny"       # default for non-whitelisted


def test_opencode_client_label_tools_are_not_a_whitelist():
    fm = _adapted("tools: [claude, opencode, codex, deepseek]", "opencode")
    assert "permission" not in fm
    assert "tools" not in fm


def test_opencode_write_maps_to_edit_permission():
    fm = _adapted("tools: [write, read]", "opencode")
    perm = fm["permission"]
    assert perm["edit"] == "allow"
    assert perm["read"] == "allow"
    assert perm["bash"] == "deny"


# --- claude transform ------------------------------------------------------


def test_claude_whitelist_becomes_comma_string_and_model_alias():
    fm = _adapted("tools: [read, grep, bash]\nmodel: anthropic/claude-sonnet-4-6", "claude")
    assert fm["tools"] == "Read, Grep, Bash"
    assert fm["model"] == "sonnet"


def test_claude_unmappable_model_dropped():
    fm = _adapted("tools: [read]\nmodel: some/opus-x", "claude")
    assert fm["model"] == "opus"


def test_claude_client_label_tools_dropped():
    fm = _adapted("tools: [claude, opencode]", "claude")
    assert "tools" not in fm


# --- packaging (filesystem) ------------------------------------------------


def _make_agent(tmp_path: Path, extra: str = "tools: [read, bash]\npermission: allow") -> Path:
    d = tmp_path / "pkg-demo"
    d.mkdir()
    (d / "AGENT.md").write_text(AGENT_MD.format(extra=extra), encoding="utf-8")
    (d / "references").mkdir()
    (d / "references" / "notes.md").write_text("# notes\n", encoding="utf-8")
    cache = d / "scripts" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "x.cpython-311.pyc").write_text("junk", encoding="utf-8")
    return d


def test_packages_all_clients_and_copies_tree(tmp_path):
    src = _make_agent(tmp_path)
    out = tmp_path / "dist"
    r = run_script("scripts/package_agent.py", str(src), "--client", "claude",
                   "--client", "opencode", "--client", "codex", "--client", "deepseek",
                   "--out", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    for client in ("claude", "opencode", "codex", "deepseek"):
        target = out / client / "pkg-demo"
        assert (target / "AGENT.md").is_file(), client
        assert (target / "references" / "notes.md").is_file(), client
        assert not (target / "scripts" / "__pycache__").exists(), client
        fm = _frontmatter_of((target / "AGENT.md").read_text(encoding="utf-8"))
        assert fm["name"] == "pkg-demo"


def test_bare_agent_md_input_packages_only_the_file(tmp_path):
    src = tmp_path / "solo"
    src.mkdir()
    agent_file = src / "AGENT.md"
    agent_file.write_text(AGENT_MD.format(extra="tools: [read]"), encoding="utf-8")
    (src / "references").mkdir()  # sibling noise must NOT be copied for file input
    out = tmp_path / "dist"
    r = run_script("scripts/package_agent.py", str(agent_file), "--client", "opencode",
                   "--out", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    target = out / "opencode" / "pkg-demo"
    assert (target / "AGENT.md").is_file()
    assert not (target / "references").exists()


def test_zip_output_contains_agent(tmp_path):
    src = _make_agent(tmp_path)
    out = tmp_path / "dist"
    r = run_script("scripts/package_agent.py", str(src), "--client", "opencode",
                   "--out", str(out), "--zip")
    assert r.returncode == 0, r.stdout + r.stderr
    z = out / "opencode" / "pkg-demo.zip"
    assert z.is_file()
    with zipfile.ZipFile(z) as zf:
        assert "pkg-demo/AGENT.md" in zf.namelist()


def test_comma_separated_clients_accepted(tmp_path):
    src = _make_agent(tmp_path)
    out = tmp_path / "dist"
    r = run_script("scripts/package_agent.py", str(src), "--client", "claude,opencode",
                   "--out", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (out / "claude" / "pkg-demo" / "AGENT.md").is_file()
    assert (out / "opencode" / "pkg-demo" / "AGENT.md").is_file()


# --- errors ----------------------------------------------------------------


def test_missing_agent_md_fails(tmp_path):
    d = tmp_path / "empty-agent"
    d.mkdir()
    r = run_script("scripts/package_agent.py", str(d), "--client", "claude",
                   "--out", str(tmp_path / "dist"))
    assert r.returncode == 1
    assert "no AGENT.md" in r.stderr or "no AGENT.md" in r.stdout


def test_unknown_client_fails(tmp_path):
    src = _make_agent(tmp_path)
    r = run_script("scripts/package_agent.py", str(src), "--client", "vim",
                   "--out", str(tmp_path / "dist"))
    assert r.returncode == 2
    assert "unknown client" in r.stderr


def test_missing_description_rejected(tmp_path):
    d = tmp_path / "pkg-demo"
    d.mkdir()
    (d / "AGENT.md").write_text('---\nname: pkg-demo\n---\n\n# x\n', encoding="utf-8")
    r = run_script("scripts/package_agent.py", str(d), "--client", "opencode",
                   "--out", str(tmp_path / "dist"))
    assert r.returncode == 1


def test_no_frontmatter_rejected(tmp_path):
    d = tmp_path / "pkg-demo"
    d.mkdir()
    (d / "AGENT.md").write_text("# no frontmatter\n", encoding="utf-8")
    r = run_script("scripts/package_agent.py", str(d), "--client", "claude",
                   "--out", str(tmp_path / "dist"))
    assert r.returncode == 1
    assert "no frontmatter" in r.stderr


def test_invalid_frontmatter_rejected(tmp_path):
    d = tmp_path / "pkg-demo"
    d.mkdir()
    (d / "AGENT.md").write_text("---\nname: [unclosed\n---\n\n# x\n", encoding="utf-8")
    r = run_script("scripts/package_agent.py", str(d), "--client", "claude",
                   "--out", str(tmp_path / "dist"))
    assert r.returncode == 1


def test_out_inside_agent_rejected(tmp_path):
    src = _make_agent(tmp_path)
    r = run_script("scripts/package_agent.py", str(src), "--client", "claude",
                   "--out", str(src / "dist"))
    assert r.returncode == 1
    assert "must not be inside" in r.stderr


def test_out_is_existing_file_rejected(tmp_path):
    src = _make_agent(tmp_path)
    out_file = tmp_path / "dist"
    out_file.write_text("i am a file\n", encoding="utf-8")
    r = run_script("scripts/package_agent.py", str(src), "--client", "claude",
                   "--out", str(out_file))
    assert r.returncode == 1
    assert "existing file" in r.stderr
