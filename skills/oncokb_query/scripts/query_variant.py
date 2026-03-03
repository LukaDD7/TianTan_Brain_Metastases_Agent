#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OncoKB Query Skill - 主查询入口

提供统一的查询接口，支持多种查询类型。
"""

import os
import json
from typing import Optional, Any, Dict, List, Literal
from enum import Enum

# Pydantic v2
from pydantic import BaseModel, Field

# 本地基类
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from core.skill import BaseSkill, SkillContext, SkillExecutionError
from scripts.oncokb_client import OncoKBClient, format_variant_response


# =============================================================================
# 输入 Schema (Pydantic 模型)
# =============================================================================

class QueryType(str, Enum):
    """查询类型枚举"""
    VARIANT = "variant"
    DRUG = "drug"
    BIOMARKER = "biomarker"
    TUMOR_TYPE = "tumor_type"
    EVIDENCE = "evidence"
    GENE = "gene"


class OncoKBQueryInput(BaseModel):
    """
    OncoKB 查询的输入参数。

    根据 query_type 不同，需要的参数也不同：
    - variant: 需要 hugo_symbol 和 variant
    - drug: 需要 hugo_symbol、variant 和 drug_name
    - biomarker: 需要 biomarker_name
    - tumor_type: 需要 tumor_type
    - evidence: 需要 evidence_uuid
    - gene: 需要 hugo_symbol
    """

    query_type: QueryType = Field(
        ...,
        description="查询类型",
        examples=["variant", "drug", "biomarker", "tumor_type", "evidence", "gene"]
    )

    # === 基因/变异相关参数 ===
    hugo_symbol: Optional[str] = Field(
        default=None,
        description="基因符号 (HGNC 标准命名)，如 EGFR、TP53、BRAF",
        examples=["EGFR", "TP53", "BRAF", "KRAS"]
    )

    variant: Optional[str] = Field(
        default=None,
        description="变异描述 (蛋白质水平)，如 L858R、V600E、exon19del",
        examples=["L858R", "V600E", "exon19del", "G12C"]
    )

    # === 药物相关参数 ===
    drug_name: Optional[str] = Field(
        default=None,
        description="药物名称 (通用名)，如 Osimertinib、Vemurafenib",
        examples=["Osimertinib", "Vemurafenib", "Dabrafenib", "Trametinib"]
    )

    # === 生物标志物相关参数 ===
    biomarker_name: Optional[str] = Field(
        default=None,
        description="生物标志物名称，如 MSI-H、TMB-H、PD-L1 high",
        examples=["MSI-H", "TMB-H", "PD-L1 high", "HRD"]
    )

    # === 癌症类型相关参数 ===
    tumor_type: Optional[str] = Field(
        default=None,
        description="癌症类型 (使用 OncoKB 标准命名)",
        examples=["Non-Small Cell Lung Cancer", "Melanoma", "Colorectal Cancer"]
    )

    # === 通用参数 ===
    evidence_uuid: Optional[str] = Field(
        default=None,
        description="证据 UUID (用于 evidence 查询)"
    )

    evidence_level: Optional[str] = Field(
        default=None,
        description="证据等级过滤",
        examples=["LEVEL_1", "LEVEL_2A", "LEVEL_2B", "LEVEL_3A", "LEVEL_3B", "LEVEL_4", "R1", "R2"]
    )

    include_evidence: bool = Field(
        default=True,
        description="是否返回详细证据说明"
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "query_type": "variant",
                    "hugo_symbol": "EGFR",
                    "variant": "L858R",
                    "tumor_type": "Non-Small Cell Lung Cancer",
                    "include_evidence": True
                },
                {
                    "query_type": "drug",
                    "hugo_symbol": "BRAF",
                    "variant": "V600E",
                    "drug_name": "Vemurafenib"
                },
                {
                    "query_type": "biomarker",
                    "biomarker_name": "MSI-H",
                    "tumor_type": "Colorectal Cancer"
                },
                {
                    "query_type": "tumor_type",
                    "tumor_type": "Non-Small Cell Lung Cancer",
                    "evidence_level": "LEVEL_1"
                }
            ]
        }


# =============================================================================
# Skill 实现
# =============================================================================

class OncoKBQuery(BaseSkill[OncoKBQueryInput]):
    """
    OncoKB 癌症知识库查询 Skill。

    支持多种查询类型：
    1. variant - 基因变异临床意义查询
    2. drug - 药物敏感性查询
    3. biomarker - 生物标志物查询
    4. tumor_type - 癌症类型治疗推荐查询
    5. evidence - 证据详情查询
    6. gene - 基因基本信息查询
    """

    name = "query_oncokb"
    description = (
        "查询 OncoKB 癌症知识库获取基因变异的临床意义、药物敏感性、生物标志物等信息。\n"
        "OncoKB 是一个精准肿瘤学知识库，提供基因变异致癌性评估、治疗敏感性预测、证据等级分级等信息。\n"
        "支持查询类型：variant(变异查询)、drug(药物查询)、biomarker(生物标志物查询)、"
        "tumor_type(癌症类型查询)、evidence(证据详情)、gene(基因信息)。\n"
        "注意：需要提供 OncoKB API Token (环境变量 ONCOKB_API_TOKEN)。"
    )
    input_schema_class = OncoKBQueryInput

    def __init__(self, api_token: Optional[str] = None):
        super().__init__()
        self.api_token = api_token or os.environ.get("ONCOKB_API_TOKEN")
        # 配置重试策略
        self.retry_config.max_retries = 3
        self.retry_config.initial_delay_ms = 1000

    @property
    def input_schema(self) -> Dict[str, Any]:
        return self.input_schema_class.model_json_schema()

    def execute(self, args: OncoKBQueryInput, context: Optional[SkillContext] = None) -> str:
        """
        执行 OncoKB 查询。

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
            client = OncoKBClient(self.api_token)

            # 根据查询类型执行不同查询
            result = self._dispatch_query(client, args)

            # 格式化输出
            output = {
                "query_type": args.query_type.value,
                "success": True,
                "data": result,
                "metadata": {
                    "api_token_used": bool(self.api_token),
                    "include_evidence": args.include_evidence
                }
            }

            # 存入上下文 (如果提供)
            if context:
                context.set(f"oncokb_result_{args.query_type.value}", result)

            return json.dumps(output, ensure_ascii=False, indent=2)

        except SkillExecutionError:
            raise
        except Exception as e:
            raise SkillExecutionError(f"OncoKB 查询失败：{str(e)}") from e

    def _dispatch_query(self, client: OncoKBClient, args: OncoKBQueryInput) -> Dict[str, Any]:
        """
        根据查询类型分发到具体查询方法。

        Args:
            client: OncoKB 客户端
            args: 查询参数

        Returns:
            查询结果
        """
        query_type = args.query_type.value

        if query_type == "variant":
            return self._query_variant(client, args)
        elif query_type == "drug":
            return self._query_drug(client, args)
        elif query_type == "biomarker":
            return self._query_biomarker(client, args)
        elif query_type == "tumor_type":
            return self._query_tumor_type(client, args)
        elif query_type == "evidence":
            return self._query_evidence(client, args)
        elif query_type == "gene":
            return self._query_gene(client, args)
        else:
            raise SkillExecutionError(f"未知的查询类型：{query_type}")

    def _query_variant(self, client: OncoKBClient, args: OncoKBQueryInput) -> Dict[str, Any]:
        """基因变异查询"""
        if not args.hugo_symbol:
            raise SkillExecutionError("variant 查询需要指定 hugo_symbol (基因符号)")
        if not args.variant:
            raise SkillExecutionError("variant 查询需要指定 variant (变异描述)")

        return client.query_variant(
            hugo_symbol=args.hugo_symbol,
            variant=args.variant,
            tumor_type=args.tumor_type,
            include_evidence=args.include_evidence
        )

    def _query_drug(self, client: OncoKBClient, args: OncoKBQueryInput) -> Dict[str, Any]:
        """药物敏感性查询"""
        if not args.hugo_symbol:
            raise SkillExecutionError("drug 查询需要指定 hugo_symbol (基因符号)")
        if not args.variant:
            raise SkillExecutionError("drug 查询需要指定 variant (变异描述)")
        if not args.drug_name:
            raise SkillExecutionError("drug 查询需要指定 drug_name (药物名称)")

        return client.query_drug_sensitivity(
            hugo_symbol=args.hugo_symbol,
            variant=args.variant,
            drug_name=args.drug_name,
            tumor_type=args.tumor_type
        )

    def _query_biomarker(self, client: OncoKBClient, args: OncoKBQueryInput) -> Dict[str, Any]:
        """生物标志物查询"""
        if not args.biomarker_name:
            raise SkillExecutionError("biomarker 查询需要指定 biomarker_name")

        return client.query_biomarker(
            biomarker_name=args.biomarker_name,
            tumor_type=args.tumor_type
        )

    def _query_tumor_type(self, client: OncoKBClient, args: OncoKBQueryInput) -> Dict[str, Any]:
        """癌症类型查询"""
        if not args.tumor_type:
            raise SkillExecutionError("tumor_type 查询需要指定 tumor_type (癌症类型)")

        return client.query_tumor_type(
            tumor_type=args.tumor_type,
            evidence_level=args.evidence_level
        )

    def _query_evidence(self, client: OncoKBClient, args: OncoKBQueryInput) -> Dict[str, Any]:
        """证据详情查询"""
        if not args.evidence_uuid:
            raise SkillExecutionError("evidence 查询需要指定 evidence_uuid")

        return client.query_evidence(evidence_uuid=args.evidence_uuid)

    def _query_gene(self, client: OncoKBClient, args: OncoKBQueryInput) -> Dict[str, Any]:
        """基因信息查询"""
        if not args.hugo_symbol:
            raise SkillExecutionError("gene 查询需要指定 hugo_symbol (基因符号)")

        return client.query_gene(hugo_symbol=args.hugo_symbol)


