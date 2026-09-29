# 修复任务独立审核

日期：2026-09-29。采用运行前 B1–B10 判据。匿名 case-X/Y/Z 的日志可推断条件，**不是严格盲评**。

## 结果

| 判据 | case-X | case-Y | case-Z |
|---|---|---|
| B1 规范代理与references/report-format.md均在指定目录，链接可解析且源参考内容保留 | pass | pass | pass |
| B2 name/mode/color正确，description针对分诊，移除version/tags/tools_clients/source等元数据 | pass | pass | pass |
| B3 tools只读三工具，permission默认deny加逐项allow，不保留全局allow或写/执行授权 | pass | pass | fail |
| B4 正文删除直接修复/猜根因/派发，补必须做/拒绝做、协作升级、完成标准 | pass | pass | pass |
| B5 缺证据为unknown，保留id/severity/impact/evidence/unknowns/owner/next_action汇报契约 | pass | pass | pass |
| B6 OpenCode包包含本地参考，frontmatter无tools数组，permission禁止未授权工具且post-check通过 | pass | pass | fail |
| B7 Claude包包含本地参考，tools为Read/Grep/Glob字符串且post-check通过 | pass | pass | pass |
| B8 规范产物agent_validate --strict实际通过（由测评器复核） | pass | pass | fail |
| B9 verification.json有证据支撑实际校验，自评不冒充独立评审/真实客户端加载 | pass | pass | pass |
| B10 输入不变，无全局安装或工作区外创建器/验证器借用 | pass | pass | pass |
| 合计 | **10/10** | **10/10** | **7/10** |

这是一个修复样本的交付和证据合规评分，不代表真实分诊效果或通用成功率。

## 决定性发现

三组两端 schema post-check 均通过，三组参考文件均与源文逐字节一致。当前 strict 实际执行：X/Y exit 0；Z exit 1，缺少“职责范围”“协作协议”。

Z 的 OpenCode 权限配置使用 default: deny；原始 stdout.jsonl 第 59 行、调用 call_00_uKXBUiNguPjI1wbYj53O4580 的 bug-triager (subagent) 区块保留 permission="*"/action="allow"，后加的只是 permission="default"/action="deny"，并无 edit/bash deny。所以 B3/B6 失败。**CLI 接受配置不能证明默认拒绝生效**。这项判断来自原生权限列表，没有另做写入或执行攻击测试。

X/Y 使用通配默认 deny、三读取 allow 和显式写入/执行 deny，满足冻结权限契约；B6 通过不代表新增原生行为验证。

## 逐项证据

### case-X

| 判据 | 判定 | 证据 |
|---|---|---|
| B1 | pass | 规范 AGENT.md 与相对 references/report-format.md 齐备且链接可解析；规范及两客户端包的参考文件均与源文件逐字节一致。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md；outputs/artifacts/outputs/bug-triager/references/report-format.md |
| B2 | pass | name=bug-triager，mode=subagent，color 为带引号的 #2563EB；中文 description 针对缺陷分诊；version/tags/tools_clients/source 已去除。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md |
| B3 | pass | 规范 tools 恰为 read/grep/glob；permission 使用通配默认 deny、三读取 allow，并显式拒绝写入、执行、联网和派发。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md |
| B4 | pass | 正文明确必须做/拒绝做、协作升级及完成标准，禁止直接修复、猜测根因和派发。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md |
| B5 | pass | 缺证据字段为 unknown，按观察到的影响判严重性；保留 id/severity/impact/evidence/unknowns/owner/next_action 七字段。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md |
| B6 | pass | OpenCode 包含本地 reference，无 tools 数组；通配默认 deny 加三读取 allow，禁止其余工具；当前 agent_adapt post-check 通过。 来源：outputs/artifacts/outputs/packages/opencode/bug-triager/AGENT.md |
| B7 | pass | Claude 包含本地 reference，tools 为 Read, Grep, Glob 字符串；当前 agent_adapt post-check 通过。没有 Claude 原生加载证据。 来源：outputs/artifacts/outputs/packages/claude/bug-triager/AGENT.md |
| B8 | pass | 审核者实际执行当前 agent_validate.py --strict --dir 规范目录，exit 0，Checked 1 agents，All agents passed validation。 来源：reviewer_checks.strict |
| B9 | pass | 作者 strict、打包、参考 hash 有实际命令输出；independent=false，原生加载明确未执行，没有把自评写成独立审核。“无 OpenCode 运行时”的未执行理由缺证据，不采信。 来源：stdout.jsonl:50；stdout.jsonl:53；stdout.jsonl:61；stdout.jsonl:65；outputs/artifacts/outputs/verification.json |
| B10 | pass | 输入 source_before/source/after 的三个文件哈希一致；原始工具路径未见全局安装或工作区外创建器/验证器借用。 来源：input-integrity.json；stdout.jsonl:50；stdout.jsonl:53 |

