"""Compare a locally created skill against upstream candidates and produce a structured score report.

Part of the skill-creator skill. See references/skill-comparison.md.

Scores are computed on the SKILL.md files themselves (no index required), using:
  - Quality 6 dimensions (mirroring quality-bar): trigger clarity, example availability,
    limitations declared, risk declared, security guardrails, metadata completeness
  - Structure 4 dimensions: progressive disclosure, resource organization, script reuse,
    body size control

Usage:
    python scripts/compare_skills.py <local-skill-dir> <upstream-skill-dir> [--json]
    python scripts/compare_skills.py <local-skill-dir> --all-candidates
    
Exit code 0 = success (report printed; verdict included).
"""

import argparse
import io
import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REFS_DIR = SCRIPT_DIR.parent / "references"

WHEN_USE_PATTERNS = [
    re.compile(r"^##\s+When\s+to\s+Use", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+Use\s+this\s+skill\s+when", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+何时使用(?:此|这|本)*技能", re.MULTILINE),
    re.compile(r"^##\s+When\s+to\s+activate\s+this\s+skill", re.MULTILINE | re.IGNORECASE),
]
EXAMPLES_PATTERNS = [
    re.compile(r"^##\s+Examples?", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+示例", re.MULTILINE),
]
LIMITATIONS_PATTERNS = [
    re.compile(r"^##\s+Limitations?", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^##\s+限制", re.MULTILINE),
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


def read_skill(skill_dir: Path) -> dict:
    """Extract a comparable representation of a skill directory."""
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.exists():
        return {"error": f"SKILL.md not found in {skill_dir}"}
    content = skill_file.read_text(encoding="utf-8", errors="replace")
    fm = {}
    m = re.match(r"^---\s*\n(.*?)\n?---(?:\s*\n|$)", content, re.DOTALL)
    if m:
        try:
            import yaml

            fm = yaml.safe_load(m.group(1)) or {}
        except Exception:
            fm = {}
    subdirs = [d for d in os.listdir(skill_dir) if (skill_dir / d).is_dir() and not d.startswith(".")]
    code_blocks = len(re.findall(r"```", content)) // 2
    return {
        "dir": str(skill_dir),
        "name": fm.get("name") or skill_dir.name,
        "frontmatter": fm,
        "content": content,
        "body_lines": content.count("\n") + 1,
        "subdirs": subdirs,
        "code_blocks": code_blocks,
        "files": sum(1 for _, _, fs in os.walk(skill_dir) for f in fs if not f.startswith(".")),
    }


def score_quality(s: dict) -> dict:
    content = s["content"]
    fm = s["frontmatter"]
    q = {}
    q["trigger_clarity"] = 1.0 if any(p.search(content) for p in WHEN_USE_PATTERNS) else 0.0
    q["example_available"] = 1.0 if any(p.search(content) for p in EXAMPLES_PATTERNS) else (0.5 if s["code_blocks"] else 0.0)
    q["limitations_declared"] = 1.0 if any(p.search(content) for p in LIMITATIONS_PATTERNS) else 0.0
    q["risk_declared"] = 1.0 if fm.get("risk") in {"none", "safe", "critical", "offensive", "unknown"} else 0.0
    q["security_guardrails"] = 1.0
    if fm.get("risk") == "offensive":
        q["security_guardrails"] = 1.0 if re.search(r"AUTHORIZED USE ONLY|仅限授权使用", content, re.IGNORECASE) else 0.0
    elif re.search(r"curl\s*\||wget\s*\||irm\s*\||/isx", content):
        q["security_guardrails"] = 0.0
    else:
        q["security_guardrails"] = 0.8  # no risk content detected -> default pass
    meta_fields = ["name", "description"]
    q["metadata_complete"] = sum(1 for f in meta_fields if fm.get(f)) / len(meta_fields)
    return q


def score_structure(s: dict) -> dict:
    sd = s["subdirs"]
    st = {}
    st["progressive_disclosure"] = 1.0 if "references" in sd else (0.4 if s["body_lines"] > 500 else 0.8)
    st["resource_organization"] = min(1.0, len(sd) / 3.0)
    st["script_reuse"] = 1.0 if "scripts" in sd else 0.0
    st["body_size_control"] = 1.0 if s["body_lines"] <= 1000 else (0.5 if s["body_lines"] <= 1500 else 0.2)
    return st


def score_skill(s: dict) -> dict:
    q = score_quality(s)
    st = score_structure(s)
    total = sum(q.values()) / len(q) * 0.6 + sum(st.values()) / len(st) * 0.4
    return {
        "name": s["name"],
        "body_lines": s["body_lines"],
        "files": s["files"],
        "subdirs": s["subdirs"],
        "quality": q,
        "structure": st,
        "quality_score": sum(q.values()) / len(q),
        "structure_score": sum(st.values()) / len(st),
        "total_score": total,
    }


def fmt_score(x: float) -> str:
    return f"{x:.2f}"


def print_report(name: str, sc: dict, indent: str = "") -> None:
    print(f"{indent}{name}  [total {fmt_score(sc['total_score'])} | quality {fmt_score(sc['quality_score'])} | structure {fmt_score(sc['structure_score'])}]")
    print(f"{indent}  body: {sc['body_lines']} lines | files: {sc['files']} | dirs: {', '.join(sc['subdirs']) or '-'}")
    q = sc["quality"]
    st = sc["structure"]
    print(f"{indent}  quality : " + "  ".join(f"{k}={fmt_score(v)}" for k, v in q.items()))
    print(f"{indent}  struct  : " + "  ".join(f"{k}={fmt_score(v)}" for k, v in st.items()))


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Compare local vs upstream skills")
    parser.add_argument("local_dir", help="Local skill directory (with SKILL.md)")
    parser.add_argument("upstream_dir", nargs="?", help="One upstream skill directory")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--all-candidates", action="store_true", help="Compare against every dir under upstream_dir (used with upstream_dir argument)")
    args = parser.parse_args()

    local = Path(args.local_dir)
    ls = score_skill(read_skill(local))

    candidates = []
    if args.all_candidates and args.upstream_dir:
        base = Path(args.upstream_dir)
        candidates = [d for d in (base.iterdir() if base.is_dir() else []) if (d / "SKILL.md").exists()]
    elif args.upstream_dir:
        candidates = [Path(args.upstream_dir)]
    if not candidates:
        print("❌ No upstream candidate given. Pass <upstream_dir> or --all-candidates <dir>.")
        return 1

    print("📊 Comparison Report\n")
    print(f"LOCAL      {ls['name']}  total {fmt_score(ls['total_score'])}")
    print_report(ls["name"], ls, indent="  ")
    print()

    results = []
    for u in candidates:
        sc = score_skill(read_skill(u))
        results.append((u, sc))
        print_report(f"UPSTREAM   {sc['name']} (from {u})", sc, indent="  ")
        print()

    # verdict
    if args.json:
        out = {
            "local": ls,
            "candidates": [{"dir": str(d), **sc} for d, sc in results],
            "meta": {
                "comparison_dimensions": "quality6+structure4",
                "quality_weight": 0.6,
                "structure_weight": 0.4,
            },
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    best = max(results, key=lambda t: t[1]["total_score"])
    verdict = "upstream" if best[1]["total_score"] > ls["total_score"] else "local"
    delta = abs(best[1]["total_score"] - ls["total_score"])
    print("=" * 60)
    if verdict == "upstream":
        print(f"🏆 上游技能更优: {best[1]['name']} (差 {fmt_score(delta)})")
        print("   建议: 分析上游优势维度 → 提炼学习点 → 改进 skill-creator 方法论")
    else:
        print(f"✅ 自建技能更优或持平: {ls['name']} (差 {fmt_score(delta)})")
        print("   建议: 采纳自建版本 → 按流程安装归档 → 可回馈上游社区")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())