"""Security scanning for agent-creator release gates (self-contained).

Sweeps AGENT.md and the text/code files bundled with an agent directory for
inline credentials and dangerous remote-execution pipelines. Mirrors the
security discipline already enforced for skills by skill-creator's validator,
adapted to this skill's self-contained layout (no shared utils module).

Design (same guarantees as the skill-side scanner):
  - A `<!-- security-allowlist -->` marker is a LOCAL exception: it excuses only
    its own line, the fenced block it annotates, or the indented (>=4-column)
    code block immediately after it — never a whole-file kill-switch.
  - Dangerous remote-exec pipes are only flagged inside code context (fenced
    blocks or indented code lines), so prose describing the pattern is not a
    runnable command. Inline secrets are scanned everywhere.
  - The right-hand side of a pipe is validated token-wise, so wrappers
    (`sudo -u root bash`, `env bash`, `/bin/bash`) are caught while `grep bash`
    is not.
"""

import os
import re

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

ALLOWLIST_MARKER_RE = re.compile(r"<!--\s*security-allowlist", re.IGNORECASE)

# Obvious inline credentials (deliberately narrow to avoid false positives).
SECRET_PATTERNS = [
    re.compile(
        r"\b(?:sk-[A-Za-z0-9_-]{16,}|gh[oprsu]_[A-Za-z0-9]{20,}"
        r"|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})"
    ),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"),
]

# Tokens that may precede the actual shell command while walking a pipe segment.
_SHELL_LAUNCHERS = {
    "sudo", "doas", "env", "nice", "nohup", "timeout", "busybox",
    "command", "exec", "setsid", "stdbuf", "xargs",
}

# (pipeline regex, shell/exec names considered dangerous on the right-hand side)
# `iex`/`invoke-expression` are included on the curl/wget chain because in
# PowerShell `curl`/`wget` are aliases of Invoke-WebRequest, so `curl x | iex`
# is a real download-and-execute cradle, not a cross-shell oddity.
_PIPE_CHAINS = [
    (
        re.compile(r"\b(?:curl|wget)\b[^\n]*?\|[^\n]*", re.IGNORECASE),
        {
            "bash", "sh", "zsh", "ksh", "dash", "ash", "fish", "powershell",
            "pwsh", "cmd", "iex", "invoke-expression",
        },
    ),
    (
        re.compile(r"\b(?:irm|iwr|Invoke-WebRequest|Invoke-RestMethod)\b[^\n]*?\|[^\n]*", re.IGNORECASE),
        {"iex", "invoke-expression"},
    ),
]

# CommonMark fence opener: up to 3 spaces indent, any blockquote prefix, then
# >=3 backticks or tildes.
_FENCE_OPEN_RE = re.compile(r"^ {0,3}(?:> ?)*(`{3,}|~{3,})")

# Text/code extensions swept for secrets/pipelines across the agent dir. Kept in
# sync with the resource extensions the validator recognizes elsewhere.
TEXT_SCAN_EXTS = {
    ".md", ".py", ".sh", ".json", ".yaml", ".yml", ".txt", ".toml", ".cfg",
    ".ini", ".conf", ".env", ".ps1", ".psm1", ".psd1", ".bat", ".cmd",
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".rb", ".go", ".java",
    ".rs", ".php", ".vue", ".svelte",
}


# Known credential-bearing files that have no (or a misleading) extension.
# ``os.path.splitext`` cannot classify these, yet they are exactly where a
# pasted key/id would land, so they are scanned by exact name. Includes
# extensionless files that commonly live inside hidden dirs (``.aws/credentials``)
# and shell rc files that frequently export tokens.
SENSITIVE_DOTFILES = {
    ".netrc", ".git-credentials", ".npmrc", ".pgpass", ".htpasswd",
    ".dockercfg", ".envrc", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519",
    ".pypirc", ".netrc.gpg", "credentials", ".gitconfig", ".bashrc",
    ".zshrc", ".profile", ".bash_profile", ".secrets",
}


def is_scannable_text(filename: str) -> bool:
    """True for a text/code file that should be swept.

    ``os.path.splitext`` mishandles dotfiles: bare ``.env`` -> ``('.env','')``
    and ``.env.local`` -> ``('.env','.local')``, so the most common dotenv names
    would be skipped. Treat any ``.env``/``.env.*`` name as scannable, and also
    sweep known credential dotfiles that carry no usable extension.
    """
    low = filename.lower()
    if low == ".env" or low.startswith(".env."):
        return True
    if low in SENSITIVE_DOTFILES:
        return True
    return os.path.splitext(filename)[1].lower() in TEXT_SCAN_EXTS


# ---------------------------------------------------------------------------
# Fenced / indented code context
# ---------------------------------------------------------------------------

def fenced_ranges(content: str, closed_only: bool = False) -> list[tuple[int, int]]:
    """Character spans of Markdown fenced code blocks (CommonMark-aware).

    Handles ``~~~`` and ```` ``` ```` openers, matching closers of at least the
    opener's run length, indentation up to 3 spaces, and an unterminated opener
    extending to end-of-file. ``closed_only=True`` excludes unterminated openers
    (used by path-reference checks so a stray fence cannot hide later refs).
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


def _line_indent_map(content: str) -> tuple[list[int], list[int]]:
    """Return (line_start_offsets, leading_indent_width_per_line).

    Indent is measured in display columns (a tab advances to the next multiple
    of 4), matching CommonMark's 4-column indented-code rule.
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


def security_allowlist_ranges(content: str) -> list[tuple[int, int]]:
    """Character ranges excused by ``<!-- security-allowlist -->`` annotations."""
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
        if not annotated_fence:
            j = i + 1
            while j < len(lines) and (indents[j] >= 4 or not lines[j].strip()):
                excused.append((offsets[j], offsets[j] + len(lines[j])))
                j += 1
    return excused


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
    """True if a pipe segment invokes a shell/exec binary (token-wise)."""
    tokens = [_normalize_token(t) for t in segment.split()]
    i = 0
    while i < len(tokens):
        base = tokens[i].rsplit("/", 1)[-1].lower()
        if base in shells:
            return True
        if base in _SHELL_LAUNCHERS:
            if base == "command" and i + 1 < len(tokens) and tokens[i + 1] in ("-v", "-V"):
                return False
            i += 1
            continue
        if tokens[i].startswith("-"):
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
    return any(_segment_runs_shell(seg, shells) for seg in re.split(r"[;&|]", chain))


def find_dangerous_pipes(content: str, fenced_only: bool = True) -> list:
    """Return dangerous remote-exec pipeline matches.

    Line-continuations and trailing pipes are joined first so a multi-line
    pipeline is not missed. With ``fenced_only`` a match counts only inside a
    fenced block or on an indented (>=4-column) code line, and never in an
    allowlisted range.
    """
    normalized = re.sub(r"\\[ \t]*\r?\n", " ", content)
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
