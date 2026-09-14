# 会话交接（2026-09-14 · 第 35 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main`；上一会话的 agent `color`/全量 permission 改动已提交推送（`bea635a`）；本会话新增技能待提交。
- 能力库：`skills/` = **6 技能**（新增 `coding-discipline`）、`agents/` = **7 代理**。
- 本会话聚焦：**按 skill-creator 方法论从上游整理新技能 `coding-discipline`**（来源 `multica-ai/andrej-karpathy-skills`，MIT，四条 LLM 编码行为准则）。
- 两工作区同构；成品即源；成品自包含；文档一律无绝对路径。

## 本会话已完成（未提交）

### 新技能：`skills/development/coding-discipline`
- **流程**：严格走 skill-creator 阶段 0→9——`search_index.py` 检索上游（命中 `andrej-karpathy`）→ `create_skill.py` 生成骨架 → 编写正文 → `validate_skills.py --strict` → 触发评测（heuristic + CLI）→ `compare_skills.py` 对比择优（**自建 0.76 > 上游 0.73**）→ 入库 → `build_catalog.py` → `install.py`。
- **命名**：`coding-discipline`（描述性、纪律取向，不直译人名；四条准则统一于「克制 + 验证」）。
- **内容**：概述 / 何时使用 / 工作原理（四条准则：想清楚再动手、保持简洁、只改必要部分、以可验证目标驱动）/ 示例（含正反例）/ 最佳实践 / 相关技能 / 常见问题 / 限制。137 行，含 `evals/evals.json`（13 条触发用例）。
- **记录**：`skills/SKILL-RECORDS.md` 追加一行（source_repo `multica-ai/andrej-karpathy-skills`，method `adapted`）；对比证据 `evolutions/2026-09-14-compare-coding-discipline.md`。
- **清理**：删除上一模型基于同一来源创建的劣质技能 `simple-coding-principles`（关键词堆砌 description + 破碎正文），并清理 `.opencode/skills/` 中的孤儿副本。

### 触发评测（关键教训）
- **heuristic 为词面覆盖代理**（description 与 query 共享 ≥2 个有义 token 即判触发），**可被关键词堆砌刷到满分**——上一模型正是塞入 40+ 无意义英文动词（含 `procurerepair` 拼写错误）刷到 100%。
- 本次坚持写**自然可读** description，heuristic 得 **7/12（precision 100%）**，属该代理对广触发行为技能的固有假阴，非缺陷。
- **权威信号是 `--mode cli`**（真实 opencode 派发，结构化判定）：延长超时（150s）后 **13/13，precision=100%，recall=100%**。两次短超时运行出现过波动（`重构`/`调试` 偶发未触发）与 1 次 run_error——run_error 与描述无关，不动 description。
- 结论：**评估广触发技能优先用 CLI 模式；不要为刷 heuristic 分而污染 description。**

## 发布门实际结果（全绿）

```text
skill-creator          python -m pytest tests/ -q           → 206 passed
                       validate_skills.py --strict --dir skills/skill-creator（成品）→ 全绿
                       validate_skills.py --strict --dir <仓库根>/skills（能力库）  → Checked 6，全绿
agent-creator          python -m pytest tests/ -q           → 112 passed
tools（仓库根）         python -m pytest tools/tests -q      → 25 passed
                       build_catalog.py --check             → up to date（skills 6 / agents 7）
CLI 触发评测           run_eval.py --mode cli --client opencode --model deepseek/deepseek-v4-flash → 13/13
```

## 未完成项 / 风险 / 下一会话精确待办

1. **待提交推送**：本会话改动（`skills/development/coding-discipline/`、`skills/CATALOG.md`、`skills/SKILL-RECORDS.md`、`skill-creator/.../evolutions/2026-09-14-compare-coding-discipline.md`）已过全部发布门，确认后 `git add` + commit + push。
2. **`skills/CATALOG.md` 中 `coding-discipline` 的用途列**取自 description（含中英文触发词），偏长；如需更简洁可调整 description 或接受现状。
3. **CLI 触发评测的非确定性**：opencode 派发依赖模型判断，同一描述跨运行会有波动（1-2 条差异）。后续回归建议固定 `--timeout 150` 并接受小幅波动。
4. **skill 验证器与 agent 验证器语义仍部分对齐**（见上一版第 2 条，未变）。
5. **`install.py` 无 `--dry-run`**；重复安装已存在落点会报「already exists」（需 `--force`），批量安装时属预期噪声。
6. **PyYAML 为硬运行时依赖**（与根 `AGENTS.md`「纯 stdlib」措辞不符）；实测 PyYAML 6.0.3 / Python 3.11.8。**已知，未改**。
7. **`.opencode/skills/` 未纳入 git**（本地安装副本），`coding-discipline` 已安装其中。

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
