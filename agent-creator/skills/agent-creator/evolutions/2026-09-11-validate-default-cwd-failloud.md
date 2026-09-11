# 验证器修复：缺省扫 0 个仍全绿（fail-open）→ 默认 CWD + fail-loud

## 基本信息
- 日期：2026-09-11
- 版本：agent-creator 0.7.4 → 0.7.5
- 触发来源：`validate_agents.py` 缺省 `--dir` 时目标为成品根 `SKILL_ROOT`（无 AGENT.md）→ 扫 0 个，但因 `explicit_dir=False` 不报错 → **全绿 fail-open**。

## 采纳要点（改了什么）
- 缺省扫描目标由成品根改为**当前工作目录（CWD）**：在代理库/代理目录根运行即可自然生效；`--dir` 仍可指定别处。
- **无论目标来自 `--dir` 还是默认 CWD，扫到 0 个代理定义一律报错（fail-loud，退出码 1）**，并给出清晰提示（含「默认目标是当前工作目录」）。
- 移除 `explicit_dir` 参数与相关分支；更新 `--help` 文案与 `SKILL.md` 阶段 5 说明。
- 孪生 `validate_skills.py` 核对：其 `skill_count == 0` 判定**无条件**报错（早已 fail-loud），无同类 fail-open，未改其默认（技能侧默认自检 `SKILL_ROOT` 是有意且有文档）。

## 验证结果
- 新增 `tests/test_hardening_round5.py` 1 例（空目录 `collect_validation_results` 报「No agent definitions found」且 `validate_agents` 返回 False）。
- 更新 `tests/test_hardening_round1.py`：原「缺省扫成品应 rc=0」改为「默认=CWD：在代理目录运行 rc=0，空 CWD rc=1」。
- agent-creator pytest 64 → **68**；能力库 `agents/`（32 代理）strict 仍全绿（显式 `--dir` 不受影响）。

## 学习点
- **空跑全绿是最隐蔽的门禁漏洞**：验证器的默认目标必须落在「用户自然会在那里运行」的位置（CWD 或库根），且 0 命中必须显式失败，而不是把「没扫到」当「没问题」。
- **孪生要按同一条纪律核对但不必强行同形**：skill 侧默认自检（成品根有 SKILL.md）是合理设计；关键是「0 命中必失败」这条纪律两侧都满足。
