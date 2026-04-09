# Clinical Expert Review SKILL

## 简介

本SKILL用于对AI生成的医疗MDT（多学科诊疗）报告进行临床专家级审查，提供标准化的6-phase审查协议，评估报告的临床一致性、质量、错误率和物理可追溯性。

## 核心功能

### 1. 6-Phase审查协议

| Phase | 名称 | 描述 |
|-------|------|------|
| Phase 1 | Patient Context Analysis | 患者上下文分析 |
| Phase 2 | Citation Verification | 引用溯源验证 |
| Phase 3 | CCR | 临床一致性率评估 |
| Phase 4 | MQR | MDT报告质量率评估 |
| Phase 5 | CER | 临床错误率评估 |
| Phase 6 | PTR | 物理可追溯率评估 |

### 2. 量化指标计算规范

**重要**: 所有分数必须来源于专家审查打分，详见 `QUANTITATIVE_METRICS_GUIDE.md`。

#### 分数来源声明
| 指标 | 来源 | 说明 |
|------|------|------|
| CCR | 专家打分 | s_line, s_scheme, s_dose, s_reject, s_align (0-4分) |
| MQR | 专家打分 | s_complete, s_applicable, s_format, s_citation, s_uncertainty (0-4分) |
| CER | 专家分级 | Critical/Major/Minor错误识别及权重分配 |
| PTR | 专家统计 | PubMed/Guideline/Web/Local引用数量统计 |

**严禁**: 使用自动化工具生成分数，所有分数必须经专家审查后手动录入。

#### 计算公式
```
CPI = 0.35×(CCR/4) + 0.25×PTR + 0.25×(MQR/4) + 0.15×(1-CER)
```

**权重说明**:
- CCR: 35% (临床决策一致性最重要)
- PTR: 25% (证据可靠性)
- MQR: 25% (报告质量)
- CER: 15% (错误惩罚)

#### 计算流程
1. **专家打分录入**: 创建 `expert_scores.json`
2. **自动化计算**: 使用 `calculate_metrics.py` 脚本
3. **结果验证**: 核对计算结果与手工计算
4. **生成报告**: 提取最终结果，生成人类可读报告

详细计算规范见: `QUANTITATIVE_METRICS_GUIDE.md`

#### CPI (Composite Performance Index)
综合性能指数，范围0-1，计算公式：
```
CPI = 0.35×(CCR/4) + 0.25×PTR + 0.25×(MQR/4) + 0.15×(1-CER)
```

#### CCR (Clinical Consistency Rate)
临床一致性率，评估维度：
- S_line: 治疗线判定准确性
- S_scheme: 首选方案选择合理性
- S_dose: 剂量参数准确性
- S_reject: 排他性论证充分性
- S_align: 临床路径一致性

#### MQR (MDT Quality Rate)
MDT报告质量率，评估维度：
- S_complete: 8模块完整性
- S_applicable: 模块适用性判断
- S_format: 结构化程度
- S_citation: 引用格式规范性
- S_uncertainty: 不确定性处理

#### CER (Clinical Error Rate)
临床错误率，分级：
- Critical (w=3.0): 可能危及生命
- Major (w=2.0): 显著影响治疗效果
- Minor (w=1.0): 轻微影响治疗质量

#### PTR (Physical Traceability Rate)
物理可追溯率，引用权重：
- PubMed: 1.0
- Guideline: 0.8
- Local: 0.8
- Web: 0.5
- Parametric: 0.0
- Insufficient: 0.0

### 3. 引用溯源验证

#### 验证步骤
1. 提取报告中的所有引用
2. 获取原始检索文档（retrieved_docs）
3. 章节匹配验证
4. 计算match_score
5. 记录验证结果

#### 常见虚假章节黑名单
- Patient Imaging Report
- Patient History
- Patient Pathology
- Patient Medical Record
- Clinical Presentation
- Treatment History

## 文件结构

```
clinical_expert_review/
├── SKILL.md                          # 主文档（规范流程SOP）
├── metadata.json                     # Skill元数据
└── examples/
    ├── citation_verification_cases.md    # 引用验证实际案例
    └── review_results_example.json       # 审查结果JSON示例
```

## 命名规范

