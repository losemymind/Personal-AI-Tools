# 字段、权限与分发

<a id="adaptation"></a>
## 09-09：从适配逻辑到可调用工具

来源为外部 `personal-workflow` 的 `tools/scripts/agent_format.py`。原是安装/更新程序 import 的纯适配模块；本成品当时仅有文档承诺和不存在的宿主安装器说明。移植为 `agent_adapt.py` CLI：输入代理文件/目录、选择 client、stdout 或 out，post-check 失败则退出 1、不输出无效结果。原记录未单列该来源许可，不能补造授权结论。

保留转换规则：OpenCode 将工具白名单转 permission，显式权限优先，write/patch 折叠到 edit；Claude 工具名映射为逗号串，无法映射的工具记 note，全无映射则拒绝，model 归为支持的 alias 或移除。Codex/DeepSeek 保留文本形态并作 YAML 检查，不据此声称已有原生代理 schema。

**已修正的旧承诺**：所谓“逐字节原样”不准确；UTF-8 BOM 去除与文本换行翻译可能改变字节。09-10 已收敛为文本透传描述。初次新增适配阶段记录 16 项回归。

<a id="permissions"></a>
## 09-11—09-12：权限不放大与保留差异

曾复现真实工具白名单与 `permission: allow` 并存时，适配器丢弃白名单而保留全局放权。09-11 先在新打包器修复，之后独立审计也修复适配器：丢弃冲突的字符串简写并记 note，白名单物化为逐工具 allow/deny，显式权限条目优先。**“只修打包器、适配器仍有同类缺陷”的中间结论已被替代。**

有意保留两点：

- 已弃用 tools bool-map 与全局 permission 简写组合仍沿历史语义；贸然丢弃 deny 可能反向放权，待 bool-map 路径整体退役时处理。
- `tools: [claude, opencode, ...]` 客户端标签辨识仅打包器覆盖，适配器未实现；当时上游/库内无此输入，作为已知差异记录。

09-12 按用户提供的 UEGameStudio `qa/security-engineer.md` 示例及 academic 代理现有用法，将脚手架升级为 `"*": deny` 加 13 键显式矩阵，由真实白名单派生，别名折叠到 edit。code-quality 两代理同步补矩阵。缺默认拒绝仅 advisory；OpenCode 适配还可补未声明工具的 deny。历史冒烟覆盖只读/编辑白名单、大小写、OpenCode/Claude 适配，不证明所有客户端权限模型等价。

<a id="metadata"></a>
## 09-11—09-12：分清入口与代理元数据

| 对象 | 有效决定与替代关系 |
|---|---|
| 创建器 SKILL.md | 09-11 移除 tools/source/date_added/author/tags/version，仅留 name/description/category/risk；本次先不改代理规则 |
| 产出的 AGENT.md | 随后移除 tools_clients/version/tags，来源/作者/日期进创建记录台账；保留 mode/maturity/tools/permission 等运行字段。因此早期导入时要求 version/tags 等字段已过时 |
| 记录生成 | `agent_create.py --records` 配合 author/source/source-repo/method 追加创建记录；不传 records 不写台账。版本依 Git，分类由目录承载，上游索引来源字段不受此瘦身影响 |
| color | 09-12 纳入可选规范字段；脚手架创建时总有 color，默认 `#DC2626`，hex 必须带引号。缺省代理仍合法；code-reviewer 用红色、code-simplifier 用 `#2563EB`，academic 保留既有色 |

脚手架已移除 version 参数与相应校验；旧导入记录的字段清单不能恢复成当前要求。颜色字段由验证器、生成器、模板和说明同步约束，避免“适配器已接受、规范未定义”的漂移。

<a id="packaging"></a>
## 09-11：整目录多端打包

`agent_package.py` 补齐单文件适配器不负责的资源复制、重复/逗号 client、多端 post-check 与 zip。输入 AGENT.md 或含该文件的目录；整树复制时排除缓存/VCS，单文件输入只打包该文件；输出 `<out>/<client>/<name>/AGENT.md`，name 优先合法 frontmatter 值，否则回退目录/文件名。

复用本地适配器常量和 schema 检查，避免规则漂移；每端先验证再写该端结果。out 位于源目录内部、指向文件、目录缺入口等情况拒绝；退出码 0 为全成功、1 为某端失败、2 为参数错误，不暗示多端失败会自动撤回其它已成功端。

当时新增 18 项回归达 86 项；anthropologist/code-reviewer 四端加 zip 冒烟通过。证据是产物/post-check 成功，不等于四端真实加载实测。

<a id="installation"></a>
## 09-11：安装分层与自安装

成品内工具负责代理打包；客户端检测、安装落点、staging、放置和回滚属于宿主编排，不成为成品依赖。此前“只有复制、无安装编排”的架构描述是早期状态。

LLM 自安装采用文档流程：定位成品与目标作用域、整体复制到客户端技能目录、索引和脚手架往返自检、清缓存、交付；无需引入安装脚本。隔离复制到仓库外后覆盖索引与生成→校验往返。

**对象识别**：agent-creator 本体入口为 SKILL.md；捆绑的 agent_validate 只检查生成的代理定义，不能拿来检查创建器自身目录。安装应按入口类型选择适用检查。客户端代理落点与支持范围随客户端变化，历史落点不作为本摘要的执行指令。

<a id="naming"></a>
## 09-29：工具和角色命名

公开工具采用 agent_ 前缀，索引为 agent_index_build / agent_index_search；安全模块为 agent_security，定位模块保留 _project_paths，角色为 agent_reviewer.md。当前入口与职责见 [产品说明](../README.md)。同步导入、CLI 提示、模板、测试和文档，不保留旧入口转发壳。

七个 CLI 在无关 cwd 执行 help、隔离后的索引读取与生成→strict→打包/zip 均通过，工作区 122 项回归通过。函数签名、输出契约和索引数据库不变；本次不新增真实任务质量证据。
