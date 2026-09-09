# 对比记录：gold-standards 描述记忆库 + 触发失败分类（借鉴反馈闭环）

## 基本信息
- 日期：2026-09-09
- 需求：description 自动优化（run_loop）每轮从零改写、无先例引导；是否吸收「高分描述记忆库 + 失败分类」增强闭环
- 上游来源：`https://github.com/antongulin/opencode-skill-creator`（Anthropic 官方版的开源 opencode 移植，插件化 npm 分发；Apache-2.0）
- 前情：本地已有 run_loop（train/test 60/40 防过拟合、test 分选优）、run_eval（heuristic/cli 双模式）、stage 7 手动档查询集审阅

## 对比报告
- **gold-standards（上游独有，本次评估核心增量）**：把经测试验证的高通过率 description 入库（含 passRate/notes，按分排序封顶 50），优化时取 top5 注入提示词当 few-shot 引导——闭环复用已验证措辞，而非每次从零想。
- **触发失败分类 taxonomy**：eval 结果分 false_negative / false_positive / run_error 三类，各配 remediation 模板注入改进提示——改进提示更结构化。
- 其余（opencode 插件注册、安装冲突护栏、`.opencode-skill-creator-version` 自更新）绑定其 npm 插件分发形态，与本地「目录复制安装」不适配，不采纳。

## 结论
- **部分采纳（机制参考，Python 化落地为轻量约定）**：
  - description 迭代时，把历史高通过率描述（含其 run_eval 得分）作为先例随改进提示一并给出，避免每轮从零发明措辞。
  - run_eval 输出按失败类型归因（应触发未触发 / 不应触发却触发 / 运行错误），改进提示按类型给 remediation。
  - 落地范围以 SKILL.md 阶段 7 与 references 为准；不新增常驻记忆库文件（本地 run_loop 以工作区 iteration 目录为记忆载体，先例取自上一轮胜出描述与其 test 分）。

## 提炼的学习点（已用于改进 skill-creator）
- 描述优化是「从好里选更好」而非「从零造好」：上一轮 test 分最高的描述就是本轮最可靠的 few-shot 先例——记忆库 = run_loop 的迭代产物，不是额外维护物。
- 失败要分型再改：假阴性（触发面漏词）、假阳性（过度匹配/泛化）、运行错误（工具/依赖问题）是三类不同病，remediation 不能混为一谈。

## 改进建议
- 无（机制已并入 SKILL.md 阶段 7 纪律；如 gold-standards 独立记忆库收益在真实场景被验证，再升级为单独脚本）。
