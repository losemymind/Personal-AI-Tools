# 审计闭环：第一轮（独立审计——安全扫描缺失、BOM 数据契约与文档≠行为）

## 基本信息
- 日期：2026-09-10
- 版本：agent-creator 0.7.0 → 0.7.1
- 触发来源：对 agent-creator 成品做与孪生 skill-creator 同套维度的独立审计（数据契约 / 安全扫描覆盖 / 文档≠行为 / 健壮性 / CLI 语义 / 索引完整性 / 验证器纪律），逐条实证复现后修复

## 需求与证据

逐条先构造最小复现，再改，再补回归（`tests/test_hardening_round1.py`）：

### A. 安全扫描缺失（验证器纪律）
1. **`validate_agents.py` 完全不扫描密钥/危险管道（中）**：SKILL.md「入库与发布纪律」要求提交前扫密钥、按安全护栏处理危险管道，但 `--strict` 对于含明文凭据或 `curl … | bash` 的代理一律全绿。端口化孪生已具备的扫描能力，新增自包含模块 `scripts/security_scan.py`，并接入 AGENT.md 与**捆绑资源**目录级扫描。复现：`AGENT.md` 写 `ghp_…` 或 `curl https://x | bash`（围栏内）→ 修复前 `--strict` 通过，修复后报 `🚨`。

### B. UTF-8 BOM 数据契约（Windows 编辑器默认写 BOM）
2. **BOM 使 frontmatter 解析失败（高）**：`validate_agents.py` / `compare_agents.py` / `build_agent_index.py` 以 `utf-8` 读取，BOM 使 `^---` 锚定失败 → 合法代理被误报「Missing or malformed YAML frontmatter」。改为 `utf-8-sig`。
3. **BOM 令适配器静默原样透传（高）**：`adapt_agent.py` 遇到 BOM 时 `FRONTMATTER_RE.match` 失败 → 判定「no frontmatter block found; installed verbatim」，把 opencode 非法的 `tools: [...]` 数组原样输出且退出码 0。改为 `utf-8-sig`。复现：BOM 版规范 AGENT.md → 修复前输出仍含 `tools: [read`，修复后正常转为 `permission`。

### C. `--json` 契约与崩溃
4. **`compare_agents.py --json` 不是纯 JSON（中）**：先打印人类报告再打印 JSON，stdout 无法被 `json.loads` 解析。改为 `--json` 时仅输出 JSON 文档。
5. **`compare_agents.py` 缺 AGENT.md 崩溃（中）**：`read_agent` 返回 `{"error":...}` 后仍被 `score_agent` 访问 `["content"]` → `KeyError` 回溯。改为清晰报错退出 1。
6. **`compare_agents.py` 非映射 frontmatter 崩溃（低）**：YAML 顶层为列表时 `fm.get` → `AttributeError`。改为非 dict 归零。

### D. 验证器健壮性与纪律
7. **非字符串 `name` 崩溃（中）**：`name: 123` / `name: true` 使 `VALID_NAME.match(int)` 抛 `TypeError`。改为类型校验后报错。
8. **默认 `--dir` 扫自身产品报 6 错（中）**：文档称 `--dir` 可选、默认技能根；实际把 `evolutions/*.md` 与 `agents/reviewer.md` 当代理并报「缺 frontmatter」。改为：非 `AGENT.md` 的 `*.md` 仅在其确有 frontmatter 时才算代理定义。
9. **fenced 代码块内链接/反引号被误报悬空（中）**：`~~~`/```` ``` ```` 内示例路径被当作必须存在的引用。改为 fenced 区块豁免。
10. **反引号引用扩展名白名单过窄（低）**：缺 `db/txt/toml/...`，`indexes/upstream.db` 类引用从不校验。补齐白名单。
11. **显式 `--dir` 指向空目录静默全绿（中）**：存在但无代理定义时打印 `Checked 0 agents` 并退出 0（fail-open）。改为显式 `--dir` 下 0 代理即失败。

### E. 脚手架 YAML / 交互
12. **`create_agent.py` 描述含引号/换行产出非法 YAML（中）**：docstring 承诺「Output validates」，实际 `description: "{description}"` 未转义，含 `"`/换行时自校验失败。改用 `json.dumps` 生成 YAML 双引号标量。
13. **`create_agent.py` `mode` 可能被描述污染（低）**：`content.replace("subagent", mode, 1)` 会改到正文/描述里第一个 "subagent"。改为仅替换 `^mode:` 行。
14. **`create_agent.py` 交互 EOF 崩溃（低）**：stdin 关闭时 `input()` 抛 `EOFError` 回溯。改为回退默认值或干净退出。
15. **`create_agent.py` 版本不校验（低）**：非 semver 版本会产出被验证器拒绝的骨架。改为前置校验。

