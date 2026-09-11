"""Package an agent directory for a target LLM client (claude/opencode/codex/deepseek).

Part of the agent-creator skill (see SKILL.md stage 7). Packaging = adapt the
AGENT.md frontmatter to the client's schema, copy the whole agent tree (minus
caches), and run a per-client post-check so a package that would not load is
never emitted (transform + post-check discipline), reusing the schema
checks/constants of `adapt_agent.py`.

Frontmatter handling (agent-specific):
  - A `tools` list whose entries are client labels (`claude`/`opencode`/...) is
    "supported-clients" metadata, NOT a tool whitelist. It is dropped for
    claude/opencode and left as-is for codex/deepseek (best-effort passthrough).
  - A `tools` list of actual tool names IS a least-privilege whitelist:
      * opencode: the whitelist is merged into a per-tool `permission` map
        (whitelisted tool -> allow, other tool-class keys -> deny; an explicit
        `permission` entry always wins). A bare `permission` **string shorthand**
        is NOT kept as a global rule (that would widen/loosen) — the whitelist is
        materialized into per-tool rules instead. This fixes the privilege
        widening in `adapt_agent.py`, where a string shorthand kept the whitelist
        from being merged at all.
      * claude: the whitelist becomes a comma-separated Claude tool-name string;
        a provider-prefixed `model` is reduced to a claude alias (sonnet/opus/
        haiku/inherit) or dropped when unmappable.
  - codex/deepseek: no official agent frontmatter convention — YAML sanity check
    plus a generic name/description check, body passes through.

Usage:
    python scripts/package_agent.py <agent_dir | AGENT.md> \
        --client claude [--client opencode ...] --out <dir> [--zip]

Output layout: <out>/<client>/<agent-name>/  (plus <out>/<client>/<agent-name>.zip
with --zip). <agent-name> = frontmatter `name` when it is valid kebab-case, else
the input directory/file stem. Exit code 0 = all requested clients packaged;
1 = a package failed (nothing partial for that client); 2 = bad arguments.
"""

import argparse
import io
import re
import shutil
import sys
import zipfile
from pathlib import Path

import yaml

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import adapt_agent as _adapt  # noqa: E402  (shared constants + schema post-checks)

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n?---(?:\s*\n|$)", re.DOTALL)
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

ALL_CLIENTS = _adapt.ALL_CLIENTS
TRANSFORM_CLIENTS = _adapt.TRANSFORM_CLIENTS
# Client labels that may appear in an agent's `tools:` field meaning "supported
# clients" — never a tool whitelist.
CLIENT_LABELS = set(ALL_CLIENTS)

