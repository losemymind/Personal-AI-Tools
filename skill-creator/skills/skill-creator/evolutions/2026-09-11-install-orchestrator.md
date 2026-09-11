# 架构：安装编排分层（P1–P4）与 package_skill 的 allowed-tools 映射

## 基本信息
- 日期：2026-09-11
- 触发来源：用户质疑 `package_skill` 只放在 skill-creator 里「不太合适」——安装库技能、安装两个创建器本身都要用它；并确认保留 `allowed-tools` 作为技能规范白名单键并按端映射。
- 结论：**打包器留成品内**（独立可安装不可破），新增仓库级 **安装编排器**。设计权威见仓库工具层文档（`tools/README.md`）。

## 分层决策
| 层 | 归属 | 职责 | 随成品分发 |
|---|---|---|---|
| 打包器 `package_skill.py` | 本成品内（已存在） | 单 skill → 单客户端：frontmatter 变换 + 树复制 + 每端 post-check | 是 |
| 安装编排器 `install.py` | 仓库 `tools/scripts/`（dev-only） | 跨产物编排 + 落点矩阵 + staging/放置 + 自检回滚 + 缓存清理 | 否 |

关键认知：创建器本身就是 skill（都有 `SKILL.md`），所以「安装创建器」「安装库技能」「给新建 skill 打包」是同一操作 `package_skill(<skill 目录>)`。

## P1：`package_skill.py` 支持 `allowed-tools` 按端映射
- claude：规范化 canonical 工具名 → 逗号串（原生键 `allowed-tools`）。
- opencode：`CLAUDE_TO_OPENCODE` 反查 → 逐工具 `permission`（白名单 allow、其余 deny、显式优先、字符串简写丢弃 = **不放大权限**）；与旧 `tools` 白名单并集。
- codex/deepseek：透传。客户端标签输入报错。
- 验证：`tests/test_package_skill.py` +8；真实库技能四端打包冒烟通过。

## P2/P3/P4
- P2：新增 `tools/scripts/install.py` + `tools/tests/`（18 例）；自动检测客户端、落点矩阵、`--force` 备份、失败回滚。
- P3：文档收敛（根 `AGENTS.md`/`README.md`、两份 `INSTALL.md`、两库 README、CI 新增 tools job）。**成品 SKILL.md 不引用 `tools/`**（铁律 2 自包含）。
- P4：本记录。

## 学习点
- **能力分层而非搬迁**：把「单产物适配」与「跨产物编排」分层，前者随成品分发（独立可安装），后者是仓库 dev 工具。移动打包器会破坏独立性。
- **规范键 + 按端翻译**：`allowed-tools` 作为技能规范白名单键保留，客户端差异全压到打包器。
- **不放大权限**：白名单必须物化为逐工具 allow/deny；全局字符串 `permission` 简写一律丢弃。
