# agents/ — 代理创建记录（AGENTS-RECORDS）

> 本文件是代理库的**集中创建/来源台账**：由 agent-creator 在创建/导入代理时追加（`create_agent.py --records <本文件>`），每个代理一行。
> 记录各代理的来源与创建元数据；`AGENT.md` frontmatter **只**保留运行时字段（`name`/`description`/`mode`/`maturity`/`tools`/`permission` 等），**不含** `version`/`tools_clients`/`tags`/来源字段（打包前代理客户端中立；版本以 git 提交历史为准）。
> 与 `AGENTS-AUDIT.md` 的分工：本台账记**逐条创建/来源事实**（可自动追加）；审计文件记**入库合规结论**（人工维护）。

| 代理 | mode | created | author | source | source_repo | method | evolutions |
|---|---|---|---|---|---|---|---|
| code-reviewer | subagent | 2026-09-02 | losemymind | self | - | created | - |
| code-simplifier | subagent | 2026-09-03 | anthropics | community | anthropics/claude-plugins-official | imported | 2026-09-03-import-code-simplifier.md |
| anthropologist | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | - |
| geographer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | - |
| historian | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | - |
| narratologist | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | - |
| psychologist | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | - |

> `evolutions` 列对应创建器成品 `agent-creator/skills/agent-creator/evolutions/` 中的对比/导入记录文件名。
