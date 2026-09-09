# evolutions/ — 对比学习记录

本目录保存 agent-creator 每次「自建代理 vs 上游候选」对比择优的完整记录，是**反馈闭环**的核心载体。

## 记录规范

### 文件名

```
<YYYY-MM-DD>-compare-<代理名>.md
```

### 记录内容模板

```markdown
# 对比记录：<自建代理名> vs 上游 <候选代理名>

## 基本信息
- 日期：
- 需求描述：
- 上游候选来源：索引 path（如 engineering/engineering-code-reviewer.md）

## 对比报告
（贴入对比结论或摘要各维度评估）

## 结论
- 优者：上游 / 自建 / 持平
- 采纳决定：

## 差异分析（仅上游更优时需要）
- 上游优势维度及具体做法（身份表述/边界清晰度/权限声明/协作协议）
- 自建差距原因

## 提炼的学习点
- 学习点 1：…（可直接用于改进 agent-creator）
- 学习点 2：…

## 改进建议（可选）
- 建议更新 agent-creator SKILL.md / references 的哪些部分
```

### 后续处理

- 每季度（或积累 5-10 条记录时）review 本目录，汇总「学习点」→ 迭代 agent-creator。
- review 后可把已采纳的学习点移入 `references/`（作为方法论沉淀），本记录作为历史留存。
