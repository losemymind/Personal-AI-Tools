# 会话交接（2026-09-09）

本文件为本次会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**本会话新增的上下文与待办**。

## 仓库状态速览

- git：`main` 分支已有**首次提交**（涵盖本会话全部仓库结构文件），已推送 origin = `losemymind/Personal-AI-Tools`。`.opencode/` 已加入 `.gitignore`（安装测试副本不入库）；`codingflow.md`（个人 URL 记录）已随提交入库。
- 两工作区已**同构精简**（无 `build/`、成品无 `AGENTS.md`、`INSTALL.md` 均在各自工作区根、成品 `SKILL.md` 为唯一入口）。发布检查差异只在**成品自校验能力**：skill-creator 用成品 `validate_skills.py --strict` 自检；agent-creator 的 `validate_agents.py` 校验 AGENT.md 代理库（非自身成品），故自包含扫描落在 dev-only pytest。
- 能力库：根 `skills/` = 3 技能（development/code-review-skill、git/pr-summarizer、product-design/prd-generator），根 `agents/` = 3 顶层分类（academic/code-quality/ue-game-studio）。`CATALOG.md` 为静态快照，本会话未改动能力库内容，无需同步。

## 本会话已完成的改动

**1. 根 AGENTS.md（新建并演进）**
- 从无到有创建，覆盖：两工作区布局、能力库准入与审计、两条铁律（成品即源/成品自包含）、发布门因工作区而异、结构要点。当前为终态，与仓库一致。

**2. skill-creator 工作区精简（用户主导）**
- 删除 `skill-creator/build/`（build_release.py / check_self_containment.py）；发布检查改为 `pytest tests/ -q` + `validate_skills.py --strict --dir skills/skill-creator`。同步根 `README.md`、根 `AGENTS.md`、工作区 `README.md`。
- 保留 `skill-creator/tests/`（15 例：validate_skills 6 / search_index 4 / quant_eval 5）——是成品脚本的回归网，非运行时依赖，**用户确认保留**。
- 删除成品 `skills/skill-creator/AGENTS.md`（用户确认 SKILL.md 为唯一入口、不要上下文注入）。同步：成品 SKILL.md 结构树、成品 README 结构树、工作区根 INSTALL.md 的目录清单、根 AGENTS.md。
- 成品 `INSTALL.md` 移至 `skill-creator/INSTALL.md`（工作区根，不随成品分发）；内容改为「安装对象 = 成品目录」，并删去与 SKILL.md「资源路径基准」重复的段落。

**3. skill-creator 产品文档「只介绍自身」**
- 成品 README/SKILL.md 概述去掉「融合 5 个 skill-creator」的沿革表述；来源与沿革移到工作区 `skill-creator/README.md`。

**4. 上游调研与成品升级（0.5.0 → 0.6.0）**
- 调研了 11 个 skill-creator 实现（anthropics/skills、anthropics/claude-plugins-official、openai/codex 内置、openai/skills .system、vercel-labs/json-render、tripleyak/SkillForge、joeseesun/qiaomu-meta-skill、AGI-comming/functional-skill-creator、antongulin/opencode-skill-creator、AgriciDaniel/skill-forge、spences10/claude-skills-cli），结论与对比记录在工作区 `skill-creator/README.md`。
- 升级落点（成品 `skills/skill-creator/`）：
  - `SKILL.md`：references 一层深引用纪律 + grep 模式；description 唯一无条件加载触发面的硬约束（单行/无 `<>`/自足）；阶段 6 增 RED→GREEN 行为差门 + 人审闭环；阶段 7 增触发失败分类（假阴/假阳/run_error）+ gold-standard 先例；阶段 9 增发布纪律（evals 随技能、secret 扫描、隔离验证）；质量清单加「渐进披露/引用纪律」组。
  - `references/quality-bar.md`：7 项 → 8 项（新增第 8 项渐进披露与引用纪律）。
  - `references/skill-writing-guide.md` §6：description 硬约束 + 失败归因。
  - `scripts/validate_skills.py`：新增 description 尖括号/跨行 advisory（不升级为 error，未破坏库门禁）。
  - `evolutions/` 新增 4 条 2026-09-09 记录（human-review-ui-loop / description-and-ref-discipline / red-green-gate-and-release-discipline / gold-standards-description-memory）。
