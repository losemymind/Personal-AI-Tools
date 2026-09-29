# 修复缺陷分诊代理

inputs/bug-triager/AGENT.md 是待修草稿。请保留名称 bug-triager，修成中文 subagent：只读缺陷记录，根据证据判断严重性、影响、需补信息和交还给谁；不得修改代码、执行修复、联网或派发任务。

规范源文件写 outputs/bug-triager/AGENT.md（目录形态），保留并正确引用同目录 references/report-format.md。tools 只允许 read/grep/glob；permission 默认拒绝并放行三种读取工具。移除版本、tags、tools_clients、来源元数据；color 是带引号的 #2563EB。

正文与权限一致，职责有必须做/拒绝做，有升级路径和可验收完成标准。遵守既定汇报格式；数据不够明确就记 unknown，不能虚构根因。修复模型有写 outputs 的授权，生成角色仍必须只读。

同时提供 OpenCode 与 Claude 的可分发包，放 outputs/packages/<client>/bug-triager/，每包包含 AGENT.md 与 references/report-format.md。OpenCode 的规范工具数组要转 permission 对象；Claude 用 Read, Grep, Glob 工具串。所有路径引用要在包内可解析。

不要安装到真实用户目录、不要修改 inputs。只用本地材料。输出 outputs/verification.json，如实区分实际执行的校验、未执行的客户端原生加载与评审方式；不能把自评写成独立审核。若环境缺工具可以直接完成文件并如实记录限制。
