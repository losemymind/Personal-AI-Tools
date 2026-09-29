---
name: skill-creator
description: "创建、改进并验证个人工作流技能（Skills）。当用户需要从零创建技能、把反复出现的工作流沉淀为技能、修改或优化现有技能、评估技能触发与质量、或为 claude/opencode/codex/deepseek 等客户端打包安装指定技能时使用。也适用于「创建skill」「写个技能」「skill-creator」「把xx做成技能」等请求。"
category: productivity
risk: safe
---

# 技能创建器（skill-creator）

## 概述

把真实工作流整理成可复用、可验证、可独立安装的技能。根据当前任务选择创建、局部修改、评测或安装流程；用观察到的失败与产出证据决定改什么。SKILL.md 是唯一入口，工具、参考、角色指令均随成品分发。

## 何时使用此技能

- 从零创建技能，或把已有对话、SOP、反复执行的工作沉淀为技能。
- 修改现有技能的指令、脚本、引用、目录或命名。
- 对比技能版本或上游候选，评估任务效果、优化 description 触发面。
- 打包或安装一个已指定的技能；批量浏览能力库和跨产物安装由所在环境的编排层处理。

## 先选择任务范围

| 当前请求 | 执行路径 | 按需读取 |
|---|---|---|
| 改名、修正引用、修复明确的小问题 | 定位调用方 → 最小修改 → 相关校验；不自动重做上游研究或整轮评测 | 相关资源与质量标准 |
| 从零创建或实质改进工作流 | 读下方「创建与改进」；先收集失败证据并检索上游 | 写作、结构、字段参考 |
| 比较产出、跑场景基准 | 固定场景与基线 → 执行 → 评分 → 配对汇总 | `references/skill-evaluation.md`、`references/benchmark-schema.md` |
| 优化触发描述 | 审查询集 → 开发集选优 → 独立最终集确认 | `references/skill-trigger-optimization.md` |
| 打包、自安装或覆盖更新 | 使用已确定的客户端与作用域；只补问缺失信息 | `references/skill-installation.md` |
| 调查上游或更新索引 | 离线检索；需要更新时按源固定提交下载 | `references/skill-index.md` |

授权与用户已给出的选择在同一任务内持续有效。局部修改仅在实际改变触发或任务行为时补相应行为评测。用户只要分析时，先交付证据与方案；不把分析自动扩大成修改或安装。

## 资源路径与按需读取

内部路径以本技能目录为根；任意 cwd 调用时使用 `python "<技能目录>/scripts/<脚本>.py" ...`。优先用客户端技能列表给出的确切路径；否则检查用户已指定的安装位置，落点见安装参考。脚本通过 `_project_paths.py` 自定位，不依赖宿主仓库。

脚本命名为 skill_<用途>.py，索引为 skill_index_<动作>.py；共享模块为 `scripts/skill_utils.py`、`scripts/skill_events.py` 与 `scripts/_project_paths.py`。本创建器的角色指令统一命名为 agents/skill_<角色>.md。

| 需要的细节 | 读取资源 |
|---|---|
| frontmatter、风险、分类、创建台账 | `references/skill-template.md` |
| 目录组织、渐进披露、资源选择 | `references/skill-anatomy.md` |
| 校验项目与质量门 | `references/quality-bar.md` |
| 失败类型、纪律型技能、措辞微测 | `references/skill-writing-guide.md` |
| 静态比较维度及采纳边界 | `references/skill-comparison.md` |
| 场景执行与评审流程 | `references/skill-evaluation.md` |
| 评分、指标、基准 JSON 契约 | `references/benchmark-schema.md` |
| 触发评测与描述优化参数 | `references/skill-trigger-optimization.md` |
| 多客户端打包与自安装 | `references/skill-installation.md` |
| 索引来源、更新、固定提交与离线状态 | `references/skill-index.md` |
| 有针对性的上游写作样本 | `examples/README.md`，再选与本任务相关的样本 |
| 历史决定与未解决事项 | `evolutions/README.md`，再按主题恢复背景 |

只读当前任务需要的资源。references 从本入口一层深访问，不互链兄弟文件；超过 100 行的参考加目录，超大文件在入口提供检索词。正文越长，上下文成本越高；元技能也应把条件性细节移至按需参考。

## 工作原理：创建与改进

### 1. 捕捉工作与失败证据

优先从对话、现有产出、脚本、SOP 提取目标、输入、输出、成功标准与真实失败。只询问无法推断且会影响结果的信息。业务定义、权限与发布决策由有权的人确定；仅对尚未获得的必要授权暂停对应动作。

新技能或行为改动先用代表性任务确认基线：新建时不带技能，改进时用原版本。保留失败与证据，再写针对失败的指导。若没有观察到增益需求，说明技能的必要性尚未验证，不虚构基线；命名、引用等机械修复可用结构校验验证。

### 2. 先查后建与上游择优

```bash
python scripts/skill_index_search.py "<关键词>" --limit 10
python scripts/skill_index_search.py --stats
```

索引 `indexes/upstream.db` 随包提供，覆盖 aas、addy、anthropics、composiohq、coevoskills、mattpocock、karpathy。查询先用领域、动作、工具关键词；中文常见词有离线扩展，未知词再补英文与近义词。一次 0 命中不证明不存在候选。

查看逐源状态与 upstream_commit；unknown 不能证明远端最新。需要更新时按源运行 `scripts/skill_index_build.py`，不为一个候选默认下载全部上游。

有候选先检查适用范围、许可和已有能力：可直接适配满足需求的部分；确有差距再自建。运行 `scripts/skill_compare.py` 做结构筛查，并在相同输入、成功标准和条件下比较至少一个真实场景。结构分不代表任务效果，没有运行条件就记录「待任务验证」。采纳后按 `evolutions/README.md` 记录来源、日期、证据、取舍和限制。

