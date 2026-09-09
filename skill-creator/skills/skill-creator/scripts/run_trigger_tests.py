"""Trigger test runner: evaluate how reliably a skill's description would trigger.

Part of skill-creator tooling. Reads a trigger eval set (evals.json, see
templates/evals.json.template) and reports which prompts should trigger vs
not. It does NOT call an LLM — it performs a deterministic keyword/substring
match against the skill's description to give a fast signal, marking manual
verification as the authoritative step (see SKILL.md stage 7).

Usage:
    python scripts/run_trigger_tests.py <skill-dir> [--evals evals.json] [--json]

Exit code 0 = all evals classified; exits 1 if no evals file found.
"""

import argparse
import io
import json
import re
import sys
from pathlib import Path


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


def read_description(skill_dir: Path) -> str:
    skill_file = skill_dir / "SKILL.md"
    content = skill_file.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^description:\s*[\"']?(.*?)[\"']?\s*$", content, re.MULTILINE)
    return m.group(1) if m else ""


def keyword_tokens(text: str) -> list[str]:
    return re.findall(r"[\u4e00-\u9fff]+|[a-z0-9][a-z0-9-]*", text.lower())


def classify(prompt: str, description: str) -> bool:
    """Deterministic heuristic: does prompt share meaningful keywords with description?
    Returns True if more than one meaningful token overlaps.
    """
    tokens = keyword_tokens(description)
    stop = {"skill", "使用", "技能", "when", "use", "this", "user", "should", "the", "a"}
    meaningful = [t for t in tokens if t not in stop and len(t) >= 2]
    prompt_tokens = set(keyword_tokens(prompt))
    overlap = sum(1 for t in meaningful if t in prompt_tokens)
    return overlap >= 2


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Run trigger tests for a skill description")
    parser.add_argument("skill_dir", help="Skill directory containing SKILL.md")
    parser.add_argument("--evals", default=None, help="Eval set JSON (default: <skill-dir>/evals.json or <skill-dir>/evals/evals.json)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir)
    if not (skill_dir / "SKILL.md").exists():
        print(f"❌ No SKILL.md in {skill_dir}")
        return 1

    evals_path = None
    if args.evals:
        evals_path = Path(args.evals)
    else:
        for cand in (skill_dir / "evals.json", skill_dir / "evals" / "evals.json"):
            if cand.exists():
                evals_path = cand
                break
    if evals_path is None:
        print(
            "❌ No evals.json found. Create one from "
            "templates/evals.json.template (skill-creator 目录内)"
        )
        return 1

    try:
        data = json.loads(evals_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        print(f"❌ Cannot read evals file {evals_path}: {e}")
        return 1

    description = read_description(skill_dir)
    evals = data.get("evals", [])
    results = []
    tp = fp = tn = fn = 0
    for ev in evals:
        prompt = ev.get("prompt", "")
        should = bool(ev.get("should_trigger", True))
        predicted = classify(prompt, description)
        if should and predicted:
            tp += 1
        elif should and not predicted:
            fn += 1
        elif not should and predicted:
            fp += 1
        else:
            tn += 1
        results.append(
            {
                "id": ev.get("id"),
                "prompt": prompt,
                "should_trigger": should,
                "predicted": predicted,
                "match": predicted == should,
            }
        )

    total = len(evals)
    correct = tp + tn
    acc = correct / total if total else 0.0
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0

    if args.json:
        print(
            json.dumps(
                {
                    "skill": skill_dir.name,
                    "description": description,
                    "results": results,
                    "summary": {"accuracy": acc, "precision": precision, "recall": recall, "tp": tp, "fp": fp, "tn": tn, "fn": fn},
                    "note": "Heuristic keyword signal only; verdict must be confirmed by real client runs (stage 7).",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(f"🎯 Trigger tests for {skill_dir.name}")
    print(f"   description: {description[:100]}{'...' if len(description) > 100 else ''}")
    print(f"   evals: {evals_path}: {total} items\n")
    for r in results:
        mark = "✓" if r["match"] else "✗"
        should = "should" if r["should_trigger"] else "should-not"
        got = "triggers" if r["predicted"] else "silent"
        print(f"  {mark} [id {r['id']}] ({should} -> {got}): {r['prompt'][:80]}")
    print()
    print(f"📊 accuracy={acc:.0%} precision={precision:.0%} recall={recall:.0%} (tp={tp} fp={fp} tn={tn} fn={fn})")
    print("ℹ️  Heuristic signal only — confirm trigger behavior with a real client run (SKILL.md 阶段 7).")
    return 0


if __name__ == "__main__":
    sys.exit(main())