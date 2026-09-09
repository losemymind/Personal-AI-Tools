# 会话交接（2026-09-09）

本文件为本次会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**本会话新增的上下文与待办**。

## 仓库状态速览

- git：`main` 分支已有两次提交，均已推送 origin = `losemymind/Personal-AI-Tools`。首次 `6824c79`（仓库结构）+ 本会话收尾提交（改动 13–20 与 CATALOG 生成器等，见下）。`.opencode/` 已加入 `.gitignore`（安装测试副本不入库）；`codingflow.md`（个人 URL 记录）已随首次提交入库。
- 根 `opencode.json`（已提交）：项目级 opencode 配置，`instructions` 显式注册三份 `AGENTS.md`（根 / skill-creator / agent-creator）——保证任意 cwd 下会话都加载全部角色守则（不依赖 opencode 按 cwd 就近自动发现）。不入 `.gitignore`，随仓库分发。
- 两工作区已**同构精简**（无 `build/`、成品无 `AGENTS.md`、`INSTALL.md` 均在各自工作区根、成品 `SKILL.md` 为唯一入口）。发布检查差异只在**成品自校验能力**：skill-creator 用成品 `validate_skills.py --strict` 自检；agent-creator 的 `validate_agents.py` 校验 AGENT.md 代理库（非自身成品），故自包含扫描落在 dev-only pytest。两工作区根均已有 dev-only `AGENTS.md` **角色守则**（成品演进维护者；agent-creator 版为本会话补齐，见改动 13）。
- 能力库：根 `skills/` = 3 技能（development/code-review-skill、git/pr-summarizer、product-design/prd-generator），根 `agents/` = 3 顶层分类（academic/code-quality/ue-game-studio）。`CATALOG.md` 由根 `tools/scripts/build_catalog.py` 自动生成（见改动 18）。

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

**13. agent-creator 工作区 AGENTS.md（本会话，用户指令「补工作区 AGENTS.md」）**
- 新建 `agent-creator/AGENTS.md`：dev-only **角色守则**——skill-creator 版的同构镜像，把在该工作区运行的代理塑造成「agent-creator 成品演进维护者」。内容结构同 skill-creator 版（角色与边界 / 演进闭环 SOP 8 步 / 硬约束 / 质量自检 / 命令速查 / 何时问用户），但按 agent 侧事实改写：产品部件列 agent-template/anatomy/quality-bar/index/comparison + create/validate/compare/search/build 脚本；发布门 = `pytest tests/ -q`（无成品 strict，自包含在 pytest 内）；命令速查含库校验与索引完整性；引用纪律标注 agent 版现状（references 交叉引用合法、未声明互不互链，如需对齐孪生纪律属方法论升级）；Step 4 注明当前无 `.opencode/skills/agent-creator/` 测试副本（仅 skill-creator 有）。
- 同步：根 `AGENTS.md` 布局树两行与「工作区根」清单补 `AGENTS.md`、定位段改为「两工作区均已建…前者为后者的同构镜像」；根 `README.md` 结构树 agent-creator 块补 `AGENTS.md`、同构句改为「成品内 AGENTS.md 均已删除、成品内 INSTALL.md 均已移至工作区根（工作区根各有 dev-only AGENTS.md 角色守则 + INSTALL.md）」；工作区 `agent-creator/README.md` 布局树补 `AGENTS.md`。
- 门禁不受影响（dev-only，成品未改）：agent pytest 6、skill pytest 15、成品 strict（skill 自检 + 库 agents 32/skills 3）全绿。
- 至此上一版 HANDOFF「已知待办」中的「agent-creator 无工作区 AGENTS.md 守则」已落地：两工作区同为「成品演进维护者」角色守则，同构补全（该待办已从清单移除）。
- 注意：opencode 会在 agent-creator/ 下工作时自动加载该 AGENTS.md（按 cwd 就近生效），与 skill-creator 侧一致。

