# 患者输入数据批次说明

**批次名称**: Set-2，0402  
**生成日期**: 2026-04-02 ~ 2026-04-03  
**处理器版本**: Patient Data Processor v2.1.0  
**处理者**: Claude Code (LLM)

---

## 批次统计

| 统计项 | 数值 |
|--------|------|
| **源数据Case数** | 46 |
| **唯一住院号数** | 34 |
| **重复住院号** | 9个 |
| **生成总文件数** | 46 |
| **第一层移除字段** | 4个 |
| **第二层发现问题** | 0个 |

---

## 重复住院号详情

| 住院号 | 就诊次数 | 涉及Case |
|--------|---------|---------|
| 466104 | 4次 | Case12, Case13, Case35, Case36 |
| 638772 | 3次 | Case30, Case40, Case8 |
| 640880 | 2次 | Case1, Case43 |
| 650180 | 2次 | Case11, Case44 |
| 877371 | 2次 | Case15, Case9 |
| 715725 | 2次 | Case17, Case18 |
| 811840 | 2次 | Case22, Case41 |
| 648307 | 2次 | Case33, Case34 |
| 638114 | 2次 | Case38, Case39 |

---

## 文件命名规范

- `patient_{住院号}_input.txt` - 首次就诊
- `patient_{住院号}_V2_input.txt` - 第2次就诊（同一患者）
- `patient_{住院号}_V3_input.txt` - 第3次就诊（同一患者）
- `patient_{住院号}_V4_input.txt` - 第4次就诊（同一患者）

---

## 数据处理说明

### 双层检查机制

**第一层（字段级）- Python代码自动**:
- ✅ 白名单过滤：保留16个输入特征字段
- ✅ 黑名单移除：入院诊断、出院诊断、**诊疗经过**、出院时间

**第二层（语义级）- Claude Code (LLM)**:
- ✅ 检查现病史中是否混入"本次诊疗经过"
- ✅ 区分"既往治疗史"vs"本次诊疗经过"
- ✅ 结果：0个Case混入本次诊疗关键词

### 关键概念

| 类别 | 定义 | 处理方式 |
|------|------|---------|
| **既往治疗史** ✅ | 患者**之前**接受的治疗 | **保留** - 属于输入特征X |
| **本次诊疗经过** ❌ | 患者**本次住院期间**的治疗 | **移除** - 属于标签Y |

---

## 文件清单

### 唯一住院号（34个）
- patient_363291_input.txt
- patient_466104_input.txt (及V2,V3,V4)
- patient_605525_input.txt
- patient_612908_input.txt
- patient_626229_input.txt
- patient_638114_input.txt (及V2)
- patient_638772_input.txt (及V2,V3)
- patient_639941_input.txt
- patient_640880_input.txt (及V2)
- patient_642538_input.txt
- patient_646846_input.txt
- patient_648307_input.txt (及V2)
- patient_648772_input.txt
- patient_650180_input.txt (及V2)
- patient_650755_input.txt
- patient_658948_input.txt
- patient_665548_input.txt
- patient_668725_input.txt
- patient_673133_input.txt
- patient_690239_input.txt
- patient_706298_input.txt
- patient_708387_input.txt
- patient_713768_input.txt
- patient_715725_input.txt (及V2)
- patient_721753_input.txt
- patient_747724_input.txt
- patient_767685_input.txt
- patient_779411_input.txt
- patient_787777_input.txt
- patient_796816_input.txt
- patient_798603_input.txt
- patient_811840_input.txt (及V2)
- patient_840093_input.txt
- patient_844105_input.txt
- patient_846891_input.txt
- patient_855793_input.txt
- patient_868183_input.txt
- patient_877371_input.txt (及V2)
- patient_890897_input.txt

---

## 相关文档

- **处理报告**: `workspace/processing_logs/batch_report_*.json`
- **过滤对比报告**: `workspace/processing_logs/FILTERING_COMPARISON_REPORT.md`
- **语义审查报告**: `workspace/processing_logs/SEMANTIC_REVIEW_REPORT_LLM.md`
- **源数据**: `patients_folder/46个病例_诊疗经过.xlsx`

---

## 数据质量

- ✅ 第一层检查（字段级）：通过
- ✅ 第二层检查（语义级）：通过
- ✅ 数据完整性：46/46文件生成
- ✅ 符合BM Agent输入标准

---

**归档时间**: 2026-04-03  
**归档位置**: `/media/luzhenyang/project/TianTan_Brain_Metastases_Agent/patient_input/Set-2，0402/`
