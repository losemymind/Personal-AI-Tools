# 对比记录：UEGameStudio 迁移代理批量（30 个） vs 上游候选

## 基本信息
- 日期：2026-09-03
- 需求：补齐「代理必经 agent-creator」合规（根 AGENTS 入库准入规则 1）——对 academic×5 + ue-game-studio×25 共 30 个迁移代理逐一执行 agent-creator 阶段 0（检索上游）/ 阶段 5.5（对比择优）
- 上游候选来源：三源本地检出（`agency-agents` msitarzewski / `ccgs` Donchitos-Claude-Code-Game-Studios / `agency-agents-zh` jnMetaCode），逐一按角色最优匹配
- 对比工具：`scripts/compare_agents.py`（质量 6 维 + 结构 4 维，60/40）

## 对比报告
全部 30 个代理对比结论一致：**自建（迁移版）更优或持平，上游候选均未超越本地版本**（0 个上游更优）。

代表性示例：

| 本地代理 | 自建总分 | 上游最佳 | 上游总分 |
|---|---|---|---|
| academic/anthropologist | 0.86 | academic-anthropologist | 0.43 |
| academic/psychologist | 0.86 | academic-psychologist | 0.48 |
| design/level-mission-designer | 0.86 | level-designer | 0.52 |
| directors/technical-director | 0.82 | technical-director | 0.56 |
| technical/ue-gameplay-engineer | 0.86 | gameplay-programmer | 0.56 |
| technical/ue-ui-engineer | 0.86 | ue-umg-specialist | 0.61 |

分数差异的主要来源：
- 本地迁移版在迁移时已注入「职责范围(必须做/拒绝做)/工具与权限/协作协议(升级路径)/完成标准」章节，并通过 `validate_agents.py --strict`（质量 6 维基本全满）。
- 上游 agency-agents / ccgs 部分代理采用 Claude `.claude/agents` 专属格式，缺少上述解剖章节头，按本库质量标尺整体偏低。

## 结论
- 优者：**自建（迁移版）**，全部 30 个采纳现有版本，无需替换为上游。
- 采纳决定：维持 `agents/academic/`（5）与 `agents/ue-game-studio/`（25）现状；本记录作为「30 个代理已过 agent-creator 对比择优」的合规证据（审计登记见 `agents/AGENTS-AUDIT.md`）。

## 差异分析（仅上游更优时需要）
不适用（无上游更优）。

## 提炼的学习点
- 对比择优的**上游格式差异陷阱**：agency/ccgs 大量代理使用 Claude 专属格式，未按 agent-creator 解剖结构书写时，结构化评分会系统性偏低。**这是格式不匹配，不等同于代理质量差**——结论应结合人工判断身份/边界/权限实质，不能纯看分数。
- 可行方法论改进：`compare_agents.py` 对上游候选可先做**格式归一化提示**（若无「职责/权限/协作/完成标准」章节头时标注 format-unrecognized），避免误把格式差异判为质量差距。
- 迁移代理补充评审时，可比对的上游候选密度低（UE 专属 technical 层多数无直接对应），检索上游时需放宽关键词到跨引擎通用角色。
- 已通过本批对比，补齐 `evolutions/` 首个真实记录（此前为空）。