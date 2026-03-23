# PubMed Search Skill

快速查询 PubMed 生物医学文献数据库，获取文献摘要、详情或搜索特定主题的文献。

## 快速开始

### 1. 设置环境变量

```bash
# Linux/macOS
export PUBMED_EMAIL="your_email@example.com"
export E_UTILITIES_API="your_api_key"

# Windows PowerShell
$env:PUBMED_EMAIL="your_email@example.com"
$env:E_UTILITIES_API="your_api_key"
```

获取 API Key: https://www.ncbi.nlm.nih.gov/account/

### 2. 安装依赖

```bash
pip install biopython requests
```

### 3. 运行查询

**搜索文献：**
```bash
python skills/pubmed_search/scripts/search_articles.py \
  --query_type search \
  --keywords "EGFR L858R NSCLC treatment" \
  --max_results 5
```

**获取文献详情：**
```bash
python skills/pubmed_search/scripts/search_articles.py \
  --query_type details \
  --pmid_list 15118073 15118125 34526717
```

**搜索病例报告：**
```bash
python skills/pubmed_search/scripts/search_articles.py \
  --query_type case_reports \
  --disease "Lung Cancer" \
  --comorbidity "Lupus" \
  --treatment "PD-1"
```

## 查询类型

| 类型 | 用途 | 必填参数 |
|------|------|---------|
| `search` | 根据关键词搜索文献 | keywords |
| `details` | 根据 PMID 获取文献详情 | pmid_list |
| `case_reports` | 搜索罕见病例报告 | disease, comorbidity |
| `clinical_trial` | 搜索临床试验文献 | keywords |

## 在代码中使用

```python
from skills.pubmed_search.scripts.search_articles import PubMedSearch, PubMedSearchInput
from core.skill import SkillContext

skill = PubMedSearch()
context = SkillContext(session_id="patient_001")

# 搜索文献
input_args = PubMedSearchInput(
    query_type="search",
    keywords="EGFR L858R NSCLC treatment",
    max_results=5
)
result = skill.execute_with_retry(input_args.model_dump(), context=context)
print(result)

# 获取文献详情
input_args = PubMedSearchInput(
    query_type="details",
    pmid_list=["15118073", "15118125"]
)
result = skill.execute_with_retry(input_args.model_dump(), context=context)
```

## 与 OncoKB 配合使用

```python
# 1. 先查询 OncoKB 获取变异的治疗推荐和引用 PMID
oncokb_result = query_oncokb(...)

# 2. 提取 OncoKB 返回的 PMID
pmids = [ref['pmid'] for ref in oncokb_result['evidence'] if 'pmid' in ref]

# 3. 使用 PubMed 获取文献详情
pubmed_result = search_pubmed(query_type="details", pmid_list=pmids)
```

## 参考资料

- [API 端点参考](references/api_endpoints.md)
- [搜索语法详解](references/search_syntax.md)

## 常见问题

**Q: 为什么需要设置邮箱？**
A: NCBI 要求所有 E-utilities 用户提供联系方式，用于必要时沟通。

**Q: API Key 有什么用？**
A: 有 API Key 每秒可请求 10 次，无 Key 仅 3 次。

**Q: 最多可以获取多少条结果？**
A: 单次查询最多 100 条，建议分批获取大结果集。

**Q: 如何获取全文？**
A: PubMed 只提供摘要，全文需通过期刊官网或 Sci-Hub 等渠道获取。
