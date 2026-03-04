#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PubMed Search Skill - 主查询入口

提供统一的 PubMed 文献查询接口，支持多种查询类型。
"""

import os
import json
from typing import Optional, Any, Dict, List
from enum import Enum

# Pydantic v2
from pydantic import BaseModel, Field

# 本地基类
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.skill import BaseSkill, SkillContext, SkillExecutionError

# 同目录导入
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from pubmed_client import PubMedClient


# =============================================================================
# 输入 Schema (Pydantic 模型)
# =============================================================================

class QueryType(str, Enum):
    """查询类型枚举"""
    SEARCH = "search"
    DETAILS = "details"
    CASE_REPORTS = "case_reports"
    CLINICAL_TRIAL = "clinical_trial"


class PubMedSearchInput(BaseModel):
    """
    PubMed 搜索的输入参数。

    根据 query_type 不同，需要的参数也不同：
    - search: 需要 keywords
    - details: 需要 pmid_list
    - case_reports: 需要 disease 和 comorbidity
    - clinical_trial: 需要 keywords
    """

    query_type: QueryType = Field(
        ...,
        description="查询类型",
        examples=["search", "details", "case_reports", "clinical_trial"]
    )

    # === 搜索相关参数 ===
    keywords: Optional[str] = Field(
        default=None,
        description="搜索关键词，用于 search 和 clinical_trial 查询",
        examples=["EGFR L858R NSCLC treatment", "Osimertinib brain metastases"]
    )

    # === 文献详情相关参数 ===
    pmid_list: Optional[List[str]] = Field(
        default=None,
        description="PMID 列表，用于 details 查询",
        examples=[["15118073", "15118125", "34526717"]]
    )

    # === 病例报告相关参数 ===
    disease: Optional[str] = Field(
        default=None,
        description="疾病名称，用于 case_reports 查询",
        examples=["Lung Cancer", "Non-Small Cell Lung Cancer"]
    )

    comorbidity: Optional[str] = Field(
        default=None,
        description="合并症，用于 case_reports 查询",
        examples=["Systemic Lupus Erythematosus", "HIV"]
    )

    treatment: Optional[str] = Field(
        default=None,
        description="治疗手段，用于 case_reports 查询 (可选)",
        examples=["Pembrolizumab", "PD-1 inhibitor"]
    )

    # === 通用参数 ===
    max_results: int = Field(
        default=5,
        description="最大结果数，默认 5，最多 100",
        ge=1,
        le=100
    )

    sort: str = Field(
        default="relevance",
        description="排序方式：relevance (相关性) 或 date (日期)",
        examples=["relevance", "date"]
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "query_type": "search",
                    "keywords": "EGFR L858R NSCLC treatment",
                    "max_results": 5
                },
                {
                    "query_type": "details",
                    "pmid_list": ["15118073", "15118125"]
                },
                {
                    "query_type": "case_reports",
                    "disease": "Lung Cancer",
                    "comorbidity": "Lupus",
                    "treatment": "PD-1"
                },
                {
                    "query_type": "clinical_trial",
                    "keywords": "Osimertinib brain metastases",
                    "max_results": 10
                }
            ]
        }


# =============================================================================
# Skill 实现
# =============================================================================

class PubMedSearch(BaseSkill[PubMedSearchInput]):
    """
    PubMed 文献搜索 Skill。

    支持多种查询类型：
    1. search - 根据关键词搜索文献
    2. details - 根据 PMID 获取文献详情
    3. case_reports - 搜索罕见病例报告
    4. clinical_trial - 搜索临床试验文献
    """

    name = "search_pubmed"
    description = (
        "【触发条件】当需要为被排除的治疗方案（rejected_alternatives）寻找文献证据等级支持，或当 OncoKB 未提供足够治疗推荐时补充循证依据，或查询罕见病例报告（如特殊合并症）时触发。\n"
        "【查询范围】用于查询 PubMed 生物医学文献数据库，获取文献摘要、详情或搜索特定主题的文献。\n"
        "【支持类型】search(文献搜索)、details(文献详情)、case_reports(罕见病例报告)、clinical_trial(临床试验文献)。\n"
        "【医疗严谨性】PubMed 包含超过 3500 万篇生物医学文献，可用于验证被排除方案的合理性（如'手术切除：证据不足（PubMed 检索未发现支持性文献）'），或提供罕见病例的治疗参考。\n"
        "【注意事项】需要设置环境变量 PUBMED_EMAIL 和 E_UTILITIES_API。"
    )
    input_schema_class = PubMedSearchInput

    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        super().__init__()
        self.email = email or os.environ.get("PUBMED_EMAIL")
        self.api_key = api_key or os.environ.get("E_UTILITIES_API")
        # 配置重试策略
        self.retry_config.max_retries = 3
        self.retry_config.initial_delay_ms = 1000

    @property
    def input_schema(self) -> Dict[str, Any]:
        return self.input_schema_class.model_json_schema()

    def execute(self, args: PubMedSearchInput, context: Optional[SkillContext] = None) -> str:
        """
        执行 PubMed 查询。

        Args:
            args: 已验证的输入参数
            context: 可选的跨技能上下文

        Returns:
            JSON 格式的查询结果

        Raises:
            SkillExecutionError: 执行失败时抛出
        """
        try:
            # 创建 API 客户端
            client = PubMedClient(email=self.email, api_key=self.api_key)

            # 根据查询类型执行不同查询
            result = self._dispatch_query(client, args)

            # 格式化输出
            output = {
                "query_type": args.query_type.value,
                "success": True,
                "data": result,
                "metadata": {
                    "max_results": args.max_results,
                    "sort": args.sort
                }
            }

            # 存入上下文 (如果提供)
            if context:
                context.set(f"pubmed_result_{args.query_type.value}", result)

            return json.dumps(output, ensure_ascii=False, indent=2)

        except SkillExecutionError:
            raise
        except Exception as e:
            raise SkillExecutionError(f"PubMed 查询失败：{str(e)}") from e

    def _dispatch_query(self, client: PubMedClient, args: PubMedSearchInput) -> Dict[str, Any]:
        """
        根据查询类型分发到具体查询方法。

        Args:
            client: PubMed 客户端
            args: 查询参数

        Returns:
            查询结果
        """
        query_type = args.query_type.value

        if query_type == "search":
            return self._search(client, args)
        elif query_type == "details":
            return self._details(client, args)
        elif query_type == "case_reports":
            return self._case_reports(client, args)
        elif query_type == "clinical_trial":
            return self._clinical_trial(client, args)
        else:
            raise SkillExecutionError(f"未知的查询类型：{query_type}")

    def _search(self, client: PubMedClient, args: PubMedSearchInput) -> Dict[str, Any]:
        """文献搜索"""
        if not args.keywords:
            raise SkillExecutionError("search 查询需要指定 keywords")

        # 搜索获取 PMID 列表
        pmids = client.search(
            query=args.keywords,
            max_results=args.max_results,
            sort=args.sort
        )

        # 获取文献详情
        articles = client.fetch_details(pmids) if pmids else []

        return {
            "search_query": args.keywords,
            "total_results": len(pmids),
            "pmids": pmids,
            "articles": articles
        }

    def _details(self, client: PubMedClient, args: PubMedSearchInput) -> Dict[str, Any]:
        """文献详情"""
        if not args.pmid_list:
            raise SkillExecutionError("details 查询需要指定 pmid_list")

        articles = client.fetch_details(args.pmid_list)

        return {
            "pmids_requested": args.pmid_list,
            "articles_found": len(articles),
            "articles": articles
        }

    def _case_reports(self, client: PubMedClient, args: PubMedSearchInput) -> Dict[str, Any]:
        """病例报告搜索"""
        if not args.disease:
            raise SkillExecutionError("case_reports 查询需要指定 disease")
        if not args.comorbidity:
            raise SkillExecutionError("case_reports 查询需要指定 comorbidity")

        pmids = client.search_case_reports(
            disease=args.disease,
            comorbidity=args.comorbidity,
            treatment=args.treatment,
            max_results=args.max_results
        )

        articles = client.fetch_details(pmids) if pmids else []

        return {
            "search_query": {
                "disease": args.disease,
                "comorbidity": args.comorbidity,
                "treatment": args.treatment
            },
            "total_results": len(pmids),
            "pmids": pmids,
            "articles": articles
        }

    def _clinical_trial(self, client: PubMedClient, args: PubMedSearchInput) -> Dict[str, Any]:
        """临床试验搜索"""
        if not args.keywords:
            raise SkillExecutionError("clinical_trial 查询需要指定 keywords")

        pmids = client.search_clinical_trials(
            topic=args.keywords,
            max_results=args.max_results
        )

        articles = client.fetch_details(pmids) if pmids else []

        return {
            "search_query": args.keywords,
            "search_type": "clinical_trial",
            "total_results": len(pmids),
            "pmids": pmids,
            "articles": articles
        }


# =============================================================================
# CLI 入口
# =============================================================================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="PubMed Search Skill")
    parser.add_argument("--query_type", required=True,
                        choices=["search", "details", "case_reports", "clinical_trial"])
    parser.add_argument("--keywords", help="搜索关键词")
    parser.add_argument("--pmid_list", nargs="+", help="PMID 列表")
    parser.add_argument("--disease", help="疾病名称")
    parser.add_argument("--comorbidity", help="合并症")
    parser.add_argument("--treatment", help="治疗手段")
    parser.add_argument("--max_results", type=int, default=5, help="最大结果数")
    parser.add_argument("--sort", default="relevance", choices=["relevance", "date"], help="排序方式")

    args = parser.parse_args()

    # 构建输入参数
    input_args = PubMedSearchInput(
        query_type=args.query_type,
        keywords=args.keywords,
        pmid_list=args.pmid_list,
        disease=args.disease,
        comorbidity=args.comorbidity,
        treatment=args.treatment,
        max_results=args.max_results,
        sort=args.sort
    )

    skill = PubMedSearch()

    try:
        result = skill.execute(input_args)
        print(result)
    except (SkillExecutionError, Exception) as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        exit(1)


if __name__ == "__main__":
    main()
