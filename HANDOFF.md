# 会话交接（2026-09-23 · 第 43 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main`；HEAD = `27654cf`（上一会话「coevoskills 索引源 + 竞品对比」）。其前 `2561c2d`（ue-editor-lifecycle 迁入 development + 补齐技能库审计）与 `27654cf` **均已提交**。
- 能力库：`skills/` = **7 技能**、`agents/` = **7 代理**。
- 本会话改动（**工作树，未提交**）：① 补齐 `ue-editor-lifecycle` 上游对比记录（审计欠账收口）② skill-creator 新增第六个上游索引源 `mattpocock`（含两层嵌套扫描）③ 新增第七个上游索引源 `karpathy`。
- 索引：5 源 2188 条 → **7 源 2227 条**（+`mattpocock/skills` 38、+`multica-ai/andrej-karpathy-skills` 1）。
- 两工作区同构；成品即源；成品自包含；文档一律无绝对路径。

## 本会话已完成（工作树，未提交）

### A. 补齐 `ue-editor-lifecycle` 上游对比记录（审计 §5 欠账收口）

- **背景**：`skills/SKILLS-AUDIT.md` §5 登记该技能自建时未做上游检索对比。
- **检索证据**（`search_index.py`，当时 5 源 2188 条）：主题词 `unreal editor` / `UnrealEditor` / `LaunchUE` / `PIE` / `rebuild` / `dll` / `frozen` / `hang` / `editor crash` / `ue5` **均 0 命中**；`--category game-development` 全列 18 条无编辑器生命周期条目。唯一相邻命中 = `skills/unreal-engine-cpp-pro`（aas，120 行）。
- **量化对比**：`compare_skills.py` 本地 **0.76** vs 最近邻 **0.72**（质量 0.97 vs 0.84）→ 采纳自建。
- **产出**：新增 `evolutions/2026-09-23-compare-ue-editor-lifecycle.md`；同步 `skills/SKILL-RECORDS.md` 与 `skills/SKILLS-AUDIT.md`（7 项全部合规，§5 无未完成整改项）。

### B. skill-creator 新增上游索引源 `mattpocock`（两层嵌套扫描）

- **背景**：用户要求加入 `https://github.com/mattpocock/skills`（MIT，「Skills for Real Engineers」，整仓约 1.8MB / 38 技能）。
- **技术要点**：该仓库把技能按类别分组到 `skills/<category>/<name>/`（`engineering`/`productivity`/`in-progress`/`misc`），比既有扫描源**深一层**——直接套用既有 `scan_skill_dir` 会得 0 条。
  - `build_index.py` 新增可选**两层嵌套扫描**：源声明 `skills_nested: True` → 扫描 `<skills_root>/<category>/<name>/SKILL.md`，`path` 保留完整相对路径；扫描逻辑抽成 `_iter_skill_dirs()`，一层/两层共用同一段条目构造。
  - **`category` 兜底**：frontmatter 未声明 `category` 时用**父目录名**兜底（该仓库 38 技能几乎都不写 category），使 `--category engineering` 等过滤可用；frontmatter 显式声明仍优先。仅含 README 的桶目录（`deprecated/`）自动跳过。
- **注册**：`SOURCES["mattpocock"]`（tarball main + `skills_root: "skills"` + `skills_nested: True`）；`search_index.py` 增别名 `mattpocock` / `matt-pocock`。
- **索引重建（增量）**：`+38 added`；5→**6 源 2226 条**。
- **测试**：`tests/test_build_index.py` 注册表断言 5→6 源 + 新增 3 例（registry 形态、嵌套扫描 path/category、frontmatter 缺 category 时父目录兜底）；`tests/test_search_index.py` 补别名断言。pytest 214 → **217 passed**。
- **文档同步**：成品 `README.md`、`references/skill-index.md`（源表 + 用法 + 两层嵌套专段）、成品 `SKILL.md` 阶段 0、`build_index.py` docstring、dev `README.md`（来源与沿革 + 2026-09-23 段）、工作区 `AGENTS.md`（6 源 2226 条 + 索引源名册）、`INSTALL.md` 校验期望值。
- **记录**：`evolutions/2026-09-23-adopt-mattpocock-source.md`。

### C. skill-creator 新增上游索引源 `karpathy`（andrej-karpathy-skills）

