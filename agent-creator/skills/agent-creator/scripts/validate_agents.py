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

# Skill root = the directory containing scripts/ (self-contained; the module
# never depends on a host repository). Used as the fallback base for backtick
# references and as the default scan target.
SKILL_ROOT = find_skill_root(__file__)
# Doc/resource dirs that must never be scanned as agent definitions
EXEMPT_DIRS = {"examples", "references", "templates"}

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


def collect_validation_results(agents_dir: str, strict_mode: bool = False) -> dict:
    errors = []
    warnings = []
    advisories = []
    agent_count = 0

    for root, dirs, files in os.walk(agents_dir):
        dirs[:] = [d for d in dirs if not d.startswith(".") and not is_exempt_dir(os.path.join(root, d))]
        # Agent definition files: AGENT.md inside a dir, or a top-level *.md
        if "AGENT.md" in files:
            candidates = [(root, "AGENT.md")]
        else:
            mds = sorted(
                f
                for f in files
                if f.endswith(".md")
                and f.lower()
                not in (
                    "readme.md",
                    "readme",
                    "changelog.md",
                    "development-plan.md",
                    "agents.md",
                    "skill.md",
                    "catalog.md",
                    "catalog",
                    "agents-audit.md",
                )
            )
            candidates = [(root, f) for f in mds]
        for base, fname in candidates:
            agent_count += 1
            agent_path = os.path.join(base, fname)
            rel_path = os.path.relpath(agent_path, agents_dir)
            try:
                with open(agent_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                errors.append(f"❌ {rel_path}: Unreadable file - {str(e)}")
                continue

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

            links = re.findall(r"\[[^\]]*\]\(([^)]+)\)", content)
            for link in links:
                link_clean = link.split("#")[0].strip()
                if not link_clean or link_clean.startswith(("http://", "https://", "mailto:", "<", ">")):
                    continue
                if os.path.isabs(link_clean):
                    continue
                target_path = os.path.normpath(os.path.join(root, link_clean))
                if not os.path.exists(target_path):
                    errors.append(f"❌ {rel_path}: Dangling link detected. Path '{link_clean}' does not exist locally.")

            backtick_refs = set(
                m
                for m in re.findall(r"`([^`\s]+\.(?:md|py|sh|json|yaml|yml|ts|js))`", content)
                if not m.startswith("http") and "/" in m
            )
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
                targets = [
                    os.path.normpath(os.path.join(root, ref_clean)),
                    os.path.normpath(os.path.join(SKILL_ROOT, ref_clean)),
                ]
                if not any(os.path.exists(t) for t in targets):
                    errors.append(f"❌ {rel_path}: Backtick reference '{ref_clean}' does not exist locally.")

    return {
        "agent_count": agent_count,
        "warnings": warnings,
        "advisories": advisories,
        "errors": errors,
        "strict_mode": strict_mode,
    }


def validate_agents(agents_dir: str, strict_mode: bool = False) -> bool:
    configure_utf8_output()
    print(f"🔍 Validating agents in: {agents_dir}")
    print(f"⚙️  Mode: {'STRICT (CI)' if strict_mode else 'Standard (Dev)'}")

    results = collect_validation_results(agents_dir, strict_mode=strict_mode)
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

    success = validate_agents(agents_dir, strict_mode=args.strict)
    if not success:
        sys.exit(1)