# 字段→纪律：agent frontmatter 增加 color（UI 显示色）

## 基本信息
- 日期：2026-09-12
- 需求：Agent frontmatter 添加 `color` 字段（如 `color: "#DC2626"`），作为可选 UI 显示色。
- 依据：opencode AgentConfig 原生支持 `color`（hex `#RRGGBB` 或主题名）；库内 academic×5 迁移时已自带 `color`；`adapt_agent.py` opencode post-check 早已校验 color（`check_opencode_frontmatter`），但**规范层面**它此前只被归为「opencode 专属字段」，验证器对未知字段一律忽略——即字段在「使用」却不在「契约」里。

## 现状与缺口
- `validate_agents.py`：忽略未知字段（forward-compatible），`color` 无格式校验 → 错误值静默通过。
- `create_agent.py`：不产出 color。
- 文档：`references/agent-template.md` 将 `color` 列在「代理专属字段（opencode）」；SKILL.md 字段示例无 color。
- **YAML 陷阱**：`#` 开头是注释，`color: #DC2626` 解析为 `None`；hex 值必须加引号（`color: "#DC2626"`）。academic×5 自带颜色均已加引号，是正确示范。

## 改动清单
- `scripts/validate_agents.py`：新增 `color` 校验（存在时须为 `#RRGGBB` hex 或主题名否则报错；**缺省不报错**——color 是可选字段）。
- `scripts/create_agent.py`：新增 `--color`；**agent-creator 创建时始终包含 `color`**（交互式带默认值询问，`--no-interactive` 默认 `#DC2626`；无效值前置拒绝 rc=1）。
- `templates/AGENT.template.md`：加一行注释示例 `# color: "#DC2626"`；`create_agent.py` 创建时将其激活为实际值。
- `references/agent-template.md`：`color` 移入**规范可选字段**（写明引号要求、明确「可选，缺失不报错」），兼容矩阵补一行（opencode ✅ / claude、codex、deepseek 透传），质量检查清单补 color 检查项。
- `SKILL.md`：前置元数据字段示例补 `color: "#DC2626"` 行（注明创建时始终包含）。
- 库：`agents/code-quality/code-reviewer` 补 `color: "#DC2626"`（用户指定），`code-simplifier` 补 `color: "#2563EB"`；academic×5 保持迁移自带色。
- 测试：`tests/test_validate_agents.py` +6（hex 过/主题名过/非法报错/未引号 hex 报错/无 color 通过/稀疏 permission advisory）、`tests/test_create_agent_tools.py` +6（注入引号并验证/主题注入/默认色/全量矩阵/编辑授权/非法前置拒绝）。

## 验证结果
```text
agent-creator  python -m pytest tests/ -q                     → 109 passed（原 101，+8）
               validate_agents.py --strict --dir agents       → Checked 7，全绿
               build_catalog.py --check (仓库根)               → up to date
```

## 学习点
- **字段要被契约化，先落验证器再写文档**：`color` 已在 adapt 层被校验、在库中被使用，却不在规范契约里——「验证器忽略未知字段」的 forward-compatible 是双刃剑，容易让新字段停留为「事实用法」而非「明文纪律」。文档化一个字段时，应同步补验证器校验，否则无效值会静默招摇过市。
- **YAML 注释即陷阱**：hex 颜色以 `#` 开头，不带引号会整行变注释、值变 `None`。因此（a）文档必须写明引号要求，（b）验证器把 `None` 判为错误，用机器强制人记住引号。
- **库内已有用法是最佳先例**：academic×5 迁移自带已引号 hex 颜色，直接采作规范形态（引号 + 6 位 hex）的实物证据，不必另造格式。