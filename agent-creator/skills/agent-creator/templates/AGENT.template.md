---
name: your-agent-name
description: "一句话：这个代理是谁、负责什么、何时被调用（≤200 字符）。前端加载「做什么+何时用」。"
mode: subagent
tools: [read, grep, glob, bash]
permission:
  edit: deny
version: "0.1.0"
tools_clients: [claude, opencode, codex, deepseek]
tags: [agent-name]
---

# 代理名称

## 角色定位

1-2 句：这个代理是谁、为什么存在。

## 职责范围

**必须做：**
- [职责 1]
- [职责 2]

**拒绝做：**
- [职责之外的请求 1]
- [破坏性操作 / 未授权操作]

## 工作方式

判断标准与流程要点。（步骤细节可引用技能或 references/）

## 工具与权限

- 允许：`read` `grep` `bash`（仅完成职责所需，最小权限）
- 禁止：`edit`（除非职责需要，否则默认拒绝）

## 协作协议

- **何时被调用**：……
- **汇报格式**：……
- **升级路径**：遇到 [情况] 时停下，交还用户决策。

## 完成标准

产出如何验收：
- [ ] 可验证标准 1
- [ ] 可验证标准 2

## 限制与边界

- 在这个环境下不工作的情况
- 已知边界与做不到的事情