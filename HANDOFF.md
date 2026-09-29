# 会话交接（2026-09-29 · 第 53 版）

本文件记录当前上下文与待办。仓库规则以根 AGENTS.md、目标工作区 AGENTS.md 与 README.md 为准。

## 仓库状态速览

- 分支 main；本轮起点为 `f68cfc8`。提交前已 fetch 确认本地与 origin/main 一致；本文件随本轮收尾提交保存，提交与推送的最终状态以 `git status -sb` 和 `git log -1` 为准。
- 上版交接的三项「未提交」已在历史中：`7a59c41` 补 ue-editor-lifecycle 对比、`0afa946` 新增 mattpocock/karpathy、`f68cfc8` 交接 v43。
- 本轮 skill-creator 五项优化、脚本与子代理命名统一、evolutions 上下文压缩及第二轮六项优化已完成。用户已明确授权提交和推送；本版交接用于该次提交，包含两创建器维护改动与全部真实测评归档。
- 随后完成真实 OpenCode 测评与子代理独立评分；证据在 `evaluation-runs/skill-creator/2026-09-29-live/REPORT.md`。保留运行错误、污染批次及重跑，未为测评修改产品逻辑/description。
- agent-creator 真实模型测评已完成，详细结果及失败边界见第 12 节和报告；该测评未修改成品。
- 能力库仍为 7 技能 / 7 代理；随包索引保持 7 源 2227 条，原数据时间 2026-09-23。本轮修改读取与构建行为，没有重抓上游或改动索引数据。
- 此前优化未改 agent-creator 运行逻辑；本次按用户要求完成其工具/角色命名迁移、文本独立性清理，并同步调用方。随后也将其 evolutions 合并为七份主题文件；两能力库条目未改，代理来源台账/审计仅更新证据导航；代理 CATALOG 仅随生成器更新适配命令名称。技能创建台账与审计的七项证据引用此前已迁移到压缩摘要锚点，来源与历史合规结论不变。

## 本轮已完成

### 1. 检索相关性与中英关键词

- `skill_index_search.py` 名称归一精确命中优先，随后用字段加权 FTS5 BM25 排序，平分按名称/来源/路径稳定排列。
- 常见中文关键词离线扩展为英文；英文限定词保留，含未知中文限定词时不做部分翻译。原文 LIKE 与英文 FTS 结果取并集。
- 实际索引中「代码审查」此前 0 命中，现在首条为 mattpocock 的 code-review；英文 code review 的同名技能此前第 12 位，现在第 1。

### 2. 触发评测错误语义

- `skill_eval.py` 新增 attempted/coverage；precision/recall 无分母为 null，文本显示 N/A。
- 保留默认报告模式的退出语义；新增 `--fail-on-error`、`--fail-on-mismatch`，可组合为质量门，报告先落盘再返回失败。
- CLI 评测把候选 description 写入临时安装副本，保证候选真实参与评测，源文件不变。报告记录客户端、模型、阈值和重复次数。

### 3. 描述优化与独立最终测试

- `skill_optimize.py` 的循环内 train/test 明确为 train/validation；重复开发查询被拒绝，validation 负责选优。
- 新增 `--eval-mode heuristic|cli`、`--final-eval-set`、`--final-mode`；独立最终集与开发集不得重叠，选优后只跑选中的描述一次，查询/结果不进入改写提示。
- 默认开发评分仍为 heuristic；最终模式默认 cli。未提供最终集时明确 not_run，不能声称真实触发已验证。
- schema_version=2；旧 test_passed/test_total 是 validation 兼容别名。confirmation 区分 not_run/proxy_only/dispatch_passed/structured_passed/failed/error；Claude 旧 approximate_passed 已由第二轮结构化检测替代。
- 改写或执行错误、最终测试失败返回 1 并保留报告；修复运行错误后再继续，不用错误驱动描述改写。

### 4. 对比评分边界

- `skill_compare.py` 空资源目录不加分；有效脚本要求非空文件与常见脚本扩展名。
- JSON/text 都明确为结构筛查，不直接输出采纳胜负。
- SKILL.md 与对比参考要求至少一个相同真实场景的双方产出证据；不具备运行条件则记录「待任务验证」。

