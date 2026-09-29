# skill-creator 真实测评（2026-09-29）

## 结论

真实运行 OpenCode **1.18.30**，请求模型为 **deepseek/deepseek-flash**；24 个正式客户端运行的本地会话元数据均记录相同 provider/model，另有 1 次连通探测。这些是客户端记录，不是对供应商底层模型版本的独立证明。

- **触发**：12 条新查询中 11 条可判定，全部符合标签；1 条运行超时，质量门未全通过。6 条正例均派发目标技能，5 条有效负例均未误触发。
- **任务**：隔离重跑的两个任务、三种配置均完成并保留实际文件。当前版通过 16/16 条断言，HEAD 旧版 14/16，无目标技能组 15/16。
- **实际改善证据**：不完整基准记录分析中，当前版正确拒绝整体增益；旧版仍将不可比样本的通过率差称为增益。
- **边界**：单模型、每任务每配置 1 次有效对照，独立评分但未做盲评。不能据此宣称普遍质量提升或稳定提速；未覆盖完整创建、安装、多客户端与长期使用。

## 触发结果

评审者仅依据当前触发范围设计并冻结 [12 条查询](queries.json)，未读取旧 evals。结果观察后没有调整查询、标签或 description。本轮没有执行描述选优，查询集不能在后续调参后继续充当未见最终集。

| 指标 | 结果 |
|---|---:|
| 尝试 / 有效 | 12 / 11 |
| 有效覆盖率 | 91.7% |
| 真阳 / 真阴 / 假阳 / 假阴 | 6 / 5 / 0 / 0 |
| 运行错误 | 1 |
| 有效样本上的 precision / recall | 100% / 100% |

Q2、Q5、Q6 在成功派发后超时：仅判定触发，**不代表任务完成**。Q12 是带 `--skill-dir` 关键词的普通应用开发负例；缺少应用文件时，模型持续查找目录，120 秒内没有派发证据也未结束，因此记运行错误，没有把它算成正确负例。触发集主要测试路由，部分请求未附业务输入，不适合作为任务完成基准。

**信号覆盖发现**：Q12 实际用普通 `read` 读取了临时目标 SKILL.md（tool_use_id：`call_01_rljZBi9dhGk2ijlF0Zxl4309`）。当前 OpenCode 检测只识别 `skill` 派发，未计这种目标文件访问；不能声称 Q12 完全未加载/未读取技能，也不能把上述 precision/recall 推广到所有加载行为。本轮保留冻结判据；若后续补充读取检测，应以新协议重评并保留旧口径。

证据：[完整结果](attempt-2/trigger/evaluation.json)、[逐请求原始事件](attempt-2/trigger/raw/)、[独立触发审核](attempt-2/trigger-review.md)。失败门的等价判定为 `errors > 0`，本轮不能宣称全部触发测试通过。

## 任务对照

输入与断言在执行前冻结于 [scenarios.json](scenarios.json)。当前版为运行前工作树；旧版为 **f68cfc8** 的成品，Git 快照解包在仓库外临时目录，未建立第二份开发源。无目标技能组仍有 OpenCode 自带 `customize-opencode`，所以这里的“无技能”仅表示没有安装目标 skill-creator。

| 场景 / 配置 | 通过断言 | 客户端耗时（秒） | 客户端累计 tokens | 工具调用 |
|---|---:|---:|---:|---:|
| 改名 / 当前 | 7/7 | 116.146 | 516,532 | 27 |
| 改名 / 旧版 | 7/7 | 115.979 | 576,870 | 29 |
| 改名 / 无目标技能 | 6/7 | 93.465 | 273,196 | 25 |
| 基准分析 / 当前 | 9/9 | 45.497 | 243,462 | 15 |
| 基准分析 / 旧版 | 7/9 | 137.785 | 977,234 | 38 |
| 基准分析 / 无目标技能 | 9/9 | 70.687 | 192,061 | 24 |

tokens 来自真实 `step_finish.tokens.total` 之和，包含各轮重复上下文与缓存，不是唯一文本的 token 数；费用未知，不能将自定义 provider 的 `cost=0` 解释为免费。耗时不包含安装副本等外层准备；各组相同上限 240 秒、24 个模型步骤，最多同时执行 2 个场景。

### 改名任务

要求复制完整技能、只改资源路径、保持正文/frontmatter/资源及输入不变，并真实执行校验。当前和旧版均满足断言。无目标技能组额外将 SKILL.md 的 38 处和 README.md 的 7 处 CRLF 改为 LF，文字语义相同，但违反冻结的“仅修改必要路径”约束。

