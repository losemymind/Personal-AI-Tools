# rename 场景独立审核：attempt-3

评分者 /root/review；按运行前冻结的7条断言评分，沿用attempt-2的原始字节比较方法。读取三组真实transcript、verification及辅助代码、全部目标文件、metrics/timing、artifacts清单、input-integrity，并重新计算冻结输入和收集文件哈希。配置可见，非盲评。未修改原始产物或attempt-2。

## 结果

| 配置 | 通过 | 墙钟秒 | 工具调用 | 收集文件 |
|---|---:|---:|---:|---:|
| with_skill | 7/7 | 116.146 | 27 | 4 |
| old_skill | 7/7 | 115.979 | 29 | 4 |
| without_skill | 6/7 | 93.465 | 25 | 5 |

## 唯一未通过断言：without_skill 的最小字节改动

冻结第3条要求frontmatter完全一致，SKILL.md/README.md除必要路径替换外保持不变。当前和旧版的产物恰等于输入原始字节中的路径替换。without_skill辅助脚本读取文本并使用newline=""重写，额外把SKILL.md的38处CRLF与README.md的7处CRLF改成LF，包括frontmatter中的换行。预期/实际字节分别1150/1112、294/287，因此第3条FAIL；内容文字、资源字节、引用及其他要求通过。此缺陷是格式保真问题，不能表述为语义内容丢失。

验证程序真实执行、commands可由transcript复核，第6条按其真实性通过；它采用文本级比较，无法替代第3条的独立字节验证。没有因保留outputs/_verify.py新增扣分。

## 隔离复核

attempt-3三组client-environment记录独立用户目录。without_skill未读取/运行真实全局skill-creator工具：在工作区搜寻validator，探测已有OpenCode --help，然后用Python标准库完成。transcript.md:34调用了所有配置均允许的客户端内置customize-opencode；without_skill表示不提供目标创建器，不表示不存在客户端内置技能。

旧版和无技能组曾尝试写工作区外的opencode临时目录，被客户端拒绝后改为outputs；当前一条空参数write被中止。三组可见调用未出现成功的外部写入、联网、安装、另起模型或子代理。本次没有发现attempt-2的全局目标工具污染，可进行限定范围内的描述性比较。这里是记录审计，不是操作系统级隔离证明。

## 其他事实与限制

- 三组输入的5文件完整哈希均与冻结夹具相同；清单原始字节全部保持一致。全部收集文件与artifacts.json哈希一致。
- 新旧两组均只是读取并执行随包validator，未观察到加载目标SKILL.md正文或调用skill-creator工具；所以本场景不能单独验证入口正文压缩收益。
- 当前116.146秒、旧版115.979秒，差0.167秒；前轮污染尝试中的明显耗时差没有复现。不能宣称稳定提速。
- 旧版先遇到Get-FileHash不可用、自检误设输入文件数6，随后用Python并修正为5重跑成功。当前也遇到Get-FileHash不可用与目录Select-String错误，随后实际完成检查。终态成功不抹掉中间错误。
- 当前verification实际10项checks，最终答复称11项，作为错误事实声明记录；本轮7条冻结任务断言没有额外的自检数量要求。
- 当前输入检查使用mtime/文件数、部分hash使用归一化文本；独立评分补做全树和原始字节核验。旧版自检stdout是整理的摘要，原始输出以transcript为准。
- 原始token数按metrics保留，不改写为真实计费金额；模型来源为requested。合成夹具、单次运行、单模型不证明统计显著性、因果提升或真实业务效果。

## 交付

三个配置的run-1/grading.json保存冻结断言、逐条证据、原始运行指标与上述限制。attempt-2按原样保留并标明污染，不与attempt-3混合计算重复样本。