- **背景**：用户要求加入 `https://github.com/multica-ai/andrej-karpathy-skills`（约 20KB / 1 技能 `karpathy-guidelines`）。
- **技术要点**：普通一层布局 `skills/<name>/SKILL.md`，既有 `scan_skill_dir` 已覆盖，**直接注册即可、无需新机制**（区别于 `coevoskills` 稀疏取数、`mattpocock` 两层扫描）。
- **意义**：该仓库是能力库 `coding-discipline` 的**上游原始源**（此前只能经 `aas` 的同源分发副本 `skills/andrej-karpathy` 命中）；本次把原始源纳入索引，补齐 `--source` 直达路径。
- **注册**：`SOURCES["karpathy"]`（tarball main + `skills_root: "skills"`）；`search_index.py` 增别名 `karpathy` / `andrej-karpathy` / `karpathy-skills` / `multica`。
- **索引重建（增量）**：`+1 added`；6→**7 源 2227 条**。
- **测试**：注册表断言 6→7 源 + 新增 1 例（registry 形态），provenance 断言补新源；`tests/test_search_index.py` 补别名断言。pytest 217 → **218 passed**。
- **文档同步**：成品 `README.md`、`references/skill-index.md`、成品 `SKILL.md` 阶段 0、`build_index.py` docstring、dev `README.md`（来源与沿革 + 2026-09-23 ② 段）、工作区 `AGENTS.md`（7 源 2227 条）、`INSTALL.md`。
- **记录**：`evolutions/2026-09-23-adopt-karpathy-source.md`。

## 上一会话已完成（已提交，供追溯）

- `2561c2d`：`git mv skills/ue-editor-lifecycle → skills/development/ue-editor-lifecycle`（规则 4）；修复 `SKILLS-AUDIT.md`（5→7）、`SKILL-RECORDS.md` 表格；根 `AGENTS.md` 技能数 3→7。
- `27654cf`：skill-creator 新增第五个上游索引源 `coevoskills`（`build_index.py` 稀疏 API 取数，避免下载 ~600MB 整仓；4 源 2187 条 → 5 源 2188 条）＋竞品方法论对比；含删除混入能力库的创建器副本（阻塞门禁修复）。

## 发布门实际结果（全绿）

```text
skill-creator  job   pytest tests/ -q                                        → 218 passed
                     validate_skills.py --strict --dir skills/skill-creator   → Checked 1，全绿
                     validate_skills.py --strict --dir <仓库根>/skills         → Checked 7，全绿
                     search_index.py --stats                                  → 2227 条 / 7 源
catalog        job   build_catalog.py --check                                → up to date（skills 7 / agents 7）
tools          job   pytest tools/tests -q                                   → 25 passed
```

（本会话未改动 agent-creator，其测试与库校验沿用上一会话结果：116 passed、agents Checked 7 全绿。）

## 未完成项 / 风险 / 下一会话精确待办

1. **本会话改动未提交**（A + B + C 三块，含 3 个新增 evolutions 记录）；门禁全绿，可直接提交（提交/推送前先按铁律 3 走完收尾并更新本 HANDOFF）。
2. **可选升级（未采纳，需用户确认）**：给 `run_loop.py` / `aggregate_benchmark.py` 增 `--html` 自包含报告（train/test 区分），或评估 `eval-viewer` 式评审页在「子代理评审闭环」中的定位（见 `evolutions/2026-09-17-compare-coevoskills.md`）。
3. `.opencode/skills/` 未纳入 git（本地安装副本，已 gitignore）；其中**没有** skill-creator / agent-creator 安装副本，无需按工作区 SOP 同步测试副本。
4. 已知小瑕疵（未处理，非阻塞）：`build_index.py` 的 `sparse_subtree_paths()` 用 GitHub contents API 列举父目录，**单页上限 1000 条**；父目录条目 >1000 时会误判「目录不存在」。当前 `coevoskills` 的 `meta_skills/` 远小于阈值，暂不影响；后续接入大目录稀疏源需加分页。

## 验证命令备忘

```bash
# skill-creator（在 skill-creator/ 根）
python -m pytest tests/ -q
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator   # 成品自检
python skills/skill-creator/scripts/validate_skills.py --strict --dir <仓库根>/skills        # 能力库校验
python skills/skill-creator/scripts/search_index.py --stats                                   # 索引完整性（7 源 2227 条）

# 索引重建（coevoskills 为稀疏取数源，不再下载整仓 600MB；mattpocock 为两层嵌套扫描源）
python skills/skill-creator/scripts/build_index.py --source coevoskills --incremental
python skills/skill-creator/scripts/build_index.py --source mattpocock --incremental
python skills/skill-creator/scripts/build_index.py --source karpathy --incremental
python skills/skill-creator/scripts/build_index.py --incremental

# 触发评测（权威 = CLI）
python skills/skill-creator/scripts/run_eval.py --eval-set <技能目录>/evals/evals.json --skill-dir <技能目录> --mode cli --client opencode --model deepseek/deepseek-v4-flash --timeout 150 --concurrency 6

# agent-creator（在 agent-creator/ 根）
python -m pytest tests/ -q
python skills/agent-creator/scripts/validate_agents.py --strict --dir <仓库根>/agents

# tools / 目录（仓库根）
python -m pytest tools/tests -q
python tools/scripts/build_catalog.py            # 刷新 CATALOG
python tools/scripts/build_catalog.py --check    # 目录过期校验（发布门）
python tools/scripts/install.py --all skills --client opencode --scope workspace --dest <目标仓库根>
```

## 新会话交接提示（可复制）

```text
读取 HANDOFF.md 交接并继续本仓库工作
```
