---
name: ue-editor-lifecycle
description: "指导 Unreal Engine 编辑器的安全关闭、重建与异步启动，避免卡死与 MCP 服务器无响应。当用户提到启动/重启编辑器、LaunchUE、PIE、MCP 未响应、DLL占用、Build失败、GenerateProjectFiles、UnrealEditor等时使用。"
category: development
risk: safe
---

# UE 编辑器生命周期管理

## 概述

指导 Unreal Engine 编辑器的安全关闭、重建与异步启动流程，特别针对源码构建版本的特殊配置与 Windows 平台特性。核心目标是避免 PowerShell 进程卡死、UE 编辑器冻结、MCP 服务器无响应、DLL 被占用等常见问题，确保开发流程顺畅。

## 何时使用此技能

- 用户需要启动/重启/打开 Unreal Engine 编辑器
- 用户提到 `UnrealEditor.exe`、`LaunchUE.bat`、`Build.bat`、`GenerateProjectFiles.bat` 等命令
- 用户报告编辑器卡死、MCP 服务器无响应、DLL 被占用、Build 失败等
- 用户需要重建项目编辑器（源码构建版本）
- 用户需要启动 PIE（Play In Editor）模式

## 工作原理

### 步骤 1：检查并结束已运行实例

检查项目是否已有 UE 编辑器实例正在运行，如果有，先安全结束，避免 DLL 占用冲突。

**检查命令：**
```powershell
Get-Process | Where-Object { $_.ProcessName -like "*Unreal*" -or $_.Path -like "*UnrealEngine*" }
```

**安全结束命令：**
```powershell
Stop-Process -Name "UnrealEditor" -Force
Stop-Process -Name "UnrealEditor-Cmd" -Force
```

### 步骤 2：源码构建版本的特殊配置

如果引擎是源码构建版本，需要在 `Engine\Build` 目录下创建 `InstalledBuild.txt` 文件，让引擎被视为安装版本。

**作用：** 构建项目编辑器时不会连引擎一起构建，大幅减少构建时间。

**创建命令：**
```powershell
New-Item -Path "<EnginePath>\Build\InstalledBuild.txt" -ItemType File -Force
```

### 步骤 3：构建项目编辑器（如需要）

在结束旧实例并完成配置后，重新构建项目编辑器：

```cmd
<ProjectPath>\Build\BatchFiles\Build.bat <ProjectName> Win64 Development -project="<ProjectPath>\<ProjectName>.uproject"
```

### 步骤 4：异步启动编辑器

避免使用阻塞的 PowerShell 调用，改用后台进程启动，防止卡死：

```powershell
Start-Process -FilePath "<ProjectPath>\Binaries\Win64\<ProjectName>.exe" -ArgumentList "<ProjectPath>\<ProjectName>.uproject" -WindowStyle Normal
```

或者使用 `start` 命令（更轻量）：

```cmd
start "" "<ProjectPath>\Binaries\Win64\<ProjectName>.exe" "<ProjectPath>\<ProjectName>.uproject"
```

## 示例

### 示例 1：安全重启编辑器

**输入：** "重新启动 UE 编辑器，项目卡死了"

**输出：**
```powershell
# 1. 结束已运行实例
Stop-Process -Name "UnrealEditor" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "UnrealEditor-Cmd" -Force -ErrorAction SilentlyContinue

# 2. 异步启动
Start-Process -FilePath "C:\Path\To\Project\Binaries\Win64\ProjectName.exe" -ArgumentList "C:\Path\To\Project\ProjectName.uproject" -WindowStyle Normal
```

### 示例 2：源码构建版本重建编辑器

**输入：** "源码构建的引擎，重建项目编辑器"

**输出：**
```powershell
# 1. 检查并结束实例
Stop-Process -Name "UnrealEditor" -Force -ErrorAction SilentlyContinue

# 2. 创建 InstalledBuild.txt（让引擎被视为安装版本）
New-Item -Path "E:\UnrealEngine\Engine\Build\InstalledBuild.txt" -ItemType File -Force

# 3. 构建项目编辑器
& "C:\Path\To\Project\Build\BatchFiles\Build.bat" ProjectName Win64 Development -project="C:\Path\To\Project\ProjectName.uproject"

# 4. 启动编辑器
Start-Process -FilePath "C:\Path\To\Project\Binaries\Win64\ProjectName.exe" -ArgumentList "C:\Path\To\Project\ProjectName.uproject" -WindowStyle Normal
```

### 示例 3：启动 PIE 模式

**输入：** "启动 PIE（Play In Editor）"

**输出：**
```powershell
# 先确保编辑器已启动
Start-Process -FilePath "C:\Path\To\Project\Binaries\Win64\ProjectName.exe" -ArgumentList "C:\Path\To\Project\ProjectName.uproject -play -ExecCmds=\"Playspace\"" -WindowStyle Normal
```

## 最佳实践

- ✅ **先检查并结束旧实例**：每次启动前先 `Stop-Process -Force` 已运行的 `UnrealEditor` 进程
- ✅ **源码构建版本创建 `InstalledBuild.txt`**：避免重复构建引擎，大幅提速
- ✅ **使用 `Start-Process` 异步启动**：避免 PowerShell 阻塞与卡死
- ✅ **分离启动与构建流程**：先检查→结束→构建（如需要）→启动，分步执行
- ✅ **记录完整路径**：避免相对路径导致的找不到文件问题

- ❌ **不要直接调用 `.exe` 而不检查路径**：路径错误会导致启动失败
- ❌ **不要在 PowerShell 中直接运行 `.exe`**：会阻塞当前会话，改用 `Start-Process`
- ❌ **不要跳过结束实例步骤**：DLL 占用会导致重建失败

## 相关技能

- `ue5-performance-optimization` — 编辑器启动后的性能剖析与优化

## 常见问题

**Q: 为什么需要创建 `InstalledBuild.txt`？**  
A: 源码构建版本默认会把引擎源码列为项目依赖，每次构建项目都会重新编译引擎。创建 `InstalledBuild.txt` 后，引擎被视为"已安装版本"，构建时只构建项目代码，不重新编译引擎，节省大量时间。

**Q: 编辑器仍卡死怎么办？**  
A: 1) 检查是否有残留进程：`Get-Process | Where-Object { $_.ProcessName -like "*Unreal*" }`；2) 强制结束所有 `UnrealEditor` 进程；3) 检查是否被杀毒软件锁定；4) 以管理员身份运行 PowerShell。

**Q: DLL 被占用如何处理？**  
A: 通常是编辑器未完全退出导致。先结束所有相关进程：`Stop-Process -Name "UnrealEditor" -Force; Stop-Process -Name "UnrealEditor-Cmd" -Force`，等待 5 秒后再重试。

## 限制和注意事项

- 需要管理员权限执行 `Stop-Process -Force`
- 路径中的空格需要用引号包裹
- 源码构建版本需要预先配置好 `InstalledBuild.txt`，否则每次构建都会很慢
- Windows 平台特性：PowerShell 的 `Start-Process` 可避免阻塞，Linux/macOS 需改用 `&` 或 `nohup`
