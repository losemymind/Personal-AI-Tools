# 架构：agent-creator 成品 frontmatter 瘦身（移除 tools / tags / version / 来源字段）

## 基本信息
- 日期：2026-09-11
- 版本：agent-creator 0.8.0 → **0.8.4** 系列（四轮 patch：移除 `tools`、`source`/`date_added`/`author`、`tags`、`version`）
- 触发来源：与 skill-creator 同 schema——创建器成品自身作为**技能**，其 frontmatter 应与技能 schema 一致（打包前客户端中立；来源/作者/日期进台账，tags 检索功能取消，版本以 git 记账）。对齐 skill-creator 同期改动（`evolutions/2026-09-11-slim-frontmatter.md`）。

## 改动范围
- 仅改 `skills/agent-creator/SKILL.md` 自身 frontmatter：移除 `tools`、`source`、`date_added`、`author`、`tags`、`version`。最终保留 `name`/`description`/`category`/`risk`。
- **代理侧完全不受影响**：`AGENT.md` 的 `tools` 是真白名单（`tools_clients` 另表客户端）、`version`、`tags`（领域/层级分类）与 `references/`、`templates/AGENT.template.md`、`SKILL.md` 正文中代理规则、`package_agent.py`/`adapt_agent.py` 行为全部保留。

## 验证结果
- `python -m pytest tests/ -q` → **86 passed**（含成品自包含/布局断言）
- `python skills/agent-creator/scripts/validate_agents.py --strict --dir <仓库>/agents` → Checked 32，全绿（代理库不受影响）
- `python tools/scripts/build_catalog.py --check` → up to date

## 学习点
- 创建器成品自身是「技能」，其 frontmatter 应与 skill-creator 定义的技能 schema 保持一致；但创建器**所生产的产物**（`AGENT.md`）有各自 schema，两者不可混淆——改自身 frontmatter 不得波及产物契约。
