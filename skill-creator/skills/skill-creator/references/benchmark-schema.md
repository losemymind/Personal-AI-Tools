# 评测与基准 JSON Schema（benchmark-schema）

> 来源：移植自 Anthropic `anthropics/skills/skills/skill-creator/references/schemas.md`，字段名与本地 skill-creator 的 `run_eval.py` / `run_loop.py` / `aggregate_benchmark.py` 对齐。客户端无关（claude/opencode/codex/deepseek 通用）。

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
      "expected_output": "预期结果描述",
      "files": []
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
- `evals[].files`：可选输入文件列表

## evaluation 结果（run_eval 输出）

`run_eval.py --json` 输出，同时含每条查询与汇总：

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
    "passed": 8, "failed": 2, "total": 10,
    "precision": 0.9, "recall": 0.8
  }
}
```

## run_loop 迭代记录（description 自动优化）

`run_loop.py --report` 输出为最终 JSON；`history[]` 记录每次迭代的 train/test 得分与 description：

```json
{
  "skill_name": "example-skill",
  "original_description": "...",
  "best_description": "...",
  "best_score": "8/10",
  "iterations_run": 3,
  "exit_reason": "all_passed",
  "holdout": 0.4,
  "history": [
    {
      "iteration": 1,
      "description": "...",
      "train_passed": 6, "train_total": 6,
      "test_passed": 4, "test_total": 4,
      "train_results": []
    }
  ]
}
```

- `best_description` 按 **test 得分** 选取（防过拟合 train）
- train/test 采用 should_trigger 分层的 60/40 split（`--holdout 0.4`）

## grading.json（单次运行评分，供 aggregate_benchmark 读取）

每个运行目录 `<workspace>/iteration-N/eval-<name>/<config>/run-1/grading.json`：

```json
{
  "expectations": [
    { "text": "输出包含 X", "passed": true, "evidence": "..." }
  ],
  "summary": { "passed": 2, "failed": 1, "total": 3, "pass_rate": 0.67 },
  "execution_metrics": { "total_tool_calls": 15, "errors_encountered": 0, "output_chars": 12450 },
  "timing": { "total_duration_seconds": 191.0 },
  "user_notes_summary": { "uncertainties": [], "needs_review": [], "workarounds": [] }
}
```

> 注意：`expectations[].text` / `.passed` / `.evidence` 三个字段名是视图与汇总的约定，不要改名为其他写法。
>
> `grading.json` 由**评分子代理**产出（`agents/grader.md`，拉起或内联执行均可）；完整字段（claims / user_notes_summary / eval_feedback 等）见该文件。

## analyzer 笔记（aggregate_benchmark --notes 输入）

分析子代理（`agents/analyzer.md` 模式二）产出的观察笔记为 **JSON 字符串数组**，经脚本合并进 `benchmark.json` 的 `notes`：

```bash
python scripts/aggregate_benchmark.py <workspace>/iteration-N --skill-name <名> --notes <notes文件>
```

## timing.json（可选，运行计时）

`<run-dir>/timing.json`，在完成任务通知收到 `total_tokens`/`duration_ms` 时立即写入：

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

## benchmark.json / benchmark.md（aggregate_benchmark 产物）

由 `aggregate_benchmark.py <workspace>/iteration-N` 生成到该目录下：

```json
{
  "metadata": {
    "skill_name": "...", "skill_path": "...",
    "executor_model": "<model>",
    "timestamp": "2026-09-03T00:00:00Z",
    "evals_run": [1, 2],
    "runs_per_configuration": 3
  },
  "runs": [{
    "eval_id": 1, "configuration": "with_skill", "run_number": 1,
    "result": { "pass_rate": 0.85, "passed": 6, "failed": 1, "total": 7,
                 "time_seconds": 42.5, "tokens": 3800, "tool_calls": 18, "errors": 0 },
    "expectations": [], "notes": []
  }],
  "run_summary": {
    "with_skill": {
      "pass_rate": {"mean": 0.85, "stddev": 0.05, "min": 0.8, "max": 0.9},
      "time_seconds": {"mean": 45.0, "stddev": 12.0, "min": 32.0, "max": 58.0},
      "tokens": {"mean": 3800, "stddev": 400, "min": 3200, "max": 4100}
    },
    "without_skill": { "...": "同上结构" },
    "delta": { "pass_rate": "+0.50", "time_seconds": "+13.0", "tokens": "+1700" }
  },
  "notes": []
}
```

- `configuration` 取值约定：`with_skill` / `without_skill`（有技能 vs 无技能基线）——比较择优时直接读 delta
- `run_summary` 给出 mean ± stddev，避免只看单次结果的下结论
- `benchmark.md` 为同一数据的人类可读表格（pass rate / time / tokens + delta）

## 工作区布局（约定）

```
<workspace>/iteration-N/
└── eval-<descriptive-name>/
    ├── with_skill/
    │   └── run-1/
    │       ├── grading.json
    │       └── timing.json
    └── without_skill/
        └── run-1/
            ├── grading.json
            └── timing.json
```

对比优先级：先看 delta 的 pass_rate（技能相对基线的提升）；其次看 tokens/time 的开销是否值得；高方差（stddev 大）的 eval 视为 flaky，需更多 run 或换提示词。