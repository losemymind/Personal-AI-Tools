# 审计闭环：第三轮（索引数据损坏 + 安全扫描覆盖/绕过 + 契约一致性）

## 基本信息
- 日期：2026-09-10
- 版本：skill-creator 0.9.16 → 0.9.17
- 触发来源：对成品的独立只读审计（两个 code-reviewer 子代理 + 主代理逐条复现）；前九轮（0.9.8-0.9.16）集中在崩溃/健壮性，漏掉了数据契约、文档-行为一致性与一类安全绕过

## 需求与证据

逐条用具体输入复现后修复（均为真实缺陷，非风格问题）：

1. **索引 frontmatter 解析写坏已提交数据（中）**：`build_index.py` 的 `frontmatter_of` 对 YAML 先试 `json.loads`，失败后只兜底读 `name`/`description` 两行。块标量描述（`>`/`|`）被存成字面指示符，结构化键全丢。实证：已提交 `indexes/upstream.db` 中 `academy-guide` 等 3 条 anthropics 记录 `description=='"' + '>' + '"'`（损坏）。
2. **claude cli 触发判定与 SKILL.md 承诺矛盾（中）**：`run_eval.detect_triggered` 对非 opencode 走全文子串匹配，而 SKILL.md 明写「**不做全文子串匹配**」并把 claude 列为支持端 → claude 触发率被系统性高估。
3. **危险管道可被 shell 续行/包装/缩进绕过（中）**：`utils` 正则要求 `curl` 与 `|` 同行且 `sh` 紧跟管道；`curl x \`+换行+`| bash`、`| sudo -u root bash`、`| env bash`、`| /bin/bash`、`| busybox sh`、4 空格缩进代码块、blockquote 内围栏全部漏检。
4. **markdown 链接扫描漏 fenced 豁免（低）**：反引号引用做了围栏豁免，markdown 链接没做 → 教学类技能用围栏展示链接语法即误报悬空。
5. **`run_loop --holdout nan/inf` 裸 traceback（低）**：`int(round(n*holdout))` 抛 `ValueError`/`OverflowError`。
6. **`run_scenario` 客户端命令不存在时 run 目录留空（低）**：违背「每次运行都落盘」的基准契约。
7. **危险管道只扫 SKILL.md，捆绑脚本不扫（高，第二轮子代理）**：`scripts/*.sh` 里的 `curl|bash` 使 `--strict` 全绿。
8. **`detect_triggered` 漏 `{"type":"tool"}` 事件（中）**：与 `run_scenario.count_tool_calls` 判定不一致，真实触发被记为假阴性。
9. **`run_loop` 丢弃最后一轮改进产物（中）**：`history` 只在每轮开始登记，`--max-iterations N` 的第 N 轮候选从不被评分/入选。
10. **目录密钥扫描扩展名白名单过窄（中）**：漏 `.ps1/.bat/.cmd/.env` 等，Windows 优先仓库里的明文凭据漏检。
11. **空/写错 `--dir` 静默 exit 0（低）**：`Checked 0 skills` 却「All passed」，发布门 fail-open。
12. **`load_eval_set` 不校验 `should_trigger`（低）**：漏字段被当成负例，污染 precision/recall。
13. **`search_index --limit -1` 返回全量（低）**：SQLite `LIMIT -1` = 无限制。
14. **`create_skill.ask()` 无 choices 时提示串打印 `None`（低）**、**benchmark markdown「N runs each」用各配置最大值（低）**、**`benchmark-schema.md` 的 timing.json 字段与实际产物不符（低）**。

### 经复核**不成立**、未采纳的两条
- 「3 个扫描源的 `category`/`risk` 全为 NULL 违反 schema」：核对上游 SKILL.md（anthropics/addy/ComposioHQ）**确实只声明 `name`/`description`**，NULL 是上游缺字段，非丢失，不改。
- 「4 反引号闭合 3 反引号围栏是 bug」：CommonMark 规定闭合围栏长度 **≥** 开启围栏，属正确行为，不改。

## 采纳要点（改了什么）

- **`scripts/build_index.py`**：`frontmatter_of` 改用共享 `utils.parse_frontmatter`（PyYAML，`utf-8-sig`），仅无 PyYAML 时退回增强的最小解析器（支持块标量/行内列表）；重建受影响源。
- **`scripts/utils.py`**：危险管道改为「管道链 + 右侧 token 化判定」——`_segment_runs_shell` 跳过 launcher/flag/`VAR=val`/数字，识别包装 shell，且**不误报 `| grep bash`**；`find_dangerous_pipes` 先合并 `\` 续行，围栏识别支持 blockquote，代码上下文含「围栏内或 ≥4 空格缩进行」；`load_eval_set` 强制 `should_trigger` 布尔。
- **`scripts/validate_skills.py`**：markdown 链接扫描加 fenced 豁免；`TEXT_SCAN_EXTS` 补 `.conf/.env/.ps1/.psm1/.psd1/.bat/.cmd`；`check_dir_secrets` 扩展为「目录级密钥 + 危险管道」扫描（.md 走围栏视图、代码文件全扫）；`skill_count == 0` 报错（fail-closed）。
- **`scripts/run_eval.py`**：`detect_triggered` 接受 `type in ("tool_use","tool")`，并注明 claude 为 best-effort 子串。
- **`scripts/run_loop.py`**：校验 `--holdout` 有限且 ∈[0,1]；`_split_count` 加非有限保护；循环结束后对最终候选再评分并纳入择优（不再丢轮）。
- **`scripts/run_scenario.py`**：`build_command` 失败与 `FileNotFoundError` 也落盘 transcript/metrics/timing，再返回 1。
- **`scripts/search_index.py`**：拒绝负 `--limit`。**`scripts/create_skill.py`**：`ask()` 提示串不再含 `None`。**`scripts/aggregate_benchmark.py`**：markdown 文案改「up to N runs」。
- **`SKILL.md`**：明确 opencode 结构化判定、claude best-effort 子串（假阳性风险）。
- **`references/benchmark-schema.md`**：timing.json 字段与 `run_scenario` 实际产物对齐。
- **`indexes/upstream.db`**：`--source anthropics --incremental` 重建，3 条损坏描述修复，总数 2187 不变。
- 测试：`tests/test_hardening.py` +18 例 → **148 例**（原 130）。

## 验证结果

- `python -m pytest tests/ -q`：**148 passed**。
- 成品 strict / 能力库 strict（5 技能）/ agent strict（32）/ `build_catalog.py --check` 全绿。
- 索引：`broken/empty descriptions == 0`；`academy-guide` 描述恢复为真实文本。

## 学习点

- **审计要按「契约」而非只看「崩溃」**：前九轮专修异常输入 traceback，却漏了「已提交产物被写坏」「文档承诺 ≠ 行为」——数据契约与声明一致性必须单独过一遍。
- **安全扫描的覆盖边界就是攻击面**：只在 SKILL.md 扫、只扫同行管道、只认 fenced——每个「只」都是一个绕过。扫描要么覆盖产物全目录，要么在文档里明确不覆盖。
- **别把上游缺字段当成自己丢数据**：审计结论必须核对上游事实（上游 frontmatter 只有 name/description），否则会「修」出假需求。
