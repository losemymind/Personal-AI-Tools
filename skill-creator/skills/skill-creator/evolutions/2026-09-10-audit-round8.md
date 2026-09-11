# 审计闭环：第八轮定向加严（脚手架空白描述契约）

## 基本信息
- 日期：2026-09-10
- 版本：skill-creator 0.9.21 → 0.9.22
- 触发来源：与 agent-creator 第四轮同批——先运行期实证第七轮修复是否真生效，再攻 HANDOFF 第 9 条待办中「脚手架非 ASCII/多行 description 产物合法性」，并按孪生对称性复核。

## 最近一轮修复生效性复核（运行期探针）
- PowerShell 反引号 / CMD 脱字符续行、引号/子壳 shell token、`SENSITIVE_DOTFILES`、隐藏目录 `.ssh/id_rsa`/`.aws/credentials`：**逐项实证已改变且无误报回归**（`command -v bash`、`grep bash` 不误报）。
- `create_skill.py` 对非 ASCII / 多行 / 含引号含冒号 / 含反斜杠的 description 均产出**合法 YAML 且解析往返一致**（其 `re.sub` 早已使用 lambda）；`search_index.py` 的 CJK+FTS 混合查询（含 `"`/`*`/`OR`/`-`/括号/`+`/`:`/不平衡引号/纯空白/`%`/`_`/`\`）全部 rc=0、无崩溃、无语法注入。

## 本轮新发现并修复（1 项，孪生共享）
1. **空白 description 产出「自不合法」产物（低-中，契约/fail-open）**：`create_skill.py` 的 `--description "   "` 非空（truthy）故通过校验并写入文件，但 `validate_skills.py` 会以「description field is empty or whitespace only」拒绝 → 脚手架产物不过自己的门。同类缺陷在孪生 `create_agent.py` 亦存在（见其 `evolutions/2026-09-10-audit-round4.md`）。修复：两侧均在写文件前前置 `if not description.strip(): 拒绝`。

## 采纳要点（改了什么）
- `scripts/create_skill.py`：描述去除前后空白后为空则拒绝（`len > 1024` 校验之前）。
- 测试：`tests/test_hardening.py` 新增 1 例 → skill-creator pytest **166 → 167**。
- 版本 0.9.21 → 0.9.22。
- `.opencode/skills/skill-creator` 安装副本同步 `SKILL.md` + `scripts/create_skill.py`（哈希一致，仅源码差异；`__pycache__` 除外）。

## 验证结果
- `python -m pytest tests/ -q`：**167 passed**（原 166 + 新 1）。
- `validate_skills.py --strict --dir skills/skill-creator`：Checked 1，全绿。
- `validate_skills.py --strict --dir E:\GitHub\Personal-AI-Tools\skills`：Checked 5，全绿。
- `search_index.py --stats`：4 源 2187 条。
- `build_catalog.py --check`：up to date。
- 运行期探针：空白描述由「写入并被验证器拒绝」变「前置拒绝、不落盘」。

## 学习点
- **「非空」不等于「有内容」**：`"   "` 是 truthy 却会被下游校验器判空；脚手架的所有契约边界（长度/空白/版本）都要与验证器判定逐一对齐，否则产物不过自己的门。
- **孪生对照可发现单侧遗漏**：本项与 agent 侧的 YAML/`--out` 缺陷同源，均因一侧有护栏、另一侧缺失。
