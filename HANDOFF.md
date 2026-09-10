# 会话交接（2026-09-10 · 第 10 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main`，origin = `losemymind/Personal-AI-Tools`。历史提交：`6824c79` 仓库结构 → `35ca36d` 双创建器工作区/适配器/CATALOG → `46830ca` evals 键名漂移 → `e20fff1` agent 评审闭环 → `79600a2` 加固验证器/评测链 → `cc0962f` 入库 mcp-builder/ue5 → `d486a26` 修复 metrics.json 契约 → `25f03f5` 补验证器缺口 → `8096810` 清四项内部债（0.9.3）→ `192c905` 打通真机无头 CLI（0.9.4）→ `e819536` 真机评测隔离化 + 独立审计两轮修复（0.9.5-0.9.18，见 §E/§F/§G）→ `dfaf829` 交接状态修正。**origin/main 已同步，GitHub Actions CI 三 job 全绿（run 34480215967）**。
- 两工作区**同构精简**（无 `build/`、成品无 `AGENTS.md`、`INSTALL.md` 在工作区根、成品 `SKILL.md` 为唯一入口）；发布检查差异只因**成品自校验能力不同**（skill-creator 有 `validate_skills.py --strict`；agent-creator 自包含扫描落在 pytest）。
- 能力库：`skills/` = **5 技能**（development/code-review-skill、development/mcp-builder、game-development/ue5-performance-optimization、git/pr-summarizer、product-design/prd-generator）；`agents/` = 32 代理（academic×5 / code-quality×2 / ue-game-studio×25）。
- 版本：**skill-creator 0.9.18**、**agent-creator 0.7.0**。
- `opencode.json`（仓库根）用 `instructions` 注册三份 `AGENTS.md`；`.opencode/`（安装测试副本）已 gitignore。
- 本机可用模型串：`deepseek/deepseek-v4-flash`、`deepseek-responses/deepseek-v4-flash`（全局 `model` 指向不存在的 `siliconflow/...`，必须用 `--model`/`-m` 显式指定）。
- ✅ 真机评测污染已修复（0.9.7，逐查询隔离工作区）；✅ 全量审计九轮（0.9.8-0.9.16）；✅ **独立审计第三/四轮（0.9.17-0.9.18）共发现并修复 19 项真实缺陷**——**第九轮子代理「成品无可复现缺陷」的结论被推翻**（那九轮只修崩溃/健壮性，漏了数据契约与文档-行为一致性）；**修复后又复核才暴露 2 项高/中（delta 角色解析、`.env` 漏扫）**。

## 本会话已完成改动

### A. skill-creator 成品演进 0.9.0 → 0.9.1（修复基准评测链 5 处缺陷）

只读审阅 skill-creator 成品后，修复基准评测链的 5 处缺陷（C1 为真实产物契约断裂）：

- **C1 metrics.json 写入/读取路径不一致**（数据丢失）：`run_scenario.py` 写 run 根目录，`agents/grader.md` 却读 `outputs/` 子目录，导致该文件无人消费、`tool_calls` 恒 0。修复：grader 路径改为 `{outputs_dir}/../metrics.json`；`aggregate_benchmark.py` 增确定性回退，直接读 run 根 `metrics.json`。
- **C2 tool 计数脆弱**：`run_scenario.py` 新增 `count_tool_calls()`，改逐行 `json.loads` 按 `type=="tool"` 计数（原空格敏感子串计数）。
- **C3 schema 缺记录**：`references/benchmark-schema.md` 补 `metrics.json` 小节、读取契约与完整工作区布局。
- **C4 run_loop 选优口径**：新增 `_test_rank()`，按 test **通过率**选优、并列回退 passed 计数。
- **C5 run_eval 汇总口径**：`summarize()` 的 `total` 只计已评分查询（`passed+failed==total`），run errors 单列。
- 测试：`tests/test_hardening.py` +5 例（tool 计数 / aggregate 回退 / grader 路径契约 / run_eval 口径 / run_loop 排序）→ skill pytest **41 → 46**。
- 记录：`evolutions/2026-09-10-fix-metrics-contract.md`（新增）。
- `.opencode/skills/skill-creator/` 安装副本已同步 7 个改动文件（逐字节一致）。

