# 方法论：AGENT.md frontmatter 瘦身 + 代理创建记录台账

## 基本信息
- 日期：2026-09-11
- 触发来源：用户要求对代理产物做与技能侧一致（`skill-creator`）的改造——AGENT.md frontmatter 移除 `tools_clients`、`version`、`tags`，并新增代理创建记录。
- 对齐：skill-creator 的 `evolutions/2026-09-11-slim-frontmatter.md`（技能 frontmatter 瘦身 + `SKILL-RECORDS.md` 台账）。

## 判据
- **打包前代理客户端中立、内容自足**：`tools_clients`（支持客户端列表）是安装/适配阶段的信息，不该进代理本体；
- **`version` 不参与运行时**：生命周期记账改由 git 提交历史 + `evolutions/` 承担；
- **来源/作者/日期属创建元数据**：集中登记可查询，而非写进每个 `AGENT.md`；
- **`tags` 冗余**：领域分层已由目录结构表达（`agents/<layer>/…`），无需 `tags` 字段；
- `maturity`/`mode`/`tools`/`permission`/`temperature`/`color` 等**运行时字段保留**（代理域语义，与技能侧不同）。

## 改动范围
- **AGENT.md ×32**（`agents/` 全库）：删除 `version: "0.1.0"` 行（32 处）、`tools_clients` 行（2 处）、`tags` 行（32 处）。
- 新增 **`agents/AGENTS-RECORDS.md`** 创建记录台账（32 行，回填）：列 `代理 | mode | created | author | source | source_repo | method | evolutions`。
- `scripts/create_agent.py`：移除 `--version`/`VERSION_PATTERN` 与 frontmatter 中的 `version`/`tools_clients`/`tags`；新增 `--records`（+`--author`/`--source`/`--source-repo`/`--method`）自动追加台账一行，不传则不写。
- `scripts/validate_agents.py`：移除 `version`/`date_added` 校验与 `VERSION_PATTERN`/`DATE_PATTERN` 常量。
- `templates/AGENT.template.md`：删除 `version`/`tools_clients`/`tags` 行。
- `tools/scripts/build_catalog.py`：代理 CATALOG 行不再输出 `version`/`tags`（保留 `mode`/`maturity`）；重生成 `agents/CATALOG.md`。
- 文档：`SKILL.md`（字段规范 + 新增「创建记录账本」+ 验证器项 + 清单 + 版本纪律 + FAQ）、`references/agent-template.md`（示例/字段/矩阵）、`references/agent-quality-bar.md`；库侧 `agents/README.md`（领域分层由目录承载 + 记录与审计段）、`agents/AGENTS-AUDIT.md`（事实源改为台账）、根 `AGENTS.md`（代理记录入口）、`tools/README.md`（安装编排设计中的代理 schema）。
- 测试：`tests/` 六处 fixture 去 `version`/`tools_clients`；`test_create_rejects_bad_version` 替换为 `test_create_records_provenance_ledger` + `test_create_agent_omits_removed_frontmatter_fields`。

## 未改动（有意）
- `package_agent.py`/`adapt_agent.py`：只读 `tools` 白名单，不引用 `tools_clients`/`tags`，无需改动。
- 上游索引 schema（`build_agent_index.py`/`search_agent_index.py` 的 `source_repo` 等）索引外部仓库，保留。
- 代理 `maturity`/`mode`/`permission`/`temperature`/`color`：属代理运行时语义，保留。

## 验证结果
- `python -m pytest tests/ -q` → **87 passed**（86 → 87：+1 台账用例，坏 version 用例替换）
- `python skills/agent-creator/scripts/validate_agents.py --strict --dir <仓库>/agents` → Checked 32，全绿
- `python tools/scripts/build_catalog.py --check` → up to date
- 脚手架冒烟：`create_agent.py --records` 产物 frontmatter 无 `version`/`tools_clients`/`tags`，台账追加正确，strict 通过

## 学习点
- **同构孪生的 schema 改造要区分产物语义**：技能移除 `tools/tags/version`；代理移除 `tools_clients/version/tags`——代理的 `maturity`/`mode`/`permission` 是运行时语义，不能照搬。
- **客户端列表是安装期信息**：`tools_clients` 与技能曾经的 `tools`（客户端标签）同理，应移出本体、交由打包/安装阶段。
- **分类信息优先由目录结构承载**：当目录已能表达分层时，`tags` 只是重复冗余；移除可减少漂移。
- **创建即记账**：`create_agent.py --records` 让台账随创建动作自动维护，与 `create_skill.py --records` 对称。
