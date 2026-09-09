"""Per-client frontmatter adaptation for agent installs (agent-creator stage 7).

The repo canonical AGENT.md keeps a tool whitelist (`tools: [read, grep, ...]`)
and a provider-prefixed model, but clients disagree on the frontmatter schema
and placing the canonical form verbatim can make the agent unloadable:

  - opencode: AgentConfig requires `tools` as object<str, bool> (deprecated in
    favor of `permission`). A YAML list under `tools:` fails strict validation
    and the agent does not load. Transform: drop the whitelist and materialize
    it into `permission` — whitelisted tool keys become `allow`, remaining
    tool-like permission keys become `deny`; explicit permission entries win.
  - claude: `tools` must be a comma-separated string of Claude tool names
    (Read, Grep, Bash, ...); `model` must be an alias (sonnet/opus/haiku/
    inherit) or absent.
  - codex / deepseek: no official agent frontmatter convention (best-effort) —
    YAML sanity check only, content passes through byte-identical.

Every transform ends with a per-client post-check derived from the client's
published schema; violations exit 1 (fail loudly, never emit a file that would
not load).

Adapted from E:\\GitHub\\personal-workflow\\tools\\scripts\\agent_format.py
(the frontmatter adapter of that repo's install/update launchers). This repo
installs agents by copying into the client agents dir (no install launcher),
so this script is the conversion step you run BEFORE the copy.

Usage:
    python scripts/adapt_agent.py <agent.md 或 代理目录> --client <claude|opencode|codex|deepseek> [--out <落点文件>]

Exit code 0 = adapted (or verbatim passthrough for codex/deepseek). 1 = the
file could not be made valid for the target client (nothing written).
"""

import argparse
import io
import os
import re
import sys

import yaml

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n?---(?:\s*\n|$)", re.DOTALL)


class AgentFormatError(ValueError):
    """Raised when agent frontmatter cannot be made valid for the target client."""


# opencode permission keys that gate plain tools. Mechanism keys
# (external_directory, doom_loop, lsp) are never rewritten automatically.
OPENCODE_TOOL_KEYS = (
    "read",
    "edit",
    "glob",
    "grep",
    "list",
    "bash",
    "task",
    "webfetch",
    "websearch",
    "todowrite",
    "question",
    "skill",
)
# Repo whitelist tool names that fold into another permission key on opencode.
OPENCODE_TOOL_ALIASES = {"write": "edit", "patch": "edit"}
OPENCODE_MODES = ("primary", "subagent", "all")
OPENCODE_THEMES = ("primary", "secondary", "accent", "success", "warning", "error", "info")
HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
PERMISSION_ACTIONS = ("allow", "ask", "deny")

# canonical lowercase tool name -> Claude tool name.
CLAUDE_TOOL_NAMES = {
    "read": "Read",
    "write": "Write",
    "edit": "Edit",
    "bash": "Bash",
    "glob": "Glob",
    "grep": "Grep",
    "webfetch": "WebFetch",
    "websearch": "WebSearch",
    "task": "Task",
    "todowrite": "TodoWrite",
}
CLAUDE_MODEL_ALIASES = ("sonnet", "opus", "haiku", "inherit")
CLAUDE_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Clients whose copies are transformed; others pass through verbatim.
TRANSFORM_CLIENTS = ("claude", "opencode")
ALL_CLIENTS = ("claude", "opencode", "codex", "deepseek")


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
        raise AgentFormatError(f"{origin}: invalid YAML frontmatter: {e}") from e
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise AgentFormatError(f"{origin}: frontmatter must be a YAML mapping, got {type(data).__name__}")
    return data


def normalize_tools(value, origin: str):
    """Canonicalize `tools` to a lowercase name list; bool maps pass through."""
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return [p.strip().lower() for p in value.split(",") if p.strip()]
    if isinstance(value, list):
        names = []
        for item in value:
            if not isinstance(item, str):
                raise AgentFormatError(f"{origin}: 'tools' entries must be tool names, got {item!r}")
            names.append(item.strip().lower())
        return names
    raise AgentFormatError(f"{origin}: unsupported 'tools' form: {type(value).__name__}")