### 5. 索引逐源状态（第一轮）

- 构建器升级为 v5，以 meta 的 source_status 键记录逐源 last_success/last_attempt/status/snapshot_sha256/error。
- 失败、空扫描保留旧行与上次成功时间/快照哈希；局部更新不刷新其他源。
- stats 展示逐源状态，包括尚无数据但更新失败的源。旧索引缺少时间时显示 unknown，不用全局 built_at 补造。
- snapshot_sha256 只标识已索引字段，不等于远端 Git SHA，也不覆盖未索引文件内容。

### 6. 工具命名统一

- 十个 CLI 入口统一为 skill 前缀：skill_create / skill_package / skill_validate / skill_compare / skill_eval / skill_optimize / skill_scenario / skill_benchmark / skill_index_build / skill_index_search，均为 .py 文件。
- 按用户补充，utils.py 改为 skill_utils.py；_project_paths.py 保持原名。共迁移 11 个脚本文件，旧路径不保留副本或转发入口。
- 同步模块导入、内部提示、当前文档、安装编排器、CI 及独立性门禁。参数、输出 schema、函数接口与退出语义保持迁移前行为。
- 完整旧新映射见 `skill-creator/skills/skill-creator/README.md`。演进摘要使用当前名称；旧文件名与上游样本名称保留作来源标识，旧命令要按映射换算。
- 安装器仍识别旧产物内的 validate_skills.py / search_index.py，避免旧包安装时漏掉自检；失败回滚覆盖新旧两种名称。

### 7. evolutions 上下文压缩

- 用户明确要求“类似上下文压缩”：保留来源、关键决策、证据、验证边界与未解决事项，精简合并重复过程。
- 压缩完成时，50 个 Markdown 文件（49 份日期记录 + README）→ 8 文件；Unicode 字符 101,579 → 25,325，减少 75.1%；行数 1,837 → 421。计数统一换行，非模型 token 计数；后续命名迁移已继续补充摘要，此处保留压缩时快照。
- 六个主题：methodology / evaluation / validation / distribution / indexing / library-decisions；README 按问题路由并汇总未解决项，record-map 保留全部 49 份旧记录到具体章节的映射。
- 已删除被合并的旧正文，未保留第二套副本或跳转壳。09-02—09-23 的 47 份已提交原文可从 f68cfc8 回溯；09-29 的两份原文此前未提交，其关键事实已归并，不能声称 Git 中有其旧全文。
- 明确替代关系：循环内 test 是 validation；结构分不证明任务增益；frontmatter 瘦身取代早期字段要求。保留不完整真机基准、HTML 候选、稀疏取数限制与静态扫描边界。
- 同步 SKILL.md、产品/工作区 README、根与工作区 AGENTS、references、安装文档沿革、技能台账/审计引用。该阶段未压缩 agent-creator；后续已完成，见第 11 节。
- 新增 4 项引用完整性回归：摘要链接/锚点、旧记录映射、技能账本证据、当前文档演进引用；原评审测试改为检查保留下来的评审决定，不依赖已删除的日期文件。

### 8. 子代理指令命名统一

- 按用户要求，成品 agents/ 下四份文件改为 skill_grader.md、skill_reviewer.md、skill_comparator.md、skill_analyzer.md；规则为 skill_<角色>.md，旧路径不保留副本。
- 同步 SKILL.md 工作流、角色间引用、基准工具注释、参考文档、根规则、产品/工作区 README、演进摘要与现有测试；完整迁移表见成品 README。
- 角色职责与 grading.json/review.json/comparison.json 契约不变；agent-creator 的 reviewer.md 属于另一独立成品，未改名。

### 9. 第二轮六项优化与子代理审核

用户批准上一轮分析的六项改进，并明确启用 subagent 分析和审核。本轮三名子代理分工：执行/触发实现、基准实现与交叉审核、索引/文档独立审核；主代理处理索引固定提交、文档路由与整合发布门。

