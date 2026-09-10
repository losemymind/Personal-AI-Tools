# 采纳升级：修复 evals.json 模板与评测链的键名漂移

## 基本信息
- 日期：2026-09-10
- 需求与证据：用两创建器做端到端能力验证时，按 `templates/evals.json.template` 写出的 evals.json 跑 `run_eval.py` 直接崩溃：
  ```
  File ".../run_eval.py", line 72, in run_heuristic
      triggered = classify(item["query"], description)
  KeyError: 'query'
  ```
- 诊断层：脚本/工具层（模板与脚本对同一 schema 的键名不一致）。

## 问题
- **权威键是 `query`**：`references/benchmark-schema.md`、`run_eval.py`、`run_loop.py`、`tests/test_quant_eval.py` 全部使用 `query`。
- **偏离点两处**：`templates/evals.json.template` 用 `prompt`（2 处）；`run_trigger_tests.py` 读 `ev.prompt`、输出结果也用 `prompt`。
- 后果：用户按官方模板落 evals.json 后，评测链第一步即 `KeyError` 崩溃；静态校验器（`validate_skills.py`）不检查 evals 内容，故发布门无法发现。

## 采纳要点（改了什么）
- `templates/evals.json.template`：`prompt` → `query`（对齐权威 schema）。
- `scripts/utils.py`：新增 `eval_query(item)`——优先 `query`，回退 `prompt`（兼容旧文件，避免 KeyError）。
- `scripts/run_eval.py`：heuristic 与 cli 两条路径改用 `eval_query`。
- `scripts/run_trigger_tests.py`：改用 `eval_query` 读取；结果 JSON 键 `prompt` → `query`，打印同步。
- 未改 `run_loop.py`：它经 `run_eval.run_heuristic` 取值，修 run_eval 即覆盖。

## 验证
- 新增 `tests/test_eval_schema.py`（4 例）：模板必须含 `query` 且不含 `prompt`（防漂移回归）；`eval_query` 优先/回退/空值；legacy `prompt` 文件跑 `run_eval.py` 不再崩溃；`run_trigger_tests.py` 读 `query` 且输出 `query`。
- skill-creator 回归 16 → **20 例全绿**；成品 `validate_skills.py --strict` 自检通过。
- 端到端复验：改前 `run_eval.py` 对模板产出的 evals.json 崩溃；改后 `run_eval.py`（`query` 键）正常出 precision/recall。
- 版本：`SKILL.md` 0.6.1 → **0.6.2**（patch，脚本/schema 修复，不改变方法论）。

## 学习点
- **模板是 schema 的第二事实源，必须与脚本同步测试**：文档/schema 声明了权威键，但没有任何测试锁住「模板 == 脚本读的键」，漂移便长期潜伏。修复不止改模板，更补了「模板键名断言」这类契约测试。
- **静态校验器不覆盖产物的运行时数据契约**：`validate_skills.py` 校验 SKILL.md frontmatter/章节，不检查 `evals.json`；因此「结构全绿」不等于「评测链能跑」。端到端功能验证（真跑一次脚本）不可被静态门禁替代。
- **向后兼容优于硬切**：新增 `eval_query` 助手让旧 `prompt` 文件继续可用，升级不破坏既有技能目录里的 evals。
