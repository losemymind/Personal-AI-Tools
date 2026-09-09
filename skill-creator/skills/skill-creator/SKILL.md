---
name: skill-creator
description: "创建、改进并验证个人工作流技能（Skills）。当用户需要从零创建技能、把反复出现的工作流沉淀为技能、修改或优化现有技能、评估技能触发与质量、或为 claude/opencode/codex/deepseek 等客户端安装与管理技能时使用。当用户提到「创建skill」「写个技能」「skill-creator」「把xx做成技能」「添加技能」等说法时，使用本技能。"
category: productivity
risk: safe
source: self
version: "0.6.0"
date_added: "2026-09-01"
author: losemymind
tags: [skill-creator, skills, workflow, llm-clients]
tools: [claude, opencode, codex, deepseek]
---

# 技能创建器（skill-creator）

## 概述

本技能指导如何把真实工作流蒸馏为可复用、可验证、跨客户端安装的高质量技能。技能的本质是一组「指令 + 资源」（`SKILL.md` 及其目录），为 LLM 客户端提供精确的触发条件与可预期的操作流程。方法遵循：证据驱动、渐进式披露、自由度匹配脆弱性、高信号命名、迭代测试循环与治理化验证；内置多源上游技能索引（`indexes/upstream.db`，检索细节见「何时使用此技能」与 `references/skill-index.md`）支撑「先查后建」，避免重复造轮子。

本技能目录结构（符合技能解剖标准）：

```
skill-creator/
├── SKILL.md                    ← 本方法论（唯一入口：何时使用/工作流/资源导览）
├── README.md                   ← 说明（上游来源/约定/结构）
├── scripts/
│   ├── build_index.py          ← 构建上游技能索引（tarball→SQLite）
│   ├── search_index.py         ← 检索上游索引（FTS5 全文/分类/风险）
│   ├── compare_skills.py       ← 自建 vs 上游对比评分（质量6维+结构4维）
│   ├── create_skill.py         ← 交互式脚手架生成器（含 version 字段）
│   ├── validate_skills.py      ← 自动验证器（frontmatter/章节/安全/链接）
│   ├── run_trigger_tests.py    ← 触发启发式工具（classify/关键词；供 run_eval 复用）
│   ├── run_eval.py             ← 触发评测（heuristic 默认 / cli 双模式；--output-dir 落盘）
│   ├── run_loop.py             ← description 自动优化循环（train/test 60/40）
│   ├── aggregate_benchmark.py  ← 量化基准汇总（benchmark.json + benchmark.md；--notes 合并分析笔记）
│   ├── utils.py                ← 共享：解析 SKILL.md frontmatter（四端通用）
│   └── _project_paths.py       ← 技能根定位辅助（自包含，不依赖宿主仓库）
├── agents/                     ← 子代理指令（SKILL.md 按需拉起，不自动加载）
│   ├── grader.md               ← 评分子代理：断言判定 → grading.json
│   ├── comparator.md           ← 盲测对比子代理：A/B 定性对比 → comparison.json
│   └── analyzer.md             ← 复盘/基准分析子代理：改进建议 / 观察笔记
├── indexes/
│   └── upstream.db             ← SQLite 索引（官方 skills_index.json + 结构扫描）
├── references/
│   ├── skill-template.md       ← 字段与分类完整参考
│   ├── skill-anatomy.md        ← 结构解剖与渐进式披露
│   ├── quality-bar.md          ← 8 项质量检查与验证标准
│   ├── skill-writing-guide.md  ← 写作规律（TDD 化/表述匹配失败类型/防借口/措辞微测）
│   ├── skill-index.md          ← 索引构建/检索/更新说明
│   ├── skill-comparison.md     ← 对比评分维度与择优流程
│   └── benchmark-schema.md     ← 评测/基准 JSON schema（移植自 Anthropic 官方）
├── examples/                   ← 上游学习样本（MIT 许可，验证豁免）
│   ├── README.md               ← 样本入口：来源/许可/目录清单/学习要点
│   ├── brainstorming/          ← 单文件·结构教科书
│   ├── copywriting/            ← 单文件·流程门控
│   ├── git-pushing/            ← 单文件+scripts·高风险模板
│   ├── systematic-debugging/   ← 单文件+references·阶段强制序
│   ├── react-best-practices/   ← 多文件·渐进式披露范本（AGENTS.md+rules/）
│   └── loki-mode/              ← 综合·复杂工作流范本（references/ 大拆分）
├── evolutions/                 ← 对比学习记录（反馈闭环；README + 日期平铺记录）
└── templates/
    ├── SKILL.template.md       ← 新技能骨架
    └── evals.json.template     ← 触发测试用例模板
```

## 何时使用此技能

