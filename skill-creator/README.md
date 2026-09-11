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
- 由成品 `validate_skills.py --strict --dir skills/skill-creator` 自检把关（引用悬空/指向不存在的路径即失败）。
- dev-only `tests/test_product_self_containment.py` 补 SKILL.md 之外的覆盖：扫成品**全 md**（fenced 豁免；跳过 `examples/`、`evolutions/`）的 dev-only/悬空引用，并断言成品根无 `AGENTS.md`/`INSTALL.md`。

## 常用命令

在**本工作区根**（`E:\GitHub\Personal-AI-Tools\skill-creator`）执行：

```bash
# 回归（发布/提交前必跑）
python -m pytest tests/ -q

# 成品 strict 自检：frontmatter/章节/安全护栏 + 引用不悬空
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator
```

## 来源与沿革

本技能（成品 `skills/skill-creator/`）参考并融合了以下三个 skill-creator 实现：

- **[anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator)**（`skills/skill-creator/`，Anthropic 官方；与 `anthropics/claude-plugins-official` 的插件版同 blob sha，以其为官方源）：方法论主体与量化评测工具链移植来源（基线双跑/子代理编排、`aggregate_benchmark.py` / `run_eval.py` / `run_loop.py` / `utils.py` 头部与 `references/benchmark-schema.md` 标注移植自其 `scripts/` / `agents/` / `references/`）。
- **[ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills/tree/master/skill-creator)**（`skill-creator/`，Apache-2.0）：官方 Anthropic skill-creator 在流行 awesome-list 中的公开分发副本（内容同官方主线：`SKILL.md` + `scripts/`），作为参考入口，与方法论源同源。
- **[antongulin/opencode-skill-creator](https://github.com/antongulin/opencode-skill-creator)**（Apache-2.0；Anthropic 官方版的开源 opencode 移植）：贡献描述优化闭环增量（高分描述作 few-shot 先例 + 触发失败分类）。

调研过的其余 skill-creator 实现（OpenAI Codex 官方内置、openai/skills `.system`、vercel-labs/json-render、SkillForge、qiaomu-meta-skill、fskill-creator、skill-forge、claude-skills-cli 等）经评估后**未作为采纳来源**（或与上述同源、或与其方法论重叠、或非方法论实现），不在融合名单内。

另有两类非「skill-creator 方法论」依赖保留其真实来源标注（不在收敛范围）：
- 成品「先查后建」的**上游技能库索引**来自 [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)（`aas`）、[addyosmani/agent-skills](https://github.com/addyosmani/agent-skills)（`addy`），以及 [anthropics/skills](https://github.com/anthropics/skills)（`anthropics`）、[ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills)（`composiohq`）。
- 成品 `references/` 若干文档头部与 `validate_skills.py` 标注「基于 agentic-awesome-skills 适配」——代码级真实出处，保留。

具体吸收点与对比择优记录见成品 `references/` 文档头与 `evolutions/`。

## 上游对比与升级（2026-09-09）

以两个方法论源为准做了系统对比调研（仓库、目录、SKILL.md 全文实抓）：[anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator)（`skills/skill-creator/`，Anthropic 官方）与 [antongulin/opencode-skill-creator](https://github.com/antongulin/opencode-skill-creator)（其官方版的开源 opencode 移植）；ComposioHQ/awesome-claude-skills 的 `skill-creator/` 为官方方法论的分发副本，不作独立对比源。两者的方法论、脚本与我们的核心高度重叠，我们已属严格超集（量化评测/盲测/evolutions 是独有）。

**可吸收优点（已并入成品，见下方升级清单）**：
1. **结构化评审回流 → agent 评审闭环（无人工）**：把「需要评分和审核」的事务交给评审子代理（`agents/reviewer.md`）产出结构化 `review.json`（`pass`/`revise` + 可执行修复项），驱动 agent1↔agent2 自动迭代直到通过。
2. **description 即唯一触发面 + 硬约束**（anthropics/skills 写作规范 + antongulin）：`description` 是唯一门面、≤1024 字符、禁占位符，强化我们的 description 规范与校验。
3. **references 引用纪律量化**（anthropics/skills 渐进披露规范）：references 一层深链接、>100 行加目录、超大文件给 grep 模式——硬规则化渐进披露。
4. **基线行为门（RED→GREEN）+ evals 随技能发布**：无技能基线失败在前、写后带技能必须消除失败，否则技能不成立；`evals/`（triggers.json + scenarios + holdout）随技能入库、改动必回归。它是编排规范而非纯脚本，引入为流程与文件格式约定。
5. **发布纪律**：入库前 secret 扫描、隔离安装实测、PR/tag 后再放行，禁止直推默认分支——沉淀为本仓库的入库/发布纪律。
6. **gold-standard 先例注入 + 失败分类 taxonomy**（antongulin）：description 优化时把本次运行中 test 分最高的 description 当 few-shot 先例注入改进提示；触发失败分 false_negative/false_positive/run_error 并各配 remediation 模板。落地为 description 优化闭环增强（参考其机制，Python 化）。

**升级落地清单（成品 `skills/skill-creator/`）**：`evolutions/` 记录（description-and-ref-discipline / red-green-gate-and-release-discipline / gold-standards-description-precedent 三条 + 2026-09-10 `adopt-agent-review-loop`）；`SKILL.md` 扩 description 硬约束/引用纪律/RED→GREEN 判定、发布纪律与 description 先例注入闭环、**agent 评审闭环（阶段 6）**；`references/skill-writing-guide.md` 与 `quality-bar.md`（7→8 项）同步增强；stage7 补 eval 集审阅（改由评审子代理执行）、holdout 与失败分类纪律；`run_loop.py` 落地 gold-standard 先例注入；`validate_skills.py` 增 description advisory。验证器/评测脚本纯增量，pytest 全绿、成品 strict 自检、能力库 strict 校验均通过。

**2026-09-10 跟进（版本 0.7.0）**：评审改为 **agent 评审闭环（无人工）**——新增评审子代理 `agents/reviewer.md`，阶段 6 由 agent1↔agent2 自动迭代；阶段 7 查询集审阅改由评审子代理执行；阶段 8 `VERIFICATION.md` 降为可选留痕；`run_loop.py` 落地 gold-standard 先例注入。孪生 agent-creator 同步（0.7.0）。

**2026-09-11 跟进（版本 0.7.1）**：一轮创建器审计修复（不扩功能，仅纠缺陷/对齐文档）。成品侧：`scripts/package_skill.py` 补 `--out` 指向已存在文件的显式守卫（不再泄漏 traceback）；`evolutions/README.md` 记录类型表补全、去掉硬编码类数。孪生 agent-creator 同批修复（`compare_agents` 递归候选发现同时覆盖带 `AGENT.md` 的目录与上游扁平 `<division>/<name>.md`、`adapt_agent` opencode 权限放大、`create_agent` 工具名大小写归一、`build_agent_index` 过期文档、发布门死分支）。记录见两成品 `evolutions/2026-09-11-fix-*`。

**2026-09-11 跟进（版本 0.7.2）**：发布门加固。交叉引用门禁覆盖 `.template` 文件并改大小写不敏感（`tools/tests` + 两侧 `test_independence.py`）；skill 侧新增 dev-only `tests/test_product_self_containment.py`，与 agent 侧对等扫描成品**全 md** 的 dev-only/悬空引用（此前仅 `validate_skills.py` 校验 SKILL.md），并修正 `references/skill-anatomy.md` 一处悬空示意路径。记录见 `evolutions/2026-09-11-fix-independence-and-self-containment-gates.md`。

## 提交说明

本目录改动技能后，跑通上方命令即可 commit/push。
