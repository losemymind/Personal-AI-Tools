# 采纳升级：agent 评审闭环取代人工评审（无人工介入）

## 基本信息
- 日期：2026-09-10
- 需求：评审此前依赖人工逐条确认，不符合「评审全程无人工介入」；评审应改由 agent 承担——agent1 修改、agent2 评审反馈、agent1 继续改，直到通过。
- 来源：本地既有子代理编排（grader / comparator / analyzer）。
- 前情：阶段 6/7 的评审此前依赖人工逐条确认，无结构化反馈载体；本次改为 agent 评审闭环。

## 对比与决定
- **采纳**：把「需要评分和审核」的事务改由**评审子代理**（`agents/reviewer.md`）完成——产出 `review.json`（`verdict: pass|revise` + 可执行 `issues[]`），驱动 **agent1 ↔ agent2 自动闭环**：agent1 改稿 → reviewer 评审 → `revise` 时按 issues 逐条修 → 重评，**`pass` 或达 `max-iterations`（默认 5）即停**，全程无人工。
- **范围**：仅「评审」去人工；授权/高风险/人力决策门（阶段 2、阶段 9 高风险升级）仍保留人工。

## 采纳要点（改了什么）
- 新增成品 `agents/reviewer.md`（通用评分/审核子代理 + `review.json` 契约 + 与 grader/comparator/analyzer 的分工）。
- `SKILL.md` 阶段 6：人审闭环 → **AI 评审闭环（agent1↔agent2，无人工）**；阶段 7：查询集审阅由用户签名 → 评审子代理 `pass`/`revise`；阶段 8：`VERIFICATION.md` 明确为**可选留痕**（不再声称必须创建）。
- `references/quality-bar.md`：评审标注由「人工」改为「评审子代理」。
- 同步孪生 agent-creator（新增 `agents/reviewer.md` + 阶段 6 闭环 + 版本 0.7.0）。

## 版本
- skill-creator `0.6.2 → 0.7.0`；agent-creator `0.6.0 → 0.7.0`（minor：新增子代理 + 方法论语义变化）。

## 学习点
- 评审的载体不必是 UI：把「判定 + 可执行修复项」结构化为 `review.json`，任何支持子代理的客户端都能自动闭环、四端通用。
- 生成者与评审者必须分离（不自评自改），但必须设**停止条件**（`verdict==pass` ∨ `max-iterations`）与**客观前置门**（`validate_*.py --strict`），否则会陷入无效/无限循环。
