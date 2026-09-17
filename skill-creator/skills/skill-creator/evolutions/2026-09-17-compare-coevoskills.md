# 对比记录：本地 skill-creator vs 上游 CoEvoSkills 的 meta skill-creator

## 基本信息
- 日期：2026-09-17
- 需求描述：用户要求把 `https://github.com/Zhang-Henry/CoEvoSkills/tree/main/meta_skills/skill-creator` 加入上游索引；该条目本身是一个 skill-creator（元技能竞品），故同期做方法论对比
- 上游来源（用户指定）：`Zhang-Henry/CoEvoSkills` → `meta_skills/skill-creator/`（Apache-2.0，67★，main，最后推送 2026-08-20）
- 索引登记：`coevoskills`（本次新增的第五个索引源，见 `2026-09-17-adopt-coevoskills-source.md`）
- 对比对象：稀疏取数落地的 18 文件上游目录（`SKILL.md` 251 行 + `agents/`×3 + `references/schemas.md` + `scripts/`×8 + `eval-viewer/` + `assets/`）

## 对比报告

```text
LOCAL      skill-creator  total 0.98
  quality : trigger_clarity=1.00  example_available=1.00  limitations_declared=1.00
            risk_declared=1.00   security_guardrails=0.80 metadata_complete=1.00
  struct  : progressive_disclosure=1.00  resource_organization=1.00
            script_reuse=1.00          body_size_control=1.00
  body: 535 lines | files: 240 | dirs: agents,evolutions,examples,indexes,references,scripts,templates

UPSTREAM   skill-creator  total 0.55
  quality : trigger_clarity=0.00  example_available=0.50  limitations_declared=0.00
            risk_declared=0.00   security_guardrails=0.80 metadata_complete=0.50
  struct  : progressive_disclosure=1.00  resource_organization=0.67
            script_reuse=1.00          body_size_control=1.00
  body: 252 lines | files: 18 | dirs: agents,assets,eval-viewer,references,scripts
```

> 评分解读需扣掉 schema 口径：`trigger_clarity` / `risk_declared` / `limitations_declared` / `metadata_complete` 的差距主要来自两库 frontmatter 约定不同——上游是 Claude 插件风格（`name`/`description`/`compatibility`，无 `risk`/`category`，正文无「限制/风险」章节），本地库 schema 强制这些章节。**不要**据此断言上游方法论更弱；下面按实质内容分析。

## 结论
- 优者：**本地（自建）**——总分 0.98 vs 0.55（结构 1.00 vs 0.92），且扣掉 schema 口径后实质内容仍为**超集**。
- 采纳决定：不整目录采纳上游；**登记为索引源 + 方法论参考源**，抽取 2 条学习点（见下），不改动成品方法论主体。

## 差异分析

**同源关系（首要事实）**：上游与**本地基线同血脉**——其 `agents/{grader,comparator,analyzer}.md`、`scripts/{aggregate_benchmark,run_eval,run_loop,utils,package_skill}.py`、`references/schemas.md` 与 Anthropic 官方 skill-creator 工具链同名同职责（本仓库的评测链即移植自官方，见工作区 `README.md`「来源与沿革」）。因此这不是「两套方法论对决」，而是「同一基线 + 各自增量」，对比重点落在增量上。

**上游相对本地的增量（3 项）**
1. **评测结果可视化评审页** `eval-viewer/generate_review.py`（471 行，纯 stdlib）：发现 workspace 下的 run 目录 → 把输出数据内嵌成**自包含 HTML** → 起微型 HTTP 服务供人审阅，反馈自动写回 `feedback.json`（支持 `--previous-feedback` 续审）。
2. **description 优化循环的 HTML 报告** `scripts/generate_report.py`（326 行）：把 `run_loop.py` 的 JSON 输出渲染成可视化报告，逐次尝试对每个用例画 ✓/✗，且**区分 train/test 查询**（过拟合一眼可见）。
3. **流程立场**：`SKILL.md` 明确「fully autonomous workflow — do not wait for or request human feedback at any step」（全程无人反馈）。

**本地相对上游的增量（更大）**
- 治理与验证：`validate_skills.py` 全量验证器（frontmatter/章节/安全/引用/密钥扫描）+ strict 发布门；上游仅 `quick_validate.py`（118 行最小 YAML 校验）。
- 方法论广度：10 阶段工作流 + 阶段 0「先查后建」多源索引（本次扩到 5 源 2188 条）+ 阶段 5.5 对比择优 + `evolutions/` 反馈闭环 + `references/` 7 篇深化文档 + `templates/` + `examples/`。
- 多端与本地化：`run_eval.py` heuristic/cli 双模式、四端客户端、进程树终止、逐查询隔离工作区；`package_skill.py` 按端适配 frontmatter + post-check。上游 `run_eval.py`/`improve_description.py` 直接调 `claude -p`（单端锁定）。
- 中文产品文档与安装手册。

**上游的明显缺陷（记录，不学习）**
- `eval-viewer/`、`generate_report.py`、`improve_description.py` **在任何 md 中都未被引用**（逐文件 grep 确认：`SKILL.md` 的「Reference files」只列 `agents/*.md` 与 `references/schemas.md`）——工具存在但入口不可达，属文档盲区；我们引入同类能力时必须同步 SKILL.md 导读。

## 提炼的学习点
1. **评测/基准的可视化评审面是有价值的缺口**：我们目前的评审产出是 `benchmark.md` 文本 + `agents/reviewer.md`（结构化 `review.json`），缺少「人类能低成本扫一遍所有 run 输出」的形态。上游的「自包含 HTML + 微型 HTTP 服务 + `feedback.json` 回流」是纯 stdlib 可实现的轻量方案，可作为 `--html` 报告或评审页的候选实现路径（**先记不采纳**——本项目「无人工评审闭环」是已定纪律，需先明确它服务的是「人审」还是「子代理审」）。
2. **train/test 划分要落到可视产物**：我们 `run_loop.py` 已有 train/test 60/40 划分，但只有 JSON；上游把 train/test 在一张报告里区分呈现，使过拟合可见。若后续给 `run_loop.py` 加报告，train/test 区分应作为必需要素。
3. **不采纳「零人工反馈」立场**：本地库的决策门（入库、发布、删除文件、验证器语义变更）明确要求人类确认（见工作区 `AGENTS.md`「何时停下来问用户」）。这是**有意差异**，记录以免后续误采。

## 改进建议（可选，未实施）
- 候选升级（不属本次范围，需用户确认）：给 `run_loop.py` / `aggregate_benchmark.py` 增 `--html` 自包含报告（stdlib，train/test 区分），或评估 `eval-viewer` 式评审页在「子代理评审闭环」中的位置。
