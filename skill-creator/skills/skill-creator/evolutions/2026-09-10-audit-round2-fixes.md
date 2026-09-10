# 审计闭环：第二轮 12 项缺陷修复（安全/正确性/健壮性/一致性）

## 基本信息
- 日期：2026-09-10
- 版本：skill-creator 0.9.7 → 0.9.8
- 触发来源：对成品全量脚本的只读审计 + 实证复现（用户要求「全部修复」）

## 需求与证据

逐项复现了成品缺陷（多为真 bug），本轮全部修复：

1. **安全扫描可被全局绕过（高）**：`validate_skills.py` 的 `if not SECRET_ALLOWLIST_RE.search(content)` 是**整文件 kill-switch**——文件任意位置出现 `<!-- security-allowlist` 字样即关闭该文件的危险管道与密钥扫描。skill-creator 自身 SKILL.md 仅在正文**提到**该标记，就使自身 `curl|bash` 示例免检；实测一个含 `curl … | bash` 的技能因散文提及该标记而 `--strict` 通过。
2. **compare_skills 崩溃（高）**：候选目录无 SKILL.md 时 `read_skill` 返回 `{"error":…}`，`score_quality` 直接 `s["content"]` → KeyError traceback（实测路径含分类目录或写错时崩溃）。
3. **benchmark delta 方向靠目录名字典序（高）**：`primary=configs[0]/baseline=configs[1]`，配置名为 `baseline`/`skill` 时符号静默反转（实测 skill 80% vs baseline 20% 输出 delta **−0.60**）。
4. **run_loop cli 未隔离（中）**：`opencode run` 以仓库为 cwd、无一次性工作区；且用 `--format json` 却按纯文本正则抽取。
5. **run_eval 并发共享工作区（中）**：`--concurrency>1` 时多查询共用同一 cwd，互相干扰。
6. **超时只杀直接子进程（中）**：`subprocess.run(timeout=)` 留孤儿孙进程（本会话实证）。
7. **run_scenario 超时不落盘（中）**：超时直接返回，run 目录消失，违背基准「每次运行都留档」契约。
8. ~~**`assets/` vs `templates/` 命名漂移（低）**：SKILL.md / skill-anatomy.md 提到不存在的 `assets/`。~~ **已撤销**：`assets/` 是「捆绑资源」的通用名（技能本就可能随附任意资源），原文无误，保留。
9. **compare_skills docstring 用法错误（低）**：`--all-candidates` 缺 `<upstream_dir>`。
10. **脚手架不产出 evals.json（低）**：生成即命中「No evals.json」advisory。
11. **声明客户端与 cli 支持不符（低）**：`tools` 列 4 端，cli 仅 claude/opencode。
12. **split 边界 + evals 数量（低）**：`max(1,…)` 会把唯一正例全抽进 test→train 空；skill-creator evals 仅 14 条。

## 采纳要点（改了什么）

