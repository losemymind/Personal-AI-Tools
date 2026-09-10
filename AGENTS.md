# AGENTS.md — Personal-AI-Tools

本仓库是「个人 AI 工具」的开发源与能力库仓库：维护两个**同构、互不依赖**的创建器技能（可独立安装到 claude / opencode / codex / deepseek），并托管两个**已验证能力库**（`skills/` 技能库、`agents/` 代理库，数据来源登记在审计文件）。不是单一代码库——没有共享依赖、没有包管理清单。

## 布局：两个各自独立的工作区

```
agent-creator/                     agent-creator 技能的工作区（把工作角色蒸馏为 AGENT.md 代理）
  skills/agent-creator/            ← 技能成品 = 唯一源（编辑就在这里）
  AGENTS.md tests/ INSTALL.md README.md   仅 dev：角色守则 + pytest（含成品自包含自检）+ 安装手册 + 工作区说明
skill-creator/                     同上（把工作流蒸馏为 SKILL.md 技能；更成熟，含评测工具链）
  skills/skill-creator/            ← 成品
  AGENTS.md tests/ INSTALL.md README.md   仅 dev：角色守则 + pytest + 安装手册 + 工作区说明
```

- 工作区根可放 `AGENTS.md` 作为 dev-only **角色守则**（两工作区均已建：`agent-creator/AGENTS.md` 与 `skill-creator/AGENTS.md` 各为「成品演进维护者」，前者为后者的同构镜像），随工作区存留、不随成品分发；它与仓库根 `AGENTS.md`（全局布局/铁律/命令）分工不同，也与已删除的「成品内 AGENTS.md」无关——成品根一律不放 `AGENTS.md`/`INSTALL.md`。

- 两工作区**同构**（已统一精简，无 `build/`）：成品 = `SKILL.md` + `README.md`（产品文档，随技能分发）+ `scripts/`/`references/`/`templates/`/`indexes/`/`agents/`/`evolutions/`（`examples/` 为 skill-creator 独有）；工作区根 = `README.md` + `INSTALL.md`（安装手册，不随成品分发）+ `tests/`（仅 dev）+ `AGENTS.md`（角色守则，仅 dev）。成品 `AGENTS.md` 均已删除、`INSTALL.md` 均已移至各自工作区根，**SKILL.md 为唯一入口**。同名不同物，别搞混。
- 根目录 `agents/` 与 `skills/` 是**已验证能力库**（区别于两个工作区 `skills/` 下的创建器成品）：`skills/` = 3 个已验证技能（code-review-skill / pr-summarizer / prd-generator），`agents/` = 32 个已验证代理（academic×5 / code-quality×2 / ue-game-studio×25）。两个「skills」同名不同物：**根 `skills/` = 能力库**、`<creator>/skills/<creator>/` = 创建器成品。
- 环境：纯 stdlib + pytest（无 requirements/锁文件），Python 3.10+（代码用 `X | None` 类型注解，实测 3.11）。

## 能力库（根 `skills/` 与 `agents/`）

- 能力库是**已验证可安装**的技能/代理集合：创建用两创建器（成品在 `<creator>/skills/<creator>/`），校验用同一成品的验证器、目录用根 `tools/scripts/build_catalog.py` 生成：
  ```bash
  python skill-creator/skills/skill-creator/scripts/validate_skills.py --strict --dir skills
  python agent-creator/skills/agent-creator/scripts/validate_agents.py --strict --dir agents
  python tools/scripts/build_catalog.py            # 刷新 skills/CATALOG.md + agents/CATALOG.md
  python tools/scripts/build_catalog.py --check    # 目录过期校验（发布门）
  ```
- **安装 = 复制**：把 `skills/<name>` / `agents/<name>` 复制到目标客户端的 `skills/` / `agents/` 目录（本仓库无 manifest 安装器；落点见各库 `README.md`）。
- `skills/CATALOG.md` 与 `agents/CATALOG.md` 由 `tools/scripts/build_catalog.py` **自动生成**（源自 frontmatter，禁止手改）：LLM 读目录匹配需求 → 命中给复制提示，人类确认后执行；新增/删除/改进能力后**重跑生成器刷新**（发布门校验用 `python tools/scripts/build_catalog.py --check`）。
- **能力库准入与审计**（新增能力入库须同时满足；与两审计文件 `agents/AGENTS-AUDIT.md` / `skills/SKILLS-AUDIT.md` 对应）：
  1. 入库 `agents/` 的代理**必经 agent-creator**（创建/改进 → 验证 → 对比择优），并在 `agents/AGENTS-AUDIT.md` 登记
  2. 入库 `skills/` 的技能**必经 skill-creator**（创建/改进 → 检索上游对比 → 验证），并在 `skills/SKILLS-AUDIT.md` 登记
  3. **参考外部仓库的必须标注数据来源**（对应审计文件的登记字段）
  4. **按功能归入分类目录**（`agents/<顶层分类>/<name>/`、`skills/<分类>/<name>/`），分类不存在则创建；**无「留顶层」例外**
