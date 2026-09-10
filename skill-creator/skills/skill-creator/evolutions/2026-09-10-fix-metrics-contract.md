# 修复记录：基准 metrics.json 契约断裂 + 汇总口径

## 基本信息
- 日期：2026-09-10
- 需求：对 skill-creator 成品做只读审阅，修复已确认的产物契约缺陷与口径问题。
- 来源：本仓库自审（无上游对照；缺陷均为本地实现问题）。

## 缺陷与修复
- **C1 metrics.json 写入/读取路径不一致（数据丢失）**：`run_scenario.py` 把 `metrics.json` 写到 run 根目录（与 `timing.json` 同级），而 `agents/grader.md` 却读 `{outputs_dir}/metrics.json`（`outputs/` 子目录）；同一句里 `timing.json` 读的是 `{outputs_dir}/../timing.json`（run 根）。结果 `metrics.json` 成为只写无人读的死数据，`execution_metrics` 拿不到 `total_tool_calls`，`aggregate_benchmark.py` 的 `tool_calls` 恒为 0。
  - 修复：`grader.md` 路径改为 `{outputs_dir}/../metrics.json`；`aggregate_benchmark.py` 增加确定性回退——`execution_metrics` 缺字段时直接读 run 根 `metrics.json`（不再只依赖 LLM 评审环节）。
- **C2 tool 计数脆弱**：`run_scenario.py` 用 `raw.count('"type":"tool"')` 数字符串，依赖客户端 JSON 无空格。改为新增 `count_tool_calls()`，逐行 `json.loads` 后按 `type == "tool"` 计数（纯文本输出自然得 0）。
- **C3 schema 未记录**：`references/benchmark-schema.md` 的工作区布局未列 `metrics.json`/`outputs/`，是 C1 漂移的根因。补 `metrics.json` 小节与读取契约，并把布局图补全。
- **C4 run_loop 选优口径**：`run_loop.py` 原按 `test_passed` 原始计数选优，test 集规模不同或为空时不可比。新增 `_test_rank()`，按 test **通过率**排序、并列回退 passed 计数。
- **C5 run_eval 汇总口径**：`summarize()` 的 `total` 原含 run errors，而 `passed/failed` 不含，显示「x/total passed」易误读。改为 `total` 只计已评分查询（`passed + failed == total`），运行错误单列 `errors`。

## 版本
- `0.9.0 → 0.9.1`（patch：缺陷修复，无方法论变更）。

## 验证
- `python -m pytest tests/ -q`：46 例全绿（新增 5 例：run_scenario tool 计数、aggregate 回退、grader 路径契约、run_eval 口径、run_loop 排序）。
- 成品 strict 自检 + 能力库 strict（5 技能）均通过。
- `.opencode/skills/skill-creator/` 安装副本已同步 7 个改动文件（逐字节一致）。

## 学习点
- **跨部件产物要有单一契约来源**：`metrics.json` 的位置同时被脚本写、被子代理读、被聚合器消费，却无任何一处成文，导致写读漂移。修复同时把它写进 schema 并让确定性脚本直接消费——「纪律能被机械消费」优于「只写在子代理指令里」。
- **确定性回退优先于依赖 LLM 环节**：聚合器直接读 `metrics.json`，使基准指标不再依赖评分子代理是否照做，回退逻辑可被 pytest 钉住。
