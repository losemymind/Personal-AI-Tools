# 纪律→工具：真机触发评测串行过慢 → run_eval 增加有界并行

## 基本信息
- 日期：2026-09-10
- 版本：skill-creator 0.9.4 → 0.9.5
- 触发来源：本轮会话续做 HANDOFF 待办 1（补跑完整真机触发/基准）

## 需求与证据

**证据 1（墙钟瓶颈）**：用 `run_eval.py --mode cli --client opencode --model deepseek/deepseek-v4-flash` 跑真机评测，批次 1（7 查询 × 3 次 = 15 次调用）耗时 **927.5s ≈ 15.5 分钟**；批次 2（21 次调用）超 10 分钟仍未返回，被中止。根因是 `run_eval.py` **串行**执行每条查询，而单条 `opencode run` 普遍 30–120s（批次 1 有 2 条撞满 `--timeout 120`）。不是死锁，是设计上过慢，导致「完整真机基准」在合理时间内不可完成。

**证据 2（触发非确定性）**：同一句「把反复出现的工作流做成一个可复用技能」两次运行结果不同——一次 `tool_use`/`tool:"skill"`/`input.name:"skill-creator"`（触发），另一次模型直接作答、`tool_use_count=0`（未触发）。**检测器无误**（对未触发那次正确判 False），低召回主要来自模型行为抖动，因此单轮判定噪声大、需要多轮取率 —— 这进一步放大了串行耗时。

批次 1（3 次/条，positive）真机触发率：0.67 / 0.33 / 超时 / 超时 / 0.00 / 1.00 / 0.00；汇总 recall=0.4，precision=1.0。

## 采纳要点（改了什么）

- `scripts/run_eval.py`：
  - 抽出模块级 `run_cli_item(item, …)`（单条查询 × N 次运行，RuntimeError → `error` 记录），worker 无共享可变状态。
  - 新增 `run_cli_batch(evals, …, concurrency=1)`：`--concurrency > 1` 时用 `ThreadPoolExecutor.map`（**保持输入顺序**）有界并行；`1` 或单条查询时走原串行路径。
  - 新增 CLI 参数 `--concurrency`（默认 1 = 串行，**向后兼容**），并在 usage/docstring、SKILL.md 阶段 7、README 同步说明。
- `tests/test_hardening.py` +8 例：并行确实重叠（峰值并发 ≥2）且结果顺序、pass 汇总正确；默认 `--concurrency 1` 峰值并发恒为 1（不回退成并行）；`run_cli_item` 的 run_error 记录形状（`trigger_rate=None`、`pass=None`、`error` 非空）；`runs_per_query>1` 的取率与阈值语义（正/负查询在 rate==threshold 边界各判 pass/fail）、负查询全未触发判 pass；单轮中途 RuntimeError 不得泄漏部分 rate（整体转 error 记录）；`concurrency<=0` 钳制为串行（峰值并发恒 1）；并行下个别条目报错仍保持输入顺序且 error 落在原位置。
- 版本 bump `SKILL.md` 0.9.4 → 0.9.5；`README.md` 目录说明同步。

## 验证结果

- `python -m pytest tests/ -q`：**69 例全绿**（61 → 69）。
- `python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator`：见收尾记录。

## 学习点

- **真机评测的成本模型**：无头 LLM 单条查询可达 30–120s，串行评测的墙钟 ≈ 查询数 × 轮数 × 单条耗时，很快突破可接受上限。评测工具应默认保守、但**必须提供有界并行开关**，否则「跑完整基准」在实践中不可行。
- **并行只取独立单元**：每条 eval 查询是独立客户端进程、结果可加性，天然适合并行；聚合仍在收集后串行完成，ndjson/顺序由 `map` 保证，不牺牲结果可比性。
- **慢会掩盖噪声**：真机触发非确定性要求多轮取率；串行让「多轮」不可行，并行是让「多轮统计」变得负担得起的前提。
