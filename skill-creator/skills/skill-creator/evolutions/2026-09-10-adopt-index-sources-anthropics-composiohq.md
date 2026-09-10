# 采纳升级：上游索引新增 anthropics/skills 与 awesome-claude-skills 两个数据源

## 需求与证据

- 用户指定把两个外部技能仓库纳入「先查后建」的上游索引数据源：
  - `https://github.com/anthropics/skills/tree/main/skills`
  - `https://github.com/ComposioHQ/awesome-claude-skills`
- 背景：原索引仅 `aas`（sickn33/agentic-awesome-skills，~2115）与 `addy`（addyosmani/agent-skills，25）两源；官方（anthropics）与高星 awesome-list（ComposioHQ）未覆盖，检索存在盲区。

## 上游来源与结构

| 别名 | 仓库 | 默认分支 | 技能位置 | 索引方式 |
|---|---|---|---|---|
| `anthropics` | `anthropics/skills` | `main` | `skills/*/SKILL.md` | 目录扫描（无官方索引文件） |
| `composiohq` | `ComposioHQ/awesome-claude-skills` | `master` | 仓库根 `*/SKILL.md` | 目录扫描（无官方索引文件） |

- `anthropics/skills`：官方示例技能目录（~19 个），含 `skill-creator`、`docx/pdf/pptx/xlsx`、`mcp-builder` 等；许可混合（多数 Apache-2.0，文档类技能 source-available）。
- `ComposioHQ/awesome-claude-skills`：74k+ star 的 awesome-list 仓库，技能为顶层目录（~28 个），含官方技能分发副本与社区技能；许可未声明（收录前以各技能来源为准）。

## 采纳要点（改了什么、对齐到哪）

- `scripts/build_index.py`：
  - `SOURCES` 注册两新源；`scan_skill_dir` 支持 `skills_root=""`（仓库根扫描，`path` 不带前导 `/`）。
  - `meta.data_source` 由硬编码改为按 `SOURCES` 派生（`data_source_note()`/`sources_meta()`）；`--incremental` 同步刷新 `meta.sources`/`data_source`，并修正此前把 `skill_count` 覆盖为**单源**计数的缺陷（改为 `SELECT COUNT(*)` 全库）。
  - `cleanup_tmp` 加固：临时目录清理改为 best-effort，遇到 Windows 无法 stat/删除的路径（只读/重解析点）跳过而非抛 `PermissionError`（此前会让一次成功的全量构建以非零码退出）。
- `indexes/upstream.db`：全量重建四源 → **2187** 条（aas 2115 + composiohq 28 + addy 25 + anthropics 19）。
- 文档同步：成品 `README.md` 源表、`references/skill-index.md`（表/计数/许可/CLI 示例）、`SKILL.md` 阶段 0「多源」表述、`skill-creator/AGENTS.md` 与 `INSTALL.md` 计数。

## 版本 bump

- skill-creator `0.8.0` → **`0.9.0`**（新增数据源，minor）。

## 验证结果

- `python skills/skill-creator/scripts/search_index.py --stats`：4 源 2187 条。
- `python -m pytest tests/ -q`：全绿。
- 成品 strict 自检全绿。
- DB 抽查：`skill-creator` 出现在 3 个源，`source_repo` 正确区分；`composiohq` 路径无前导 `/`。

## 学习点

- **同名不同源是常态**：官方技能常被 awesome-list 分发副本收录，索引按 `source_repo` 区分即可，不需去重——检索结果标注来源让用户判断。
- **源结构异质需抽象**：源可分为「有官方索引文件（aas）」与「目录扫描」两类，且技能目录既可能在 `skills/` 下、也可能在仓库根。`skills_root=""` + `path` 归一化即可覆盖。
- **清理逻辑也是发布门的一部分**：下载/解压临时目录的清理失败不应污染构建退出码；OS 级不可访问路径必须 best-effort 跳过。
- **派生元数据优于硬编码**：`meta.data_source`/`sources` 从 `SOURCES` 派生后，增源不会漏改元数据。
