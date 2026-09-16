# 修复：create_agent.py 脚手架输出布局（默认扁平单文件 + --layout dir + --out 误用守卫）

## 基本信息
- 日期：2026-09-16
- 触发来源：真实使用缺陷报告——在某 UE 项目（扁平代理库 `agents/<分类>/<name>.md`）中执行脚手架，产出 `agents/technical/performance-architecture-specialist/performance-architecture-specialist/AGENT.md`，而该客户端实际加载的是同级的扁平文件 `agents/technical/performance-architecture-specialist.md`。
- 对象：`scripts/create_agent.py`、`tests/test_create_agent_tools.py`、`tests/test_hardening_round1.py`、`tests/test_hardening_round4.py`、`SKILL.md`（解剖段 + 阶段 3）、`references/agent-anatomy.md`、成品 `README.md`。

## 缺陷分析（两层）

1. **布局硬编码（主因）**：脚手架只会写 `<out>/<name>/AGENT.md`，但 `validate_agents.py` 早已同时接受两种等价形态（`AGENT.md` 目录形态，或**带 frontmatter 的顶层 `*.md`**，见 `validate_agents.py` 候选发现逻辑）。代理定义并非只有目录形态一种——`adapt_agent.py` / `package_agent.py` 也都接受裸文件。脚手架却把目录形态当成唯一形态，于是**无法产出扁平库/客户端 agent 目录直接加载的单文件形态**。
2. **`--out` 误用静默加深（放大因）**：`agent_dir = out_dir / name` 无条件追加名字。当 `--out` 已经指向代理自身目录（`.../<name>`）时，脚本不报错而是产出 `<name>/<name>/AGENT.md` 的深度嵌套——错误路径静默落地，无人加载也无人报警。

证据：报告中的错误路径恰为双层嵌套，且同级存在真正的扁平文件；`validate_agents.py --strict` 对两种形态均通过（证明形态合法，缺陷在脚手架的产出选择与守卫）。

## 采纳方案（用户确认后实施）

- **默认扁平输出**：`<out>/<name>.md`（多数客户端 agent 目录与扁平库直接加载的形态）。
- **`--layout {flat,dir}`**：默认 `flat`；需捆绑 `references/`、或目标库以 `AGENT.md` 为键时用 `dir` 输出 `<out>/<name>/AGENT.md`。
- **`--out` 误用守卫**：当 `out_dir.name == name` 时 fail loudly（rc=1）并提示 `--out` 应为父/分类目录——宁可报错也不产出无人加载的深度嵌套。
- **存在即拒绝**：目标文件/目录已存在时拒绝（不再区分「目录已存在」与「文件已存在」，两种布局统一不覆盖）。
- 校验指引随布局变化：`--dir {target.parent}`（扁平 → 库目录；目录形态 → 代理目录）。

## 验证

```text
python -m pytest tests/ -q                     → 116 passed（112 + 新增 4：默认扁平/--layout dir/守卫拒绝/存在即拒绝）
python scripts/validate_agents.py --strict --dir <两种布局混合目录> → All agents passed（2 agents）
```

- 回归改动：原先断言 `<out>/probe/AGENT.md` 的用例改为断言默认扁平 `<out>/probe.md`；`--layout dir` 另有用例覆盖目录形态。
- 能力库未受影响：本仓库 `agents/` 条目仍为目录形态，`install.py` 按 `AGENT.md` 定位的契约未变（`agents/README.md` 已补「库条目须加 `--layout dir`」提示）。

## 提炼的学习点

- **「唯一必需产物」不等于「唯一合法形态」**：验证器接受两种形态时，脚手架若硬编码一种，就会在合法但不同约定的目标库中静默产出错误路径。工具链的形态支持面应与验证器对齐。
- **路径拼接要有「我自己会追加名字」的守卫**：任何 `out_dir / name` 型 CLI 都应检测 `out_dir` 末级是否已是 `name`——否则用户/AI 把 `--out` 当产物目录用时，错误会以**成功退出码 + 错误路径**的形式静默发生，比直接失败危险得多。
- **默认值随生态选择**：扁平单文件是大多数客户端 agent 目录直接加载的形态，作为默认更贴合「复制即生效」；目录形态作为显式选项保留给需要捆绑资源的代理。
