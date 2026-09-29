# agent-creator

创建自定义 Agent（代理）的目录。技能回答「怎么做」，代理回答「谁来做」——本目录专注后者。

## 上游外部仓库（索引来源）

「先查后建」检索的上游代理目录已内置为多源索引（`indexes/upstream.db`，随技能分发）：

| 源 | 仓库 | 代理数 | 索引方式 | 检索 `--source` |
|---|---|---|---|---|
| **agency** | [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | 258 | 扫描顶层 division 目录下的 `*.md` 代理定义 | `agency` |
| **ccgs** | [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) | 49 | 扫描 `.claude/agents/*.md`（Claude Code 子代理） | `ccgs` |
| **agency-zh** | [jnMetaCode/agency-agents-zh](https://github.com/jnMetaCode/agency-agents-zh) | 261 | 同 agency 布局的中文版（含 company/hr/legal 等特有 division） | `agency-zh` |

- 检索全库：`python scripts/agent_index_search.py "<关键词>"`（默认查所有源）
- 按源检索：加 `--source agency`（或 `ccgs` / `agency-zh`）
- 重建：`python scripts/agent_index_build.py [--source all|agency|ccgs|agency-zh]`
- 许可以各上游仓库 LICENSE 为准，入库代理需保留来源归属
- 索引细节见 `references/agent-index.md`；新建代理时先在多源中「先查后建」

## 结构

```
agent-creator/
  README.md                        # 说明
  SKILL.md                         # 核心：创建/改进/验证/安装代理的方法论（唯一入口）
  scripts/
    agent_create.py                # 交互式脚手架生成器（默认扁平 <out>/<名>.md；--layout dir 出 <out>/<名>/AGENT.md）
    agent_validate.py              # 自动验证器（frontmatter/边界/权限/协作/链接/密钥与危险管道扫描）
    agent_compare.py               # 自建 vs 上游候选对比择优（质量7维+结构4维）
    agent_adapt.py                 # 安装前 frontmatter 四端转换器（claude/opencode 适配+post-check）
    agent_package.py               # 代理目录打包器（按端适配 frontmatter + 复制整目录 + post-check）
    agent_index_search.py          # 检索上游代理索引（FTS5/CJK/分类过滤）
    agent_index_build.py           # 构建上游代理索引（三源：agency/ccgs/agency-zh）
    agent_security.py              # 密钥/危险远程执行管道扫描（由校验器与比较器复用）
    _project_paths.py              # 技能根定位辅助（自包含，不依赖宿主仓库）
  indexes/
    upstream.db                    # 上游代理 SQLite 索引（随技能分发，安装即得）
  references/
    agent-template.md              # 代理模板：字段与四端兼容矩阵
    agent-anatomy.md               # 代理解剖：结构与技能/代理取舍
    agent-quality-bar.md           # 质量标准（7 项质量检查）
    agent-index.md                 # 上游代理索引：构建/检索/更新说明
    agent-comparison.md            # 对比择优：质量7维+结构4维评分维度
  agents/
    agent_reviewer.md              # 评审子代理：评分/审核 → pass·revise + review.json（无人工评审闭环）
  templates/
    AGENT.template.md              # 新代理骨架
  evolutions/                      # 对比择优学习记录（反馈闭环）
    README.md                      # 按问题导读、维护规则与未解决边界
    methodology.md                 # 方法论、评审与发布
    validation.md                  # 校验、安全、生成与比较契约
    distribution.md                # 字段、权限、分发与命名
    indexing.md                    # 索引、检索与数据证据
    library-decisions.md           # 代理导入与采纳证据
    record-map.md                  # 旧日期记录到摘要章节的映射
```

## 工具与角色命名

- 公开脚本采用 `agent_<动作>.py`；同类索引工具采用 `agent_index_<动作>.py`，动作使用小写下划线命名。
- 共享安全模块为 `scripts/agent_security.py`，由校验器与比较器导入；目录定位辅助保留 `scripts/_project_paths.py`，这两个模块不提供独立 CLI。
- 评审角色文件采用 `agent_<角色>.md`，当前入口为 `agents/agent_reviewer.md`。
- 命令、导入、模板和维护记录使用当前资源名；不分发旧名称入口。成品独立定位资源，不依赖宿主仓库布局。

## 使用

1. 参考本目录 `SKILL.md` 的代理创建方法论
2. 先查上游代理索引（先查后建）：`python scripts/agent_index_search.py "<关键词>"`（如无现成再创建）
3. 使用 `templates/AGENT.template.md` 作为骨架（或 `agent_create.py` 脚手架：默认扁平单文件 `<out>/<名>.md`；需捆绑 `references/` 或目标库以 `AGENT.md` 为键时加 `--layout dir`）
4. 运行自动验证：`python scripts/agent_validate.py --dir <存放代理的目录>`
5. 安装到客户端：本技能自身的安装 = 把本目录放置到目标客户端 skills 目录；产出的代理**先 `scripts/agent_adapt.py <目录> --client <claude|opencode|codex|deepseek>` 转换 frontmatter，再把产物放置**到目标客户端 agents 目录（命令与落点见 SKILL.md「多客户端安装指引」/阶段 7）
6. 需要把同一代理目录一次打包给多个客户端时，用 `scripts/agent_package.py <代理目录|AGENT.md> --client claude --client opencode --client codex --client deepseek --out <产物目录> [--zip]`（复制整棵代理目录 + 各端适配 + post-check；用法见 SKILL.md 阶段 7）
7. 经验证的代理归档到可分发位置

## 技能 vs 代理

| | 技能 | 代理 |
|---|---|---|
| 回答 | 怎么做 | 谁来做 |
| 内容 | 步骤与规则 | 身份、边界、权限、协作 |
| 时机 | 用户触发场景 | 被调用/被分派 |
| 例子 | PR 摘要技能 | 审查者、规划者、测试者 |
