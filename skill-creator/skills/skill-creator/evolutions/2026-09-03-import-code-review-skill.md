# 对比记录：code-review-skill（本地 A 空） → 上游直接导入（B 采用）

## 基本信息
- 日期：2026-09-03
- 需求：创建 `code-review-skill`，数据来源为用户指定的 `https://github.com/awesome-skills/code-review-skill`
- 本地候选 A：仓库 `skills/CATALOG.md` 无 code-review 类技能（仅有 `pr-summarizer`，聚焦 PR 摘要、不重叠）→ **A 为空**
- 上游 B：`awesome-skills/code-review-skill`（MIT，1.9k star；SKILL.md ~232 行 + `reference/` 26 语言指南 + `cross-cutting/` 5 篇 + `assets/` + `scripts/pr-analyzer.py`，共 ~50 文件 / ~848KB）

## 对比分析
- 本地无候选（先查后建确认 A 空），无法与上游对比择优，直接按「谁优用谁」采纳上游 B。
- 采纳方式：**整目录导入 + 本地 schema 适配**，非自建薄壳（避免 21k 行参考语料旁置）。
- 适配要点（skill-creator 验证入口强制）：
  1. frontmatter 补齐本地 schema：`category: development` / `risk: safe` / `source: community` / `source_repo` / `source_type` / `version` / `date_added` / `tags` / `tools`，description 上限 1024 字符（本次调整后），写入完整触发词（20+ 语言/框架 + review/PR/security/architecture/performance）
  2. 补 `## Examples`（3 个可复制流程示例）与 `## Limitations and Considerations`（7 条边界）章节——上游原文缺此二者，strict 验证要求
  3. 保留 `allowed-tools` 与全部正文（四阶段流程/严重性分级/渐进式加载表），`LICENSE` 一并入库保留归属
  4. 顶层网页脚手架（`.hive/`、`index.html`、`index.en.html`、`CONTRIBUTING.md`、`.nojekyll`、`.gitignore`）不入库
- 验证：`validate_skills.py --strict --dir skills/development/code-review-skill` → **通过**；CATALOG 重建，install 命令可用。

## 结论
- 入库位置符合规则 4（按功能分类）：`skills/development/code-review-skill/`
- 审计登记：`skills/SKILLS-AUDIT.md`（数据来源 = 上游仓库地址 + 条目形态）
- 采用确定：**上游 B 整目录导入（本地 A 空，无择优竞争者）**

## 提炼的学习点
- 直接指定上游仓库的「创建」需求 = 导入适配任务：整目录导入优于只抄 SKILL.md（避免悬空引用、保留渐进式披露语料价值）
- 上游优质技能常缺 `Examples`/`Limitations` 显式章节：入库 strict 验证会拦下，需按本地质量条补齐
- frontmatter `description` 是验证与触发的双重门：压缩至规范内仍须保留全部触发词（review/PR/security/architecture/performance）