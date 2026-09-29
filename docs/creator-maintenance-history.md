# 创建器内部借鉴历史（仓库级）

本页保全从独立工作区维护文本中移出的历史来源事实。记录只用于仓库维护与溯源；各创建器成品不引用本页，也不以另一创建器作为指令入口或运行依赖。外部仓库的来源与许可继续保留在对应产品记录中。

## 2026-09-29：统一命名与独立文本

用户要求工具与子代理使用相同命名格式，同时各创建器不包含彼此的引用或关系说明。agent 工具迁移为 agent_adapt / agent_index_build / agent_compare / agent_create / agent_package / agent_index_search / agent_validate / agent_security；角色文件迁移为 agent_reviewer.md。skill 工具及角色沿用已完成的 skill_ 前缀规范。各自的 `_project_paths.py` 只定位本地成品。

工作区守则、测试注释和 evolutions 改为本产品的变更事实与约束；仓库独立性门覆盖这些文本。此次清理不表示过去从未借鉴，也不宣称相关实现独立原创。已有 Git 原文（本轮起点 f68cfc8）保留旧名称和当时来源关系。

## 保留的内部来源事实

| 日期 | 历史事实 |
|---|---|
| 09-09 | agent-creator 的引用、description 与发布纪律曾参考 skill-creator 0.6.0/0.6.1 的维护实践。原事件为 agent 侧 adopt-ref-description-release-discipline。 |
| 09-10 | agent 的评审闭环参考了 skill 侧同日 adopt-agent-review-loop 记录，使用作者修订、独立评审、有限迭代及结构化 verdict。 |
| 09-10 | agent 首轮安全扫描和 FTS5 查询字面化借鉴已有本地实现；后续 skill 的 PowerShell curl/wget→iex 覆盖也曾参照 agent 审计结果。 |
| 09-10 | skill 的命名/kebab-case与安全扫描审计曾对照 validate_agents.py；代理创建的 re.sub 替换串修复也曾对照已有 create_skill.py 的 lambda 用法。 |
| 09-11 | agent 的整目录多端打包工具参考 skill-creator 0.10 的 package_skill.py；frontmatter/records 改造参考同期 slim-frontmatter 记录；shell 归一化使用已有 utils 实现。 |
| 09-11 | 仓库安装器曾误用 agent 创建器捆绑的 AGENT 验证器检查其 SKILL 入口，导致安装失败；后来按实际入口类型选择验证器。skill_package 的权限白名单回归注释也曾引用 adapt_agent 的权限合并缺陷。 |

这些内部历史与外部来源不同：agent_format.py 的 personal-workflow 来源、Anthropic 方法论/评测来源、各索引源和样本许可均不因本次清理而移除。

## 历史验证口径

命名迁移中曾记录 skill 工作区 250 项、agent 工作区 116 项、tools 28 项，以及成品 1 / 技能库 7 / 代理库 7 的 strict 检查；这些是当时快照。后续优化与真实测评的测试计数及限制分别由 HANDOFF 和仓库级 evaluation-runs 保存，不能累计成同一次运行。

## 真实测评证据归档

09-29 的真实测评记录从 skill 工作区移到根 evaluation-runs/skill-creator/2026-09-29-live。原始事件、冻结哈希、执行指标、模型输出和评分保持历史内容；维护报告、复现命令和导航更新新位置。原事件中的旧绝对路径是当时执行事实，不能据此改写历史或要求它们指向当前文件。
