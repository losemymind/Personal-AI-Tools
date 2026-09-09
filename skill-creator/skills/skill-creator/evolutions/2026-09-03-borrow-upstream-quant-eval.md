# 对比记录：本地 skill-creator vs Anthropic 官方 skill-creator（借鉴反馈闭环）

## 基本信息
- 日期：2026-09-03
- 需求：对比本地 `skill-creator` 与上游官方 `anthropics/skills/skills/skill-creator`（经同 blob sha 的 `claude-plugins-official` 插件版取用）的优劣，并执行择优建议
- 上游来源：`https://github.com/anthropics/skills`（`skills/skill-creator/`，与 `anthropics/claude-plugins-official` 插件版同 blob sha；sparse-checkout 提交 `0120fb8`）
- 对比工具：`compare_skills.py`（质量 6 维 + 结构 4 维，60/40）

## 对比报告
- **本地**：total 0.90（quality 0.83 / structure 1.00），SKILL.md 417 行，6 个资源目录
- **上游官方**：total 0.63（quality 0.38 / structure 1.00），SKILL.md 486 行，5 个资源目录

### 上游优势维度（本次采纳）
1. **量化基准引擎**：有技能 vs 无技能基线双跑 + mean±stddev 汇总 + delta 对比（`aggregate_benchmark.py` → `benchmark.json` + `benchmark.md`）——本地此前只有触发启发式，无量化增益判断
2. **触发评测无头 CLI 双模式**：真实客户端无头运行（`run_eval.py`，`claude -p`）或确定性启发式降级——本地 `run_trigger_tests.py` 只有启发式
3. **description 自动优化循环**：should_trigger 分层 60/40 train/test split、多轮迭代、按 test 得分选最优防过拟合（`run_loop.py` + improve prompt）

### 上游缺口（本地差异化保留）
1. 上游为 Claude Code 专属（`claude -p`、`.claude/commands`、HTML viewer）；本地需四端通用（claude/opencode/codex/deepseek），故移植版本做成客户端无关：heuristic 默认、cli 可选
2. 上游无仓库内集成（无审计文件、无 CI、无 install 生命周期）；本地保留仓库级编排与准入规则

## 结论
- 优者：**本地**（结构化评分 0.90 vs 0.63，因质量维完整性：触发清晰/示例/限制/风险/元数据）
- 采纳决定：保留本地主体 + **移植上游量化 eval 引擎**（`utils.py`、`run_eval.py`、`run_loop.py`、`aggregate_benchmark.py`）+ `references/benchmark-schema.md`，SKILL.md 阶段 6/7 已接入。触发评测默认启发式（无 CLI 依赖），真实客户端可用 `--mode cli`。

## 差异分析（上游更优维度 → 反哺本技能）
- 上游优势维度：量化基准（delta/mean±stddev）、触发评测双模式、description 自动优化防过拟合
- 本地差距原因：此前仅启发式触发测试，缺「有/无技能」双跑与统计汇总

## 提炼的学习点（已用于改进 skill-creator）
- 技能评估应区分**触发评估**（description 是否被调用）与**效果评估**（用了技能是否更好）——前者用 run_loop/run_eval，后者用 aggregate_benchmark 的 delta
- 统计汇总（mean±stddev、delta）优于单次主观判断；高方差 eval 视为 flaky
- description 优化必须有 holdout test 集，避免过拟合训练查询

## 改进建议
- 建议在真实客户端环境（如 opencode）试跑 `run_loop.py --improve-mode cli --client opencode` 前先确认该客户端无头 CLI 的触发判定支持（当前 cli 模式仅 claude 有完整实现），其余客户端以 heuristic 为主、cli 为进阶