# Copied tree noise that must never be shipped.
_IGNORE_NAMES = {"__pycache__", ".git", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


class PackageError(ValueError):
    """Raised when an agent cannot be packaged for a target client."""


def configure_utf8_output() -> None:
    _adapt.configure_utf8_output()


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


def _translate_schema_check(fn, fm: dict, origin: str) -> None:
    try:
        fn(fm, origin)
    except _adapt.AgentFormatError as e:
        raise PackageError(str(e)) from e


# ---------------------------------------------------------------------------
# Per-client post-checks (never emit a package the client would reject)
# ---------------------------------------------------------------------------

def _check_common(fm: dict, origin: str) -> None:
    name = fm.get("name")
    if not isinstance(name, str) or not NAME_RE.match(name):
        raise PackageError(f"{origin}: agent requires a kebab-case 'name' in frontmatter, got {name!r}")
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        raise PackageError(f"{origin}: agent requires a non-empty 'description' string")


def check_opencode_frontmatter(fm: dict, origin: str) -> None:
    _check_common(fm, origin)
    _translate_schema_check(_adapt.check_opencode_frontmatter, fm, origin)


def check_claude_frontmatter(fm: dict, origin: str) -> None:
    _check_common(fm, origin)
    _translate_schema_check(_adapt.check_claude_frontmatter, fm, origin)


def check_generic_frontmatter(fm: dict, origin: str) -> None:
    _check_common(fm, origin)


# ---------------------------------------------------------------------------
# Transforms
# ---------------------------------------------------------------------------

def _merge_whitelist_into_permission(perm, tools: list[str]) -> dict:
    """Materialize a tool whitelist as per-tool permission rules.

    Whitelisted tool-class keys -> allow; every other tool-class key -> deny; an
    explicit entry in an existing `permission` map always wins. A bare permission
    string is intentionally NOT honored as a global rule: keeping e.g. `allow`
    globally would grant un-whitelisted tools and is exactly the privilege
    widening this merge prevents.
    """
    merged = dict(perm) if isinstance(perm, dict) else {}
    allowed = set()
    extra = []
    for tool in tools:
        key = _adapt.OPENCODE_TOOL_ALIASES.get(tool, tool)
        if key in _adapt.OPENCODE_TOOL_KEYS:
            allowed.add(key)
        else:
            extra.append(key)
    for key in _adapt.OPENCODE_TOOL_KEYS:
        if key not in merged:
            merged[key] = "allow" if key in allowed else "deny"
    for key in extra:
        merged.setdefault(key, "allow")
    return merged


def adapt_for_opencode(fm: dict, notes: list, origin: str) -> None:
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
            perm = fm.get("permission")
            if isinstance(perm, str):
                notes.append(
                    f"opencode: dropped global permission shorthand {perm!r} (would widen); "
                    "tools whitelist merged into per-tool permission"
                )
            merged = _merge_whitelist_into_permission(perm, tools)
            fm["permission"] = merged
            denied = [k for k in _adapt.OPENCODE_TOOL_KEYS if merged.get(k) == "deny"]
            notes.append(
                "opencode: tools whitelist -> permission ({allow} allow{denied})".format(
                    allow=", ".join(
                        sorted(t for t, v in merged.items() if v == "allow" and t in _adapt.OPENCODE_TOOL_KEYS)
                    ) or "-",
                    denied=f"; deny {', '.join(denied)}" if denied else "",
                )
            )
    check_opencode_frontmatter(fm, origin)


def adapt_for_claude(fm: dict, notes: list, origin: str) -> None:
    if "tools" in fm:
        tools = normalize_tools(fm["tools"], origin)
        if isinstance(tools, dict):
            names = [str(k).strip().lower() for k, v in tools.items() if v is True]
        elif _is_client_label_list(tools):
            names = None
            fm.pop("tools")
            notes.append("claude: 'tools' listed supported clients (metadata); dropped for this client")
        else:
            names = tools
        if names is not None:
            mapped, dropped = [], []
            for tool in names:
                claude_name = _adapt.CLAUDE_TOOL_NAMES.get(tool)
                if claude_name:
                    if claude_name not in mapped:
                        mapped.append(claude_name)
                else:
                    dropped.append(tool)
            if not mapped:
                raise PackageError(
                    f"{origin}: claude 'tools' whitelist {names} maps to no Claude tool names; "
                    "refusing to omit 'tools' (absent tools = ALL tools in Claude)"
                )
            fm["tools"] = ", ".join(mapped)
            note = f"claude: tools whitelist -> \"{fm['tools']}\""
            if dropped:
                note += f" (no Claude equivalent, dropped: {', '.join(dropped)})"
            notes.append(note)
    if "model" in fm:
        model = str(fm["model"]).strip().lower()
        if model in _adapt.CLAUDE_MODEL_ALIASES:
            fm["model"] = model
        else:
            alias = next((a for a in ("sonnet", "opus", "haiku") if a in model), None)
            if alias:
                notes.append(f"claude: model {fm['model']!r} -> '{alias}'")
                fm["model"] = alias
            else:
                notes.append(f"claude: unmappable model {fm['model']!r} dropped (inherits default)")
                del fm["model"]
    check_claude_frontmatter(fm, origin)


def adapt_agent_markdown(content: str, client: str, origin: str = "AGENT.md"):
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
        raise PackageError(f"{origin}: no frontmatter block found (an agent requires name/description)")
    fm = parse_frontmatter(fm_text, origin)
    notes: list = []
    if client == "opencode":
        adapt_for_opencode(fm, notes, origin)
    elif client == "claude":
        adapt_for_claude(fm, notes, origin)
    else:
        check_generic_frontmatter(fm, origin)
        notes.append(f"{client}: no official agent frontmatter schema (best-effort); kept after YAML check")
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


def _resolve_agent(agent_path: Path):
    """Return (agent_file, base_dir, is_dir) for a dir or a bare AGENT.md file."""
    if agent_path.is_dir():
        agent_file = agent_path / "AGENT.md"
        if not agent_file.is_file():
            raise PackageError(f"no AGENT.md found in: {agent_path}")
        return agent_file, agent_path, True
    if agent_path.is_file():
        return agent_path, agent_path.parent, False
    raise PackageError(f"agent path does not exist: {agent_path}")


def package_agent(agent_path, clients, out_dir, make_zip: bool = False) -> list[Path]:
    """Package one agent dir (or bare AGENT.md) for each client; return written dirs."""
    agent_path = Path(agent_path)
    agent_file, base_dir, is_dir = _resolve_agent(agent_path)
    content = agent_file.read_text(encoding="utf-8-sig")
    origin = agent_file.name if not is_dir else f"{base_dir.name}/{agent_file.name}"

    out_dir = Path(out_dir)
    if out_dir.exists() and not out_dir.is_dir():
        raise PackageError(f"--out is an existing file, expected a directory: {out_dir}")
    out_resolved = out_dir.resolve()
    base_resolved = base_dir.resolve()
    if out_resolved == base_resolved or base_resolved in out_resolved.parents:
        raise PackageError(f"--out must not be inside the agent directory: {out_dir}")

    fm_text, _body = split_frontmatter(content)
    fm = parse_frontmatter(fm_text, origin) if fm_text is not None else {}
    raw_name = fm.get("name")
    if isinstance(raw_name, str) and NAME_RE.match(raw_name):
        agent_name = raw_name
    else:
        agent_name = agent_path.name if is_dir else agent_path.stem

    written: list[Path] = []
    for client in clients:
        adapted, notes = adapt_agent_markdown(content, client, origin=origin)
        target = out_dir / client / agent_name
        if target.exists():
            shutil.rmtree(target)
        if is_dir:
            _copy_tree(base_dir, target)
        else:
            target.mkdir(parents=True, exist_ok=True)
        (target / "AGENT.md").write_text(adapted, encoding="utf-8")
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
        description="Package an agent directory (or bare AGENT.md) for one or more LLM "
                    "clients (adapts AGENT.md frontmatter + copies the tree + post-checks)."
    )
    parser.add_argument("agent_path", help="Agent directory containing AGENT.md, or a bare AGENT.md file")
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
        package_agent(args.agent_path, clients, args.out, make_zip=args.zip)
    except PackageError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
