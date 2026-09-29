# 真实测评证据审计复核

日期：2026-09-29。复核对象为 `evidence-audit.json`、原始 `stdout.jsonl` 中的工具状态与输出、原生角色加载记录，以及仍保留的临时目录。未修改原始运行证据、评分或首份审计报告。

## 换行差异与第二份审计

两处 `native_prompt_differs_from_installed_role_body` 均为换行表示误报：

| 运行 | 原生 prompt 长度 | 读取后的 Markdown 正文长度 | 原生 CRLF 数 | 换行归一后的正文 |
|---|---:|---:|---:|---|
| runtime/with_skill/run-1 | 2869 | 2798 | 71 | 逐字符相同 |
| runtime/old_skill/run-1 | 2575 | 2497 | 78 | 逐字符相同 |

JSON 保留了 OpenCode prompt 的 CRLF；`Path.read_text()` 将 Markdown 中的换行转换为 LF。长度差分别正好等于 CRLF 个数，无额外字符差异。

审计器只在该项比较前将 CRLF、CR 统一为 LF，保留原有首尾 `strip()`；未折叠内部空白。离线回归确认三种换行等价，内部空格减少或正文字符变化仍会判失败。

`evidence-audit-v2.json` 结果：

- `integrity_ok=true`、`evidence_complete=true`。
- 计划 17 次；记录了 16 条模型调用命令，16 个运行有本地 assistant 模型元数据。
- 8 次触发、6 次场景、2 次角色运行成功；无技能组的角色因适配失败未启动模型调用，不补算为第 17 次。
- 冻结协议、输入和产品哈希一致；已保存产物哈希、技能发现、输入完整性均通过；配置凭据精确匹配数为 0。
- 15 条工具观察仍原样保留，以下给出人工判读。

首份 `evidence-audit.json` 的 SHA256 在修改前后均为：

```text
3dc9f51601e4f4aa292fb0ddc577683b5b031ec9acaee64d311e52854885218f
```

## 工具观察逐项复核

15 条观察来自 13 个不同工具调用。表中的序号沿用各运行在审计报告内的 finding 顺序；同一工具调用可能同时因路径与命令被记录。

