# 纪律→工具：validate_skills.py 静态校验 allowed-tools 形状

## 基本信息
- 日期：2026-09-11
- 对象：`scripts/validate_skills.py`（技能验证器）
- 触发来源：安装编排设计（`tools/README.md`）P1 收尾遗留——`allowed-tools` 成为技能侧唯一权限白名单键后，只有 `package_skill.py` 在**打包时**做形状 post-check；验证器不识别该键，形状错误可穿过发布门。决策依据：用户确认补此验证器缺口。

## 背景
技能 frontmatter 瘦身后，`allowed-tools`（可选，Claude 工具名白名单）是技能侧唯一的权限声明。`package_skill.py` 会在打包时拒绝畸形白名单（dict 形式、非字符串项、客户端标签列表、空表），但 `validate_skills.py` 的 frontmatter schema 检查完全跳过该键——一个形状错误的技能能通过 `--strict` 发布门，直到打包阶段才失败，且客户端标签列表会被静默误用为元数据。

## 改动
- `validate_skills.py` 新增 `check_allowed_tools(metadata, rel_path)`，在元数据 schema 检查（`category` 之后）调用：
  - **复用** `package_skill` 的 `normalize_allowed_tools` / `CLIENT_LABELS` / `PackageError`，验证器与打包器对「合法白名单」的判定不可能分歧（single source of truth）。
  - 拒绝：非 list/str 形式（dict 等）、list 内非字符串项、空白名单、纯客户端标签列表（`claude`/`opencode`/…）。输出 `❌` 错误（非 advisory），与打包器的拒绝语义一致。
  - 键缺席 = 不限制，保持可选语义。
- `references/quality-bar.md` 第 1 项补注「形状由验证器自动校验」。

## 验证结果
- `python -m pytest tests/ -q` → **199 passed**（193 → 199：`test_validate_skills.py` +6）
- `python skills/skill-creator/scripts/validate_skills.py --strict --dir skills/skill-creator` → 全绿
- `python skills/skill-creator/scripts/validate_skills.py --strict --dir <仓库>/skills` → Checked 5，全绿
- 新增用例覆盖：list 形式通过、string 形式通过、dict 形式失败、非字符串项失败、客户端标签列表失败、空表失败。

## 学习点
- **校验下沉到发布门**：只在打包器做 post-check 的纪律，必须在验证器再强制一遍——否则错误穿过 gate，晚失败（或静默降级）。
- **复用权威实现而非重写**：验证器不复制白名单形状规则，而是 import 打包器的 canonicalizer，从根上消除「两处规则各自漂移」。
