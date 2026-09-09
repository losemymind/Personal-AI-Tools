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

代理按 **类别 + layer 分层目录**组织。`academic/` 是**公共/通用代理**（不随 UE 包移动）；`ue-game-studio/` 是 **UE 游戏开发专用安装包**（6 个 layer 子目录，含安装清单 README 与协作规则 AGENTS.md）；`code-quality/` 为通用代码质量代理分类。

```
agents/
├── README.md
├── CATALOG.md             # 能力目录（自动生成：tools/scripts/build_catalog.py，禁止手改）
├── academic/              # 公共通用代理（学术研究层，不随 UE 包移动）
│   └── anthropologist/    #   人类学家/地理学家/历史学家/叙事学家/心理学家…
├── code-quality/          # 通用代码质量代理
│   ├── code-reviewer/     #   常驻代码审查（PR/diff 多轴审查）
│   └── code-simplifier/   #   简化重构最近改动
├── ue-game-studio/        # UE 游戏开发专用安装包
│   ├── AGENTS.md          #   UEGameStudio 项目级协作规则（源 AGENTS.md）
│   ├── README.md          #   安装清单：要装哪些 agent + 冲突处理策略
│   ├── design/            #   设计层（数值/经济/关卡与任务设计）
│   ├── directors/         #   决策层（游戏总设计师/技术总监/制作人/视听总监）
│   ├── orchestration/     #   总控编排层（orchestration-director）
│   ├── production/        #   生产层（资产管理/视觉资产/本地化 LQA）
│   ├── qa/                #   QA 层（合规审计/测试/安全）
│   └── technical/         #   技术层（UE 核心系统/Gameplay/AI/动画/UI/工具管线等）
└── <顶层分类>/<agent-name>/   # 其他通用分类代理（kebab-case，与 frontmatter 的 name 一致）
```

> `ue-game-studio/README.md` 是安装时的**权威清单**：列出该包在 UE 游戏项目中要安装的全部 agent，并引用 `academic/` 公共代理；**安装冲突时必须让用户选择保留哪一个**（本包版本/目标已有/并存改名/跳过），确认前不覆盖目标文件。

## 领域分类（tag 约定）

代理按 **frontmatter `tags`** 表达领域分类，两标签组合：

- `layer`：代理在协作体中的分层（academic / design / directors / orchestration / production / qa / technical）
- `domain`：适用域（统一为 `ue-game-studio`，标识这批代理源自 UEGameStudio 项目组）

示例：`ue-gameplay-engineer` → `tags: [technical, ue-game-studio]`；`game-director` → `tags: [directors, ue-game-studio]`；`anthropologist` → `tags: [academic, ue-game-studio]`。目录放置须与 `layer` 标签一致（`ue-gameplay-engineer` 位于 technical 层下；academic 层内不以 `academic-` 为前缀）。

## 与 agent-creator 的关系

- 创建/改进/验证代理 → 使用本仓库内代理创建器成品（`agent-creator/skills/agent-creator/`，方法论见其 `SKILL.md`，脚手架 `scripts/create_agent.py`，验证器 `scripts/validate_agents.py`）
- 从本目录安装代理到 LLM 客户端 → **先转换 frontmatter、再复制**：用 agent-creator 成品转换器把仓库规范形适配到目标客户端，再把产物放到该客户端 agents/ 目录（落点：claude `~/.claude/agents/`、opencode `~/.config/opencode/agent/`；工作区版本放 `<项目根>/.<客户端>/agents/`）：
  ```bash
  python agent-creator/skills/agent-creator/scripts/adapt_agent.py agents/<name> --client <claude|opencode|codex|deepseek> --out <落点>/AGENT.md
  ```
  `claude`/`opencode` 会自动把 `tools:[...]` 白名单转为该端合法形态并做 post-check（转换失败即退出、不产出无法加载的文件）；`codex`/`deepseek` 无官方 frontmatter schema，YAML 校验后逐字节原样。
- 库内 frontmatter **两种形**：`code-quality/` 2 个为仓库规范形（`tools:[...]` 数组）；`academic/` + `ue-game-studio/` 30 个为 opencode 原生 permission 形（含 `color`/`temperature`/`lsp` 等 opencode-only 字段）。前者落 `claude`/`opencode` 前**必须**先 `adapt_agent.py` 转换；后者按目标端校验后复制（含 opencode-only 字段在其它端被忽略）。
- 代理更新/卸载 → 更新即重新转换复制覆盖；卸载即删除目标副本（本仓库无 manifest 生命周期工具）

## 能力目录（CATALOG.md）

`CATALOG.md` 由根 `tools/scripts/build_catalog.py` 从各 `AGENT.md` frontmatter **自动生成**（禁止手改）。它是 LLM 按需安装的检索入口：读目录匹配需求 → 命中即给条目「先 `adapt_agent.py` 转换、再复制到客户端 agents/ 目录」提示，用户确认后执行。新增/删除/改进代理后**重跑生成器刷新**（发布门可用 `python tools/scripts/build_catalog.py --check` 校验）。

## 审计（AGENTS-AUDIT.md）

本目录随放 `AGENTS-AUDIT.md`（数据来源 + 入库合规的唯一记录，规则见根 `AGENTS.md`）：新增/改进代理后同步登记。agent-creator 是**创建工具**（工作区 + 成品在 `agent-creator/`），不在代理库审计范围内。

## 回馈流程

1. 代理验证通过并稳定使用一段时间
2. 完善 frontmatter 元数据（含 `maturity`）
3. 重跑根 `tools/scripts/build_catalog.py` 刷新 `CATALOG.md`
4. 提交到仓库

## 注意

各客户端代理格式有差异（如 opencode 用单文件 .md，claude 也可用单个文件）；入库统一采用**单文件 AGENT.md + 可选子目录**，落地时按目标客户端格式放置。
