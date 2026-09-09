# 对比记录：本地 eval 流水线（纯脚本）vs Anthropic 官方（agent 编排 + 脚本）（借鉴反馈闭环）

## 基本信息
- 日期：2026-09-04
- 需求：本地评估流水线仅有确定性脚本（heuristic 触发 + 规则化打分），官方用三个子代理（grader/comparator/analyzer）做语义判断——是否采纳官方编排
- 上游来源：`https://github.com/anthropics/skills`（`skills/skill-creator/agents/{grader,comparator,analyzer}.md` + SKILL.md 编排；与 `anthropics/claude-plugins-official` 插件版同 blob sha）
- 前情：2026-09-03 已移植官方脚本层（run_eval/run_loop/aggregate_benchmark），当时未移植 `agents/`（本地按四端无子代理派发约束简化）

## 对比报告（两阶段分工）
- **脚本（两方共有，本地已移植）**：确定性、零依赖、可进 CI、秒级免费可复现；但只能测 description 触发面（关键词重叠），测不了输出语义质量与盲测对比
- **官方子代理（本次采纳）**：语义断言打分（PASS 要求真实完成而非表面合规）、隐含声明核验、盲测 A/B（消除位置偏差）、基准模式分析（恒过/恒败/单侧过/flaky 侦测）；代价是依赖模型判断、不可脚本化复现

## 结论
- 两者测的维度互补，不是二选一：**确定性脚本打底 + SKILL.md 拉起子代理判断 + 脚本聚合收尾**
- 采纳决定：移植三个子代理指令到 `agents/`（适配本地 schema 与中文语境，grading.json 字段契约不变），SKILL.md 阶段 5/5.5/6 编排接入；`aggregate_benchmark.py` 增 `--notes` 合并 analyzer 笔记
- 四端兼容处理：客户端无子代理派发能力时，主持会话按同一份 `agents/*.md` 内联完成，产物格式不变（不进自动加载，天然不依赖客户端子代理机制）

## 提炼的学习点（已用于改进 skill-creator）
- 评估流水线应分层：**可程序验证的**交脚本（可复现/可进 CI），**语义判断的**交模型（子代理提示文件作为可移植的「判断单元」）
- 盲测协议（A/B 随机标签、保密来源）是消除位置偏差的最廉手段，值得写进编排纪律而非靠自觉
- 子代理指令文件（`agents/*.md`）是「不进自动加载、由 SKILL.md 按需拉起」的渐进式披露形态——与 `references/` 同构，只是消费者是被拉起的子代理而非主持会话
- grader 的双重职责（打分 + 审视断言本身）能防「弱断言上的虚假信心」——恒过断言比没有断言更危险

## 改进建议
- 首次在真实任务上跑通「有/无技能双跑 → grader 打分 → aggregate → analyzer 笔记 --notes 合并」全链路后，把样例产物（grading.json/benchmark.json/comparison.json）沉淀为 `references/benchmark-schema.md` 的实例附录
