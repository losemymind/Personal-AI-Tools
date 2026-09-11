# 质量标准与验证标准（Quality Bar）

基于 agentic-awesome-skills 的 `quality-bar.md` 适配。技能必须达到以下 **8 项质量检查** 才能视为合格。其中部分由 `scripts/validate_skills.py` 自动执行（标注「自动」），其余由**评审子代理**（`agents/reviewer.md`）评审。

## 8 项质量检查

### 1. 元数据完整性（自动）

`SKILL.md` 前置元数据必须是有效 YAML，并包含：

- `name`：kebab-case，与文件夹名完全一致（长度 ≤100）
- `description`：≤1024 字符（验证器上限 1024），**单行、无 `<`/`>` 占位符、触发场景优先 + 一句能力定位**，不写执行步骤/流程阶段摘要；`description` 是唯一无条件加载的触发面，须**自足**覆盖触发场景（触发面规律见 SKILL.md「读取规则」中的写作规律文档 §6）
- `risk`：`none` / `safe` / `critical` / `offensive` / `unknown` 之一
- `category`：推荐（验证器给出提示）
- `allowed-tools`：可选最小权限白名单（Claude 工具名；打包时按端映射，见阶段 9）
- 来源/作者/日期/版本（`source`/`source_repo`/`source_type`/`author`/`date_added`/`version`）**不进 frontmatter**，来源登记在技能库根的创建记录账本（见 SKILL.md「创建记录账本」），版本以 git 提交历史为准

### 2. 清晰的触发条件（自动）

技能必须有一个章节明确说明何时触发它。

- **良好**：「当用户要求调试 React 组件时使用」
- **不佳**：「此技能帮助你处理代码」

接受的标题：`## When to Use` / `## Use this skill when` / `## 何时使用此技能` 等。

### 3. 安全与风险分类（自动）

每个技能必须声明 `risk` 级别：

- 🟢 `none` — 纯文本/推理，无命令或变更
- 🔵 `safe` — 读取文件、运行非破坏性命令（多数指导类用此级）
- 🟠 `critical` — 修改状态、删除文件、推送生产环境
- 🔴 `offensive` — 渗透测试/红队，**必须**含「仅限授权使用」警告
- ⚪ `unknown` — 遗留/未分类，新技能应避免

### 4. 可复制粘贴的示例（自动）

至少有一个代码块或交互示例，用户（或代理）可以立即复制使用。

### 5. 明确的限制（自动）

已知边缘情况或技能**无法**做的事情列表，例如「在无 WSL 的 Windows 上不工作」。

### 6. 指令安全审查（命令/安装类内容；危险管道与明文密钥自动扫描）

技能包含命令示例、远程获取步骤、密钥或变更指导时，内容必须通过安全审查：

- 不得有 `curl ... | bash`、`wget ... | sh`、`irm ... | iex` 等危险管道
- 不得有内联令牌/密钥风格的命令示例
- 高风险但必要的命令使用 `<!-- security-allowlist: ... -->` 显式允许并附警告
- offensive 技能必须含「AUTHORIZED USE ONLY / 仅限授权使用」免责声明与强制用户确认门

### 7. 写作规律（评审子代理；读取见 `SKILL.md`「读取规则」中写作规律文档）

- **先失败后写（Iron Law）**：无技能状态的基线失败观察在写作之前
- **行为差门（RED→GREEN）**：基线不失败 → 技能不必要，不硬写；带技能跑必须消除基线失败
- **表述形式匹配失败类型**：禁止 vs 正面配方 vs REQUIRED 槽 vs 条件谓词，选错适得其反
- **纪律型技能防合理化**：借口表 / 红旗清单 / 封漏洞 / 字即神
- **跨技能引用不用 `@` 语法**（force-load 烧上下文），用显式 REQUIRED 标记

### 8. 渐进披露与引用纪律（自动查悬空 + 评审子代理查层级）

- references 只从 SKILL.md **一层深**引用，references 之间不互链成图
- 单文件 >100 行顶部加**目录**；超大文件（>10k 词）在 SKILL.md 引用处附 **grep 模式**
- 触发用例（`evals.json`/场景）随技能沉淀；入库前 secret 扫描 + 基线失败记录留存

## 验证器使用

```bash
# 标准模式（警告不阻断，有错误时退出码 1）
python scripts/validate_skills.py [--dir <skills目录>]

# 严格模式（警告即失败，适合 CI）
python scripts/validate_skills.py --strict
```

## 验证器检查项一览

- [x] frontmatter 有效 YAML 且为映射
- [x] `name` 存在、与文件夹名一致、为小写 kebab-case（`a-z0-9` 单连字符）且 ≤100 字符
- [x] `description` 存在、为字符串、未超长
- [x] `risk` 存在（标准模式缺失仅警告）且取值为合法级别
- [x] `category` 缺失仅提示（frontmatter 只认 name/description/risk/category）
- [x] 中英文「何时使用」章节存在
- [x] 中英文「示例」章节存在
- [x] 中英文「限制」章节存在
- [x] offensive 技能的安全免责声明（中英均可）
- [x] offensive 技能的强制用户确认门
- [x] 危险远程执行管道（`curl|sh`、`wget|bash`、`irm|iex`）与常见明文密钥扫描（`<!-- security-allowlist -->` 可豁免）
- [x] markdown 链接无悬空
- [x] 反引号路径引用（`references/x.md`、`scripts/x.py`、`indexes/upstream.db` 等）存在且可解析（代码块内的示例路径豁免；引用只在技能自身目录内解析，不借道 skill-creator）
- [x] `evals.json`（`evals/evals.json` 或技能根）存在时形状合法：可解析、含 `evals` 数组、每项有非空 `query` 与布尔 `should_trigger`；缺失仅提示（建议随技能发布，质量门槛第 8 项）
- [x] `references/*.md` 不互链成图：references 文件不得在反引号里指向**同目录兄弟 references 文件**（自引用与带 `references/` 前缀的普通引用不受影响；跨目录引用请经 SKILL.md「读取规则」导读）
- [x] 跳过隐藏目录、符号链接与 `examples/`（上游学习样本豁免）

## 支持级别

| 级别 | 徽章 | 含义 |
| :-- | :-- | :-- |
| **未验证** | — | 新建技能草稿，尚未检查 |
| **已验证** | ✅ | 通过全部自动检查（标准或严格模式） |
| **试运行验证** | ✨ | 在真实任务上运行过一次并符合预期（评审子代理确认） |

经验证 + 试运行通过的技能才可安装到客户端 / 提交到仓库。

## 维护者审计（可选）

需要对整个技能库做合规/可用性报告时，可回答：

- 哪些技能结构有效但仍需可用性清理？
- 哪些技能缺少示例或限制？
- 哪些技能有截断的描述或过高的警告数？