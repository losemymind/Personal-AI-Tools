# UE5.6 性能剖析工具箱（profiling-toolkit）

本文件是「剖析定位」阶段的查表依据：命令、工具与采集方法。**具体分类与 cvar 随 UE 版本变化，以目标 5.6 构建的实际输出为准。**

## 快速分流：`stat` 命令

在游戏中按 `~` 打开控制台输入，或用 `-ExecCmds="stat unit"` 启动。

| 命令 | 作用 |
|---|---|
| `stat unit` | 帧时间拆解：**Frame**（总）/ **Game**（Game Thread）/ **Draw**（Render Thread）/ **GPU** |
| `stat unitgraph` | 上述指标随时间曲线，用于看卡顿尖峰 |
| `stat fps` | 仅显示 FPS |
| `stat game` | Game Thread 细分（Tick、蓝图、物理、动画、GC…） |
| `stat gpu` | GPU pass 成本概览（按 pass 排序） |
| `stat scenerendering` | 渲染线程统计与 draw call 数 |
| `stat renderthread` / `stat rhi` | 渲染线程 / RHI 线程细分 |
| `stat memory` | 进程内存分类（物理、UObject、渲染资源等） |
| `stat streaming` | 纹理流送池状态 |
| `stat anim` / `stat physics` / `stat particles` | 动画 / 物理 / 粒子成本 |
| `stat uobjects` | UObject 数量与分类 |
| `stat slate` / `stat umg` | UI（Slate/UMG）成本 |
| `stat dumphitches` | 打印已记录的 hitch 事件 |

> 判定口诀：`stat unit` 里 Frame ≈ max(Game, Draw, GPU) + 同步开销。谁最大就是主要限制；Game 与 GPU 接近时留意同步/等待。

## 深度采集：Unreal Insights

Unreal Insights 是 CPU/GPU/内存/加载的主剖析工具。

**启动采集**（示例，通道按需增删）：

```text
# 启动参数
-trace=cpu,gpu,frame,memory,bookmark,loading,file,asset

# 或运行时控制台
Trace.Start
Trace.Stop
```

采集产物为 `.utrace`，用 Unreal Insights（引擎自带 `UnrealInsights`）打开：

- **Timing Insights**：逐帧 → 线程 → Scope。定位超预算帧的责任 Scope 与系统。
- **CPU 限制**：看 Game Thread / Render Thread 各 Scope 占比与调用栈。
- **GPU 限制**：看 GPU 轨道各 pass（BasePass、Lumen、Shadow、PostProcess 等）。
- **Memory Insights**：内存随时间与调用栈的分配/释放，定位峰值与泄漏。
- **Loading Insights**：地图加载、流送、资产请求的阶段耗时。

用 **Bookmark**（`TRACE_BOOKMARK` / `Trace.Bookmark`）对齐关键事件（关卡流送、Boss 战、菜单切换）与 Trace 时间轴。

## 其他采集手段

| 工具 / 命令 | 用途 |
|---|---|
| `stat startfile` / `stat stopfile` | 生成 `.uestats`，在 Session Frontend 的 Profiler 中查看 CPU 采样 |
| CSV Profiler（`-csvCaptureFrames=N` 等） | 逐帧导出指标为 CSV，便于脚本化对比与回归 |
| `-memreport -full` 或 `MemReport -full` | 生成内存报告（UObject、资源、分配器分类） |
| `profilegpu` | 触发单帧 GPU 抓帧，输出各 pass 耗时 |
| `-game -windowed -resx= -resy=` + `-benchmark` | 可复现的基准运行（避开 Editor 开销） |
| `-deterministic` / 固定随机种子 | 保证场景可复现 |
| 平台抓帧器（PIX / RenderDoc / Xcode GPU / Mali/Adreno 工具） | 平台侧 GPU 深度分析，结论需注明采集条件 |

## 采集纪律

- 每次 Capture 关联：构建 ID、UE 版本、设备与驱动、画质档位、分辨率/帧率上限、场景与复现步骤、启用的 trace 通道。
- 区分 **Editor / PIE / Development / Test / Shipping** 的数据，不得混写。
- 区分**冷启动 / 热启动 / 首次缓存 / 稳态**：首次运行的 Shader/PSO 编译成本与稳态帧率是两回事。
- 短场景需预热与多次重复；长时问题记录持续时间、阶段与资源变化。
- 结论必须可追溯到原始 Capture/日志与时间范围，不能只给截图或主观感受。
- 不把**均值**单独作为卡顿/尾延迟结论——看高分位与超预算频率。

## 常见症状 → 责任域速查

| 症状 | 可能责任域 | 下一步 |
|---|---|---|
| Game Thread 高 | Tick/蓝图、GC、物理、动画、AI、UI | `stat game` → Unreal Insights CPU 轨道 |
| Draw / Render Thread 高 | Draw Call 数、材质、动态阴影、半透明、粒子 | `stat scenerendering` → GPU/渲染轨道 |
| GPU 高 | Nanite/Lumen/VSM、后处理/TSR、分辨率、过度绘制 | `stat gpu` → GPU 轨道逐 pass |
| 周期性卡顿 | GC、流送、Shader/PSO 编译、同步加载 | `stat dumphitches` + Memory/Loading Insights |
| 内存/显存增长 | UObject 泄漏、资源常驻、流送池 | `stat memory` / `MemReport` / Memory Insights |
| 加载慢、首次交互卡 | Shader/PSO、资产请求、IO、关卡流送 | Loading Insights + Bookmark |
