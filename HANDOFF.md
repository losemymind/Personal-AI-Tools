# 会话交接（2026-09-11 · 第 29 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main`；上会话提交 `0bd46ce` 已推送（`origin/main` 同步）。**本会话改动尚未提交**（待用户确认后收尾提交）。
- 版本：两创建器成品 frontmatter 无 `version`；`skill-creator/README.md` 沿革标记 **0.7.2**（本轮发布门加固）。
- 能力库：`skills/` = **5 技能**、`agents/` = **32 代理**（数量未变；`CATALOG.md` up to date）。
- 本会话聚焦：**加固零交叉引用 / 成品自包含发布门盲区**（交接第 28 版未完成项 2）。
- 两工作区同构；成品即源；成品自包含；两成品严格零交叉引用。

## 本会话已完成（未提交）

### 门禁加固（`.template` + 大小写 + 对等自包含扫描）
- `tools/tests/test_creators_independent.py`：`SCAN_EXTS` 增 `.template`；token 匹配改**大小写不敏感**；抽出 `_scan_for_tokens`，新增两个回归用例——「`.template`/大小写变体必被捕获」与「`evolutions/`+`examples/` 按设计跳过」，并把排除理由写进注释/模块 docstring。
- `skill-creator/tests/test_independence.py` 与 `agent-creator/tests/test_independence.py`（同模板各一份）：同步 `.template` + 大小写不敏感。
- **新增** `skill-creator/tests/test_product_self_containment.py`：镜像 agent-creator 侧——成品**全 md**（fenced 豁免；跳过 `examples/`、`evolutions/`）dev-only/悬空引用扫描 + 成品根布局 slim 断言（无 `AGENTS.md`/`INSTALL.md`）+ 死分支可达性回归。补齐了此前只有 `validate_skills.py`（仅 SKILL.md 反引号引用）的覆盖盲区。
- 成品文档修正：`skill-creator/.../references/skill-anatomy.md` 悬空示意路径 `templates/component.tsx` → 占位形式 `templates/<模板名>.tsx`（探测自包含扫描时发现）。
- 文档同步：`skill-creator/AGENTS.md`（Step 5 发布门 + 硬约束 2）、`skill-creator/README.md`（自包含硬约束 + 0.7.2 沿革）、仓库根 `AGENTS.md` 结构要点（改为「两侧都有自包含 pytest，差异仅在 skill 另有 validate_skills 成品自校验」）。
- 记录：新增 `skill-creator/.../evolutions/2026-09-11-fix-independence-and-self-containment-gates.md`。
- 同步 `.opencode/skills/skill-creator/` 安装测试副本 → 与成品**零漂移**（排除 `__pycache__`）。

### 关键判定（保留的有意排除，非缺陷）
- `evolutions/` 有 39 处兄弟 token 命中，全是历史跨创建器对比/借鉴记录；`examples/` 是上游样例。**保持排除**并补回归测试固定该设计，防止下次审计误判。

## 发布门实际结果（全绿）

```text
tools（仓库根）        python -m pytest tools/tests -q                 → 25 passed
skill-creator          python -m pytest tests/ -q                      → 206 passed
                       validate_skills.py --strict --dir skills/skill-creator  → 1 全绿
                       validate_skills.py --strict --dir <仓库>/skills            → 5 全绿
agent-creator          python -m pytest tests/ -q                      → 100 passed
                       validate_agents.py --strict --dir <仓库>/agents           → 32 全绿
仓库根                 build_catalog.py --check                        → up to date
```

## 未完成项 / 风险 / 下一会话精确待办

1. **待提交**：本会话改动经用户确认后收尾提交（提交前先完成 HANDOFF 收尾——当前已完成验证与文档同步）。
2. **skill 验证器与 agent 验证器语义仍是部分对齐**（`risk`/`category`/`evals.json` 形状/refs 互链/正文行数/符号链接等为 skill 侧独有；agent 侧独有边界/协作/完成标准章节与纯 `.md` 发现）——不对称理由目前只在仓库根 `AGENTS.md` 说明，**成品自身文档未解释**（可选补文档）。
3. **`install.py` 扩展（非必须）**：`--dry-run`、批量失败汇总；代理 codex/deepseek 落点若官方明确后再补。
4. **deepseek 落点**：技能 best-effort `~/.deepseek/skills/`；代理 deepseek 无落点（报错）。
5. **PyYAML 为硬运行时依赖**，与根 `AGENTS.md`「纯 stdlib + pytest」措辞不符（CI 每 job `pip install pyyaml pytest`）；实测 PyYAML 6.0.3 / Python 3.11.8。**已知，未改**。
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