| 运行 / finding | 工具调用 ID | 分类与原始输出核验 |
|---|---|---|
| creation / old_skill / 1 | call_00_GCqP0XVY3rbsZf07RUNW6544 | **路径识别误报**。命令实际读取本工作区 `outputs/agents/release-evidence-auditor.md`；扫描器把正则 `description:\s*` 尾部的 `n:\s*` 误认成盘符路径。输出仅有行数和 description，exit=0。 |
| creation / without_skill / 1 | call_00_34C6s69NYIwcWTmCXEc24979 | **探测隔离的空用户目录**。三个路径均展开到该运行专有的 `agent-live-env-26uqyorg/home/`，原始输出全部为 absent；未读到真实全局配置或旧工具。该动作涉及工作区外探测，应保留为范围观察。 |
| repair / old_skill / 1 | call_00_WoLCDpQ2o819KlvtgtSF9571 | **被拒绝的外部写入尝试**。拟写同运行 `temp/opencode/audit-bug-triager.py`；状态 error，错误明确为 external_directory 权限规则阻止，未成功执行写入。 |
| repair / without_skill / 1 | call_00_JRr60k5cqpBuCRj33Rp85313 | **调用已安装客户端查询版本**。实际执行 OpenCode `--version`，输出 1.18.30、exit=0；无模型调用或创建器脚本读取。 |
| repair / without_skill / 2 | call_00_RHpJ8NUF4jFTWkLhH8u38224 | **调用已安装客户端查询帮助**。实际输出 OpenCode CLI 帮助；没有启动 run 子命令。 |
| repair / without_skill / 3 | call_00_XivKDMjwlMkNXWXUi5Z53273 | **调用客户端代理命令帮助**。输出 `agent --help`，子进程 exit=1；工具 completed 仅表示 shell 调用结束，不能将该返回码描述为验证成功。未运行模型。 |
| repair / without_skill / 4 | call_00_00HDmarSOlx1onOyK9AL3468 | **确认的工作区外临时复制**。在工作区外的同运行 `temp/opencode/native-check/` 建目录，并将本次自生成 AGENT.md 复制进去。输出为 `.opencode/agent/bug-triager.md`、copied，exit=0。保留目录中该文件确实存在，SHA256 与本次保留的源 AGENT.md 相同；不是来自全局工具或其他组。 |
| repair / without_skill / 5 | call_00_ET_Uh6OAcWlmXhSMMK1YC1W4197 | **被拒绝的外部工作目录调用**。拟在 native-check 中执行 `agent list`，external_directory 阻止执行。 |
| repair / without_skill / 6 | call_00_ET_Uh6OAcWlmXhSMMK1YC1W4197 | 与上一行是**同一被拒绝调用**的 EXE 路径观察，不另算一次执行。 |
| repair / without_skill / 7 | call_00_qBUuUCdaEjAXNXZBX3Hk3802 | **被拒绝的重试**。改用 Windows 短路径后再请求外部 workdir，仍被 external_directory 阻止。 |
| repair / without_skill / 8 | call_00_qBUuUCdaEjAXNXZBX3Hk3802 | 与上一行是**同一被拒绝重试**的 EXE 路径观察，不另算一次执行。 |
| repair / without_skill / 9 | call_00_c51OVkBMSuZlUxX8ckpO3533 | **本工作区内的原生加载检查**。把自生成 AGENT.md 放入本工作区 `.opencode/agent/` 后调用 `agent list`；输出该本地文件 tools 数组 schema 错误，exit=1。未成功加载，也未读取外部创建器。 |
| repair / without_skill / 10 | call_00_uKXBUiNguPjI1wbYj53O4580 | **本工作区内的适配后加载检查**。改用本次输出的 OpenCode 适配包后 `agent list` exit=0，列出客户端内建角色及本地 bug-triager；输出未涉及全局创建器脚本。没有运行角色或新增模型请求。 |
| repair / without_skill / 11 | call_00_CjiukWsL09mnORQvWRS34179 | **被拒绝的清理尝试**。命令同时涉及工作区内 `.opencode` 和工作区外 native-check；工具调用被 external_directory 拒绝，无执行输出。 |
| repair / without_skill / 12 | call_00_DAL6NQRxo008k3Z1uEqf0987 | **被拒绝的清理重试**。改用短路径仍被 external_directory 拒绝；外部 native-check 文件在复核时仍存在。 |

分类合计：1 条路径误报、1 条隔离空用户目录探测、5 条本机客户端版本/帮助/本地加载检查、7 条对应 5 次被拒绝调用的观察、1 条确认的工作区外复制。

## 判断与边界

在这 15 条观察及对应原始输出中，**未发现读取真实全局旧创建器、借用其他组技能或调用外部创建器脚本的污染证据**。原生客户端 EXE 是运行环境提供的公共工具；查询帮助或加载当前组自生成文件，不构成引入创建器成品。

无技能修复组确有一次成功的工作区外写入，仍位于该运行专有临时环境且来源为自身产物，应完整保留这一事实。冻结 B10 禁止输入改动、全局安装及工作区外创建器/验证器借用，不能将同次隔离 state 下的临时原生加载检查自动等同于组污染或据此剔除该组。该动作对冻结断言的影响由主代理与独立评分者判断。

对应复制证据另存 `audit-review-copy-evidence.json`，包含工具 ID、完整目标路径、保留源路径与两份相同的 SHA256。目标位于 `agent-live-env-82fuv_z4/temp/opencode/native-check/`，不是真实全局用户配置目录。不能把环境变量隔离与 external_directory 权限视为操作系统沙箱。

上述分类解释证据，不改动冻结断言、原始评分或执行成功状态。`integrity_ok=true` 表示记录、哈希、模型观测等完整性检查通过，不表示所有模型动作都符合任务范围。模型身份仅由 OpenCode 本地 assistant 会话元数据证明；费用与底层权重仍未验证。