- 用户要求「把这个工作流做成一个技能」、「创建一个 skill」
- 用户描述了一个反复出现的手动流程或专业领域知识，值得沉淀为技能
- 需要改进、重构或评估一个现有技能
- 需要把一个技能安装到 claude / opencode / codex / deepseek 等客户端的 skills 目录
- 需要为技能编写测试用例、评估触发准确性、或运行自动验证

> 本技能只管**创建/改进 + 与上游对比**；若用户只是想「按需安装已有的现成技能」（读现有能力清单直接给安装命令、不创建），不在本技能范围——由所在环境的编排层自行处理。

## 资源路径基准

本技能是**自包含完整体**：内部所有引用（脚本、参考、索引、模板、示例、演进记录）一律以 **skill-creator 目录自身为根**书写，不依赖任何外部布局：

- 脚本：`python scripts/<脚本>.py ...`（如 `python scripts/validate_skills.py`）
- 参考：`references/skill-template.md`、`references/quality-bar.md` 等
- 索引：`indexes/upstream.db`；模板：`templates/`；示例：`examples/`；记录：`evolutions/`

**调用约定**：上述命令均以「在本技能目录内执行」为准；不在技能目录内执行时，给命令加上技能目录前缀：`python "<技能目录>/scripts/<脚本>.py" ...`。定位本技能目录的方法：codex 的技能列表自带文件路径，直接使用；claude/opencode 按存在性依次探测——工作区候选 `<项目>/.claude/skills/skill-creator/`、`<项目>/.opencode/skills/skill-creator/`、`<项目>/.agents/skills/skill-creator/`；全局候选 `~/.claude/skills/skill-creator/`、`~/.config/opencode/skills/skill-creator/`、`~/.agents/skills/skill-creator/`。脚本会以自身位置定位索引/模板等内部资源，无需其他配置。

读取规则：references 文档**按需读取**（渐进式披露），需要字段/分类细节时读 `references/skill-template.md`，需要结构规范时读 `references/skill-anatomy.md`，需要质量标准时读 `references/quality-bar.md`，需要写作规律（TDD 化/表述匹配失败类型/防借口/微测）时读 `references/skill-writing-guide.md`；不要一次性全部注入。

## 核心理念

### 证据驱动，而非规格驱动

从**用户实际做过的工作**出发，而不是从技术需求规格出发。让用户贴出真实产出（报表、脚本、邮件、截图、SOP、表格、对话记录）作为证据。更好的源材料产出更可用的初版。

### 渐进式披露（Progressive Disclosure）

技能有三层加载模型：
1. **元数据**（`name` + `description`）—— 任何时刻都在上下文（约 100 词），决定是否触发
2. **SKILL.md 正文** —— 触发后加载（理想 <1000 行）
3. **捆绑资源**（`scripts/` `references/` `assets/`）—— 按需加载，无限量

正文超过 1000 行时，把细节下沉到 `references/` 并按需读取；正文保留工作流 + 选择逻辑 + 明确指引。

**references 引用纪律（硬规则）**：references 只允许从 SKILL.md **一层深**引用，references 之间不互相链接成图（保持按需加载路径可预期）；单文件 >100 行在顶部加**目录**；超大文件（>10k 词）在 SKILL.md 引用处附 **grep 模式**（如 `grep -n "阶段 7" references/xxx.md`）让代理跳过读全文直接定位。

**元技能豁免**：skill-creator 自身是**元技能**（为了"创建更完善的技能"而存在），不受本行数指引约束——它优先保证方法论完整度，若后续扩展需要超出 1000 行，允许超出（references 已按需加载，正文变长不影响客户端加载性能）。行数指引只适用于它所产出的**普通技能**，不适用于它自己。

### 自由度匹配脆弱性（Guardrails to Fragility）

结构化的程度应与「犯错代价」匹配：
- **高自由度**：启发式、检查清单、示例（代价低、创造性工作）
- **中自由度**：伪代码、模板、带参数的脚本（流程半固定）
- **低自由度**：精确命令、严格模板、强制验证步骤（易碎、代价高、如删除/推送/资金操作）

不要给简单技能堆一大串 MUST/NEVER；也不要让高危流程含糊。

### 高信号命名与描述

`name`/`description` 是技能的唯一门面，直接决定是否触发：
- `name`：小写-连字符，与目录名完全一致，≤100 字符，稳定不变
- `description`：触发场景优先——以「何时用/Use when」开头，前部加载具体触发关键词（文件名、领域、工具、用户惯用语）；可保留一句能力定位，但**不写执行步骤/流程阶段摘要**（实证：总结流程的描述会让 agent 跳过正文走捷径）。实测 LLM 倾向**欠触发**，描述可稍「主动」——列举会触发它的用户说法，即使没字面提到技能名。

