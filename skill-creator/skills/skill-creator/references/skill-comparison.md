# 技能对比标准（Skill Comparison）

定义 skill-creator「阶段 5.5 与上游候选对比择优」的评分维度，由 `compare_skills.py` 自动计算，供执行代理结合用户需求做最终判断。

## 评分模型

**总分 = 质量得分 × 60% + 结构得分 × 40%**

| 维度 | 权重 | 计算方式 |
|---|---|---|
| 质量（Quality） | 60% | 6 个子维度平均 |
| 结构（Structure） | 40% | 4 个子维度平均 |

## 质量 6 维（对应 quality-bar 的检查项）

| 维度 | 满分条件 | 权重说明 |
|---|---|---|
| 触发清晰度 `trigger_clarity` | 存在中英文「何时使用」章节 | 决定 LLM 是否触发，最重要 |
| 示例可得性 `example_available` | 有「示例/Examples」章节；退化：有代码块给 0.5 | 质量门槛第 4 项 |
| 限制声明 `limitations_declared` | 有「限制/Limitations」章节 | 质量门槛第 5 项 |
| 风险声明 `risk_declared` | frontmatter 的 `risk` 是合法值 | 质量门槛第 3 项 |
| 安全护栏 `security_guardrails` | offensive 技能必有免责声明；无危险管道 | 安全审查核心 |
| 元数据完整性 `metadata_complete` | `name` + `description` 齐全 | 质量门槛第 1 项 |

## 结构 4 维（对应 skill-anatomy 的渐进式披露）

| 维度 | 满分条件 | 评分逻辑 |
|---|---|---|
| 渐进式披露 `progressive_disclosure` | 有 `references/` 目录 | 无 references 时 >500 行给 0.4 |
| 资源组织 `resource_organization` | 有 scripts/references/examples/templates 子目录 | 按实际拥有数/3 封顶 |
| 脚本复用 `script_reuse` | 有 `scripts/` 目录 | 重复任务是否脚本化 |
| 正文行数控制 `body_size_control` | ≤1000 行 | 1000-1500 给 0.5，>1500 给 0.2 |

## 对比与择优流程

1. 先运行 `compare_skills.py` 得到双方各项分数。
2. **只看总分还不够**——检查双方差距所在的维度是否与用户需求相关：
   - 需求强调"可复现、高质量"→ 重点看结构维（脚本复用、渐进式披露）
   - 需求强调"可靠触发"→ 重点看触发清晰度
   - 需求强调"安全"→ 重点看安全护栏、风险声明
3. 综合总分 + 需求相关维度 + 语义贴合度，由执行代理向用户给出建议：
   - 上游更优 → 建议采纳上游（或借鉴优势后改进自建）
   - 自建更优 → 采纳自建
4. 对比结果记录到 `evolutions/`。

## 反馈闭环（择优后的学习）

- **上游更优时**：分析上游在优势维度上的做法（章节组织、门控设计、资源结构），提炼为可复用的方法论要点，追加到 skill-creator 的 SKILL.md 或本文件。
- 记录模板：`evolutions/<日期>-compare-<技能名>.md`，内容包含：对比报告、优势维度分析、提炼的学习点、改进建议。
- 定期 review `evolutions/` 汇总改进建议 → 迭代 skill-creator。

## 限制

- 自动评分衡量的是**结构与质量门槛**，不衡量领域知识深度与语义贴合度——最终择优需结合代理判断与用户需求。
- 行数/资源判断基于文件系统启发式，大型复杂技能（如 loki-mode）可能被低估，需人工复核。