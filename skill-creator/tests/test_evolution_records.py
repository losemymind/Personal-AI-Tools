"""Compacted history must remain navigable and preserve library evidence links."""

import re
from pathlib import Path

from conftest import ARTIFACT


EVOLUTIONS = ARTIFACT / "evolutions"
ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def check_target(source, href):
    path, _, anchor = href.partition("#")
    target = (source.parent / path).resolve() if path else source.resolve()
    assert target.is_relative_to(ARTIFACT.resolve()), (source, href)
    assert target.is_file(), (source, href)
    if anchor:
        assert f'id="{anchor}"' in target.read_text(encoding="utf-8"), (source, href)


def test_evolution_markdown_links_resolve():
    for source in EVOLUTIONS.glob("*.md"):
        for href in LINK.findall(source.read_text(encoding="utf-8")):
            if href.startswith(("https://", "http://")):
                continue
            check_target(source, href)


def test_record_map_has_unique_records_and_resolvable_destinations():
    source = EVOLUTIONS / "record-map.md"
    rows = re.findall(
        r"^\| (20\d\d-\d\d-\d\d-[^| ]+\.md) \| (.+) \|$",
        source.read_text(encoding="utf-8"), re.MULTILINE,
    )
    assert rows
    assert len({name for name, _ in rows}) == len(rows)
    for name, destinations in rows:
        assert not (EVOLUTIONS / name).exists(), f"duplicate original: {name}"
        links = LINK.findall(destinations)
        assert links, name
        for href in links:
            check_target(source, href)


def test_library_ledger_links_to_each_skill_evidence_section():
    source = ROOT / "skills" / "SKILL-RECORDS.md"
    rows = re.findall(r"^\| ([a-z0-9-]+) \| (.+) \|$",
                      source.read_text(encoding="utf-8"), re.MULTILINE)
    assert rows
    for name, columns in rows:
        evidence = columns.split("|")[-1].strip()
        links = LINK.findall(evidence)
        assert len(links) <= 1, (name, evidence)
        # New independent events may still use a dated filename before compaction.
        href = links[0] if links else "../skill-creator/skills/skill-creator/evolutions/" + evidence.strip("`")
        if "library-decisions.md" in href:
            assert href.endswith(f"#{name}"), (name, evidence)
        check_target(source, href)


def test_current_docs_have_no_dangling_evolution_references():
    docs = [ROOT / name for name in ("AGENTS.md", "README.md", "HANDOFF.md", "tools/README.md")]
    docs += list((ROOT / "skills").glob("*.md"))
    docs += list((ROOT / "skill-creator").glob("*.md"))
    docs += list(ARTIFACT.glob("*.md"))
    docs += list((ARTIFACT / "references").glob("*.md"))
    for source in docs:
        for path, anchor in re.findall(r"evolutions/([\w.-]+\.md)(?:#([\w-]+))?",
                                      source.read_text(encoding="utf-8")):
            check_target(EVOLUTIONS / "README.md", path + (f"#{anchor}" if anchor else ""))
