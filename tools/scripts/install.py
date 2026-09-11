"""Install verified capabilities (skills / agents / creators) into client dirs.

Dev-only orchestrator for the tools layer (see tools/README.md). It does NOT
reimplement frontmatter adaptation: it dispatches to the creators' packagers
(`package_skill.py` / `package_agent.py`) per target-client, then places the
packaged tree into the client's landing directory, validates it, and cleans
caches. The packagers stay inside the creator products (independent install).

Landing matrix (authoritative sources):
  - skills: skill-creator/INSTALL.md §0 / agent-creator/INSTALL.md §0
  - agents: agents/README.md (claude, opencode); codex/deepseek have no
    documented agent landing → those combinations fail loudly.
  - deepseek skill path is best-effort (harness path varies by version).

Usage:
    python tools/scripts/install.py <target-dir>... \
        [--all skills|agents] [--creator skill-creator|agent-creator] \
        [--client <name>]... [--scope global|workspace] [--dest <repo>] \
        [--artifact auto|skill|agent] [--force] [--zip --out <dir>]

Exit codes: 0 all ok; 1 a unit failed (package/place/validate); 2 bad arguments.
"""

import argparse
import io
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]

ALL_CLIENTS = ("claude", "opencode", "codex", "deepseek")

PACKAGERS = {
    "skill": REPO_ROOT / "skill-creator" / "skills" / "skill-creator" / "scripts" / "package_skill.py",
    "agent": REPO_ROOT / "agent-creator" / "skills" / "agent-creator" / "scripts" / "package_agent.py",
}
ENTRY_FILE = {"skill": "SKILL.md", "agent": "AGENT.md"}

# name -> (artifact kind, product dir)
CREATORS = {
    "skill-creator": ("skill", REPO_ROOT / "skill-creator" / "skills" / "skill-creator"),
    "agent-creator": ("skill", REPO_ROOT / "agent-creator" / "skills" / "agent-creator"),
}

# kind -> client -> {scope: relative landing dir}. "~" is expanded to home.
LANDING = {
    "skill": {
        "claude": {"global": "~/.claude/skills", "workspace": ".claude/skills"},
        "opencode": {"global": "~/.config/opencode/skills", "workspace": ".opencode/skills"},
        "codex": {"global": "~/.agents/skills", "workspace": ".agents/skills"},
        "deepseek": {"global": "~/.deepseek/skills", "workspace": ".deepseek/skills"},
    },
    "agent": {
        "claude": {"global": "~/.claude/agents", "workspace": ".claude/agents"},
        "opencode": {"global": "~/.config/opencode/agent", "workspace": ".opencode/agent"},
    },
}

# Client auto-detection markers (best-effort; --client always overrides).
CLIENT_ENV_MARKERS = {
    "claude": ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT"),
    "opencode": ("OPENCODE", "OPENCODE_BIN", "OPENCODE_PID"),
    "codex": ("CODEX_HOME", "CODEX_SANDBOX"),
    "deepseek": ("DEEPSEEK_HARNESS", "DEEPSEEK_AGENT"),
}
# Config-dir markers probed under a workspace root (the "current workspace").
CLIENT_DIR_MARKERS = (
    ("claude", ".claude"),
    ("opencode", ".opencode"),
    ("codex", ".agents"),
    ("deepseek", ".deepseek"),
)

CACHE_DIRS = ("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")


class ArgError(ValueError):
    """Bad arguments → exit code 2."""


class UnitError(RuntimeError):
    """A single package/place/validate unit failed → exit code 1."""


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
# Client detection
# ---------------------------------------------------------------------------

def detect_clients(env: dict, search_dirs: list[Path]) -> list[str]:
    """Best-effort detect the client(s) in use.

    Priority: environment markers of a running client; else config-dir markers
    under the workspace search dirs. Home dirs are NOT probed (they would match
    every client the user has ever installed, not "the one in use"). Returns a
    sorted list.
    """
    hits = [c for c, marks in CLIENT_ENV_MARKERS.items() if any(env.get(m) for m in marks)]
    if hits:
        return sorted(set(hits))
    found: set[str] = set()
    for d in search_dirs:
        for client, rel in CLIENT_DIR_MARKERS:
            if (Path(d) / rel).is_dir():
                found.add(client)
    return sorted(found)


def resolve_clients(arg_clients: list[str], env: dict, scope: str, dest: Path | None) -> list[str]:
    if arg_clients:
        return arg_clients
    search = [dest] if dest and scope == "workspace" else [Path.cwd()]
    detected = detect_clients(env, search)
    if not detected:
        raise ArgError(
            "could not auto-detect a client (no env marker / workspace config dir); "
            f"pass --client <name> (choose from {', '.join(ALL_CLIENTS)})"
        )
    print(f"ℹ️  auto-detected client(s): {', '.join(detected)}")
    return detected


