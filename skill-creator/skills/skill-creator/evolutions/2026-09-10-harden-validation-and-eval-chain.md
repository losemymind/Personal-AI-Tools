# 加固记录：验证器 / 评测链缺陷修复 + 脚本裁剪

## 基本信息
- 日期：2026-09-10
- 需求：基于一次只读缺陷审计，修复 skill-creator 成品的全部已确认缺陷，并依工作流移除冗余脚本。
- 来源：本仓库自审（无上游对照；缺陷均为本地实现问题）。

## 修复清单
- **A1 验证器假通过**：`validate_skills.py` 的反引号引用解析曾回退到 skill-creator 自身根目录，导致校验外部技能库时，引用仅存在于 skill-creator 的路径被判通过。改为只在技能自身目录内解析（保留模块自引用前缀剥离）。
- **A2 CJK 触发启发式失准**：`keyword_tokens` 把连续中文当整词，`classify` 的「≥2 token 重叠」对中文查询几乎恒不成立。改为 CJK 单字 + 双字切分，仅以（拉丁词 + 中文双字）参与重叠判定。
- **A3 run_eval 吞运行错误**：`--mode cli` 的超时/缺命令/非零退出曾 `return False`（记为未触发）。改为抛 `RuntimeError`，汇总单列 `errors`，与假阴性区分（对齐阶段 7 失败分类）。
- **A4 安全正则笔误**：`compare_skills.py` 的 `|/isx` 修正为真正的危险管道检测。
- **A5 基准元数据失真**：`runs_per_configuration` 由硬编码 3 改为实际观测值。
- **A6 量纲错误**：基准 `tokens` 不再取自 `output_chars`（字符≠token），改读 token 字段。
- **A7 BOM 解析**：验证器读取改 `utf-8-sig`，与 `utils.parse_skill_md` 一致。
- **B1 名称上限不一致**：统一为 ≤100 字符并由验证器强制。
- **B2 章节模式漂移**：章节正则集中到 `utils.py`（单一来源），`validate_skills` 与 `compare_skills` 共用，消除「When to Use This Skill」判定分歧。
- **B3 脚手架反模式**：`create_skill.py` 回退骨架的 `@other-skill` 改为纯技能名（遵守本技能「禁 `@` 语法」硬规则）。
- **B4 元数据维度偏窄**：`compare_skills` 的 `metadata_complete` 由 name+description 扩为 quality-bar 第 1 项的 7 字段。
- **C2 客户端覆盖**：`run_eval --mode cli` 与 `run_loop --improve-mode cli` 增加 opencode（除 claude）。
- **C3 安全扫描落地**：危险远程执行管道与常见明文密钥纳入 `validate_skills.py` 自动扫描（`<!-- security-allowlist -->` 豁免），不再仅是纪律。
- **C4 对比非递归**：`compare_skills --all-candidates` 改 `rglob`，覆盖分类目录树。
- **C5 死字段**：`evals.json` 的 `files` 字段无消费者，从模板与 schema 移除。
- **D1 校验缺口**：`tags`（列表/≤5）、`tools`（列表/已知客户端）纳入验证器。
- **D2 免责声明匹配脆弱**：offensive 免责声明由逐字全文匹配改为「授权横幅 + 许可语句」的容错匹配。
- **E1/E2 解析与模式重复**：frontmatter 解析与章节模式收敛到 `utils.py`（PyYAML 惰性导入，保持 stdlib-only 调用方不引入依赖）。

## 脚本裁剪（依工作流）
- 移除 `scripts/run_trigger_tests.py`：其独立 CLI 与 `run_eval --mode heuristic` 重复，且不在工作流阶段工具之列；其 `classify`/`keyword_tokens` 逻辑迁入 `utils.py`（CJK 修正一并落地）。
- 新增 `scripts/run_scenario.py`：补上量化闭环缺失的「场景执行器」——跑单个任务、把 `transcript.md`/`outputs/`/`metrics.json`/`timing.json` 落到基准布局，使 `aggregate_benchmark.py` 可端到端消费。

## 版本
- `0.7.1 → 0.8.0`（minor：新增/移除脚本 + 验证器与评测语义变化）。

## 学习点
- **发布门本身要有测试**：A1 这类「验证器假通过」不会被验证器自己发现，必须由独立 pytest（临时外部技能目录）钉住。
- **单一来源是防漂移的硬手段**：章节模式/解析器重复是 B2/E1 的根因，收敛到 `utils.py` 后两工具不可能再分歧。
- **纪律要能被机械强制**：C3 把「secret 扫描」从文档纪律变成验证器检查，符合本技能 writing-guide §5「能用工具强制的机械约束不要只做成文字」。
