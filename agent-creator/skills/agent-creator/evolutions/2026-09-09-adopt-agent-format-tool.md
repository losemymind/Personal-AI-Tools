# 纪律→工具：移植四端安装适配器 adapt_agent.py（对齐可安装性承诺）

## 基本信息
- 日期：2026-09-09
- 需求：用户确认把 CATALOG 生成器所在来源（`E:\GitHub\personal-workflow`）的另一工具 `tools/scripts/agent_format.py` 移植为本成品工具——把「安装到四端」从文档承诺兑现为确定性工具。
- 上游候选：`E:\GitHub\personal-workflow\tools\scripts\agent_format.py`（claude/opencode 的 frontmatter 转换 + post-check 适配层；原为 install_agent.py / update_agent.py 的共享库）。
- 本成品缺口证据：`references/agent-template.md` 整段描述该转换语义却推给**不存在的「宿主安装器」**（与上次清掉的 `install_agent.py` 幽灵引用同源悬空）；`agents/` 库以 `tools: [...]` 数组规范形存文件，直接复制到 opencode/claude 可能无法加载，仓库无任何工具保证「复制即能装」。

## 对比分析
- 上游 agent_format.py 是纯适配逻辑（无 CLI、无文件 I/O 外接），被 install/update launcher import。
- 本仓库**刻意无 install launcher（安装=复制）**：直接照搬上游会得到无人 import 的孤儿模块。故移植形态为「复制前转换器」CLI：输入仓库规范 AGENT.md/目录 → `--client` → 输出目标客户端合法 AGENT.md（`--out` 写盘或 stdout）→ 失败即 exit 1 不产出。
- 保留上游全部转换语义：opencode tools 白名单 → permission（allow/deny + 显式条目优先、write/patch 折叠到 edit）；claude tools → 逗号串（Claude 大写名映射、无映射名丢弃并记 note、全无映射拒绝）；model → alias（sonnet/opus/haiku/inherit 或删除）；codex/deepseek 无官方 schema → YAML 校验后逐字节原样。每端 post-check（对齐 opencode config.json AgentConfig / claude subagent schema）违规即 AgentFormatError。

## 结论
- 优者：移植上游适配逻辑 + 按本仓库「无 launcher」形态包成 CLI → 采纳。
- 落点：`scripts/adapt_agent.py`（成品脚本，随技能分发）；SKILL.md 阶段 7 +「多客户端安装指引」+ FAQ 指向它；`references/agent-template.md` 三处「宿主安装器/安装器」改为指向 adapt_agent.py（悬空表述清除）；产品 README 脚本树补条目。
- 版本：0.5.0 → **0.6.0**（minor，新增能力）。测试：agent pytest 9 → 16（+7：opencode 转换/显式权限胜出/write→edit 折叠/claude 映射+model alias/全无映射拒绝/codex 逐字节原样/缺路径失败/--out 写盘）。

## 提炼的学习点
- 「描述中的承诺」若指向不存在的工具就是文档悬空：写文档时凡声称「某工具会自动…」，要么该工具有真实落点，要么改成具体工具路径。agent-template 的「宿主安装器」与 anatomy 的幽灵 install_agent.py 是同一类债。
- 移植「被 launcher import 的纯逻辑库」到「无 launcher」仓库时，形态要重构：给纯逻辑加 CLI 壳，并让它有真实调用方（阶段 7 安装指引），否则产生新孤儿。
- 转换类工具的价值在 fail loudly：宁可 exit 1 也不产出客户端无法加载的文件——这与验证器「目录不存在即报错」是同一纪律（不产生静默假绿）。
