"""Tests for validate_agents.py."""


def test_valid_agent_passes(temp_agent):
    from conftest import run_script

    r = run_script(
        "scripts/validate_agents.py",
        "--strict",
        "--dir",
        str(temp_agent),
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "All agents passed" in r.stdout


def test_missing_boundary_fails_strict(temp_agent):
    from conftest import run_script

    content = (temp_agent / "AGENT.md").read_text(encoding="utf-8")
    content = content.replace("## 职责范围", "## 职责（无边界）")
    (temp_agent / "AGENT.md").write_text(content, encoding="utf-8")

    r = run_script(
        "scripts/validate_agents.py",
        "--strict",
        "--dir",
        str(temp_agent),
    )
    assert r.returncode == 1
    assert "职责范围" in r.stdout or "boundary" in r.stdout


def test_tools_declaration_required(temp_agent):
    from conftest import run_script

    content = (temp_agent / "AGENT.md").read_text(encoding="utf-8")
    content = content.replace("tools: [read, grep, bash]\n", "")
    content = content.replace("permission:\n  edit: deny\n", "")
    # remove the body section too, so no permission declaration remains anywhere
    content = content.replace("## 工具与权限\n\n- 允许：read grep bash\n- 禁止：edit\n\n", "")
    (temp_agent / "AGENT.md").write_text(content, encoding="utf-8")

    r = run_script(
        "scripts/validate_agents.py",
        "--strict",
        "--dir",
        str(temp_agent),
    )
    assert r.returncode == 1
    assert "tools/permission" in r.stdout


def test_audit_file_is_exempt(temp_agent):
    """A library may hold an audit ledger (AGENTS-AUDIT.md) next to its agents;
    the validator must not treat it as an agent definition."""
    from conftest import run_script

    (temp_agent / "AGENTS-AUDIT.md").write_text(
        "# agents/ — 代理审计\n\n> 记录数据来源与入库合规。\n", encoding="utf-8"
    )

    r = run_script(
        "scripts/validate_agents.py",
        "--strict",
        "--dir",
        str(temp_agent),
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "Checked 1 agents" in r.stdout


def test_nonexistent_dir_fails(tmp_path):
    """`--dir` pointing at a missing directory must FAIL loudly instead of
    printing "Checked 0 agents" and exiting 0 (os.walk on a missing path yields
    nothing, which would silently turn a wrong --dir into a green release gate)."""
    from conftest import run_script

    r = run_script(
        "scripts/validate_agents.py",
        "--strict",
        "--dir",
        str(tmp_path / "no-such-agent-dir"),
    )
    assert r.returncode == 1
    assert "Scan directory does not exist" in r.stdout
    assert "All agents passed" not in r.stdout


def test_description_angle_bracket_advisory(temp_agent):
    """Angle-bracket placeholders in description distort trigger matching; flagged
    as advisory (never a failure), mirroring validate_skills.py discipline."""
    from conftest import run_script

    content = (temp_agent / "AGENT.md").read_text(encoding="utf-8")
    content = content.replace(
        'description: "测试代理"', 'description: "测试 <agent-name> 代理"'
    )
    (temp_agent / "AGENT.md").write_text(content, encoding="utf-8")

    r = run_script("scripts/validate_agents.py", "--strict", "--dir", str(temp_agent))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "placeholder" in r.stdout


def test_description_multiline_advisory(temp_agent):
    """Multi-line description breaks the single-line trigger surface; advisory only."""
    from conftest import run_script

    content = (temp_agent / "AGENT.md").read_text(encoding="utf-8")
    content = content.replace('description: "测试代理"', 'description: "首行\\n次行"')
    (temp_agent / "AGENT.md").write_text(content, encoding="utf-8")

    r = run_script("scripts/validate_agents.py", "--strict", "--dir", str(temp_agent))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "multi-line" in r.stdout


def _with_color(temp_agent, color_line: str):
    content = (temp_agent / "AGENT.md").read_text(encoding="utf-8")
    content = content.replace("mode: subagent\n", f"mode: subagent\n{color_line}", 1)
    (temp_agent / "AGENT.md").write_text(content, encoding="utf-8")


def test_hex_color_passes(temp_agent):
    """A quoted #RRGGBB color is a valid optional UI-display field."""
    from conftest import run_script

    _with_color(temp_agent, 'color: "#DC2626"\n')
    r = run_script("scripts/validate_agents.py", "--strict", "--dir", str(temp_agent))
    assert r.returncode == 0, r.stdout + r.stderr


def test_theme_color_passes(temp_agent):
    """An opencode theme name is a valid color value."""
    from conftest import run_script

    _with_color(temp_agent, "color: accent\n")
    r = run_script("scripts/validate_agents.py", "--strict", "--dir", str(temp_agent))
    assert r.returncode == 0, r.stdout + r.stderr


def test_invalid_color_fails(temp_agent):
    """A non-hex, non-theme color is a frontmatter error."""
    from conftest import run_script

    _with_color(temp_agent, 'color: "red"\n')
    r = run_script("scripts/validate_agents.py", "--strict", "--dir", str(temp_agent))
    assert r.returncode == 1
    assert "color" in r.stdout


def test_unquoted_hex_color_fails(temp_agent):
    """An unquoted hex color parses as a YAML comment (value None) and must be
    rejected, enforcing the `color: "#DC2626"` quoting discipline."""
    from conftest import run_script

    _with_color(temp_agent, color_line="color: #DC2626\n")
    r = run_script("scripts/validate_agents.py", "--strict", "--dir", str(temp_agent))
    assert r.returncode == 1
    assert "color" in r.stdout


def test_sparse_permission_advises_full_matrix(temp_agent):
    """A permission map without the `"*": deny` default-reject is an advisory
    (never a failure), nudging toward the full permission matrix."""
    from conftest import run_script

    r = run_script("scripts/validate_agents.py", "--strict", "--dir", str(temp_agent))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "默认拒绝" in r.stdout


def test_no_color_is_fine(temp_agent):
    """color is optional: an agent without a color field must pass. Only the
    field's value is validated when present."""
    from conftest import run_script

    r = run_script("scripts/validate_agents.py", "--strict", "--dir", str(temp_agent))
    assert r.returncode == 0, r.stdout + r.stderr
