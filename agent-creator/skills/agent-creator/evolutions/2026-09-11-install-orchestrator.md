# 架构：安装编排分层（P1–P4）对 agent-creator 的影响

## 基本信息
- 日期：2026-09-11
- 触发来源：与 skill-creator 同构的 package/install 讨论（设计权威见仓库工具层文档 `tools/README.md`）。用户确认安装编排器 `install.py` 以**完整编排**落地。
- 结论：**打包器 `package_agent.py` 留成品内**；仓库级安装编排由 `tools/scripts/install.py`（dev-only）承担。agent-creator 产物的适配逻辑无需改动。

## 对本成品的影响
- `package_agent.py` **未改动**：它只读 `tools` 真白名单；代理 frontmatter 瘦身后 `tools_clients` 已移除，其客户端标签启发式分支不再被真实数据触发（保留为回退兼容）。
- 安装编排（`tools/scripts/install.py`）负责：自动检测客户端、落点矩阵、staging/放置、自检回滚。**代理落点以 `agents/README.md` 为准**（claude `~/.claude/agents/`、opencode `~/.config/opencode/agent/` 单数；codex/deepseek 无落点则报错）。
- 成品 `SKILL.md` **不引用仓库 `tools/`**（铁律 2 自包含）：跨产物编排只写在 dev-only 文档里。

## 学习点
- **同构分层的两侧一致**：技能侧（package_skill）与代理侧（package_agent）都留成品内，编排下沉到仓库工具层。
- **不越界**：install.py 是仓库工具，不进入创建器产物；创建器仍可独立安装并自用其打包器。
