# 对比记录：coding-discipline vs 上游 andrej-karpathy

## 基本信息
- 日期：2026-09-14
- 需求描述：把 multica-ai/andrej-karpathy-skills 的四条 LLM 编码行为准则整理为可安装技能
- 上游来源（用户指定）：`multica-ai/andrej-karpathy-skills`（MIT，213k stars）
- 上游候选（索引命中）：`skills/andrej-karpathy`，src `sickn33/agentic-awesome-skills`
- 对比对象：临时获取 `sickn33/agentic-awesome-skills@skills/andrej-karpathy/SKILL.md`（与用户指定源同源内容）

## 对比报告

```text
LOCAL      coding-discipline  total 0.76
  quality : trigger_clarity=1.00  example_available=1.00  limitations_declared=1.00
            risk_declared=1.00   security_guardrails=0.80 metadata_complete=1.00
  struct  : progressive_disclosure=0.80 resource_organization=0.00
            script_reuse=0.00        body_size_control=1.00
  body: 137 lines | files: 2（SKILL.md + evals/evals.json）

UPSTREAM   andrej-karpathy       total 0.73
  quality : 同 LOCAL，仅 metadata_complete=0.75
  struct  : 同 LOCAL（progressive_disclosure=0.80 等）
  body: 120 lines | files: 1
```

## 结论
- 优者：**自建**（total +0.03，quality +0.05）
- 采纳决定：采纳自建版本 `coding-discipline`，按流程安装归档

## 差异分析
- **metadata_complete**：上游 0.75 低于自建 1.00——其 frontmatter 含 `source`/`source_repo`/`license`/`tags`/`tools`/`date_added`/`author` 等字段，与本库「frontmatter 只保留 `name`/`description`/`risk`/`category`，来源进创建记录台账」的约定相反；在本库约定下自建更规范。
- **结构**：双方均为单文件 + 无 `scripts/`/`references/`（本库另带 `evals/` 触发用例），持平。
- **触发/示例/限制/风险**：双方齐备，持平。

## 提炼的学习点
- 上游把「Tradeoff：对 trivial 任务放宽」置于正文前部，位置醒目——本库保留该提示（概述 + 限制章节各一处）。
- 上游示例用「Better response」组织正面范例——本库改为「反例 → 正例」对照，更贴合纠错场景。
- 上游每条准则以「粗体一句话 + 要点清单」呈现，信息密度高——本库沿用该结构。

## 改进建议
- 无（自建持平/更优）。可选：把本技能回馈上游社区。