- **`scripts/utils.py`（新增共享层）**：安全扫描单一源——`security_allowlist_ranges`（标记仅豁免**本行**或**紧邻其后的 fenced 块**，实现局部豁免）、`find_dangerous_pipes`（**只扫 fenced 代码块**，散文/行内反引号里的模式说明不再误报）、`find_inline_secrets`（全文扫描，局部豁免）；`run_client`（Popen + `taskkill /T`/`killpg` **杀进程树**，超时抛 `TimeoutExpired` 并携带部分输出）；`fenced_ranges`。
- **`validate_skills.py`**：删本地模式，改用 utils 共享扫描；allowlist 局部化。
- **`compare_skills.py`**：`read_skill` 失败不再崩溃（本地不可读→清晰报错；候选跳过并告警；无有效候选→退出 1）；security_guardrails 改用 `find_dangerous_pipes`（散文不再误判 0 分）；修正 docstring。
- **`aggregate_benchmark.py`**：新增 `--primary/--baseline` 与 `_ordered_configs`（角色→别名→输入序回退），delta 记录实际 `primary/baseline`；`generate_markdown` 沿用该顺序。
- **`run_eval.py`**：`run_cli` 改用 `run_client`（树杀 + 部分输出）；`run_cli_batch` 改为**逐查询**独立隔离工作区（并发安全）。
- **`run_scenario.py`**：改用 `run_client`；超时也写 transcript/timing/metrics（`timed_out: true`，rc=-1）。
- **`run_loop.py`**：improver 走 `run_client` + 一次性工作区；opencode 输出经 `run_scenario.extract_text` 解析 JSON 流；`_split_count` 保证 train/test 各至少 1（n≥2）。
- **`create_skill.py`**：脚手架写出 `evals/evals.json`（来自模板，替换 skill_name）。
- **`SKILL.md` / `README.md` / `references/skill-anatomy.md`**：cli 仅 claude/opencode；逐查询隔离；delta 角色说明；超时树杀。（`assets/` 保留为捆绑资源通用名，未改 `templates/`。）
- **`evals.json`**：14 → 20 条（11 正 / 9 负）。
- 测试：`tests/test_hardening.py` +15 例 → **92 例**（原 77）。

## 第二轮审计（子代理复查，0.9.8 → 0.9.9）

第一轮修复后由代码审查子代理复跑，又发现并修复一批缺陷：

- **H1 围栏检测可绕过（高）**：原 ` ```.*?``` ` 正则漏掉 `~~~` 围栏、未闭合围栏、4 反引号围栏——危险命令藏其中即逃过扫描。重写 `fenced_ranges` 为 CommonMark 感知（≥3 反引号或波浪线、闭合长度≥开启、未闭合延到 EOF、≤3 缩进）。
- **M1 检索崩溃（中）**：`search_index.py` 把裸查询交给 FTS5 `MATCH`，`c++`/`(`/`"` 等触发 `OperationalError`。改为按空白分词后逐词加双引号转义（字面检索）。
- **M2 输入形状崩溃（中）**：`run_eval`/`run_loop` 对坏 `evals.json`（无 `evals` 的字典、`[1,2,3]`、非 JSON、目录）与坏 `SKILL.md` 直接 traceback。新增共享 `utils.load_eval_set` + 包裹 `parse_skill_md`，转清晰报错。
- **M3 基准聚合崩溃（中）**：`aggregate_benchmark` 对非字典 `grading.json`/`timing`/`metrics.json`、非 `run-<int>` 目录名崩溃。全面加 `isinstance` 守卫与 `run_number` 容错。
- **M4 脚手架产出非法 YAML（中）**：描述含 `"` 时 `create_skill` 生成坏 frontmatter。改用 `json.dumps` 转义（描述与作者），并校验 `--version` 为 semver。
- **M5 `--client-cmd` Windows 失效（中）**：POSIX `shlex.split` 吞反斜杠；改平台自适应切分 + 去引号 + 捕获 `ValueError`。
- **M6 改进器接受空描述（中）**：空 description 会污染迭代并可能被选优。空/纯空白即拒绝。
- **M7 无基线假增益（中）**：某配置 0 个成功 run 时仍按 0.0 计算 delta。改为两侧都有 run 才算 delta，否则 `null` + note。
- **L1 缩进标注围栏被误报（低）**：allowlist 匹配改为按围栏起始偏移，兼容缩进/波浪线。
- **L2/L3/L4/L5/L6/L7/L8**：对比文档与 0.8 默认分对齐；markdown delta 改百分比单位；`--keep-workspace`/`--keep` 打印保留路径；`build_workspace` 失败即清理半成品临时目录；密钥扫描扩展到 references/agents/scripts 全目录（反引号悬空引用仍只扫 SKILL.md，避免泛化占位路径误报）；`--max-iterations` 校验≥1、report 自动建父目录；修 SKILL.md 标点/结构树补 `evals.json`；`benchmark-schema.md` 同步新字段；`compare --json` 改为纯 JSON 输出。
- **`utils.py`**：`fenced_ranges`（CommonMark）、`load_eval_set`、`run_client`（进程树终止）为共享层。
- 测试：`tests/test_hardening.py` +15 例 → **107 例**（原 92）。

