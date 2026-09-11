"""Package a skill directory for a target LLM client (claude/opencode/codex/deepseek).

Part of the skill-creator skill (see SKILL.md stage 9). Packaging = adapt the
SKILL.md frontmatter to the client's schema, copy the whole skill tree (minus
caches), and run a per-client post-check so a package that would not load is
never emitted (transform + post-check discipline).

Frontmatter handling (the skill-side twist):
  - `allowed-tools` is the repo's canonical least-privilege whitelist (Claude tool
    names, e.g. `[Read, Grep, Glob, Bash]`):
      * claude keeps the native `allowed-tools` key, normalized to a
        comma-separated string (unknown names kept as-is).
      * opencode translates each Claude name back to an opencode tool-class key
        and merges it into a per-tool `permission` map (see below).
      * codex/deepseek pass it through unchanged (best-effort).
  - A legacy `tools` list whose entries are client labels (`claude`/`opencode`/...)
    is the repo's *supported-clients* metadata, NOT a tool whitelist. It is dropped
    for claude/opencode and left as-is for codex/deepseek. (Retained for backward
    compatibility; the repo no longer emits `tools` in skills.)
  - A legacy `tools` list of actual tool names IS a least-privilege whitelist
    (same treatment as `allowed-tools`):
      * opencode: the whitelist is merged into a per-tool `permission` map
        (whitelisted tool -> allow, other tool-class keys -> deny; an explicit
        `permission` entry always wins). A bare `permission` **string shorthand**
        is NOT kept as a global rule (that would widen/loosen) — the whitelist is
        materialized into per-tool rules instead.
      * claude: the whitelist becomes a comma-separated Claude tool-name string.
  - `allowed-tools` and a legacy `tools` whitelist are unioned when both appear.
  - codex/deepseek: no official skill frontmatter convention — YAML sanity check
    plus a generic name/description check, body passes through.

Usage:
    python scripts/package_skill.py <skill_dir> --client claude [--client opencode ...] \
        --out <dir> [--zip]

Output layout: <out>/<client>/<skill-name>/  (plus <out>/<client>/<skill-name>.zip
with --zip). Exit code 0 = all requested clients packaged; 1 = a package failed
(nothing partial for that client); 2 = bad arguments.
"""

import argparse
import io
import re
import shutil
import sys
import zipfile
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n?---(?:\s*\n|$)", re.DOTALL)
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

ALL_CLIENTS = ("claude", "opencode", "codex", "deepseek")
TRANSFORM_CLIENTS = ("claude", "opencode")
# Client labels that may appear in a skill's `tools:` field meaning "supported
# clients" (skill-creator convention) — never a tool whitelist.
CLIENT_LABELS = {"claude", "opencode", "codex", "deepseek"}

# opencode permission keys that gate plain tools. Mechanism keys are never
# rewritten automatically.
OPENCODE_TOOL_KEYS = (
    "read", "edit", "glob", "grep", "list", "bash", "task",
    "webfetch", "websearch", "todowrite", "question", "skill",
)
OPENCODE_TOOL_ALIASES = {"write": "edit", "patch": "edit"}
PERMISSION_ACTIONS = ("allow", "ask", "deny")

CLAUDE_TOOL_NAMES = {
    "read": "Read", "write": "Write", "edit": "Edit", "bash": "Bash",
    "glob": "Glob", "grep": "Grep", "webfetch": "WebFetch",
    "websearch": "WebSearch", "task": "Task", "todowrite": "TodoWrite",
}

# Reverse of CLAUDE_TOOL_NAMES (plus the tool classes with no forward mapping):
# maps an `allowed-tools` Claude tool name to an opencode tool-class key. Used to
# translate the skill's canonical whitelist into opencode per-tool permissions.
CLAUDE_TO_OPENCODE = {
    "read": "read", "write": "edit", "edit": "edit", "bash": "bash",
    "glob": "glob", "grep": "grep", "webfetch": "webfetch",
    "websearch": "websearch", "task": "task", "todowrite": "todowrite",
    "list": "list", "skill": "skill", "question": "question",
}

