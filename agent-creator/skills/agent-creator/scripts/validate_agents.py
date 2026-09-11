"""Validate agent definitions (AGENT.md).

Part of the agent-creator skill (see SKILL.md).
Checks frontmatter schema, identity/boundary/permission/collaboration
sections, and dangling local references. Parallel to validate_skills.py.

Usage:
    python scripts/validate_agents.py [--dir <agents_dir>] [--strict]

Exit code 0 = all passed, 1 = errors found (or warnings in strict mode).
"""

import argparse
import io
import os
import re
import sys
from collections.abc import Mapping
from datetime import date, datetime

import yaml

from _project_paths import find_skill_root
from security_scan import (
    fenced_ranges,
    find_dangerous_pipes,
    find_inline_secrets,
    is_scannable_text,
)

# Skill root = the directory containing scripts/ (self-contained; the module
# never depends on a host repository). Used as the fallback base for backtick
# references and as the default scan target.
SKILL_ROOT = find_skill_root(__file__)
# Doc/resource dirs that must never be scanned as agent definitions
EXEMPT_DIRS = {"examples", "references", "templates"}

# Noise dirs skipped by the security sweep. Unlike definition discovery, the
# sweep must descend into *hidden* dirs: credentials commonly live in `.ssh/`,
# `.aws/`, etc., so skipping every dotdir let a bundled `id_rsa` slip through.
# Only VCS/cache trees that cannot hold authored text are skipped.
SECURITY_SKIP_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", "node_modules",
    ".mypy_cache", ".pytest_cache", ".ruff_cache", ".tox", ".venv", "venv",
}

# Non-agent docs that may sit beside agents in a library (mirrored by
# compare_agents.py). Kept lowercase for case-insensitive matching.
NON_AGENT_DOCS = {
    "readme.md", "readme", "changelog.md", "development-plan.md",
    "agents.md", "skill.md", "catalog.md", "catalog", "agents-audit.md",
}

# Backtick resource references that must resolve on disk. The extension
# whitelist is broader than script types so data/text artifacts
# (`indexes/upstream.db`, `.txt`, …) are covered too. Refs inside fenced code
# blocks are illustrative and exempt.
BACKTICK_REF_RE = re.compile(
    r"`([^`\s]+\.(?:md|py|sh|json|ya?ml|toml|txt|xml|db|sqlite|csv|ts|tsx|js|jsx|mjs|cjs|css|html|rs|go|java|rb|php))`"
)

VALID_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

