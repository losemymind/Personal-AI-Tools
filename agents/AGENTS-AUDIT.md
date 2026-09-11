# agents/ — 代理审计（AGENTS-AUDIT）

> 用途：审计 `agents/` 库中每个代理的**数据来源** 与 **入库流程合规性**。事实源 = 创建记录台账 `AGENTS-RECORDS.md` + 本仓库 git 历史 + 迁移记录。
> 范围：只审计能力库条目（`agents/` 下入库代理）。agent-creator 工作区及其成品是**创建工具**，排除在审计之外（其迭代记录走自身 `evolutions/`）。
> 依据：本仓库根 `AGENTS.md`「能力库准入与审计」（规则 1：代理入库**无论参考本地文件还是远程仓库，必须经过 agent-creator**；规则 3：**参考外部仓库的代理必须在创建记录台账 `AGENTS-RECORDS.md` 标注数据来源**；规则 4：**代理按功能归入分类目录 `agents/<顶层分类>/<name>/`，分类不存在则创建；无「留顶层」例外**）。来源/作者/日期**不进** `AGENT.md` frontmatter，集中登记于 `AGENTS-RECORDS.md`（`version`/`tools_clients` 亦不写 frontmatter，版本以 git 为准）。
> 本次审计日期：2026-09-03
> 2026-09-03 更新：academic×5 + ue-game-studio×25 已逐一执行 agent-creator 对比择优（上游三源比对），结论全部为「自建（迁移版）更优/持平」→ **已转合规**。对比证据（agent-creator 成品 evolutions）：`agent-creator/skills/agent-creator/evolutions/2026-09-03-compare-migrated-ue-agents.md`。
> 2026-09-09 更新：agent-creator 已在**本仓库** `agent-creator/skills/agent-creator/`；`agents/` 库校验用其 `scripts/validate_agents.py`。

## 1. 审计结论摘要

| 指标 | 数值 |
|---|---|
| 代理总数 | 32 |
| 自建（无外部引用） | 1（code-reviewer） |
| 外部来源 | 31（30 外部本地仓库 UEGameStudio 迁移 + 1 远程官方仓库导入） |
| 远程仓库来源 | 1（anthropics/claude-plugins-official） |
| 经 agent-creator 生成流程 | 32（code-reviewer 创建时；30 走迁移审计对比择优；code-simplifier 阶段 0+5.5 对比后导入）✅ |
| 未走 agent-creator | 0 |
| `runtime-verified` | 1（code-reviewer） |
| `static-verified` | 31 |

**审计结论**：
- ✅ **全部 32 个代理合规（规则 1）**：code-reviewer 创建时经 agent-creator；academic×5 + ue-game-studio×25 在本次审计中逐一执行 agent-creator 阶段 0（检索上游）/ 5.5（对比择优），结论为自建（迁移版）更优或持平、上游候选未取代；**code-simplifier**（2026-09-03）本地无候选 A → 检索上游索引无命中 → 按用户指定从 `anthropics/claude-plugins-official` 导入并适配，对比 0.86 vs 0.48 采纳适配版 → 转合规。
- ✅ **规则 3 达标**：本文件已为全部 31 个外部代理标注数据来源。

## 2. 数据来源汇总

| 来源类型 | 来源详情 | 涉及代理 |
|---|---|---|
| 外部本地仓库 | `E:\GitHub\UEGameStudio\UEGameStudio\agents`（UEGameStudio 项目组，30 代理，7 层） | 全部 30 个迁移代理 |
| 远程仓库（官方导入） | `anthropics/claude-plugins-official` → `plugins/code-simplifier/agents/code-simplifier.md`（2026-09-03 按用户指定导入并适配） | code-simplifier |
| 自建 | 本仓库创建（agent-creator 流程） | code-reviewer |

> 说明：UEGameStudio 为**本机本地仓库**（非远程 Git 仓库）；迁移时包内文件已去除对源仓库的引用并改写为自包含描述（见 `agents/ue-game-studio/README.md`）。code-simplifier 为库内首个**远程官方仓库**来源代理。

## 3. 分组：code-quality（代码质量通用代理，2 个）

> 2026-09-03 更新：code-reviewer / code-simplifier 按规则 4 迁入新增分类 `agents/code-quality/`（无「留顶层」例外）。

| 代理名 | 位置 | mode | maturity | 数据来源 | 经 agent-creator | 结论 |
|---|---|---|---|---|---|---|
| code-reviewer | `agents/code-quality/code-reviewer/AGENT.md` | subagent | runtime-verified | 自建（本仓库） | ✅ | ✅ 合规 |
| code-simplifier | `agents/code-quality/code-simplifier/AGENT.md` | subagent | static-verified | 远程 `anthropics/claude-plugins-official`（code-simplifier.md）导入适配 | ✅ | ✅ 合规（2026-09-03；对比 0.86 vs 0.48 采纳适配版）|

## 4. 分组：academic（公共研究代理，5 个）

> 数据来源（全部）：外部本地仓库 `E:\GitHub\UEGameStudio\UEGameStudio\agents\academic`（随 UEGameStudio 迁移保留为公共代理）。
> 审计期已逐一执行 agent-creator 对比择优（上游：agency-agents / agency-agents-zh 同名 academic 代理），结论自建更优 → ✅ 合规（规则 1）。

| 代理名 | 位置 | layer（目录） | maturity | 数据来源 | 经 agent-creator | 结论 |
|---|---|---|---|---|---|---|
| anthropologist | `agents/academic/anthropologist/AGENT.md` | academic | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| geographer | `agents/academic/geographer/AGENT.md` | academic | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| historian | `agents/academic/historian/AGENT.md` | academic | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| narratologist | `agents/academic/narratologist/AGENT.md` | academic | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| psychologist | `agents/academic/psychologist/AGENT.md` | academic | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |

