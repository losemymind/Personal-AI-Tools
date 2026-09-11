# 纪律：成品零交叉引用 + 自安装文档化（LLM 直接安装）

## 基本信息
- 日期：2026-09-11
- 对象：`SKILL.md`（多客户端安装指引）、`scripts/package_skill.py`、`scripts/validate_skills.py`
- 触发来源：用户要求「验证两创建器独立性 + 设计测试用例 + 支持 LLM 客户端自行安装（不用 `install.py`）」。决策：严格「零交叉引用」（连「相关技能」提及也禁止）+ 自安装用**纯文档流程**（不加脚本）。

## 背景与证据
- 两创建器声称互不依赖，但成品内散落对 sibling 的文档/注释引用（`SKILL.md` 相关技能段、`package_skill.py` docstring、`validate_skills.py` 注释），缺失自动门。
- 用户选定更严约束：成品不得出现 sibling 的名称与脚本名（零交叉引用）。

## 改动
- `SKILL.md`：删除「相关技能」中的 `agent-creator` 交叉条目；「多客户端安装指引」新增「**自安装**」小节——6 步（定位→作用域/端→整体复制→自检 `validate_skills.py`/`search_index.py`→清缓存→交付），LLM 客户端可直接照做，不依赖仓库级 `install.py`。
- `scripts/package_skill.py`：docstring/注释去除对 agent 侧打包器与适配器的提及，改为自述式表述。
- `scripts/validate_skills.py`：`SENSITIVE_DOTFILES` 注释去除对 agent 侧扫描器的提及。
- 新增 dev-only `tests/test_independence.py`（3 例）：成品复制到**仓库外**仍能自校验、索引可用；成品无 sibling 引用。
- 记录：`tools/tests/test_creators_independent.py`（仓库级零交叉引用门）+ `tools/README.md` 沿革。

## 验证结果
- `python -m pytest tests/ -q` → **202 passed**（199 → 202：`test_independence.py` +3）
- `python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator` → 全绿
- `python skills/skill-creator/scripts/validate_skills.py --strict --dir <仓库>/skills` → Checked 5，全绿
- `python -m pytest tools/tests -q` → **23 passed**（18 → 23：install 回归 +2、独立性 +3）

## 学习点
- **独立性要可执行验证，不是声明**：零交叉引用必须落成扫描门（名称 + 脚本名），否则文档/注释里的耦合会长期潜伏。
- **自安装 = 落点 + 自检 + 清缓存的三件事**：成品自带验证器时，LLM 只需按文档复制并跑自检即可完成；把该流程写进 SKILL.md（成品自包含），INSTALL.md 保持 dev-only。