**description 硬约束（唯一无条件加载的触发面）**：`description` 是客户端在触发前唯一始终加载的字段——必须**自足**覆盖全部触发场景，不依赖正文兜底。约束：≤1024 字符（validate 强制）、**单行、不含 `<`/`>` 占位符**（`<技能名>`、`<path>` 之类），禁流程摘要。正文保留「何时使用此技能」章节作触发后的范围确认（claude/opencode/codex 加载正文后依赖它），但**触发判定只看 description**——写正文前先把 description 当唯一门面试一遍触发查询。

### 迭代验证循环

技能是迭代出来的，不是一次写成的：**草案 → 测试 → 评审 → 改进 → 重跑**，直到用户满意或反馈为空。

### 先失败后写 + 表述匹配失败类型（TDD 化）

技能写作是对**过程文档的 TDD**：先在无技能状态跑真实场景看基线失败（verbatim 记录 agent 借口），再写**只针对这些失败**的最小正文，重测补漏直到无法绕开——**无「失败先例」不写技能**。且指导措辞的形式必须**匹配失败类型**（违规→禁止+借口表；形状错→正面配方；漏元素→模板 REQUIRED 槽；条件行为→可观察谓词）；实证显示禁止清单会反噬「输出形状错」类问题。防借口、措辞微测、类型取舍与 Token 预算等完整规律见 `references/skill-writing-guide.md`。

### 无意外原则（Lack of Surprise）

技能不得包含恶意、利用或误导内容，也不得在意图上隐藏改动。拒绝创建「伪装成正常技能但实际做不该做的事」的技能。

## 技能目录解剖（Anatomy）

```
skills/<skill-name>/
├── SKILL.md              ← 必需：主技能定义（frontmatter + 指令）
├── examples/             ← 可选：真实示例
├── scripts/              ← 可选：可执行辅助脚本（可复现/重复任务）
├── templates/            ← 可选：输出模板
├── references/           ← 可选：参考文档（>300 行的大文件附目录；多领域按文件拆分）
├── agents/               ← 可选：子代理指令文件（由 SKILL.md 按需拉起，不自动加载）
└── README.md             ← 可选：附加说明（跨客户端差异、维护记录）
```

关键规则：**只有 `SKILL.md` 是必需的**。`scripts/` 用于确定性/重复性任务（脚本被执行，不进上下文）；`references/` 用于按需注入的深度文档；`agents/` 存子代理角色指令——SKILL.md 在流程中拉起子代理时让其读入（语义判断类工作），与 `scripts/`（确定性可复现工作）分工互补。

## 前置元数据字段规范

SKILL.md 顶部用 `---` 包裹 YAML frontmatter：

```yaml
---
name: <skill-name>                 # 必需：小写-连字符，与目录名完全一致
description: "..."                 # 必需：触发场景优先 + 一句能力定位（不写步骤流程摘要），≤1024 字符
category: <category>               # 必需：见下方分类值
risk: <none|safe|critical|offensive|unknown>  # 必需
source: <self|community|official|URL>         # self 表示原创
date_added: "YYYY-MM-DD"           # 必需
author: <your-name-or-handle>      # 可选
tags: [tag-one, tag-two]           # 可选：小写、≤5 个
tools: [claude, opencode, codex]   # 可选：支持的客户端
---

# <技能标题>
```

**风险级别：**
- `none` — 纯文本 / 推理，无命令或状态变更
- `safe` — 读取文件、运行非破坏性命令（推荐用于多数指导类技能）
- `critical` — 修改状态、删除文件、推送生产环境
- `offensive` — 渗透测试 / 红队；**必须**含「仅限授权使用」警告，并强制要求执行前向用户确认
- `unknown` — 遗留 / 未分类；**新技能不要用**

**分类常用值：** `development` / `frontend` / `backend` / `testing` / `devops` / `architecture` / `security` / `ai` / `prompt-engineering` / `git` / `productivity` / `documentation` / `planning` / `communication` / `research` 等。

## 内容结构与写作指南

推荐结构（必需章节：概述 / 何时使用此技能 / 工作原理；其余可选）：

```markdown
# <技能标题>
## 概述            # 2-4 句：做什么、为什么存在
## 何时使用此技能     # 具体触发场景列表
## 工作原理          # 步骤化执行流程（技能核心）
## 示例             # 至少 1 个可立即复制使用的代码块/交互示例
## 最佳实践          # ✅ 要这样做 / ❌ 避免什么
## 相关技能          # 纯技能名 + 何时用；禁止 @ 语法（force-load 烧上下文）
## 常见问题          # 故障排查
## 限制和注意事项     # 已知边界与做不到的事
## 安全与安全说明     # 涉及命令/安装/权限/高风险时才需要
```

