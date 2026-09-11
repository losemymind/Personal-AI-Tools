---
name: agent-creator
description: "创建、改进并验证个人工作流代理（Agents）。当用户需要从零创建代理、把反复出现的工作角色或子代理需求沉淀为代理、修改或优化现有代理、评估代理质量、或为 claude/opencode/codex/deepseek 等客户端管理代理时使用。当用户提到「创建agent」「写个代理」「agent-creator」「把这个角色做成代理」等说法时，使用本技能。"
category: productivity
risk: safe
---

# 代理创建器（agent-creator）

## 概述

本技能指导如何把**工作角色与职责边界**蒸馏为可复用、可验证、跨客户端安装的高质量代理（Agent）。代理与技能不同：技能是「任务怎么做」的指令集，代理是「谁来负责、以什么身份、带什么权限、怎么协作」的角色定义。四端客户端（claude/opencode/codex/deepseek-harness）的代理格式差异由 `references/agent-template.md` 统一承载，安装通过直接放置完成。

一个代理 = **身份定义 + 职责边界 + 工具权限 + 协作协议**，用 AGENT.md（含 frontmatter）表达。

## 何时使用此技能

- 用户要求「把这个角色做成一个代理」、「创建一个 agent」
- 需要一名常驻 LLM 扮演特定角色（审查者、调试者、规划者、测试者等）持续参与工作
- 需要把重复出现的负责人职责（如"PR 审查人""架构决策者"）固化为可复用定义
- 需要改进、重构或评估一个现有代理
- 需要把代理安装到 claude / opencode / codex / deepseek 等客户端的 agents 目录
- 用户明确要分派子代理（subagent）处理某项工作

## 核心理念

### 技能 vs 代理的选择

- **技能**：用户每次触发「怎么做」——流程、规则、模板。适合可描述的步骤化工作。
- **代理**：常驻「谁来做」——身份、权限、协作模式。适合需要持续判断、被其他代理调用、或独立承担责任的角色。
- 规则：流程单一且触发明确 → 技能；需要角色化长期参与 → 代理。二者可嵌套（代理在其职责内引用技能）。

### 身份先于指令

代理的核心是**身份与边界**，不是步骤列表：

1. **角色**：它是谁？（一句话，用户一眼能理解）
2. **职责**：它负责什么？（边界清晰——哪些事它必须做、哪些事它拒绝做）
3. **权限**：它能用什么工具？（最小权限：只给完成职责所需的工具）
4. **协作**：它何时被调用、如何汇报、何时升级给人？
5. **质量**：它的产出如何验收？（可验证的完成标准）

把步骤留给技能，代理只做判断与协调——这是代理与技能的本质分工。

### 最小权限

代理的工具权限遵循**最小权限原则**：只授予完成职责必需的工具。审查代理不该有编辑权限，规划代理不该有执行权限。权限声明清晰可审计（高风险动作显式声明并默认拒绝，必要时请求用户确认）。

### 渐进式披露

代理定义同样遵循三层加载：frontmatter（元数据，始终在上下文）→ AGENT.md 主体（身份/边界/协作）→ 捆绑资源（references/，按需加载）。主体保持克制（理想 <500 行），细节下沉到 `references/`。

**references 引用纪律（硬规则）**：references 只允许从 SKILL.md「读取规则」**一层深**导读，references 之间不互相链接成图（保持按需加载路径可预期）；单文件 >100 行在顶部加**目录**；超大文件（>10k 词）在 SKILL.md 引用处附 **grep 模式**（如 `grep -n "阶段 6" references/xxx.md`）让代理跳过读全文直接定位。

## 资源路径基准

本技能是**自包含完整体**：内部所有引用（`scripts/`、`references/`、`templates/`、`agents/`、`indexes/upstream.db`、`evolutions/`）一律以 **agent-creator 目录自身为根**书写，不依赖任何外部布局。脚本调用：在本技能目录内执行 `python scripts/xxx.py ...`；不在技能目录内执行时加目录前缀 `python "<技能目录>/scripts/xxx.py" ...`。定位本技能目录的方法：codex 的技能列表自带文件路径，直接使用；claude/opencode 按存在性依次探测——工作区候选 `<项目>/.claude/skills/agent-creator/`、`<项目>/.opencode/skills/agent-creator/`、`<项目>/.agents/skills/agent-creator/`；全局候选 `~/.claude/skills/agent-creator/`、`~/.config/opencode/skills/agent-creator/`、`~/.agents/skills/agent-creator/`。

