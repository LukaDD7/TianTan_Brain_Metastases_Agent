---
name: search_pubmed
description: |
  查询 PubMed 生物医学文献数据库，获取文献摘要、详情或搜索特定主题的文献。

  PubMed 是美国国立医学图书馆 (NLM) 维护的生物医学文献数据库，包含：
  - 超过 3500 万篇生物医学文献
  - 涵盖医学、护理、牙科、兽医、卫生保健系统、临床前科学等领域
  - 提供文献标题、摘要、作者、期刊信息

  适用于以下查询场景：
  1. **文献搜索**：根据关键词搜索相关文献 (如 "EGFR L858R NSCLC treatment")
  2. **文献详情获取**：根据 PMID 获取文献的完整信息 (标题、摘要、期刊等)
  3. **罕见病例报告搜索**：搜索特定合并症或治疗背景下的病例报告
  4. **临床试验搜索**：搜索特定主题的临床试验文献

  注意：PubMed API 无需认证，但有速率限制，建议合理使用。
version: 2.1.1
author: TianTan Brain Metastases Agent Team
metadata:
  openclaw:
    os: ["linux", "darwin", "windows"]
    requires:
      binaries: ["python3"]
      env: ["PUBMED_EMAIL", "E_UTILITIES_API"]
      config: []
  dependencies:
    - biopython>=1.79
user-invocable: true
---

## 使用说明

### 查询类型

PubMed Search Skill 支持多种查询类型，Agent 可根据需要选择：

| 查询类型 | 方法 | 适用场景 |
|---------|------|---------|
| `search` | `query_type="search"` | 根据关键词搜索文献 |
| `details` | `query_type="details"` | 根据 PMID 获取文献详情 |
| `case_reports` | `query_type="case_reports"` | 搜索罕见病例报告 |
| `clinical_trial` | `query_type="clinical_trial"` | 搜索临床试验文献 |

### 输入参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query_type | string | 是 | 查询类型：search/details/case_reports/clinical_trial |
| keywords | string | 条件必填 | 搜索关键词，search 查询需要 |
| pmid_list | array | 条件必填 | PMID 列表，details 查询需要 |
| disease | string | 条件必填 | 疾病名称，case_reports 查询需要 |
| comorbidity | string | 条件必填 | 合并症，case_reports 查询需要 |
| treatment | string | 否 | 治疗手段，case_reports 可选 |
| max_results | integer | 否 | 最大结果数，默认 5，最多 100 |
| sort | string | 否 | 排序方式："relevance" 或 "date" |

### 输出格式

返回 JSON 格式结果：
```json
{
  "query_type": "search",
  "success": true,
  "data": {
    "search_query": "EGFR L858R NSCLC",
    "total_results": 1234,
    "pmids": ["12345678", "23456789", ...],
    "articles": [
      {
        "pmid": "12345678",
        "title": "文献标题",
        "abstract": "摘要内容",
        "journal": "期刊名称",
        "year": "2023",
        "authors": ["Author1", "Author2"],
        "link": "https://pubmed.ncbi.nlm.nih.gov/12345678/"
      }
    ]
  }
}
```

## 临床使用场景

### 场景 1：查询特定基因突变的治疗研究
```
查询 EGFR L858R 突变非小细胞肺癌的治疗研究文献。
→ 使用 query_type="search", keywords="EGFR L858R NSCLC treatment"
```

### 场景 2：获取 OncoKB 引用文献详情
```
OncoKB 返回了 PMID 列表，需要获取这些文献的摘要。
→ 使用 query_type="details", pmid_list=["15118073", "15118125"]
```

### 场景 3：搜索罕见病例报告
```
搜索肺癌合并系统性红斑狼疮患者使用 PD-1 抑制剂的病例报告。
→ 使用 query_type="case_reports", disease="Lung Cancer", comorbidity="Lupus", treatment="PD-1"
```

### 场景 4：搜索临床试验
```
搜索奥希替尼治疗脑转移的临床试验。
→ 使用 query_type="clinical_trial", keywords="Osimertinib brain metastases"
```

## 环境变量说明

| 变量 | 说明 | 获取方式 |
|------|------|---------|
| `PUBMED_EMAIL` | NCBI 注册的邮箱地址 | 免费注册地址：https://www.ncbi.nlm.nih.gov/account/ |
| `E_UTILITIES_API` | E-utilities API Key | 在 NCBI 账号中申请，提供更高访问限额 |

## 依赖说明

- 需要安装 `biopython` (pip install biopython)
- NCBI E-utilities API 无需认证，但有速率限制
- 建议设置 API Key 以提高访问限额 (每秒请求数)

## 目录结构

```
pubmed_search/
├── SKILL.md                  # 本文件
├── README.md                 # 快速开始
├── scripts/
│   ├── pubmed_client.py      # API 客户端封装
│   └── search_articles.py    # Skill 主实现
├── references/
│   ├── api_endpoints.md      # E-utilities API 参考
│   └── search_syntax.md      # PubMed 搜索语法
└── examples/
    ├── example_queries.md    # 查询示例
    └── sample_responses.json # 示例响应
```

## 速率限制

| 类型 | 限制 |
|------|------|
| 无 API Key | 每秒 3 次请求 |
| 有 API Key | 每秒 10 次请求 |

## 相关资源

- [NCBI E-utilities 文档](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [PubMed 搜索语法](https://pubmed.ncbi.nlm.nih.gov/help/)
- [MeSH 主题词表](https://meshb.nlm.nih.gov/search)