- 发布门全绿：pytest 15 例、成品 strict 自检、能力库 strict（3 技能）均通过。

**5. 来源收敛与归因统一（用户最后指令：只保留两个源）**
- 工作区 `skill-creator/README.md`：被采纳来源只列 **anthropics/skills** 与 **antongulin/opencode-skill-creator**；其余 9 个实现一行注明「已评估、未作为采纳来源」；`sickn33/agentic-awesome-skills`（索引源 aas）、`addyosmani/agent-skills`（索引源 addy）、references 文档头「基于 agentic-awesome-skills 适配」等**真实代码出处保留**。
- 成品 scripts 头部（utils/run_eval/run_loop/aggregate_benchmark）+ `benchmark-schema.md`：移植来源由 `claude-plugins-official` 统一为 `anthropics/skills`（两者同 blob sha，官方 sync from）。
- evolutions 2026-09-09 记录、SKILL.md 阶段 8 去掉了对 codex/json-render/SkillForge/qiaomu/agent-skill-creator 等外部点名。

**6. agent-creator 孪生对齐精简（本会话，用户决策）**
- 删除 `agent-creator/build/`（build_release.py / check_self_containment.py）；自包含扫描迁入 dev-only pytest（`tests/test_product_self_containment.py`：引用不悬空 + 无 dev-only 引用 + 无 AGENTS.md/INSTALL.md 残留布局断言）。发布检查 = `python -m pytest tests/ -q` 一个命令全含。
- 删除成品 `skills/agent-creator/AGENTS.md`（SKILL.md 为唯一入口、不要上下文注入）。
- 成品 `INSTALL.md` 移至工作区根 `agent-creator/INSTALL.md`（不随成品分发）；内容改为「安装对象 = 成品目录」，删除完整目录清单里的 AGENTS.md。
- 成品 SKILL.md：version 0.3.0 → 0.4.0；两处引用 `INSTALL.md` 改为自包含的「多客户端安装指引」段落（技能形态落点 skills/ 目录）；成品 README 结构树删 AGENTS.md/INSTALL.md、`使用` 步骤去 `INSTALL.md` 引用。
- 同步：工作区 `agent-creator/README.md`、根 `README.md`、根 `AGENTS.md`（布局图/发布命令/「布局分化」表述改为「同构精简」，自包含铁律去掉 build/）。
- 发布门全绿：agent-creator pytest 5 例（含 2 个成品自包含/布局断言）、skill-creator pytest 15 例、skill-creator 成品 strict、能力库 strict（agents 32 / skills 3）。

**7. skill-creator 工作区安装实测（本会话）**
- 按 `skill-creator/INSTALL.md` 装了**工作区 opencode** 端点：`.opencode/skills/skill-creator/`。三验证关卡全绿（成品 `--dir .` strict、索引 2 源 2132 条、关键资源就位）；副本与源文件集一致（139=139）。发现验证关卡会在安装副本内生成 `__pycache__/`，已在两份工作区 INSTALL.md 补「验证后清理缓存」说明。
- 待办风险：重启/新会话后 opencode 才会加载该技能；`.opencode/` 副本是本会话测试产物，**首次 git 提交时注意**是否纳入（建议加 `.gitignore` 排除或确认纳入）。

**8. 移除对已废弃外部宿主仓库的全部引用（本会话，用户指令「全部移除」）**
- 根 AGENTS.md / README.md、两工作区 README、「与宿主仓库的关系」节、能力库 skills/ & agents/ README、两份 CATALOG.md、两份审计文件：删去全部指向已废弃外部宿主仓库的字样与「随…迁移而来」「已废弃仓库 build_catalog」等源起表述；审计文件里「最近迁移提交」引用删除；`docs/…AUDIT.md` 旧路径引用改指仓库根审计文件（含三处 evolutions 记录里的登记路径）。
- 保留泛化词「宿主/个人工作流」（指向任意 LLM 客户端等使用环境的通用语义）与真实外部数据来源标注（UEGameStudio 本地仓库、anthropics、sickn33 等，属审计数据来源）。
- `.opencode/skills/skill-creator/` 测试副本同步源文件改动。