### B. skill-creator 成品演进 0.9.1 → 0.9.2（补齐 `validate_skills.py` 三个机械缺口）

- **E1 name 字符集（twin parity）**：验证器补 `NAME_PATTERN`，强制小写 kebab-case（孪生 `validate_agents.py` 早已强制，skill-creator 漏掉）。
- **E2 evals.json 形状**：技能存在 `evals/evals.json` 或根 `evals.json` 时强制形状（可解析、含 `evals` 数组、每项有非空 `query`（legacy `prompt` 可）与布尔 `should_trigger`）；**缺失仅 advisory**（不阻断，能力库 3 个技能尚未随附 evals）。
- **E3 反引号引用白名单**：由 `md|py|sh|json|yaml|yml|ts|js` 扩为含 `db`/`txt`/`xml`/`toml`/`css`/`html`/`rs`/`go` 等，使 `indexes/upstream.db` 类引用纳入校验。
- **minor**：`risk: unknown` 新增 advisory。
- 测试：`tests/test_hardening.py` +6 例 → skill pytest **46 → 52**。
- 记录：`evolutions/2026-09-10-close-validator-gaps.md`（新增）。
- `.opencode/skills/skill-creator/` 镜像已同步 4 个改动文件。
- 未改动：agent-creator、根能力库 `skills/`/`agents/` 内容、两份 `CATALOG.md`（`--check` 仍 up to date）。

### C. skill-creator 成品演进 0.9.2 → 0.9.3（清四项内部债）

1. **references 互链（内容 + 护栏）**：修 `skill-writing-guide.md`/`skill-template.md`/`quality-bar.md` 三处裸兄弟文件名互链；`validate_skills.py` 新增 `check_references_cross_links()`，把「references 不互链」变成机械 error。
2. **连带发现并修复 `utils.classify` 缺陷**：原按 description 中**重复 token 计数**，导致「创建」出现 3 次时任何含「创建」的查询假阳性。改为按去重 token 集合求交。
3. **dogfooding evals**：为 skill-creator 主体现增 `evals.json`（14 条），并为 `code-review-skill`/`pr-summarizer`/`prd-generator` 各补 `evals.json`（各 11 条）→ 成品与 5 个库技能 strict 的「No evals.json」advisory 全部清零。
4. **CI**：新增 `.github/workflows/validate.yml`（3 job：skill-creator pytest+strict、agent-creator pytest+strict、CATALOG `--check`），复刻本地发布门。
5. **债 4（对比评分粒度）暂不修**：维持文档化（改动会破坏 `evolutions/` 历史分值可比性，投入产出比低）。
- 测试：`tests/test_hardening.py` +3（references 互链失败/放行、classify 去重）→ skill pytest **52 → 55**；另新增 4 份 evals.json（非 pytest）。
- 记录：`evolutions/2026-09-10-close-audit-debts.md`（新增）。
- 文档：根 `AGENTS.md` 补 CI 说明；`.opencode/skills/skill-creator/` 镜像同步 8 个文件。
- 未改动：agent-creator 及两名库内容、两份 `CATALOG.md`（`--check` 仍 up to date）。

> 备注：`code-review-skill` 触发评测 10/11，唯一假阳性「总结…PR 改动」源于与 pr-summarizer 共享通用词 `pr`/`改动`，属词重叠启发式固有（同 ue5 先例），已保留记录。

### D. skill-creator 成品演进 0.9.3 → 0.9.4（打通真机无头 CLI）

