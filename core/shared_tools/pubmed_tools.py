#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pubmed_tools.py - PubMed 文献检索原子工具集 (L1 层)

基于 NCBI E-utilities API 的文献检索与摘要获取
严格遵循 Single Brain 架构：只做 API 管道，返回结构化数据
"""

import requests
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional
from datetime import datetime
from langchain.tools import tool

# NCBI E-utilities API 配置
NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_EMAIL = "research@tiantan.edu.cn"  # 用于 NCBI 使用统计
REQUEST_TIMEOUT = 30


def _construct_pubmed_query(
    disease: str,
    gene: Optional[str] = None,
    biomarker: Optional[str] = None,
    treatment: Optional[str] = None,
    study_type: Optional[str] = None,
    year_from: Optional[int] = None
) -> str:
    """
    构造布尔逻辑的 PubMed 查询语句。

    Args:
        disease: 疾病名称 (如 "Brain Neoplasms", "Lung Cancer")
        gene: 基因名称 (如 "EGFR", "BRAF")
        biomarker: 生物标志物 (如 "T790M", "V600E")
        treatment: 治疗药物 (如 "Osimertinib")
        study_type: 研究类型 (如 "Clinical Trial")
        year_from: 起始年份 (如 2020)

    Returns:
        布尔逻辑的 PubMed 查询字符串
    """
    query_parts = []

    # 疾病 (使用 MeSH 标签)
    if disease:
        query_parts.append(f'"{disease}"[Mesh]')

    # 基因
    if gene:
        query_parts.append(f'"{gene}"[Title/Abstract]')

    # 生物标志物
    if biomarker:
        query_parts.append(f'"{biomarker}"[Title/Abstract]')

    # 治疗
    if treatment:
        query_parts.append(f'"{treatment}"[Title/Abstract]')

    # 研究类型
    if study_type:
        study_type_map = {
            "Clinical Trial": "Clinical Trial[ptyp]",
            "Randomized Controlled Trial": "Randomized Controlled Trial[ptyp]",
            "Meta-Analysis": "Meta-Analysis[ptyp]",
            "Review": "Review[ptyp]",
            "Case Report": "Case Reports[ptyp]",
            "Cohort": "Cohort Studies[Mesh]"
        }
        query_parts.append(study_type_map.get(study_type, f'"{study_type}"[ptyp]'))

    # 年份限制
    if year_from:
        query_parts.append(f'("{year_from}"[Date - Publication] : "3000"[Date - Publication])')

    return " AND ".join(query_parts)


def _esearch_pubmed(query: str, max_results: int = 5) -> Dict:
    """
    使用 ESearch 查询 PubMed 获取 PMID 列表。

    Args:
        query: PubMed 查询语句
        max_results: 返回的最大结果数

    Returns:
        包含 pmid_list 和 count 的字典，或错误信息
    """
    url = f"{NCBI_BASE_URL}/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "sort": "relevance",
        "tool": "tiantan_brain_metastases_agent",
        "email": NCBI_EMAIL
    }

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()

        esearchresult = data.get("esearchresult", {})
        idlist = esearchresult.get("idlist", [])
        count = esearchresult.get("count", 0)

        return {
            "status": "success",
            "pmid_list": idlist,
            "total_count": int(count),
            "query": query
        }

    except requests.exceptions.Timeout:
        return {"status": "error", "error": "PubMed search timeout", "query": query}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": f"PubMed search failed: {str(e)}", "query": query}


def _efetch_pubmed_abstracts(pmids: List[str]) -> Dict:
    """
    使用 EFetch 获取 PubMed 文章摘要。

    Args:
        pmids: PMID 列表

    Returns:
        包含文章列表的字典，或错误信息
    """
    if not pmids:
        return {"status": "success", "articles": []}

    url = f"{NCBI_BASE_URL}/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
        "tool": "tiantan_brain_metastases_agent",
        "email": NCBI_EMAIL
    }

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        xml_content = response.text

        # 解析 XML
        articles = _parse_pubmed_xml(xml_content)

        return {
            "status": "success",
            "articles": articles,
            "count": len(articles)
        }

    except requests.exceptions.Timeout:
        return {"status": "error", "error": "PubMed fetch timeout", "pmids": pmids}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": f"PubMed fetch failed: {str(e)}", "pmids": pmids}
    except ET.ParseError as e:
        return {"status": "error", "error": f"XML parse failed: {str(e)}", "pmids": pmids}


def _parse_pubmed_xml(xml_content: str) -> List[Dict]:
    """
    解析 PubMed XML 返回的文章信息。

    Args:
        xml_content: XML 字符串

    Returns:
        文章信息列表
    """
    articles = []

    try:
        root = ET.fromstring(xml_content)

        # PubMed XML 结构: PubmedArticleSet -> PubmedArticle
        for article in root.findall(".//PubmedArticle"):
            try:
                # 提取 PMID
                pmid_elem = article.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None else "N/A"

                # 提取标题
                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else "No title available"

                # 提取期刊信息
                journal_elem = article.find(".//Journal")
                journal_title = "Unknown"
                if journal_elem is not None:
                    title_elem = journal_elem.find("Title")
                    if title_elem is not None:
                        journal_title = title_elem.text

                # 提取年份
                year_elem = article.find(".//PubDate/Year")
                if year_elem is None:
                    # 尝试 MedlineDate
                    medline_date = article.find(".//PubDate/MedlineDate")
                    if medline_date is not None:
                        year = medline_date.text[:4] if len(medline_date.text) >= 4 else "Unknown"
                    else:
                        year = "Unknown"
                else:
                    year = year_elem.text

                # 提取摘要
                abstract_elem = article.find(".//Abstract/AbstractText")
                if abstract_elem is not None:
                    abstract = abstract_elem.text
                else:
                    # 尝试多个 AbstractText
                    abstract_parts = article.findall(".//Abstract/AbstractText")
                    if abstract_parts:
                        abstract = " ".join([part.text for part in abstract_parts if part.text])
                    else:
                        abstract = "No abstract available"

                # 提取作者
                author_list = article.findall(".//Author")
                authors = []
                for author in author_list[:3]:  # 只取前3个作者
                    last_name = author.find("LastName")
                    fore_name = author.find("ForeName")
                    if last_name is not None:
                        name = f"{fore_name.text} {last_name.text}" if fore_name is not None else last_name.text
                        authors.append(name)

                # 提取 DOI
                doi_elem = article.find(".//ArticleId[@IdType='doi']")
                doi = doi_elem.text if doi_elem is not None else None

                articles.append({
                    "pmid": pmid,
                "title": title,
                    "journal": journal_title,
                    "year": year,
                    "abstract": abstract,
                    "authors": authors,
                    "doi": doi
                })

            except Exception as e:
                # 单篇文章解析失败，继续下一篇
                continue

    except ET.ParseError as e:
        raise

    return articles


@tool
def pubmed_search_and_fetch_abstracts(
    query: str,
    max_results: int = 5
) -> str:
    """
    搜索 PubMed 并获取文献摘要的组合工具。

    使用场景：
    1. 指南未涵盖患者的特殊复杂情况
    2. OncoKB 返回 VUS (临床意义未明) 或只有低级别证据时
    3. 需要寻找最新的临床证据（特别是超适应症用药案例）

    Query 构造示例（必须使用布尔逻辑）：
    - "Non-Small Cell Lung Cancer"[Mesh] AND Osimertinib AND "Brain Metastases"
    - "Melanoma"[Mesh] AND BRAF AND "Stereotactic Radiosurgery" AND "Clinical Trial"[ptyp]

    Args:
        query: PubMed 查询语句（建议使用布尔逻辑和 MeSH 标签）
        max_results: 返回的最大文献数（默认 5，建议 3-10）

    Returns:
        包含文献信息的结构化 Markdown 文本，格式如下：

        ## PubMed 文献检索结果

        **查询**: {query}
        **检索到**: {total_count} 篇文献

        ### 文献 1
        **PMID**: xxx
        **标题**: xxx
        **期刊**: xxx (Year)
        **作者**: xxx et al.
        **摘要**: xxx

        ### 文献 2
        ...
    """
    # 执行搜索
    search_result = _esearch_pubmed(query, max_results)

    if search_result["status"] == "error":
        return f"## PubMed 检索失败\n\n**错误**: {search_result.get('error', 'Unknown error')}\n**查询**: {query}"

    pmid_list = search_result.get("pmid_list", [])
    total_count = search_result.get("total_count", 0)

    if not pmid_list:
        return f"## PubMed 检索结果\n\n**查询**: {query}\n**结果**: 未找到相关文献"

    # 获取摘要
    fetch_result = _efetch_pubmed_abstracts(pmid_list)

    if fetch_result["status"] == "error":
        return f"## PubMed 检索部分成功\n\n**查询**: {query}\n**找到**: {total_count} 篇文献\n**获取摘要失败**: {fetch_result.get('error', 'Unknown error')}\n\n**PMID 列表**: {', '.join(pmid_list)}"

    articles = fetch_result.get("articles", [])

    # 组装 Markdown 输出
    lines = [
        "## PubMed 文献检索结果",
        "",
        f"**查询**: {query}",
        f"**检索到**: {total_count} 篇相关文献",
        f"**显示前**: {len(articles)} 篇",
        ""
    ]

    for i, article in enumerate(articles, 1):
        lines.extend([
            f"### 文献 {i}",
            "",
            f"**PMID**: {article['pmid']}",
            f"**标题**: {article['title']}",
            f"**期刊**: {article['journal']} ({article['year']})",
        ])

        if article['authors']:
            lines.append(f"**作者**: {', '.join(article['authors'])} et al.")

        if article['doi']:
            lines.append(f"**DOI**: {article['doi']}")

        lines.extend([
            "",
            f"**摘要**: {article['abstract']}",
            ""
        ])

    return "\n".join(lines)


@tool
def pubmed_construct_query(
    disease: str,
    treatment: Optional[str] = None,
    gene: Optional[str] = None,
    study_type: Optional[str] = None,
    year_from: Optional[int] = 2020
) -> str:
    """
    辅助工具：构造布尔逻辑的 PubMed 查询语句。

    当你不确定如何构造查询时，可使用此工具生成标准化的查询字符串。

    Args:
        disease: 疾病名称 (如 "Brain Neoplasms", "Lung Neoplasms")
        treatment: 治疗药物或方法 (如 "Osimertinib", "Stereotactic Radiosurgery")
        gene: 基因名称 (如 "EGFR", "BRAF")
        study_type: 研究类型 (如 "Clinical Trial", "Randomized Controlled Trial", "Meta-Analysis", "Case Report")
        year_from: 起始年份 (默认 2020)

    Returns:
        布尔逻辑的 PubMed 查询字符串，可直接用于 pubmed_search_and_fetch_abstracts
    """
    query = _construct_pubmed_query(
        disease=disease,
        gene=gene,
        treatment=treatment,
        study_type=study_type,
        year_from=year_from
    )

    return f"## PubMed 查询构造\n\n**参数**: disease={disease}, treatment={treatment}, gene={gene}, study_type={study_type}, year_from={year_from}\n\n**生成的查询**: {query}\n\n**可直接使用此查询字符串调用 pubmed_search_and_fetch_abstracts**"
