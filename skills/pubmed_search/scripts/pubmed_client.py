#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PubMed API Client

封装 NCBI E-utilities API 调用，处理检索、解析、错误处理。
API 文档：https://www.ncbi.nlm.nih.gov/books/NBK25501/
"""

import os
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# 本地基类
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.skill import SkillExecutionError


# =============================================================================
# 常量定义
# =============================================================================

# NCBI E-utilities API 基础 URL
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# 默认配置
DEFAULT_MAX_RESULTS = 5
DEFAULT_SORT = "relevance"
DEFAULT_RETRIEVAL_MODE = "abstract"


# =============================================================================
# PubMed Client
# =============================================================================

class PubMedClient:
    """
    NCBI PubMed API 客户端。

    功能：
    1. ESearch - 搜索文献并获取 PMID 列表
    2. EFetch - 根据 PMID 获取文献详情
    3. ESummary - 获取文献摘要信息
    4. 自动速率限制处理
    5. 错误处理和重试

    使用示例：
        client = PubMedClient()
        pmids = client.search("EGFR L858R NSCLC")
        articles = client.fetch_details(pmids)
    """

    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        """
        初始化 PubMed 客户端。

        Args:
            email: NCBI 注册邮箱，必需 (NCBI 要求)
            api_key: E-utilities API Key，可选 (提供更高访问限额)
        """
        self.email = email or os.environ.get("PUBMED_EMAIL")
        self.api_key = api_key or os.environ.get("E_UTILITIES_API")

        if not self.email:
            raise SkillExecutionError(
                "PUBMED_EMAIL 环境变量未设置。\n"
                "请在 NCBI 免费注册获取：https://www.ncbi.nlm.nih.gov/account/"
            )

        # 速率限制配置
        self.request_interval = 0.34 if self.api_key else 0.34  # 有 API Key 每秒 10 次，无 Key 每秒 3 次
        self._last_request_time = 0.0

        self.session = self._create_session()

    def _create_session(self):
        """创建 HTTP 会话"""
        try:
            import requests
            session = requests.Session()
            return session
        except ImportError:
            raise SkillExecutionError(
                "requests 库未安装。请运行：pip install requests"
            )

    def _rate_limit(self):
        """处理请求速率限制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self._last_request_time = time.time()

    def _request(self, method: str, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送 HTTP 请求。

        Args:
            method: HTTP 方法
            endpoint: API 端点路径
            params: 请求参数

        Returns:
            JSON 或 XML 响应解析后的字典
        """
        url = f"{EUTILS_BASE}{endpoint}"

        # 添加通用参数
        params["tool"] = "TianTan_Brain_Metastases_Agent"
        params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key

        self._rate_limit()

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                timeout=30
            )
            response.raise_for_status()

            # 检测响应类型
            content_type = response.headers.get("Content-Type", "")
            if "json" in content_type:
                return response.json()
            else:
                # XML 响应需要特殊处理
                return self._parse_xml(response.text)

        except Exception as e:
            raise SkillExecutionError(f"PubMed API 请求失败：{str(e)}")

    def _parse_xml(self, xml_text: str) -> Dict[str, Any]:
        """
        解析 XML 响应。

        使用 biopython 的 Entrez 模块解析 NCBI XML。
        """
        try:
            from Bio import Entrez
            from io import StringIO

            # 使用 Entrez 解析 XML
            handle = StringIO(xml_text)
            records = Entrez.read(handle)
            return records
        except ImportError:
            raise SkillExecutionError(
                "biopython 库未安装。请运行：pip install biopython"
            )
        except Exception as e:
            # 如果解析失败，返回原始文本
            return {"raw_xml": xml_text, "parse_error": str(e)}

    # ==================== 文献搜索 ====================

    def search(
        self,
        query: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        sort: str = DEFAULT_SORT,
        use_mesh: bool = False
    ) -> List[str]:
        """
        搜索 PubMed 文献并返回 PMID 列表。

        Args:
            query: 搜索查询字符串
            max_results: 最大结果数
            sort: 排序方式 ("relevance" 或 "date")
            use_mesh: 是否使用 MeSH 术语增强搜索 (默认 False)

        Returns:
            PMID 列表
        """
        # 构建搜索语句 (默认直接使用查询，不添加额外限定)
        search_term = self._build_search_query(query, use_mesh)

        params = {
            "db": "pubmed",
            "term": search_term,
            "retmax": max_results,
            "sort": sort,
            "retmode": "json"
        }

        result = self._request("GET", "/esearch.fcgi", params)

        if "esearchresult" in result:
            return result["esearchresult"].get("idlist", [])
        return []

    def _build_search_query(self, query: str, use_mesh: bool = True) -> str:
        """
        构建 PubMed 搜索查询。

        Args:
            query: 原始查询
            use_mesh: 是否使用 MeSH 术语

        Returns:
            增强后的搜索查询
        """
        if not use_mesh:
            return query

        # 简单实现：将查询包装在 [Title/Abstract] 中
        # 更复杂的实现可以使用 MeSH 术语转换
        return f'"{query}"[Title/Abstract]'

    # ==================== 文献详情获取 ====================

    def fetch_details(
        self,
        pmid_list: List[str],
        retmode: str = "xml"
    ) -> List[Dict[str, Any]]:
        """
        根据 PMID 列表获取文献详细信息。

        Args:
            pmid_list: PMID 列表
            retmode: 返回模式 ("xml" 或 "abstract")

        Returns:
            文献详情列表
        """
        if not pmid_list:
            return []

        # 过滤非法 PMID
        clean_pmids = [str(p) for p in pmid_list if str(p).isdigit()]
        if not clean_pmids:
            return []

        # 直接获取二进制响应
        xml_bytes = self._fetch_details_binary(clean_pmids)

        # 解析 XML
        return self._parse_efetch_xml_binary(xml_bytes)

    def _fetch_details_binary(self, pmid_list: List[str]) -> bytes:
        """获取二进制 XML 响应"""
        url = f"{EUTILS_BASE}/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": ",".join(pmid_list),
            "retmode": "xml",
            "tool": "TianTan_Brain_Metastases_Agent",
            "email": self.email
        }
        if self.api_key:
            params["api_key"] = self.api_key

        self._rate_limit()

        response = self.session.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.content

    def _parse_efetch_xml_binary(self, xml_bytes: bytes) -> List[Dict[str, Any]]:
        """
        解析 EFetch XML 响应（二进制模式）。

        提取：PMID、标题、摘要、期刊、年份、作者、链接
        """
        try:
            from Bio import Entrez
            from io import BytesIO

            handle = BytesIO(xml_bytes)
            records = Entrez.read(handle)

            results = []
            for article in records.get("PubmedArticle", []):
                try:
                    results.append(self._extract_article_data(article))
                except Exception as e:
                    # 单篇文章解析失败不应阻塞整个流程
                    print(f"Error parsing article: {e}")
                    continue

            return results

        except Exception as e:
            return [{"error": f"Failed to parse PubMed XML: {str(e)}"}]

    def _extract_article_data(self, article: Dict) -> Dict[str, Any]:
        """
        从 PubMed 文章中提取关键数据。
        """
        medline = article.get("MedlineCitation", {})
        article_data = medline.get("Article", {})
        journal = article_data.get("Journal", {})

        # 提取 PMID - 注意：PMID 是一个 Bio.Entrez 特殊对象
        pmid = str(medline.get("PMID", ""))

        # 提取标题
        title = article_data.get("ArticleTitle", "No Title")

        # 提取摘要 (处理结构化摘要)
        abstract_text = self._extract_abstract(article_data)

        # 提取期刊
        journal_title = journal.get("Title", "Unknown Journal")

        # 提取年份
        pub_date = journal.get("JournalIssue", {}).get("PubDate", {})
        year = str(pub_date.get("Year", "Unknown"))

        # 提取作者
        authors = []
        author_list = article_data.get("AuthorList", [])
        for author in author_list:
            if "LastName" in author:
                full_name = f"{author.get('LastName', '')} {author.get('ForeName', '')}".strip()
                if full_name:
                    authors.append(full_name)

        return {
            "pmid": pmid,
            "title": title,
            "abstract": abstract_text,
            "journal": journal_title,
            "year": year,
            "authors": authors[:10],  # 限制作者数量
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        }

    def _extract_abstract(self, article_data: Dict) -> str:
        """
        提取摘要 (处理结构化摘要和普通摘要)。
        """
        abstract_data = article_data.get("Abstract", None)
        if not abstract_data:
            return "No Abstract Available."

        abstract_list = abstract_data.get("AbstractText", [])

        if isinstance(abstract_list, list):
            # 处理结构化摘要
            parts = []
            for item in abstract_list:
                # 检查是否有 Label 属性 (结构化摘要的段落标题)
                if hasattr(item, "attributes") and "Label" in item.attributes:
                    label = item.attributes["Label"]
                    parts.append(f"{label}: {item}")
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        else:
            # 普通摘要
            return str(abstract_list)

    # ==================== 特殊搜索 ====================

    def search_case_reports(
        self,
        disease: str,
        comorbidity: str,
        treatment: Optional[str] = None,
        max_results: int = 5
    ) -> List[str]:
        """
        搜索特定合并症或治疗背景下的罕见病例报告。

        Args:
            disease: 主病 (如 "Lung Neoplasms")
            comorbidity: 合并症 (如 "Systemic Lupus Erythematosus")
            treatment: 治疗手段 (如 "Pembrolizumab")
            max_results: 最大结果数

        Returns:
            PMID 列表
        """
        # 构建组合查询语句
        terms = []
        terms.append(f'"{disease}"[Title/Abstract]')
        if comorbidity:
            terms.append(f'"{comorbidity}"[Title/Abstract]')
        if treatment:
            terms.append(f'"{treatment}"[Title/Abstract]')

        # 核心：限制文章类型为病例报告
        terms.append('"Case Reports"[Publication Type]')

        # 用 AND 连接所有条件
        query = " AND ".join(terms)

        return self.search(query, max_results=max_results, sort="relevance")

    def search_clinical_trials(
        self,
        topic: str,
        max_results: int = 10
    ) -> List[str]:
        """
        搜索临床试验相关文献。

        Args:
            topic: 主题
            max_results: 最大结果数

        Returns:
            PMID 列表
        """
        terms = []
        terms.append(f'"{topic}"[Title/Abstract]')
        terms.append('"Clinical Trial"[Publication Type]')

        query = " AND ".join(terms)
        return self.search(query, max_results=max_results, sort="date")


# =============================================================================
# 辅助函数
# =============================================================================

def get_client(email: Optional[str] = None, api_key: Optional[str] = None) -> PubMedClient:
    """获取 PubMed 客户端实例"""
    return PubMedClient(email=email, api_key=api_key)
