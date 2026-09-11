# 技能模板（Skill Template）

基于 agentic-awesome-skills 的 `skill-template.md` 适配。本文件是**字段与规范参考**；可复制的骨架见 `templates/SKILL.template.md`（复制后直接替换占位符）。

## 示例 frontmatter

```yaml
---
name: react-patterns              # 必需：小写-连字符，与目录名完全一致
description: "当用户要求设计 React 组件、实现 hooks 或选择状态管理方案时使用。覆盖组件模式与状态管理最佳实践。"
category: frontend                # 必需：见下方分类列表
risk: safe                        # 必需：见下方风险级别定义
allowed-tools: [Read, Grep, Glob] # 可选：最小权限白名单（Claude 工具名）
---
```

## 字段说明

**必需字段：**
- `name`：kebab-case（小写-连字符），与目录名完全一致，≤100 字符，单行
- `description`：≤1024 字符（验证器上限 1024），**触发场景优先**（「何时用/Use when」开头 + 触发关键词前置）+ 一句能力定位；**不写执行步骤/流程摘要**（写法的实证原因见 SKILL.md「读取规则」中的写作规律文档 §6）；单行
- `category`：见下方分类列表
- `risk`：`none` / `safe` / `critical` / `offensive` / `unknown` 之一（新技能避免 `unknown`）

**可选字段：**
- `allowed-tools`：最小权限白名单（Claude 工具名列表，如 `[Read, Grep, Glob, Bash, WebFetch]`）。只有需要限制工具的技能才写；不写 = 该端不限制。打包时按端映射（claude 保留、opencode 反查为逐工具 `permission`、codex/deepseek 透传；见阶段 9）。

**来源/作者/日期/版本不进 frontmatter**：打包前技能**客户端中立、内容自足**，`source`/`source_repo`/`source_type`/`author`/`date_added`/`version` 一律不写 `SKILL.md`，来源与创建元数据集中登记在技能库根的**创建记录账本**（`create_skill.py --records` 追加；见 SKILL.md「创建记录账本」），版本以 git 提交历史为准。

## 技能分类列表

- **开发类**：`development` `frontend` `backend` `mobile` `testing` `devops`
- **架构类**：`architecture` `design` `database` `api`
- **安全类**：`security` `pen-testing` `compliance` `cryptography`
- **AI 类**：`ai` `machine-learning` `prompt-engineering` `data-science`
- **工具类**：`git` `productivity` `documentation` `deployment`
- **业务类**：`product` `planning` `communication` `research`

## 风险级别定义

- `none` — 纯文本/推理，无命令或状态变更（例：头脑风暴）
- `safe` — 代码审查、设计建议、文档编写、只读命令（多数指导类技能用此级）
- `critical` — 修改状态、删除文件、推送生产环境、自动化脚本执行
- `offensive` — 渗透测试/红队工具，**必须**含「仅限授权使用」警告与强制用户确认门
- `unknown` — 遗留/未分类；新技能应避免，除非确需维护者分流

## 章节要求

**必需章节：** 概述、何时使用此技能、工作原理
**质量门槛要求章节：** 示例、限制和注意事项（自动验证器检查）
**可选章节：** 最佳实践、相关技能、常见问题、安全与安全说明（高风险/命令类才需要）

## 写作指南

- 用清晰直接的动作动词：「创建文件…」「在继续之前检查…」，不用「应该被创建」「您可能要考虑」
- 解释每个指令的**为什么**，而不是堆砌大写 MUST/NEVER
- 示例具体、可直接复制；可标注 输入 → 输出
- 定义输出格式时直接给固定模板
- 用「渐进式披露」组织：`## 基本用法`（常见场景）+ `## 高级用法`（复杂场景）
- 从通用模式出发，不要过拟合到狭窄例证
- `description` 说「何时触发」，正文写「怎么执行」——不要对调

## 质量检查清单（提交前逐项核对）

**元数据：**
- [ ] frontmatter 是有效 YAML，`name` 小写-连字符且与目录名一致
- [ ] `description` ≤1024 字符，触发场景优先 + 一句能力定位，无步骤流程摘要
- [ ] `risk` / `category` 已声明；**无** `source`/`date_added`/`author`/`tags`/`version`（来源进创建记录账本，版本以 git 为准）

**内容质量：**
- [ ] 指令清晰、可操作（祈使句、动作动词）
- [ ] 有明确的「何时使用此技能」触发说明
- [ ] 至少有 1 个可复制粘贴的示例
- [ ] 列出了限制和注意事项（已知边缘情况 / 做不到的事）
- [ ] 表述形式与基线失败类型匹配（判定规则见 `SKILL.md`「读取规则」中写作规律文档）
- [ ] 技术准确性已验证，无拼写错误

**可用性：**
- [ ] 初学者能按步骤执行
- [ ] 解决一个真实问题，而非空泛建议
- [ ] 不依赖超窄的具体例证（避免过拟合到测试用例）
- [ ] 涉及命令/安装的内容通过安全审查（无 `curl ... | bash` 等管道，无明文密钥示例）

## 提交指南

- 目录名 = 技能名（小写-连字符），文件名固定为 `SKILL.md`
- 目录结构：按功能归入分类 `<分类>/<skill-name>/SKILL.md`（规则 4；分类不存在先创建）+ `examples/` `scripts/` `templates/` `references/`（可选）
- 运行验证：`python scripts/validate_skills.py`（或 `--strict`）
- 验证通过 + 真实任务试跑通过后才提交到仓库 `skills/`