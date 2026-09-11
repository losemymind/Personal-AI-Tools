# 审计闭环：第五轮（独立复查——数据契约推导、扫描覆盖与允许清单语义）

## 基本信息
- 日期：2026-09-10
- 版本：skill-creator 0.9.18 → 0.9.19
- 触发来源：用户要求继续对成品做独立审计；本轮覆盖「已提交产物的数据契约」与「文档承诺 ≠ 行为」两个前几轮的盲区，逐条实证复现后修复

## 需求与证据

逐条复现后修复（每条均先构造最小复现，再改，再补回归）：

1. **`aggregate_benchmark` 缺 `pass_rate` 时静默记 0%（中，数据契约）**：`grading.json` 由 LLM 评分子代理产出，`summary` 可能只给 `passed/failed/total` 而不含派生字段 `pass_rate`。原实现 `_as_float(grading_summary.get("pass_rate", 0.0))` 会把它记成 0%，并把这个 0 带进 delta 与 benchmark 结论。复现：`{"passed":2,"failed":1,"total":3}` → 汇总 pass_rate mean=0.0（应为 2/3）。
2. **`compare_skills.score_structure.resource_organization` 计数任意子目录（低，文档≠行为）**：文档 `references/skill-comparison.md` 定义为「有 scripts/references/examples/templates 子目录」，实现却是 `len(sd)/3`（任意子目录）。复现：建 `foo/bar/baz` 三个垃圾目录 → 该维满分 1.0。
3. **安全扫描按扩展名漏扫捆绑代码（中，覆盖缺口）**：`TEXT_SCAN_EXTS` 不含 `.js/.ts/.tsx/.jsx/.mjs/.cjs/.rb/.go/.java/.rs/.php`，而 `BACKTICK_REF_RE` 却认这些扩展名——捆绑的 `scripts/deploy.js` 里的密钥/危险管道可绕过发布门。复现：`scripts/deploy.js` 写 `sk-…` → `--strict` 全绿（未扫）。
4. **常见凭据格式漏检（中，覆盖缺口）**：`SECRET_PATTERNS` 只认 `sk-`/`ghp_`/`gho_`/`xox*`/`AKIA`，漏 `github_pat_`、`ghs_`/`ghr_`、Google `AIza…`、以及 PEM 私钥头 `-----BEGIN … PRIVATE KEY-----`。复现：以上样本 `find_inline_secrets` 全为 0。
5. **允许清单无法豁免缩进代码块（低，文档≠行为）**：验证器报错文案与质量清单都承诺「annotate its block/line」即可豁免，但 `security_allowlist_ranges` 只豁免围栏块；4 空格缩进代码块即使加了 `<!-- security-allowlist -->` 仍被报错。复现：marker + 缩进 `curl x | bash` → 仍 1 命中。
6. **`build_index.enrich_structure` 路径回退不一致（低，数据契约）**：`extract_fields` 对仅有 `id` 的官方索引项把 `path` 回退为 `skills/<id>`，但 `enrich_structure` 仍读 `entry["path"]`（空）→ 结构统计落到仓库根，把无关文件计入 `file_count`。复现：仅 `id=foo` 的条目 → `file_count` 计到仓库根文件。
7. **SKILL.md 自身 TOC 阈值残留（低，文档不一致）**：第四轮已把 skill-anatomy 的 `>300` 统一为 `>100`，但 SKILL.md 解剖代码块里仍写 `>300 行的大文件附目录`，与同文件 §读取规则/质量清单的 `>100` 矛盾。

## 采纳要点（改了什么）

- **`scripts/aggregate_benchmark.py`**：先算 `passed/failed/total`，`pass_rate` 缺失时由 `passed/total`（total>0）推导，缺失且无计数才为 0。
- **`scripts/compare_skills.py`**：`resource_organization` 只计 `{scripts, references, examples, templates}` 与子目录名的交集 / 3。
- **`scripts/validate_skills.py`**：`TEXT_SCAN_EXTS` 补齐常见代码扩展名（js/ts 家族 + rb/go/java/rs/php/vue/svelte），与 `BACKTICK_REF_RE` 对齐。
- **`scripts/utils.py`**：`SECRET_PATTERNS` 增 `github_pat_`、`gh[oprsu]_`、Google `AIza…`、PEM 私钥头；`security_allowlist_ranges` 增「marker 紧邻的缩进（≥4 列）代码块」豁免（围栏豁免优先，避免误豁免被正文隔开的块）。
- **`scripts/build_index.py`**：`enrich_structure` 复用 `extract_fields` 的 `path→skills/<id>` 回退。
- **`SKILL.md`**：解剖代码块 TOC 阈值 `>300` → `>100`。
- 测试：`tests/test_hardening.py` +6 例 → **159 例**（原 153）。
- 同步 `.opencode` 镜像；版本 0.9.18 → 0.9.19。

## 验证结果

- `python -m pytest tests/ -q`：**159 passed**。
- 成品 strict / 能力库 strict（5）/ agent strict（32）/ `build_catalog.py --check` 全绿；索引 4 源 2187 条完整性 OK。

## 学习点

- **派生字段不能假设存在**：LLM 产出的 `grading.json` 很可能省略 `pass_rate` 这类可推导字段；读取方应以原始计数兜底，否则「缺失」被静默当成「0 分」，直接污染 delta 决策。
- **同一约束的两处实现必须同集合**：`BACKTICK_REF_RE` 与 `TEXT_SCAN_EXTS` 描述的是「哪些后缀算代码/文本」，二者不一致就会留下按扩展名绕过的扫描缺口。
- **豁免机制要与错误文案同语义**：既然文案说「block/line」可豁免，就必须同时覆盖围栏与缩进两种代码形态，否则合法的操作必需命令永远无法通过发布门。