def _check_permission(perm, origin: str) -> None:
    if isinstance(perm, str):
        if perm not in PERMISSION_ACTIONS:
            raise AgentFormatError(f"{origin}: permission must be one of {'/'.join(PERMISSION_ACTIONS)}, got {perm!r}")
        return
    if isinstance(perm, dict):
        for key, value in perm.items():
            if isinstance(value, str):
                if value not in PERMISSION_ACTIONS:
                    raise AgentFormatError(f"{origin}: permission.{key} must be allow/ask/deny, got {value!r}")
            elif isinstance(value, dict):
                for pattern, action in value.items():
                    if not isinstance(pattern, str) or not isinstance(action, str) or action not in PERMISSION_ACTIONS:
                        raise AgentFormatError(
                            f"{origin}: permission.{key} pattern rules must map pattern -> allow/ask/deny"
                        )
            else:
                raise AgentFormatError(
                    f"{origin}: permission.{key} must be a string action or a pattern map, "
                    f"got {type(value).__name__}"
                )
        return
    raise AgentFormatError(f"{origin}: permission must be a string action or a map, got {type(perm).__name__}")


def check_opencode_frontmatter(fm: dict, origin: str) -> None:
    """Post-check against opencode's published AgentConfig schema."""
    if "tools" in fm:
        tools = fm["tools"]
        if not isinstance(tools, dict) or any(not isinstance(v, bool) for v in tools.values()):
            raise AgentFormatError(
                f"{origin}: opencode 'tools' must be a map of tool-name -> boolean "
                "(arrays/strings are invalid; canonical whitelists are converted automatically)"
            )
    if "mode" in fm and fm["mode"] not in OPENCODE_MODES:
        raise AgentFormatError(f"{origin}: opencode 'mode' must be one of {'/'.join(OPENCODE_MODES)}, got {fm['mode']!r}")
    if "permission" in fm and fm["permission"] is not None:
        _check_permission(fm["permission"], origin)
    for key in ("temperature", "top_p"):
        if key in fm and (isinstance(fm[key], bool) or not isinstance(fm[key], (int, float))):
            raise AgentFormatError(f"{origin}: opencode '{key}' must be a number, got {fm[key]!r}")
    for key in ("steps", "maxSteps"):
        if key in fm and (isinstance(fm[key], bool) or not isinstance(fm[key], int) or fm[key] <= 0):
            raise AgentFormatError(f"{origin}: opencode '{key}' must be a positive integer, got {fm[key]!r}")
    for key in ("hidden", "disable"):
        if key in fm and not isinstance(fm[key], bool):
            raise AgentFormatError(f"{origin}: opencode '{key}' must be a boolean, got {fm[key]!r}")
    for key in ("name", "description", "model", "variant"):
        if key in fm and not isinstance(fm[key], str):
            raise AgentFormatError(f"{origin}: opencode '{key}' must be a string, got {type(fm[key]).__name__}")
    if "color" in fm:
        color = fm["color"]
        if not isinstance(color, str) or not (HEX_COLOR_RE.match(color) or color in OPENCODE_THEMES):
            raise AgentFormatError(
                f"{origin}: opencode 'color' must be a hex color (#RRGGBB) or one of "
                f"{'/'.join(OPENCODE_THEMES)}, got {color!r}"
            )
    if "options" in fm and not isinstance(fm["options"], dict):
        raise AgentFormatError(f"{origin}: opencode 'options' must be a map, got {type(fm['options']).__name__}")


def check_claude_frontmatter(fm: dict, origin: str) -> None:
    """Post-check against Claude Code's subagent frontmatter requirements."""
    name = fm.get("name")
    if not isinstance(name, str) or not CLAUDE_NAME_RE.match(name):
        raise AgentFormatError(f"{origin}: claude requires a kebab-case 'name' in frontmatter, got {name!r}")
    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        raise AgentFormatError(f"{origin}: claude requires a non-empty 'description' string")
    if "tools" in fm and (not isinstance(fm["tools"], str) or not fm["tools"].strip()):
        raise AgentFormatError(
            f"{origin}: claude 'tools' must be a non-empty comma-separated string, got {fm['tools']!r}"
        )
    if "model" in fm and str(fm["model"]) not in CLAUDE_MODEL_ALIASES:
        raise AgentFormatError(
            f"{origin}: claude 'model' must be one of {'/'.join(CLAUDE_MODEL_ALIASES)} or absent, "
            f"got {fm['model']!r}"
        )