BOUNDARY_PATTERNS = [
    re.compile(r"^##\s+职责范围", re.MULTILINE),
    re.compile(r"^##\s+Responsibilities?", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+Scope", re.MULTILINE | re.IGNORECASE),
]
MUST_DO_PATTERNS = [
    re.compile(r"必须做", re.MULTILINE),
    re.compile(r"Must\s+Do", re.MULTILINE | re.IGNORECASE),
]
REFUSE_PATTERNS = [
    re.compile(r"拒绝做", re.MULTILINE),
    re.compile(r"Refuse|Decline|Never", re.MULTILINE | re.IGNORECASE),
]
PERMISSION_PATTERNS = [
    re.compile(r"^##\s+工具与权限", re.MULTILINE),
    re.compile(r"^##\s+Tools?\s*(?:&|and)\s*Permissions?", re.MULTILINE | re.IGNORECASE),
]
COLLAB_PATTERNS = [
    re.compile(r"^##\s+协作协议", re.MULTILINE),
    re.compile(r"^##\s+Collaboration", re.MULTILINE | re.IGNORECASE),
]
ESCALATION_PATTERNS = [
    re.compile(r"升级路径|升级|交还", re.MULTILINE),
    re.compile(r"Escalat", re.MULTILINE | re.IGNORECASE),
]
COMPLETION_PATTERNS = [
    re.compile(r"^##\s+完成标准", re.MULTILINE),
    re.compile(r"^##\s+Completion\s*(?:Criteria|Standard)", re.MULTILINE | re.IGNORECASE),
]
TOOLS_FIELD_PATTERNS = [
    re.compile(r"^tools:", re.MULTILINE),
    re.compile(r"^permission:", re.MULTILINE),
]
SECURITY_DISCLAIMER_PATTERNS = [
    re.compile(r"AUTHORIZED USE ONLY", re.IGNORECASE),
    re.compile(r"仅限授权使用"),
]


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
            setattr(
                sys,
                stream_name,
                io.TextIOWrapper(buffer, encoding="utf-8", errors="backslashreplace"),
            )


def is_exempt_dir(path: str) -> bool:
    parts = path.replace("\\", "/").split("/")
    return any(p in EXEMPT_DIRS for p in parts)


def normalize_yaml_value(value):
    if isinstance(value, Mapping):
        return {k: normalize_yaml_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [normalize_yaml_value(v) for v in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def parse_frontmatter(content: str):
    fm_match = re.search(r"^---\s*\n(.*?)\n?---(?:\s*\n|$)", content, re.DOTALL)
    if not fm_match:
        return None, ["Missing or malformed YAML frontmatter"]
    fm_text = fm_match.group(1)
    fm_errors = []
    try:
        metadata = yaml.safe_load(fm_text) or {}
        metadata = normalize_yaml_value(metadata)
        if not isinstance(metadata, Mapping):
            return None, ["Frontmatter must be a YAML mapping/object."]
        if "description" in metadata:
            desc = metadata["description"]
            if not desc or (isinstance(desc, str) and not desc.strip()):
                fm_errors.append("description field is empty or whitespace only.")
        return dict(metadata), fm_errors
    except yaml.YAMLError as e:
        return None, [f"YAML Syntax Error: {e}"]


def agent_name_from_path(agent_path: str) -> str:
    """Determine the agent name from its file/dir name (strip trailing .md)."""
    name = os.path.basename(agent_path)
    if name.endswith(".md"):
        name = name[:-3]
    return name


def check_dir_security(agent_dir: str, agent_file: str, rel_path: str) -> list[str]:
    """Scan every text/code file bundled with an agent for secrets / dangerous pipes.

    Release discipline says to sweep the agent directory and its scripts before
    publishing; a credential or `curl … | bash` pasted into a bundled resource
    is as harmful as one in AGENT.md. Markdown files use the fenced-only
    (prose-aware) view; code files are scanned in full.
    """
    errs: list[str] = []
    if not os.path.isdir(agent_dir):
        return errs
    agent_file_abs = os.path.abspath(agent_file)
    for dirpath, dirs, files in os.walk(agent_dir):
        # Exempt dirs (references/templates/examples) are excluded from agent-
        # *definition* discovery, but bundled resources are exactly what the
        # security sweep must cover — descend into hidden dirs (credential
        # locations such as `.ssh/`/`.aws/`), skipping only VCS/cache trees.
        dirs[:] = [d for d in dirs if d not in SECURITY_SKIP_DIRS]
        for fn in files:
            p = os.path.join(dirpath, fn)
            if os.path.abspath(p) == agent_file_abs or not is_scannable_text(fn):
                continue
            try:
                with open(p, "r", encoding="utf-8-sig", errors="replace") as f:
                    text = f.read()
            except OSError:
                continue
            is_markdown = fn.lower().endswith(".md")
            for m in find_dangerous_pipes(text, fenced_only=is_markdown):
                errs.append(
                    f"🚨 {rel_path}: Dangerous remote-execution pipe detected in "
                    f"{os.path.relpath(p, agent_dir)} ({m.group(0)[:60]!r}); remove it or annotate "
                    "its block/line with a `<!-- security-allowlist -->` note."
                )
            for m in find_inline_secrets(text):
                errs.append(
                    f"🚨 {rel_path}: Possible inline secret/credential detected in "
                    f"{os.path.relpath(p, agent_dir)} ({m.group(0)[:6]}…); remove it or annotate "
                    "its line with a `<!-- security-allowlist -->` note."
                )
    return errs


def collect_validation_results(
    agents_dir: str, strict_mode: bool = False, explicit_dir: bool = False
) -> dict:
    agents_dir = os.path.abspath(agents_dir)
    errors = []
    if not os.path.isdir(agents_dir):
        # A wrong/typo'd --dir must FAIL loudly. os.walk on a missing path yields
        # nothing, so without this guard we'd print "Checked 0 agents" and exit 0.
        errors.append(f"❌ Scan directory does not exist: {agents_dir}")
        return {
            "agent_count": 0,
            "warnings": [],
            "advisories": [],
            "errors": errors,
            "strict_mode": strict_mode,
        }
    warnings = []
    advisories = []
    agent_count = 0

    for root, dirs, files in os.walk(agents_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and not is_exempt_dir(os.path.join(root, d))]
        # Agent definition files: AGENT.md inside a dir, or a top-level *.md
        if "AGENT.md" in files:
            candidates = [(root, "AGENT.md")]
        else:
            mds = sorted(f for f in files if f.endswith(".md") and f.lower() not in NON_AGENT_DOCS)
            candidates = [(root, f) for f in mds]
        for base, fname in candidates:
            agent_path = os.path.join(base, fname)
            rel_path = os.path.relpath(agent_path, agents_dir)
            try:
                with open(agent_path, "r", encoding="utf-8-sig", errors="replace") as f:
                    content = f.read()
            except Exception as e:
                errors.append(f"❌ {rel_path}: Unreadable file - {str(e)}")
                continue

            # Only AGENT.md is a mandatory marker. A plain *.md is an agent
            # definition only when it actually carries frontmatter, so library
            # docs (evolution records, subagent prompt files) are not mistaken
            # for agents and blamed for "missing frontmatter".
            if fname != "AGENT.md" and not re.match(r"^---\s*\n", content):
                continue

            agent_count += 1
            metadata, fm_errors = parse_frontmatter(content)
            if metadata is None:
                errors.append(f"❌ {rel_path}: Missing or malformed YAML frontmatter")
                continue
            for fe in fm_errors:
                errors.append(f"❌ {rel_path}: YAML Structure Error - {fe}")

            dir_name = agent_name_from_path(root) if fname == "AGENT.md" else agent_name_from_path(fname)
            if "name" not in metadata:
                errors.append(f"❌ {rel_path}: Missing 'name' in frontmatter")
            else:
                n = metadata["name"]
                if not isinstance(n, str):
                    errors.append(f"❌ {rel_path}: 'name' must be a string, got {type(n).__name__}")
                else:
                    if not VALID_NAME.match(n):
                        errors.append(f"❌ {rel_path}: 'name' must be kebab-case, got '{n}'")
                    if n != dir_name:
                        warnings.append(f"⚠️  {rel_path}: name '{n}' differs from dir/file name '{dir_name}'")

            if "description" not in metadata or metadata["description"] is None:
                errors.append(f"❌ {rel_path}: Missing 'description' in frontmatter")
            else:
                desc = metadata["description"]
                if not isinstance(desc, str):
                    errors.append(f"❌ {rel_path}: 'description' must be a string, got {type(desc).__name__}")
                elif len(desc) > 300:
                    errors.append(f"❌ {rel_path}: Description is oversized ({len(desc)} chars). Must be concise.")
                else:
                    # Trigger-surface discipline (mirror of validate_skills.py):
                    # description is the only always-loaded field — keep it single-line
                    # and free of angle-bracket placeholders so trigger matching stays
                    # reliable. Advisory only, never a failure.
                    if any(ch in desc for ch in ("<", ">")):
                        advisories.append(
                            f"ℹ️  {rel_path}: Description contains '<'/'>' placeholder chars — "
                            "these distort trigger matching (use plain wording, not placeholders)."
                        )
                    if "\n" in desc:
                        advisories.append(
                            f"ℹ️  {rel_path}: Description is multi-line — keep it single-line "
                            "(description is the only unconditionally loaded trigger surface)."
                        )

            risk = metadata.get("risk")
            if risk == "offensive" and not any(p.search(content) for p in SECURITY_DISCLAIMER_PATTERNS):
                errors.append(f"🚨 {rel_path}: OFFENSIVE AGENT MISSING THE AUTHORIZED-USE DISCLAIMER")

            if "version" in metadata:
                v = metadata["version"]
                if not isinstance(v, str) or not VERSION_PATTERN.match(v):
                    errors.append(f"❌ {rel_path}: Invalid 'version' format. Must be semver x.y.z, got '{metadata['version']}'")
            else:
                advisories.append(f"ℹ️  {rel_path}: Missing 'version' field (recommended for lifecycle tracking)")

            if "date_added" in metadata:
                d = metadata["date_added"]
                if not isinstance(d, str) or not DATE_PATTERN.match(d):
                    errors.append(f"❌ {rel_path}: Invalid 'date_added' format. Must be YYYY-MM-DD.")

            body = content.split("---", 2)[2] if content.startswith("---") else content
            if not body.strip():
                errors.append(f"❌ {rel_path}: Agent body is empty (identity/boundary sections required)")

            if not any(p.search(content) for p in BOUNDARY_PATTERNS):
                msg = f"⚠️  {rel_path}: Missing '## 职责范围' section (identity boundary required)"
                (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)
            elif not (any(p.search(content) for p in MUST_DO_PATTERNS) and any(p.search(content) for p in REFUSE_PATTERNS)):
                msg = f"⚠️  {rel_path}: '职责范围' should declare both 必须做 and 拒绝做"
                (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)

            if not any(p.search(content) for p in PERMISSION_PATTERNS) and not any(
                p.search(content) for p in TOOLS_FIELD_PATTERNS
            ):
                msg = f"⚠️  {rel_path}: No tools/permission declaration (least-privilege principle)"
                (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)

            if not any(p.search(content) for p in COLLAB_PATTERNS):
                msg = f"⚠️  {rel_path}: Missing '## 协作协议' section (when called / how to report)"
                (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)
            elif not any(p.search(content) for p in ESCALATION_PATTERNS):
                msg = f"⚠️  {rel_path}: '协作协议' should declare an escalation path (when to hand back to human)"
                (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)

            if not any(p.search(content) for p in COMPLETION_PATTERNS):
                msg = f"⚠️  {rel_path}: Missing '## 完成标准' section (verifiable acceptance criteria)"
                (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)

            # Links and backtick refs shown inside a fenced code block are
            # illustrative (a doc teaching syntax) and exempt from on-disk checks.
            fenced_spans = fenced_ranges(content, closed_only=True)

            def _is_in_fence(pos: int) -> bool:
                return any(s <= pos < e for s, e in fenced_spans)

            for m in re.finditer(r"\[[^\]]*\]\(([^)]+)\)", content):
                if _is_in_fence(m.start()):
                    continue
                link = m.group(1).strip()
                # CommonMark allows an optional title after the destination
                # (`[x](path "Title")`). Strip it so a valid titled link is not
                # mistaken for a path containing spaces and reported dangling.
                link = re.sub(r"\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\))\s*$", "", link).strip()
                link_clean = link.split("#")[0].strip()
                if not link_clean or link_clean.startswith(("http://", "https://", "mailto:", "<", ">")):
                    continue
                if os.path.isabs(link_clean):
                    continue
                target_path = os.path.normpath(os.path.join(root, link_clean))
                if not os.path.exists(target_path):
                    errors.append(f"❌ {rel_path}: Dangling link detected. Path '{link_clean}' does not exist locally.")

            backtick_refs = set()
            for m in BACKTICK_REF_RE.finditer(content):
                ref = m.group(1)
                if ref.startswith("http") or "/" not in ref or _is_in_fence(m.start()):
                    continue
                backtick_refs.add(ref)
            for ref in sorted(backtick_refs):
                ref_clean = ref.split("#")[0].strip()
                if (
                    not ref_clean
                    or ref_clean.startswith("~/")
                    or any(ch in ref_clean for ch in ("<", ">", "*", "?", "…"))
                    or "xxx" in ref_clean
                    or "your-agent-name" in ref_clean
                ):
                    continue
                if os.path.isabs(ref_clean):
                    continue
                # Resolve relative to the agent's own directory only. Falling back
                # to this validator's own SKILL_ROOT would let an agent "borrow" a
                # path that only exists inside agent-creator — a false pass that
                # hides dangling references (mirrors the skill validator).
                target = os.path.normpath(os.path.join(root, ref_clean))
                if not os.path.exists(target):
                    errors.append(f"❌ {rel_path}: Backtick reference '{ref_clean}' does not exist locally.")

            # Security scan: inline secrets everywhere; dangerous remote-exec
            # pipes in code context. Local `<!-- security-allowlist -->` markers
            # excuse only the annotated line/block.
            for m in find_dangerous_pipes(content):
                errors.append(
                    f"🚨 {rel_path}: Dangerous remote-execution pipe detected "
                    f"({m.group(0)[:60]!r}); remove it or annotate its block/line with a "
                    "`<!-- security-allowlist -->` note."
                )
            for m in find_inline_secrets(content):
                errors.append(
                    f"🚨 {rel_path}: Possible inline secret/credential detected "
                    f"({m.group(0)[:6]}…); remove it or annotate its line with a "
                    "`<!-- security-allowlist -->` note."
                )
            if fname == "AGENT.md":
                errors.extend(check_dir_security(base, agent_path, rel_path))

    if agent_count == 0 and explicit_dir:
        # An explicit --dir that exists but holds no agent definitions is almost
        # always a wrong path; fail loudly instead of a green, empty release gate.
        errors.append(
            f"❌ No agent definitions found under: {agents_dir} "
            "(wrong --dir? point it at a directory containing AGENT.md)"
        )

    return {
        "agent_count": agent_count,
        "warnings": warnings,
        "advisories": advisories,
        "errors": errors,
        "strict_mode": strict_mode,
    }


def validate_agents(agents_dir: str, strict_mode: bool = False, explicit_dir: bool = False) -> bool:
    configure_utf8_output()
    print(f"🔍 Validating agents in: {agents_dir}")
    print(f"⚙️  Mode: {'STRICT (CI)' if strict_mode else 'Standard (Dev)'}")

    results = collect_validation_results(agents_dir, strict_mode=strict_mode, explicit_dir=explicit_dir)
    warnings = results["warnings"]
    advisories = results["advisories"]
    errors = results["errors"]
    agent_count = results["agent_count"]

    print(f"\n📊 Checked {agent_count} agents.")

    if warnings:
        print(f"\n⚠️  Found {len(warnings)} Warnings:")
        for w in warnings:
            print(w)
    if advisories:
        print(f"\nℹ️  Found {len(advisories)} Advisories:")
        for advisory in advisories:
            print(advisory)
    if errors:
        print(f"\n❌ Found {len(errors)} Critical Errors:")
        for e in errors:
            print(e)
        return False
    if strict_mode and warnings:
        print("\n❌ STRICT MODE: Failed due to warnings.")
        return False

    print("\n✨ All agents passed validation!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate agent definitions (AGENT.md)")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings (for CI)")
    parser.add_argument("--dir", default=None, help="Agents directory to validate (default: this skill's root directory)")
    args = parser.parse_args()

    agents_dir = args.dir or str(SKILL_ROOT)

    success = validate_agents(agents_dir, strict_mode=args.strict, explicit_dir=args.dir is not None)
    if not success:
        sys.exit(1)