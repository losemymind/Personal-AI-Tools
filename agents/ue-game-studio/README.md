# ue-game-studio — UE 游戏开发代理安装包

本目录是 **UE 游戏开发专用**的代理安装包。这里的所有 agent 都是为 Unreal Engine（UE）项目开发准备的；安装到目标项目时，把本包内 agent 与公共代理（仓库根 `agents/academic/`，相对本包为 `../academic/`）一并部署。

> 公共代理（不随本包移动）：仓库根 `agents/academic/`（相对本包为 `../academic/`）下的 5 个学术/研究代理。本包在协议与协作上引用它们，安装时应一并部署到客户端 agents 目录。

## 目录结构

```
ue-game-studio/
├── AGENTS.md                    # UE 游戏开发项目级协作规则（部署时复制到目标项目根 AGENTS.md）
├── README.md                    # 本安装清单
├── design/                      # 数值/经济/关卡与任务设计
│   └── <agent>/AGENT.md
├── directors/                   # 决策层：游戏总设计师/技术总监/制作人/视听总监
│   └── <agent>/AGENT.md
├── orchestration/               # 总控编排（入口建议）orchestration-director
│   └── <agent>/AGENT.md
├── production/                  # 资产生命周期/视觉资产/本地化 LQA
│   └── <agent>/AGENT.md
├── qa/                          # 资产合规审计/QA 测试/安全评审
│   └── <agent>/AGENT.md
└── technical/                   # UE 引擎专属：核心系统/Gameplay/AI/动画/UI/工具管线等
    └── <agent>/AGENT.md
```

## 本包安装清单

当目标项目是 **UE 游戏开发**项目时，安装以下 agent（按 layer 分组）：

- **design**：
  - `lead-game-balance-designer` — 数值平衡设计
  - `lead-game-economy-designer` — 经济系统设计
  - `level-mission-designer` — 关卡与任务设计
- **directors**：
  - `audiovisual-director` — 视听方向
  - `game-director` — 游戏总设计师（Canon/体验支柱）
  - `game-producer` — 游戏制作人（范围/里程碑/门禁）
  - `technical-director` — 技术总监（架构/数据所有权/ADR）
- **orchestration**：
  - `orchestration-director` — 总控编排专家（跨域入口）
- **production**：
  - `game-asset-production-manager` — 资产生产管理
  - `game-visual-asset-artist` — 视觉资产制作
  - `localization-lqa-specialist` — 本地化与 LQA
- **qa**：
  - `asset-compliance-auditor` — 资产合规审计
  - `qa-test-specialist` — QA 测试
  - `security-engineer` — 安全评审
- **technical**：
  - `character-animation-engineer` — 角色动画
  - `game-ai-engineer` — 游戏 AI
  - `game-audio-technical-specialist` — 音频技术
  - `performance-profiler` — 性能剖析
  - `ue-build-engineer` — UE 构建
  - `ue-core-systems-engineer` — UE 核心系统
  - `ue-gameplay-engineer` — UE 玩法
  - `ue-technical-art-engineer` — UE 技术美术
  - `ue-tools-pipeline-engineer` — UE 工具与资产管线
  - `ue-ui-engineer` — UE UI
  - `ue-world-builder` — UE 世界构建

## 引用公共代理（相对本包 `../academic/`，随本包一并部署）

- `anthropologist` — 人类学家（文化一致性/民族志/现实敏感性）
- `geographer` — 地理学家（地形/气候/资源/交通）
- `historian` — 历史学家（时间线/时代错误/制度与因果）
- `narratologist` — 叙事学家（结构/人物弧/主题）
- `psychologist` — 心理学家（动机/心智/玩家行为）

这些是通用研究型代理，不依赖 UE 引擎；本包的 design/directors 层在设定构建时会引用它们。

## 安装与冲突处理

安装 = 把 agent 目录**复制**到目标客户端 `agents/` 目录（无统一安装器；落点见 `agents/README.md`）。本包内引用公共代理的相对路径为 `../academic/<agent>`。

```bash
# 复制到客户端 agents/ 目录（示例：opencode 全局）
Copy-Item -Recurse agents/ue-game-studio/<layer>/<agent>   ~/.config/opencode/agent/<agent>
Copy-Item -Recurse agents/academic/<agent>                 ~/.config/opencode/agent/<agent>
```

**冲突处理策略（必须人工确认）**：当 `ue-game-studio` 中的某个 agent 与目标项目客户端 agents 目录已存在的同名 agent 冲突时——

1. 先列出两侧差异（本包版本 vs 目标已有版本）。
2. **停下来让用户选择保留哪一个**：本包版本 / 目标已有版本 / 两者并存改名 / 跳过该 agent。
3. 用户确认前不覆盖、不删除目标已有文件。
4. AGENTS.md 部署到目标项目根时，先备份目标既有 `AGENTS.md`，再按合并流程人工处理差异。