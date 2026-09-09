---
name: pr-summarizer
description: "将 git diff 转为结构化 PR 总结：一句话摘要、变更分类表、审查清单、风险标注与语义化标题建议。当用户要求总结变更、撰写 PR 描述、review 前梳理 diff、或说「总结我的改动」「写 PR 描述」「PR 摘要」时使用。"
category: git
risk: safe
source: self
version: "0.1.0"
date_added: "2026-09-02"
author: losemymind
tags: [git, pr, summary, review]
tools: [claude, opencode, codex, deepseek]
---

# PR 总结助手（pr-summarizer）

## 概述

将 git diff 转化为**审阅者友好、可快速跳读**的 PR 总结：先给一句话摘要，再用分类表呈现变更，按变更类别动态生成审查清单，显式标注风险与语义化标题建议。定位是「轻量快速总结 + 决策辅助」，而非完整 PR 增强（后者由更重的工具承担）。本技能融合了上游 comprehensive-review-pr-enhance 的分类表/清单/分拆/风险规则精华。

## 何时使用此技能

- 用户要求「总结我的改动」「写 PR 描述」「PR 摘要」「review 前梳理 diff」
- 需要把一段 git diff 变成审阅者能快速理解的结构化总结
- 提交 PR 或请求审查前，需要一份自检清单与风险标注
- 需要为 PR 推荐 conventional commit 风格标题

## 工作原理

### 步骤 1：获取 diff 范围

与用户确认对比基准（默认 `HEAD` 前的当前改动，或指定 `git diff <base>...HEAD`）：

```bash
git diff HEAD --stat          # 改动文件与规模总览
git diff <base>...HEAD --stat # 指定分叉点
```

读 `--stat` 得出：改动文件数、总行数、涉及类别（source/test/config/docs/build）。

### 步骤 2：一句话摘要（优先输出）

用 1-2 句回答：**改了什么、为什么、影响谁**。这是最重要的内容——审阅者先读它，细节靠分类表。

### 步骤 3：生成变更分类表

按文件类别归类（可多文件合并一行）：

```markdown
## Changes
| Category | Files | Key change |
|----------|-------|------------|
| source   | `src/auth.ts` | 新增 OAuth2 PKCE 流程 |
| test     | `tests/auth.test.ts` | 覆盖 token 刷新边界 |
| config   | `.env.example` | 新增 `OAUTH_CLIENT_ID` |
```

分类：`source` / `test` / `config` / `docs` / `build` / `styles`。出现安全敏感路径（auth/crypto/token/password/secret）时在 key change 处标注 🔒。

### 步骤 4：按类别动态生成审查清单

**只**为 diff 中实际出现的类别生成清单项（类别驱动，不盲目铺满）：

- `source`：无调试遗留、函数 <50 行、命名描述性、错误处理完整
- `test`：断言有意义、覆盖边界、无 flaky、AAA 模式
- `config`：无硬编码密钥、环境变量有文档、向后兼容
- `docs`：内容准确、含示例、changelog 已更新
- 安全敏感路径：输入验证、日志无密钥泄漏、授权逻辑正确

### 步骤 5：风险标注与分拆建议

- **Breaking？** 是/否（API 签名、数据格式、依赖大版本变更 → 是）
- **风险级别**：低/中/高 + 原因
- **大型 diff**（>20 文件或 >1000 行）：建议按 feature 分拆：

```bash
git checkout -b feature/part-1
git cherry-pick <commits-for-part-1>
```

### 步骤 6：语义化标题建议（差异化能力）

按 conventional commit 格式给出 1-2 个标题建议：

```markdown
## Suggested Title
feat(auth): 新增 OAuth2 PKCE 登录流程
```

type 推断：新功能 `feat` / 缺陷修复 `fix` / 重构 `refactor` / 文档 `docs` / 性能 `perf` / 测试 `test` / 构建 `build` / 其他 `chore`。scope 从主要改动目录推断。

## 示例

### 示例 1：快速总结（常用）

```text
输入: git diff HEAD --stat（authentication 分支 3 文件）
输出:
一句话摘要: 为登录流程新增 OAuth2 PKCE，修复 token 刷新竞态，补充对应测试。
Changes:
| Category | Files | Key change |
|----------|-------|------------|
| source   | src/auth.ts | 新增 PKCE 流程 🔒 |
| test     | tests/auth.test.ts | 覆盖刷新竞态边界 |
| config   | .env.example | 新增 OAUTH vars |
风险: 中（安全敏感变更，需二次审查）
Suggested Title: feat(auth): 新增 OAuth2 PKCE 登录流程
```

### 示例 2：大型 diff 分拆建议

```text
输入: 28 文件 / 1400 行
输出: 摘要 + 分类表后追加:
大型 diff（28 文件/1400 行）建议按 feature 分拆:
git checkout -b feature/part-1
git cherry-pick <commits-for-part-1>
```

## 最佳实践

- ✅ 摘要永远第一：审阅者 30 秒内应能判断「这是否与我相关」
- ✅ 分类表只写关键变更，不逐文件罗列
- ✅ 审查清单按实际类别生成，没有 test 变更就不给测试清单
- ✅ 标题建议给 1-2 个，带 type 推断理由
- ❌ 不要复制整个 diff 进总结（那是 diff 不是总结）
- ❌ 不要无中生有写测试覆盖或影响范围（只写可验证的）

## 相关技能

- `skill-creator`（技能创建器，本仓库 `skill-creator/skills/skill-creator/`） — 创建/改进本类工作流技能
- `code-reviewer` 代理 — 本技能产出可交代理复检（代理专注多轴质量审查）

## 常见问题

**Q: 用户只要「简单总结一下」？**
A: 输出一句话摘要 + 分类表即可，跳过清单/风险/标题（按需渐进披露）。

**Q: diff 里有安全敏感文件？**
A: 分类表标注 🔒，审查清单加安全类，风险级别至少「中」。

**Q: 与完整 PR 增强工具的区别？**
A: 本技能面向「快速理解与决策」；需要完整 PR 描述（含 Why 段落、测试计划、回滚方案）时建议用重工具或扩展本技能输出模板。

## 限制和注意事项

- 输出质量依赖 git 变更的可读性；二进制/large 生成文件改动难以总结
- 无法代替真正的代码审查——清单辅助自检，不保证无遗漏
- 标题 type 推断基于变更特征，最终由用户确认
- 不适用于非 git 工作流（无 diff 可读）

## 安全与安全说明

- 本技能只读 git 仓库状态，无破坏性操作
- 不向任何外部服务器上传 diff 内容
- 涉及密钥/凭据路径仅标注类别，不输出内容