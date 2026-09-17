# 采纳升级：新增上游索引源 `coevoskills`（含稀疏 API 取数模式）

## 基本信息
- 日期：2026-09-17
- 类型：采纳升级（adopt-）——索引覆盖扩展 + `build_index.py` 取数层新增能力
- 触发来源：用户要求把 `https://github.com/Zhang-Henry/CoEvoSkills/tree/main/meta_skills/skill-creator` 加入 skill-creator 的上游索引
- 来源：`Zhang-Henry/CoEvoSkills`（Apache-2.0，67★，默认分支 `main`，最后推送 2026-08-20）；技能子树 `meta_skills/skill-creator/`，18 文件 / 约 200KB

## 问题与证据（未加源前的实证）
- 该仓库**整仓约 600MB**（GitHub trees API 统计 blob 合计 599,488,789 B），绝大部分是 `tasks/**/environment/` 的基准数据（13f zip 86MB×2、pcap、mp4、csv），与技能无关。
- 现有 `SOURCES` 只有「整仓 tarball 下载 → 解包 → 扫描」一条取数路径。若照搬现有四源写法，`--source coevoskills` 与「全量重建 / `--incremental`（默认 all）」都会**下载整个约 426MB 的归档来索引 1 个技能**（约 3000 倍浪费，实测下载速率下为小时级）。
- 而 `meta_skills/` 子树本身仅 **18 文件 / 201,545 B**，完全适合按需取数。

## 采纳要点
1. **`build_index.py` 新增可选稀疏取数模式**：源声明 `api_subtree` + `branch` 时，走 `fetch_sparse_checkout()`：
   - `sparse_subtree_paths()` 用两次 **scoped** GitHub API 调用定位子树（父目录 `contents` 列目录取 dir 的 tree SHA → 该 tree SHA 的 `?recursive=1` 列表），避免整仓递归列表——既省流量，也绕开大仓库的 tree 截断风险；
   - 按 raw URL 逐文件下载（2 次重试），落成一个「形如仓库根」的最小 checkout（`<dest>/meta_skills/...`），从而**复用** `scan_skill_dir` / `enrich_structure` 全部既有逻辑；
   - `_read_url` 改为分块读（`resp.read()` 在 chunked 响应上会 `IncompleteRead`，与 `download_tarball` 同款处理）。
   - 离线/限流/截断仍按源降级为 `SourceUnavailable` → `main` 保留已提交行（既有优雅降级契约不变）。
2. **注册源**：`coevoskills`（`repo` / `tarball` 兜底 / `skills_root: "meta_skills"` / `api_subtree: "meta_skills"` / `branch: "main"`）；`search_index.py` 增别名 `coevoskills` / `coevo` / `zhang-henry`。
3. **索引重建（增量）**：`+1 added`；`search_index.py --stats` 由 4 源 2187 条 → **5 源 2188 条**。
4. **文档同步**：成品 `README.md`（源表 + `--source` + 许可）、`references/skill-index.md`（源表 + 用法 + 稀疏取数说明）、成品 `SKILL.md` 阶段 0 源列举、dev `README.md`、`AGENTS.md` 命令速查、`INSTALL.md` 校验期望值。
5. **测试**：`tests/test_build_index.py` 更新注册表断言（4→5 源）并新增 6 例（稀疏子树枚举/前缀、缺失目录、写入与重试失败、`load_source_checkout` 走稀疏分支而非 tarball、**provenance meta 覆盖新源**）；`tests/test_search_index.py` 补别名断言。

## 验证结果
```text
build_index.py --source coevoskills --incremental  → +1 added, ~0 updated, -0 removed
search_index.py --stats                            → 2188 条，5 源（Zhang-Henry/CoEvoSkills 1）
search_index.py "skill creator" --source coevoskills → 1 命中（meta_skills/skill-creator，252 行，18 文件）
pytest tests/ -q                                   → 全绿
validate_skills.py --strict --dir skills/skill-creator → 全绿
```

## 学习点
- **「先查后建」的覆盖不该被仓库体积绑架**：上游仓库的体量与其技能价值不成比例是常态（本例 3000:1）。索引层应为「技能子树小、仓库巨大」的源提供按需取数，而不是把整仓下载成本摊给每次构建。
- **稀疏取数应复用既有扫描逻辑**：把「按需取数」实现为「落成最小 checkout」，比另写一条解析管线更省代码、更少分叉，结构统计（`has_script`/`file_count`/`subdirs`）自动一致。
- **API 取数要 scoped**：整仓 `recursive=1` 列表既有流量成本，也会在超大仓库上触发截断；先列父目录拿 tree SHA 再列子树是 2 次小请求换稳健性。

## 改进建议（未实施，供后续）
- 若再有同类「巨大仓库 + 小子树」源，`api_subtree` 已是即插即用；可考虑把 `branch` 抽成源级默认值以省去重复声明。
