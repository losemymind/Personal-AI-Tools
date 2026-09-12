# 审计闭环：第三轮对抗式交叉验证（续行绕过 + 隐藏目录 + 引用回退假通过）

## 基本信息
- 日期：2026-09-10
- 版本：agent-creator 0.7.2 → 0.7.3
- 触发来源：对「两成品已达标」结论做**最终独立交叉验证**——主动构造同类变体、换角度攻击面（续行绕过、隐藏目录凭据、验证器假通过），逐条运行期实证。与 skill-creator 第七轮同批进行。

## 本轮新发现并修复（agent 侧 3 项 + 共享 2 项）

1. **PowerShell 反引号 / CMD 脱字符续行绕过（中，安全）**：`curl x ` + 换行 + `| iex`、`curl x ^` + 换行 + `| cmd` 把管道拆行漏检。修复：`find_dangerous_pipes` 归一化阶段合并续行；**仅当续行后紧跟 `|`**，避免吞掉 Markdown 围栏首行反引号（初版无条件合并造成围栏检测回归，已纠正）。
2. **引号/子壳包裹的 shell token 绕过（中，安全）**：`curl x | "bash"`、`curl x | (bash)`、`curl x | $(bash)` 漏检。修复：新增 `_normalize_token` 剥离配对引号与 `(`/`$(`/`)`；`| grep "(bash)"`、`| python -c "bash"` 仍不误报。
3. **隐藏目录整体跳过（中，安全覆盖缺口）**：`check_dir_security` 跳过 `.` 开头目录，而凭据常驻 `.ssh/`、`.aws/` → 捆绑的 `.ssh/id_rsa`、`.aws/credentials` 不可见（实证 0 命中）。修复：安全扫描下钻隐藏目录，仅跳过 VCS/缓存噪声（`SECURITY_SKIP_DIRS`）。
4. **无扩展名凭据文件名补强（中，覆盖缺口）**：`SENSITIVE_DOTFILES` 补 `credentials`（`.aws/credentials` 文件名无扩展名）、`.gitconfig`、`.bashrc`、`.zshrc`、`.profile`、`.bash_profile`、`.secrets`。
5. **backtick 引用回退 `SKILL_ROOT` 造成假通过（中，验证器 fail-open）**：`validate_agents.py` 在本地解析不到反引号引用时会回退到 agent-creator 自己的 `SKILL_ROOT`。实证：AGENT.md 写 `` `references/agent-anatomy.md` ``（本地不存在、agent-creator 内存在）→ `--strict` 全绿。skill 侧早已移除同款回退（理由：外部产物不得「借用」创建器内部路径）。修复：移除该回退，只按代理自身目录解析；缺失引用正常报错。

> 与 skill 侧的孪生差额：`curl/wget | iex` 与 `SENSITIVE_DOTFILES` 两项是 skill 侧落后于 agent 侧，已在 skill-creator 第七轮补齐（见其 `evolutions/2026-09-10-audit-round7.md`）。

## 采纳要点（改了什么）

- `scripts/security_scan.py`：`find_dangerous_pipes` 合并 PowerShell/CMD 续行；新增 `_normalize_token` 并用于 `_segment_runs_shell`；`SENSITIVE_DOTFILES` 补无扩展名凭据名。
- `scripts/validate_agents.py`：新增 `SECURITY_SKIP_DIRS`，`check_dir_security` 下钻隐藏目录；移除反引号引用的 `SKILL_ROOT` 回退。
- 测试：新增 `tests/test_hardening_round3.py` **5 例** → agent-creator pytest **53 → 58**。
- 版本 0.7.2 → 0.7.3。

## 验证结果

- `python -m pytest tests/ -q`：**58 passed**（原 53 + 新 5）。
- `validate_agents.py --strict --dir <仓库根>/agents`：Checked 32，全绿（移除回退后库 32 代理无悬空引用）。
- `search_agent_index.py --stats`：3 源 568 条，完整性 OK。
- `build_catalog.py --check`：skills / agents 目录均 up to date。
- 运行期探针：续行/引号/子壳绕过由漏检变检出；隐藏目录凭据 0 → 2 命中；假通过变为明确报错；benign 用例零误报。

## 学习点

- **验证器的「便利回退」就是 fail-open**：为让本仓自身路径可解析而回退到创建器根目录，会让任何代理的悬空引用被静默放过；解析基准必须锁定被校验产物自身。
- **安全扫描的盲区常在「没被 walk 到」的文件**：跳过 dotdir 使 `.ssh/`、`.aws/` 这类凭据高发目录整体不可见，比正则漏检更隐蔽。
- **续行符与 shell 包裹是一整类等价写法**：`\`/`` ` ``/`^` 续行，`"`/`'`/`()`/`$()` 包裹，都要按语义等价类覆盖，且改动后必须做误报回归。