- skill_scenario：支持 --input-dir / --output-dir；清理前收集真实产物到 outputs/artifacts 并写 artifacts.json（大小/哈希/来源）；失败与超时保留证据；拒绝非空 run 目录；过滤输入、配置、缓存、符号链接。
- skill_events：新增共享结构化事件模块，解析 Claude/OpenCode 工具、错误与指标。skill_eval 不再按 Claude 名称子串判触发，保存 skill_dispatch/target_read 证据；缺协议或流内错误为运行错误。Claude 最终确认改 structured_passed，OpenCode 为 dispatch_passed。
- skill_benchmark schema_version=2：保留全部已发现尝试；completed/error/incomplete 与覆盖率可见；按 eval_id+run_number 配对，缺失/失败/重复/已知模型条件不一致时 delta 不可用；未知成本 null、真实0保留，统计带 n；保留模型集合及指标来源。新增 --strict，先落报告再失败。
- skill_index_build v6：远程先解析完整 commit SHA，目录枚举、raw、archive 统一该 SHA；每次独立临时目录；source_status 新增 upstream_commit/source_ref/fetch_mode。失败保留旧版本，本地源标 local/null，旧索引显示 unknown。日常按源更新文档明确 --incremental；随包数据库未更新。
- SKILL.md 从 547 行/26,671 字符压到 148 行/5,620 字符，入口字符减少78.9%（非token计数）。新增 skill-evaluation / skill-trigger-optimization / skill-installation 三份参考；局部机械修改走短流程，行为改动才走相关评测。
- 子代理交叉审核复现并修复：rc=0但客户端流内报错、OpenCode错误被记为负例通过、多模型被请求模型覆盖、声明输出路径含缓存目录导致产物丢失。最终独立审核补齐confirmation schema与新来源文档。
- 新增 test_benchmark_integrity 22 项、test_execution_integrity 31 项、test_index_provenance 8 项；旧fixture改为同场景配对和自洽计数，并更新信号/mock/helper契约。合计新增61项。

### 10. 创建器命名统一与文本独立（09-29）

- 用户要求命名格式统一，同时两个创建器不得引用或描述彼此。脚本/模块各用 skill_ / agent_ 前缀，索引采用 <前缀>_index_<动作>，角色指令为 <前缀>_<角色>.md；各自的 _project_paths.py 仍为本地定位模块。
- agent 迁移8个文件：adapt_agent→agent_adapt、build_agent_index→agent_index_build、compare_agents→agent_compare、create_agent→agent_create、package_agent→agent_package、search_agent_index→agent_index_search、validate_agents→agent_validate、security_scan→agent_security；reviewer.md→agent_reviewer.md。无旧入口转发副本，CLI参数与运行逻辑不变。
- 两个完整工作区的维护文本均清理交叉说明：入口、references、evolutions、开发守则、README/INSTALL、测试注释。工作区中原硬编码另一创建器的扫描测试转由仓库tools层集中维护；各自隔离运行测试保留。内部真实借鉴史在 docs/creator-maintenance-history.md 保存，不伪造独立原创或删除外部来源。
- tools/tests/test_creators_independent.py覆盖完整工作区、双向新旧模块/角色/资源名、命名格式及AST导入；evolutions不再豁免。第三方6个样本目录与准确位置索引数据库例外，examples/README仍检查，任意examples目录或upstream.db名字不能绕过。
- 根安装器、CI、库维护文档与目录生成器切换agent新入口；安装器兼容外部旧包检查名称并补失败回滚用例。仓库级安装编排按产物类型复用打包器，不应与成品自身依赖关系混淆。
- 真实测评记录整体迁至 evaluation-runs/skill-creator/2026-09-29-live；原始事件/指标/冻结哈希/评分保持历史内容，仅导航与复现命令更新。51个交付产物哈希一致；两个索引数据库与HEAD一致。原始日志的旧绝对路径保留，不再作为当前工作区维护文本。
- 未改技能触发/评测逻辑，未重新调用模型；上一轮真实测评仍只是当时版本的证据。最终回归314/122/44，全量独立性与命名门17项；两库strict各7、成品strict1、目录和diff检查通过。仓库内两者安装测试副本均不存在。本次没有提交、推送或更改全局安装。

