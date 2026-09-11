# 审计闭环：第六轮收尾复核（带标题的 Markdown 链接误报）

## 基本信息
- 日期：2026-09-10
- 版本：skill-creator 0.9.19 → 0.9.20
- 触发来源：对 0.9.19 做轻量收尾确认复核（确认第五轮 6 项修复生效、无新回归），过程中新发现 1 个可复现的验证器误报

## 复核结论：第五轮 6 项修复均生效

- `pass_rate` 缺失由 `passed/total` 推导：`{passed:2,failed:1,total:3}` → 2/3（非 0）。
- `resource_organization` 只计 `{scripts,references,examples,templates}` 交集，垃圾目录不虚高。
- `TEXT_SCAN_EXTS` 已含 js/ts 家族等；`scripts/deploy.js` 中的密钥可检出。
- `SECRET_PATTERNS` 覆盖 `github_pat_`/`gh[oprsu]_`/`AIza…`/PEM 头；`.env`/`.env.local` 可扫。
- `<!-- security-allowlist -->` 可豁免紧邻缩进（≥4 列）代码块。
- `build_index.enrich_structure` 复用 `path→skills/<id>` 回退。

无新回归。发布门全绿（见下）。

## 本轮新发现并修复（1 项）

1. **带标题的 Markdown 链接误报悬空（中，正确性）**：`validate_skills.py` 的 dangling-link 检查把 `[x](guide.md "标题")` 整体当路径，标题（空格+引号）使 `guide.md` 存在也被判 `Dangling link`。复现：`[guide](guide.md "The Guide")` → 报 `Path 'guide.md "The Guide"' does not exist`。修复：解析前剥离 CommonMark 可选标题（`"…"` / `'…'` / `(…)`）；指向缺失文件的带标题链接仍正常报错。

> 同一缺陷在 agent-creator 的 `validate_agents.py` 中存在，已在其第二轮审计中同步修复（见 `agent-creator/.../evolutions/2026-09-10-audit-round2.md`）。

## 采纳要点（改了什么）

- `scripts/validate_skills.py`：markdown 链接在解析前剥离可选标题。
- 测试：`tests/test_hardening.py` +2 例 → **161 例**（原 159）。
- 同步 `.opencode/skills/skill-creator` 镜像（`validate_skills.py`、`SKILL.md`，哈希一致）。
- 版本 0.9.19 → 0.9.20。

## 验证结果

- `python -m pytest tests/ -q`：**161 passed**。
- 成品 strict / 能力库 strict（5）/ agent strict（32）/ `build_catalog.py --check` 全绿；索引 4 源 2187 条完整性 OK。

## 学习点

- **收尾复核仍有价值**：前五轮聚焦崩溃与数据契约，Markdown 语法层面（链接标题）一直未被覆盖；「轻量确认」也能再次暴露盲区。
- **孪生缺陷同步排查**：同一段链接解析逻辑在两个创建器各写一份，改一侧时应立即检索另一侧，避免只修半套。