**14. 根 opencode.json 注册三份 AGENTS.md（本会话，用户指令「使用 instructions 加入工作区 opencode」）**
- 新建仓库根 `opencode.json`（用户确认入库，非 `.opencode/` 或全局）：`$schema` + `instructions: ["AGENTS.md", "skill-creator/AGENTS.md", "agent-creator/AGENTS.md"]`。相对路径自配置所在目录（仓库根）解析，三份均存在。
- 效果：仓库内任意 cwd 的 opencode 会话都无条件加载全部三份守则（根 AGENTS.md 本就按 cwd 自动发现；两工作区角色守则此前仅在对应子目录工作时才加载）。注意两工作区 AGENTS.md 现为 always-on，且各自声明「只负责本工作区成品、不负责根能力库」，多份同时在场时以任务所处 cwd/目录为准。
- 配置改动需**重启 opencode 生效**（本会话运行时已加载的配置不含该指令）。
- 同步：`HANDOFF.md` 仓库状态速览补该文件说明。新文件尚未 git add/提交，属待提交改动。

**15. validate_*.py 目录守卫修复（本会话，用户指令「修复两脚本守卫」）**
- 背景：巡检确认原 HANDOFF 待办 2 的根因 = 两层——(a) `--dir ../../skills` 本身就是错误相对路径（skill-creator 根到仓库 skills 应为 `../skills`）；(b) 更本质的缺陷：两验证器对**不存在的目录**静默通过（`os.walk` 空 → `Checked 0` → exit 0「✨ 全绿」），传错目录会让发布门假绿。
- 修改（同构孪生，两侧同步）：
  - `skill-creator/skills/skill-creator/scripts/validate_skills.py` `collect_validation_results`：`os.path.abspath` 后加 `isdir` 守卫，缺失即返回含 ❌ `Scan directory does not exist: <abs>` 的结果（→ exit 1）。
  - `agent-creator/skills/agent-creator/scripts/validate_agents.py` `collect_validation_results`：同款守卫（并把 `agents_dir` abs 化，显示路径与解析一致）。
  - 各补 pytest：`test_nonexistent_dir_fails`（skill tests 现 16 例、agent tests 现 7 例），断言 returncode==1、报错文案在、`All … passed` 不出现。
- 版本 bump：skill-creator 0.6.0 → **0.6.1**、agent-creator 0.4.0 → **0.4.1**（patch，验证器行为修复）。
- 实测：`--dir ../../skills` 现报 `❌ Scan directory does not exist: E:\GitHub\skills` 且 exit=1；`--dir ../skills` 正常 3 技能全绿。
- `.opencode/skills/skill-creator/` 测试副本已同步（validate_skills.py + SKILL.md version 0.6.1）。
- 门禁全绿：skill pytest 16、agent pytest 7、skill 成品 strict、能力库 strict（agents 32 / skills 3）。一致性巡检另确认：能力库目录 = CATALOG = 审计登记全部一致，frontmatter 字段（mode/version/maturity/category/risk/source/date_added）与 CATALOG 表一致；prd-generator `category: product` vs 目录 `product-design/` 属规则 4 的功能目录差异，非缺陷。

