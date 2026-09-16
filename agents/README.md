# agents/ — 已验证代理库

本目录存放**经验证、可复用**的代理（Agents），是 Personal-AI-Tools 的代理回馈与分发目标位置。

## 准入规则

一个代理进入本目录，必须满足：

1. 有明确的 frontmatter（name/description/mode 等）与可辨识的用途
2. 通过 `validate_agents.py --strict`（frontmatter/职责范围/权限声明/协作协议/完成标准/引用不悬空）：`python agent-creator/skills/agent-creator/scripts/validate_agents.py --strict --dir agents/<name>`
3. 声明验证等级 `maturity`，分两档：
   - `runtime-verified`：在真实任务/目标环境中**试跑验证过**（准入第 2 条）
   - `static-verified`：仅通过静态严格校验、**尚未真实试跑**，待运行时验证后升档
4. 符合各客户端代理定义规范（claude 的 `.claude/agents/`、opencode 的 `agent/*.md` 等）

> `maturity` 是 frontmatter 字段，`agents/CATALOG.md` 由根 `tools/scripts/build_catalog.py` 从各 frontmatter 自动生成，供 LLM 检索时区分「可立即用」与「待验证」；无需手改，新增/改进代理后重跑生成器即可。

## 目录结构约定

代理按 **类别 + layer 分层目录**组织。`academic/` 是**公共/通用代理**（学术研究层）；`code-quality/` 为通用代码质量代理分类。分层由目录结构承载，不再使用 frontmatter `tags`。

```
agents/
├── README.md
├── CATALOG.md             # 能力目录（自动生成：tools/scripts/build_catalog.py，禁止手改）
├── academic/              # 公共通用代理（学术研究层）
│   └── anthropologist/    #   人类学家/地理学家/历史学家/叙事学家/心理学家…
├── code-quality/          # 通用代码质量代理
│   ├── code-reviewer/     #   常驻代码审查（PR/diff 多轴审查）
│   └── code-simplifier/   #   简化重构最近改动
└── <顶层分类>/<agent-name>/   # 其他通用分类代理（kebab-case，与 frontmatter 的 name 一致）
```

## 领域分层（目录约定）

代理的领域分层由**目录结构**表达（不写 frontmatter `tags`）：

- `layer`：代理在协作体中的分层 = `agents/` 下的第一层分类目录（academic / code-quality）
- `domain`：适用域由顶层分类目录表达

示例：`anthropologist` 位于 `agents/academic/`；`code-reviewer` 位于 `agents/code-quality/`。目录放置即分类，无需 `tags` 字段。

## 与 agent-creator 的关系

- 创建/改进/验证代理 → 使用本仓库内代理创建器成品（`agent-creator/skills/agent-creator/`，方法论见其 `SKILL.md`，脚手架 `scripts/create_agent.py`，验证器 `scripts/validate_agents.py`）
- 从本目录安装代理到 LLM 客户端 → **经根 `tools/scripts/install.py` 打包放置**（先按端适配 frontmatter、再落点 + 自检/回滚；落点矩阵见 `tools/README.md`）：
  ```bash
  python tools/scripts/install.py agents/<分类>/<name> --client claude --scope workspace --dest <目标仓库根>
  ```
  落点：claude `~/.claude/agents/`、opencode `~/.config/opencode/agent/`（**单数**）；工作区版本放 `<项目根>/.<客户端>/<agents|agent>/`。纯复制仅作无该脚本时的回退（先 `adapt_agent.py` 转换再复制）。
- 库内 frontmatter **两种形**：`code-quality/` 2 个为仓库规范形（`tools:[...]` 数组）；`academic/` 5 个为 opencode 原生 permission 形（含 `color`/`temperature`/`lsp` 等 opencode-only 字段）。`install.py`/`package_agent.py` 会按目标端适配并 post-check，无需手工转换。
- 代理更新/卸载 → 更新即重装覆盖（`--force`）；卸载即删除目标副本（本仓库无独立 manifest 生命周期工具）。

## 能力目录（CATALOG.md）

`CATALOG.md` 由根 `tools/scripts/build_catalog.py` 从各 `AGENT.md` frontmatter **自动生成**（禁止手改）。它是 LLM 按需安装的检索入口：读目录匹配需求 → 命中即给条目「先 `adapt_agent.py` 转换、再复制到客户端 agents/ 目录」提示，用户确认后执行。新增/删除/改进代理后**重跑生成器刷新**（发布门可用 `python tools/scripts/build_catalog.py --check` 校验）。

## 记录与审计

- `AGENTS-RECORDS.md`：**创建/来源台账**（逐条事实，agent-creator 自动追加）。入库代理用 `python agent-creator/skills/agent-creator/scripts/create_agent.py ... --records agents/AGENTS-RECORDS.md` 追加一行；来源/作者/日期只记在此，不进 `AGENT.md` frontmatter（`version`/`tools_clients` 也不写，版本以 git 提交历史为准）。本库条目采用目录形态（`<分类>/<name>/AGENT.md`），生成时须加 `--layout dir`（脚手架默认输出扁平单文件 `<name>.md`；`install.py` 按 `AGENT.md` 定位条目，扁平形态不会被收录）。
- `AGENTS-AUDIT.md`：**入库合规审计**（人工维护，规则见根 `AGENTS.md`）：新增/改进代理后同步登记。
- agent-creator 是**创建工具**（工作区 + 成品在 `agent-creator/`），不在代理库审计范围内。

## 回馈流程

1. 代理验证通过并稳定使用一段时间
2. frontmatter 保持 `name`/`description`/`mode`/`maturity`（及 `tools`/`permission`）等运行时字段；**不写** `version`/`tools_clients`/`tags`/来源字段；来源信息登记到 `AGENTS-RECORDS.md`
3. 重跑根 `tools/scripts/build_catalog.py` 刷新 `CATALOG.md`
4. 提交到仓库

## 注意

各客户端代理格式有差异（如 opencode 用单文件 .md，claude 也可用单个文件）；入库统一采用**单文件 AGENT.md + 可选子目录**，落地时按目标客户端格式放置。
