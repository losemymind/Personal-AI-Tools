"""Shared utilities for skill-creator scripts.

Two groups of helpers live here so the CLI scripts never drift apart:

1. **Section-header patterns** (`WHEN_TO_USE_PATTERNS` / `EXAMPLES_PATTERNS` /
   `LIMITATIONS_PATTERNS` + `has_*_section`) — the single source of truth used by
   both `validate_skills.py` and `compare_skills.py`.
2. **Frontmatter / trigger helpers** — `parse_frontmatter` (PyYAML, imported
   lazily so stdlib-only callers such as `run_eval.py` stay dependency-free),
   `parse_skill_md`, `eval_query`, and the CJK-aware `keyword_tokens` / `classify`
   heuristic that `run_eval.py` reuses.

Port of the parse utility from Anthropic's official anthropics/skills
skill-creator, generalized for the four-client SKILL.md format used by this
repository (frontmatter keys name/description are common across
claude/opencode/codex/deepseek).
"""

import json
import os
import re
import signal
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Section-header patterns (single source of truth)
# ---------------------------------------------------------------------------
# English + Chinese variants accepted across the ecosystem. Keeping them in one
# module is why the validator and the comparison scorer can never disagree about
# whether a skill "has" a section.

WHEN_TO_USE_PATTERNS = [
    re.compile(r"^##\s+When\s+to\s+Use", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+When\s+to\s+Use\s+This\s+Skill", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+Use\s+this\s+skill\s+when", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+When\s+to\s+activate\s+this\s+skill", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+何时使用(?:此|这|本)*技能", re.MULTILINE),
]