- **环境根因**：`~/.config/opencode/opencode.json` 顶层 `model` 指向不存在的 `siliconflow/...` → 每次 `opencode run` 报 `UnknownError`。**解法：`opencode run -m <provider>/<model>` 显式指定，无需改全局配置。** 本机可用模型串：`deepseek/deepseek-v4-flash`、`deepseek-responses/deepseek-v4-flash`。
- **真机暴露并修复 4 处评测链缺陷**（合成 stub 发现不了）：
  1. cli 三处（`run_eval`/`run_scenario`/`run_loop`）不支持 `--model` → 默认模型错时全 run_error；已加并透传。
  2. **触发判定假阳性**：原按「技能名出现在整段输出」判定，实测「帮我写单元测试」因 `Get-ChildItem` 列出 `.opencode\skills\skill-creator` 路径被误判为触发；已改为**只认客户端派发技能工具**（opencode `tool_use` 且 `tool=="skill"`、`input.name==技能名`）。
  3. `summarize()` 对 cli 结果 `KeyError: 'triggered'`（cli 用 `trigger_rate`）；已归一化两种形状。
  4. `run_scenario` 工具计数恒 0（真机事件是 `tool_use`）；已兼容。
  5. `run_eval` 新增 `--timeout`。
- **真机证据（部分）**：受控实验确认 skill-creator 被真实触发（事件流出现 `tool:"skill"` / `input.name:"skill-creator"`）；6 条子集实跑出 1 超时 + 2 pass 后，完整重跑因**单条查询耗时长、命令卡死**被用户中止——**完整真机基准仍待**在有充裕时间时补跑。
- 测试：`tests/test_hardening.py` +5 → skill pytest **55 → 61**。
- 记录：`evolutions/2026-09-10-realmachine-cli-unblock.md`。
- 镜像同步 5 文件；docs（SKILL.md 阶段 5/7 用法）已更新。

### E. skill-creator 成品演进 0.9.4 → 0.9.7（真机评测：提速 + 信号保真 + 隔离）

**E1（0.9.5）run_eval 有界并行**：真机 `--mode cli` 原为**串行**，批次 1（7 查询 × 3 次 = 15 次 `opencode run`）耗时 **927.5s**，批次 2 超 10 分钟卡死（单条查询 30–120s）。新增 `--concurrency N`（默认 1=串行、向后兼容；`ThreadPoolExecutor.map` 保序），抽出 `run_cli_item`/`run_cli_batch`。真机提速 **~4.8×**（批次 1：928s → 194s）。+3 测试。

**E2（0.9.6）超时保留已发生的触发信号**：`run_cli` 原在 `TimeoutExpired` 时直接抛错、丢弃部分 stdout，但技能派发（`tool_use`）常发生在耗时任务**之前** → 真实触发被误记 `run_error`、系统性低估 recall。改为超时先解析部分输出（`_partial_text`），已见本技能派发即记触发，无证据才报错。+3 测试。

**E3（0.9.7）一次性隔离工作区**：`run_eval --mode cli` 原在仓库根**就地**运行，触发代理会真的执行技能并改动仓库（实证：追加测试、生成 `.eval-baseline/`/`.tmp-eval/`、派生孤儿进程）。新增 `build_workspace()`（`tempfile.mkdtemp` + 技能装入 `SKILL_SUBPATHS` 发现路径，与 `run_scenario` 一致）与 `run_cli(..., workspace=)`；`main()` 结束即 `rmtree`，`--keep-workspace` 可保留调试。+5 测试。

**真机复跑（0.9.7 隔离版，14 查询 × 3 轮，`deepseek-v4-flash` + opencode，`--concurrency 7 --timeout 120`）**：
- 批次 1：**4/7 过线、recall 0.571、0 run_error**；批次 2：**7/7 全过、recall 100%**（6 条负例全部正确不触发）。
- 汇总：正例 **5/8 过线（recall ≈ 0.625）**、precision **100%**；**git status 零污染、无孤儿进程、临时工作区自动清理**。
- 对比：隔离前就地运行时触发代理会卡在仓库里执行技能（超时/低触发）；隔离后既卫生又显著提升测量质量。