**写作要点：**
- 祈使句、动作动词、具体步骤：「创建文件…」「在继续之前检查…」，避免「应该被创建」「您可能需要考虑」。
- 解释每个指令的**为什么**，而不是用大写 MUST/NEVER 堆砌。
- 示例具体、可直接使用；可标注输入 → 输出。
- 定义输出格式时直接给固定模板。
- 用「渐进式披露」组织：`## 基本用法`（常见场景）+ `## 高级用法`（复杂场景）。
- 从通用模式出发，不要过拟合到狭窄例证。
- `description` 说「何时触发」，正文写「怎么执行」——不要对调。

## 创建流程（核心工作流）

> **可独立安装**：作为独立模块，本技能不依赖宿主仓库的目录结构。
>
> **闭环（3 步）**：
> 1. **按用户需求创建一个技能**（阶段 1-4）
> 2. **检索上游**是否已有同类（阶段 0）——有候选 → 与自建对比（阶段 5.5）取最优；无候选 → 用自建版本
> 3. **若上游更优** → 采纳并记录 `evolutions/` → 优化本技能方法论（反馈闭环）

### 阶段 0：检索上游技能库（先查后建）

动手创建前，**先在本地索引中检索上游技能库是否已有可用技能**（索引为双源：`aas` = agentic-awesome-skills、`addy` = agent-skills，默认全库检索，`--source` 过滤单源；避免重复造轮子，是本技能的第一个决策门）：

```bash
python scripts/search_index.py "<用户需求关键词>" [--category <分类>] [--risk <级别>] [--limit 10]
python scripts/search_index.py --stats                # 查看索引状态
python scripts/search_index.py --list-categories      # 列出全部分类
```

- 索引文件 `indexes/upstream.db` 已随仓库提交，无需联网即可检索。
- **索引落后于上游时**（上游有更新）：运行 `python scripts/build_index.py` 重建。
- 检索结果给出：技能名/描述/路径/风险/分类/行数/目录结构标志（scripts/references/examples）。
- 检索详情见 `references/skill-index.md`。

**决策分支：**
- **有匹配候选** → 记录候选；照常进入创建（阶段 1-5），在阶段 5.5 与候选对比择优（自建 vs 上游 → 取最优）。
- **无匹配候选** → 跳过阶段 5.5，用自建版本。
- 若上游更优被采纳 → 提炼学习点记录到 `evolutions/`（阶段 5.5），反哺优化本技能。

### 阶段 1：捕捉工作与证据

让用户描述**他们实际做的工作**，并贴出真实产出作为证据。优先从当前对话提取（工具、步骤、纠正过的错误、输入输出格式）。

可用的提问（一次一条，避免轰炸）：
1. 这个技能最终要让 LLM 能做什么？
2. 平时你**反复做**的是哪几步？（这是技能的价值所在）
3. 输入是什么（文件类型、数据、场景），输出要什么格式？
4. 有没有现成的产出、脚本、SOP、表格可以贴出来当证据？有的话质量会好很多。
5. 有没有需要**人才能拍板**的决策、权限边界或风险边界？（没有就继续）

如果用户只是抽象地说「帮我做个技能处理数据」，引导到具体工作流上再继续。

### 阶段 2：确认唯一的「人力决策点」

梳理出整个工作流里**只有人才能决定**的事情——业务定义、授权、风险边界。把它明确记录，并询问是否有权作决定的人能确认该定义。

- 能确认 → 记录决策，继续构建。
- 无法确认/无权 → 结果为 `BLOCKED`，向合适的负责人索取那一个缺失的授权。**不要替用户拍板，不要编造授权。**

### 阶段 3：设计与脚手架

- 先读本地 `examples/README.md`（样本入口：来源/许可/目录清单/学习要点），再研究 `examples/` 中的 6 个上游学习样本（对应 skill-anatomy 的「研究这些示例」），按需求类型选取参考：结构清晰 → `brainstorming`；高风险操作模板 → `git-pushing`；流程门控 → `copywriting`；阶段强制序 → `systematic-debugging`；多文件渐进式披露 → `react-best-practices`；复杂工作流 → `loki-mode`。
- 确定技能结构与所需资源（`scripts/`、`references/`、`examples/`、`templates/`）。
- 结构规范见 `references/skill-anatomy.md`（目录解剖 + 渐进式披露 + 大小指南）。
- 按「自由度匹配脆弱性」决定结构强度（见 `references/quality-bar.md` 与正文「核心理念」节）。
- 从最小可行开始，先让技能「跑起来」，再按反馈扩展。
- 使用 `templates/SKILL.template.md` 作为骨架；字段与分类完整参考见 `references/skill-template.md`。
- 可一键生成骨架：`python scripts/create_skill.py --name <技能名> --category <分类> --risk <级别>`（交互式或 `--no-interactive`）。
- frontmatter 应声明 `version: "0.1.0"`（语义化版本，生命周期管理依赖它记账）。

