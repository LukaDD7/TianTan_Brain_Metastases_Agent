---
name: clinical_expert_review
description: |
  临床专家审查SKILL - 用于替代临床医生对BM Agent生成的MDT报告进行专业评审。
  核心功能：1) 基于患者具体情况推理决策合理性；2) 溯源验证所有引用（本地指南/PubMed）。
  评审指标：CCR、MQR、CER、PTR。
type: assessment
version: 1.0.0
author: Claude Code
---

# Clinical Expert Review SKILL

## 1. 核心原则

### 1.1 双重验证机制

对每个诊疗决策，必须执行：

**验证1 - 患者情境推理**:
```
患者具体情况 → 临床推理 → 决策合理性判断
```

**验证2 - 引用溯源验证**:
```
报告引用 → 溯源检索 → 内容匹配度验证
```

### 1.2 引用类型处理

| 引用类型 | 验证方法 | 工具 |
|---------|---------|------|
| `[Local: <文件>, Line/Section]` | 读取本地指南MD文件 | `read_file` |
| `[PubMed: PMID XXXXXX]` | PubMed API检索 | `search_pubmed` |
| `[OncoKB: Level X]` | OncoKB API验证 | `query_oncokb` |
| `[Web: ...]` | 标记为部分可追溯 | - |

---

## 2. 审查流程（6步法）

### Phase 1: 准备阶段

**输入文件**:
- 患者输入: `patient_input/Set-1/patient_{id}_input.txt`
- BM Agent报告: `analysis/samples/{id}/MDT_Report_{id}.md`
- 真实临床路径: `workspace/test_cases_wide.xlsx`

**初始化审查工作目录**:
```bash
analysis/reviews/work_{patient_id}/
├── patient_summary.json       # 患者信息摘要
├── report_extracted.json      # 报告关键信息提取
├── citations_to_verify.json   # 待验证引用清单
└── review_notes.md            # 审查过程记录
```

### Phase 2: 患者情境分析

**步骤**:
1. 读取患者输入文件
2. 提取关键临床信息:
   - 肿瘤类型、分期、分子分型
   - 既往治疗史（线数、方案、疗效）
   - 当前疾病状态（初治/经治/进展）
   - 合并症、KPS/ECOG评分
3. 构建患者临床画像
4. 标注信息来源状态 (`confirmed`/`inferred`/`unknown`)

**输出**: `patient_summary.json`

### Phase 3: 报告关键信息提取

**提取内容**:
1. 治疗线判定
2. 推荐方案及理由
3. 剂量参数及引用
4. 排他性论证
5. 所有引用标记

**引用分类**:
```json
{
  "citations": {
    "local_guidelines": [...],
    "pubmed": [...],
    "oncokb": [...],
    "web": [...]
  }
}
```

**输出**: `report_extracted.json`, `citations_to_verify.json`

### Phase 4: 引用溯源验证（核心环节）

#### 4.1 本地指南验证

**流程**:
```python
for citation in local_citations:
    # 1. 读取指南文件
    content = read_file(f"Guidelines/{filename}")
    
    # 2. 定位具体位置
    if line_number:
        verify_content = content.split('\n')[line_number-1]
    elif section:
        verify_content = extract_section(content, section)
    
    # 3. 验证支持度
    match_score = check_claim_support(verify_content, report_claim)
    
    # 4. 记录结果
    record_verification(citation, match_score, verify_content)
```

**验证标准**:
- ✅ **完全支持**: 引用内容直接支撑报告声称
- ⚠️ **部分支持**: 引用内容与声称相关但非直接支撑
- ❌ **不支持**: 引用内容与声称矛盾或无关
- ❓ **无法验证**: 引用位置不存在或格式错误

#### 4.2 PubMed验证

**流程**:
```python
for pmid in pubmed_citations:
    # 1. 调用PubMed Search Skill
    result = search_pubmed(query=f"{pmid}[uid]", max_results=1)
    
    # 2. 获取文章详情
    article = result.articles[0]
    
    # 3. 提取关键信息
    title = article.title
    abstract = article.abstract
    
    # 4. 验证声称支持度
    claim_support = verify_claim_against_abstract(
        report_claim=report_claim,
        article_title=title,
        article_abstract=abstract
    )
    
    # 5. 记录结果
    record_pubmed_verification(pmid, title, claim_support)
```

**特别注意 - 剂量引用陷阱**:
```
报告声称: "SRS 18-24Gy/1f [PubMed: PMID 32921513]"
验证步骤:
1. PMID是否存在? ✅
2. 文章是否提到18-24Gy范围? ⚠️ 可能只提单一剂量
3. 如文章只提"median 18Gy"，则报告范围是推断而非直接引用
4. 判定: 部分支持（需标注为"基于文献的合理推断"）
```

#### 4.3 OncoKB验证

**流程**:
```python
for oncokb_citation in oncokb_citations:
    # 提取基因和突变
    gene, alteration = parse_oncokb_citation(oncokb_citation)
    
    # 调用OncoKB Query Skill
    result = query_oncokb(
        gene=gene,
        alteration=alteration,
        tumor_type=tumor_type
    )
    
    # 验证声称
    verify_oncokb_claim(result, report_claim)
```

**输出**: `citation_verification_report.json`

### Phase 5: 临床一致性评审 (CCR)

