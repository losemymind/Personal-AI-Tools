# agents/ — 已验证代理（Agent）能力目录

> 本文件由 `python tools/scripts/build_catalog.py` 自动生成，**禁止手改**。事实源 = 各 `SKILL.md` / `AGENT.md` 的 frontmatter。

> 新增/删除/改进能力后重跑 `python tools/scripts/build_catalog.py`；发布门可用 `python tools/scripts/build_catalog.py --check` 校验目录是否过期。

> 检索：让 LLM 读本文件匹配需求 → 命中即复制对应 `agents/<name>` 目录到目标客户端对应目录，人类确认后执行。

> 落地前转换：仓库规范形 frontmatter 复制到 claude/opencode 前，先用 `python agent-creator/skills/agent-creator/scripts/adapt_agent.py <目录> --client <claude|opencode> --out <落点>` 转换。


## 分组：academic

_共 5 个代理，安装路径位于 `agents/academic/` 下。_

## anthropologist

| mode | subagent |
| maturity | static-verified |
| install | 复制 `agents/academic/anthropologist` → 客户端 agents/ 目录 |

**用途**：分析现实或虚构社会的文化、亲属关系、仪式、信仰、交换、生计与社会权力；在需要文化一致性、民族志语境或现实群体敏感性审查时使用

## geographer

| mode | subagent |
| maturity | static-verified |
| install | 复制 `agents/academic/geographer` → 客户端 agents/ 目录 |

**用途**：分析或设计游戏世界的地形、气候、水文、资源、聚落、交通与地缘关系；在世界观、地图或关卡布局需要地理一致性检查时使用

## historian

| mode | subagent |
| maturity | static-verified |
| install | 复制 `agents/academic/historian` → 客户端 agents/ 目录 |

**用途**：核验游戏设定的时间线、时代错误、物质文化、制度与历史因果；在历史、架空历史或反事实世界观需要证据化分析时使用

## narratologist

| mode | subagent |
| maturity | static-verified |
| install | 复制 `agents/academic/narratologist` → 客户端 agents/ 目录 |

**用途**：分析游戏、小说、剧本或互动叙事的结构、信息、人物弧、类型承诺、玩家选择与主题；在诊断叙事问题或比较改稿方案时使用

## psychologist

| mode | subagent |
| maturity | static-verified |
| install | 复制 `agents/academic/psychologist` → 客户端 agents/ 目录 |

**用途**：分析虚构角色的人格、动机、信念、压力反应、发展轨迹、群体行为与关系动力；在构建心理可信的角色、冲突和成长弧时使用

## 分组：code-quality

_共 2 个代理，安装路径位于 `agents/code-quality/` 下。_

## code-reviewer

| mode | subagent |
| maturity | runtime-verified |
| install | 复制 `agents/code-quality/code-reviewer` → 客户端 agents/ 目录 |

**用途**：常驻代码审查代理：对 PR/diff 做多轴质量审查（正确性/可维护性/性能/安全），分级输出问题清单与修改建议。当用户要求「审查代码」「review 我的改动」「合并前把关」时被调用。只读角色，无编辑权限。

## code-simplifier

| mode | subagent |
| maturity | static-verified |
| install | 复制 `agents/code-quality/code-simplifier` → 客户端 agents/ 目录 |

**用途**：简化重构最近修改的代码：提升清晰度、一致性、可维护性，保持功能完全不变、聚焦本次会话刚改动的代码（除非用户指定更广范围）。当用户要求简化代码、重构、清理冗余、改善可读性，或代码改动后希望自动精炼时被调用。