### 阶段 4：编写 SKILL.md

按「前置元数据字段规范」与「内容结构与写作指南」两节编写；字段细节见 `references/skill-template.md`，结构规范见 `references/skill-anatomy.md`。编写顺序建议：

1. 先写「何时使用此技能」——明确目的
2. 再写示例——帮自己理解在教什么
3. 然后补全工作流正文

### 阶段 5：运行自动验证

编写完成后、测试前，运行技能自带的验证器（基于 agentic-awesome-skills 的验证器实现，位于本技能的 `scripts/`）：

```bash
python scripts/validate_skills.py                # 标准模式（警告不阻断）
python scripts/validate_skills.py --strict       # 严格模式（有警告即失败，适合 CI）
python scripts/validate_skills.py --dir <skills目录>  # 校验指定目录
```

说明：不带 `--dir` 时默认扫描**技能根自身目录**（`scripts/` 的上一级，即自检，不依赖任何宿主仓库布局）；校验其他技能目录或技能库时用 `--dir <目录>`。

验证器检查项（完整列表见 `references/quality-bar.md`）：frontmatter 有效性（YAML、`name` 与目录名一致、`description` ≤1024 字符、`risk` 合法、`version` 语义化格式）、`source`/`source_repo`/`source_type`、`date_added` 格式、中英文「何时使用」章节、示例章节、限制章节、offensive 技能的安全免责声明与用户确认门、以及本地链接是否悬空。存在错误时 exit code 为 1，严格模式下警告也会导致失败。

技能正文稳定后开始量化评估。采用「**确定性脚本打底 + SKILL.md 拉起子代理判断 + 脚本聚合收尾**」的混合编排（子代理指令在 `agents/`，移植自 Anthropic 官方；子代理负责语义判断，脚本负责可复现的确定性工作）：

**第 1 步：触发评测（确定性脚本，先跑）**——`templates/evals.json.template` 为 evals 模板：

```bash
# 1) 确定性触发启发式（无外部 CLI，默认）
python scripts/run_eval.py --eval-set <技能目录>/evals.json --skill-dir <技能目录>
# 2) 真实客户端无头 CLI 触发（有 claude CLI 时可用；opencode/codex 后续可接入）
python scripts/run_eval.py --eval-set <技能目录>/evals.json --skill-dir <技能目录> --mode cli --client claude
```

输出每条查询的触发判定 + 汇总（passed/total、precision、recall）；`--json` 可机器读取；`--output-dir <目录>` 把结果 JSON 落盘为 `eval-results-<技能名>.json`（供后续评分/复盘引用）。

> **职责边界**：`run_eval.py` 只产出触发判定信号（stdout / 落盘文件），不铺设目录结构——评分所需的工作区布局（`<workspace>/iteration-N/eval-<名>/<配置>/run-N/`）由编排层（主持会话或拉起方）按下节工作区布局搭建。

**第 2 步：输出打分（拉起评分子代理）**：对每个 eval 跑完「有技能」与「无技能（基线）」两组运行、产物按「工作区布局」落到 `<workspace>/iteration-N/eval-<名>/<with_skill|without_skill>/run-N/` 后，**拉起评分（grader）子代理**：提示词中给出 `expectations` / `transcript_path` / `outputs_dir`，令其读入 `agents/grader.md` 执行——逐条断言判定、核验隐含声明、审视断言质量，把 `grading.json` 写进每个 run 目录（字段契约见 `references/benchmark-schema.md`）。

**第 3 步：聚合（确定性脚本）**：

```bash
python scripts/aggregate_benchmark.py <workspace>/iteration-N --skill-name <名>
```

读取各 `grading.json`（+ `timing.json`）汇总为带 mean±stddev 与 delta 的 `benchmark.json`（+ `benchmark.md`）；直接读 delta 判断技能相对基线的真实增益。

**第 4 步：模式分析（拉起分析子代理）**：**拉起分析（analyzer）子代理**，按 `agents/analyzer.md` 模式二分析 `benchmark.json`——逐断言模式（恒过/恒败/单侧过/高方差 flaky）、跨 eval 模式、耗时与 token 模式——产出**观察笔记**（JSON 字符串数组），再用脚本合并进基准：

```bash
python scripts/aggregate_benchmark.py <workspace>/iteration-N --skill-name <名> --notes <notes文件>
```

**可选第 5 步：盲测对比（拉起对比子代理）**：需要定性比较两份输出（如 with_skill vs without_skill、新旧版本技能）时，**拉起盲测对比（comparator）子代理**：A/B 标签随机分配且保密来源，令其读入 `agents/comparator.md` 出 `comparison.json`；随后可再拉起 analyzer 模式一复盘「胜者为何胜出」。盲测是定性补充——`compare_skills.py` 的结构评分与 `aggregate_benchmark.py` 的 delta 仍是主决策依据。

