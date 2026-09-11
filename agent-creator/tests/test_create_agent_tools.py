"""create_agent.py scaffold must keep frontmatter and body tools consistent.

Regression: the template body hard-coded ``允许：`read` `grep` `bash```, so any
``--tools`` value disagreed with the frontmatter whitelist (and the default even
omitted ``glob``). The body is now derived from the whitelist, and an explicit
edit-family grant no longer contradicts the boilerplate ``permission: edit: deny``.
"""

from conftest import run_script


def _scaffold(tmp_path, *extra):
    r = run_script(
        "scripts/create_agent.py", "--no-interactive", "--name", "probe",
        "--out", str(tmp_path), *extra,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    return (tmp_path / "probe" / "AGENT.md").read_text(encoding="utf-8")


def test_scaffold_body_matches_frontmatter_tools(tmp_path):
    md = _scaffold(tmp_path, "--tools", "read,grep,glob")
    assert "tools: [read, grep, glob]" in md
    assert "- 允许：`read` `grep` `glob`" in md
    assert "`bash`" not in md  # the old hard-coded body leaked bash
    assert "- 禁止：`edit`" in md
    assert "permission:\n  edit: deny" in md


def test_scaffold_default_tools_are_consistent(tmp_path):
    md = _scaffold(tmp_path)
    assert "tools: [read, grep, glob, bash]" in md
    assert "- 允许：`read` `grep` `glob` `bash`" in md


def test_scaffold_edit_grant_drops_default_deny(tmp_path):
    md = _scaffold(tmp_path, "--tools", "read,edit")
    assert "tools: [read, edit]" in md
    assert "- 允许：`read` `edit`" in md
    # An explicit edit grant must not be silently denied by boilerplate.
    assert "permission:" not in md
    assert "edit: deny" not in md
    assert "- 禁止：`edit`" not in md


def test_scaffold_write_alias_also_drops_default_deny(tmp_path):
    md = _scaffold(tmp_path, "--tools", "read,write")
    assert "tools: [read, write]" in md
    assert "edit: deny" not in md


def test_scaffold_edit_alias_case_insensitive(tmp_path):
    md = _scaffold(tmp_path, "--tools", "read,Edit")
    assert "tools: [read, edit]" in md
    assert "permission:" not in md
    assert "edit: deny" not in md


def test_scaffold_output_still_validates(tmp_path):
    _ = _scaffold(tmp_path, "--tools", "read,grep,glob")
    v = run_script("scripts/validate_agents.py", "--strict", "--dir", str(tmp_path / "probe"))
    assert v.returncode == 0, v.stdout + v.stderr
