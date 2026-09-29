# skill-creator 开发目录

本目录是 skill-creator 技能的**开发工作区**（位于 `losemymind/Personal-AI-Tools` 仓库内）。真正的技能本体只存放一处：

```
skill-creator/                     ← 开发工作区（本目录）
├── AGENTS.md                      ← dev 角色守则：成品演进维护者（不随成品分发）
├── README.md                      ← 本文件：布局与开发指引
├── INSTALL.md                     ← 安装手册：把成品 skills/skill-creator/ 装到各客户端（不随成品分发）
├── tests/                         ← dev-only：pytest 回归（针对 skills/skill-creator 的脚本运行）
└── skills/
    └── skill-creator/             ← 成品目录 = 技能唯一源（编辑就在此处；随仓库提交分发）
```

## 成品即源，不复制

`skills/skill-creator/` 是技能（SKILL.md 方法论 + scripts/ + references/ + …）的**唯一存放处**，也是被安装、被 LLM 客户端调用的形态。开发时直接编辑该目录下的文件；**本工作区根目录不保留任何技能文件的副本**——没有「dev 源 + 拷贝」两层，也就没有重合与漂移问题。

## 自包含硬约束

成品 `skills/skill-creator/` 必须**不依赖上层任何文件或工具**：
- 内部引用（`scripts/`、`references/` 等）一律以成品目录自身为根书写。
- 不得引用本工作区的 `INSTALL.md`、`tests/`、`README.md`（那是 dev-only，不进成品）。
- 由成品 `skill_validate.py --strict --dir skills/skill-creator` 自检把关（引用悬空/指向不存在的路径即失败）。
- dev-only `tests/test_product_self_containment.py` 补 SKILL.md 之外的覆盖：扫成品**全 md**（fenced 豁免；跳过 `examples/`、`evolutions/`）的 dev-only/悬空引用，并断言成品根无 `AGENTS.md`/`INSTALL.md`。

## 常用命令

在**本工作区根**（`skill-creator/`，本文件所在目录）执行：

```bash
# 回归（发布/提交前必跑）
python -m pytest tests/ -q

# 成品 strict 自检：frontmatter/章节/安全护栏 + 引用不悬空
python skills/skill-creator/scripts/skill_validate.py --strict --dir skills/skill-creator
```

## 来源与沿革

本技能（成品 `skills/skill-creator/`）参考并融合了以下三个 skill-creator 实现：

