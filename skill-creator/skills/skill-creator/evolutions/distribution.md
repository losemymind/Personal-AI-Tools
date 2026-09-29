# 成品结构、安装与命名决策

覆盖 2026-09-11—09-29；摘要保留当前决定与迁移边界。

<a id="schema"></a>
## frontmatter 瘦身（09-11）

用户要求技能保持客户端中立并减小内容。核心字段为 name/description/risk/category，可选 allowed-tools 表达权限；移除 tools（客户端标签）、tags、version、作者/日期/来源字段。创建元数据进入集中创建账本，版本由 Git 记账；`skill_create.py --records` 可追加作者、来源和创建方式，不传则仅创建技能。

目录匹配依靠 name/description/category；对比 metadata_complete 使用四个核心字段。旧 tools 白名单仅作适配兼容；上游索引和原始学习样本的 schema 保留。历史“七字段完整度”与 semver 参数检查已被替代。

<a id="packaging"></a>
## 四端打包（09-11）

`skill_package.py` 留在成品内，单技能经 frontmatter 适配、整树复制、逐端 post-check 后输出；支持 claude/opencode/codex/deepseek、重复或逗号分隔 client、可选 zip，排除缓存/VCS。输出不得位于源技能内，已存在普通文件的 --out 清晰失败，不泄漏 traceback。

<a id="permissions"></a>
## 白名单映射与前置验证（09-11）

- Claude：canonical 工具名，allowed-tools 输出逗号串。
- OpenCode：白名单映射为逐工具 permission，白名单 allow、其余 deny，既有显式条目优先；write/patch 归入 edit。与旧 tools 白名单取并集，不能保留会扩大权限的全局字符串简写。
- Codex/DeepSeek：通过基础 YAML/name/description 校验后透传。
- allowed-tools 缺席保持可选语义；dict、非字符串项、空表、客户端标签列表等畸形值拒绝。validator 复用打包器 canonicalizer，避免只有打包时才暴露错误。

验证依据包括四端打包、zip/缓存检查、显式权限优先、大小写/形状输入和真实库技能四端冒烟；历史新增 13、8、6 例分属不同批次，不能重复累加。

<a id="installation"></a>
## 安装分层（09-11）

单产物打包器随成品分发，仓库安装编排层负责跨产物选择、落点、staging、备份/回滚和缓存清理。创建器自身是 SKILL.md 技能形态，也走技能打包。

成品支持按 SKILL.md 的自安装流程定位→选端/作用域→放置→自检→清缓存→交付，不依赖仓库编排工具。技能自检仅在目标目录存在 SKILL.md 入口时运行，避免入口形态不匹配造成安装失败；已有回归。

<a id="gates"></a>
## 独立性与自包含（09-11）

成品为唯一源、可独立安装；入口仅 SKILL.md，开发用 AGENTS/INSTALL/测试留工作区。运行依赖以脚本位置自定位；维护文档、模板和模块导入均以本成品的资源与职责为范围。

成品外部目录复制后运行 strict/索引检查，开发测试再扫描全产品文档的自包含引用，补足 validator 只查 SKILL.md 的范围。09-29 压缩增加摘要链接与账本锚点检查，旧逐轮记录由映射索引追溯；同日进一步将维护记录收敛为本产品的决定、验证与限制。第三方学习样本保留真实来源，不改写历史原始证据。

<a id="naming"></a>
## 统一工具与子代理命名（09-29）

用户要求统一前缀，随后指定 utils 也改名。十个 CLI 为 skill_create/package/validate/compare/eval/optimize/scenario/benchmark/index_build/index_search，均以 skill_ 开头；共享模块为 skill_utils.py，_project_paths.py 保留。完整旧新映射见成品 `README.md`。

模块导入、帮助提示、文档、CI、安装检查均同步；参数、函数接口、报告与退出语义不变。旧入口不保留转发副本，外部调用需迁移；安装器仍识别旧包内的 validate_skills.py/search_index.py，防止漏掉自检。

迁移后十个 CLI 从无缓存的独立成品副本、无宿主工作目录启动通过；本工作区 250 项回归、strict 成品 1 / 技能库 7 与目录时效检查通过。此为压缩前的本产品验证快照。

同日用户补充要求子代理也采用 skill_ 前缀：agents/ 下 grader、reviewer、comparator、analyzer 四份指令迁为 skill_<角色>.md；工作流、角色间引用、基准工具注释、参考与测试同步，旧路径无副本。角色名与 grading.json/review.json/comparison.json 契约保留，外部提示词需按 `README.md` 的映射更新路径。此规则仅适用于本创建器的内置角色指令。
