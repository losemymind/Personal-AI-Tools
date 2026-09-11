# agent-creator

创建自定义 Agent（代理）的目录。与技能创建器（skill-creator，独立项目 `losemymind/Personal-AI-Tools`）平行同构：skill 回答「怎么做」，agent 回答「谁来做」。

## 结构

```
agent-creator/
  README.md                        # 说明
  SKILL.md                         # 核心：创建/改进/验证/安装代理的方法论（唯一入口）
  scripts/
    create_agent.py                 # 交互式脚手架生成器
    validate_agents.py              # 自动验证器（frontmatter/边界/权限/协作/链接/密钥与危险管道扫描）
    compare_agents.py               # 自建 vs 上游候选对比择优（质量7维+结构4维）
    adapt_agent.py                  # 安装前 frontmatter 四端转换器（claude/opencode 适配+post-check）
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
3. 使用 `templates/AGENT.template.md` 作为骨架（或 `create_agent.py` 脚手架）
4. 运行自动验证：`python scripts/validate_agents.py --dir <你的代理目录>`
5. 安装到客户端：本技能自身的安装 = 把本目录放置到目标客户端 skills 目录；产出的代理**先 `scripts/adapt_agent.py <目录> --client <claude|opencode|codex|deepseek>` 转换 frontmatter，再把产物放置**到目标客户端 agents 目录（命令与落点见 SKILL.md「多客户端安装指引」/阶段 7）
6. 经验证的代理归档到可分发位置

## 技能 vs 代理

| | 技能 | 代理 |
|---|---|---|
| 回答 | 怎么做 | 谁来做 |
| 内容 | 步骤与规则 | 身份、边界、权限、协作 |
| 时机 | 用户触发场景 | 被调用/被分派 |
| 例子 | 技能创建器 | 审查者、规划者、测试者 |