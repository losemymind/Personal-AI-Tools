# 上游技能索引（Skill Index）

基于多个上游技能仓库构建的本地 SQLite 检索索引，让 skill-creator 在创建前能快速检查"上游是否已有可用技能"（先查后建）。

## 数据来源与规模

| 项 | 值 |
|---|---|
| 索引文件 | `indexes/upstream.db` |
| 技能总数 | ~2130（随上游更新变化） |
| 数据源 | 多源：见下表 |
| 许可 | 各上游仓库 MIT License |

### 上游源

| 别名 | 仓库 | 技能数 | 索引方式 |
|---|---|---|---|
| `aas` | [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills) | ~2100 | 官方 `skills_index.json`（权威元数据）+ 目录扫描补充结构 |
| `addy` | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 25 | 扫描 `skills/*/SKILL.md`（无官方索引文件） |

## 索引说明

每条记录包含：`name` / `path` / `description` / `category` / `risk` / `source` / `source_repo`（来源仓库）/ `date_added` / `tags` / `tools` / 客户端支持（`client_targets`）。

结构信息：`has_script` / `has_references` / `has_examples` / `has_templates` / `body_lines` / `file_count` / `subdirs`。

内含 FTS5 全文检索表 `skills_fts`，支持关键词匹配 name/description/category/tags。

FTS5 的 `unicode61` 分词器不切分中文，因此**含中文（CJK）的查询**由 `search_index.py` 自动降级为对 name/description/tags/category 的子串 `LIKE` 匹配（按空格分词 AND；`%`/`_` 已转义），可直接用中文关键词检索，无需重建索引文件。英文/ASCII 查询仍走 FTS5。

## 使用

```bash
# 检索全库（默认所有源）
python scripts/search_index.py "debugging"
python scripts/search_index.py "git push" --category devops --risk safe

# 按源检索（aas 或 addy）
python scripts/search_index.py "accessibility" --source addy

# 查看索引状态（含按源分布）/ 分类分布
python scripts/search_index.py --stats
python scripts/search_index.py --list-categories

# JSON 输出（便于程序化处理）
python scripts/search_index.py "pdf" --json
```

## 构建与更新（多源）

```bash
# 全量重建所有源（默认：下载各源 tarball → 构建 → 自动清理）
python scripts/build_index.py

# 只重建某个源
python scripts/build_index.py --source aas
python scripts/build_index.py --source addy

# 增量同步（推荐日常使用：复用现有 upstream.db，只更新增/改/删项，速度快）
python scripts/build_index.py --incremental

# 从本地已 clone/解压的仓库构建（避免重复下载；需与 --source 单值搭配）
python scripts/build_index.py --source addy --from-extracted <本地仓库目录>
```

**同步策略：** 手动触发（推荐）。索引文件已提交入仓库，用户克隆即得索引；日常更新上游用 `--incremental`（快），索引结构变更时用完整重建。注意多源全量构建会下载全部源（约 110MB+），建议用 `--source <单源>` + `--incremental` 按需同步。