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
import json
import os
import re
import sys

from _project_paths import find_skill_root
from utils import (
    has_examples_section,
    has_limitations_section,
    has_when_to_use_section,
    parse_frontmatter,
)

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


# Section-header patterns live in utils.py (single source of truth shared with
# compare_skills.py, so the validator and the scorer never disagree).

SOURCE_REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
VALID_SOURCE_TYPES = {"official", "community", "self"}
VALID_RISK_LEVELS = ["none", "safe", "critical", "offensive", "unknown"]
VALID_TOOLS = {"claude", "opencode", "codex", "deepseek"}
NAME_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")  # lowercase kebab-case
NAME_MAX_LEN = 100
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")  # semver x.y.z

# Backtick resource references that must resolve on disk. Extension whitelist keeps
# the check from flagging non-path tokens (prose, command fragments); it is broader
# than the script types so data/text artifacts (`indexes/upstream.db`, `.txt`, …)
# are covered too. Files inside fenced code blocks are exempt.
BACKTICK_REF_RE = re.compile(
    r"`([^`\s]+\.(?:md|py|sh|json|ya?ml|toml|txt|xml|db|sqlite|csv|ts|tsx|js|jsx|mjs|cjs|css|html|rs|go|java|rb|php))`"
)

# evals.json prompt key: `query` is canonical (utils.eval_query); `prompt` is the
# accepted legacy fallback (references/benchmark-schema.md).
EVAL_QUERY_KEYS = ("query", "prompt")

# Dangerous remote-execution pipes (quality bar item 6 / SKILL.md safety guardrails)
DANGEROUS_PIPE_PATTERNS = [
    re.compile(r"\b(curl|wget)\b[^\n]*\|\s*(?:sudo\s+)?(?:ba|z|k)?sh\b", re.IGNORECASE),
    re.compile(r"\birm\b[^\n]*\|\s*iex\b", re.IGNORECASE),
]
SECRET_ALLOWLIST_RE = re.compile(r"<!--\s*security-allowlist", re.IGNORECASE)
# Obvious inline credentials (kept deliberately narrow to avoid false positives)
SECRET_PATTERNS = [
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
]

