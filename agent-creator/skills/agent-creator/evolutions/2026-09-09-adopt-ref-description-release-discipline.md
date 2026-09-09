# 纪律升级：对齐 skill-creator 0.6 的引用 / description / 发布纪律（孪生同构）

## 基本信息
- 日期：2026-09-09
- 需求：把 agent-creator 成品（SKILL.md / references / scripts / tests）升级到与同构孪生 skill-creator 0.6 一致的纪律水位——skill 侧此前已把「references 一层深 / description 即触发面 / 发布纪律」硬化，agent 侧缺失。
- 可对照基准：同构孪生 `skill-creator`（0.6.0/0.6.1，本仓库）：`SKILL.md` references 引用纪律硬规则、description 触发面（单行/无 `<>` 占位符）、触发失败分类（假阴/假阳/run_error）、入库发布纪律（secret 扫描/隔离验证/版本化原子补丁）、`validate_skills.py` description advisory。
- 上游代理库（agency/ccgs/agency-zh）非本次对比对象（它们是代理内容源，不是方法论源）。

## 采纳要点（按孪生纪律逐项对齐）
1. **references 引用纪律（硬规则）**：SKILL.md「渐进式披露」节增声明——references 只从 SKILL.md 一层深导读、refs 间不互链成图、>100 行加目录、超大文件附 grep 模式。落点修正：`references/agent-anatomy.md` 的 refs→refs（→ `references/agent-template.md`）改经 SKILL.md 导读的文字指向；同文件顺带修复**悬空的 `install_agent.py` 引用**（脚本从未存在，改指 SKILL.md「多客户端安装指引」）。
2. **description 触发面（硬约束）**：SKILL.md「前置元数据字段规范」增段——description 是唯一触发门面，单行、≤200、无 `<>` 占位符、不写步骤摘要；质量清单「元数据」组 description 行补「单行/无占位符」；`references/agent-template.md` 字段说明与 `agent-quality-bar.md` 元数据项同步补约束。
3. **触发失败分类**：SKILL.md 阶段 6 增假阴性/假阳性/run_error 归因纪律（改前先归因，run_error 别乱改 description）。
4. **发布纪律**：SKILL.md 新增「入库与发布纪律（提交/入库前逐项）」节——secret 扫描、隔离安装实测再交付、版本化原子补丁（未验证草稿不直入 SKILL.md）。
5. **质量条增项**：`agent-quality-bar.md` 5 项 → **6 项**（新增「渐进披露与引用纪律」，自动查悬空 + 人工查层级）；SKILL.md 质量清单增「渐进披露与引用组织」组。
6. **验证器 advisory**：`validate_agents.py` description 检查补 `<`/`>` 占位符与跨行 advisory（仅提示不失败，镜像 validate_skills.py，不改变库门禁语义）；补 pytest 2 例（test_description_angle_bracket_advisory / test_description_multiline_advisory）。
- 版本：0.4.1 → **0.5.0**（方法论升级，minor）。
- 验证：`pytest tests/`（agent 7 → 9 例）+ 能力库 `validate_agents.py --strict --dir agents`（32，全绿）通过。

## 结论
- 优者：对齐孪生 skill-creator 0.6 纪律（其为已被采纳的更成熟纪律来源）→ 采纳移植。
- 本成品 references 从「互链合法但无纪律」升级为「一层深 + 不互链」硬规则（agent 侧先前 guard 注明「如需对齐孪生须用户确认」，本次用户确认全做）。

## 提炼的学习点
- 孪生纪律移植可整段对照：引用纪律（SKILL 段+anatomy 落点）、description（SKILL 段+template+quality-bar 三处同步）、发布（独立节）——纪律须在 SKILL.md 声明 + 各 references 落点 + 质量条/清单 + 验证器/测试四处闭环，只改一处会漂移。
- references 内容会携带上游残留（如幽灵 `install_agent.py`）：做引用纪律梳理时顺带全量核对 references 内反引号文件名是否真实存在（自包含扫描只查 `/` 内含路径，无 `/` 的孤立脚本名会被豁免漏检）。
- advisory（不失败）是「纪律未被自动 enforce 但不想破坏库门禁」的中间态：description 触发纪律以 advisory 落地，质量条注明「自动查悬空 + 人工查层级」而非全部自动化。
