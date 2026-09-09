"""Compare a locally created agent against upstream candidates and produce a structured score report.

Part of the agent-creator skill. See references/agent-comparison.md.

Scores are computed on the AGENT.md files themselves (no index required), using:
   - Quality 6 dimensions (mirroring agent-quality-bar): boundary clarity, must/refuse
    declared, permission declared, collaboration/escalation declared, completion criteria,
    metadata completeness
   - Structure 4 dimensions: progressive disclosure, resource organization,
    single-responsibility, body size control

Usage:
    python scripts/compare_agents.py <local-agent-dir> <upstream-agent-dir> [--json]
    python scripts/compare_agents.py <local-agent-dir> --all-candidates

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
    re.compile(r"^tools\s*:", re.MULTILINE | re.IGNORECASE),
    re.compile(r"^permission\s*:", re.MULTILINE | re.IGNORECASE),
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


def read_agent(agent_dir: Path) -> dict:
    """Extract a comparable representation of an agent directory (or single .md file)."""
    agent_file = agent_dir / "AGENT.md" if agent_dir.is_dir() else agent_dir
    if not agent_file.exists():
        return {"error": f"AGENT.md not found in {agent_dir}"}
    content = agent_file.read_text(encoding="utf-8", errors="replace")
    fm = {}
    m = re.match(r"^---\s*\n(.*?)\n?---(?:\s*\n|$)", content, re.DOTALL)
    if m:
        try:
            import yaml

            fm = yaml.safe_load(m.group(1)) or {}
        except Exception:
            fm = {}
    subdirs = []
    if agent_dir.is_dir():
        subdirs = [d for d in os.listdir(agent_dir) if (agent_dir / d).is_dir() and not d.startswith(".")]
    files = 1
    if agent_dir.is_dir():
        files = sum(1 for _, _, fs in os.walk(agent_dir) for f in fs if not f.startswith("."))
    return {
        "dir": str(agent_dir),
        "name": fm.get("name") or agent_dir.name,
        "frontmatter": fm,
        "content": content,
        "body_lines": content.count("\n") + 1,
        "subdirs": subdirs,
        "files": files,
    }


def score_quality(a: dict) -> dict:
    content = a["content"]
    fm = a["frontmatter"]
    q = {}
    q["boundary_clarity"] = 1.0 if any(p.search(content) for p in BOUNDARY_PATTERNS) else 0.0
    has_must = any(p.search(content) for p in MUST_DO_PATTERNS)
    has_refuse = any(p.search(content) for p in REFUSE_PATTERNS)
    if has_must and has_refuse:
        q["must_refuse_declared"] = 1.0
    elif has_must or has_refuse:
        q["must_refuse_declared"] = 0.5
    else:
        q["must_refuse_declared"] = 0.0
    has_perm = any(p.search(content) for p in PERMISSION_PATTERNS) or fm.get("tools") or fm.get("permission")
    q["permission_declared"] = 1.0 if has_perm else 0.0
    has_collab = any(p.search(content) for p in COLLAB_PATTERNS)
    has_escalate = any(p.search(content) for p in ESCALATION_PATTERNS)
    if has_collab and has_escalate:
        q["collab_escalation"] = 1.0
    elif has_collab:
        q["collab_escalation"] = 0.6
    else:
        q["collab_escalation"] = 0.0
    q["completion_criteria"] = 1.0 if any(p.search(content) for p in COMPLETION_PATTERNS) else 0.0
    if fm.get("risk") == "offensive":
        q["security_guardrails"] = 1.0 if any(p.search(content) for p in SECURITY_DISCLAIMER_PATTERNS) else 0.0
    elif re.search(r"curl\s*\||wget\s*\||irm\s*\||/isx", content):
        q["security_guardrails"] = 0.0
    else:
        q["security_guardrails"] = 0.8
    meta_fields = ["name", "description"]
    q["metadata_complete"] = sum(1 for f in meta_fields if fm.get(f)) / len(meta_fields)
    return q


def score_structure(a: dict) -> dict:
    sd = a["subdirs"]
    st = {}
    st["progressive_disclosure"] = 1.0 if "references" in sd else (0.4 if a["body_lines"] > 500 else 0.8)
    st["resource_organization"] = min(1.0, len(sd) / 2.0)
    st["single_responsibility"] = 1.0 if a["body_lines"] <= 300 else (0.6 if a["body_lines"] <= 500 else 0.3)
    st["body_size_control"] = 1.0 if a["body_lines"] <= 500 else (0.5 if a["body_lines"] <= 800 else 0.2)
    return st


def score_agent(a: dict) -> dict:
    q = score_quality(a)
    st = score_structure(a)
    total = sum(q.values()) / len(q) * 0.6 + sum(st.values()) / len(st) * 0.4
    return {
        "name": a["name"],
        "body_lines": a["body_lines"],
        "files": a["files"],
        "subdirs": a["subdirs"],
        "quality": q,
        "structure": st,
        "quality_score": sum(q.values()) / len(q),
        "structure_score": sum(st.values()) / len(st),
        "total_score": total,
    }


def fmt_score(x: float) -> str:
    return f"{x:.2f}"


def print_report(name: str, sc: dict, indent: str = "") -> None:
    print(f"{indent}{name}   [total {fmt_score(sc['total_score'])} | quality {fmt_score(sc['quality_score'])} | structure {fmt_score(sc['structure_score'])}]")
    print(f"{indent}  body: {sc['body_lines']} lines | files: {sc['files']} | dirs: {', '.join(sc['subdirs']) or '-'}")
    q = sc["quality"]
    st = sc["structure"]
    print(f"{indent}  quality : " + "   ".join(f"{k}={fmt_score(v)}" for k, v in q.items()))
    print(f"{indent}  struct  : " + "   ".join(f"{k}={fmt_score(v)}" for k, v in st.items()))


def main() -> int:
    configure_utf8_output()
    parser = argparse.ArgumentParser(description="Compare local vs upstream agents")
    parser.add_argument("local_dir", help="Local agent directory (with AGENT.md) or a single .md file")
    parser.add_argument("upstream_dir", nargs="?", help="One upstream agent directory (or .md file)")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    parser.add_argument("--all-candidates", action="store_true", help="Compare against every AGENT.md under upstream_dir")
    args = parser.parse_args()

    local = Path(args.local_dir)
    ls = score_agent(read_agent(local))

    # Non-agent docs to skip when scanning a directory as candidates (mirrors validate_agents.py)
    NON_AGENT_DOCS = {
         "readme.md", "readme", "changelog.md", "development-plan.md",
         "agents.md", "skill.md", "catalog.md",
    }
    candidates = []
    if args.all_candidates and args.upstream_dir:
        base = Path(args.upstream_dir)
        if base.is_dir():
            candidates = [
                d
                for d in base.iterdir()
                if (d / "AGENT.md").exists() or (d.is_file() and d.suffix.lower() == ".md" and d.name.lower() not in NON_AGENT_DOCS)
             ]
    elif args.upstream_dir:
        candidates = [Path(args.upstream_dir)]
    if not candidates:
        print("❌ No upstream candidate given. Pass <upstream_dir> or --all-candidates <dir>.")
        return 1

    print("📊 Comparison Report\n")
    print(f"LOCAL       {ls['name']}  total {fmt_score(ls['total_score'])}")
    print_report(ls["name"], ls, indent="   ")
    print()

    results = []
    for u in candidates:
        sc = score_agent(read_agent(u))
        results.append((u, sc))
        print_report(f"UPSTREAM    {sc['name']} (from {u})", sc, indent="   ")
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
        print(f"🏆 上游代理更优: {best[1]['name']} (差 {fmt_score(delta)})")
        print("   建议: 分析上游优势维度 → 提炼学习点 → 改进 agent-creator 方法论")
    else:
        print(f"✅ 自建代理更优或持平: {ls['name']} (差 {fmt_score(delta)})")
        print("   建议: 采纳自建版本 → 按流程安装归档 → 可回馈上游社区")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
