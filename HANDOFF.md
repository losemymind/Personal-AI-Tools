# 会话交接（2026-09-17 · 第 40 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main`；HEAD = `e3e0a2a`（更新 HANDOFF v38）。**本会话全部改动仍留在工作树、尚未提交**（三块，见下）。
- 能力库：`skills/` = **7 技能**（本会话全部归入分类目录）、`agents/` = **7 代理**。
- 本会话三块工作：① 修复被破坏的发布门（根 `skills/` 下混入创建器副本）② 补齐技能库审计欠账 ③ skill-creator 新增第五个上游索引源 `coevoskills`（含稀疏取数）+ 竞品方法论对比。
- 两工作区同构；成品即源；成品自包含；文档一律无绝对路径。

## 本会话已完成（工作树，未提交）

### A. 删除混入能力库的创建器副本（阻塞门禁修复）
- **现象**：根 `skills/` 下出现两份未跟踪副本 `skills/agent-creator/`、`skills/skill-creator/`（270 文件）。后果：`build_catalog.py --check` 报 stale（生成器把它们当库技能，往 `skills/CATALOG.md` 多写 2 条）；`validate_skills.py --strict --dir skills` 变 `Checked 9` 并因 `agent-creator` 缺 `## Examples` 失败。
- **判定**：违反铁律 1「成品即源，不复制」；与真源仅 `SKILL.md` 有格式差异（旧式无引号 description、frontmatter 后无空行），无独有内容。
- **处置**：删除两份副本（用户确认）；真源仍在 `skill-creator/skills/skill-creator/`、`agent-creator/skills/agent-creator/`。

### B. 规则 4 目录归位 + 技能库审计欠账
- `git mv skills/ue-editor-lifecycle → skills/development/ue-editor-lifecycle`（规则 4）；刷新 `skills/CATALOG.md`。
- `skills/SKILL-RECORDS.md`：修复被引用块打断的表格（引用块移到表后）。
- `skills/SKILLS-AUDIT.md`：技能总数 5 → **7**，补 `coding-discipline`（上游 `multica-ai/andrej-karpathy-skills`，0.76 vs 0.73 采纳自建）与 `ue-editor-lifecycle`（自建，规则 4 迁入 development）；§5 记其「缺上游对比记录」欠账。
- 根 `AGENTS.md:19` 技能数 3 → 7 修正。

### C. skill-creator 上游索引扩容 + 竞品对比（本会话主体）
- **背景**：用户要求加入 `https://github.com/Zhang-Henry/CoEvoSkills/tree/main/meta_skills/skill-creator`。实测该仓库**整仓约 600MB**（`tasks/**/environment/` 基准数据），而技能子树 `meta_skills/` 仅 **18 文件 / ~200KB** —— 现有「整仓 tarball」取数路径会为 1 个技能下载 426MB。
- **新增可选稀疏取数模式**（`build_index.py`）：源声明 `api_subtree` + `branch` 时走 `fetch_sparse_checkout()`——`sparse_subtree_paths()` 用 **scoped** 两次 API 调用（父目录 `contents` 取 dir tree SHA → 该 SHA `?recursive=1`），再按 raw URL 逐文件下载（2 次重试），落成「形如仓库根」的最小 checkout，从而复用既有 `scan_skill_dir` / `enrich_structure`。`_read_url` 改分块读（修 chunked `IncompleteRead`）。离线/限流/截断仍按源降级为 `SourceUnavailable`，既有优雅降级契约不变。
- **注册源 `coevoskills`** + `search_index.py` 别名（`coevoskills`/`coevo`/`zhang-henry`）；**索引 4 源 2187 条 → 5 源 2188 条**。
- **测试**：`tests/test_build_index.py` 注册表断言 4→5 源 + 新增 6 例（稀疏子树枚举/前缀、缺失目录、写入与重试失败、`load_source_checkout` 走稀疏分支而非 tarball、provenance meta 覆盖新源）；`tests/test_search_index.py` 补别名断言。
- **文档同步**：成品 `README.md`（源表 + `--source` + 许可）、`references/skill-index.md`（源表 + 用法 + 稀疏取数专段）、成品 `SKILL.md` 阶段 0 源列举、dev `README.md`（来源与沿革 + 2026-09-17 沿革段）、工作区 `AGENTS.md`（命令速查 5 源 2188 条 + 方法论来源名册）、`INSTALL.md`（校验期望值）。
- **竞品方法论对比**（成果：`evolutions/2026-09-17-compare-coevoskills.md`）：与本地**同血脉**（同 Anthropic 官方工具链：`agents/{grader,comparator,analyzer}` + `aggregate_benchmark/run_eval/run_loop/utils` + `references/schemas.md`），故属「同基线 + 各自增量」。量化 `compare_skills.py`：本地 0.98 vs 上游 0.55（质量差距含 schema 口径，已在记录中扣减解读）；结构 1.00 vs 0.92。上游真实增量 = **`eval-viewer/generate_review.py`**（stdlib 自包含 HTML 评审页 + `feedback.json` 回流）与 **`generate_report.py`**（run_loop 的 HTML 报告，**train/test 区分**）；且这两个脚本+`improve_description.py` 在上游**任何 md 中都未被引用**（文档盲区，已记录）。结论：不采纳、抽取 2 条学习点；「零人工反馈」立场明确**不采纳**（与本库决策门纪律冲突）。
- 索引源扩容单独记录：`evolutions/2026-09-17-adopt-coevoskills-source.md`。

