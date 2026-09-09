# 上游代理索引（Agent Index）

基于多个上游代理仓库构建的本地 SQLite 检索索引，让 agent-creator 在创建前能快速检查"上游是否已有可用代理"（先查后建）。

## 数据来源与规模

| 项 | 值 |
|---|---|
| 索引文件 | `indexes/upstream.db` |
| 代理总数 | ~570（随上游更新变化） |
| 数据源 | 多源：见下表 |
| 许可 | 各上游仓库自身 License |

### 上游源

| 别名 | 仓库 | 代理数 | 索引方式 |
|---|---|---|---|
| `agency` | [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | ~258 | 扫描顶层 division 目录下的 `*.md` 代理定义 |
| `ccgs` | [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) | ~50 | 扫描 `.claude/agents/*.md`（Claude Code 子代理） |
| `agency-zh` | [jnMetaCode/agency-agents-zh](https://github.com/jnMetaCode/agency-agents-zh) | ~261 | 同 agency 布局的中文版（含 company/hr/legal/supply-chain 等特有 division） |

> 三个上游仓库都**没有统一官方索引文件**，因此全部用"扫描 frontmatter 代理定义"方式发现（与 skill 源中 addy 的处理一致）。非代理目录（examples/、scripts/、integrations/、strategy/、assets/、CCGS Skill Testing Framework 等）与无 frontmatter 的说明类 `.md` 均被排除。

## 索引说明

每条记录包含：`name` / `path`（仓库内相对路径）/ `description` / `category`（division 或分类，agency 系）/ `tools` / `model` / `source_repo` / `body_lines`。

- 三源命名与字段体系不同：`agency` 英文名 + description + emoji/color/vibe；`ccgs` 用 kebab-case name + description + tools/model/maxTurns；`agency-zh` 中文名+中文描述。索引统一收敛到上述公共字段。
- `path` 在单个源内唯一（增量同步按 `source_repo + path` 定位）。
- 内含 FTS5 全文检索表 `agents_fts`，匹配 name/description/category/tools。

FTS5 的 `unicode61` 分词器不切分中文，因此**含中文（CJK）的查询**由 `search_agent_index.py` 自动降级为对 name/description/category/tools 的子串 `LIKE` 匹配（按空格分词 AND；`%`/`_` 已转义），可直接用中文检索 `agency-zh` 的中文代理。英文/ASCII 查询仍走 FTS5。

## 使用

```bash
# 检索全库（默认所有源）
python scripts/search_agent_index.py "code review"
python scripts/search_agent_index.py "code review" --category security

# 按源检索
python scripts/search_agent_index.py "frontend" --source agency
python scripts/search_agent_index.py "前端" --source agency-zh
python scripts/search_agent_index.py "programmer" --source ccgs

# 查看索引状态（含按源分布）/ 分类分布
python scripts/search_agent_index.py --stats
python scripts/search_agent_index.py --list-categories

# JSON 输出（便于程序化处理）
python scripts/search_agent_index.py "review" --json
```

## 构建与更新（多源）

```bash
# 全量重建所有源（默认：下载各源 tarball → 构建 → 自动清理）
python scripts/build_agent_index.py

# 只重建某个源
python scripts/build_agent_index.py --source agency
python scripts/build_agent_index.py --source ccgs
python scripts/build_agent_index.py --source agency-zh

# 从本地已 clone/解压的仓库构建（避免重复下载；需与 --source 单值搭配）
python scripts/build_agent_index.py --source agency --from-extracted <本地仓库目录>
```

**同步策略：** 手动触发（推荐）。索引文件已提交入仓库，用户克隆即得索引；日常更新上游用 `--source <单源>` 按需同步。结构变更（新增/改名源）时用全量重建。注意构建会下载源 tarball，网络不可用时用 `--from-extracted` 指向本地 checkout。
