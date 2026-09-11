# 修复：create_agent.py 脚手架正文工具行与 frontmatter 白名单不一致

## 基本信息
- 日期：2026-09-11
- 对象：`scripts/create_agent.py`、`templates/AGENT.template.md`
- 触发来源：三工作区安装/引导安装集成测试（TestOpenCode / TestCodex / TestClaude）。opencode 真机创建代理时报告：`--tools read,grep,glob` 生成后正文「允许」行仍显示 `read grep bash`，与 frontmatter `tools: [read, grep, glob]` 矛盾（且默认模板正文漏了 `glob`）。

## 证据
- `templates/AGENT.template.md` 正文「工具与权限 → 允许」为硬编码 `read` `grep` `bash`，不随 `--tools` 变化；只有 frontmatter 的 `tools:` 行在 `build_agent_md` 里被替换。
- 非交互 `--tools read,grep,glob` 产出：frontmatter `tools: [read, grep, glob]`，正文「允许：`read` `grep` `bash`」——白名单里的 `glob` 未体现，`bash` 被误列。

## 改动
- `templates/AGENT.template.md`：正文「允许/禁止」改用占位符 `{{ALLOWED_TOOLS}}` / `{{FORBIDDEN_TOOLS}}`。
- `scripts/create_agent.py`：新增 `_render_body_tools(tools)`——从白名单派生正文允许/禁止 prose；`build_agent_md` 替换占位符。
  - **权限一致性**：当白名单含编辑类工具（`edit`/`write`/`patch`，新增 `EDIT_TOOL_ALIASES`）时，移除样板中的 `permission: edit: deny`——否则打包时显式 deny 会覆盖白名单，把用户明确请求的编辑权静默拒绝；正文「禁止」改为「无（编辑类工具已显式列入白名单…）」。
  - 非模板回退分支同步（同一派生逻辑）。
- 新增 `tests/test_create_agent_tools.py`（5 例）：白名单→正文一致（含 bash 不泄漏）、默认 4 工具一致、显式 edit 授权撤销默认 deny、write 别名同理、产出仍 strict 通过。

## 验证结果
- `python -m pytest tests/ -q` → **95 passed**（90 → 95：`test_create_agent_tools.py` +5）
- `python skills/agent-creator/scripts/validate_agents.py --strict --dir <仓库>/agents` → Checked 32，全绿
- `python -m pytest tools/tests -q`（仓库根）→ **23 passed**（独立性/安装回归未受影响）
- 冒烟：`--tools read,grep,glob`、`--tools read,edit`、默认三例的正文与 frontmatter 均一致，`validate_agents.py` 全部通过。

## 学习点
- **脚手架必须自洽**：生成器承诺「产出即通过自身验证」，但验证器只查 frontmatter，正文漂移不会失败——需要专门的「正文与 frontmatter 一致」测试兜底。
- **默认安全值也要服从显式输入**：样板 `permission: edit: deny` 在用户显式 `--tools edit` 时必须让位，否则是「默认值静默覆盖用户意图」的同类缺陷。