> 客户端无子代理派发能力时**降级不跳过**：由主持会话按同一份 `agents/*.md` 内联完成评分/对比/分析，产物格式不变。高方差 eval 视为 flaky 需更多 run。Schema 与布局见 `references/benchmark-schema.md`。

### 阶段 5.5：与上游候选对比择优

若阶段 0 检索到匹配候选，将自建技能与上游候选进行结构化对比（使用 `compare_skills.py`，实现 **质量 6 维 + 结构 4 维** 评分）：

```bash
# 对比单个技能目录
python scripts/compare_skills.py <自建目录> <上游候选目录>

# 对比某上下游候选目录下的全部技能
python scripts/compare_skills.py <自建目录> <上游目录> --all-candidates
```

评分维度（详见 `references/skill-comparison.md`）：
- **质量 6 维**（权重 60%）：触发清晰度 / 示例可得性 / 限制声明 / 风险声明 / 安全护栏 / 元数据完整
- **结构 4 维**（权重 40%）：渐进式披露 / 资源组织 / 脚本复用 / 正文行数控制

**决策：**
- **上游更优** → 分析上游优势维度，提炼学习点，改进 skill-creator 方法论（记录到 `evolutions/`，形成反馈闭环）；必要时直接采纳上游技能。
- **自建更优或持平** → 采纳自建版本，继续阶段 6。
- 对比报告保存至 `evolutions/<日期>-compare-<技能名>.md`。

结构分相近（±0.05 内）难以定夺、且双方都能实际产出时，可追加**输出级盲测**：拉起 `agents/comparator.md` 盲测对比子代理比较双方真实输出，再拉起 `agents/analyzer.md` 模式一复盘胜因——语义判断补结构评分之短，结论并入对比报告。

### 阶段 6：测试与迭代

> **纪律（Iron Law）**：基线必须先于写作——**无技能状态的失败观察在前，写技能在后**（RED→GREEN→REFACTOR）。如果技能已写好才想起基线，回到正文会写前先跑一遍无技能场景。指导措辞的**形式须匹配失败类型**，防借口/微测/正反对照见 `references/skill-writing-guide.md`。

**RED→GREEN 行为差门（技能是否成立的显式判定）**：用 fresh-context 子代理**不带技能**跑真实场景（RED）：
- **基线不失败 → 技能不必要**——停下，向用户说明「没有可修的行为差」，不硬写技能（写出来也只是冗余指导）。
- **基线失败（verbatim 记录借口）→ 才进入写作**；写后带技能重跑（GREEN）必须消除基线失败——若仍失败则补正/删冗余，直到行为差消失。

**人审闭环**：把「有/无技能」两组输出交给带反馈 UI 的人审（或在对话里请用户逐条给结构化意见），意见随 iteration 目录版本化并回流下一轮——先给人看，再自己改，别让 agent 自评自改闭环自嗨。

提出 2-3 个**真实用户会说的话**作为测试提示词，请用户确认后运行：

- **有技能** 和 **无技能（基线）** 两组对比运行同一提示词，记录输出、耗时与 token。
- 断言打分**拉起评分子代理**（读 `agents/grader.md`，产物 `grading.json`）：客观断言逐条判过/不过并引用证据；客户端不支持子代理时由主持会话按同一份指令内联完成。主观部分交用户定性评审；两组输出需定性比较时拉起盲测对比子代理（`agents/comparator.md`，A/B 随机标签保密来源）。
- 把结果整理成便于用户对照的形式（输出对比 + 量化指标），请用户逐条反馈。
- 根据反馈改进：从反馈中**归纳共性**而非死板套用；剔除不生效的指令；把各测试中反复手写的辅助脚本沉淀为 `scripts/`。
- 重复「改进 → 重跑 → 评审」直到用户满意或反馈为空。

测试用例与结果记录在工作区内，参考官方结构的元数据字段（eval id、描述性名称、断言、输出路径、时间/token）。

### 阶段 7：描述优化（触发测试 + 自动优化循环）

技能内容稳定后进行。两档做法：

**手动档（默认）**：
1. 生成约 20 条**真实风格**触发查询：约一半应触发、一半不应触发。不应触发的最有价值的是「近似干扰项」——关键词重叠但实际需要别的技能。
2. **先审查询集再跑**：请用户审阅并签名确认查询集（坏查询会训练出坏描述——假阴性/假阳性/运行错误必须先排除，再让它们进评测）。
3. 用现版与改进版描述分别跑 `run_eval.py`，对比触发率。
4. 选择测试集分数更高的版本，展示前后对比与得分。

