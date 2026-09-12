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
    # Full permission matrix derives from the whitelist: edit is denied, no tools leak.
    assert '  "*": deny' in md
    assert "  edit: deny" in md
    assert "  bash: allow" not in md


def test_scaffold_default_tools_are_consistent(tmp_path):
    md = _scaffold(tmp_path)
    assert "tools: [read, grep, glob, bash]" in md
    assert "- 允许：`read` `grep` `glob` `bash`" in md


def test_scaffold_edit_grant_permits_edit(tmp_path):
    md = _scaffold(tmp_path, "--tools", "read,edit")
    assert "tools: [read, edit]" in md
    assert "- 允许：`read` `edit`" in md
    # The full permission matrix follows the tools whitelist: edit is allowed,
    # never silently denied by boilerplate.
    assert '  "*": deny' in md
    assert "  edit: allow" in md
    assert "  edit: deny" not in md
    assert "- 禁止：`edit`" not in md


def test_scaffold_write_alias_also_permits_edit(tmp_path):
    md = _scaffold(tmp_path, "--tools", "read,write")
    assert "tools: [read, write]" in md
    assert "  edit: allow" in md
    assert "  edit: deny" not in md


def test_scaffold_edit_alias_case_insensitive(tmp_path):
    md = _scaffold(tmp_path, "--tools", "read,Edit")
    assert "tools: [read, edit]" in md
    assert "  edit: allow" in md
    assert "  edit: deny" not in md


def test_scaffold_default_permission_is_full_matrix(tmp_path):
    md = _scaffold(tmp_path)
    fm = md.split("---", 2)[1]
    assert '  "*": deny' in fm
    assert "  read: allow" in fm
    assert "  glob: allow" in fm
    assert "  grep: allow" in fm
    assert "  bash: allow" in fm
    assert "  edit: deny" in fm
    assert "  task: deny" in fm
    assert "  lsp: deny" in fm
    assert "  external_directory: deny" in fm


def test_scaffold_output_still_validates(tmp_path):
    _ = _scaffold(tmp_path, "--tools", "read,grep,glob")
    v = run_script("scripts/validate_agents.py", "--strict", "--dir", str(tmp_path / "probe"))
    assert v.returncode == 0, v.stdout + v.stderr


def test_scaffold_color_injected_quoted_and_validates(tmp_path):
    """--color injects a quoted hex line and the scaffold still passes strict."""
    md = _scaffold(tmp_path, "--color", "#DC2626")
    assert 'color: "#DC2626"' in md
    v = run_script("scripts/validate_agents.py", "--strict", "--dir", str(tmp_path / "probe"))
    assert v.returncode == 0, v.stdout + v.stderr


def test_scaffold_theme_color_injected(tmp_path):
    md = _scaffold(tmp_path, "--color", "accent")
    assert 'color: "accent"' in md


def test_scaffold_without_color_uses_default(tmp_path):
    """No --color: the scaffold still carries the default UI display color."""
    md = _scaffold(tmp_path)
    fm = md.split("---", 2)[1]
    assert 'color: "#DC2626"' in fm
    assert "# color:" not in fm


def test_scaffold_rejects_invalid_color(tmp_path):
    r = run_script(
        "scripts/create_agent.py", "--no-interactive", "--name", "probe",
        "--color", "red", "--out", str(tmp_path),
    )
    assert r.returncode == 1
    assert "color" in r.stdout