两有技能组都使用了随包验证器，没有加载目标 SKILL.md 正文；这个场景不能证明正文压缩收益。当前组最终回复将 10 项自检说成 11 项，独立审核已记录；不追加冻结断言外的扣分。

证据：[改名审核](attempt-3/iteration-1/eval-rename/independent-review.md)，各配置 run-1 包含 transcript、真实 outputs、artifacts 哈希清单、input-integrity 与 grading。

### 不完整基准分析

输入是**明确标注 synthetic 的固定记录**：共 4 次尝试，一侧缺评分且退出失败，只有 1/2 有效配对，tokens 均未知。真实被测对象是模型分析这些文件的行为；输入中的 5/8/10/12 秒不是下游任务实测。

当前版及无目标技能组正确保留失败、未知成本、配对缺口并拒绝整体增益。旧版输出 `delta_available=true`，将 2 次有效评分对 1 次有效评分的均值差 `+1.00` 当成有证据的整体增益；相关两条断言失败。原始数据与错误结论均保留。

证据：[基准任务审核](attempt-3/benchmark-review.md)、[当前对旧版聚合](attempt-3/current-vs-old.md)、[当前对无目标技能聚合](attempt-3/current-vs-without.md)。聚合器按场景通过率等权取均值，与上表直接相加的断言计数口径不同。

## 失败批次、隔离与可复核性

1. 首次启动检查把 Windows `ADMINI~1` 与 `Administrator` 的相同路径当成不同目录，模型调用前失败。已规范化路径并保留 [preflight 记录](trigger/preflight-failure.json)；没有将它算进触发准确率。
2. attempt-2 使用独立 XDG 配置/数据/状态/缓存，排除了全局技能发现，但 shell 仍能访问真实用户目录。无技能改名组借用了全局旧验证器，整轮不作为干净任务对照；其 [全部原始任务证据](attempt-2/iteration-1/)与评分均保留。该轮三组均完成了原始任务断言，不能只展示重跑中旧版失败的一次。
3. 在查看重跑结果前统一增加每运行独立的子进程 USERPROFILE/APPDATA/LOCALAPPDATA，三个配置的两个场景全部重跑为 attempt-3。模型、提示、夹具、断言、权限、超时和步骤上限不变。审核未发现此次基线借用全局目标工具。
4. 使用 `--pure`，无 MCP/外部插件，禁用 web/task/question；技能权限仅允许目标和客户端内置技能，阻止成品 examples 被额外调用。临时用户目录及权限配置**不是操作系统沙箱**；被拒绝的越界尝试在各独立审核中单列，未声称完全无法越界。
5. 子代理独立复核结构化事件、文件字节、输入哈希、真实命令和评分。运行前记录成品/旧版/夹具/查询 SHA-256；模型运行结束后确认成品无漂移。没有为了通过本次测评修改产品逻辑或描述。

审计汇总见 [evidence-audit.json](evidence-audit.json)：全部收集产物哈希一致，未发现已配置 API key 的明文匹配。凭据只通过进程环境提供，仓库不保存配置密钥；原始执行器 metrics 没有被后处理覆盖，模型身份旁证另存 observed-models.json。

回归与门禁记录见 [verification.json](verification.json)：315 项回归、补记文档后的 7 项引用/布局检查、成品 strict 与 diff 检查通过；任务聚合的两次 strict 完整性门通过，真实触发门仍有 1 条运行错误。

## 复现

需要现有 OpenCode 程序及当前用户配置中的 deepseek provider；脚本读取凭据但不输出。使用新输出目录，运行器拒绝复用已有任务目录。以下命令会产生真实模型调用：

```powershell
python -X utf8 evaluation-runs/skill-creator/2026-09-29-live/run_live_evaluation.py trigger --out <新目录>
python -X utf8 evaluation-runs/skill-creator/2026-09-29-live/run_live_evaluation.py scenarios --out <另一个新目录> --isolate-home
```

脚本不自动评分；独立评分应沿用 scenarios.json 断言，落 grading.json 后再执行 skill_benchmark 的 `--strict`。核验现有证据不调用模型：

```powershell
python -X utf8 evaluation-runs/skill-creator/2026-09-29-live/audit_evidence.py
```

配置合并与技能发现参考 [OpenCode 配置文档](https://opencode.ai/docs/config/)和[技能文档](https://opencode.ai/docs/skills/)，本机执行与审计结果优先于推测。客户端临时状态保留在环境清单记录的仓库外位置；交付证据已保存在本目录。
