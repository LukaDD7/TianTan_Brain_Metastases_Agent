# NCBI E-utilities API 参考

> 最后更新：2026-03-04
> API 版本：2.0

---

## API 基础 URL

```
https://eutils.ncbi.nlm.nih.gov/entrez/eutils
```

---

## 主要端点

### 1. ESearch - 文献搜索

**用途：** 搜索 PubMed 数据库并获取 PMID 列表

**端点：**
```
GET /esearch.fcgi
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| db | string | 是 | 数据库名 ("pubmed") |
| term | string | 是 | 搜索词 |
| retmax | integer | 否 | 最大返回数 (默认 20，最多 100000) |
| retmode | string | 否 | 返回模式 ("json" 或 "xml") |
| sort | string | 否 | 排序方式 ("relevance" 或 "date") |
| tool | string | 推荐 | 客户端工具名称 |
| email | string | 推荐 | 联系邮箱 |
| api_key | string | 可选 | API Key (提供更高访问限额) |

**示例：**
```bash
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=EGFR+L858R&retmax=5&retmode=json"
```

**响应示例：**
```json
{
  "esearchresult": {
    "count": "1234",
    "retmax": "5",
    "retstart": "0",
    "idlist": ["12345678", "23456789", "34567890", "45678901", "56789012"]
  }
}
```

---

### 2. EFetch - 获取文献详情

**用途：** 根据 PMID 获取文献完整信息

**端点：**
```
GET /efetch.fcgi
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| db | string | 是 | 数据库名 ("pubmed") |
| id | string | 是 | PMID 列表 (逗号分隔) |
| retmode | string | 否 | 返回模式 ("xml" 或 "abstract") |

**示例：**
```bash
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=15118073,15118125&retmode=xml"
```

---

### 3. ESummary - 获取文献摘要

**用途：** 获取文献的摘要信息 (比 EFetch 轻量)

**端点：**
```
GET /esummary.fcgi
```

**参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| db | string | 是 | 数据库名 ("pubmed") |
| id | string | 是 | PMID 列表 (逗号分隔) |
| retmode | string | 否 | 返回模式 ("json" 或 "xml") |

**示例：**
```bash
curl "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=15118073&retmode=json"
```

---

## PubMed 搜索语法

### 字段限定符

| 限定符 | 说明 | 示例 |
|--------|------|------|
| [Title/Abstract] | 标题或摘要 | "EGFR"[Title/Abstract] |
| [Title] | 仅标题 | "Lung Cancer"[Title] |
| [Author] | 作者 | "Smith JA"[Author] |
| [Journal] | 期刊 | "NEJM"[Journal] |
| [Publication Type] | 文章类型 | "Case Reports"[Publication Type] |
| [Mesh] | MeSH 主题词 | "Carcinoma, Non-Small-Cell Lung"[Mesh] |
| [Date] | 日期 | "2023"[Date] |
| [Language] | 语言 | "English"[Language] |

### 布尔运算符

- **AND** - 同时包含
- **OR** - 包含任一
- **NOT** - 排除

**示例：**
```
"EGFR"[Title/Abstract] AND "L858R"[Title/Abstract] AND "Clinical Trial"[Publication Type]
```

### 短语搜索

使用双引号进行精确短语搜索：
```
"non-small cell lung cancer"
```

---

## 特殊搜索示例

### 病例报告搜索
```
"Lung Cancer"[Title/Abstract] AND "Systemic Lupus Erythematosus"[Title/Abstract] AND "Case Reports"[Publication Type]
```

### 临床试验搜索
```
"Osimertinib"[Title/Abstract] AND "brain metastases"[Title/Abstract] AND "Clinical Trial"[Publication Type]
```

### 综述文章搜索
```
"EGFR inhibitors"[Title/Abstract] AND "Review"[Publication Type]
```

### 指南搜索
```
"NSCLC treatment"[Title/Abstract] AND "Practice Guideline"[Publication Type]
```

---

## 速率限制

| 类型 | 限制 |
|------|------|
| 无 API Key | 每秒 3 次请求 |
| 有 API Key | 每秒 10 次请求 |

**建议：**
- 批量请求时使用逗号分隔的 PMID 列表
- 大结果集分批获取
- 本地缓存已获取的数据

---

## 错误码

| 错误 | 说明 |
|------|------|
| 400 Bad Request | 请求参数错误 |
| 429 Too Many Requests | 超过速率限制 |
| 500 Server Error | 服务器错误 |

---

## 相关资源

- [NCBI E-utilities 官方文档](https://www.ncbi.nlm.nih.gov/books/NBK25501/)
- [PubMed 搜索帮助](https://pubmed.ncbi.nlm.nih.gov/help/)
- [MeSH 数据库](https://meshb.nlm.nih.gov/search)
- [NCBI 账号注册](https://www.ncbi.nlm.nih.gov/account/)
