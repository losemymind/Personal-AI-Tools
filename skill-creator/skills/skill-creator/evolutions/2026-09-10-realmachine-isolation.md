# 纪律→工具：真机评测污染仓库 → run_eval 一次性隔离工作区

## 基本信息
- 日期：2026-09-10
- 版本：skill-creator 0.9.6 → 0.9.7
- 触发来源：0.9.5/0.9.6 真机基准期间发现的仓库污染（本会话实证）

## 需求与证据

**证据（真机评测的副作用）**：`run_eval --mode cli` 在**仓库根就地**运行 `opencode run`。被触发的 skill-creator 代理会**真的执行技能工作流**，于是：
1. **改动真实仓库**：向 `tests/test_hardening.py` 追加了 5 个针对当时新增的 `run_cli_item`/`run_cli_batch` 的测试（内容正确，但属未受控改动）。
2. **生成评测产物**：写出 `skill-creator/.eval-baseline/`、`.eval-cli/`、`.tmp-eval/`、根 `.eval-baseline/` 等未跟踪目录。
3. **派生孤儿进程**：触发代理又去跑它自己的 `run_eval --mode cli`，这些子进程在父进程退出后**继续运行**（实测残留根 PID 27484/43800 及 11 个后代 `opencode run` 进程），持续消耗资源。

评测器本应是只读观察者，却在被评测对象触发的副作用下**改写了自己的被测仓库**——这既是对结果可信度的威胁，也会误伤后续会话。

## 采纳要点（改了什么）

- `scripts/run_eval.py`：
  - 新增 `SKILL_SUBPATHS`（`opencode`→`.opencode/skills`、`claude`→`.claude/skills`，与 `run_scenario` 一致）与 `build_workspace(skill_dir, client)`：`tempfile.mkdtemp` 建一次性目录，把技能 copy 到客户端发现路径下。
  - `run_cli(..., workspace=None)` 以 `workspace` 为 `cwd` 运行；`workspace=None` 时保持旧行为（继承当前目录）。
  - `run_cli_item` / `run_cli_batch` 透传 `workspace`；`main()` 在 cli 模式建工作区、`finally` 中 `shutil.rmtree` 清理（`--keep-workspace` 可保留用于调试）。
  - 新增 `--keep-workspace`；usage/docstring 说明隔离语义。
- `tests/test_hardening.py` +5 例：`build_workspace` 在客户端发现路径装入技能；`run_cli` 传 `workspace` → `cwd`、省略 → `cwd=None`；`main` 隔离后清理工作区；`--keep-workspace` 保留。
- 版本 bump `SKILL.md` 0.9.6 → 0.9.7；SKILL.md 阶段 7 与 README 同步。

## 验证结果

- `python -m pytest tests/ -q`：**77 例全绿**（72 → 77）。
- 成品 strict / 能力库 strict（5 技能）/ agent strict（32）/ `build_catalog.py --check` 全绿。
- 真机复跑（见收尾报告）确认：测试目录/根目录**不再产生**评测产物，且无孤儿进程。

## 学习点

- **被评测对象会真的干活**：触发评测不是无副作用的观察——触发成功后客户端真执行技能，可能写文件、起进程。评测器必须像对待不可信代码一样**隔离运行**。
- **隔离即贴近真实安装**：把技能放进一次性目录的发现路径（`.opencode/skills`）再运行，既防污染又与真实安装形态一致（与 `run_scenario` 收敛到同一模式）。
- **孤儿进程是隐藏成本**：子进程若在父进程超时/退出后继续存活，会拖慢机器并持续改动环境；隔离目录 + 明确清理是必要护栏。
