# 对比记录：基线行为门（RED→GREEN）+ evals 随技能发布 + 发布纪律（借鉴反馈闭环）

## 基本信息
- 日期：2026-09-09
- 需求：引入「技能不成立」的显式判定门与发布纪律——目前本地缺「基线不失败则技能无必要」的决策点，也缺发布/入库的隔离验证
- 上游来源：`https://github.com/anthropics/skills`（`skills/skill-creator/`；基线双跑/without_skill 对比为官方评测闭环一部分，Apache-2.0）+ antongulin/opencode-skill-creator（安装/发布健壮性）
- 前情：本地 stage 6 已有「有/无技能基线对比」纪律（Iron Law：基线先于写作），但缺「若基线不失败即砍掉技能」的显式决策；发布走「复制到客户端 + 归档入库」，无隔离验证

## 对比报告
- **基线行为门**：fresh 子代理**无技能**跑场景（RED）——若基线不失败则技能不必要、停；写后带技能重跑（GREEN）必须消除基线失败。随技能发布 `evals/`（triggers.json + scenarios，带 baseline_failure/assertions/holdout），改动必回归。
- **发布纪律**：入库前 secret 扫描；隔离 HOME 安装实测；feature branch→PR→tag→验证后放行，禁止直推默认分支。

## 结论
- 基线行为门**采纳为流程判定**（RED→GREEN 是编排纪律，本地 stage 6 Iron Law 已同向，补上「基线不失败 → 技能无必要」的显式门）。
- `evals/` 随技能发布、holdout 防过拟合**采纳为入库约定**（推荐层；触发用例/场景与技能同目录沉淀）。
- 发布纪律（secret 扫描、PR/tag、隔离安装实测）**采纳为 stage 9 入库前检查项**；不新增重型 CLI（本地无 npm/联网发布管道，落地为可手工/脚本执行的检查清单）。

## 提炼的学习点（已用于改进 skill-creator）
- 一个技能值得存在的判据是**它改变了行为**：无技能基线不失败 = 没有要修的东西（与措辞微测的 no-guidance 对照组同构）——不是「写得好」，是「有必要」。
- 触发测试的查询质量决定描述质量：坏查询（假阴性/假阳性/run_error）会训练出坏描述——上线前先人工审阅触发集。
- 发布 = 可逆且可验证：secret 扫描在推前、隔离安装实测在 tag 后，都是低成本高杠杆的防呆。

## 改进建议
- 本日期随「上游对比与升级（2026-09-09）」落地为 SKILL.md 阶段 6/7/9 纪律与 quality-bar 检查项；「gold-standard 先例注入」见同日 antongulin 记录。
