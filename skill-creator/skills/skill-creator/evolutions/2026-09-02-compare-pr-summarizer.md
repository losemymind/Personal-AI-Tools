# 对比记录：pr-summarizer（自建） vs comprehensive-review-pr-enhance（上游）

## 基本信息
- 日期：2026-09-02
- 需求：从 git diff 生成结构化的 PR 总结，配审查清单与风险标注
- 上游候选：上游仓库（`sickn33/agentic-awesome-skills`）的 `skills/comprehensive-review-pr-enhance`（83 行，2 文件，risk: critical）
  - 注：`skills/...` 在此指上游仓库路径，非本仓库的 `skills/` 目录

## 对比分析

### 上游优势（采纳到自建版）
1. **变更分类表**：source/test/config/docs 分类驱动清单——比模糊的"总结一下"结构化
2. **类别驱动的审查清单**：按 diff 中出现的文件类别动态加清单项，避免盲目铺满
3. **大 diff 分拆建议**：>20 文件或 >1000 行时提示按 feature 分拆
4. **风险标注**：breaking/安全敏感文件（auth/crypto/token/password 路径）/大 diff 显式标注

### 上游缺口（自建版的差异化）
1. **语义化标题建议**：无 type/scope 格式建议（PR 标题优化）
2. **一句话摘要优先**：PR 全文太长时先给执行摘要
3. **受众分层**：对人（reviewer）完整版 vs 对机器（自动通知/记录）精简版
4. **与 code-reviewer 代理协作衔接**：技能产出交代理复检的明确路径

## 结论
- **自建 pr-summarizer**（借鉴上游精华 + 差异化定位：轻量快速总结 + 标题建议 + 协作衔接）
- 对比评估：上游在"为审查者完整增强"上更强；自建在"个人工作流中快速 PR 总结"场景更贴合
- 采纳确定：自建 + 吸收上游分类表/清单/分拆/风险规则

## 提炼的学习点
- 技能设计上"类别驱动清单"优于"固定清单"：规则随输入内容自适应
- "先给摘要再给细节"是 LLM 输出的人性化分层：读者可快速跳读