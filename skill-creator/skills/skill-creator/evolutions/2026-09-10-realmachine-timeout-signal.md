# 纪律→工具：超时丢弃部分输出 → run_eval 保留已发生的触发信号

## 基本信息
- 日期：2026-09-10
- 版本：skill-creator 0.9.5 → 0.9.6
- 触发来源：0.9.5 完整真机基准（14 查询 × 3 轮）暴露的召回低估

## 需求与证据

**证据（真机基准，0.9.5）**：批次 1 中「改进现有技能的描述…」「评估一下这个技能的触发准确性」两次运行撞满 `--timeout 120`，被记为 `run_error`；批次 2「帮我写单元测试」同样超时。而 `run_cli` 在 `TimeoutExpired` 时**直接抛错、丢弃已捕获的部分 stdout**——但客户端派发技能工具（`tool_use`/`tool:"skill"`）通常发生在技能启动的耗时任务**之前**。因此一次真实触发若随后卡在长任务上超时，会被误判为 `error`，**系统性低估 recall**。

## 采纳要点（改了什么）

- `scripts/run_eval.py`：
  - 新增 `_partial_text(e)`：拼接 `TimeoutExpired.stdout/stderr`（text 模式为 str，防御性解码 bytes）。
  - `run_cli` 的 `except TimeoutExpired`：先 `detect_triggered(client, _partial_text(e), skill_name)`——**已见本技能派发即返回 True**；无触发证据才抛 `RuntimeError`（仍是 run_error）。
  - 判定只认真实技能工具事件（opencode `tool_use` 且 `tool=="skill"` 且 `input.name==本技能`），不做全文子串匹配，故 EOF 截断的半行 JSON 不会被误读为触发。
- `tests/test_hardening.py` +3 例：超时+已派发 → True；超时+无触发证据 → 仍 run_error；`_partial_text` 的 bytes/None 形状。
- 版本 bump `SKILL.md` 0.9.5 → 0.9.6；阶段 7 说明补充「超时保留已发生的触发」语义。

## 验证结果

- `python -m pytest tests/ -q`：**72 例全绿**（64 → 72，含并发与超时两组新例）。
- 成品 strict / 能力库 strict（5 技能）/ `build_catalog.py --check` 全绿。

**0.9.6 真机复跑**（14 查询 × 3 轮，`deepseek-v4-flash` + opencode，`--concurrency 7 --timeout 120`）：
- 批次 1：7/7 全部评分、**0 run_error**（0.9.5 时是 5 评分 + 2 超时错误）；此前超时的 q3/q4 部分输出**未见触发事件**，故正确转为 non-trigger（0.0 / 0.333）。
- 批次 2：6 条负例中 5 条正确不触发，1 条（`帮我写单元测试`）超时且部分输出无触发证据 → 仍正确记为 run_error。
- 正例得分（2/8 过线，recall ≈ 0.25）、precision 100%（无假阳性）。

> 关键：错误数从 3 降到 1 不是靠放宽判定，而是靠**不再丢弃已有信号**；无触发证据的超时仍如实报错。

## 学习点

- **超时 ≠ 无信号**：阻塞型 CLI 在超时前可能已完成关键动作（此处是技能派发），评测器应解析部分输出、保留已发生的事实，否则慢=假阴性。
- **保留信号与放宽判定是两回事**：只对「真实触发事件」放行，无证据的超时仍报错——既修低估，又不引入假阳性。
- **确定性单测是不可替代的证明**：真机很难稳定复现「超时且部分输出含触发」，故该分支由单测（构造 `TimeoutExpired(output=…)`）精确钉死，真机复跑只作回归佐证。
