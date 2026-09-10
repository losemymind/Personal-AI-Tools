# skills/ — 已验证技能（Skill）能力目录

> 本文件由 `python tools/scripts/build_catalog.py` 自动生成，**禁止手改**。事实源 = 各 `SKILL.md` / `AGENT.md` 的 frontmatter。

> 新增/删除/改进能力后重跑 `python tools/scripts/build_catalog.py`；发布门可用 `python tools/scripts/build_catalog.py --check` 校验目录是否过期。

> 检索：让 LLM 读本文件匹配需求 → 命中即复制对应 `skills/<name>` 目录到目标客户端对应目录，人类确认后执行。


## code-review-skill

| category | development |
| risk | safe |
| version | 0.1.0 |
| source | community |
| date_added | 2026-09-03 |
| tags | [code-review, pr, security, performance, architecture] |
| install | 复制 `skills/development/code-review-skill` → 客户端 skills/ 目录 |

**用途**：Provides comprehensive, expert-level code review guidance across 20+ languages and frameworks — React 19, Vue 3, Angular 17+, Svelte 5, Rust, TypeScript, Java 17/21, Java 8, PHP, Ruby/Rails, Python, Django/DRF, FastAPI, Go, C#/.NET 8, Kotlin/Android, Swift/SwiftUI, Dart/Flutter, NestJS, C/C++, Zig, CSS/Less/Sass, Qt, and more. Covers architecture review, performance review, security audit, code-quality anti-patterns, and common bugs across all ecosystems, with progressive-disclosure per-language guides. Use when: reviewing pull requests, conducting PR reviews, code review, reviewing code changes, establishing review standards, mentoring developers, architecture reviews, security audits, performance reviews, checking code quality, finding bugs, giving feedback on code — 或用户要求代码审查、review PR/代码改动、架构审查、安全审计、检查代码质量、找 Bug、给代码反馈时使用。

**触发器**：Reviewing pull requests and code changes

## mcp-builder

| category | development |
| risk | safe |
| version | 0.1.0 |
| source | community |
| date_added | 2026-09-10 |
| tags | [mcp, fastmcp, typescript-sdk, tool-design, llm-integration] |
| install | 复制 `skills/development/mcp-builder` → 客户端 skills/ 目录 |

**用途**：指导构建高质量的 MCP（Model Context Protocol）应用：让 LLM 通过精心设计的工具与外部服务交互，覆盖端点覆盖 vs 工作流工具取舍、工具命名与 schema 设计、上下文与分页、可执行错误信息、评测集构建，并提供 Python（FastMCP）与 TypeScript 官方 SDK 两套实现路径。当用户要创建或设计这类工具、编写工具 schema、提升可发现性、建评测集，或提到 FastMCP、tool schema、分页返回时使用。

**触发器**：用户要**构建 MCP 服务器**以集成某个外部 API 或服务（Python/FastMCP 或 TypeScript/MCP SDK）。

## ue5-performance-optimization

| category | game-development |
| risk | safe |
| version | 0.1.0 |
| source | self |
| date_added | 2026-09-10 |
| tags | [unreal-engine, ue5, performance, profiling, optimization] |
| install | 复制 `skills/game-development/ue5-performance-optimization` → 客户端 skills/ 目录 |

**用途**：指导 Unreal Engine 5.6 游戏的性能剖析与优化：先用 Unreal Insights、stat 命令与 CSV Profiler 在可复现场景中定位 Game Thread、Render Thread、GPU、内存、加载与卡顿瓶颈，再落到实现层优化（Tick 与蓝图、GC 与内存分配、Draw Call 与实例化、Nanite/Lumen/VSM/TSR 可扩展性、Niagara、异步并行）。当用户要求 UE5 性能优化、卡顿/掉帧排查、Insights 分析、stat 命令解读、降低 Draw Call、GC 卡顿、内存/显存超标、打包后帧率低时使用。

**触发器**：用户报告 UE5 项目**掉帧、卡顿（hitch）、加载慢、内存/显存超标**，要求排查原因。

## pr-summarizer

| category | git |
| risk | safe |
| version | 0.1.0 |
| source | self |
| date_added | 2026-09-02 |
| tags | [git, pr, summary, review] |
| install | 复制 `skills/git/pr-summarizer` → 客户端 skills/ 目录 |

**用途**：将 git diff 转为结构化 PR 总结：一句话摘要、变更分类表、审查清单、风险标注与语义化标题建议。当用户要求总结变更、撰写 PR 描述、review 前梳理 diff、或说「总结我的改动」「写 PR 描述」「PR 摘要」时使用。

**触发器**：用户要求「总结我的改动」「写 PR 描述」「PR 摘要」「review 前梳理 diff」

## prd-generator

| category | product |
| risk | safe |
| version | 0.1.0 |
| source | community |
| date_added | 2026-09-07 |
| tags | [prd, requirements, feature-spec, planning] |
| install | 复制 `skills/product-design/prd-generator` → 客户端 skills/ 目录 |

**用途**：将用户需求转化为结构化 PRD（Product Requirements Document）：接收功能描述 → 交互式澄清问题 → 生成完整章节文档。当用户要求『创建 PRD』『写需求文档』或说 plan this feature、requirements for spec out 时使用。

**触发器**：用户要求「创建 PRD」「写需求文档」「spec out 一个功能」

