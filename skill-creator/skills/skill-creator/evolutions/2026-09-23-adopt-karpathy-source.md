# 采纳升级：新增上游索引源 `karpathy`（andrej-karpathy-skills）

## 基本信息
- 日期：2026-09-23
- 类型：采纳升级（adopt-）——索引覆盖扩展（无扫描层新能力，直接复用既有的一层扫描）
- 触发来源：用户要求把 `https://github.com/multica-ai/andrej-karpathy-skills` 加入 skill-creator 的上游索引
- 来源：`multica-ai/andrej-karpathy-skills`（约 20KB，默认分支 `main`）；单技能 `skills/karpathy-guidelines/SKILL.md`（68 行）

## 问题与证据（未加源前的实证）
- 该仓库是能力库 `coding-discipline` 的**上游原始源**（四条 LLM 编码行为准则，改写为「反例 → 正例」后入库 `skills/development/coding-discipline/`，见 `skills/SKILLS-AUDIT.md` 与 `evolutions/2026-09-14-compare-coding-discipline.md`）。
- 但「先查后建」索引**并未收录该原始源**：只能经 `aas`（`sickn33/agentic-awesome-skills`）的同源分发副本 `skills/andrej-karpathy` 命中。原始源缺索引 = 检索覆盖盲区（按 `--source` 无法直达上游原始条目，且副本可能滞后于原始源）。
- 布局为普通一层 `skills/<name>/SKILL.md`，仓库体量极小，**整仓 tarball + 既有 `scan_skill_dir` 一层扫描即可**，无需新取数/新扫描模式。

## 采纳要点
1. **注册源**：`karpathy`（`repo` / `tarball`（main）/ `skills_root: "skills"` / `index_file: None`），复用默认一层扫描（未设 `skills_nested`）。
2. **`search_index.py` 增别名**：`karpathy` / `andrej-karpathy` / `karpathy-skills` / `multica`。
3. **索引重建（增量）**：`+1 added`；`search_index.py --stats` 由 6 源 2226 条 → **7 源 2227 条**（`multica-ai/andrej-karpathy-skills` 1：`skills/karpathy-guidelines`）。
4. **文档同步**：成品 `README.md`（源表 + `--source` + 许可）、`references/skill-index.md`（源表 + 用法）、成品 `SKILL.md` 阶段 0 源列举、`build_index.py` 模块 docstring、dev `README.md`（来源与沿革 + 2026-09-23 ② 段）、工作区 `AGENTS.md`（命令速查 7 源 2227 条 + 索引源名册）、`INSTALL.md` 校验期望值。
5. **测试**：`tests/test_build_index.py` 更新注册表断言（6→7 源）、provenance 断言、docstring；新增 1 例 registry 形态断言（`test_karpathy_source_scans_single_level`）；`tests/test_search_index.py` 补别名断言。

## 验证结果
```text
build_index.py --source karpathy --incremental      → +1 added, ~0 updated, -0 removed
search_index.py --stats                             → 2227 条，7 源（multica-ai/andrej-karpathy-skills 1）
search_index.py "karpathy" --source karpathy        → karpathy-guidelines（skills/karpathy-guidelines，68 行）
pytest tests/ -q                                    → 全绿
validate_skills.py --strict --dir skills/skill-creator → 全绿
```

## 学习点
- **「先查后建」要收原始源，而非只靠分发副本**：同一技能常同时存在于原始源与 awesome-list 分发副本中。只索引副本会漏掉 `--source <原始源>` 的检索路径，也让副本滞后风险传导到「先查后建」。凡能力库已引用的上游，其**原始仓库本身**应登记为索引源。
- **不是每个新源都需要新机制**：与 `coevoskills`（稀疏取数）、`mattpocock`（两层扫描）不同，本源的布局/体量都落在既有能力内——先判断「既有扫描是否已覆盖」，别为加源而加机制。

## 改进建议（未实施，供后续）
- 可在 `SKILLS-AUDIT.md` 的 `coding-discipline` 行补注「上游原始源现已入索引」，使审计与索引覆盖保持一致（本次未改审计，避免扩大用户请求范围）。