**9. 审计文件随能力库目录存放 + 创建器排除审计（本会话，用户指令）**
- 移动：`AGENTS-AUDIT.md` → `agents/AGENTS-AUDIT.md`、`SKILLS-AUDIT.md` → `skills/SKILLS-AUDIT.md`（与各自 CATALOG.md 同目录存放）。
- `validate_agents.py` 排除名单加 `agents-audit.md`（否则 `--strict --dir agents` 会把审计文件当代理候选扫描而失败；skills 侧验证器只扫含 SKILL.md 的目录，无需改动）。
- 根 AGENTS.md：审计登记/唯一记录入口路径改指库内新位置，新增「创建器排除在审计之外」条目。
- 两份审计文件：标题随目录（`agents/ — 代理审计` / `skills/ — 技能审计`），用途补「范围：只审计能力库条目；创建器是工具、排除在审计之外」，互为镜像引用改为 `agents/AGENTS-AUDIT.md` ↔ `skills/SKILLS-AUDIT.md`。
- 三处 evolutions 记录 + `.opencode/` 镜像的审计登记路径改指新位置。

**10. 两创建器完整性审计（本会话，用户指令）**
- 双向检查：引用→文件（无悬空）、文件→被引用/调用（无孤立）。方式：文件树盘点 + 逐脚本引用分布 + import 链核对 + 全脚本 `--help` 冒烟 + compileall + 全发布门。
- 结论与修复：
  - 所有脚本均被文档（SKILL/README/references）+ import 链 + tests 覆盖：skill（11 脚本，utils←run_eval/run_loop、_project_paths←validate_skills、run_trigger_tests←run_eval、run_eval←run_loop）、agent（6 脚本）；全部 `--help` 可启动。
  - references/templates/agents/indexes 全部被 SKILL/README/脚本消费；evolutions 按集合归档惯例（入口 evolutions/README）。
  - **skill 侧 `examples/README.md` 原本孤立**（无外部点名）→ SKILL.md 结构树与阶段 3、成品 README 结构树补齐入口（「样本入口：来源/许可/清单/学习要点」）。
  - **skill 侧 references 内部互链违反自身「references 只从 SKILL.md 一层深引用」硬规则**（skill-anatomy/skill-template/quality-bar 共 5 处 `references/skill-writing-guide.md`/`references/skill-template.md` 引用）→ 改为经 `SKILL.md`「读取规则」导读的文字指向，消除 refs→refs 文件路径引用。
  - agent 侧同款 references 互链（agent-anatomy→agent-template 一处）保留：agent SKILL 未声明「references 不互链」纪律，属合法交叉引用（如需与 skill 对齐可后续移植纪律）。
  - evolutions 历史记录文件按集合归档惯例豁免逐个点名（发布门亦跳过）；examples/ 内 systematic-debugging 的 CREATION-LOG/test-*.md、loki-mode 的 COMPETITIVE-ANALYSIS/take-screenshots.js 是上游整目录样本自带、验证豁免，保留（非本仓库功能）。
- 同步 `.opencode/skills/skill-creator/` 测试副本 5 个改动文件。
- 门禁全绿：skill pytest 15、agent pytest 6、成品 strict（skill 自检 + 能力库 agents 32/skills 3）全通过。

**11. skill-creator 工作区 AGENTS.md（本会话，用户指令「先定方案再实施」）**
- 新建 `skill-creator/AGENTS.md`：dev-only **角色守则**——把在该工作区运行的代理塑造成「skill-creator 成品演进维护者」（负责 `skills/skill-creator/` 的不断完善与进化）。内容：角色与边界（含不负责项）/ 演进闭环 SOP 8 步（证据→诊断分层→上游对比→方案→实施→验证门→evolutions 记录→版本→汇报）/ 硬约束 7 条（成品即源、自包含、SKILL.md 唯一入口、引用纪律、渐进披露、写作规范、验证优先）/ 质量自检清单 / 命令速查 / 何时问用户。
- 与已删除的「成品内 AGENTS.md」无关：本文件在工作区根、不随成品分发；成品内文档不得引用它（已核对无悬空）。
- 同步：根 `AGENTS.md` 布局节补工作区 AGENTS.md 定位说明；根 `README.md` 结构树补 `AGENTS.md` 条目；工作区 `README.md` 布局树补 `AGENTS.md`。
- 门禁不受影响（dev-only，成品未改）：skill pytest 15、成品 strict 全绿。
- 注意：opencode 会在 skill-creator/ 下工作时自动加载该 AGENTS.md（按 cwd 就近生效）；agent-creator 无此守则，仍是纯 dev 布局。

