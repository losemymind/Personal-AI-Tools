# 会话交接（2026-09-11 · 第 27 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main` @ `6f62cb5`（上次提交）；本会话改动**已提交**（见下，待推送）。
- 版本：两创建器成品 frontmatter 无 `version`（版本以 git + `evolutions/` 记账）。
- 能力库：`skills/` = **5 技能**、`agents/` = **32 代理**（数量未变；`CATALOG.md` 均 up to date）。
- 本会话聚焦：**allowed-tools 验证器校验**、**两创建器零交叉引用独立性**、**LLM 自安装文档化**、**install.py 修复**、**create_agent 脚手架修复**、**三工作区端到端集成测试**。
- 两工作区同构；成品即源；成品自包含（本会话通过）。

## 本会话已完成

### A. 验证器：静态校验 `allowed-tools`
- `skill-creator/.../scripts/validate_skills.py` 新增 `check_allowed_tools()`，**复用** `package_skill` 的 `normalize_allowed_tools`/`CLIENT_LABELS`/`PackageError`（验证器与打包器判定不漂移）；拒绝 dict 形式/非字符串项/空表/纯客户端标签列表。`tests/test_validate_skills.py` +6；`references/quality-bar.md` 补注。`evolutions/2026-09-11-validate-allowed-tools.md`。

### B. 文档修正：`skill-anatomy.md`
- 第 1 部分字段清单与瘦身后 schema 对齐（删误列的 `source` 必需、`risk` 去重），`skill-anatomy.md` ← 唯一修正点。

### C. 零交叉引用独立性 + 自安装
- 删除两成品全部对端引用（相关技能段、docstring/注释里的对端名称与脚本名）——**严格零交叉引用**（用户选定更严口径）。
- 新增门：`tools/tests/test_creators_independent.py`（名称中英 + 脚本名 + 无跨成品 import）；两工作区 `tests/test_independence.py`（成品复制到**仓库外**仍可自校验/自跑工具链）。
- 两 `SKILL.md`「多客户端安装指引」新增 **`### 自安装`**（LLM 客户端直接执行 6 步：定位→作用域/端→整目录复制→自检→清缓存→交付；成品自包含，不引用 `tools/`）。`evolutions/2026-09-11-independence-and-self-install.md` ×2。

### D. 修复 `tools/scripts/install.py`（真实缺陷）
- `validate_install` 原盲跑所有自带 `validate_*.py` → `--creator agent-creator` 被其分发的 `validate_agents.py` 误校验（技能形态目录无 AGENT.md）而**回滚 rc=1**。修：**验证器仅在产物含对应入口文件时运行**（`validate_skills.py`→`SKILL.md`、`validate_agents.py`→`AGENT.md`）。`tools/tests/test_install.py` +2。`tools/README.md` §5.4 + 沿革。

### E. 修复 `create_agent.py` 脚手架（真实缺陷）
- 模板正文「允许」行硬编码 `read grep bash`，与 `--tools` 白名单矛盾（且默认漏 `glob`）。修：正文由白名单派生（`_render_body_tools` + 模板占位符 `{{ALLOWED_TOOLS}}`/`{{FORBIDDEN_TOOLS}}`）；白名单含编辑类工具（`edit`/`write`/`patch`）时移除样板 `permission: edit: deny`（防显式 deny 静默覆盖用户授权）。`tests/test_create_agent_tools.py` +5。`evolutions/2026-09-11-fix-create-agent-tool-body.md`。

### F. 三工作区端到端集成测试（未入库，外部目录）
- `E:\GitHub\Personal-AI-Tools_TestOpenCode`：`install.py` 装两创建器 → 已装 skill-creator 建 `changelog-writer`(命中 7)/`schema-drift-audit`(命中 0)、已装 agent-creator 建 `code-reviewer`(3)/`quantum-ops-runner`(0) → `install.py` 落库产物。**全通过**。
- 同目录清空后：**opencode CLI v1.18.18 引导自安装**两创建器 + CLI 真机创建上述四个产物。**全通过**（修复后复测）。
- `Personal-AI-Tools_TestCodex`（`.agents/skills`）与 `_TestClaude`（`.claude/skills` + `.claude/agents`）：`install.py` 装创建器 + 四产物，strict 全过；codex 代理**无落点按设计 rc=1**；claude 代理 frontmatter 适配为 `tools: Read, Grep, Glob`。**全通过**。

## 发布门实际结果（全绿）

```text
tools（仓库根）        python -m pytest tools/tests -q                 → 23 passed
skill-creator          python -m pytest tests/ -q                      → 202 passed
                       validate_skills.py --strict --dir skills/skill-creator  → 1 全绿
                       validate_skills.py --strict --dir <仓库>/skills            → 5 全绿
agent-creator          python -m pytest tests/ -q                      → 95 passed
                       validate_agents.py --strict --dir <仓库>/agents           → 32 全绿
仓库根                 build_catalog.py --check                        → up to date
```

## 未完成项 / 风险 / 下一副 agent 精确待办

1. **本次改动已提交、未推送**：`main` 领先 `origin/main` 1 个提交（收尾提交）。如需共享执行 `git push`。
2. **测试工作区为外部产物**（`E:\GitHub\Personal-AI-Tools_Test{OpenCode,Codex,Claude}`，不在本仓库、未提交）：如需保留证据可自行归档；否则可删除。
3. **`install.py` 扩展（非必须）**：`--dry-run`、批量失败汇总更详细、代理 codex/deepseek 落点若官方明确后再补。
4. **deepseek 落点**：技能 best-effort `~/.deepseek/skills/`；代理 deepseek 无落点（报错）。
5. **`package_agent` 不改正文 prose**：claude 端 frontmatter 适配为 `Read, Grep, Glob` 而正文保持小写工具名（语义一致，非缺陷）；如需正文同步属新需求。
6. **触发评测**：`--mode heuristic` 为词面覆盖代理指标；真机 `--mode cli` 为权威信号。

## 验证命令备忘

```bash
# tools / 目录（仓库根）
python -m pytest tools/tests -q
python tools/scripts/build_catalog.py --check

# skill-creator（在 skill-creator/ 根）
python -m pytest tests/ -q
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator
python skills/skill-creator/scripts/validate_skills.py --strict --dir E:\GitHub\Personal-AI-Tools\skills

# agent-creator（在 agent-creator/ 根）
python -m pytest tests/ -q
python skills/agent-creator/scripts/validate_agents.py --strict --dir E:\GitHub\Personal-AI-Tools\agents

# 安装（仓库根）
python tools/scripts/install.py --creator skill-creator --creator agent-creator --client opencode --scope workspace --dest <目标仓库根>
python tools/scripts/install.py --all skills --client claude --scope workspace --dest <目标仓库根>
```

## 新会话交接提示（可复制）

```text
读取 HANDOFF.md 交接并继续本仓库工作
```
