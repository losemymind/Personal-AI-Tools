# 触发测评独立审核

审核日期：2026-09-29。审核者独立读取冻结协议、8 条查询和原始事件，不调用模型、不重跑测评、不修改原始证据或产品。

## 结论

本轮 8 条尝试全部正常完成，分类覆盖 8/8；四个正例均观察到目标技能成功派发，四个负例均未观察到加载信号。独立重算与 trigger/evaluation.json、各 signals.json 和 result.json 一致。无触发计分阻断问题。

这是当前描述、单客户端、单模型、每条一次的固定小样本结果，不能外推稳定准确率，也不能证明生成产物或下游角色执行合格。

## 逐条证据

下表行号是相应 trigger/raw/query-XX/stdout.jsonl 的物理行号。派发须为结构化 tool_use，tool=skill、input.name=agent-creator、state.status=completed；另核对工具返回 metadata.dir 属于本条安装目录。

| 查询 | 冻结标签 | 成功派发 | 精确读取目标 SKILL.md | 执行状态 | 独立结论 |
|---|---|---|---|---|---|
| 01：创建只读日志代理 | 正 | 第 2 行，call_00_apiC9i8mlcFo5WfzA7kT5124 | 无 | completed，rc=0，20.203 s | 通过 |
| 02：改进已有代理定义 | 正 | 第 3 行，call_01_eACx8G6tYsoZ9ttq96jk2688 | 无 | completed，rc=0，21.266 s | 通过 |
| 03：固化发布核对负责人 | 正 | 第 2 行，call_00_ICqsHzeTOJCXrV0XPdlA0347 | 无 | completed，rc=0，21.531 s | 通过 |
| 04：适配 OpenCode 代理 | 正 | 第 3 行，call_00_nftDUUE4XkSDNbQYXEIg9499 | 无 | completed，rc=0，13.296 s | 通过 |
| 05：解释 Markdown | 负 | 无 | 无 | completed，rc=0，4.641 s | 通过；结构化工具调用 0 |
| 06：直接审查 Python | 负 | 无 | 无 | completed，rc=0，4.968 s | 通过；结构化工具调用 0 |
| 07：整理发布风险 | 负 | 无 | 无 | completed，rc=0，5.390 s | 通过；结构化工具调用 0 |
| 08：翻译短句 | 负 | 无 | 无 | completed，rc=0，4.047 s | 通过；结构化工具调用 0 |

- combined 按协议取成功派发 OR 成功精确读取；本批全部四个正信号来自派发，未实际覆盖“只 read、不 dispatch”的分支。
- 读取模板、参考文档、代理输入或输出均不计为读取目标 SKILL.md；普通文本提及不参与计分。
- 八条均 timed_out=false、无顶层 error 事件，负例不存在把 timeout/error 当成未触发通过的问题。工具运行或产物质量的失败应在产物审核中另行判断；进程正常结束本身不证明任务完成。

## 冻结与证据完整性

- queries.json 的 SHA256 为 7f03d56c9fc0e5cc82a2b1bee122988b2f5e1357b4538fb1f8b129dab2112d0d，与 frozen-inputs.json 及触发环境记录一致；协议、场景、runtime 四份冻结文件哈希均核对一致。
- 逐条核对 invocation.json 的实际提示词、evaluation.json 的 query/should_trigger 与冻结查询一致，未看到运行后标签替换。
- 八组 evidence-hashes.json 共 128 个文件全部重新计算 SHA256，零不一致。
- 八份安装副本 SKILL.md 均匹配冻结产品哈希；输入完整性记录均显示源及运行副本不变。

## 模型与环境

- 客户端版本记录为 OpenCode 1.18.30；实际 argv 包含 --pure、--format json、请求 deepseek/deepseek-flash，超时 90 秒。保存配置的 build steps 为 8。
- 八个独立 state_root。环境配置包含独立 XDG、USERPROFILE/HOME、APPDATA/LOCALAPPDATA；MCP 为空、plugin 为空，webfetch/websearch/question/task/external_directory 禁止。
- baseline discovery 只有内置 customize-opencode。每条 discovery 中目标技能恰有一个，位置均为本条工作区 .opencode/skills/agent-creator/SKILL.md；内置 customize-opencode 可被发现但配置禁止调用。结构化事件中没有它的调用。
- 独立以只读方式打开八份本地 OpenCode 会话数据库，仅查询 message 表。原始事件 sessionID 对应的 27 条 assistant 消息，message_id/session_id/provider/model/finish 与 observed-models.json 完全一致，均记录 provider=deepseek、model=deepseek-flash；不是仅复述请求参数。该元数据不能证明供应商底层权重或实际账单。
- 核对 read/write 的具体路径和 bash 命令：可见访问落在各自工作区，执行的是随本条安装副本携带的工具；没有可见的全局目标技能调用或工作区外文件访问。该结论限于保留的可见事件，进程目录隔离仍不等于操作系统沙箱。

## 审核边界

此文件仅审核触发信号、标签、执行状态及相关来源证据。未把四份正例产生的定义文件认定为合格产物，未将外层独立审核算作模型自身派发评审；后续产物与下游运行须按各自冻结断言评分。
