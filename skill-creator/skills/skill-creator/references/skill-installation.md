# 多客户端打包与自安装

只在用户要求打包、安装或更新指定技能时读取。遵循用户已给出的客户端、作用域和路径；缺少关键落点时再询问。安装到用户指定范围，不默认扩展到全部客户端。

## 打包

```bash
python scripts/skill_package.py <技能目录> --client claude --client opencode \
  --out <产物目录> --zip
```

--client 可重复，支持 claude/opencode/codex/deepseek。产物为 <产物目录>/<客户端>/<技能名>/，--zip 另生成压缩包。输出目录不能位于源技能内。

打包器适配 frontmatter 并逐端 post-check，排除缓存/VCS；可选 allowed-tools 在 Claude 规范为逗号串，在 OpenCode 映射为逐工具 permission（白名单 allow、其余 deny，已有显式设置优先），Codex/DeepSeek 透传。不把全局 permission 字符串误当成受限白名单。旧 tools 字段只作兼容输入。

打包通过证明目录与字段符合工具检查，不证明目标客户端实际加载或权限隔离；安装后仍要验证。

## 自安装

1. 从技能列表或用户路径定位源目录；已有技能直接更新同一源，避免产生第二套开发文件。
2. 沿用已确定的客户端与作用域。工作区安装以目标项目根为基准，全局安装使用目标客户端的用户技能目录。
3. 用打包产物放置；若按客户端约定直接复制，保持目录完整并排除缓存。更新前备份已有安装，避免合并后遗留废弃文件；安装失败恢复备份。
4. 对带本技能验证器的安装副本运行自检；含索引时检查来源与状态：

```bash
python scripts/skill_validate.py --strict --dir .
python scripts/skill_index_search.py --stats
```

5. 使用客户端的刷新/重启方式重新发现技能，再用真实小任务确认加载；报告确切安装路径与已完成的检查。未运行真实任务时明确说明。

## 常用落点

| 客户端 | 用户级 | 工作区级 |
|---|---|---|
| Claude Code | ~/.claude/skills/<name>/ | <项目根>/.claude/skills/<name>/ |
| OpenCode | ~/.config/opencode/skills/<name>/ | <项目根>/.opencode/skills/<name>/ |
| Codex | ~/.agents/skills/<name>/ | <项目根>/.agents/skills/<name>/ |
| DeepSeek | 由承载它的客户端确定 | 由承载它的客户端确定 |

客户端可能配置了额外发现目录或兼容路径，以实际技能列表与目标版本的发现规则为准。同名技能重复安装时先识别来源，不覆盖客户端内置技能；安装通用 skill-creator 时尤其要区分同名的系统技能。

## 交付与发布边界

技能的脚本依赖 Python 3.10+ 与 PyYAML，先检查环境；纯复制不安装依赖。入库时按宿主的分类、来源台账与审计规则执行，保存 evals 与已完成验证；仅靠安装副本的 strict 检查不能声称真实任务已通过。提交、推送与发布仍需要对应授权。
