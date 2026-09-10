# skill-creator

创建自定义 Skill 的目录。本技能是**技能创建器**：把用户的真实工作流蒸馏为可复用、可验证、跨客户端安装的高质量技能，走「先查后建（检索上游）→ 创建 → 对比择优 → 自动验证 → 触发测试 → 安装 → 回馈」的完整闭环。方法遵循：证据驱动、渐进式披露、自由度匹配脆弱性、高信号命名、迭代测试循环、触发优化与治理化验证。完整方法论见 `SKILL.md`（唯一入口）。

## 上游外部仓库（索引来源）

「先查后建」检索的上游技能目录已内置为多源索引（`indexes/upstream.db`，随仓库提交）：

| 源 | 仓库 | 技能数 | 索引方式 | 检索 `--source` |
|---|---|---|---|---|
| **aas** | [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills) | ~2100 | 官方 `skills_index.json` + 目录扫描 | `aas` |
| **addy** | [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 25 | 扫描 `skills/*/SKILL.md`（无官方索引） | `addy` |

- 检索全库：`python scripts/search_index.py "<关键词>"`（默认查所有源）
- 按源检索：加 `--source addy`（或 `aas`）
- 重建/增量：`python scripts/build_index.py [--source all|aas|addy] [--incremental]`
- 双源均在 MIT 许可下使用，入库技能需保留来源归属
- 索引细节见 `references/skill-index.md`；新建技能时先在两库中「先查后建」

## 约定

- 每个 Skill 一个子目录，命名 `kebab-case`，例如 `code-review/`
- 每个 Skill 以 `SKILL.md` 为核心，含 frontmatter（含 `version: x.y.z`）与说明

## 结构

```
skill-creator/
  README.md                 # 说明
  SKILL.md                  # 核心：创建/改进/验证/安装技能的方法论（唯一入口，10 阶段工作流）
  scripts/
    build_index.py          # 构建上游技能索引（tarball→SQLite，支持 --incremental）
    search_index.py         # 检索上游索引（FTS5 全文/分类/风险过滤）
    compare_skills.py       # 自建 vs 上游对比评分（质量6维+结构4维）
    create_skill.py         # 交互式脚手架生成器（含 version 字段）
    validate_skills.py      # 自动验证器（frontmatter/章节/安全/链接/密钥扫描）
    utils.py                # 共享：frontmatter 解析 + 章节模式 + 触发启发式（四端通用）
    run_eval.py             # 触发评测（heuristic 默认 / cli 双模式；--output-dir 落盘）
    run_loop.py             # description 自动优化循环（train/test 60/40）
    run_scenario.py         # 场景执行器（跑单个任务、落盘 run 目录供评分/汇总）
    aggregate_benchmark.py  # 量化基准汇总（benchmark.json + benchmark.md，纯 stdlib；--notes 合并分析笔记）
    _project_paths.py       # 仓库根定位辅助
  agents/                   # 子代理指令（SKILL.md 按需拉起，不自动加载）
    grader.md               # 评分子代理：断言判定 → grading.json
    reviewer.md             # 评审子代理：评分/审核 → pass·revise + review.json（无人工评审闭环）
    comparator.md           # 盲测对比子代理：A/B 定性对比 → comparison.json
    analyzer.md             # 复盘/基准分析子代理：改进建议 / 观察笔记
  indexes/
    upstream.db             # SQLite 索引（官方 skills_index.json + 结构扫描，随仓库提交）
  references/
    skill-template.md       # 技能模板：字段与分类完整参考
    skill-anatomy.md        # 技能解剖：结构与渐进式披露
    quality-bar.md          # 质量标准与验证标准（8 项质量检查）
    skill-writing-guide.md  # 写作规律（TDD 化/表述匹配失败类型/防借口/措辞微测）
    skill-index.md          # 上游索引：构建/检索/增量更新说明
    skill-comparison.md     # 对比评分维度与择优流程
    benchmark-schema.md     # 评测/基准 JSON schema（移植自 Anthropic 官方）
  templates/
    SKILL.template.md       # 新技能骨架模板（含 version 字段）
    evals.json.template     # 触发测试用例模板
  examples/                 # 上游学习样本（MIT 许可，验证豁免）
    README.md               # 样本入口：来源/许可/目录清单/学习要点
    brainstorming/          # 单文件·结构教科书
    copywriting/            # 单文件·流程门控
    git-pushing/            # 单文件+scripts·高风险模板
    systematic-debugging/   # 单文件+references·阶段强制序
    react-best-practices/   # 多文件·渐进式披露范本
    loki-mode/              # 综合·复杂工作流范本
  evolutions/               # 对比择优学习记录（反馈闭环）
    README.md                 # 记录规范与模板
    <YYYY-MM-DD>-<主题>.md    # 日期平铺的对比/采纳记录
```

## 使用

1. 参考本目录 `SKILL.md` 的技能创建方法（10 阶段工作流）
2. 使用 `scripts/create_skill.py` 脚手架或 `templates/SKILL.template.md` 作为骨架创建你的 Skill
3. 运行自动验证：`python scripts/validate_skills.py --strict --dir <技能目录>`（失败必须修复）
4. 将产出的技能安装到目标客户端的 skills/ 目录（落点见 SKILL.md「多客户端安装指引」），按客户端文档完成后续配置
5. 经验证的技能归档到可分发位置