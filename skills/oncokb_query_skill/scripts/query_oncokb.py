#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OncoKB CLI 脚本 - 供 Agent 通过 execute 调用

用法:
    python query_oncokb.py mutation --gene BRAF --alteration V600E --tumor-type "Melanoma"
    python query_oncokb.py fusion --gene1 EML4 --gene2 ALK --tumor-type "Non-Small Cell Lung Cancer"
    python query_oncokb.py cna --gene EGFR --type Amplification --tumor-type "Glioblastoma"
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict

ONCOKB_BASE_URL = "https://www.oncokb.org/api/v1"
ONCOKB_API_KEY = os.environ.get("ONCOKB_API_KEY", "")


def make_oncokb_request(endpoint: str, params: Dict) -> Dict:
    """发送 OncoKB API 请求"""
    if not ONCOKB_API_KEY:
        return {"error": "ONCOKB_API_KEY not set", "status": "error"}

    url = f"{ONCOKB_BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {ONCOKB_API_KEY}", "Accept": "application/json"}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {"error": f"HTTP {response.status_code}", "status": "error", "details": str(e)}
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "status": "error"}


def query_mutation(gene: str, alteration: str, tumor_type: str):
    """查询点突变"""
    params = {"hugoSymbol": gene, "alteration": alteration, "tumorType": tumor_type}
    result = make_oncokb_request("/annotate/mutations/byProteinChange", params)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def query_fusion(gene1: str, gene2: str, tumor_type: str):
    """查询融合基因"""
    params = {
        "hugoSymbolA": gene1,
        "hugoSymbolB": gene2,
        "tumorType": tumor_type,
        "structuralVariantType": "FUSION",
        "isFunctionalFusion": "true"
    }
    result = make_oncokb_request("/annotate/structuralVariants", params)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def query_cna(gene: str, alteration_type: str, tumor_type: str):
    """查询拷贝数变异"""
    params = {
        "hugoSymbol": gene,
        "copyNumberAlterationType": alteration_type.upper(),
        "tumorType": tumor_type
    }
    result = make_oncokb_request("/annotate/copyNumberAlterations", params)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="OncoKB Query CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # mutation
    p_mut = subparsers.add_parser("mutation", help="查询点突变")
    p_mut.add_argument("--gene", required=True)
    p_mut.add_argument("--alteration", required=True)
    p_mut.add_argument("--tumor-type", required=True)

    # fusion
    p_fus = subparsers.add_parser("fusion", help="查询融合基因")
    p_fus.add_argument("--gene1", required=True)
    p_fus.add_argument("--gene2", required=True)
    p_fus.add_argument("--tumor-type", required=True)

    # cna
    p_cna = subparsers.add_parser("cna", help="查询拷贝数变异")
    p_cna.add_argument("--gene", required=True)
    p_cna.add_argument("--type", choices=["Amplification", "Deletion"], required=True)
    p_cna.add_argument("--tumor-type", required=True)

    args = parser.parse_args()

    if args.command == "mutation":
        query_mutation(args.gene, args.alteration, args.tumor_type)
    elif args.command == "fusion":
        query_fusion(args.gene1, args.gene2, args.tumor_type)
    elif args.command == "cna":
        query_cna(args.gene, args.type, args.tumor_type)


if __name__ == "__main__":
    main()