# Offensive-skill disclaimer: accept either language, tolerant of whitespace/format,
# but require BOTH the "authorized use only" banner and a permission/consent clause.
SECURITY_DISCLAIMER_PATTERNS = [
    # English
    re.compile(
        r"AUTHORIZED\s+USE\s+ONLY[\s\S]{0,400}?permission",
        re.IGNORECASE,
    ),
    # Chinese equivalent (our convention)
    re.compile(
        r"仅限授权使用[\s\S]{0,400}?(?:许可|授权|同意)",
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


def check_evals_file(evals_path: str, rel_path: str) -> list[str]:
    """Validate an evals.json's shape when the skill ships one.

    Presence is only an advisory (quality bar item 8: trigger tests should ship
    with the skill), but a *present* file is a contract: it must parse and carry
    the canonical `query` + boolean `should_trigger` per item, so the historical
    key drift (a `prompt`-only or malformed eval set) cannot recur silently.
    """
    errs: list[str] = []
    try:
        with open(evals_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return [f"❌ {rel_path}: evals file invalid JSON ({os.path.basename(evals_path)}): {e}"]
    items = data.get("evals", data) if isinstance(data, dict) else data
    if not isinstance(items, list):
        return [f"❌ {rel_path}: evals file must be an object with an 'evals' array (or a bare array)."]
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            errs.append(f"❌ {rel_path}: evals[{i}] must be an object.")
            continue
        if not any(isinstance(item.get(k), str) and item.get(k).strip() for k in EVAL_QUERY_KEYS):
            errs.append(f"❌ {rel_path}: evals[{i}] missing a non-empty 'query' (canonical prompt key).")
        if not isinstance(item.get("should_trigger"), bool):
            errs.append(f"❌ {rel_path}: evals[{i}].should_trigger must be a boolean.")
    return errs


def collect_validation_results(skills_dir: str, strict_mode: bool = False) -> dict:
    # Normalize so `--dir .` (running inside an installed skill dir) resolves the
    # real folder name for the name-vs-folder check and stable relative paths.
    skills_dir = os.path.abspath(skills_dir)
    errors = []
    if not os.path.isdir(skills_dir):
        # A wrong/typo'd --dir must FAIL loudly. os.walk on a missing path yields
        # nothing, so without this guard we'd print "Checked 0 skills" and exit 0.
        errors.append(f"❌ Scan directory does not exist: {skills_dir}")
        return {
            "skill_count": 0,
            "warnings": [],
            "advisories": [],
            "errors": errors,
            "strict_mode": strict_mode,
        }
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
            with open(skill_path, "r", encoding="utf-8-sig") as f:
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
        else:
            name_val = metadata["name"]
            if name_val != os.path.basename(root):
                errors.append(f"❌ {rel_path}: Name '{name_val}' does not match folder name '{os.path.basename(root)}'")
            if isinstance(name_val, str) and not NAME_PATTERN.fullmatch(name_val):
                errors.append(
                    f"❌ {rel_path}: Name must be lowercase kebab-case "
                    f"(a-z, 0-9, single hyphens), got '{name_val}'"
                )
            if isinstance(name_val, str) and len(name_val) > NAME_MAX_LEN:
                errors.append(f"❌ {rel_path}: Name is too long ({len(name_val)} chars). Max {NAME_MAX_LEN}.")

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
        elif metadata["risk"] == "unknown":
            advisories.append(
                f"ℹ️  {rel_path}: risk 'unknown' is discouraged for new skills (see quality bar item 3)."
            )

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

        # 2b. Optional advisory metadata (tags/tools/category shape)
        tags = metadata.get("tags")
        if tags is not None:
            if not isinstance(tags, list):
                errors.append(f"❌ {rel_path}: 'tags' must be a YAML list, got {type(tags).__name__}")
            elif len(tags) > 5:
                advisories.append(f"ℹ️  {rel_path}: {len(tags)} tags declared (>5); keep tags focused (≤5).")

        tools = metadata.get("tools")
        if tools is not None:
            if not isinstance(tools, list):
                errors.append(f"❌ {rel_path}: 'tools' must be a YAML list, got {type(tools).__name__}")
            else:
                unknown = [t for t in tools if isinstance(t, str) and t.lower() not in VALID_TOOLS]
                if unknown:
                    advisories.append(
                        f"ℹ️  {rel_path}: Unknown client tool(s) {unknown}; "
                        f"known values: {sorted(VALID_TOOLS)}."
                    )

        # 3. Content checks (triggers)
        if not has_when_to_use_section(content):
            msg = f"⚠️  {rel_path}: Missing '## When to Use' or '## 何时使用此技能' section"
            (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)

        # 4. Content quality (examples + limitations per quality bar)
        if not has_examples_section(content):
            msg = f"⚠️  {rel_path}: Missing '## Examples' or '## 示例' section (quality bar requires at least one copy-pasteable example)"
            (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)
        if not has_limitations_section(content):
            msg = f"⚠️  {rel_path}: Missing '## Limitations' or '## 限制和注意事项' section (quality bar requires known limits)"
            (errors if strict_mode else warnings).append(msg.replace("⚠️", "❌") if strict_mode else msg)

        # 4b. Security scan: dangerous pipes + inline secrets (quality bar item 6).
        # `<!-- security-allowlist -->` marks a reviewed exception.
        if not SECRET_ALLOWLIST_RE.search(content):
            for pattern in DANGEROUS_PIPE_PATTERNS:
                if pattern.search(content):
                    errors.append(
                        f"🚨 {rel_path}: Dangerous remote-execution pipe detected "
                        f"({pattern.pattern!r}); remove it or add a `<!-- security-allowlist -->` note."
                    )
            for pattern in SECRET_PATTERNS:
                m = pattern.search(content)
                if m:
                    errors.append(
                        f"🚨 {rel_path}: Possible inline secret/credential detected "
                        f"({m.group(0)[:6]}…); remove it or add a `<!-- security-allowlist -->` note."
                    )

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
        for m in BACKTICK_REF_RE.finditer(content):
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
            # Resolve relative to the skill's own directory only. Falling back to
            # this validator's own SKILL_ROOT would let an external skill "borrow"
            # a path that only exists inside skill-creator — a false pass that
            # hides dangling references in other skill libraries.
            targets = [os.path.normpath(os.path.join(root, ref_clean))]
            # Module-style self-references (`<own-folder>/...`) must also resolve once
            # the skill is installed outside the repo (e.g. ~/.config/opencode/skills/):
            # strip the leading segment that matches the skill's own folder name.
            parts = ref_clean.split("/")
            if len(parts) > 1 and parts[0] == os.path.basename(root):
                targets.append(os.path.normpath(os.path.join(root, *parts[1:])))
            if not any(os.path.exists(t) for t in targets):
                errors.append(f"❌ {rel_path}: Backtick reference '{ref_clean}' does not exist locally.")

        # 6. evals.json (quality bar item 8): present -> enforce shape; absent -> advise.
        evals_file = None
        for cand in (os.path.join(root, "evals", "evals.json"), os.path.join(root, "evals.json")):
            if os.path.exists(cand):
                evals_file = cand
                break
        if evals_file is not None:
            errors.extend(check_evals_file(evals_file, rel_path))
        else:
            advisories.append(
                f"ℹ️  {rel_path}: No evals.json found (recommended: ship trigger tests with the skill)."
            )

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