# ---------------------------------------------------------------------------
# Target resolution
# ---------------------------------------------------------------------------

def _kind_of_dir(d: Path) -> str | None:
    if (d / "SKILL.md").is_file():
        return "skill"
    if (d / "AGENT.md").is_file():
        return "agent"
    return None


def _discover(library: Path, kind: str) -> list[Path]:
    entry = ENTRY_FILE[kind]
    out = []
    if not library.is_dir():
        return out
    for f in sorted(library.rglob(entry)):
        if any(part.startswith(".") for part in f.relative_to(library).parts):
            continue
        out.append(f.parent)
    return out


def resolve_targets(targets, all_kinds, creators, artifact) -> list[tuple[str, Path]]:
    """Return a list of (kind, source_dir)."""
    items: list[tuple[str, Path]] = []
    for raw in all_kinds:
        for part in str(raw).split(","):
            part = part.strip().lower()
            if not part:
                continue
            if part not in ("skills", "agents"):
                raise ArgError(f"--all must be 'skills' or 'agents', got {part!r}")
            kind = "skill" if part == "skills" else "agent"
            items.extend((kind, p) for p in _discover(REPO_ROOT / part, kind))
    for raw in creators:
        for part in str(raw).split(","):
            part = part.strip()
            if not part:
                continue
            if part not in CREATORS:
                raise ArgError(f"unknown creator: {part!r} (choose from {', '.join(CREATORS)})")
            kind, product = CREATORS[part]
            items.append((kind, product))
    for raw in targets:
        p = Path(raw)
        if not p.is_dir():
            raise ArgError(f"target is not a directory: {raw}")
        kind = _kind_of_dir(p)
        if kind is None:
            raise ArgError(f"target has no SKILL.md or AGENT.md: {raw}")
        if artifact != "auto" and artifact != kind:
            raise ArgError(f"--artifact {artifact} does not match target kind {kind}: {raw}")
        items.append((kind, p))
    # de-dup, keep order
    seen, uniq = set(), []
    for it in items:
        key = (it[0], str(it[1].resolve()))
        if key not in seen:
            seen.add(key)
            uniq.append(it)
    if not uniq:
        raise ArgError("no targets given (pass a dir, --all skills|agents, or --creator <name>)")
    return uniq


# ---------------------------------------------------------------------------
# Landing
# ---------------------------------------------------------------------------

def landing_base(kind: str, client: str, scope: str, dest: Path | None) -> Path | None:
    spec = LANDING.get(kind, {}).get(client)
    if spec is None:
        return None
    rel = spec[scope]
    if rel.startswith("~/"):
        return Path.home() / rel[2:]
    if scope == "workspace":
        if dest is None:
            raise ArgError("--scope workspace requires --dest <target repo root>")
        return dest / rel
    return Path(rel)


def run_packager(kind: str, src_dir: Path, client: str, out_dir: Path, make_zip: bool) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(PACKAGERS[kind]), str(src_dir), "--client", client, "--out", str(out_dir)]
    if make_zip:
        cmd.append("--zip")
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def _single_package(out_dir: Path, client: str) -> Path:
    root = out_dir / client
    dirs = [p for p in root.iterdir() if p.is_dir()] if root.is_dir() else []
    if len(dirs) != 1:
        raise UnitError(f"expected exactly one packaged dir under {root}, found {len(dirs)}")
    return dirs[0]


def clean_caches(root: Path) -> None:
    for name in CACHE_DIRS:
        for p in root.rglob(name):
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)


def _generic_frontmatter_ok(kind: str, final: Path) -> None:
    entry = final / ENTRY_FILE[kind]
    text = entry.read_text(encoding="utf-8-sig")
    import re
    import yaml
    m = re.match(r"^---\s*\n(.*?)\n?---(?:\s*\n|$)", text, re.DOTALL)
    if not m:
        raise UnitError(f"{entry.name} has no frontmatter")
    fm = yaml.safe_load(m.group(1)) or {}
    if not isinstance(fm, dict) or not fm.get("name") or not fm.get("description"):
        raise UnitError(f"{entry.name} frontmatter missing name/description")


