# 会话交接（2026-09-11 · 第 26 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main` @ `5e67152`（上次提交；本会话改动**尚未提交**，工作树 ~95 改 + 11 新增）。
- 版本：两创建器成品 frontmatter **已无 `version`**；技能与代理产物 frontmatter 亦**无 `version`**（版本改以 git 提交 + `evolutions/` 记账）。
- 能力库：`skills/` = **5 技能**、`agents/` = **32 代理**（数量未变；两份 `CATALOG.md` 均已重生成）。
- 新增 **`tools/scripts/install.py`**（安装编排器）+ **`tools/tests/`**（18 例）+ **`tools/README.md`**（工具层设计权威）。
- CI 新增 `tools` job。两工作区同构；成品即源；成品自包含（本会话通过）。

## 本会话已完成（A–F）

### A. 设计文档：`tools/README.md`（新增）

安装编排设计记录：打包器留成品内、新增 `tools/scripts/install.py` 作编排层。**§11 显示 P1–P4 全部完成**。

### B. 技能 frontmatter 瘦身

**最终 schema：`name` / `description` / `risk` / `category`**（移除 `tools`、`tags`、`version`、`author`、`date_added`、`source`、`source_repo`、`source_type`）；**可选字段 `allowed-tools`**（最小权限白名单，保留）。新增 **`skills/SKILL-RECORDS.md`** 创建/来源台账；`create_skill.py --records` 自动追加。`evolutions/2026-09-11-slim-frontmatter.md`。

### C. 代理 frontmatter 瘦身 + 创建记录

- **AGENT.md ×32**：删除 `version`（32）、`tools_clients`（2）、`tags`（32）。保留运行时字段；领域分层由目录结构表达。新增 **`agents/AGENTS-RECORDS.md`** 台账（32 行回填）。`create_agent.py`/`validate_agents.py`/`build_catalog.py`/库文档同步；`evolutions/2026-09-11-agent-frontmatter-records.md`。

### D. package/install P1：`package_skill` 支持 `allowed-tools`

- claude 规范化逗号串；opencode 反查 `CLAUDE_TO_OPENCODE` → 逐工具 `permission`（**不放大权限**）；codex/deepseek 透传；与旧 `tools` 并集。`tests/test_package_skill.py` +8；文档补 `allowed-tools` 可选字段；`evolutions/2026-09-11-package-skill-allowed-tools.md`。

### E. package/install P2：`tools/scripts/install.py` 完整编排

- 新脚本 + `tools/tests/`（18 例）。**自动检测客户端**（环境标记 → 工作区配置目录）、派发打包器、落点矩阵、staging→放置、`--force` 备份、自检 + 索引 `--stats`、失败**回滚**、缓存清理。CLI：`<target>...` / `--all` / `--creator` / `--client`（缺省自动检测）/ `--scope` / `--dest` / `--artifact` / `--force` / `--zip --out`。退出码 0/1/2。

### F. package/install P3+P4：文档收敛 + 记录

- 根 `AGENTS.md`（安装语义改为经 `install.py` + 命令 + CI 说明）、根 `README.md`（结构补 `tools/`、使用方式）、两份 `INSTALL.md`（优先路径注记）、`skills/README.md`、`agents/README.md`、`.github/workflows/validate.yml`（新增 tools job）。
- **成品 `SKILL.md` 不引用 `tools/`**（铁律 2 自包含）——跨产物编排只写在 dev-only 文档。
- 两创建器 `evolutions/2026-09-11-install-orchestrator.md`。

## 发布门实际结果（全绿）

```text
tools（在 tools/ 根或仓库根）
  python -m pytest tools/tests -q                                       → 18 passed
skill-creator（在 skill-creator/ 根）
  python -m pytest tests/ -q                                            → 193 passed
  validate_skills.py --strict --dir skills/skill-creator                → Checked 1，全绿
  validate_skills.py --strict --dir <仓库>/skills                       → Checked 5，全绿
agent-creator（在 agent-creator/ 根）
  python -m pytest tests/ -q                                            → 87 passed
  validate_agents.py --strict --dir <仓库>/agents                       → Checked 32，全绿
仓库根
  build_catalog.py --check                                              → skills/agents 均 up to date
```

## 未完成项 / 风险 / 下一副 agent 精确待办

1. **本会话改动未提交**：`main` 仍 @ `5e67152`。提交前本 HANDOFF 已更新为第 26 版；建议一个 commit 收口（A–F）。
2. **`tools/README.md` P1–P4 全部完成**；如需下一步扩展（非必须）：`install.py` 支持 `--dry-run`、批量失败汇总更详细、代理 codex/deepseek 落点若官方明确后再补。
3. **`allowed-tools` 验证器缺口**：`validate_skills.py` 目前不校验 `allowed-tools` 形状（仅打包时 post-check）；如需静态强制可后续补。
4. **deepseek 落点**：技能 best-effort 约定 `~/.deepseek/skills/`（路径随 harness 版本可能需调整）；代理 deepseek 无落点（报错）。
5. **创建记录台账双库落地**：`skills/SKILL-RECORDS.md` + `agents/AGENTS-RECORDS.md`，由对应 `create_*.py --records` 维护。
6. **索引文档未动**：上游索引 schema（`build_index.py`/`search_index.py`/`build_agent_index.py`/`search_agent_index.py` 的 `source_repo` 等）索引外部仓库，保留。
7. **触发评测**：`--mode heuristic` 为词面覆盖代理指标；真机 `--mode cli` 为权威信号（沿用定性）。

## 验证命令备忘

```bash
# tools（仓库根）
python -m pytest tools/tests -q                                               # 18 例

# 安装能力（自动检测 client / workspace 落点）
python tools/scripts/install.py skills/git/pr-summarizer --client claude --client opencode --scope workspace --dest <目标仓库根>
python tools/scripts/install.py --all skills --scope workspace --dest <目标仓库根>
python tools/scripts/install.py --creator skill-creator --client opencode --scope workspace --dest <目标仓库根>
python tools/scripts/install.py --all agents --client claude --force --scope workspace --dest <目标仓库根>

# skill-creator（在 skill-creator/ 根）
python -m pytest tests/ -q                                                    # 193 例
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator   # 1
python skills/skill-creator/scripts/validate_skills.py --strict --dir E:\GitHub\Personal-AI-Tools\skills   # 5

# agent-creator（在 agent-creator/ 根）
python -m pytest tests/ -q                                                    # 87 例
python skills/agent-creator/scripts/validate_agents.py --strict --dir E:\GitHub\Personal-AI-Tools\agents   # 32

# 能力库 / 目录（仓库根）
python tools/scripts/build_catalog.py --check                                 # up to date

# 创建并记来源台账
python skill-creator/skills/skill-creator/scripts/create_skill.py --name <名> --no-interactive \
  --out <目录> --records skills/SKILL-RECORDS.md \
  --author <作者> --source <self|community|official|URL> --source-repo <OWNER/REPO> --method <created|imported|adapted>
python agent-creator/skills/agent-creator/scripts/create_agent.py --name <名> --no-interactive \
  --out <目录> --records agents/AGENTS-RECORDS.md \
  --author <作者> --source <self|community|official|external|URL> --source-repo <OWNER/REPO|来源名> --method <created|imported|migrated>
```

## 新会话交接提示（可复制）

```text
读取 HANDOFF.md 交接并继续本仓库工作
```
