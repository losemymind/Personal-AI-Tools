# 缺陷修复：package_skill.py 的 --out 已存在文件守卫

## 基本信息
- 日期：2026-09-11
- 需求：审计确认的真缺陷——`package_skill.py` 在 `--out` 指向一个**已存在的普通文件**时，未做类型校验，须补显式守卫。

## 问题
- `package_skill()` 只校验 `--out` 不能位于技能目录内部，未校验 `--out` 是否为目录。
- 当 `--out` 指向已存在文件时，后续 `shutil.copytree(..., dirs_exist_ok=True)` 会抛出未捕获的异常，向用户暴露原始 traceback，而非可读的打包错误。

## 修复
- 在 `package_skill()` 中解析 `out_dir` 后、`resolve()` 前加入与对侧打包器一致的守卫：
  ```python
  if out_dir.exists() and not out_dir.is_dir():
      raise PackageError(f"--out is an existing file, expected a directory: {out_dir}")
  ```
- 守卫命中时由既有 `main()` 的 `PackageError` 分支统一处理：打印 `❌ …` 并以退出码 1 结束，不再抛 traceback。

## 验证
- 新增 pytest `test_package_out_existing_file_fails_cleanly`：构造已存在的 `--out` 文件，断言退出码为 1、stderr 无 `Traceback`、输出含 `expected a directory`。
- 工作区根 `python -m pytest tests/ -q` 全绿。

## 学习点
- 文件系统边界参数（输入目录、输出路径）都应显式判型，避免把底层 stdlib 异常泄漏成 traceback；同类打包器应共享同一守卫语义。
