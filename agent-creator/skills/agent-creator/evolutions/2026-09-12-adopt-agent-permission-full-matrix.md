# 纪律→模式：agent permission 尽量全（默认拒绝 + 逐键显式）

## 基本信息
- 日期：2026-09-12
- 需求：agent frontmatter 中的 `permission` **尽量全**（用户举例：UEGameStudio `qa/security-engineer.md` 的全量矩阵形态），把「最小权限」从一两个键的样板升级为完整声明。
- 参照形态（UEGameStudio security-engineer 示例 + 本库 academic×5 已用）：

```yaml
permission:
  "*": deny
  read: allow
  glob: allow
  grep: allow
  list: deny
  ...
  edit: deny
  task: deny
  lsp: deny
  external_directory: deny
```

## 现状与缺口
- 之前规范将对 opencode 的完整 permission **延迟到安装时生成**（`adapt_agent.py` 把 `tools` 白名单物化为逐键 permission）——仓库规范形只带 `edit: deny` 样板；code-quality 二代理是稀疏矩阵（`edit: deny, write: deny`）。
- 缺点：规范形不"全"，拿到即缺大多数字段；稀疏矩阵在 opencode 默认语义下未被显式覆盖的键受客户端默认支配；安全审查价值低。

## 改动清单
- `scripts/create_agent.py`：新增 `PERMISSION_ORDER`（13 键全量）+ `_render_permission()`——由 `--tools` 白名单生成 `"*": deny` + 逐键显式 allow/deny（`write`/`patch` 折叠到 `edit`）；模板 permission 块整体替换。
- `templates/AGENT.template.md`：permission 改为全量矩阵示例（默认拒绝 + 逐键，注释标注「尽量全」）。
- `scripts/validate_agents.py`：新增 **advisory**（不 fail）——`permission` 存在但缺 `"*": deny` 时提示补全量矩阵；缺失 permission 仍按原最小权限 warning 处理。
- `references/agent-template.md`：示例 frontmatter 改为全量矩阵；字段说明的 `permission` 词条写「尽量全」纪律。
- `SKILL.md`：前置元数据字段示例改用全量矩阵片段；质量清单补「permission 尽量全」项。
- 库：code-reviewer/code-simplifier 由稀疏矩阵升级为全量矩阵（按各自 `tools` 白名单生成）。
- 测试：脚手架默认产全量矩阵、编辑授权在矩阵中 allow、case-insensitive；验证器稀疏矩阵 advisory 不 fail。
- 适配验证：`adapt_agent.py --client opencode` 对全量矩阵 + color 冒烟通过（合并后无漂移，自动补 `todowrite: deny`）；claude 端 tools→Claude 名、color/permission 透传正常。

## 验证结果
```text
agent-creator  python -m pytest tests/ -q                     → 112 passed（+11）
               validate_agents.py --strict --dir agents       → Checked 7，全绿
               build_catalog.py --check                       → up to date
冒烟           create_agent --tools read,grep,glob → validate → adapt opencode/claude 全通过
```

## 学习点
- **「全」比「少」更安全**：最小权限的可靠表达是「默认拒绝 + 显式放行」，稀疏矩阵的缺口语义取决于客户端默认，跨用户/跨端不可预测；把默认动作写死（`"*": deny`）才是跨端稳定的最小权限。
- **验证器用 advisory 而非 error 推进软性纪律**：`尽量全` 是方向而非硬性契约，缺 `"*": deny` 给提示不拦发布；而「缺失 permission」仍保持 fail-loud。区分「必须」与「提倡」的强制强度。
- **规范形先全、安装形只减不增**：规范 AGENT.md 直接呈现完整 permission，客户端适配仅做工具名/形态映射（opencode 合并后增加未声明键的 deny，即「只收窄不放宽」），与「复制即装载、绝不放大权限」纪律一致。