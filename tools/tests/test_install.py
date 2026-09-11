"""Tests for tools/scripts/install.py (install orchestrator).

Covers: client auto-detection, target resolution, workspace landing for
skills/agents, --force backup, validation rollback, and argument errors.
"""

import importlib.util
from pathlib import Path

import pytest
from conftest import INSTALL, REPO_ROOT, run_install


def _load():
    spec = importlib.util.spec_from_file_location("install", INSTALL)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


# --- pure functions: detection & landing -----------------------------------


def test_detect_clients_from_env_markers():
    mod = _load()
    assert mod.detect_clients({"CLAUDECODE": "1"}, []) == ["claude"]
    assert mod.detect_clients({"OPENCODE": "1"}, []) == ["opencode"]
    assert mod.detect_clients({}, []) == []


def test_detect_clients_from_workspace_dirs(tmp_path):
    mod = _load()
    (tmp_path / ".opencode").mkdir()
    assert mod.detect_clients({}, [tmp_path]) == ["opencode"]


def test_landing_matrix_workspace_paths(tmp_path):
    mod = _load()
    assert mod.landing_base("skill", "claude", "workspace", tmp_path) == tmp_path / ".claude" / "skills"
    assert mod.landing_base("skill", "opencode", "workspace", tmp_path) == tmp_path / ".opencode" / "skills"
    assert mod.landing_base("agent", "opencode", "workspace", tmp_path) == tmp_path / ".opencode" / "agent"
    assert mod.landing_base("agent", "codex", "workspace", tmp_path) is None  # no documented landing


# --- argument errors (rc=2) -------------------------------------------------


def test_no_targets_is_arg_error():
    r = run_install("--client", "claude")
    assert r.returncode == 2
    assert "no targets" in r.stderr


def test_unknown_client_is_arg_error(tmp_path, make_skill):
    src = make_skill()
    r = run_install(str(src), "--client", "vim", "--scope", "workspace", "--dest", str(tmp_path))
    assert r.returncode == 2
    assert "unknown client" in r.stderr


def test_workspace_without_dest_is_arg_error(make_skill):
    src = make_skill()
    r = run_install(str(src), "--client", "claude", "--scope", "workspace")
    assert r.returncode == 2
    assert "--dest" in r.stderr


def test_target_without_marker_is_arg_error(tmp_path):
    d = tmp_path / "junk"
    d.mkdir()
    r = run_install(str(d), "--client", "claude", "--scope", "workspace", "--dest", str(tmp_path))
    assert r.returncode == 2
    assert "no SKILL.md or AGENT.md" in r.stderr


def test_artifact_mismatch_is_arg_error(tmp_path, make_skill):
    src = make_skill()
    r = run_install(str(src), "--artifact", "agent", "--client", "claude",
                    "--scope", "workspace", "--dest", str(tmp_path))
    assert r.returncode == 2
    assert "--artifact" in r.stderr


def test_zip_without_out_is_arg_error(make_skill, tmp_path):
    src = make_skill()
    r = run_install(str(src), "--client", "claude", "--scope", "workspace",
                    "--dest", str(tmp_path), "--zip")
    assert r.returncode == 2
    assert "--out" in r.stderr


# --- workspace landing ------------------------------------------------------