**16. prd-generator 合规闭环（本会话，用户指令「补 prd-generator 合规闭环」）**
- 背景：`skills/SKILLS-AUDIT.md` 中 prd-generator 曾标 ⚠️「待补 evolutions 记录」，合规闭环未完成。本任务补全。
- 证据与对比：检索 skill-creator 成品自带上游索引（aas/addy 2132 条）`prd`/`requirements`/`spec` 关键词 **0 命中**（A 空，无择优竞争者）；抓取上游 `snarktank/ralph`（MIT，已核 LICENSE）`skills/prd/SKILL.md` 原文比对。
- 新增 `skill-creator/skills/skill-creator/evolutions/2026-09-09-import-prd-generator.md`：记录「本地 A 空 → 上游 B 直接导入（方法论吸收 + 中文产品化）」，含适配要点（frontmatter 补 category/risk/source/version/author/tools、补何时使用/示例/限制/安全章节、PRD 输出模板章节名保留英文、description 双语触发词）与 4 条学习点（单文件方法论型 vs 整目录语料型导入策略分流；叙述汉化但产物模板保上游结构）。
- `skills/SKILLS-AUDIT.md` 同步：prd-generator ⚠️→✅（摘要「经 skill-creator 生成流程」2✅/1⚠️ → 3✅；审计结论第 3 条转合规；§2 数据来源表增「远程仓库（方法论导入，MIT）」行；§3 技能清单行 ⚠️→✅；evaluations 指针补 `2026-09-09-import-prd-generator.md`）。
- 无成品版本 bump（SKILL.md/scripts 未改，仅 evolutions 记录 + 库审计）；`.opencode/skills/skill-creator/evolutions/` 测试副本已同步。
- 门禁全绿：skill pytest 16、skill 成品 strict、能力库 skills strict（3）全通过。

**17. agent-creator 成品升级 0.4.1 → 0.5.0（本会话，用户指令「全做」对标孪生 skill-creator 0.6 纪律）**
- 升级内容（A/B/C/D/E 全套）：
  - **A 引用纪律**：SKILL.md「渐进式披露」节增 references 引用纪律硬规则（一层深、refs 不互链成图、>100 行目录、超大文件 grep）；`references/agent-anatomy.md` refs→refs（→agent-template）改经 SKILL.md 导读；同文件修复悬空的 `install_agent.py` 引用（脚本从未存在）→ 改指 SKILL.md「多客户端安装指引」。
  - **B description 触发纪律**：SKILL.md 增「description 触发面（硬约束）」段（单行/≤200/无 `<>`/不写步骤摘要）；阶段 6 增触发失败分类（假阴/假阳/run_error，改前先归因）；质量清单「元数据」组补单行/无占位符；`agent-template.md` 字段说明与 `agent-quality-bar.md` 元数据项同步补约束。
  - **C 发布纪律**：SKILL.md 新增「入库与发布纪律」节（secret 扫描/隔离安装实测/版本化原子补丁）。
  - **D 验证器**：`validate_agents.py` description 加 `<>`/跨行 advisory（不失败，镜像 skill，不改变库门禁语义）；补 pytest 2 例 → agent tests 7→9。
  - **E 质量条**：`agent-quality-bar.md` 5→6 项（新增「渐进披露与引用纪律」）；SKILL.md 质量清单增「渐进披露与引用组织」组。
- 版本：SKILL.md frontmatter 0.4.1 → **0.5.0**（minor）。evolutions 新增 `2026-09-09-adopt-ref-description-release-discipline.md`（对齐孪生记录）。
- agent-creator 无 `.opencode` 测试副本（仅 skill-creator 有），无需同步。
- 门禁全绿：agent pytest 9（含自包含/布局）、能力库 agents strict 32、skill pytest 16、skill 成品 strict、能力库 skills strict 3；库 description 无 advisory 噪音。

