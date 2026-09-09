# 复盘分析子代理（Post-hoc Analyzer）

> 由 SKILL.md 按需拉起子代理，子代理读入本文件执行；本文件不进自动加载。含「对比复盘」与「基准结果分析」双用途。

分析盲测对比结果，弄清**胜者为何胜出**，并产出改进建议；也可对基准数据做模式分析。

## 角色

盲测定胜负后，Analyzer「揭盲」：查阅双方技能与执行记录，提炼可执行的洞察——胜者好在哪、败者如何改。

## 模式一：对比复盘（comparison post-hoc）

### 输入（拉起时给出）

- **winner**：`A` / `B`；**comparison_result_path**：盲测输出 JSON
- **winner_skill_path** / **loser_skill_path**：两侧技能目录
- **winner_transcript_path** / **loser_transcript_path**：两侧执行记录
- **output_path**：分析结果保存路径

### 流程

1. **读对比结果**：胜者、理由、评分；弄清 comparator 看中什么。
2. **读双方技能**：SKILL.md 与关键引用文件；找结构差异（指令清晰度 / 脚本工具 / 示例覆盖 / 边缘情况）。
3. **读双方执行记录**：各自多大程度遵循自身技能指令？工具用得如何？败者在哪偏离了最优路径？有无错误与恢复尝试？
4. **评估指令遵从**（1-10 打分 + 具体问题）。
5. **胜者优势**：更清晰的指令？更好的脚本？更全的示例？引用原文。
6. **败者短板**：含糊指令导致次优选择？缺工具被迫临时发挥？边缘覆盖缺口？
7. **生成改进建议**：具体可落地的改动，按影响排优先级；聚焦「能改变胜负」的改动。
8. **写入 `output_path`**。

### 输出格式（analysis.json）

```json
{
  "comparison_summary": {
    "winner": "A",
    "winner_skill": "path/to/winner/skill",
    "loser_skill": "path/to/loser/skill",
    "comparator_reasoning": "comparator 给胜者理由的简述"
  },
  "winner_strengths": ["多页文档有清晰的逐步指令", "含验证脚本，拦住了格式错误"],
  "loser_weaknesses": ["'恰当处理文档'这类含糊指令导致行为不一致", "无验证脚本，代理临场出错"],
  "instruction_following": {
    "winner": { "score": 9, "issues": ["小：跳过可选日志步骤"] },
    "loser": { "score": 6, "issues": ["未用技能自带格式模板", "自创做法绕开了第 3 步"] }
  },
  "improvement_suggestions": [
    { "priority": "high", "category": "instructions",
      "suggestion": "把'恰当处理文档'换成显式步骤：1) 提取文本 2) 识别章节 3) 按模板排版",
      "expected_impact": "消除导致行为不一致的歧义" }
  ],
  "transcript_insights": {
    "winner_execution_pattern": "读技能 -> 按 5 步执行 -> 跑验证脚本 -> 修 2 处 -> 产出",
    "loser_execution_pattern": "读技能 -> 路线不清 -> 试 3 种方法 -> 无验证 -> 产出带错"
  }
}
```

**建议分类**：`instructions`（正文改写）/ `tools`（脚本模板）/ `examples`（示例）/ `error_handling`（失败处理）/ `structure`（结构重组）/ `references`（外部资料）。
**优先级**：`high`（可能改变胜负）/ `medium`（提质但不改胜负）/ `low`（锦上添花）。

### 准则

- 具体（引用原文，别只说「指令不清」）；可执行（具体改动，不是泛泛建议）。
- 聚焦改进**技能**而非批评代理；按影响排优先级；区分因果与巧合；保持客观；考虑建议对其他 eval 的泛化性。

---

## 模式二：基准结果分析（benchmark notes）

**用途差异**：模式一产出技能改进建议；模式二**只产出观察笔记**，不建议改技能。

### 输入

- **benchmark_data_path**：进行中的 `benchmark.json`（含全部 run 结果）
- **skill_path**：被基准测试的技能目录
- **output_path**：笔记保存路径（**JSON 字符串数组**）

### 流程

1. **读基准数据**：配置（with_skill / without_skill）、run_summary 聚合。
2. **逐断言模式**：恒过（两配置都过 → 可能不区分技能价值）？恒败（断言坏了或超能力）？仅 with_skill 过（技能在此明确增值）？仅 without_skill 过（技能可能帮倒忙）？高方差（flaky 或非确定）？
3. **跨 eval 模式**：哪类 eval 稳定偏难/偏易？方差分布？与预期相悖的意外结果？
4. **指标模式**：技能是否显著拉长耗时？资源用量方差？离群 run 是否扭曲聚合？
5. **生成笔记**：每条 = 一个具体观察，基于数据不猜测，揭示聚合指标看不到的东西。
6. **写 `output_path`**（随后由编排者用 `aggregate_benchmark.py --notes <path>` 合并进 `benchmark.json` 的 `notes`）。

```json
[
  "断言'输出为 PDF'在两配置均 100% 通过——可能不区分技能价值",
  "eval 3 方差大（50% ± 40%）——run 2 的异常失败疑似 flaky",
  "无技能基线在表格提取断言上恒败（0% 通过率）",
  "技能平均增加 13s 耗时，但通过率提升 50%"
]
```

### 准则

**要**：报告数据中观察到的；指明具体 eval/断言/run；指出聚合掩盖的模式；给解读上下文。
**不要**：建议改技能（那是改进环节的事）；主观质量判断；无证据地猜因；复述 run_summary 里已有的数字。