def test_install_skill_to_claude_workspace(tmp_path, make_skill):
    src = make_skill("my-skill")
    r = run_install(str(src), "--client", "claude", "--scope", "workspace", "--dest", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    target = tmp_path / ".claude" / "skills" / "my-skill"
    assert (target / "SKILL.md").is_file()
    assert "name: my-skill" in (target / "SKILL.md").read_text(encoding="utf-8")


def test_install_agent_to_opencode_workspace(tmp_path, make_agent):
    src = make_agent("my-agent")
    r = run_install(str(src), "--client", "opencode", "--scope", "workspace", "--dest", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    target = tmp_path / ".opencode" / "agent" / "my-agent"
    assert (target / "AGENT.md").is_file()


def test_install_creator_product(tmp_path):
    # skill-creator is itself a skill; installing it is a package_skill op.
    r = run_install("--creator", "skill-creator", "--client", "claude",
                    "--scope", "workspace", "--dest", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    target = tmp_path / ".claude" / "skills" / "skill-creator"
    assert (target / "SKILL.md").is_file()
    # creator products carry their own validator + index; install must self-check.
    assert (target / "scripts" / "validate_skills.py").is_file()


def test_install_agent_creator_product(tmp_path):
    # agent-creator is a skill-shaped creator that BUNDLES validate_agents.py
    # (for AGENT libraries) but has no AGENT.md itself. Install must not run the
    # agent validator against the creator dir (regression: it used to fail with
    # "no agent definitions found" and roll back).
    r = run_install("--creator", "agent-creator", "--client", "opencode",
                    "--scope", "workspace", "--dest", str(tmp_path))
    assert r.returncode == 0, r.stdout + r.stderr
    target = tmp_path / ".opencode" / "skills" / "agent-creator"
    assert (target / "SKILL.md").is_file()
    assert (target / "scripts" / "validate_agents.py").is_file()
    assert not (target / "AGENT.md").exists()


def test_creators_install_independently(tmp_path):
    # Each creator installs on its own without the other present in the landing.
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    r1 = run_install("--creator", "skill-creator", "--client", "claude",
                     "--scope", "workspace", "--dest", str(a))
    assert r1.returncode == 0, r1.stdout + r1.stderr
    assert (a / ".claude" / "skills" / "skill-creator" / "SKILL.md").is_file()
    assert not (a / ".claude" / "skills" / "agent-creator").exists()

    r2 = run_install("--creator", "agent-creator", "--client", "claude",
                     "--scope", "workspace", "--dest", str(b))
    assert r2.returncode == 0, r2.stdout + r2.stderr
    assert (b / ".claude" / "skills" / "agent-creator" / "SKILL.md").is_file()
    assert not (b / ".claude" / "skills" / "skill-creator").exists()


def test_unknown_creator_is_arg_error(tmp_path):
    r = run_install("--creator", "nope", "--client", "claude",
                    "--scope", "workspace", "--dest", str(tmp_path))
    assert r.returncode == 2
    assert "unknown creator" in r.stderr


# --- existing landing / --force --------------------------------------------


def test_existing_landing_without_force_fails(tmp_path, make_skill):
    src = make_skill("dup-skill")
    (tmp_path / ".claude" / "skills" / "dup-skill").mkdir(parents=True)
    r = run_install(str(src), "--client", "claude", "--scope", "workspace", "--dest", str(tmp_path))
    assert r.returncode == 1
    assert "use --force" in r.stderr


def test_force_backs_up_existing_landing(tmp_path, make_skill):
    src = make_skill("dup-skill")
    old = tmp_path / ".claude" / "skills" / "dup-skill"
    old.mkdir(parents=True)
    (old / "OLD.txt").write_text("old", encoding="utf-8")
    r = run_install(str(src), "--client", "claude", "--scope", "workspace",
                    "--dest", str(tmp_path), "--force")
    assert r.returncode == 0, r.stdout + r.stderr
    assert (old / "SKILL.md").is_file()
    backup = tmp_path / ".claude" / "skills" / "dup-skill.bak"
    assert (backup / "OLD.txt").is_file()


# --- validation rollback ----------------------------------------------------


def test_validation_failure_rolls_back(tmp_path):
    # A fake skill shipping its own failing validator must not be landed.
    src = tmp_path / "bad-skill"
    (src / "scripts").mkdir(parents=True)
    (src / "SKILL.md").write_text(
        "---\nname: bad-skill\ndescription: \"d\"\ncategory: testing\nrisk: safe\n---\n\n# x\n",
        encoding="utf-8",
    )
    (src / "scripts" / "validate_skills.py").write_text("import sys; sys.exit(1)\n", encoding="utf-8")
    r = run_install(str(src), "--client", "claude", "--scope", "workspace", "--dest", str(tmp_path))
    assert r.returncode == 1
    assert not (tmp_path / ".claude" / "skills" / "bad-skill").exists()


# --- auto-detection via env -------------------------------------------------


def test_client_autodetected_from_env(tmp_path, make_skill):
    src = make_skill("auto-skill")
    import os
    import subprocess
    import sys
    env = dict(os.environ)
    env["CLAUDECODE"] = "1"
    env.pop("OPENCODE", None)
    r = subprocess.run(
        [sys.executable, str(INSTALL), str(src), "--scope", "workspace", "--dest", str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT), env=env,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "auto-detected client" in r.stdout
    assert (tmp_path / ".claude" / "skills" / "auto-skill" / "SKILL.md").is_file()


def test_no_client_and_no_markers_is_arg_error(tmp_path, make_skill):
    src = make_skill("nocli-skill")
    import os
    import subprocess
    import sys
    env = {k: v for k, v in os.environ.items() if k not in
           ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "OPENCODE", "OPENCODE_BIN", "OPENCODE_PID",
            "CODEX_HOME", "CODEX_SANDBOX", "DEEPSEEK_HARNESS", "DEEPSEEK_AGENT")}
    r = subprocess.run(
        [sys.executable, str(INSTALL), str(src), "--scope", "workspace", "--dest", str(tmp_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(REPO_ROOT), env=env,
    )
    assert r.returncode == 2
    assert "auto-detect" in r.stderr