- **[anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator)**（`skills/skill-creator/`，Anthropic 官方；与 `anthropics/claude-plugins-official` 的插件版同 blob sha，以其为官方源）：方法论主体与量化评测工具链移植来源（基线双跑/子代理编排、`skill_benchmark.py` / `skill_eval.py` / `skill_optimize.py` / `skill_utils.py` 头部与 `references/benchmark-schema.md` 标注移植自其 `scripts/` / `agents/` / `references/`）。
- **[ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills/tree/master/skill-creator)**（`skill-creator/`，Apache-2.0）：官方 Anthropic skill-creator 在流行 awesome-list 中的公开分发副本（内容同官方主线：`SKILL.md` + `scripts/`），作为参考入口，与方法论源同源。
- **[antongulin/opencode-skill-creator](https://github.com/antongulin/opencode-skill-creator)**（Apache-2.0；Anthropic 官方版的开源 opencode 移植）：贡献描述优化闭环增量（高分描述作 few-shot 先例 + 触发失败分类）。

调研过的其余 skill-creator 实现（OpenAI Codex 官方内置、openai/skills `.system`、vercel-labs/json-render、SkillForge、qiaomu-meta-skill、fskill-creator、skill-forge、claude-skills-cli 等）经评估后**未作为采纳来源**（或与上述同源、或与其方法论重叠、或非方法论实现），不在融合名单内。

另有两类非「skill-creator 方法论」依赖保留其真实来源标注（不在收敛范围）：
- 成品「先查后建」的**上游技能库索引**来自 [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)（`aas`）、[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)（`addy`），以及 [anthropics/skills](https://github.com/anthropics/skills)（`anthropics`）、[ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)（`composiohq`）、[Zhang-Henry/CoEvoSkills](https://github.com/Zhang-Henry/CoEvoSkills)（`coevoskills`，稀疏 API 取数 `meta_skills/`）、[mattpocock/skills](https://github.com/mattpocock/skills)（`mattpocock`，两层嵌套 `skills/<category>/<name>/`）、[multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills)（`karpathy`，`karpathy-guidelines`）。
- 成品 `references/` 若干文档头部与 `skill_validate.py` 标注「基于 agentic-awesome-skills 适配」——代码级真实出处，保留。

具体吸收点与对比择优记录见成品 `references/` 文档头与 `evolutions/`。

## 演进记录与上下文压缩（2026-09-29）

成品 `evolutions/` 已将 49 份日期记录和原 README 合并为 8 文件：一个阅读入口、六个主题摘要、一份旧记录映射。来源、决策、关键验证与未解决事项保留；重复审计过程、过时版本流水和已被替代的规则归并。

| 历史主题 | 当前证据入口（成品内） |
|---|---|
| 09-03 写作纪律、09-04 编排、09-09 描述规范、09-10 AI 评审、09-17 CoEvo 取舍 | [methodology](skills/skill-creator/evolutions/methodology.md) |
| 量化工具、真机信号/隔离、指标契约、独立最终测试 | [evaluation](skills/skill-creator/evolutions/evaluation.md) |
| 多轮验证器审计、安全扫描与结构评分 | [validation](skills/skill-creator/evolutions/validation.md) |
| 字段精简、白名单、安装、自包含与命名 | [distribution](skills/skill-creator/evolutions/distribution.md) |
| 09-10 四源、09-17 CoEvo、09-23 mattpocock/karpathy、09-29 检索与逐源状态 | [indexing](skills/skill-creator/evolutions/indexing.md) |
| 七个入库技能的导入/比较依据 | [library-decisions](skills/skill-creator/evolutions/library-decisions.md) |

按成品 `evolutions/README.md` 的问题路由读取；查原文件名时用 `evolutions/record-map.md`。后续同主题直接更新摘要并标日期，新事件可先独立记账再合并。来源台账、审计、当前文档与测试应同步改引用，不能把缺失原文解释为免除证据要求。

## 工具与子代理命名统一（2026-09-29）

十个命令行脚本统一为 `skill_<用途>.py`，索引采用 `skill_index_<动作>.py`；共享模块改为 `skill_utils.py`，定位模块 `_project_paths.py` 保持原名。完整迁移表见成品 `skills/skill-creator/README.md`，记录见 `skills/skill-creator/evolutions/distribution.md#naming`。外部命令和模块导入需切换新名称；现有参数、输出与退出语义保持不变。仓库调用、安装编排、CI 和独立性门禁已同步。

成品 agents/ 下四份角色指令统一为 skill_grader.md、skill_reviewer.md、skill_comparator.md、skill_analyzer.md，命名规则为 `skill_<角色>.md`。工作流、互相引用、工具注释和测试使用新路径，外部提示词按成品迁移表更新；角色职责与 JSON 产物契约保持不变。

## 提交说明

本目录改动技能后，跑通发布门，更新受影响文档与演进记录，并按仓库根 AGENTS.md 完成 HANDOFF 收尾；提交/推送须用户授权。

## 检索与评测可信度优化（2026-09-29）

- 检索改为名称精确命中 + BM25 字段加权排序，加入离线中英关键词扩展；「代码审查」能召回英文技能，未知词提示补英文检索。
- 触发报告增加覆盖率和不可用指标语义，以及可选失败退出门；CLI 安装副本实际使用候选 description。
- description 优化明确 train/validation 选优边界，支持独立最终测试集、CLI 开发/最终评测与确认状态；保留旧报告字段为兼容别名。
- 对比工具只做静态筛查，空资源目录不加分，采纳需同场景任务证据。
- 索引 v5 逐源记录成功/尝试时间、状态和已索引数据的 SHA-256；旧索引兼容读取，缺失时间标 unknown。本次保留原 7 源 2227 条快照，不重抓上游。

实现与上游对照见成品 `evolutions/evaluation.md`、`evolutions/indexing.md` 与 `evolutions/validation.md`。

## 第二轮证据完整性优化（2026-09-29）

用户批准六项优化并要求子代理分析审核。场景收集真实产物，触发用结构化证据，基准 v2 按任务配对并保留错误、未知成本、模型与来源；增加可选 --strict。索引 v6 固定远程提交并隔离下载目录，本地来源保守标记 unknown。入口按任务路由，三份新参考承载场景评测、触发优化与安装细节。

子代理独立分析、模块实现和交叉审核发现并修复流内错误/退出码不一致、混合模型回填、嵌套输出被跳过等边界。演进依据见 evaluation 的 evidence-integrity、indexing 的 pinned-revision、methodology 的 task-routing。仅使用本地假客户端和网络模拟做验证，未运行真实模型或修改随包索引数据。

## 真实模型测评（2026-09-29）

随后按用户要求运行 OpenCode 1.18.30 + deepseek/deepseek-flash：新触发集 12 条中 11 条可判定且符合标签、1 条运行超时；隔离后的两任务三组对照，当前/旧版/无目标技能断言通过 16/16、14/16、15/16。旧版在不完整配对上误报整体增益，当前版正确拒绝；小样本不足以证明普遍增益或稳定提速。

完整原始事件、真实产物、污染批次与重跑、独立评分、用量和复现命令见 [真实测评报告](../evaluation-runs/skill-creator/2026-09-29-live/REPORT.md)。评测资产仅 dev，成品仍为唯一源；旧版快照留在仓库外。产品总结归入 evolutions/evaluation 的 live-2026-09-29，不为本次测试改写描述或产品逻辑。
