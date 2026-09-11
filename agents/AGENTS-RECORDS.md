# agents/ — 代理创建记录（AGENTS-RECORDS）

> 本文件是代理库的**集中创建/来源台账**：由 agent-creator 在创建/导入代理时追加（`create_agent.py --records <本文件>`），每个代理一行。
> 记录各代理的来源与创建元数据；`AGENT.md` frontmatter **只**保留运行时字段（`name`/`description`/`mode`/`maturity`/`tools`/`permission` 等），**不含** `version`/`tools_clients`/`tags`/来源字段（打包前代理客户端中立；版本以 git 提交历史为准）。
> 与 `AGENTS-AUDIT.md` 的分工：本台账记**逐条创建/来源事实**（可自动追加）；审计文件记**入库合规结论**（人工维护）。

| 代理 | mode | created | author | source | source_repo | method | evolutions |
|---|---|---|---|---|---|---|---|
| code-reviewer | subagent | 2026-09-02 | losemymind | self | - | created | - |
| code-simplifier | subagent | 2026-09-03 | anthropics | community | anthropics/claude-plugins-official | imported | 2026-09-03-import-code-simplifier.md |
| anthropologist | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| geographer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| historian | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| narratologist | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| psychologist | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| lead-game-balance-designer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| lead-game-economy-designer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| level-mission-designer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| audiovisual-director | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| game-director | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| game-producer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| technical-director | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| orchestration-director | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| game-asset-production-manager | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| game-visual-asset-artist | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| localization-lqa-specialist | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| asset-compliance-auditor | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| qa-test-specialist | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| security-engineer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| character-animation-engineer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| game-ai-engineer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| game-audio-technical-specialist | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| performance-profiler | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| ue-build-engineer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| ue-core-systems-engineer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| ue-gameplay-engineer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| ue-technical-art-engineer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| ue-tools-pipeline-engineer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| ue-ui-engineer | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |
| ue-world-builder | subagent | 2026-09-03 | UEGameStudio | external | UEGameStudio/UEGameStudio | migrated | 2026-09-03-compare-migrated-ue-agents.md |

> `evolutions` 列对应创建器成品 `agent-creator/skills/agent-creator/evolutions/` 中的对比/导入记录文件名。
