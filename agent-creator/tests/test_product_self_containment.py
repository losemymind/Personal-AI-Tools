"""Self-containment scan for the agent-creator artifact (dev-only release gate).

The agent-creator product (skills/agent-creator) is a skill-shaped creator whose
shipped validator (validate_agents.py) validates AGENT.md agent libraries — not
the creator itself. Release-readiness therefore enforces self-containment here,
in the dev-only pytest suite: the mirror of skill-creator's "product strict
self-check" becomes a pytest because agent-creator cannot self-validate its own
skill-shaped product with its own tooling.

Scan rules (mirror the former build/check_self_containment.py):
  - every *.md under the artifact is scanned, except examples/ and evolutions/
    (upstream learning samples / historical records)
  - fenced code blocks are ignored (illustrative command examples)
  - refs to ~/client paths, URLs, placeholders (<, >, *, ?, xxx, your-) skip
  - a ref whose first path segment is a dev-only dir (tests/, build/, .git)
    is an error (the artifact must not depend on the development layout)
  - a ref resolves if it exists relative to the md's dir or the skill root
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = REPO_ROOT / "skills" / "agent-creator"

KNOWN_TOP = (
    "SKILL.md",
    "README.md",
    "scripts",
    "indexes",
    "references",
    "templates",
    "agents",
    "evolutions",
)
SKIP_DIRS = {"examples", "evolutions"}
DEV_ONLY_MARKERS = ("tests", "build", ".git", ".pytest_cache", ".github")
PLACEHOLDER_MARKERS = ("<", ">", "*", "?", "…", "xxx", "your-", "x.md", "x.py", "x.sh", "setup.sh")


def is_cjk(text: str) -> bool:
    return any("\u4e00" <= ch <= "\u9fff" for ch in text)


def clean_fenced(content: str) -> str:
    return re.sub(r"```.*?```", "", content, flags=re.DOTALL)


def extract_path_token(cand: str) -> str:
    """Pull the artifact-internal path token out of a command-like ref
    (`python scripts/validate_agents.py ...` -> `scripts/validate_agents.py`)."""
    for token in cand.split():
        for known in (*KNOWN_TOP, *DEV_ONLY_MARKERS):
            if token == known or token.startswith(known + "/"):
                return token
    return cand


def check_dir(artifact: Path) -> list[str]:
    problems: list[str] = []
    tops = (*KNOWN_TOP, *DEV_ONLY_MARKERS)

    for md in sorted(artifact.rglob("*.md")):
        rel_parts = md.relative_to(artifact).parts
        if any(p in SKIP_DIRS for p in rel_parts):
            continue
        content = clean_fenced(md.read_text(encoding="utf-8", errors="replace"))
        refs = set(re.findall(r"`([^`]+)`", content))
        links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", content)
        candidates = set()
        for ref in refs:
            cand = ref.strip()
            if not cand or is_cjk(cand):
                continue
            if cand.startswith(("~", "$", "{", "http://", "https://", "mailto:")):
                continue
            if any(m in cand for m in PLACEHOLDER_MARKERS):
                continue
            token = extract_path_token(cand)
            if "." in token and "/" not in token:
                continue
            if not any(token == k or token.startswith(k + "/") for k in tops):
                continue  # client path / field name, not artifact-internal
            candidates.add(token)
        for link in links:
            link_clean = link.split("#")[0].strip()
            if not link_clean or link_clean.startswith(("http://", "https://", "mailto:", "~", "<")):
                continue
            if link_clean.startswith("http") or "://" in link_clean:
                continue
            if Path(link_clean).is_absolute():
                continue
            token = link_clean.rstrip("/")
            if any(token == k or token.startswith(k + "/") for k in tops):
                candidates.add(token)

        rel_md = md.relative_to(artifact).parent
        for token in sorted(candidates):
            first = token.split("/", 1)[0]
            if first in DEV_ONLY_MARKERS:
                problems.append(
                    f"{md.relative_to(artifact)} -> `{token}` (references dev-only path '{first}/')"
                )
                continue
            probes = [
                artifact / token,
                rel_md / token,
            ]
            if token.startswith(artifact.name + "/"):
                probes.append(artifact / token[len(artifact.name) + 1:])
            if not any(p.exists() for p in probes):
                problems.append(f"{md.relative_to(artifact)} -> `{token}` (no such file in artifact)")

    return problems


def test_product_is_self_contained():
    assert ARTIFACT.is_dir(), f"Artifact not found at {ARTIFACT}"
    problems = check_dir(ARTIFACT)
    assert not problems, "Product docs reference dev-only or missing paths:\n" + "\n".join(problems)


def test_product_layout_is_slim():
    """Mirror of skill-creator slimming: SKILL.md is the sole product entry doc
    at the artifact root (no product AGENTS.md/INSTALL.md) alongside README.md."""
    assert (ARTIFACT / "SKILL.md").is_file()
    assert (ARTIFACT / "README.md").is_file()
    assert not (ARTIFACT / "AGENTS.md").exists(), "product AGENTS.md must be removed (SKILL.md single entry)"
    assert not (ARTIFACT / "INSTALL.md").exists(), "product INSTALL.md must live at the workspace root, not ship"


def test_check_dir_flags_dev_only_command_ref(tmp_path):
    """The dev-only branch must stay reachable (regression: it was dead code)."""
    artifact = tmp_path / "art"
    (artifact / "references").mkdir(parents=True)
    (artifact / "SKILL.md").write_text(
        "# probe\n\nRun `python tests/foo.py` before shipping.\n", encoding="utf-8"
    )
    problems = check_dir(artifact)
    assert problems, "a dev-only command reference must be flagged"
    assert any("tests" in p for p in problems)
