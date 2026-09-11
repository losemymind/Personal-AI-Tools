# 审计修复：compare/adapt/build/create/reviewer 的计数、递归、权限与自包含门

## 基本信息
- 日期：2026-09-11
- 对象：`scripts/compare_agents.py`、`scripts/adapt_agent.py`、`scripts/build_agent_index.py`、`scripts/create_agent.py`、`agents/reviewer.md`、`references/agent-index.md`、`evolutions/README.md`、`tests/`（新增用例与发布门可达性）、`AGENTS.md`；仓库级 `tools/tests/test_creators_independent.py`（把恒真的跨成品 import 检测改为按对端脚本模块名的真实判据）
- 触发来源：独立审计确认的一批真缺陷（计数漂移、递归漏扫、权限放大、文档声明未实现参数、工具名大小写、发布门死分支）

## 问题 → 修复

1. **compare_agents 候选扫描漏扫（正确性）**：`--all-candidates` 只扫 `upstream_dir` 顶层——分类目录布局（`category/agent/AGENT.md`）会整体漏掉；而若递归实现只认 `AGENT.md`，又会丢掉上游真实的扁平 `<division>/<name>.md` 候选（索引实证 path 形如 `academic/academic-anthropologist.md`）。
   → 修复：递归同时收集「含 `AGENT.md` 的目录」与「带 frontmatter 的独立 `.md` 代理文件」（排除非代理文档与 `AGENT.md` 目录子树），无候选时干净报错 rc=1；`--json` 下错误走 stderr 保持机器契约。

2. **adapt_agent opencode 权限放大（安全）**：白名单工具遇 `permission` 字符串简写时保留全局简写（如 `allow`），等于给未列入白名单的工具放权。
   → 修复：始终物化逐工具权限，字符串简写丢弃并记入 note；白名单外一律 `deny`，与打包路径的合并行为一致。

3. **build_agent_index 文档声明未实现参数（文档-行为不一致）**：docstring 列出 `--incremental`，但 CLI 并无该参数。
   → 修复：删除该 usage 行；行唯一性说明改写为按 (source_repo, path) 识别，去除 incremental 表述。

4. **create_agent 工具名大小写（正确性）**：`--tools read,Edit` 未归一为小写，编辑类别名识别失败，样板 `permission: edit: deny` 未被移除，用户显式授权被静默拒绝。
   → 修复：`--tools` 解析即 `lower()`，与适配器的归一逻辑一致。

5. **reviewer 标尺计数漂移（文档）**：评审子代理写「6 项」，canonical 质量门槛实为 7 项。
   → 修复：改为 7 项。

6. **自包含发布门死分支（验证器）**：dev-only 路径检测分支因扫描集合不含 dev-only 标记而恒不可达，`tests/`、`build/`、`.github/` 之类引用无法被检出。
   → 修复：把 dev-only 标记并入扫描集合并复用；不改动其它规则，当前受检文档无误报。

## 验证
- 工作区回归测试全绿，本轮新增 4 例覆盖：递归 `AGENT.md` 候选树命中、扁平 `<division>/<name>.md` 候选命中（README 除外）、全局 `permission: allow` 不残留且未白名单工具 `deny`、`read,Edit` 归一为 `read, edit` 且无样板 deny。
- 发布门 `test_product_self_containment` 的 dev-only 分支补可达性回归测试（命令式 `python tests/...` 现被检出）。
- 成品自检与能力库 strict 保持全绿（未改验证器错误语义）。
- 冒烟：分类布局上游树被完整枚举；权限简写被丢弃并物化；工具大小写归一后样板 deny 正确移除。

## 范围边界（已确认，非本轮修复）
- `adapt_agent` 在 `tools` 为**已弃用的 bool-map** 且并存全局 `permission` 字符串简写时仍保留简写：盲目丢弃 `deny` 简写会反向放宽权限，故不改，随 bool-map 路径整体退役。
- `adapt_agent` 未实现 `package_agent` 的「`tools: [claude, opencode]` 支持客户端元数据」判定；当前上游与库内无此用法，仅打包器覆盖。属已知差异，非缺陷。

## 学习点
- **遍历布局要与真实目录结构对齐**：候选树常按分类分层，顶层扫描是隐蔽漏扫，应与校验器同样递归；递归时又必须超集覆盖既有可命中形态（此处为扁平 `.md`），否则修一个漏扫引入另一个。
- **字符串简写是权限放大的入口**：任何「全局 permission 简写 + 工具白名单」组合都必须物化为逐工具规则，否则白名单形同虚设。
- **文档声明的参数必须与 CLI 一致**：未实现参数会误导调用者，属契约缺陷。
- **归一化要覆盖别名识别路径**：大小写不归一会让显式授权被样板 deny 静默覆盖。
- **发布门自身也要有可达性**：恒不可达的检查等于没有检查；把 dev-only 标记并入扫描集合即可让分支真正生效。
- **把「已接受边界」写进记录**：明确不改的次要项（弃用输入、理论路径）应落档，避免下一轮审计重复列为新发现。