- 测试：`tests/test_hardening.py` +6（0.9.5/0.9.6）再 +5（0.9.7）→ skill pytest **61 → 77**。
- 记录：`evolutions/2026-09-10-realmachine-concurrency.md`、`-timeout-signal.md`、`-isolation.md`。
- 镜像同步 run_eval.py / SKILL.md / README.md / 三份 evolutions。
- 未改动：agent-creator、根能力库内容、两份 `CATALOG.md`（`--check` 仍 up to date）。

### F. skill-creator 全量审计九轮修复 0.9.8 → 0.9.16（用户要求「全部修复 + 子代理续查至无问题」）

对成品全部脚本做只读审计，实证复现并修复 12 项缺陷；随后由 code-reviewer 子代理连续复查 8 轮，逐轮修复其新发现，直至末轮判定**成品在合理用户路径上无可复现的正确性/安全/契约缺陷**。

**第一轮（0.9.8）12 项**：安全 allowlist 全局绕过→局部豁免；compare 缺 SKILL.md 崩溃；aggregate delta 方向靠字典序；run_loop cli 未隔离/JSON 解析；run_eval 并发共享工作区；超时只杀直接子进程→杀进程树；run_scenario 超时不落盘；`assets/` vs `templates/`；compare docstring；脚手架不出 evals.json；cli 客户端范围说明；split 边界 + evals 扩到 20。

**子代理八轮追加（0.9.9→0.9.16）**：
- 围栏检测 CommonMark 化（`~~~`/未闭合/4 反引号不再绕过安全扫描）；
- FTS5 特殊字符查询崩溃 → 逐词字面引用；
- 大批 `aggregate_benchmark`/`run_eval`/`run_loop`/`run_scenario`/`create_skill` 的**畸形输入崩溃**（非字典 JSON/`part`、混合 `eval_id`、非有限值 `Infinity`/`NaN`、非数字字段、路径参数指向文件、父路径是文件等）全部转清晰报错；
- 脚手架 YAML 转义（描述/作者/tools）、描述长度校验、版本校验、交互 EOF；
- compare `--json` 纯 JSON；`--keep-workspace` 打印路径；`build_workspace` 失败清理；密钥扫描扩到全目录（引用扫描仍限 SKILL.md）；
- 基准 delta 无基线时置 `null`+note（不再假增益）、markdown delta 百分比单位。

- 测试：`tests/test_hardening.py` 从 72 → **130 例**（0.9.8 起 +58）；成品/能力库/agent strict 与 CATALOG 全绿。
- 记录：`evolutions/2026-09-10-audit-round2-fixes.md`（含各轮明细）。
- 镜像同步 utils/validate/compare/aggregate/run_eval/run_loop/run_scenario/create_skill/search_index + SKILL/README/references/evals。
- 未改动：agent-creator、根能力库内容、两份 `CATALOG.md`（`--check` 仍 up to date）。

### G. skill-creator 独立审计第三轮 0.9.16 → 0.9.17（14 项真实缺陷）

前九轮只修「崩溃/健壮性」，本轮由主代理 + 两个 code-reviewer 子代理独立复查，逐条复现后修复**数据契约、安全扫描覆盖/绕过、文档-行为一致性**类缺陷：

