#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OncoKB API - L1 原子工具

纯净的 API 封装，不含医学推理。
大段内容写入 Sandbox 文件，返回文件路径。
"""

import os
import json
import time
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


# =============================================================================
# 常量定义
# =============================================================================

# OncoKB API 基础 URL
ONCOKB_AUTHENTICATED_API = "https://www.oncokb.org/api/v1"

# 默认重试配置
DEFAULT_MAX_RETRIES = 3


# =============================================================================
# OncoKB Client (内联版本，消除 L1 对 L2 的依赖)
# =============================================================================

class OncoKBClient:
    """
    OncoKB API 客户端。

    功能：
    1. 自动选择公共 API 或认证 API
    2. 请求速率限制处理
    3. 自动重试
    4. 统一错误处理
    """

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.environ.get("ONCOKB_API_KEY")
        self.base_url = ONCOKB_AUTHENTICATED_API
        self.session = self._create_session()
        self._last_request_time = 0
        self._min_request_interval = 0.5

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
            from core.skill import SkillExecutionError
            raise SkillExecutionError("requests 库未安装。请运行：pip install requests")

    def _rate_limit(self):
        """处理请求速率限制"""
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
        """发送 HTTP 请求"""
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
                    from core.skill import SkillExecutionError
                    raise SkillExecutionError("API Token 无效或缺失。请检查 ONCOKB_API_KEY 环境变量。")
                elif response.status_code == 404:
                    return {"error": "Not found", "message": "未找到请求的资源", "status": 404}
                elif response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    time.sleep(retry_after)
                    continue
                elif response.status_code >= 500:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    from core.skill import SkillExecutionError
                    last_error = SkillExecutionError(f"API 请求失败：{response.status_code} - {response.text[:200]}")

            except Exception as e:
                last_error = e
                time.sleep(2 ** attempt)

        if last_error:
            from core.skill import SkillExecutionError
            raise last_error if isinstance(last_error, Exception) and "SkillExecutionError" in str(type(last_error)) else SkillExecutionError(f"API 请求失败：{last_error}")
        from core.skill import SkillExecutionError
        raise SkillExecutionError("API 请求失败：达到最大重试次数")

    def query_variant(
        self,
        hugo_symbol: str,
        variant: str,
        tumor_type: Optional[str] = None,
        include_evidence: bool = True
    ) -> Dict[str, Any]:
        """查询基因变异的临床意义"""
        endpoint = "/annotate/mutations/byProteinChange"
        params = {
            "hugoSymbol": hugo_symbol,
            "alteration": variant,
            "tumorType": tumor_type
        }
        params = {k: v for k, v in params.items() if v is not None}
        return self._request("GET", endpoint, params=params)

    def query_drug_sensitivity(
        self,
        hugo_symbol: str,
        variant: str,
        drug_name: Optional[str] = None,
        tumor_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """查询药物敏感性"""
        endpoint = "/annotate/tumorTypes"
        params = {
            "hugoSymbol": hugo_symbol,
            "alteration": variant,
            "tumorType": tumor_type
        }
        params = {k: v for k, v in params.items() if v is not None}
        result = self._request("GET", endpoint, params=params)

        if drug_name and "treatments" in result:
            drug_name_lower = drug_name.lower()
            filtered_treatments = []
            for treatment in result["treatments"]:
                drug_info = treatment.get("drug", {})
                if drug_name_lower in drug_info.get("drugName", "").lower():
                    filtered_treatments.append(treatment)
            result["treatments"] = filtered_treatments
        return result


# =============================================================================
# 核心函数
# =============================================================================

def query_oncokb_variant(
    hugo_symbol: str,
    variant: str,
    tumor_type: Optional[str] = None,
    sandbox_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    查询 OncoKB 基因变异临床意义。

    Args:
        hugo_symbol: 基因符号 (如 BRAF)
        variant: 变异描述 (如 V600E)
        tumor_type: 肿瘤类型 (可选)
        sandbox_root: Sandbox 工作目录根路径

    Returns:
        {
            "status": "success" | "error",
            "gene": str,
            "variant": str,
            "oncogenicity": str,
            "level": str,
            "treatments_summary": {"sensitive": [...], "resistant": [...]},
            "full_evidence_file": str | None
        }
    """
    client = OncoKBClient()

    try:
        result = client.query_variant(
            hugo_symbol=hugo_symbol,
            variant=variant,
            tumor_type=tumor_type,
            include_evidence=True
        )
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "gene": hugo_symbol,
            "variant": variant
        }

    response = {
        "status": "success" if "error" not in result else "error",
        "gene": result.get("gene", {}).get("hugoSymbol", hugo_symbol),
        "variant": result.get("variant", result.get("alteration", variant)),
        "oncogenicity": result.get("oncogenic", "Unknown"),
        "level": result.get("level", "Unknown"),
        "treatments_summary": {
            "sensitive": [
                {"drug": t.get("drug", {}).get("drugName", ""), "level": t.get("level", "")}
                for t in result.get("treatments", [])[:10]
            ],
            "resistant": [
                {"drug": t.get("drug", {}).get("drugName", ""), "level": t.get("level", "")}
                for t in result.get("resistantTreatments", [])[:10]
            ]
        },
        "full_evidence_file": None
    }

    evidence = result.get("evidence", [])
    if evidence:
        evidence_json = json.dumps(evidence, ensure_ascii=False, indent=2)
        if len(evidence_json) > 5000:
            filename = f"oncokb_{hugo_symbol}_{variant}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            file_path = _write_to_sandbox(evidence_json, filename, sandbox_root)
            response["full_evidence_file"] = file_path

    return response


