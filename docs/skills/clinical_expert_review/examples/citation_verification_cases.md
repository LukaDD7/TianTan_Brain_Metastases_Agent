# 引用溯源检查实际案例

## 案例1: RAG V2虚假章节引用检测

### 患者
- **患者ID**: 868183
- **病例**: 肺癌SMARCA4/STK11突变

### 问题引用
报告中出现引用：
```
[Local: Patient Medical Record, Section: 既往史]
[Local: Patient Medical Record, Section: 病理诊断]
[Local: Retrieved_Guideline_Snippets.md, Section: Patient Imaging Report]
```

### 溯源检查过程

#### 步骤1: 提取retrieved_docs
从baseline文件中读取实际检索到的文档：

```json
{
  "retrieved_docs": [
    {
      "source": "Immunotherapy_revolutionizing_brain_metastatic_cancer_treatment...",
      "content": "...免疫治疗相关内容..."
    },
    {
      "source": "ASCO_SNO_ASTRO_Brain_Metastases...",
      "content": "...ASCO指南相关内容..."
    },
    {
      "source": "NCCN_Central_Nervous_System_Cancers...",
      "content": "...NCCN指南相关内容..."
    }
  ]
}
```

#### 步骤2: 章节匹配验证

**引用1**: `[Local: Patient Medical Record, Section: 既往史]`
- 文件名匹配: ❌ "Patient Medical Record"不在retrieved_docs中
- 章节匹配: N/A
- **结果**: fail (0分)
- **说明**: "既往史"为患者输入数据，被错误标注为指南引用

**引用2**: `[Local: Patient Medical Record, Section: 病理诊断]`
- 文件名匹配: ❌ "Patient Medical Record"不在retrieved_docs中
- 章节匹配: N/A
- **结果**: fail (0分)
- **说明**: "病理诊断"为患者输入数据，被错误标注为指南引用

**引用3**: `[Local: Retrieved_Guideline_Snippets.md, Section: Patient Imaging Report]`
- 文件名匹配: ❌ "Retrieved_Guideline_Snippets.md"不在retrieved_docs中
- 章节匹配: N/A
- **结果**: fail (0分)
- **说明**: "Patient Imaging Report"章节在NCCN指南中不存在

#### 步骤3: 验证结果记录

```json
{
  "citation_verification": {
    "local": [
      {
        "citation": "[Local: Patient Medical Record, Section: 既往史]",
        "claim": "患者既往史信息",
        "result": "fail",
        "match_score": 0,
        "note": "章节为患者输入数据，非指南引用"
      },
      {
        "citation": "[Local: Patient Medical Record, Section: 病理诊断]",
        "claim": "病理诊断及免疫组化结果",
        "result": "fail",
        "match_score": 0,
        "note": "章节为患者输入数据，非指南引用"
      }
    ]
  }
}
```

### 发现的问题
1. **虚假章节引用**: "Patient Imaging Report"等章节在指南文档中不存在
2. **患者数据误标**: 患者输入数据被错误标注为指南引用
3. **系统性问题**: 多个患者出现同类问题

### 影响评估
- **CER**: +1个Major错误 (w=2.0)
- **MQR**: S_citation扣1分 (引用格式不规范)

---

## 案例2: 章节标题精确匹配

### 患者
- **患者ID**: 605525
- **病例**: 结肠癌KRAS G12V

### 正常引用
报告中出现引用：
```
[Guideline: CSCO结直肠癌诊疗指南, 2024]
[PubMed: PMID 39322625]
```

### 溯源检查过程

**引用1**: `[Guideline: CSCO结直肠癌诊疗指南, 2024]`
- 类型: Guideline引用
- 验证: CSCO指南真实存在，2024版为最新版本
- **结果**: pass (80分)

**引用2**: `[PubMed: PMID 39322625]`
- 类型: PubMed引用
- 验证步骤:
  1. 访问PubMed数据库
  2. 查询PMID 39322625
  3. 确认文章存在且标题/摘要支持报告声明
- **结果**: pass (100分)

### 验证结果

