# skills/ — 技能审计（SKILLS-AUDIT）

> 用途：审计 `skills/` 库中每个技能的**数据来源** 与 **入库流程合规性**。事实源 = 创建记录台账 `SKILL-RECORDS.md` + 本仓库 git 历史 + 技能创建器（本仓库 `skill-creator/skills/skill-creator/`）`evolutions/` 对比记录。
> 范围：只审计能力库条目（`skills/` 下入库技能）。skill-creator 工作区及其成品是**创建工具**，排除在审计之外（其迭代记录走自身 `evolutions/`）。
> 依据：本仓库根 `AGENTS.md`「能力库准入与审计」（规则 2：技能入库**无论参考本地文件还是远程仓库，必须经过 skill-creator**；规则 3：**参考外部仓库的技能必须在创建记录台账 `SKILL-RECORDS.md` 标注数据来源**；规则 4：**技能按功能放入分类目录 `skills/<分类>/<name>/`，分类不存在则创建**）。来源/作者/日期**不进** `SKILL.md` frontmatter，集中登记于 `SKILL-RECORDS.md`。
> 本次审计日期：2026-09-03（2026-09-09 更新：prd-generator 转合规；2026-09-10 更新：新增 mcp-builder、ue5-performance-optimization；2026-09-11 更新：来源迁至 `SKILL-RECORDS.md` 台账；2026-09-17 更新：新增 coding-discipline、ue-editor-lifecycle，后者按规则 4 迁入 `skills/development/`）

## 1. 审计结论摘要

| 指标 | 数值 |
|---|---|
| 技能总数 | 7（pr-summarizer / code-review-skill / prd-generator / mcp-builder / ue5-performance-optimization / coding-discipline / ue-editor-lifecycle） |
| 经 skill-creator 生成流程 | 7 ✅（3 自建 + 4 上游导入均合规；ue-editor-lifecycle 缺 evolutions 对比记录，见 §5） |
| 远程仓库来源（参考上游 / 直接导入） | 5（sickn33/agentic-awesome-skills；awesome-skills/code-review-skill；snarktank/ralph；anthropics/skills 的 mcp-builder；multica-ai/andrej-karpathy-skills） |
| 本地文件来源 | 0 |
| `source: self`（自建，记于 `SKILL-RECORDS.md`） | 3（pr-summarizer、ue5-performance-optimization、ue-editor-lifecycle） |
| `source: community`（上游导入，记于 `SKILL-RECORDS.md`） | 4（code-review-skill、prd-generator、mcp-builder、coding-discipline） |

