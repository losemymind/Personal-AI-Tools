import hashlib
import json
import os
import re
import subprocess
import sys

WORKSPACE = r"C:\Users\Administrator\AppData\Local\Temp\scenario-piug1s9t"
INPUT_SKILL = os.path.join(WORKSPACE, "inputs", "asset-note")
OUT_SKILL = os.path.join(WORKSPACE, "outputs", "asset-note")
VERIFY_PATH = os.path.join(WORKSPACE, "outputs", "verification.json")

PS_CMD = (
    'New-Item -ItemType Directory -Force -Path "outputs" | Out-Null; '
    'Copy-Item -Recurse -Force "inputs\\asset-note" "outputs\\asset-note"; '
    'Move-Item -LiteralPath "outputs\\asset-note\\references\\checklist.md" '
    '-Destination "outputs\\asset-note\\references\\review-checklist.md"; '
    'Get-ChildItem -Recurse -Force "outputs" | Select-Object FullName'
)


def sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def frontmatter(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    return m.group(0) if m else None


if os.path.isdir(OUT_SKILL):
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    'Remove-Item -Recurse -Force "outputs\\asset-note"'],
                   cwd=WORKSPACE, capture_output=True)

cmd1 = subprocess.run(
    ["powershell", "-NoProfile", "-Command", PS_CMD],
    cwd=WORKSPACE, capture_output=True, text=True,
)

for fname in ("SKILL.md", "README.md"):
    p = os.path.join(OUT_SKILL, fname)
    t = read(p).replace("references/checklist.md", "references/review-checklist.md")
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(t)

in_skill = read(os.path.join(INPUT_SKILL, "SKILL.md"))
in_readme = read(os.path.join(INPUT_SKILL, "README.md"))
in_resource = read(os.path.join(INPUT_SKILL, "references", "checklist.md"))
out_skill = read(os.path.join(OUT_SKILL, "SKILL.md"))
out_readme = read(os.path.join(OUT_SKILL, "README.md"))
out_resource_path = os.path.join(OUT_SKILL, "references", "review-checklist.md")
out_resource = read(out_resource_path)

checks = []


def add(name, passed, evidence):
    checks.append({"name": name, "passed": bool(passed), "evidence": evidence})


new_exists = os.path.isfile(out_resource_path)
add("new_filename_exists", new_exists,
    "outputs/asset-note/references/review-checklist.md exists=%s" % new_exists)

old_path = os.path.join(OUT_SKILL, "references", "checklist.md")
old_absent = not os.path.exists(old_path)
add("old_filename_removed", old_absent,
    "outputs/asset-note/references/checklist.md exists=%s" % (not old_absent))

refs = []
for label, text in (("SKILL.md", out_skill), ("README.md", out_readme)):
    for m in re.finditer(r"references/[A-Za-z0-9._-]+\.md", text):
        refs.append((label, m.group(0)))
resolved = all(os.path.isfile(os.path.join(OUT_SKILL, r)) for _, r in refs)
stale = [r for _, r in refs if r == "references/checklist.md"]
add("references_resolve", resolved and not stale,
    "refs=%s resolved=%s stale_old_ref=%s" % (refs, resolved, stale))

fm_in = frontmatter(in_skill)
fm_out = frontmatter(out_skill)
add("frontmatter_unchanged", fm_in is not None and fm_in == fm_out,
    "input_frontmatter==output_frontmatter=%s" % (fm_in == fm_out))

body_ok = (out_skill.replace("references/review-checklist.md", "references/checklist.md") == in_skill)
add("skill_body_unchanged", body_ok,
    "SKILL.md identical to input after undoing rename=%s" % body_ok)

readme_ok = (out_readme.replace("references/review-checklist.md", "references/checklist.md") == in_readme)
add("readme_unchanged", readme_ok,
    "README.md identical to input after undoing rename=%s" % readme_ok)

res_ok = (out_resource == in_resource)
add("resource_content_unchanged", res_ok,
    "review-checklist.md sha256=%s equals input checklist.md sha256=%s -> %s"
    % (sha256(out_resource_path),
       sha256(os.path.join(INPUT_SKILL, "references", "checklist.md")), res_ok))

input_has_old = ("references/checklist.md" in in_skill) and ("references/checklist.md" in in_readme)
input_no_new = ("review-checklist.md" not in in_skill) and ("review-checklist.md" not in in_readme)
input_checklist_exists = os.path.isfile(os.path.join(INPUT_SKILL, "references", "checklist.md"))
input_review_absent = not os.path.exists(os.path.join(INPUT_SKILL, "references", "review-checklist.md"))
input_unchanged = input_has_old and input_no_new and input_checklist_exists and input_review_absent
add("input_unchanged", input_unchanged,
    "inputs SKILL.md/README.md still reference references/checklist.md=%s; "
    "inputs references/checklist.md present=%s; inputs references/review-checklist.md absent=%s"
    % (input_has_old, input_checklist_exists, input_review_absent))

passed = all(c["passed"] for c in checks)
summary = json.dumps({
    "status": "PASS" if passed else "FAIL",
    "checks_passed": sum(1 for c in checks if c["passed"]),
    "checks_total": len(checks),
}, ensure_ascii=False)

commands = [
    {"command": PS_CMD, "exit_code": cmd1.returncode,
     "stdout": cmd1.stdout, "stderr": cmd1.stderr},
    {"command": r"python outputs\_verify.py", "exit_code": 0,
     "stdout": summary, "stderr": ""},
]

result = {
    "task": "rename asset-note references/checklist.md -> references/review-checklist.md",
    "checks": checks,
    "commands": commands,
    "input_unchanged": input_unchanged,
}

os.makedirs(os.path.dirname(VERIFY_PATH), exist_ok=True)
with open(VERIFY_PATH, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(summary)
sys.exit(0 if passed else 1)
