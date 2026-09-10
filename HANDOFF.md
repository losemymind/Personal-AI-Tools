# 会话交接（2026-09-10 · 第 5 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main`，origin = `losemymind/Personal-AI-Tools`。历史提交：`6824c79` 仓库结构 → `35ca36d` 双创建器工作区/适配器/CATALOG → `46830ca` evals 键名漂移 → `e20fff1` agent 评审闭环 → `79600a2` 加固验证器/评测链 → `cc0962f` 入库 mcp-builder/ue5 → `d486a26` 修复 metrics.json 契约 → `25f03f5` 补验证器缺口 → **本会话续：清四项内部债（见下）**。
- 两工作区**同构精简**（无 `build/`、成品无 `AGENTS.md`、`INSTALL.md` 在工作区根、成品 `SKILL.md` 为唯一入口）；发布检查差异只因**成品自校验能力不同**（skill-creator 有 `validate_skills.py --strict`；agent-creator 自包含扫描落在 pytest）。
- 能力库：`skills/` = **5 技能**（development/code-review-skill、development/mcp-builder、game-development/ue5-performance-optimization、git/pr-summarizer、product-design/prd-generator）；`agents/` = 32 代理（academic×5 / code-quality×2 / ue-game-studio×25）。
- 版本：**skill-creator 0.9.3**、**agent-creator 0.7.0**。
- `opencode.json`（仓库根）用 `instructions` 注册三份 `AGENTS.md`；`.opencode/`（安装测试副本）已 gitignore。

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

## 已知待办 / 潜在风险

1. **真实客户端 CLI 场景未跑通**：本环境嵌套 `opencode run` 返回 server error，skill-creator 量化基准只能以合成 stub 客户端验证**链路**（非真实模型行为）。有可用无头客户端时应补跑 `run_scenario.py` 真机基准。
2. **触发评测为词重叠启发式**：仅代表词面覆盖，不代表真实触发率；`ue5-performance-optimization` 对「Unity 性能优化」的假阳性属固有（性能/优化为核心词不可去），不宜继续为此改描述。
3. **能力库/审计一致性**：`skills/` 现 5 技能、`agents/` 32 代理；增删须同步 `skills/SKILLS-AUDIT.md`/`agents/AGENTS-AUDIT.md` 与两份 `CATALOG.md`，重跑 `python tools/scripts/build_catalog.py`。（本次为技能新增 `evals.json`，未改变技能/代理集合，审计与 CATALOG 无需变动。）
4. **已评估、用户明确「不需要修复」的项（勿再主动提出）**：skill-creator 成品 `examples/`（103 文件学习样本）、两份 `indexes/upstream.db`（随成品提交）、能力库 UE/academic 垂直内容——维持现状。
5. **提交纪律（铁律 3）**：任何 git 提交/推送前，必先跑发布门全绿 + 同步受影响的文档（README/审计/CATALOG/evolutions/版本号）+ 更新本 `HANDOFF.md` + 向用户输出可点击复制的新会话交接提示。
6. **CI 已加但未在真机运行**：`.github/workflows/validate.yml` 仅本地校验了 YAML 语法与等价命令，首次 push 后才能确认 Actions 端全绿。

## 验证命令备忘

```bash
# agent-creator（在 agent-creator/ 根）——发布门 = 一个 pytest 命令全含
python -m pytest tests/ -q        # 回归 + 成品自包含自检（18 例）

# skill-creator（在 skill-creator/ 根）
python -m pytest tests/ -q                                                    # 55 例
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator
python skills/skill-creator/scripts/validate_skills.py --strict --dir E:\GitHub\Personal-AI-Tools\skills
python skills/skill-creator/scripts/search_index.py --stats                   # 4 源 2187 条

# 能力库（仓库根）
python agent-creator/skills/agent-creator/scripts/validate_agents.py --strict --dir agents  # 32
python skill-creator/skills/skill-creator/scripts/validate_skills.py --strict --dir skills   # 5
python tools/scripts/build_catalog.py
python tools/scripts/build_catalog.py --check
```
