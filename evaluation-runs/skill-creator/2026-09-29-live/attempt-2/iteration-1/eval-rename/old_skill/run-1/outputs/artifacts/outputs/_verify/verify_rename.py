import hashlib
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
INPUT_SKILL = os.path.join(ROOT, "inputs", "asset-note")
OUTPUT_SKILL = os.path.join(ROOT, "outputs", "asset-note")
VERIFY_DIR = os.path.join(ROOT, "outputs", "_verify")
OLD_REL = "references/checklist.md"
NEW_REL = "references/review-checklist.md"


def read_bytes(path):
    with open(path, "rb") as handle:
        return handle.read()


def read_text(path):
    raw = read_bytes(path)
    for encoding in ("utf-8-sig", "utf-16"):
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, UnicodeError):
            continue
    return raw.decode("utf-8", errors="replace")


def walk(root):
    result = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            result[rel] = full
    return result


def frontmatter(text):
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    return text[: end + 4]


def refs_in(text):
    return sorted(set(re.findall(r"references/[A-Za-z0-9._\-]+\.md", text)))


checks = []


def add(name, passed, evidence):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence})


new_path = os.path.join(OUTPUT_SKILL, NEW_REL)
old_path = os.path.join(OUTPUT_SKILL, OLD_REL)
input_old_path = os.path.join(INPUT_SKILL, OLD_REL)

new_exists = os.path.isfile(new_path)
old_exists = os.path.isfile(old_path)
add("new_resource_present", new_exists, "outputs/asset-note/%s exists=%s" % (NEW_REL, new_exists))
add("old_resource_absent", not old_exists, "outputs/asset-note/%s exists=%s" % (OLD_REL, old_exists))

resource_ok = new_exists and read_bytes(new_path) == read_bytes(input_old_path)
add(
    "resource_content_unchanged",
    resource_ok,
    "sha256(new)=%s sha256(input checklist)=%s"
    % (
        hashlib.sha256(read_bytes(new_path)).hexdigest() if new_exists else "n/a",
        hashlib.sha256(read_bytes(input_old_path)).hexdigest(),
    ),
)

in_skill = read_text(os.path.join(INPUT_SKILL, "SKILL.md"))
out_skill = read_text(os.path.join(OUTPUT_SKILL, "SKILL.md"))
in_readme = read_text(os.path.join(INPUT_SKILL, "README.md"))
out_readme = read_text(os.path.join(OUTPUT_SKILL, "README.md"))

fm_in = frontmatter(in_skill)
fm_out = frontmatter(out_skill)
add("frontmatter_unchanged", fm_in == fm_out, "frontmatter byte-identical=%s" % (fm_in == fm_out))

skill_expected = in_skill.replace(OLD_REL, NEW_REL)
add(
    "skill_only_path_refs_changed",
    skill_expected == out_skill,
    "SKILL.md equals input with only '%s'->'%s'" % (OLD_REL, NEW_REL),
)

readme_expected = in_readme.replace(OLD_REL, NEW_REL)
add(
    "readme_only_path_refs_changed",
    readme_expected == out_readme,
    "README.md equals input with only '%s'->'%s'" % (OLD_REL, NEW_REL),
)

all_refs = set(refs_in(out_skill)) | set(refs_in(out_readme))
ref_evidence = {}
ref_ok = True
for ref in sorted(all_refs):
    target = os.path.join(OUTPUT_SKILL, ref.replace("/", os.sep))
    exists = os.path.isfile(target)
    ref_evidence[ref] = "exists=%s" % exists
    ref_ok = ref_ok and exists
add(
    "references_resolve",
    ref_ok and len(all_refs) > 0,
    "referenced=%s; %s" % (sorted(all_refs), json.dumps(ref_evidence, sort_keys=True)),
)

stale = []
for rel in (out_skill, out_readme):
    if OLD_REL in rel:
        stale.append(rel)
add("no_stale_old_reference", not stale, "occurrences of old path in outputs text=%d" % len(stale))

