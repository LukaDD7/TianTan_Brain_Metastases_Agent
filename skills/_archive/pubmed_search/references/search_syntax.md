# PubMed 搜索语法详解

> 来源：https://pubmed.ncbi.nlm.nih.gov/help/

---

## 一、基础搜索

### 1. 关键词搜索

最简单的搜索方式，直接输入关键词：
```
lung cancer treatment
```

PubMed 会自动在所有字段中搜索，并使用 AND 连接多个词。

### 2. 短语搜索

使用双引号进行精确短语匹配：
```
"non-small cell lung cancer"
```

### 3. 字段限定搜索

使用 `[字段名]` 限定搜索范围：

```
"EGFR"[Author]
"2023"[Date - Publication]
"NEJM"[Journal]
```

---

## 二、常用字段限定符

| 限定符 | 缩写 | 示例 |
|--------|------|------|
| Title/Abstract | TIAB | "EGFR"[TIAB] |
| Title | TI | "Lung Cancer"[TI] |
| Author | AU | "Zhang Y"[AU] |
| Journal | TA | "J Clin Oncol"[TA] |
| Publication Type | PT | "Case Reports"[PT] |
| Mesh Terms | MH | "Carcinoma, Non-Small-Cell Lung"[MH] |
| Date - Publication | DP | "2023"[DP] |
| Language | LA | "English"[LA] |
| Publisher | PB | "Nature"[PB] |

---

## 三、布尔运算符

### AND - 同时包含

```
EGFR AND L858R AND NSCLC
```
返回同时包含三个词的文献。

### OR - 包含任一

```
NSCLC OR "Non-Small Cell Lung Cancer"
```
返回包含任一术语的文献。

### NOT - 排除

```
lung cancer NOT "small cell"
```
排除包含"small cell"的文献。

---

## 四、高级搜索技巧

### 1. 组合搜索

```
("EGFR"[TIAB] OR "Epidermal Growth Factor Receptor"[TIAB])
AND ("L858R"[TIAB] OR "exon 19 deletion"[TIAB])
AND "Clinical Trial"[PT]
```

### 2. 日期范围限定

```
"lung cancer"[TIAB] AND ("2020"[DP] : "2023"[DP])
```
返回 2020-2023 年的文献。

### 3. 年龄/性别限定

```
"lung cancer"[TIAB] AND ("aged"[MH] OR "elderly"[TIAB])
```

### 4. 文章类型限定

```
"immunotherapy"[TIAB] AND ("Meta-Analysis"[PT] OR "Systematic Review"[PT])
```

---

## 五、MeSH 术语搜索

MeSH (Medical Subject Headings) 是 NCBI 的医学主题词表。

### 使用 MeSH 搜索

```
"Carcinoma, Non-Small-Cell Lung"[MH]
```

### 带副主题词的 MeSH 搜索

```
"Carcinoma, Non-Small-Cell Lung/drug therapy"[MH]
```

### 扩展 MeSH 搜索 (包括下级术语)

```
"Carcinoma, Non-Small-Cell Lung"[MH:NoExp]
```

---

## 六、特殊搜索场景

### 1. 罕见病例报告搜索

```
"disease_name"[TIAB] AND "comorbidity"[TIAB] AND "Case Reports"[PT]
```

**示例：**
```
"Lung Cancer"[TIAB] AND "Lupus"[TIAB] AND "Case Reports"[PT]
```

### 2. 临床试验搜索

```
"topic"[TIAB] AND "Clinical Trial"[PT]
```

**示例：**
```
"Osimertinib"[TIAB] AND "brain metastases"[TIAB] AND "Clinical Trial"[PT]
```

### 3. 指南搜索

```
"disease"[TIAB] AND ("Practice Guideline"[PT] OR "Guideline"[PT])
```

### 4. 系统综述/Meta 分析搜索

```
"topic"[TIAB] AND ("Meta-Analysis"[PT] OR "Systematic Review"[PT])
```

### 5. 特定基因突变搜索

```
"gene_name"[TIAB] AND "mutation"[TIAB] AND "cancer_type"[TIAB]
```

**示例：**
```
"EGFR"[TIAB] AND "L858R"[TIAB] AND "NSCLC"[TIAB]
```

---

## 七、搜索策略模板

### 肿瘤精准治疗搜索模板

```
("gene_name"[TIAB] OR "gene_full_name"[MH])
AND ("mutation_name"[TIAB] OR "variant"[TIAB])
AND ("cancer_type"[TIAB] OR "cancer_mesh"[MH])
AND ("treatment"[TIAB] OR "drug_name"[TIAB] OR "therapy"[SH])
```

### 药物副作用搜索模板

```
("drug_name"[TIAB] OR "drug_mesh"[MH])
AND ("adverse event"[TIAB] OR "toxicity"[SH] OR "side effect"[TIAB])
AND ("cancer_type"[TIAB])
```

### 预后因素搜索模板

```
("factor"[TIAB] OR "biomarker"[TIAB] OR "predictor"[TIAB])
AND ("prognosis"[SH] OR "survival"[TIAB] OR "outcome"[TIAB])
AND ("cancer_type"[TIAB])
```

---

## 八、常见 MeSH 术语

### 肿瘤相关

| MeSH 术语 | 说明 |
|-----------|------|
| "Carcinoma, Non-Small-Cell Lung"[MH] | 非小细胞肺癌 |
| "Brain Neoplasms"[MH] | 脑肿瘤 |
| "Neoplasm Metastasis"[MH] | 肿瘤转移 |

### 治疗相关

| MeSH 术语 | 说明 |
|-----------|------|
| "Antineoplastic Agents"[MH] | 抗肿瘤药物 |
| "Protein Kinase Inhibitors"[MH] | 蛋白激酶抑制剂 |
| "Immunotherapy"[MH] | 免疫治疗 |

### 研究类型

| MeSH 术语 | 说明 |
|-----------|------|
| "Clinical Trial"[PT] | 临床试验 |
| "Randomized Controlled Trial"[PT] | 随机对照试验 |
| "Meta-Analysis"[PT] | Meta 分析 |
| "Systematic Review"[PT] | 系统综述 |
| "Case Reports"[PT] | 病例报告 |

---

## 九、搜索历史与保存

### 查看搜索历史

在 PubMed 网站登录后，可以查看和保存搜索历史。

### 保存搜索策略

登录 NCBI 账号后可以：
- 保存搜索策略
- 设置邮件提醒 (My NCBI)
- 导出搜索结果

---

## 十、相关资源

- [PubMed 官方帮助](https://pubmed.ncbi.nlm.nih.gov/help/)
- [MeSH 数据库](https://meshb.nlm.nih.gov/search)
- [PubMed 高级搜索教程](https://pubmed.ncbi.nlm.nih.gov/advanced/)
- [NCBI 培训资源](https://training.nlm.nih.gov/)
