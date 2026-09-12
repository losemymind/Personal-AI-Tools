# 会话交接（2026-09-12 · 第 32 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main`；与 `origin/main` 同步（上一会话 45f4349 已提交推送）；工作区仅本会话 14 文件改动（待提交后推送）。
- 能力库：`skills/` = **5 技能**、`agents/` = **7 代理**（academic×5 / code-quality×2）。
- 本会话聚焦：**全仓库文档去绝对路径化（跨设备可移植性修复）**——所有 `.md` 文档与脚本 provenance 注释不得含本机路径，否则克隆到其他设备路径即失效。
- 两工作区同构；成品即源；成品自包含；两成品严格零交叉引用。

## 本会话已完成（14 文件，未提交）

### 规则（后续写文档继续遵守）
- **所有文档（`.md`）不得出现绝对文件路径**（含任意驱动器盘符路径）；仓库内路径一律用相对路径或 `<仓库根>/…` 占位符（把 `<仓库根>` 换成克隆仓库的实际路径）。
- 保留项：`https://`/`file://` URI 是资源标识而非文件系统路径（合法）；代码/测试中的**示例字符串**（如 `test_hardening_round4.py` 的 `C:\Users\me`、`run_scenario.py` 注释的 `C:\x`）是测试数据/占位，非路径引用，保留。

### 替换清单（机器特定绝对路径 → 可移植写法）
- 工作区身份描述：两 `AGENTS.md` / 两 `README.md` 中的本机工作区绝对路径 → `agent-creator/` / `skill-creator/`（即本文件所在目录）。
- 库校验命令：`--dir` 处的本机绝对路径 → `--dir <仓库根>/skills|agents`（同时补充「`<仓库根>` = 克隆仓库绝对路径」提示）。涉及：两 `AGENTS.md` 命令段 + agent-creator evolutions audit-round1/2/3/4 + skill-creator evolutions audit-round8、fix-independence。
- 外部仓库来源：本机上的外部仓库绝对路径 → 仓库名相对描述（`personal-workflow` / `UEGameStudio 的 agents/academic`）。涉及：evolutions 2026-09-09-adopt-agent-format-tool.md、`adapt_agent.py`、`build_catalog.py`、`agents/AGENTS-AUDIT.md` 2 处（来源台账保留仓库名，不保留本机路径）。
- audit-round4 中作为 bug 实证的 Windows 路径示例字符串 → 泛化为「Windows 反斜杠路径」。

## 澄清（供参考，非本改动）
- 上上一会话「validate_agents 对技能根 fail-loud」问题已修复并提交（`45f4349`）。
- 上一会话「install.py --creator 无 bug」结论仍成立；`--dir` 解析为 `os.path.abspath`（相对运行目录），文档用 `<仓库根>` 占位符兼容任意平台。

## 发布门实际结果（全绿）

```text
tools（仓库根）        python -m pytest tools/tests -q                 → 25 passed
                       build_catalog.py --check                        → up to date（skills 5 / agents 7）
agent-creator          python -m pytest tests/ -q                      → 101 passed
skill-creator          python -m pytest tests/ -q                      → 206 passed
                       validate_skills.py --strict --dir skills/skill-creator  → Checked 1，全绿
残留扫描               git status → 仅预期 14 文件改动
```

## 未完成项 / 风险 / 下一会话精确待办

1. **待提交推送**：本会话 14 文件改动已过全部发布门，确认后 `git add` + commit + push。
2. **skill 验证器与 agent 验证器语义仍部分对齐**（`risk`/`category`/`evals.json` 形状/refs 互链/正文行数/符号链接等为 skill 侧独有；agent 侧独有边界/协作/完成标准章节与纯 `.md` 发现）——不对称理由目前只在仓库根 `AGENTS.md` 说明，**成品自身文档未解释**（可选补文档）。
3. **`install.py` 扩展（非必须）**：`--dry-run`、批量失败汇总；代理 codex/deepseek 落点若官方明确后再补。
4. **deepseek 落点**：技能 best-effort `~/.deepseek/skills/`；代理 deepseek 无落点（报错）。
5. **PyYAML 为硬运行时依赖**，与根 `AGENTS.md`「纯 stdlib + pytest」措辞不符（CI 每 job `pip install pyyaml pytest`）；实测 PyYAML 6.0.3 / Python 3.11.8。**已知，未改**。
6. **触发评测**：`--mode heuristic` 为词面覆盖代理指标；真机 `--mode cli` 为权威信号。
7. **上一个会话遗留：交互式 install 问答（已 git 还原，不再做）**——用户明确作废，后续勿重启该思路。
8. **去绝对路径纪律**：新增/修改任何文档时复查是否带入新绝对路径（含 evolutions 应急预案里的命令复现）。

## 验证命令备忘

```bash
# tools / 目录（仓库根）
python -m pytest tools/tests -q
python tools/scripts/build_catalog.py --check            # 或直接重生成：python tools/scripts/build_catalog.py

# skill-creator（在 skill-creator/ 根；<仓库根> = 克隆仓库实际绝对路径）
python -m pytest tests/ -q
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator
python skills/skill-creator/scripts/validate_skills.py --strict --dir <仓库根>/skills

# agent-creator（在 agent-creator/ 根）
python -m pytest tests/ -q
python skills/agent-creator/scripts/validate_agents.py --strict --dir <仓库根>/agents

# 对技能根误跑 validate_agents 的可行动提示复现
python skills/agent-creator/scripts/validate_agents.py --strict --dir <任意含 SKILL.md 且无 AGENT.md 的目录>

# 安装（仓库根）
python tools/scripts/install.py --creator skill-creator --creator agent-creator --client opencode --scope workspace --dest <目标仓库根>
python tools/scripts/install.py --all skills --client claude --scope workspace --dest <目标仓库根>
```

## 新会话交接提示（可复制）

```text
读取 HANDOFF.md 交接并继续本仓库工作
```