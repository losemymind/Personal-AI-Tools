# skill-creator

创建自定义 Skill 的目录。本技能是**技能创建器**：把用户的真实工作流蒸馏为可复用、可验证、跨客户端安装的高质量技能，走「先查后建（检索上游）→ 创建 → 对比择优 → 自动验证 → 触发测试 → 安装 → 回馈」的完整闭环。方法遵循：证据驱动、渐进式披露、自由度匹配脆弱性、高信号命名、迭代测试循环、触发优化与治理化验证。完整方法论见 `SKILL.md`（唯一入口）。

## 工具命名与迁移

命令行入口统一使用 `skill_<用途>.py`；索引工具使用 `skill_index_<动作>.py`。共享模块使用 `skill_utils.py` 与 `skill_events.py`，定位模块 `_project_paths.py` 保持原名。

| 旧入口 | 当前入口 | 用途 |
|---|---|---|
| validate_skills.py | `scripts/skill_validate.py` | 校验技能 |
| create_skill.py | `scripts/skill_create.py` | 创建脚手架 |
| package_skill.py | `scripts/skill_package.py` | 按客户端打包 |
| compare_skills.py | `scripts/skill_compare.py` | 结构与质量筛查 |
| run_eval.py | `scripts/skill_eval.py` | 触发评测 |
| run_loop.py | `scripts/skill_optimize.py` | description 优化 |
| run_scenario.py | `scripts/skill_scenario.py` | 执行单个任务场景 |
| aggregate_benchmark.py | `scripts/skill_benchmark.py` | 汇总基准结果 |
| build_index.py | `scripts/skill_index_build.py` | 构建与更新索引 |
| search_index.py | `scripts/skill_index_search.py` | 检索与查看索引状态 |
| utils.py | `scripts/skill_utils.py` | 共享工具模块（供导入） |

2026-09-29 起使用新入口；参数、输出格式与退出语义沿用迁移前行为。外部命令和 Python 模块导入需更新名称，成品不保留旧入口副本或转发脚本。演进摘要使用当前名称，旧文件名与上游源码名保留作历史标识；旧命令按此表换算。

本创建器的子代理指令统一使用 `agents/skill_<角色>.md`，同日起按下表迁移；外部提示词中的文件路径也需更新。

| 旧文件名 | 当前路径 |
|---|---|
| grader.md | `agents/skill_grader.md` |
| reviewer.md | `agents/skill_reviewer.md` |
| comparator.md | `agents/skill_comparator.md` |
| analyzer.md | `agents/skill_analyzer.md` |

角色职责与产物契约沿用原定义：评分仍输出 grading.json，评审输出 review.json，盲测输出 comparison.json；旧指令文件不保留副本。

## 上游外部仓库（索引来源）

「先查后建」检索的上游技能目录已内置为多源索引（`indexes/upstream.db`，随仓库提交）：