**触发失败分类（改前先归因）**：把每次 eval 失败归入三类再决定怎么改——**假阴性**（应触发未触发 → 触发面漏词/说法没覆盖）、**假阳性**（不应触发却触发 → 描述过度泛化/兜底词过多）、**run_error**（运行失败 → 工具/依赖/路径问题，与描述无关别乱改 description）。三类混改会把「改错病」当成「改好病」。

**gold-standard 先例（从好里选更好）**：每轮改进提示里，附上上一轮 test 分最高的 description（连同其 run_eval 得分）当 few-shot 先例——描述优化是「从已验证的好措辞里选更好的」，不是每轮从零发明措辞。历史高通过率描述按分数优先复用。

**自动档（借鉴 Anthropic 官方 run_loop，train/test 60/40 分层分集，防过拟合）**：

```bash
python scripts/run_loop.py --eval-set <技能目录>/evals.json --skill-dir <技能目录> \
  --holdout 0.4 --max-iterations 5 --improve-mode manual|cli --report <输出>.json
```

- 评测按 `should_trigger` 分层的 60/40 切分为 train/test；每轮用当前 description 评 train+test，再按失败模式请求改写。
- `--improve-mode manual`（默认）：打印改进提示词，粘贴返回的 description，以独立 `EOF` 行结束。
- `--improve-mode cli`：调用客户端无头 CLI（如 `claude -p`）生成新 description。
- **最终选取以 test 集得分最高者为准**（不选 train 满分者），避免过拟合到测试用例。

注意：复杂、多步、专精的查询才适合评估触发（简单单步查询无论描述多好都常不触发）。触发评测结果 `--json` 输出写入 `evals/` 或技能目录，作为阶段 8 验证记录的一部分。

### 阶段 8：记录验证与治理信息

创建 `VERIFICATION.md`（生成时检查记录：结构、代码、安全模式、示例）：它记录**当时**做过的检查，不承诺未来的运行安全。缺失的凭据、权限或安全输入应产出「verification-blocked」说明，并给出一个具体的下一步动作。

技能使用后若需修正，记录修正的原因与回归记录（版本化、带原因的原子补丁，即本技能的 `evolutions/` 模式）。**不要把未经单独验证的草稿直接应用进 `SKILL.md`。**

### 阶段 9：安装与验证

- 按「多客户端安装指引」把技能复制到目标客户端的 skills 目录。
- 重启客户端后用真实小任务触发一次，确认技能被加载、按指令执行。
- 经验证、可复用的技能按质量检查清单归档到宿主技能库的分类目录 `skills/<分类>/<name>/`——按功能分类入库，分类目录不存在则先创建，不得散置在库根目录。

**入库/发布纪律（提交前逐项）**：
- **evals 随技能发布**：触发用例（`evals.json` 或场景清单）与技能同目录沉淀——入库后任何人改动技能都能回归触发，不用重新发明测试。
- **secret 扫描**：入库/提交前扫一遍技能目录与脚本，确认无明文密钥/token/凭据示例（危险管道 `curl|bash` 等按「安全护栏」处理，必要时 `<!-- security-allowlist -->` 声明）。
- **隔离验证再交付**：非直推——经 PR 评审、tag 版本后，在**隔离环境**（独立 HOME/临时目录）安装一次实测跑通，再宣告入库；禁止未经隔离验证直推默认分支。
- 高风险（`critical`/`offensive`）技能的发布升级给负责人确认，不自行放行。

## 质量检查清单

提交/入库前逐项核对：

**元数据：**
- [ ] frontmatter 是有效 YAML，`name` 小写-连字符且与目录一致
- [ ] `description` ≤1024 字符、单行、**无 `<`/`>` 占位符**，触发场景优先 + 一句能力定位，**无步骤流程摘要**（E：说什么场景触发，不替正文写短版；description 须自足覆盖触发，不依赖正文兜底）
- [ ] `risk` / `category` / `source` / `date_added` 已声明

**内容质量：**
- [ ] 指令清晰、可操作（祈使句、动作动词）
- [ ] 有明确的「何时使用此技能」触发说明（触发后作范围确认）
- [ ] 至少有 1 个可复制粘贴的示例
- [ ] 列出了限制和注意事项（已知边缘情况 / 做不到的事）
- [ ] 指导措辞的形式与基线失败类型匹配（禁止 vs 配方 vs REQUIRED 槽 vs 条件谓词；见 `references/skill-writing-guide.md`）
- [ ] 技术准确性已验证，无拼写错误

**可用性：**
- [ ] 初学者能按步骤执行
- [ ] 解决一个真实问题，而非空泛建议
- [ ] 不依赖超窄的具体例证（避免过拟合到测试用例）
- [ ] 涉及命令/安装的内容通过安全审查（无 `curl ... | bash` 等管道，无明文密钥示例）
- [ ] 若为纪律型技能：已含防合理化设计（借口表/红旗清单/封漏洞）
- [ ] 跨技能引用不用 `@` 语法（用纯技能名 + 显式 REQUIRED 标记）

