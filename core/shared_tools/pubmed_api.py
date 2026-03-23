#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PubMed API - L1 原子工具

纯净的 API 封装，不含医学推理。
大段内容写入 Sandbox 文件，返回文件路径。
"""

import os
import json
import time
from typing import List, Optional, Dict, Any
from datetime import datetime


# =============================================================================
# 常量定义
# =============================================================================

# NCBI E-utilities API 基础 URL
EUTILS_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# 默认配置
DEFAULT_MAX_RESULTS = 5
DEFAULT_SORT = "relevance"


# =============================================================================
# PubMed Client (内联版本，消除 L1 对 L2 的依赖)
# =============================================================================

class PubMedClient:
    """
    NCBI PubMed API 客户端。

    功能：
    1. ESearch - 搜索文献并获取 PMID 列表
    2. EFetch - 根据 PMID 获取文献详情
    3. 自动速率限制处理
    4. 错误处理和重试
    """

    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        self.email = email or os.environ.get("PUBMED_EMAIL")
        self.api_key = api_key or os.environ.get("E_UTILITIES_API")

        if not self.email:
            from core.skill import SkillExecutionError
            raise SkillExecutionError(
                "PUBMED_EMAIL 环境变量未设置。\n"
                "请在 NCBI 免费注册获取：https://www.ncbi.nlm.nih.gov/account/"
            )

        self.request_interval = 0.34 if self.api_key else 0.34
        self._last_request_time = 0.0
        self.session = self._create_session()

    def _create_session(self):
        """创建 HTTP 会话"""
        try:
            import requests
            session = requests.Session()
            return session
        except ImportError:
            from core.skill import SkillExecutionError
            raise SkillExecutionError("requests 库未安装。请运行：pip install requests")

    def _rate_limit(self):
        """处理请求速率限制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self._last_request_time = time.time()

    def _request(self, method: str, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        url = f"{EUTILS_BASE}{endpoint}"
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

            content_type = response.headers.get("Content-Type", "")
            if "json" in content_type:
                return response.json()
            else:
                return self._parse_xml(response.text)

        except Exception as e:
            from core.skill import SkillExecutionError
            raise SkillExecutionError(f"PubMed API 请求失败：{str(e)}")

    def _parse_xml(self, xml_text: str) -> Dict[str, Any]:
        """解析 XML 响应"""
        try:
            from Bio import Entrez
            from io import StringIO
            handle = StringIO(xml_text)
            records = Entrez.read(handle)
            return records
        except ImportError:
            from core.skill import SkillExecutionError
            raise SkillExecutionError("biopython 库未安装。请运行：pip install biopython")
        except Exception as e:
            return {"raw_xml": xml_text, "parse_error": str(e)}

    def search(
        self,
        query: str,
        max_results: int = DEFAULT_MAX_RESULTS,
        sort: str = DEFAULT_SORT,
        use_mesh: bool = False
    ) -> List[str]:
        """搜索 PubMed 文献并返回 PMID 列表"""
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
        """构建 PubMed 搜索查询"""
        if not use_mesh:
            return query
        return f'"{query}"[Title/Abstract]'

    def fetch_details(self, pmid_list: List[str], retmode: str = "xml") -> List[Dict[str, Any]]:
        """根据 PMID 列表获取文献详细信息"""
        if not pmid_list:
            return []

        clean_pmids = [str(p) for p in pmid_list if str(p).isdigit()]
        if not clean_pmids:
            return []

        xml_bytes = self._fetch_details_binary(clean_pmids)
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
        """解析 EFetch XML 响应"""
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
                    print(f"Error parsing article: {e}")
                    continue
            return results
        except Exception as e:
            return [{"error": f"Failed to parse PubMed XML: {str(e)}"}]

    def _extract_article_data(self, article: Dict) -> Dict[str, Any]:
        """从 PubMed 文章中提取关键数据"""
        medline = article.get("MedlineCitation", {})
        article_data = medline.get("Article", {})
        journal = article_data.get("Journal", {})

        pmid = str(medline.get("PMID", ""))
        title = article_data.get("ArticleTitle", "No Title")
        abstract_text = self._extract_abstract(article_data)
        journal_title = journal.get("Title", "Unknown Journal")
        pub_date = journal.get("JournalIssue", {}).get("PubDate", {})
        year = str(pub_date.get("Year", "Unknown"))

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
            "authors": authors[:10],
            "link": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        }

    def _extract_abstract(self, article_data: Dict) -> str:
        """提取摘要"""
        abstract_data = article_data.get("Abstract", None)
        if not abstract_data:
            return "No Abstract Available."

        abstract_list = abstract_data.get("AbstractText", [])
        if isinstance(abstract_list, list):
            parts = []
            for item in abstract_list:
                if hasattr(item, "attributes") and "Label" in item.attributes:
                    label = item.attributes["Label"]
                    parts.append(f"{label}: {item}")
                else:
                    parts.append(str(item))
            return "\n".join(parts)
        else:
            return str(abstract_list)