**18. 移植 CATALOG 生成器（本会话，用户指令「CATALOG 源自 personal-workflow，参照其完成实现」）**
- 来源：`E:\GitHub\personal-workflow\tools\scripts\build_catalog.py`（本仓库 CATALOG.md 实际移植自该生成器的产物；此前迁移/精简时未把生成器一起带回，文档长期以「本仓库无目录生成器/手工同步」记之，用户本次指出并指示参照实现）。
- 新建根 `tools/scripts/build_catalog.py`（同源布局 tools/scripts/）：扫描 skills/SKILL.md + agents/AGENT.md frontmatter → 渲染两份 CATALOG.md；`--check`（过期即 exit 1）/`--verbose`/`--root`。两处适配本仓库约定：install 列改为「复制 `<库>/<name>` → 客户端 库/ 目录」（本仓库无 install_*.py launcher）；docstring 标注移植来源。新增「库目录不存在即 ❌ + exit 1」守卫（与 validate_*.py 守卫同纪律，含 `--root` 传错场景）。
- 重生成两份 CATALOG：正文与既有手写条目**逐字节一致**（3 技能 + 32 代理零漂移），仅文件头由「静态快照/手工同步」改为「自动生成/禁止手改/--check 发布门」。
- 同步表述（去除「无目录生成器/静态快照/手工同步」）：根 `AGENTS.md`（§能力库 bullet + 命令块加生成器 2 行 + 结尾刷新 CATALOG 表述）、`agents/README.md`（maturity 注释/CATALOG 树注释/§能力目录/回馈流程 step3）、`skills/README.md`（树注释/§能力目录/回馈流程 step3）。全仓扫描无残留旧表述（仅 HANDOFF 历史行已随本记录更新）。
- 门禁：`--check` exit 0；坏 `--root` exit 1。能力库校验无涉（未改能力内容）。后续改能力库 = 跑生成器刷新 + `--check` 把关。

**19. agent-creator 移植安装适配器 adapt_agent.py（本会话，用户指令「移植为 agent-creator 工具」）**
- 背景：用户问 personal-workflow 的 `agent_format.py` 是否也移植——它是该仓库 install_agent.py/update_agent.py 的 frontmatter 适配层（与 build_catalog 无依赖）。诊断：本仓库「安装=复制、无 launcher」，直接照搬会成孤儿；但 `agent-template.md` 整段描述的转换语义被推给**不存在的「宿主安装器」**（与上次清除的 install_agent.py 幽灵引用同源悬空），`agents/` 的 `tools:[...]` 规范形直接复制到 claude/opencode 可能无法加载。
- 决策（用户选）：移植为 agent-creator 成品工具——复制前转换器 CLI，而非照搬 install launcher 形态。
- 落点 `agent-creator/skills/agent-creator/scripts/adapt_agent.py`：输入规范 AGENT.md/目录 → `--client claude|opencode|codex|deepseek` → stdout/`--out` 输出目标客户端合法 AGENT.md；保留上游全部语义（opencode tools→permission 显式条目优先 + write/patch 折叠 edit；claude tools→Comma 串映射大写名 + model→alias；codex/deepseek YAML 校验后逐字节原样）+ 每端 post-check + fail loudly（exit 1 不产出）；docstring 标注移植来源。
- 接线：SKILL.md 阶段 7 改「先转换再放置」+ 多客户端安装指引 + FAQ 指向 adapt_agent.py；`references/agent-template.md` 三处「宿主安装器/安装器」改指 adapt_agent.py（悬空清除）；产品 README 脚本树补 adapt_agent.py 行 + 顺带修 quality-bar 注释 5→6（#17 漏改）；dev `agent-creator/AGENTS.md` scripts 列举 + adapt。
- 测试：agent pytest 9→16（新增 `tests/test_adapt_agent.py` 7 例：opencode 转换/显式权限胜出/write→edit 折叠/claude tools+model 映射/全无映射拒绝/codex 逐字节原样/缺路径失败/--out 写盘）。
- 版本：SKILL.md 0.5.0 → **0.6.0**（minor）。evolutions 新增 `2026-09-09-adopt-agent-format-tool.md`。
- 同步计数：`skill-creator/AGENTS.md` 命令速查 15→16 例、`agent-creator/AGENTS.md` 6→16 例（此前改动已漂移）。
- 门禁全绿：agent pytest 16、能力库 agents strict 32、skill pytest 16、skill 成品 strict、能力库 skills strict 3。agent-creator 无 .opencode 副本。

