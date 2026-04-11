# Clinical Expert Review SKILL

## 概述

本SKILL用于对AI生成的MDT（多学科诊疗）报告进行临床专家级审查，评估其临床一致性、报告质量、错误率和物理可追溯性。

## 审查协议（6-Phase Protocol）

【专家级审查铁律 (Expert Review Directives)】

严禁外貌协会：不得因报告排版美观、使用了表格或 Markdown 特效而提高 MQR 评分。质量评估必须且仅基于医疗逻辑的完整性与证据的硬核程度。

对未经物理验证的数字保持零容忍：在评估 S_dose 和 S_scheme 时，如果对应的治疗剂量或参数没有紧跟 [Local...] 或 [PubMed...] 等确凿的循证锚点，必须将其视为“潜在幻觉”，对应的评分不得高于 2/4。

医疗信源洁癖：任何将普通互联网资讯站点（如百度、好大夫在线等非同行评议平台）作为临床推荐依据的行为，必须在 Phase 5 (CER) 中直接判定为 Major Error 或 Critical Error。

### Phase 1: Patient Context Analysis（患者上下文分析）
- 提取患者基本信息、肿瘤类型、分期、治疗史
- 识别关键临床决策点

### Phase 2: Citation Verification（引用验证）
- 验证所有临床声明的引用来源
- 检查引用格式规范性
- **关键**: 追溯引用到原始检索文档

### Phase 3: CCR - Clinical Consistency Rate（临床一致性率）
评估维度（0-4分）：
- **S_line**: 治疗线判定准确性
- **S_scheme**: 首选方案选择合理性
- **S_dose**: 剂量参数准确性
- **S_reject**: 排他性论证充分性
- **S_align**: 临床路径一致性

### Phase 4: MQR - MDT Quality Rate（MDT报告质量率）
评估维度（0-4分）：
- **S_complete**: 8模块完整性
- **S_applicable**: 模块适用性判断
- **S_format**: 结构化程度
- **S_citation**: 引用格式规范性
- **S_uncertainty**: 不确定性处理

### Phase 5: CER - Clinical Error Rate（临床错误率）
- **Critical错误** (w=3.0): 可能危及生命
- **Major错误** (w=2.0): 显著影响治疗效果
- **Minor错误** (w=1.0): 轻微影响治疗质量
- 公式: CER = min((Σ w_j × n_j) / 15, 1.0)

### Phase 6: PTR - Physical Traceability Rate（物理可追溯率）
- **Tier 1 (权威物理溯源 - 权重 1.0)：** [PubMed: PMID XXXXX] | [OncoKB: XXX] (精准肿瘤学数据库) | [Local: <文件名>, Section: <章节>] (本地挂载的官方指南文件，必须精确定位)
- **Tier 2 (不可验证的泛指南 - 权重 0.3)：** [Guideline: XXX] (没有提供物理路径或精确章节的开放域指南声明，给予极低权重以惩罚未溯源行为)
- **Tier 3 (开放网络链接 - 权重 -0.5 到 0.1)：** [Web: 权威机构/官方说明书] (如 FDA, NMPA, 药企官网说明书 PDF)：权重 0.1 | [Web: 商业健康资讯/论坛] (如 Baidu Health, Haodf, 微信公众号)：权重 -0.5（倒扣分，因为引入了严重的医疗合规风险）
- **无效证据 (权重 0.0)：** Parametric Knowledge | Insufficient。
- 公式: PTR = Σ(各类型引用数×权重) / 总声明数

## CPI计算

```
CPI = 0.35×(CCR/4) + 0.25×PTR + 0.25×(MQR/4) + 0.15×(1-CER)
```

权重分配说明:
- CCR: 35%（临床决策最重要）
- PTR: 25%（证据可靠性）
- MQR: 25%（报告质量）
- CER: 15%（错误惩罚）

## 引用溯源检查SOP

### 步骤1: 提取报告中的所有引用
扫描报告，识别以下格式引用：
- `[PubMed: PMID XXXXXXXX]`
- `[OncoKB: XXXXXXXX]`  <-- 【一定要补上这行】
- `[Guideline: XXX Guidelines, YYYY]`
- `[Local: <文件名>, Section: <章节>]`
- `[Web: <URL>, Accessed: YYYY-MM-DD]`
- `[Parametric Knowledge: ...]`
- `[Evidence: Insufficient]`
- `[ClinicalTrial: NCTXXXXXXXX]`

### 步骤2: 获取原始检索文档
对于RAG报告：
- 读取baseline JSON文件中的`retrieved_docs`数组
- 记录每个文档的`source`和`content`

对于Web Search报告：
- 检查`full_output`中的`search_sources`
- 验证搜索调用记录

### 步骤3: 章节匹配验证
对于`[Local: <文件>, Section: <章节>]`引用：