读取规则：references 文档**按需读取**；需要字段/四端差异时读 `references/agent-template.md`，需要结构规范时读 `references/agent-anatomy.md`，需要质量标准时读 `references/agent-quality-bar.md`，需要检索上游/索引细节时读 `references/agent-index.md`，进行对比择优时读 `references/agent-comparison.md`。评审子代理指令在 `agents/`（按需拉起，不自动加载）：需要评分/审核时读 `agents/reviewer.md`（产出 `pass`/`revise` + `review.json`）。

## 代理文件解剖（Anatomy）

```
agents/<agent-name>/
├── AGENT.md             ← 必需：代理定义（frontmatter + 身份/边界/协作）
├── references/          ← 可选：按需加载的深化文档（协作协议、领域准则）
└── README.md            ← 可选：附加说明
```

**关键规则**：只有 `AGENT.md` 是必需的。各客户端的代理文件格式与安装位置见 `references/agent-template.md`。

## 前置元数据字段规范

AGENT.md 顶部用 `---` 包裹 YAML frontmatter。四端支持程度不同（完整对照见 `references/agent-template.md`）：

```yaml
---
name: <agent-name>              # 必需：kebab-case
description: "..."              # 必需：做什么 + 何时使用/被调用，≤200 字符（触发依据）
mode: subagent                  # 客户端相关（opencode: primary/subagent/all）；其他客户端可忽略
model: <provider/model-id>      # 可选：指定模型
tools: [read, grep, bash]       # 可选：允许的工具列表（最小权限）
permission: { "edit": "deny" }  # 可选：权限规则
temperature: 0.2                # 可选
---

# <代理名>
```

**来源/版本/标签不进 frontmatter**：`version`、`tools_clients`、`tags`、`source`、`author`、`date_added` 一律不写入 `AGENT.md`——打包前代理应是**客户端中立、内容自足**的，来源/作者/日期集中记录在代理库根的**创建记录账本**（见「创建记录账本」），版本以 git 提交历史为准；`tools_clients` 的多端适配由打包器/安装阶段决定；领域分层由目录结构表达（`agents/<分类>/…`），无需 `tags`。

### 创建记录账本

frontmatter 只承载**打包前必需且客户端中立**的字段。来源/作者/日期等创建元数据集中写入**创建记录账本**——代理库根的一个 Markdown 文件（本仓库约定 `AGENTS-RECORDS.md`），由 `create_agent.py --records <文件>` 在创建/导入时追加一行：

| 代理 | mode | created | author | source | source_repo | method | evolutions |
|---|---|---|---|---|---|---|---|

- `create_agent.py` 传 `--records` 即自动追加一行；`--author` / `--source`（默认 `self`）/ `--source-repo` / `--method`（默认 `created`）提供各列值。不传 `--records` 则不写账本（任意目录脚手架保持干净）。
- 导入/迁移上游代理时 `method` 记 `imported`/`migrated`，`source` 记 `community`/`official`/`external`，`source_repo` 记 `OWNER/REPO` 或本地来源名。
- 账本是**逐条创建/来源的可查询台账**；与库的**入库审计**文件（`AGENTS-AUDIT.md`）互补：账本记事实，审计记合规结论。

**字段细节与四端兼容矩阵见 `references/agent-template.md`。**

**description 触发面（硬约束）**：description 是代理被**检索/触发/调度**的唯一门面——必须单行、≤200 字符、含「做什么 + 何时被调用/被谁调用」、**不含 `<`/`>` 占位符**、不写步骤摘要。占位符或抽象泛化词会直接扭曲下游的触发匹配，导致代理该出现时不出现、不该出现时乱入。

## 内容结构与写作指南

推荐结构（AGENT.md 主体）：