## 第三轮审计（子代理复查复核，0.9.9 → 0.9.10）

子代理复核确认第一/二轮全部 FIXED，另发现并修复：

- **M6 补全**：`--improve-mode manual` 也拒绝空描述（此前只 guard 了 cli 模式）；`call_improver_manual` 的提示改输出到 stderr，stdout 保持纯 JSON。
- **N1**：`eval_metadata.json` 非字典崩溃 → `isinstance` 守卫。
- **N2**：`eval_id` 类型混用（int/str）→ `sorted(..., key=str)`。
- **N3**：名为 `eval-*` 的**文件**（非目录）→ 跳过。
- **N4**：`compare_skills --json` 的错误路径仍写 stdout → 统一走 stderr（stdout 保持纯 JSON）。
- **N5**：`check_references_cross_links` 仍用朴素围栏正则 → 复用 `fenced_ranges`。
- **N6**：未闭合围栏把其后所有引用当代码而漏检 → `fenced_ranges(closed_only=True)` 用于引用豁免；安全扫描仍用「未闭合到 EOF」的严格视图。
- **N7**：把**文件**当 `benchmark_dir` → `is_dir()` 校验。
- **N8**：无基线时 CLI 打印 `Delta: None` → `or '—'`。
- **N9**：`create_skill` 不校验描述长度（>1024 即生出校验不过的技能）→ 加长度校验。
- 测试：`tests/test_hardening.py` +8 例 → **115 例**（原 107）。

## 第四轮审计（子代理复核，0.9.10 → 0.9.11）

子代理复核确认 N1-N9/M6 全 FIXED，再补四处**标量类型**健壮性缺口：

- **R1**：`eval_metadata.json` 的 `eval_id` 为非可哈希值（dict/list）→ set 构建崩溃。加 `_coerce_eval_id`（仅放行可哈希标量）。
- **R2**：eval 项的 `query` 非字符串（如数字）→ `keyword_tokens` 调 `.lower()` 崩溃。`load_eval_set` 增加「每项须有非空字符串 query/prompt」校验，坏输入转清晰报错。
- **R3**：`grading.json` 的标量字段为字符串（`pass_rate:"0.5"`、`total_tokens:"abc"`、`total_duration_seconds:"12.5"`）→ 聚合崩溃。加 `_as_float`/`_as_int` 容错转换（非法值回退 0）。
- **R4**：上游目录里存在**名为 `SKILL.md` 的子目录** → `read_text` `PermissionError`。`read_skill` 加 `is_file()` 守卫。
- 测试：`tests/test_hardening.py` +4 例 → **119 例**（原 115）。

## 第五轮审计（子代理复核，0.9.11 → 0.9.12）

子代理复核确认 R1-R4 全 FIXED，再补三处非有限值/类型缺口：

- **D1**：`_as_float`/`_as_int` 未捕获 `OverflowError`，JSON 的 `Infinity`/`1e400`/超大整数导致聚合崩溃。改为捕获 `OverflowError` 并拒绝非有限值（回退默认）。
- **D2**：`user_notes_summary` 的**值**非法（非列表）时 `notes.extend` 崩溃（int）或把字符串拆成单字符（str）。改为仅接受 list。
- **D3**：`NaN`/`Infinity` 会写进 `benchmark.json`（非合法严格 JSON）。`calculate_stats` 过滤非有限值；字段经 `_as_float` 净化，产物不再含 `NaN`/`Infinity`。
- 测试：`tests/test_hardening.py` +2 例 → **121 例**（原 119）。

## 第六轮审计（子代理复核，0.9.12 → 0.9.13）

子代理复核确认 D1-D3 全 FIXED，再补收尾级缺口：

