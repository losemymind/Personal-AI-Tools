# tools 层：仓库级工具与安装编排设计

> 本目录是仓库 **dev-only 工具层**（不随任何成品分发，不属于能力库条目，不受「成品自包含」约束——按设计它可以引用仓库内任意路径）。当前含 `scripts/build_catalog.py`（能力库目录生成器，已实现）与本文档描述的 `scripts/install.py`（安装编排器，**待实现**）。
>
> 本文档是 `install.py` 的权威设计记录；实现后本文档仍作为工具层总览，历史决策保留在文末「设计沿革」。

## 1. 问题陈述

仓库当前把「安装」定义为**纯复制**（根 `AGENTS.md`：把 `skills/<name>` / `agents/<name>` 复制到目标客户端目录）。但客户端适配逻辑其实已经存在——`package_skill.py` / `package_agent.py` 会按端变换 frontmatter 并做 post-check。这导致三个割裂：

1. **适配器只在创建器内，仓库安装库条目时没复用**：库技能/代理直接复制，未走 `package_skill` / `package_agent` 的按端变换。
2. **落点矩阵重复**：global/workspace × 各端的落点表在两份 `INSTALL.md` 与 `agents/README.md` 各写一份，易漂移。
3. ~~**前言约定缺口**~~（**P1 已修复**）：库技能的可选白名单键 `allowed-tools:`（Claude 风格）此前 `package_skill.py` 不认识；现已支持按端映射（见 §7）。

同时用户提出直觉性质疑：`package_skill` **只**放在 `skill-creator` 里「不太合适」——安装库技能、安装两个创建器本身都要用它。

## 2. 现状盘点

| 产物 | 打包器（宿主成品） | 前言关键字段 | 备注 |
|---|---|---|---|
| 库技能 `skills/<分类>/<name>/`（含 `SKILL.md`） | `skill-creator/.../scripts/package_skill.py` | `allowed-tools`=白名单（技能无 `tools`/`tags`/`version`/来源字段：打包前客户端中立） | 5 个：code-review-skill / mcp-builder / ue5-performance-optimization / pr-summarizer / prd-generator |
| 库代理 `agents/<分类>/<name>/`（含 `AGENT.md`） | `agent-creator/.../scripts/package_agent.py` | `tools`=**真白名单**、`permission`=权限图（`tools_clients` 已移除——打包前客户端中立） | 7 个 |
| `skill-creator` 成品 | `package_skill.py`（它自己就是 skill） | 技能 schema（无 `tools`/`tags`/`version`/来源字段） | `skill-creator/skills/skill-creator/` |
| `agent-creator` 成品 | `package_skill.py`（它自己就是 skill，**不是** agent） | 技能 schema（无 `tools`/`tags`/`version`/来源字段） | `agent-creator/skills/agent-creator/` |

**关键不对称（本文档重点记录）**：技能与代理的 `tools` 语义不同——

- **技能**：frontmatter **不再携带 `tools`**（打包前技能客户端中立，支持哪些端是打包器/安装器的职责）；唯一权限声明是可选的白名单键 `allowed-tools`。
- **代理**：`tools` 是「真白名单」；客户端列表（`tools_clients`）已从 frontmatter 移除，多端适配由打包/安装阶段决定。

因此 `package_skill`/`package_agent` 的前言适配**不能互相照搬**，扩展时须各自尊重本侧约定（见 §7）。

## 3. 不可违反的约束

1. **成品即源，不复制**（根 `AGENTS.md` 铁律 1）：打包器只能有一份。
2. **成品必须自包含**（铁律 2）：成品内文档/脚本不得引用本 `tools/` 或别的成品。
3. **两个创建器互不依赖、各自独立可安装**（根 `AGENTS.md` §布局 + `agent-creator/AGENTS.md`）：安装后的 `skill-creator` 必须能给它刚创建的 skill 打包 → **打包器必须随成品分发**。

## 4. 设计决策：分层，不搬迁

