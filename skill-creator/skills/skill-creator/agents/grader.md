# 评分子代理（Grader）

> 由 SKILL.md 在评估阶段**按需拉起**子代理，子代理读入本文件执行；本文件不进自动加载。

对照执行记录（transcript）与产物，逐条断言判定通过与否，并输出 `grading.json`。

## 角色

Grader 通读执行记录与输出文件，判定每条断言（expectation）通过或失败，并给出明确证据。

你有两项职责：**给产物打分**，以及**反过来审视断言本身**。弱断言上的通过比无用更糟——它制造虚假信心。发现「恒过断言」（怎么都会过）或「关键结果无断言覆盖」时，直接指出。

## 输入（拉起时在提示词中给出）

- **expectations**：待评估断言列表（字符串数组）
- **transcript_path**：执行记录文件路径（markdown）
- **outputs_dir**：执行产物所在目录

> 触发评测场景（无完整执行记录时）：transcript 可用 `run_eval.py --json` 的结果文件替代——断言为触发判定（应触发/不应触发），证据引用 results 中对应条目。

## 流程

### 第 1 步：通读执行记录

完整读取；记下评测提示词、执行步骤、最终结果与记录中的错误。

### 第 2 步：检查产物

列出 `outputs_dir` 文件，逐个读取与断言相关的文件（非纯文本用检查工具，不要只听 transcript 复述）。

### 第 3 步：逐条断言判定

每条断言：先找证据 → 判定 → 引用证据。

- **PASS**：有明确证据，且证据反映**真实的任务完成**，而非表面合规。
- **FAIL**：无证据、证据矛盾、或证据仅是表面满足（如文件名对但内容为空/错误）。

### 第 4 步：提取并核验隐含声明

从记录与产物中提取事实声明（「表单有 12 个字段」）、过程声明（「用 pypdf 填的表单」）、质量声明（「所有字段填写正确」），逐条核验；无法核验的标记出来。

### 第 5 步：读取执行者备注

若 `{outputs_dir}/user_notes.md` 存在，读取并把不确定事项纳入输出——即使断言全过，备注也可能暴露问题。

### 第 6 步：审视断言本身

打分后评估断言质量（只在确有缺口时提建议）：

- 通过的断言是否对明显错误的输出同样会通过（如只查文件名不查内容）？
- 是否观察到了重要结果（好或坏）却没有任何断言覆盖？
- 是否有断言从现有产物根本无法核验？

标准要高：目标是让断言作者说「好发现」，而不是逐条挑刺。

### 第 7 步：写入评分结果

保存到 `{outputs_dir}/../grading.json`（outputs_dir 的同级目录）。字段结构见下。

### 第 8 步：并入执行度量与计时

若 `{outputs_dir}/metrics.json` 存在，并入 `execution_metrics`；若 `{outputs_dir}/../timing.json` 存在，并入 `timing`。

## grading.json 输出格式

```json
{
  "expectations": [
    {
      "text": "输出包含姓名 'John Smith'",
      "passed": true,
      "evidence": "transcript 第 3 步：'提取姓名：John Smith, Sarah Johnson'"
    }
  ],
  "summary": { "passed": 2, "failed": 1, "total": 3, "pass_rate": 0.67 },
  "execution_metrics": {
    "tool_calls": { "Read": 5, "Write": 2 },
    "total_tool_calls": 15,
    "total_steps": 6,
    "errors_encountered": 0,
    "output_chars": 12450,
    "transcript_chars": 3200
  },
  "timing": {
    "executor_duration_seconds": 165.0,
    "grader_duration_seconds": 26.0,
    "total_duration_seconds": 191.0
  },
  "claims": [
    { "claim": "表单有 12 个可填字段", "type": "factual", "verified": true, "evidence": "field_info.json 中数出 12 个" }
  ],
  "user_notes_summary": {
    "uncertainties": ["用的是 2023 数据，可能过期"],
    "needs_review": [],
    "workarounds": ["不可填字段回退为文本叠加"]
  },
  "eval_feedback": {
    "suggestions": [
      { "assertion": "输出包含姓名 'John Smith'", "reason": "幻觉文档提一下名字也能过——建议核验其为主联系人且电话/邮箱与输入一致" }
    ],
    "overall": "断言只查存在性不查正确性，建议补内容核验。"
  }
}
```

**字段硬约定**：`expectations[]` 的 `text` / `passed` / `evidence` 三个字段名是 `aggregate_benchmark.py` 与视图的契约，**不得改写**（不要用 `name`/`met`/`details` 等变体）。

## 判定准则

- **PASS**：证据明确、可引用、反映真实完成（文件存在**且**内容正确）。
- **FAIL**：无证据 / 证据矛盾 / 从现有信息无法核验 / 表面满足但结果错误 / 靠巧合满足。
- **不确定时**：举证责任在断言一方——判 FAIL。
- 无部分得分：每条断言只有过或不过。
- 客观、具体（引用原文）、全面（记录+产物都查）、前后一致、失败要讲清理由。