1. **索引写坏已提交数据（中）**：`build_index.frontmatter_of` 块标量描述存成 `'>'`/`'|-'` 字面量（`indexes/upstream.db` 中 3 条 anthropics 记录实证损坏）→ 改用共享 `utils.parse_frontmatter`（PyYAML/UTF-8-sig）+ 增强 min 解析回退；`--source anthropics --incremental` 重建，损坏清零、总数 2187 不变。
2. **危险管道绕过/误报（中/高）**：续行 `\`+换行、`| sudo -u root bash`、`env bash`、`/bin/bash`、`busybox sh`、4 空格缩进、blockquote 围栏全部漏检；且**只扫 SKILL.md、捆绑脚本不扫** → 重写为「管道链 + 右侧 token 化判定」（不误报 `| grep bash`），覆盖续行/缩进/引号围栏，并把目录级危险管道扫描并入 `check_dir_secrets`。
3. **claude 触发判定与文档矛盾（中）**：`detect_triggered` 走全文子串却声称「不做子串匹配」→ 接受 `type in ("tool_use","tool")`，SKILL.md 明写 claude 为 best-effort 子串。
4. **契约/健壮性（低）**：markdown 链接加 fenced 豁免；`run_loop --holdout nan/inf` 校验；`run_loop` 补评最后一轮改进候选（不再丢轮）；`run_scenario` 命令缺失也落盘；`load_eval_set` 强制 `should_trigger`；`skill_count==0` 报错；`search_index` 拒负 limit；`ask()`/benchmark 文案/timing schema 小修；密钥扫描扩展名补 `.ps1/.bat/.cmd/.env`。
5. **经复核不成立、未改**：扫描源 `category/risk` NULL（上游 frontmatter 确实只有 name/description）、4 反引号闭合 3 反引号围栏（符合 CommonMark）。
- 测试：`tests/test_hardening.py` **130 → 148 例**；索引重建；`.opencode` 镜像全量同步（53 文件哈希一致）。
- 记录：`evolutions/2026-09-10-audit-round3-data-and-coverage.md`。

### H. skill-creator 第四轮复核 0.9.17 → 0.9.18（修复后再查，又 5 项）

对第三轮**修复后**的成品再跑子代理复核，暴露 2 项高/中真实缺陷（证明「修了但没修对」）：

1. **`aggregate_benchmark._ordered_configs` 混合命名下 delta 符号反转（高）**：primary 仅以别名出现、baseline 以精确名出现时，单次遍历把 baseline 放进 primary 位 → 报告 `primary=without_skill`、增益取反。先独立解析角色再排序。
2. **`.env` 密钥漏扫（高，第三轮补的扩展名从未生效）**：`os.path.splitext(".env")==('.env','')`、`.env.local==('.env','.local')` → 裸 dotenv 文件跳过。新增 `_is_scannable_text`。
3. **危险管道三类绕过（中）**：`|` 落行尾换行、tab 缩进代码块（1 tab=4 列）、PowerShell 别名错配（`irm`/`iwr`）与 `pwsh/powershell/cmd` 未覆盖。
4. **`scan_skill_dir` 丢弃 `tags`/`tools`（中）**：透传（映射 `plugin.targets`）。
5. **低**：`command -v bash` 误报；`--no-dl` 根目录差一级；`skill-anatomy.md` 的 `{{#include}}` 伪语法与 TOC 阈值 300/100 不一致。
- 测试：`tests/test_hardening.py` **148 → 153 例**；`.opencode` 镜像同步（54 文件哈希一致）。
- 记录：`evolutions/2026-09-10-audit-round4-recheck.md`。

### I. 交付收尾：推送 + CI 首次验证（本次会话）

- 复核上会话所有改动（0.9.5-0.9.18）实为已提交 `e819536`，HANDOFF 中「未提交」表述过期。
- 本地发布门全绿：agent-creator pytest 18、skill-creator pytest 153、skill-creator 成品 strict + 能力库 5 技能 strict、能力库 32 代理 strict、`build_catalog.py --check`、索引 4 源 2187 条。
- 修正 HANDOFF 过期状态 → 提交 `dfaf829` → 推送 `origin/main`。
- **CI 首次真机运行全绿**：`.github/workflows/validate.yml` 三 job success（run 34480215967）。未改任何成品/能力库内容。

## 已知待办 / 潜在风险

1. **真机基准已跑通（0.9.7，隔离版）**：工具侧 `--model`/`--timeout`/`--concurrency`/超时保信号/隔离全部就绪；14 查询 × 3 轮复跑 <5 分钟、零污染。当前成绩：正例 recall ≈ 0.625、precision 100%、0 假阳性。触发仍有非确定性（同句可能一次派发、一次直接作答）。**待办**：如需进一步提升 recall，方向是优化 description 或增加 runs——不属工具缺陷，勿擅自改描述。
2. **成品已修至 0.9.18（第三/四轮审计）**：九轮后子代理曾判定「无可复现缺陷」，但独立审计两轮又找出 19 项真实缺陷并已修复；**教训：①审计要覆盖「已提交产物的数据契约」与「文档承诺 ≠ 行为」，不能只盯异常输入 traceback；②修复后必须再复核「修是否真的生效」**（第三轮补的 `.env` 扩展名就因 `splitext` 对 dotfile 失效而形同虚设）。后续再改脚本仍按 SOP 补 pytest 并重跑发布门。已知残留（低，未改）：`examples/README.md` 称 `loki-mode/references/` 有 16 个子文件，实为 14——按用户「examples/ 不需修复」指示保留。
3. **触发评测为词重叠启发式**：仅代表词面覆盖，不代表真实触发率；`ue5-performance-optimization` 对「Unity 性能优化」的假阳性属固有（性能/优化为核心词不可去），不宜继续为此改描述。
4. **能力库/审计一致性**：`skills/` 现 5 技能、`agents/` 32 代理；增删须同步 `skills/SKILLS-AUDIT.md`/`agents/AGENTS-AUDIT.md` 与两份 `CATALOG.md`，重跑 `python tools/scripts/build_catalog.py`。（本会话只改创建器成品，未改技能/代理集合，审计与 CATALOG 无需变动。）
5. **触发代理追加的 5 个测试已保留**：`tests/test_hardening.py` 中 `test_run_cli_item_threshold_semantics` 等 5 例——经审阅内容正确、全绿，用户决定保留。
6. **已评估、用户明确「不需要修复」的项（勿再主动提出）**：skill-creator 成品 `examples/`（103 文件学习样本）、两份 `indexes/upstream.db`（随成品提交）、能力库 UE/academic 垂直内容——维持现状。
7. **提交纪律（铁律 3）**：任何 git 提交/推送前，必先跑发布门全绿 + 同步受影响的文档（README/审计/CATALOG/evolutions/版本号）+ 更新本 `HANDOFF.md` + 向用户输出可点击复制的新会话交接提示。（改动已提交 `e819536`、交接修正 `dfaf829` 并推送；本次会话确认发布门全绿后完成。）
8. **CI 已首次在真机运行并全绿**：`.github/workflows/validate.yml` 在推送 `dfaf829` 后运行，三个 job（agent-creator pytest+strict / skill-creator pytest+strict / CATALOG --check）全部 **success**（run 34480215967，https://github.com/losemymind/Personal-AI-Tools/actions/runs/34480215967 ）。

## 验证命令备忘

```bash
# agent-creator（在 agent-creator/ 根）——发布门 = 一个 pytest 命令全含
python -m pytest tests/ -q        # 回归 + 成品自包含自检（18 例）

# skill-creator（在 skill-creator/ 根）
python -m pytest tests/ -q                                                    # 153 例
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator
python skills/skill-creator/scripts/validate_skills.py --strict --dir E:\GitHub\Personal-AI-Tools\skills
python skills/skill-creator/scripts/search_index.py --stats                   # 4 源 2187 条

# 能力库（仓库根）
python agent-creator/skills/agent-creator/scripts/validate_agents.py --strict --dir agents  # 32
python skill-creator/skills/skill-creator/scripts/validate_skills.py --strict --dir skills   # 5
python tools/scripts/build_catalog.py
python tools/scripts/build_catalog.py --check

# 真机触发评测（仓库根；单条查询 30–120s，务必并行 + 超时兜底；cli 模式自动隔离、结束清理临时工作区）
python skill-creator/skills/skill-creator/scripts/run_eval.py --eval-set skill-creator/skills/skill-creator/evals.json --skill-dir skill-creator/skills/skill-creator --mode cli --client opencode --model deepseek/deepseek-v4-flash --timeout 120 --runs-per-query 3 --concurrency 7 --output-dir <dir>
```
