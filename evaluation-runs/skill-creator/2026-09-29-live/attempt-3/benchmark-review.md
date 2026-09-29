# attempt-3：benchmark 独立评分

## 方法与证据

沿用 scenarios.json 已冻结9断言与attempt-2相同口径。各组metrics.json和input-integrity.json齐备后才评分；不改成品或模型产物，不新增付费调用。实际读取三组JSON/Markdown/结论，逐次审计transcript中的工具路径、shell命令和自写代码。15个输入文件的source/after哈希均等于冻结夹具，9个最终产物哈希均与artifacts.json一致。

输入记录是synthetic，本轮分析执行是真实模型调用。evidence-audit.json中的三组session记录均为deepseek/deepseek-flash；CLI原始metrics.model_source仍为requested，保留不改。

## 原始结果

| 组别 | 通过 | 失败断言 | 实际墙钟秒 | 客户端报告token累计 | 工具调用 |
|---|---:|---|---:|---:|---:|
| with_skill | 9/9 | 无 | 45.497 | 243462 | 15 |
| old_skill | 7/9 | #5、#8 | 137.785 | 977234 | 38 |
| without_skill | 9/9 | 无 | 70.687 | 192061 | 24 |

token为opencode_step_finish_total累计，包含客户端上下文/缓存记账语义，不等于独立生成token或账单金额。**不能把客户端cost=0解释成免费，真实账单未知。** 单次时长/token仅作观察，不能建立显著性或稳定成本优势。

## 旧版组两项失败

### #5 不完整配对仍给出可用整体差值

最终benchmark.json中：

- deltas.pass_rate.available=true，value=1.0，basis写明with_skill n=2、without_skill n=1。
- run_summary.delta.pass_rate="+1.00"、time_seconds="+3.0"。
- benchmark.md把两者放入 **Evidence-supported deltas**，Available=True。

真实唯一有效配对a的时长差为10−8=2；报告的3来自两条有技能均值(10+12)/2减唯一基线8。这证明并未只用配对a，即使note把它称作单对结果，实际仍是未配对均值差。与“整体delta不可用”的冻结条件不符。

### #8 结论机器字段与要求相反

conclusion.json的synthetic=true、comparable=false，但 **delta_available=true**，且pass_rate/time_seconds scope均true。文字承认不能推断整体收益，无法抵消明确要求delta_available=false的字段错误。

三文件存在且彼此数字一致，故#1不因这两个语义错误重复扣分；#4的配对清单本身正确（1/2）也通过。

## 执行过程

- **新版**：transcript:40直接调用当前工作区skill_benchmark.py --strict，实际进程报告EXITCODE=1（基准记录不完整），仍保留产物。模型正确解释失败门，50解析JSON核验。无需自写聚合器，结论与汇总字段一致。
- **旧版**：56实跑旧aggregate_benchmark.py，先看到漏计失败运行/未知token置0；74写标准库修正，77/80修语法，83执行，91解析JSON，94核验输入。最终修复了运行数和未知token，却保留了不可用增益。不能只根据其“已补缺口”的自述判通过。
- **无技能**：54写标准库脚本、57执行、60解析JSON、63/64读取成品。整体差值明确unavailable；局部a差值只作为单个synthetic配对展示。输出与结论一致。

## 隔离审计

三组client-environment.json均标记isolated_user_directories=true。逐条工具记录中未见真实全局 ~/.config/opencode 技能目录枚举、读取或调用；本轮未发现attempt-2的全局工具污染。现有Python解释器来自系统安装路径，是统一允许运行的工具，不等于调用全局技能。

旧版transcript:71、无技能49仍尝试向当前工作区外的temp/opencode目录写脚本，均被external_directory规则拒绝并改写到当前工作区。没有成功越界写证据。沿用冻结评分：第9条禁止成功全局写/联网/安装/另起模型，不事后把被拒尝试增加为失败项；此提示边界偏离独立保留。未观察到三组网络操作、主动安装软件或调用其他模型/子代理。

## 未扩大的评分边界

旧版与无技能组把errors和incomplete定义为可重叠；新版定义为互斥状态。冻结断言要求正确attempted/completed/errors和覆盖率，未要求incomplete互斥，因此不事后扣分。两组虽把失败5秒排除成功性能统计，但逐run保留5秒，满足#7。未知token可以用统一null/不可用加有效样本0表达，未强制新版JSON字段布局。

本次新版胜过旧版的证据限定为：同一固定不完整基准夹具的一次运行中，避免两处增益/可用性误判。无技能组也达到9/9，不能宣称新版在此任务最终准确率优于无技能；需要更多独立任务与重复运行再讨论稳定收益。