def adapt_for_opencode(fm: dict, notes: list, origin: str) -> None:
    if "tools" in fm:
        tools = normalize_tools(fm.pop("tools"), origin)
        if isinstance(tools, dict):
            fm["tools"] = tools
            notes.append("opencode: kept legacy tools bool-map (deprecated; prefer permission)")
        else:
            perm = fm.get("permission")
            if isinstance(perm, str):
                notes.append(
                    f"opencode: dropped tools whitelist ({', '.join(tools)}); permission shorthand "
                    f"{perm!r} kept as-is (per-tool rules not merged into a shorthand)"
                )
            else:
                allowed = set()
                extra = []
                for tool in tools:
                    key = OPENCODE_TOOL_ALIASES.get(tool, tool)
                    if key in OPENCODE_TOOL_KEYS:
                        allowed.add(key)
                    else:
                        extra.append(key)
                merged = dict(perm) if isinstance(perm, dict) else {}
                for key in OPENCODE_TOOL_KEYS:
                    if key not in merged:
                        merged[key] = "allow" if key in allowed else "deny"
                for key in extra:
                    merged.setdefault(key, "allow")
                fm["permission"] = merged
                denied = [k for k in OPENCODE_TOOL_KEYS if merged.get(k) == "deny"]
                notes.append(
                    "opencode: tools whitelist -> permission ({allow} allow{denied})".format(
                        allow=", ".join(sorted(allowed)) or "-",
                        denied=f"; deny {', '.join(denied)}" if denied else "",
                    )
                )
    check_opencode_frontmatter(fm, origin)


def adapt_for_claude(fm: dict, notes: list, origin: str) -> None:
    if "tools" in fm:
        tools = normalize_tools(fm["tools"], origin)
        if isinstance(tools, dict):
            names = [str(k).strip().lower() for k, v in tools.items() if v is True]
        else:
            names = tools
        mapped, dropped = [], []
        for tool in names:
            claude_name = CLAUDE_TOOL_NAMES.get(tool)
            if claude_name:
                if claude_name not in mapped:
                    mapped.append(claude_name)
            else:
                dropped.append(tool)
        if not mapped:
            raise AgentFormatError(
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
        if model in CLAUDE_MODEL_ALIASES:
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

    Raises AgentFormatError on malformed frontmatter or when the result would
    violate the client's schema. codex/deepseek (and unknown labels) receive a
    YAML sanity check and byte-identical passthrough.
    """
    client = (client or "").lower()
    fm_text, body = split_frontmatter(content)
    if fm_text is None:
        return content, [f"{client}: no frontmatter block found; installed verbatim"]
    fm = parse_frontmatter(fm_text, origin)
    if client in TRANSFORM_CLIENTS:
        notes: list = []
        if client == "opencode":
            adapt_for_opencode(fm, notes, origin)
        else:
            adapt_for_claude(fm, notes, origin)
        dumped = yaml.safe_dump(fm, sort_keys=False, allow_unicode=True, default_flow_style=False, width=4096)
        return f"---\n{dumped}---\n{body}", notes
    return content, [f"{client}: no official agent frontmatter schema (best-effort); kept verbatim after YAML check"]


def resolve_agent_path(path: str) -> str:
    """Accept a file or a dir holding AGENT.md; return the file to adapt."""
    if os.path.isdir(path):
        candidate = os.path.join(path, "AGENT.md")
        if not os.path.isfile(candidate):
            raise AgentFormatError(f"no AGENT.md found in directory: {path}")
        return candidate
    if os.path.isfile(path):
        return path
    raise AgentFormatError(f"path does not exist: {path}")


def main(argv: list[str] | None = None) -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(
        description="Adapt a repo-canonical AGENT.md frontmatter to one client's schema (run before copying into the client agents dir)."
    )
    parser.add_argument("agent_path", help="AGENT.md file, or a directory containing AGENT.md")
    parser.add_argument("--client", required=True, choices=ALL_CLIENTS, help="Target client")
    parser.add_argument("--out", default=None, help="Write adapted file here instead of stdout")
    args = parser.parse_args(argv)

    try:
        agent_file = resolve_agent_path(args.agent_path)
        content = open(agent_file, "r", encoding="utf-8").read()
        adapted, notes = adapt_agent_markdown(content, args.client, origin=os.path.basename(agent_file))
    except AgentFormatError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 1

    for note in notes:
        print(f"ℹ️  {note}", file=sys.stderr)

    if args.out:
        out_dir = os.path.dirname(os.path.abspath(args.out))
        os.makedirs(out_dir, exist_ok=True)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(adapted)
        print(f"✅ wrote {args.out} ({args.client})")
    else:
        sys.stdout.write(adapted)
    return 0


if __name__ == "__main__":
    sys.exit(main())
