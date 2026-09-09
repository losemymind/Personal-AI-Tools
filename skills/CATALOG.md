# skills/ — 已验证技能（Skill）能力目录

> 本文件是**静态快照**（本仓库无目录生成器）：事实源 = 各 `SKILL.md` frontmatter；新增/删除/改进技能后**手工同步本文件条目**。
> 检索：让 LLM 读本文件匹配需求 → 命中即复制对应技能目录到目标客户端的 `skills/` 目录（落点见 `skills/README.md`），人类确认后执行。


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