EXAMPLES_PATTERNS = [
    re.compile(r"^##\s+Examples?", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+示例", re.MULTILINE),
]

LIMITATIONS_PATTERNS = [
    re.compile(r"^##\s+Limitations?", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+限制", re.MULTILINE),
]


def has_when_to_use_section(content: str) -> bool:
    return any(pattern.search(content) for pattern in WHEN_TO_USE_PATTERNS)


def has_examples_section(content: str) -> bool:
    return any(pattern.search(content) for pattern in EXAMPLES_PATTERNS)


def has_limitations_section(content: str) -> bool:
    return any(pattern.search(content) for pattern in LIMITATIONS_PATTERNS)


# ---------------------------------------------------------------------------
# Eval-item helper
# ---------------------------------------------------------------------------


def eval_query(item: dict) -> str:
    """Return an eval item's prompt text.

    Canonical key is ``query`` (see references/benchmark-schema.md). Legacy eval
    sets written from an older template may use ``prompt``; accept it as a
    fallback so those files keep working instead of raising KeyError.
    """
    return item.get("query") or item.get("prompt") or ""


def load_eval_set(path) -> list[dict]:
    """Load and shape-validate an evals.json, raising ValueError with a clear message.

    Guards the CLI tools against the common mistakes that otherwise surface as raw
    tracebacks: a missing path, a directory, invalid JSON, or a JSON value that is
    not an array of objects (e.g. a bare dict without `evals`, or an array of ints).
    """
    p = Path(path)
    if not p.exists():
        raise ValueError(f"eval set not found: {p}")
    if p.is_dir():
        raise ValueError(f"eval set is a directory, not a file: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"eval set is not valid JSON ({p}): {e}") from e
    items = data.get("evals", data) if isinstance(data, dict) else data
    if not isinstance(items, list) or not all(isinstance(i, dict) for i in items):
        raise ValueError(
            f"eval set must be an array of objects, or an object with an 'evals' array ({p})"
        )
    for idx, item in enumerate(items):
        q = item.get("query") or item.get("prompt")
        if not isinstance(q, str) or not q.strip():
            raise ValueError(
                f"eval set item {idx} must have a non-empty string 'query' ({p})"
            )
        # A missing should_trigger would be silently treated as False, silently
        # mislabelling the item as a negative and polluting precision/recall.
        if not isinstance(item.get("should_trigger"), bool):
            raise ValueError(
                f"eval set item {idx} must have a boolean 'should_trigger' ({p})"
            )
    return items


# ---------------------------------------------------------------------------
# Frontmatter parsing (PyYAML imported lazily)
# ---------------------------------------------------------------------------


def _normalize_yaml_value(value):
    from collections.abc import Mapping
    from datetime import date, datetime

    if isinstance(value, Mapping):
        return {key: _normalize_yaml_value(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_normalize_yaml_value(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def parse_frontmatter(content: str):
    """Parse a SKILL.md frontmatter block with PyYAML.

    Returns ``(metadata, error_messages)``. ``metadata`` is a plain dict on
    success or ``None`` on failure. PyYAML is imported lazily so stdlib-only
    callers (e.g. run_eval.py) never require the dependency.
    """
    import yaml

    fm_match = re.search(r"^---\s*\n(.*?)\n?---(?:\s*\n|$)", content, re.DOTALL)
    if not fm_match:
        return None, ["Missing or malformed YAML frontmatter"]

    fm_errors: list[str] = []
    try:
        metadata = yaml.safe_load(fm_match.group(1)) or {}
        metadata = _normalize_yaml_value(metadata)
        if not isinstance(metadata, dict):
            return None, ["Frontmatter must be a YAML mapping/object."]

        if "description" in metadata:
            desc = metadata["description"]
            if not desc or (isinstance(desc, str) and not desc.strip()):
                fm_errors.append("description field is empty or whitespace only.")
            elif desc == "|":
                fm_errors.append(
                    "description contains only the YAML block indicator '|', "
                    "likely due to a parsing regression."
                )

        return dict(metadata), fm_errors
    except yaml.YAMLError as e:
        return None, [f"YAML Syntax Error: {e}"]


# ---------------------------------------------------------------------------
# Line-based skill parser (no PyYAML; used by run_eval / run_loop)
# ---------------------------------------------------------------------------


def parse_skill_md(skill_path: Path) -> tuple[str, str, str]:
    """Parse a skill's SKILL.md, returning (name, description, full_content).

    Handles single-line and YAML-block-scalar descriptions (> / | / >- / |-).
    """
    content = (skill_path / "SKILL.md").read_text(encoding="utf-8-sig")
    lines = content.split("\n")

    if not lines or lines[0].strip() != "---":
        raise ValueError("SKILL.md missing frontmatter (no opening ---)")

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        raise ValueError("SKILL.md missing frontmatter (no closing ---)")

    name = ""
    description = ""
    fm_lines = lines[1:end_idx]
    i = 0
    while i < len(fm_lines):
        line = fm_lines[i]
        if line.startswith("name:"):
            name = line[len("name:"):].strip().strip('"').strip("'")
        elif line.startswith("description:"):
            value = line[len("description:"):].strip()
            if value in (">", "|", ">-", "|-"):
                continuation_lines: list[str] = []
                i += 1
                while i < len(fm_lines) and (
                    fm_lines[i].startswith("  ") or fm_lines[i].startswith("\t")
                ):
                    continuation_lines.append(fm_lines[i].strip())
                    i += 1
                description = " ".join(continuation_lines)
                continue
            description = value.strip().strip('"').strip("'")
        i += 1

    return name, description, content


# ---------------------------------------------------------------------------
# CJK-aware trigger heuristic (deterministic, no external CLI)
# ---------------------------------------------------------------------------
#
# The heuristic is a keyword-overlap proxy, not an authoritative trigger test
# (real client runs are authoritative — see SKILL.md stage 7). CJK text has no
# spaces, so a word-based tokenizer collapses an entire Chinese phrase into one
# token and overlap can never reach the threshold. We therefore emit CJK
# bigrams (and latin words) as the comparable tokens.

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")

_TRIGGER_STOP = {
    "skill", "使用", "技能", "when", "use", "this", "user", "should", "the", "a",
}


def keyword_tokens(text: str) -> list[str]:
    """Tokenize for trigger overlap: latin words + CJK unigrams/bigrams.

    CJK is split into bigrams so Chinese phrases share tokens with a description
    (e.g. 总结我的改动 vs a description containing 总结/改动). Bigrams are what
    `classify` compares; unigrams are emitted for callers that want them.
    """
    text = text.lower()
    tokens = re.findall(r"[a-z0-9][a-z0-9-]*", text)
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        if len(run) == 1:
            tokens.append(run)
            continue
        tokens.extend(run)  # unigrams
        tokens.extend(run[i:i + 2] for i in range(len(run) - 1))  # bigrams
    return tokens


def classify(prompt: str, description: str) -> bool:
    """Deterministic heuristic: does the prompt share >=2 distinct meaningful tokens?

    Meaningful tokens are latin words (len >= 2) and CJK bigrams (len == 2);
    CJK unigrams are intentionally excluded to avoid single-common-character
    false positives. Tokens are compared as *sets*: a term repeated in the
    description (e.g. 创建 appearing three times) is one shared token, not three —
    counting occurrences would let any single-word overlap cross the threshold.
    """
    tokens = keyword_tokens(description)
    meaningful = {t for t in tokens if t not in _TRIGGER_STOP and len(t) >= 2}
    prompt_tokens = set(keyword_tokens(prompt))
    return len(meaningful & prompt_tokens) >= 2


# ---------------------------------------------------------------------------
# Security scanning (single source of truth for validate_skills / compare_skills)
# ---------------------------------------------------------------------------
#
# An allowlist marker must be a *local* exception, never a file-global
# kill-switch: a skill that merely mentions `security-allowlist` in prose must not
# thereby disable scanning of a dangerous command elsewhere in the file. A match
# is excused only when the marker sits on the same line, or annotates the
# immediately following fenced block.
#
# Dangerous remote-exec pipes are only flagged inside fenced code blocks: prose
# and inline backticks describing the pattern (e.g. a security guide) are not
# runnable command examples. Inline secrets are scanned everywhere (a leaked
# credential is harmful wherever it appears).

ALLOWLIST_MARKER_RE = re.compile(r"<!--\s*security-allowlist", re.IGNORECASE)
# A remote download piped into a shell executes arbitrary code. Rather than a
# brittle regex for the right-hand side, capture the pipeline and validate the
# right side token-wise (see `_segment_runs_shell`): that catches wrappers
# (`| sudo -u root bash`, `| env bash`, `| /bin/bash`, `| busybox sh`) and
# line-continuations while NOT falsely flagging `| grep bash`.
_PIPE_CHAINS = [
    # (pipeline regex, set of shell/exec names considered dangerous on the right)
    # `iex`/`invoke-expression` are included here because in PowerShell `curl`
    # and `wget` are aliases of Invoke-WebRequest, so `curl x | iex` is a real
    # download-and-execute cradle (kept in sync with the agent-side scanner).
    (re.compile(r"\b(?:curl|wget)\b[^\n]*?\|[^\n]*", re.IGNORECASE),
     {"bash", "sh", "zsh", "ksh", "dash", "ash", "fish",
      "powershell", "pwsh", "cmd", "iex", "invoke-expression"}),
    # `irm`=Invoke-RestMethod, `iwr`=Invoke-WebRequest (both pipe into iex).
    (re.compile(r"\b(?:irm|iwr|Invoke-WebRequest|Invoke-RestMethod)\b[^\n]*?\|[^\n]*",
                re.IGNORECASE),
     {"iex", "invoke-expression"}),
]
# Tokens that may precede the actual shell command and are skipped while walking
# a pipe segment left-to-right.
_SHELL_LAUNCHERS = {
    "sudo", "doas", "env", "nice", "nohup", "timeout", "busybox",
    "command", "exec", "setsid", "stdbuf", "xargs",
}
# Obvious inline credentials (kept deliberately narrow to avoid false positives)
SECRET_PATTERNS = [
    # GitHub tokens: ghp_/gho_/ghu_/ghs_/ghr_ (classic) + github_pat_ (fine-grained),
    # Slack tokens, and the generic sk- API-key prefix.
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[oprsu]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # Google API key.
    re.compile(r"\bAIza[0-9A-Za-z_\-]{35}"),
    # PEM private-key header (any of the common algorithm variants).
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
]
# CommonMark fence opener: up to 3 spaces of indent, any blockquote prefix, then
# >=3 backticks or tildes. Blockquote fences (`> ``` `) are real fenced blocks;
# missing them let a dangerous command there escape the (fenced-only) scan.
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(?:> ?)*(`{3,}|~{3,})")


def fenced_ranges(content: str, closed_only: bool = False) -> list[tuple[int, int]]:
    """Character spans of Markdown fenced code blocks (CommonMark-aware).

    Handles `~~~` and ```` ```` openers, matching closers of at least the opener's
    run length, indentation up to 3 spaces, and an unterminated opener extending
    to end-of-file. A naive ``\\`\\`\\`.*?\\`\\`\\``` regex misses all of these, which
    would let a dangerous command in such a fence escape the security scan.

    `closed_only=True` excludes unterminated openers. Security scanning wants the
    strict (unterminated = to EOF) view; path-reference checks use closed_only so a
    stray ``` cannot silently hide every later reference.
    """
    lines = content.split("\n")
    offsets: list[int] = []
    pos = 0
    for ln in lines:
        offsets.append(pos)
        pos += len(ln) + 1
    ranges: list[tuple[int, int]] = []
    i = 0
    n = len(lines)
    while i < n:
        m = _FENCE_OPEN_RE.match(lines[i])
        if not m:
            i += 1
            continue
        fence = m.group(1)
        char, length = fence[0], len(fence)
        closer_re = re.compile(
            r"^ {0,3}(?:> ?)*" + re.escape(char) + "{" + str(length) + r",}\s*$"
        )
        start = offsets[i]
        j = i + 1
        end = None
        while j < n:
            if closer_re.match(lines[j]):
                end = offsets[j] + len(lines[j])
                j += 1
                break
            j += 1
        if end is None:  # unterminated fence runs to EOF
            end = offsets[-1] + len(lines[-1]) if lines else start
            j = n
            if closed_only:
                i = j
                continue
        ranges.append((start, end))
        i = j
    return ranges


def _in_any(pos: int, ranges: list[tuple[int, int]]) -> bool:
    return any(s <= pos < e for s, e in ranges)


def security_allowlist_ranges(content: str) -> list[tuple[int, int]]:
    """Character ranges excused by `<!-- security-allowlist -->` annotations.

    A marker excuses (a) anything on its own line and (b) the fenced code block
    it annotates when it sits on the fence-opener line or the line immediately
    before it — a scoped, auditable exception.
    """
    lines = content.split("\n")
    offsets: list[int] = []
    pos = 0
    for ln in lines:
        offsets.append(pos)
        pos += len(ln) + 1
    fences = fenced_ranges(content)
    fence_starts = {s for s, _ in fences}
    _, indents = _line_indent_map(content)
    excused: list[tuple[int, int]] = []
    for i, ln in enumerate(lines):
        if not ALLOWLIST_MARKER_RE.search(ln):
            continue
        excused.append((offsets[i], offsets[i] + len(ln)))
        annotated_fence = False
        for j in (i, i + 1):
            if j < len(lines) and offsets[j] in fence_starts:
                for s, e in fences:
                    if s == offsets[j]:
                        excused.append((s, e))
                        break
                annotated_fence = True
                break
        # The marker also excuses the immediately following indented (>=4-column)
        # code block. The validator's own message promises "annotate its block/line";
        # honoring only fenced blocks left an indented `curl … | bash` example
        # impossible to excuse even when the author annotated it.
        if not annotated_fence:
            j = i + 1
            while j < len(lines) and (indents[j] >= 4 or not lines[j].strip()):
                excused.append((offsets[j], offsets[j] + len(lines[j])))
                j += 1
    return excused


def _line_indent_map(content: str) -> tuple[list[int], list[int]]:
    """Return (line_start_offsets, leading_indent_width_per_line).

    Indent is measured in display columns (a tab advances to the next multiple of
    4), matching CommonMark's 4-column indented-code rule. Counting a tab as one
    column let a tab-indented `curl | bash` escape the code-context check.
    """
    starts: list[int] = []
    indents: list[int] = []
    pos = 0
    for ln in content.split("\n"):
        starts.append(pos)
        col = 0
        for ch in ln:
            if ch == " ":
                col += 1
            elif ch == "\t":
                col += 4 - (col % 4)
            else:
                break
        indents.append(col)
        pos += len(ln) + 1
    return starts, indents


def _line_index(pos: int, starts: list[int]) -> int:
    import bisect
    return max(0, bisect.bisect_right(starts, pos) - 1)


def _normalize_token(tok: str) -> str:
    """Strip shell quoting/grouping wrappers from a command token.

    `"bash"` (quoted), `(bash)` (subshell), and `$(bash)` (command substitution)
    all invoke bash; a plain token comparison would miss them. Only balanced
    leading `(` / `$(`, trailing `)`, and surrounding quotes are peeled.
    """
    t = tok.strip("\"'")
    for _ in range(3):
        if t.startswith("$("):
            t = t[2:]
        elif t.startswith("("):
            t = t[1:]
        if t.endswith(")"):
            t = t[:-1]
    return t.strip("\"'")


def _segment_runs_shell(segment: str, shells: set[str]) -> bool:
    """True if a pipe segment invokes a shell/exec binary.

    Token-wise so wrappers and their flags are covered: `sudo -u root bash`,
    `env bash`, `/bin/bash`, `busybox sh`, `timeout 30 bash` all match, while a
    benign `grep bash` (first token is a non-launcher) does not.
    """
    tokens = [_normalize_token(t) for t in segment.split()]
    i = 0
    while i < len(tokens):
        base = tokens[i].rsplit("/", 1)[-1].lower()
        if base in shells:
            return True
        if base in _SHELL_LAUNCHERS:
            # `command -v bash` only queries a path; it does not run bash.
            if base == "command" and i + 1 < len(tokens) and tokens[i + 1] in ("-v", "-V"):
                return False
            i += 1
            continue
        if tokens[i].startswith("-"):
            # A flag may take a value (`-u root`): skip it when the next token is
            # an ordinary word rather than another flag or the shell itself.
            i += 1
            if i < len(tokens):
                nxt = tokens[i].rsplit("/", 1)[-1].lower()
                if not tokens[i].startswith("-") and nxt not in shells:
                    i += 1
            continue
        if "=" in tokens[i] or tokens[i].isdigit():
            i += 1
            continue
        return False
    return False


def _chain_runs_shell(chain: str, shells: set[str]) -> bool:
    """True if any pipe/&&/; segment of a pipeline starts a shell invocation."""
    return any(_segment_runs_shell(seg, shells) for seg in re.split(r"[;&|]", chain))


def find_dangerous_pipes(content: str, fenced_only: bool = True) -> list:
    """Return dangerous remote-exec pipeline matches.

    Analysis runs on a copy with shell line-continuations (`curl x \\<newline> |
    bash`) joined, so the pipe is not missed by a per-line regex. When
    `fenced_only`, a match counts when it lies inside a fenced code block or on
    an indented (>=4 space / tab) code line — the two CommonMark code shapes —
    and is not excused by a local `<!-- security-allowlist -->` marker.
    """
    normalized = re.sub(r"\\[ \t]*\r?\n", " ", content)
    # A shell also allows a trailing pipe at end-of-line with the command on the
    # next line (`curl x |` <newline> `bash`); join that so the chain matches.
    normalized = re.sub(r"\|[ \t]*\r?\n[ \t]*", "| ", normalized)
    # PowerShell uses a trailing backtick and CMD a trailing caret as their line
    # continuations; without joining them `curl x ` + newline + `| iex` splits
    # the pipeline across lines and escapes a per-line regex. Only join when the
    # pipe actually follows, so a bare backtick at end-of-line (Markdown inline
    # code, or a ``` fence opener) is never swallowed.
    normalized = re.sub(r"(?<!`)`(?!`)[ \t]*\r?\n[ \t]*(?=\|)", " ", normalized)
    normalized = re.sub(r"\^[ \t]*\r?\n[ \t]*(?=\|)", " ", normalized)
    excused = security_allowlist_ranges(normalized)
    fences = fenced_ranges(normalized)
    starts, indents = _line_indent_map(normalized)
    found = []
    for pattern, shells in _PIPE_CHAINS:
        for m in pattern.finditer(normalized):
            if fenced_only:
                on_code_line = indents[_line_index(m.start(), starts)] >= 4
                if not on_code_line and not _in_any(m.start(), fences):
                    continue
            if _in_any(m.start(), excused):
                continue
            if not _chain_runs_shell(m.group(0), shells):
                continue
            found.append(m)
    return found


def find_inline_secrets(content: str) -> list:
    """Return inline-secret matches not excused by a local allowlist marker."""
    excused = security_allowlist_ranges(content)
    found = []
    for pattern in SECRET_PATTERNS:
        for m in pattern.finditer(content):
            if _in_any(m.start(), excused):
                continue
            found.append(m)
    return found


# ---------------------------------------------------------------------------
# Client process runner (shared by run_eval / run_scenario / run_loop)
# ---------------------------------------------------------------------------


def _kill_process_tree(proc: subprocess.Popen) -> None:
    """Kill a client process and all of its descendants.

    `subprocess.run(timeout=)` kills only the direct child; a blocked client can
    leave grandchildren alive (observed: an `opencode run` descendant outliving a
    timed-out parent, burning CPU). Use the OS tree-kill primitive instead.
    """
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
            capture_output=True, text=True,
        )
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            proc.kill()


def run_client(cmd: list[str], *, timeout: int, cwd=None, env=None,
               input_text: str | None = None) -> tuple[int, str, str]:
    """Run a client CLI with a timeout, killing the whole process tree on timeout.

    Returns `(returncode, stdout, stderr)`. On timeout raises
    `subprocess.TimeoutExpired` *after* killing the tree, carrying whatever the
    process had already emitted in `.stdout`/`.stderr` (so callers can preserve a
    trigger signal that fired before the client got stuck).
    """
    popen_kwargs: dict = {}
    if os.name == "nt":
        popen_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        popen_kwargs["start_new_session"] = True
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        cwd=cwd, env=env, **popen_kwargs,
    )
    try:
        out, err = proc.communicate(input=input_text, timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_process_tree(proc)
        try:
            out, err = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            out, err = "", ""
        raise subprocess.TimeoutExpired(cmd, timeout, output=out, stderr=err)
    return proc.returncode, out or "", err or ""

