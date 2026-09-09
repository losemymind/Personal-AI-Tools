# 对比记录：skill-creator（本地） vs writing-skills（obra/superpowers 上游）

## 基本信息
- 日期：2026-09-03
- 需求：评估 `obra/superpowers/skills/writing-skills/SKILL.md`（社区「写技能的技能」）是否有可反哺本地 skill-creator 的内容
- 上游来源：`https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md`
- 评估方式：本地方法论逐节比对上游独有/实证支撑项 → 判定 A-G 七项可反哺 → 用户选「完整采纳」（含 E 描述规范 + F @ 修正）

## 上游独有且被采纳的维度
- **A. RED-GREEN-REFACTOR + Iron Law**：技能写作 = 对过程文档做 TDD；先无技能跑基线看失败（verbatim 记录借口）→ 写只针对失败的最小正文 → 重测补漏。本地阶段 6 有 baseline 对比与量化基准（aggregate_benchmark），但缺「基线必须先于写作」的强制序。
- **B. 表述形式匹配失败类型（核心实证）**：违规→禁止+借口表；输出形状错→正面配方（禁止清单会反噬、实测比无指导更差）；漏必需元素→模板 REQUIRED 槽；条件行为→可观察谓词。加 nuance/豁免子句会重新打开谈判。
- **C. Bulletproofing（纪律型）**：封死漏洞变体 / 借口表 / 红旗清单 / 「违字即违神」/ 违规症状写进 description。
- **D. 措辞微测**：fresh-context 单样本、必带 no-guidance 对照、每变体 ≥5 次、人工逐条核验、方差即指标——先于全量压力场景。
- **E. description = 何时用，不是做什么**：总结流程的描述让 agent 走捷径跳过正文（对照实证）。
- **F. 禁止 `@` 引用技能**（force-load 烧上下文），改 `**REQUIRED:**` 显式标记。
- **G. 取舍**：regex/校验可自动强制的机械约束不做技能（自动化它，文档留给判断）；Technique/Pattern/Reference 三型分别测。

## 本地化调整（不盲抄）
- E 与本仓库 CATALOG 设计有张力（CATALOG 用 description 渲染「用途」列）→ 折中：description 触发场景优先 + 允许一句能力定位，**但不写步骤/流程阶段摘要**（保住上游实证核心）。
- F 落地：清掉本地方法论/模板/既有技能中的 `@other-skill`/`@skill-creator`（skill-creator SKILL.md 结构样例、SKILL.template.md、skill-anatomy.md 交叉引用节、pr-summarizer 相关技能节）。
- 工具层不重复：本地已有 run_eval/run_loop/aggregate_benchmark（触发+增益量化），只补「纪律闸门」与方法论。

## 产出
- 新增 `references/skill-writing-guide.md`（A-G 完整方法论，本地化细则）
- `SKILL.md`：核心理念新增「先失败后写 + 表述匹配失败类型」小节；读取规则补新 reference；description 指南（E）；结构样例相关技能禁 @（F）；阶段 6 补 Iron Law 纪律块；阶段 9 归档路径改 `skills/<分类>/<name>/`（规则 4）；质量检查清单补 E/F/形式匹配/防借口项
- `references/quality-bar.md`：description 定义（E）+ 新增「写作规律」检查项 7
- `references/skill-template.md` / `references/skill-anatomy.md` / `templates/SKILL.template.md`：description 写法、@ 修正、目录结构规则 4 对齐
- 验证：`validate_skills.py --strict --dir skill-creator`（及 skills）通过；pytest 通过

## 提炼的学习点
- 上游技能写作方法论（尤其「表述形式匹配失败类型」）是**有对照实验支撑**的通用规律，非特定生态意见——值得整块反哺本地，且与本地 quant eval 工具互补（工具量化触发/增益，上游补写作纪律与措辞形式）
- description 的「做什么 vs 何时用」之争不是非此即彼：仓库目录驱动（CATALOG 渲染用途）与触发质量可并存——触发为主、一句定位为辅、禁流程摘要
- 采纳「上游更优」时不等于照抄正文：把可复用规律提炼成独立 reference（渐进式披露），正文只留指针，符合本技能自身方法论