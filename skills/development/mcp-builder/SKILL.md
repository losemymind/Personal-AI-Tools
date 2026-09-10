---
name: mcp-builder
description: "指导构建高质量的 MCP（Model Context Protocol）应用：让 LLM 通过精心设计的工具与外部服务交互，覆盖端点覆盖 vs 工作流工具取舍、工具命名与 schema 设计、上下文与分页、可执行错误信息、评测集构建，并提供 Python（FastMCP）与 TypeScript 官方 SDK 两套实现路径。当用户要创建或设计这类工具、编写工具 schema、提升可发现性、建评测集，或提到 FastMCP、tool schema、分页返回时使用。"
category: development
risk: safe
source: community
source_repo: anthropics/skills
source_type: community
version: "0.1.0"
date_added: "2026-09-10"
author: anthropics
tags: [mcp, fastmcp, typescript-sdk, tool-design, llm-integration]
tools: [claude, opencode, codex, deepseek]
---

# MCP 服务器开发指南（mcp-builder）

## 概述

创建 MCP（Model Context Protocol）服务器，让 LLM 通过**精心设计的工具**与外部服务交互。衡量一个 MCP 服务器质量的唯一标准是：**它在多大程度上让 LLM 真正完成现实任务**——不是接口数量多，而是工具是否可发现、可组合、误差可控。本技能给出四阶段工作流（研究规划 → 实现 → 评审测试 → 建评测集），并附 Python（FastMCP）与 Node/TypeScript（MCP SDK）两套实现参考。