**20. 核心需求体检修复 A 全修（本会话，用户指令「检查缺陷与多余设计」→ 选 A 全修）**
- 体检结论（只读分析）：核心工具闭环健康；缺陷集中在周边断点与文档债；多余/负载（examples 103 文件、双 upstream.db 2.2MB、能力库 30 迁移垂直内容）供后续定夺未动。
- **A1 库安装指引接 adapt_agent**：`agents/README.md` 安装 bullet 改「先转换 frontmatter 再复制」+ 库内**两种形**说明（code-quality 2 = tools 数组规范形；academic+ue-game-studio 30 = opencode permission map 形含 color/temperature/lsp）；`tools/scripts/build_catalog.py` header 给 agents 增加「落地前转换」提示行（skill 不加）→ 重跑 `agents/CATALOG.md`（仅头多 1 行）；`agent-creator` 产品 README 使用步 5 补 `adapt_agent.py --client` 提示。
- **A2 evolutions 模板补齐**：两份 `evolutions/README.md` 从只定义 compare- 扩为三类表格（compare- 择优 / import- 上游导入 / adopt- 采纳升级，各配真实示例）+ import/adopt 记录要点。
- **A3 文档同步债扫描**：全仓 grep 计数/版本/幽灵工具名——skill 8 项、agent 6 项、10 阶段、0.6.x/0.5.0 引用均一致；无 install_/rollback_/uninstall_ 残留（除 evolutions 历史）；skill-creator/README.md:65 pytest 15 例属历史沿革保留。
- 门禁全绿：agent pytest 16、skill pytest 16、skill 成品 strict、能力库 strict（agents 32/skills 3）、CATALOG `--check` exit 0。

## 已知待办 / 潜在风险（给下一会话）

1. **升级中「记为纪律、未实现为工具」的项**（对应 evolutions 记录的「待真实场景验证后再升级为脚本」）：
   - 人审 UI 环（eval-viewer 静态 HTML viewer + eval_review.html 触发集审阅）——目前只在 SKILL.md 阶段 6/7 写了纪律，未移植官方 HTML/脚本。
   - gold-standards 独立记忆库——当前以 run_loop 上一轮胜出描述当先例，未做独立 gold_store CLI。
   - `.skill` 打包（package_skill.py）——未做。
   - skill-forge 的 Tier 分级模板 / 加权健康分——评估过、用户未确认采纳。
2. **能力库校验的「相对路径漏扫」已修复（本会话，见改动 15）**：`--dir` 指向不存在目录时两脚本现会打 ❌ 并 exit 1，不再静默 `Checked 0` 假绿。从 skill-creator 根校验能力库用 `../skills`（`../../skills` 会解析到 `E:\GitHub\skills` 不存在 → 现报错退出）。
3. **能力库 / 审计一致性**：根 AGENTS.md 称 agents/ = 32 代理（academic×5/code-quality×2/ue-game-studio×25），与审计文件登记一致；若后续增删代理/技能，须按 AGENTS.md §能力库规则同步 `agents/AGENTS-AUDIT.md`/`skills/SKILLS-AUDIT.md` 与两份 `CATALOG.md`。
4. **agent-creator 成品已升 0.6.0**（删 AGENTS.md、INSTALL.md 移出、SKILL.md 唯一入口；0.5.0 对齐孪生引用/description/发布纪律、0.6.0 新增 adapt_agent.py 安装适配器，见改动 17/19）；宿主/客户端若在旧版上按 AGENTS.md 或成品内 INSTALL.md 引用，需按新形态更新路径。
5. **已评估、用户明确「B 不需要修复」的项（勿再主动提出/改动）**：核心需求体检（改动 20）中判为「多余/负载」的 3 项维持现状——(a) skill-creator 成品 `examples/` 103 文件（含 react-best-practices 55 rules + loki-mode 40 文件整树拷贝，验证豁免、作学习样本）；(b) 两份 `indexes/upstream.db`（skill 1.7MB + agent 0.5MB）随成品提交；(c) 能力库 30 个 UE/academic 迁移垂直内容 + 逐条审计开销。后续会话别再据此提瘦身。
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
