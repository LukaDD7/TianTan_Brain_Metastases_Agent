#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
oncokb_tools.py - OncoKB API 原子工具集 (L1 层)

严格遵循 Single Brain 架构原则：
- 只做 API 管道，不做临床解读
- 返回原始 JSON，由 L3 Agent 进行认知推理
"""

import os
import requests
from typing import Dict, Optional
from langchain.tools import tool

# OncoKB API 配置
ONCOKB_BASE_URL = "https://www.oncokb.org/api/v1"
ONCOKB_API_KEY = os.environ.get("ONCOKB_API_KEY", "")


def _make_oncokb_request(endpoint: str, params: Dict) -> Dict:
    """
    发送 OncoKB API 请求的底层函数。

    Args:
        endpoint: API 端点路径 (如 "/annotate/mutations/byProteinChange")
        params: 查询参数

    Returns:
        API 返回的 JSON Dict，或包含 error 字段的错误信息
    """
    if not ONCOKB_API_KEY:
        return {
            "error": "ONCOKB_API_KEY not found. Please set ONCOKB_API_KEY environment variable.",
            "status": "error"
        }

    url = f"{ONCOKB_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {ONCOKB_API_KEY}",
        "Accept": "application/json"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            return {"error": "Invalid ONCOKB_API_KEY", "status": "error", "details": str(e)}
        elif response.status_code == 404:
            return {"error": "Variant not found in OncoKB", "status": "not_found"}
        else:
            return {"error": f"HTTP {response.status_code}", "status": "error", "details": str(e)}

    except requests.exceptions.Timeout:
        return {"error": "Request timeout", "status": "error"}

    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}", "status": "error"}


@tool
def oncokb_annotate_mutation(
    gene: str,
    alteration: str,
    tumor_type: str = "Non-Small Cell Lung Cancer"
) -> Dict:
    """
    查询 OncoKB 获取点突变 (SNV/Indel) 的临床注释信息。

    使用场景：病历中出现 V600E、L858R、G12C 等点突变时调用。

    Args:
        gene: 基因符号 (如 "BRAF", "EGFR", "KRAS")
        alteration: 突变描述 (如 "V600E", "L858R", "G12C")
        tumor_type: 肿瘤类型 (默认 "Non-Small Cell Lung Cancer")，支持如:
                   "Melanoma", "Colorectal Cancer", "Breast Cancer" 等

    Returns:
        OncoKB API 原始 JSON，包含以下关键字段:
        - oncogenic: 致癌性评估 ("Oncogenic", "Likely Oncogenic", "Unknown", "Likely Neutral")
        - mutationEffect: 突变效应描述
        - treatments: 治疗建议列表 (含证据等级)
        - highestSensitiveLevel: 最高敏感证据等级 (如 "LEVEL_1")
        - highestResistanceLevel: 最高耐药证据等级 (如 "LEVEL_R1")
    """
    params = {
        "hugoSymbol": gene,
        "alteration": alteration,
        "tumorType": tumor_type
    }

    return _make_oncokb_request("/annotate/mutations/byProteinChange", params)


@tool
def oncokb_annotate_structural_variant(
    gene1: str,
    gene2: str,
    tumor_type: str
) -> Dict:
    """
    查询 OncoKB 获取基因融合 (Fusion) 的临床注释信息。

    使用场景：病历中出现 "EML4-ALK fusion", "BCR-ABL fusion", "融合基因" 等时调用。

    Args:
        gene1: 第一个基因符号 (如 "EML4", "BCR")
        gene2: 第二个基因符号 (如 "ALK", "ABL1")
        tumor_type: 肿瘤类型 (如 "Non-Small Cell Lung Cancer", "Chronic Myeloid Leukemia")

    Returns:
        OncoKB API 原始 JSON，包含以下关键字段:
        - oncogenic: 致癌性评估
        - treatments: 针对该融合的治疗建议
        - highestSensitiveLevel: 最高敏感证据等级
        - highestResistanceLevel: 最高耐药证据等级
    """
    params = {
        "hugoSymbolA": gene1,
        "hugoSymbolB": gene2,
        "tumorType": tumor_type,
        "structuralVariantType": "FUSION",
        "isFunctionalFusion": "true"
    }

    return _make_oncokb_request("/annotate/structuralVariants", params)


@tool
def oncokb_annotate_cna(
    gene: str,
    alteration_type: str,
    tumor_type: str
) -> Dict:
    """
    查询 OncoKB 获取基因拷贝数变异 (CNA) 的临床注释信息。

    使用场景：病历中出现 "EGFR amplification", "BRCA1 deletion", "基因扩增", "基因缺失" 等时调用。

    Args:
        gene: 基因符号 (如 "EGFR", "BRCA1", "MYC")
        alteration_type: 变异类型，必须是 "Amplification" 或 "Deletion"
        tumor_type: 肿瘤类型 (如 "Glioblastoma", "Breast Cancer")

    Returns:
        OncoKB API 原始 JSON，包含以下关键字段:
        - oncogenic: 致癌性评估
        - treatments: 针对该 CNA 的治疗建议
        - highestSensitiveLevel: 最高敏感证据等级
        - highestResistanceLevel: 最高耐药证据等级
    """
    if alteration_type not in ["Amplification", "Deletion"]:
        return {
            "error": f"Invalid alteration_type: {alteration_type}. Must be 'Amplification' or 'Deletion'",
            "status": "error"
        }

    params = {
        "hugoSymbol": gene,
        "copyNumberAlterationType": alteration_type.upper(),
        "tumorType": tumor_type
    }

    return _make_oncokb_request("/annotate/copyNumberAlterations", params)