# =============================================================================
# CLI 入口
# =============================================================================

def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description="OncoKB Query Skill")
    parser.add_argument("--query_type", required=True,
                        choices=["variant", "drug", "biomarker", "tumor_type", "evidence", "gene"])
    parser.add_argument("--hugo_symbol", help="基因符号 (如 EGFR)")
    parser.add_argument("--variant", help="变异描述 (如 L858R)")
    parser.add_argument("--drug_name", help="药物名称")
    parser.add_argument("--biomarker_name", help="生物标志物名称")
    parser.add_argument("--tumor_type", help="癌症类型")
    parser.add_argument("--evidence_uuid", help="证据 UUID")
    parser.add_argument("--evidence_level", help="证据等级")
    parser.add_argument("--no-evidence", action="store_true", help="不返回详细证据")

    args = parser.parse_args()

    # 构建输入参数
    input_args = OncoKBQueryInput(
        query_type=args.query_type,
        hugo_symbol=args.hugo_symbol,
        variant=args.variant,
        drug_name=args.drug_name,
        biomarker_name=args.biomarker_name,
        tumor_type=args.tumor_type,
        evidence_uuid=args.evidence_uuid,
        evidence_level=args.evidence_level,
        include_evidence=not args.no_evidence
    )

    skill = OncoKBQuery()

    try:
        result = skill.execute(input_args)
        print(result)
    except (SkillExecutionError, Exception) as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        exit(1)


if __name__ == "__main__":
    main()
