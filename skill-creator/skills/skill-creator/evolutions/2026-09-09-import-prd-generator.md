# 对比记录：prd-generator（本地 A 空） → 上游直接导入 + 适配（B 采用）

## 基本信息
- 日期：2026-09-09（合规闭环补齐本记录；技能导入 `date_added` = 2026-09-07）
- 需求：把「PRD 生成」沉淀为能力库技能 `prd-generator`，数据来源为用户指定的 `https://github.com/snarktank/ralph`（skills/prd）
- 本地候选 A：检索时本仓库 `skills/CATALOG.md` 无 PRD/需求规格类技能（仅 pr-summarizer/code-review-skill，聚焦 PR 摘要与代码审查、不重叠）→ **A 为空**；2026-09-09 复核本技能自带上游索引（aas/addy 共 2132 条）`prd`/`requirements`/`spec` 等关键词 **0 命中** → 索引无候选
- 上游 B：`snarktank/ralph`（MIT，2026-09-09 核 LICENSE）的 `skills/prd/SKILL.md`（英文，单文件，约 300 行；frontmatter 仅 name/description/user-invocable，无 category/risk/source/version 等）

## 对比分析
- 本地无候选（先查后建确认 A 空），无法对比择优，直接按「谁优用谁」采纳上游 B。
- 采纳方式：**方法论吸收 + 中文产品化适配**（上游为方法论单文件，本地重写为自包含中文产品形态），非薄壳非整目录（上游无 resources）。
- 适配要点（本地成品形态 + skill-creator strict 验证入口）：
  1. frontmatter 补齐本地 schema：`name: prd-generator`（kebab + 与目录一致，区别于上游 `prd`）/ `category: product` / `risk: safe` / `source: community` / `version` / `date_added` / `author: https://github.com/snarktank/ralph` / `tags` / `tools`；description 中文、含中英双触发词（创建 PRD/写需求文档/plan this feature/requirements for/spec out）
  2. 补 strict 要求的章节：`## 何时使用此技能`（WHEN_TO_USE，含触发词清单）、`## 示例`（可复制示例，另链上游完整示例）、`## 限制和注意事项`（4 条边界）、`## 安全与安全说明`
  3. 方法论完整保留：接收描述 → 3-5 个字母选项澄清（`1A, 2C, 3B` 速答）→ 9 章节 PRD 模板 → 存 `tasks/prd-[feature-name].md`；验收标准可验证硬约束、UI 故事追加 dev-browser 验证、Non-Goals 边界、**只产出文档不写代码** 全部照单吸收
  4. 正文中文产品化：概述/步骤说明汉化，但 PRD 输出模板章节名保留英文（Introduction/Goals/User Stories/FR/Non-Goals/Success Metrics/…，与上游一致，便于对接英文工具链）
  5. 增补本地「最佳实践 ✅/❌」与「相关技能」节（关联 pr-summarizer），比上游更完整的产品化骨架
- 验证：`validate_skills.py --strict --dir skills/product-design/prd-generator` → **通过**（2026-09-09 能力库 strict 复核：3 技能全绿）。

## 结论
- 入库位置符合规则 4（按功能分类，无「留顶层」例外）：`skills/product-design/prd-generator/`
- 审计登记：`skills/SKILLS-AUDIT.md`（数据来源 = 上游仓库 + LICENSE(MIT) + 上游文件路径）
- 采用确定：**上游 B 方法论吸收 + 本地中文产品化适配（A 空，无择优竞争者）**

## 提炼的学习点
- 直接指定上游仓库的「创建」需求 = 导入适配任务：**单文件方法论型**上游宜「吸收重写 + 补齐本地 schema/章节」，与**整目录语料型**上游（code-review-skill）的导入策略不同——按上游形态选策略
- 上游官方技能 frontmatter 常只有 name/description（无 risk/source/version/date_added）：入库 strict 强制补齐；`source: community` + `author`/审计登记保留归属
- 方法论型技能汉化时：**叙述层本地化、产物模板层保留上游原文结构**，兼顾中文用户与英文工具链
- 上游描述为纯英文触发面：本地 description 需双语触发词，避免中文用户触发失效（与 skill-creator description 纪律一致）
