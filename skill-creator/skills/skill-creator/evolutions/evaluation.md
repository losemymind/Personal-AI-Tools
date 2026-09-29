# 评测：契约、真机证据与可信度边界

覆盖 2026-09-03—09-29；按最终有效语义压缩早期反复修复。当前字段细节见 `references/benchmark-schema.md`。

<a id="origins"></a>
## 工具来源与职责

09-03 移植 [Anthropic skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator) 的评测、描述优化、汇总与解析工具；原取用插件副本与官方同 blob，记录的 sparse-checkout 提交为 0120fb8。本地/上游静态分 0.90/0.63 受 schema 影响，采纳依据是此前缺少量化基准与优化循环。

触发评测回答“是否调用”；有/无技能场景双跑回答“产出是否改善”。保留 mean/stddev、delta 和模型语义评分，客户端按能力接入。09-10 删除重复的 run_trigger_tests 入口，其启发式并入共享模块；补齐 `skill_scenario.py` 执行、评分、汇总闭环。

<a id="schema"></a>
## 输入与报告契约（09-10）

- eval 项的权威键是 `query`，兼容旧 `prompt`，二者并存时 query 优先；非空字符串与布尔 `should_trigger` 必须验证。模板、读取器和报告保持一致。
- 畸形 JSON、错误路径、空 description、非有限参数须清晰报错。manual 改写提示写 stderr，JSON 输出保持干净。
- `total` 只计已评分查询，`passed + failed == total`；运行错误单列。CLI 的 trigger_rate 与 heuristic 的 triggered 经统一阈值归一，避免形状漂移。

<a id="heuristic"></a>
## 离线代理指标（09-10—09-11）

`skill_utils.classify` 以去重的拉丁词与中文双字 token 交集判定，修复连续中文不匹配、重复 token 虚增命中。此指标仅代表措辞覆盖；共用 PR/改动、性能/优化等词会产生固有假阳性。09-11 决定保留确定性实现，未向触发启发式引入同义词模型。

09-29 的中英扩展仅用于上游索引检索，不能理解为触发评测改用语义模型。真实调用应看 CLI 派发证据。

<a id="execution"></a>
## 执行与隔离（09-10）

真机曾在被测仓库追加测试、生成评测目录并派生孤儿进程，因此：

- CLI 每条查询使用独立临时工作区，按客户端发现路径安装；改写器也隔离。失败清理半成品，保留开关输出实际路径。
- `--concurrency` 默认 1；有界并发保留输入顺序，多次运行计算触发率。某轮运行错误使该查询转 error，不能泄漏部分成功率。
- 共享运行器超时终止进程树并保留部分输出。场景执行失败、缺 CLI 或超时仍落盘 transcript、metrics、timing；Windows 命令切分保留反斜杠，拒绝空 argv。
- `--model` 显式透传；一处不存在的默认 provider 曾造成所有运行失败，指定模型恢复，未改全局配置。

<a id="real-evidence"></a>
## 真机证据及局限（09-10）

历史环境为 opencode + deepseek/deepseek-v4-flash。观察到“把这个工作流做成一个技能”确有 `tool: skill`、`input.name: skill-creator` 派发。相同正例也曾直接回答、不派发，说明存在模型波动。旧全文子串检测把列目录输出误判为触发，已改为读取 opencode 的 tool / tool_use 结构化事件；Claude 仍为 best-effort 近似信号。

超时前若已有本技能派发证据，触发事实保留；无证据则记 run_error。该分支用模拟 TimeoutExpired 定向回归，不能仅靠真机偶现证明。

旧批次记录曾报告 recall 约 0.25、precision 1.0，并记录串行批次耗时 927.5 秒、超时及用户中止；查询数/调用数和部分超时叙述有不一致，不能合成为可靠的完整基准。保留的结论是“链路打通、真实触发可观测、完整效果尚未确认”。09-29 使用离线样本与模拟客户端，未重新测真实模型触发率。

<a id="benchmark"></a>
## 基准汇总不变量（09-10 多轮修复）

- metrics.json、timing.json 位于 run 根；grader 从 outputs 的父目录读取。汇总器在 execution_metrics 缺字段时直接回退读 metrics，避免依赖模型搬运数据。
- 工具调用解析 JSON 事件；token 数不能用字符数代替；运行次数取实际观测。pass_rate 缺失时由 passed/total 推导。
- primary/baseline 各自先按精确名→别名解析，再排序；delta 不依赖字典序。两侧必须各有有效 run，否则 delta 为 null 并注明原因。
- 容忍非标准目录名、混合标量 eval_id、缺字段、字符串数值；拒绝或净化非有限值、不可哈希 ID，输出严格 JSON。notes 仅接受数组，错误目录与输出路径清晰失败。

<a id="optimization"></a>
## 描述优化选优（09-09—09-29）

