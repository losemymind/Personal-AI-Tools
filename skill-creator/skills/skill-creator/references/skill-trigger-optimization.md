# 触发评测与 description 优化

用于技能内容已稳定、需要调整触发面的任务。工具支持 heuristic 与 Claude/OpenCode CLI；其他客户端的安装支持不等于自动评测支持。

## 查询集与失败归因

设计约 20 条真实风格查询，覆盖应触发场景与关键词相近但不应触发的干扰项。使用具体输入、任务目标与上下文，避免全是显然无关的负例。查询格式为对象数组，字段 query（字符串）、should_trigger（布尔）。

先由 `agents/skill_reviewer.md` 审核查询是否准确标注、能区分相邻能力，修正后再跑。分开记录：假阴性（范围遗漏）、假阳性（描述过宽）、run_error（执行/配置错误）；运行错误不用于改写描述。

## 单次评测

```bash
python scripts/skill_eval.py --eval-set <开发集.json> --skill-dir <技能目录> --json
python scripts/skill_eval.py --eval-set <开发集.json> --skill-dir <技能目录> \
  --mode cli --client claude --model <模型id> --timeout 120 \
  --fail-on-error --fail-on-mismatch --output-dir <报告目录> --json
```

- 默认 heuristic 是词面覆盖代理指标，不能证明真实触发。
- CLI 为查询安装临时技能副本，候选 description 写进副本；源技能不变。--concurrency 控制并发，--runs-per-query 控制重复，--keep-workspace 可保留现场。
- Claude 解析 stream-json 中的 Skill 调用或目标 SKILL.md 的 Read 调用；仅在回复中提及名字、列目录或读取别的技能均不算。OpenCode 识别 skill 工具对目标名称的调用。
- trigger_evidence 保留结构化证据，skill_dispatch 与 target_read 分开。读取说明技能被访问，不能据此证明调用成功或任务完成。
- 超时前已有有效触发证据时保留该触发；没有证据的超时为运行错误。场景是否成功由场景执行状态另行判断。
- 汇总展示 attempted、coverage、errors 与 precision/recall；无有效分母时为 null / N/A。
- 默认输出报告后返回 0；--fail-on-error / --fail-on-mismatch 按请求启用失败门，失败时仍保存报告。

临时工作区不是权限沙箱，客户端可能继承全局技能、配置和权限。真实对照需要控制这些条件并记录客户端/模型版本。

## 描述优化循环

```bash
python scripts/skill_optimize.py --eval-set <开发集.json> --skill-dir <技能目录> \
  --holdout 0.4 --max-iterations 5 --improve-mode cli --eval-mode cli \
  --final-eval-set <未见最终集.json> --final-mode cli \
  --client claude --model <模型id> --report <报告.json>
```

- 开发集按 should_trigger 分层切为 train/validation。训练失败用于改写，验证集用于选优；反复选择后的 validation 不是独立测试。
- 默认 --improve-mode manual：读取提示并输入 description，以独立 EOF 行结束；cli 模式调用指定客户端改写。
- 默认 --eval-mode heuristic，仅作低成本开发参考；需要验证真实客户端行为时选 cli。运行错误终止并保留报告，不当描述失败。
- 改写提示可使用历史最佳开发描述作先例。最终测试查询与结果不得进入改写或候选选择。
- --final-eval-set 与开发集不得重复，只在选优后评选中候选一次；默认 --final-mode cli。看过最终结果后再改写，应换未见最终集。
- confirmation：not_run 未做最终测试；proxy_only 仅词面通过；dispatch_passed 为 OpenCode 派发信号通过；structured_passed 为 Claude 结构化调用/读取信号通过；failed/error 表示未通过/运行错误。历史 approximate_passed 来自旧名称匹配，不是当前检测方法。
- 旧 test_* 字段是 validation 的兼容别名。最终失败或运行错误返回 1，报告仍保留。

交付时展示修改前后 description、开发与最终集范围、信号来源和未测边界；通过触发测试后才应用选中的描述，不能把离线词面分说成实际触发率提升。
