# 会话交接（2026-09-16 · 第 37 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main`；`042b3a9`（创建器上游来源文档补齐）已提交推送；本会话另有「create_agent.py 输出布局修复」改动待提交。
- 能力库：`skills/` = **7 技能**、`agents/` = **7 代理**。
- 本会话聚焦：**修复 `create_agent.py` 脚手架输出布局缺陷**（默认扁平单文件 + `--layout dir` + `--out` 误用守卫）。
- 两工作区同构；成品即源；成品自包含；文档一律无绝对路径。

## 本会话已完成

### 缺陷修复：`create_agent.py` 输出布局（未提交）
- **证据（真实使用）**：在某 UE 项目扁平代理库中执行脚手架，产出 `agents/technical/performance-architecture-specialist/performance-architecture-specialist/AGENT.md`（双层嵌套），而客户端实际加载的是同级扁平文件 `agents/technical/performance-architecture-specialist.md`。
- **根因两层**：① 布局硬编码为 `<out>/<name>/AGENT.md`，但 `validate_agents.py` 早已同时接受「目录 AGENT.md」与「带 frontmatter 的顶层 `*.md`」两种等价形态；② `agent_dir = out_dir / name` 无条件追加名字，`--out` 已指向代理自身目录时静默加深一层，**成功退出码 + 错误路径**。
- **方案（用户确认）**：默认改**扁平** `<out>/<name>.md`；新增 `--layout {flat,dir}`（dir 用于需捆绑 `references/` 或库以 `AGENT.md` 为键的场景）；`out_dir.name == name` 时 fail loudly（rc=1）；目标已存在时拒绝（统一不覆盖）。
- **改动文件**：`scripts/create_agent.py`、`tests/test_create_agent_tools.py`（+4 例）、`tests/test_hardening_round1.py`、`tests/test_hardening_round4.py`、`SKILL.md`（解剖段 + 阶段 3）、`references/agent-anatomy.md`、成品 `README.md`、`agents/README.md`（补「本库条目须加 `--layout dir`」——`install.py` 按 `AGENT.md` 定位，扁平形态不会被收录）、`evolutions/2026-09-16-create-agent-flat-layout-default.md`。
- **孪生观察（未改，跨工作区须用户点名）**：`create_skill.py` 同为 `<out>/<name>` 拼接，但技能**无扁平形态**（`validate_skills.py` 要求目录内 `SKILL.md`），故布局本身正确；仅「`--out` 误用守卫」是对称可选项。

### 创建器上游来源文档补齐（已提交 `042b3a9`）
- **背景**：`skill-creator` 成品 `README.md` 已有「上游外部仓库（索引来源）」表（aas/addy/anthropics/composiohq），`agent-creator` 成品 `README.md` 缺对应记录；两工作区 dev `README.md` 同样不对称。
- **改动**：
  1. `agent-creator/skills/agent-creator/README.md`（成品）：新增「上游外部仓库（索引来源）」表（agency 258 / ccgs 49 / agency-zh 261，共 568）。
  2. `agent-creator/README.md`（dev 工作区）：新增「来源与沿革」段（三源索引 + `anthropics/claude-plugins-official` 导入源 + 外部仓库 `personal-workflow` 移植源）。

### 新技能：`skills/development/ue-editor-lifecycle`（已提交 `b8e0dfe`）

- **流程**：严格走 skill-creator 方法论——`create_skill.py` 生成骨架 → 编写正文（源码构建版本 `InstalledBuild.txt` 配置、检查并结束已运行实例、异步启动编辑器）→ `validate_skills.py --strict` → 触发评测（heuristic → CLI 微调）→ 入库 → `build_catalog.py` → `install.py`。
- **命名**：`ue-editor-lifecycle`（描述性、聚焦编辑器生命周期）。
- **内容**：概述（安全关闭/重建/异步启动，避免卡死与 MCP 无响应）/ 何时使用（启动/重启/PIE/MCP未响应/DLL占用/Build失败等）/ 工作原理（检查结束实例→源码构建配置→构建编辑器→异步启动）/ 4 个完整示例/最佳实践/常见问题/限制。262 行，含 `evals/evals.json`（10 条触发用例）。
- **关键设计**：
  1. **源码构建版本特殊配置**：在 `Engine\Build\InstalledBuild.txt` 让引擎被视为安装版本，避免重建时连引擎一起构建。
  2. **检查并结束已运行实例**：启动前先 `Stop-Process -Name "UnrealEditor" -Force`，避免 DLL 占用。
  3. **异步启动**：使用 `Start-Process` 避免 PowerShell 阻塞与卡死。
- **记录**：`skills/SKILL-RECORDS.md` 追加一行（source_repo `-`，method `created`）。
- **清理**：无（首次创建）。

### 触发评测调整（关键改进）
- **heuristic 初始结果**：9/10（FN：`LaunchUE.bat 如何使用`）。
- **调整方案**：将 `query` 从"如何使用"改为"启动编辑器失败"，匹配 description 中的触发关键词。
- **最终结果**：**10/10 passed，precision=100%，recall=100%**。

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
CLI 触发评测          未运行（本次无技能/描述变更）
```

## 未完成项 / 风险 / 下一会话精确待办

1. **待提交推送**：`create_agent.py` 输出布局修复（11 个文件，见上）已过全部发布门，确认后 `git add` + commit + push。
2. **上报中的错误路径未清理**（用户明确「只加守卫，不动 UEGameStudio」）：外部仓库 `E:\GitHub\UEGameStudio\UEGameStudio\agents\technical\performance-architecture-specialist\`（空目录，0 项）仍在；真正的扁平文件 `performance-architecture-specialist.md` 同级、未跟踪。本次**未触碰**该仓库。
3. **孪生对称可选项**：`create_skill.py` 的「`--out` 误用守卫」未加（布局本身正确，仅守卫缺失）——属跨工作区，须用户点名后再动。
4. **`ue-editor-lifecycle` 无 CLI 触发评测**：后续建议补 `--timeout 150` 固定超时的 CLI 评测。
5. **`.opencode/skills/` 未纳入 git**（本地安装副本，含 `ue-editor-lifecycle`）。

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
