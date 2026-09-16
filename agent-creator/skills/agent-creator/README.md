# agent-creator

创建自定义 Agent（代理）的目录。技能回答「怎么做」，代理回答「谁来做」——本目录专注后者。

## 上游外部仓库（索引来源）

「先查后建」检索的上游代理目录已内置为多源索引（`indexes/upstream.db`，随技能分发）：

| 源 | 仓库 | 代理数 | 索引方式 | 检索 `--source` |
|---|---|---|---|---|
| **agency** | [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | 258 | 扫描顶层 division 目录下的 `*.md` 代理定义 | `agency` |
| **ccgs** | [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) | 49 | 扫描 `.claude/agents/*.md`（Claude Code 子代理） | `ccgs` |
| **agency-zh** | [jnMetaCode/agency-agents-zh](https://github.com/jnMetaCode/agency-agents-zh) | 261 | 同 agency 布局的中文版（含 company/hr/legal 等特有 division） | `agency-zh` |

- 检索全库：`python scripts/search_agent_index.py "<关键词>"`（默认查所有源）
- 按源检索：加 `--source agency`（或 `ccgs` / `agency-zh`）
- 重建：`python scripts/build_agent_index.py [--source all|agency|ccgs|agency-zh]`
- 许可以各上游仓库 LICENSE 为准，入库代理需保留来源归属
- 索引细节见 `references/agent-index.md`；新建代理时先在多源中「先查后建」

## 结构

```
agent-creator/
  README.md                        # 说明
  SKILL.md                         # 核心：创建/改进/验证/安装代理的方法论（唯一入口）
  scripts/
    create_agent.py                 # 交互式脚手架生成器（默认扁平 <out>/<名>.md；--layout dir 出 <out>/<名>/AGENT.md）
    validate_agents.py              # 自动验证器（frontmatter/边界/权限/协作/链接/密钥与危险管道扫描）
    compare_agents.py               # 自建 vs 上游候选对比择优（质量7维+结构4维）
    adapt_agent.py                  # 安装前 frontmatter 四端转换器（claude/opencode 适配+post-check）
    package_agent.py                # 代理目录打包器（按端适配 frontmatter + 复制整目录 + post-check）
    search_agent_index.py           # 检索上游代理索引（FTS5/CJK/分类过滤）
    build_agent_index.py           # 构建上游代理索引（三源：agency/ccgs/agency-zh）
    security_scan.py                # 密钥/危险远程执行管道扫描（被 validate_agents.py 复用）
    _project_paths.py              # 技能根定位辅助（自包含，不依赖宿主仓库）
  indexes/
    upstream.db                    # 上游代理 SQLite 索引（随技能分发，安装即得）
  references/
    agent-template.md              # 代理模板：字段与四端兼容矩阵
    agent-anatomy.md               # 代理解剖：结构与技能/代理取舍
    agent-quality-bar.md            # 质量标准（7 项质量检查）
    agent-index.md                  # 上游代理索引：构建/检索/更新说明
    agent-comparison.md             # 对比择优：质量7维+结构4维评分维度
  agents/
    reviewer.md                    # 评审子代理：评分/审核 → pass·revise + review.json（无人工评审闭环）
  templates/
    AGENT.template.md              # 新代理骨架
  evolutions/                      # 对比择优学习记录（反馈闭环）
    README.md                      # 记录规范与模板
    <YYYY-MM-DD>-<主题>.md         # 日期平铺的对比/采纳记录
```

## 使用

1. 参考本目录 `SKILL.md` 的代理创建方法论
2. 先查上游代理索引（先查后建）：`python scripts/search_agent_index.py "<关键词>"`（如无现成再创建）
3. 使用 `templates/AGENT.template.md` 作为骨架（或 `create_agent.py` 脚手架：默认扁平单文件 `<out>/<名>.md`；需捆绑 `references/` 或目标库以 `AGENT.md` 为键时加 `--layout dir`）
4. 运行自动验证：`python scripts/validate_agents.py --dir <存放代理的目录>`
5. 安装到客户端：本技能自身的安装 = 把本目录放置到目标客户端 skills 目录；产出的代理**先 `scripts/adapt_agent.py <目录> --client <claude|opencode|codex|deepseek>` 转换 frontmatter，再把产物放置**到目标客户端 agents 目录（命令与落点见 SKILL.md「多客户端安装指引」/阶段 7）
6. 需要把同一代理目录一次打包给多个客户端时，用 `scripts/package_agent.py <代理目录|AGENT.md> --client claude --client opencode --client codex --client deepseek --out <产物目录> [--zip]`（复制整棵代理目录 + 各端适配 + post-check；用法见 SKILL.md 阶段 7）
7. 经验证的代理归档到可分发位置

## 技能 vs 代理

| | 技能 | 代理 |
|---|---|---|
| 回答 | 怎么做 | 谁来做 |
| 内容 | 步骤与规则 | 身份、边界、权限、协作 |
| 时机 | 用户触发场景 | 被调用/被分派 |
| 例子 | PR 摘要技能 | 审查者、规划者、测试者 |