## 5. 分组：ue-game-studio（UE 专用安装包，25 个）

> 数据来源（全部）：外部本地仓库 `E:\GitHub\UEGameStudio\UEGameStudio\agents`（按 layer 迁入 `agents/ue-game-studio/<layer>/`）。
> 审计期已逐一执行 agent-creator 对比择优（上游：agency-agents / ccgs / agency-agents-zh 按角色最佳匹配），结论自建更优或持平 → ✅ 合规（规则 1）。

### design（3）

| 代理名 | 位置 | layer（目录） | maturity | 数据来源 | 经 agent-creator | 结论 |
|---|---|---|---|---|---|---|
| lead-game-balance-designer | `agents/ue-game-studio/design/lead-game-balance-designer/AGENT.md` | design | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| lead-game-economy-designer | `agents/ue-game-studio/design/lead-game-economy-designer/AGENT.md` | design | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| level-mission-designer | `agents/ue-game-studio/design/level-mission-designer/AGENT.md` | design | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |

### directors（4）

| 代理名 | 位置 | layer（目录） | maturity | 数据来源 | 经 agent-creator | 结论 |
|---|---|---|---|---|---|---|
| audiovisual-director | `agents/ue-game-studio/directors/audiovisual-director/AGENT.md` | directors | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| game-director | `agents/ue-game-studio/directors/game-director/AGENT.md` | directors | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| game-producer | `agents/ue-game-studio/directors/game-producer/AGENT.md` | directors | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| technical-director | `agents/ue-game-studio/directors/technical-director/AGENT.md` | directors | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |

### orchestration（1）

| 代理名 | 位置 | layer（目录） | maturity | 数据来源 | 经 agent-creator | 结论 |
|---|---|---|---|---|---|---|
| orchestration-director | `agents/ue-game-studio/orchestration/orchestration-director/AGENT.md` | orchestration | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |

### production（3）

| 代理名 | 位置 | layer（目录） | maturity | 数据来源 | 经 agent-creator | 结论 |
|---|---|---|---|---|---|---|
| game-asset-production-manager | `agents/ue-game-studio/production/game-asset-production-manager/AGENT.md` | production | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| game-visual-asset-artist | `agents/ue-game-studio/production/game-visual-asset-artist/AGENT.md` | production | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| localization-lqa-specialist | `agents/ue-game-studio/production/localization-lqa-specialist/AGENT.md` | production | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |

### qa（3）

| 代理名 | 位置 | layer（目录） | maturity | 数据来源 | 经 agent-creator | 结论 |
|---|---|---|---|---|---|---|
| asset-compliance-auditor | `agents/ue-game-studio/qa/asset-compliance-auditor/AGENT.md` | qa | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| qa-test-specialist | `agents/ue-game-studio/qa/qa-test-specialist/AGENT.md` | qa | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| security-engineer | `agents/ue-game-studio/qa/security-engineer/AGENT.md` | qa | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |

### technical（11）

| 代理名 | 位置 | layer（目录） | maturity | 数据来源 | 经 agent-creator | 结论 |
|---|---|---|---|---|---|---|
| character-animation-engineer | `agents/ue-game-studio/technical/character-animation-engineer/AGENT.md` | technical | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| game-ai-engineer | `agents/ue-game-studio/technical/game-ai-engineer/AGENT.md` | technical | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| game-audio-technical-specialist | `agents/ue-game-studio/technical/game-audio-technical-specialist/AGENT.md` | technical | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| performance-profiler | `agents/ue-game-studio/technical/performance-profiler/AGENT.md` | technical | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| ue-build-engineer | `agents/ue-game-studio/technical/ue-build-engineer/AGENT.md` | technical | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| ue-core-systems-engineer | `agents/ue-game-studio/technical/ue-core-systems-engineer/AGENT.md` | technical | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| ue-gameplay-engineer | `agents/ue-game-studio/technical/ue-gameplay-engineer/AGENT.md` | technical | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| ue-technical-art-engineer | `agents/ue-game-studio/technical/ue-technical-art-engineer/AGENT.md` | technical | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| ue-tools-pipeline-engineer | `agents/ue-game-studio/technical/ue-tools-pipeline-engineer/AGENT.md` | technical | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| ue-ui-engineer | `agents/ue-game-studio/technical/ue-ui-engineer/AGENT.md` | technical | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |
| ue-world-builder | `agents/ue-game-studio/technical/ue-world-builder/AGENT.md` | technical | static-verified | UEGameStudio 外部仓库 | ✅ | ✅ 合规 |

## 6. 维护要求

- 新增/迁移/改进代理入库后，**必须更新本文件**：登记数据来源（规则 3）与是否经 agent-creator（规则 1）。
- 逐条创建/来源事实记入 `AGENTS-RECORDS.md`（`create_agent.py --records` 自动追加）；本文件记合规结论。
- 审计状态变化（如 30 个迁移代理补走 agent-creator 后转合规）应及时在「审计结论摘要」中刷新。
- 本文件与 `skills/SKILLS-AUDIT.md` 同构（互为镜像，随各自能力库目录存放），均为数据来源的唯一记录入口。

## 7. 未完成项

- **30 个迁移代理逐档升级 `runtime-verified`**：当前全部为 `static-verified`（仅静态 --strict），需在真实 UE Editor / 目标项目试跑后逐档升级并同步刷新本文件与 `agents/CATALOG.md`。
- agent-creator 阶段 6（真实场景测试）：迁移代理补走时以静态对比为主，待运行时验证覆盖。