参考 [antongulin/opencode-skill-creator](https://github.com/antongulin/opencode-skill-creator) 的高分先例和假阴性/假阳性/运行错误分类。先例只取本次迭代历史，无常驻 gold-standard 文件；未采纳其 npm 插件注册与自动更新机制。

原循环 train/test 60/40 的 test 反复参与选优，09-29 明确为 train/validation。选优看有效覆盖和通过率；最后一个候选也须评分；有限 holdout、空集和单样本边界单独处理。运行错误先修运行环境，不用于训练描述。

`--eval-mode heuristic|cli` 控制开发评分，默认 heuristic；`--final-eval-set` 指定与开发集不重叠的独立查询，选优后只跑选定描述一次，结果不反馈改写。最终模式默认 cli；重复开发查询与交叉重叠均拒绝。CLI 临时安装副本实际写入候选 description，源技能不变。

<a id="confidence"></a>
## 09-29 可信度修正与验证

最小复现发现“全部运行错误仍 precision/recall=1.0”及循环测试泄漏；新增回归先有 15 项失败，最终补成 21 个行为用例。修正：attempted/coverage；无分母指标 null（文本 N/A）；`--fail-on-error` / `--fail-on-mismatch` 可组成失败门，先落报告再退出。模型、客户端、重复次数与阈值进入报告。

优化报告 schema_version=2；旧 test_* 是 validation 别名。confirmation 区分 not_run / proxy_only / dispatch_passed / approximate_passed / failed / error；无最终集为 not_run，改写/执行错误或最终失败退出 1。最终结果一旦用于再改写，就需要新的未见查询集。

上游对照：[Anthropic run_loop](https://github.com/anthropics/skills/blob/main/skills/skill-creator/scripts/run_loop.py)（09-29 查阅）。该轮回归 239 项通过；命名迁移后 250 项通过。它们证明实现契约，未证明当前真实触发率提高。

<a id="evidence-integrity"></a>
## 09-29 第二轮：产物、配对与结构化信号

复现：场景在临时 cwd 生成 CSV 后仅保留回复、真文件被清理；两组无共同场景仍算出 +1.00；Claude 回复“不要使用 skill-creator”仍判触发；缺成本记 0、模型写占位符。此次按用户批准修复，并启用子代理实现及独立交叉审核。

参考：[Anthropic 结构化触发实现](https://github.com/anthropics/skills/blob/main/skills/skill-creator/scripts/run_eval.py)、[antongulin 配对检查](https://github.com/antongulin/opencode-skill-creator#review-workflow-guard-strict-by-default)。沿用既有 Apache-2.0 来源登记；本轮借鉴检测与配对思路，独立适配本地 Python 工具链，没有整包替换上游。

- 场景新增 input-dir/output-dir，清理前收集真实文件和哈希清单，失败/超时也留证据；拒绝非空 run 目录，防旧评分串入；输入、配置、缓存和符号链接不当产物。
- Claude 用结构化 Skill/Read，OpenCode 用 skill 派发；记录 skill_dispatch/target_read，不认名称提及。协议缺失或结构化错误单列 run_error；临时 cwd 仅隔离文件，不是权限沙箱。
- benchmark schema v2 保留全部尝试，展示 completed/error/incomplete、覆盖率；按 eval_id+run_number 完整配对，已知运行条件不一致不算增益。缺失指标为 null，真实 0 保留，每项统计含 n；成本包含观测到的失败尝试。只覆盖已发现的 run 目录，不证明计划任务全部启动。
- 模型、模型集合、请求模型与指标来源均留痕；不能以请求值覆盖实际多模型结果。--strict 先输出报告，再对不完整数据失败退出；默认仍支持查看部分结果。
- 优化最终确认中 Claude 改为 structured_passed；旧 approximate_passed 仅是历史检测结果。这替代此前全文匹配的近似边界；结构化信号不等于任务完成。

独立审核找出并复现：rc=0 但流内报错、多模型回填误标、嵌套缓存名输出被跳过；均补回归修复。测试基于假客户端和流事件，没有付费模型或当前真机准确率结论。完整发布结果记录在开发交接中；输出保留与指标真实性是本轮验收重点。

<a id="live-2026-09-29"></a>
## 优化后真实测评（09-29）

- 用户要求真机验证，使用 OpenCode 1.18.30 + deepseek/deepseek-flash；保留原始事件、产物、哈希、输入完整性、独立评分与客户端会话模型旁证。单模型小样本，非盲评，账单未知，客户端 cost=0 不代表免费。
- 新冻结触发集 12 条：6 正例均派发、5 有效负例未误触发、1 负例 120 秒超时无结论；有效覆盖 11/12。三个正例派发后超时只证明触发，不证明任务完成。未据此调整 description，不能声称全部通过。
- 独立审核发现超时负例 Q12 虽未派发，却通过普通 read 读取了目标 SKILL.md；当前 OpenCode 只统计 skill 派发，存在读取信号覆盖盲区。不可解释为完全未加载，precision/recall 仅为派发口径；本轮不在看过结果后改判据，后续需以新协议重评。
- 两个真实模型任务比较当前成品、Git f68cfc8 旧版、无目标技能；基准分析输入是假记录，仅分析行为为真机测量。最终隔离批次断言合计 16/16、14/16、15/16。旧版把不完整配对的均值差称为整体增益，当前版拒绝；无技能组改名时额外改变 CRLF，文字语义未变。
- 首轮 XDG 隔离仍允许 shell 找到全局旧验证器，无技能基线受污染；原始记录保留。统一增加每运行独立的子进程用户目录后，三组全部重跑，审计未再发现全局目标工具污染。技能权限排除成品 examples 的递归发现干扰；临时目录与权限配置不是操作系统沙箱。
- 当前/旧版改名耗时 116.146/115.979 秒；两组只用了随包验证器，未加载正文，不能证明入口压缩提速。基准分析耗时 45.497/137.785 秒为单次观察；首轮旧版曾自行修正而通过，结果存在波动，不外推稳定增益。
- 运行前冻结版本/查询/夹具，运行后成品无漂移；未为本次结果修改产品逻辑或描述。保留失败与重跑的决定先后，后续调参须另备未见查询集。来源为本地真机事件与独立产物审核；没有新增上游代码采纳。
