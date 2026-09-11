# 审计闭环：第四轮定向加严（脚手架 YAML 安全 + --out 路径冲突 + 描述校验边界）

## 基本信息
- 日期：2026-09-10
- 版本：agent-creator 0.7.3 → 0.7.4
- 触发来源：HANDOFF 第 9 条「下一步精确待办」——攻 `adapt_agent.py` 四端 post-check 边界与 `create_agent.py` 脚手架在非 ASCII/多行 description 下的产物合法性；先运行期实证最近一轮（第三轮）修复是否真生效，再逐条复现新缺陷。

## 最近一轮修复生效性复核（运行期探针，非仅看测试变绿）
- PowerShell 反引号 / CMD 脱字符续行、引号/子壳 shell token、`SENSITIVE_DOTFILES`、隐藏目录 `.ssh/id_rsa`/`.aws/credentials`、backtick 引用 fail-open：**逐项实证已改变且无误报回归**（`command -v bash`、`grep bash`、`curl x | grep bash` 均不误报）。

## 本轮新发现并修复（3 项）

1. **`create_agent.py` 模板替换用 f-string 当 `re.sub` 替换串 → 反斜杠/多行 description 产物非法（高，正确性/契约）**：`build_agent_md` 用 `re.sub(pattern, f"description: {_yaml_str(desc)}", ...)` 替换，替换串会经过 `re` 的反斜杠转义处理。实证：description 含 Windows 路径（`C:\Users\me`）或 `\d+` 时，JSON 转义的 `\\` 被折叠成 `\` → 产出**非法 YAML**（`ScannerError`）；含换行 `\n` 时 JSON 的 `\n` 被还原成真实换行 → YAML 折叠为空格，**内容静默丢失**。孪生 `create_skill.py` 早已用 lambda 替换，属孪生不对称。修复：`description`/`version`/`tools`/`mode` 四处统一改为 `lambda m: ...`。
2. **`create_agent.py` 缺 description 长度/空白校验（中，契约）**：docstring 承诺「Output validates with validate_agents.py」，但 >300 字符或纯空白的 description 会照写，产物立即被自己的验证器拒绝。修复：前置拒绝 `len > 300` 与非空白（对齐 `create_skill.py` 的 1024 校验）。
3. **`--out` 路径冲突未捕获 → 原始 traceback（中，健壮性/契约）**：`create_agent.py` 与 `adapt_agent.py` 在 `--out` 指向已存在目录、或路径父级是文件时抛出未捕获的 `FileExistsError`/`PermissionError`/`FileNotFoundError`，而非文档承诺的「干净报错、rc=1」。修复：`create_agent` 增加 `--out` 非目录检查 + `mkdir` `try/except OSError`；`adapt_agent` 增加目录检查 + 写入 `try/except OSError`（对齐 `create_skill.py` 已有的同类处理）。

> 附带（文档-行为一致性，低）：`adapt_agent.py` 文档块「content passes through byte-identical」与实际不符（`utf-8-sig` 读取会去掉 BOM，文本模式换行翻译亦非逐字节），按 HANDOFF 记录的待收敛项改为准确措辞。

## 采纳要点（改了什么）
- `scripts/create_agent.py`：模板替换改 lambda；description 长度/非空白前置校验；`--out` 目录检查 + `mkdir` OSError 捕获。
- `scripts/adapt_agent.py`：`--out` 目录检查 + 写入 OSError 捕获；passthrough 文档措辞收敛。
- 测试：新增 `tests/test_hardening_round4.py` **6 例** → agent-creator pytest **58 → 64**。
- 版本 0.7.3 → 0.7.4。

## 验证结果
- `python -m pytest tests/ -q`：**64 passed**（原 58 + 新 6）。
- `validate_agents.py --strict --dir E:\GitHub\Personal-AI-Tools\agents`：Checked 32，全绿。
- `search_agent_index.py --stats`：3 源 568 条。
- `build_catalog.py --check`：up to date。
- 运行期探针：反斜杠/多行 description 由「非法 YAML / 内容丢失」变 YAML 解析往返一致；300/301 边界与空白描述正确拒绝；`--out` 目录/父级为文件由 traceback 变干净 rc=1。

## 学习点
- **`re.sub` 的替换串不是字面量**：任何用户内容拼进替换串都要走 lambda（或 `re.escape`），否则反斜杠转义既会破坏 YAML，也可能触发组引用；这是孪生实现易漂移的典型点（`create_skill` 对、`create_agent` 错）。
- **脚手架的价值是「产物必过自己的门」**：断言必须用真实 YAML 解析器做往返，而非子串检查——多行/反斜杠只有在解析往返里才暴露。
- **写路径冲突是契约的一部分**：`--out` 是目录、父级是文件都应走干净错误分支，不能把 `OSError` 冒泡成 traceback。