```markdown
# <代理名>

## 角色定位          # 1-2 句：它是谁、为什么存在
## 职责范围          # 它负责什么（必须做 / 拒绝做）
## 工作方式          # 判断标准、流程要点（步骤细节可引用技能）
## 工具与权限        # 允许/禁止的工具，最小权限声明
## 协作协议          # 何时被调用、如何汇报、何时升级给人
## 完成标准          # 产出如何验收（可验证）
## 限制与边界        # 已知边界、做不到的事、免责声明
```

**写作要点：**
- 祈使句、动作动词；解释每个条款的**为什么**。
- 身份表述比步骤表述优先：「你是 PR 审查者，负责…」而非「1. 读 diff 2. 打分」。
- 职责边界用「必须做 / 拒绝做」两组明确列出——边界是代理质量的核心。
- 工具权限显式声明，最小权限原则。
- 升级路径必须明确（何时把决策交还人类）。
- 用「渐进式披露」：主体克制度，细节进 `references/`。

## 创建流程（核心工作流）

> **可独立安装**：本技能是自包含完整体，可安装到任意客户端/目标项目独立使用——自带角色澄清、脚手架、验证、对比、安装全流程，不依赖任何外部目录结构，也不读取调用方已有的代理库（安装见「多客户端安装指引」）。
>
> **闭环（3 步）**：
> 1. **按用户需求创建一个代理**（阶段 1-4）
> 2. **检索上游**是否已有同类（阶段 0）——有候选 → 对比择优取最优；无候选 → 用自建版本
> 3. **若上游更优** → 采纳并提炼学习点 → 优化本技能方法论（反馈闭环）

### 阶段 0：检索上游代理（先查后建）

先在**本技能自带的上游代理索引**中检索是否有可参考/采纳的现成代理，避免重复造轮子：

```bash
python scripts/search_agent_index.py "<需求关键词>" [--source agency|ccgs|agency-zh] [--category X] [--limit 10]
python scripts/search_agent_index.py --stats               # 索引状态
python scripts/search_agent_index.py --list-categories     # 分类（division）分布
```

- 索引文件 `indexes/upstream.db` 已随技能分发，无需联网即可检索。
- 覆盖三个上游代理仓库（msitarzewski/agency-agents、Donchitos/Claude-Code-Game-Studios、jnMetaCode/agency-agents-zh），含中文代理（`agency-zh`）；英文/中文关键词均可检索。索引细节见 `references/agent-index.md`。
- 索引落后于上游时运行 `python scripts/build_agent_index.py` 重建。

**决策分支：**
- **有匹配候选** → 记录候选；照常创建（阶段 1-4），随后在阶段 5.5 与候选对比择优取最优。
- **无匹配候选** → 用自建版本。
- 若上游更优被采纳 → 提炼学习点记录到 `evolutions/`，反哺优化本技能。

### 阶段 1：捕捉角色与证据

让用户描述**他们实际希望谁来负责什么**，优先提取：

1. 这个代理扮演什么角色？一句话怎么说？
2. 它被谁调用、在什么时机？
3. 它必须做什么？**它坚决拒绝做什么**？（边界最重要）
4. 它需要哪些工具？哪些工具它绝不该碰？
5. 它的产出给谁看、如何验收？
6. 什么情况下它应该停下并交还人类？

有现成的角色描述、PR 审查习惯、协作流程文档就贴出来当证据。

### 阶段 2：确认唯一「人力决策点」

涉及权限授予、生产数据、外部动作的决策必须由用户确认。无法确认 → `BLOCKED`，不替用户拍板。

### 阶段 3：设计与脚手架

- 参考 `references/agent-template.md` 的四端字段兼容矩阵与 `references/agent-anatomy.md` 的结构规范；研究上游候选（阶段 0 命中）的身份表述、边界与协作写法作为范本。
- 使用 `templates/AGENT.template.md` 骨架（或 `python scripts/create_agent.py --name <名> --mode subagent --out <目录>`）。
- 按「身份先于指令」与「最小权限」确定职责边界与工具列表。

### 阶段 4：编写 AGENT.md

按「内容结构与写作指南」编写。顺序建议：先写角色定位（1 句）→ 再写边界（必须/拒绝）→ 然后补协作协议与完成标准。

### 阶段 5：运行自动验证

```bash
python scripts/validate_agents.py [--dir <agents目录>] [--strict]
```