## 发布门实际结果（全绿）

```text
skill-creator  job   pytest tests/ -q                                            → 214 passed
                     validate_skills.py --strict --dir skills/skill-creator       → Checked 1，全绿
                     validate_skills.py --strict --dir skills（能力库）            → Checked 7，全绿
                     build_index.py --source coevoskills --incremental            → +1 added
                     search_index.py --stats                                      → 2188 条 / 5 源
agent-creator  job   pytest tests/ -q                                            → 116 passed（本会话未改动）
                     validate_agents.py --strict --dir agents（能力库）           → Checked 7，全绿
catalog        job   build_catalog.py --check                                    → up to date（skills 7 / agents 7）
tools          job   pytest tools/tests -q                                       → 25 passed
```

## 未完成项 / 风险 / 下一会话精确待办

1. **`ue-editor-lifecycle` 缺上游对比记录**（审计 `skills/SKILLS-AUDIT.md` §5 已登记）：`SKILL-RECORDS.md` 的 evolutions 列为 `-`。待办：跑 `search_index.py` 检索同类 UE 编辑器/构建流程技能；有候选补写 `evolutions/2026-09-xx-compare-ue-editor-lifecycle.md`，无候选则注明「索引 0 命中」。
2. **可选升级（未采纳，需用户确认）**：给 `run_loop.py` / `aggregate_benchmark.py` 增 `--html` 自包含报告（train/test 区分），或评估 `eval-viewer` 式评审页在「子代理评审闭环」中的定位（见 `evolutions/2026-09-17-compare-coevoskills.md` 改进建议）。
3. `.opencode/skills/` 未纳入 git（本地安装副本）；**预期行为**（已 gitignore）。本会话确认其中**没有** skill-creator / agent-creator 安装副本，故无需按工作区 SOP 同步测试副本。
4. 三块改动（A/B/C）均**未提交**；工作树全绿，可直接提交（提交/推送前先按铁律 3 走完收尾）。

## 验证命令备忘

```bash
# skill-creator（在 skill-creator/ 根）
python -m pytest tests/ -q
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator   # 成品自检
python skills/skill-creator/scripts/validate_skills.py --strict --dir <仓库根>/skills        # 能力库校验
python skills/skill-creator/scripts/search_index.py --stats                                   # 索引完整性（5 源 2188 条）

# 索引重建（coevoskills 为稀疏取数源，不再下载整仓 600MB）
python skills/skill-creator/scripts/build_index.py --source coevoskills --incremental
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
