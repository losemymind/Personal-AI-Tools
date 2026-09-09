# agents/ — 已验证代理（Agent）能力目录

> 本文件由 `python tools/scripts/build_catalog.py` 自动生成，**禁止手改**。事实源 = 各 `SKILL.md` / `AGENT.md` 的 frontmatter。

> 新增/删除/改进能力后重跑 `python tools/scripts/build_catalog.py`；发布门可用 `python tools/scripts/build_catalog.py --check` 校验目录是否过期。

> 检索：让 LLM 读本文件匹配需求 → 命中即复制对应 `agents/<name>` 目录到目标客户端对应目录，人类确认后执行。

> 落地前转换：仓库规范形 frontmatter 复制到 claude/opencode 前，先用 `python agent-creator/skills/agent-creator/scripts/adapt_agent.py <目录> --client <claude|opencode> --out <落点>` 转换。


## 分组：academic

_共 5 个代理，安装路径位于 `agents/academic/` 下。_

## anthropologist

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [academic, ue-game-studio] |
| install | 复制 `agents/academic/anthropologist` → 客户端 agents/ 目录 |

**用途**：分析现实或虚构社会的文化、亲属关系、仪式、信仰、交换、生计与社会权力；在需要文化一致性、民族志语境或现实群体敏感性审查时使用

## geographer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [academic, ue-game-studio] |
| install | 复制 `agents/academic/geographer` → 客户端 agents/ 目录 |

**用途**：分析或设计游戏世界的地形、气候、水文、资源、聚落、交通与地缘关系；在世界观、地图或关卡布局需要地理一致性检查时使用

## historian

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [academic, ue-game-studio] |
| install | 复制 `agents/academic/historian` → 客户端 agents/ 目录 |

**用途**：核验游戏设定的时间线、时代错误、物质文化、制度与历史因果；在历史、架空历史或反事实世界观需要证据化分析时使用

## narratologist

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [academic, ue-game-studio] |
| install | 复制 `agents/academic/narratologist` → 客户端 agents/ 目录 |

**用途**：分析游戏、小说、剧本或互动叙事的结构、信息、人物弧、类型承诺、玩家选择与主题；在诊断叙事问题或比较改稿方案时使用

## psychologist

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [academic, ue-game-studio] |
| install | 复制 `agents/academic/psychologist` → 客户端 agents/ 目录 |

**用途**：分析虚构角色的人格、动机、信念、压力反应、发展轨迹、群体行为与关系动力；在构建心理可信的角色、冲突和成长弧时使用

## 分组：code-quality

_共 2 个代理，安装路径位于 `agents/code-quality/` 下。_

## code-reviewer

| mode | subagent |
| version | 0.1.0 |
| maturity | runtime-verified |
| tags | [code-review, quality, agent] |
| install | 复制 `agents/code-quality/code-reviewer` → 客户端 agents/ 目录 |

**用途**：常驻代码审查代理：对 PR/diff 做多轴质量审查（正确性/可维护性/性能/安全），分级输出问题清单与修改建议。当用户要求「审查代码」「review 我的改动」「合并前把关」时被调用。只读角色，无编辑权限。

## code-simplifier

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [code-simplify, refactor, code-quality] |
| install | 复制 `agents/code-quality/code-simplifier` → 客户端 agents/ 目录 |

**用途**：简化重构最近修改的代码：提升清晰度、一致性、可维护性，保持功能完全不变、聚焦本次会话刚改动的代码（除非用户指定更广范围）。当用户要求简化代码、重构、清理冗余、改善可读性，或代码改动后希望自动精炼时被调用。

## 分组：ue-game-studio

_共 25 个代理，安装路径位于 `agents/ue-game-studio/` 下。_