**12. 根 AGENTS.md 铁律 3「提交/推送必先收尾交接」（本会话，用户指令）+ 首次提交收尾**
- 根 `AGENTS.md`：标题「两条铁律」→「三条铁律」，新增铁律 3——git 提交/推送前必须先完成收尾（发布门全绿 + 同步受影响文档 README/审计/CATALOG/evolutions/版本号）→ 编写或更新新会话交接文件（仓库根 `HANDOFF.md`）→ 向用户输出可点击复制的新会话交接提示（独立代码块，如「读取 HANDOFF.md 交接并继续本仓库工作」）；未完成不得提交/推送。§命令段末加交叉引用。
- 首次提交范围（用户确认）：全部仓库结构文件 + `codingflow.md` 入库；`.opencode/`（本会话 skill-creator 安装测试副本）加入 `.gitignore` 排除。
- 发布门全绿后执行首次提交并推送 origin。

## 已知待办 / 潜在风险（给下一会话）

1. **升级中「记为纪律、未实现为工具」的项**（对应 evolutions 记录的「待真实场景验证后再升级为脚本」）：
   - 人审 UI 环（eval-viewer 静态 HTML viewer + eval_review.html 触发集审阅）——目前只在 SKILL.md 阶段 6/7 写了纪律，未移植官方 HTML/脚本。
   - gold-standards 独立记忆库——当前以 run_loop 上一轮胜出描述当先例，未做独立 gold_store CLI。
   - `.skill` 打包（package_skill.py）——未做。
   - skill-forge 的 Tier 分级模板 / 加权健康分——评估过、用户未确认采纳。
2. **能力库校验建议用绝对路径**：本会话发现 `validate_skills.py --dir ../../skills`（相对路径）从工作区根跑会报「Checked 0 skills」，用绝对路径 `--dir E:\...\skills` 正常（3 技能）。原因未深究，别被相对路径的空结果误导。
3. **能力库 / 审计一致性**：根 AGENTS.md 称 agents/ = 32 代理（academic×5/code-quality×2/ue-game-studio×25），与审计文件登记一致；若后续增删代理/技能，须按 AGENTS.md §能力库规则同步 `agents/AGENTS-AUDIT.md`/`skills/SKILLS-AUDIT.md` 与两份 `CATALOG.md`。
4. **agent-creator 成品已升 0.4.0**（删 AGENTS.md、INSTALL.md 移出、SKILL.md 唯一入口）；宿主/客户端若在旧版上按 AGENTS.md 或成品内 INSTALL.md 引用，需按新形态更新路径。
5. **agent-creator 无工作区 AGENTS.md 守则**：skill-creator 有（成品演进维护者）；agent-creator 仍是纯 dev 布局。若用户想让孪生同构，可在 `agent-creator/` 补同款角色守则（动前先读 `agent-creator/README.md` 与 skill-creator 版作模板）。
6. **提交纪律**：本仓库所有 git 提交/推送前，必先跑发布门全绿 + 更新 `HANDOFF.md` + 输出可点击复制的新会话交接提示（根 AGENTS.md §三条铁律 3）。

## 验证命令备忘

```bash
# agent-creator（在 agent-creator/ 根）——发布门 = 一个 pytest 命令全含
python -m pytest tests/ -q        # 回归 + 成品自包含自检（引用不悬空、无 AGENTS.md/INSTALL.md 残留）

# skill-creator（在 skill-creator/ 根）
python -m pytest tests/ -q
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator
python skills/skill-creator/scripts/validate_skills.py --strict --dir E:\GitHub\Personal-AI-Tools\skills

# 能力库（仓库根）
python agent-creator/skills/agent-creator/scripts/validate_agents.py --strict --dir agents
python skill-creator/skills/skill-creator/scripts/validate_skills.py --strict --dir skills
```
