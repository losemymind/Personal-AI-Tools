"""Tests for search_index.py query construction.

Covers the CJK fallback (FTS5 unicode61 cannot tokenize Chinese, so CJK
queries must route to substring LIKE matching) and the unchanged ASCII/FTS5
path.
"""

import importlib.util
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SEARCH_INDEX = REPO_ROOT / "skills" / "skill-creator" / "scripts" / "search_index.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("search_index", SEARCH_INDEX)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _make_args(query="", **kwargs):
    defaults = dict(
        category=None,
        risk=None,
        tool=None,
        source=None,
        only_scripts=False,
        only_references=False,
        limit=10,
    )
    defaults.update(kwargs)
    return types.SimpleNamespace(query=query, **defaults)


def test_ascii_query_uses_fts5_match():
    mod = _load_module()
    sql, params = mod.build_query(_make_args("code review"))
    assert "skills_fts MATCH ?" in sql
    assert "LIKE ?" not in sql
    # Each whitespace token is quoted as a literal FTS5 string so punctuation
    # (c++, parens, quotes) cannot inject FTS5 syntax and crash the MATCH.
    assert params[0] == '"code" "review"'


def test_fts5_special_chars_are_quoted_literally():
    mod = _load_module()
    for q in ("c++", "(", '"', "foo:bar", "NEAR("):
        sql, params = mod.build_query(_make_args(q))
        assert "skills_fts MATCH ?" in sql
        # every quote in the payload is doubled, never left as raw syntax
        assert params[0].startswith('"') and params[0].endswith('"')


def test_cjk_query_falls_back_to_like():
    mod = _load_module()
    sql, params = mod.build_query(_make_args("病史"))
    assert "skills_fts MATCH" not in sql
    assert "LIKE ?" in sql
    # one token x four text columns + trailing LIMIT param
    assert len(params) == 5


def test_cjk_multiword_query_is_and_joined():
    mod = _load_module()
    sql, params = mod.build_query(_make_args("综合 分析"))
    assert " AND " in sql
    # two tokens x four text columns + trailing LIMIT param
    assert len(params) == 9
    assert params.count("%综合%") == 4
    assert params.count("%分析%") == 4


def test_cjk_query_escapes_like_wildcards():
    mod = _load_module()
    sql, params = mod.build_query(_make_args("100% 纯_净"))
    assert params.count("%100\\%%") == 4
    assert params.count("%纯\\_净%") == 4
    assert "ESCAPE" in sql


def test_source_aliases_cover_all_index_sources():
    mod = _load_module()
    assert mod.SOURCE_ALIASES["aas"] == "sickn33/agentic-awesome-skills"
    assert mod.SOURCE_ALIASES["addy"] == "addyosmani/agent-skills"
    assert mod.SOURCE_ALIASES["anthropics"] == "anthropics/skills"
    assert mod.SOURCE_ALIASES["composiohq"] == "ComposioHQ/awesome-claude-skills"