1. **文件名匹配**
   - 检查引用文件名是否在retrieved_docs的source中
   - 匹配成功 → 继续章节验证
   - 匹配失败 → 标记为fail (0分)

2. **章节标题匹配**
   - 在匹配的文档content中搜索章节标题
   - 使用精确匹配或模糊匹配（相似度>80%）
   - 找到 → pass (80-100分)
   - 未找到 → fail (0分)

3. **特殊情况处理**
   - "Patient Imaging Report"等章节 → 必为虚假引用（实际不存在于指南文档）
   - "既往史"、"病理诊断"等 → 必为患者输入数据（非指南引用）

4. **针对 [Guideline: XXX] 泛引用的强制降级：**
如果智能体仅输出了指南名称而未使用 [Local: ...] 挂载物理文件并定位章节，裁判模型不得将其判定为有效指南引用（不能给 0.8），必须将其降级为 Tier 2 (0.3分)，并记录在 Note 中：“未提供可追溯的物理文件与章节证据”。

### 步骤4: 计算match_score

```python
if section_found_in_content:
    match_score = 80 + min(exact_match_bonus, 20)  # 80-100分
elif filename_matches:
    match_score = 50  # partial，仅文件名匹配
else:
    match_score = 0   # fail
```

### 步骤5: 记录验证结果

```json
{
  "citation": "[Local: Provided_Guideline_Snippets.md, Section: DIAGNOSIS]",
  "claim": "具体临床声明",
  "result": "pass|partial|fail",
  "match_score": 85,
  "note": "章节在文档第X行找到"
}
```

## 输出文件命名规范

### 目录结构
```
analysis/
├── reviews_rag_v2/              # RAG V2审查结果
│   ├── work_<patient_id>/
│   │   ├── review_results.json
│   │   └── clinical_expert_review_report.md
│   └── SUMMARY_REPORT.md
├── reviews_websearch/           # Web Search审查结果
│   ├── work_<patient_id>/
│   │   ├── review_results.json
│   │   └── clinical_expert_review_report.md
│   └── SUMMARY_REPORT.md
└── COMPARISON_REPORT.md         # 对比分析报告
```

### 命名规则
1. **审查工作目录**: `reviews_<method>_<version>/`
   - 例: `reviews_rag_v2`, `reviews_websearch_v1`

2. **单个患者目录**: `work_<patient_id>/`
   - 例: `work_605525`, `work_868183`

3. **结果文件**: `review_results.json`
   - 结构化JSON，包含所有指标

4. **报告文件**: `clinical_expert_review_report.md`
   - 人类可读的审查报告

5. **汇总文件**: `SUMMARY_REPORT.md`
   - 同类型审查的汇总

6. **对比文件**: `COMPARISON_REPORT.md`
   - 不同类型间的对比分析

## 审查数据来源说明

在每次审查报告中，必须明确标注：

### 输入数据来源
```markdown
**输入数据**:
- Baseline方法: RAG V2 / WebSearch_LLM
- Baseline文件: `baseline/set1_results_v2/<method>/<patient_id>_baseline_results.json`
- 患者输入: `patient_input/Set-1/<patient_id>/patient_<patient_id>_input.txt`
```

### 输出位置
```markdown
**输出位置**:
- 审查结果: `analysis/reviews_<method>/work_<patient_id>/review_results.json`
- 审查报告: `analysis/reviews_<method>/work_<patient_id>/clinical_expert_review_report.md`
```

## 度量计算说明

在报告中，每个度量必须说明计算依据：

### CCR示例
```markdown
**CCR: 3.2/4.0**
- S_line: 4/4（治疗线判定准确，患者为二线治疗）
- S_scheme: 3/4（首选方案合理，但备选方案说明不足）
- S_dose: 3/4（剂量参数正确，缺乏具体计算依据）
- S_reject: 3/4（排他性论证基本充分）
- S_align: 3/4（临床路径基本一致）
```

### PTR示例
**PTR: 0.320**
- Tier 1 权威溯源 (PubMed/OncoKB/Local): 6处 × 1.0 = 6.0
- Tier 2 泛指南引用 (仅Guideline名称): 4处 × 0.3 = 1.2
- Tier 3 官方Web引用 (FDA等): 2处 × 0.1 = 0.2
- Tier 3 商业Web引用 (Baidu/Haodf等): 2处 × (-0.5) = -1.0
- 总引用得分: 6.4
- 总声明数: 20
- PTR = 6.4 / 20 = 0.320
（注：由于包含了商业健康网站，已在CER中追加Major Error惩罚）

### CER示例
```markdown
**CER: 0.133**
- Major错误: 0处 × 2.0 = 0
- Minor错误: 2处 × 1.0 = 2
- 总错误权重: 2
- CER = min(2/15, 1.0) = 0.133
```
