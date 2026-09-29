# 技能对比标准（Skill Comparison）

定义 skill-creator「先查后建与上游择优」的静态筛查维度，由 `skill_compare.py` 自动计算。采纳结论还需要相同真实场景的产出证据。

## 评分模型

**总分 = 质量得分 × 60% + 结构得分 × 40%**

| 维度 | 权重 | 计算方式 |
|---|---|---|
| 质量（Quality） | 60% | 6 个子维度平均 |
| 结构（Structure） | 40% | 4 个子维度平均 |

## 质量 6 维（对应 quality-bar 的检查项）

| 维度 | 满分条件 | 权重说明 |
|---|---|---|
| 触发章节 `trigger_clarity`（兼容字段名） | 存在中英文「何时使用」章节 | 只检查章节存在；真实触发由 description 和客户端评测确认 |
| 示例可得性 `example_available` | 有「示例/Examples」章节；退化：有代码块给 0.5 | 质量门槛第 4 项 |
| 限制声明 `limitations_declared` | 有「限制/Limitations」章节 | 质量门槛第 5 项 |
| 风险声明 `risk_declared` | frontmatter 的 `risk` 是合法值 | 质量门槛第 3 项 |
| 安全护栏 `security_guardrails` | offensive 技能必有免责声明；非 offensive 且无（fenced 代码块内的）危险管道 | 无危险内容时默认给 0.8（无法自动确认即留余量） |
| 元数据完整性 `metadata_complete` | `name`/`description`/`risk`/`category` 齐全 | 质量门槛第 1 项 |

## 结构 4 维（对应 skill-anatomy 的渐进式披露）

| 维度 | 满分条件 | 评分逻辑 |
|---|---|---|
| 渐进式披露 `progressive_disclosure` | references 内有非空文件 | 无有效 references 时 >500 行给 0.4 |
| 资源组织 `resource_organization` | scripts/references/examples/templates 内有有效文件 | 按有效资源目录数/3 封顶，空目录、缓存、符号链接不加分 |
| 脚本存在 `script_reuse`（兼容字段名） | scripts 内有非空脚本文件 | 仅检查常见脚本扩展名存在，功能与复用价值需执行验证 |
| 正文行数控制 `body_size_control` | ≤1000 行 | 1000-1500 给 0.5，>1500 给 0.2 |

## 对比与择优流程

1. 先运行 `skill_compare.py` 得到双方各项分数。
2. 检查结构差距是否与用户需求相关；简单技能无需为得分增加目录。JSON 中 `assessment_kind=structural_screening`、`adoption_verdict=requires_task_evidence` 明确证据边界。
3. 至少选一个与用户需求对应的真实场景，对双方使用相同输入、成功标准和运行条件，比较产出与成本。没有运行条件时记录「待任务验证」，不凭结构分宣告优劣。
4. 综合任务证据、语义贴合度和静态筛查，由执行代理向用户给出建议：
   - 上游更优 → 建议采纳上游（或借鉴优势后改进自建）
   - 自建更优 → 采纳自建
5. 对比结果记录到 `evolutions/`，包含场景、双方产出证据、结构分与采纳理由。

## 反馈闭环（择优后的学习）

- **上游更优时**：分析上游在优势维度上的做法（章节组织、门控设计、资源结构），提炼为可复用的方法论要点，追加到 skill-creator 的 SKILL.md 或本文件。
- 记录方式见 `evolutions/README.md`：按主题保留日期、来源、双方证据、采纳理由、验证与限制；独立事件可先记日期文件，成熟后合并并更新映射。
- 定期复盘 `evolutions/`，把有效经验落实到方法论，合并重复审计过程；保留未测、未采纳和待解决项。

## 限制

- 自动评分衡量的是**结构与质量门槛**，不衡量领域知识深度与语义贴合度——最终择优需结合代理判断与用户需求。
- 行数/资源判断基于文件系统启发式，大型复杂技能（如 loki-mode）可能被低估，需评审子代理复核。