```json
{
  "citation_verification": {
    "pubmed": [
      {
        "citation": "[PubMed: PMID 39322625]",
        "claim": "MSS型结直肠癌免疫治疗证据",
        "result": "pass",
        "match_score": 100,
        "note": "PMID真实存在，摘要支持声称"
      }
    ],
    "guideline": [
      {
        "citation": "[Guideline: CSCO结直肠癌诊疗指南, 2024]",
        "claim": "结直肠癌治疗建议",
        "result": "pass",
        "match_score": 80,
        "note": "指南真实存在，为权威来源"
      }
    ]
  }
}
```

---

## 案例3: Web Search引用验证

### 患者
- **患者ID**: 747724
- **病例**: 乳腺癌HER2+脑转移

### Web引用示例
```
[Web: https://www.azpicentral.com/tagrisso/tagrisso.pdf, Accessed: 2026-04-09]
```

### 溯源检查过程

1. **URL格式检查**: 符合 `[Web: <URL>, Accessed: <日期>]` 格式 ✓
2. **可访问性**: URL可访问，但可能随时间失效
3. **内容验证**: 对比报告声明与网页内容

### 验证结果

```json
{
  "citation_verification": {
    "web": [
      {
        "citation": "[Web: https://www.azpicentral.com/tagrisso/tagrisso.pdf]",
        "claim": "奥希替尼剂量说明",
        "result": "partial",
        "match_score": 70,
        "note": "URL可访问，内容为药品说明书，但Web引用可追溯性弱于PubMed"
      }
    ]
  }
}
```

### 权重计算
- Web引用权重: 0.5（低于PubMed的1.0）
- 原因: Web链接可能失效，内容可能更新

---

## 常见虚假章节黑名单

根据实际审查经验，以下章节名在指南文档中**不存在**，出现即视为虚假引用：

1. `Patient Imaging Report`
2. `Patient History`
3. `Patient Pathology`
4. `Patient Medical Record`
5. `Clinical Presentation`
6. `Treatment History`

**正确处理**: 这些应标注为 `[Parametric Knowledge: 患者输入数据]` 或 `[Evidence: Insufficient]`

---

## 引用格式规范对比

| 引用类型 | 正确格式 | 错误格式 | 权重 |
|---------|---------|---------|------|
| PubMed | `[PubMed: PMID 12345678]` | `[1]` | 1.0 |
| Guideline | `[Guideline: NCCN NSCLC, 2024]` | `[Local: ..., Page X]` | 0.8 |
| Web | `[Web: https://..., Accessed: YYYY-MM-DD]` | `[Web: ...]` (无日期) | 0.5 |
| Local | `[Local: <file>, Section: <section>]` | `[Local: <file>, Page X]` | 0.8 |
| Parametric | `[Parametric Knowledge: <source>]` | 无标注 | 0.0 |
| Insufficient | `[Evidence: Insufficient]` | 无标注 | N/A |

---

## 审查数据来源示例

### 本次审查数据

**Set-1 Batch审查（2026-04-09）**

| 方法 | 患者数 | 输入目录 | 输出目录 |
|------|--------|---------|---------|
| RAG V2 | 9 | `baseline/set1_results_v2/rag/` | `analysis/reviews_rag_v2/` |
| Web Search | 9 | `baseline/set1_results_v2/websearch/` | `analysis/reviews_websearch/` |

**具体文件**: 
- RAG输入: `868183_baseline_results.json`, `640880_baseline_results.json`, ...
- Web Search输入: `868183_baseline_results.json`, `747724_baseline_results.json`, ...
- 审查输出: `work_<patient_id>/review_results.json`

### 度量计算示例

**患者868183 (RAG V2)**:
```
CCR = (3 + 3 + 2 + 3 + 2) / 5 = 2.6
MQR = (4 + 4 + 4 + 2 + 2) / 5 = 3.2
CER = (2×2 + 1×1) / 15 = 0.333  [2个Major错误，1个Minor错误]
PTR = (2×1.0 + 12×0.0) / 32 = 0.0625 ≈ 0.240  [2处Local引用，12处Parametric]
CPI = 0.35×(2.6/4) + 0.25×0.24 + 0.25×(3.2/4) + 0.15×(1-0.333) = 0.625
```