def query_oncokb_drug(
    hugo_symbol: str,
    variant: str,
    drug_name: str,
    tumor_type: Optional[str] = None,
    sandbox_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    查询特定药物的敏感性。

    Args:
        hugo_symbol: 基因符号
        variant: 变异描述
        drug_name: 药物名称
        tumor_type: 肿瘤类型 (可选)
        sandbox_root: Sandbox 工作目录

    Returns:
        {
            "status": "success" | "error",
            "sensitivity": "sensitive" | "resistant" | "unknown",
            "level": str,
            "full_response_file": str | None
        }
    """
    client = OncoKBClient()

    try:
        result = client.query_drug_sensitivity(
            hugo_symbol=hugo_symbol,
            variant=variant,
            drug_name=drug_name,
            tumor_type=tumor_type
        )
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

    sensitivity = "unknown"
    level = "Unknown"

    treatments = result.get("treatments", [])
    for t in treatments:
        drug_info = t.get("drug", {})
        if drug_name.lower() in drug_info.get("drugName", "").lower():
            sensitivity = "sensitive" if t.get("sensitivity") == "sensitive" else "resistant"
            level = t.get("level", "Unknown")
            break

    response = {
        "status": "success",
        "sensitivity": sensitivity,
        "level": level,
        "full_response_file": None
    }

    result_json = json.dumps(result, ensure_ascii=False, indent=2)
    if len(result_json) > 5000:
        filename = f"oncokb_drug_{drug_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        file_path = _write_to_sandbox(result_json, filename, sandbox_root)
        response["full_response_file"] = file_path

    return response


# =============================================================================
# 工具函数
# =============================================================================

def _write_to_sandbox(content: str, filename: str, sandbox_root: Optional[str] = None) -> str:
    """
    写入 Sandbox 文件，返回绝对路径。

    路径解析优先级：
    1. SANDBOX_ROOT 环境变量（最高优先级，唯一真理）
    2. 动态推导的备用路径（基于当前文件位置）

    Args:
        content: 文件内容
        filename: 文件名
        sandbox_root: 传入的 Sandbox 根目录（可为 "/sandbox" 虚拟路径）

    Returns:
        写入文件的绝对路径
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

    基于当前文件位置（core/shared_tools/oncokb_api.py）向上推导：
    core/shared_tools -> core -> 项目根目录 -> workspace/sandbox

    Returns:
        备用 Sandbox 根目录的绝对路径
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(current_dir, '../../workspace/sandbox'))