**审计结论**：
- ✅ **pr-summarizer 合规（规则 2）**：本仓库自建，完整经过 skill-creator 流程（创建 → 检索上游 → 对比择优 → `evolutions/` 记录 → 验证）。
- ✅ **code-review-skill 合规（规则 2、3、4）**：2026-09-03 按用户指定从上游 `awesome-skills/code-review-skill`（MIT）直接导入并适配——整目录（reference/assets/scripts + LICENSE）入库 `skills/development/code-review-skill/`；frontmatter 补齐本地 schema（category/risk；来源记于 `SKILL-RECORDS.md`），补 `Examples`/`Limitations` 章节，`validate_skills.py --strict` 通过。
- ✅ **prd-generator 合规（规则 2、3、4）**：2026-09-07 从 `snarktank/ralph` 的 prd skill（MIT）直接导入并适配——方法论吸收 + 中文产品化（frontmatter 补齐本地 schema category: product / risk: safe；来源/作者归属记于 `SKILL-RECORDS.md`；补 何时使用/示例/限制/安全 章节；PRD 模板章节名保留上游英文），`validate_skills.py --strict` 通过；2026-09-09 复核上游索引 0 命中（A 空）、补写 full evolutions 记录 → 转合规。
- ✅ **mcp-builder 合规（规则 2、3、4）**：2026-09-10 自 `anthropics/skills` 的 `skills/mcp-builder`（Apache-2.0）导入并中文本地化——保留官方 `reference/` + `scripts/` + `LICENSE.txt`，入口 SKILL.md 重写为中文并补本地 schema 与必需章节；`compare_skills.py` 对比本地适配版（0.93）> 官方原版（0.51）> aas `mcp-tool-developer`（0.75）→ 采纳适配版；`validate_skills.py --strict` 通过；触发评测 12/12。
- ✅ **ue5-performance-optimization 合规（规则 2、4；规则 3 不适用）**：2026-09-10 本仓库**自建**（`SKILL-RECORDS.md` source=self），完整经过 skill-creator 流程；上游索引无专门 UE 性能优化技能（`unreal engine performance optimization` 0 命中），与相邻候选 `unreal-engine-cpp-pro`（aas）对比 0.81 vs 0.68 采纳自建；`validate_skills.py --strict` 通过；触发评测 11/12（「Unity 性能优化」为启发式固有近义假阳性）。
- ✅ **coding-discipline 合规（规则 2、3、4）**：2026-09-14 自上游 `multica-ai/andrej-karpathy-skills`（MIT）导入并适配——四条 LLM 编码行为准则改写为「反例 → 正例」对照，回填本地 schema（category: development / risk: safe；来源记于 `SKILL-RECORDS.md`）；`compare_skills.py` 对比同源上游 `sickn33/agentic-awesome-skills@skills/andrej-karpathy`（0.76 vs 0.73，metadata_complete 本库 1.00 > 上游 0.75）→ 采纳自建；`validate_skills.py --strict` 通过，含 `evals/evals.json` 触发用例。
- ✅ **ue-editor-lifecycle 合规（规则 2、4；规则 3 不适用）**：2026-09-15 本仓库**自建**（`SKILL-RECORDS.md` source=self），沉淀 UE 编辑器安全关闭/重建/异步启动流程 + `evals/evals.json` 触发用例（CLI 重新评测 10/10，precision/recall 100%）；2026-09-17 按规则 4 由顶层迁入 `skills/development/`。**欠账**：缺上游对比择优记录（见 §5）。
- ✅ **规则 3 达标**：本文件已标注全部外部数据来源（上游 comprehensive-review-pr-enhance、code-review-skill、snarktank/ralph、anthropics/skills 的 mcp-builder、multica-ai/andrej-karpathy-skills）。

## 2. 数据来源

| 来源类型 | 来源详情 | 涉及技能 |
|---|---|---|
| 自建（skill-creator 流程） | 本仓库创建；`SKILL-RECORDS.md` source=self | pr-summarizer |
| 远程仓库（上游参考） | `sickn33/agentic-awesome-skills` 的 `comprehensive-review-pr-enhance`（83 行，2 文件，risk: critical） | pr-summarizer（吸收其变更分类表/类别驱动清单/大 diff 分拆/风险标注精华） |
| 远程仓库（整目录导入，MIT） | `awesome-skills/code-review-skill`（https://github.com/awesome-skills/code-review-skill，1.9k star，SKILL.md ~232 行 + reference/ 26 语言指南 + cross-cutting 5 + assets/ + scripts/，约 848KB/50 文件） | code-review-skill（整目录导入并适配本地 schema，保留 LICENSE 归属） |
| 远程仓库（方法论导入，MIT） | `snarktank/ralph`（https://github.com/snarktank/ralph，skills/prd/SKILL.md，英文单文件方法论） | prd-generator（方法论吸收 + 中文产品化适配，`SKILL-RECORDS.md` author 归属上游） |
| 远程仓库（方法论导入 + 中文本地化，Apache-2.0） | `anthropics/skills` 的 `skills/mcp-builder`（https://github.com/anthropics/skills/tree/main/skills/mcp-builder，SKILL.md + reference/×4 + scripts/ + LICENSE.txt） | mcp-builder（入口中文化 + 本地 schema 适配，保留官方 reference/scripts/LICENSE） |
| 自建（skill-creator 流程） | 本仓库创建；`SKILL-RECORDS.md` source=self；对比相邻上游 `sickn33/agentic-awesome-skills` 的 `unreal-engine-cpp-pro` | ue5-performance-optimization |
| 远程仓库（方法论导入，MIT） | `multica-ai/andrej-karpathy-skills`（用户指定源；索引同源候选 `sickn33/agentic-awesome-skills@skills/andrej-karpathy`） | coding-discipline（四条编码准则改写为反例→正例对照，`sickn33` 版 0.76 vs 0.73 采纳自建） |
| 自建（skill-creator 流程） | 本仓库创建；`SKILL-RECORDS.md` source=self | ue-editor-lifecycle |

