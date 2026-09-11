# 新工具：package_skill.py（按客户端打包技能）

## 基本信息
- 日期：2026-09-11
- 版本：skill-creator 0.9.22 → **0.10.0**（新增脚本，feature → minor）
- 触发来源：需要一个确定性工具把某个 skill 目录打包/适配给其它 LLM 客户端；对齐 agent-creator 的 `adapt_agent.py`「按客户端变换 frontmatter + 每端 post-check」模式。
- 覆盖客户端：**claude / opencode / codex / deepseek**（与 INSTALL.md 一致）。

## 设计（用法）
```bash
python scripts/package_skill.py <技能目录> --client <claude|opencode|codex|deepseek> [--client ...] \
    --out <产物目录> [--zip]
```
- `--client` 可重复 / 逗号分隔；`--out` 必填；`--zip` 另出压缩包。
- 产物布局：`<out>/<client>/<技能名>/`（含完整目录树，排除 `__pycache__`/`.pyc`/VCS 缓存），`--zip` 出 `<out>/<client>/<技能名>.zip`。
- 流程：解析 SKILL.md frontmatter → 按端变换 → 复制目录 → 覆盖写回适配后的 SKILL.md → 每端 post-check（不合格则该项报错、不出包，退出码 1；参数错误 2）。

## 关键修复：opencode 权限合并不得丢白名单、不得放大为全局简写
- 旧 `adapt_agent.py` 在 `permission` 为**字符串简写**时会**丢弃 `tools` 白名单**、保留全局简写（放权）。
- `package_skill.py` 的 opencode 适配：把 `tools` 白名单**合并**为逐工具 `permission`：
  - 白名单工具类 key → `allow`；其余工具类 key → `deny`；已有 `permission` 映射中的**显式条目优先**（不被覆盖）；
  - `write`/`patch` 别名并入 `edit`；
  - **不保留可能放大权限的全局 `permission` 字符串简写**（会授予非白名单工具），改为物化逐工具规则。
- `tools: [claude, opencode, codex, deepseek]` 这类「支持客户端」元数据**不**被误当工具白名单（按客户端标签集合识别；对 claude/opencode 丢弃该元数据，codex/deepseek 透传）。
- 其他端：claude 把工具白名单转成逗号分隔的 Claude 工具名（无对应项则报错，绝不省略 `tools`）；codex/deepseek 做 YAML + name/description 冒烟检查后透传。

## 验证结果
- 新增 `tests/test_package_skill.py` **13 例**：opencode 字符串简写下白名单合并、显式 permission 优先、`write→edit` 别名、客户端标签列表不误判、claude 白名单→逗号串、四端打包 + 目录复制 + `__pycache__` 排除、zip 内容、逗号分隔客户端、缺 SKILL.md/未知客户端/缺 description/`--out` 落在技能内等错误路径。
- 本轮 skill-creator pytest 167 → **184**（本项 +13）。

## 学习点
- **适配器的「简写」是权限陷阱**：把结构化白名单与全局字符串简写混用时，简写会放大权限；正确做法是把白名单物化为逐项规则，并让显式声明优先。
- **元数据字段存在同名歧义**：同一 `tools` 字段既可能是「支持客户端列表」又可能是「工具白名单」，适配器必须先判别语义再变换，否则会误改用户数据。
- **每端 post-check 是「不出坏包」的保证**：变换后立即按该端 schema 校验，失败即不写产物，而不是先出包再指望用户发现。
