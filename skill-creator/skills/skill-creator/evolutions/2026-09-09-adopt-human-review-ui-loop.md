# 对比记录：人审 UI 环（eval-viewer / eval_review.html）（借鉴反馈闭环）

## 基本信息
- 日期：2026-09-09
- 需求：本地主观评审只在对话里进行——无版本化、不可回流为结构化反馈；是否吸收 Anthropic 官方的「人审 UI 环」
- 上游来源：`https://github.com/anthropics/skills`（`skills/skill-creator/`，Apache-2.0）
- 前情：2026-09-03 已移植官方脚本层（run_eval/run_loop/aggregate_benchmark）、2026-09-04 已移植 agents/ 编排；两版 eval-viewer / eval_review.html 一直未移植

## 对比报告
- **本地现状**：grader 子代理产出 `grading.json`（字段契约已对齐官方），aggregate 出 benchmark.json/.md；但「人工定性评审」发生在对话流里，意见不可版本化、无法在下一轮迭代自动回流。
- **官方增量（本次评估）**：
  1. `eval-viewer/viewer.html` + `generate_review.py`：把 grading/benchmark 渲染为双 tab HTML（Outputs/Benchmark），逐条用例给反馈文本框并自动保存，`--static` 可无头导出、feedback.json 回流下轮。
  2. `assets/eval_review.html`：跑 run_loop 前把触发查询集（应触发 + 近似干扰否定项）做成可编辑/开关 UI，导出 eval_set.json——防止「坏查询 → 坏描述」。
  3. 写作纪律：改稿前先给人看（generate_report/eval-viewer 强制前置）；「先给人看，再自己改」。

## 结论
- 采纳 UI 环**思路与产物格式**（feedback.json 回流、双 tab 视图、触发集审阅），不以「必须部署本地服务器」为前提——`--static` 无头导出天然四端通用，规避官方 viewer 依赖 Python http 服务的宿主假设。
- grading.json 字段契约（text/passed/evidence + summary/claims/execution_metrics/user_notes_summary）保持锁定，不得改名（viewer 与回流依赖它）。
- 触发集审阅并入阶段 7 手动档（run_loop 前人工把关查询质量）。

## 提炼的学习点（已用于改进 skill-creator）
- 主观评审与客观断言应分轨：**客观断言**交 grader（可脚本判），**主观质量**交带 UI 的人类（可回流 feedback）——两轨产物都进 iteration 目录做版本对比。
- 人机闭环需要「结构化的意见载体」：无结构的聊天反馈无法参与下一轮 train/test 对比；feedback.json 这类最小 schema 是回流前提。
- 先给人看再自己改：描述/技能改稿前先渲染对比，避免 agent 自评自改的盲区。

## 改进建议
- 本日期随「上游对比与升级（2026-09-09）」落地：SKILL.md 阶段 6/7 补审阅闭环纪律；新脚本 eval_review 静态导出待真实场景跑通后补充。