**打包器留原地。** 把它们移到 `tools/` 会让成品残缺（违反约束 3）；在成品内再留一份副本违反约束 1；软链在 Windows 与分发场景不可靠。**核心逻辑的少量重复（skill 侧 vs agent 侧）是独立性有意付出的代价**，不抽公共模块。

**新增组合层。** 真正缺失的是「把能力组合起来」的一层。关键认知：

> 创建器本身就是 skill（都有 `SKILL.md`），库技能也是 skill。所以「安装 `skill-creator`」「安装库技能」「给新建 skill 打包」**是同一个操作**——`package_skill(<某 skill 目录>)`；只有 agent 走 `package_agent`。

于是分层为：

| 层 | 归属 | 职责 | 是否随成品分发 |
|---|---|---|---|
| **打包器** | 各创建器成品内（已实现） | 单产物 → 单客户端：frontmatter 变换 + 树复制 + 每端 post-check | 是 |
| **安装编排器** | `tools/scripts/install.py`（待实现） | 跨产物编排 + 落点解析 + 验证关卡 + 缓存清理 | 否（dev-only） |

`install.py` 复用现有打包器（脚本自定位成品根、可从任意 cwd 用绝对路径调用），不复制其逻辑。

## 5. `install.py` 设计

### 5.1 CLI（**已实现**）

```bash
python tools/scripts/install.py <target>... \
    [--all skills|agents] [--creator skill-creator|agent-creator] \
    [--client <claude|opencode|codex|deepseek>]... \
    [--scope global|workspace] [--dest <目标仓库根>] \
    [--artifact auto|skill|agent] [--force] [--zip --out <目录>]
```

- `<target>`：一个目录（含 `SKILL.md` 或 `AGENT.md`）。
- `--all skills|agents`：安装**库条目**（`skills/**` / `agents/**`；不含创建器成品）。
- `--creator`：安装创建器成品（`skill-creator` / `agent-creator`，本身是 skill）。
- `--client`：可重复 / 逗号分隔；**缺省自动检测**「当前使用的客户端」（环境标记 → 工作区配置目录；不探测 home，避免匹配到所有历史安装端）；检测不到则报错 rc=2。
- `--scope`：`global`（默认）或 `workspace`；`workspace` 必须给 `--dest <目标 git 仓库根>`。
- `--artifact`：`auto`（默认）按目录内 `SKILL.md`/`AGENT.md` 自动判定，与 `--artifact` 冲突即报错。
- `--force`：落点已存在时先备份（`<name>.bak`）再覆盖。
- `--zip`：另出压缩包到 `--out/<client>/<name>.zip`（需 `--out`）。

### 5.2 派发（dispatch）

```
target 解析
  ├─ 目录含 SKILL.md  → skill-creator/.../package_skill.py
  ├─ 目录含 AGENT.md  → agent-creator/.../package_agent.py
  ├─ --all skills     → 遍历 skills/** 逐个走 skill 分支
  ├─ --all agents     → 遍历 agents/** 逐个走 agent 分支
  └─ --creator <名>   → 映射到 <creator-workspace>/skills/<名>/（是 skill，走 skill 分支）
```

打包器以 **CLI 子进程**方式**每 (target, client) 一次**调用（隔离失败；保持稳定契约、隔离 sys.path）。定位方式：相对本文件向上到仓库根，再拼各成品 `scripts/` 路径。

### 5.3 落点与放置

打包器输出布局为 `<out>/<client>/<name>/`。`install.py` 流程：

1. 解析客户端**落点基目录**（§6 矩阵；代理落点以 `agents/README.md` 为准）。
2. 调打包器输出到 **staging 临时目录**（已含每端 post-check，坏包不落）。
3. 把 `<staging>/<client>/<name>/` 放置到 `<base>/<name>/`（`--force` 时先备份旧目录）。
4. 清理 `__pycache__/`、`.pytest_cache` 等缓存噪音。

### 5.4 验证关卡

