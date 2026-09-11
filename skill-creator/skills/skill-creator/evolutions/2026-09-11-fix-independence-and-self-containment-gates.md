# 门禁加固：零交叉引用 / 成品自包含覆盖盲区

## 基本信息
- 日期：2026-09-11
- 类型：缺陷修复（审计发现的发布门覆盖盲区，不扩功能、不改验证器语义）
- 触发来源：上一轮创建器审计（`evolutions/2026-09-11-fix-audit-findings.md`）遗留的「zero-cross-reference 门禁仍有覆盖盲区」

## 证据（修前实测）
- 现行交叉引用门禁（`tools/tests/test_creators_independent.py` + 两侧 `tests/test_independence.py`）按后缀白名单扫描，`.template`（如 `templates/evals.json.template`）不在其中；token 匹配大小写敏感，`Agent-Creator` 一类写法漏检。
- 实测：两成品在「非 `evolutions/`、非 `examples/`」范围内，`templates` 扩展与大小写不敏感匹配下**均 clean**——加固不会引入误报。
- `evolutions/` 有 39 处兄弟 token 命中，全部是历史「跨创建器对比/借鉴」记录的应有内容；`examples/` 是上游样例。**二者保持排除**属有意设计，非盲区。
- skill-creator 侧确实缺少与 agent-creator `tests/test_product_self_containment.py` 对等的「全 md dev-only/悬空」扫描（`validate_skills.py` 只校验 SKILL.md 的反引号引用）。将该扫描逻辑套到 skill 成品，暴露 1 处真实悬空：`references/skill-anatomy.md` 的示意路径 `templates/component.tsx`。

## 改动
- `tools/tests/test_creators_independent.py`：`SCAN_EXTS` 增 `.template`；token 匹配改大小写不敏感；抽出 `_scan_for_tokens` 并为「.template/大小写变体必被捕获」与「evolutions/examples 按设计跳过」各补回归用例；注释写明排除理由。
- `skill-creator/tests/test_independence.py`、`agent-creator/tests/test_independence.py`：同步 `.template` 与大小写不敏感（同模板各一份，保持同构）。
- 新增 `skill-creator/tests/test_product_self_containment.py`：镜像 agent-creator 版本——成品全 md（fenced 豁免；跳过 `examples/`、`evolutions/`）dev-only/悬空扫描 + 布局 slim 断言 + 死分支回归。
- 成品文档修正：`references/skill-anatomy.md` 把示意路径改为占位形式 `templates/<模板名>.tsx`，消除悬空、明确其为范例。
- 文档同步：workspace `AGENTS.md`（Step 5 发布门 + 硬约束 2）、`README.md`（自包含硬约束）说明 dev-only 全 md 自包含 pytest；仓库根 `AGENTS.md` 结构要点改为「两侧都有自包含 pytest，差异仅在 skill 另有 validate_skills 成品自校验」。

## 验证
```bash
python -m pytest tools/tests -q                                   # 25 passed
python -m pytest tests/ -q                                        # skill-creator
python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator
python -m pytest tests/ -q                                        # agent-creator
python skills/agent-creator/scripts/validate_agents.py --strict --dir E:\GitHub\Personal-AI-Tools\agents
python tools/scripts/build_catalog.py --check
```

## 学习点
- 门禁的「后缀白名单 + 大小写敏感」是两类静默盲区；白名单式扫描应显式覆盖随产物分发的模板/数据扩展名，并统一大小写归一。
- 「排除目录」必须写明理由并有回归用例固定，否则下次审计会把有意排除误判为缺陷、或反过来把缺陷洗成有意排除。
- 同构孪生的工作区应各自持有对等的门禁能力；skill 侧此前凭「成品可自校验」省略了全 md 扫描，实则 `validate_skills.py` 的引用检查仅 SKILL.md 作用域——能力差异要在文档里说清，而不是靠注释。