> 改编自 Anthropic 官方 [anthropics/skills](https://github.com/anthropics/skills) 的 `mcp-builder`（Apache-2.0），保留其 `reference/` 与 `scripts/`；详见 `LICENSE.txt`。

## 何时使用此技能

- 用户要**构建 MCP 服务器**以集成某个外部 API 或服务（Python/FastMCP 或 TypeScript/MCP SDK）。
- 设计或评审 **MCP 工具**（命名、输入/输出 schema、注解、错误信息、分页）。
- 为 MCP 服务器**建评测集**，验证 LLM 能否用这些工具完成真实任务。
- 排查「MCP 工具没被正确调用 / 返回信息太多 / 报错不可用」等可用性问题。
- 用户提到 mcp、model context protocol、FastMCP、MCP SDK、tool schema 等。

**不适用**：仅配置某个现成 MCP 服务器（那是配置任务）；纯 API 客户端库开发（不涉及 MCP 工具暴露）；把 MCP 服务器部署到生产（本技能产出实现与评测，不覆盖运维）。

## 工作原理

### 阶段 1：研究与规划

- **API 覆盖 vs 工作流工具**：在「全面覆盖 API 端点」与「面向具体任务的高层工作流工具」之间取舍。不确定时**优先全面覆盖**——它让 agent 自由组合；某些客户端支持代码执行，能更高效地组合基础工具。
- **命名与可发现性**：工具名清晰、动作导向、统一前缀（如 `github_create_issue`、`github_list_repos`），让 agent 快速找对工具。
- **上下文管理**：工具描述简洁，支持过滤与分页，返回聚焦数据而非整页 JSON。
- **可执行的错误信息**：错误要给出具体建议与下一步，而不是只报「失败」。
- **调研协议与框架**：从 MCP 规范 sitemap（`https://modelcontextprotocol.io/sitemap.xml`）读取相关页面（`.md` 后缀取 markdown），理清传输方式（远程用 streamable HTTP + 无状态 JSON，本地用 stdio）、工具/资源/prompt 定义；再读 SDK 文档。
- **规划实现范围**：阅读目标服务 API 文档，列出要实现的关键端点与最常用操作。

> 官方推荐栈：**TypeScript**（SDK 支持好、静态类型、模型生成质量高）用于远程/集成场景；Python（FastMCP）适合快速集成与 Pydantic 生态。

### 阶段 2：实现

- **项目结构**：按语言指南搭建（见参考文档）。
- **核心基础设施**：API 客户端（含认证）、错误处理、响应格式化（JSON/Markdown）、分页。
- **逐个工具实现**：
  - **输入 schema**：TypeScript 用 Zod、Python 用 Pydantic；带约束与清晰描述，字段描述可含示例。
  - **输出 schema**：尽量定义 `outputSchema`，用 `structuredContent` 返回结构化数据。
  - **工具描述**：功能简述 + 参数说明 + 返回类型。
  - **实现**：I/O 用 async；可执行错误处理；支持分页；同时返回文本与结构化数据。
  - **注解**：`readOnlyHint` / `destructiveHint` / `idempotentHint` / `openWorldHint`。

### 阶段 3：评审与测试

- 代码质量：无重复、错误处理一致、类型完整、工具描述清晰。
- TypeScript：`npm run build` 验证编译，用 MCP Inspector（`npx @modelcontextprotocol/inspector`）测试。
- Python：`python -m py_compile your_server.py` 验证语法，用 MCP Inspector 测试。

### 阶段 4：建立评测集

用评测验证 LLM 能否用你的服务器回答现实、复杂的问题。生成 **10 个**问题，每个须满足：独立、只读、复杂（需多次工具调用与深挖）、现实、可验证（单一明确答案，可字符串比对）、稳定（答案不随时间变化）。输出为 XML（见 `scripts/example_evaluation.xml`），并可用 `scripts/evaluation.py` 运行。

## 示例

一个 TypeScript 工具的最小骨架（Zod 输入 + 结构化输出 + 注解）：

```ts
import { z } from "zod";

server.registerTool(
  "github_list_repos",
  {
    title: "List repositories",
    description: "List repositories for a user, with pagination.",
    inputSchema: { username: z.string().describe("GitHub username"), page: z.number().int().min(1).default(1) },
    annotations: { readOnlyHint: true, openWorldHint: true },
  },
  async ({ username, page }) => {
    const repos = await client.listRepos(username, page);
    return { content: [{ type: "text", text: JSON.stringify(repos, null, 2) }] };
  },
);
```

Python（FastMCP）等价形态：

```python
from fastmcp import FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("github-server")

class ListReposInput(BaseModel):
    username: str = Field(description="GitHub username")
    page: int = Field(default=1, ge=1, description="Page number")

@mcp.tool
def github_list_repos(params: ListReposInput) -> list[dict]:
    """List repositories for a user, with pagination."""
    return client.list_repos(params.username, params.page)
```

## 参考文档（按需读取）

- `reference/mcp_best_practices.md` — 通用最佳实践：命名、响应格式、分页、传输选择、安全、注解、错误处理。
- `reference/python_mcp_server.md` — Python/FastMCP 完整实现指南（Pydantic v2、`@mcp.tool`、完整示例、质量清单）。
- `reference/node_mcp_server.md` — TypeScript/MCP SDK 完整实现指南（项目结构、Zod、`registerTool`、完整示例、质量清单）。
- `reference/evaluation.md` — 评测集创建指南（问题/答案准则、流程、XML 格式、示例、验证）。
- `scripts/evaluation.py` — 评测运行器；`scripts/example_evaluation.xml` 为评测样例；`scripts/connections.py`、`scripts/requirements.txt` 为依赖与连接辅助。
- 外部：MCP 规范（`https://modelcontextprotocol.io/sitemap.xml`）、[TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)、[Python SDK](https://github.com/modelcontextprotocol/python-sdk)。

## 最佳实践

- ✅ 优先全面 API 覆盖，再按真实任务补高层工作流工具。
- ✅ 工具名 = 统一前缀 + 动作；描述简洁、可发现。
- ✅ 输入/输出都用 schema 约束；返回结构化数据 + 文本摘要。
- ✅ 错误信息给出具体修复建议与下一步。
- ✅ 大数据集必须分页；避免把整页原始 JSON 灌进上下文。
- ✅ 实现后建 10 题评测集，用真实任务验证可用性。
- ❌ 不要为每个端点堆一个无描述、无 schema 的薄包装。
- ❌ 不要用 `destructiveHint: false` 掩盖有副作用的操作。
- ❌ 不要把认证令牌等机密回显到工具输出或错误信息。

## 限制和注意事项

- 本技能覆盖**设计与实现 + 评测**，不含 MCP 服务器的生产部署、托管与运维。
- 具体 SDK API 会随版本演进——实现前应拉取当前 SDK README/规范，不要照搬过时写法。
- 评测集要求目标数据可只读访问且答案稳定；依赖实时变动数据的服务难以建立可验证评测。
- 参考文档为英文（上游原文），正文与触发层为中文。
- 涉及真实第三方 API 时，认证、配额与数据合规由使用者自行确认。

## 安全与安全说明

- 实现工具时遵循最小权限：只读操作标 `readOnlyHint`，破坏性操作标 `destructiveHint` 并要求调用方确认。
- 不在代码、工具输出或错误信息中硬编码或回显 API key / token；用环境变量或密钥管理注入。
- 对会修改外部状态的工具，在描述中明确副作用；必要时要求显式确认参数。
