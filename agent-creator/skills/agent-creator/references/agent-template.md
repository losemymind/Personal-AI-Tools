# 代理模板（Agent Template）

基于四端客户端（claude/opencode/codex/deepseek-harness）的代理定义规范适配。可复制的骨架见 `templates/AGENT.template.md`（复制后替换占位符）。

## 示例 frontmatter（仓库规范形）

```yaml
---
name: my-reviewer
description: "PR 审查代理：负责代码风格与架构审查，当用户要求审查 PR 或合并请求时被调用。"
mode: subagent
model: anthropic/claude-sonnet-4-6
tools: [read, grep, glob]   # ← 仓库规范：工具白名单清单（数组形式）
permission:
  edit: deny
---
```

**安装时注意事项**：此形是仓库内使用的**规范形式**。安装到不同客户端时必须转换（见下方矩阵与适配规则）。例如 `tools: [...]` 数组形式的列表在 opencode AgentConfig schema（要求 `object<str,bool>`）下会导致加载失败——用 `scripts/adapt_agent.py --client <端>` 自动转换为对应客户端的合法形态。**切勿**将带 `tools: []` 的仓库规范文件直接粘贴到客户端目录。

## 字段说明

**必需字段：**
- `name`：kebab-case，与目录名一致，单行，≤50 字符
- `description`：≤200 字符（验证器上限 300），单行、含「做什么 + 何时被调用」、无 `<`/`>` 占位符（description 是唯一无条件加载的触发面）

**可选字段（按客户端支持程度声明）：**
- `mode`：`primary` / `subagent` / `all`（opencode 语义）
- `model`：`provider/model-id` 格式（opencode/claude 支持）
- `tools`：允许的工具列表（最小权限原则，越少越好）
- `permission`：权限规则（如 `edit: deny`、`bash: ask`）
- `temperature` / `top_p`：采样参数（opencode 支持）

**不进 frontmatter（记于代理库根 `AGENTS-RECORDS.md` 创建记录账本）**：`version`（版本以 git 提交历史为准）、`tools_clients`（多端适配由打包器/安装阶段决定）、`source`/`source_repo`/`author`/`date_added`。打包前代理客户端中立、内容自足。

**代理专属字段（opencode）**：`hidden`（隐藏于 TUI 列表）、`color`、`steps`、`options`、`disable`（禁用内置代理）。

## 四端兼容矩阵

| 字段 | claude | opencode | codex | deepseek |
|---|---|---|---|---|
| `name` | ✅ | ✅ | ⚠️ 文件名即名称 | ⚠️ 随版本 |
| `description` | ✅（触发依据） | ✅（触发依据） | ✅ | ⚠️ 随版本 |
| `mode` | ⚠️ subagent 才有此语义 | ✅ primary/subagent/all | ⚠️ 随版本 | ⚠️ 随版本 |
| `model` | ✅ | ✅ | ✅ | ⚠️ |
| `tools` | ✅（Claude 工具名） | ✅（opencode 工具名） | ⚠️ | ⚠️ |
| `permission` | ✅（Claude 格式） | ✅（opencode 格式） | ⚠️ | ⚠️ |
| `maturity` | 忽略（自定义） | ⚠️ | ⚠️ | ⚠️ |

**兼容策略**：仓库内保持规范形式（`tools: [read, ...]` 数组白名单），**安装时用 `scripts/adapt_agent.py` 做 frontmatter 适配**自动转换为对应客户端的合法形态并执行 post-check：

| 操作 | 效果 |
|---|---|
| opencode | `tools` 数组 → 删除；按列表为相关 permission keys 添加 `allow`，未列入权限 key 添加 `deny`（显式权限条目保留不变）；`tools/object<str,bool>`（已弃用）数组在 schema 层验证会直接失败 |
| claude | `tools` 数组 → 转为逗号分隔字符串（小写名映射为 Claude 工具名，如 `read` → `Read`；未映射名标记丢弃）；`model` 前缀形式（如 `anthropic/claude-sonnet-4-6`）→ 简化为 alias（`sonnet`/`opus`/`haiku`/`inherit`） |
| codex / deepseek | 无官方 agent frontmatter schema → YAML 语法检查通过后逐字节保留 |

任何客户端 post-check 不通过时适配器**拒绝产出/写盘**（fail loudly）。具体转换规则由 `scripts/adapt_agent.py` 实现（移植自 personal-workflow `tools/scripts/agent_format.py`，原为 install/update launcher 的适配层；本仓库无 launcher，故作为复制前的转换步骤）。

**整目录打包**：需要把同一个代理目录一次产出多端（并复制整棵目录、附同名压缩包）时，用 `scripts/package_agent.py <代理目录|AGENT.md> --client <端>… --out <产物目录> [--zip]`（用法见 SKILL.md 阶段 7）。它复用上表的适配与 post-check；注意其 opencode 转换对 `tools` 白名单与 `permission` **字符串简写**并存的情况会**丢弃简写**（保留会放大权限），把白名单物化为逐工具 `permission`——这是相对 `adapt_agent.py` 的权限放大修复。

## 章节要求（AGENT.md 主体）

**必需章节**：角色定位、职责范围（必须做/拒绝做）、工具与权限
**质量门槛要求**：协作协议（含升级路径）、完成标准、限制与边界
**可选章节**：工作方式、相关技能/参考文档

## 质量检查清单

- [ ] name 与目录一致，description 含触发场景
- [ ] 职责范围同时含「必须做 / 拒绝做」
- [ ] 工具最小权限，破坏性动作显式声明或拒绝
- [ ] 有升级路径（何时交还人类）
- [ ] 完成标准可验证
- [ ] 通过 `validate_agents.py --strict`