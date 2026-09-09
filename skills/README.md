# skills/ — 已验证技能库

本目录存放**经验证、可复用**的技能（Skills），是 Personal-AI-Tools 的技能回馈与分发目标位置。

## 准入规则

一个技能进入本目录，必须满足：

1. 通过自动验证：`python skill-creator/skills/skill-creator/scripts/validate_skills.py --strict --dir skills/<name>`（创建器成品在本仓库 `skill-creator/skills/skill-creator/`）
2. 经过真实任务试跑（skill-creator 阶段 6）
3. 若上游已有同类技能，需完成对比择优并记录到创建器的 `evolutions/`（`skill-creator/skills/skill-creator/evolutions/`）

## 目录结构约定

```
skills/
├── README.md
├── CATALOG.md             # 能力目录（自动生成：tools/scripts/build_catalog.py，禁止手改）
└── <分类>/<skill-name>/   # kebab-case，与 SKILL.md 的 name 一致
    ├── SKILL.md
    ├── scripts/           # 可选：辅助脚本
    ├── references/        # 可选：参考文档
    ├── examples/          # 可选：示例
    └── templates/         # 可选：模板
```

## 与 skill-creator 的关系

- 创建/改进/验证技能 → 使用本仓库内技能创建器成品（`skill-creator/skills/skill-creator/`，方法论见其 `SKILL.md`）
- 从本目录安装技能到 LLM 客户端 → **复制** `skills/<name>` 到客户端 `skills/` 目录（落点：claude `~/.claude/skills/`、opencode `~/.config/opencode/skills/`、codex `~/.agents/skills/`；工作区版本放 `<项目根>/.<客户端>/skills/`）
- 技能更新/卸载 → 更新即重新复制覆盖；卸载即删除目标副本（本仓库无 manifest 生命周期工具）

## 能力目录（CATALOG.md）

`CATALOG.md` 由根 `tools/scripts/build_catalog.py` 从各 `SKILL.md` frontmatter **自动生成**（禁止手改）。它是 LLM 按需安装的检索入口：读目录匹配需求 → 命中即给条目「复制到客户端目录」提示，用户确认后执行。新增/删除/改进技能后**重跑生成器刷新**（发布门可用 `python tools/scripts/build_catalog.py --check` 校验）。

## 审计（SKILLS-AUDIT.md）

本目录随放 `SKILLS-AUDIT.md`（数据来源 + 入库合规的唯一记录，规则见根 `AGENTS.md`）：新增/改进技能后同步登记。skill-creator 是**创建工具**（工作区 + 成品在 `skill-creator/`），不在技能库审计范围内。

## 回馈流程

1. 技能在本目录验证通过并稳定使用一段时间
2. 补充 frontmatter 元数据（source/date_added/author/tags/version）
3. 重跑根 `tools/scripts/build_catalog.py` 刷新 `CATALOG.md`（maturity 等字段照抄 frontmatter）
4. 提交到仓库（含对比择优的 `evolutions/` 记录）
