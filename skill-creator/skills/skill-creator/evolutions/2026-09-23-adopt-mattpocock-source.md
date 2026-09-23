# 采纳升级：新增上游索引源 `mattpocock`（含两层嵌套扫描模式）

## 基本信息
- 日期：2026-09-23
- 类型：采纳升级（adopt-）——索引覆盖扩展 + `build_index.py` 扫描层新增能力
- 触发来源：用户要求把 `https://github.com/mattpocock/skills` 加入 skill-creator 的上游索引
- 来源：`mattpocock/skills`（MIT，默认分支 `main`，整仓约 1.8MB）；「Skills for Real Engineers」，38 个技能

## 问题与证据（未加源前的实证）
- 既有扫描源全是**一层深**：`scan_skill_dir` 只查 `<skills_root>/<name>/SKILL.md`（`anthropics` / `addy`）或仓库根 `*/SKILL.md`（`composiohq`）。
- 该仓库把技能按类别分组：`skills/engineering/<name>/`、`skills/productivity/<name>/`、`skills/in-progress/<name>/`、`skills/misc/<name>/`——比既有扫描源**深一层**。直接套用现有扫描会得到 **0 条**。
- 仓库体量小（约 1.8MB），整仓 tarball 取数即可，无需稀疏模式。

## 采纳要点
1. **`build_index.py` 新增可选两层嵌套扫描**：源声明 `skills_nested: True` 时，`scan_skill_dir` 改走 `<skills_root>/<category>/<name>/SKILL.md`，索引 `path` 保留完整相对路径（`skills/engineering/code-review`）；扫描逻辑抽成 `_iter_skill_dirs()` 统一产出 `(skill_dir, path, parent_category)`，一层/两层共用同一段 frontmatter 解析与条目构造。
   - **`category` 兜底**：当技能 frontmatter 未声明 `category`（该仓库正是如此，多数只有 `name`/`description`）时，用**父目录名**兜底（`engineering`/`productivity`/…），使 `--category` 过滤对新源可用。frontmatter 显式 `category` 仍优先。
   - 只有含 `SKILL.md` 的目录才收录；仅有 README 的桶目录（`skills/deprecated/`、各 `README.md`）自动跳过。
2. **注册源**：`mattpocock`（`repo` / `tarball`（main）/ `skills_root: "skills"` / `skills_nested: True`）；`search_index.py` 增别名 `mattpocock` / `matt-pocock`。
3. **索引重建（增量）**：`+38 added`；`search_index.py --stats` 由 5 源 2188 条 → **6 源 2226 条**（`mattpocock/skills` 38：engineering / productivity / in-progress / misc）。
4. **文档同步**：成品 `README.md`（源表 + `--source` + 许可）、`references/skill-index.md`（源表 + 用法 + 两层嵌套专段）、成品 `SKILL.md` 阶段 0 源列举、dev `README.md`（来源与沿革 + 2026-09-23 沿革段）、工作区 `AGENTS.md`（命令速查 6 源 2226 条 + 索引源名册）、`INSTALL.md` 校验期望值、`build_index.py` 模块 docstring。
5. **测试**：`tests/test_build_index.py` 更新注册表断言（5→6 源）、更新 provenance 与 docstring；新增 3 例（registry 断言 mattpocock 形态、嵌套扫描 path/category、frontmatter 缺 category 时父目录兜底）；`tests/test_search_index.py` 补别名断言。

## 验证结果
```text
build_index.py --source mattpocock --incremental   → +38 added, ~0 updated, -0 removed
search_index.py --stats                            → 2226 条，6 源（mattpocock/skills 38）
search_index.py "review" --source mattpocock       → code-review（engineering，88 行）
pytest tests/test_build_index.py tests/test_search_index.py → 全绿
validate_skills.py --strict --dir skills/skill-creator     → 全绿
```

## 学习点
- **扫描层应容忍目录布局差异**：不同上游对「技能放在哪一层」没有共识（根 / 一层 / 类别分组）。把「一层 vs 两层」抽成源声明（`skills_nested`）而非硬编码，比按仓库名开特例更可维护；两层扫描复用同一段条目构造，避免第二条解析管线分叉。
- **目录即分类，可作元数据兜底**：当上游把「类别」编码在目录名而不是 frontmatter 时（该仓库 38 个技能几乎都不写 `category`），用父目录名兜底能把仓库的隐式结构转成可检索的 `category`，且不覆盖上游显式声明。
- **先查后建的覆盖是「按仓库补齐」而非常态全扫**：每接一个新源先看其布局与体量，分别决定「整仓 tarball / 稀疏 API / 一层 / 两层 / 根扫描」，再注册——避免为一个源新写一条与既有逻辑平行的取数路径。

## 改进建议（未实施，供后续）
- 若后续出现**三层**或更深的目录布局，可把 `skills_nested` 泛化为「扫描深度」参数；当前仅有两层证据，不做超前泛化。