### 3. 设计与编写

- 只有 SKILL.md 必需；脚本、模板、示例和参考按任务价值添加，不为目录数量凑结构。
- 脚本负责确定性和重复操作；正文保留工作流、关键约束、选择逻辑与输出契约。
- 固定步骤用于脆弱或高风险操作；开放任务保留判断空间，解释约束的原因。
- 违规型失败用边界和可观察条件，形状错误用正面输出配方，漏项用模板槽；纪律型技能按写作参考验证压力场景。
- 新技能可用 `templates/SKILL.template.md` 或 `scripts/skill_create.py` 初始化；已有技能直接修改。

frontmatter 的核心字段为 name、description、risk、category，可选 allowed-tools。name 与目录一致、小写 kebab-case；本地验证器上限 100 字符，目标客户端有更严格限制时从其要求。description 单行、≤1024 字符，无尖括号占位，描述能力与触发条件，不写执行步骤摘要。正文保留范围确认。

来源、作者、日期和版本不进入 frontmatter；创建元数据用 `skill_create.py --records <账本>` 的 author/source/source-repo/method 参数登记，版本由 Git 历史追溯。产品文档用中文，外部来源与许可保留。

### 4. 校验、测试与 AI 评审闭环

```bash
python scripts/skill_validate.py --strict --dir <技能目录>
```

校验 frontmatter、章节、安全模式、资源引用和 evals 形状；目标目录必须显式给出，否则默认自检本创建器。修改脚本时运行对应行为测试；修复错误后再进入语义评估。

需要评估行为增益时，从本入口读取场景评测与 schema 参考。使用相同输入和运行条件生成两组结果，保存真实产物与失败状态；缺失样本或成本不得补成成功或零。

AI 评审闭环：作者修订，独立评审者按 `agents/skill_reviewer.md` 产出 review.json（pass|revise、issues、上轮修复核验）。通过或达到 max-iterations（默认 5）停止，达到上限不等于通过。仅在任务需要且客户端支持时派发；无法派发可按同一指令内联评审并标明缺少独立性。

- 客观断言评分：`agents/skill_grader.md`，输出 grading.json。
- 单份产物质量与查询集审核：`agents/skill_reviewer.md`。
- 输出级匿名 A/B 比较：`agents/skill_comparator.md`，输出 comparison.json；随机标签并隐藏来源。
- 基准模式及比较结果复盘：`agents/skill_analyzer.md`。

描述影响触发时再走触发优化路径。heuristic 是词面代理指标；真实客户端信号与独立最终测试单独报告，测试全绿不证明实际触发率提升。

### 5. 交付与反馈

交付当前技能、改动理由、验证结果与未解决项。需要时保留 VERIFICATION.md，记录当时检查，不承诺未来安全。上游吸收和方法论决定按主题更新 evolutions；机械修改更新相关命名与引用记录即可。

入库按宿主技能库的分类、台账与审计要求执行；evals 随技能保存，发布前运行安全扫描及相关校验。提交、推送、发布与外部动作遵循用户授权和宿主仓库规则，不由本技能自动授权。

## 多客户端安装指引

仅在请求包含打包或安装时读取 `references/skill-installation.md`，按其中「自安装」或「打包」路径执行。安装位置、客户端与作用域已有答案时直接沿用；只安装用户指定的范围。产物适配后自检，再用真实小任务确认加载。

## 示例

**局部修改**：「把四份子代理指令改为 skill_*.md」→ 查找调用方 → 改名并同步引用 → 相关测试与 strict 自检 → 说明外部旧路径需要迁移。

**创建**：「把每周报表整理工作做成技能」→ 提取实际输入与报表样本 → 确认基线问题、检索候选 → 写最小指令和必要脚本 → 对相同输入验证真实产物 → 评审后交付。

**触发优化**：「相关请求经常不调用技能」→ 检查是否运行错误 → 审真实查询与近似干扰项 → 开发集选择描述 → 未见最终集确认，并注明读取或派发证据。

## 质量检查清单

- [ ] 修改范围与请求一致，约束解决实际问题，未重复索取已有授权。
- [ ] description 自足且能区分相邻任务；正文与参考职责清楚。
- [ ] 资源自包含、路径可达；产品内不依赖宿主的测试或安装文档。
- [ ] 脚本已验证；行为改动有代表性任务证据，失败和未测状态如实保留。
- [ ] 评分基于真实产物；配对、覆盖率、模型和未知成本清楚。
- [ ] 来源、采纳理由、许可与必要演进记录可追溯。

## 安全护栏

- 攻击性技能须声明 AUTHORIZED USE ONLY / 仅限授权使用，并在攻击操作前确认所需授权；以受控测试环境为目标。
- 默认不把用户数据上传到第三方；外部状态变更需要对应授权。
- 不在示例或脚本中埋入密钥、危险下载执行管道或隐藏操作。确有必要的危险示例使用 security-allowlist 注释并解释上下文。
- 临时 cwd 用于分离生成文件，不是权限沙箱；客户端仍可能继承全局技能、配置、凭据和工具权限。敏感评测需要独立客户端环境。

## 限制和注意事项

- 自动工具依赖 Python 3.10+ 与 PyYAML；没有运行条件时做静态检查并标明未执行。
- 自动触发与场景执行当前支持 Claude / OpenCode CLI；Codex / DeepSeek 是打包目标，不能据此声称已支持其自动评测。
- 结构化读取或派发证明技能被加载/调用，不证明任务完成；场景失败仍须单独报告。
- 统计结论只适用于记录的场景、版本与运行条件；旧索引缺失的提交号为 unknown，本地目录不冒充远端提交。