# =============================================================================
# 核心函数
# =============================================================================

def search_pubmed(
    query: str,
    max_results: int = 20,
    use_mesh: bool = False,
    sandbox_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    搜索 PubMed 文献，返回 PMID 列表。

    Args:
        query: 检索词
        max_results: 最大结果数
        use_mesh: 是否使用 MeSH 术语增强搜索
        sandbox_root: Sandbox 工作目录

    Returns:
        {
            "status": "success" | "error",
            "query": str,
            "pmid_count": int,
            "pmid_list_file": str,
            "preview": [str, ...]
        }
    """
    client = PubMedClient()

    try:
        pmids = client.search(query, max_results=max_results, use_mesh=use_mesh)
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "query": query
        }

    pmids_json = json.dumps(pmids, indent=2)
    filename = f"pubmed_pmids_{_safe_filename(query)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    pmid_file = _write_to_sandbox(pmids_json, filename, sandbox_root)

    return {
        "status": "success",
        "query": query,
        "pmid_count": len(pmids),
        "pmid_list_file": pmid_file,
        "preview": [str(p) for p in pmids[:5]]
    }


def fetch_pubmed_details(
    pmid_list: List[str],
    sandbox_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    根据 PMID 列表获取文献详情。

    Args:
        pmid_list: PMID 列表
        sandbox_root: Sandbox 工作目录

    Returns:
        {
            "status": "success" | "error",
            "article_count": int,
            "details_file": str,
            "preview": [...]
        }
    """
    client = PubMedClient()

    try:
        articles = client.fetch_details(pmid_list)
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

    articles_json = json.dumps(articles, ensure_ascii=False, indent=2)
    filename = f"pubmed_details_{len(articles)}articles_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    details_file = _write_to_sandbox(articles_json, filename, sandbox_root)

    preview = [
        {"pmid": a.get("pmid"), "title": a.get("title"), "journal": a.get("journal")}
        for a in articles[:3]
    ]

    return {
        "status": "success",
        "article_count": len(articles),
        "details_file": details_file,
        "preview": preview
    }


# =============================================================================
# 工具函数
# =============================================================================

def _safe_filename(text: str, max_len: int = 30) -> str:
    """生成安全的文件名片"""
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in text)
    return safe[:max_len]


def _write_to_sandbox(content: str, filename: str, sandbox_root: Optional[str] = None) -> str:
    """
    写入 Sandbox 文件，返回绝对路径。

    路径解析优先级：
    1. SANDBOX_ROOT 环境变量（最高优先级，唯一真理）
    2. 动态推导的备用路径（基于当前文件位置）
    """
    root = os.environ.get("SANDBOX_ROOT")

    if root:
        pass
    elif sandbox_root and sandbox_root == "/sandbox":
        root = _get_fallback_sandbox_root()
    elif sandbox_root:
        root = sandbox_root
    else:
        root = _get_fallback_sandbox_root()

    os.makedirs(root, exist_ok=True)
    file_path = os.path.join(root, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return os.path.abspath(file_path)


def _get_fallback_sandbox_root() -> str:
    """
    动态推导备用 Sandbox 根目录。

    基于当前文件位置（core/shared_tools/pubmed_api.py）向上推导：
    core/shared_tools -> core -> 项目根目录 -> workspace/sandbox
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, '../../workspace/sandbox'))