- **通用**：适配后的 SKILL.md/AGENT.md 能被 YAML 解析、`name`/`description` 就位。
- **自带验证器者**：若产物含 `scripts/validate_skills.py`/`validate_agents.py`，放置后跑 `--strict --dir <安装目录>`；失败即**回滚**（删新、还原备份）。**验证器只在产物根部存在其所校验的入口文件时才运行**（`validate_skills.py`→`SKILL.md`、`validate_agents.py`→`AGENT.md`）：`agent-creator` 是技能形态的创建器，虽分发 `validate_agents.py`（用于校验 AGENT 库）但自身无 `AGENT.md`，不得拿它校验创建器目录（见 2026-09-11 沿革）。
- **索引**：若含 `indexes/upstream.db`，跑对应 `search_*_index.py --stats` 核对（创建器成品）。
- 任一项失败 → 该单元不落（回滚），退出码 1；不带病交付。

### 5.5 退出码

| 码 | 含义 |
|---|---|
| 0 | 所有 `target × client` 成功 |
| 1 | 某产物某端打包/放置/验证失败（该单元回滚，其余继续并汇总） |
| 2 | 参数错误（未知 client / workspace 缺 `--dest` / target 无标记 / `--artifact` 冲突 / 检测不到 client / `--zip` 缺 `--out`） |

### 5.6 幂等

同一 `target × client` 重复执行结果一致；默认遇已存在落点**报错并要求 `--force`**，`--force` 走「备份 → 覆盖」。

## 6. 落点矩阵（权威）

**技能**（源自两份 `INSTALL.md` §0）：

| 端 | global | workspace（`<dest>` = 目标 git 仓库根） |
|---|---|---|
| claude | `~/.claude/skills/` | `<dest>/.claude/skills/` |
| opencode | `~/.config/opencode/skills/` | `<dest>/.opencode/skills/` |
| codex | `~/.agents/skills/`（USER 域） | `<dest>/.agents/skills/`（REPO 域） |
| deepseek | `~/.deepseek/skills/`（best-effort，随 harness 版本可能需调整） | `<dest>/.deepseek/skills/`（同左） |

**代理**（权威 = `agents/README.md`；已实现 claude/opencode）：

| 端 | global | workspace |
|---|---|---|
| claude | `~/.claude/agents/` | `<dest>/.claude/agents/` |
| opencode | `~/.config/opencode/agent/`（**单数**） | `<dest>/.opencode/agent/` |
| codex / deepseek | 无文档化代理落点 → 该组合**报错**（不静默） | 同左 |

## 7. 打包器前言适配扩展（**P1 已实现**）

目标：让 `package_skill` 能直接打包**库技能**。约束：**不得放大权限**（缺 `allowed-tools` = 该端全部工具，映射必须显式收紧）。

> 背景更新（2026-09-11）：技能 frontmatter 已移除 `tools`（客户端列表不再进技能本体，技能打包前客户端中立），因此技能侧只剩 `allowed-tools` 一条白名单来源。`package_skill` 的旧 `tools` 客户端标签/白名单分支保留为**回退兼容**，不再是仓库规范形态。

### 7.1 `package_skill.py`（技能侧）— 已实现

| 字段 | claude | opencode | codex/deepseek |
|---|---|---|---|
| `allowed-tools: [Read, Grep, ...]`（Claude 工具名白名单） | 规范化为逗号串（原生键 `allowed-tools` 保留） | 经 `CLAUDE_TO_OPENCODE` 反查为 opencode 工具类 key，合并入逐工具 `permission`（白名单→allow、其余→deny；显式 `permission` 优先；字符串 `permission` 简写丢弃，防放大） | 透传 |
| `tools: [read, grep, ...]`（旧真白名单；回退兼容） | 映射为 Claude 工具名逗号串（现有行为） | 合并入逐工具 `permission`（现有行为） | 透传 |

