# 架构：技能 frontmatter 瘦身（移除 tools / tags / version / 来源字段）

## 基本信息
- 日期：2026-09-11
- 版本：skill-creator 0.10.0 → **0.11.2** 系列（方法论/schema 级变更：字段移除 + 验证器放宽 + 新增创建记录账本能力；技能 frontmatter `version` 也随之移除，改以 git 提交记账）
- 触发来源：用户要求「技能 frontmatter 优化」。核心判据：
  1. **打包前技能是客户端中立的**——`tools`（支持客户端列表）是安装/适配阶段才知道的信息，不该进技能本体；
  2. **来源/作者/日期是创建元数据**——不属于技能内容，应集中登记可查询，而非写进每个 `SKILL.md`；
  3. **tags 的「按工作关键词查找技能」功能取消**——不再需要；CATALOG 检索改用 name/description/category；
  4. **version 不进 frontmatter**——生命周期记账改由 git 提交历史 + `evolutions/` 承担；
  5. 要**尽量减小技能内容体积**，frontmatter 只留「打包前必需且客户端中立」的字段。

## 最终 schema
`name` / `description` / `risk` / `category`（移除 `tools`、`tags`、`version`、`author`、`date_added`、`source`、`source_repo`、`source_type`）。

## 改动范围
- frontmatter：`skills/` 5 个库技能 + `skill-creator`/`agent-creator` 两个创建器成品 `SKILL.md` 删除以上字段。
- 验证器 `scripts/validate_skills.py`：删除 `VALID_TOOLS`、`source` 必需、`source_repo`/`source_type`、`date_added` 格式、`tools`/`tags` 形状、`version` 格式等校验与相应常量（`SOURCE_REPO_PATTERN`/`VALID_SOURCE_TYPES`/`DATE_PATTERN`/`VERSION_PATTERN`）。
- `scripts/create_skill.py`：移除 `--tools`/`--version` 与 frontmatter 中的 `source/date_added/author/tools/tags/version`；新增 **创建记录账本** 能力——`--records <文件>` 追加一行（`--author`/`--source`(默认 self)/`--source-repo`/`--method`(默认 created)），不传则只脚手架不写账本。
- 新增库根台账 `skills/SKILL-RECORDS.md`（回填 5 个技能来源行）。
- 目录生成器 `tools/scripts/build_catalog.py`：技能行不再输出 `source`/`date_added`/`tags`/`version`（来源改由台账承载），并重生成 `skills/CATALOG.md`（代理 version/tags 保留）。
- 对比打分 `scripts/compare_skills.py`：`metadata_complete` 字段集改为 `name`/`description`/`risk`/`category`。
- 文档同步：`SKILL.md`（字段规范 + 新增「创建记录账本」小节 + 验证项 + 清单）、`references/skill-template.md`（删「标签规范」节 + version 字段）、`references/skill-anatomy.md`、`references/quality-bar.md`、`references/skill-comparison.md`、`templates/SKILL.template.md`、成品 `README.md`。
- 审计/台账/约定：`skills/SKILLS-AUDIT.md`、`skills/README.md`、根 `AGENTS.md`（技能 frontmatter 约定改为仅 name/description/risk/category；记录入口改为「台账 + 审计」双轨）、两工作区 `AGENTS.md`（版本记账改为 git + evolutions）。

## 设计决策
- **集中账本**（而非每技能伴生记录文件）：`skills/SKILL-RECORDS.md`，`create_skill.py --records` 追加一行，技能本体不增重。
- 台账与审计分工：台账记**逐条创建/来源事实**（可自动追加）；`SKILLS-AUDIT.md` 记**入库合规结论**（人工）。
- **技能 tags 与代理 tags 分离**：技能移除 `tags`；代理 `AGENT.md` 的 `tags`（领域/层级分类，`agents/README.md` 明确其用途）保留，属 agent-creator 域。
- 代理侧 `tools` 不受影响：`AGENT.md` 的 `tools` 是真白名单（另有 `tools_clients`），语义不同，保留。

## 未改动（有意）
- `package_skill.py` 的旧 `tools` 处理分支（回退兼容）；`allowed-tools` 的按端映射与安装编排仍待后续 package 讨论。
- `examples/`（上游学习样本，验证器豁免）；历史 `evolutions/`；`references/skill-index.md`、`build_index.py`/`search_index.py`（上游**索引** schema，非本仓库技能 schema）。
- 代理库 `agents/`（tags/工具白名单属代理域）。

## 验证结果
- `python -m pytest tests/ -q` → **185 passed**
- `python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator` → Checked 1，全绿
- `python skills/skill-creator/scripts/validate_skills.py --strict --dir <仓库>/skills` → Checked 5，全绿
- `python tools/scripts/build_catalog.py --check` → skills/agents 均 up to date
- agent-creator：`pytest tests/ -q` 86 passed；代理库 strict 32 全绿

## 学习点
- **frontmatter 只放「打包前必需且客户端中立」的字段**：支持端、目标路径、权限映射属安装期信息；来源/作者/日期/版本属元数据——都不该常驻技能。
- **检索元数据应服务于实际检索面**：tags 的「按关键词查技能」功能取消后，tags 即为纯冗余，连同其校验/渲染一并移除；CATALOG 靠 name/description/category 已足够匹配。
- **版本记账不一定靠字段**：`version` 字段一旦不参与运行时/触发，就是纯记账；改以 git 提交 + `evolutions/` 记录，技能本体更轻，且不产生「忘记 bump」的漂移。
- **元数据去冗余**：来源信息此前在 frontmatter 与审计文件双写；移除 frontmatter 副本后，单一台账成为事实源，消除漂移。
- **创建即记账**：把「创建记录」做成 `create_skill.py` 的能力（`--records`），使台账随创建动作自动维护，而不是事后手工补。