不带 `--dir` 时默认扫描**当前工作目录（CWD）**——在代理库/代理目录根运行即可自然生效；`--dir` 指定其他目录。**无论目标来自哪里，扫到 0 个代理定义都会 fail-loud（退出码 1）**，避免空跑全绿。

验证器检查：frontmatter 有效性（YAML、`name` 格式、`description` 存在且 ≤300 字符）、「职责边界」章节、工具/权限声明、正文非空、引用不悬空（fenced 代码块豁免）、**安全扫描**（明文密钥/凭据、危险远程执行管道，`<!-- security-allowlist -->` 可按行/块豁免）。offensive 类代理（渗透等）同样要求授权声明。

### 阶段 5.5：与上游候选对比择优

若阶段 0 检索到匹配候选，将自建代理与上游候选进行结构化对比（使用 `compare_agents.py`，实现 **质量 7 维 + 结构 4 维** 评分）：

```bash
# 对比单个代理
python scripts/compare_agents.py <自建目录> <上游候选目录>

# 对比某上游目录下的全部候选
python scripts/compare_agents.py <自建目录> <上游目录> --all-candidates
```

评分维度（详见 `references/agent-comparison.md`）：
- **质量 7 维**（权重 60%）：边界清晰度 / 必须做-拒绝做 / 权限声明 / 协作与升级 / 完成标准 / 安全护栏 / 元数据完整
- **结构 4 维**（权重 40%）：渐进式披露 / 资源组织 / 单一职责 / 正文行数控制

**决策：**
- **上游更优** → 分析上游优势维度，提炼学习点，改进 agent-creator 方法论（记录到 `evolutions/`，形成反馈闭环）；必要时直接采纳上游代理。
- **自建更优或持平** → 采纳自建版本，继续阶段 6。
- 对比报告保存至 `evolutions/<日期>-compare-<代理名>.md`。

### 阶段 6：测试与迭代

提出 2-3 个该代理会被调用的真实场景，让代理实际跑一次：验证身份表述、边界执行、权限遵守、汇报格式。根据结果迭代 AGENT.md。

**AI 评审闭环（agent1 ↔ agent2，无人工）**：把代理产物交给**评审子代理**（agent2，读 `agents/reviewer.md`）独立评审，产出 `review.json`（`verdict: pass|revise` + 可执行 `issues[]`）。`revise` 时由作者代理（agent1）按 `issues[]` 逐条修订，再交评审；**`pass` 或达 `max-iterations`（默认 5）即停**。评审者与作者分离——**别让 agent 自评自改闭环自嗨**；客观结构/元数据先过 `validate_agents.py --strict`，主观质量与纪律合规交 reviewer。`review.json` 随迭代目录版本化，下一轮用 `previous_review_path` 核验上轮问题是否修复。客户端无子代理派发能力时**降级不跳过**：由主持会话按同一份 `agents/reviewer.md` 内联扮演评审者。

**触发失败分类（改前先归因）**：被调用行为不符预期时，先归因再决定改哪里——**假阴性**（该出现未出现 → description 漏触发词/说法没覆盖）、**假阳性**（不该出现却乱入 → description 过度泛化/兜底词过多）、**run_error**（被正确调用但运行失败 → 客户端格式/工具/环境问题，与 description 无关别乱改）。三类混改会把「改错病」当成「改好病」。

### 阶段 7：安装与验证

安装 = 把 AGENT.md（或代理目录）放到目标客户端的 agents 目录，重启后调用验证。

- **先按目标客户端转换 frontmatter**：仓库内保持规范形式（`tools: [...]` 白名单 + provider 前缀 model），安装前用本技能适配器转为目标客户端合法形态再放置（各端转换规则与 post-check 见 `references/agent-template.md`）：
  ```bash
  python scripts/adapt_agent.py <代理目录> --client opencode --out <落点>/AGENT.md
  python scripts/adapt_agent.py <代理目录> --client claude  --out <落点>/AGENT.md
  # codex / deepseek：无官方 frontmatter 规范，适配器仅做 YAML 校验后逐字节原样输出
  ```
