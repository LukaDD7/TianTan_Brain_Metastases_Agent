#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OncoKB API Client

封装 OncoKB 公共 API 调用，处理认证、重试、错误处理。
API 文档：https://docs.oncokb.org/
"""

import os
import time
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# 本地基类
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.skill import SkillExecutionError


# =============================================================================
# 常量定义
# =============================================================================

# OncoKB API 基础 URL
# 参考现有代码实现，使用 www.oncokb.org 作为认证 API
ONCOKB_AUTHENTICATED_API = "https://www.oncokb.org/api/v1"

# 默认重试配置
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 1.0  # 秒


# =============================================================================
# 数据类型
# =============================================================================

@dataclass
class GeneQuery:
    """基因查询参数"""
    hugo_symbol: str
    variant: Optional[str] = None


@dataclass
class DrugQuery:
    """药物查询参数"""
    hugo_symbol: str
    variant: Optional[str] = None
    drug_name: Optional[str] = None


@dataclass
class BiomarkerQuery:
    """生物标志物查询参数"""
    biomarker_name: str
    tumor_type: Optional[str] = None


@dataclass
class TumorTypeQuery:
    """癌症类型查询参数"""
    tumor_type: str
    evidence_level: Optional[str] = None


# =============================================================================
# OncoKB Client
# =============================================================================

class OncoKBClient:
    """
    OncoKB API 客户端。

    功能：
    1. 自动选择公共 API 或认证 API
    2. 请求速率限制处理
    3. 自动重试
    4. 统一错误处理

    使用示例：
        client = OncoKBClient(api_token="your_token")
        result = client.query_variant("EGFR", "L858R")
        result = client.query_drug("BRAF", "V600E", "Vemurafenib")
    """

    def __init__(self, api_token: Optional[str] = None):
        """
        初始化 OncoKB 客户端。

        Args:
            api_token: OncoKB API Token，可选。如果没有提供，
                       将尝试从环境变量 `ONCOKB_API_KEY` 读取
        """
        # 使用 ONCOKB_API_KEY 环境变量 (与现有代码保持一致)
        self.api_token = api_token or os.environ.get("ONCOKB_API_KEY")
        self.base_url = ONCOKB_AUTHENTICATED_API
        self.session = self._create_session()
        self._last_request_time = 0
        self._min_request_interval = 0.5  # 认证 API 最小请求间隔

    def _create_session(self):
        """创建 HTTP 会话"""
        try:
            import requests
            session = requests.Session()
            if self.api_token:
                session.headers["Authorization"] = f"Bearer {self.api_token}"
            session.headers["Content-Type"] = "application/json"
            session.headers["Accept"] = "application/json"
            session.headers["User-Agent"] = "TianTan-Brain-Metastases-Agent/2.1.0"
            return session
        except ImportError:
            raise SkillExecutionError(
                "requests 库未安装。请运行：pip install requests"
            )

    def _rate_limit(self):
        """处理请求速率限制"""
        # 认证 API 也有速率限制，但更宽松
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        max_retries: int = DEFAULT_MAX_RETRIES
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求。

        Args:
            method: HTTP 方法 (GET/POST)
            endpoint: API 端点路径
            params: URL 查询参数
            json_data: JSON 请求体
            max_retries: 最大重试次数

        Returns:
            JSON 响应

        Raises:
            SkillExecutionError: 请求失败
        """
        url = f"{self.base_url}{endpoint}"
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                self._rate_limit()

                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data,
                    timeout=30
                )

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    raise SkillExecutionError(
                        "API Token 无效或缺失。请检查 ONCOKB_API_KEY 环境变量。"
                    )
                elif response.status_code == 404:
                    # 404 不一定代表错误，可能是该变异未被收录
                    return {"error": "Not found", "message": "未找到请求的资源", "status": 404}
                elif response.status_code == 429:
                    # 速率限制，等待后重试
                    retry_after = int(response.headers.get("Retry-After", 5))
                    time.sleep(retry_after)
                    continue
                elif response.status_code >= 500:
                    # 服务器错误，稍后重试
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    last_error = SkillExecutionError(
                        f"API 请求失败：{response.status_code} - {response.text[:200]}"
                    )

            except requests.exceptions.RequestException as e:
                last_error = e
                time.sleep(2 ** attempt)  # 指数退避
            except Exception as e:
                last_error = e
                time.sleep(2 ** attempt)  # 指数退避

        if last_error:
            raise last_error if isinstance(last_error, SkillExecutionError) else SkillExecutionError(f"API 请求失败：{last_error}")
        raise SkillExecutionError("API 请求失败：达到最大重试次数")

    # ==================== 变异查询 ====================

    def query_variant(
        self,
        hugo_symbol: str,
        variant: str,
        tumor_type: Optional[str] = None,
        include_evidence: bool = True
    ) -> Dict[str, Any]:
        """
        查询基因变异的临床意义。

        Args:
            hugo_symbol: 基因符号 (如 "EGFR")
            variant: 变异描述 (如 "L858R", "V600E")
            tumor_type: 可选的癌症类型
            include_evidence: 是否包含详细证据

        Returns:
            变异注释结果
        """
        # 使用正确的端点：/annotate/mutations/byProteinChange
        endpoint = "/annotate/mutations/byProteinChange"
        params = {
            "hugoSymbol": hugo_symbol,
            "alteration": variant,
            "tumorType": tumor_type
        }
        # 移除 evidenceType 参数，因为它可能导致 500 错误
        # 完整的证据信息会包含在响应中

        # 移除 None 值
        params = {k: v for k, v in params.items() if v is not None}

        return self._request("GET", endpoint, params=params)

    def query_variant_by_genomic_change(
        self,
        chromosome: str,
        start: int,
        end: int,
        variant_type: str,
        include_evidence: bool = True
    ) -> Dict[str, Any]:
        """
        通过基因组坐标查询变异。

        Args:
            chromosome: 染色体 (如 "1", "X")
            start: 起始位置
            end: 结束位置
            variant_type: 变异类型 ("SNV", "INDEL", "FUSION")
            include_evidence: 是否包含详细证据

        Returns:
            变异注释结果
        """
        endpoint = "/annotate/variants/byGenomicChange"
        params = {
            "chromosome": chromosome,
            "start": start,
            "end": end,
            "variantType": variant_type,
            "includeEvidence": str(include_evidence).lower()
        }

        return self._request("GET", endpoint, params=params)

    # ==================== 药物查询 ====================

    def query_drug_sensitivity(
        self,
        hugo_symbol: str,
        variant: str,
        drug_name: Optional[str] = None,
        tumor_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询药物敏感性。

        Args:
            hugo_symbol: 基因符号
            variant: 变异描述
            drug_name: 可选的药物名称
            tumor_type: 可选的癌症类型

        Returns:
            药物敏感性结果
        """
        endpoint = "/annotate/tumorTypes"
        params = {
            "hugoSymbol": hugo_symbol,
            "alteration": variant,
            "tumorType": tumor_type
        }

        params = {k: v for k, v in params.items() if v is not None}

        result = self._request("GET", endpoint, params=params)

        # 过滤特定药物 (如果指定)
        if drug_name and "treatments" in result:
            drug_name_lower = drug_name.lower()
            filtered_treatments = []
            for treatment in result["treatments"]:
                drug_info = treatment.get("drug", {})
                if drug_name_lower in drug_info.get("drugName", "").lower():
                    filtered_treatments.append(treatment)
            result["treatments"] = filtered_treatments

        return result

    def query_drug_info(self, drug_name: str) -> Dict[str, Any]:
        """
        查询药物基本信息。

        Args:
            drug_name: 药物名称

        Returns:
            药物信息
        """
        endpoint = f"/drugs/{drug_name}"
        return self._request("GET", endpoint)

    # ==================== 生物标志物查询 ====================

    def query_biomarker(
        self,
        biomarker_name: str,
        tumor_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询生物标志物信息。

        Args:
            biomarker_name: 生物标志物名称 (如 "MSI-H", "TMB-H")
            tumor_type: 可选的癌症类型

        Returns:
            生物标志物信息
        """
        endpoint = "/annotate/biomarkers"
        params = {
            "biomarkerName": biomarker_name,
            "tumorType": tumor_type
        }

        params = {k: v for k, v in params.items() if v is not None}

        return self._request("GET", endpoint, params=params)

    # ==================== 癌症类型查询 ====================

    def query_tumor_type(
        self,
        tumor_type: str,
        evidence_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询特定癌症类型的治疗推荐。

        Args:
            tumor_type: 癌症类型 (如 "Non-Small Cell Lung Cancer")
            evidence_level: 可选的证据等级过滤 (如 "LEVEL_1", "LEVEL_2A")

        Returns:
            治疗推荐列表
        """
        endpoint = "/tumorTypes"
        params = {"tumorType": tumor_type}

        if evidence_level:
            params["evidenceLevel"] = evidence_level

        return self._request("GET", endpoint, params=params)

    # ==================== 证据查询 ====================

    def query_evidence(self, evidence_uuid: str) -> Dict[str, Any]:
        """
        获取特定证据的详细信息。

        Args:
            evidence_uuid: 证据 UUID

        Returns:
            证据详情
        """
        endpoint = f"/evidence/{evidence_uuid}"
        return self._request("GET", endpoint)

    def query_evidence_types(self) -> List[Dict[str, Any]]:
        """
        获取所有证据类型定义。

        Returns:
            证据类型列表
        """
        endpoint = "/evidence/types"
        return self._request("GET", endpoint)

    # ==================== 基因查询 ====================

    def query_gene(self, hugo_symbol: str) -> Dict[str, Any]:
        """
        查询基因基本信息。

        Args:
            hugo_symbol: 基因符号

        Returns:
            基因信息
        """
        endpoint = f"/genes/{hugo_symbol}"
        return self._request("GET", endpoint)

    # ==================== 批量查询 ====================

    def batch_query_variants(
        self,
        queries: List[Dict[str, str]],
        include_evidence: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量查询多个变异。

        Args:
            queries: 查询列表，每项包含 {"hugoSymbol": ..., "alteration": ...}
            include_evidence: 是否包含详细证据

        Returns:
            结果列表
        """
        endpoint = "/annotate/variants/byProteinChanges"
        params = {
            "includeEvidence": str(include_evidence).lower()
        }

        return self._request("POST", endpoint, params=params, json_data={
            "queries": queries
        })


# =============================================================================
# 辅助函数
# =============================================================================

def get_client(api_token: Optional[str] = None) -> OncoKBClient:
    """获取 OncoKB 客户端实例"""
    return OncoKBClient(api_token=api_token)


def format_variant_response(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    格式化变异查询响应为标准格式。

    Args:
        result: OncoKB API 原始响应

    Returns:
        格式化后的响应
    """
    return {
        "query_type": "variant",
        "gene": result.get("gene", {}),
        "variant": result.get("variant", result.get("alteration", "")),
        "oncogenicity": result.get("oncogenic", ""),
        "oncogenicity_explanation": result.get("oncogenicity", ""),
        "treatments": {
            "sensitive": result.get("treatments", []),
            "resistant": result.get("resistantTreatments", [])
        },
        "summary": result.get("summary", ""),
        "evidence": result.get("evidence", []),
        "last_updated": result.get("lastUpdate", "")
    }
