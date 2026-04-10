# Tools 目录索引

**位置**: `/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/tools/`

本目录包含项目开发和评估阶段的专用工具，供 Claude Code 使用（非BM Agent运行时组件）。

---

## 工具清单

| 工具 | 目录 | 用途 | 使用阶段 |
|------|------|------|---------|
| **Patient Data Processor** | `patient_data_processor/` | 患者数据清洗与输入文件生成 | 测试准备阶段 |
| **Clinical Expert Review** | `clinical_expert_review/` | MDT报告专家审查与量化评估 | 结果评估阶段 |

---

## 1. Patient Data Processor

**用途**: 将原始临床数据（Excel）转换为BM Agent标准化输入格式

**核心功能**:
- 双层数据隔离检查（字段级白名单 + 语义级审查）
- 自动移除Ground Truth标签（入院诊断、出院诊断等）
- 生成符合BM Agent输入标准的文本文件

**快速使用**:
```bash
# 批量处理Set-1患者
cd /media/luzhenyang/project/TianTan_Brain_Metastases_Agent
python tools/patient_data_processor/scripts/generate_set1.py

# 验证文件是否污染
python tools/patient_data_processor/scripts/clean_contaminated_files.py --preview
```

**详细文档**: [patient_data_processor/README.md](./patient_data_processor/README.md)

---

## 2. Clinical Expert Review

**用途**: 模拟临床专家审查BM Agent生成的MDT报告，输出CCR/MQR/CER/PTR/CPI量化指标

**核心功能**:
- **患者情境分析**: 提取关键临床信息，标注confirmed/inferred/unknown
- **引用溯源验证**: 
  - 本地指南: 读取MD文件验证
  - PubMed: API检索验证PMID内容
  - OncoKB: API验证突变注释
- **临床一致性评审 (CCR)**: 5维度评分
- **报告质量评审 (MQR)**: 5维度评分
- **错误审查 (CER)**: 分级错误识别

**快速使用**:
```bash
# 审查单个患者
python tools/clinical_expert_review/scripts/review_single.py \
    --patient-id 605525 \
    --report analysis/samples/605525/MDT_Report_605525.md

# 批量审查
python tools/clinical_expert_review/scripts/review_batch.py \
    --patient-list 605525,612908,638114
```

**详细文档**: [clinical_expert_review/SKILL.md](./clinical_expert_review/SKILL.md)

---

## 使用流程

```
原始数据
    ↓
[Patient Data Processor] → 生成 patient_{id}_input.txt
    ↓
运行BM Agent → 生成MDT_Report_{id}.md
    ↓
[Clinical Expert Review] → 输出CCR/MQR/CER/PTR/CPI
    ↓
论文结果
```

---

## 相关路径速查

| 数据类型 | 路径 |
|---------|------|
| Set-1患者输入 | `patient_input/Set-1/patient_{id}_input.txt` |
| BM Agent报告 | `analysis/samples/{id}/MDT_Report_{id}.md` |
| 本地指南 | `workspace/sandbox/Guidelines/` |
| 审查报告输出 | `analysis/reviews/` |

---

**更新日期**: 2026-04-07
