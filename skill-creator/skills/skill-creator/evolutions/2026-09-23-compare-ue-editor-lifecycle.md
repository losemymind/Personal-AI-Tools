# 对比记录：ue-editor-lifecycle vs 上游 unreal-engine-cpp-pro（最近邻）

## 基本信息

- 日期：2026-09-23
- 需求：补齐 `ue-editor-lifecycle`（本仓库自建，2026-09-15 沉淀 UE 编辑器安全关闭/重建/异步启动流程）缺失的上游对比择优记录（审计欠账 `skills/SKILLS-AUDIT.md` §5）。
- 上游候选来源（`search_index.py`，5 源 2188 条）：
  - 主题检索 `unreal editor` / `UnrealEditor` / `LaunchUE` / `PIE` / `rebuild` / `dll` / `frozen` / `hang` / `editor crash` / `ue5` → **均 0 命中**（无专门的 UE 编辑器生命周期/构建/启动技能）。
  - 唯一相邻命中：索引 path `skills/unreal-engine-cpp-pro`（`sickn33/agentic-awesome-skills`，120 行，risk: safe，UE5.x C++ 通用开发指南——UObject 卫生/性能模式，**非**编辑器生命周期）。
  - `--category game-development` 全列 18 条：均为引擎选择/2D/3D/美术/音频/设计/多人/VR 等泛化主题，无编辑器生命周期条目。

## 对比报告

`compare_skills.py skills/development/ue-editor-lifecycle <上游 unreal-engine-cpp-pro>`：

| 维度 | 本地 | 上游 |
|---|---|---|
| 总分 | **0.76** | 0.72 |
| 质量（60%） | 0.97 | 0.84 |
| 结构（40%） | 0.45 | 0.53 |
| body lines | 150 | 120 |
| files | 2（evals） | 3（examples×2 + SKILL.md） |
| 元数据完整 | 1.00 | 0.75 |
| example_available | 1.00 | 0.50 |

质量子项：本地 trigger/example/limitations/risk/metadata 均 1.00；上游 metadata 0.75、example 0.50。结构子项：本地 resource_organization 0.00（无 `references/`/`scripts/`），上游 0.33（有 `examples/`）。

## 结论

- 优者：**自建**（差 0.04）。
- 采纳决定：采纳自建版本，**不采纳**上游。
- 理由：二者领域几乎不重叠——上游是 C++ 开发指南（性能仅其相邻话题），本技能以「检查实例 → 源码构建配置 → 构建 → 异步启动」的操作闭环为核心；在质量维度（触发/示例/限制/元数据完整）本地全面领先，总分略高。结构分本地偏低仅因缺少 `references/`（150 行单文件，尚未到拆分阈值），非内容缺陷。

## 差异分析

- 上游优势：结构分（0.53 > 0.45）来自 `examples/` 目录与更小的正文；其 C++/UObject 细节对本技能无直接可吸收内容。
- 自建差距：无 `references/`；当前 150 行未触发渐进披露拆分，符合「细节进 references」的阈值纪律（普通技能 <1000 行），暂不拆。

## 提炼的学习点

- **主题 0 命中时以「最近邻」量化对比收口**：目标主题无上游候选时，仍应选取同域最近邻做 `compare_skills.py`，把「无同类」从主观判断变为可复核的证据（与 ue5-performance-optimization 的 `unreal-engine-cpp-pro` 对比同法）。
- **领域专精 vs 泛化相邻的再次验证**：泛化的引擎/C++ 上游不能替代具体的编辑器生命周期技能；操作流程类技能的价值在「可复现步骤 + 故障处置」而非编码细节。

## 改进建议

- 无需改 skill-creator 方法论（该欠账属能力库条目的流程补记，非工具缺陷）。
- 若后续上游出现专门的 UE 编辑器/构建/启动生命周期技能，应重跑对比择优。
