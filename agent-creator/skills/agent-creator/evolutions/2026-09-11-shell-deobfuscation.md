# 安全扫描增强：危险管道的常见 shell 混淆归一化（孪生同步）

## 基本信息
- 日期：2026-09-11
- 版本：agent-creator 0.7.4 → 0.7.5
- 触发来源：与 skill-creator 同批——`| ba"sh"`、`| { bash; }`、`| bash${IFS}` 等变体在 `security_scan.py` 漏检。

## 采纳要点（改了什么）
- `security_scan.py` 增加与 skill 侧 `utils.py` **同款的有界归一化**（保持孪生一致）：
  - `_normalize_shell_text()`：`${IFS}`/`$IFS` → 空白、反斜杠转义还原、游离 `$` 去除、`{}()` 括号/子壳包裹 → 空白；
  - `_normalize_token()`：token **内部成对**的引号/反引号移除（`ba"sh"` → `bash`）；**未成对**的单个反引号保留，避免把 AGENT.md/代码 docstring 里的行内代码引用误判为可执行管道。
- 边界同 skill 侧：`eval`/二次展开/base64 等需要运行时语义的混淆不在静态扫描范围。

## 验证结果
- 变体全部检出、benign 零误报（`grep bash`/`tee`/`command -v bash`/`a^b`/`` echo `date` ``/`grep -e 'sh'`）。
- 新增 `tests/test_hardening_round5.py`（本项 3 例：端到端变体检出、端到端 benign 无误报、模块直测）。
- agent-creator pytest 64 → **68**。

## 学习点
- **孪生安全逻辑要逐份对照**：一份实现的补丁不会自动出现在另一侧；本项与 skill 侧同批修改，避免再次出现不对称。
- **去混淆与误报的平衡点**：引号只在成对时移除，才能既覆盖混淆又不误伤 Markdown 行内代码。
