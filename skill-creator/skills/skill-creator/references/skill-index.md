# 上游技能索引（Skill Index）

基于多个上游技能仓库构建的本地 SQLite 检索索引，让 skill-creator 在创建前能快速检查"上游是否已有可用技能"（先查后建）。

## 目录

- [数据来源与规模](#数据来源与规模)
- [索引说明](#索引说明)
- [使用](#使用)
- [构建与更新](#构建与更新多源)
- [逐源更新状态](#逐源更新状态)

## 数据来源与规模

| 项 | 值 |
|---|---|
| 索引文件 | `indexes/upstream.db` |
| 技能总数 | ~2227（随上游更新变化） |
| 数据源 | 多源：见下表 |
| 许可 | 各上游仓库 LICENSE 为准 |

### 上游源

| 别名 | 仓库 | 技能数 | 索引方式 | 许可 |
|---|---|---|---|---|
| `aas` | [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills) | ~2115 | 官方 `skills_index.json`（权威元数据）+ 目录扫描补充结构 | MIT |
| `addy` | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 25 | 扫描 `skills/*/SKILL.md`（无官方索引文件） | MIT |
| `anthropics` | [anthropics/skills](https://github.com/anthropics/skills) | ~19 | 扫描 `skills/*/SKILL.md`（官方示例技能目录，无索引文件） | 混合：多数 Apache-2.0，`docx`/`pdf`/`pptx`/`xlsx` 为 source-available |
| `composiohq` | [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | ~28 | 扫描**仓库根** `*/SKILL.md`（技能即顶层目录，无索引文件） | 未声明（收录前以各技能来源为准） |
| `coevoskills` | [Zhang-Henry/CoEvoSkills](https://github.com/Zhang-Henry/CoEvoSkills) | 1 | **稀疏 API 取数** `meta_skills/*/SKILL.md`（GitHub trees API 定位子树 + raw 取文件；无索引文件） | Apache-2.0 |
| `mattpocock` | [mattpocock/skills](https://github.com/mattpocock/skills) | 38 | 扫描 `skills/<category>/<name>/SKILL.md`（**两层嵌套**，无索引文件） | MIT |
| `karpathy` | [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) | 1 | 扫描 `skills/*/SKILL.md`（`karpathy-guidelines`，无索引文件） | 无 LICENSE 文件；`SKILL.md` 声明 MIT |

> 同名技能可能出现在多个源（如 `skill-creator`、`brand-guidelines`）：索引按 `source_repo` 区分，检索结果会标注来源。

## 索引说明

每条记录包含：`name` / `path` / `description` / `category` / `risk` / `source` / `source_repo`（来源仓库）/ `date_added` / `tags` / `tools` / 客户端支持（`client_targets`）。

结构信息：`has_script` / `has_references` / `has_examples` / `has_templates` / `body_lines` / `file_count` / `subdirs`。

内含 FTS5 全文检索表 `skills_fts`，支持关键词匹配 name/description/category/tags。

英文/ASCII 查询走 FTS5；名称精确命中优先（连字符/下划线按空格归一），其余按 BM25 排序，name/description/category/tags 权重分别为 8/1/1/2。名称、来源、路径作稳定的平分排序。只有过滤条件时按名称浏览。

FTS5 的 `unicode61` 不切分中文，原文保留 name/description/tags/category 子串 `LIKE` 匹配（空格分词 AND；转义 `%`/`_`）。常见关键词另用离线词表扩展为英文 FTS 查询，例如「代码审查/代码评审」→ `code review`、「单元测试」→ `unit testing`、「性能优化」→ `performance optimization`，中文与英文结果取并集再排序，无需重建索引或联网翻译。

扩展按空格分隔的关键词进行，保留英文限定词；存在未收录的中文限定词时不做部分翻译，避免丢失条件。自然语言长句先提取关键词；未知中文或 0 命中时，执行代理应再用英文/近义词检索。一次 0 命中不能证明上游没有候选。

## 使用

```bash
# 检索全库（默认所有源）
python scripts/skill_index_search.py "debugging"
python scripts/skill_index_search.py "代码审查"
python scripts/skill_index_search.py "代码审查 Python"
python scripts/skill_index_search.py "git push" --category devops --risk safe

# 按源检索（aas / addy / anthropics / composiohq / coevoskills / mattpocock / karpathy）
python scripts/skill_index_search.py "accessibility" --source addy
python scripts/skill_index_search.py "skill creator" --source anthropics
python scripts/skill_index_search.py "skill creator" --source coevoskills
python scripts/skill_index_search.py "code review" --source mattpocock
python scripts/skill_index_search.py "karpathy" --source karpathy

# 查看索引状态（含按源分布）/ 分类分布
python scripts/skill_index_search.py --stats
python scripts/skill_index_search.py --list-categories

# JSON 输出（便于程序化处理）
python scripts/skill_index_search.py "pdf" --json
```

## 构建与更新（多源）

```bash
# 全量重建所有源（默认：下载各源 tarball → 构建 → 自动清理）
python scripts/skill_index_build.py

# 更新某个源并保留其他源
python scripts/skill_index_build.py --source aas --incremental
python scripts/skill_index_build.py --source addy --incremental
python scripts/skill_index_build.py --source anthropics --incremental
python scripts/skill_index_build.py --source composiohq --incremental
python scripts/skill_index_build.py --source coevoskills --incremental
python scripts/skill_index_build.py --source mattpocock --incremental
python scripts/skill_index_build.py --source karpathy --incremental

# 增量同步（推荐日常使用：复用现有 upstream.db，只更新增/改/删项，速度快）
python scripts/skill_index_build.py --incremental

# 从本地已 clone/解压的仓库构建（避免重复下载；需与 --source 单值搭配）
python scripts/skill_index_build.py --source addy --from-extracted <本地仓库目录> --incremental
```

**同步策略：** 手动触发（推荐）。索引文件已提交入仓库，用户克隆即得索引；日常更新上游用 `--incremental`（快），索引结构变更时用完整重建。注意多源全量构建会下载全部源（约 117MB+，`aas` 单源即约 110MB），建议用 `--source <单源>` + `--incremental` 按需同步。

不带 --incremental 的成功完整重建会替换整个索引；若只选择一个源，结果就是单源库。离线保留分支仍按源增量保护已有数据。

**固定来源版本：** 远程同步先把每源 branch 解析为完整 commit SHA，再用同一 SHA 枚举目录、下载 raw 文件或 archive；不会先抓分支文件再补记当时 HEAD。每次构建使用独立临时目录，避免 --keep 或失败遗留文件混入新快照。固定 SHA 解析失败时该源不可用，沿用离线保留策略。

**稀疏取数（`api_subtree`）：** 当上游把技能放在一个超大仓库的小子树里时（`coevoskills` = `Zhang-Henry/CoEvoSkills`：`meta_skills/` 仅约 200KB，整仓却约 600MB 基准数据），整仓 tarball 是约 3000 倍的浪费。此类源在 `SOURCES` 里声明 `api_subtree` + `branch`：构建时用 GitHub trees API 定位子树、按 raw URL 只取该子树文件（`coevoskills` 为 18 个文件），落成一个「形如仓库根」的最小 checkout，后续扫描/结构统计复用同一套逻辑。`--from-extracted` / `--no-dl` 仍按整仓 checkout 语义工作。

**两层嵌套目录（`skills_nested`）：** 默认扫描布局是 `<skills_root>/<name>/SKILL.md`（一层深）；当上游把技能按类别分组到子目录时（`mattpocock` = `mattpocock/skills`：`skills/engineering/<name>/`、`skills/productivity/<name>/` 等），该源声明 `skills_nested: True`，扫描改为 `<skills_root>/<category>/<name>/SKILL.md`，索引 `path` 保留完整相对路径（如 `skills/engineering/code-review`）。当技能 frontmatter 未声明 `category` 时，用其**父目录名**兜底（如 `engineering`）；含 `SKILL.md` 的目录才收录，仅有 README 的目录（如 `deprecated/`）自动跳过。

## 逐源更新状态

索引 v6 在 meta 表的 `source_status:<仓库>` 中记录状态，`skill_index_search.py --stats` 显示：

- `last_success`：该源最后成功写入快照的 UTC 时间；本地 checkout 构建也表示写入时间，不证明远端最新。
- `last_attempt` / `status`：最近尝试时间与 ready/unavailable 状态。失败或扫描空结果时保留旧技能行、上次成功时间与哈希，只更新尝试状态。
- `snapshot_sha256`：该源已索引字段按路径排序后的 SHA-256，用于辨别索引快照；它不是上游 Git 提交号，也不覆盖未索引的文件内容。
- `upstream_commit`：远程下载时实际固定的完整提交号；与索引字段哈希分开。`source_ref` 是解析前的分支，`fetch_mode` 为 archive/sparse/local/unknown。
- --from-extracted / --no-dl 的本地目录统一记 local、提交号 null；不推断远端 HEAD，也不把祖先仓库提交冒认为来源版本。
- 下载失败保留上一成功快照的提交号；本地目录成功覆盖后清空旧的远端提交号，防止把已修改内容关联到旧 SHA。
- 旧版索引缺少逐源记录时显示 unknown；仅在该源下次成功同步后产生记录，不用全局时间回填。局部更新不刷新其他源的成功时间。

全局 `built_at` 仅代表数据库数据更新时间。离线保留策略仍返回 0，自动化需要检查逐源状态才能判断是否全部刷新。
