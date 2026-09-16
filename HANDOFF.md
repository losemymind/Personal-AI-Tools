# 会话交接（2026-09-16 · 第 38 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main`；`042b3a9`（创建器上游来源文档补齐）+ `c1a2b3c`（create_agent.py 输出布局修复）+ `ue-editor-lifecycle` 已提交推送。
- 能力库：`skills/` = **7 技能**、`agents/` = **7 代理**。
- 本会话聚焦：**修复 `create_agent.py` 脚手架输出布局缺陷**（默认扁平单文件 + `--layout dir` + `--out` 误用守卫）。
- 两工作区同构；成品即源；成品自包含；文档一律无绝对路径。

## 本会话已完成

### 创建器 upstream来源文档补齐（已提交 `042b3a9`）
- **背景**：`skill-creator` 成品 `README.md` 已有「上游外部仓库（索引来源）」表（aas/addy/anthropics/composiohq），`agent-creator` 成品 `README.md` 缺对应记录；两工作区 dev `README.md` 同样不对称。
- **改动**：
  1. `agent-creator/skills/agent-creator/README.md`（成品）：新增「上游外部仓库（索引来源）」表（agency 258 / ccgs 49 / agency-zh 261，共 568）。
  2. `agent-creator/README.md`（dev 工作区）：新增「来源与沿革」段（三源索引 + `anthropics/claude-plugins-official` 导入源 + 外部仓库 `personal-workflow` 移植源）。

### 新技能：`skills/ue-editor-lifecycle`（已提交 `b8e0dfe`+`ue-layout`）

- **流程**：严格走 skill-creator 方法论——`create_skill.py` 生成骨架 → 编写正文（源码构建版本 `InstalledBuild.txt` 配置、检查并结束已运行实例、异步启动编辑器）→ `validate_skills.py --strict` → 触发评测（heuristic → CLI 补 `.md` → CLI 重新评测，10/10 通过）→ 入库 → `build_catalog.py` → `install.py`。
- **命名**：`ue-editor-lifecycle`（描述性、聚焦编辑器生命周期）。
- **内容**：概述（安全关闭/重建/异步启动，避免卡死与 MCP 无响应）/ 何时使用（启动/重启/PIE/MCP未响应/DLL占用/Build失败等）/ 工作原理（检查结束实例→源码构建配置→构建编辑器→异步启动）/ 4 个完整示例/最佳实践/常见问题/限制。262 行，含 `evals/evals.json`（10 条触发用例）。
- **关键设计**：
  1. **源码构建版本特殊配置**：在 `Engine\Build\InstalledBuild.txt` 让引擎被视为安装版本，避免重建时连引擎一起构建。
  2. **检查并结束已运行实例**：启动前先 `Stop-Process -Name "UnrealEditor" -Force`，避免 DLL 占用。
  3. **异步启动**：使用 `Start-Process` 避免 PowerShell 阻塞与卡死。
- **记录**：`skills/SKILL-RECORDS.md` 追加一行（source_repo `-`，method `created`）。
- **清理**：无（首次创建）。

- **触发评测调整（CLI 补 `.md`）**：补充 `打开` 关键词到 description，10/10 passed，precision=100%，recall=100%。

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
2. **上报中的错误路径未清理**：外部仓库 `E:\GitHub\UEGameStudio\UEGameStudio\agents\technical\performance-architecture-specialist\`（空目录，0 项）仍在；真正的扁平文件 `performance-architecture-specialist.md` 同级、未跟踪。本次**未触碰**该仓库，如需清理须用户明确指示。

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