要点：
- 已新增 `CLAUDE_TO_OPENCODE` 反查表（`Read`→`read`、`Write`→`edit`…），与 `CLAUDE_TOOL_NAMES` 互为逆映射。
- `allowed-tools` 与旧 `tools` 白名单**同时出现**：取并集后映射（claude 折叠到 `allowed-tools`）。
- `allowed-tools` 中若混入客户端标签（异常输入）→ 报错，不静默丢弃。
- `allowed-tools` 值大小写不敏感，claude 端规范化为 canonical 名（`read`→`Read`）。
- 冒烟：真实 `skills/development/code-review-skill` 四端打包通过（claude `allowed-tools: Read, Grep, Glob, Bash, WebFetch`；opencode 逐工具 permission；codex/deepseek 透传）。
- 测试：`skill-creator/tests/test_package_skill.py` 已补 8 例（claude 规范化/字符串形式/大小写、opencode permission 映射/显式优先、客户端标签报错、codex·deepseek 透传）。

### 7.2 `package_agent.py`（代理侧）

代理侧 `tools` 恒为真白名单，无 `tools_clients` 歧义，故**无需** `allowed-tools` 语义。仅需确认：库代理若混入 `allowed-tools` 键，应识别并映射（同 §7.1 规则），而非透传成未知字段。

## 8. 被否决的替代

| 方案 | 否决理由 |
|---|---|
| 把打包器移到 `tools/` | 破坏成品自包含 + 独立可安装（约束 3）；安装后的创建器将无法打包 |
| 成品内保留打包器副本 | 违反铁律 1 |
| 独立 `packager` 成品，两创建器依赖它 | 破坏「互不依赖 / 独立可安装」；否则仍需各自内置副本 |
| 抽 public `packaging` 公共模块 | 同上；跨成品的共享库破坏独立性 |
| 软链/符号链接 | Windows 与分发场景不可靠；且等于变相第二份源 |

## 9. 文档收敛清单（**P3 已完成**）

- [x] 根 `AGENTS.md`：「**安装 = 复制**」→「**安装 = 经 `tools/scripts/install.py` 打包放置**（复制降级为回退）」；命令段加 `python -m pytest tools/tests -q` 与 install 示例；CI 说明补 `tools/tests`。
- [x] 根 `README.md`：结构树补 `tools/`；§使用方式指向 `tools/scripts/install.py`。
- [x] `skill-creator/INSTALL.md`、`agent-creator/INSTALL.md`：§0 顶部注明「优先路径 = `tools/scripts/install.py`，落点矩阵权威见 `tools/README.md` §6；下方复制为回退」。
- [x] `skills/README.md`、`agents/README.md`：安装段改为经 `tools/scripts/install.py`（复制为回退）。
- [x] `.github/workflows/validate.yml`：新增 `tools` job（`python -m pytest tools/tests -q`）。
- [x] **修正**：成品 `SKILL.md`（skill-creator 阶段 9 / agent-creator 阶段 7）**不**引用 `tools/`（铁律 2 自包含），仅描述各自打包器；跨产物编排只写在 dev-only 文档（本文件/根文档）里。
- [x] 版本：成品 frontmatter 已无 `version`——改动以 git 提交 + `evolutions/` 记账。

## 10. 验证计划（已落实）

- `tools/scripts/install.py` 测试在 **`tools/tests/`**（已建）：18 例，覆盖客户端自动检测、落点矩阵（workspace 技能/代理）、`--creator`、`--force` 备份、验证失败回滚、`--artifact` 冲突 / 未知 client / 缺 `--dest` / 无标记 / `--zip` 缺 `--out` 等 rc=2 错误。
- `package_skill` 的 `allowed-tools` 映射用例在 `skill-creator/tests/test_package_skill.py`（+8，已落实）。
- 端到端冒烟：真实 `skills/git/pr-summarizer`、`agents/code-quality/code-reviewer`、`--creator skill-creator` 安装到临时 workspace，落点与自检均通过（已实测）。
- 全绿门槛：`agent-creator` 与 `skill-creator` 各自 `pytest`、两侧 strict、`build_catalog.py --check`、新增 `tools/tests` pytest。

## 11. 分阶段实施

