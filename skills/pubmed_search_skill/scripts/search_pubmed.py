#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PubMed CLI 脚本 - 供 Agent 通过 execute 调用

用法:
    python search_pubmed.py --query "Osimertinib AND lung cancer" --max-results 5
    python search_pubmed.py --disease "Brain Neoplasms" --gene EGFR --treatment Osimertinib --study-type "Clinical Trial" --year-from 2022
"""

import os
import sys
import json
import argparse
import requests
import xml.etree.ElementTree as ET
from typing import Dict, List

NCBI_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
NCBI_EMAIL = "research@tiantan.edu.cn"
REQUEST_TIMEOUT = 30


def esearch(query: str, max_results: int) -> Dict:
    """ESearch 查询"""
    url = f"{NCBI_BASE_URL}/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "json",
        "retmax": max_results,
        "sort": "relevance",
        "tool": "tiantan_agent",
        "email": NCBI_EMAIL
    }

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        esearchresult = data.get("esearchresult", {})
        return {
            "status": "success",
            "pmid_list": esearchresult.get("idlist", []),
            "total_count": int(esearchresult.get("count", 0))
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def efetch(pmids: List[str]) -> Dict:
    """EFetch 获取摘要"""
    if not pmids:
        return {"status": "success", "articles": []}

    url = f"{NCBI_BASE_URL}/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "xml",
        "rettype": "abstract",
        "tool": "tiantan_agent",
        "email": NCBI_EMAIL
    }

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        articles = parse_xml(response.text)
        return {"status": "success", "articles": articles}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def parse_xml(xml_content: str) -> List[Dict]:
    """解析 PubMed XML"""
    articles = []
    try:
        root = ET.fromstring(xml_content)
        for article in root.findall(".//PubmedArticle"):
            try:
                pmid_elem = article.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None else "N/A"

                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else "No title"

                journal_elem = article.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None else "Unknown"

                year_elem = article.find(".//PubDate/Year")
                year = year_elem.text if year_elem is not None else "Unknown"

                abstract_elem = article.find(".//Abstract/AbstractText")
                abstract = abstract_elem.text if abstract_elem is not None else "No abstract"

                author_list = article.findall(".//Author")
                authors = []
                for author in author_list[:3]:
                    last = author.find("LastName")
                    fore = author.find("ForeName")
                    if last is not None:
                        name = f"{fore.text} {last.text}" if fore is not None else last.text
                        authors.append(name)

                doi_elem = article.find(".//ArticleId[@IdType='doi']")
                doi = doi_elem.text if doi_elem is not None else None

                articles.append({
                    "pmid": pmid,
                    "title": title,
                    "journal": journal,
                    "year": year,
                    "abstract": abstract,
                    "authors": authors,
                    "doi": doi
                })
            except:
                continue
    except:
        pass
    return articles


def construct_query(disease: str, gene: str = None, treatment: str = None, study_type: str = None, year_from: int = None) -> str:
    """构造布尔查询"""
    parts = [f'"{disease}"[Mesh]']
    if gene:
        parts.append(f'"{gene}"[Title/Abstract]')
    if treatment:
        parts.append(f'"{treatment}"[Title/Abstract]')
    if study_type:
        study_map = {
            "Clinical Trial": "Clinical Trial[ptyp]",
            "Randomized Controlled Trial": "Randomized Controlled Trial[ptyp]",
            "Meta-Analysis": "Meta-Analysis[ptyp]",
            "Case Report": "Case Reports[ptyp]"
        }
        parts.append(study_map.get(study_type, f'"{study_type}"[ptyp]'))
    if year_from:
        parts.append(f'("{year_from}"[Date - Publication] : "3000"[Date - Publication])')
    return " AND ".join(parts)


def main():
    parser = argparse.ArgumentParser(description="PubMed Search CLI")

    # 直接查询模式
    parser.add_argument("--query", help="直接输入查询语句")
    parser.add_argument("--max-results", type=int, default=5)

    # 构造查询模式
    parser.add_argument("--disease", help="疾病名称")
    parser.add_argument("--gene", help="基因名称")
    parser.add_argument("--treatment", help="治疗药物")
    parser.add_argument("--study-type", help="研究类型")
    parser.add_argument("--year-from", type=int, help="起始年份")

    args = parser.parse_args()

    # 构造查询或直接使用
    if args.query:
        query = args.query
    elif args.disease:
        query = construct_query(args.disease, args.gene, args.treatment, args.study_type, args.year_from)
    else:
        print("错误: 必须提供 --query 或 --disease", file=sys.stderr)
        sys.exit(1)

    # 执行搜索
    search_result = esearch(query, args.max_results)

    if search_result["status"] == "error":
        print(json.dumps(search_result, ensure_ascii=False, indent=2))
        sys.exit(1)

    pmids = search_result.get("pmid_list", [])
    total = search_result.get("total_count", 0)

    if not pmids:
        result = {
            "status": "success",
            "query": query,
            "total_count": 0,
            "articles": []
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 获取摘要
    fetch_result = efetch(pmids)

    if fetch_result["status"] == "error":
        result = {
            "status": "partial",
            "query": query,
            "total_count": total,
            "error": fetch_result.get("error"),
            "pmids": pmids
        }
    else:
        result = {
            "status": "success",
            "query": query,
            "total_count": total,
            "articles": fetch_result.get("articles", [])
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