# Copied tree noise that must never be shipped.
_IGNORE_NAMES = {"__pycache__", ".git", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


class PackageError(ValueError):
    """Raised when a skill cannot be packaged for a target client."""


def configure_utf8_output() -> None:
    if sys.platform != "win32":
        return
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
            continue
        except Exception:
            pass
        buffer = getattr(stream, "buffer", None)
        if buffer is not None:
            setattr(sys, stream_name, io.TextIOWrapper(buffer, encoding="utf-8", errors="backslashreplace"))


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------

def split_frontmatter(content: str):
    """Return (fm_text or None, body). fm_text None = no well-formed block."""
    m = FRONTMATTER_RE.match(content)
    if not m:
        return None, content
    return m.group(1), content[m.end():]


def parse_frontmatter(fm_text: str, origin: str) -> dict:
    try:
        data = yaml.safe_load(fm_text)
    except yaml.YAMLError as e:
        raise PackageError(f"{origin}: invalid YAML frontmatter: {e}") from e
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise PackageError(f"{origin}: frontmatter must be a YAML mapping, got {type(data).__name__}")
    return data


def normalize_tools(value, origin: str):
    """Canonicalize `tools` to a lowercase name list; a bool map passes through."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return [p.strip().lower() for p in value.split(",") if p.strip()]
    if isinstance(value, list):
        names = []
        for item in value:
            if not isinstance(item, str):
                raise PackageError(f"{origin}: 'tools' entries must be tool names, got {item!r}")
            names.append(item.strip().lower())
        return names
    raise PackageError(f"{origin}: unsupported 'tools' form: {type(value).__name__}")


def _is_client_label_list(tools) -> bool:
    """True when a tools list is really the repo's supported-clients metadata."""
    return bool(tools) and all(isinstance(t, str) and t.lower() in CLIENT_LABELS for t in tools)


def normalize_allowed_tools(value, origin: str) -> list[str]:
    """Canonicalize `allowed-tools` to a list of Claude tool-name strings."""
    if isinstance(value, str):
        return [p.strip() for p in value.split(",") if p.strip()]
    if isinstance(value, list):
        names = []
        for item in value:
            if not isinstance(item, str):
                raise PackageError(f"{origin}: 'allowed-tools' entries must be tool names, got {item!r}")
            names.append(item.strip())
        return names
    raise PackageError(f"{origin}: unsupported 'allowed-tools' form: {type(value).__name__}")


def _allowed_tools_keys(names: list[str], origin: str):
    """Map Claude tool names -> (opencode tool-class keys, unknown names).

    A list that is really the repo's supported-clients metadata is rejected: a
    whitelist must never silently degrade into a client-label list.
    """
    lowered = [n.lower() for n in names]
    if lowered and all(n in CLIENT_LABELS for n in lowered):
        raise PackageError(
            f"{origin}: 'allowed-tools' listed client labels, not tool names: {names}"
        )
    keys, unknown = [], []
    for n in names:
        key = CLAUDE_TO_OPENCODE.get(n.lower())
        if key:
            keys.append(key)
        else:
            unknown.append(n.lower())
    return keys, unknown


def _canonical_claude_tool(name: str) -> str:
    """Normalize a tool name to its canonical Claude spelling (unknown kept)."""
    return CLAUDE_TOOL_NAMES.get(name.strip().lower(), name.strip())


def _check_permission(perm, origin: str) -> None:
    if isinstance(perm, str):
        if perm not in PERMISSION_ACTIONS:
            raise PackageError(f"{origin}: permission must be one of {'/'.join(PERMISSION_ACTIONS)}, got {perm!r}")
        return
    if isinstance(perm, dict):
        for key, value in perm.items():
            if isinstance(value, str):
                if value not in PERMISSION_ACTIONS:
                    raise PackageError(f"{origin}: permission.{key} must be allow/ask/deny, got {value!r}")
            elif isinstance(value, dict):
                for pattern, action in value.items():
                    if not isinstance(pattern, str) or not isinstance(action, str) or action not in PERMISSION_ACTIONS:
                        raise PackageError(
                            f"{origin}: permission.{key} pattern rules must map pattern -> allow/ask/deny"
                        )
            else:
                raise PackageError(
                    f"{origin}: permission.{key} must be a string action or a pattern map, "
                    f"got {type(value).__name__}"
                )
        return
    raise PackageError(f"{origin}: permission must be a string action or a map, got {type(perm).__name__}")


# ---------------------------------------------------------------------------
# Per-client post-checks (never emit a package the client would reject)
# ---------------------------------------------------------------------------

def _check_common(fm: dict, origin: str) -> None:
    name = fm.get("name")
    if not isinstance(name, str) or not NAME_RE.match(name):
        raise PackageError(f"{origin}: skill requires a kebab-case 'name' in frontmatter, got {name!r}")
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        raise PackageError(f"{origin}: skill requires a non-empty 'description' string")


def check_opencode_frontmatter(fm: dict, origin: str) -> None:
    _check_common(fm, origin)
    if "tools" in fm and not isinstance(fm["tools"], dict):
        raise PackageError(
            f"{origin}: opencode 'tools' must be a map of tool-name -> boolean "
            "(a whitelist is merged into `permission` automatically)"
        )
    if "permission" in fm and fm["permission"] is not None:
        _check_permission(fm["permission"], origin)


def check_claude_frontmatter(fm: dict, origin: str) -> None:
    _check_common(fm, origin)
    if "tools" in fm and (not isinstance(fm["tools"], str) or not fm["tools"].strip()):
        raise PackageError(
            f"{origin}: claude 'tools' must be a non-empty comma-separated string, got {fm['tools']!r}"
        )
    if "allowed-tools" in fm and (not isinstance(fm["allowed-tools"], str) or not fm["allowed-tools"].strip()):
        raise PackageError(
            f"{origin}: claude 'allowed-tools' must be a non-empty comma-separated string, "
            f"got {fm['allowed-tools']!r}"
        )


def check_generic_frontmatter(fm: dict, origin: str) -> None:
    _check_common(fm, origin)


# ---------------------------------------------------------------------------
# Transforms
# ---------------------------------------------------------------------------

def _merge_whitelist_into_permission(perm, allow_keys, unknown_keys) -> dict:
    """Materialize a normalized tool whitelist as per-tool permission rules.

    Whitelisted tool-class keys -> allow; every other tool-class key -> deny; an
    explicit entry in an existing `permission` map always wins. Unknown named keys
    (from `unknown_keys`) are added as allow. A bare permission string is
    intentionally NOT honored as a global rule: keeping e.g. `allow` globally would
    grant un-whitelisted tools and is exactly the privilege widening this merge
    prevents.
    """
    merged = dict(perm) if isinstance(perm, dict) else {}
    allow = set(allow_keys)
    for key in OPENCODE_TOOL_KEYS:
        if key not in merged:
            merged[key] = "allow" if key in allow else "deny"
    for key in unknown_keys:
        merged.setdefault(key, "allow")
    return merged


def _whitelist_note(merged: dict) -> str:
    denied = [k for k in OPENCODE_TOOL_KEYS if merged.get(k) == "deny"]
    return "opencode: whitelist -> permission ({allow} allow{denied})".format(
        allow=", ".join(
            sorted(t for t, v in merged.items() if v == "allow" and t in OPENCODE_TOOL_KEYS)
        ) or "-",
        denied=f"; deny {', '.join(denied)}" if denied else "",
    )


def adapt_for_opencode(fm: dict, notes: list, origin: str) -> None:
    allow_keys: list[str] = []
    unknown_keys: list[str] = []
    whitelist_seen = False

    if "allowed-tools" in fm:
        names = normalize_allowed_tools(fm.pop("allowed-tools"), origin)
        keys, unknown = _allowed_tools_keys(names, origin)
        allow_keys.extend(keys)
        unknown_keys.extend(unknown)
        whitelist_seen = True
        notes.append(
            "opencode: allowed-tools -> permission ({})".format(", ".join(sorted(keys)) or "-")
        )

    if "tools" in fm:
        tools = normalize_tools(fm.pop("tools"), origin)
        if isinstance(tools, dict):
            fm["tools"] = tools
            notes.append("opencode: kept legacy tools bool-map (deprecated; prefer permission)")
        elif _is_client_label_list(tools):
            notes.append(
                "opencode: 'tools' listed supported clients (metadata); dropped for this client"
            )
        else:
            whitelist_seen = True
            for tool in tools:
                key = OPENCODE_TOOL_ALIASES.get(tool, tool)
                if key in OPENCODE_TOOL_KEYS:
                    allow_keys.append(key)
                else:
                    unknown_keys.append(key)

    if whitelist_seen:
        perm = fm.get("permission")
        if isinstance(perm, str):
            notes.append(
                f"opencode: dropped global permission shorthand {perm!r} (would widen); "
                "whitelist merged into per-tool permission"
            )
        merged = _merge_whitelist_into_permission(perm, allow_keys, unknown_keys)
        fm["permission"] = merged
        notes.append(_whitelist_note(merged))
    check_opencode_frontmatter(fm, origin)


def adapt_for_claude(fm: dict, notes: list, origin: str) -> None:
    allowed_present = "allowed-tools" in fm
    mapped: list[str] = []
    dropped: list[str] = []

    if allowed_present:
        names = normalize_allowed_tools(fm.pop("allowed-tools"), origin)
        lowered = [n.lower() for n in names]
        if lowered and all(n in CLIENT_LABELS for n in lowered):
            raise PackageError(
                f"{origin}: 'allowed-tools' listed client labels, not tool names: {names}"
            )
        for n in names:
            canonical = _canonical_claude_tool(n)
            if canonical not in mapped:
                mapped.append(canonical)

    if "tools" in fm:
        tools = normalize_tools(fm["tools"], origin)
        if isinstance(tools, dict):
            tools = [str(k).strip().lower() for k, v in tools.items() if v is True]
        elif _is_client_label_list(tools):
            fm.pop("tools")
            notes.append("claude: 'tools' listed supported clients (metadata); dropped for this client")
            tools = None
        if tools is not None:
            for tool in tools:
                claude_name = CLAUDE_TOOL_NAMES.get(tool)
                if claude_name:
                    if claude_name not in mapped:
                        mapped.append(claude_name)
                else:
                    dropped.append(tool)
            if allowed_present:
                fm.pop("tools")  # folded into allowed-tools
            else:
                if not mapped:
                    raise PackageError(
                        f"{origin}: claude 'tools' whitelist {tools} maps to no Claude tool names; "
                        "refusing to omit 'tools' (absent tools = ALL tools in Claude)"
                    )
                fm["tools"] = ", ".join(mapped)
                note = f"claude: tools whitelist -> \"{fm['tools']}\""
                if dropped:
                    note += f" (no Claude equivalent, dropped: {', '.join(dropped)})"
                notes.append(note)

    if allowed_present:
        if not mapped:
            raise PackageError(
                f"{origin}: claude 'allowed-tools' maps to no Claude tool names "
                "(absent = ALL tools in Claude; refusing to emit an empty whitelist)"
            )
        fm["allowed-tools"] = ", ".join(mapped)
        note = f"claude: allowed-tools whitelist -> \"{fm['allowed-tools']}\""
        if dropped:
            note += f" (no Claude equivalent, dropped: {', '.join(dropped)})"
        notes.append(note)

    check_claude_frontmatter(fm, origin)


def adapt_skill_markdown(content: str, client: str, origin: str = "SKILL.md"):
    """Return (adapted_content, notes) for one target client.

    Raises PackageError on malformed frontmatter or a result the client schema
    would reject. codex/deepseek get a YAML + name/description sanity check and a
    best-effort passthrough.
    """
    client = (client or "").lower()
    if client not in ALL_CLIENTS:
        raise PackageError(f"unknown client: {client!r} (choose from {', '.join(ALL_CLIENTS)})")
    fm_text, body = split_frontmatter(content)
    if fm_text is None:
        raise PackageError(f"{origin}: no frontmatter block found (a skill requires name/description)")
    fm = parse_frontmatter(fm_text, origin)
    notes: list = []
    if client == "opencode":
        adapt_for_opencode(fm, notes, origin)
    elif client == "claude":
        adapt_for_claude(fm, notes, origin)
    else:
        check_generic_frontmatter(fm, origin)
        notes.append(f"{client}: no official skill frontmatter schema (best-effort); kept after YAML check")
    dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, default_flow_style=False, width=4096)
    return f"---\n{dumped}---\n{body}", notes


