# skills/ — 技能审计（SKILLS-AUDIT）

> 用途：审计 `skills/` 库中每个技能的**数据来源** 与 **入库流程合规性**。事实源 = 各 `SKILL.md` frontmatter + 本仓库 git 历史 + 技能创建器（本仓库 `skill-creator/skills/skill-creator/`）`evolutions/` 对比记录。
> 范围：只审计能力库条目（`skills/` 下入库技能）。skill-creator 工作区及其成品是**创建工具**，排除在审计之外（其迭代记录走自身 `evolutions/`）。
> 依据：本仓库根 `AGENTS.md`「能力库准入与审计」（规则 2：技能入库**无论参考本地文件还是远程仓库，必须经过 skill-creator**；规则 3：**参考外部仓库的技能必须在审计文件中标注数据来源**；规则 4：**技能按功能放入分类目录 `skills/<分类>/<name>/`，分类不存在则创建**）。
> 本次审计日期：2026-09-03（2026-09-09 更新：prd-generator 转合规）

## 1. 审计结论摘要

| 指标 | 数值 |
|---|---|
| 技能总数 | 3（pr-summarizer / code-review-skill / prd-generator） |
| 经 skill-creator 生成流程 | 3 ✅（1 自建 + 2 上游导入均合规，含 evolutions 记录） |
| 远程仓库来源（参考上游 / 直接导入） | 3（sickn33/agentic-awesome-skills 的 comprehensive-review-pr-enhance；awesome-skills/code-review-skill；snarktank/ralph 的 prd skill） |
| 本地文件来源 | 0 |
| `source: self`（自建） | 1 |
| `source: community`（上游导入） | 2 |

**审计结论**：
- ✅ **pr-summarizer 合规（规则 2）**：本仓库自建，完整经过 skill-creator 流程（创建 → 检索上游 → 对比择优 → `evolutions/` 记录 → 验证）。
- ✅ **code-review-skill 合规（规则 2、3、4）**：2026-09-03 按用户指定从上游 `awesome-skills/code-review-skill`（MIT）直接导入并适配——整目录（reference/assets/scripts + LICENSE）入库 `skills/development/code-review-skill/`；frontmatter 补齐本地 schema（category/risk/source/version/date_added/tags/tools），补 `Examples`/`Limitations` 章节，`validate_skills.py --strict` 通过。
- ✅ **prd-generator 合规（规则 2、3、4）**：2026-09-07 从 `snarktank/ralph` 的 prd skill（MIT）直接导入并适配——方法论吸收 + 中文产品化（frontmatter 补齐本地 schema category: product / risk: safe / source: community / author 归属；补 何时使用/示例/限制/安全 章节；PRD 模板章节名保留上游英文），`validate_skills.py --strict` 通过；2026-09-09 复核上游索引 0 命中（A 空）、补写 full evolutions 记录 → 转合规。
- ✅ **规则 3 达标**：本文件已标注全部外部数据来源（上游 comprehensive-review-pr-enhance、code-review-skill、snarktank/ralph）。

## 2. 数据来源

| 来源类型 | 来源详情 | 涉及技能 |
|---|---|---|
| 自建（skill-creator 流程） | 本仓库创建；frontmatter `source: self` | pr-summarizer |
| 远程仓库（上游参考） | `sickn33/agentic-awesome-skills` 的 `comprehensive-review-pr-enhance`（83 行，2 文件，risk: critical） | pr-summarizer（吸收其变更分类表/类别驱动清单/大 diff 分拆/风险标注精华） |
| 远程仓库（整目录导入，MIT） | `awesome-skills/code-review-skill`（https://github.com/awesome-skills/code-review-skill，1.9k star，SKILL.md ~232 行 + reference/ 26 语言指南 + cross-cutting 5 + assets/ + scripts/，约 848KB/50 文件） | code-review-skill（整目录导入并适配本地 schema，保留 LICENSE 归属） |
| 远程仓库（方法论导入，MIT） | `snarktank/ralph`（https://github.com/snarktank/ralph，skills/prd/SKILL.md，英文单文件方法论） | prd-generator（方法论吸收 + 中文产品化适配，`author` 字段归属上游） |

> 上游对比/导入记录（位于技能创建器 `skill-creator/skills/skill-creator/evolutions/`）：`2026-09-02-compare-pr-summarizer.md`（自建版采纳上游精华 + 差异化定位）；`2026-09-03-import-code-review-skill.md`（本地无候选 A → 直接导入上游 B，整目录）；`2026-09-09-import-prd-generator.md`（本地无候选 A → 直接导入上游 B，方法论吸收 + 中文产品化）。

## 3. 技能清单

| 技能名 | 位置 | category | risk | source | 数据来源 | 经 skill-creator | 结论 |
|---|---|---|---|---|---|---|---|
| pr-summarizer | `skills/git/pr-summarizer/SKILL.md` | git | safe | self | 自建 + 上游 sickn33/agentic-awesome-skills（comprehensive-review-pr-enhance） | ✅ | ✅ 合规（2026-09-03 按规则 4 迁入 `skills/git/`） |
| code-review-skill | `skills/development/code-review-skill/SKILL.md` | development | safe | community | 上游 `awesome-skills/code-review-skill`（MIT）整目录导入 | ✅ | ✅ 合规（2026-09-03 导入，保留 LICENSE 归属） |
| prd-generator | `skills/product-design/prd-generator/SKILL.md` | product | safe | community | 上游 `snarktank/ralph` 的 prd skill（交互式需求规格化，MIT，方法论吸收 + 中文产品化） | ✅ | ✅ 合规（2026-09-09 补 evolutions 记录后转合规） |

## 4. 维护要求

- 新增/迁移/改进技能入库后，**必须更新本文件**：登记数据来源（规则 3）与是否经 skill-creator（规则 2）。
- 参考外部仓库（远程或本地）的技能，数据来源必须可追溯到具体上游仓库与条目（连同技能创建器 `skill-creator/skills/skill-creator/evolutions/` 对比记录）。
- 本文件与 `agents/AGENTS-AUDIT.md` 同构（互为镜像，随各自能力库目录存放），均为数据来源的唯一记录入口。

## 5. 整改建议（未完成项）

- 后续每个入库技能都应在本文件中登记；若存在上游同类技能但未做对比择优，需补走技能创建器对比环节并记录到其 `skill-creator/skills/skill-creator/evolutions/`。