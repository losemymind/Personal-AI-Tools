# 评测与基准 JSON Schema（benchmark-schema）

> 来源：移植自 Anthropic `anthropics/skills/skills/skill-creator/references/schemas.md`，字段名与本地 skill-creator 的 `skill_eval.py` / `skill_optimize.py` / `skill_benchmark.py` 对齐。客户端无关（claude/opencode/codex/deepseek 通用）。

## 目录

- 触发评测输入与 evaluation 结果
- skill_optimize 开发验证与最终测试
- grading / analyzer / timing / metrics 产物
- benchmark 汇总与工作区布局

## evals.json（触发评测集）

技能目录 `evals/evals.json`（或直接挂在技能目录下的 `evals.json`）：

```json
{
  "skill_name": "example-skill",
  "evals": [
    {
      "id": 1,
      "query": "用户会真实说的话（应触发该技能）",
      "should_trigger": true,
      "expected_output": "预期结果描述"
    },
    {
      "id": 2,
      "query": "近似干扰项（关键词重叠但应不触发）",
      "should_trigger": false,
      "expected_output": ""
    }
  ]
}
```

字段：
- `skill_name`：与 SKILL.md frontmatter 的 `name` 一致
- `evals[].id`：唯一整数
- `evals[].query`：真实用户提示词（不是抽象请求）
- `evals[].should_trigger`：是否应触发本技能
- `evals[].expected_output`：成功时的人类可读描述（可选）

## evaluation 结果（skill_eval 输出）

`skill_eval.py --json` 输出，同时含每条查询与汇总：

```json
{
  "skill_name": "example-skill",
  "description": "当前 description",
  "mode": "heuristic",
  "results": [
    {
      "query": "...",
      "should_trigger": true,
      "triggered": true,
      "pass": true
    }
  ],
  "summary": {
    "passed": 8, "failed": 2, "errors": 1, "total": 10,
    "attempted": 11, "coverage": 0.909,
    "precision": 0.9, "recall": 0.8
  }
}
```

- `total` 仅计有效评测查询，`attempted` 包含运行错误；`coverage=total/attempted`，无查询为 0。
- `precision` / `recall` 无分母时为 null（文本 N/A）；全部运行错误不能解释为 100% 准确。
- 顶层另记录 `client` / `model`（heuristic 为 null）、`threshold`、`runs_per_query`，便于重现。
- 默认仅出报告，退出码 0；`--fail-on-error` 在 errors>0 时退出 1，`--fail-on-mismatch` 在 failed>0 时退出 1，组合使用可作质量门。报告先写出再返回失败码。

## skill_optimize 迭代记录（description 自动优化）

`skill_optimize.py --report` 输出为最终 JSON；`history[]` 记录开发 train/validation 得分。独立最终查询集只在选优后运行一次：

```json
{
  "schema_version": 2,
  "skill_name": "example-skill",
  "original_description": "...",
  "best_description": "...",
  "best_score": "4/4",
  "selection_set": "validation",
  "evaluation_mode": "heuristic",
  "confirmation": "not_run",
  "final_evaluation": null,
  "iterations_run": 3,
  "exit_reason": "train_all_passed (iteration 3)",
  "holdout": 0.4,
  "history": [
    {
      "iteration": 1,
      "description": "...",
      "train_passed": 6, "train_total": 6,
      "train_errors": 0,
      "validation_passed": 4, "validation_total": 4, "validation_errors": 0,
      "validation_results": [],
      "test_passed": 4, "test_total": 4,
      "train_results": []
    }
  ]
}
```

- `best_description` 按开发 validation 通过率选取；该集参与反复选择，不能充当独立测试。开发集按 should_trigger 分层 60/40 切分（`--holdout 0.4`）。样本过少或 holdout=0 时退回 train，`selection_set` 显式标记；开发查询重复会被拒绝。
- `history[].test_passed/test_total` 保留为 validation 的兼容别名；顶层 `legacy_test_fields` 说明其含义。`seed`、`client`、`model`、`threshold`、`runs_per_query` 记录运行参数。
- `--eval-mode heuristic|cli` 决定开发评分方式；`--improve-mode` 只决定怎样生成候选。CLI 会评测写入临时安装副本的候选描述。
- `--final-eval-set` 必须与开发集查询不重叠；最后只评测选定描述一次。`final_evaluation` 含 mode/results/summary，summary 与 skill_eval 一致；默认 `--final-mode cli`，未传最终集则为 null。
- `confirmation`：not_run（未测）、proxy_only（词面通过）、dispatch_passed（opencode 派发通过）、structured_passed（Claude 结构化调用/读取信号通过）、failed（触发不符）、error（运行/改写失败）。旧 approximate_passed 仅属于历史全文匹配报告。最终查询与结果不进入改写提示或候选选择；最终集一经用于指导后续调整，需换新集。
- 优化/评测错误或最终测试不通过返回 1，仍保留报告。缺少最终测试或只测 heuristic 不能宣称已验证真实触发。