- **D4**：`_coerce_eval_id` 放行非有限 float（`Infinity`/`NaN`）→ `benchmark.json` 又出现非法 JSON。改为非有限 float 回退默认。
- **D5**：`aggregate_benchmark` 的 `--notes`/`--output` 指到目录或缺失父目录时 traceback。加 `is_file` 校验、父目录自动创建、`OSError` 捕获。
- **D6**：`run_eval --output-dir`、`run_loop --report`、`run_scenario --run-dir`、`create_skill --out` 指向文件时 traceback。统一加路径类型校验与 `OSError` 捕获，转清晰报错。
- 测试：`tests/test_hardening.py` +3 例 → **124 例**（原 121）。

## 第七轮审计（子代理复核，0.9.13 → 0.9.14）

子代理复核确认 D4-D6 全 FIXED，残留一处低危：

- **D7**：`run_scenario --run-dir` / `create_skill --out` 的**父路径是文件**时 `mkdir` 抛 `FileExistsError` traceback。两处 `mkdir` 加 `try/except OSError`，转清晰报错。
- 测试：`tests/test_hardening.py` +1 例 → **125 例**（原 124）。

> 子代理第六轮复核结论：除 D7 外**无可复现缺陷**（104 例 fuzz 无异常、无非法 JSON 输出；全部前轮修复保持绿色）。

## 第八轮审计（子代理复核，0.9.14 → 0.9.15）

子代理确认 D7 FIXED，并指出四处**仅异常输入可达**的低危加固点（正常 CLI 不受影响）：

- **F1**：交互模式下 stdin 结束（重定向/EOF）→ `input()` `EOFError` traceback。`ask()` 捕获 `EOFError`：有默认值则用默认，否则清晰退出。
- **F2**：`--tools` 值未转义直接插入 YAML，含 `]`/`,`/`"` 等即生成坏 frontmatter。改为逐项 `json.dumps` 引用。
- **F3**：`run_scenario.extract_text` 遇非字典 `part` 崩溃 → 加 `isinstance` 守卫与文本类型校验。
- **F4**：`run_eval.detect_triggered` 遇非字典 `part`/`state`/`input` 崩溃 → 逐层 `isinstance` 守卫。
- 测试：`tests/test_hardening.py` +4 例 → **129 例**（原 125）。

## 第九轮审计（子代理复核，0.9.15 → 0.9.16）

子代理确认 F1-F4 FIXED，残留最后一处低危：

- **G1**：空白字符串 `--client-cmd "   "` 切分为空 argv → `Popen([])` `OSError` traceback。`build_command` 检测空结果即抛 `RuntimeError`（已被既有 try 捕获，转清晰报错）。
- 测试：`tests/test_hardening.py` +1 例 → **130 例**（原 129）。

> 子代理最终结论：**除 G1 外，成品在合理用户路径上无可复现的正确性/安全/契约缺陷**；G1 修复后收尾。

## 验证结果

- `python -m pytest tests/ -q`：**92 passed**。
- 成品 strict / 能力库 strict（5 技能）/ agent strict（32）/ `build_catalog.py --check` 全绿。
- 关键回归：skill-creator 自身 SKILL.md（散文中含 `curl|bash`）**strict 通过**且未被 security 扫描误杀；`curl|bash` 位于非标注 fenced 块时**仍报错**。

## 学习点

- **豁免必须局部**：安全扫描的 allowlist 一旦是文件级开关，任何一句散文都能关闭它——豁免要锚定到具体命中（同行/紧邻块）。
- **文档里的模式串 ≠ 可执行示例**：把危险管道扫描限定在 fenced 代码块，既让安全指南能自述规则，又不放过真实的可运行命令。
- **「记录每次运行」是基准契约**：超时/失败也是运行，必须落盘，否则基准样本被静默吞掉。
- **角色显式化优于命名约定**：delta 方向、train/test 归属都应显式传参，别依赖字典序/max(1,…) 这类隐式约定。
- **共享层收敛**：安全扫描与客户端运行器下沉 utils，validator/comparator/eval trio 不再各写一份而漂移。
