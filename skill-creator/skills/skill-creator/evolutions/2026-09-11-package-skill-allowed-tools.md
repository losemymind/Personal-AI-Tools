# 工具：package_skill.py 支持 allowed-tools 按端映射（P1）

## 基本信息
- 日期：2026-09-11
- 对象：`scripts/package_skill.py`（技能打包器）
- 触发来源：安装编排设计（`tools/README.md`）P1——让打包器能直接打包**库技能**（此前漏掉 `allowed-tools`）。决策依据：用户确认保留 `allowed-tools` 作为技能规范白名单键并按端映射（不放大权限）。

## 背景
技能 frontmatter 瘦身后（只留 `name`/`description`/`risk`/`category` + 可选 `allowed-tools`），技能侧唯一权限声明是 `allowed-tools`（Claude 工具名白名单）。`package_skill.py` 此前完全不识别该键 → 库技能（如 `code-review-skill`）打包时会丢失权限声明。

## 改动
- 新增 `CLAUDE_TO_OPENCODE` 反查表（`Read`→`read`、`Write`→`edit`…）与 `allowed-tools` 归一化/校验辅助。
- `adapt_for_opencode`：`allowed-tools` → 反查为 opencode 工具类 key，与旧 `tools` 白名单**并集**后合并入逐工具 `permission`（白名单→allow、其余→deny；显式 `permission` 优先；字符串 `permission` 简写丢弃）。
- `adapt_for_claude`：`allowed-tools` 规范化为 canonical Claude 工具名并输出逗号串（原生键保留）；与旧 `tools` 取并集、折叠到 `allowed-tools`。
- `check_claude_frontmatter`：增补 `allowed-tools` 形状校验。
- `allowed-tools` 值大小写不敏感；混入客户端标签 → 报错而非静默丢弃。

## 兼容
- 旧 `tools` 白名单分支保留（回退兼容），行为不变。
- codex/deepseek 仍走通用 YAML + name/description 校验后透传。

## 验证结果
- `python -m pytest tests/ -q` → **193 passed**（185 → 193：`test_package_skill.py` +8）
- `python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator` → 全绿
- `python skills/skill-creator/scripts/validate_skills.py --strict --dir <仓库>/skills` → Checked 5，全绿
- 冒烟：`skills/development/code-review-skill` 四端打包通过（claude `allowed-tools: Read, Grep, Glob, Bash, WebFetch`；opencode 逐工具 permission；codex/deepseek 透传）

## 学习点
- **规范键 + 按端翻译**：`allowed-tools` 作为技能侧的规范白名单键保留；客户端差异全部压到打包器（claude 原生、opencode 反查、codex/deepseek 透传）。
- **不放大权限**：白名单必须物化为逐工具 allow/deny；全局字符串 `permission` 简写一律丢弃。
- **并集而非覆盖**：`allowed-tools` 与旧 `tools` 并存时取并集，避免漏权。