- 审计文件（`agents/AGENTS-AUDIT.md`、`skills/SKILLS-AUDIT.md`，随各自能力库目录存放）是数据来源与入库合规的**唯一记录入口**：新增/迁移/改进能力后同步更新，并把对比择优证据记入对应创建器成品的 `evolutions/`。
- **创建器排除在审计之外**：两个创建器工作区（`agent-creator/`、`skill-creator/`）及其成品是**创建工具**，不是能力库条目，不在能力库审计范围内；它们自身的迭代改进记录走各自成品 `evolutions/`，不做库条目审计登记。

## 三条铁律

1. **成品即源，不复制**：编辑直接改 `skills/<name>/` 下的文件。仓库内不保留任何第二份技能文件副本；不要「建 dev 源再拷贝」，否则产生漂移。
2. **成品必须自包含**：`skills/<name>/` 内文档引用只能指向成品内部（`scripts/`、`references/`、`templates/`、`indexes/`、`agents/`…），**不得引用**工作区的 `tests/`、`INSTALL.md`、README 或仓库其它路径。发布门扫描成品 md 里的反引号引用（fenced 代码块豁免；`examples/`、`evolutions/` 跳过），引用悬空或指向 dev-only 目录即失败。写成品文档时把这条当硬约束。
3. **提交/推送必先收尾交接**：执行 git 提交或推送前，必须先完成收尾——跑通相关发布门/校验并全绿、同步受影响的文档（README / 审计 / CATALOG / evolutions / 版本号），然后**编写或更新新会话交接文件**（仓库根 `HANDOFF.md`：仓库状态速览 + 本会话已完成改动 + 已知待办与风险 + 验证命令备忘），并向用户**输出可点击复制的新会话交接提示**（一段独立代码块，例如「读取 HANDOFF.md 交接并继续本仓库工作」）。收尾未完成、交接文件未就绪，不得提交/推送。

## 命令（在对应工作区根目录执行；提交/推送前必跑）

```bash
python -m pytest tests/ -q           # 回归（两工作区）
```

聚焦单测：`python -m pytest tests/test_validate_agents.py -q`（skill-creator 另含 `test_search_index.py`、`test_quant_eval.py`）。

发布门**因工作区而异**（别想当然）：
- **agent-creator**（成品无自校验脚本——`validate_agents.py` 校验对象是 AGENT.md 代理库，不是技能形态的创建器成品，故自包含扫描落在 dev-only pytest）：
  ```bash
  python -m pytest tests/ -q        # 回归 + 成品自包含自检（引用不悬空、无 AGENTS.md/INSTALL.md 残留）
  ```
- **skill-creator**（成品有自校验能力）：`pytest` 之外，用成品 strict 自检当发布检查：
  ```bash
  python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator
  ```
  （校验成品自身：frontmatter/章节/安全护栏/引用不悬空）

成品自校验（CLI，均支持 `--strict` / `--dir`；不指定 `--dir` 时默认扫对应成品根）：

```bash
python agent-creator/skills/agent-creator/scripts/validate_agents.py --strict --dir <agents目录>   # 校验代理库/目录
python skill-creator/skills/skill-creator/scripts/validate_skills.py --strict --dir <skills目录>   # 校验技能库/目录
```

**CI**：`.github/workflows/validate.yml` 在 push/PR 时复刻上述发布门（两工作区 pytest、成品/库 strict、`build_catalog.py --check`）——是本仓库唯一的自动门禁，改门禁时同步该文件。

## 结构要点

- 两工作区是同构孪生（agent↔skill），dev 布局已统一精简（无 `build/`）。发布检查差异只源于**成品自校验能力不同**：skill-creator 成品是 SKILL.md 技能形态，`validate_skills.py` 能自校验自身；agent-creator 成品的 `validate_agents.py` 校验对象是 AGENT.md 代理库（非技能形态成品），故自包含扫描以 pytest 形式落在 dev-only tests。tests 脚本仍同模板各写一份（仅命名差异，哈希不同）。改一处共享模式时，先想另一侧是否需要同步或删除。
- skill-creator 更完整：评测工具链（`run_eval.py` / `run_loop.py` / `aggregate_benchmark.py`）、子代理提示（`agents/grader|reviewer|comparator|analyzer.md`）、`examples/`、`templates/evals.json.template`。agent-creator 有 validate/search/build/compare/create/adapt + 子代理提示（`agents/reviewer.md`）+ `evolutions/`。
- 脚本通过 `scripts/_project_paths.py` 自定位成品根，不依赖宿主仓库布局；文档可从任意 cwd 以绝对路径调用脚本。
- 约定：产品文档用**中文**撰写（含 frontmatter description）；frontmatter 必须含 `version: "0.x.y"`（新产出物从 `0.1.0` 起步，校验器会查）；`evolutions/` 以 `YYYY-MM-DD-<slug>.md` 记录「上游更优」对比结论（反馈闭环）。
- 改动创建器后跑通 §命令发布门、改动能力库后跑通 §能力库校验并同步审计、重跑 `tools/scripts/build_catalog.py` 刷新 CATALOG 即可推送；**提交/推送前必做收尾交接，见 §三条铁律 3**。

## 权威文档

每个工作区的 `README.md` 是布局与发布指引的权威来源（本文件是其摘要）。改动成品内容前，先读目标工作区的 `README.md` 与成品内 `references/`（按需渐进披露）。