def _run_validator(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def validate_install(kind: str, final: Path) -> None:
    _generic_frontmatter_ok(kind, final)
    scripts = final / "scripts"
    for validator in ("validate_skills.py", "validate_agents.py"):
        v = scripts / validator
        if v.is_file():
            r = _run_validator(v, "--strict", "--dir", str(final))
            if r.returncode != 0:
                raise UnitError(f"self-validation failed ({validator}):\n{r.stdout}{r.stderr}")
    idx = final / "indexes" / "upstream.db"
    for searcher in ("search_index.py", "search_agent_index.py"):
        s = scripts / searcher
        if s.is_file() and idx.is_file():
            r = _run_validator(s, "--stats")
            if r.returncode != 0:
                raise UnitError(f"index integrity check failed ({searcher}):\n{r.stdout}{r.stderr}")
            break


def place(pkg_dir: Path, final: Path, force: bool) -> Path | None:
    """Copy pkg_dir -> final. Returns the backup path when one was made."""
    backup = None
    base = final.parent
    base.mkdir(parents=True, exist_ok=True)
    if final.exists():
        if not force:
            raise UnitError(f"landing already exists: {final} (use --force to back up and replace)")
        backup = final.with_name(final.name + ".bak")
        if backup.exists():
            shutil.rmtree(backup)
        shutil.move(str(final), str(backup))
    shutil.copytree(pkg_dir, final)
    return backup


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def install_unit(kind, src_dir, client, scope, dest, force, make_zip, zip_out) -> str:
    base = landing_base(kind, client, scope, dest)
    if base is None:
        raise UnitError(f"no landing configured for artifact '{kind}' + client '{client}'")
    with tempfile.TemporaryDirectory(prefix="install-") as td:
        staging = Path(td)
        r = run_packager(kind, src_dir, client, staging, make_zip)
        if r.returncode != 0:
            raise UnitError(f"packaging failed:\n{r.stdout}{r.stderr}")
        pkg = _single_package(staging, client)
        name = pkg.name
        final = base / name
        backup = place(pkg, final, force)
        try:
            clean_caches(final)
            validate_install(kind, final)
            clean_caches(final)
        except UnitError:
            shutil.rmtree(final, ignore_errors=True)
            if backup is not None and backup.exists():
                shutil.move(str(backup), str(final))
            raise
        if make_zip and zip_out is not None:
            zip_dir = Path(zip_out) / client
            zip_dir.mkdir(parents=True, exist_ok=True)
            shutil.make_archive(str(zip_dir / name), "zip", root_dir=str(final.parent), base_dir=name)
        return str(final)


def main(argv=None) -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Install skills/agents/creators into client directories.")
    parser.add_argument("targets", nargs="*", help="Directories containing SKILL.md or AGENT.md")
    parser.add_argument("--all", action="append", default=[], dest="all_kinds",
                        help="Install every library entry: 'skills' or 'agents' (repeatable/comma)")
    parser.add_argument("--creator", action="append", default=[],
                        help="Install a creator product: skill-creator | agent-creator")
    parser.add_argument("--client", action="append", default=[],
                        help=f"Target client (repeatable/comma): {', '.join(ALL_CLIENTS)}; default: auto-detect")
    parser.add_argument("--scope", choices=("global", "workspace"), default="global")
    parser.add_argument("--dest", default=None, help="Target repo root (required for --scope workspace)")
    parser.add_argument("--artifact", choices=("auto", "skill", "agent"), default="auto",
                        help="Force the artifact kind for dir targets (default: auto)")
    parser.add_argument("--force", action="store_true", help="Back up and replace an existing landing")
    parser.add_argument("--zip", action="store_true", help="Also write a .zip per package")
    parser.add_argument("--out", default=None, help="Directory for --zip archives (required with --zip)")
    args = parser.parse_args(argv)

    try:
        clients = []
        for raw in args.client:
            for part in str(raw).split(","):
                part = part.strip().lower()
                if part:
                    clients.append(part)
        unknown = [c for c in clients if c not in ALL_CLIENTS]
        if unknown:
            raise ArgError(f"unknown client(s): {', '.join(unknown)} (choose from {', '.join(ALL_CLIENTS)})")
        if args.zip and not args.out:
            raise ArgError("--zip requires --out <dir>")
        dest = Path(args.dest).resolve() if args.dest else None
        if args.scope == "workspace" and dest is None:
            raise ArgError("--scope workspace requires --dest <target repo root>")
        clients = resolve_clients(clients, dict(os.environ), args.scope, dest)
        items = resolve_targets(args.targets, args.all_kinds, args.creator, args.artifact)
    except ArgError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2

    ok = failed = 0
    for kind, src in items:
        for client in clients:
            label = f"[{kind}] {src.name} -> {client}"
            try:
                final = install_unit(kind, src, client, args.scope, dest, args.force, args.zip, args.out)
                print(f"✅ {label}: {final}")
                ok += 1
            except UnitError as e:
                print(f"❌ {label}: {e}", file=sys.stderr)
                failed += 1
            except Exception as e:  # never crash the batch
                print(f"❌ {label}: unexpected error: {e}", file=sys.stderr)
                failed += 1

    print(f"\n合计：{ok} 成功，{failed} 失败")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