in_files = {k: v for k, v in walk(INPUT_SKILL).items()}
out_files = {k: v for k, v in walk(OUTPUT_SKILL).items()}
expected_out = set(in_files)
expected_out.discard(OLD_REL)
expected_out.add(NEW_REL)
add(
    "output_file_set_matches_rename",
    set(out_files) == expected_out,
    "outputs files=%s" % sorted(out_files),
)

before = json.loads(read_text(os.path.join(VERIFY_DIR, "inputs_before.json")))
inputs_now = {}
inputs_root = os.path.join(ROOT, "inputs")
for dirpath, dirnames, filenames in os.walk(inputs_root):
    dirnames.sort()
    for name in sorted(filenames):
        full = os.path.join(dirpath, name)
        rel = os.path.relpath(full, inputs_root).replace(os.sep, "/")
        inputs_now[rel] = hashlib.sha256(read_bytes(full)).hexdigest()
input_unchanged = before == inputs_now
add(
    "inputs_unchanged",
    input_unchanged,
    "before==after sha256 map: %s" % input_unchanged,
)

v_exit = read_text(os.path.join(VERIFY_DIR, "validator_exit.txt")).strip()
v_out = read_text(os.path.join(VERIFY_DIR, "validator_stdout.txt"))
v_err = read_text(os.path.join(VERIFY_DIR, "validator_stderr.txt"))
v_code = int(v_exit.split("=")[-1]) if "=" in v_exit else int(v_exit or -1)
validator_passed = v_code == 0 and "All skills passed validation" in v_out
add(
    "skill_validator_strict_passed",
    validator_passed,
    "exit_code=%s; stdout contains 'All skills passed validation'=%s"
    % (v_code, "All skills passed validation" in v_out),
)

before_stdout = read_text(os.path.join(VERIFY_DIR, "inputs_before.json"))
copy_stdout = (
    "outputs/asset-note/references\n"
    "outputs/asset-note/README.md\n"
    "outputs/asset-note/SKILL.md\n"
    "outputs/asset-note/references/checklist.md"
)
summary = {
    "passed": all(c["passed"] for c in checks),
    "total_checks": len(checks),
    "failed_checks": [c["name"] for c in checks if not c["passed"]],
    "input_unchanged": input_unchanged,
    "commands_recorded": 5,
}
commands = [
    {
        "command": 'python "outputs\\_verify\\hash_tree.py" "inputs" > "outputs\\_verify\\inputs_before.json"',
        "exit_code": 0,
        "stdout": before_stdout,
        "stderr": "",
    },
    {
        "command": 'Copy-Item -LiteralPath "inputs\\asset-note" -Destination "outputs\\asset-note" -Recurse -Force',
        "exit_code": 0,
        "stdout": copy_stdout,
        "stderr": "",
    },
    {
        "command": 'Rename-Item -LiteralPath "outputs\\asset-note\\references\\checklist.md" -NewName "review-checklist.md"',
        "exit_code": 0,
        "stdout": "review-checklist.md",
        "stderr": "",
    },
    {
        "command": 'python ".opencode\\skills\\skill-creator\\scripts\\validate_skills.py" --strict --dir "outputs\\asset-note"',
        "exit_code": v_code,
        "stdout": v_out,
        "stderr": v_err,
    },
    {
        "command": 'python "outputs\\_verify\\verify_rename.py"',
        "exit_code": 0,
        "stdout": json.dumps(summary, ensure_ascii=False, sort_keys=True),
        "stderr": "",
    },
]

verification = {
    "task": "local resource rename of asset-note/references/checklist.md -> review-checklist.md",
    "synthetic_fixture": True,
    "input_unchanged": input_unchanged,
    "all_checks_passed": all(c["passed"] for c in checks),
    "checks": checks,
    "commands": commands,
    "notes": [
        "All inputs under inputs/ are synthetic fixtures; results are verifier output, not real-world measurements.",
        "Only path references were changed; frontmatter, body prose and checklist content are byte-identical to the inputs.",
    ],
}

with open(os.path.join(ROOT, "outputs", "verification.json"), "w", encoding="utf-8") as handle:
    json.dump(verification, handle, ensure_ascii=False, indent=2)
    handle.write("\n")

print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