## grading.json（单次运行评分，供 skill_benchmark 读取）

每个运行目录 `<workspace>/iteration-N/eval-<name>/<config>/run-1/grading.json`：

```json
{
  "expectations": [
    { "text": "输出包含 X", "passed": true, "evidence": "..." }
  ],
  "summary": { "passed": 1, "failed": 0, "total": 1, "pass_rate": 1.0 },
  "execution_metrics": { "total_tool_calls": 15, "errors_encountered": 0, "output_chars": 12450 },
  "timing": { "total_duration_seconds": 191.0 },
  "user_notes_summary": { "uncertainties": [], "needs_review": [], "workarounds": [] }
}
```

> 注意：`expectations[].text` / `.passed` / `.evidence` 三个字段名是视图与汇总的约定，不要改名为其他写法。
>
> `grading.json` 由**评分子代理**产出（`agents/skill_grader.md`，拉起或内联执行均可）；完整字段（claims / user_notes_summary / eval_feedback 等）见该文件。

## analyzer 笔记（skill_benchmark --notes 输入）

分析子代理（`agents/skill_analyzer.md` 模式二）产出的观察笔记为 **JSON 字符串数组**，经脚本合并进 `benchmark.json` 的 `notes`：

```bash
python scripts/skill_benchmark.py <workspace>/iteration-N --skill-name <名> --notes <notes文件>
```

## timing.json（可选，运行计时）

`<run-dir>/timing.json`，由 `skill_scenario.py` 产出。**必写**：`total_duration_seconds`（墙钟秒）与 `timed_out`（是否超时）；若客户端回报了 token 数与精确毫秒，再补 `total_tokens` / `duration_ms`（可选）：

```json
{
  "total_duration_seconds": 23.3,
  "timed_out": false,
  "total_tokens": 84852,
  "duration_ms": 23332
}
```

## metrics.json（可选，场景执行计数）

`<run-dir>/metrics.json`，由 `skill_scenario.py` 产出（与 `timing.json`/`grading.json` 同级；`outputs/` 是其子目录）：

```json
{
  "client": "opencode",
  "model": "",
  "skill": "example-skill",
  "returncode": 0,
  "output_chars": 12450,
  "total_tool_calls": 15
}
```

- **读取契约**：评分子代理从 `{outputs_dir}/../metrics.json`（即 run 根目录）并入 `grading.json` 的 `execution_metrics`。汇总器优先读 run 根原始 metrics/timing，再回退评分内嵌字段；原始记录的真实 0 不能被回退值覆盖。metrics/timing 可省略以兼容外部执行器；提供后必须为有效 JSON 对象，执行失败、超时不能被评分结果覆盖。

## benchmark.json / benchmark.md（skill_benchmark 产物，schema_version=2）

由 `skill_benchmark.py <workspace>/iteration-N` 生成。默认报告模式仍退出 0；`--strict` 写完报告后，在存在 error/incomplete 或无完整配对通过率时退出 1。未知成本本身不使 strict 失败。

```json
{
  "schema_version": 2,
  "metadata": {
    "skill_name": "example-skill", "skill_path": null,
    "executor_model": null, "executor_models": [], "clients": ["opencode"],
    "unknown_model_runs": 2, "unknown_client_runs": 0,
    "timestamp": "2026-09-29T00:00:00Z", "evals_run": [1],
    "runs_per_configuration": 1,
    "primary_configuration": "with_skill", "baseline_configuration": "without_skill"
  },
  "runs": [{
    "eval_id": 1, "configuration": "with_skill", "run_number": 1,
    "run_path": "eval-example/with_skill/run-1", "status": "completed", "issues": [],
    "execution_status": "completed", "client": "opencode", "model": null, "models": [],
    "model_source": null, "requested_model": null, "tokens_source": null, "tool_calls_source": null,
    "measurement_sources": {"tokens": null, "time_seconds": "timing.json.total_duration_seconds", "tool_calls": null},
    "result": {"pass_rate": 1.0, "passed": 1, "failed": 0, "total": 1,
               "time_seconds": 42.5, "tokens": null, "tool_calls": null},
    "expectations": [{"text": "正确完成", "passed": true, "evidence": "产物核验"}], "notes": []
  }],
  "run_summary": {
    "with_skill": {
      "runs": 1, "attempted": 1, "completed": 1, "errors": 0, "incomplete": 0, "coverage": 1.0,
      "pass_rate": {"n": 1, "mean": 1.0, "stddev": 0.0, "min": 1.0, "max": 1.0},
      "time_seconds": {"n": 1, "mean": 42.5, "stddev": 0.0, "min": 42.5, "max": 42.5},
      "tokens": {"n": 0, "mean": null, "stddev": null, "min": null, "max": null}
    },
    "without_skill": {"...": "同上结构；runs[] 中也有对应记录，此处省略"},
    "delta": {"primary": "with_skill", "baseline": "without_skill",
              "expected_pairs": 1, "paired_samples": 1, "coverage": 1.0,
              "duplicate_keys": [], "identity_mismatches": [],
              "metric_pairs": {"pass_rate": 1, "time_seconds": 1, "tokens": 0},
              "pass_rate": "+1.00", "time_seconds": "+13.0", "tokens": null,
              "note": "cost delta unavailable where any paired measurement is missing"}
  },
  "notes": []
}
```

