# Personal-AI-Tools

个人 AI 技能/代理创建器集合仓库：维护两个**同构、互不依赖**的创建器技能（`skill-creator` / `agent-creator`），并托管已验证能力库（`skills/` 技能库、`agents/` 代理库）。

## 结构（dev 工作区 + 成品即源）

```
Personal-AI-Tools/
├── README.md                   # 本文件
├── skill-creator/              # dev 工作区（仅开发所需文件）
│   ├── README.md               布局与开发指引
│   ├── AGENTS.md               dev 角色守则：成品演进维护者
│   ├── INSTALL.md              安装手册（不随成品分发）
│   ├── tests/                  dev-only：pytest
│   └── skills/skill-creator/   成品 = 技能唯一源（编辑在此；随仓库提交）
├── agent-creator/              # dev 工作区（同构）
│   ├── README.md
│   ├── AGENTS.md               dev 角色守则：成品演进维护者
│   ├── INSTALL.md              安装手册（不随成品分发）
│   ├── tests/                  pytest（成品自包含自检 + validate 回归）
│   └── skills/agent-creator/   成品 = 技能唯一源（编辑在此；随仓库提交）
└── tools/                      # dev-only 工具层（不随成品分发）
    ├── README.md               工具层总览 + 安装编排设计（权威）
    ├── scripts/build_catalog.py 能力库 CATALOG 生成器
    ├── scripts/install.py       安装编排器（打包放置到客户端落点）
    └── tests/                   install.py 回归
```

两工作区**同构精简**（无 `build/`）：成品 = `SKILL.md`（唯一入口）+ `README.md` + `scripts/` 等；成品内 `AGENTS.md` 均已删除、成品内 `INSTALL.md` 均已移至工作区根（工作区根各有 dev-only `AGENTS.md` 角色守则 + `INSTALL.md`，不随成品分发）。

成品即源：两创建器的能力本体**只**存于各自 `skills/<creator>/`（源即成品，随仓库提交，无生成/拷贝步骤）；工作区根不保留副本，从根上避免重合与漂移。成品须**自包含**——不依赖本仓库任何 dev-only 文件（tests/、INSTALL.md、README.md），也不依赖宿主仓库。

## 常用命令（在各 creator 工作区根执行）

```bash
python -m pytest tests/ -q              # 各 creator 工作区回归 + 成品自包含自检
python -m pytest tools/tests -q         # 工具层回归（安装编排器 install.py）
# skill-creator 发布检查：pytest 之外，成品 strict 自检（引用不悬空等）
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator
```

## 使用方式

- opencode 之类客户端可经 `skills.paths` 直接指向成品目录（`skill-creator/skills/skill-creator/`、`agent-creator/skills/agent-creator/`）；安装到各客户端的完整步骤见各工作区根 `INSTALL.md`。
- **安装能力库 / 创建器 = 经 `tools/scripts/install.py` 打包放置**（按各端适配 frontmatter + 自检/回滚；落点矩阵与编排见 `tools/README.md`）：
  ```bash
  python tools/scripts/install.py --all skills --client claude --scope workspace --dest <目标仓库根>
  python tools/scripts/install.py --creator skill-creator --client opencode --scope workspace --dest <目标仓库根>
  ```
  纯复制仅作无该脚本时的回退（落点见各库 `README.md`）。
