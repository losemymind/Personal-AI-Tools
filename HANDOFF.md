# 会话交接（2026-09-10 · 第 2 版）

本文件为最近会话的收尾记录，供后续会话快速接续。仓库权威指引是根 `AGENTS.md`（布局/铁律/命令）与两个工作区各自的 `README.md`；本文件只记录**当前上下文与待办**。

## 仓库状态速览

- git：`main`，origin = `losemymind/Personal-AI-Tools`。历史提交：`6824c79` 仓库结构 → `35ca36d` 双创建器工作区/适配器/CATALOG → `46830ca` evals 键名漂移 → `e20fff1` agent 评审闭环 → `79600a2` 加固验证器/评测链 → **本会话续提交**（见下「本会话已完成改动」分组提交）。
- 两工作区**同构精简**（无 `build/`、成品无 `AGENTS.md`、`INSTALL.md` 在工作区根、成品 `SKILL.md` 为唯一入口）；发布检查差异只因**成品自校验能力不同**（skill-creator 有 `validate_skills.py --strict`；agent-creator 自包含扫描落在 pytest）。
- 能力库：`skills/` = **5 技能**（development/code-review-skill、development/mcp-builder、game-development/ue5-performance-optimization、git/pr-summarizer、product-design/prd-generator）；`agents/` = 32 代理（academic×5 / code-quality×2 / ue-game-studio×25）。
- 版本：**skill-creator 0.9.0**、**agent-creator 0.7.0**。
- `opencode.json`（仓库根）用 `instructions` 注册三份 `AGENTS.md`；`.opencode/`（安装测试副本）已 gitignore。

## 本会话已完成改动

**1. skill-creator 参考来源扩为三个**
- `skill-creator/README.md`「来源与沿革」：`anthropics/skills`（深路径链接）、`ComposioHQ/awesome-claude-skills`（新增，官方方法论分发副本）、`antongulin/opencode-skill-creator` 三源；2026-09-09 对比段表述同步为「两个方法论源」。
- `skill-creator/AGENTS.md` SOP「被采纳/参考来源」补 ComposioHQ。均为 dev-only 文档，不 bump 版本。

**2. 上游索引新增两个数据源（skill-creator 0.8.0 → 0.9.0）**
- 用户指定纳入 `anthropics/skills`（`skills/*/SKILL.md`）与 `ComposioHQ/awesome-claude-skills`（**仓库根** `*/SKILL.md`）。
- `scripts/build_index.py`：`SOURCES` 注册两源（别名 `anthropics` / `composiohq`）；`scan_skill_dir` 支持 `skills_root=""`（根级扫描、`path` 无前导 `/`）；`meta.data_source`/`sources` 改为按 `SOURCES` 派生；`--incremental` 刷新元数据并**修正 `skill_count` 被写成单源计数的缺陷**；`cleanup_tmp` 加固为 best-effort（Windows 不可访问路径不再抛错污染退出码）。
- `scripts/search_index.py`：`SOURCE_ALIASES` 增 `anthropics`/`composiohq` 等，帮助文案更新。
- `indexes/upstream.db`：全量重建四源 → **2187 条**（aas 2115 + composiohq 28 + addy 25 + anthropics 19）。
- 文档同步：`references/skill-index.md`、成品 `README.md`、`SKILL.md` 阶段 0、`skill-creator/AGENTS.md`、`INSTALL.md`、工作区 `README.md`。
- 测试：新增 `tests/test_build_index.py`（7 例）+ `test_search_index.py` 别名断言 → skill pytest 41。
- evolutions：`2026-09-10-adopt-index-sources-anthropics-composiohq.md`。

**3. 两个新技能入库（走完整 skill-creator 流程）**
- **`skills/development/mcp-builder/`**（`source: community`）：用户需求与官方 `anthropics/skills` 的 `mcp-builder` description 逐字一致 → **官方导入 + 中文本地化**。保留官方 `reference/`×4 + `scripts/`×4 + `LICENSE.txt`（Apache-2.0），入口 `SKILL.md` 重写为中文并补本地 schema/章节，新增 `evals.json`。对比：本地适配版 0.93 > 官方 0.51 > aas `mcp-tool-developer` 0.75 → 采纳适配版。触发评测 12/12。
- **`skills/game-development/ue5-performance-optimization/`**（`source: self`）：自建，兼顾剖析定位（Unreal Insights/stat/内存）与实现层优化（Tick/GC/Draw Call/Nanite-Lumen-VSM/TSR/Niagara/异步）。含 `references/profiling-toolkit.md` + `references/optimization-patterns.md` + `evals.json`。上游无专门 UE 性能技能（0 命中），与相邻候选 `unreal-engine-cpp-pro` 对比 0.81 vs 0.68 → 采纳自建。触发评测 11/12（「Unity 性能优化」为启发式固有近义假阳性）。
- 合规登记：`skills/SKILLS-AUDIT.md`（3→5 技能，两行 + 数据来源 + evolutions 指针）；`skills/CATALOG.md` 重跑生成器刷新。
- evolutions：`2026-09-10-import-mcp-builder.md`、`2026-09-10-compare-ue5-performance-optimization.md`。
- `.opencode/skills/skill-creator/` 镜像已同步（146 文件逐字节一致）。

## 已知待办 / 潜在风险

1. **真实客户端 CLI 场景未跑通**：本环境嵌套 `opencode run` 返回 server error，skill-creator 量化基准只能以合成 stub 客户端验证**链路**（非真实模型行为）。有可用无头客户端时应补跑 `run_scenario.py` 真机基准。
2. **触发评测为词重叠启发式**：仅代表词面覆盖，不代表真实触发率；`ue5-performance-optimization` 对「Unity 性能优化」的假阳性属固有（性能/优化为核心词不可去），不宜继续为此改描述。
3. **能力库/审计一致性**：`skills/` 现 5 技能、`agents/` 32 代理；增删须同步 `skills/SKILLS-AUDIT.md`/`agents/AGENTS-AUDIT.md` 与两份 `CATALOG.md`，重跑 `python tools/scripts/build_catalog.py`。
4. **已评估、用户明确「不需要修复」的项（勿再主动提出）**：skill-creator 成品 `examples/`（103 文件学习样本）、两份 `indexes/upstream.db`（随成品提交）、能力库 UE/academic 垂直内容——维持现状。
5. **提交纪律（铁律 3）**：任何 git 提交/推送前，必先跑发布门全绿 + 同步受影响的文档（README/审计/CATALOG/evolutions/版本号）+ 更新本 `HANDOFF.md` + 向用户输出可点击复制的新会话交接提示。

## 验证命令备忘

```bash
# agent-creator（在 agent-creator/ 根）——发布门 = 一个 pytest 命令全含
python -m pytest tests/ -q        # 回归 + 成品自包含自检（18 例）

# skill-creator（在 skill-creator/ 根）
python -m pytest tests/ -q                                                    # 41 例
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator
python skills/skill-creator/scripts/validate_skills.py --strict --dir E:\GitHub\Personal-AI-Tools\skills
python skills/skill-creator/scripts/search_index.py --stats                   # 4 源 2187 条

# 能力库（仓库根）
python agent-creator/skills/agent-creator/scripts/validate_agents.py --strict --dir agents  # 32
python skill-creator/skills/skill-creator/scripts/validate_skills.py --strict --dir skills   # 5
python tools/scripts/build_catalog.py
python tools/scripts/build_catalog.py --check
```
