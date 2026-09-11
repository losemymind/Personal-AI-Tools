"""Round-4 audit for the agent-creator artifact.

Covers the post-check / scaffold boundaries flagged as next-round todos:
`create_agent.py` YAML-safety under non-ASCII / multiline / backslash-bearing
descriptions (the twin `create_skill.py` already used lambda replacements),
description-length parity, and clean `--out` path-conflict handling in both
`create_agent.py` and `adapt_agent.py`.
"""

import yaml

from conftest import ARTIFACT, run_script


def _frontmatter(path) -> dict:
    text = path.read_text(encoding="utf-8")
    end = text.index("\n---", 3)
    return yaml.safe_load(text[3:end])


def test_create_agent_description_with_backslash_is_valid_yaml(tmp_path):
    # A Windows path or regex in the description must not be mangled by `re`'s
    # replacement-escape processing (the f-string-as-replacement bug).
    desc = r"use C:\Users\me\project and \d+ regex"
    r = run_script(
        "scripts/create_agent.py", "--name", "probe-backslash",
        "--description", desc, "--no-interactive", "--out", str(tmp_path),
    )
    assert r.returncode == 0, r.stdout + r.stderr
    fm = _frontmatter(tmp_path / "probe-backslash" / "AGENT.md")
    assert fm["description"] == desc


def test_create_agent_description_multiline_round_trips(tmp_path):
    desc = "line one\nline two\nline three"
    r = run_script(
        "scripts/create_agent.py", "--name", "probe-multiline",
        "--description", desc, "--no-interactive", "--out", str(tmp_path),
    )
    assert r.returncode == 0, r.stdout + r.stderr
    fm = _frontmatter(tmp_path / "probe-multiline" / "AGENT.md")
    assert fm["description"] == desc


def test_create_agent_rejects_oversized_description(tmp_path):
    ok = "a" * 300
    r = run_script(
        "scripts/create_agent.py", "--name", "probe-len-ok",
        "--description", ok, "--no-interactive", "--out", str(tmp_path),
    )
    assert r.returncode == 0, r.stdout + r.stderr
    over = "a" * 301
    r2 = run_script(
        "scripts/create_agent.py", "--name", "probe-len-over",
        "--description", over, "--no-interactive", "--out", str(tmp_path),
    )
    assert r2.returncode == 1
    assert "超长" in r2.stdout
    assert not (tmp_path / "probe-len-over").exists()


def test_create_agent_rejects_whitespace_description(tmp_path):
    r = run_script(
        "scripts/create_agent.py", "--name", "probe-blank",
        "--description", "   ", "--no-interactive", "--out", str(tmp_path),
    )
    assert r.returncode == 1
    assert not (tmp_path / "probe-blank").exists()


def test_create_agent_out_conflicts_fail_cleanly(tmp_path):
    a_file = tmp_path / "afile"
    a_file.write_text("x", encoding="utf-8")
    for out in (str(a_file), str(a_file / "sub")):
        r = run_script(
            "scripts/create_agent.py", "--name", "probe-out",
            "--description", "d", "--no-interactive", "--out", out,
        )
        assert r.returncode == 1, f"out={out}: " + r.stdout + r.stderr
        assert "Traceback" not in r.stderr, r.stderr


def test_adapt_agent_out_conflicts_fail_cleanly(tmp_path):
    agent = tmp_path / "AGENT.md"
    agent.write_text(
        '---\nname: probe\ndescription: "d"\ntools: [read]\n---\n\n# x\n',
        encoding="utf-8",
    )
    outdir = tmp_path / "outdir"
    outdir.mkdir()
    a_file = tmp_path / "afile"
    a_file.write_text("x", encoding="utf-8")
    for out in (str(outdir), str(a_file / "sub" / "AGENT.md")):
        r = run_script(
            "scripts/adapt_agent.py", str(agent), "--client", "opencode", "--out", out,
        )
        assert r.returncode == 1, f"out={out}: " + r.stdout + r.stderr
        assert "Traceback" not in r.stderr, r.stderr