### 目录结构
```
analysis/
├── reviews_<method>_<version>/
│   ├── work_<patient_id>/
│   │   ├── review_results.json
│   │   └── clinical_expert_review_report.md
│   └── SUMMARY_REPORT.md
└── COMPARISON_REPORT.md
```

### 命名规则
- 审查工作目录: `reviews_<method>_<version>/`
  - 例: `reviews_rag_v2`, `reviews_websearch_v1`
- 单个患者目录: `work_<patient_id>/`
  - 例: `work_605525`, `work_868183`
- 结果文件: `review_results.json`
- 报告文件: `clinical_expert_review_report.md`
- 汇总文件: `SUMMARY_REPORT.md`
- 对比文件: `COMPARISON_REPORT.md`

## 使用示例

### 执行审查

```python
# 1. 读取baseline文件
baseline_file = f"baseline/set1_results_v2/rag/{patient_id}_baseline_results.json"
with open(baseline_file) as f:
    data = json.load(f)
    retrieved_docs = data["results"]["rag"]["retrieved_docs"]
    report_content = data["results"]["rag"]["report"]

# 2. 执行6-phase审查
review_result = clinical_expert_review(
    patient_id=patient_id,
    baseline_data=data,
    method="RAG V2"
)

# 3. 输出结果
output_path = f"analysis/reviews_rag_v2/work_{patient_id}/review_results.json"
with open(output_path, "w") as f:
    json.dump(review_result, f, indent=2)
```

### 引用溯源验证

```python
# 提取引用
citations = extract_citations(report_content)

# 验证每个引用
for citation in citations:
    if citation["type"] == "Local":
        # 检查文件名是否在retrieved_docs中
        filename_match = citation["file"] in [doc["source"] for doc in retrieved_docs]
        
        if filename_match:
            # 检查章节是否存在于文档内容中
            doc_content = get_doc_content(retrieved_docs, citation["file"])
            section_match = citation["section"] in doc_content
            
            if section_match:
                citation["result"] = "pass"
                citation["match_score"] = 85
            else:
                citation["result"] = "fail"
                citation["match_score"] = 0
                citation["note"] = "章节在检索文档中不存在"
        else:
            citation["result"] = "fail"
            citation["match_score"] = 0
            citation["note"] = "文件名不在检索文档列表中"
```

## 实际应用案例

### Set-1 Batch审查（2026-04-09）

**审查对象**: 9例患者MDT报告  
**Baseline方法**: RAG V2 vs Web Search V2  
**计算方法**: 标准化Python脚本 (calculate_final_metrics.py)

**结果对比**:

| 指标 | RAG V2 (Mean±SD) | Web Search V2 (Mean±SD) | 提升 |
|------|-----------------|------------------------|------|
| **CPI** | 0.616±0.047 | 0.729±0.027 | +18.3% |
| **CCR** | 2.867±0.231 | 3.133±0.189 | +9.3% |
| **MQR** | 3.467±0.231 | 3.511±0.099 | +1.3% |
| **CER** | 0.222±0.083 | 0.074±0.021 | -66.7% |
| **PTR** | 0.128±0.061 | 0.386±0.025 | +201.6% |

**关键发现**:
- RAG V2存在虚假章节引用问题（如Patient Imaging Report）
- Web Search的PubMed引用丰富，可追溯性强
- Parametric Knowledge过度使用是RAG V2的主要问题

**审查文件位置**:
- RAG V2审查: `analysis/reviews_rag_v2/work_<patient_id>/review_results.json`
- Web Search V2审查: `analysis/reviews_websearch_v2/work_<patient_id>/review_results.json`
- 最终报告: `analysis/FINAL_REVIEW_REPORT.md`
- 详细计算: `analysis/DETAILED_CALCULATIONS.md`

详见 `examples/citation_verification_cases.md`

## 数据来源说明

在每次审查报告中，必须明确标注：

### 输入数据
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

## 贡献与改进

欢迎通过以下方式改进本SKILL：
1. 添加更多引用验证案例
2. 完善度量计算规则
3. 优化虚假章节检测
4. 扩展支持的引用格式

## 版本历史

- v1.0.0 (2026-04-09): 初始版本，支持6-phase审查协议，完成Set-1 Batch审查

---

**维护者**: Claude Code
**最后更新**: 2026-04-09
