---
name: prd-generator
description: "将用户需求转化为结构化 PRD（Product Requirements Document）：接收功能描述 → 交互式澄清问题 → 生成完整章节文档。当用户要求『创建 PRD』『写需求文档』或说 plan this feature、requirements for spec out 时使用。"
category: product
risk: safe
source: community
version: "0.1.0"
date_added: "2026-09-07"
author: https://github.com/snarktank/ralph
tags: [prd, requirements, feature-spec, planning]
tools: [claude, opencode, codex, deepseek]
---

# PRD Generator（prd-generator）

## 概述

将用户需求转化为结构化 PRD（Product Requirements Document），使文档清晰、可操作、适合直接实施。核心工作流：接收功能描述 → 交互式澄清（字母选项快速回复）→ 生成完整章节 PRD → 保存到 tasks/ 目录下 prd-[特色名称].md 格式。定位是「轻量交互式需求规格化」，而非代码实现——**不开始编写产品代码**。本技能源自 [snarktank/ralph](https://github.com/snarktank/ralph/skills/prd)。

## 何时使用此技能

- 用户要求「创建 PRD」「写需求文档」「spec out 一个功能」
- 需要把一个模糊的功能想法结构化为一开发者可执行的需求文档
- 项目启动前或新功能规划阶段，需要明确范围、边界和验收标准
- 触发词：create a prd, write prd for, plan this feature, requirements for, spec out

## 工作原理

### 步骤 1：接收功能描述

让用户提供想规划的功能/产品的大致描述。如果描述已有充分信息，直接进入澄清；否则先补充背景。

### 步骤 2：交互式澄清（关键）

提出 3-5 个核心澄清问题，聚焦于：
- **Problem/Goal：** 这个特性解决什么问题？
- **Core Functionality：** 关键操作是什么？
- **Scope/Boundaries：** 什么**不**包括？
- **Success Criteria：** 怎样算完成？

**格式示例：**
```
1. 主要目标是什么？
   A. 改善新手用户引导体验
   B. 提高用户留存率
   C. 减少客服负担
   D. 其他：[请注明]

2. 目标用户是？
   A. 仅新用户
   B. 仅现有用户
   C. 所有用户
```

让用户用 `1A, 2B, 3C` 格式快速回复。

### 步骤 3：生成 PRD

基于回答按以下模板输出完整 PRD：

#### 1. Introduction/Overview
功能简要描述与解决的问题。

#### 2. Goals
具体的、可度量的目标（列表）。

#### 3. User Stories
每条故事包含：
- **Title：** 简短描述性名称
- **Description：** "作为一名 [用户]，我想要 [功能] 以便 [收益]"
- **Acceptance Criteria：** 可验证的检查清单

```markdown
### US-001: [标题]
**Description:** 作为 [用户]，我想要 [功能] 以便 [收益]。

**验收标准：**
- [ ] 具体可验证标准
- [ ] 类型检查通过
- [ ] **[UI 相关故事]** 使用浏览器验证
```

要求：
- 验收标准必须可验证（"Shows confirmation dialog before deleting" OK；"Works correctly" NO）
- **任何有 UI 变更的故事：** 追加 "Verify in browser using dev-browser skill"

#### 4. Functional Requirements
编号列表：
- `FR-1: The system must allow users to...`
- `FR-2: When a user clicks X, the system must...`

#### 5. Non-Goals (Out of Scope)
该特性**不会**包含的内容。对范围控制至关重要。

#### 6. Design Considerations (可选)
- UI/UX 要求
- 链接到 mockup（如有）
- 需要复用的现有组件

#### 7. Technical Considerations (可选)
- 已知约束或依赖
- 集成点
- 性能要求

#### 8. Success Metrics
如何衡量成功：
- "减少 X 操作耗时 50%"
- "提升转化率 10%"

#### 9. Open Questions
待解决的疑问。

### 步骤 4：保存 PRD

输出到 'tasks/' 目录，文件名格式：'prd-[feature-name].md'（kebab-case）。

**重要：** **不要开始实施。** 只生成 PRD 文档。

## Writing for Junior Developers

PRD 阅读者可能是初级开发者或 AI Agent。因此：
- 明确且不歧义
- 避免行话或解释清楚
- 提供足够细节理解目的和核心逻辑
- 编号需求便于引用
- 使用具体示例

## 示例

### 示例 1：Task Priority System（简化 PRD）

```markdown
# PRD: Task Priority System

## Introduction

Add priority levels to tasks so users can focus on what matters most.

## Goals

- Allow assigning priority (high/medium/low) to any task
- Provide clear visual differentiation between priority levels
- Enable filtering and sorting by priority

## User Stories

### US-001: Add priority field to database
**Description:** 作为开发者，我需要存储任务优先级使其跨会话持久化。

**验收标准：**
- [ ] 添加 `priority` 列到 tasks 表：'high' | 'medium' | 'low'（默认 'medium'）
- [ ] Migration 成功执行
- [ ] 类型检查通过

### US-002: Display priority indicator on task cards
**Description:** 作为用户，我想一眼看到任务优先级。

**验收标准：**
- [ ] 每个任务卡片显示彩色优先级徽章（red=high, yellow=medium, gray=low）
- [ ] 悬浮或点击时不需额外查看
- [ ] 类型检查通过
- [ ] 使用 dev-browser skill 验证

## Functional Requirements

- FR-1: 添加 `priority` 字段到 tasks 表（'high'|'medium'|'low', 默认 'medium')）
- FR-2: 每个任务卡片显示彩色优先级徽章
- FR-3: 任务编辑模态框包含优先级下拉选择器
```

见 [完整示例](https://github.com/snarktank/ralph/blob/main/skills/prd/SKILL.md) 的 Task Priority System。

## 检查清单（保存前）

- [ ] 已用字母选项提问并获取回答
- [ ] 用户故事具体且可验证
- [ ] 功能需求编号且不歧义
- [ ] Non-goals 章节定义了清晰边界
- [ ] 保存到 'tasks/prd-[feature-name].md'（kebab-case）

## 最佳实践

- ✅ **先澄清再输出：** 3-5 个问题足以定位核心；不要一次性列出 20 个细节问题
- ✅ **字母选项快速回复：** `1A, 2C, 3B` 格式减少交互成本
- ✅ **验收标准必须可验证：** "Button shows dialog" OK；"Works correctly" NO
- ✅ **Non-goals 显式定义边界：** 防止范围蔓延
- ❌ **不要跳过澄清直接生成 PRD**（描述模糊时）
- ❌ **不要开始实施代码**（PRD 是需求文档，不是实现）

## 相关技能

- `prd` (源技能) — [snarktank/ralph/skills/prd](https://github.com/snarktank/ralph/blob/main/skills/prd/SKILL.md)
- `pr-summarizer` — PR diff 总结辅助（互补：PRD → 需求，pr-summarizer → diff 摘要）

## 限制和注意事项

- **交互式依赖：** 质量取决于用户回答；如果选择不回复问题直接获取 PRD，输出可能不完整
- **UI 验证假设：** "Verify in browser" 语句仅在被执行时有效；技能本身不自动调用浏览器
- **输出目录假设：** `tasks/` 目录需用户已存在；不会自动创建缺失的父目录
- **范围限制：** 只生产需求文档，不提供代码实现、架构设计或测试编写

## 安全与安全说明

- 本技能仅生成 Markdown 文档，无破坏性操作
- 不向任何外部服务器上传内容
- 不涉及敏感数据或凭据处理
