"""Repository-level naming and independence gates for maintained workspaces.

Policy is kept outside the creators. Historical notes are maintained text;
only explicitly registered third-party samples and index data are exempt.
"""
import ast
from pathlib import Path
import re

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACES = {name: REPO_ROOT / name for name in ("skill-creator", "agent-creator")}
CREATORS = {name: root / "skills" / name for name, root in WORKSPACES.items()}
SAMPLE_DIRS = ("brainstorming", "copywriting", "git-pushing", "loki-mode",
               "react-best-practices", "systematic-debugging")
SCAN_EXTS = {".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt", ".template", ".db"}
RELATION_WORDS = {"孪生", "同构", "兄弟创建器", "另一创建器",
                  "sibling creator", "twin creator", "mirror of"}
LEGACY_MODULES = {
    "agent-creator": ("adapt_agent", "package_agent", "validate_agents", "security_scan",
                      "search_agent_index", "build_agent_index", "compare_agents", "create_agent"),
    "skill-creator": ("aggregate_benchmark", "compare_skills", "create_skill", "package_skill",
                      "run_eval", "run_loop", "run_scenario", "search_index", "build_index", "validate_skills"),
}


def _exclusions(name):
    product = Path("skills") / name
    excluded = [product / "indexes/upstream.db"]
    if name == "skill-creator":
        excluded += [product / "examples" / sample for sample in SAMPLE_DIRS]
    return tuple(excluded)


def _authored_files(root, excluded=()):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if {"__pycache__", ".pytest_cache"}.intersection(rel.parts):
            continue
        if any(rel == item or item in rel.parents for item in excluded):
            continue
        if path.suffix.lower() in SCAN_EXTS:
            yield path


def _peer_tokens(name):
    peer = next(key for key in CREATORS if key != name)
    tokens = {peer, peer.replace("-", "_"), peer.replace("-", " "),
              "代理创建器" if peer == "agent-creator" else "技能创建器", *LEGACY_MODULES[peer]}
    for folder, suffix in (("scripts", ".py"), ("agents", ".md"), ("references", ".md")):
        own = {p.stem for p in (CREATORS[name] / folder).glob(f"*{suffix}")}
        for path in (CREATORS[peer] / folder).glob(f"*{suffix}"):
            if path.stem not in own:
                tokens.add(path.stem if folder != "references" else path.name)
                if path.stem.startswith(peer.split("-")[0] + "-"):
                    tokens.add(path.stem)
    return tokens | RELATION_WORDS


def _scan_for_tokens(root, tokens, excluded=()):
    problems = []
    patterns = [(token, re.compile(r"(?<![A-Za-z0-9_-])" + re.escape(token) + r"(?![A-Za-z0-9_-])", re.I)
                 if token.isascii() else re.compile(re.escape(token))) for token in sorted(tokens)]
    for path in _authored_files(root, excluded):
        text = path.read_text(encoding="utf-8", errors="replace")
        for token, pattern in patterns:
            if pattern.search(text):
                problems.append(f"{path.relative_to(root).as_posix()}: {token!r}")
    return problems


@pytest.mark.parametrize("name", WORKSPACES)
def test_workspace_has_no_cross_references(name):
    assert CREATORS[name].is_dir()
    problems = _scan_for_tokens(WORKSPACES[name], _peer_tokens(name), _exclusions(name))
    assert not problems, f"{name} must describe and use its own resources:\n" + "\n".join(problems)


@pytest.mark.parametrize("relative", [
    "README.md", "AGENTS.md", "INSTALL.md", "tests/test_contract.py",
    "skills/demo/evolutions/2026-09-29-note.md", "templates/evals.json.template",
    "examples/local/README.md", "upstream.db",
])
def test_maintained_text_has_no_history_or_directory_bypass(tmp_path, relative):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("```text\nAGENT-CREATOR\n```", encoding="utf-8")
    assert len(_scan_for_tokens(tmp_path, {"agent-creator"}, _exclusions("skill-creator"))) == 1


def test_registered_upstream_data_is_not_scanned(tmp_path):
    for relative in ("skills/skill-creator/examples/brainstorming/SKILL.md",
                     "skills/skill-creator/indexes/upstream.db"):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("agent-creator", encoding="utf-8")
    assert not _scan_for_tokens(tmp_path, {"agent-creator"}, _exclusions("skill-creator"))
    overview = tmp_path / "skills/skill-creator/examples/README.md"
    overview.write_text("agent-creator", encoding="utf-8")
    assert len(_scan_for_tokens(tmp_path, {"agent-creator"}, _exclusions("skill-creator"))) == 1


@pytest.mark.parametrize("text", ["与Agent-Creator一致", "引用agent_validate.py", "遵循agent_reviewer.md"])
def test_names_embedded_in_chinese_text_are_detected(tmp_path, text):
    (tmp_path / "README.md").write_text(text, encoding="utf-8")
    assert _scan_for_tokens(tmp_path, {"agent-creator", "agent_validate", "agent_reviewer"})


@pytest.mark.parametrize("name", CREATORS)
def test_scripts_and_agent_prompts_use_domain_prefix(name):
    product = CREATORS[name]
    prefix = name.split("-")[0]
    for path in (product / "scripts").glob("*.py"):
        if path.name != "_project_paths.py":
            assert re.fullmatch(prefix + r"_[a-z0-9]+(?:_[a-z0-9]+)*\.py", path.name), path
    for path in (product / "agents").glob("*.md"):
        assert re.fullmatch(prefix + r"_[a-z0-9]+(?:_[a-z0-9]+)*\.md", path.name), path


def test_no_cross_artifact_imports():
    for name, product in CREATORS.items():
        peer = next(key for key in CREATORS if key != name)
        own = {p.stem for p in (product / "scripts").glob("*.py")}
        foreign = {p.stem for p in (CREATORS[peer] / "scripts").glob("*.py")} - own
        for path in (product / "scripts").glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8-sig"))):
                names = ([a.name for a in node.names] if isinstance(node, ast.Import)
                         else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
                assert not foreign.intersection(n.split(".")[0] for n in names), path
