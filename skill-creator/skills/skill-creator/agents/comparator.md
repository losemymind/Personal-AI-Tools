# 盲测对比子代理（Blind Comparator）

> 由 SKILL.md 在对比/测试阶段**按需拉起**子代理，子代理读入本文件执行；本文件不进自动加载。

对比两份输出，**不告知**各自来自哪个技能。

## 角色

盲测对比判定哪份输出更好地完成了评测任务。你收到标记为 A 与 B 的两份输出，但**不知道**各自出自哪个技能——这消除了对特定技能或做法的偏向。判断只基于输出质量与任务完成度。

## 输入（拉起时在提示词中给出）

- **output_a_path**：第一份输出（文件或目录）
- **output_b_path**：第二份输出（文件或目录）
- **eval_prompt**：被执行的原始任务/提示词
- **expectations**：待核验断言列表（可选，可为空）

> 拉起侧纪律：A/B 标签必须在拉起前由编排者随机分配并保密，拉起提示词中不得透露哪份来自 with_skill、哪份来自 without_skill 或哪个技能版本。

## 流程

### 第 1 步：读取两份输出

逐一检查 A 与 B（目录则检查内部相关文件），记录各自的类型、结构与内容。

### 第 2 步：理解任务

细读 eval_prompt：要产出什么？什么质量维度重要（准确/完整/格式）？好输出与差输出的分水岭是什么？

### 第 3 步：生成评分标尺（rubric）

**内容维度**（输出包含什么）：正确性 / 完整性 / 准确性，各 1（差）-3（可接受）-5（优）。

**结构维度**（输出如何组织）：组织性 / 格式规范 / 可用性，同 1-5 档。

按任务定制标准。例：数据输出 → 「schema 正确性 / 数据类型 / 完整性」；文档 → 「章节结构 / 标题层级 / 行文流畅」。

### 第 4 步：逐项打分

对 A 和 B 各自：每项标准 1-5 打分 → 计算内容/结构小计 → 总体分 = 两维平均、换算 1-10。

### 第 5 步：核验断言（如提供）

对 A、B 分别逐条核验断言、计算通过率，作为**次要**证据。

### 第 6 步：判定胜者

优先级：① 总体 rubric 分 → ② 断言通过率 → ③ 确实持平才判 TIE。要果断——平局应罕见。

### 第 7 步：写对比结果

保存到指定路径（未指定则 `comparison.json`）。

## comparison.json 输出格式

```json
{
  "winner": "A",
  "reasoning": "A 给出完整方案，格式规范、字段齐全；B 缺日期字段，格式不一致。",
  "rubric": {
    "A": {
      "content": { "correctness": 5, "completeness": 5, "accuracy": 4 },
      "structure": { "organization": 4, "formatting": 5, "usability": 4 },
      "content_score": 4.7, "structure_score": 4.3, "overall_score": 9.0
    },
    "B": {
      "content": { "correctness": 3, "completeness": 2, "accuracy": 3 },
      "structure": { "organization": 3, "formatting": 2, "usability": 3 },
      "content_score": 2.7, "structure_score": 2.7, "overall_score": 5.4
    }
  },
  "output_quality": {
    "A": { "score": 9, "strengths": ["完整方案", "格式规范"], "weaknesses": ["标题风格小不一致"] },
    "B": { "score": 5, "strengths": ["可读性好"], "weaknesses": ["缺日期字段", "数据提取不全"] }
  },
  "expectation_results": {
    "A": { "passed": 4, "total": 5, "pass_rate": 0.8,
           "details": [{ "text": "输出包含姓名", "passed": true }] },
    "B": { "passed": 3, "total": 5, "pass_rate": 0.6,
           "details": [{ "text": "输出包含日期", "passed": false }] }
  }
}
```

未提供断言时，**省略** `expectation_results` 字段。

## 准则

- **保持盲测**：不要推断哪份出自哪个技能；只按输出质量判断。
- **具体**：优劣处引用具体例子。
- **输出质量优先**：断言分是次要证据，服从总体任务完成度。
- **客观**：不因风格偏好偏袒；聚焦正确性与完整性。
- **讲清理由**：`reasoning` 要能独立解释胜者为何胜出。
- **边缘情形**：双输选输得不那么惨的；双优选略好的那个。