### 11. agent-creator 演进记录上下文压缩（09-29）

- 按用户要求，以当前工作区文本为输入，21 份日期记录加 README → 7 文件：README、methodology、validation、distribution、indexing、library-decisions、record-map。
- Unicode 字符 42,690 → 13,893，减少 67.5%；行数 737 → 255。统一换行后计数，非模型 token。保留来源、决定、关键失败证据、替代关系和未解决边界，删除重复过程及原正文，不留副本/跳转壳。
- 全部 21 个事件映射到有效章节；20 份旧记录在 f68cfc8 有已提交版本，但近期命名/文字改动未提交，不能称 Git 保存了压缩前逐字文本。09-29 命名记录此前也未提交，其决定及证据已归并。
- 明确替代：默认扫描改 CWD 且 0 命中失败；适配器白名单/permission 简写放权已修复，bool-map 旧路径仍为边界；代理记录字段已移出 frontmatter 并转由台账保存；默认输出 flat、目录库显式 dir；Codex/DeepSeek 仅文本透传，不承诺字节一致或原生代理加载。
- 同步入口、产品/工作区 README、开发守则、比较说明、根规则、代理台账/审计与安装工具沿革；既有评审回归改查主题中的决定。未修改工具逻辑、索引、客户端配置或原始真实测评证据。
- 本次验证：agent 全量 122 项、仓库独立性 17 项、既有相关演进引用回归 4 项通过；21 条映射完整、56 处内部链接/锚点可达，旧引用清理、目录时效与 diff 检查通过。独立子代理审核通过，无阻断或实质遗漏；仓库安装测试副本不存在，无需同步。其余全量回归为第 10 节的前次结果，本次未重复模型测评。

### 12. agent-creator 真实测评（09-29）

- 用户明确要求运行真实测评。证据在 `evaluation-runs/agent-creator/2026-09-29-live/REPORT.md`；运行前固定4份协议/场景文件、10个夹具文件与26个当前成品文件的哈希。合成输入、真实模型调用，客户端为 OpenCode 1.18.30，模型为 deepseek/deepseek-flash。
- 计划17个运行槽：8触发、2任务×当前/f68cfc8/无目标技能共6场景、3个生成代理下游调用。实际16次模型调用都有客户端SQLite模型证据；无目标技能组生成角色因color=amber在下游适配前置失败，未调用模型，保留1失败+6不可评估，不能按输入未变给行为分。
- 触发8/8完成且匹配4正4负，均无错误或超时；正例使用成功skill派发，精确read分支本批未命中。协议预先采用派发OR确切SKILL.md读取，不在事后改标签。
- 三组创建/修复均产出真实文件。创建固定断言当前10/10、旧版10/10、无目标技能8/10；修复分别10/10、10/10、7/10，综合为20/20、20/20、15/20。无目标技能组创建失败为颜色/规范章节；修复产物的permission.default被原生加载为普通键，继承全局allow仍在，格式post-check通过不等于权限正确。逐项评分与证据见REPORT和独立审核。
- 下游当前/旧版生成角色均原生加载并实际以release-evidence-auditor身份完成，各7/7；正确识别integration失败、security缺失、rollback未验证并保持BLOCKED，拒绝材料内写文件/直接批准的指令。实际输入/sentinel不变，无越界工具尝试；本次没有观察到相对旧版效果提升。
- 固定评分外观察：两组验证说明未经探测就声称环境无OpenCode；两组下游回复忽略release-notes标题的R17发布标识而称无版本/构建号；旧版创建记录行数未更新。这些作为待改进点保留，不事后追加评分标准。
- 独立子代理负责协议、触发、创建、修复和下游审核。产物以匿名标签分发但日志可推断组别，非严格盲评；下游非盲评。外层审核不计为生成器自行派发独立评审的成功。
- evidence-audit-v2通过，首份审计把CRLF/LF差异误报为native prompt变化，窄修换行比较后复核、首份报告原样保留。15条观察逐项核验，无全局旧创建器或跨组污染；同run隔离state内有一次cwd外临时复制，保存路径/工具ID/哈希，不隐瞒且不扩大B10判据扣分。
- 每次隔离用户/XDG目录与cwd，但不是OS沙箱；两阶段各并发2且时间重叠，不作稳定延迟比较。tokens取客户端累计step，费用未知。未改被测成品/索引/真实安装配置，未提交或推送。工作区README仅新增测评导航，成品保持冻结哈希。
- 收尾复核：40份冻结文件哈希一致、报告证据链接可达、仓库独立性17项测试通过、git diff --check通过；机器可读评分汇总保存在本批 attempt-1/summary.json。未重复无关全量回归。

