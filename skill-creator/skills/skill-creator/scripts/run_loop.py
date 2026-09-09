#!/usr/bin/env python3
"""Run the description auto-optimization loop for a skill.

Port from Anthropic's official anthropics/skills skill-creator
(run_loop.py), kept client-agnostic:

  - Stratified 60/40 train/test split over the eval set (by should_trigger).
  - Each iteration evaluates the current description (heuristic mode by
    default) and requests an improved description via an LLM improve prompt.
    --improve-mode manual prints the prompt and reads a human/pasted reply;
    --improve-mode cli shells out to a client CLI (default `claude -p`).
  - Best description is selected by TEST score to avoid overfitting train.

Usage:
    python scripts/run_loop.py --eval-set <evals.json> --skill-dir <skill> \
        [--holdout 0.4] [--max-iterations 5] [--improve-mode manual|cli] \
        [--client claude] [--seed 42] [--report <out.json>]

Reads the eval set via run_eval's heuristic (no external CLI needed for
evaluation). Exit code 0 = loop completed.
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from utils import parse_skill_md
from run_eval import run_heuristic, summarize

SCRIPT_DIR = Path(__file__).resolve().parent


def configure_utf8_output() -> None:
    if sys.platform != "win32":
        return
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if not stream:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="backslashreplace")
        except Exception:
            pass


def split_eval_set(eval_items: list[dict], holdout: float, seed: int = 42) -> tuple[list[dict], list[dict]]:
    """Stratified split: separate should-trigger / should-not-trigger, shuffle, split each by holdout."""
    random.seed(seed)
    trigger = [e for e in eval_items if e.get("should_trigger")]
    no_trigger = [e for e in eval_items if not e.get("should_trigger")]
    random.shuffle(trigger)
    random.shuffle(no_trigger)
    n_t_test = max(1, int(len(trigger) * holdout)) if trigger else 0
    n_nt_test = max(1, int(len(no_trigger) * holdout)) if no_trigger else 0
    test = trigger[:n_t_test] + no_trigger[:n_nt_test]
    train = trigger[n_t_test:] + no_trigger[n_nt_test:]
    return train, test


def build_improve_prompt(
    skill_name: str,
    skill_content: str,
    current_description: str,
    train_results: list[dict],
) -> str:
    failed = [r for r in train_results if r["should_trigger"] and not r["pass"]]
    false_positive = [r for r in train_results if not r["should_trigger"] and not r["pass"]]
    passed = sum(1 for r in train_results if r["pass"])
    total = len(train_results)

    def lines(items: list[dict]) -> str:
        return "\n".join(f'- "{r["query"]}"' for r in items) or "(none)"

    return f"""You are optimizing the description of the skill "{skill_name}".

The description is the ONLY thing an LLM client sees when deciding whether to
trigger the skill. Goal: trigger for relevant queries, stay silent for
irrelevant ones.

Current description:
<current_description>
"{current_description}"
</current_description>

Train score: {passed}/{total} correct on the training set.