- **直接放置**：转换产物按目标客户端官方文档说明放入 agents 目录（兼容矩阵与落点见「多客户端安装指引」）。
- **整目录打包（多端产物）**：需要把**同一个代理目录**适配给多个客户端时，用打包器一键生成各端产物（自动复制整棵代理目录 + frontmatter 适配 + 该端 post-check，避免手改漂移）：

  ```bash
  python scripts/package_agent.py <代理目录|AGENT.md> --client claude --client opencode --client codex --client deepseek --out <产物目录> [--zip]
  ```

  产物布局为 `<产物目录>/<客户端>/<代理名>/`（`--zip` 另出同名压缩包，代理名取 frontmatter `name`，缺失时回退目录名/文件名），把该目录放到目标客户端的 agents 目录即可。与单文件适配器 `scripts/adapt_agent.py` 的关系：`adapt_agent.py` 只转换**一个** AGENT.md（写文件/标准输出），`package_agent.py` 则转换**并复制整棵代理目录**、一次产出多端并做同名压缩。关键适配：opencode 端把 `tools` 工具白名单合并进逐工具 `permission`（白名单→allow、其余工具类→deny、显式 permission 优先；**不保留可能放大权限的全局 `permission` 字符串简写**）；claude 端把工具白名单转成逗号分隔的 Claude 工具名、把 provider 前缀 `model` 简化为 alias（无法映射则丢弃）；`tools: [claude, opencode, …]` 这类「支持客户端」元数据不会被误当成工具白名单。各端适配结果均过该端 post-check，不合格不出包。

### 阶段 8：沉淀稳定代理

代理稳定使用后：完善元数据 → 归档到技能库或发布渠道，含测试记录一并沉淀。

## 质量检查清单（提交/入库前）

**元数据：**
- [ ] frontmatter 是有效 YAML，`name` kebab-case 且与目录一致
- [ ] `description` 单行、≤200 字符，包含做什么 + 何时调用，无 `<`/`>` 占位符
- [ ] **无** `version`/`tools_clients`/`tags`/来源字段（来源进创建记录账本 `AGENTS-RECORDS.md`，版本以 git 为准）

**边界与权限：**
- [ ] 「职责范围」章节同时列出 必须做 / 拒绝做
- [ ] 工具列表最小权限（无无关工具）
- [ ] 权限有风险的动作（删除/推送/生产）显式声明或拒绝
- [ ] 有清晰的升级路径（何时交还人类）

**内容质量：**
- [ ] 角色定位一句话可懂
- [ ] 协作协议明确（何时被调用/如何汇报）
- [ ] 完成标准可验证
- [ ] 列出限制与边界

**可用性：**
- [ ] 初学者（其他代理）能按协议调用它
- [ ] 解决一个真实角色需求，而非泛泛职责堆砌
- [ ] 涉及命令/安装的内容通过安全审查

**渐进披露与引用组织：**
- [ ] 主体克制（理想 <500 行），细节下沉 `references/`
- [ ] references 由 SKILL.md 一层深导读，references 之间不互链成图
- [ ] 大文件顶部有目录；正文/资源引用不悬空

## 入库与发布纪律（提交/入库前逐项）

- **secret 扫描**：提交/入库前扫一遍代理目录与脚本，确认无明文密钥/token/凭据示例；危险管道（curl 下载执行等）按「安全护栏」处理，必要时显式声明授权边界。
- **隔离验证再交付**：非直推——代理先在本技能验证（阶段 5）+ 真实场景试跑（阶段 6），在**隔离环境**（独立客户端/临时目录）安装实测一次通过后再宣告入库；未经验证的草稿不得直接当成品交付。
- **版本化原子补丁**：代理或方法论改动记录原因（代理版本以 git 提交历史为准、不写 frontmatter；本技能改进记 `evolutions/`），不要把未经单独验证的草稿直接应用进 `SKILL.md`。

## 安全护栏

- 代理执行权限遵循最小权限；涉及破坏性动作的代理必须显式声明并默认拒绝。
- 攻击性代理（渗透/红队）：同样要求「AUTHORIZED USE ONLY / 仅限授权使用」声明与执行前用户确认。
- 不创建「伪装成正常身份但实际授权越界」的代理——身份与权限必须一致、可审计。
- 需要凭据、权限、生产数据的场景：停下来升级给用户，不要「尽力而为」。