# ---------------------------------------------------------------------------
# Filesystem packaging
# ---------------------------------------------------------------------------

def _ignore(_dirpath, names):
    return [n for n in names if n in _IGNORE_NAMES or n.endswith((".pyc", ".pyo"))]


def _copy_tree(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst, ignore=_ignore, dirs_exist_ok=True)


def _make_zip(src_dir: Path, zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(src_dir.rglob("*")):
            if p.is_file():
                z.write(p, arcname=str(Path(src_dir.name) / p.relative_to(src_dir)))


def package_skill(skill_dir, clients, out_dir, make_zip: bool = False) -> list[Path]:
    """Package one skill dir for each client; return the list of written dirs."""
    skill_dir = Path(skill_dir)
    if not skill_dir.is_dir():
        raise PackageError(f"skill directory does not exist: {skill_dir}")
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise PackageError(f"no SKILL.md found in: {skill_dir}")
    content = skill_md.read_text(encoding="utf-8-sig")
    origin = f"{skill_dir.name}/SKILL.md"

    out_dir = Path(out_dir)
    if out_dir.exists() and not out_dir.is_dir():
        raise PackageError(f"--out is an existing file, expected a directory: {out_dir}")
    out_resolved = out_dir.resolve()
    if out_resolved == skill_dir.resolve() or skill_dir.resolve() in out_resolved.parents:
        raise PackageError(f"--out must not be inside the skill directory: {out_dir}")

    written = []
    for client in clients:
        adapted, notes = adapt_skill_markdown(content, client, origin=origin)
        target = out_dir / client / skill_dir.name
        if target.exists():
            shutil.rmtree(target)
        _copy_tree(skill_dir, target)
        (target / "SKILL.md").write_text(adapted, encoding="utf-8")
        for note in notes:
            print(f"ℹ️  [{client}] {note}")
        if make_zip:
            zip_path = target.with_suffix(".zip")
            _make_zip(target, zip_path)
            print(f"📦 {zip_path}")
        print(f"✅ [{client}] wrote {target}")
        written.append(target)
    return written


def main(argv: list[str] | None = None) -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(
        description="Package a skill directory for one or more LLM clients "
                    "(adapts SKILL.md frontmatter + copies the tree + post-checks)."
    )
    parser.add_argument("skill_dir", help="Skill directory containing SKILL.md")
    parser.add_argument("--client", action="append", required=True,
                        help=f"Target client (repeatable / comma-separated): {', '.join(ALL_CLIENTS)}")
    parser.add_argument("--out", required=True, help="Output directory (per-client subdirs are created)")
    parser.add_argument("--zip", action="store_true", help="Also write a .zip per client package")
    args = parser.parse_args(argv)

    clients = []
    for raw in args.client:
        for part in raw.split(","):
            part = part.strip().lower()
            if part:
                clients.append(part)
    unknown = [c for c in clients if c not in ALL_CLIENTS]
    if unknown:
        print(f"❌ unknown client(s): {', '.join(unknown)} (choose from {', '.join(ALL_CLIENTS)})", file=sys.stderr)
        return 2
    if not clients:
        print("❌ no client specified", file=sys.stderr)
        return 2

    try:
        package_skill(args.skill_dir, clients, args.out, make_zip=args.zip)
    except PackageError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
