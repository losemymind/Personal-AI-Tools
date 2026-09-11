# skill-creator 安装指引（INSTALL）

> 本文件位于 skill-creator **开发工作区根**，说明如何把**成品** `skills/skill-creator/` 安装到各客户端的技能目录。成品是自包含完整体：安装 = 把该目录完整放置到目标客户端的技能目录，跑完下方验证关卡即完成，不依赖任何外部工具。
> 覆盖已支持的 3 端：**claude / opencode / codex**。deepseek-harness 路径随版本变动，以其当前版本官方文档为准（best-effort，不在本手册范围）。
>
> **优先路径**：仓库内安装直接用根 `tools/scripts/install.py`（自动按端适配 frontmatter + 自检 + 回滚；落点矩阵权威见 `tools/README.md` §6）：
> ```bash
> python tools/scripts/install.py --creator skill-creator --client <claude|opencode|codex> --scope <global|workspace> --dest <目标仓库根>
> ```
> 下方「复制」流程是**无该脚本时的回退**；LLM 客户端也可按成品 `SKILL.md`「多客户端安装指引 → 自安装」直接执行（不使用本仓库工具）。

## 0. 安装作用域（执行前必须询问用户）

| 作用域 | 含义 | 何时选 |
|---|---|---|
| **全局（global）** | 装到用户级目录，所有项目可用 | 想让每个项目都能用创建器 |
| **目标工作区（workspace）** | 装到**目标仓库根**的项目级目录，仅该仓库可用 | 只想在某个项目内启用，或想随项目提交共享 |

落点矩阵（**工作区必须装到 git 仓库根**——三端都从 cwd 向上扫描到仓库根，装进子目录会漏）：

| 端 | 全局 | 工作区 |
|---|---|---|
| claude | `~/.claude/skills/skill-creator/` | `<项目根>/.claude/skills/skill-creator/` |
| opencode | `~/.config/opencode/skills/skill-creator/` | `<项目根>/.opencode/skills/skill-creator/` |
| codex | `~/.agents/skills/skill-creator/`（USER 域） | `<项目根>/.agents/skills/skill-creator/`（REPO 域） |

询问模板：
> 「安装到**全局**（所有项目可用）还是**目标工作区**（仅当前/指定仓库）？默认全局。要装到哪几端？（默认：全部支持的端）」

## 1. 前置自检（安装前，在成品目录内执行）

```bash
cd skills/skill-creator     # 成品目录（在 skill-creator 工作区根执行本手册时）

# 依赖：Python 3 + PyYAML（脚本与验证器依赖）
python -c "import yaml; print('PyYAML OK')"

# 成品目录完整且有效（--dir . = 以本目录为根校验自身）
python scripts/validate_skills.py --strict --dir .
```

完整目录必须包含：`SKILL.md`、`README.md`、`scripts/`（12 个脚本）、`agents/`（grader/comparator/analyzer 三个子代理指令）、`indexes/upstream.db`、`references/`、`templates/`、`examples/`、`evolutions/`。缺任何一项（尤其 `indexes/upstream.db` 与 `examples/`）都会导致安装后方法论不完整。

## 2. 安装（放置目录）

把**成品目录**（`<仓库根>/skill-creator/skills/skill-creator/`）整个复制到第 0 步选定的落点，目录名保持 `skill-creator`。复制时排除 `__pycache__/` 等缓存噪音。

```bash
# Unix / WSL 示例（claude 全局）：从 skill-creator 工作区根执行
cp -r skills/skill-creator ~/.claude/skills/skill-creator

# Windows PowerShell 示例（opencode 工作区，$root = 目标仓库根）：
Copy-Item -Recurse skills/skill-creator "$root\.opencode\skills\skill-creator"
```

若宿主环境提供安装/生命周期工具，可使用它完成复制与记账；手册本身不依赖任何特定工具。

## 3. 验证关卡（全部通过才算安装完成）

进入**安装后**的技能目录逐项执行：

```bash
cd <安装目录>     # 例如 ~/.claude/skills/skill-creator

# 1) 自校验：安装副本在自身位置可通过严格验证（--dir .）
python scripts/validate_skills.py --strict --dir .

# 2) 索引完整性：应显示 4 个来源共 2187 条（离线可用，无需联网）
python scripts/search_index.py --stats

# 3) 关键资源就位
python -c "from pathlib import Path; [print(p, p.exists()) for p in map(Path, ['indexes/upstream.db','references','templates','examples','scripts/validate_skills.py'])]"
```

任一项失败：删除该安装目录，修复来源后重新放置，不要带病交付。

> **验证后清理缓存**：关卡 1 运行验证器会在安装目录内生成 `__pycache__/`。交付前删除它，保持安装副本与源一致（Windows: `Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force`；Unix: `find . -name __pycache__ -type d -exec rm -r {} +`）。

## 4. 交付（重启 + 触发测试 + 告知路径）

1. 提示用户**重启客户端**使技能生效。
2. 用真实请求触发一次（如「帮我创建一个技能」），确认技能被加载、按 SKILL.md 执行。
3. 向用户输出**确切的安装路径**，供后续会话直接引用。

## 安装后的调用范式（代理/用户须知）

本技能内部命令一律以**技能目录为根**书写，脚本可自定位内部资源；客户端只把 SKILL.md 正文交给模型时如何定位技能目录——均见 `SKILL.md`「资源路径基准」，此处不重复。

## 生命周期（客户端中立）

- **更新**：先备份已装目录，再用新版本整目录覆盖（保持目录名 `skill-creator`）。
- **卸载**：删除安装目录（建议先备份）。只删本技能的安装副本，不动其他技能。
- **回滚**：把备份目录复制回原安装位置。

## 注意事项

- **Codex 同名并存**：Codex 内置 `.system/skill-creator`（系统技能）。本技能装到 USER/REPO 域后，选择器中会**同时出现两个**，请选路径在 `~/.agents/skills/`（或项目 `.agents/skills/`）的那个。
- **Opencode 多枢纽**：opencode 除自己的目录外还兼容读 `~/.claude/skills/` 与 `~/.agents/skills/`。同一技能别装多个枢纽，避免重复触发；本手册按端各装一处即可。
- **`~/.codex/skills` 禁写**：那是 Codex 的 SYSTEM 域（内置技能）。
- **工作区扫描方向**：客户端从 cwd 向上扫到仓库根，技能装在子目录会被漏掉——务必装到 git 仓库根。