### F. 检索 / 索引
16. **FTS5 特殊字符查询崩溃（中）**：`AND`/`foo:bar`/`*`/`(` 等交给 `MATCH` 直接抛 `sqlite3.OperationalError` 回溯。改为逐词 FTS5 字面引用（对齐孪生）。
17. **`--limit` 负数被当无限（低）**：`LIMIT -1` 返回全量。改为报错。
18. **`build_agent_index` 块标量描述损坏（中，数据契约）**：`description: >`/`|` 被存成字面量 `">"`。改为消费缩进续行、按折叠/字面类型拼接并去公共缩进。
19. **`build_agent_index` 死参数（中，文档≠行为）**：`--no-dl`（承诺「扫描本地 checkout」）实现仍下载；`--keep`（承诺「保留 tarball」）从未被引用，构建后照旧清理。分别改为 `root = Path.cwd()` 与把 `args.keep` 纳入清理条件。

### G. 文档一致性
20. **评分维度数错位（低，文档≠行为）**：`compare_agents.py` 实算 **7** 个质量维度（含 `security_guardrails`），SKILL.md / README / `agent-comparison.md` 却写「质量 6 维」，且 SKILL.md 的 6 维列表漏了安全护栏。统一为「质量 7 维 + 结构 4 维」并补全列表/表格/docstring。
21. **`agent-anatomy.md` 自相矛盾（低）**：一处提及兄弟 reference `agent-template.md`，同文件又声明「本文件不直接链接其它 reference」。改为经 SKILL.md「读取规则」导读。

## 采纳要点（改了什么）

- **新增** `scripts/security_scan.py`：密钥 `SECRET_PATTERNS` + 危险远程执行管道 `find_dangerous_pipes`（管道右侧 token 化判定，覆盖 `sudo … bash`/`env bash`/`/bin/bash`/`irm | iex`、续行与行尾管道）、`<!-- security-allowlist -->` 局部豁免、CommonMark 围栏与缩进代码识别。
- **`validate_agents.py`**：`utf-8-sig` 读取；非 `AGENT.md` 需 frontmatter 才计为代理；fenced 豁免链接/反引号；扩展名白名单补齐；接入安全扫描（AGENT.md + 捆绑资源目录级）；`name` 类型校验；显式 `--dir` 空目录 fail-loud。
- **`compare_agents.py`**：`utf-8-sig`；`--json` 纯 JSON；缺文件/非 dict 骨架干净报错；`resource_organization` 只计 `references`/`scripts` 子目录。
- **`create_agent.py`**：YAML 安全标量、`mode` 行精确替换、EOF 兜底、版本校验。
- **`search_agent_index.py`**：FTS5 字面引用、拒绝负 `--limit`。
- **`build_agent_index.py`**：`utf-8-sig`、块标量解析、`--no-dl` 落地为扫描 cwd、`--keep` 纳入清理条件、`--from-extracted` 前置校验目录。
- **文档**：SKILL.md / README.md / `agent-comparison.md` / `agent-quality-bar.md` / `agent-anatomy.md` 同步为真实行为。
- 测试：`tests/test_hardening_round1.py` 新增 24 例 → agent-creator pytest **18 → 42**。
- 版本 0.7.0 → 0.7.1。

## 验证结果

- `python -m pytest tests/ -q`：**42 passed**。
- `validate_agents.py --strict --dir <仓库根>/agents`：Checked 32，全绿（能力库无密钥/危险管道）。
- `search_agent_index.py --stats`：3 源 568 条，完整性 OK。
- `build_catalog.py --check`：skills / agents 目录均 up to date。

## 学习点

- **验证器的「扫描」必须覆盖捆绑资源**：只扫 AGENT.md 会漏掉 `references/`、脚本里的密钥与危险管道；而定义发现的 `EXEMPT_DIRS` 不能复用于安全扫描，否则 exemptions 会变成安全盲区。
- **BOM 是 Windows 用户路径上的高频输入**：任何读取用户产出文件的入口都应 `utf-8-sig`；读端不一致会让「同一份合法文件」在不同脚本里表现不同，甚至静默产出不可加载的安装文件。
- **机器可读输出要守住契约**：`--json` 混入人类文本 = 契约破坏；`--no-dl` 之类的开关若只出现在 help 而不在实现里，就是文档≠行为。
- **计数即文档**：评分维度数、豁免清单、扩展名白名单这类「集合」最易随实现漂移，改动时须同步文档并被测试钉住。
