---
name: your-agent-name
description: "一句话：这个代理是谁、负责什么、何时被调用（≤200 字符）。前端加载「做什么+何时用」。"
mode: subagent
# color: "#DC2626"   # ← 可选：UI 显示色（#RRGGBB 或主题名；hex 值在 YAML 中需加引号）；create_agent.py 创建时始终启用
tools: [read, grep, glob, bash]      # ← 工具白名单；permission 按它生成全量矩阵
permission:                          # ← 默认拒绝("*") + 逐键显式 allow/deny（尽量全）
  "*": deny
  read: allow
  glob: allow
  grep: allow
  list: deny
  skill: deny
  webfetch: deny
  websearch: deny
  question: deny
  edit: deny
  bash: allow
  task: deny
  lsp: deny
  external_directory: deny
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

- 允许：{{ALLOWED_TOOLS}}（仅完成职责所需，最小权限）
- 禁止：{{FORBIDDEN_TOOLS}}

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