# UE5.6 实现层优化模式（optimization-patterns）

本文件是「阶段 5」的模式库：按定位到的责任域给出可落地的 UE5.6 优化手法。**每条都应先有证据再实施，一次只改一个变量，改完复测。** cvar/设置名以目标版本为准。

## 1. Tick 与蓝图

**问题**：大量 Actor 每帧 Tick、蓝图里做重活（查找、排序、字符串拼接、遍历）。

**做法**：
- 能不用 Tick 就不用：改用**事件驱动**（委托/Overlap/定时器）。
- 必须轮询时降低频率：`PrimaryActorTick.TickInterval = 0.1f;`（C++）或类默认值里设 Tick Interval。
- 远离玩家/不可见时关闭：`SetActorTickEnabled(false)`，或用 Tick Group、`bStartWithTickEnabled=false`。
- 用 `TickGroup` 把非关键 Tick 移出关键路径。
- 蓝图热路径下沉到 C++（UE5 无蓝图 nativization；热点逻辑用 C++ 实现）。
- 缓存引用：不要在 Tick 里 `GetAllActorsOfClass` / `FindComponentByClass` / 反复 `Cast`。

```cpp
// 只调整间隔，仍每帧逻辑判断
PrimaryActorTick.TickInterval = 0.25f;
```

## 2. GC 与内存分配

**问题**：周期性 GC 卡顿；每帧产生垃圾（FString/TArray/UObject）。

**做法**：
- **零分配热路径**：避免在 Tick 内 `NewObject`、`FString` 拼接、`TArray::Add` 反复增长；复用容器（`Reset()` 保留容量、`Reserve()` 预分配）。
- **对象池**：子弹、特效、UI 项等高频创建销毁对象改用池化。
- **弱引用/软引用**：`TWeakObjectPtr<>`、`TSoftObjectPtr<>` 减少强引用造成的常驻与 GC 压力；仅在使用时 `LoadSynchronous`/异步加载。
- **减少 UObject 数量**：能用 POD/`USTRUCT` 就不建 UObject。
- GC 调参（如 `gc.` 系列、`gc.TimeBetweenPurgingPendingKillObjects`）**需有证据、谨慎**，可能只是把卡顿挪走。
- 用 Memory Insights / `MemReport -full` 定位峰值与未释放资源。

## 3. Draw Call 与实例化

**问题**：对象数量多、材质变体多、静态网格未合并，导致 Render Thread/Draw Call 高。

**做法**：
- **实例化**：大量相同网格用 ISM/HISM（植被、场景道具）；Nanite 网格走 Nanite 路径。
- **合并**：可合并的静态网格合并；减少材质槽。
- **LOD 与剔除**：配置合理 LOD、距离剔除、视锥/遮挡剔除；远处用简化表示。
- **材质**：减少材质变体（Static Switch 爆炸）、控制指令数与纹理采样。
- 用 `stat scenerendering` 看 draw call 数与 render thread 时间。

## 4. GPU 与渲染可扩展性

**问题**：GPU 限制，Nanite/Lumen/VSM/后处理/TSR 成本高。

**做法**（先量化每项成本，再决定降级，并记录体验代价）：
- **分辨率**：`r.ScreenPercentage`、TSR 上采样设置；动态分辨率。
- **Lumen**：投影方法（硬件光追 vs 软件）、`r.Lumen.*` 质量档、反射质量。
- **虚拟阴影贴图（VSM）**：分辨率与页池；必要时回退传统阴影。
- **Nanite**：`r.Nanite` 开/关、Nanite 与传统路径的取舍。
- **后处理**：Bloom、DOF、SSR、运动模糊等逐项测成本；按画质档位配置。
- 用渲染可扩展性（Scalability）分组把档位收敛为「低/中/高/史诗」，而不是散落 cvar。
- 阈值判断前先 `stat gpu` 与 GPU 轨道确认瓶颈 pass，避免降错方向。

## 5. Niagara 与粒子

- 降低发射数与粒子片数；用 **Significance（显著性）** 按距离/可见性降级或剔除。
- 大量粒子用 GPU 粒子；避免每粒子单独材质。
- 关掉屏幕外特效；用固定边界与 LOD。

## 6. 异步与并行

- 重计算放 `AsyncTask(ENamedThreads::AnyBackgroundThreadNormalTask, ...)`、`ParallelFor`、TaskGraph。
- 资产用**异步加载**（`StreamableManager`/软引用），避免 Game Thread 同步 `LoadObject`。
- 流送（World Partition / Level Streaming）按需加载，管理流送源与预算。
- 注意线程安全：不要在 worker 线程直接改 UObject/Game Thread 状态。

## 7. 加载、Shader 与 PSO 卡顿

- **PSO 预缓存**：启用并维护 PSO 缓存，减少首次遇到材质/后处理时的编译卡顿。
- **Shader 编译**：预热关卡与材质（`ShaderPipelineCache`），避免运行中首编译卡顿；共享材质减少变体。
- **异步 IO**：避免 Game Thread 同步读盘；用异步加载与预加载。
- 用 Loading Insights 与 Bookmark 把卡顿对齐到具体加载阶段。

## 8. 优化对比记录模板

```text
Baseline Build：
Candidate Build：
唯一预期变量：
测试场景 / 设备 / 画质 / 分辨率：
重复次数与统计方法：
指标（Frame/Game/Draw/GPU/内存）：
基线结果：
候选结果：
绝对与相对变化：
副作用（画质/内存/其他线程/功能）：
结论：IMPROVED / REGRESSED / NO_CLEAR_CHANGE / INVALID_COMPARISON
```

## 反模式清单

- ❌ 未定位瓶颈就降画质/关系统（可能降错方向且牺牲体验）。
- ❌ 一次改多个变量后归因单项。
- ❌ 用 Editor/PIE 数据当 Shipping 结论。
- ❌ 只看平均帧率而忽略卡顿峰值与高分位。
- ❌ 在热路径里做分配、查找、日志字符串拼接。
- ❌ 事务性大批量重保存资产而不确认影响与恢复方式。
