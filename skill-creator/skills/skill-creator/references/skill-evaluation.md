# 场景评测与产出审核

用于比较技能带来的任务效果。方法参考 Anthropic skill-creator 的基线双跑、评分和分析流程，以及 antongulin 的配对完整性检查；本地执行与统计契约以随包工具为准。

## 1. 固定任务与基线

- 先记录代表性输入、成功标准、评测提示、模型与客户端；断言要能区分真正完成和表面回答。
- 新建技能用 without_skill；改进已有技能用修改前的 old_skill。旧版本快照放评测临时区，不作为另一份开发源。
- 同一 eval 的双方使用相同输入、断言与重复次数；运行编号一一对应。若并行能力可用且已有授权，可并行执行，否则顺序执行。
- 每轮写入新 iteration 目录。不要重用已有 run 目录，防止旧输出或旧 grading 混入。
- eval_metadata.json 记录 eval_id、名称、prompt、assertions；任务清单可保存在目标技能的 evals/evals.json。

## 2. 执行并保留真实产物

```bash
python scripts/skill_scenario.py --client opencode --model <模型id> --prompt "<任务>" \
  --input-dir <输入目录> --output-dir outputs --skill-dir <技能目录> \
  --run-dir <workspace>/iteration-1/eval-report/with_skill/run-1
python scripts/skill_scenario.py --client opencode --model <模型id> --prompt "<相同任务>" \
  --input-dir <相同输入目录> --output-dir outputs \
  --run-dir <workspace>/iteration-1/eval-report/without_skill/run-1
```

input-dir 可省略；输入被复制到临时工作区的 inputs/。output-dir 指定工作区内相对输出目录，默认 outputs/；不允许覆盖 inputs/ 或安装配置目录。工具把目录约定附加到任务提示中；两组保持一致。

执行器在清理前收集工作区新生成的文件，保存到运行目录 outputs/artifacts/，并写 artifacts.json 清单（来源、大小、哈希、跳过项与错误）。原始回复保存在 outputs/response.txt。安装的技能、输入及配置文件不作为输出复制，符号链接不跟随。

每次运行还保存 transcript.md、metrics.json、timing.json；超时和非零退出也保留已有产物及失败状态。检查真实文件，不能只根据回复“已生成”判成功。--keep 保留工作区供排查；--client-cmd 支持自定义客户端命令及 {prompt}/{model} 占位，用于适配和本地测试。

临时 cwd 只分离文件；without_skill 表示本次没有安装目标技能，不保证客户端全局技能不可见。严格对照需使用明确的独立客户端配置和一致权限，记录这些条件。不要把临时目录称为安全沙箱。

## 3. 打分与评审

评分代理读取 `agents/skill_grader.md`，提供 expectations、transcript_path、outputs_dir，逐条检查真实产物并保存 grading.json。可程序判断的断言优先用脚本验证；评分者不能覆盖执行器记录的失败状态或补造 token 数。

主观质量、纪律合规及修复反馈交 `agents/skill_reviewer.md`，输出 review.json。作者修订后再次评审，通过或达到最大迭代数停止；上限退出需交代剩余问题。没有独立代理时可内联按角色审核，说明证据缺少独立性。

盲测按 `agents/skill_comparator.md`：随机 A/B 标签、隐藏版本来源，先比较输出，再交 `agents/skill_analyzer.md` 复盘。不要向盲测者泄露作者预期结论。

## 4. 聚合与检查完整性

```bash
python scripts/skill_benchmark.py <workspace>/iteration-1 --skill-name <名> \
  --primary with_skill --baseline without_skill --strict
```

生成 benchmark.json 与 benchmark.md。默认报告模式允许查看不完整结果；--strict 在报告落盘后对数据完整性问题返回失败。

- 每个 run-* 都计入尝试；缺评分、损坏数据、执行失败或超时必须在统计中可见。
- 每配置展示 attempted、completed、errors、incomplete、coverage；评分成功率只在有效观测上计算，并与覆盖率一起读。
- delta 按 eval_id 和 run_number 配对。场景、重复数不齐或失败时不能据总体均值宣称增益；查看不可比原因与配对覆盖。
- 成本缺失为 null / N/A；真实 0 保留。每项统计查看有效样本 n，不把没有记录的 tokens 或耗时当节省。
- 模型和客户端来自运行记录；未知与混合条件如实展示。不要用模型占位符代表实测来源。
- JSON 字段细节由 SKILL.md 中的「评分、指标、基准 JSON 契约」入口按需读取。

## 5. 分析与迭代

分析代理按 `agents/skill_analyzer.md` 检查恒过/恒败断言、单侧通过、高方差、失败分布与成本取舍，输出 JSON 字符串数组形式的观察笔记：

```bash
python scripts/skill_benchmark.py <workspace>/iteration-1 --skill-name <名> --notes <笔记.json>
```

优先修执行错误，再修任务行为；重复工作可沉淀为脚本。新一轮使用新目录并重跑双方；只对可比数据下结论。结构分不能证明任务效果，真实触发也不能证明产物质量。