> 上游对比/导入记录（位于技能创建器 `skill-creator/skills/skill-creator/evolutions/`）：`2026-09-02-compare-pr-summarizer.md`（自建版采纳上游精华 + 差异化定位）；`2026-09-03-import-code-review-skill.md`（本地无候选 A → 直接导入上游 B，整目录）；`2026-09-09-import-prd-generator.md`（本地无候选 A → 直接导入上游 B，方法论吸收 + 中文产品化）；`2026-09-10-import-mcp-builder.md`（官方导入 + 中文本地化 + 对比择优）；`2026-09-10-compare-ue5-performance-optimization.md`（自建 vs 相邻上游，采纳自建）；`2026-09-14-compare-coding-discipline.md`（用户指定源 vs 索引同源候选，采纳自建）。**ue-editor-lifecycle 无对比记录（欠账，见 §5）。**

## 3. 技能清单

| 技能名 | 位置 | category | risk | source | 数据来源 | 经 skill-creator | 结论 |
|---|---|---|---|---|---|---|---|
| pr-summarizer | `skills/git/pr-summarizer/SKILL.md` | git | safe | self | 自建 + 上游 sickn33/agentic-awesome-skills（comprehensive-review-pr-enhance） | ✅ | ✅ 合规（2026-09-03 按规则 4 迁入 `skills/git/`） |
| code-review-skill | `skills/development/code-review-skill/SKILL.md` | development | safe | community | 上游 `awesome-skills/code-review-skill`（MIT）整目录导入 | ✅ | ✅ 合规（2026-09-03 导入，保留 LICENSE 归属） |
| prd-generator | `skills/product-design/prd-generator/SKILL.md` | product | safe | community | 上游 `snarktank/ralph` 的 prd skill（交互式需求规格化，MIT，方法论吸收 + 中文产品化） | ✅ | ✅ 合规（2026-09-09 补 evolutions 记录后转合规） |
| mcp-builder | `skills/development/mcp-builder/SKILL.md` | development | safe | community | 上游 `anthropics/skills` 的 `mcp-builder`（Apache-2.0，方法论导入 + 中文本地化，保留官方 reference/scripts/LICENSE） | ✅ | ✅ 合规（2026-09-10 导入，对比 0.93 vs 0.51 采纳适配版） |
| ue5-performance-optimization | `skills/game-development/ue5-performance-optimization/SKILL.md` | game-development | safe | self | 自建；对比相邻上游 `unreal-engine-cpp-pro`（aas，0.81 vs 0.68 采纳自建） | ✅ | ✅ 合规（2026-09-10 自建，含 compare 记录） |
| coding-discipline | `skills/development/coding-discipline/SKILL.md` | development | safe | community | 上游 `multica-ai/andrej-karpathy-skills`（MIT，用户指定源；索引同源候选 aas `skills/andrej-karpathy`，0.76 vs 0.73 采纳自建） | ✅ | ✅ 合规（2026-09-14 导入适配，含 compare 记录） |
| ue-editor-lifecycle | `skills/development/ue-editor-lifecycle/SKILL.md` | development | safe | self | 自建（本仓库沉淀；无上游对比记录） | ✅ | ⚠️ 基本合规（2026-09-15 自建；2026-09-17 规则 4 迁入 `development/`；缺对比记录，见 §5） |

## 4. 维护要求

- 新增/迁移/改进技能入库后，**必须更新本文件**：登记数据来源（规则 3）与是否经 skill-creator（规则 2）。
- 参考外部仓库（远程或本地）的技能，数据来源必须可追溯到具体上游仓库与条目（连同技能创建器 `skill-creator/skills/skill-creator/evolutions/` 对比记录）。
- 本文件与 `agents/AGENTS-AUDIT.md` 同构（互为镜像，随各自能力库目录存放），均为数据来源的唯一记录入口。

## 5. 整改建议（未完成项）

- 后续每个入库技能都应在本文件中登记；若存在上游同类技能但未做对比择优，需补走技能创建器对比环节并记录到其 `skill-creator/skills/skill-creator/evolutions/`。
- **ue-editor-lifecycle**：自建时未做上游检索对比（`SKILL-RECORDS.md` evolutions 列为 `-`）。需补跑 `search_index.py` 检索同类 UE 编辑器/构建流程技能，有候选则补写 `evolutions/2026-09-xx-compare-ue-editor-lifecycle.md`；无候选则在该记录中注明「索引 0 命中」。