"""Tests for package_skill.py (per-client skill packaging).

Covers the opencode permission/whitelist merge (the bug inherited from
adapt_agent.py: a bare permission string must not discard the tools whitelist or
widen it to a global rule), per-client post-checks, the copied tree, zip output,
and argument/input errors.
"""

import importlib.util
import zipfile
from pathlib import Path

import yaml
from conftest import ARTIFACT, run_script

PACKAGE_SKILL = ARTIFACT / "scripts" / "package_skill.py"

SKILL_MD = """---
name: pkg-demo
description: "打包测试技能"
category: testing
risk: safe
source: self
version: "0.1.0"
date_added: "2026-09-11"
{extra}
---

# pkg-demo

## 何时使用此技能

- 测试

## 示例

```text
a -> b
```

## 限制和注意事项

- 无
"""


def _load():
    spec = importlib.util.spec_from_file_location("package_skill", PACKAGE_SKILL)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _frontmatter_of(text: str) -> dict:
    import re
    m = re.match(r"^---\s*\n(.*?)\n?---", text, re.DOTALL)
    assert m, text[:200]
    return yaml.safe_load(m.group(1))


def _adapted(extra: str, client: str):
    mod = _load()
    content = SKILL_MD.format(extra=extra)
    out, _notes = mod.adapt_skill_markdown(content, client, origin="SKILL.md")
    return _frontmatter_of(out)


# --- opencode permission merge ---------------------------------------------


def test_opencode_merges_whitelist_when_permission_is_string_shorthand():
    fm = _adapted("tools: [read, bash]\npermission: allow", "opencode")
    # The whitelist must not be dropped, and the global shorthand must not survive.
    assert "tools" not in fm
    perm = fm["permission"]
    assert perm["read"] == "allow"
    assert perm["bash"] == "allow"
    assert perm["edit"] == "deny"
    assert perm["grep"] == "deny"
    assert perm["webfetch"] == "deny"


def test_opencode_explicit_permission_entry_wins_over_whitelist_default():
    fm = _adapted("tools: [read]\npermission:\n  edit: allow", "opencode")
    perm = fm["permission"]
    assert perm["read"] == "allow"
    assert perm["edit"] == "allow"      # explicit wins
    assert perm["bash"] == "deny"       # default for non-whitelisted


def test_opencode_client_label_tools_are_not_a_whitelist():
    # `tools: [claude, opencode, ...]` is the repo's supported-clients metadata.
    fm = _adapted("tools: [claude, opencode, codex, deepseek]", "opencode")
    assert "permission" not in fm
    assert "tools" not in fm


def test_opencode_write_maps_to_edit_permission():
    fm = _adapted("tools: [write, read]", "opencode")
    perm = fm["permission"]
    assert perm["edit"] == "allow"   # write aliases edit
    assert perm["read"] == "allow"
    assert perm["bash"] == "deny"


# --- claude transform ------------------------------------------------------


def test_claude_whitelist_becomes_comma_string():
    fm = _adapted("tools: [read, grep, bash]", "claude")
    assert fm["tools"] == "Read, Grep, Bash"


def test_claude_client_label_tools_dropped():
    fm = _adapted("tools: [claude, opencode]", "claude")
    assert "tools" not in fm


# --- packaging (filesystem) ------------------------------------------------


def _make_skill(tmp_path: Path, extra: str = "tools: [read, bash]\npermission: allow") -> Path:
    d = tmp_path / "pkg-demo"
    d.mkdir()
    (d / "SKILL.md").write_text(SKILL_MD.format(extra=extra), encoding="utf-8")
    (d / "scripts").mkdir()
    (d / "scripts" / "helper.py").write_text("print('x')\n", encoding="utf-8")
    cache = d / "scripts" / "__pycache__"
    cache.mkdir()
    (cache / "helper.cpython-311.pyc").write_text("junk", encoding="utf-8")
    return d


def test_packages_all_clients_and_copies_tree(tmp_path):
    src = _make_skill(tmp_path)
    out = tmp_path / "dist"
    r = run_script("scripts/package_skill.py", str(src), "--client", "claude",
                   "--client", "opencode", "--client", "codex", "--client", "deepseek",
                   "--out", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    for client in ("claude", "opencode", "codex", "deepseek"):
        target = out / client / "pkg-demo"
        assert (target / "SKILL.md").is_file(), client
        assert (target / "scripts" / "helper.py").is_file(), client
        assert not (target / "scripts" / "__pycache__").exists(), client
        # every emitted SKILL.md must parse and carry the adapted frontmatter
        _frontmatter_of((target / "SKILL.md").read_text(encoding="utf-8"))


def test_zip_output_contains_skill(tmp_path):
    src = _make_skill(tmp_path)
    out = tmp_path / "dist"
    r = run_script("scripts/package_skill.py", str(src), "--client", "opencode",
                   "--out", str(out), "--zip")
    assert r.returncode == 0, r.stdout + r.stderr
    z = out / "opencode" / "pkg-demo.zip"
    assert z.is_file()
    with zipfile.ZipFile(z) as zf:
        assert "pkg-demo/SKILL.md" in zf.namelist()


def test_comma_separated_clients_accepted(tmp_path):
    src = _make_skill(tmp_path)
    out = tmp_path / "dist"
    r = run_script("scripts/package_skill.py", str(src), "--client", "claude,opencode",
                   "--out", str(out))
    assert r.returncode == 0, r.stdout + r.stderr
    assert (out / "claude" / "pkg-demo" / "SKILL.md").is_file()
    assert (out / "opencode" / "pkg-demo" / "SKILL.md").is_file()


# --- errors ----------------------------------------------------------------


def test_missing_skill_md_fails(tmp_path):
    d = tmp_path / "empty-skill"
    d.mkdir()
    r = run_script("scripts/package_skill.py", str(d), "--client", "claude",
                   "--out", str(tmp_path / "dist"))
    assert r.returncode == 1
    assert "no SKILL.md" in r.stderr or "no SKILL.md" in r.stdout


def test_unknown_client_fails(tmp_path):
    src = _make_skill(tmp_path)
    r = run_script("scripts/package_skill.py", str(src), "--client", "vim",
                   "--out", str(tmp_path / "dist"))
    assert r.returncode == 2
    assert "unknown client" in r.stderr


def test_missing_description_rejected(tmp_path):
    d = tmp_path / "pkg-demo"
    d.mkdir()
    (d / "SKILL.md").write_text(
        '---\nname: pkg-demo\n---\n\n# x\n', encoding="utf-8"
    )
    r = run_script("scripts/package_skill.py", str(d), "--client", "opencode",
                   "--out", str(tmp_path / "dist"))
    assert r.returncode == 1


def test_out_inside_skill_rejected(tmp_path):
    src = _make_skill(tmp_path)
    r = run_script("scripts/package_skill.py", str(src), "--client", "claude",
                   "--out", str(src / "dist"))
    assert r.returncode == 1
    assert "must not be inside" in r.stderr
