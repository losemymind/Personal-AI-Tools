"""Tests for validate_skills.py."""


def test_valid_skill_passes(temp_skill):
    from conftest import run_script

    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(temp_skill))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "All skills passed" in r.stdout


def test_missing_risk_fails_strict(temp_skill):
    from conftest import run_script

    content = (temp_skill / "SKILL.md").read_text(encoding="utf-8")
    content = content.replace("risk: safe\n", "")
    (temp_skill / "SKILL.md").write_text(content, encoding="utf-8")

    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(temp_skill))
    assert r.returncode == 1
    assert "Missing 'risk'" in r.stdout


def test_dangling_backtick_reference_fails(temp_skill):
    from conftest import run_script

    content = (temp_skill / "SKILL.md").read_text(encoding="utf-8")
    content += "\n参考 `references/missing.md` 获取细节。\n"
    (temp_skill / "SKILL.md").write_text(content, encoding="utf-8")

    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(temp_skill))
    assert r.returncode == 1
    assert "Backtick reference" in r.stdout


def test_backtick_ref_inside_fence_is_ignored(temp_skill):
    """Illustrative paths inside fenced code blocks must NOT fail validation."""
    from conftest import run_script

    content = (temp_skill / "SKILL.md").read_text(encoding="utf-8")
    content += "\n## 示例路径\n\n```\nsrc/auth.ts\ntests/auth.test.ts\n```\n"
    (temp_skill / "SKILL.md").write_text(content, encoding="utf-8")

    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(temp_skill))
    assert r.returncode == 0, r.stdout + r.stderr


def test_dir_dot_resolves_real_folder_name(temp_skill):
    """`--dir .` from inside a skill dir must compare against the real folder name.

    Installed skills (e.g. ~/.config/opencode/skills/<name>/) are typically
    validated from within their own directory.
    """
    from conftest import run_script

    r = run_script(
        "scripts/validate_skills.py", "--strict", "--dir", ".", cwd=temp_skill
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "does not match folder name" not in r.stdout


def test_module_style_self_reference_resolves_outside_repo(temp_skill):
    """`<own-folder>/scripts/x.py` refs must resolve once installed outside the repo.

    The skill dir lives under tmp (no repo root above it), so only the
    self-name-prefix resolution rule can make this reference resolve.
    """
    from conftest import run_script

    scripts_dir = temp_skill / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "helper.py").write_text("print('ok')\n", encoding="utf-8")
    content = (temp_skill / "SKILL.md").read_text(encoding="utf-8")
    content += "\n运行 `test-skill/scripts/helper.py` 执行辅助任务。\n"
    (temp_skill / "SKILL.md").write_text(content, encoding="utf-8")

    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(temp_skill))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Backtick reference" not in r.stdout


def _set_allowed_tools(temp_skill, line: str) -> None:
    content = (temp_skill / "SKILL.md").read_text(encoding="utf-8")
    content = content.replace("risk: safe\n", f"risk: safe\n{line}\n")
    (temp_skill / "SKILL.md").write_text(content, encoding="utf-8")


def test_allowed_tools_list_form_passes(temp_skill):
    from conftest import run_script

    _set_allowed_tools(temp_skill, "allowed-tools: [Read, Grep, Glob]")
    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(temp_skill))
    assert r.returncode == 0, r.stdout + r.stderr


def test_allowed_tools_string_form_passes(temp_skill):
    from conftest import run_script

    _set_allowed_tools(temp_skill, 'allowed-tools: "Read, Grep"')
    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(temp_skill))
    assert r.returncode == 0, r.stdout + r.stderr


def test_allowed_tools_mapping_form_fails(temp_skill):
    """`allowed-tools` must be a list/string of tool names, not a bool map."""
    from conftest import run_script

    _set_allowed_tools(temp_skill, "allowed-tools: {Read: true}")
    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(temp_skill))
    assert r.returncode == 1
    assert "allowed-tools" in r.stdout
    assert "All skills passed" not in r.stdout


def test_allowed_tools_non_string_entry_fails(temp_skill):
    from conftest import run_script

    _set_allowed_tools(temp_skill, "allowed-tools: [Read, 5]")
    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(temp_skill))
    assert r.returncode == 1
    assert "allowed-tools" in r.stdout


def test_allowed_tools_client_label_list_fails(temp_skill):
    """A client-label list is supported-clients metadata, never a whitelist."""
    from conftest import run_script

    _set_allowed_tools(temp_skill, "allowed-tools: [claude, opencode]")
    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(temp_skill))
    assert r.returncode == 1
    assert "client labels" in r.stdout


def test_allowed_tools_empty_fails(temp_skill):
    from conftest import run_script

    _set_allowed_tools(temp_skill, "allowed-tools: []")
    r = run_script("scripts/validate_skills.py", "--strict", "--dir", str(temp_skill))
    assert r.returncode == 1
    assert "empty" in r.stdout


def test_nonexistent_dir_fails(tmp_path):
    """`--dir` pointing at a missing directory must FAIL loudly instead of
    printing "Checked 0 skills" and exiting 0 (os.walk on a missing path yields
    nothing, which would silently turn a wrong --dir into a green release gate)."""
    from conftest import run_script

    r = run_script(
        "scripts/validate_skills.py",
        "--strict",
        "--dir",
        str(tmp_path / "no-such-skill-dir"),
    )
    assert r.returncode == 1
    assert "Scan directory does not exist" in r.stdout
    assert "All skills passed" not in r.stdout