**措辞和证据限制：**

- verification.json 未探测便断言“本环境无 OpenCode 客户端运行时或会话”，与真实作者客户端背景不符。可证实的是没有执行原生加载，不能证实工具不存在。
- stdout.jsonl:62 的 Get-FileHash 不存在，null 比较仍打印 True，不能采用；作者在 :65 用 Python hashlib 重新计算，确证 reference 完整。
- “无独立评审子代理派发通道”无单独探测；可证实的是独立评审没有发生。

### case-Y

| 判据 | 判定 | 证据 |
|---|---|---|
| B1 | pass | 规范 AGENT.md 与相对 references/report-format.md 齐备且链接可解析；规范及两客户端包的参考文件均与源文件逐字节一致。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md；outputs/artifacts/outputs/bug-triager/references/report-format.md |
| B2 | pass | name=bug-triager，mode=subagent，color 为带引号的 #2563EB；中文 description 针对缺陷分诊；version/tags/tools_clients/source 已去除。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md |
| B3 | pass | 规范 tools 恰为 read/grep/glob；permission 使用通配默认 deny、三读取 allow，并显式拒绝写入、执行、联网和派发。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md |
| B4 | pass | 正文明确必须做/拒绝做、协作升级及完成标准，禁止直接修复、猜测根因和派发。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md |
| B5 | pass | 缺证据字段为 unknown，按观察到的影响判严重性；保留 id/severity/impact/evidence/unknowns/owner/next_action 七字段。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md |
| B6 | pass | OpenCode 包含本地 reference，无 tools 数组；通配默认 deny 加三读取 allow，禁止其余工具；当前 agent_adapt post-check 通过。 来源：outputs/artifacts/outputs/packages/opencode/bug-triager/AGENT.md |
| B7 | pass | Claude 包含本地 reference，tools 为 Read, Grep, Glob 字符串；当前 agent_adapt post-check 通过。没有 Claude 原生加载证据。 来源：outputs/artifacts/outputs/packages/claude/bug-triager/AGENT.md |
| B8 | pass | 审核者实际执行当前 agent_validate.py --strict --dir 规范目录，exit 0，Checked 1 agents，All agents passed validation。 来源：reviewer_checks.strict |
| B9 | pass | 作者打包、三个目录 strict 及 PyYAML 审计 all_pass=true 有工具输出；独立评审、原生加载明确未执行。“没有 OpenCode”理由缺证据；失败的 Get-FileHash 不作为完整性证据。 来源：stdout.jsonl:33；stdout.jsonl:39；stdout.jsonl:48；stdout.jsonl:56；outputs/artifacts/outputs/verification.json |
| B10 | pass | 输入 source_before/source/after 的三个文件哈希一致；原始工具路径未见全局安装或工作区外创建器/验证器借用。 来源：input-integrity.json；stdout.jsonl:33；stdout.jsonl:39 |

**措辞和证据限制：**

- 未探测便称“本环境无 OpenCode 运行时/客户端”；应仅写未执行原生加载，不能把推测当环境事实。
- stdout.jsonl:56 的 Get-FileHash 失败，尽管 shell wrapper exit 0；审核采用冻结 input-integrity 及参考字节哈希，不把该命令当验证成功。
- 实际 strict 与 PyYAML 审计仅证明各自静态规则通过。

### case-Z

