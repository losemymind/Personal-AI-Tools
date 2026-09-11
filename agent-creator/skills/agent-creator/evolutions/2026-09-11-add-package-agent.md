# 新增工具：为 agent-creator 增加 `package_agent.py`（代理版打包器）

## 基本信息
- 日期：2026-09-11
- 类型：采纳升级（adopt-）——把孪生 skill-creator 的 `package_skill.py` 纪律移植到 agent 侧，并修复 `adapt_agent.py` 的权限放大缺陷
- 需求来源：为 agent-creator 增加与 skill-creator `package_skill.py` 对应的「整目录/多端打包」确定性工具
- 上游/孪生来源：`skill-creator/skills/skill-creator/scripts/package_skill.py`（0.10.0 新增）与 `agent-creator/skills/agent-creator/scripts/adapt_agent.py`

## 证据与动机
- `adapt_agent.py` 只能转换**一个** AGENT.md（stdout 或 `--out` 单文件），不复制代理目录、不产 zip、一次只针对一个客户端；安装「含 references/ 的代理目录」到多端时需要手工循环，易漂移。
- skill-creator 已有 `package_skill.py` 承担同类职责（复制整树 + 各端适配 + post-check + zip），agent 侧缺失形成不对称。
- 复现 `adapt_agent.py` 的权限放大：给 `tools: [read, grep, write]` + `permission: allow` 的代理做 opencode 适配时，代码走「permission 是字符串」分支，**丢弃整个 tools 白名单**并把 `permission: allow` 原样保留——产出的 opencode 配置对**所有**工具放开权限，且白名单丢失。最小复现：`python scripts/adapt_agent.py <dir> --client opencode`，输出 `permission: allow` 且无逐工具规则。

## 设计与实现
- 新增 `scripts/package_agent.py`，用法 `package_agent.py <agent_dir|AGENT.md> --client claude|opencode|codex|deepseek（可重复/逗号） --out <目录> [--zip]`。
- 输入既可是含 `AGENT.md` 的目录（复制整棵树，排除 `__pycache__`/`.git`/`.pytest_cache` 等缓存与 `.pyc/.pyo`），也可是单个 `AGENT.md`（包内仅该文件）。
- 输出 `<out>/<client>/<agent-name>/AGENT.md`；`<agent-name>` 取 frontmatter `name`（合法 kebab-case），否则回退目录名/文件名 stem；`--zip` 另出同名压缩包。
- 每端先适配再 post-check，不合格**绝不写出**该端产物（fail loudly）。
- 复用 `adapt_agent.py` 的常量与 schema 校验（`OPENCODE_TOOL_KEYS`/`OPENCODE_TOOL_ALIASES`/`CLAUDE_TOOL_NAMES`/`CLAUDE_MODEL_ALIASES` + `check_opencode_frontmatter`/`check_claude_frontmatter`，经 `_translate_schema_check` 统一为 `PackageError`），确保两端 schema 判定不漂移。
- 边界：`--out` 不得位于代理目录内部；`--out` 指向已存在文件报错；目录缺 `AGENT.md` 报错；未知 client 退出码 2；各错误转清晰报错（无 traceback）。退出码 0 全成功 / 1 某端打包失败 / 2 参数错误。

## opencode 放大权限修复（相对 `adapt_agent.py`）
- 修复点：当 `tools` 是真实工具白名单且 `permission` 为**字符串简写**（如 `allow`）时，`package_agent.py` **丢弃该全局简写**，改为把白名单物化为逐工具 `permission`（白名单→allow、其余 tool-class 键→deny、显式 permission 条目优先，`write`/`patch`→`edit`），与 `package_skill.py` 完全一致。
- 实证（运行期复核）：样本 `tools: [read, grep, write]` + `permission: allow` 跑 opencode 打包，产物 frontmatter 为逐工具 map（`read/edit/grep: allow`，`glob/list/bash/task/webfetch/websearch/todowrite/question/skill: deny`），**无全局 `allow`、无 `tools`**；note 明确「dropped global permission shorthand 'allow' (would widen)」。对应 pytest `test_opencode_drops_shorthand_and_merges_whitelist`。
- 范围纪律：**不改** `adapt_agent.py` 既有行为（保持其对现有 7 例测试的语义）；修复只落在新增 `package_agent.py`。`adapt_agent.py` 的同一缺陷作为已知项记录，若后续要对齐需单独评审（其字符串分支是有意的历史语义）。

## 与孪生 `package_skill.py` 的差异
- 输入/产物文件是 `AGENT.md`（非 `SKILL.md`）；frontmatter 校验用 agent 版 schema（opencode 的 `mode`/`color`/`temperature`/`steps`/`options` 等，claude 的 name/description/tools/model）。
- claude 端额外处理 `model`：provider 前缀 `model`（如 `anthropic/claude-sonnet-4-6`）简化为 alias（sonnet/opus/haiku/inherit），无法映射则丢弃；`package_skill.py` 无 model 逻辑。
- `tools: [claude, opencode, codex, deepseek]` 这类「支持客户端」元数据在两端都不会被误当工具白名单。

## 验证结果
```text
agent-creator：pytest 86 passed（68 → +18 新增 test_package_agent.py）
  成品自包含自检通过（package_agent.py / SKILL.md / README / references 引用均解析）
  能力库冒烟：agents/academic/anthropologist 与 agents/code-quality/code-reviewer
    逐客户端（claude/opencode/codex/deepseek）+ --zip 均 rc=0，产物可被对应 post-check 通过
```

## 提炼的学习点
- 孪生技能的工具应对称：skill 侧有「整目录多端打包」后，agent 侧补齐同一纪律，两库安装路径一致、可预期。
- 权限适配必须**最小权限优先**：字符串 `permission` 简写与 `tools` 白名单语义冲突时，安全侧选择是「丢弃可能放权的简写、物化白名单」，而非保留简写丢白名单。
- 修复缺陷应落在新工具而非改动既有工具语义，避免破坏既有测试与历史行为；旧工具的同类问题显式记录、另行评审。
