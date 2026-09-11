# 工具升级：build_index.py 离线优雅降级

## 基本信息
- 日期：2026-09-11
- 版本：skill-creator 0.9.22 → 0.10.0（本轮批次）
- 触发来源：`--source X` 需联网下载，无网络时直接抛错失败——离线环境无法沿用已提交索引。

## 采纳要点（改了什么）
- 新增 `SourceUnavailable` 异常；`download_tarball` 最终失败改抛它，`load_source_checkout` 捕获下载/解包类错误（`URLError`/`socket`/`TimeoutError`/`OSError`/`TarError`）后统一抛 `SourceUnavailable`。
- `main()` 按源降级：
  - 全部源不可达且 DB 存在 → 打印清晰提示、**保留现有 `indexes/upstream.db`、退出 0**；
  - 部分源不可达且有 DB → 对可达源做**按源增量同步**（`sync_incremental`），不可达源的已提交行原样保留（不做会丢行的整库重建）；
  - 仅当**既无网络又无可用 DB** → 退出 1。
- 抽出 `sync_incremental()` 供 `--incremental` 与降级路径共用。
- 更新模块 docstring 说明离线行为。

## 验证结果
- 新增 `tests/test_build_index.py` 3 例（离线+有 DB 保留旧数据 rc=0；离线+无 DB rc=1；多源部分降级保留离线源行、可达源增量）。
- 本轮 skill-creator 全量 pytest 由 167 → **184**（本项 +3，另见 #3/#6 记录）。

## 学习点
- **只读工具要能优雅降级**：确定性脚本在离线/上游变更下应「保留已提交制品并成功退出」，而不是把可用的本地数据连同命令一起作废。
- **整库重建 vs 增量**：多源场景下，某源不可达时不能走整库重建（会静默删掉该源全部行）；按 `(source_repo, path)` 作用域的增量同步天然保留其他源。
