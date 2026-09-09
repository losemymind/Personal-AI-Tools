"""Validate skill directories (SKILL.md frontmatter/sections/security/links).

Part of the skill-creator skill (see SKILL.md).
Adapted from agentic-awesome-skills' tools/scripts/validate_skills.py.
Checks frontmatter schema, content triggers/examples/limitations,
security guardrails, dangling local links, and backtick resource
references (`references/x.md`, `scripts/x.py`, `templates/x`).
Supports both English and Chinese section headers.

Usage:
    python scripts/validate_skills.py [--dir <skills_dir>] [--strict]

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


def configure_utf8_output() -> None:
    """Best-effort UTF-8 stdout/stderr on Windows without dropping diagnostics."""
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


# Directories exempt from validation (upstream learning samples, not our outputs)
EXEMPT_DIRS = {"examples"}


def is_exempt_dir(path: str) -> bool:
    """Return True if any path segment is an exempted directory name."""
    parts = path.replace("\\", "/").split("/")
    return any(p in EXEMPT_DIRS for p in parts)


# English + Chinese "when to use" section headers (both accepted)
WHEN_TO_USE_PATTERNS = [
    re.compile(r"^##\s+When\s+to\s+Use", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+Use\s+this\s+skill\s+when", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+When\s+to\s+Use\s+This\s+Skill", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+When\s+to\s+activate\s+this\s+skill", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+何时使用(?:此|这|本)*技能", re.MULTILINE),
]

# English + Chinese "examples" and "limitations" section headers (both accepted)
EXAMPLES_PATTERNS = [
    re.compile(r"^##\s+Examples?", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+示例", re.MULTILINE),
]
LIMITATIONS_PATTERNS = [
    re.compile(r"^##\s+Limitations?", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+限制", re.MULTILINE),
]

SOURCE_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
VALID_SOURCE_TYPES = {"official", "community", "self"}
VALID_RISK_LEVELS = ["none", "safe", "critical", "offensive", "unknown"]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")  # semver x.y.z

SECURITY_DISCLAIMER_PATTERNS = [
    # English (exact, from agentic-awesome-skills)
    re.compile(
        r"> \*\*⚠️ AUTHORIZED USE ONLY\*\*\s*\n"
        r"> This skill is for educational purposes or authorized security assessments only\.\s*\n"
        r"> You must have explicit, written permission from the system owner before using this tool\.\s*\n"
        r"> Misuse of this tool is illegal and strictly prohibited\.",
    ),
    # Chinese equivalent (our convention)
    re.compile(
        r"> \*\*⚠️ 仅限授权使用\*\*\s*\n"
        r"> 此技能仅用于教育目的或授权的安全评估。\s*\n"
        r"> 在使用此工具之前，您必须获得系统所有者的明确书面许可。\s*\n"
        r"> 滥用此工具是非法的，严格禁止。",
    ),
]

OFFENSIVE_CONFIRMATION_PATTERNS = [
    re.compile(
        r"Mandatory confirmation gate[\s\S]{0,900}"
        r"exact target URL, IP, account, or resource[\s\S]{0,900}"
        r"Wait for explicit confirmation in the current conversation",
        re.IGNORECASE,
    ),
    re.compile(r"请求用户确认", re.IGNORECASE),
]


def has_when_to_use_section(content: str) -> bool:
    return any(pattern.search(content) for pattern in WHEN_TO_USE_PATTERNS)


def normalize_yaml_value(value):
    if isinstance(value, Mapping):
        return {key: normalize_yaml_value(val) for key, val in value.items()}
    if isinstance(value, list):
        return [normalize_yaml_value(item) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def parse_frontmatter(content: str):
    """Parse frontmatter using PyYAML. Returns (metadata, error_messages)."""
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
            elif desc == "|":
                fm_errors.append("description contains only the YAML block indicator '|', likely due to a parsing regression.")

        return dict(metadata), fm_errors
    except yaml.YAMLError as e:
        return None, [f"YAML Syntax Error: {e}"]


def collect_validation_results(skills_dir: str, strict_mode: bool = False) -> dict:
    # Normalize so `--dir .` (running inside an installed skill dir) resolves the
    # real folder name for the name-vs-folder check and stable relative paths.
    skills_dir = os.path.abspath(skills_dir)
    errors = []
    warnings = []
    advisories = []
    skill_count = 0

    for root, dirs, files in os.walk(skills_dir):
        # Skip hidden folders (e.g. .disabled) and exempt dirs (e.g. examples/)
        dirs[:] = [d for d in dirs if not d.startswith(".") and not is_exempt_dir(os.path.join(root, d))]

        if "SKILL.md" not in files:
            continue
        skill_count += 1
        skill_path = os.path.join(root, "SKILL.md")
        if os.path.islink(skill_path):
            warnings.append(f"⚠️  {os.path.relpath(skill_path, skills_dir)}: Skipping symlinked SKILL.md")
            continue
        rel_path = os.path.relpath(skill_path, skills_dir)

        try:
            with open(skill_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            errors.append(f"❌ {rel_path}: Unreadable file - {str(e)}")
            continue

        # 1. Frontmatter
        metadata, fm_errors = parse_frontmatter(content)
        if metadata is None:
            errors.append(f"❌ {rel_path}: Missing or malformed YAML frontmatter")
            continue
        for fe in fm_errors:
            errors.append(f"❌ {rel_path}: YAML Structure Error - {fe}")

        # 2. Metadata schema
        if "name" not in metadata:
            errors.append(f"❌ {rel_path}: Missing 'name' in frontmatter")
        elif metadata["name"] != os.path.basename(root):
            errors.append(f"❌ {rel_path}: Name '{metadata['name']}' does not match folder name '{os.path.basename(root)}'")

        if "description" not in metadata or metadata["description"] is None:
            errors.append(f"❌ {rel_path}: Missing 'description' in frontmatter")
        else:
            desc = metadata["description"]
            if not isinstance(desc, str):
                errors.append(f"❌ {rel_path}: 'description' must be a string, got {type(desc).__name__}")
            elif len(desc) > 1024:
                errors.append(f"❌ {rel_path}: Description is oversized ({len(desc)} chars). Max 1024.")
            else:
                # Trigger-surface discipline (see references/skill-writing-guide.md §6):
                # description is the only always-loaded field — keep it single-line and
                # free of angle-bracket placeholders so trigger matching stays reliable.
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

        if "risk" not in metadata:
            msg = f"⚠️  {rel_path}: Missing 'risk' label (defaulting to 'unknown')"
            (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)
        elif metadata["risk"] not in VALID_RISK_LEVELS:
            errors.append(f"❌ {rel_path}: Invalid risk level '{metadata['risk']}'. Must be one of {VALID_RISK_LEVELS}")

        if "source" not in metadata:
            msg = f"⚠️  {rel_path}: Missing 'source' attribution"
            (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)

        source_repo = metadata.get("source_repo")
        if source_repo is not None:
            if not isinstance(source_repo, str) or not SOURCE_REPO_PATTERN.fullmatch(source_repo.strip()):
                errors.append(f"❌ {rel_path}: Invalid 'source_repo' format. Must be OWNER/REPO, got '{source_repo}'")

        source_type = metadata.get("source_type")
        if source_type is not None:
            if not isinstance(source_type, str) or source_type not in VALID_SOURCE_TYPES:
                errors.append(f"❌ {rel_path}: Invalid 'source_type' value. Must be one of {sorted(VALID_SOURCE_TYPES)}")

        if "date_added" in metadata:
            date_added = metadata["date_added"]
            if not isinstance(date_added, str) or not DATE_PATTERN.match(date_added):
                errors.append(f"❌ {rel_path}: Invalid 'date_added' format. Must be YYYY-MM-DD (e.g., '2026-01-15'), got '{metadata['date_added']}'")
        else:
            advisories.append(f"ℹ️  {rel_path}: Missing 'date_added' field (optional, but recommended)")

        if "category" not in metadata:
            advisories.append(f"ℹ️  {rel_path}: Missing 'category' field (recommended)")

        if "version" in metadata:
            version = metadata["version"]
            if not isinstance(version, str) or not VERSION_PATTERN.match(version):
                errors.append(f"❌ {rel_path}: Invalid 'version' format. Must be semver x.y.z (e.g., '0.1.0'), got '{metadata['version']}'")
        elif metadata.get("name") != "skill-creator":
            advisories.append(f"ℹ️  {rel_path}: Missing 'version' field (recommended for lifecycle tracking)")

        # 3. Content checks (triggers)
        if not has_when_to_use_section(content):
            msg = f"⚠️  {rel_path}: Missing '## When to Use' or '## 何时使用此技能' section"
            (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)

        # 4. Content quality (examples + limitations per quality bar)
        if not any(p.search(content) for p in EXAMPLES_PATTERNS):
            msg = f"⚠️  {rel_path}: Missing '## Examples' or '## 示例' section (quality bar requires at least one copy-pasteable example)"
            (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)
        if not any(p.search(content) for p in LIMITATIONS_PATTERNS):
            msg = f"⚠️  {rel_path}: Missing '## Limitations' or '## 限制和注意事项' section (quality bar requires known limits)"
            (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)

        # 3b. Body length advisory (progressive disclosure) — NO failure, ever
        # Meta-skills (name == folder == "skill-creator" etc.) are exempt:
        # they must preserve full methodology, not squeeze into 1000 lines.
        if metadata.get("name") == "skill-creator":
            pass  # meta-skill exemption: line count is guidance, not a limit
        else:
            body_lines = content.count("\n") + 1
            if body_lines > 1000:
                advisories.append(f"ℹ️  {rel_path}: Body is {body_lines} lines (>1000). Consider moving details to references/ (guidance only, not a failure).")

        # 4. Security guardrails
        if metadata.get("risk") == "offensive":
            if not any(p.search(content) for p in SECURITY_DISCLAIMER_PATTERNS):
                errors.append(f"🚨 {rel_path}: OFFENSIVE SKILL MISSING THE EXACT AUTHORIZED-USE DISCLAIMER")
            if not any(p.search(content) for p in OFFENSIVE_CONFIRMATION_PATTERNS):
                errors.append(f"🚨 {rel_path}: OFFENSIVE SKILL MISSING THE MANDATORY PER-ACTION CONFIRMATION GATE")

# 5. Dangling links (markdown links)
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

        # 5b. Backtick path references (`references/xxx.md`, `scripts/xxx.py`, `templates/xxx`)
        # These are the convention used by progressive-disclosure skills (SKILL.md points to
        # on-disk resources with backticks, not markdown links). Keep them resolvable.
        # Exclude references that appear inside fenced code blocks (examples/demos show
        # illustrative paths that are not meant to resolve on disk).
        fenced_ranges = [m.span() for m in re.finditer(r"```.*?```", content, re.DOTALL)]

        def _is_in_fence(pos: int) -> bool:
            return any(s <= pos < e for s, e in fenced_ranges)

        backtick_refs = set()
        for m in re.finditer(r"`([^`\s]+\.(?:md|py|sh|json|yaml|yml|ts|js))`", content):
            ref = m.group(1)
            if ref.startswith("http") or "/" not in ref:
                continue
            if _is_in_fence(m.start()):
                continue
            backtick_refs.add(ref)
        for ref in sorted(backtick_refs):
            ref_clean = ref.split("#")[0].strip()
            # Skip placeholders/globs (e.g. <name>, **/SKILL.md, xxx.md, ~/...)
            if (
                not ref_clean
                or ref_clean.startswith("~/")
                or any(ch in ref_clean for ch in ("<", ">", "*", "?", "…"))
                or "xxx" in ref_clean
                or "your-skill-name" in ref_clean
            ):
                continue
            if os.path.isabs(ref_clean):
                continue
            # Resolve relative to the skill dir first, then fall back to the repo root
            # (covers both `references/x.md` and `<skill-dir>/references/x.md` forms).
            targets = [
                os.path.normpath(os.path.join(root, ref_clean)),
                os.path.normpath(os.path.join(SKILL_ROOT, ref_clean)),
            ]
            # Module-style self-references (`<own-folder>/...`) must also resolve once
            # the skill is installed outside the repo (e.g. ~/.config/opencode/skills/):
            # strip the leading segment that matches the skill's own folder name.
            parts = ref_clean.split("/")
            if len(parts) > 1 and parts[0] == os.path.basename(root):
                targets.append(os.path.normpath(os.path.join(root, *parts[1:])))
            if not any(os.path.exists(t) for t in targets):
                errors.append(f"❌ {rel_path}: Backtick reference '{ref_clean}' does not exist locally.")

    return {
        "skill_count": skill_count,
        "warnings": warnings,
        "advisories": advisories,
        "errors": errors,
        "strict_mode": strict_mode,
    }


def validate_skills(skills_dir: str, strict_mode: bool = False) -> bool:
    configure_utf8_output()

    print(f"🔍 Validating skills in: {skills_dir}")
    print(f"⚙️  Mode: {'STRICT (CI)' if strict_mode else 'Standard (Dev)'}")

    results = collect_validation_results(skills_dir, strict_mode=strict_mode)
    warnings = results["warnings"]
    advisories = results["advisories"]
    errors = results["errors"]
    skill_count = results["skill_count"]

    print(f"\n📊 Checked {skill_count} skills.")

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

    print("\n✨ All skills passed validation!")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate skill directories (SKILL.md frontmatter/sections/security/links)")
    parser.add_argument("--strict", action="store_true", help="Fail on warnings (for CI)")
    parser.add_argument("--dir", default=None, help="Skills directory to validate (default: this skill's root directory)")
    args = parser.parse_args()

    skills_dir = args.dir or str(SKILL_ROOT)

    success = validate_skills(skills_dir, strict_mode=args.strict)
    if not success:
        sys.exit(1)