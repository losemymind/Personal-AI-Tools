# agent-creator 开发目录

本目录是 agent-creator 技能的**开发工作区**（位于 `losemymind/Personal-AI-Tools` 仓库内）。真正的技能本体只存放一处：

```
agent-creator/                     ← 开发工作区（本目录）
├── AGENTS.md                      ← dev 角色守则：成品演进维护者（不随成品分发）
├── README.md                      ← 本文件：布局与开发指引
├── INSTALL.md                     ← 安装手册：把成品 skills/agent-creator/ 装到各客户端（不随成品分发）
├── tests/                         ← dev-only：pytest 回归 + 成品自包含自检
└── skills/
    └── agent-creator/             ← 成品目录 = 技能唯一源（编辑就在此处；随仓库提交分发）
```

## 成品即源，不复制

`skills/agent-creator/` 是技能（AGENT 方法论 SKILL.md + scripts/ + references/ + indexes/upstream.db + …）的**唯一存放处**，也是被安装、被 LLM 客户端调用的形态。开发时直接编辑该目录下的文件；**本工作区根目录不保留任何技能文件的副本**——没有「dev 源 + 拷贝」两层，也就没有重合与漂移问题。

## 自包含硬约束

成品 `skills/agent-creator/` 必须**不依赖上层任何文件或工具**：
- 内部引用（`scripts/`、`references/`、`templates/`、`indexes/upstream.db` 等）一律以成品目录自身为根书写。
- 不得引用本工作区的 `INSTALL.md`、`tests/`、`README.md`（那是 dev-only，不进成品）。
- 发布自检由 `tests/test_product_self_containment.py` 把关（引用悬空/指向 dev-only 路径即失败）。成品自身无自校验脚本——`validate_agents.py` 的校验对象是 AGENT.md 代理库，不是本技能成品（技能形态），所以自包含扫描落在 dev-only pytest 里，与 skill-creator 用成品 `validate_skills.py` 自检是不同实现、同一纪律。

## 常用命令

在**本工作区根**（`E:\GitHub\Personal-AI-Tools\agent-creator`）执行：

```bash
# 回归 + 发布自检（提交/推送前必跑）
python -m pytest tests/ -q        # 含成品自包含自检（引用不悬空、无 AGENTS.md/INSTALL.md 残留）
```

## 提交说明

本目录改动技能后，跑通上方命令即可 commit/push。
