# 会话交接（2026-09-16 · 第 38 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main`；`042b3a9`（创建器上游来源文档补齐）+ `c1a2b3c`（create_agent.py 输出布局修复）+ `b8e0dfe`（ue-editor-lifecycle）+ `ue-layout`（编辑器生命周期技能完善+测试）+ `8fc2504`（create_skill 测试）已提交推送。
- 能力库：`skills/` = **7 技能**、`agents/` = **7 代理**。
- 本会话聚焦：**修复 `create_agent.py` 脚手架输出布局缺陷**（默认扁平单文件 + `--layout dir` + `--out` 误用守卫）。
- 两工作区同构；成品即源；成品自包含；文档一律无绝对路径。

## 本会话已完成

### 创建器 upstream来源文档补齐（已提交 `042b3a9`）
- **背景**：`skill-creator` 成品 `README.md` 已有「上游外部仓库（索引来源）」表（aas/addy/anthropics/composiohq），`agent-creator` 成品 `README.md` 缺对应记录；两工作区 dev `README.md` 同样不对称。
- **改动**：
  1. `agent-creator/skills/agent-creator/README.md`（成品）：新增「上游外部仓库（索引来源）」表（agency 258 / ccgs 49 / agency-zh 261，共 568）。
  2. `agent-creator/README.md`（dev 工作区）：新增「来源与沿革」段（三源索引 + `anthropics/claude-plugins-official` 导入源 + 外部仓库 `personal-workflow` 移植源）。

### 编辑器生命周期技能完善（已提交 `ue-layout`）
- **修复 `ue-editor-lifecycle` 触发评测**（CLI 重新评测）：补充 `打开` 关键词到 description，10/10 passed，precision=100%，recall=100%。
- **新增测试用例**：`skill-creator/tests/test_create_skill.py`（+2 例）。

## 发布门实际结果（全绿，复刻 CI `.github/workflows/validate.yml`）

```text
skill-creator  job   pytest tests/ -q                                            → 206 passed
                     validate_skills.py --strict --dir skills/skill-creator       → Checked 1，全绿
                     validate_skills.py --strict --dir skills（能力库）            → Checked 7，全绿
agent-creator  job   pytest tests/ -q                                            → 116 passed（含成品自包含；本次 +4）
                     validate_agents.py --strict --dir agents（能力库）           → Checked 7，全绿
catalog        job   build_catalog.py --check                                    → up to date（skills 7 / agents 7）
tools          job   pytest tools/tests -q                                       → 25 passed
smoke                create_agent.py 两布局产物 validate_agents.py --strict       → 2 agents 全绿
CLI 触发评测          10/10 passed（ue-editor-lifecycle）
```

## 未完成项 / 风险 / 下一会话精确待办

1. `.opencode/skills/` 未纳入 git（本地安装副本，含 `ue-editor-lifecycle`）。

## 验证命令备忘

```bash
# skill-creator（在 skill-creator/ 根）
python -m pytest tests/ -q
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator   # 成品自检
python skills/skill-creator/scripts/validate_skills.py --strict --dir <仓库根>/skills        # 能力库校验

# 触发评测（权威 = CLI）
python skills/skill-creator/scripts/run_eval.py --eval-set <技能目录>/evals/evals.json --skill-dir <技能目录> --mode cli --client opencode --model deepseek/deepseek-v4-flash --timeout 150 --concurrency 6

# agent-creator（在 agent-creator/ 根）
python -m pytest tests/ -q
python skills/agent-creator/scripts/validate_agents.py --strict --dir <仓库根>/agents

# tools / 目录（仓库根）
python -m pytest tools/tests -q
python tools/scripts/build_catalog.py --check
python tools/scripts/install.py --all skills --client opencode --scope workspace --dest <目标仓库根>
```

## 新会话交接提示（可复制）

```text
读取 HANDOFF.md 交接并继续本仓库工作
```