### 尝试、有效评分与缺失值

- `runs[]` 记录所有发现的 run 目录，即使缺少或损坏 grading 也保留。`runs` 是 attempted 的兼容别名；`completed` 为有效评分且无已知执行失败的次数，errors 为明确失败/超时，incomplete 为评分缺失/损坏、指标文件无效或数据矛盾；三者之和等于 attempted。coverage=completed/attempted，无尝试为 0。
- `status` 为 completed/error/incomplete，`issues[]` 保留原因码与文件/字段。执行失败优先于评分，失败运行即使得到 100% 的 grading 也不进入通过率。`execution_status=unknown` 表示外部执行器未提供退出状态，不能宣称已验证执行成功。
- summary 的 passed/failed/total 必须是非负整数、total>0、passed+failed=total。缺省 pass_rate 从计数推导；提供时必须为 [0,1] 有限数且与比值一致（允许两位小数舍入）。非空 expectations 必须是完整列表，布尔 passed 的计数与 summary 一致；summary-only 旧记录可读。
- tokens/time/tool_calls 未知为 null，不能用 output_chars 估算 tokens。数值必须有限且非负；真实 0 保留。每项统计记录有效 n，n=0 的均值、标准差、最小、最大均为 null；Markdown 显示 N/A。
- 通过率仅统计 completed；成本统计所有尝试中已知的观测值，含失败尝试，避免隐藏失败开销。`measurement_sources` 指明原始字段。
- model/client 来自 metrics（缺省回退内嵌 execution_metrics）。保留 models/model_source/requested_model/tokens_source/tool_calls_source，区分客户端观测与请求参数。非空观测 models 集合优先于单个 model；多个已知模型时 model=null，不用 requested_model 伪装为单模型。空集合表示未记录的默认模型，保留未知。metadata 汇总模型/客户端集合及未知次数；仅当全部尝试明确记录同一模型时设置 executor_model，其他情况为 null。

### 配对与增益边界

- configuration 默认为 with_skill/without_skill；`--primary`/`--baseline` 显式指定角色，也识别 skill/treatment、baseline/control/no_skill 别名。未知角色不自动拿无关目录作对照。
- 配对键为 **eval_id + run_number**。eval_id 优先来自场景的 eval_metadata.json，缺省用 eval 目录名；不同场景或不同重复编号不能配对。同一配置重复键标记歧义，不任选一条。
- expected_pairs 是两配置已观察键的并集大小；paired_samples 只计两侧各有唯一 completed 记录且无已知 models 集合/client 差异的配对；coverage 为其比例。这里只覆盖已发现目录，**无法证明未创建目录的计划场景也已运行**。
- 仅所有已观察键完整配对时输出通过率差值；缺失、失败、重号或已知模型/客户端不一致时 delta=null，并给 note，避免幸存样本制造增益。未记录模型/客户端的旧数据仍可描述性比较，但身份一致性未经确认。
- 成本差值另要求所有配对都提供该指标；否则仅该项 delta=null。差值方向为 primary−baseline，沿用原字符串格式。均值与标准差是描述统计；一次配对不证明显著性或因果关系。
- benchmark.md 展示每项 n、各配置 attempted/completed/errors/incomplete/coverage 和配对覆盖。分析时先检查完整性与模型身份，再解释差值及方差。

## 工作区布局（约定）

```
<workspace>/iteration-N/
└── eval-<descriptive-name>/
    ├── with_skill/
    │   └── run-1/
    │       ├── transcript.md      # skill_scenario.py
    │       ├── metrics.json       # skill_scenario.py（run 根，见上）
    │       ├── timing.json
    │       ├── outputs/
    │       │   └── response.txt   # skill_scenario.py
    │       └── grading.json       # 评分子代理
    └── without_skill/
        └── run-1/
            └── ...                # 同结构
```

对比顺序：先检查尝试覆盖、配对完整性与模型/客户端身份，再解释可用的通过率和成本差值。高方差提示需要更多重复运行；不要仅凭标准差把原因定为 flaky。