## 多客户端安装指引

本技能自身是**技能形态**（SKILL.md + scripts/ + references/…）：安装 = 把本技能目录复制到目标客户端的 **skills** 目录，重启客户端生效（落点：claude `~/.claude/skills/`、opencode `~/.config/opencode/skills/`、codex `~/.agents/skills/`；工作区对应 `<项目根>/.claude/skills/` 等）。

### 自安装（本技能自身；LLM 客户端直接执行，无需外部工具）

被要求把本技能安装到某客户端时，按序执行，不依赖任何仓库级工具：

1. **定位本技能目录**：按「资源路径基准」的探测顺序定位（codex 用技能列表自带路径）。
2. **选定作用域与端**（先问用户）：全局（默认）或工作区（**必须落到 git 仓库根**）。
3. **放置**：把本技能目录**整体**复制到目标客户端的 **skills** 目录（矩阵见上一段），排除 `__pycache__/` 等缓存。
4. **安装后自检**（本技能工具链自包含，逐项确认可用）：`python scripts/search_agent_index.py --stats`（索引来源与条数）；再跑一次脚手架→验证往返：`python scripts/create_agent.py --name install-check --mode subagent --no-interactive --out ./install-check-tmp`，随后 `python scripts/validate_agents.py --strict --dir ./install-check-tmp`，通过后删除临时目录。
5. **清理缓存**：删除安装目录内的 `__pycache__/`。
6. **交付**：提示重启客户端，用真实代理请求触发一次，并输出确切安装路径。

> 覆盖更新：备份已装目录 → 新版本整目录覆盖（目录名不变）→ 重跑第 4 步；卸载 = 删除安装目录（只删本技能副本）。

产出的**代理**本体是单文件 `AGENT.md`（或含 references 的目录 `agents/<name>/`）。安装 = 用 `scripts/adapt_agent.py` 按目标客户端转换 frontmatter → 放到目标客户端的 agents 目录 → 重启客户端生效：

| 端 | 代理目录（全局） | 代理目录（工作区） |
|---|---|---|
| claude | `~/.claude/agents/` | `<项目根>/.claude/agents/` |
| opencode | `~/.config/opencode/agent/` | `<项目根>/.opencode/agent/` |
| codex | 代理放置无官方约定（best-effort，以官方文档为准） | 同左 |
| deepseek | 随版本，`DEEPSEEK_HARNESS_ROOT` 兜底 | 同左 |

不同客户端对代理的字段支持不同（兼容矩阵见 `references/agent-template.md`）；仓库规范形 → 目标客户端形的前置转换由 `scripts/adapt_agent.py` 完成（转换失败即退出、不产出无法加载的文件）。

## 常见问题

**Q: 什么时候该做代理而不是技能？**
A: 需要常驻角色、权限、协作协议 → 代理；只是一次性步骤流程 → 技能。技能是代理的「工具包」。

**Q: 四端 frontmatter 不兼容怎么办？**
A: 仓库内保持规范形式（name/description/mode + `tools: [...]` 白名单，来源进创建记录账本）；安装时用 `scripts/adapt_agent.py --client <端>` 转换（claude/opencode 自动适配 + post-check，codex/deepseek 原样校验后输出）。

**Q: 代理需要跨多个职责？**
A: 保持单一职责——一个代理一件事，协作流程解决多角色需求（多个代理通过协作协议互相调用）。

**Q: 代理与子代理（subagent）？**
A: mode=subagent 的代理被主代理调用，用于隔离上下文与专注任务；mode=primary 用于用户直接对话。

## 限制和注意事项

- 各客户端对代理字段支持程度不同，安装前以目标客户端文档为准（兼容矩阵在 `references/agent-template.md`）。
- 代理的「协作协议」依赖客户端实际的多代理能力（如 opencode 的 task/subagent、claude 的 subagent），能力差异会影响协作效果。
- 本技能不自动执行测试运行环境、不代替最终审核；安装到生产客户端前先验证。
- Windows 下路径与类 Unix 不同（`~/.config` 对应 `%USERPROFILE%\\.config`），跨平台以实际路径为准。