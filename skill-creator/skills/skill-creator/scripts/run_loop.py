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
  - The improve prompt injects the best-so-far description (highest test
    score in the run) as a few-shot gold-standard precedent, so each round
    improves on validated wording instead of inventing from scratch.

Usage:
    python scripts/run_loop.py --eval-set <evals.json> --skill-dir <skill> \
        [--holdout 0.4] [--max-iterations 5] [--improve-mode manual|cli] \
        [--client claude] [--seed 42] [--report <out.json>]

Reads the eval set via run_eval's heuristic (no external CLI needed for
evaluation). Exit code 0 = loop completed.
"""

import argparse
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from utils import load_eval_set, parse_skill_md, run_client
from run_eval import run_heuristic, summarize
from run_scenario import extract_text

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


def _split_count(n: int, holdout: float) -> int:
    """Number of items to hold out, keeping at least one item on each side.

    A bare `max(1, ...)` steals a lone item into test and empties train (or vice
    versa); keep both splits non-empty whenever n >= 2.
    """
    if n < 2 or not math.isfinite(holdout) or not (0.0 <= holdout <= 1.0):
        return 0
    k = int(round(n * holdout))
    return min(max(k, 1), n - 1)


def split_eval_set(eval_items: list[dict], holdout: float, seed: int = 42) -> tuple[list[dict], list[dict]]:
    """Stratified split: separate should-trigger / should-not-trigger, shuffle, split each by holdout."""
    random.seed(seed)
    trigger = [e for e in eval_items if e.get("should_trigger")]
    no_trigger = [e for e in eval_items if not e.get("should_trigger")]
    random.shuffle(trigger)
    random.shuffle(no_trigger)
    n_t_test = _split_count(len(trigger), holdout)
    n_nt_test = _split_count(len(no_trigger), holdout)
    test = trigger[:n_t_test] + no_trigger[:n_nt_test]
    train = trigger[n_t_test:] + no_trigger[n_nt_test:]
    return train, test


def _test_rank(entry: dict) -> tuple[float, int]:
    """Rank key for best-description selection: test pass rate, then passed count.

    Selecting by rate (not the raw passed count) keeps iterations with different
    test-set sizes comparable; ties fall back to the raw passed count so the
    earlier, equal-scoring iteration is not silently preferred on a size artifact.
    """
    total = entry.get("test_total", 0)
    rate = entry["test_passed"] / total if total else 0.0
    return (rate, entry["test_passed"])


def build_improve_prompt(
    skill_name: str,
    skill_content: str,
    current_description: str,
    train_results: list[dict],
    best_so_far: str = "",
) -> str:
    failed = [r for r in train_results if r["should_trigger"] and not r["pass"]]
    false_positive = [r for r in train_results if not r["should_trigger"] and not r["pass"]]
    passed = sum(1 for r in train_results if r["pass"])
    total = len(train_results)

    def lines(items: list[dict]) -> str:
        return "\n".join(f'- "{r["query"]}"' for r in items) or "(none)"

    # Gold-standard precedent: the best description seen so far (by test score) is
    # a few-shot guide — "pick a better wording from a validated one", not invent
    # from scratch each round. Mirrors the antongulin gold-standards mechanism.
    precedent_block = ""
    if best_so_far and best_so_far != current_description:
        precedent_block = (
            "\nBest description so far (highest test score in this run) — treat it as a\n"
            "few-shot precedent and improve on this wording instead of starting from scratch:\n"
            "<best_so_far>\n"
            f'"{best_so_far}"\n'
            "</best_so_far>\n"
        )

    return f"""You are optimizing the description of the skill "{skill_name}".

The description is the ONLY thing an LLM client sees when deciding whether to
trigger the skill. Goal: trigger for relevant queries, stay silent for
irrelevant ones.

Current description:
<current_description>
"{current_description}"
</current_description>
{precedent_block}
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