| 源 | 仓库 | 技能数 | 索引方式 | 检索 `--source` |
|---|---|---|---|---|
| **aas** | [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills) | ~2115 | 官方 `skills_index.json` + 目录扫描 | `aas` |
| **addy** | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 25 | 扫描 `skills/*/SKILL.md`（无官方索引） | `addy` |
| **anthropics** | [anthropics/skills](https://github.com/anthropics/skills) | ~19 | 扫描 `skills/*/SKILL.md`（无官方索引） | `anthropics` |
| **composiohq** | [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | ~28 | 扫描仓库根 `*/SKILL.md`（无官方索引） | `composiohq` |
| **coevoskills** | [Zhang-Henry/CoEvoSkills](https://github.com/Zhang-Henry/CoEvoSkills) | 1 | **稀疏 API 取数** `meta_skills/*/SKILL.md`（仓库约 600MB，不走整仓 tarball） | `coevoskills` |
| **mattpocock** | [mattpocock/skills](https://github.com/mattpocock/skills) | 38 | 扫描 `skills/<category>/<name>/SKILL.md`（两层嵌套，无官方索引） | `mattpocock` |
| **karpathy** | [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) | 1 | 扫描 `skills/*/SKILL.md`（`karpathy-guidelines`，无官方索引） | `karpathy` |

- 检索全库：`python scripts/skill_index_search.py "<关键词>"`（默认查所有源）
- 关键词按名称精确命中 + BM25 相关性排序；常见中文词离线扩展为英文，例如「代码审查」→ `code review`。未知词需再用英文检索，0 命中不直接判定不存在。
- 按源检索：加 `--source anthropics`（或 `aas` / `addy` / `composiohq` / `coevoskills` / `mattpocock` / `karpathy`）
- 重建/增量：`python scripts/skill_index_build.py [--source all|aas|addy|anthropics|composiohq|coevoskills|mattpocock|karpathy] [--incremental]`
- 离线优雅降级：某源下载/解包失败且已有 `indexes/upstream.db` 时，跳过该源并保留其已提交数据（可达源仍增量同步），退出码 0；仅当既无网络又无可用 DB 时才失败
- `skill_index_search.py --stats` 显示逐源成功/尝试时间、状态、索引快照哈希与固定来源提交号；旧索引的缺失记录显示 unknown，局部更新不刷新其他源的时间。
- 许可以各上游仓库 LICENSE 为准（aas/addy/mattpocock 为 MIT；anthropics 多数 Apache-2.0、文档类技能为 source-available；composiohq 未声明；coevoskills 为 Apache-2.0；karpathy 无 LICENSE 文件、`SKILL.md` 声明 MIT），入库技能需保留来源归属
- 索引细节见 `references/skill-index.md`；新建技能时先在多源中「先查后建」

## 约定

- 每个 Skill 一个子目录，命名 `kebab-case`，例如 `code-review/`
- 每个 Skill 以 `SKILL.md` 为核心，含 frontmatter（`name`/`description`/`risk`/`category`）与说明

## 结构

```
skill-creator/
  README.md                 # 说明
  SKILL.md                  # 核心：创建/改进/验证/安装技能的方法论（唯一入口，按任务选择路径）
  evals.json                # 本技能自身的触发测试用例（随技能回归）
  scripts/
    skill_index_build.py    # 构建上游技能索引（tarball→SQLite，支持 --incremental）
    skill_index_search.py   # 检索上游索引（FTS5 全文/分类/风险过滤）
    skill_compare.py        # 自建 vs 上游对比评分（质量6维+结构4维）
    skill_create.py         # 交互式脚手架生成器（含 evals/evals.json）
    skill_package.py        # 客户端打包器（按端适配 frontmatter + 复制整目录 + post-check）
    skill_validate.py       # 自动验证器（frontmatter/章节/安全/链接/密钥扫描）
    skill_events.py         # 共享：Claude/OpenCode 结构化事件、触发证据与指标解析
    skill_utils.py          # 共享：frontmatter 解析 + 章节模式 + 触发启发式 + 安全扫描 + 进程树终止客户端运行器（四端通用）
    skill_eval.py           # 触发评测（heuristic 默认 / cli 双模式；--concurrency 有界并行；逐查询隔离工作区；--output-dir 落盘）
    skill_optimize.py       # description 优化（train/validation 60/40；独立最终测试；cli 隔离运行）
    skill_scenario.py       # 场景执行器（跑单个任务、落盘 run 目录供评分/汇总；超时也留档）
    skill_benchmark.py      # 量化基准汇总（benchmark.json + benchmark.md，纯 stdlib；--primary/--baseline 定 delta 方向；--notes 合并分析笔记）
    _project_paths.py       # 技能根定位辅助（自包含，不依赖宿主仓库）
  agents/                   # 子代理指令（SKILL.md 按需拉起，不自动加载）
    skill_grader.md         # 评分子代理：断言判定 → grading.json
    skill_reviewer.md       # 评审子代理：评分/审核 → pass·revise + review.json（无人工评审闭环）
    skill_comparator.md     # 盲测对比子代理：A/B 定性对比 → comparison.json
    skill_analyzer.md       # 复盘/基准分析子代理：改进建议 / 观察笔记
  indexes/
    upstream.db             # SQLite 索引（官方 skills_index.json + 结构扫描，随仓库提交）
  references/
    skill-template.md       # 技能模板：字段与分类完整参考
    skill-anatomy.md        # 技能解剖：结构与渐进式披露
    quality-bar.md          # 质量标准与验证标准（8 项质量检查）
    skill-writing-guide.md  # 写作规律（TDD 化/表述匹配失败类型/防借口/措辞微测）
    skill-index.md          # 上游索引：构建/检索/增量更新说明
    skill-comparison.md     # 对比评分维度与择优流程
    skill-evaluation.md     # 场景产物、配对基准与评审
    skill-trigger-optimization.md # 触发信号、开发/最终查询与优化
    skill-installation.md   # 打包、自安装与客户端落点
    benchmark-schema.md     # 评测/基准 JSON schema（移植自 Anthropic 官方）
  templates/
    SKILL.template.md       # 新技能骨架模板
    evals.json.template     # 触发测试用例模板
  examples/                 # 上游学习样本（MIT 许可，验证豁免）
    README.md               # 样本入口：来源/许可/目录清单/学习要点
    brainstorming/          # 单文件·结构教科书
    copywriting/            # 单文件·流程门控
    git-pushing/            # 单文件+scripts·高风险模板
    systematic-debugging/   # 单文件+references·阶段强制序
    react-best-practices/   # 多文件·渐进式披露范本
    loki-mode/              # 综合·复杂工作流范本
  evolutions/               # 演进上下文摘要（反馈闭环，按需读取）
    README.md               # 主题路由、未解决事项、记录与压缩规范
    methodology.md          # 写作纪律、评审与上游取舍
    evaluation.md           # 评测契约、真机证据与限制
    validation.md           # 校验、安全扫描与评分边界
    distribution.md         # 字段、权限、安装与命名
    indexing.md             # 索引源、检索与数据状态
    library-decisions.md    # 七项技能的来源与采纳依据
    record-map.md           # 旧日期记录 → 摘要章节
    <YYYY-MM-DD>-<主题>.md    # 日期平铺的对比/采纳记录
```

## 使用

1. 参考本目录 `SKILL.md` 的任务路由与创建方法
2. 使用 `scripts/skill_create.py` 脚手架或 `templates/SKILL.template.md` 作为骨架创建你的 Skill
3. 运行自动验证：`python scripts/skill_validate.py --strict --dir <技能目录>`（失败必须修复）
4. 多客户端打包：`python scripts/skill_package.py <技能目录> --client claude --client opencode --client codex --client deepseek --out <产物目录> [--zip]`（按端适配 frontmatter + post-check，产物在 `<产物目录>/<客户端>/<技能名>/`）
5. 将产出的技能安装到目标客户端的 skills/ 目录（落点见 SKILL.md「多客户端安装指引」），按客户端文档完成后续配置
6. 经验证的技能归档到可分发位置

触发评测默认出报告；接入质量门时为 `skill_eval.py` 加 `--fail-on-error --fail-on-mismatch`。报告包含运行覆盖率，无有效分母的 precision/recall 显示 null，避免把运行失败当满分。

描述优化使用开发验证集选候选，可加 `--final-eval-set` 对独立查询集只评一次，默认由真实客户端运行；`confirmation` 区分未测、词面通过、派发通过和失败。静态 `skill_compare.py` 只输出结构筛查，采纳前须比较至少一个相同真实任务的产出。从 `SKILL.md` 按需读取场景评测、触发优化与基准契约。

## 评测证据与按需加载（2026-09-29）

- SKILL.md 按创建、局部修改、场景评测、触发优化、安装和索引任务路由；操作细节按需读取。
- 场景执行支持 --input-dir / --output-dir，清理前收集真实产物及清单；拒绝非空 run 目录，失败/超时仍保留证据。
- Claude/OpenCode 触发使用结构化事件，记录派发/读取证据；名称提及不算触发。CLI 协议缺失或执行错误单列。
- 基准 schema_version=2 保留全部尝试及覆盖率，按场景和运行编号配对；缺成本为 null，统计给出有效 n，模型与指标来源随报告保存。--strict 在报告落盘后阻断不完整比较。
- 索引 v6 远程下载先固定提交号，本地来源记 local/unknown；失败保留上一成功快照。随包索引未重新下载，旧数据缺失的来源提交仍为 unknown。
