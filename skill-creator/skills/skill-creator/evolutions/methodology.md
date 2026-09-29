# 方法论：采纳来源与设计取舍

覆盖 2026-09-03—09-17；2026-09-29 合并。脚本使用当前名称，分数与实验描述均保留原日期语境。

<a id="writing"></a>
## 写作纪律（09-03）

来源：[obra/superpowers 的 writing-skills](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md)。用户选择完整吸收 A—G 七项，落入 `references/skill-writing-guide.md` 与入口质量清单：

- 先在无技能环境复现失败、记录借口，再写针对失败的最小指导，带技能重测。
- 措辞匹配失败类型：违规用禁止与借口表；输出形状用正面配方；漏项用 REQUIRED 槽；条件行为用可观察谓词。上游报告过禁止清单对形状错误的反效果，本地保留为写作依据，未重新做该实验。
- 纪律型技能补漏洞变体、红旗和借口表；措辞微测用 fresh context、无指导对照、每变体至少 5 次，观察方差。
- description 以触发场景为主，可加一句能力定位以兼容目录展示，禁止写步骤摘要。去除强制加载其他技能的 `@` 写法。
- 机械约束优先交给程序；Technique / Pattern / Reference 按各自失败类型评估。

当时 strict 与回归通过。原“人工逐条核验”评审要求已由 09-10 的 reviewer 闭环替代；业务授权仍由用户决定。

<a id="description"></a>
## description 与渐进披露（09-09）

来源：[Anthropic skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) 与 [antongulin 移植版](https://github.com/antongulin/opencode-skill-creator)。采纳 description 自足、单行、≤1024 字符、禁尖括号占位与流程摘要；保留正文“何时使用”节作为加载后范围确认。长度是硬检查，部分写作约束在验证器中为 advisory，不能混称全部已机械强制。

references 从 SKILL.md 一层深按需读取；超过 100 行加目录，超大文件提供检索词；去除未经客户端支持的 include 伪语法。兄弟 references 裸文件名互链已有验证检查，文件路径与章节模式统一，避免文档和工具各定一套规则。

<a id="orchestration"></a>
## 语义评测编排（09-04）

来源：Anthropic 的 grader / comparator / analyzer 指令与编排。确定性脚本负责运行、统计、校验；模型负责语义断言、隐含声明核验、匿名 A/B 比较和恒过/恒败/flaky 模式分析。保留 grading / comparison / benchmark 数据契约，分析笔记由 `skill_benchmark.py --notes` 合并。

子代理指令按需加载；客户端无派发能力时，由主持会话按同一指令内联完成并标明执行方式。盲测随机标签、隐藏来源；grader 同时审视断言质量，避免弱断言产生虚假高分。

<a id="agent-review"></a>
## AI 评审闭环（09-10）

本地决策：生成与评审角色分离，`agents/skill_reviewer.md` 输出 `review.json`，含 `verdict: pass|revise`、可执行 `issues[]` 及修复核验。生成者据反馈修改；通过或达到最大迭代数（默认 5）即停，不能把达到上限视为通过。先过客观校验，再进入语义评审。

阶段 6 产出评审与阶段 7 查询集审阅均交 reviewer；阶段 8 的 VERIFICATION.md 为可选留痕。此决定替代旧人审/UI 闭环，保留业务定义、授权和高风险决策的人工边界。原记录版本为 0.7.0，当前版本以 Git 历史为准。

<a id="baseline"></a>
## 行为基线与发布纪律（09-09）

参考 Anthropic 基线双跑与 antongulin 安装健壮性。基线不失败时先判断技能是否必要；带技能后须消除已观察的失败。evals 随技能保存，开发/最终查询隔离，secret 扫描与隔离安装组成发布验证。分支、PR、tag 的操作仍服从当前仓库规则与已有用户授权，历史流程记录不另增授权。

<a id="coevoskills"></a>
## CoEvoSkills 对比与未采纳项（09-17）

来源：[Zhang-Henry/CoEvoSkills 的 meta skill-creator](https://github.com/Zhang-Henry/CoEvoSkills/tree/main/meta_skills/skill-creator)，Apache-2.0，18 文件；与本地均衍生自 Anthropic 工具链。当时结构筛查本地 0.98、上游 0.55，差值受本地 schema/章节要求影响，不能据此证明任务效果胜出。

决定：加入索引与方法论参考，保留本地实现。上游增量为自包含 HTML 评审页、feedback.json 回流、逐查询显示开发/测试的 HTML 报告；旧分析同时发现这些工具缺少文档入口。候选功能仍未采纳，先明确报告的读者与其在 reviewer 流程中的位置。后续若实现，必须区分 validation 与独立最终集。

上游“任何步骤均不等用户反馈”的立场未采纳。已有授权可继续执行；实际业务授权边界仍保留。

<a id="task-routing"></a>
## 09-29 第二轮：按任务加载

入口原有 547 行、26,671 字符，将创建、评测、描述优化和安装一起加载；“元技能正文变长不影响加载性能”的表述不成立。参考既有 Anthropic 渐进披露原则，入口保留范围、核心约束、局部修改短流程和资源路由；场景评测、触发优化、安装细节分成三份 references，由 SKILL.md 直接访问。

局部改名/引用修复用相关校验，实质行为变更才补行为基线；写作参考同步限定适用范围。已有授权和明确安装选择直接沿用；原版固定阶段编号改为任务路径，资料不再引用失效阶段。此次用户明确批准方法论及拆分；自包含校验继续覆盖全部当前文档。
