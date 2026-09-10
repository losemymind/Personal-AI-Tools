# 对比记录：ue5-performance-optimization vs 上游 unreal-engine-cpp-pro

## 基本信息

- 日期：2026-09-10
- 需求：创建 UE5.6 性能优化技能，兼顾**剖析定位**（Unreal Insights / stat / 内存）与**实现层优化**（Tick/蓝图/GC/Draw Call/渲染可扩展性/Niagara/异步）。入库 `skills/game-development/ue5-performance-optimization/`。
- 上游候选来源：
  - 索引 path `skills/unreal-engine-cpp-pro`（`sickn33/agentic-awesome-skills`，120 行，risk: safe，UE5.x C++ 开发与性能模式，非专门性能优化技能）。
  - 索引检索 `unreal engine performance optimization` / `game performance profiling` → **0 命中**（无专门性能优化技能）。

## 对比报告

`compare_skills.py skills/game-development/ue5-performance-optimization <上游 unreal-engine-cpp-pro>`：

| 维度 | 本地 | 上游 |
|---|---|---|
| 总分 | **0.81** | 0.68 |
| 质量（60%） | 0.97 | 0.84 |
| 结构（40%） | 0.58 | 0.45 |
| body lines | 134 | 120 |
| files | 4（references×2 + evals） | 1 |
| 元数据完整 | 1.00 | 0.71 |

## 结论

- 优者：**自建**（差 0.13）。
- 采纳决定：采纳自建版本。
- 理由：上游 `unreal-engine-cpp-pro` 是 C++ 通用开发指南，性能仅为其一节；本技能以「测量→定位→优化→复测」闭环为核心，含剖析工具箱与实现模式两份 reference、触发用例，结构分与元数据完整度更高。

## 差异分析

- 上游优势：C++ 编码细节（UObject 卫生等）更细，但非性能专项；单文件无渐进披露。
- 自建差距：无（在性能优化定位上更聚焦）。

## 提炼的学习点

- **领域专精优于泛化相邻**：相邻上游（C++ 开发）不能替代专门性能技能；「测量先行 + 单变量对比」是性能类技能的核心纪律。
- **复用本仓库领域资产**：编写时参考了本仓库 `agents/ue-game-studio/technical/performance-profiler/AGENT.md`（剖析维度与证据纪律），把 agent 的「只测量不改」纪律转写为 skill 的「先测量再优化、每次单变量」流程。
- **触发描述的固有假阳性**：性能类技能对「Unity 性能优化」这类近义干扰项，词重叠启发式无法区分（性能/优化为核心词不可去）；此类残留应视为启发式局限而非描述缺陷。

## 改进建议

- 无需改 skill-creator 方法论；若后续上游出现专门的 UE 性能优化技能，应重跑对比。
