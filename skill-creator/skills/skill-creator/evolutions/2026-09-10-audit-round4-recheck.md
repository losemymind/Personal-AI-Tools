# 审计闭环：第四轮（修复后复核，delta 角色解析 + dotenv/续行/tab/PowerShell 覆盖）

## 基本信息
- 日期：2026-09-10
- 版本：skill-creator 0.9.17 → 0.9.18
- 触发来源：第三轮修复后由 code-reviewer 子代理对**修复后成品**复核，又发现 2 项高/多项中低真实缺陷

## 需求与证据

逐条复现后修复：

1. **`aggregate_benchmark._ordered_configs` 混合命名下 delta 符号反转（高）**：primary 仅以别名出现（如 `skill`、`with_skill` 缺席）而 baseline 以精确名出现（`without_skill`）时，单次遍历把 `without_skill` 放进 ordered[0]（primary 位）→ 报告 `primary=without_skill, pass_rate=-0.60`。复现：配置 `skill`(1.0)/`without_skill`(0.2) → 得 −0.80（应为 +0.80）。既有测试只覆盖「两侧皆别名」，漏此混合。
2. **`.env` 密钥漏扫（高，第三轮修复不完整）**：`os.path.splitext(".env")==('.env','')`、`.env.local==('.env','.local')`，扩展名白名单对最典型的 dotenv 文件名失效；第三轮补的 `.env` 扩展名从未生效。复现：技能放裸 `.env`（`sk-…`）→ `--strict` 全绿。
3. **管道落行尾绕过（中）**：shell 允许 `curl x |` 换行 `bash`；原归一化只合并反斜杠续行。`curl x |`+换行+`bash`、`wget … |`+换行+`sh`、`irm … |`+换行+`iex` 均漏检。
4. **tab 缩进代码块漏检（中）**：`_line_indent_map` 把 tab 记 1 列，而 CommonMark 中 1 tab = 4 列；`\tcurl … | bash` 逃过代码上下文判定。
5. **PowerShell/Windows shell 覆盖错配（中）**：别名映射颠倒（`irm`=Invoke-RestMethod、`iwr`=Invoke-WebRequest），且 `pwsh`/`powershell`/`cmd` 未在 shell 集合 → `iwr … | iex`、`curl … | pwsh|powershell|cmd` 全漏（本仓库主平台 Windows）。
6. **`scan_skill_dir` 丢弃 `tags`/`tools`（中，第三轮修复不完整）**：`frontmatter_of` 已能解析，但扫描项未透传 → 扫描源的 `tags`/`tools`/`client_targets` 恒空，`--tool` 与 tags 检索对这些源永久失效。
7. **`command -v bash` 误报（低）**：`command` 在 launcher 集，`-v` 被当取值跳过、`bash` 被当执行体；实际只是查路径。
8. **`--no-dl` 根目录差一级（低）**：`parents[2]` 指到 `skills/`，使 `skills_root="skills"` 解析为不存在的 `skills/skills`；改为当前目录。
9. **文档（低）**：`skill-anatomy.md` 建议的 `{{#include …}}` 无任何客户端支持（删除）；TOC 阈值 `>300` 与 SKILL.md/quality-bar 的 `>100` 不一致（统一为 100）。

## 采纳要点（改了什么）

- **`scripts/aggregate_benchmark.py`**：`_ordered_configs` 先**独立**把 primary/baseline 各自解析为实际配置名（精确名 → 别名），再按角色排序。
- **`scripts/validate_skills.py`**：新增 `_is_scannable_text`，把 `.env`/`.env.*` 纳入扫描。
- **`scripts/utils.py`**：归一化补「`|` 落行尾续行」；`_line_indent_map` 按显示列（tab→4 倍数）计缩进；`_PIPE_CHAINS` 修正 PowerShell 别名（`irm`/`iwr`/`Invoke-RestMethod`/`Invoke-WebRequest`）并为 curl 链补 `powershell`/`pwsh`/`cmd`；`command -v`/`-V` 不再判为执行。
- **`scripts/build_index.py`**：`scan_skill_dir` 透传 `tags` 与 `tools`（映射为 `plugin.targets`）；`--no-dl` 改用当前目录并更新帮助。
- **`references/skill-anatomy.md`**：删除 `{{#include}}` 伪语法；TOC 阈值统一 100。
- 测试：`tests/test_hardening.py` +5 例 → **153 例**（原 148）。
- 同步 `.opencode` 镜像；版本 0.9.17 → 0.9.18。

## 验证结果

- `python -m pytest tests/ -q`：**153 passed**。
- 成品 strict / 能力库 strict（5）/ agent strict（32）/ `build_catalog.py --check` 全绿。

## 学习点

- **修复本身要回归复核**：第三轮「补 `.env` 扩展名」其实无效（`splitext` 对 dotfile 失效），只有拿到修复后成品再跑一遍才暴露——修完必须验「修是否真的生效」，别只验「测试还是绿」。
- **单次遍历决定角色顺序是危险的隐式约定**：角色解析必须先独立求解再排序，混合命名（别名/精确名）是常规输入，不是边角。
- **平台覆盖即正确性**：本仓库主平台是 Windows，安全扫描却只认 POSIX shell——`iwr | iex`、`curl | cmd` 必须同列覆盖。