## 文档与记录

### 真实测评补充（09-29）

- OpenCode 1.18.30 内置程序不在原 PATH，通过绝对路径调用；模型 deepseek/deepseek-flash，24 个正式运行的本地会话元数据一致，另 1 次连通探测。provider 凭据仅进子进程环境，不进评测记录。
- 触发：新冻结 12 查询；6 正派发、5 有效负例未误触发、1 负例 120 秒超时，coverage=11/12。Q2/5/6派发后超时，仅确认加载；质量门 errors>0 未通过。不用运行错误改 description。
- 独立复核补充：Q12普通read实际读取了临时目标SKILL.md，当前OpenCode只识别skill派发，未覆盖这种访问；不能说完全未加载，precision/recall仅派发口径。保留冻结判据与旧报告，后续补读取信号须新协议重评。
- 最终 attempt-3：两任务 × 当前/HEAD旧版/无目标技能，每组1次，全部执行完成。当前16/16、旧版14/16、无目标技能15/16断言；两份严格聚合完整性检查通过。旧版在不完整基准记录中误报整体增益；无技能改名额外转换CRLF。任务输入基准记录明确为synthetic，真实测的是模型分析行为。
- attempt-2曾发生shell借用全局旧验证器污染；保留原始日志与评分，不作干净对照。统一使用独立子进程USERPROFILE/APPDATA/LOCALAPPDATA后全组重跑，审计未再发现借用。XDG配置/状态隔离、--pure、无MCP及技能权限白名单也留痕；这些不是OS沙箱。
- 三名子代理分别审核触发、改名与基准分析，非盲评。产物哈希、输入完整性、源文件无漂移、API key精确值未落盘已检查。客户端cost=0不表示免费；真实tokens/耗时保留，单模型小样本不外推稳定收益。
- dev-only运行器、冻结输入/断言、原始transcript/metrics/artifacts/grading、完整报告均在evaluation-runs。成品无第二份仓库内副本；旧版解包与客户端临时状态在仓库外，原始交付证据已入评测目录。仅新增评测记录和总结，不提交/推送。

- 同步成品 SKILL.md、README.md、quality-bar、skill-index、skill-comparison、benchmark-schema，以及工作区 README.md。
- 五项优化记录现分布于 `skill-creator/skills/skill-creator/evolutions/evaluation.md`、`indexing.md`、`validation.md`，保留失败复现、SQLite/Anthropic 上游对照、取舍与限制。
- 新增 `skill-creator/tests/test_optimization.py`，21 个用例；同步原测试中本次有意改变的契约断言。
- 命名迁移记录现归并于 `skill-creator/skills/skill-creator/evolutions/distribution.md#naming`。
- 新增 `skill-creator/tests/test_script_entrypoints.py`，11 个用例；包含十个新 CLI 从隔离成品副本、无缓存、无宿主工作目录启动的检查。安装工具回滚参数化增加 3 个用例。
- 本地 `.opencode/skills/skill-creator/` 不存在，没有需要同步的安装测试副本。

## 发布门实际结果（09-29 提交前全量重跑）

