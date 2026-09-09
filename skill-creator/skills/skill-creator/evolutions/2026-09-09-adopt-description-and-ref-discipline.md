# 对比记录：description 即唯一触发面 + references 引用纪律（借鉴反馈闭环）

## 基本信息
- 日期：2026-09-09
- 需求：把「description 是唯一始终加载的触发面」落实为硬约束，并给 references 引用纪律定量化阈值——本地是否吸收
- 上游来源：`https://github.com/anthropics/skills`（`skills/skill-creator/`；与 antongulin/opencode-skill-creator 的 description 规范同源，Apache-2.0）
- 前情：本地已把 description 写成「触发场景优先、禁流程摘要」（2026-09-03 superpowers 写作规律吸收），且 validate 已查 ≤1024 字符；但未把约束推成「唯一门面」级硬规则，references 引用纪律也未量化

## 对比报告
- **本地现状**：description 触发优先已落实；正文仍允许并推荐「何时使用此技能」章节（validate 强制要求存在）——对多客户端生态合理（正文触发后确认范围）；references 链接只查悬空，未约束层级/长度。
- **上游增量（本次评估）**：
  1. **description 硬约束**：≤1024 字符、禁 `<`/`>` 占位符、触发面必须自足（正文禁重复 when-to-use 担当触发职责）。
  2. **references 引用纪律量化**：references 只允许从 SKILL.md **一层深**引用、禁止嵌套；单文件 >100 行顶部加目录；超大文件（>10k 词）在 SKILL.md 附 **grep 模式** 便于定位。

## 结论
- **部分采纳**（适配本地多客户端生态，不整套照搬）：
  - description：保留正文「何时使用」章节（claude/opencode/codex 在 body 加载后依赖它确认范围，validate 已强制），但把 description 提升为「**唯一始终在上下文的触发面**」——必须自足覆盖触发场景，禁尖括号占位、禁流程摘要、≤1024 硬上限。
  - references 纪律：采纳「一层深 + >100 行加目录」为推荐硬规则；SKILL.md 自身与 skill-writing-guide 同步示例。
  - validate：description 增「含尖括号占位/跨行」为 advisory（不改库门禁）。

## 提炼的学习点（已用于改进 skill-creator）
- description 是**唯一无条件加载**的字段：它既要当触发面也要当技能目录的「用途」渲染源——把它写成「完整触发描述」，不要依赖 body 兜底。
- references 引用图越扁平越好：一层深链接让「按需加载」的路径可预期，嵌套引用把渐进披露重新变成迷宫。
- 大文件加目录 + 给 grep 模式，是让 LLM「跳过读全文直接定位」的关键设施。

## 改进建议
- 无（纪律已并入 SKILL.md 与 writing-guide；如后续出现 references 深层嵌套违规，再考虑进 validate 硬门禁）。
