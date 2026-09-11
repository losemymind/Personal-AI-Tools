# 纪律：成品零交叉引用 + 自安装文档化（LLM 直接安装）

## 基本信息
- 日期：2026-09-11
- 对象：`SKILL.md`（多客户端安装指引）、`README.md`、`references/agent-comparison.md`、`scripts/{package_agent,validate_agents,security_scan,create_agent}.py`
- 触发来源：用户要求「验证两创建器独立性 + 设计测试用例 + 支持 LLM 客户端自行安装（不用 `install.py`）」。决策：严格「零交叉引用」+ 自安装用**纯文档流程**（不加脚本）。

## 背景与证据
- 成品多处引用 sibling：`README.md` 首段与「技能 vs 代理」表、`SKILL.md` 渐进披露标题与相关技能段、`references/agent-comparison.md`、以及四个脚本的 docstring/注释。
- 用户选定更严约束：成品不得出现 sibling 的名称（中英）与脚本名（零交叉引用）。

## 改动
- `SKILL.md`：`### 渐进式披露（与 skill-creator 同构）` → `### 渐进式披露`；删除「相关技能」中的 `skill-creator` 条目；「多客户端安装指引」新增「**自安装**」小节——6 步（定位→作用域/端→整体复制到 skills 目录→自检 `search_agent_index.py --stats` 与脚手架→验证往返回合→清缓存→交付），LLM 客户端可直接照做，不依赖仓库级 `install.py`。
- `README.md`：首段与「技能 vs 代理」表改为自述式、不含 sibling。
- `references/agent-comparison.md`：评分模型描述去除「与另一端同构」的对比句。
- `scripts/package_agent.py` / `validate_agents.py` / `security_scan.py` / `create_agent.py`：docstring/注释去 sibling 脚本名与创建器名。
- 新增 dev-only `tests/test_independence.py`（3 例）：成品复制到**仓库外**仍能跑索引、脚手架→验证往返；成品无 sibling 引用。
- 记录：`tools/tests/test_creators_independent.py`（仓库级门）+ `tools/README.md` 沿革。同时修复 `install.py` 对 agent-creator 的误校验（技能形态目录不该跑 `validate_agents.py`）。

## 验证结果
- `python -m pytest tests/ -q` → **90 passed**（87 → 90：`test_independence.py` +3）
- `python skills/agent-creator/scripts/validate_agents.py --strict --dir <仓库>/agents` → Checked 32，全绿
- `python -m pytest tools/tests -q` → **23 passed**（含 `--creator agent-creator` 安装回归）

## 学习点
- **自包含 ≠ 无交叉引用**：脚本能独立运行不等于成品文档零耦合；把「名称/脚本名不得出现对端」落成扫描门才能锁死独立。
- **agent-creator 是技能形态的创建器**：分发 `validate_agents.py` 只用于校验它所创建的代理库，不能用以校验自身目录——安装编排须按入口文件判定验证器是否适用。
