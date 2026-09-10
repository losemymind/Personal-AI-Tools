# 加固记录：验证器缺口补齐（name 字符集 / evals.json / 反引号引用）

## 基本信息
- 日期：2026-09-10
- 需求：审阅 `validate_skills.py` 后，把「已声明但未被机器强制」的纪律补成验证器检查。
- 来源：本仓库自审；E1 对照同构孪生 `validate_agents.py`（twin parity）。

## 缺口与修复
- **E1 name 字符集未强制（twin parity）**：验证器原只查「`name` 与目录名一致 + ≤100」，不校验小写 kebab-case；而孪生 `agent-creator` 的 `validate_agents.py` 早已用 `^[a-z0-9]+(-[a-z0-9]+)*$` 强制。目录名 `Bad_Name` 能通过，违反 SKILL.md/模板声明的命名规则。修复：`validate_skills.py` 增 `NAME_PATTERN`，`name` 非 kebab-case 即报错。
- **E2 evals.json 无机械检查**：quality-bar 第 8 项与发布纪律要求「触发用例随技能沉淀」，但验证器完全不检查。而历史 `prompt`/`query` 键漂移正是这类缺口漏掉的。修复：技能存在 `evals/evals.json` 或根 `evals.json` 时**强制形状**——可解析、含 `evals` 数组、每项有非空 `query`（legacy `prompt` 可接受）与布尔 `should_trigger`；**缺失仅给 advisory**（不阻断，因能力库尚有技能未随附 evals）。
- **E3 反引号引用扩展名白名单偏窄**：原仅覆盖 `md|py|sh|json|yaml|yml|ts|js`，数据/文本资源（如成品的 `indexes/upstream.db`）引用不受检。修复：白名单扩为常见代码/数据/文本类型（含 `db`/`txt`/`xml`/`toml`/`css`/`html`/`rs`/`go` 等）。
- **minor risk: unknown**：新增 advisory（新技能不建议用 `unknown`）。

## 版本
- `0.9.1 → 0.9.2`（patch：验证器检查增强，无方法论变更）。

## 验证
- `python -m pytest tests/ -q`：52 例全绿（新增 6 例：非 kebab 失败、kebab 通过、db 引用悬空/存在、evals 畸形失败、evals 合法通过、evals 缺失仅 advisory）。
- 成品 strict 自检 + 能力库 strict（5 技能）均通过；新 advisory 不阻断 strict（strict 仅对 warnings 失败）。
- `.opencode/skills/skill-creator/` 安装副本同步（SKILL.md / validate_skills.py / references/quality-bar.md）。
- 能力库现状：`code-review-skill`、`pr-summarizer`、`prd-generator` 未随附 evals → 现以 advisory 提示（非失败）；`mcp-builder`、`ue5-performance-optimization` 的 evals.json 形状通过。

## 学习点
- **孪生纪律要成对落地**：E1 表明同构工作区里一侧 enforce、另一侧漏掉，会产生「文档说 kebab、验证器却不查」的漂移；同模板改动应两侧同查。
- **advisory 与 error 的分寸**：把「应做但尚未普及」的纪律（evals）做成「存在则强制、缺失仅提示」，既堵住形状漂移，又不误伤存量技能——比一刀切 error 更可持续。
