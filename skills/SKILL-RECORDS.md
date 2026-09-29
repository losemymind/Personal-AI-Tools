# skills/ — 技能创建记录（SKILL-RECORDS）

> 本文件是技能库的**集中创建/来源台账**：由 skill-creator 在创建/导入技能时追加（`skill_create.py --records <本文件>`），每个技能一行。
> 记录各技能的来源与创建元数据；`SKILL.md` frontmatter **只**保留 `name`/`description`/`risk`/`category`（打包前技能客户端中立，来源与版本不进 frontmatter；版本以 git 提交历史为准）。
> 与 `SKILLS-AUDIT.md` 的分工：本台账记**逐条创建/来源事实**（可自动追加）；审计文件记**入库合规结论**（人工维护）。

| 技能 | category | created | author | source | source_repo | method | evolutions |
|---|---|---|---|---|---|---|---|
| pr-summarizer | git | 2026-09-02 | losemymind | self | - | created | [pr-summarizer](../skill-creator/skills/skill-creator/evolutions/library-decisions.md#pr-summarizer) |
| code-review-skill | development | 2026-09-03 | awesome-skills | community | awesome-skills/code-review-skill | imported | [code-review-skill](../skill-creator/skills/skill-creator/evolutions/library-decisions.md#code-review-skill) |
| prd-generator | product | 2026-09-07 | https://github.com/snarktank/ralph | community | snarktank/ralph | imported | [prd-generator](../skill-creator/skills/skill-creator/evolutions/library-decisions.md#prd-generator) |
| mcp-builder | development | 2026-09-10 | anthropics | community | anthropics/skills | imported | [mcp-builder](../skill-creator/skills/skill-creator/evolutions/library-decisions.md#mcp-builder) |
| ue5-performance-optimization | game-development | 2026-09-10 | personal-ai-tools | self | - | created | [ue5-performance-optimization](../skill-creator/skills/skill-creator/evolutions/library-decisions.md#ue5-performance-optimization) |
| coding-discipline | development | 2026-09-14 | losemymind | community | multica-ai/andrej-karpathy-skills | adapted | [coding-discipline](../skill-creator/skills/skill-creator/evolutions/library-decisions.md#coding-discipline) |
| ue-editor-lifecycle | development | 2026-09-15 | losemymind | self | - | created | [ue-editor-lifecycle](../skill-creator/skills/skill-creator/evolutions/library-decisions.md#ue-editor-lifecycle) |

> `evolutions` 列对应创建器成品 `skill-creator/skills/skill-creator/evolutions/` 中的对比/导入摘要及章节锚点。2026-09-29 合并历史记录，来源事实与创建日期保持不变。