**渐进披露 / 引用纪律：**
- [ ] references 只从 SKILL.md 一层深引用、references 之间不互链成图
- [ ] >100 行的 references 文件顶部有目录；超大文件在 SKILL.md 引用处附 grep 模式
- [ ] 触发用例（`evals.json`/场景）随技能沉淀，改动技能后跑过回归
- [ ] 入库前做过 secret 扫描；基线失败记录（verbatim）留存

## 安全护栏

- 攻击性技能（渗透 / 红队 / 利用）：**必须以「AUTHORIZED USE ONLY / 仅限授权使用」免责声明开头**，指令中明确要求代理在执行任何利用或攻击命令前请求用户确认，推荐在 Docker/VM 等受控环境运行。
- 防御性/分析类技能：审计默认只读；未经用户明确同意不得把数据上传到第三方。
- 技能正文中的命令示例不得包含危险管道（`curl|bash`、`wget|sh`、`irm|iex`）或内联密钥/token；确为操作必需的，需使用 `<!-- security-allowlist: ... -->` 声明并附警告上下文。
- 不编写、不复制恶意软件、勒索软件或非教育性利用负载。
- 一旦发现技能需要凭据、权限、生产数据或会造成后果的外部动作，停下来升级给负责人，而不是「尽力而为」。

## 多客户端安装指引

技能本体是通用目录格式 `skills/<name>/SKILL.md`，安装 = 把该目录放到目标客户端的 skills 目录，重启客户端生效。本技能自身与本技能产出的技能安装同理（直接放置本技能目录 + 重启 + 用真实任务触发验证）。

### 直接放置到客户端目录

三种已支持客户端均可手动放置（以目标客户端官方文档为准）：

- **Claude Code**：全局 `~/.claude/skills/<name>/`；工作区 `<项目根>/.claude/skills/<name>/`。同名时全局覆盖工作区；技能目录可以是符号链接。
- **OpenCode**：全局 `~/.config/opencode/skills/<name>/`；工作区 `<项目根>/.opencode/skills/<name>/`；也可在 `opencode.json` 的 `skills.paths` 注册任意目录（loader 递归扫描 `**/SKILL.md`）。opencode 还兼容读 `~/.claude/skills/` 与 `~/.agents/skills/`——别在多个枢纽重复安装同一技能。
- **Codex (OpenAI)**：全局 USER 域 `~/.agents/skills/<name>/`；工作区 REPO 域 `<项目根>/.agents/skills/<name>/`。`~/.codex/skills` 是 Codex 的 SYSTEM 域（内置技能），不要写入。注意 Codex 内置同名 `.system/skill-creator`，安装后选择器会并存两个。

安装后验证：用一个真实小任务触发试运行，确认技能被正确加载、按指令执行。

## 相关技能

- `agent-creator` — 同构的代理创建器（技能沉淀到一定规模后，可升级为专职 Agent）

## 常见问题

**Q: 技能不会被触发怎么办？**
A: 优化 `description`：前部加具体触发场景、口语/近义说法；补充「近似干扰项」做触发测试（见阶段 7）。

**Q: 技能太长超过 1000 行？**
A: 把细节拆到 `references/` 子文件按需加载，正文保留工作流与选择逻辑，给出读取指引。

**Q: 技能同时覆盖多个领域？**
A: 按变体拆分：正文放工作流+选择逻辑，`references/` 每领域一个文件（如 `aws.md` / `gcp.md` / `azure.md`）。

**Q: 一个工作流应该做成技能还是 Agent 或命令？**
A: 简短的单次交互用命令；可复用的多步骤流程先做技能；技能稳定、需持续关注某领域后再考虑专职 Agent。

**Q: 用户给的是抽象需求，没有具体工作流？**
A: 引用阶段 1 的提问逐条引导，让用户描述「平时反复做的那几件事」，而不是替用户设计一个。

## 限制和注意事项

- 本技能产出的是**通用目录格式**的技能，各客户端对 frontmatter 扩展字段支持程度不同；以目标客户端文档为准。
- 触发准确性无法 100% 保证，`description` 需要持续迭代。
- 本技能不自动执行测试运行环境（如无 Python）、不代替用户最终审核；安装到生产客户端前应先在测试项目验证。
- 自动验证脚本依赖 Python 3 + PyYAML；缺 `python` 时手动对照质量检查清单。
- Windows 下安装路径与类 Unix 不同（`~/.config` 对应 `%USERPROFILE%\.config`），跨平台请以实际路径为准。
- 本技能不替代业务负责人与市场/治理方的审批；需要授信或发布时升级给相应负责人。