基于Phase 2-4的结果，进行5维度评分：

| 维度 | 评分依据 |
|------|---------|
| **治疗线判定** | 患者情境分析 + 既往治疗史验证 |
| **方案选择** | 指南引用验证 + 分子分型匹配 |
| **剂量参数** | PubMed验证 + 剂量引用陷阱检查 |
| **排他性论证** | 引用完整性和支持度验证 |
| **临床路径一致性** | 与真实路径对比 |

**引用验证结果影响评分**:
- 引用完全支持 → 基础分
- 引用部分支持 → 扣0.5分
- 引用不支持 → 扣1-2分
- 引用无法验证 → 扣1分

### Phase 6: 错误审查 (CER)

**引用相关错误**:

| 错误类型 | 级别 | 说明 |
|---------|------|------|
| 引用内容与声称矛盾 | 严重(3.0) | 如声称Level 1但OncoKB显示Level 4 |
| 剂量范围推断未标注 | 主要(2.0) | 将推断剂量标注为直接引用 |
| 引用格式不规范 | 次要(1.0) | 如缺少页码/章节信息 |

---

## 3. 状态词约定

- **confirmed**: 来自病历原文或已验证数据库
- **inferred**: 基于证据的合理推断（需标注）
- **unknown**: 无明确支持证据
- **verified**: 引用已验证，内容支持声称
- **partial**: 引用部分支持声称
- **contradicted**: 引用与声称矛盾

---

## 4. 输出规范

### 4.1 审查报告结构

```markdown
## 患者 {patient_id} 专家审查报告

### 一、患者情境分析
| 项目 | 内容 | 状态 |
|------|------|------|
| 肿瘤类型 | xxx | confirmed |
| 分子分型 | xxx | confirmed |
| 既往治疗线数 | X线 | inferred |
| 当前疾病状态 | PD | inferred |

### 二、引用溯源验证
#### 本地指南引用
| 引用 | 声称 | 验证结果 | 匹配度 |
|------|------|---------|--------|
| [Local: NCCN_CNS, Section: brain-c] | SRS剂量15-24Gy | verified | 完全支持 |

#### PubMed引用
| PMID | 报告声称 | 文章标题 | 支持度 | 备注 |
|------|---------|---------|--------|------|
| 32921513 | SRS 18-24Gy | Dose tolerances... | partial | 文章讨论NTCP，范围系推断 |

#### OncoKB引用
| 突变 | 声称 | 实际 | 状态 |
|------|------|------|------|
| KRAS G12V | LEVEL_R1 | LEVEL_R1 | verified |

### 三、CCR评审
...

### 四、CER评审（引用相关错误）
| 级别 | 错误描述 | 涉及引用 |
|------|---------|---------|
| 主要 | 剂量范围推断未标注来源 | PMID 32921513 |
```

### 4.2 JSON输出

```json
{
  "patient_id": "xxx",
  "patient_context": {...},
  "citation_verification": {
    "local": [...],
    "pubmed": [...],
    "oncokb": [...]
  },
  "ccr": {...},
  "mqr": {...},
  "cer": {...},
  "cpi": xxx
}
```

---

## 5. 使用示例

### 单个患者审查

```bash
# 1. 准备患者信息
python tools/clinical_expert_review/scripts/extract_patient_context.py \
    --patient-id 605525 \
    --input patient_input/Set-1/patient_605525_input.txt

# 2. 提取报告引用
python tools/clinical_expert_review/scripts/extract_citations.py \
    --report analysis/samples/605525/MDT_Report_605525.md

# 3. 验证引用（本地指南）
python tools/clinical_expert_review/scripts/verify_local_citations.py \
    --citations work_605525/citations_to_verify.json \
    --guidelines-dir Guidelines/

# 4. 验证引用（PubMed）
python tools/clinical_expert_review/scripts/verify_pubmed_citations.py \
    --citations work_605525/citations_to_verify.json

# 5. 生成完整审查报告
python tools/clinical_expert_review/scripts/generate_review.py \
    --patient-id 605525 \
    --verification-results work_60525/citation_verification_report.json \
    --output analysis/reviews/
```

---

## 6. 相关文档索引

### 6.1 核心文档

| 文档 | 路径 |
|------|------|
| SKILL主文件 | `tools/clinical_expert_review/SKILL.md` |
| 量化指标定义 | `CLAUDE.md` Section 2 |
| 患者输入数据 | `patient_input/Set-1/` |
| BM Agent报告 | `analysis/samples/{id}/` |
| 本地指南 | `workspace/sandbox/Guidelines/` |

### 6.2 工具依赖

- `read_file`: 读取本地文件
- `search_pubmed`: PubMed文献检索
- `query_oncokb`: OncoKB查询

---

## 7. 过期文档（归档）

| 文档 | 路径 | 状态 | 说明 |
|------|------|------|------|
| 旧审查脚本 | `analysis/generate_clinical_reviews.py` | 过期 | 缺少引用验证环节 |
| 旧CER评估 | `analysis/batch_cer_assessment.py` | 过期 | 使用预估数据 |
| 旧汇总报告 | `analysis/UNIFIED_EVALUATION_REPORT_v2.md` | 已删除 | 被v2.1取代 |

---

**创建日期**: 2026-04-07  
**版本**: v1.0.0