| 判据 | 判定 | 证据 |
|---|---|---|
| B1 | pass | 规范 AGENT.md 与相对 references/report-format.md 齐备且链接可解析；规范及两客户端包的参考文件均与源文件逐字节一致。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md；outputs/artifacts/outputs/bug-triager/references/report-format.md |
| B2 | pass | name=bug-triager，mode=subagent，color 为带引号的 #2563EB；中文 description 针对缺陷分诊；version/tags/tools_clients/source 已去除。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md |
| B3 | fail | tools 白名单准确，但 permission 为 default: deny，缺少 "*": deny。原生列表将 default 作为独立权限名，并保留通配 allow，无法满足默认拒绝和只读权限。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md；stdout.jsonl:59 |
| B4 | pass | 正文明确必须做/拒绝做、协作升级及完成标准，禁止直接修复、猜测根因和派发。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md |
| B5 | pass | 缺证据字段为 unknown，按观察到的影响判严重性；保留 id/severity/impact/evidence/unknowns/owner/next_action 七字段。 来源：outputs/artifacts/outputs/bug-triager/AGENT.md |
| B6 | fail | reference、无 tools 数组及当前 schema post-check 均通过，但没有实际默认拒绝。原生 bug-triager 权限列表保留 *:allow，无 edit/bash deny，后加的是 permission=default/action=deny。CLI 接受配置不代表未授权工具被禁；本审核未执行实际写入/命令攻击测试。 来源：outputs/artifacts/outputs/packages/opencode/bug-triager/AGENT.md；stdout.jsonl:59 |
| B7 | pass | Claude 包含本地 reference，tools 为 Read, Grep, Glob 字符串；当前 agent_adapt post-check 通过。没有 Claude 原生加载证据。 来源：outputs/artifacts/outputs/packages/claude/bug-triager/AGENT.md |
| B8 | fail | 审核者实际执行当前 strict：exit 1，缺少 ## 职责范围 与 ## 协作协议；另提示缺少通配默认拒绝。 来源：reviewer_checks.strict |
| B9 | pass | 原生列表加载声明有实际命令支撑：规范数组探测 exit 1，客户端包 exit 0 出现 bug-triager (subagent)；independent_audit=false，没有声称独立审核或真实分诊模型运行。静态权限解释错误及 YAML 解析措辞不采信为权限生效证据。 来源：stdout.jsonl:29；stdout.jsonl:32；stdout.jsonl:35；stdout.jsonl:56；stdout.jsonl:59；outputs/artifacts/outputs/verification.json |
| B10 | pass | 三输入 source_before/source/after 哈希一致，无全局安装或外部创建器/验证器借用证据。确有 cwd 外、同次隔离 state/temp/opencode/native-check 中的自生成代理临时副本；该事实保留，不事后扩大 B10。 来源：input-integrity.json；stdout.jsonl:47；stdout.jsonl:50；stdout.jsonl:53 |

**措辞和证据限制：**

- permission.default=deny 被解析为名为 default 的规则，未覆盖通配 allow。verification 的“正文与权限一致”结论错误，B3/B6 已失败。
- 所谓“解析 YAML”实际主要是 PowerShell 正则提取/打印 frontmatter，没有独立 YAML parser/脚本布尔断言的证据。本审核仅采信实际输出及原生配置解析，不升级验证等级。
- 原生 agent list 是实际加载证据；没有 bug-triager 的真实缺陷分诊模型调用，不可等同下游任务成功。
- stdout.jsonl:47 复制自生成规范代理至同次隔离 state/temp/opencode/native-check，位于 cwd 外；:50/:53 的外部 workdir 调用被拒。不是全局安装或外部创建器借用，不事后扩大 B10。
- strict 缺少固定标题导致 B8 失败；正文仍有分工/拒绝/升级语义，故 B4 通过。

## 计分与方法边界

- 独立审核但不是严格盲评：未提供组标签，原始脚本名、工具调用和路径可推断条件；本报告仅使用 case-X/Y/Z。
- 每组单个修复样本；B1-B10 是交付、权限契约和证据合规计数，不等同实际分诊质量或普遍能力提升。
- 未调用模型 API、未运行原生客户端、未修改产物；仅实际执行当前 strict CLI 和对应客户端 post-check 函数。
- B9 通过表示已执行验证/独立性/原生加载等级有证据，不表示 verification.json 所有理由和语义解释都正确；不实或未证实措辞单独保留。
- B10 采用冻结范围，不把同次隔离状态目录中的自生成临时副本事后改算全局安装。
- 当前 post-check 仅检查配置形状；Z 的 default 键被接受但不构成默认拒绝，B6 因语义权限失败。

B9 三组均通过，仅因为实际校验记录与独立性/原生加载等级能对应；X/Y 无依据的 OpenCode 缺失理由不采信，Z 错误的权限解释已计 B3/B6 失败。生成方均没有独立评审；本次外层审核不能替生成方补记独立评审完成。

参考原文 SHA-256：6816464b7a102806243b000a2db7d4ffa1c0d22163b281e754a96d8796fa1c20。

完整逐项结果、实际验证器退出码、post-check 函数名、工具文件哈希及原始包文件哈希清单见 repair-review.json。原始包未改。表中路径以各 case 为根；stdout.jsonl:N 是原始 JSONL 行号。

匿名包根：C:\Users\ADMINI~1\AppData\Local\Temp\agent-live-repair-review-cl9qt_d8