| 阶段 | 内容 | 门 | 状态 |
|---|---|---|---|
| P1 | 扩展 `package_skill` 识别 `allowed-tools`，补 pytest | 单测绿、不放大权限 | ✅ 已完成（2026-09-11） |
| P2 | 新增 `tools/scripts/install.py`（派发 + 落点 + 放置 + 验证 + 清理）+ `tools/tests/` | 新增用例绿 | ✅ 已完成（2026-09-11，18 例） |
| P3 | 文档收敛（§9）+ 端到端冒烟 | 全部发布门全绿 | ✅ 已完成（2026-09-11） |
| P4 | 记 `evolutions/` + 收尾交接 | HANDOFF 就绪 | ✅ 已完成（2026-09-11） |

## 12. 待决项（已定案）

1. 测试归属 → **`tools/tests/`**（已建）。
2. `--client` 缺省 → **自动检测当前使用的客户端**（环境标记 → 工作区配置目录；检测不到报错 rc=2）。
3. deepseek 落点 → **纳入自动落点**（best-effort 约定路径 `~/.deepseek/skills/`）。
4. 代理落点权威 → **以 `agents/README.md` 为准**（本文 §6 交叉引用；codex/deepseek 无代理落点 → 报错）。
5. `--all` 范围 → **仅库条目**；创建器成品用显式 `--creator`。

## 设计沿革

- **2026-09-11（独立性门 + 修复 `--creator agent-creator`）**：新增 `tools/tests/test_creators_independent.py`（零交叉引用扫描：两成品互不出现对端名称与脚本名；无跨成品 import）与两工作区 `tests/test_independence.py`（成品复制到仓库外仍可自校验/自跑工具链）。修复 `install.py` 的 `validate_install`——验证器仅在产物含对应入口文件时运行，`--creator agent-creator` 由此恢复 rc=0（此前误用其分发的 `validate_agents.py` 校验技能形态创建器目录而回滚）；`tools/tests` 补两例。自安装（不依赖 `install.py`）改为**纯文档流程**写进两成品 `SKILL.md`「多客户端安装指引」（LLM 直接执行：定位→落点→复制→自检→清缓存），`INSTALL.md` 仍是 dev-only 手册。
- **2026-09-11（P3/P4 完成）**：文档收敛（根 `AGENTS.md`/`README.md`、两份 `INSTALL.md`、两库 README、CI 新增 tools job）；两创建器 `evolutions/` 各记 `2026-09-11-install-orchestrator.md`。**P1–P4 全部完成。**
- **2026-09-11（P2 实现）**：新增 `tools/scripts/install.py`（完整编排：自动检测客户端 / 派发 / 落点 / staging / 放置 / `--force` 备份 / 自检回滚 / 缓存清理）与 `tools/tests/`（18 例）；§12 五项待决定案。真实库技能/代理/创建器安装冒烟通过。
- **2026-09-11（P1 实现）**：`package_skill.py` 支持 `allowed-tools` 按端映射（claude 规范化逗号串；opencode 经 `CLAUDE_TO_OPENCODE` 反查并入逐工具 `permission`；codex/deepseek 透传）；与旧 `tools` 白名单并集；客户端标签输入报错。补 8 例 pytest；真实库技能四端打包冒烟通过。技能 frontmatter 文档补记 `allowed-tools` 为可选字段。
- **2026-09-11（同日更新）**：代理 frontmatter 亦移除 `tools_clients`/`version`/`tags`——打包前代理客户端中立；来源登记在 `agents/AGENTS-RECORDS.md` 台账（§2 已更新）。`package_agent` 只读 `tools` 白名单，不受影响。
- **2026-09-11（同日更新）**：技能 frontmatter 移除 `tools`——技能打包前客户端中立，支持端不再进技能本体；技能侧唯一白名单键变为 `allowed-tools`（§2/§7.1 已更新）。`package_skill` 的旧 `tools` 分支保留为回退兼容。
- **2026-09-11**：首版。确立「打包器留成品内、新增 `tools/scripts/install.py` 作安装编排层」的分层；记录技能 `tools` vs 代理 `tools_clients` 的语义差异；确认扩展 `package_skill` 支持 `allowed-tools` 映射。**代码未实现，待二审后按 §11 分阶段推进。**
