# 加固记录：审计四项内部债（references 互链 / evals / CI / 评分粒度）

## 基本信息
- 日期：2026-09-10
- 需求：修复只读审阅列出的四项内部债，使成品与自身声明的纪律自洽并补上可复现性环节。
- 来源：本仓库自审。

## 债 1 — references 互链（内容 + 机器护栏）
- **现状**：SKILL.md 声明「references 之间不互链成图」，但 `skill-writing-guide.md` / `skill-template.md` / `quality-bar.md` 正文用**裸兄弟文件名**互相提及，验证器只解析含 `/` 的引用，故从未查出。
- **修复**：三处改为「SKILL.md『读取规则』中的写作规律文档」措辞，去掉 references→references 的图边。
- **护栏**：`validate_skills.py` 新增 `check_references_cross_links()`——扫 `references/*.md`，反引号中出现**同目录已存在的兄弟 references 文件名**（排除自引用、带 `/` 的路径引用、fenced 代码块）即报 error；把「不互链」从文字纪律变成机械强制。

## 债 1.5 — `classify` 重复 token 计数缺陷（连带发现）
- **现状**：`utils.classify` 用 `sum(1 for t in meaningful if t in prompt_tokens)` 计数，`meaningful` 保留了 description 中的**重复 token**。description 里「创建」出现三次，于是任何含「创建」的查询重叠数=3 直接触发（实测 `创建一个专门的代码审查 agent` 假阳性）。
- **修复**：改为按**去重后的 distinct token 集合**求交（`len(set(meaningful) & prompt_tokens) >= 2`），与函数 docstring 的「share >=2 meaningful tokens」语义一致。

## 债 2 — 缺 evals.json（dogfooding）
- 为 skill-creator 主体新增 `evals.json`（14 条，8 应触发 / 6 干扰项），并为能力库三个技能 `code-review-skill` / `pr-summarizer` / `prd-generator` 各补 evals.json（各 11 条）。
- 校准：`run_eval.py`（heuristic）——skill-creator 14/14、pr-summarizer 11/11、prd-generator 11/11、code-review-skill 10/11（唯一假阳性「总结…PR 改动」源于 code-review 与 pr-summarizer 共享通用词 pr/改动，属词重叠固有，保留并记录）。
- 效果：成品与全部 5 个库技能 strict 自检的「No evals.json」advisory 清零。

## 债 3 — 无 CI（可复现性）
- 新增 `.github/workflows/validate.yml`，三个 job 复刻本地发布门：skill-creator（pytest + 成品 strict + 库 strict）、agent-creator（pytest + 库 strict）、catalog（`build_catalog.py --check`）。
- 本地已用 Python `yaml.safe_load` 校验 workflow 语法，并逐一跑通等价命令（全绿）。

## 债 4 — 对比评分粒度（暂不修，维持文档化）
- `compare_skills.py` 的 0/0.5/1 档为结构与门槛启发式，不衡量领域深度（`references/skill-comparison.md` 已声明为局限）。细化会改变分数口径、使 `evolutions/` 历史分值不可比，投入产出比低，**维持现状**。

## 版本
- `0.9.2 → 0.9.3`（patch：验证器新增检查 + 触发启发式修正 + evals 补齐）。

## 验证
- `python -m pytest tests/ -q`：55 例全绿（新增 3 例：references 互链失败、自引用/路径引用放行、classify 去重）。
- 成品 strict 自检 + 能力库 strict（5 技能，advisory 清零）+ 代理库 strict（32）全通过。
- `.opencode/skills/skill-creator/` 安装副本同步 7 个改动/新增文件。

## 学习点
- **声明的纪律没被机器强制 = 会被自己违反**：references 互链纪律写在 SKILL.md 却没进验证器，结果成品自身就踩线。补验证器是唯一可靠的止损。
- **评测器自身要被评测**：`classify` 的重复计数缺陷只有在新写 evals、遇到真实假阳性时才暴露——「拿真实查询压评测器」本身是有效的自检手段。
