# 上游索引：来源、数据契约与检索

覆盖 2026-09-10—09-29。下表为 09-23 随包快照（7 源 2227 条），不是远端实时数量；本次压缩未联网刷新。

<a id="sources"></a>
## 来源与采纳理由

| 别名 / 来源 | 条目 | 布局与取数 | 许可记录 |
|---|---:|---|---|
| aas / [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills) | 2115 | 官方 skills_index.json + 结构扫描 | MIT |
| addy / [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills) | 25 | skills 下单层扫描 | MIT |
| anthropics / [anthropics/skills](https://github.com/anthropics/skills) | 19 | skills 下单层扫描，09-10 加入 | 多数 Apache-2.0，文档类 source-available |
| composiohq / [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) | 28 | 仓库根扫描，09-10 加入 | 仓库未声明，按具体条目核对 |
| coevoskills / [Zhang-Henry/CoEvoSkills](https://github.com/Zhang-Henry/CoEvoSkills) | 1 | meta_skills 子树，09-17 加入 | Apache-2.0 |
| mattpocock / [mattpocock/skills](https://github.com/mattpocock/skills) | 38 | skills/分类/技能 两层，09-23 加入 | MIT |
| karpathy / [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) | 1 | skills/karpathy-guidelines，09-23 加入 | 无独立 LICENSE，SKILL.md 声明 MIT |

同名不同源按 source_repo 区分，保留分发副本与原始源。计数里程碑：4 源 2187 → CoEvo +1 为 2188 → mattpocock +38 为 2226 → karpathy +1 为 2227。karpathy 原先只能经 aas 副本命中，收录原始源修复了来源过滤盲区。

CoEvo 整仓约 600MB、技能子树 18 文件约 200KB，采用父 contents 定位 tree SHA→scoped recursive tree→raw 文件，落成最小 checkout 复用扫描器；分块读取与重试处理网络中断/截断。mattpocock 整仓约 1.8MB，普通 tarball 足够，两层扫描由 skills_nested 声明，保留完整相对路径，category 缺席用父目录兜底，显式字段优先。karpathy 约 20KB，复用单层扫描。

<a id="integrity"></a>
## 数据完整性（09-10）

曾把 YAML 块标量描述存成字面 `>` 并丢字段，修复为共享 PyYAML 解析（惰性导入、BOM 支持），无依赖时最小解析器支持块标量/行内列表；当时重建 anthropics 三条损坏记录，总数不变。上游确实缺 category/risk 时保留 NULL，不造数据。

tags/tools 等上游索引字段继续透传，与本地技能 frontmatter 瘦身分开。结构统计复用 path→skills/id 回退；仓库根扫描无前导斜杠；--no-dl 以当前目录为根。来源元数据从 SOURCES 派生，增量计数取全库，Windows 临时清理 best-effort 不污染已成功构建。

<a id="offline"></a>
## 离线与部分同步（09-11）

下载/解包/限流/截断统一为 SourceUnavailable。已有 DB 时保留不可达源，对可达源按 source_repo/path 增量；全部不可达仍保留 DB 并退出 0。既无网络又无可用 DB 才失败，不能用全量重建静默删掉离线源。

<a id="retrieval"></a>
## 检索修正（09-10、09-29）

FTS 查询逐词转义作字面匹配，特殊标点、CJK 混合与负 limit 有回归。09-29 实测 code review 有 53 条但精确名称排第 12、落在默认前 10 外；“代码审查”0 命中。按名称归一精确命中→[FTS5 BM25](https://www.sqlite.org/fts5.html#the_bm25_function) 字段权重（name/description/category/tags = 8/1/1/2）→稳定名称/来源/路径排序后，两查询首条均为 mattpocock 的 code-review。

常见中文词离线扩展为英文，原文 LIKE 与英文 FTS 取并集；保留英文限定词与过滤条件，含未知中文限定词时不做部分翻译。有限词表不等于通用翻译，0 命中后仍需补关键词检索。

<a id="status"></a>
## 逐源状态（09-29）

构建器 schema v5 的 source_status 记录 last_success、last_attempt、status、snapshot_sha256、error。失败或空扫描保留上次行/时间/哈希；局部更新不刷新其他源。无数据但同步失败的源也出现在 stats。

旧 DB 没有逐源记录时为 unknown，不从全局 built_at 补造；SHA-256 仅标识已索引字段，不是远端 Git SHA，也不覆盖未索引内容。随包仍是 09-23 快照，逐源状态在后续实际同步时形成；相关离线/恢复测试已通过。

<a id="samples"></a>
## 学习样本快照（09-11）

从 aas 的 skills/loki-mode（MIT）重新同步，references 14→15（新增 detailed-guide），精选快照 91 文件约 0.88MB。保留技能内容，排除 benchmarks、demo、大图与上游 CI，修正原文档误写的 16；避免上游生成产物膨胀本地样本。

<a id="limits"></a>
## 未解决与有意不扩展

稀疏源父目录定位仍用 contents API，超大目录存在返回条目上限；接入此类源前需改定位方式。更深目录扫描仍为候选；源级 branch 的 main/master 差异已在 09-29 固定提交下载时明确。原始源入索引的事实已在本摘要保留，不自动把索引收录等同于能力库的使用授权或质量证明。

<a id="pinned-revision"></a>
## 09-29 第二轮：固定来源提交

原稀疏流程按分支先枚举、再逐文件下载，期间分支移动可能混合版本；共享临时目录还可能让旧文件进入新快照。v6 每源先解析完整 commit SHA，contents/raw/archive 都使用该 SHA；每次构建使用独立临时目录。

来源状态新增 upstream_commit/source_ref/fetch_mode，与索引字段 snapshot_sha256 分开。失败保留上一成功 SHA；旧 DB 缺字段显示 unknown。本地 --from-extracted/--no-dl 统一标 local、提交 null，不推断远程或祖先 Git 状态；本地更新成功清空旧远程关联。

行为验证覆盖分支固定、archive与元数据一致、非法提交响应、离线保留、本地切换、临时目录不复用；独立审核确认方案与实现。本轮没有重抓随包索引，现有 7 源 2227 条快照保持原样。单源日常命令明确加 --incremental，完整单源重建仍会替换成单源库。
