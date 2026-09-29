# 七个技能的来源与采纳摘要

覆盖 2026-09-02—09-23；2026-09-29 合并，技能身份与原始来源事实不变。原记录逐项对应 [旧记录映射](record-map.md)。

下列分数来自当时静态比较器，受元数据 schema 与资源结构影响；启发式触发通过率代表词面代理指标。保留历史采纳理由，不将其提升为同场景实测增益。旧 frontmatter 来源/版本字段已迁入创建账本，不能按旧记录回填。

<a id="pr-summarizer"></a>
## pr-summarizer（09-02，自建并借鉴）

- **需求/候选**：从 git diff 生成 PR 摘要、检查清单与风险；对比 [aas 的 comprehensive-review-pr-enhance](https://github.com/sickn33/agentic-awesome-skills/tree/main/skills/comprehensive-review-pr-enhance)，当时 83 行、2 文件、risk critical。
- **决定**：保留自建的轻量总结定位，吸收 source/test/config/docs 分类、类别驱动清单、大 diff 分拆（>20 文件或 >1000 行）和 breaking/安全路径风险提示；增加语义化标题、一句话摘要、受众分层与复检衔接。
- **证据/边界**：原比较是方法论逐项分析，无量化任务增益；后续 09-10 启发式 11/11。上游优势与本地差异分别保留，不宣称全面胜出。
- **学习点**：清单随输入类别调整，摘要先于细节。

<a id="code-review-skill"></a>
## code-review-skill（09-03，整目录导入）

- **来源**：用户指定 [awesome-skills/code-review-skill](https://github.com/awesome-skills/code-review-skill)，MIT，保留 LICENSE；本地当时无同类候选（仅 PR 摘要）。上游约 50 文件/848KB，含 26 语言指南、5 篇跨领域指南、assets 与分析脚本。
- **决定**：整目录语料导入，补本地字段、Examples 与 Limitations，保留 allowed-tools 和原四阶段流程；不纳入网页脚手架与站点配置。来源、作者等现集中记账。
- **证据/边界**：当时 strict 通过；09-10 启发式 10/11，残留“总结 PR 改动”假阳性由共享关键词导致。无本地竞争者，属于导入适配，不能伪称完成双方任务比较。
- **学习点**：资源丰富的上游保留完整可用引用树；显式补齐示例与限制。

<a id="prd-generator"></a>
## prd-generator（09-07 导入，09-09 补齐对比）

- **来源**：[snarktank/ralph 的 skills/prd](https://github.com/snarktank/ralph/tree/main/skills/prd)，09-09 核 LICENSE 为 MIT。英文单文件方法论约 300 行；本地无候选，当时 aas/addy 的 2132 条索引中 prd/requirements/spec 检索 0 命中。
- **决定**：方法论吸收并中文化，保留英文产物模板章节。保留 3—5 个选项澄清、9 章节 PRD、可验证验收标准、UI 验证、Non-Goals，以及只生成文档的范围；输出 tasks/prd-[feature-name].md。
- **证据/边界**：09-09 strict 复核通过，09-10 启发式 11/11。检索 0 命中是当时索引事实，不代表所有外部实现均不存在。
- **学习点**：叙述本地化、模板结构保真；单文件方法论适合吸收重写。

<a id="mcp-builder"></a>
## mcp-builder（09-10，官方导入与中文适配）

- **来源**：[anthropics/skills 的 mcp-builder](https://github.com/anthropics/skills/tree/main/skills/mcp-builder)，Apache-2.0，保留 LICENSE.txt、四份 reference 与 scripts。索引有 MCP 候选，本地无现成条目；另比 Composio 分发副本、aas 的 mcp-builder / mcp-tool-developer。
- **决定**：中文入口保留研究规划→实现→评审测试→评测集四阶段、Python/TypeScript 两条路径；补本地 schema、章节与 12 个触发用例。
- **证据/边界**：静态分适配版 0.93、官方原版 0.51、aas mcp-tool-developer 0.75；差值主要来自本地规范适配，不表示官方内容质量低。strict、脚本编译与启发式 12/12 通过，无双方真实任务增益记录。
- **学习点**：入口层可本地化，深文档与运行脚本保持来源完整。

<a id="ue5-performance-optimization"></a>
## ue5-performance-optimization（09-10，自建专项）

- **需求/候选**：UE5.6 测量→定位→优化→复测；当时 unreal engine performance optimization / game performance profiling 检索无专项，选最近邻 [aas unreal-engine-cpp-pro](https://github.com/sickn33/agentic-awesome-skills/tree/main/skills/unreal-engine-cpp-pro)（120 行）比较。
- **决定**：保留性能专项、剖析工具箱和实现模式两份 reference。相邻上游是通用 C++/UObject 指南，无法替代性能排查流程。
- **证据/边界**：静态总分 0.81/0.68（质量 0.97/0.84，结构 0.58/0.45）；strict 通过，历史启发式 11/12，“Unity 性能优化”是假阳性。没有双方同场景帧时间改善数据。
- **后续**：出现真正同类上游再对比；不要为相邻候选的目录分数增加无用资源。

<a id="coding-discipline"></a>
## coding-discipline（09-14，四条准则适配）

- **原始源**：用户指定 [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)；当时通过 [aas 的 andrej-karpathy](https://github.com/sickn33/agentic-awesome-skills/tree/main/skills/andrej-karpathy) 同源副本比较。09-23 已把原始源作为 karpathy 加入索引。
- **许可记录**：09-14 导入记录记为 MIT；09-23 来源核对说明仓库无独立 LICENSE、SKILL.md 声明 MIT。保留该区别，不扩写授权结论。
- **决定**：四条准则改为反例→正例；保留轻任务的权衡提示和一句原则加要点列表，补本地字段与触发用例。
- **证据/边界**：总分 0.76/0.73；差值来自 metadata_complete 1.00/0.75，其余大致持平。strict 通过，原对比未记触发通过率或真实任务双跑，不能补造。

<a id="ue-editor-lifecycle"></a>
## ue-editor-lifecycle（09-15 自建，09-23 补对比）

- **需求/候选**：检查编辑器实例→源码构建配置→构建→异步启动；09-17 归入 development。09-23 在 5 源 2188 条快照中检索 unreal editor / UnrealEditor / LaunchUE / PIE / rebuild / dll / frozen / hang / editor crash / ue5 均无主题命中，游戏分类 18 条无专项；以同上 unreal-engine-cpp-pro 作最近邻。
- **决定**：保留自建操作流程，相邻 C++ 指南无直接可吸收的生命周期步骤。150 行单文件无需为结构分强拆 references。
- **证据/边界**：总分 0.76/0.72（质量 0.97/0.84、结构 0.45/0.53）；来源审计记载历史 CLI 10/10、precision/recall 100%，未在本次重跑。静态比较不等于任务效果胜负。
- **后续**：出现真正同类上游时复评；该记录补齐的是入库流程证据。
