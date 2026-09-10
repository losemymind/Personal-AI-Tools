# 上游导入：mcp-builder（Anthropic 官方 → 本地适配）

## 基本信息

- 日期：2026-09-10
- 需求：创建指导开发者构建高质量 MCP（Model Context Protocol）服务器的技能，让 LLM 通过精心设计的工具与外部服务交互；覆盖 Python（FastMCP）与 Node/TypeScript（MCP SDK）两条实现路径。入库 `skills/development/mcp-builder/`。
- 证据：需求描述与上游官方 `mcp-builder` 的 description 高度一致 → 判定为「官方已有权威实现」。

## 本地 A / 上游 B

- **本地 A（候选）**：无（新技能）。索引检索 `mcp`/`model context protocol` 命中多个上游候选，非空。
- **上游 B（选定）**：`anthropics/skills` 的 `skills/mcp-builder`（Apache-2.0，`LICENSE.txt` 已核）——SKILL.md ~237 行 + `reference/{mcp_best_practices,evaluation,node_mcp_server,python_mcp_server}.md` + `scripts/{connections.py,evaluation.py,example_evaluation.xml,requirements.txt}`。
- 其他候选（未采纳）：
  - `ComposioHQ/awesome-claude-skills` 的 `mcp-builder`（329 行，官方分发副本）。
  - `sickn33/agentic-awesome-skills` 的 `mcp-builder`（279 行）与 `mcp-tool-developer`（133 行，单文件）——对比结构分较低。

## 采纳形态

**方法论导入 + 中文本地化**（非整目录原样拷贝）：

- 保留官方 `reference/*.md`（英文技术深文档）、`scripts/*`（评测运行器）、`LICENSE.txt`（Apache-2.0 归属）。
- 重写入口 `SKILL.md` 为**中文**：`概述` / `何时使用此技能` / `工作原理`（四阶段：研究规划→实现→评审测试→建评测集）/ `示例` / `参考文档` / `最佳实践` / `限制和注意事项` / `安全与安全说明`；补本地 frontmatter schema（category/risk/source/source_repo/version/date_added/author/tags/tools），description 中英触发词。
- 新增 `evals.json`（12 条：7 正 / 5 干扰），随技能沉淀。

## 对比择优

`compare_skills.py`（本地适配版 vs 上游/其他候选）：

| 对局 | 本地总分 | 上游总分 | 结论 |
|---|---|---|---|
| mcp-builder vs anthropics 官方 `mcp-builder` | 0.93 | 0.51 | 采纳本地适配版（上游缺本地 schema/必需章节） |
| mcp-builder vs aas `mcp-tool-developer` | 0.93 | 0.75 | 采纳本地（结构/资源组织更全） |

> 上游 0.51 非质量差，而是缺本地库判定所要求的 frontmatter 字段与「何时使用/限制」章节；本地适配补齐后更贴合本库。

## 验证

- `validate_skills.py --strict --dir skills/development/mcp-builder` 通过。
- 触发评测（heuristic）：12/12，precision 100%、recall 100%。
- `scripts/*.py` `py_compile` 通过。

## 学习点

- **需求描述与官方 description 逐字一致 = 强信号**：优先「官方导入 + 本地化适配」，避免重造轮子（与 code-review-skill / prd-generator 同一策略）。
- **导入不等于原样拷贝**：入口层中文化 + 补本地 schema/章节，深文档（reference）保留上游英文以保真。
- **触发描述需控重复 token**：本地启发的词重叠判定会被同名 core token（mcp/server/API）重复拉高，收敛为单次出现可显著降假阳性，且不损真实触发。
