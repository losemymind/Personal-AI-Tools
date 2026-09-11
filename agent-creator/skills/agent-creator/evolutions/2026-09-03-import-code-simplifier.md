# 对比记录：code-simplifier（本地 A 空） → 官方上游导入 + 适配（B 采用）

## 基本信息
- 日期：2026-09-03
- 需求：创建 `code-simplifier` 代理，数据来源为用户指定的 `https://github.com/anthropics/claude-plugins-official/blob/main/plugins/code-simplifier/agents/code-simplifier.md`
- 本地候选 A：`agents/CATALOG.md` 无 code-simplifier（仅有 code-reviewer/academic）→ **A 为空**
- 上游索引检索：`search_agent_index.py "simplify code refactor"` → 0 命中（三源 agency/ccgs/agency-zh 均无）→ 上游索引无候选
- 上游 B：官方 Anthropic `anthropics/claude-plugins-official` 的 `plugins/code-simplifier/agents/code-simplifier.md`（52 行，单文件，`model: opus`，无模式/权限/协作/完成标准章节）

## 对比分析（compare_agents.py：质量 6 维 + 结构 4 维）
- **本地适配版 0.86**（quality 0.97 / structure 0.70）vs **上游 0.48**（quality 0.33 / structure 0.70）→ 差 0.39，**适配版更优**
- 上游缺失维度：boundary_clarity=0（无职责范围）、must/refuse=0.5（无「拒绝做」）、permission_declared=0（无工具/权限声明）、collab_escalation=0（无协作协议/升级路径）、completion_criteria=0（无完成标准）
- 适配要点：
  1. frontmatter 补齐本地 schema：`mode: subagent` / `tools`（read/grep/glob/edit/write）/ `permission`（edit/write allow，delete/破坏性操作默认拒）/ `version` / `tools_clients` / `tags` / `maturity: static-verified` / `source_repo`；`description ≤300`
  2. 按本地 7 章节重组原文：角色定位 / 职责范围（必须做 5 条：保功能/应用规范/提升清晰度/保持平衡/聚焦范围；拒绝做 6 条）/ 工作方式 / 工具与权限 / 协作协议（含升级路径）/ 完成标准（可验证清单）/ 限制与边界
  3. 保留官方方法论全部要点（保功能不变、避免嵌套三元、克制过度简化、主动精炼最近修改代码）
- 验证：`validate_agents.py --strict --dir agents/code-quality/code-simplifier` → **通过**

## 结论
- 入库位置符合规则 4（按功能分类，通用研发代理同 code-reviewer 归入 `code-quality/` 分类，无「留顶层」例外）：`agents/code-quality/code-simplifier/AGENT.md`
- 审计登记：`agents/AGENTS-AUDIT.md`（数据来源 = 远程官方仓库 + 上游文件路径）
- 采用确定：**上游 B 官方方法论导入 + 本地 schema/章节适配（A 空，无择优竞争者）**

## 提炼的学习点
- 官方 Anthropic 单文件代理（如 claude-plugins-official 的 agents/）是**连续散文式**定义：身份强、职责清，但缺「必须做/拒绝做」二分、权限声明、协作/升级路径与完成标准——按本地 schema 重组章节即达严格验证
- 此类官方代理 frontmatter 常用 `model:` 而非本地 `mode:`/`tools:`/`permission:`：导入时需补最小权限声明（本代理职责即精炼代码，edit/write 属职责必需，须在「工具与权限」显式声明范围与禁止项）
- 「简化类」代理与「审查类」代理权限相反：审查=只读拒绝写；简化=实际写代码。权限必须与职责边界一致（最小权限不是一律禁止写）