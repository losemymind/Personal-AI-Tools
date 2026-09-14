# skills/ — 技能创建记录（SKILL-RECORDS）

> 本文件是技能库的**集中创建/来源台账**：由 skill-creator 在创建/导入技能时追加（`create_skill.py --records <本文件>`），每个技能一行。
> 记录各技能的来源与创建元数据；`SKILL.md` frontmatter **只**保留 `name`/`description`/`risk`/`category`（打包前技能客户端中立，来源与版本不进 frontmatter；版本以 git 提交历史为准）。
> 与 `SKILLS-AUDIT.md` 的分工：本台账记**逐条创建/来源事实**（可自动追加）；审计文件记**入库合规结论**（人工维护）。

| 技能 | category | created | author | source | source_repo | method | evolutions |
|---|---|---|---|---|---|---|---|
| pr-summarizer | git | 2026-09-02 | losemymind | self | - | created | 2026-09-02-compare-pr-summarizer.md |
| code-review-skill | development | 2026-09-03 | awesome-skills | community | awesome-skills/code-review-skill | imported | 2026-09-03-import-code-review-skill.md |
| prd-generator | product | 2026-09-07 | https://github.com/snarktank/ralph | community | snarktank/ralph | imported | 2026-09-09-import-prd-generator.md |
| mcp-builder | development | 2026-09-10 | anthropics | community | anthropics/skills | imported | 2026-09-10-import-mcp-builder.md |
| ue5-performance-optimization | game-development | 2026-09-10 | personal-ai-tools | self | - | created | 2026-09-10-compare-ue5-performance-optimization.md |

> `evolutions` 列对应创建器成品 `skill-creator/skills/skill-creator/evolutions/` 中的对比/导入记录文件名。
| coding-discipline | development | 2026-09-14 | losemymind | community | multica-ai/andrej-karpathy-skills | adapted | 2026-09-14-compare-coding-discipline.md |
