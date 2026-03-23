# PubMed Search 查询示例

## 示例 1：搜索基因突变治疗文献

**场景：** 查询 EGFR L858R 突变非小细胞肺癌的治疗研究文献。

**输入：**
```json
{
  "query_type": "search",
  "keywords": "EGFR L858R NSCLC treatment",
  "max_results": 5
}
```

**命令：**
```bash
python skills/pubmed_search/scripts/search_articles.py \
  --query_type search \
  --keywords "EGFR L858R NSCLC treatment" \
  --max_results 5
```

**预期输出：**
```json
{
  "query_type": "search",
  "success": true,
  "data": {
    "search_query": "EGFR L858R NSCLC treatment",
    "total_results": 5,
    "pmids": ["26864588", "27920122", "31163472", "34526717", "35184123"],
    "articles": [
      {
        "pmid": "26864588",
        "title": "Osimertinib or Platinum-Pemetrexed in EGFR T790M-Positive Lung Cancer",
        "abstract": "BACKGROUND: Osimertinib is a third-generation EGFR tyrosine kinase inhibitor...",
        "journal": "N Engl J Med",
        "year": "2016",
        "link": "https://pubmed.ncbi.nlm.nih.gov/26864588/"
      }
    ]
  }
}
```

---

## 示例 2：获取 OncoKB 引用文献详情

**场景：** OncoKB 返回了多个 PMID，需要获取这些文献的摘要以支持诊疗决策。

**输入：**
```json
{
  "query_type": "details",
  "pmid_list": ["15118073", "15118125", "34526717"]
}
```

**命令：**
```bash
python skills/pubmed_search/scripts/search_articles.py \
  --query_type details \
  --pmid_list 15118073 15118125 34526717
```

**预期输出：**
```json
{
  "query_type": "details",
  "success": true,
  "data": {
    "pmids_requested": ["15118073", "15118125", "34526717"],
    "articles_found": 3,
    "articles": [
      {
        "pmid": "15118073",
        "title": "EGFR mutations in lung cancer: correlation with clinical response to gefitinib",
        "abstract": "Epidermal growth factor receptor (EGFR) mutations are associated with...",
        "journal": "Science",
        "year": "2004",
        "authors": ["Lynch TJ", "Bell DW", "Sordella R"],
        "link": "https://pubmed.ncbi.nlm.nih.gov/15118073/"
      }
    ]
  }
}
```

---

## 示例 3：搜索罕见病例报告

**场景：** 搜索肺癌合并系统性红斑狼疮患者使用 PD-1 抑制剂的病例报告。

**输入：**
```json
{
  "query_type": "case_reports",
  "disease": "Lung Cancer",
  "comorbidity": "Systemic Lupus Erythematosus",
  "treatment": "PD-1 inhibitor",
  "max_results": 5
}
```

**命令：**
```bash
python skills/pubmed_search/scripts/search_articles.py \
  --query_type case_reports \
  --disease "Lung Cancer" \
  --comorbidity "Lupus" \
  --treatment "PD-1" \
  --max_results 5
```

**预期输出：**
```json
{
  "query_type": "case_reports",
  "success": true,
  "data": {
    "search_query": {
      "disease": "Lung Cancer",
      "comorbidity": "Lupus",
      "treatment": "PD-1"
    },
    "total_results": 3,
    "pmids": ["32123456", "33234567", "34345678"],
    "articles": [
      {
        "pmid": "32123456",
        "title": "Successful treatment with pembrolizumab in a patient with lung cancer and systemic lupus erythematosus",
        "abstract": "We report a case of...",
        "journal": "J Immunother Cancer",
        "year": "2020"
      }
    ]
  }
}
```

---

## 示例 4：搜索临床试验文献

**场景：** 搜索奥希替尼治疗脑转移的临床试验。

**输入：**
```json
{
  "query_type": "clinical_trial",
  "keywords": "Osimertinib brain metastases",
  "max_results": 10,
  "sort": "date"
}
```

**命令：**
```bash
python skills/pubmed_search/scripts/search_articles.py \
  --query_type clinical_trial \
  --keywords "Osimertinib brain metastases" \
  --max_results 10 \
  --sort date
```

---

## 示例 5：组合使用 OncoKB + PubMed

**场景：** 先查询 OncoKB 获取治疗推荐，再获取引用文献详情。

**Python 代码：**
```python
from skills.oncokb_query.scripts.query_variant import OncoKBQuery, OncoKBQueryInput
from skills.pubmed_search.scripts.search_articles import PubMedSearch, PubMedSearchInput
from core.skill import SkillContext

context = SkillContext(session_id="patient_001")

# Step 1: 查询 OncoKB
oncokb_skill = OncoKBQuery()
oncokb_input = OncoKBQueryInput(
    query_type="variant",
    hugo_symbol="EGFR",
    variant="L858R",
    tumor_type="Non-Small Cell Lung Cancer"
)
oncokb_result = oncokb_skill.execute_with_retry(
    oncokb_input.model_dump(), context=context
)

# Step 2: 从 OncoKB 结果中提取 PMID
import json
data = json.loads(oncokb_result)
pmids = []
for evidence in data.get("data", {}).get("evidence", []):
    for ref in evidence.get("references", []):
        if "pmid" in ref:
            pmids.append(str(ref["pmid"]))

print(f"Found {len(pmids)} PMIDs: {pmids}")

# Step 3: 使用 PubMed 获取文献详情
if pmids:
    pubmed_skill = PubMedSearch()
    pubmed_input = PubMedSearchInput(
        query_type="details",
        pmid_list=pmids[:5]  # 最多获取 5 篇
    )
    pubmed_result = pubmed_skill.execute_with_retry(
        pubmed_input.model_dump(), context=context
    )
    print(pubmed_result)
```

---

## 示例 6：高级搜索 - 系统综述/Meta 分析

**场景：** 搜索关于某主题的系统综述或 Meta 分析。

**输入：**
```json
{
  "query_type": "search",
  "keywords": "\"EGFR inhibitors\" AND (\"Meta-Analysis\" OR \"Systematic Review\")",
  "max_results": 10
}
```

**命令：**
```bash
python skills/pubmed_search/scripts/search_articles.py \
  --query_type search \
  --keywords "\"EGFR inhibitors\" AND (\"Meta-Analysis\" OR \"Systematic Review\")" \
  --max_results 10
```

---

## 示例 7：日期范围限定搜索

**场景：** 搜索最近 5 年 (2020-2024) 的文献。

**输入：**
```json
{
  "query_type": "search",
  "keywords": "EGFR NSCLC AND (\"2020\"[Date] : \"2024\"[Date])",
  "max_results": 10,
  "sort": "date"
}
```

---

## 注意事项

1. **PMID 验证**：PubMed 会自动过滤无效的 PMID
2. **批量获取**：建议每次最多获取 5-10 篇文献详情，避免超时
3. **结构化摘要**：部分文献摘要包含多个段落 (Background, Methods, Results...)
4. **作者列表**：默认限制返回前 10 位作者