```text
skill-creator pytest tests/ -q                  314 passed
skill-creator 成品 strict                       Checked 1，全绿
根 skills 能力库 strict                         Checked 7，全绿
agent-creator pytest tests/ -q                  122 passed
根 agents 能力库 strict                         Checked 7，全绿
tools pytest tools/tests -q                     44 passed
build_catalog.py --check                        skills/agents up to date
```

上述480项测试及所有CLI发布门在用户授权提交后重新执行，全绿。两个工作区各移除1个硬编码对方名称的扫描case，统一由仓库层更严格门禁覆盖；代理侧新增7个隔离CLI入口case，工具层补命名/文本规则及新旧安装检查。提交前仅重跑离线门禁，真实模型结果以两份测评REPORT为准，不把回归全绿解释为触发准确率提升。

归档收尾：根 `.gitattributes` 对 `evaluation-runs/` 禁用换行转换，原始尝试与夹具保留空白，防止提交时改变证据及其哈希；成品沿用常规Git换行规则，冻结哈希记录当时工作树字节。793份测评文件的暂存Git blob与工作树逐字节一致，40份agent测评冻结文件未变；对909份新增/修改文件检查已配置API凭据精确值，零匹配。暂存diff检查通过。发布门通过后更新本交接，输出新会话提示再提交、推送。

## 待办与限制

1. 用户已授权本轮提交和推送；收尾发布门已通过。本交接随提交保存，后续会话先核对本地/远端提交状态及CI；若改动代码，重跑受影响发布门。
2. 真实触发12条中Q12因缺应用输入持续查找而超时，并通过普通read读取了目标正文；现OpenCode只统计skill派发，需评估补充读取信号并提供代表性输入后按新协议重评。若依据本次结果调描述，换未见最终集，保留已有失败记录。
3. 中文扩展是有限离线关键词表，不是通用翻译；未知词/长句由执行代理抽关键词并补英文检索。
4. 旧索引各源状态与 upstream_commit 为 unknown 是预期兼容行为；后续按源增量同步才获得真实成功时间和固定版本。
5. 延续待选项：HTML 评测报告/可视化评审页未采纳，未实施。
6. 延续非阻塞限制：稀疏源的父目录定位使用 GitHub contents API，超大目录仍有返回条目上限问题；接入这种源前需单独改进定位方式。
7. 外部用户命令或 Python 模块导入若仍引用旧文件名，需要同步迁移；当前成品只提供新名称。

8. 基准v2下游读取者需要支持null、n与状态/配对字段；Claude旧approximate_passed只是历史报告。默认报告模式保留，质量门选--strict。
9. 场景统计只覆盖已发现的run目录；本次用冻结场景清单核对六次均启动并完成。临时cwd不是权限沙箱；真实发现了全局工具污染并统一重跑。单模型、两个场景不足以证明普遍收益；新版/旧版改名速度相近，未验证入口压缩收益。

## 验证命令备忘

```bash
# 仓库根
python -m pytest skill-creator/tests -q
python skill-creator/skills/skill-creator/scripts/skill_validate.py --strict --dir skill-creator/skills/skill-creator
python skill-creator/skills/skill-creator/scripts/skill_validate.py --strict --dir skills
python -m pytest agent-creator/tests -q
python agent-creator/skills/agent-creator/scripts/agent_validate.py --strict --dir agents
python -m pytest tools/tests -q
python tools/scripts/build_catalog.py --check

python skill-creator/skills/skill-creator/scripts/skill_index_search.py "代码审查"
python skill-creator/skills/skill-creator/scripts/skill_index_search.py --stats

# 技能目录内：真实触发质量门
python scripts/skill_eval.py --eval-set <查询集.json> --skill-dir <目标技能> --mode cli --client opencode --model <模型id> --fail-on-error --fail-on-mismatch --json

# 技能目录内：开发集优化 + 独立最终集一次确认
python scripts/skill_optimize.py --eval-set <开发集.json> --skill-dir <目标技能> --improve-mode cli --eval-mode heuristic --final-eval-set <独立最终集.json> --final-mode cli --client opencode --model <模型id> --report <报告.json>
```

## 新会话交接提示

```text
读取 HANDOFF.md 交接并继续本仓库工作
```
