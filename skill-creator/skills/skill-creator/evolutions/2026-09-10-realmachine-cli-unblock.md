# 采纳升级：打通真机无头 CLI（并修其暴露的 4 处评测链缺陷）

## 基本信息
- 日期：2026-09-10
- 需求：HANDOFF 待办 1——量化评测链只在合成 stub 上验证过链路，缺真机端到端。本次尝试在真实 `opencode` 无头 CLI 上跑通，并把暴露的缺陷修掉。
- 来源：本仓库自审 + 真机实测（模型 `deepseek/deepseek-v4-flash`，经 `opencode run`）。

## 环境诊断（为何此前「嵌套 opencode run 报 server error」）
- 根因：`~/.config/opencode/opencode.json` 的顶层 `model` 指向不存在的 provider `siliconflow/deepseek-ai/DeepSeek-V4-Flash`，每次运行 `ProviderModelNotFoundError`（表现为 `UnknownError`）。
- 解法：`opencode run -m <provider>/<model>` 显式指定模型即可正常返回——**无需改全局配置**。真机链路因此可用。

## 真机暴露并修复的缺陷（合成 stub 无法发现）
1. **cli 模式无法指定模型**（阻断）：`run_eval`/`run_scenario`/`run_loop` 的 cli 调用不接受 model，默认模型配错时全部 run_error。修复：三处均加 `--model` 并透传（opencode 用 `-m`，claude 用 `--model`）；`run_scenario` 去掉无效的 `OPENCODE_MODEL` 环境变量写法。
2. **触发判定假阳性**（严重）：原判定是「技能名出现在整段输出里」——实测「帮我写单元测试」被误判为触发，实为模型跑 `Get-ChildItem` 列出 `.opencode\skills\skill-creator` 路径所致，并非技能被加载。修复：`detect_triggered()` 改为只认**客户端派发技能工具**（opencode `tool_use` 事件中 `tool=="skill"` 且 `input.name==技能名`）；未建模的客户端回退子串匹配。
3. **`summarize()` 对 cli 结果 KeyError**：cli 结果用 `trigger_rate`，heuristic 用 `triggered`；`summarize` 只认后者 → 真机一跑就崩。修复：`_is_triggered()` 归一化两种形状，按同一阈值派生。
4. **`run_scenario` 工具计数恒 0**：真机事件类型是 `tool_use`（`part.type=="tool"`），原代码只数顶层 `type=="tool"`。修复：`count_tool_calls()` 兼容 `tool_use`。
5. **`run_eval` 缺 `--timeout`**：真机单条查询耗时不定，原 60s 硬编码易超时。修复：暴露 `--timeout`。

## 真机触发证据（部分）
- 受控实验：临时工作区装 skill-creator，跑「把这个工作流做成一个技能」→ 事件流出现 `tool:"skill"` / `input.name:"skill-creator"`，模型确实加载并进入流程（真触发确认）。
- 6 条子集实跑：在修复判定前跑出 1 run_error（超时）+ 2 pass；判定修复后的完整重跑因**单条查询耗时过长、命令卡死**被用户中止——完整真机基准**仍待**在有充裕时间/更稳客户端时补跑（不改结论：链路已打通、判定已可信）。

## 版本
- `0.9.3 → 0.9.4`（patch：评测链 cli 能力与判定修复）。

## 验证
- `python -m pytest tests/ -q`：61 例全绿（新增 5 例：model 透传×2、summarize cli 形状、真触发判定、opencode tool_use 计数）。
- 成品 strict 自检 + 能力库 strict 全通过。
- `.opencode/skills/skill-creator/` 镜像同步。

## 学习点
- **合成 stub 证明不了判定正确**：stub 只能证明「链路能跑」，无法暴露「判定标准错」——真机第一次跑就发现假阳性来自路径字符串，这是本次最有价值的发现。
- **环境报错要追根因，别接受『不可用』**：此前记的「嵌套 opencode run 必报错」实为一处配置笔误；显式 `-m` 即可绕过，成本极低。
- **真机基准要有时间预算**：无头 LLM 单条查询可达数十秒，循环评测须配合 `--timeout` 与分批跑，否则易卡死。