## asset-compliance-auditor

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [qa, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/qa/asset-compliance-auditor` → 客户端 agents/ 目录 |

**用途**：审计 UE 项目资产的命名、目录、引用、导入设置、预算、Cook 包含范围、来源记录与项目规范；在功能集成或构建游戏包前需要资产合规门禁时使用

## audiovisual-director

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [directors, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/directors/audiovisual-director` → 客户端 agents/ 目录 |

**用途**：统筹本地 UE 游戏的美术、动画、VFX、UI 与声音方向，定义统一视听语言、质量标尺和创意验收；在跨资产类型需要方向裁决而非直接制作时使用

## character-animation-engineer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [technical, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/technical/character-animation-engineer` → 客户端 agents/ 目录 |

**用途**：实现 UE 角色骨骼兼容、动画重定向、AnimBP、Montage、Motion Warping、Control Rig、IK 与运行时动画优化；在需要解决生物体如何运动而非战斗结算时使用

## game-ai-engineer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [technical, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/technical/game-ai-engineer` → 客户端 agents/ 目录 |

**用途**：实现 UE 游戏角色的环境感知、行为决策、导航查询与战术协同，维护 AIController、Behavior Tree、StateTree、Blackboard 和 EQS；在需要改变 AI 如何判断与行动而非遭遇设计时使用

## game-asset-production-manager

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [production, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/production/game-asset-production-manager` → 客户端 agents/ 目录 |

**用途**：管理本地 UE 游戏资产从需求、Asset ID、Brief、版本、依赖、来源到多门禁交付的完整生命周期；在需要组织资产生产而非亲自创作或批准专业质量时使用

## game-audio-technical-specialist

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [technical, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/technical/game-audio-technical-specialist` → 客户端 agents/ 目录 |

**用途**：制作并集成本地 UE 游戏的 SFX、环境声、音乐、对白处理、MetaSound 或 Wwise 动态声学资产；在需要听觉物料、空间音频与标准触发句柄而非玩法逻辑时使用

## game-director

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [directors, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/directors/game-director` → 客户端 agents/ 目录 |

**用途**：统筹游戏创意愿景、玩家体验、世界设定、设计支柱、核心循环、系统需求与 GDD 一致性；在需要调用学术专家完善设定、进行创意取舍或把世界观转化为可验证设计任务时使用

## game-producer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [directors, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/directors/game-producer` → 客户端 agents/ 目录 |

**用途**：负责 UE 游戏项目的范围治理、产能规划、任务依赖、负责人分配、Sprint、里程碑、风险、变更控制与生产阶段门禁；在批准的设计和技术工作包需要转化为可执行开发计划时使用

## game-visual-asset-artist

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [production, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/production/game-visual-asset-artist` → 客户端 agents/ 目录 |

**用途**：根据批准的 Asset Brief 制作角色、环境、道具、纹理等视觉源资产及规范导出物；在需要生产视觉内容而非决定风格、渲染架构或最终地图集成时使用

## lead-game-balance-designer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [design, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/design/lead-game-balance-designer` → 客户端 agents/ 目录 |

**用途**：负责 UE 游戏战斗、成长、资源、掉落与随机系统的公式、参数、曲线、边界和可验证平衡目标；在机制规则已明确、需要建立数值模型、模拟调参或进行数值门禁时使用

## lead-game-economy-designer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [design, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/design/lead-game-economy-designer` → 客户端 agents/ 目录 |

**用途**：负责本地 UE 游戏包内货币、资源、物品与服务的价值结构、产出消耗、库存流转、价格锚点和经济稳定性；在设计游戏经济循环或评审资源系统时使用

## level-mission-designer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [design, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/design/level-mission-designer` → 客户端 agents/ 目录 |

**用途**：设计 UE 游戏关卡的玩家路径、任务状态、遭遇节奏、触发条件、检查点与失败恢复，并形成可实施的 Level/Mission Brief；在需要决定体验流程而非直接搭建最终地图时使用

## localization-lqa-specialist

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [production, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/production/localization-lqa-specialist` → 客户端 agents/ 目录 |

**用途**：负责本地 UE 游戏本地化数据模型、Loc 文本/术语/字符串资源、i18n 就绪契约与语言质量验证（LQA）；在需要建立本地化管线、多语言文本交付或本地化质量门禁时使用

## orchestration-director

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [orchestration, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/orchestration/orchestration-director` → 客户端 agents/ 目录 |

**用途**：统筹复杂 UE 游戏项目任务的强制需求澄清、递归任务树落盘、专业 Agent 路由、依赖编排、状态治理、质量门禁、冲突升级与结果综合；在任务跨越多个专业域或需要协作闭环时使用

## performance-profiler

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [technical, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/technical/performance-profiler` → 客户端 agents/ 目录 |

**用途**：在目标 UE 版本、平台、配置和可重复场景中采集并分析 CPU、GPU、内存、加载与卡顿证据，对照批准预算定位性能瓶颈；在性能门禁或优化前后验证时使用

## qa-test-specialist

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [qa, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/qa/qa-test-specialist` → 客户端 agents/ 目录 |

**用途**：对 UE 游戏的编辑器版本和本地构建包执行功能、集成、探索、回归与 Smoke Test，形成可复现缺陷和独立包体验收证据；在功能交付或构建包门禁前使用

## security-engineer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [qa, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/qa/security-engineer` → 客户端 agents/ 目录 |

**用途**：对本地 UE 游戏项目的源码、Blueprint、网络复制、Save/Load、凭据、插件依赖与本地构建包执行独立安全评审与威胁建模；在构建包门禁前需要绑定性安全结论时使用

## technical-director

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [directors, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/directors/technical-director` → 客户端 agents/ 目录 |

**用途**：负责 UE 游戏项目的技术战略、系统架构、实现可行性、非功能预算、ADR、引擎风险与技术阶段门禁；在设计需求需要转化为可验证的 UE 技术方案和工作包时使用

## ue-build-engineer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [technical, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/technical/ue-build-engineer` → 客户端 agents/ 目录 |

**用途**：配置、执行和诊断 UE 项目的本地 Build、Cook、Stage 与 Package，维护 UBT、UAT、BuildCookRun、BuildGraph 和可追溯构建产物；在需要生成或修复本地游戏构建包时使用

## ue-core-systems-engineer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [technical, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/technical/ue-core-systems-engineer` → 客户端 agents/ 目录 |

**用途**：实现 UE 项目跨玩法域复用的 C++ 核心框架、Subsystem、公共接口、组件与生命周期基础设施；在技术总监已批准架构、需要落地纯文本底座而非具体玩法或网络业务时使用

## ue-gameplay-engineer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [technical, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/technical/ue-gameplay-engineer` → 客户端 agents/ 目录 |

**用途**：端到端实现边界明确的 UE 玩法及其多人网络同步，覆盖业务层 C++、Gameplay Actor、具体 GAS Ability/Effect、Replication、RPC、预测与回滚；在公共底座已确定、需要交付具体玩法闭环时使用

## ue-technical-art-engineer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [technical, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/technical/ue-technical-art-engineer` → 客户端 agents/ 目录 |

**用途**：实现 UE 材质、Shader、Niagara 与视觉资产运行时技术化，负责纹理设置、LOD/Nanite、渲染预算和视觉性能适配；在视觉源资产需要进入 UE 或解决渲染技术问题时使用

## ue-tools-pipeline-engineer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [technical, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/technical/ue-tools-pipeline-engineer` → 客户端 agents/ 目录 |

**用途**：构建 UE Editor Utility、Python、Commandlet 与 DCC 导入批处理，自动化资产命名、元数据、验证和可追溯管线；在重复资产操作需要安全自动化而非人工逐项修改时使用

## ue-ui-engineer

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [technical, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/technical/ue-ui-engineer` → 客户端 agents/ 目录 |

**用途**：端到端实现 UE 的 UMG、CommonUI、Widget C++、输入焦点、数据绑定、HUD 与菜单；在 UI/UX 规格已明确、需要完成界面技术实现而非玩法计算时使用

## ue-world-builder

| mode | subagent |
| version | 0.1.0 |
| maturity | static-verified |
| tags | [technical, ue-game-studio] |
| install | 复制 `agents/ue-game-studio/technical/ue-world-builder` → 客户端 agents/ 目录 |

**用途**：在 UE Editor 中实施关卡空间、World Partition、Data Layer、Level Instance、PCG 与场景 Actor 最终组装；在 Level/Mission Brief 已批准、需要搭建或集成生产地图时使用

