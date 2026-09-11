# 安全扫描增强：危险管道的常见 shell 混淆归一化

## 基本信息
- 日期：2026-09-11
- 版本：skill-creator 0.9.22 → 0.10.0（本轮批次）
- 触发来源：`| ba"sh"`、`| { bash; }`、`| bash${IFS}` 等刻意变体漏检（`utils.py`；孪生 `security_scan.py` 同款）。

## 决策：已按推荐做法增强，残余极端混淆属静态扫描设计边界，不再作为缺陷
- 采用**有界归一化**（固定、非递归的若干条改写）在右侧 token 判定前规范常见 shell 混淆：
  - `${IFS}` / `${IFS:-…}` / `$IFS` → 分隔空白；
  - 反斜杠转义 `\(.)` → 字符本身（`b\ash` → `bash`）；
  - 游离 `$`（`$(bash)` → `(bash)` → `bash`）；
  - 花括号/圆括号/子壳包裹 `{}()` → 空白（`{ bash; }`、`(bash)`）。
  - **引号/反引号仅在 token 内成对出现时移除**（`ba"sh"` → `bash`）；未成对的单个反引号（Markdown 行内代码 `` `curl x | iex` `` 的收尾）保留，避免把文档里的引用误判为可执行管道。
- 边界（设计决定）：`eval`、变量二次展开、base64 解码后再执行等**需要运行时语义**的混淆不在静态扫描范围内——静态扫描只做确定性的词法归一，覆盖常见规避形态即止。

## 验证结果
- 变体全部检出：`ba"sh"` / `ba'sh'` / `{ bash; }` / `bash${IFS}` / `bash${IFS}-c` / `b\ash` / `(bash)` / `$(bash)` / `sudo -u root ba"sh"` / `irm … | iex`。
- benign 零误报：`grep bash`、`tee out.txt`、`command -v bash`、`a^b`、`` echo `date` ``、`grep -e 'sh'`、`shasum`、`bashful`、`env`。
- 关键回归修复：初版**全局删除**引号/反引号导致成品自身 `.py` docstring 里的 `` `curl x | iex` `` 被误报（`test_skill_creator_docs_pass_security_scan` 失败）；改为「成对才删」后恢复。
- 新增 `tests/test_hardening.py` 1 例 → 本轮 skill-creator pytest 167 → **184**（含本项）。

## 学习点
- **去混淆要有界且方向性**：只去「常见混淆」，并保证对良性用法（非 shell 首 token、行内反引号）零误报；扩大规则前先跑成品自扫描做误报回归。
- **引号处理要看是否成对**：无脑删引号会把 Markdown 行内代码的收尾反引号也删掉，从而把文档引用变成「危险管道」。
