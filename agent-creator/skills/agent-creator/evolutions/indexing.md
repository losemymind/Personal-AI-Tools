# 索引与检索

<a id="sources"></a>
## 三源范围与数据快照

本次审计使用随成品分发的 SQLite 索引，三源共 568 条：

| 别名 | 来源 | 条目 | 扫描形态 |
|---|---|---:|---|
| agency | [msitarzewski/agency-agents](https://github.com/msitarzewski/agency-agents) | 258 | 顶层 division 下 Markdown |
| ccgs | [Donchitos/Claude-Code-Game-Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) | 49 | `.claude/agents/` 下 Markdown |
| agency-zh | [jnMetaCode/agency-agents-zh](https://github.com/jnMetaCode/agency-agents-zh) | 261 | 中文 division 布局 |

这是本地索引范围和历史快照，不代表上游最新总量。09-10 复核已提交数据库：损坏块标量描述 0、null name/path 0、FTS 行数与主表均 568。09-29 命名整理未重建或修改数据库。

<a id="build"></a>
## 09-10—09-11：构建不能静默毁掉旧数据

- BOM 读取用 utf-8-sig；description 的 `>`/`|` 消费缩进续行并按折叠/字面规则拼接，避免把标量标记当描述存库。
- `--no-dl` 真正扫描当前 cwd；与 `--from-extracted` 一样必须指定单一 source，防止同一目录套三种源规则重复索引；本地目录先检查存在性。
- `--keep` 纳入清理条件，兑现保留下载内容的承诺。下载/解包错误清晰退出，任一选定源 0 命中就中止、不写库，防止部分索引覆盖完整库。
- 09-11 删除文档里未实现的 `--incremental` 参数；条目以 `(source_repo, path)` 识别，不把去重说明当成增量更新能力。

索引完整性以实际数据库和运行期探针确认，不能只看构建脚本已修改。对应审计记录统计始终为 3 源 568 条。

<a id="retrieval"></a>
## 09-10：字面查询与参数边界

FTS5 查询将各词作字面引用，避免 AND、冒号、星号、括号等被当表达式导致 OperationalError；limit 负值清晰拒绝，不能让 SQLite 的 LIMIT -1 变成隐式全量。

检索 0 命中只说明当前索引和查询没有候选，不能证明外部不存在可用代理；code-simplifier 即为用户指定而三源未收录的来源。