def call_improver_cli(prompt: str, client: str, timeout: int = 300, model: str = "") -> str:
    """Shell out to a client's headless CLI to improve the description.

    Runs in a throwaway workspace (a triggered improver call must not execute the
    skill or write into the caller's repo) and kills the process tree on timeout.
    --model is appended only when given (a client whose default model is unset or
    misconfigured needs it, else the improver call fails).
    """
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    tmp = Path(tempfile.mkdtemp(prefix="improver-"))
    try:
        if client == "claude":
            # claude -p reads the prompt from stdin when no positional arg is given.
            cmd = ["claude", "-p"] + (["--model", model] if model else [])
            rc, out, err = run_client(cmd, timeout=timeout, cwd=str(tmp), env=env, input_text=prompt)
        elif client == "opencode":
            cmd = ["opencode", "run", "--format", "json"] + (["-m", model] if model else []) + [prompt]
            rc, out, err = run_client(cmd, timeout=timeout, cwd=str(tmp), env=env)
        else:
            raise RuntimeError(f"--improve-mode cli not available for client '{client}'")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        raise RuntimeError(f"improver CLI failed: {e}") from e
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if rc != 0:
        raise RuntimeError(f"improver CLI exited {rc}: {(err or '')[-500:]}")
    # opencode emits a JSON event stream; claude emits plain text. extract_text
    # passes plain text through unchanged, so this is safe for both.
    text = extract_text(out or "")
    m = re.search(r"<new_description>(.*?)</new_description>", text, re.DOTALL)
    desc = m.group(1).strip().strip('"') if m else text.strip().strip('"')
    if not desc:
        # An empty description classifies every query as non-trigger; on a test set
        # skewed to negatives it could even win _test_rank. Reject it outright.
        raise RuntimeError("improver returned an empty description")
    if len(desc) > 1024:
        raise RuntimeError("improver output exceeded 1024 chars; rerun with --improve-mode manual")
    return desc


def call_improver_manual(prompt: str) -> str:
    print("\n=== IMPROVEMENT PROMPT (paste reply below; end with a line containing exactly EOF) ===\n", file=sys.stderr)
    # Prompt goes to stderr so stdout stays the pure JSON result (machine-readable).
    print(prompt, file=sys.stderr)
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
    parser.add_argument("--client", default="claude", choices=["claude", "opencode"],
                        help="CLI client for --improve-mode cli")
    parser.add_argument("--model", default="",
                        help="Model id passed to the client CLI (--model/-m) for --improve-mode cli")
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

    try:
        eval_items = load_eval_set(eval_set_path)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    try:
        name, original_description, content = parse_skill_md(skill_dir)
    except (ValueError, OSError) as e:
        print(f"Error: cannot read SKILL.md at {skill_dir}: {e}", file=sys.stderr)
        return 1

    if args.max_iterations < 1:
        print("Error: --max-iterations must be >= 1", file=sys.stderr)
        return 1
    if not math.isfinite(args.holdout) or not (0.0 <= args.holdout <= 1.0):
        print("Error: --holdout must be a finite number between 0 and 1", file=sys.stderr)
        return 1

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

        best_so_far = max(history, key=_test_rank)["description"]
        prompt = build_improve_prompt(name, content, current, train_results, best_so_far)
        try:
            if args.improve_mode == "cli":
                new_desc = call_improver_cli(prompt, args.client, model=args.model)
            else:
                new_desc = call_improver_manual(prompt)
            if not new_desc.strip():
                # Empty description classifies everything as non-trigger; never let
                # it enter history (it can even win _test_rank on negative-heavy sets).
                raise RuntimeError("improver returned an empty description")
            current = new_desc
        except RuntimeError as e:
            print(f"Improver failed: {e}", file=sys.stderr)
            exit_reason = f"improver_error (iteration {iteration})"
            break

    # The improvement produced on the final iteration was assigned to `current`
    # but never scored (history is appended at the *start* of each iteration), so
    # `--max-iterations N` would silently drop the Nth candidate and never select
    # it. Score the final candidate now and let it compete.
    if current != history[-1]["description"]:
        final_train = run_heuristic(train, current)
        final_test = run_heuristic(test, current) if test else []
        f_train = summarize(final_train)
        f_test = summarize(final_test) if test else {"passed": 0, "failed": 0, "total": 0}
        history.append({
            "iteration": len(history) + 1,
            "description": current,
            "train_passed": f_train["passed"],
            "train_total": f_train["total"],
            "test_passed": f_test["passed"],
            "test_total": f_test["total"],
            "train_results": final_train,
        })

    best = max(history, key=_test_rank)
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
        if args.report.is_dir():
            print(f"Error: --report is a directory: {args.report}", file=sys.stderr)
            return 1
        try:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as e:
            print(f"Error: cannot write report: {e}", file=sys.stderr)
            return 1
        print(f"Report written: {args.report}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())