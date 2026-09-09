# examples/ — 上游学习样本

本目录收录来自 [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills) 的 6 个技能完整目录，作为 skill-creator 的**学习样本**（对应官方 `skill-anatomy.md` 的「研究这些示例」）。它们不是 skill-creator 自身的产出物，**验证器自动豁免**（`EXEMPT_DIRS = {"examples"}`）。

## 来源与许可

- 上游仓库：`https://github.com/sickn33/agentic-awesome-skills`（MIT License）
- 每个技能保留其原始 `frontmatter` 的 `source` / `date_added` / `author` 字段
- 复制许可：MIT，允许复制、修改、再分发；需保留上游版权声明

## 样本清单与学习要点

| 目录 | 形态 | 针对以下需求学习 |
|:--|:--|:--|
| `brainstorming/` | 单文件 · 结构教科书 | 阶段化流程（1-7 步）、硬性门控（Understanding Lock）、决策日志、退出条件 |
| `copywriting/` | 单文件 · 流程门控 | 硬门（Copy Brief Lock）、完成标准（Hard Stop）、防虚构规则 |
| `git-pushing/` | 单文件 + `scripts/` | 高风险操作的安全门（Safety Gates）、辅助脚本化、保护区规则 |
| `systematic-debugging/` | 单文件 + `references/` | 阶段强制序（4 相）、红旗清单、合理化借口对照表、量化影响数据 |
| `react-best-practices/` | 多文件 · 渐进式披露范本 | 规则前缀分类、Quick Reference 决策表、`rules/` 按需加载 |
| `loki-mode/` | 综合 · 复杂工作流范本 | 决策树首屏、`references/` 大拆分（16 个子文件）、状态目录结构、模型路由 |

## 使用方式

1. 创建技能前先读 1-2 个形态相近的样本
2. 对比其结构、门控、章节组织，再套用 `templates/SKILL.template.md`
3. 不要直接复制样本正文（它们面向特定领域），只借鉴**结构与方法论**

## 更新方式

上游更新后重新同步：

```bash
# 重新拉取指定目录（以 git-pushing 为例）
git clone --depth 1 --filter=blob:none --sparse <上游仓库> /tmp/upstream
cd /tmp/upstream && git sparse-checkout set skills/<技能名>
# 然后覆盖拷贝到 examples/<技能名>/
```