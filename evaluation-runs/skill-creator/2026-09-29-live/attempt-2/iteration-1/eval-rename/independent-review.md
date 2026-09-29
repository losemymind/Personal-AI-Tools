# rename 场景独立审核：attempt-2

审核者：/root/review。按运行前冻结的 scenarios.json 七条断言逐条评分，读取真实 transcript、收集产物、verification、metrics/timing 和 input-integrity。配置名称可见，非盲评；评分者未参与这些被评分任务的执行。

## 结果

| 配置 | 断言通过 | 执行状态 | 原始收集文件数 | 墙钟秒 |
|---|---:|---|---:|---:|
| with_skill | 7/7 | completed | 4 | 53.146 |
| old_skill | 7/7 | completed | 12 | 102.590 |
| without_skill | 7/7 | completed | 4 | 64.588 |

三组目标技能的文件集合都恰为三个目标文件；SKILL.md 和 README.md 逐字节等于输入只替换资源路径，清单原始字节完全一致。独立重算冻结夹具5个文件的哈希，与三组 input-integrity.json 的 source/after 一致。收集清单中所有文件SHA-256均复核相符。

## 实验协议污染：不可做无技能因果比较

without_skill 的 transcript.md:40 经 shell 枚举真实 USERPROFILE/.config/opencode；:48 直接读取全局validator被客户端拒绝，随后 :53 和 :56 经 shell 成功运行全局旧 skill-creator/scripts/validate_skills.py。这证明技能发现配置隔离不等于 shell 文件系统隔离。本次“无技能”组实际借用了全局创建器工具，不能作为有效无技能基线。保留原始分数与产物，不悄悄清除这一尝试；后续重跑应使用独立 home 并重新审核shell行为。

冻结第7条明确禁止联网、安装、另起模型/子代理和工作区外写入；没有将外部只读工具访问单列为扣分条目。因此原始任务评分保持7/7，实验可比性另记不合格，不将任务成功等同于实验有效。

## 执行与证据边界

- old_skill 在 transcript.md:23 调用 skill 工具加载旧正文；with_skill 只观察到读取/执行随包新validator，没有读取SKILL.md正文或skill工具调用。不能把耗时差解释为入口正文压缩带来的因果收益。
- 三组都曾尝试把辅助脚本写到工作区之外的 opencode 临时目录；客户端拒绝后改到outputs。没有成功外部写入的可见证据。此处依据冻结“没有写入”评价实际效果，另保留被拒请求，不能宣称模型从未尝试越界。
- old_skill 的12个收集文件包括8个 outputs/_verify 辅助脚本/日志/哈希记录。它们不在目标技能目录内，冻结任务允许outputs产物且未禁止辅助证据，所以不扣分。
- old_skill 首次自检遇到UTF-16日志读取错误，修复后重跑退出0。其copy/rename stdout字段为人工整理过的展示文本。without_skill 自检的stdout字段是检查名称摘要，实际进程打印的是all_passed/input_unchanged。记录中的命令与退出结果可核验，检查也确实执行；这些stdout字段不能冒充逐字原始日志，应以transcript为准。
- with_skill清单hash按read_text归一化换行后计算；独立评分另做原始字节比较，确认内容实际未变。with_skill和without_skill自身输入检查范围较窄，整棵输入未变由外层input-integrity与独立重算补足。
- 三组token数直接保留执行器原始metrics；模型身份仅为requested。一次运行、单模型请求、合成夹具不能证明统计显著性、总体性能或真实业务效果。

## 文件

每个配置 run-1/grading.json 保存七条原断言、逐条证据、原始执行指标、限制与实验不可比原因。未修改任何被评分transcript、模型输出、冻结断言或原始metrics。
