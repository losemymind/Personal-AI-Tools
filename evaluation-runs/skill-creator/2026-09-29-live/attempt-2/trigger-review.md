# 触发证据独立审核

审核日期：2026-09-29。范围：本 attempt 的 `trigger/evaluation.json`，以及 12 份 query 目录中的 `stdout.jsonl`、`execution.json`、`discovery.json`、`observed-models.json`。只读检查冻结证据；没有调用模型，没有修改原始数据。本文件是唯一新增文件。

## 结论

未发现阻断问题。独立按原始 OpenCode 工具事件重算，结果与 [evaluation.json](trigger/evaluation.json) 完全一致：**6 个正例成功派发、5 个有效负例无派发、Q12 超时无结论**。有效查询 11/12，passed=11、failed=0、errors=1、coverage=0.917；有效查询中的 precision/recall 均为 1.0。不能表述为 12/12 通过或任务完成率 100%。

| 查询 | 应派发 | 目标 skill 事件 | 执行记录 | 审核判定 |
|---|---|---|---|---|
| [Q1](trigger/raw/query-01/stdout.jsonl) | 是 | 1 次，completed | rc=0 | 派发成功 |
| [Q2](trigger/raw/query-02/stdout.jsonl) | 是 | 1 次，completed | 120 秒超时 | 派发成功；任务完成未知 |
| [Q3](trigger/raw/query-03/stdout.jsonl) | 是 | 1 次，completed | rc=0 | 派发成功 |
| [Q4](trigger/raw/query-04/stdout.jsonl) | 是 | 1 次，completed | rc=0 | 派发成功 |
| [Q5](trigger/raw/query-05/stdout.jsonl) | 是 | 1 次，completed | 120 秒超时 | 派发成功；任务完成未知 |
| [Q6](trigger/raw/query-06/stdout.jsonl) | 是 | 1 次，completed | 120 秒超时 | 派发成功；任务完成未知 |
| [Q7](trigger/raw/query-07/stdout.jsonl) | 否 | 无 | rc=0 | 有效负例，无派发 |
| [Q8](trigger/raw/query-08/stdout.jsonl) | 否 | 无 | rc=0 | 有效负例，无派发 |
| [Q9](trigger/raw/query-09/stdout.jsonl) | 否 | 无 | rc=0 | 有效负例，无派发 |
| [Q10](trigger/raw/query-10/stdout.jsonl) | 否 | 无 | rc=0 | 有效负例，无派发 |
| [Q11](trigger/raw/query-11/stdout.jsonl) | 否 | 无 | rc=0 | 有效负例，无派发 |
| [Q12](trigger/raw/query-12/stdout.jsonl) | 否 | 无 | 120 秒超时 | 不计成功负例；保留运行错误 |

## 目标版本与原始证据核对

- 6 个正例均含 `tool=skill`、`input.name=skill-creator`、`state.status=completed`；各自 callID 与报告的 tool_use_id 一致，依据是工具事件，不是模型在回复中提到名称。
- 每次 discovery 中目标技能只有一个；6 个事件输出的 Base directory 分别为临时 `eval-qnu3p8bk`、`eval-bn9yjnmc`、`eval-thx66b0m`、`eval-t0huod59`、`eval-z2sl10wq`、`eval-gw75n7kf` 下的 `.opencode/skills/skill-creator`，与对应 discovery.location 一致。每次输出列出的 10 个资源路径均位于该目标目录，没有指向全局同名安装。
- 6 个工具输出均完整包含当前 SKILL.md 的正文，规范化 CRLF/LF 后逐字匹配。审核时源 SKILL.md 的 SHA-256 为 `dfa43a980752f701375a3d208dc3017807cc84784eb2b9768a2a4800f0a4bfd3`，与 [运行前冻结记录](trigger-product-hashes.json) 一致。因此这些事件确实加载本次当前版本正文。
- 逐条重算 step_finish 的 tokens.total 之和及工具事件数量，均与 execution.json 一致；12 条的判定、超时和错误归因与汇总一致。未发现这些证据之间的内部矛盾或伪造迹象；本审核不提供客户端以外的独立签名认证。
- 每条 observed-models.json 均报告 `deepseek/deepseek-flash`，其 session_id 与对应原始流一致，且消息 ID 可以关联到原始事件。这证明本地 OpenCode 会话记录使用该 provider/model 标识，不等于供应商底层模型权重认证。原流未给出模型名时的 null 保持不变，没有改写为已观测值。

## 必须保留的解释边界

1. Q2/Q5/Q6 在超时前已有 completed 的技能派发事件，所以只在“是否派发”层计成功；不能据此宣称工作任务完成或产出合格。
2. Q12 没有 skill 派发，但确实通过 `read` 读取临时目标 SKILL.md，callID 为 `call_01_rljZBi9dhGk2ijlF0Zxl4309`。后续记录包含搜索当前目录、读取创建器脚本以及枚举外部 Temp 的命令。它没有所需应用目录，超时行为与寻找缺失输入一致；不能说“完全未读取技能”，也不能把超时当作不触发成功。
   本轮保持运行前的 OpenCode skill 派发判据，不根据观测结果追改计分。precision/recall 仅适用于派发口径，不涵盖所有读取或加载行为；目标 Read 访问可作为后续信号覆盖改进项。
3. 部分查询需要的业务文件没有随触发集提供。这一批只评价路由信号，不能用于评价任务完成度、产出质量或文件隔离的安全性。
4. 本批为单客户端、单请求模型、每题一次；没有旧版触发对照，也不能从 11 个有效查询外推总体准确率。成品 examples 中的技能和客户端内置技能也在 discovery 中可见，结论限于该安装配置。
5. tokens 是客户端原始事件的报告值；客户端 cost=0 不是实际账单，不支持“零费用”结论。