FAILED TO TRIGGER (should trigger, but didn't):
{lines(failed)}

FALSE TRIGGERS (triggered, but shouldn't have):
{lines(false_positive)}

Skill body (context of what the skill does):
<skill_body>
{skill_content[:4000]}
</skill_body>

Write a new, improved description. Generalize from the failures to broader
categories of user intent — do NOT grow an ever-expanding list of specific
queries, and do NOT overfit to these examples. Keep it imperative: "Use this
skill for …". Stay under {1024} characters.

Respond with ONLY the new description text inside <new_description> tags.
"""


def call_improver_cli(prompt: str, client: str, timeout: int = 300) -> str:
    """Shell out to a client's headless CLI to improve the description."""
    cmd_map = {"claude": ["claude", "-p", "--output-format", "text"]}
    if client not in cmd_map:
        raise RuntimeError(f"--improve-mode cli not available for client '{client}'")
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    try:
        proc = subprocess.run(cmd_map[client], input=prompt, capture_output=True, text=True, env=env, timeout=timeout)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        raise RuntimeError(f"improver CLI failed: {e}") from e
    if proc.returncode != 0:
        raise RuntimeError(f"improver CLI exited {proc.returncode}: {proc.stderr[-500:]}")
    text = proc.stdout
    m = re.search(r"<new_description>(.*?)</new_description>", text, re.DOTALL)
    desc = m.group(1).strip().strip('"') if m else text.strip().strip('"')
    if len(desc) > 1024:
        raise RuntimeError("improver output exceeded 1024 chars; rerun with --improve-mode manual")
    return desc


def call_improver_manual(prompt: str) -> str:
    print("\n=== IMPROVEMENT PROMPT (paste reply below; end with a line containing exactly EOF) ===\n", file=sys.stderr)
    print(prompt)
    print("\n=== END PROMPT ===\n", file=sys.stderr)
    lines = []
    for line in sys.stdin:
        if line.strip() == "EOF":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Run description auto-optimization loop")
    parser.add_argument("--eval-set", required=True, help="Path to evals.json")
    parser.add_argument("--skill-dir", required=True, help="Path to skill directory containing SKILL.md")
    parser.add_argument("--holdout", type=float, default=0.4, help="Fraction held out for test set (default 0.4)")
    parser.add_argument("--max-iterations", type=int, default=5, help="Max improvement iterations")
    parser.add_argument("--improve-mode", choices=["manual", "cli"], default="manual",
                        help="manual=print prompt & read pasted reply (default), cli=headless client CLI")
    parser.add_argument("--client", default="claude", help="CLI client for --improve-mode cli")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for train/test split")
    parser.add_argument("--report", type=Path, help="Write final JSON iteration log here")
    args = parser.parse_args()

    eval_set_path = Path(args.eval_set)
    skill_dir = Path(args.skill_dir)
    if not eval_set_path.exists():
        print(f"Error: eval set not found: {eval_set_path}", file=sys.stderr)
        return 1
    if not (skill_dir / "SKILL.md").exists():
        print(f"Error: no SKILL.md at {skill_dir}", file=sys.stderr)
        return 1

    evals = json.loads(eval_set_path.read_text(encoding="utf-8-sig"))
    eval_items = evals.get("evals", evals) if isinstance(evals, dict) else evals
    name, original_description, content = parse_skill_md(skill_dir)

    train, test = split_eval_set(eval_items, args.holdout, seed=args.seed)
    if not train:
        print("Error: empty train set after split", file=sys.stderr)
        return 1

    history = []
    current = original_description
    exit_reason = f"max_iterations ({args.max_iterations})"

    for iteration in range(1, args.max_iterations + 1):
        print(f"Iteration {iteration}/{args.max_iterations}", file=sys.stderr)
        train_results = run_heuristic(train, current)
        test_results = run_heuristic(test, current) if test else []
        train_sum = summarize(train_results)
        test_sum = summarize(test_results) if test else {"passed": 0, "failed": 0, "total": 0}
        history.append({
            "iteration": iteration,
            "description": current,
            "train_passed": train_sum["passed"],
            "train_total": train_sum["total"],
            "test_passed": test_sum["passed"],
            "test_total": test_sum["total"],
            "train_results": train_results,
        })
        print(f"  train {train_sum['passed']}/{train_sum['total']} | "
              f"test {test_sum['passed']}/{test_sum['total']}", file=sys.stderr)

        if train_sum["failed"] == 0:
            exit_reason = f"all_passed (iteration {iteration})"
            break

        prompt = build_improve_prompt(name, content, current, train_results)
        try:
            if args.improve_mode == "cli":
                current = call_improver_cli(prompt, args.client)
            else:
                current = call_improver_manual(prompt)
        except RuntimeError as e:
            print(f"Improver failed: {e}", file=sys.stderr)
            exit_reason = f"improver_error (iteration {iteration})"
            break

    best = max(history, key=lambda h: h["test_passed"])
    output = {
        "skill_name": name,
        "original_description": original_description,
        "best_description": best["description"],
        "best_score": f"{best['test_passed']}/{best['test_total']}",
        "iterations_run": len(history),
        "exit_reason": exit_reason,
        "holdout": args.holdout,
        "history": history,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if args.report:
        args.report.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Report written: {args.report}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())