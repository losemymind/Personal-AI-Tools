# attempt-2：benchmark 独立评分

## 范围与判定

按 scenarios.json 已冻结的 9 条断言评分；不新增付费调用、不修改成品或执行产物。三组均已出现 metrics.json 和 input-integrity.json 后才开始评分。接受等价 JSON 结构，不强制只有新版工具的字段布局。

实际读取三组 benchmark.json、benchmark.md、conclusion.json，解析完整 transcript 中的工具调用与生成脚本；15 个输入的 source/after 哈希均与冻结夹具相同，9 个最终产物哈希均匹配各 artifacts.json。conclusion 的自述未作为唯一证据。

**输入基准记录是 synthetic；执行这些分析任务的模型调用是真实的。二者的 token/时间不得混用。**

## 原始质量评分

| 组别 | 通过 | 失败 | 实际墙钟秒 | 原始报告 token 累计 | 工具调用数 |
|---|---:|---:|---:|---:|---:|
| with_skill | 9/9 | 0 | 66.641 | 899089 | 33 |
| old_skill | 9/9 | 0 | 69.818 | 587617 | 42 |
| without_skill | 9/9 | 0 | 82.656 | 479409 | 34 |

token 来自 opencode_step_finish_total 累计，含客户端报告的上下文/缓存记账语义；不是费用或独立新生成 token。model 为 requested deepseek/deepseek-flash；客户端流未给出可独立核验的实际 model 名集合。单次时长和 token 不足以建立成本优势。

## 逐条结果

三组均保留4次尝试：有技能配置2完成，基线1完成1执行错误；完成覆盖1.0与0.5；唯一有效配对a/run-1，1/2配对覆盖；整体增益不可用；未知token为null/不可用且有效样本0；全部10/8/12/5秒保留；结论承认synthetic、失败、配对不完整和未知成本。逐项文件字段、运行记录行号见各 run-1/grading.json。

- **with_skill**：直接运行工作区内新版 skill_benchmark.py 两次（transcript:64/80），补notes后生成最终报告。其数据与冻结夹具一致。
- **old_skill**：实跑工作区内旧 aggregate_benchmark.py（transcript:81），看见其丢弃失败尝试、把token记0并输出+1.00。随后自写标准库汇总（84/87）纠正最终产物。最终aggregate_delta为null；unsupported_deltas的数字明确标为不受支持的反例，单对a差值亦限定局部，故第5条通过。
- **without_skill**：自写Python标准库分析并执行（transcript:79/82），94再次解析验证。token缺失用统一 measurements.tokens.value=null 和每配置token_samples=0表达；没有虚构token均值，按等价语义通过第6条。

## 隔离与提示边界问题

**attempt-2不能作为干净的有技能/无技能因果比较。保留原始评分，不删除或重写证据。**

1. 无技能组 transcript:49/54 的 shell 成功列举真实 USERPROFILE/.config/opencode/skills；68确认旧聚合脚本存在。57/58 的 read、62/63 的Get-Content、71的复制均被external_directory拒绝，未见成功读取旧工具正文或执行全局聚合脚本。仍存在全局目录信息泄漏及禁止外部访问的提示偏离。
2. 新版组72尝试写工作区外临时notes、旧版组78尝试向外部临时目录输出，两次均被拒绝；随后改为当前outputs，未观察到成功越界写。
3. 第9条冻结断言明确禁止全局写、联网、安装和另起模型，未把外部只读发现/被拒绝的越界尝试列为独立失败项，因此不在结果出来后扩大规则扣分。该问题单独登记为评测协议/环境风险，后续隔离修复后的attempt-3应另评分。
4. 未观察到三组联网、安装软件或调用另一个模型/子代理。客户端本身的运行环境与已有工具缓存不是受测模型主动安装行为。

## 解释边界与后续

本场景的原始质量分相同，无法据此宣称新版提升最终准确率。可观察到新版工具本身输出正确，旧版需要模型额外纠错；这只是一个固定夹具的一次执行证据。需要以完整隔离的新attempt为主结果，并保留本attempt作为环境缺陷证据。

后续改进断言时应在下一版本冻结前拆分第9条，把工作区外读取/写入尝试、输入完整性与实际执行分别测量；不能按本次结果倒推调整评分。
