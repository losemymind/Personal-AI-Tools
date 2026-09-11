# 更新学习样本：重新同步 examples/loki-mode

## 基本信息
- 日期：2026-09-11
- 版本：skill-creator 0.9.22 → 0.10.0（本轮批次）
- 触发来源：`examples/README.md` 称 `loki-mode/references/` 有 16 个子文件，实际 14；上游该目录已增至 15（新增 `detailed-guide.md`）。
- 上游来源：`sickn33/agentic-awesome-skills`（MIT），目录 `skills/loki-mode/`。

## 采纳要点（改了什么）
- 按 `examples/README.md` §更新方式 记录的 sparse-checkout 方式重新拉取上游 `skills/loki-mode/`，覆盖到成品 `examples/loki-mode/`。
- 上游 SKILL.md 的 frontmatter 已与本仓库样本一致（`source: community` / `date_added: 2026-02-27`，无 `author`），无需回填；同步后上/下一致。
- **精选而非全量**：上游该目录现含大量非技能产物（`benchmarks/` 基准结果 999 文件、`demo/` 含 1.28 MB gif、上游 `.github/` CI 配置），按仓库「轻量学习样本」定位**剔除这三类**，仅保留技能内容（`SKILL.md`/`references/`/`scripts/`/`docs/`/`tests/`/`autonomy/`/`integrations/`/`examples/`）。
- `examples/README.md`：`references/` 子文件数由错误的 16 改为同步后的真实值 **15**；补注 loki-mode 为**精选快照**（共 **91 个文件**），并说明未纳入的上游产物类别。

## 验证结果
- 本地 `references/` 计数由 14 → **15**（新增 `detailed-guide.md`）；精选后整目录文件数 **91**（约 0.88 MB）。
- `examples/` 属 `EXEMPT_DIRS`，不参与验证器与自包含扫描；同步后 skill-creator pytest / strict / 能力库 strict 全绿（见本批其他记录与 HANDOFF）。

## 学习点
- **文档里的数字会漂移**：样本目录说明与磁盘实况容易脱节，需在每次上游同步后核对「描述数字 = 磁盘真实值」。
- **上游目录会膨胀**：`loki-mode/` 现含大量生成型基准产物（SWE-bench patch / HumanEval 解）与大体积 demo 资源；同步技能样本时应**剔除产物类目录**（benchmarks/demo/CI），只保留技能内容，避免把仓库当产物仓库。
